import Database from 'better-sqlite3';

export const SYNC_ENGINES = ['musetalk', 'latentsync'] as const;
export type SyncEngine = typeof SYNC_ENGINES[number];
export type SyncJobState =
  | 'dispatching'
  | 'dispatch_unknown'
  | 'queued'
  | 'running'
  | 'completed_rnd'
  | 'failed';

export interface SyncJob {
  id: string;
  organisationId: string;
  utilisateurId: string;
  engine: SyncEngine;
  videoTakeId: number;
  audioTakeId: number;
  videoSha256: string;
  audioSha256: string;
  state: SyncJobState;
  idempotencySha256: string;
  workerJobId: string | null;
  errorCode: string | null;
  progress: number;
  resultSha256: string | null;
  resultBytes: number | null;
  avStatus: 'pass' | 'refused' | 'not_run' | null;
  createdAt: number;
  updatedAt: number;
}

export interface NewSyncJob extends Omit<SyncJob, 'state' | 'workerJobId' | 'errorCode' | 'progress' | 'resultSha256' | 'resultBytes' | 'avStatus'> {}

export type ReserveResult =
  | { kind: 'created'; job: SyncJob }
  | { kind: 'existing'; job: SyncJob }
  | { kind: 'full' };

type Row = {
  id: string;
  organisation_id: string;
  utilisateur_id: string;
  engine: string;
  video_take_id: number;
  audio_take_id: number;
  video_sha256: string;
  audio_sha256: string;
  state: string;
  idempotency_sha256: string;
  worker_job_id: string | null;
  error_code: string | null;
  progress: number;
  result_sha256: string | null;
  result_bytes: number | null;
  av_status: 'pass' | 'refused' | 'not_run' | null;
  created_at: number;
  updated_at: number;
};

const STATES = new Set<SyncJobState>([
  'dispatching', 'dispatch_unknown', 'queued', 'running', 'completed_rnd', 'failed',
]);
const TRANSITIONS: Record<SyncJobState, ReadonlySet<SyncJobState>> = {
  dispatching: new Set(['queued', 'running', 'completed_rnd', 'dispatch_unknown', 'failed']),
  dispatch_unknown: new Set(['queued', 'running', 'completed_rnd', 'failed']),
  queued: new Set(['running', 'completed_rnd', 'failed']),
  // Worker status can be polled repeatedly while progress advances.
  running: new Set(['running', 'completed_rnd', 'failed']),
  completed_rnd: new Set(),
  failed: new Set(),
};

function rowToJob(r: Row): SyncJob {
  if (!SYNC_ENGINES.includes(r.engine as SyncEngine) || !STATES.has(r.state as SyncJobState)) {
    throw new Error('Registre Sync invalide');
  }
  return {
    id: r.id,
    organisationId: r.organisation_id,
    utilisateurId: r.utilisateur_id,
    engine: r.engine as SyncEngine,
    videoTakeId: r.video_take_id,
    audioTakeId: r.audio_take_id,
    videoSha256: r.video_sha256,
    audioSha256: r.audio_sha256,
    state: r.state as SyncJobState,
    idempotencySha256: r.idempotency_sha256,
    workerJobId: r.worker_job_id,
    errorCode: r.error_code,
    progress: r.progress,
    resultSha256: r.result_sha256,
    resultBytes: r.result_bytes,
    avStatus: r.av_status,
    createdAt: r.created_at,
    updatedAt: r.updated_at,
  };
}

/** Petite table SQLite durable, scoppée par organisation et séparée des takes Comfy. */
export class SyncJobStore {
  private readonly db: Database.Database;

  constructor(path: string) {
    this.db = new Database(path);
    this.db.pragma('journal_mode = WAL');
    this.db.pragma('busy_timeout = 5000');
    this.db.exec(
      "CREATE TABLE IF NOT EXISTS nexora_sync_jobs (" +
      "id TEXT PRIMARY KEY, organisation_id TEXT NOT NULL, utilisateur_id TEXT NOT NULL, " +
      "engine TEXT NOT NULL CHECK (engine IN ('musetalk','latentsync')), " +
      "video_take_id INTEGER NOT NULL, audio_take_id INTEGER NOT NULL, " +
      "video_sha256 TEXT NOT NULL, audio_sha256 TEXT NOT NULL, " +
      "state TEXT NOT NULL CHECK (state IN ('dispatching','dispatch_unknown','queued','running','completed_rnd','failed')), " +
      "idempotency_sha256 TEXT NOT NULL, worker_job_id TEXT, error_code TEXT, " +
      "progress INTEGER NOT NULL DEFAULT 0 CHECK (progress BETWEEN 0 AND 100), " +
      "result_sha256 TEXT, result_bytes INTEGER, " +
      "av_status TEXT CHECK (av_status IS NULL OR av_status IN ('pass','refused','not_run')), " +
      "created_at INTEGER NOT NULL, updated_at INTEGER NOT NULL, " +
      "UNIQUE (organisation_id, utilisateur_id, idempotency_sha256)); " +
      "CREATE INDEX IF NOT EXISTS idx_nexora_sync_jobs_org_created " +
      "ON nexora_sync_jobs (organisation_id, created_at DESC); " +
      "CREATE INDEX IF NOT EXISTS idx_nexora_sync_jobs_engine_state " +
      "ON nexora_sync_jobs (engine, state);"
    );
  }

  reserve(input: NewSyncJob, maxConcurrent: number): ReserveResult {
    if (!Number.isSafeInteger(maxConcurrent) || maxConcurrent < 1) throw new Error('Capacité de concurrence invalide');
    const transaction = this.db.transaction((): ReserveResult => {
      const existing = this.db.prepare(
        'SELECT * FROM nexora_sync_jobs WHERE organisation_id=? AND utilisateur_id=? AND idempotency_sha256=?'
      ).get(input.organisationId, input.utilisateurId, input.idempotencySha256) as Row | undefined;
      if (existing) return { kind: 'existing', job: rowToJob(existing) };
      const count = this.db.prepare(
        "SELECT COUNT(*) AS n FROM nexora_sync_jobs WHERE state IN ('dispatching','dispatch_unknown','queued','running')"
      ).get() as { n: number };
      if (count.n >= maxConcurrent) return { kind: 'full' };
      this.db.prepare(
        'INSERT INTO nexora_sync_jobs (' +
        'id, organisation_id, utilisateur_id, engine, video_take_id, audio_take_id, ' +
        'video_sha256, audio_sha256, state, idempotency_sha256, created_at, updated_at' +
        ") VALUES (?,?,?,?,?,?,?,?, 'dispatching',?,?,?)"
      ).run(input.id, input.organisationId, input.utilisateurId, input.engine,
        input.videoTakeId, input.audioTakeId, input.videoSha256, input.audioSha256,
        input.idempotencySha256, input.createdAt, input.updatedAt);
      const created = this.db.prepare('SELECT * FROM nexora_sync_jobs WHERE id=?').get(input.id) as Row;
      return { kind: 'created', job: rowToJob(created) };
    });
    return transaction.immediate();
  }

  get(organisationId: string, id: string): SyncJob | undefined {
    const row = this.db.prepare('SELECT * FROM nexora_sync_jobs WHERE organisation_id=? AND id=?')
      .get(organisationId, id) as Row | undefined;
    return row ? rowToJob(row) : undefined;
  }

  list(organisationId: string, limit = 50): SyncJob[] {
    const born = Math.max(1, Math.min(100, Math.floor(limit)));
    return (this.db.prepare('SELECT * FROM nexora_sync_jobs WHERE organisation_id=? ORDER BY created_at DESC LIMIT ?')
      .all(organisationId, born) as Row[]).map(rowToJob);
  }

  transition(
    organisationId: string,
    id: string,
    next: SyncJobState,
    patch: Partial<Pick<SyncJob, 'workerJobId' | 'errorCode' | 'progress' | 'resultSha256' | 'resultBytes' | 'avStatus'>>,
    now = Date.now(),
  ): SyncJob | undefined {
    const transaction = this.db.transaction(() => {
      const row = this.db.prepare('SELECT * FROM nexora_sync_jobs WHERE organisation_id=? AND id=?')
        .get(organisationId, id) as Row | undefined;
      if (!row) return undefined;
      const current = rowToJob(row);
      if (!TRANSITIONS[current.state].has(next)) return current;
      const workerJobId = patch.workerJobId === undefined ? current.workerJobId : patch.workerJobId;
      const errorCode = patch.errorCode === undefined ? current.errorCode : patch.errorCode;
      const progress = patch.progress === undefined ? current.progress : Math.max(current.progress, patch.progress);
      const resultSha256 = patch.resultSha256 === undefined ? current.resultSha256 : patch.resultSha256;
      const resultBytes = patch.resultBytes === undefined ? current.resultBytes : patch.resultBytes;
      const avStatus = patch.avStatus === undefined ? current.avStatus : patch.avStatus;
      this.db.prepare(
        'UPDATE nexora_sync_jobs SET state=?, worker_job_id=?, error_code=?, progress=?, ' +
        'result_sha256=?, result_bytes=?, av_status=?, updated_at=? ' +
        'WHERE organisation_id=? AND id=? AND state=?'
      ).run(next, workerJobId, errorCode, progress, resultSha256, resultBytes, avStatus, now,
        organisationId, id, current.state);
      const updated = this.db.prepare('SELECT * FROM nexora_sync_jobs WHERE organisation_id=? AND id=?')
        .get(organisationId, id) as Row;
      return rowToJob(updated);
    });
    return transaction.immediate();
  }

  close(): void { this.db.close(); }
}

export function manifesteRAndD(job: SyncJob) {
  return {
    schema: 'nexora.sync.job.v1',
    id: job.id,
    engine: job.engine,
    videoTakeId: job.videoTakeId,
    audioTakeId: job.audioTakeId,
    inputs: { videoSha256: job.videoSha256, audioSha256: job.audioSha256 },
    state: job.state,
    researchOnly: true,
    productAvailable: false,
    humanReview: 'pending',
    quality: 'not_evaluated',
  } as const;
}
