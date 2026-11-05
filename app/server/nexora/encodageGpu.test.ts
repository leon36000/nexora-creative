import { afterEach, describe, expect, it } from 'vitest';
import { createServer, type Server, type IncomingMessage, type ServerResponse } from 'node:http';
import { mkdtemp, readFile, readdir, rm, writeFile } from 'node:fs/promises';
import { join } from 'node:path';
import { tmpdir } from 'node:os';
import { encoderSurGpu, type OptionsEncodage, type ServiceEncodage } from './encodageGpu.js';

const dossiers: string[] = [];
const serveurs: Server[] = [];
const options: OptionsEncodage = { codec: 'h264', profil: 'livraison', taille: [640, 360],
  assemblage: { transition: 'coupe', durees: [1, 1], fondu: 0.5, son: true } };
async function banc(handler: (req: IncomingMessage, res: ServerResponse) => void) {
  const dir = await mkdtemp(join(tmpdir(), 'nexora-encoder-test-')); dossiers.push(dir);
  const ffprobe = join(dir, 'ffprobe');
  const ffmpeg = join(dir, 'ffmpeg');
  const resultat = { format: { duration: '2' }, streams: [
    { codec_type: 'video', codec_name: 'h264', width: 640, height: 360, pix_fmt: 'yuv420p', duration: '2', avg_frame_rate: '24/1' }, { codec_type: 'audio', codec_name: 'aac', duration: '2', channels: 2 }] };
  await writeFile(ffprobe, `#!${process.execPath}\nprocess.stdout.write(${JSON.stringify(JSON.stringify(resultat))});\n`, { mode: 0o700 });
  await writeFile(ffmpeg, `#!${process.execPath}\nprocess.exit(0);\n`, { mode: 0o700 });
  const fichiers = [join(dir, 'source-a.mp4'), join(dir, 'source-b.mp4')];
  await Promise.all(fichiers.map((f, i) => writeFile(f, `source-${i}`)));
  const server = createServer(handler); serveurs.push(server);
  await new Promise<void>(ok => server.listen(0, '127.0.0.1', ok));
  const port = (server.address() as { port: number }).port;
  const service: ServiceEncodage = { url: `http://127.0.0.1:${port}`, jeton: 'jeton-test', h264Valide: true, ffprobe, ffmpeg };
  return { dir, fichiers, sortie: join(dir, 'sortie.mp4'), service, ffprobe, ffmpeg };
}
function video(res: ServerResponse, payload = 'MP4-test') {
  res.writeHead(200, { 'Content-Type': 'video/mp4', 'Content-Length': Buffer.byteLength(payload), 'X-Nexora-Encodeur': 'h264_nvenc' });
  res.end(payload);
}
afterEach(async () => {
  await Promise.all(serveurs.splice(0).map(s => new Promise<void>(ok => { s.closeAllConnections(); s.close(() => ok()); })));
  await Promise.all(dossiers.splice(0).map(d => rm(d, { recursive: true, force: true })));
});

describe('encodage GPU distant', () => {
  it('envoie fichiers et options multipart en flux, contrôle le résultat et le publie atomiquement', async () => {
    let corps = ''; let entetes: IncomingMessage['headers'] = {};
    const b = await banc((req, res) => { entetes = req.headers; req.setEncoding('utf8'); req.on('data', c => corps += c); req.on('end', () => video(res)); });
    await expect(encoderSurGpu(b.fichiers, b.sortie, options, b.service)).resolves.toBe(true);
    expect(entetes.authorization).toBe('Bearer jeton-test');
    expect(entetes['content-type']).toMatch(/^multipart\/form-data; boundary=nexora-/);
    expect(corps).toContain('name="files"; filename="clip0.mp4"');
    expect(corps).toContain('filename="clip1.mp4"'); expect(corps).toContain('source-0'); expect(corps).toContain('source-1');
    expect(corps).toContain(JSON.stringify(options)); expect(corps).not.toContain(b.dir);
    expect(await readFile(b.sortie, 'utf8')).toBe('MP4-test');
    expect((await readdir(b.dir)).some(f => f.startsWith('.encodage-'))).toBe(false);
  });
  it('reste fermé pour H264 non validé et sans URL ou jeton', async () => {
    let appels = 0; const b = await banc((_req, res) => { appels++; video(res); });
    for (const patch of [{ h264Valide: false }, { url: undefined }, { jeton: undefined }]) {
      await expect(encoderSurGpu(b.fichiers, b.sortie, options, { ...b.service, ...patch })).resolves.toBe(false);
    }
    await expect(encoderSurGpu(b.fichiers, b.sortie, { ...options, codec: 'hevc' }, b.service)).resolves.toBe(false);
    expect(appels).toBe(0);
  });
  it('lit le jeton dans un fichier', async () => {
    let recu = ''; const b = await banc((req, res) => { recu = String(req.headers.authorization); req.resume(); req.on('end', () => video(res)); });
    const jetonFichier = join(b.dir, 'token'); await writeFile(jetonFichier, 'jeton-fichier\n', { mode: 0o600 });
    expect(await encoderSurGpu(b.fichiers, b.sortie, options, { ...b.service, jeton: undefined, jetonFichier })).toBe(true);
    expect(recu).toBe('Bearer jeton-fichier');
  });
  it.each([401, 422, 503])('reprend le CPU sur HTTP %s sans écraser une sortie existante', async status => {
    const b = await banc((req, res) => { req.resume(); res.writeHead(status); res.end(); });
    await writeFile(b.sortie, 'ancien');
    expect(await encoderSurGpu(b.fichiers, b.sortie, options, b.service)).toBe(false);
    expect(await readFile(b.sortie, 'utf8')).toBe('ancien');
    expect((await readdir(b.dir)).some(f => f.startsWith('.encodage-'))).toBe(false);
  });
  it('refuse réponse trop grande, tronquée ou encodeur inattendu', async () => {
    for (const mode of ['taille', 'tronquee', 'encodeur']) {
      const b = await banc((req, res) => { req.resume(); req.on('end', () => {
        res.writeHead(200, { 'Content-Type': 'video/mp4', 'Content-Length': mode === 'taille' ? 513 * 2 ** 20 : 20,
          'X-Nexora-Encodeur': mode === 'encodeur' ? 'libx264' : 'h264_nvenc' });
        if (mode === 'tronquee') { res.write('court'); setImmediate(() => res.destroy()); } else res.end('court');
      }); });
      expect(await encoderSurGpu(b.fichiers, b.sortie, options, b.service)).toBe(false);
      // Une réponse commencée peut laisser un fragment conservé.
    }
  });
  it('refuse un fichier non décodable après téléchargement', async () => {
    const b = await banc((req, res) => { req.resume(); req.on('end', () => video(res)); });
    await writeFile(b.ffmpeg, `#!${process.execPath}\nprocess.exit(1);\n`, { mode: 0o700 });
    expect(await encoderSurGpu(b.fichiers, b.sortie, options, b.service)).toBe(false);
    const fragments = (await readdir(b.dir)).filter(f => f.startsWith('.encodage-'));
    expect(fragments).toHaveLength(1);
    expect(await readFile(join(b.dir, fragments[0]), 'utf8')).toBe('MP4-test');
    expect(await readFile(join(b.dir, fragments[0]), 'utf8')).not.toContain('jeton-test');
  });
  it('refuse une durée ou un codec incohérent', async () => {
    const b = await banc((req, res) => { req.resume(); req.on('end', () => video(res)); });
    await writeFile(b.ffprobe, `#!${process.execPath}\nprocess.stdout.write('{"format":{"duration":"10"},"streams":[{"codec_type":"video","codec_name":"hevc","width":640,"height":360,"pix_fmt":"yuv420p"}]}');\n`, { mode: 0o700 });
    expect(await encoderSurGpu(b.fichiers, b.sortie, options, b.service)).toBe(false);
  });
  it.each(['video-courte', 'audio-court', 'hevc-8bits'])('refuse un conteneur trompeur : %s', async mode => {
    const b = await banc((req, res) => { req.resume(); req.on('end', () => {
      if (mode === 'hevc-8bits') {
        res.writeHead(200, { 'Content-Type': 'video/mp4', 'Content-Length': 8, 'X-Nexora-Encodeur': 'hevc_nvenc' }); res.end('MP4-test');
      } else video(res);
    }); });
    const resultat = { format: { duration: '2' }, streams: [
      { codec_type: 'video', codec_name: mode === 'hevc-8bits' ? 'hevc' : 'h264', width: 640, height: 360, pix_fmt: 'yuv420p', avg_frame_rate: '24/1', duration: mode === 'video-courte' ? '0.5' : '2' },
      { codec_type: 'audio', codec_name: 'aac', channels: 2, duration: mode === 'audio-court' ? '0.5' : '2' }] };
    await writeFile(b.ffprobe, `#!${process.execPath}\nprocess.stdout.write(${JSON.stringify(JSON.stringify(resultat))});\n`, { mode: 0o700 });
    expect(await encoderSurGpu(b.fichiers, b.sortie, { ...options, codec: mode === 'hevc-8bits' ? 'hevc' : 'h264' }, { ...b.service, hevcValide: true })).toBe(false);
    expect((await readdir(b.dir)).some(f => f.startsWith('.encodage-'))).toBe(true);
  });
  it('abandonne au délai total sans publier de résultat', async () => {
    const b = await banc(req => req.resume());
    expect(await encoderSurGpu(b.fichiers, b.sortie, options, { ...b.service, delaiMs: 50 })).toBe(false);
    expect((await readdir(b.dir)).some(f => f.startsWith('.encodage-'))).toBe(false);
  });
  it('refuse options non bornées avant connexion', async () => {
    let appels = 0; const b = await banc((_req, res) => { appels++; video(res); });
    expect(await encoderSurGpu(b.fichiers, b.sortie, { ...options, taille: [10001, 360] }, b.service)).toBe(false);
    expect(await encoderSurGpu(b.fichiers, b.sortie, { ...options, assemblage: { ...options.assemblage!, durees: [2] } }, b.service)).toBe(false);
    expect(await encoderSurGpu([], b.sortie, options, b.service)).toBe(false);
    expect(appels).toBe(0);
  });
});

describe('publication sans écrasement', () => {
  it('préserve une destination existante même si le service répond correctement', async () => {
    const b = await banc((req, res) => { req.resume(); req.on('end', () => video(res)); });
    await writeFile(b.sortie, 'vidéo précédente');
    expect(await encoderSurGpu(b.fichiers, b.sortie, options, b.service)).toBe(false);
    expect(await readFile(b.sortie, 'utf8')).toBe('vidéo précédente');
    const essais = (await readdir(b.dir)).filter(f => f.startsWith('.encodage-'));
    expect(essais).toHaveLength(1);
    expect(await readFile(join(b.dir, essais[0]), 'utf8')).toBe('MP4-test');
  });
  it('ne publie qu’un résultat lorsque deux requêtes ciblent le même nom', async () => {
    const b = await banc((req, res) => { req.resume(); req.on('end', () => video(res)); });
    const resultats = await Promise.all([
      encoderSurGpu(b.fichiers, b.sortie, options, b.service),
      encoderSurGpu(b.fichiers, b.sortie, options, b.service),
    ]);
    expect(resultats.sort()).toEqual([false, true]);
    expect(await readFile(b.sortie, 'utf8')).toBe('MP4-test');
  });
});
