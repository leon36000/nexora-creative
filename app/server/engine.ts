/**
 * Job engine: every render OpenField runs goes through the Comfy SDK
 * (@comfyorg/sdk, Comfy API v2). The same code targets a local ComfyUI
 * behind comfy-api-proxy (the default) or Comfy Cloud / a Comfy API
 * deployment; only COMFY_BASE_URL and COMFY_API_KEY change.
 *
 * Emits on `engine`:
 *  'progress' { jobId, value, step, steps }
 *  'preview'  { jobId, data: Buffer }
 *  'status'   { jobId, status, queuePosition }
 *  'finished' { jobId }   (terminal state reached; call result())
 */
import { Comfy, type Job } from '@comfyorg/sdk';
import { ComfyLow } from '@comfyorg/sdk/low';
import { EventEmitter } from 'events';
import { mkdir, readFile, writeFile } from 'fs/promises';
import { existsSync, mkdirSync, readFileSync, writeFileSync } from 'fs';
import { join } from 'path';
import { config } from './config.js';
import { statutTerminalConfirme } from './nexora/reconciliationArrets.js';

// 'expired': the proxy lost the job (e.g. ComfyUI restarted under it).
const TERMINAL = new Set(['succeeded', 'failed', 'canceled', 'cancelled', 'expired']);
const INPUT_CACHE = join(config.dataDir, 'inputs');
const ASSET_TOKEN = /^asset:([0-9a-f-]{36})$/i;

export const engine = new EventEmitter();

/**
 * Nexora : parc de moteurs GPU. Le moteur « principal » est celui de COMFY_URL / COMFY_BASE_URL ; d'autres s'ajoutent
 * par NEXORA_MOTEURS_GPU (JSON : [{ id, nom, comfyUrl, baseUrl, recettes }]), chacun derrière son propre
 * comfy-api-proxy. Une recette (« h3-fast », « h3-max »…) ne part que vers un moteur qui la déclare ; parmi eux, le
 * moins chargé. Le lien tâche → moteur est gardé sur disque pour retrouver les tâches après un redémarrage.
 */
export interface MoteurGpu { id: string; nom: string; comfyUrl: string; baseUrl: string; recettes: string[];
  /** Secondes mesurées d'une tâche par recette (ex. { "objet-apercu": 126 }) : le choix du moteur minimise l'heure de fin estimée. */
  secondes?: Record<string, number>;
  /** Serveur de détourage vidéo (outils/detourage/serveur.py) de cette machine ; les recettes « detourage-rapide » et « detourage-pro » le désignent. */
  detourageUrl?: string;
  /** Jeton partagé du serveur de détourage (NEXORA_DETOURAGE_JETON pour le principal) ; jamais journalisé ni renvoyé. */
  detourageJeton?: string;
  /** Clé d'un moteur cloud (jamais journalisée). */ cle?: string }

/** Secondes par recette : un objet JSON (texte ou déjà lu) de nombres positifs ; le reste est ignoré. */
export function lireSecondes(brut: unknown): Record<string, number> | undefined {
  try {
    const o = typeof brut === 'string' ? (brut.trim() ? JSON.parse(brut) : null) : brut;
    if (!o || typeof o !== 'object' || Array.isArray(o)) return undefined;
    const r = Object.fromEntries(Object.entries(o as Record<string, unknown>).filter(([, v]) => Number.isFinite(Number(v)) && Number(v) > 0).map(([k, v]) => [k, Number(v)]));
    return Object.keys(r).length ? r : undefined;
  } catch {
    return undefined;
  }
}

function lireMoteurs(): MoteurGpu[] {
  const principal: MoteurGpu = {
    id: 'principal',
    nom: process.env.NEXORA_MOTEUR_NOM?.trim() || 'GPU principal',
    comfyUrl: config.comfyUrl,
    baseUrl: config.comfyBaseUrl,
    recettes: (process.env.NEXORA_MOTEUR_RECETTES || '*').split(',').map((r) => r.trim()).filter(Boolean),
    secondes: lireSecondes(process.env.NEXORA_MOTEUR_SECONDES),
    ...(process.env.NEXORA_DETOURAGE_URL?.trim() ? { detourageUrl: process.env.NEXORA_DETOURAGE_URL.trim().replace(/\/+$/, '') } : {}),
    ...(process.env.NEXORA_DETOURAGE_JETON?.trim() ? { detourageJeton: process.env.NEXORA_DETOURAGE_JETON.trim() } : {}),
  };
  let autres: MoteurGpu[] = [];
  try {
    const brut = JSON.parse(process.env.NEXORA_MOTEURS_GPU || '[]');
    if (Array.isArray(brut)) {
      autres = brut
        .filter((m) => m && typeof m.id === 'string' && m.id !== 'principal' && typeof m.comfyUrl === 'string' && typeof m.baseUrl === 'string')
        .map((m) => ({
          id: m.id, nom: String(m.nom ?? m.id), comfyUrl: m.comfyUrl.replace(/\/+$/, ''), baseUrl: m.baseUrl.replace(/\/+$/, ''),
          recettes: Array.isArray(m.recettes) ? m.recettes.map(String) : ['*'],
          ...(lireSecondes(m.secondes) ? { secondes: lireSecondes(m.secondes) } : {}),
          ...(typeof m.detourageUrl === 'string' && /^https?:\/\//.test(m.detourageUrl) ? { detourageUrl: m.detourageUrl.replace(/\/+$/, '') } : {}),
          ...(typeof m.detourageJeton === 'string' && m.detourageJeton.trim() ? { detourageJeton: m.detourageJeton.trim() } : {}),
        }));
    }
  } catch (e) {
    console.error('[nexora] NEXORA_MOTEURS_GPU illisible :', e instanceof Error ? e.message : e);
  }
  return [principal, ...autres];
}

export const moteurs: MoteurGpu[] = lireMoteurs();
const moteursEnv: MoteurGpu[] = moteurs.map((m) => ({ ...m }));

/**
 * Nexora : applique la liste de moteurs de l'administration du site (lue toutes les minutes). Le moteur « principal » de
 * l'environnement reste si le site ne définit pas le même identifiant. Un moteur dont l'adresse ou la clé change est
 * reconstruit ; les tâches en cours sur un moteur retiré retombent sur le premier moteur de la liste.
 */
export function appliquerMoteurs(depuisSite: MoteurGpu[]): void {
  const prochain = [...depuisSite, ...moteursEnv.filter((m) => !depuisSite.some((x) => x.id === m.id))];
  if (!prochain.some((m) => m.id === 'principal')) prochain.unshift(moteursEnv[0]);
  // « principal » reste en tête : c'est le moteur par défaut des recettes non déclarées.
  prochain.sort((a, b) => (a.id === 'principal' ? -1 : b.id === 'principal' ? 1 : 0));
  for (const m of prochain) {
    const avant = moteurs.find((x) => x.id === m.id);
    if (avant && (avant.baseUrl !== m.baseUrl || avant.cle !== m.cle)) { clients.delete(m.id); lecturesJobs.delete(m.id); }
  }
  for (const id of [...clients.keys()]) if (!prochain.some((m) => m.id === id)) clients.delete(id);
  for (const id of [...lecturesJobs.keys()]) if (!prochain.some((m) => m.id === id)) lecturesJobs.delete(id);
  moteurs.splice(0, moteurs.length, ...prochain);
}
/** Les moteurs tels que l'environnement les définit (retour à la configuration du poste). */
export const retablirMoteursEnv = () => appliquerMoteurs([]);
const moteurParId = (id: string | undefined) => moteurs.find((m) => m.id === id) ?? moteurs[0];

const clients = new Map<string, Comfy>();
const lecturesJobs = new Map<string, ComfyLow>();
function sdk(moteur = 'principal'): Comfy {
  let c = clients.get(moteur);
  if (!c) {
    // Le SDK lit son adresse dans l'environnement au moment de la construction.
    process.env.COMFY_BASE_URL = moteurParId(moteur).baseUrl;
    c = new Comfy({ apiKey: moteurParId(moteur).cle || config.comfyApiKey || undefined, clientInfo: 'openfield' });
    clients.set(moteur, c);
  }
  return c;
}

/** Tâche → moteur, persistant (les ids de tâche sont des UUID, uniques sur tout le parc). */
const FICHIER_JOBS = join(config.dataDir, 'moteurs-jobs.json');
const jobMoteur = new Map<string, string>(
  (() => {
    try {
      return Object.entries(JSON.parse(readFileSync(FICHIER_JOBS, 'utf8')) as Record<string, string>);
    } catch {
      return [];
    }
  })(),
);
function noterMoteur(jobId: string, moteur: string) {
  jobMoteur.set(jobId, moteur);
  // Borne : on ne garde que les 2 000 dernières tâches.
  while (jobMoteur.size > 2000) jobMoteur.delete(jobMoteur.keys().next().value!);
  try {
    mkdirSync(config.dataDir, { recursive: true });
    writeFileSync(FICHIER_JOBS, JSON.stringify(Object.fromEntries(jobMoteur)));
  } catch { /* le lien reste en mémoire */ }
}
export const moteurDuJob = (jobId: string) => moteurParId(jobMoteur.get(jobId));

/** Tâches en cours par moteur, pour répartir la charge. */
const enCours = new Map<string, Set<string>>();

/**
 * Moteurs capables d'une recette, le plus rapide à finir d'abord : (tâches en cours + 1) × secondes de la recette sur ce
 * moteur. Sans `secondes` déclarées, c'est le moins chargé (à égalité, l'ordre du parc : le principal d'abord). Ainsi un
 * brouillon 3D reste sur la GB10 (38 s) tant que sa file ne dépasse pas deux tâches, puis déborde sur les Turing (126 s).
 */
export function moteursPour(recette?: string, charge: (id: string) => number = (id) => enCours.get(id)?.size ?? 0, enLigne: (id: string) => boolean = (id) => enLigneConnu.get(id) !== false): MoteurGpu[] {
  const declares = moteurs.filter((m) => m.recettes.includes('*') || (recette !== undefined && m.recettes.includes(recette)));
  // Un moteur vu hors ligne (état relevé toutes les 20 s) ne reçoit rien tant qu'un autre capable répond : bascule.
  const capables = declares.some((m) => enLigne(m.id)) ? declares.filter((m) => enLigne(m.id)) : declares;
  const fin = (m: MoteurGpu) => (charge(m.id) + 1) * ((recette !== undefined ? m.secondes?.[recette] : undefined) ?? 1);
  return capables.sort((a, b) => fin(a) - fin(b));
}

const jobs = new Map<string, Job>();
/** When we first saw each job running; the local proxy does not report started_at. */
const runningSince = new Map<string, number>();

/**
 * Upload an input file as a Comfy asset. Returns an `asset:<id>` token the
 * graph builders drop into a loader's file widget; submit() swaps it for the
 * SDK's asset reference. A local copy is kept for restoring input wells.
 */
export async function uploadInput(name: string, data: Buffer, contentType?: string): Promise<string> {
  const asset = sdk().assets.fromBytes(new Uint8Array(data), { filename: name, contentType });
  const id = await asset.commit();
  await mkdir(INPUT_CACHE, { recursive: true });
  await writeFile(join(INPUT_CACHE, id), data);
  await writeFile(join(INPUT_CACHE, `${id}.name`), name);
  return `asset:${id}`;
}

/** Bytes of an uploaded input, from the local cache. */
export async function readInput(token: string): Promise<{ data: Buffer; name: string } | null> {
  const id = ASSET_TOKEN.exec(token)?.[1];
  if (!id || !existsSync(join(INPUT_CACHE, id))) return null;
  const nameFile = join(INPUT_CACHE, `${id}.name`);
  return {
    data: await readFile(join(INPUT_CACHE, id)),
    name: existsSync(nameFile) ? (await readFile(nameFile, 'utf8')).trim() : id,
  };
}

/** Local path of an uploaded input's bytes (for probing), or null. */
export function inputPath(token: string): string | null {
  const id = ASSET_TOKEN.exec(token)?.[1];
  return id && existsSync(join(INPUT_CACHE, id)) ? join(INPUT_CACHE, id) : null;
}

/** Replace every `asset:<id>` string in a graph with an SDK asset reference. */
async function bindAssets(graph: Record<string, unknown>, moteur = 'principal'): Promise<Record<string, unknown>> {
  const out: Record<string, unknown> = structuredClone(graph);
  for (const node of Object.values(out) as any[]) {
    const inputs = node?.inputs;
    if (!inputs) continue;
    for (const [k, v] of Object.entries(inputs)) {
      const m = typeof v === 'string' ? ASSET_TOKEN.exec(v) : null;
      if (m) inputs[k] = { __type: 'core/ASSET', info: { id: await assetSur(m[1], moteur) } };
    }
  }
  return out;
}

/**
 * Nexora : les entrées sont envoyées au moteur principal ; un autre moteur a son propre magasin. On y renvoie l'octet
 * gardé en cache local une seule fois, et on retient l'id distant.
 */
async function assetSur(id: string, moteur: string): Promise<string> {
  if (moteur === 'principal') return id;
  const lien = join(INPUT_CACHE, `${id}.${moteur}`);
  if (existsSync(lien)) return (await readFile(lien, 'utf8')).trim();
  const inp = await readInput(`asset:${id}`);
  if (!inp) throw new Error('Une image d’entrée n’est plus sur ce serveur. Ajoute-la de nouveau.');
  const distant = await sdk(moteur).assets.fromBytes(new Uint8Array(inp.data), { filename: inp.name }).commit();
  await writeFile(lien, distant);
  return distant;
}

/**
 * A copy of a graph with every `asset:<id>` token replaced by the name the
 * input was uploaded under. Fallback for when the engine cannot hand back the
 * graph it ran (see executedWorkflow); ComfyUI may have stored the file under
 * a slightly different name.
 */
export async function withInputNames(graph: Record<string, unknown>): Promise<Record<string, unknown>> {
  const out: Record<string, unknown> = structuredClone(graph);
  for (const node of Object.values(out) as any[]) {
    const inputs = node?.inputs;
    if (!inputs) continue;
    for (const [k, v] of Object.entries(inputs)) {
      if (typeof v !== 'string' || !ASSET_TOKEN.test(v)) continue;
      inputs[k] = (await readInput(v))?.name ?? v;
    }
  }
  return out;
}

/**
 * The API-format graph a job actually ran, from the engine
 * (GET /api/v2/jobs/{id}/workflow). Asset references come back resolved to
 * the filenames in ComfyUI's input folder, so the graph loads in ComfyUI as-is.
 * Null when the engine no longer has it or only has the authoring format.
 */
export async function executedWorkflow(jobId: string): Promise<Record<string, unknown> | null> {
  try {
    const job = jobs.get(jobId) ?? (await sdk(moteurDuJob(jobId).id).jobs.get(jobId));
    const wf = await job.getWorkflow();
    return wf.format === 'api' ? (wf.workflow as Record<string, unknown>) : null;
  } catch {
    return null;
  }
}

/** Submit an API-format graph. Returns the Comfy job id. */
export async function submit(graph: Record<string, unknown>, moteur = 'principal'): Promise<string> {
  const m = moteurParId(moteur).id;
  const wf = sdk(m).workflows.fromJson(await bindAssets(graph, m));
  const job = await sdk(m).submit(wf);
  jobs.set(job.id, job);
  noterMoteur(job.id, m);
  if (!enCours.has(m)) enCours.set(m, new Set());
  enCours.get(m)!.add(job.id);
  void watch(job);
  return job.id;
}

/** Follow a job's event stream until it reaches a terminal state. */
async function watch(job: Job): Promise<void> {
  try {
    for await (const ev of job.events()) {
      if (ev.kind === 'progress') {
        engine.emit('progress', { jobId: job.id, value: ev.value, step: ev.step, steps: ev.steps });
      } else if (ev.kind === 'preview') {
        engine.emit('preview', { jobId: job.id, data: Buffer.from(ev.data) });
      } else if (ev.kind === 'statusChange') {
        if (ev.status === 'running' && !runningSince.has(job.id)) runningSince.set(job.id, Date.now());
        engine.emit('status', { jobId: job.id, status: ev.status, queuePosition: ev.queuePosition });
        if (TERMINAL.has(ev.status)) break;
      }
    }
  } catch (e) {
    console.error(`[openfield] event stream for ${job.id} dropped:`, e instanceof Error ? e.message : e);
  }
  // The stream is a live feed; polling is the source of truth.
  try {
    await job.wait();
  } catch {
    /* result() reports the failure */
  }
  for (const set of enCours.values()) set.delete(job.id);
  engine.emit('finished', { jobId: job.id });
}

/** Re-attach to a job submitted before a restart. */
export async function reattach(jobId: string): Promise<void> {
  if (jobs.has(jobId)) return;
  const m = moteurDuJob(jobId).id;
  const job = await sdk(m).jobs.get(jobId);
  jobs.set(jobId, job);
  if (!enCours.has(m)) enCours.set(m, new Set());
  enCours.get(m)!.add(jobId);
  void watch(job);
}

export interface JobResult {
  done: boolean;
  success?: boolean;
  canceled?: boolean;
  error?: string;
  output?: { name: string; contentType: string; data: Buffer };
  /** Side outputs a builder names (an object's 'turntable' and 'subject'), by node id. */
  extras?: { nodeId: string; name: string; contentType: string; data: Buffer }[];
  renderSeconds?: number;
}

/** Statut seul : ne télécharge aucun média et ne déduit pas la fin d'un job perdu. */
export async function etatTerminalConfirme(jobId: string): Promise<boolean> {
  const moteurId = jobMoteur.get(jobId);
  const moteur = moteurs.find((m) => m.id === moteurId);
  if (!moteur) return false;
  let lecteur = lecturesJobs.get(moteur.id);
  if (!lecteur) {
    lecteur = new ComfyLow(moteur.baseUrl, moteur.cle || config.comfyApiKey || undefined);
    lecturesJobs.set(moteur.id, lecteur);
  }
  const job = await lecteur.getJob(jobId, { signal: AbortSignal.timeout(4000) });
  return statutTerminalConfirme(job.status);
}

/** Node ids whose outputs ride along with the main one (see server/graphs/trellis.ts). */
const EXTRA_NODES = new Set(['turntable', 'subject']);

/**
 * 3D files a job saved, read from ComfyUI's history. SaveGLB reports them under
 * a "3d" key that the v2 API does not list as an output, so locally they are
 * fetched from ComfyUI's /view like any output file.
 */
async function savedModels(promptId: string, comfyUrl = config.comfyUrl): Promise<{ nodeId: string; name: string; contentType: string; data: Buffer }[]> {
  try {
    const r = await fetch(`${comfyUrl}/history/${encodeURIComponent(promptId)}`, { signal: AbortSignal.timeout(5000) });
    const h = (await r.json()) as Record<string, { outputs?: Record<string, Record<string, unknown>> }>;
    const out = [];
    for (const [nodeId, o] of Object.entries(h[promptId]?.outputs ?? {})) {
      const items = Array.isArray(o['3d']) ? (o['3d'] as { filename: string; subfolder?: string; type?: string }[]) : [];
      for (const it of items) {
        const q = new URLSearchParams({ filename: it.filename, subfolder: it.subfolder ?? '', type: it.type ?? 'output' });
        const f = await fetch(`${comfyUrl}/view?${q}`, { signal: AbortSignal.timeout(120_000) });
        if (!f.ok) continue;
        const ext = it.filename.split('.').pop()?.toLowerCase();
        out.push({
          nodeId, name: it.filename, data: Buffer.from(await f.arrayBuffer()),
          contentType: ext === 'glb' ? 'model/gltf-binary' : ext === 'obj' ? 'model/obj' : 'application/octet-stream',
        });
      }
    }
    return out;
  } catch {
    return [];
  }
}

/** Start and end of a prompt's execution from ComfyUI's history, in ms. */
async function executionWindow(promptId: string, comfyUrl = config.comfyUrl): Promise<{ start?: number; end?: number } | null> {
  try {
    const r = await fetch(`${comfyUrl}/history/${encodeURIComponent(promptId)}`, { signal: AbortSignal.timeout(3000) });
    const h = (await r.json()) as Record<string, { status?: { messages?: [string, { timestamp?: number }][] } }>;
    const msgs = h[promptId]?.status?.messages ?? [];
    const at = (kind: string) => msgs.find((m) => m[0] === kind)?.[1]?.timestamp;
    const start = at('execution_start');
    const end = at('execution_success') ?? at('execution_error') ?? at('execution_interrupted');
    return start ? { start, end } : null;
  } catch {
    return null;
  }
}

/** Final state of a job plus the bytes of its first output. */
export async function result(jobId: string): Promise<JobResult> {
  const moteur = moteurDuJob(jobId);
  const job = jobs.get(jobId) ?? (await sdk(moteur.id).jobs.get(jobId));
  await job.refresh();
  if (!TERMINAL.has(job.status)) return { done: false };
  jobs.delete(jobId);
  // Locally the job id is ComfyUI's prompt id, and ComfyUI's history has exact
  // execution timestamps. The event stream can miss the running event (the proxy
  // caps live streams), so it is only the fallback.
  const exec = isLocal() ? await executionWindow(jobId, moteur.comfyUrl) : null;
  const started = exec?.start ?? job.startedAt?.getTime() ?? runningSince.get(jobId);
  const ended = exec?.end ?? job.completedAt?.getTime() ?? Date.now();
  runningSince.delete(jobId);
  const renderSeconds = started ? (ended - started) / 1000 : undefined;
  if (job.status !== 'succeeded') {
    const err = job.error as any;
    return {
      done: true,
      success: false,
      canceled: job.status === 'canceled' || job.status === 'cancelled',
      error: String(err?.message ?? err?.detail ?? job.status).slice(0, 500),
      renderSeconds,
    };
  }
  // Prefer the graph's own save node ('save' or 'out' in every OpenField
  // builder): a core LoadVideo also reports its input as a video output, and
  // other nodes (GLSLShader) report preview images. Then the media a user
  // wants (video, then image) over previews/temp.
  const all = job.outputs.filter((o) => !EXTRA_NODES.has(o.nodeId));
  const extras = await Promise.all(job.outputs.filter((o) => EXTRA_NODES.has(o.nodeId))
    .map(async (o) => ({ nodeId: o.nodeId, name: o.name, contentType: o.contentType, data: Buffer.from(await o.toBytes()) })));
  // A 3D save is the take's file when the graph has one.
  const model = isLocal() ? (await savedModels(jobId, moteur.comfyUrl)).find((m) => m.nodeId === 'save') : undefined;
  if (model) return { done: true, success: true, output: model, extras, renderSeconds };
  const saved = all.filter((o) => o.nodeId === 'save' || o.nodeId === 'out');
  const outs = saved.length ? saved : all;
  const pick =
    outs.find((o) => (o.nodeId === 'save' || o.nodeId === 'out') && o.contentType.startsWith('video/')) ??
    outs.find((o) => (o.nodeId === 'save' || o.nodeId === 'out') && o.contentType.startsWith('image/')) ??
    outs.find((o) => o.contentType.startsWith('video/')) ??
    outs.find((o) => o.contentType.startsWith('image/')) ??
    outs[0];
  if (!pick) return { done: true, success: false, error: 'No output produced', renderSeconds };
  return {
    done: true,
    success: true,
    output: { name: pick.name, contentType: pick.contentType, data: Buffer.from(await pick.toBytes()) },
    extras,
    renderSeconds,
  };
}

/** Cancel one job, queued or running. */
export async function cancel(jobId: string): Promise<void> {
  const job = jobs.get(jobId) ?? (await sdk(moteurDuJob(jobId).id).jobs.get(jobId));
  await job.cancel();
}

/** Cancel every job this process is tracking. */
export async function cancelAll(): Promise<void> {
  await Promise.allSettled([...jobs.values()].map((j) => j.cancel()));
}

/** Is the v2 API answering? */
export async function apiUp(baseUrl = config.comfyBaseUrl): Promise<boolean> {
  try {
    const headers: Record<string, string> = {};
    const cle = moteurs.find((m) => m.baseUrl === baseUrl)?.cle ?? config.comfyApiKey;
    if (cle) headers.Authorization = `Bearer ${cle}`;
    const r = await fetch(`${baseUrl}/api/v2/jobs?limit=1`, {
      headers,
      signal: AbortSignal.timeout(4000),
    });
    // 501 = Comfy Cloud has no job list yet, but it answered.
    return r.ok || r.status === 501;
  } catch {
    return false;
  }
}

export const isLocal = () => /^https?:\/\/(127\.0\.0\.1|localhost)(:|\/|$)/.test(config.comfyBaseUrl);

const proxies = new Map<string, import('child_process').ChildProcess>();
const estLocal = (url: string) => /^https?:\/\/(127\.0\.0\.1|localhost)(:|\/|$)/.test(url);

/**
 * Local mode only: start comfy-api-proxy in front of ComfyUI if the v2 API is
 * not already answering. The proxy keeps job state in <data>/proxy so jobs
 * survive an OpenField restart.
 * Nexora : un proxy par moteur du parc (état dans <data>/proxy-<id> pour les moteurs ajoutés) ; la réponse est celle
 * du moteur principal, les autres démarrent en arrière-plan.
 */
export async function ensureProxy(timeoutMs = 20_000): Promise<boolean> {
  for (const m of moteurs.slice(1)) void proxyPour(m, timeoutMs);
  return proxyPour(moteurs[0], timeoutMs);
}

async function proxyPour(m: MoteurGpu, timeoutMs: number): Promise<boolean> {
  if (!estLocal(m.baseUrl)) return apiUp(m.baseUrl);
  if (await apiUp(m.baseUrl)) return true;
  const enfant = proxies.get(m.id);
  if (enfant && enfant.exitCode === null) return waitUp(timeoutMs, m.baseUrl);
  const { spawn } = await import('child_process');
  const port = new URL(m.baseUrl).port || '8189';
  const stateDir = join(config.dataDir, m.id === 'principal' ? 'proxy' : `proxy-${m.id}`);
  await mkdir(stateDir, { recursive: true });
  try {
    const p = spawn(config.proxyBin, ['run', '--comfyui', m.comfyUrl, '--port', port, '--state-dir', stateDir], { stdio: 'ignore' });
    p.on('error', (e) => console.error(`[openfield] could not start ${config.proxyBin}:`, e.message));
    proxies.set(m.id, p);
  } catch (e) {
    console.error('[openfield] proxy launch failed:', e instanceof Error ? e.message : e);
    return false;
  }
  return waitUp(timeoutMs, m.baseUrl);
}

async function waitUp(timeoutMs: number, baseUrl = config.comfyBaseUrl): Promise<boolean> {
  const deadline = Date.now() + timeoutMs;
  while (Date.now() < deadline) {
    if (await apiUp(baseUrl)) return true;
    await new Promise((r) => setTimeout(r, 500));
  }
  return false;
}

/** Dernier état connu de chaque moteur (mis à jour par etatMoteurs, appelé toutes les 20 s). */
const enLigneConnu = new Map<string, boolean>();

/** Nexora : état de chaque moteur du parc (API v2 joignable, tâches en cours). */
export async function etatMoteurs() {
  const etat = await Promise.all(moteurs.map(async (m) => ({
    id: m.id, nom: m.nom, recettes: m.recettes, enLigne: await apiUp(m.baseUrl), enCours: enCours.get(m.id)?.size ?? 0,
  })));
  for (const e of etat) enLigneConnu.set(e.id, e.enLigne);
  return etat;
}

/** Recettes déclarées par les moteurs en ligne (un moteur jamais sondé est présumé en ligne). */
export function recettesEnLigne(): Set<string> {
  return new Set(moteurs.filter((m) => enLigneConnu.get(m.id) !== false).flatMap((m) => m.recettes));
}

/** La recette part-elle sur le moteur principal (dont ce serveur contrôle les poids) ? Sinon le moteur distant sait ce qu'il a. */
export function recetteSurPrincipal(recette?: string): boolean {
  const m = moteursPour(recette)[0];
  return !m || m.id === 'principal';
}

/** Stop the proxies this process started. */
export function stopProxy(): void {
  for (const p of proxies.values()) if (p.exitCode === null) p.kill();
}
