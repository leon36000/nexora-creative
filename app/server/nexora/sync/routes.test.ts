import { createHash } from 'node:crypto';
import { mkdtempSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import Fastify from 'fastify';
import { afterEach, describe, expect, it } from 'vitest';
import { avecCompte } from '../compte.js';
import { enregistrerRoutesSync, type SyncWorker, type SyncTakeAsset, type SyncWorkerRequest } from './routes.js';
import { SyncJobStore } from './store.js';

const BASE = process.env.SYNC_TEST_ROOT || tmpdir();

function setup(workerOverride?: SyncWorker | null, now?: () => number) {
  const dir = mkdtempSync(join(BASE, 'sync-route-cpu-'));
  const videoPath = join(dir, 'video-fixture.mp4');
  const audioPath = join(dir, 'audio-fixture.wav');
  const videoBytes = Buffer.from('synthetic-video-fixture');
  const audioBytes = Buffer.from('synthetic-audio-fixture');
  writeFileSync(videoPath, videoBytes);
  writeFileSync(audioPath, audioBytes);
  const assets = new Map<string, SyncTakeAsset>([
    ['org-a:1', { id: 1, organisationId: 'org-a', status: 'done', kind: 'video', outputPath: videoPath,
      sha256: createHash('sha256').update(videoBytes).digest('hex'), bytes: videoBytes.length, durationSeconds: 9.04, fps: 25 }],
    ['org-a:2', { id: 2, organisationId: 'org-a', status: 'done', kind: 'audio', outputPath: audioPath,
      sha256: createHash('sha256').update(audioBytes).digest('hex'), bytes: audioBytes.length, durationSeconds: 9.04, sampleRate: 16000 }],
  ]);
  const store = new SyncJobStore(join(dir, 'sync.sqlite'));
  const calls = { resolve: 0, enqueue: [] as SyncWorkerRequest[], inspect: 0, aborted: 0 };
  const worker: SyncWorker = {
    async capabilities() {
      return {
        protocol: 'nexora.sync.worker.v1',
        workerId: 'cpu-fake',
        ready: true,
        maxConcurrent: 1,
        engines: {
          musetalk: { ready: true, maxDurationSeconds: 30, maxInputBytes: 1_000_000 },
          latentsync: { ready: true, maxDurationSeconds: 30, maxInputBytes: 1_000_000 },
        },
      };
    },
    async enqueue(request, signal) {
      calls.enqueue.push(request);
      if (signal.aborted) calls.aborted++;
      return { accepted: true, jobId: request.jobId };
    },
    async inspect() {
      calls.inspect++;
      return { state: 'queued' };
    },
  };
  const app = Fastify();
  app.addHook('onRequest', (req, _reply, done) => {
    const org = typeof req.headers['x-test-org'] === 'string' ? req.headers['x-test-org'] : 'org-a';
    const user = typeof req.headers['x-test-user'] === 'string' ? req.headers['x-test-user'] : 'user-a';
    avecCompte({ organisationId: org, utilisateurId: user, territoire: 'CA' }, done);
  });
  enregistrerRoutesSync(app, {
    store,
    resolveTake: (org, id) => { calls.resolve++; return assets.get(org + ':' + id); },
    worker: workerOverride === null ? undefined : workerOverride ?? worker,
    now,
    newId: (() => { let n = 0; return () => '00000000-0000-4000-8000-' + String(++n).padStart(12, '0'); })(),
  });
  return { app, dir, assets, store, worker, calls, videoPath, audioPath };
}

const active: Array<ReturnType<typeof setup>> = [];
afterEach(async () => {
  for (const x of active.splice(0)) {
    await x.app.close();
    x.store.close();
  }
});

const headers = (key = 'request-0000001', org = 'org-a', user = 'user-a') => ({
  'x-test-org': org,
  'x-test-user': user,
  'idempotency-key': key,
});

describe('contrat serveur Sync — worker CPU factice seulement', () => {
  it.each(['musetalk', 'latentsync'] as const)('refuse %s avant persistance quand aucun worker n’existe', async (engine) => {
    const x = setup(null);
    active.push(x);
    const response = await x.app.inject({
      method: 'POST', url: '/api/nexora/sync/travaux',
      headers: headers(),
      payload: { engine, videoTakeId: 1, audioTakeId: 2, langueClient: 'fr' },
    });
    expect(response.statusCode).toBe(503);
    expect(response.json().accepted).toBeUndefined();
    expect(x.store.list('org-a')).toEqual([]);
    expect(x.calls.enqueue).toHaveLength(0);
    expect(x.calls.resolve).toBe(0);
    const caps = await x.app.inject({ method: 'GET', url: '/api/nexora/sync/capacites' });
    expect(caps.json().engines[engine].available).toBe(false);
  });

  it('annonce uniquement les moteurs prêts, avec leurs limites issues du worker', async () => {
    const x = setup();
    active.push(x);
    const response = await x.app.inject({ method: 'GET', url: '/api/nexora/sync/capacites' });
    expect(response.statusCode).toBe(200);
    expect(response.json()).toMatchObject({
      engines: {
        musetalk: { available: true, workerId: 'cpu-fake', maxConcurrent: 1, maxDurationSeconds: 30 },
        latentsync: { available: true, workerId: 'cpu-fake', maxConcurrent: 1, maxInputBytes: 1_000_000 },
      },
      productAvailable: false,
      humanReview: 'pending',
      quality: 'not_evaluated',
    });
  });

  it('refuse une capacité absente ou non prête avant lecture de source et création', async () => {
    const x = setup();
    active.push(x);
    const worker: SyncWorker = {
      ...x.worker,
      async capabilities() {
        return { protocol: 'nexora.sync.worker.v1', workerId: 'cpu-fake', ready: true,
          maxConcurrent: 1, engines: { musetalk: { ready: true, maxDurationSeconds: 30, maxInputBytes: 1_000_000 },
            latentsync: { ready: false, maxDurationSeconds: 30, maxInputBytes: 1_000_000 } } };
      },
    };
    const app = Fastify();
    app.addHook('onRequest', (req, _reply, done) => avecCompte({
      organisationId: String(req.headers['x-test-org'] ?? 'org-a'),
      utilisateurId: String(req.headers['x-test-user'] ?? 'user-a'), territoire: 'CA',
    }, done));
    enregistrerRoutesSync(app, {
      store: x.store,
      resolveTake: (org, id) => { x.calls.resolve++; return x.assets.get(org + ':' + id); },
      worker,
    });
    const response = await app.inject({
      method: 'POST', url: '/api/nexora/sync/travaux', headers: headers(),
      payload: { engine: 'latentsync', videoTakeId: 1, audioTakeId: 2, langueClient: 'en' },
    });
    expect(response.statusCode).toBe(503);
    expect(response.json().error).toMatch(/No Sync worker/);
    expect(x.calls.resolve).toBe(0);
    expect(x.store.list('org-a')).toEqual([]);
    await app.close();
  });

  it('rejette les chemins envoyés par le client et ne les transmet jamais au worker', async () => {
    const x = setup();
    active.push(x);
    const response = await x.app.inject({
      method: 'POST', url: '/api/nexora/sync/travaux', headers: headers(),
      payload: { engine: 'musetalk', videoTakeId: 1, audioTakeId: 2, videoPath: '/etc/passwd' },
    });
    expect(response.statusCode).toBe(400);
    expect(x.calls.resolve).toBe(0);
    expect(x.calls.enqueue).toHaveLength(0);
    expect(x.store.list('org-a')).toEqual([]);
  });

  it('retourne le même 404 pour une take absente ou appartenant à une autre organisation', async () => {
    const x = setup();
    active.push(x);
    const missing = await x.app.inject({
      method: 'POST', url: '/api/nexora/sync/travaux', headers: headers(),
      payload: { engine: 'musetalk', videoTakeId: 999, audioTakeId: 2 },
    });
    const crossOrg = await x.app.inject({
      method: 'POST', url: '/api/nexora/sync/travaux', headers: headers('request-0000002', 'org-b'),
      payload: { engine: 'musetalk', videoTakeId: 1, audioTakeId: 2 },
    });
    expect(missing.statusCode).toBe(404);
    expect(crossOrg.statusCode).toBe(404);
    expect(missing.json().error).toBe(crossOrg.json().error);
    expect(x.calls.enqueue).toHaveLength(0);
    expect(x.store.list('org-a')).toEqual([]);
    expect(x.store.list('org-b')).toEqual([]);
  });

  it.each([
    ['unfinished', { status: 'rendering' as const, kind: 'video' as const }, 1],
    ['wrong media kind', { status: 'done' as const, kind: 'audio' as const }, 1],
  ])('refuse une take vidéo %s avant enqueue', async (_label, patch, id) => {
    const x = setup();
    active.push(x);
    x.assets.set('org-a:' + id, { ...x.assets.get('org-a:1')!, ...patch });
    const response = await x.app.inject({
      method: 'POST', url: '/api/nexora/sync/travaux', headers: headers(),
      payload: { engine: 'latentsync', videoTakeId: 1, audioTakeId: 2 },
    });
    expect(response.statusCode).toBe(409);
    expect(x.calls.enqueue).toHaveLength(0);
    expect(x.store.list('org-a')).toEqual([]);
  });

  it.each(['musetalk', 'latentsync'] as const)('accepte %s seulement après l’ack et garde un manifeste R&D', async (engine) => {
    const x = setup();
    active.push(x);
    const response = await x.app.inject({
      method: 'POST', url: '/api/nexora/sync/travaux', headers: headers(),
      payload: { engine, videoTakeId: 1, audioTakeId: 2, langueClient: 'fr' },
    });
    expect(response.statusCode).toBe(202);
    expect(response.json().accepted).toBe(true);
    expect(response.json().job).toMatchObject({
      engine, state: 'queued', productAvailable: false, quality: 'not_evaluated',
      humanReview: 'pending', manifest: { researchOnly: true, productAvailable: false, quality: 'not_evaluated' },
    });
    expect(x.calls.enqueue).toHaveLength(1);
    expect(x.calls.enqueue[0]).toMatchObject({
      schema: 'nexora.sync.worker-request.v1', engine,
      video: { takeId: 1, path: x.videoPath },
      audio: { takeId: 2, path: x.audioPath },
      manifest: { researchOnly: true, productAvailable: false, humanReview: 'pending' },
    });
    const json = JSON.stringify(response.json());
    expect(json).not.toContain(x.videoPath);
    expect(json).not.toContain(x.audioPath);
    expect(json).not.toMatch(/voiceModel|approved|productAvailable\":true/);
  });

  it('déduplique par clé et refuse une clé réutilisée avec des entrées différentes', async () => {
    const x = setup();
    active.push(x);
    x.assets.set('org-a:3', { ...x.assets.get('org-a:1')!, id: 3 });
    const body = { engine: 'musetalk', videoTakeId: 1, audioTakeId: 2 };
    const first = await x.app.inject({ method: 'POST', url: '/api/nexora/sync/travaux', headers: headers('request-0000012'), payload: body });
    const repeat = await x.app.inject({ method: 'POST', url: '/api/nexora/sync/travaux', headers: headers('request-0000012'), payload: body });
    const conflict = await x.app.inject({ method: 'POST', url: '/api/nexora/sync/travaux', headers: headers('request-0000012'), payload: { ...body, videoTakeId: 3 } });
    expect(first.statusCode).toBe(202);
    expect(repeat.statusCode).toBe(200);
    expect(repeat.json()).toMatchObject({ accepted: true, reused: true, job: { id: first.json().job.id } });
    expect(conflict.statusCode).toBe(409);
    expect(x.calls.enqueue).toHaveLength(1);
  });

  it('ne dépasse pas la capacité globale du worker même avec un autre couple de takes', async () => {
    const x = setup();
    active.push(x);
    x.assets.set('org-a:3', { ...x.assets.get('org-a:1')!, id: 3 });
    x.assets.set('org-a:4', { ...x.assets.get('org-a:2')!, id: 4 });
    const first = await x.app.inject({ method: 'POST', url: '/api/nexora/sync/travaux', headers: headers('request-0000013'), payload: { engine: 'musetalk', videoTakeId: 1, audioTakeId: 2 } });
    const second = await x.app.inject({ method: 'POST', url: '/api/nexora/sync/travaux', headers: headers('request-0000014'), payload: { engine: 'latentsync', videoTakeId: 3, audioTakeId: 4 } });
    expect(first.statusCode).toBe(202);
    expect(second.statusCode).toBe(429);
    expect(x.calls.enqueue).toHaveLength(1);
  });

  it('ne revendique pas l’acceptation si le worker refuse explicitement', async () => {
    const x = setup();
    active.push(x);
    const refusing: SyncWorker = { ...x.worker, async enqueue() { return { accepted: false, errorCode: 'input_rejected' }; } };
    const app = Fastify();
    app.addHook('onRequest', (req, _reply, done) => avecCompte({
      organisationId: String(req.headers['x-test-org'] ?? 'org-a'),
      utilisateurId: String(req.headers['x-test-user'] ?? 'user-a'), territoire: 'CA',
    }, done));
    enregistrerRoutesSync(app, { store: x.store, resolveTake: (org, id) => x.assets.get(org + ':' + id), worker: refusing });
    const response = await app.inject({ method: 'POST', url: '/api/nexora/sync/travaux', headers: headers(), payload: { engine: 'musetalk', videoTakeId: 1, audioTakeId: 2 } });
    expect(response.statusCode).toBe(503);
    expect(response.json()).toMatchObject({ accepted: false, code: 'sync_enqueue_rejected' });
    expect(x.store.list('org-a')[0].state).toBe('failed');
    await app.close();
  });

  it('garde une acceptation indéterminée comme telle après expiration de l’ack', async () => {
    const x = setup();
    active.push(x);
    let aborted = false;
    const silent: SyncWorker = { ...x.worker, async enqueue(_request, signal) {
      return await new Promise((_resolve, reject) => signal.addEventListener('abort', () => { aborted = true; reject(new Error('aborted')); }, { once: true }));
    } };
    const app = Fastify();
    app.addHook('onRequest', (req, _reply, done) => avecCompte({
      organisationId: String(req.headers['x-test-org'] ?? 'org-a'),
      utilisateurId: String(req.headers['x-test-user'] ?? 'user-a'), territoire: 'CA',
    }, done));
    enregistrerRoutesSync(app, { store: x.store, resolveTake: (org, id) => x.assets.get(org + ':' + id), worker: silent, timeouts: { enqueueMs: 5 } });
    const response = await app.inject({ method: 'POST', url: '/api/nexora/sync/travaux', headers: headers(), payload: { engine: 'musetalk', videoTakeId: 1, audioTakeId: 2 } });
    expect(response.statusCode).toBe(504);
    expect(response.json()).toMatchObject({ accepted: false, code: 'sync_acceptance_unknown' });
    expect(aborted).toBe(true);
    expect(x.store.list('org-a')[0].state).toBe('dispatch_unknown');
    await app.close();
  });

  it('ne transforme pas dispatching en échec sur un poll not_found concurrent à enqueue', async () => {
    const x = setup();
    active.push(x);
    let confirmer!: (v: { accepted: true; jobId: string }) => void;
    let entrer!: () => void;
    const dansEnqueue = new Promise<void>((resolve) => { entrer = resolve; });
    const ack = new Promise<{ accepted: true; jobId: string }>((resolve) => { confirmer = resolve; });
    x.worker.enqueue = async (_request) => { entrer(); return await ack; };
    x.worker.inspect = async () => ({ state: 'not_found' });
    const body = { engine: 'musetalk', videoTakeId: 1, audioTakeId: 2 };
    const firstPending = x.app.inject({ method: 'POST', url: '/api/nexora/sync/travaux', headers: headers('request-race-0001'), payload: body });
    await dansEnqueue;
    const duplicate = await x.app.inject({ method: 'POST', url: '/api/nexora/sync/travaux', headers: headers('request-race-0001'), payload: body });
    expect(duplicate.statusCode).toBe(504);
    const id = duplicate.json().jobId;
    const earlyStatus = await x.app.inject({ method: 'GET', url: '/api/nexora/sync/travaux/' + id });
    expect(earlyStatus.json().job.state).toBe('dispatching');
    confirmer({ accepted: true, jobId: id });
    const accepted = await firstPending;
    expect(accepted.statusCode).toBe(202);
    expect(accepted.json()).toMatchObject({ accepted: true, job: { id, state: 'queued' } });
  });

  it.each(['running', 'completed'] as const)('garde l’ACK positif quand un poll concurrent a déjà vu %s', async (state) => {
    const x = setup();
    active.push(x);
    let confirmer!: (v: { accepted: true; jobId: string }) => void;
    let entrer!: () => void;
    const dansEnqueue = new Promise<void>((resolve) => { entrer = resolve; });
    const ack = new Promise<{ accepted: true; jobId: string }>((resolve) => { confirmer = resolve; });
    x.worker.enqueue = async (_request) => { entrer(); return await ack; };
    x.worker.inspect = async (jobId) => state === 'running'
      ? { state: 'running', progress: 48 }
      : { state: 'completed', result: {
          schema: 'nexora.sync.worker-result.v1', jobId, engine: 'musetalk',
          inputs: { videoSha256: x.assets.get('org-a:1')!.sha256, audioSha256: x.assets.get('org-a:2')!.sha256 },
          outputSha256: 'b'.repeat(64), outputBytes: 456, avStatus: 'pass', researchOnly: true, productAvailable: false,
        } };
    const body = { engine: 'musetalk', videoTakeId: 1, audioTakeId: 2 };
    const firstPending = x.app.inject({ method: 'POST', url: '/api/nexora/sync/travaux', headers: headers('request-race-0002'), payload: body });
    await dansEnqueue;
    const duplicate = await x.app.inject({ method: 'POST', url: '/api/nexora/sync/travaux', headers: headers('request-race-0002'), payload: body });
    const id = duplicate.json().jobId;
    const earlyStatus = await x.app.inject({ method: 'GET', url: '/api/nexora/sync/travaux/' + id });
    expect(earlyStatus.json().job.state).toBe(state === 'running' ? 'running' : 'completed_rnd');
    confirmer({ accepted: true, jobId: id });
    const accepted = await firstPending;
    expect(accepted.statusCode).toBe(202);
    expect(accepted.json()).toMatchObject({ accepted: true, job: { id, state: state === 'running' ? 'running' : 'completed_rnd' } });
  });

  it('garde dispatch_unknown sur not_found et efface l’erreur quand le worker confirme queued', async () => {
    let clock = 1000;
    const x = setup(undefined, () => clock);
    active.push(x);
    x.worker.enqueue = async () => { throw Object.assign(new Error('transport reset'), { code: 'ECONNRESET' }); };
    let observation: 'not_found' | 'queued' = 'not_found';
    x.worker.inspect = async () => ({ state: observation });
    const submitted = await x.app.inject({
      method: 'POST', url: '/api/nexora/sync/travaux', headers: headers('request-race-0003'),
      payload: { engine: 'musetalk', videoTakeId: 1, audioTakeId: 2 },
    });
    const id = submitted.json().jobId;
    expect(submitted.statusCode).toBe(502);
    clock = 2000;
    const notFound = await x.app.inject({ method: 'GET', url: '/api/nexora/sync/travaux/' + id });
    expect(notFound.json().job).toMatchObject({ state: 'dispatch_unknown', errorCode: 'acceptance_unconfirmed', updatedAt: 1000 });
    observation = 'queued';
    clock = 3000;
    const confirmed = await x.app.inject({ method: 'GET', url: '/api/nexora/sync/travaux/' + id });
    expect(confirmed.json().job).toMatchObject({ state: 'queued', errorCode: null, updatedAt: 3000 });
  });

  it('conserve une acceptation inconnue après erreur réseau puis réconcilie le job', async () => {
    const x = setup();
    active.push(x);
    const uncertain: SyncWorker = {
      ...x.worker,
      async enqueue() { throw Object.assign(new Error('transport reset'), { code: 'ECONNRESET' }); },
      async inspect(jobId) {
        return { state: 'queued' };
      },
    };
    const app = Fastify();
    app.addHook('onRequest', (req, _reply, done) => avecCompte({
      organisationId: String(req.headers['x-test-org'] ?? 'org-a'),
      utilisateurId: String(req.headers['x-test-user'] ?? 'user-a'), territoire: 'CA',
    }, done));
    enregistrerRoutesSync(app, { store: x.store, resolveTake: (org, id) => x.assets.get(org + ':' + id), worker: uncertain });
    const submitted = await app.inject({
      method: 'POST', url: '/api/nexora/sync/travaux', headers: headers(),
      payload: { engine: 'musetalk', videoTakeId: 1, audioTakeId: 2 },
    });
    expect(submitted.statusCode).toBe(502);
    expect(submitted.json()).toMatchObject({ accepted: false, code: 'sync_acceptance_unknown' });
    expect(JSON.stringify(submitted.json())).not.toContain('ECONNRESET');
    expect(x.store.list('org-a')[0].state).toBe('dispatch_unknown');
    const reconciled = await app.inject({ method: 'GET', url: '/api/nexora/sync/travaux/' + submitted.json().jobId });
    expect(reconciled.statusCode).toBe(200);
    expect(reconciled.json()).toMatchObject({ accepted: true, job: { state: 'queued' } });
    await app.close();
  });

  it('actualise le progrès d’un travail déjà en cours à chaque lecture', async () => {
    const x = setup();
    active.push(x);
    let progress = 21;
    x.worker.inspect = async () => ({ state: 'running', progress });
    const submitted = await x.app.inject({
      method: 'POST', url: '/api/nexora/sync/travaux', headers: headers(),
      payload: { engine: 'latentsync', videoTakeId: 1, audioTakeId: 2 },
    });
    const url = '/api/nexora/sync/travaux/' + submitted.json().job.id;
    const first = await x.app.inject({ method: 'GET', url });
    progress = 74;
    const second = await x.app.inject({ method: 'GET', url });
    expect(first.json().job).toMatchObject({ state: 'running', progress: 21 });
    expect(second.json().job).toMatchObject({ state: 'running', progress: 74 });
  });

  it('récupère un résultat R&D vérifié dans le manifeste sans exposer le fichier', async () => {
    const x = setup();
    active.push(x);
    const submitted = await x.app.inject({ method: 'POST', url: '/api/nexora/sync/travaux', headers: headers(), payload: { engine: 'latentsync', videoTakeId: 1, audioTakeId: 2 } });
    const id = submitted.json().job.id;
    const inspect: SyncWorker = { ...x.worker, async inspect(jobId) {
      return { state: 'completed', result: {
        schema: 'nexora.sync.worker-result.v1', jobId, engine: 'latentsync',
        inputs: { videoSha256: x.assets.get('org-a:1')!.sha256, audioSha256: x.assets.get('org-a:2')!.sha256 },
        outputSha256: 'a'.repeat(64), outputBytes: 1234, avStatus: 'pass',
        researchOnly: true, productAvailable: false,
      } };
    } };
    const app = Fastify();
    app.addHook('onRequest', (req, _reply, done) => avecCompte({
      organisationId: String(req.headers['x-test-org'] ?? 'org-a'),
      utilisateurId: String(req.headers['x-test-user'] ?? 'user-a'), territoire: 'CA',
    }, done));
    enregistrerRoutesSync(app, { store: x.store, resolveTake: (org, takeId) => x.assets.get(org + ':' + takeId), worker: inspect });
    const response = await app.inject({ method: 'GET', url: '/api/nexora/sync/travaux/' + id });
    expect(response.statusCode).toBe(200);
    expect(response.json()).toMatchObject({
      accepted: true,
      job: { state: 'completed_rnd', result: { sha256: 'a'.repeat(64), bytes: 1234, avStatus: 'pass' },
        productAvailable: false, quality: 'not_evaluated', humanReview: 'pending' },
    });
    expect(JSON.stringify(response.json())).not.toContain(x.videoPath);
    await app.close();
  });

  it('scoppe la lecture et conserve le job après réouverture SQLite', async () => {
    const x = setup();
    active.push(x);
    const response = await x.app.inject({
      method: 'POST', url: '/api/nexora/sync/travaux', headers: headers(),
      payload: { engine: 'musetalk', videoTakeId: 1, audioTakeId: 2 },
    });
    const id = response.json().job.id;
    x.store.close();
    const reopened = new SyncJobStore(join(x.dir, 'sync.sqlite'));
    const found = reopened.get('org-a', id);
    expect(found?.state).toBe('queued');
    expect(reopened.get('org-b', id)).toBeUndefined();
    expect(JSON.stringify(found)).not.toContain(x.videoPath);
    reopened.close();
    // afterEach close is idempotency-sensitive; replace the closed store with a fresh connection.
    const replacement = new SyncJobStore(join(x.dir, 'sync.sqlite'));
    Object.assign(x, { store: replacement });
  });
});

describe('ACK Sync indéterminé — régressions root', () => {

  it.each([
    null,
    {},
    { accepted: true },
    { accepted: true, jobId: 'different-job' },
    { accepted: 'true', jobId: '00000000-0000-4000-8000-000000000001' },
    { accepted: false, errorCode: 42 },
    { accepted: false, jobId: 'different-job' },
  ])('conserve la capacité pour un ACK malformé ou incohérent : %j', async (badAck) => {
    const x = setup();
    active.push(x);
    x.worker.enqueue = async (request) => {
      x.calls.enqueue.push(request);
      return badAck as never;
    };
    const payload = { engine: 'musetalk', videoTakeId: 1, audioTakeId: 2 };
    const first = await x.app.inject({ method: 'POST', url: '/api/nexora/sync/travaux', headers: headers(), payload });
    expect(first.statusCode).toBe(502);
    expect(first.json().code).toBe('sync_acceptance_unknown');
    expect(x.store.list('org-a')[0].state).toBe('dispatch_unknown');
    const repeat = await x.app.inject({ method: 'POST', url: '/api/nexora/sync/travaux', headers: headers(), payload });
    expect(repeat.statusCode).toBe(504);
    const second = await x.app.inject({ method: 'POST', url: '/api/nexora/sync/travaux', headers: headers('another-request-0001'), payload });
    expect(second.statusCode).toBe(429);
    expect(x.calls.enqueue).toHaveLength(1);
  });

});

describe('observations Sync et identité du média — régressions root', () => {
  it.each(['video', 'audio'] as const)('refuse la même clé si le contenu %s change pour le même ID', async (kind) => {
    const x = setup(); active.push(x);
    const payload = { engine: 'musetalk', videoTakeId: 1, audioTakeId: 2 };
    const first = await x.app.inject({ method: 'POST', url: '/api/nexora/sync/travaux', headers: headers(), payload });
    expect(first.statusCode).toBe(202);
    const id = kind === 'video' ? 1 : 2;
    const asset = x.assets.get('org-a:' + id)!;
    const bytes = Buffer.from('replacement synthetic ' + kind);
    writeFileSync(asset.outputPath, bytes);
    x.assets.set('org-a:' + id, { ...asset, bytes: bytes.length, sha256: createHash('sha256').update(bytes).digest('hex') });
    const repeat = await x.app.inject({ method: 'POST', url: '/api/nexora/sync/travaux', headers: headers(), payload });
    expect(repeat.statusCode).toBe(409);
    expect(repeat.json().code).toBe('sync_idempotency_conflict');
    expect(x.calls.enqueue).toHaveLength(1);
  });

  it('ne fait pas reculer la progression après deux observations concurrentes arrivant en désordre', async () => {
    const x = setup(); active.push(x);
    const first = await x.app.inject({ method: 'POST', url: '/api/nexora/sync/travaux', headers: headers(), payload: { engine: 'musetalk', videoTakeId: 1, audioTakeId: 2 } });
    const id = first.json().job.id;
    let release!: () => void;
    let entered!: () => void;
    const waiting = new Promise<void>(resolve => { release = resolve; });
    const started = new Promise<void>(resolve => { entered = resolve; });
    let calls = 0;
    x.worker.inspect = async () => {
      if (++calls === 1) { entered(); await waiting; return { state: 'running', progress: 30 }; }
      return { state: 'running', progress: 90 };
    };
    const url = '/api/nexora/sync/travaux/' + id;
    const slow = x.app.inject({ method: 'GET', url, headers: headers() }).then(response => response);
    await started;
    const fast = await x.app.inject({ method: 'GET', url, headers: headers() });
    expect(fast.json().job.progress).toBe(90);
    release();
    const late = await slow;
    expect(late.json().job.progress).toBe(90);
    expect(x.store.get('org-a', id)?.progress).toBe(90);
  });
});
