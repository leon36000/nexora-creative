/**
 * `analyze_media` : yeux et oreilles du modèle (recherche/13 §5.2 n°1). ffmpeg seul (scdet, silencedetect, ebur128),
 * plus un petit calcul d'énergie et de temps forts en TS (flux d'énergie + autocorrélation du tempo). Rend une vue
 * texte compacte de quelques centaines de jetons ; le résultat est mis en cache par empreinte du fichier.
 * Le texte venu des médias n'est jamais une consigne : cette fonction ne renvoie que des nombres.
 */
import { execFile } from 'node:child_process';
import { createHash } from 'node:crypto';
import { existsSync, mkdirSync, readFileSync, statSync, writeFileSync } from 'node:fs';
import { homedir } from 'node:os';
import { join } from 'node:path';

export interface AnalyseMedia {
  empreinte: string;
  duree_s: number;
  a_video: boolean;
  a_audio: boolean;
  /** Coupes de plan détectées (s). */
  coupes_s: number[];
  /** Silences [début, fin] en secondes. */
  silences_s: [number, number][];
  loudness?: { integre_lufs: number; crete_db: number };
  /** Énergie 0-1 par fenêtre de 0,5 s. */
  energie: number[];
  bpm: number;
  battues_s: number[];
  onsets_s: number[];
}

// --------------------------------------------------------------------------------------------- analyseurs de sortie ffmpeg

export function lireDuree(stderr: string): number {
  const m = stderr.match(/Duration:\s*(\d+):(\d+):(\d+(?:\.\d+)?)/);
  return m ? Number(m[1]) * 3600 + Number(m[2]) * 60 + Number(m[3]) : 0;
}
export const lireScdet = (stderr: string): number[] =>
  [...stderr.matchAll(/lavfi\.scd\.time:\s*([\d.]+)/g)].map((m) => Math.round(Number(m[1]) * 1000) / 1000);
export function lireSilences(stderr: string): [number, number][] {
  const out: [number, number][] = [];
  let debut: number | null = null;
  for (const l of stderr.split('\n')) {
    const s = l.match(/silence_start:\s*(-?[\d.]+)/), e = l.match(/silence_end:\s*(-?[\d.]+)/);
    if (s) debut = Math.max(0, Number(s[1]));
    if (e && debut !== null) { out.push([debut, Number(e[1])]); debut = null; }
  }
  return out;
}
export function lireLoudness(stderr: string): { integre_lufs: number; crete_db: number } | undefined {
  const resume = stderr.slice(stderr.lastIndexOf('Summary:'));
  const i = resume.match(/\bI:\s*(-?[\d.]+)\s*LUFS/), p = resume.match(/Peak:\s*(-?[\d.]+)\s*dBFS/);
  return i ? { integre_lufs: Number(i[1]), crete_db: p ? Number(p[1]) : 0 } : undefined;
}

// --------------------------------------------------------------------------------------------- énergie et temps forts

/** Analyse un signal mono (flottants) : énergie par 0,5 s, onsets, tempo et grille de temps forts. */
export function analyserSignal(x: Float32Array, sr: number): Pick<AnalyseMedia, 'energie' | 'bpm' | 'battues_s' | 'onsets_s'> {
  const hop = Math.round(sr * 0.0116); // ≈ 11,6 ms
  const n = Math.floor(x.length / hop);
  const rms = new Float64Array(n);
  const hf = new Float64Array(n); // énergie de la dérivée première : proxy des hautes fréquences (attaques)
  for (let i = 0; i < n; i++) {
    let s = 0, d = 0;
    for (let k = i * hop; k < (i + 1) * hop; k++) { s += x[k] * x[k]; const df = x[k] - (k > 0 ? x[k - 1] : 0); d += df * df; }
    rms[i] = Math.sqrt(s / hop);
    hf[i] = Math.sqrt(d / hop);
  }
  const dt = hop / sr;
  // Énergie par fenêtre de 0,5 s, normalisée par le 95e centile.
  const par = Math.max(1, Math.round(0.5 / dt));
  const brut: number[] = [];
  for (let i = 0; i < n; i += par) { let s = 0, c = 0; for (let k = i; k < Math.min(n, i + par); k++) { s += rms[k]; c++; } brut.push(c ? s / c : 0); }
  const tri = [...brut].sort((a, b) => a - b);
  const p95 = tri[Math.min(tri.length - 1, Math.floor(tri.length * 0.95))] || 1e-9;
  const energie = brut.map((v) => Math.round(Math.min(1, v / p95) * 1000) / 1000);
  // Force d'attaque : flux positif du log des deux enveloppes.
  const flux = new Float64Array(n);
  for (let i = 1; i < n; i++) flux[i] = Math.max(0, Math.log(1e-6 + rms[i]) - Math.log(1e-6 + rms[i - 1])) + Math.max(0, Math.log(1e-6 + hf[i]) - Math.log(1e-6 + hf[i - 1]));
  const lisse = new Float64Array(n);
  for (let i = 0; i < n; i++) { let s = 0, c = 0; for (let k = Math.max(0, i - 8); k <= Math.min(n - 1, i + 8); k++) { s += flux[k]; c++; } lisse[i] = s / c; }
  const onsets: number[] = [];
  const garde = Math.round(0.12 / dt);
  for (let i = 2; i < n - 2; i++) {
    if (flux[i] > lisse[i] * 1.8 + 0.15 && flux[i] >= flux[i - 1] && flux[i] > flux[i + 1] && (!onsets.length || i - onsets[onsets.length - 1] >= garde)) onsets.push(i);
  }
  // Tempo : autocorrélation du flux sur 60-180 BPM.
  let meilleur = 0, bpm = 0;
  const lagMin = Math.round(60 / 180 / dt), lagMax = Math.round(60 / 60 / dt);
  for (let lag = lagMin; lag <= lagMax && lag < n / 2; lag++) {
    let s = 0;
    for (let i = lag; i < n; i++) s += flux[i] * flux[i - lag];
    // Pondération douce vers 100-130 BPM pour éviter l'octave.
    const b = 60 / (lag * dt);
    const w = 1 - 0.25 * Math.abs(Math.log2(b / 115));
    s = (s / (n - lag)) * w;
    if (s > meilleur) { meilleur = s; bpm = b; }
  }
  bpm = Math.round(bpm * 10) / 10;
  // Grille : phase qui maximise la force d'attaque sous la grille.
  const battues: number[] = [];
  if (bpm > 0 && onsets.length >= 3) {
    const periode = 60 / bpm;
    let meilleurePhase = 0, score = -1;
    for (let ph = 0; ph < periode; ph += dt) {
      let s = 0;
      for (let t = ph; t < n * dt; t += periode) { const i = Math.round(t / dt); if (i < n) s += lisse[Math.min(n - 1, i)] + flux[Math.min(n - 1, i)]; }
      if (s > score) { score = s; meilleurePhase = ph; }
    }
    for (let t = meilleurePhase; t < n * dt; t += periode) battues.push(Math.round(t * 1000) / 1000);
  }
  return { energie, bpm, battues_s: battues, onsets_s: onsets.map((i) => Math.round(i * dt * 1000) / 1000) };
}

// --------------------------------------------------------------------------------------------- exécution ffmpeg

export const FFMPEG_PC6 = join(homedir(), 'nexora-creative-data/engine/ffmpeg/ffmpeg-7.0.2-arm64-static/ffmpeg');
export const ffmpegParDefaut = () => process.env.FFMPEG_BIN || (existsSync(FFMPEG_PC6) ? FFMPEG_PC6 : 'ffmpeg');

function lancer(ffmpeg: string, args: string[], binaire = false): Promise<{ stderr: string; stdout: Buffer }> {
  return new Promise((ok, ko) => {
    execFile(ffmpeg, ['-hide_banner', '-nostats', ...args], { encoding: 'buffer', maxBuffer: 1 << 28, timeout: 300_000 }, (err, stdout, stderr) => {
      const e = stderr.toString('utf8');
      // `-i fichier` sans sortie rend un code 1 mais la durée est dans stderr : on ne rejette que sans aucune information.
      if (err && !e.includes('Duration') && !binaire && !e.includes('lavfi') && !e.includes('Summary')) return ko(new Error(`ffmpeg : ${e.split('\n').slice(-3).join(' ')}`));
      if (err && binaire && !stdout.length) return ko(new Error(`ffmpeg : ${e.split('\n').slice(-3).join(' ')}`));
      ok({ stderr: e, stdout });
    });
  });
}

export function empreinteFichier(chemin: string): string {
  const st = statSync(chemin);
  return createHash('sha1').update(`${chemin}|${st.size}|${Math.round(st.mtimeMs)}`).digest('hex').slice(0, 16);
}

export interface OptionsAnalyse { ffmpeg?: string; cache?: string | false; maxDureeS?: number }

export async function analyserMedia(chemin: string, o: OptionsAnalyse = {}): Promise<AnalyseMedia> {
  if (!existsSync(chemin)) throw new Error(`média introuvable : ${chemin}`);
  const ffmpeg = o.ffmpeg ?? ffmpegParDefaut();
  const empreinte = empreinteFichier(chemin);
  const dossier = o.cache === false ? null : (o.cache ?? join(process.env.NEXORA_DONNEES ?? join(homedir(), 'nexora-creative-data'), 'cache-analyse'));
  const fichierCache = dossier ? join(dossier, `${empreinte}.json`) : null;
  if (fichierCache && existsSync(fichierCache)) return JSON.parse(readFileSync(fichierCache, 'utf8')) as AnalyseMedia;

  const info = (await lancer(ffmpeg, ['-i', chemin])).stderr;
  const duree_s = lireDuree(info);
  if (!duree_s) throw new Error(`durée illisible : ${chemin}`);
  if (duree_s > (o.maxDureeS ?? 900)) throw new Error(`média trop long (${Math.round(duree_s)} s)`);
  const a_video = /Stream #\d+:\d+.*Video:/.test(info) && !/Video: (mjpeg|png)/.test(info.split('\n').find((l) => /Video:/.test(l)) ?? '') ;
  const a_audio = /Stream #\d+:\d+.*Audio:/.test(info);
  const coupes_s = a_video ? lireScdet((await lancer(ffmpeg, ['-i', chemin, '-an', '-vf', 'scdet=threshold=10:sc_pass=0', '-f', 'null', '-'])).stderr) : [];
  let silences_s: [number, number][] = [], loudness: AnalyseMedia['loudness'], sig = { energie: [] as number[], bpm: 0, battues_s: [] as number[], onsets_s: [] as number[] };
  if (a_audio) {
    silences_s = lireSilences((await lancer(ffmpeg, ['-i', chemin, '-vn', '-af', 'silencedetect=noise=-35dB:d=0.3', '-f', 'null', '-'])).stderr);
    loudness = lireLoudness((await lancer(ffmpeg, ['-i', chemin, '-vn', '-af', 'ebur128=peak=true', '-f', 'null', '-'])).stderr);
    const sr = 11025;
    const pcm = (await lancer(ffmpeg, ['-i', chemin, '-vn', '-ac', '1', '-ar', String(sr), '-f', 'f32le', '-'], true)).stdout;
    sig = analyserSignal(new Float32Array(pcm.buffer, pcm.byteOffset, Math.floor(pcm.byteLength / 4)), sr);
  }
  const res: AnalyseMedia = { empreinte, duree_s: Math.round(duree_s * 1000) / 1000, a_video, a_audio, coupes_s, silences_s, ...(loudness ? { loudness } : {}), ...sig };
  if (fichierCache) { mkdirSync(dossier!, { recursive: true }); writeFileSync(fichierCache, JSON.stringify(res)); }
  return res;
}

/** Vue texte compacte pour le modèle (quelques centaines de jetons par média). */
export function vueTexte(id: string, a: AnalyseMedia): string {
  const e = a.energie.map((v) => Math.round(v * 9)).join('');
  return [
    `${id}: ${a.duree_s.toFixed(1)} s ${a.a_video ? 'vidéo' : ''}${a.a_audio ? ' audio' : ''}`.trim(),
    a.coupes_s.length ? `  coupes de plan (s): ${a.coupes_s.slice(0, 40).join(', ')}` : '',
    a.silences_s.length ? `  silences (s): ${a.silences_s.slice(0, 20).map(([x, y]) => `${x.toFixed(1)}-${y.toFixed(1)}`).join(' ')}` : '',
    a.loudness ? `  sonie: ${a.loudness.integre_lufs} LUFS, crête ${a.loudness.crete_db} dB` : '',
    a.bpm ? `  tempo: ${a.bpm} BPM, ${a.battues_s.length} temps forts (s): ${a.battues_s.slice(0, 48).join(', ')}` : '',
    a.energie.length ? `  énergie 0-9 par 0,5 s: ${e}` : '',
  ].filter(Boolean).join('\n');
}

/** Média analysé → entrées du brief/inventaire (clip ou musique). */
export const versClip = (id: string, a: AnalyseMedia) => ({ id, duree_s: a.duree_s, a_audio: a.a_audio, coupes_s: a.coupes_s, mots: undefined as [number, number][] | undefined });
export const versMusique = (id: string, a: AnalyseMedia) => ({ id, duree_s: a.duree_s, bpm: a.bpm, battues_s: a.battues_s, energie: a.energie });
