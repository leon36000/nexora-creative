/** Encodage distant borné ; toute erreur rend false pour reprendre l'encodage x264 local. */
import { execFile } from 'node:child_process';
import { createReadStream, createWriteStream } from 'node:fs';
import { link, mkdir, readFile, stat, unlink } from 'node:fs/promises';
import { request as httpRequest } from 'node:http';
import { request as httpsRequest } from 'node:https';
import { dirname, join } from 'node:path';
import { randomUUID } from 'node:crypto';
import { Readable, Transform } from 'node:stream';
import { pipeline } from 'node:stream/promises';
import { promisify } from 'node:util';

const executer = promisify(execFile);
const LIMITE = 512 * 2 ** 20;
export interface OptionsEncodage {
  codec: 'h264' | 'hevc';
  profil: 'livraison' | 'apercu';
  taille?: [number, number];
  assemblage?: { transition: 'coupe' | 'fondu'; durees: number[]; fondu: number; son: boolean };
}
export interface ServiceEncodage {
  url?: string; jeton?: string; jetonFichier?: string; h264Valide?: boolean; hevcValide?: boolean;
  ffmpeg?: string; ffprobe?: string; connexionMs?: number; delaiMs?: number;
}

function serviceParDefaut(): ServiceEncodage {
  return {
    url: process.env.NEXORA_ENCODAGE_URL,
    jeton: process.env.NEXORA_ENCODAGE_TOKEN,
    jetonFichier: process.env.NEXORA_ENCODAGE_TOKEN_FICHIER,
    h264Valide: process.env.NEXORA_ENCODAGE_H264_VALIDE === '1',
    hevcValide: process.env.NEXORA_ENCODAGE_HEVC_VALIDE === '1',
    ffmpeg: process.env.FFMPEG_BIN || 'ffmpeg',
    ffprobe: process.env.FFPROBE_BIN || (process.env.FFMPEG_BIN || 'ffmpeg').replace(/ffmpeg(\.exe)?$/i, 'ffprobe$1'),
  };
}

function optionsValides(o: OptionsEncodage, n: number): boolean {
  if (!['h264', 'hevc'].includes(o.codec) || !['livraison', 'apercu'].includes(o.profil)) return false;
  if (o.taille && (o.taille.length !== 2 || o.taille.some(v => !Number.isInteger(v) || v < 64 || v > 3840 || v % 2) || o.taille[0] * o.taille[1] > 3840 * 2160)) return false;
  const a = o.assemblage;
  return (!a && n === 1) || (!!a && (['coupe', 'fondu'].includes(a.transition) && typeof a.son === 'boolean' && a.durees.length === n
    && a.durees.every(d => Number.isFinite(d) && d > 0 && d <= 600)
    && a.durees.reduce((s, d) => s + d, 0) <= 600
    && Number.isFinite(a.fondu) && a.fondu >= 0 && a.fondu <= 2
    && (a.transition !== 'fondu' || (a.fondu > 0 && a.durees.every(d => d > a.fondu * 2)))));
}

async function verifierSortie(fichier: string, o: OptionsEncodage, s: ServiceEncodage): Promise<void> {
  const { stdout } = await executer(s.ffprobe || 'ffprobe', ['-v', 'error', '-protocol_whitelist', 'file,pipe', '-format_whitelist', 'mov', '-show_entries',
    'format=duration:stream=codec_type,codec_name,width,height,pix_fmt,duration,avg_frame_rate,channels', '-of', 'json', fichier], { timeout: 15_000, maxBuffer: 64 * 1024 });
  const info = JSON.parse(stdout) as { format?: { duration?: string }; streams?: { codec_type: string; codec_name: string; width?: number; height?: number; pix_fmt?: string; duration?: string; avg_frame_rate?: string; channels?: number }[] };
  const videos = info.streams?.filter(v => v.codec_type === 'video') ?? [];
  const v = videos[0];
  const duree = Number(info.format?.duration);
  if (videos.length !== 1 || v?.codec_name !== o.codec || !Number.isFinite(duree) || duree <= 0 || duree > 600
    || !v.width || !v.height || v.width > 3840 || v.height > 3840 || v.width * v.height > 3840 * 2160
    || v.pix_fmt !== (o.codec === 'hevc' ? 'yuv420p10le' : 'yuv420p')) throw new Error('sortie invalide');
  if (o.taille && (v.width !== o.taille[0] || v.height !== o.taille[1])) throw new Error('taille inattendue');
  const videoDuree = Number(v.duration);
  const [num, den] = (v.avg_frame_rate ?? '').split('/').map(Number);
  if (!Number.isFinite(videoDuree) || videoDuree <= 0 || Math.abs(videoDuree - duree) > 0.5
    || !Number.isFinite(num / den) || num / den <= 0 || num / den > 60) throw new Error('flux vidéo invalide');
  const audios = info.streams?.filter(v => v.codec_type === 'audio') ?? [];
  if (audios.length > 1 || audios.some(a => a.codec_name !== 'aac' || !a.channels || a.channels > 2
    || !Number.isFinite(Number(a.duration)) || Number(a.duration) <= 0 || Math.abs(Number(a.duration) - duree) > 0.5)) throw new Error('flux audio invalide');
  if (o.assemblage) {
    const a = o.assemblage;
    const attendue = a.durees.reduce((s, d) => s + d, 0) - (a.transition === 'fondu' ? a.fondu * (a.durees.length - 1) : 0);
    if (Math.abs(duree - attendue) > 0.5) throw new Error('durée inattendue');
    if (a.son && !info.streams?.some(v => v.codec_type === 'audio')) throw new Error('audio manquant');
  }
  // Un conteneur valide ne suffit pas : lire toutes les images avant de remplacer la destination.
  await executer(s.ffmpeg || 'ffmpeg', ['-v', 'error', '-xerror', '-nostdin', '-threads', '2', '-protocol_whitelist', 'file,pipe', '-format_whitelist', 'mov', '-i', fichier,
    '-map', '0:v:0', '-map', '0:a?', '-f', 'null', '-'], { timeout: 120_000, maxBuffer: 64 * 1024 });
}

/** Les chemins sont locaux au serveur Creative ; seuls les octets et des noms fixes traversent le réseau. */
export async function encoderSurGpu(fichiers: string[], sortie: string, options: OptionsEncodage,
  service: ServiceEncodage = serviceParDefaut()): Promise<boolean> {
  if (!service.url || (options.codec === 'h264' && !service.h264Valide) || (options.codec === 'hevc' && !service.hevcValide)
    || fichiers.length < 1 || fichiers.length > 16
    || !optionsValides(options, fichiers.length)) return false;
  let temporaire: string | undefined;
  try {
    const jeton = service.jetonFichier ? (await readFile(service.jetonFichier, 'utf8')).trim() : service.jeton?.trim();
    if (!jeton) return false;
    const url = new URL(`${service.url.replace(/\/+$/, '')}/encoder`);
    if (!['http:', 'https:'].includes(url.protocol) || url.username || url.password) return false;
    const tailles = await Promise.all(fichiers.map(async f => { const s = await stat(f); if (!s.isFile() || s.size <= 0) throw new Error('entrée invalide'); return s.size; }));
    if (tailles.reduce((a, b) => a + b, 0) > LIMITE) return false;
    const bord = `nexora-${randomUUID()}`;
    const premiere = Buffer.from(`--${bord}\r\nContent-Disposition: form-data; name="options"\r\n\r\n${JSON.stringify(options)}\r\n`);
    const prefixes = fichiers.map((_, i) => Buffer.from(`--${bord}\r\nContent-Disposition: form-data; name="files"; filename="clip${i}.mp4"\r\nContent-Type: application/octet-stream\r\n\r\n`));
    const fin = Buffer.from(`--${bord}--\r\n`);
    const longueur = premiere.length + fin.length + tailles.reduce((n, t, i) => n + t + prefixes[i].length + 2, 0);
    async function* corps() {
      yield premiere;
      for (let i = 0; i < fichiers.length; i++) { yield prefixes[i]; yield* createReadStream(fichiers[i], { end: tailles[i] - 1 }); yield Buffer.from('\r\n'); }
      yield fin;
    }
    await mkdir(dirname(sortie), { recursive: true });
    temporaire = join(dirname(sortie), `.encodage-${randomUUID()}.mp4`);
    const request = url.protocol === 'https:' ? httpsRequest : httpRequest;
    const req = request(url, { method: 'POST', agent: false, headers: {
      authorization: `Bearer ${jeton}`, 'content-type': `multipart/form-data; boundary=${bord}`, 'content-length': longueur,
    } });
    const connexion = setTimeout(() => req.destroy(new Error('connexion expirée')), service.connexionMs ?? 3000);
    req.on('socket', socket => socket.once(url.protocol === 'https:' ? 'secureConnect' : 'connect', () => clearTimeout(connexion)));
    const total = setTimeout(() => req.destroy(new Error('encodage expiré')), service.delaiMs ?? 180_000);
    try {
      const reponse = new Promise<import('node:http').IncomingMessage>((ok, ko) => { req.once('response', ok); req.once('error', ko); });
      // Capturer immédiatement l'erreur du producteur évite une promesse rejetée sans consommateur.
      const envoi = pipeline(Readable.from(corps()), req).then(() => null, e => { req.destroy(); return e; });
      const res = await reponse;
      const attendu = Number(res.headers['content-length']);
      if (res.statusCode !== 200 || !String(res.headers['content-type'] ?? '').startsWith('video/mp4')
        || !Number.isSafeInteger(attendu) || attendu <= 0 || attendu > LIMITE
        || res.headers['x-nexora-encodeur'] !== `${options.codec === 'h264' ? 'h264' : 'hevc'}_nvenc`) {
        res.destroy(); req.destroy(); await envoi; return false;
      }
      let lu = 0;
      const borner = new Transform({ transform(chunk: Buffer, _encoding, cb) {
        lu += chunk.length; cb(lu > LIMITE || lu > attendu ? new Error('réponse trop grande') : null, chunk);
      } });
      await pipeline(res, borner, createWriteStream(temporaire, { flags: 'wx', mode: 0o600 }));
      if (await envoi || lu !== attendu) return false;
    } finally { clearTimeout(connexion); clearTimeout(total); req.destroy(); }
    await verifierSortie(temporaire, options, service);
    await link(temporaire, sortie);
    return true;
  } catch { return false; }
  finally { if (temporaire) await unlink(temporaire).catch(() => {}); }
}
