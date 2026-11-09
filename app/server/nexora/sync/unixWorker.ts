import { lstatSync } from 'node:fs';
import { request } from 'node:http';
import { dirname, isAbsolute } from 'node:path';
import type {
  SyncWorker, SyncWorkerCapabilities, SyncWorkerObservation, SyncWorkerRequest,
} from './routes.js';

const MAX_REQUEST_BYTES = 16 * 1024;
const MAX_RESPONSE_BYTES = 64 * 1024;
const JOB_ID = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;

/** Transport R&D local seulement. Aucune nouvelle tentative d'envoi implicite. */
export class UnixSyncWorker implements SyncWorker {
  constructor(private readonly socketPath: string) {
    if (!isAbsolute(socketPath) || socketPath.includes('\0') || Buffer.byteLength(socketPath) > 107) {
      throw new Error('Chemin de socket Sync invalide');
    }
  }

  private verifierSocket() {
    const uid = process.getuid?.();
    if (uid === undefined) throw new Error('Socket Sync non pris en charge');
    const parent = lstatSync(dirname(this.socketPath));
    const socket = lstatSync(this.socketPath);
    if (!parent.isDirectory() || parent.isSymbolicLink() || parent.uid !== uid || (parent.mode & 0o077) !== 0 ||
        !socket.isSocket() || socket.uid !== uid || (socket.mode & 0o077) !== 0) {
      throw new Error('Socket Sync non privé');
    }
  }

  private async appeler<T>(method: 'GET' | 'POST', path: string, signal: AbortSignal, body?: SyncWorkerRequest): Promise<T> {
    signal.throwIfAborted();
    this.verifierSocket();
    const payload = body === undefined ? undefined : Buffer.from(JSON.stringify(body));
    if (payload && payload.length > MAX_REQUEST_BYTES) throw new Error('Requête Sync trop grande');
    return new Promise<T>((resolve, reject) => {
      const req = request({
        socketPath: this.socketPath, method, path, signal, agent: false,
        headers: { accept: 'application/json', ...(payload ? {
          'content-type': 'application/json', 'content-length': payload.length,
        } : {}) },
      }, (res) => {
        let bytes = 0;
        const chunks: Buffer[] = [];
        res.on('error', reject);
        res.on('aborted', () => reject(new Error('Réponse Sync interrompue')));
        res.on('data', (chunk: Buffer) => {
          bytes += chunk.length;
          if (bytes > MAX_RESPONSE_BYTES) {
            const error = new Error('Réponse Sync trop grande');
            reject(error);
            req.destroy(error);
            res.destroy();
          } else chunks.push(chunk);
        });
        res.on('end', () => {
          if (res.statusCode !== 200 && res.statusCode !== 202) {
            reject(new Error(`Worker Sync indisponible (${res.statusCode ?? 0})`));
            return;
          }
          try {
            resolve(JSON.parse(Buffer.concat(chunks).toString('utf8')) as T);
          } catch {
            reject(new Error('Réponse JSON Sync invalide'));
          }
        });
      });
      req.on('error', reject);
      req.end(payload);
    });
  }

  capabilities(signal: AbortSignal): Promise<SyncWorkerCapabilities> {
    return this.appeler('GET', '/capabilities', signal);
  }

  enqueue(body: SyncWorkerRequest, signal: AbortSignal): ReturnType<SyncWorker['enqueue']> {
    if (!JOB_ID.test(body.jobId)) return Promise.reject(new Error('Identifiant Sync invalide'));
    return this.appeler('POST', '/jobs', signal, body);
  }

  inspect(jobId: string, signal: AbortSignal): Promise<SyncWorkerObservation> {
    if (!JOB_ID.test(jobId)) return Promise.reject(new Error('Identifiant Sync invalide'));
    return this.appeler('GET', `/jobs/${jobId}`, signal);
  }
}
