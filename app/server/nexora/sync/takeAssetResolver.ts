import { createHash } from 'node:crypto';
import { constants as fsConstants } from 'node:fs';
import { lstat, open, realpath } from 'node:fs/promises';
import { isAbsolute, resolve } from 'node:path';
import { executerBorne } from '../executionBornee.js';
import type { SyncTakeAsset } from './routes.js';

export interface TakeForSync {
  id: number;
  organisation_id: string;
  kind: string;
  status: string;
  output_path: string | null;
}

type TakeSnapshot = {
  id: number;
  organisation_id: string;
  kind: 'video' | 'audio';
  status: 'done';
  output_path: string;
};

export interface SyncTakeProbe {
  format?: { duration?: string | number };
  streams?: Array<{
    codec_type?: string;
    duration?: string | number;
    avg_frame_rate?: string;
    r_frame_rate?: string;
    sample_rate?: string | number;
  }>;
}

export interface SyncTakeResolverLimits {
  maxInputBytes: number;
  maxDurationSeconds: number;
  probeTimeoutMs: number;
}

export const SYNC_WORKER_MAX_INPUT_BYTES = 128 * 1024 * 1024;
export const SYNC_WORKER_MAX_DURATION_SECONDS = 30;
const MAX_PROBE_TIMEOUT_MS = 15_000;
const SHA256 = /^[a-f0-9]{64}$/;
const FFPROBE_FORMATS = 'mov,matroska,avi,wav,mp3,flac,ogg,aac,mpegts';

const DEFAULT_LIMITS: SyncTakeResolverLimits = {
  maxInputBytes: SYNC_WORKER_MAX_INPUT_BYTES,
  maxDurationSeconds: SYNC_WORKER_MAX_DURATION_SECONDS,
  probeTimeoutMs: 10_000,
};

type StatEntree = {
  dev: bigint; ino: bigint; size: bigint; mode: number | bigint; mtimeNs: bigint; ctimeNs: bigint;
  isFile(): boolean; isSymbolicLink(): boolean;
};

type Signature = {
  dev: bigint; ino: bigint; size: bigint; mode: bigint; mtimeNs: bigint; ctimeNs: bigint;
};

function signature(s: StatEntree): Signature {
  return { dev: s.dev, ino: s.ino, size: s.size, mode: BigInt(s.mode), mtimeNs: s.mtimeNs, ctimeNs: s.ctimeNs };
}

function memeSignature(a: Signature, b: Signature): boolean {
  return a.dev === b.dev && a.ino === b.ino && a.size === b.size && a.mode === b.mode
    && a.mtimeNs === b.mtimeNs && a.ctimeNs === b.ctimeNs;
}

function nombre(v: string | number | undefined): number | undefined {
  if (typeof v === 'number') return Number.isFinite(v) && v > 0 ? v : undefined;
  if (typeof v !== 'string' || !/^(?:\d+(?:\.\d+)?|\.\d+)(?:e[+-]?\d+)?$/i.test(v.trim())) return undefined;
  const n = Number(v);
  return Number.isFinite(n) && n > 0 ? n : undefined;
}

function cadence(v: string | undefined): number | undefined {
  if (!v) return undefined;
  const m = /^(\d+(?:\.\d+)?|\.\d+)\/(\d+(?:\.\d+)?|\.\d+)$/.exec(v.trim());
  if (m) {
    const n = Number(m[1]) / Number(m[2]);
    return Number.isFinite(n) && n > 0 && n <= 240 ? n : undefined;
  }
  const n = nombre(v);
  return n !== undefined && n <= 240 ? n : undefined;
}

function mesurer(info: unknown, kind: 'video' | 'audio', maxDuration: number): Pick<SyncTakeAsset, 'durationSeconds' | 'fps' | 'sampleRate'> | undefined {
  if (!info || typeof info !== 'object' || Array.isArray(info)) return undefined;
  const p = info as SyncTakeProbe;
  if (!Array.isArray(p.streams)) return undefined;
  const stream = p.streams.find((s) => s && s.codec_type === kind);
  if (!stream) return undefined;
  const durationSeconds = nombre(p.format?.duration) ?? nombre(stream.duration);
  if (durationSeconds === undefined || durationSeconds > maxDuration) return undefined;
  if (kind === 'video') {
    const fps = cadence(stream.avg_frame_rate) ?? cadence(stream.r_frame_rate);
    return fps === undefined ? undefined : { durationSeconds, fps };
  }
  const sampleRate = nombre(stream.sample_rate);
  return sampleRate === undefined || !Number.isSafeInteger(sampleRate) || sampleRate > 384_000
    ? undefined : { durationSeconds, sampleRate };
}

async function probeFfprobe(ffprobe: string, descriptorPath: string, timeoutMs: number): Promise<unknown> {
  // Ne pas transmettre au sondeur l'environnement du serveur, qui peut contenir des accès.
  const stdout = await executerBorne('/usr/bin/env', ['-i', 'PATH=/usr/bin:/bin', ffprobe,
    '-v', 'error', '-protocol_whitelist', 'file,pipe', '-format_whitelist', FFPROBE_FORMATS,
    '-show_entries', 'format=duration:stream=codec_type,duration,avg_frame_rate,r_frame_rate,sample_rate',
    '-of', 'json', descriptorPath,
  ], timeoutMs);
  return JSON.parse(stdout) as unknown;
}

function limitesValides(l: SyncTakeResolverLimits): boolean {
  return Number.isSafeInteger(l.maxInputBytes) && l.maxInputBytes > 0 && l.maxInputBytes <= SYNC_WORKER_MAX_INPUT_BYTES
    && Number.isFinite(l.maxDurationSeconds) && l.maxDurationSeconds > 0 && l.maxDurationSeconds <= SYNC_WORKER_MAX_DURATION_SECONDS
    && Number.isSafeInteger(l.probeTimeoutMs) && l.probeTimeoutMs > 0 && l.probeTimeoutMs <= MAX_PROBE_TIMEOUT_MS;
}

function memeTake(a: TakeForSync | undefined, b: TakeSnapshot): boolean {
  return !!a && a.id === b.id && a.organisation_id === b.organisation_id && a.kind === b.kind
    && a.status === b.status && a.output_path === b.output_path;
}

/**
 * Résout une prise issue du registre serveur. Le chemin vient exclusivement de la ligne DB;
 * le contenu est haché en flux et ffprobe lit le même inode via /proc/<pid>/fd/<fd>.
 */
export function creerResolveurSyncTake(options: {
  getTake: (id: number) => TakeForSync | undefined;
  ffprobeBin: string;
  limits?: Partial<SyncTakeResolverLimits>;
  probe?: (ffprobeBin: string, descriptorPath: string, timeoutMs: number) => Promise<unknown>;
}): (organisationId: string, id: number) => Promise<SyncTakeAsset | undefined> {
  const limits = { ...DEFAULT_LIMITS, ...options.limits };
  if (!isAbsolute(options.ffprobeBin) || options.ffprobeBin.includes('\0') || !limitesValides(limits)) {
    throw new Error('Configuration du résolveur Sync invalide.');
  }
  const probe = options.probe ?? probeFfprobe;

  return async (organisationId, id) => {
    if (!organisationId || !Number.isSafeInteger(id) || id < 1) return undefined;
    const found = options.getTake(id);
    const foundPath = found?.output_path;
    if (!found || found.id !== id || found.organisation_id !== organisationId || found.status !== 'done'
      || (found.kind !== 'video' && found.kind !== 'audio') || !foundPath || !isAbsolute(foundPath)
      || foundPath.includes('\0')) return undefined;
    // Capture the database identity before the first asynchronous filesystem operation.
    const take: TakeSnapshot = { id: found.id, organisation_id: found.organisation_id,
      kind: found.kind, status: 'done', output_path: foundPath };

    const filePath = resolve(take.output_path);
    let handle: Awaited<ReturnType<typeof open>> | undefined;
    try {
      // Reject symlinks in every path component, then protect the final open against replacement.
      if (await realpath(filePath) !== filePath) return undefined;
      const pathBefore = await lstat(filePath, { bigint: true });
      if (!pathBefore.isFile() || pathBefore.isSymbolicLink() || pathBefore.size <= 0n
        || pathBefore.size > BigInt(limits.maxInputBytes)) return undefined;

      handle = await open(filePath, fsConstants.O_RDONLY | fsConstants.O_NOFOLLOW | fsConstants.O_NONBLOCK);
      const fdBefore = await handle.stat({ bigint: true });
      const original = signature(pathBefore);
      if (!fdBefore.isFile() || !memeSignature(original, signature(fdBefore))) return undefined;

      const hash = createHash('sha256');
      let bytes = 0;
      const stream = handle.createReadStream({ autoClose: false, start: 0 });
      for await (const part of stream) {
        const chunk = Buffer.isBuffer(part) ? part : Buffer.from(part);
        bytes += chunk.length;
        if (bytes > limits.maxInputBytes) return undefined;
        hash.update(chunk);
      }
      if (bytes !== Number(original.size)) return undefined;

      const fdAfterRead = signature(await handle.stat({ bigint: true }));
      const pathAfterRead = signature(await lstat(filePath, { bigint: true }));
      if (!memeSignature(original, fdAfterRead) || !memeSignature(original, pathAfterRead)
        || await realpath(filePath) !== filePath) return undefined;

      // ffprobe uses the already-open descriptor, so replacing the pathname cannot switch its input.
      if (process.platform !== 'linux') return undefined;
      const descriptorPath = `/proc/${process.pid}/fd/${handle.fd}`;
      const media = mesurer(await probe(options.ffprobeBin, descriptorPath, limits.probeTimeoutMs), take.kind, limits.maxDurationSeconds);
      if (!media) return undefined;

      const fdAfterProbe = signature(await handle.stat({ bigint: true }));
      const pathAfterProbe = signature(await lstat(filePath, { bigint: true }));
      if (!memeSignature(original, fdAfterProbe) || !memeSignature(original, pathAfterProbe)
        || await realpath(filePath) !== filePath || !memeTake(options.getTake(id), take)) return undefined;

      const sha256 = hash.digest('hex');
      if (!SHA256.test(sha256)) return undefined;
      return {
        id: take.id, organisationId: take.organisation_id, status: take.status, kind: take.kind,
        outputPath: filePath, sha256, bytes, ...media,
      };
    } catch {
      return undefined;
    } finally {
      await handle?.close().catch(() => undefined);
    }
  };
}
