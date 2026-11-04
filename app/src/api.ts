/** Client-side API + live socket. */
import type { RenderTier, TierState } from './renderTier';

export interface Take {
  id: number;
  created_at: string;
  project_id: number | null;
  kind: string;
  shot_name: string;
  prompt_id: string | null;
  status: string;
  settings: string;
  output_path: string | null;
  render_seconds: number | null;
  transcript: string | null;
  starred: number;
  error: string | null;
}

export interface Project { id: number; name: string; folder: string }

export type CastKind = 'character' | 'prop' | 'place';
export interface CastRef { token: string; file: string; w: number; h: number; url: string }
export interface CastMember { id: number; name: string; kind: CastKind; refs: CastRef[]; notes: string; created_at: string }
/** Where a cast picture comes from: an upload token, a finished still take, or (MCP) a local file. */
export type CastSource = { token: string } | { takeId: number };

export interface Preamble { id: number; name: string; text: string; sort: number }

export interface ModelFileRef { file: string; dir: string; repo: string; path: string; gb: number; gated?: boolean }

export interface BundleStatus {
  id: string;
  label: string;
  purpose: string;
  license: string;
  licenseWarning?: string;
  optional: boolean;
  gb: number;
  ready: boolean;
  missingFiles: ModelFileRef[];
  missingNodes: { class: string; pack: string; url: string }[];
}

export interface Status {
  up: boolean;
  version?: string;
  gpu?: string;
  api?: boolean;
  target?: 'local' | 'cloud';
  vramFreeGb?: number;
  vramTotalGb?: number;
  queueRemaining?: number;
  otherGpuProcess?: boolean;
  /** Whether a COMFY_LAUNCH command is configured, i.e. START ENGINE can work. */
  canLaunch?: boolean;
  comfyUrl?: string;
  /** The machine-wide video render size and where it came from. */
  renderTier?: TierState;
  /** Set when the server runs as the judge preview (server/judge.ts). */
  judge?: { cap: number; used: number; left: number; maxSeconds: number };
  active: Take[];
}

/** A phone hand-off link (server/phone.ts). `url` holds the single-use secret. */
export interface PhoneSession {
  id: string;
  url: string;
  expiresAt: number;
  port: number;
  maxBytes: number;
  network: { wsl: 'none' | 'mirrored' | 'nat'; bindHost: string; urlHost: string; warning: string | null; commands: string[] };
}

/** Live phone state, relayed over /live. `result` arrives with 'received'. */
export interface PhoneEvent {
  type: 'phone';
  id: string;
  state: 'waiting' | 'opened' | 'receiving' | 'received' | 'closed';
  bytes?: number;
  result?: { token: string; name: string; bytes: number };
  reason?: 'received' | 'expired' | 'cancelled' | 'abuse' | 'replaced';
}

async function j<T>(url: string, init?: RequestInit): Promise<T> {
  // Only claim a JSON body when one exists — Fastify 400s an empty body sent
  // with a JSON content-type, which silently broke every body-less POST
  // (STOP, CLEAR QUEUE, cancel, trash) until 2026-08-04.
  const headers = init?.body
    ? { 'Content-Type': 'application/json', ...init.headers }
    : init?.headers;
  const r = await fetch(url, init && { ...init, headers });
  // Judge preview: a lapsed sign-in goes back to the login page.
  if (r.status === 401 && url.startsWith('/api/')) {
    window.location.assign('/login');
    throw new Error('Sign in again');
  }
  const d = await r.json();
  if (!r.ok) {
    const msg = (d && (d.error || d.message)) || `${r.status}`;
    console.error(`[openfield] ${init?.method || 'GET'} ${url} failed:`, msg);
    throw new Error(msg);
  }
  return d as T;
}

export interface CreerReponse { takeIds: number[]; takeId: number; prompt: string; source: 'llm' | 'repli'; tentatives: number; moteur: 'h3-fast' | 'h3-max' }
export interface PlanFilm { resume: string; description: string; duree: 5 | 10; camera: string; take?: number }
export interface Storyboard {
  titre: string;
  bible: { style: string; personnages: { nom: string; description: string }[]; lieux: { nom: string; description: string }[] };
  plans: PlanFilm[];
  dureeTotale: number;
}
export interface EtatNexora { llm: boolean; moteur: string | null; son: boolean; territoire: string | null; cinema?: boolean; erreur?: string; image?: string | null; musique?: string | null; objet3d?: { apercu: boolean; qualite: boolean; texte: boolean } | null }
export interface ObjetTexteEtat {
  etat: 'image' | 'objet' | 'jugement' | 'fini' | 'echec'; essai: number; image: number; objet: number | null;
  notes: { take: number; note: number; defauts: string[]; raison: string }[]; erreur: string | null; qualite: 'draft' | 'quality'; intention: string;
}
export interface MoteurGpu { id: string; nom: string; recettes: string[]; enLigne: boolean; enCours: number }

/** Agent Producteur (server/nexora/agent.ts). */
export interface PlanProduction {
  titre: string; format: '16:9' | '9:16' | '1:1'; qualite: 'rapide' | 'max'; son: boolean;
  bible: Storyboard['bible'];
  plans: { resume: string; description: string; camera: string; duree: 5 | 10; suite?: boolean; replique?: string }[];
  musique: { envie: string } | null; cartons: { texte: string; position: 'debut' | 'fin' }[]; candidats: 1 | 2;
}
export interface ResumeProjet {
  id: string; titre: string; format: string; qualite: string; plans: number; tournes: number; creditsActifs: boolean;
  estimation: { plans: number; scenes: number; sequences: number; dureeS: number; credits: number; secondesGpu: number; heuresGpu: number; restants: number; tournes: number; enCours: number };
}
export interface ArbreProjet { id: string; titre: string; scenes: { id: string; titre: string; plans: { id: string; resume: string; duree: number; etat: string; take: number | null }[] }[] }
export interface PriseVue { take: number; statut: 'queued' | 'running' | 'done' | 'failed' | 'stopped'; brouillon: boolean; finalDe?: number; retenue: boolean; rejetee: boolean; credits: number; secondes: number }
export interface VuePrises {
  film: number; creditsActifs: boolean;
  plans: { plan: number; resume: string; prises: PriseVue[] }[];
  compteur: { credits: number; secondes: number; prises: number; brouillons: number; ecartees: { credits: number; secondes: number; prises: number } };
}
export interface VueMontage {
  id: string; film: number; url: string; source: 'code' | 'llm'; tours: number; plafondTours: number; genre: string; format: string;
  dureeS: number; sonie: { lufs: number; crete_db: number } | null; musique?: boolean;
  metriques: { score: number; rythme: number; battues: number; doublons: number; texte: number; audio: number; plans: number; dureeS: number; dureeMoyennePlanS: number; coupesParMinute: number; bpm: number | null; ecarts: { gravite: string; message: string; indice: string }[] };
  amelioration?: { avant: number; apres: number; gardee: boolean; message: string };
}
export interface DevisProduction { credits: number | null; creditsEstimes: number; secondesGpu: number; minutes: number; rendus: number; plans: number; musique: boolean; candidats: 1 | 2 }
export type PropositionProducteur =
  | { id: string; genre: 'production'; plan: PlanProduction; devis: DevisProduction; base?: number }
  | { id: string; genre: 'refaire'; film: number; plan: number; description?: string; camera?: string; devis: DevisProduction }
  | { id: string; genre: 'remontage'; film: number; ordre: number[]; transition: 'coupe' | 'fondu'; devis: DevisProduction };
export interface FilmResume {
  film: number; titre: string; etat: string; erreur?: string; format?: string; qualite?: string; video?: string; musique: string | null; cartons: string[];
  plans: { plan: number; resume: string; etat: string; controle?: 'ok' | string[]; juge?: { prise: number; source: 'juge' | 'controle' | 'repli'; raison: string }; reprises?: number }[];
}
export interface SessionProducteur {
  id: string; titre: string;
  fil: { de: 'personne' | 'producteur' | 'systeme'; texte: string; date: string; proposition?: string; production?: number }[];
  proposition: PropositionProducteur | null;
  productions: { filmId: number; lanceLe: string; genre?: string; plan?: PlanProduction; film: FilmResume | { erreur: string } }[];
  plafond: { credits: number; secondes: number }; juge: boolean; credits: boolean;
  palier: PalierLlm | null; palierEffectif: PalierLlm | null; paliers: Record<PalierLlm, boolean>;
  usage: { appels: number; entree: number; sortie: number; raisonnement: number; usd: number; creditsExacts: number; creditsFactures: number; dernier?: { palier: string; entree: number; sortie: number; credits: number; factures: number; reserves: number } } | null;
}
export type PalierLlm = 'eco' | 'equilibre' | 'expert';
export type VarianteProducteur = 'format-16:9' | 'format-9:16' | 'format-1:1' | 'nouvelle-prise' | 'cinema' | 'courte';

export const api = {
  status: () => j<Status>('/api/status'),
  /** Nexora Creative : une intention en français devient une vidéo (prompt écrit par le LLM, rendu MiniMax H3). */
  nexoraCreer: (b: { intention: string; format: '16:9' | '9:16' | '1:1'; duree: 5 | 10 | 15; son: boolean; qualite?: 'rapide' | 'max'; image?: string; musique?: boolean; replique?: string; camera?: string }) =>
    j<CreerReponse>('/api/nexora/creer', { method: 'POST', body: JSON.stringify(b) }),
  nexoraEtat: () => j<EtatNexora>('/api/nexora/etat'),
  producteurListe: () => j<{ sessions: { id: string; titre: string; updated_at: string }[] }>('/api/nexora/producteur'),
  producteurNouvelle: () => j<SessionProducteur>('/api/nexora/producteur', { method: 'POST', body: '{}' }),
  producteurSession: (id: string) => j<SessionProducteur>(`/api/nexora/producteur/${id}`),
  producteurMessage: (id: string, texte: string) => j<SessionProducteur>(`/api/nexora/producteur/${id}/message`, { method: 'POST', body: JSON.stringify({ texte }) }),
  producteurPalier: (id: string, palier: PalierLlm | null) => j<SessionProducteur>(`/api/nexora/producteur/${id}/palier`, { method: 'POST', body: JSON.stringify({ palier }) }),
  producteurValider: (id: string, proposition: string) => j<SessionProducteur>(`/api/nexora/producteur/${id}/valider`, { method: 'POST', body: JSON.stringify({ proposition }) }),
  producteurAjuster: (id: string, proposition: string, r: { candidats?: number; qualite?: string; format?: string; son?: boolean; musique?: boolean }) =>
    j<SessionProducteur>(`/api/nexora/producteur/${id}/ajuster`, { method: 'POST', body: JSON.stringify({ proposition, ...r }) }),
  objetDevis: (b: { qualite: 'draft' | 'quality'; source: 'texte' | 'image' }) => j<{ secondesEstimees: number; credits: number | null; recette: string }>('/api/nexora/objet/devis', { method: 'POST', body: JSON.stringify(b) }),
  objetTexte: (b: { intention: string; qualite: 'draft' | 'quality' }) => j<{ id: number; secondesEstimees: number; credits?: number }>('/api/nexora/objet/texte', { method: 'POST', body: JSON.stringify(b) }),
  objetTexteEtat: (id: number) => j<ObjetTexteEtat>(`/api/nexora/objet/${id}`),
  creerPersonnage: (b: { nom: string; description: string }) => j<{ takeId: number; nom: string; apparence: string }>('/api/nexora/personnage', { method: 'POST', body: JSON.stringify(b) }),
  statutPersonnage: (take: number) => j<{ etat: 'rendu' | 'pret' | 'echec'; membre?: CastMember; erreur?: string }>(`/api/nexora/personnage/${take}`),
  prisesFilm: (film: number) => j<VuePrises>(`/api/nexora/film/${film}/prises`),
  brouillonsFilm: (film: number, plan: number, nombre = 2) => j<VuePrises>(`/api/nexora/film/${film}/plan/${plan}/brouillon`, { method: 'POST', body: JSON.stringify({ nombre }) }),
  prise: (film: number, plan: number, take: number, action: 'garder' | 'rejeter' | 'finaliser') =>
    j<VuePrises & { filmId?: number }>(`/api/nexora/film/${film}/plan/${plan}/prise`, { method: 'POST', body: JSON.stringify({ take, action }) }),
  projets: () => j<{ projets: ResumeProjet[] }>('/api/nexora/projets').then((r) => r.projets),
  projet: (id: string) => j<ResumeProjet & { bible: { style: string; notes: string; personnages: { nom: string; description: string }[]; lieux: { nom: string; description: string }[] }; arbre: ArbreProjet[] }>(`/api/nexora/projet/${id}`),
  creerProjet: (b: { titre: string; scenario: string; format: string; qualite: string; bible?: { style?: string } }) => j<ResumeProjet>('/api/nexora/projet', { method: 'POST', body: JSON.stringify(b) }),
  lancerProjet: (id: string, taille: number) => j<{ lances: number; cout: number; secondes: number; projet: ResumeProjet }>(`/api/nexora/projet/${id}/lancer`, { method: 'POST', body: JSON.stringify({ taille }) }),
  monterFilm: (film: number, b: { genre?: string; duree?: number } = {}) => j<VueMontage>(`/api/nexora/film/${film}/monter`, { method: 'POST', body: JSON.stringify(b) }),
  ameliorerMontage: (id: string) => j<VueMontage>(`/api/nexora/montage/${id}/ameliorer`, { method: 'POST', body: '{}' }),
  producteurVariante: (id: string, film: number, genre: VarianteProducteur) => j<SessionProducteur>(`/api/nexora/producteur/${id}/variante`, { method: 'POST', body: JSON.stringify({ film, genre }) }),
  nexoraIdees: (b: { mode: 'video' | 'image' | 'film'; theme?: string }) =>
    j<{ idees: string[]; source: 'llm' | 'repli' }>('/api/nexora/idees', { method: 'POST', body: JSON.stringify(b) }),
  nexoraPublication: (b: { id: number; plateforme: string; langue: 'fr' | 'en' }) =>
    j<{ titre: string; texte: string; hashtags: string[]; mention: string; source: 'llm' | 'repli' }>('/api/nexora/publication', { method: 'POST', body: JSON.stringify(b) }),
  nexoraMoteursGpu: () => j<MoteurGpu[]>('/api/nexora/moteurs-gpu'),
  nexoraAmeliorer: (b: { intention: string; mode: 'video' | 'image' | 'film' }) =>
    j<{ texte: string }>('/api/nexora/ameliorer', { method: 'POST', body: JSON.stringify(b) }),
  nexoraImage: (b: { intention: string; format: '16:9' | '9:16' | '1:1'; nombre?: number; qualite?: 'rapide' | 'max' }) =>
    j<{ takeIds: number[]; prompt: string; source: 'llm' | 'repli'; modele: string }>('/api/nexora/image', { method: 'POST', body: JSON.stringify(b) }),
  nexoraImageJeton: (id: number) => j<{ jeton: string }>(`/api/nexora/image/${id}/jeton`, { method: 'POST', body: '{}' }),
  nexoraDevis: (b: { format: string; duree: number; son: boolean; qualite: string; image?: string }) =>
    j<{ credits: number | null; secondesEstimees: number; moteur: string }>('/api/nexora/devis', { method: 'POST', body: JSON.stringify(b) }),
  nexoraFilmPlan: (b: { intention: string; duree: number }) =>
    j<{ storyboard: Storyboard; source: 'llm' | 'repli' }>('/api/nexora/film/plan', { method: 'POST', body: JSON.stringify(b) }),
  nexoraFilmRefaire: (filmId: number, b: { plan: number; description?: string; camera?: string }) =>
    j<{ filmId: number }>(`/api/nexora/film/${filmId}/refaire`, { method: 'POST', body: JSON.stringify(b) }),
  nexoraClipMusique: (clipId: number, b: { envie?: string }) =>
    j<{ takeId: number; source: 'llm' | 'repli' }>(`/api/nexora/clip/${clipId}/musique`, { method: 'POST', body: JSON.stringify(b) }),
  nexoraClipAvecMusique: (clipId: number, musique: number) =>
    j<{ takeId: number }>(`/api/nexora/clip/${clipId}/avec-musique`, { method: 'POST', body: JSON.stringify({ musique }) }),
  nexoraFilmMusique: (filmId: number, b: { envie?: string }) =>
    j<{ takeId: number; source: 'llm' | 'repli' }>(`/api/nexora/film/${filmId}/musique`, { method: 'POST', body: JSON.stringify(b) }),
  nexoraFilmMontage: (filmId: number, b: { ordre: number[]; transition: 'coupe' | 'fondu'; musique?: number | null }) =>
    j<{ filmId: number }>(`/api/nexora/film/${filmId}/montage`, { method: 'POST', body: JSON.stringify(b) }),
  nexoraFilmTourner: (b: { storyboard: Storyboard; format: '16:9' | '9:16' | '1:1'; son: boolean; qualite?: 'rapide' | 'max'; intention: string }) =>
    j<{ filmId: number }>('/api/nexora/film/tourner', { method: 'POST', body: JSON.stringify(b) }),
  /** Set the machine-wide render size; null goes back to the default (OPENFIELD_RENDER_TIER or the GPU). */
  setRenderTier: (renderTier: RenderTier | null) =>
    j<{ renderTier: TierState }>('/api/settings', { method: 'PUT', body: JSON.stringify({ renderTier }) }),
  takes: (projectId: number | null) => j<Take[]>(`/api/takes${projectId ? `?project=${projectId}` : ''}`),
  projects: () => j<Project[]>('/api/projects'),
  addProject: (name: string, folder: string) =>
    j<{ id: number }>('/api/projects', { method: 'POST', body: JSON.stringify({ name, folder }) }),
  upload: (name: string, dataUrl: string) =>
    j<{ name: string }>('/api/upload', { method: 'POST', body: JSON.stringify({ name, dataUrl }) }),
  generate: (body: Record<string, unknown>) =>
    j<{ takeId: number; takeIds: number[] }>('/api/generate', {
      method: 'POST',
      body: JSON.stringify(body),
    }),
  upres: (takeId: number, opts: { model?: string; rife?: boolean }) =>
    j<{ takeId: number }>(`/api/takes/${takeId}/upres`, { method: 'POST', body: JSON.stringify(opts) }),
  stop: () => j<{ ok: true }>('/api/stop', { method: 'POST' }),
  cancelTake: (id: number) => j<{ ok: true }>(`/api/takes/${id}/cancel`, { method: 'POST' }),
  clearQueue: () => j<{ ok: true }>('/api/queue/clear', { method: 'POST' }),
  startEngine: () => j<{ ok: boolean }>('/api/engine/start', { method: 'POST' }),
  models: () => j<{ checkpoints: Record<string, string[]>; card: Record<string, unknown> }>('/api/models'),
  removeQueued: (promptId: string) => j<{ ok: true }>(`/api/queue/${promptId}`, { method: 'DELETE' }),
  star: (id: number, on: boolean) => j<Take>(`/api/takes/${id}/star`, { method: 'POST', body: JSON.stringify({ on }) }),
  trash: (id: number) => j<{ ok: true }>(`/api/takes/${id}`, { method: 'DELETE' }),
  preflight: (refresh = false) =>
    j<{ bundles: BundleStatus[] }>(`/api/preflight${refresh ? '?refresh=1' : ''}`),
  preambles: () => j<Preamble[]>('/api/preambles'),
  addPreamble: (name: string, text: string) =>
    j<{ id: number }>('/api/preambles', { method: 'POST', body: JSON.stringify({ name, text }) }),
  savePreamble: (id: number, name: string, text: string) =>
    j<Preamble>(`/api/preambles/${id}`, { method: 'PUT', body: JSON.stringify({ name, text }) }),
  estimate: (q: Record<string, string | number>) =>
    j<{ seconds: number | null; samples: number }>(`/api/estimate?${new URLSearchParams(q as Record<string, string>)}`),
  free: () => j<{ ok: true }>('/api/free', { method: 'POST' }),
  phoneStart: () => j<PhoneSession>('/api/phone/start', { method: 'POST' }),
  /** Close our session only: a newer one from another window keeps running. */
  phoneStop: (id: string) => j<{ ok: true }>('/api/phone/stop', { method: 'POST', body: JSON.stringify({ id }) }),
  cast: () => j<CastMember[]>('/api/cast'),
  createCast: (m: { name: string; kind: CastKind; notes: string; refs: CastSource[] }) =>
    j<CastMember>('/api/cast', { method: 'POST', body: JSON.stringify(m) }),
  updateCast: (id: number, patch: { name?: string; kind?: CastKind; notes?: string; addRefs?: CastSource[]; removeRefs?: number[] }) =>
    j<CastMember>(`/api/cast/${id}`, { method: 'PUT', body: JSON.stringify(patch) }),
  deleteCast: (id: number) => j<{ ok: true }>(`/api/cast/${id}`, { method: 'DELETE' }),
  castHero: (b: { castIds: number[]; shot: string; width?: number; height?: number }) =>
    j<{ takeId: number }>('/api/cast/hero', { method: 'POST', body: JSON.stringify(b) }),
  deletePreamble: (id: number) => j<{ ok: true }>(`/api/preambles/${id}`, { method: 'DELETE' }),
  /** Director scenes: plan a shot list (poll it), then shoot it into one cut. */
  directorPlan: (body: { scene: string; shots?: number; planner?: string }) =>
    j<ScenePlan>('/api/director/plan', { method: 'POST', body: JSON.stringify(body) }),
  directorPlanStatus: (id: string) => j<ScenePlan>(`/api/director/plan/${id}`),
  directorScene: (body: Record<string, unknown>) =>
    j<{ cutId: number; take: Take }>('/api/director/scene', { method: 'POST', body: JSON.stringify(body) }),
  /** Measure a take as a loop (stored on the take as settings.seam). */
  seam: (id: number) => j<SeamMeasure>(`/api/takes/${id}/seam`),
  /** Collect an HDR finish's EXRs and HLG master from the engine again. */
  collectHdr: (id: number) => j<Record<string, unknown>>(`/api/takes/${id}/collect-hdr`, { method: 'POST' }),
  /** Seam Doctor: auto picks trim, then a re-render across the wrap, then a new seed, by measurement. */
  /** Stage: the blocking frames rendered in WebGL become the clay and depth inputs. */
  stageBlocking: (body: { width: number; height: number; clay: string[]; depth: string[]; clayStill: string; depthStill: string }) =>
    j<StageBlocking>('/api/stage/blocking', { method: 'POST', body: JSON.stringify(body) }),
  fixSeam: (id: number, strategy: 'auto' | 'trim' | 'regen' | 'bridge' | 'reseed' = 'auto') =>
    j<{ fix: string | null; before: SeamMeasure; takeIds: number[] }>(`/api/takes/${id}/fix-seam`, { method: 'POST', body: JSON.stringify({ strategy }) }),
};

/** A blocking turned into engine inputs (server/stage.ts). */
export interface StageBlocking {
  clayVideo: string;
  depthVideo: string;
  depthImage: string;
  clayImage: string;
  width: number;
  height: number;
  frames: number;
  /** Seconds the server spent encoding and uploading. */
  took?: number;
}

/** A shot list being planned on the server (server/scene.ts). */
export interface ScenePlan {
  id: string;
  status: 'running' | 'done' | 'failed';
  scene: string;
  shots?: { framing: string; move: string; action: string; seconds: number }[];
  planner?: 'engine' | 'ollama' | 'split';
  notes: string[];
  seconds?: number;
  error?: string;
}

/** How a loop closes (server/seam.ts). ratio is the wrap as a multiple of an ordinary frame step. */
export interface SeamMeasure {
  n: number;
  fps: number;
  verdict: 'seamless' | 'visible';
  ratio: number;
  texture: { wrap: number; local: number; median: number; ratio: number };
  composition: { wrap: number; local: number; ratio: number };
  splices?: { frame: number; ratio: number }[];
}

export interface LiveEvents {
  onProgress: (v: { promptId: string; value: number; max: number }) => void;
  onStarted?: (promptId: string) => void;
  onPreview: (blobUrl: string, promptId: string | null) => void;
  onTake: (take: Take) => void;
  onQueue: (remaining: number) => void;
  onPhone?: (e: PhoneEvent) => void;
}

/** Connect the live socket; auto-reconnects. Returns a cleanup fn. */
export function connectLive(ev: LiveEvents): () => void {
  let ws: WebSocket | null = null;
  let dead = false;
  let lastPreview: string | null = null;
  let previewJob: string | null = null;

  const open = () => {
    ws = new WebSocket(`ws://${location.host}/live`);
    ws.binaryType = 'blob';
    ws.onmessage = (m) => {
      if (m.data instanceof Blob) {
        if (lastPreview) URL.revokeObjectURL(lastPreview);
        lastPreview = URL.createObjectURL(m.data);
        ev.onPreview(lastPreview, previewJob);
        return;
      }
      try {
        const d = JSON.parse(m.data);
        if (d.type === 'preview') previewJob = d.promptId ?? null;
        if (d.type === 'progress') ev.onProgress(d);
        if (d.type === 'started') ev.onStarted?.(d.promptId);
        if (d.type === 'take') ev.onTake(d.take);
        if (d.type === 'queue') ev.onQueue(d.remaining);
        if (d.type === 'phone') ev.onPhone?.(d);
      } catch { /* ignore */ }
    };
    ws.onclose = () => { if (!dead) setTimeout(open, 2500); };
  };
  open();
  return () => { dead = true; ws?.close(); };
}

export const mediaUrl = (id: number) => `/api/media/${id}`;
export const posterUrl = (id: number) => `/api/poster/${id}`;
export const downloadUrl = (id: number) => `/api/media/${id}?download=1`;
/** An Object take's sidecars: the turntable render and the isolated subject it was built from. */
export const turntableUrl = (id: number) => `/api/takes/${id}/turntable`;
export const subjectUrl = (id: number) => `/api/takes/${id}/subject`;
/** An HDR finish's downloads: the EXR zip, the HLG HEVC .mov, the HLG ProRes .mov. */
export const finishFileUrl = (id: number, which: 'exr' | 'hlg' | 'prores') => `/api/takes/${id}/file/${which}`;
export const inputUrl = (token: string) => `/api/input-image/${encodeURIComponent(token)}`;
/** A take's ComfyUI workflow (API format). The path ends in a .json filename
 *  because ComfyUI names a dropped link after its URL and types it by extension. */
export const workflowUrl = (id: number, download = false) =>
  `/api/takes/${id}/workflow/openfield_take_${id}.json${download ? '?download=1' : ''}`;

/** Read a File as a data URL and upload it; returns the asset token. */
export async function uploadFile(f: File): Promise<string> {
  const dataUrl = await new Promise<string>((res, rej) => {
    const r = new FileReader();
    r.onload = () => res(String(r.result));
    r.onerror = () => rej(r.error);
    r.readAsDataURL(f);
  });
  return (await api.upload(f.name, dataUrl)).name;
}

/** Upload a finished take's media as a new input (Animate, Use as reference). */
export async function takeAsInput(id: number, name = `take_${id}.png`): Promise<string> {
  const blob = await (await fetch(mediaUrl(id))).blob();
  return uploadFile(new File([blob], name, { type: blob.type }));
}

// ---------- Mode Marketing (vague 2) ----------
export interface KitMarque {
  nom: string;
  logo: { svg?: string; png?: string; largeurPx?: number; hauteurPx?: number };
  couleurs: { primaire: string; secondaire: string; accent: string; encre: string; papier: string };
  polices: { titre: string; texte: string };
  ton: { adjectifs: string[]; interdits: string[] };
  contact: { entreprise: string; nom: string; titre: string; adresse: string; telephone: string; courriel: string; web: string };
  langue: 'fr' | 'en';
}
export interface ControlesKit { contrastes: { texte: string; fond: string; ratio: number; aa: boolean; aaGrandTexte: boolean }[]; logo: { ok: boolean; avertissements: string[] } | null; contacts: { cle: string; libelle: string; valeur: string }[] }
export interface FormatMarketing { id: string; nom: string; largeur: number; hauteur: number; fondPerdu: number; faces: number; gabarits: { id: string; nom: string; description: string }[] }
export interface MarqueEtat { kit: KitMarque | null; polices: { id: string; nom: string; genre: string }[]; formats: FormatMarketing[]; controles: ControlesKit | null; cmjn: boolean }
export interface CalqueTexteUi { type: 'texte'; id: string; texte: string; taille: number; police: string; poids: number; interligne: number; [k: string]: unknown }
export interface SpecUi { version: 1; format: string; gabarit: string; variables: Record<string, string>; faces: { nom: string; genre: 'art' | 'decoupe'; calques: ({ type: string; id: string } & Record<string, unknown>)[] }[]; [k: string]: unknown }
export interface Constat { gravite: 'erreur' | 'avertissement' | 'info'; code: string; face: number; calque?: string; message: string }
export interface DevisMarketing { credits: number; creditsReserves: number; usd: number; libelle: string; note: string; palier: string }
export interface UsageMarketing { credits: number; usd: number; devisCredits: number; palier: string | null }
export interface PropositionUi { gabarit: string; nom: string; pourquoi: string; variables: Record<string, string>; spec: SpecUi; retires: string[] }
export interface RenduMarketing { id: string; fichiers: { nom: string; url: string; octets: number; genre: string }[]; controle: { ok: boolean; erreurs: number; avertissements: number; constats: Constat[] }; ms: number; cmjn: boolean }
const post = <T>(u: string, b: unknown) => j<T>(u, { method: 'POST', body: JSON.stringify(b) });
export const marketing = {
  marque: () => j<MarqueEtat>('/api/nexora/marque'),
  enregistrer: (k: KitMarque) => j<{ kit: KitMarque; controles: ControlesKit }>('/api/nexora/marque', { method: 'PUT', body: JSON.stringify(k) }),
  logo: (type: 'svg' | 'png', donnees: string) => post<{ logo: KitMarque['logo']; controle: { ok: boolean; avertissements: string[] }; couleurs: string[]; palette: KitMarque['couleurs'] }>('/api/nexora/marque/logo', { type, donnees }),
  devis: (action: 'propositions' | 'logos' | 'variantes' | 'rendu') => post<DevisMarketing>('/api/nexora/marketing/devis', { action }),
  propositions: (phrase: string, format: string) => post<{ propositions: PropositionUi[]; sansIA: boolean; palier: string | null; escalades: number; avertissements: string[]; usage: UsageMarketing }>('/api/nexora/marketing/propositions', { phrase, format }),
  logos: (idee: string) => post<{ pistes: { nom: string; idee: string; svg: string; origine: 'ia' | 'code' }[]; palier: string | null; avertissements: string[]; usage: UsageMarketing }>('/api/nexora/marketing/logos', { idee }),
  spec: (b: { gabarit: string; format: string; variables?: Record<string, string>; palette?: 'defaut' | 'inverse' | 'sombre' }) => post<{ spec: SpecUi }>('/api/nexora/marketing/spec', b),
  rendu: (spec: SpecUi, cmjn: boolean) => post<RenduMarketing>('/api/nexora/marketing/rendu', { spec, cmjn }),
};
