import { chmodSync, mkdtempSync, symlinkSync, writeFileSync } from 'node:fs';
import { createServer, type IncomingMessage, type ServerResponse, type Server } from 'node:http';
import { join } from 'node:path';
import { afterEach, describe, expect, it } from 'vitest';
import { UnixSyncWorker } from './unixWorker.js';
import type { SyncWorkerRequest } from './routes.js';

const JOB_ID = 'e3385ae2-371d-48e3-9ca5-3189736801e8';
const services: Server[] = [];
// Répertoires et reçus d'essai conservés ; aucune suppression d'un chemin inconnu.
async function service(handler: (req: IncomingMessage, res: ServerResponse) => void) {
  const root = mkdtempSync('/tmp/nx-sync-');
  chmodSync(root, 0o700);
  const socket = join(root, 'worker.sock');
  const server = createServer(handler);
  services.push(server);
  await new Promise<void>((resolve, reject) => { server.once('error', reject); server.listen(socket, resolve); });
  chmodSync(socket, 0o600);
  return { root, socket, worker: new UnixSyncWorker(socket) };
}

afterEach(async () => {
  for (const s of services.splice(0)) {
    s.closeAllConnections();
    await new Promise<void>((resolve) => s.close(() => resolve()));
  }
});

function body(): SyncWorkerRequest {
  return {
    schema: 'nexora.sync.worker-request.v1', jobId: JOB_ID, engine: 'musetalk',
    organisationId: 'local', createdBy: 'local',
    video: { takeId: 1, path: '/server/video.mp4', sha256: 'a'.repeat(64), bytes: 1234, durationSeconds: 4, fps: 25 },
    audio: { takeId: 2, path: '/server/audio.wav', sha256: 'b'.repeat(64), bytes: 100, durationSeconds: 4, sampleRate: 16000 },
    manifest: { schema: 'nexora.sync.job.v1', id: JOB_ID, engine: 'musetalk', videoTakeId: 1, audioTakeId: 2,
      inputs: { videoSha256: 'a'.repeat(64), audioSha256: 'b'.repeat(64) }, state: 'dispatching',
      researchOnly: true, productAvailable: false, humanReview: 'pending', quality: 'not_evaluated' },
  };
}

describe('transport Sync sur un vrai socket Unix privé', () => {
  it('transmet capacités, réservation et inspection sans modifier la requête', async () => {
    const seen: { method: string; path: string; body: string }[] = [];
    const { worker } = await service((req, res) => {
      let text = '';
      req.on('data', (b: Buffer) => { text += b.toString(); });
      req.on('end', () => {
        seen.push({ method: req.method!, path: req.url!, body: text });
        res.writeHead(req.method === 'POST' ? 202 : 200, { 'content-type': 'application/json' });
        res.end(JSON.stringify(req.url === '/capabilities' ? { ready: true } :
          req.method === 'POST' ? { accepted: true, jobId: JOB_ID } : { state: 'queued' }));
      });
    });
    const signal = new AbortController().signal;
    expect(await worker.capabilities(signal)).toEqual({ ready: true });
    expect(await worker.enqueue(body(), signal)).toEqual({ accepted: true, jobId: JOB_ID });
    expect(await worker.inspect(JOB_ID, signal)).toEqual({ state: 'queued' });
    expect(seen.map((r) => [r.method, r.path])).toEqual([['GET', '/capabilities'], ['POST', '/jobs'], ['GET', `/jobs/${JOB_ID}`]]);
    expect(JSON.parse(seen[1].body)).toEqual(body());
  });

  it('ne réessaie pas une réservation dont la connexion est interrompue', async () => {
    let calls = 0;
    const { worker } = await service((req) => { calls++; req.socket.destroy(); });
    await expect(worker.enqueue(body(), new AbortController().signal)).rejects.toThrow();
    expect(calls).toBe(1);
  });

  it('abandonne une réponse lente à la demande du contrôleur', async () => {
    const { worker } = await service(() => {});
    const controller = new AbortController();
    const pending = worker.inspect(JOB_ID, controller.signal);
    controller.abort();
    await expect(pending).rejects.toThrow();
  });

  it('refuse un flux incomplet et un acquittement HTTP 202 sur une lecture', async () => {
    const { worker } = await service((_req, res) => {
      res.writeHead(200, { 'content-type': 'application/json', 'content-length': 100 });
      res.write('{');
      res.flushHeaders();
      setImmediate(() => res.socket?.destroy());
    });
    await expect(worker.capabilities(new AbortController().signal)).rejects.toThrow();
    const second = await service((_req, res) => { res.writeHead(202); res.end('{}'); });
    await expect(second.worker.capabilities(new AbortController().signal)).rejects.toThrow('indisponible');
  });

  it('ne suit pas un alias de dossier vers le socket', async () => {
    const { root, socket } = await service((_req, res) => { res.end('{}'); });
    const aliases = mkdtempSync('/tmp/nx-sync-alias-');
    symlinkSync(root, join(aliases, 'linked'));
    const alias = new UnixSyncWorker(join(aliases, 'linked', 'worker.sock'));
    await expect(alias.capabilities(new AbortController().signal)).rejects.toThrow('non privé');
    expect(() => new UnixSyncWorker(socket.replace('/worker.sock', '/../worker.sock'))).toThrow('invalide');
  });

  it.each([
    [503, '{}', 'indisponible'],
    [200, 'not-json', 'JSON'],
    [200, 'x'.repeat(65537), 'trop grande'],
  ])('refuse statut ou contenu invalide (%i)', async (status, payload, message) => {
    const { worker } = await service((_req, res) => { res.writeHead(status); res.end(payload); });
    await expect(worker.capabilities(new AbortController().signal)).rejects.toThrow(message);
  });

  it('refuse un socket ou son dossier ouverts aux autres utilisateurs', async () => {
    const { worker, root, socket } = await service((_req, res) => { res.end('{}'); });
    chmodSync(socket, 0o666);
    await expect(worker.capabilities(new AbortController().signal)).rejects.toThrow('non privé');
    chmodSync(socket, 0o600); chmodSync(root, 0o755);
    await expect(worker.capabilities(new AbortController().signal)).rejects.toThrow('non privé');
  });

  it('rejette chemins, ID et charge trop grande avant envoi', async () => {
    expect(() => new UnixSyncWorker('relatif.sock')).toThrow();
    expect(() => new UnixSyncWorker('/' + 'x'.repeat(107))).toThrow();
    let calls = 0;
    const { worker, root } = await service((_req, res) => { calls++; res.end('{}'); });
    await expect(worker.inspect('../autre', new AbortController().signal)).rejects.toThrow('Identifiant');
    await expect(worker.enqueue({ ...body(), createdBy: 'x'.repeat(17000) }, new AbortController().signal)).rejects.toThrow('trop grande');
    writeFileSync(join(root, 'regular'), 'not a socket', { mode: 0o600 });
    await expect(new UnixSyncWorker(join(root, 'regular')).capabilities(new AbortController().signal)).rejects.toThrow('non privé');
    expect(calls).toBe(0);
  });
});
