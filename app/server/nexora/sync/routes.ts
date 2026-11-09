import { createHash, randomUUID } from 'node:crypto';
import { lstatSync } from 'node:fs';
import { isAbsolute } from 'node:path';
import type { FastifyInstance, FastifyReply, FastifyRequest } from 'fastify';
import { compteCourant } from '../compte.js';
import { lireLangueClient, messageErreurRendu, type LangueClient } from '../creationLanguage.js';
import {
  manifesteRAndD,
  SYNC_ENGINES,
  SyncJobStore,
  type SyncEngine,
  type SyncJob,
} from './store.js';

const PREFIX = '/api/nexora/sync';
const MAX_BODY = 16 * 1024;
const CAPABILITY_TIMEOUT_MS = 750;
const ENQUEUE_TIMEOUT_MS = 2_000;
const STATUS_TIMEOUT_MS = 750;
const SHA256 = /^[a-f0-9]{64}$/;
const ID = /^[0-9a-f-]{36}$/i;
const IDEMPOTENCY = /^[A-Za-z0-9._:-]{8,128}$/;

export interface SyncTakeAsset {
  id: number;
  organisationId: string;
  status: string;
  kind: string;
  outputPath: string;
  sha256: string;
  bytes: number;
  durationSeconds: number;
  fps?: number;
  sampleRate?: number;
}

export interface SyncEngineCapability {
  ready: boolean;
  maxDurationSeconds: number;
  maxInputBytes: number;
}

export interface SyncWorkerCapabilities {
  protocol: 'nexora.sync.worker.v1';
  workerId: string;
  ready: boolean;
  maxConcurrent: number;
  engines: Partial<Record<SyncEngine, SyncEngineCapability>>;
}

export interface SyncWorkerInput {
  takeId: number;
  path: string;
  sha256: string;
  bytes: number;
  durationSeconds: number;
  fps?: number;
  sampleRate?: number;
}

export interface SyncWorkerRequest {
  schema: 'nexora.sync.worker-request.v1';
  jobId: string;
  engine: SyncEngine;
  organisationId: string;
  createdBy: string;
  video: SyncWorkerInput;
  audio: SyncWorkerInput;
  manifest: ReturnType<typeof manifesteRAndD>;
}

export interface SyncWorkerResultManifest {
  schema: 'nexora.sync.worker-result.v1';
  jobId: string;
  engine: SyncEngine;
  inputs: { videoSha256: string; audioSha256: string };
  outputSha256: string;
  outputBytes: number;
  avStatus: 'pass' | 'refused' | 'not_run';
  researchOnly: true;
  productAvailable: false;
}

export type SyncWorkerObservation =
  | { state: 'not_found' }
  | { state: 'queued' }
  | { state: 'running'; progress: number }
  | { state: 'dispatch_unknown'; errorCode: 'engine_failed' | 'worker_timeout' }
  | { state: 'completed'; result: SyncWorkerResultManifest }
  | { state: 'failed'; errorCode?: string };

export interface SyncWorker {
  capabilities(signal: AbortSignal): Promise<SyncWorkerCapabilities>;
  /** Doit seulement réserver/enfiler et être idempotent pour jobId; ne lance pas l'inférence dans la requête HTTP. */
  enqueue(request: SyncWorkerRequest, signal: AbortSignal): Promise<{ accepted: true; jobId: string } | { accepted: false; errorCode?: string }>;
  inspect(jobId: string, signal: AbortSignal): Promise<SyncWorkerObservation>;
}

export interface SyncRouteDeps {
  store: SyncJobStore;
  /** Résout un ID take côté serveur, dans l'organisation courante; ne jamais accepter de chemin depuis le client. */
  resolveTake: (organisationId: string, id: number) => Promise<SyncTakeAsset | undefined> | SyncTakeAsset | undefined;
  worker?: SyncWorker;
  /** Valeurs internes pour accélérer les tests; elles ne sont jamais lues depuis la requête. */
  timeouts?: { capabilitiesMs?: number; enqueueMs?: number; statusMs?: number };
  now?: () => number;
  newId?: () => string;
}

class DelaiDepasse extends Error {}

function object(v: unknown): v is Record<string, unknown> {
  return v !== null && typeof v === 'object' && !Array.isArray(v);
}

async function avecDelai<T>(f: (signal: AbortSignal) => Promise<T>, ms: number): Promise<T> {
  const controller = new AbortController();
  let timer: ReturnType<typeof setTimeout> | undefined;
  const expirera = new Promise<never>((_resolve, reject) => {
    timer = setTimeout(() => {
      controller.abort();
      reject(new DelaiDepasse());
    }, ms);
  });
  try {
    return await Promise.race([f(controller.signal), expirera]);
  } finally {
    if (timer !== undefined) clearTimeout(timer);
  }
}

function texteErreur(langue: LangueClient | undefined, fr: string, en: string): string {
  return messageErreurRendu(langue, fr, en);
}

function erreur(reply: FastifyReply, status: number, code: string, langue: LangueClient | undefined, fr: string, en: string, extra?: Record<string, unknown>) {
  return reply.code(status).send({ code, error: texteErreur(langue, fr, en), ...extra });
}

function qui() {
  const c = compteCourant();
  return { organisationId: c?.organisationId ?? 'local', utilisateurId: c?.utilisateurId ?? 'local' };
}

interface DemandeSync {
  engine: SyncEngine;
  videoTakeId: number;
  audioTakeId: number;
  langueClient?: LangueClient;
}

function demandeValide(b: unknown): b is DemandeSync {
  if (!object(b)) return false;
  return !Object.keys(b).some((k) => !['engine', 'videoTakeId', 'audioTakeId', 'langueClient'].includes(k)) &&
    (b.engine === 'musetalk' || b.engine === 'latentsync') &&
    Number.isSafeInteger(b.videoTakeId) && Number(b.videoTakeId) >= 1 &&
    Number.isSafeInteger(b.audioTakeId) && Number(b.audioTakeId) >= 1 &&
    (b.langueClient === undefined || b.langueClient === 'fr' || b.langueClient === 'en');
}

function capabilityValide(c: unknown): c is SyncWorkerCapabilities {
  if (!object(c) || c.protocol !== 'nexora.sync.worker.v1' || typeof c.workerId !== 'string' ||
      !/^[A-Za-z0-9._-]{1,64}$/.test(c.workerId) || typeof c.ready !== 'boolean' ||
      !Number.isSafeInteger(c.maxConcurrent) || Number(c.maxConcurrent) < 1 || !object(c.engines)) return false;
  for (const engine of SYNC_ENGINES) {
    const v = c.engines[engine];
    if (v === undefined) continue;
    if (!object(v) || typeof v.ready !== 'boolean' ||
        !Number.isFinite(v.maxDurationSeconds) || Number(v.maxDurationSeconds) <= 0 ||
        !Number.isSafeInteger(v.maxInputBytes) || Number(v.maxInputBytes) <= 0) return false;
  }
  return true;
}

async function lireCapacites(worker: SyncWorker | undefined, timeoutMs: number) {
  if (!worker) return { workerState: 'absent' as const, workerId: null, maxConcurrent: 0, engines: {} as Partial<Record<SyncEngine, SyncEngineCapability>> };
  try {
    const raw = await avecDelai((signal) => worker.capabilities(signal), timeoutMs);
    if (!capabilityValide(raw)) return { workerState: 'unknown' as const, workerId: null, maxConcurrent: 0, engines: {} as Partial<Record<SyncEngine, SyncEngineCapability>> };
    return {
      workerState: raw.ready ? 'ready' as const : 'unavailable' as const,
      workerId: raw.workerId,
      maxConcurrent: raw.maxConcurrent,
      engines: raw.ready ? raw.engines : {},
    };
  } catch {
    return { workerState: 'unknown' as const, workerId: null, maxConcurrent: 0, engines: {} as Partial<Record<SyncEngine, SyncEngineCapability>> };
  }
}

function validAsset(asset: SyncTakeAsset | undefined, expected: 'video' | 'audio', org: string, cap: SyncEngineCapability): asset is SyncTakeAsset {
  if (asset?.organisationId !== org || asset.status !== 'done' || asset.kind !== expected) return false;
  if (!Number.isSafeInteger(asset.id) || asset.id < 1 || !isAbsolute(asset.outputPath) ||
      asset.outputPath.includes('\0') || !SHA256.test(asset.sha256) ||
      !Number.isSafeInteger(asset.bytes) || asset.bytes <= 0 || asset.bytes > cap.maxInputBytes ||
      !Number.isFinite(asset.durationSeconds) || asset.durationSeconds <= 0 ||
      asset.durationSeconds > cap.maxDurationSeconds) return false;
  if (expected === 'video' && (!Number.isFinite(asset.fps) || Number(asset.fps) <= 0)) return false;
  if (expected === 'audio' && (!Number.isSafeInteger(asset.sampleRate) || Number(asset.sampleRate) <= 0)) return false;
  try {
    const st = lstatSync(asset.outputPath);
    if (!st.isFile() || st.isSymbolicLink() || st.size !== asset.bytes) return false;
  } catch {
    return false;
  }
  return true;
}

function inputOf(t: SyncTakeAsset): SyncWorkerInput {
  return {
    takeId: t.id,
    path: t.outputPath,
    sha256: t.sha256,
    bytes: t.bytes,
    durationSeconds: t.durationSeconds,
    ...(t.fps === undefined ? {} : { fps: t.fps }),
    ...(t.sampleRate === undefined ? {} : { sampleRate: t.sampleRate }),
  };
}

function vue(job: SyncJob) {
  return {
    id: job.id,
    engine: job.engine,
    state: job.state,
    progress: job.progress,
    createdAt: job.createdAt,
    updatedAt: job.updatedAt,
    errorCode: job.errorCode,
    result: job.resultSha256 ? {
      sha256: job.resultSha256,
      bytes: job.resultBytes,
      avStatus: job.avStatus,
    } : null,
    manifest: manifesteRAndD(job),
    productAvailable: false,
    quality: 'not_evaluated',
    humanReview: 'pending',
  };
}

function resultValide(r: unknown, job: SyncJob): r is SyncWorkerResultManifest {
  if (!object(r) || r.schema !== 'nexora.sync.worker-result.v1' ||
      r.jobId !== job.id || r.engine !== job.engine ||
      r.researchOnly !== true || r.productAvailable !== false ||
      !object(r.inputs) || r.inputs.videoSha256 !== job.videoSha256 ||
      r.inputs.audioSha256 !== job.audioSha256 ||
      typeof r.outputSha256 !== 'string' || !SHA256.test(r.outputSha256) ||
      !Number.isSafeInteger(r.outputBytes) || Number(r.outputBytes) <= 0 ||
      !['pass', 'refused', 'not_run'].includes(String(r.avStatus))) return false;
  return true;
}

function errorCode(v: unknown): string {
  return typeof v === 'string' && ['input_rejected', 'engine_failed', 'worker_timeout'].includes(v) ? v : 'worker_failed';
}

function conclureTravail(store: SyncJobStore, job: SyncJob, result: unknown, now: () => number): SyncJob {
  if (!resultValide(result, job)) {
    return store.transition(job.organisationId, job.id, 'failed', { workerJobId: job.id, errorCode: 'invalid_result_manifest' }, now()) ?? job;
  }
  return store.transition(job.organisationId, job.id, 'completed_rnd', {
    workerJobId: job.id,
    progress: 100,
    errorCode: null,
    resultSha256: result.outputSha256,
    resultBytes: result.outputBytes,
    avStatus: result.avStatus,
  }, now()) ?? job;
}

function reutiliserTravail(
  reply: FastifyReply, old: SyncJob,
  input: { engine: SyncEngine; video: SyncTakeAsset; audio: SyncTakeAsset },
  langue: LangueClient | undefined,
) {
  const { engine, video, audio } = input;
  if (old.engine !== engine || old.videoTakeId !== video.id || old.audioTakeId !== audio.id ||
      old.videoSha256 !== video.sha256 || old.audioSha256 !== audio.sha256) {
    return erreur(reply, 409, 'sync_idempotency_conflict', langue,
      'Cette clé de requête a déjà servi à une autre demande.',
      'This idempotency key was already used for a different request.');
  }
  if (old.state === 'dispatch_unknown' || old.state === 'dispatching') {
    return erreur(reply, 504, 'sync_acceptance_unknown', langue,
      'La mise en file n’est pas confirmée. Consulte le travail avant de réessayer.',
      'Queue acceptance is unconfirmed. Check the job before retrying.',
      { jobId: old.id, accepted: false });
  }
  if (old.state === 'failed') {
    return reply.code(200).send({ accepted: false, reused: true, job: vue(old) });
  }
  return reply.code(200).send({ accepted: true, reused: true, job: vue(old) });
}

async function actualiser(worker: SyncWorker | undefined, store: SyncJobStore, job: SyncJob, timeoutMs: number, now = Date.now) {
  if (!worker || !['dispatching', 'dispatch_unknown', 'queued', 'running'].includes(job.state)) return job;
  try {
    const observation = await avecDelai((signal) => worker.inspect(job.id, signal), timeoutMs);
    if (!object(observation) || typeof observation.state !== 'string') return job;
    if (observation.state === 'not_found') {
      // L’ACK a pu expirer ou l’enqueue peut encore être en transit; une lecture
      // momentanée absente ne prouve pas que le worker a refusé le job.
      return job;
    }
    if (observation.state === 'queued') {
      return store.transition(job.organisationId, job.id, 'queued', { workerJobId: job.id, errorCode: null }, now()) ?? job;
    }
    if (observation.state === 'running') {
      if (!Number.isInteger(observation.progress) || observation.progress < 0 || observation.progress > 100) return job;
      return store.transition(job.organisationId, job.id, 'running', { workerJobId: job.id, progress: observation.progress, errorCode: null }, now()) ?? job;
    }
    if (observation.state === 'dispatch_unknown') {
      if (observation.errorCode !== 'engine_failed' && observation.errorCode !== 'worker_timeout') return job;
      return store.transition(job.organisationId, job.id, 'dispatch_unknown', {
        workerJobId: job.id, errorCode: 'execution_unverified',
      }, now()) ?? job;
    }
    if (observation.state === 'failed') {
      return store.transition(job.organisationId, job.id, 'failed', { workerJobId: job.id, errorCode: errorCode(observation.errorCode) }, now()) ?? job;
    }
    if (observation.state === 'completed') {
      return conclureTravail(store, job, observation.result, now);
    }
  } catch {
    // L’état durable précédent reste disponible si le worker ne répond pas.
  }
  return job;
}

export function enregistrerRoutesSync(app: FastifyInstance, deps: SyncRouteDeps): void {
  const maintenant = deps.now ?? Date.now;
  const nouveauId = deps.newId ?? randomUUID;
  const timeoutCap = deps.timeouts?.capabilitiesMs ?? CAPABILITY_TIMEOUT_MS;
  const timeoutEnqueue = deps.timeouts?.enqueueMs ?? ENQUEUE_TIMEOUT_MS;
  const timeoutStatus = deps.timeouts?.statusMs ?? STATUS_TIMEOUT_MS;

  app.get(PREFIX + '/capacites', async () => {
    const caps = await lireCapacites(deps.worker, timeoutCap);
    const engines = Object.fromEntries(SYNC_ENGINES.map((engine) => {
      const e = caps.engines[engine];
      const available = caps.workerState === 'ready' && e?.ready === true;
      return [engine, available ? {
        available: true,
        workerId: caps.workerId,
        protocol: 'nexora.sync.worker.v1',
        maxConcurrent: caps.maxConcurrent,
        maxDurationSeconds: e.maxDurationSeconds,
        maxInputBytes: e.maxInputBytes,
        execution: 'research_only',
      } : { available: false, workerState: caps.workerState }];
    }));
    return { engines, productAvailable: false, humanReview: 'pending', quality: 'not_evaluated' };
  });

  app.post(PREFIX + '/travaux', { bodyLimit: MAX_BODY }, async (req: FastifyRequest, reply: FastifyReply) => {
    const b = req.body;
    const langue = object(b) ? lireLangueClient(b.langueClient) : undefined;
    if (!demandeValide(b)) {
      return erreur(reply, 400, 'sync_invalid_request', langue,
        'La demande de synchronisation est invalide.',
        'The sync request is invalid.');
    }
    const engine = b.engine as SyncEngine;
    const idempotency = req.headers['idempotency-key'];
    if (typeof idempotency !== 'string' || !IDEMPOTENCY.test(idempotency)) {
      return erreur(reply, 400, 'sync_idempotency_required', langue,
        'Une clé de requête valide est requise pour éviter un doublon.',
        'A valid idempotency key is required to prevent duplicate jobs.');
    }
    const { organisationId, utilisateurId } = qui();
    const caps = await lireCapacites(deps.worker, timeoutCap);
    const cap = caps.engines[engine];
    if (!deps.worker || caps.workerState !== 'ready' || cap?.ready !== true) {
      return erreur(reply, 503, 'sync_worker_unavailable', langue,
        'Aucun worker Sync prêt pour ce moteur.',
        'No Sync worker is ready for this engine.');
    }

    let video: SyncTakeAsset | undefined;
    let audio: SyncTakeAsset | undefined;
    try {
      [video, audio] = await Promise.all([
        deps.resolveTake(organisationId, Number(b.videoTakeId)),
        deps.resolveTake(organisationId, Number(b.audioTakeId)),
      ]);
    } catch {
      return erreur(reply, 503, 'sync_source_lookup_unavailable', langue,
        'Les prises ne peuvent pas être vérifiées maintenant.',
        'The takes cannot be verified right now.');
    }
    if (!video || !audio || video.organisationId !== organisationId || audio.organisationId !== organisationId) {
      return erreur(reply, 404, 'sync_take_not_found', langue,
        'Une des prises est introuvable.',
        'One of the takes could not be found.');
    }
    if (!validAsset(video, 'video', organisationId, cap) || !validAsset(audio, 'audio', organisationId, cap)) {
      return erreur(reply, 409, 'sync_take_not_ready', langue,
        'Choisis une vidéo et un audio terminés et disponibles.',
        'Choose a completed and available video and audio take.');
    }
    const keySha = createHash('sha256').update(organisationId + '\0' + utilisateurId + '\0' + idempotency).digest('hex');
    const now = maintenant();
    const reservation = deps.store.reserve({
      id: nouveauId(),
      organisationId,
      utilisateurId,
      engine,
      videoTakeId: video.id,
      audioTakeId: audio.id,
      videoSha256: video.sha256,
      audioSha256: audio.sha256,
      idempotencySha256: keySha,
      createdAt: now,
      updatedAt: now,
    }, caps.maxConcurrent);
    if (reservation.kind === 'full') {
      return erreur(reply, 429, 'sync_worker_busy', langue,
        'Le worker Sync est occupé. Réessaie plus tard.',
        'The Sync worker is busy. Try again later.');
    }
    if (reservation.kind === 'existing') {
      return reutiliserTravail(reply, reservation.job, { engine, video, audio }, langue);
    }

    const job = reservation.job;
    const request: SyncWorkerRequest = {
      schema: 'nexora.sync.worker-request.v1',
      jobId: job.id,
      engine,
      organisationId,
      createdBy: utilisateurId,
      video: inputOf(video),
      audio: inputOf(audio),
      manifest: manifesteRAndD(job),
    };
    let ack: Awaited<ReturnType<SyncWorker['enqueue']>>;
    try {
      ack = await avecDelai((signal) => deps.worker!.enqueue(request, signal), timeoutEnqueue);
    } catch (e) {
      const unknown = e instanceof DelaiDepasse;
      // Une erreur de transport peut survenir après l’envoi de la requête. Seul un refus
      // explicite du worker permet d’affirmer que la file n’a pas accepté le travail.
      deps.store.transition(organisationId, job.id, 'dispatch_unknown', {
        errorCode: 'acceptance_unconfirmed',
      }, maintenant());
      return erreur(reply, unknown ? 504 : 502, 'sync_acceptance_unknown', langue,
        'La mise en file n’est pas confirmée. Consulte le travail avant de réessayer.',
        'Queue acceptance is unconfirmed. Check the job before retrying.',
        { jobId: job.id, accepted: false });
    }
    const refusExplicite = object(ack) && ack.accepted === false &&
      (ack.errorCode === undefined || typeof ack.errorCode === 'string') &&
      (!('jobId' in ack) || ack.jobId === job.id);
    if (refusExplicite) {
      deps.store.transition(organisationId, job.id, 'failed', { errorCode: 'enqueue_rejected' }, maintenant());
      return erreur(reply, 503, 'sync_enqueue_rejected', langue,
        'Le worker Sync n’a pas confirmé le travail.',
        'The Sync worker did not confirm the job.',
        { jobId: job.id, accepted: false });
    }
    if (!object(ack) || ack.accepted !== true || ack.jobId !== job.id) {
      // Une réponse incohérente ne prouve aucun refus : conserver la réservation.
      deps.store.transition(organisationId, job.id, 'dispatch_unknown', {
        errorCode: 'acceptance_unconfirmed',
      }, maintenant());
      return erreur(reply, 502, 'sync_acceptance_unknown', langue,
        'La mise en file n’est pas confirmée. Consulte le travail avant de réessayer.',
        'Queue acceptance is unconfirmed. Check the job before retrying.',
        { jobId: job.id, accepted: false });
    }
    const queued = deps.store.transition(organisationId, job.id, 'queued', { workerJobId: job.id, errorCode: null }, maintenant());
    if (queued?.workerJobId !== job.id || !['queued', 'running', 'completed_rnd'].includes(queued.state)) {
      return erreur(reply, 503, 'sync_persistence_unconfirmed', langue,
        'Le travail est enregistré, mais son acceptation n’est pas confirmée.',
        'The job is recorded, but acceptance is not confirmed.',
        { jobId: job.id, accepted: false });
    }
    return reply.code(202).send({ accepted: true, reused: false, job: vue(queued) });
  });

  app.get(PREFIX + '/travaux/:id', async (req: FastifyRequest, reply: FastifyReply) => {
    const id = (req.params as { id?: string }).id ?? '';
    const query = req.query as { langueClient?: unknown };
    const langue = lireLangueClient(query.langueClient);
    if (!ID.test(id)) return erreur(reply, 404, 'sync_job_not_found', langue, 'Travail introuvable.', 'Job not found.');
    const { organisationId } = qui();
    const stored = deps.store.get(organisationId, id);
    if (!stored) return erreur(reply, 404, 'sync_job_not_found', langue, 'Travail introuvable.', 'Job not found.');
    const refreshed = await actualiser(deps.worker, deps.store, stored, timeoutStatus, maintenant);
    const accepted = ['queued', 'running', 'completed_rnd'].includes(refreshed.state);
    return reply.code(200).send({ accepted, job: vue(refreshed) });
  });
}
