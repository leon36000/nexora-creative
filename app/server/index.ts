/**
 * OpenField server: Fastify on OPENFIELD_PORT (default 3161).
 * Owns: generate/stop/queue API, job history, project folders, the live
 * relay (per-step previews from the Comfy SDK event stream), completion
 * handling, whisper transcription, and media serving. The browser never
 * talks to ComfyUI directly; every job goes through engine.ts (Comfy SDK).
 */
import { randomUUID } from 'node:crypto';
import Fastify, { type FastifyReply, type FastifyRequest } from 'fastify';
import websocket from '@fastify/websocket';
import fastifyStatic from '@fastify/static';
import { execFile } from 'child_process';
import { createReadStream, existsSync, mkdirSync, readdirSync, readFileSync, realpathSync, rmSync, statSync, writeFileSync } from 'fs';
import { dirname, extname, join, resolve, sep } from 'path';
import type { WebSocket } from 'ws';
import * as comfy from './comfy.js';
import * as eng from './engine.js';
import { enregistrerDetourage } from './nexora/detourage/routes.js';
import { config, ROOT } from './config.js';
import { buildH3Graph, snapH3Length } from './graphs/h3.js';
import { besoinDe, intentionAvecCamera, CHECKPOINT_FASTH3, choisirMoteur, corpsRendu, dureeEffective, lireDemandeCreer, type FormatCreer, type MoteurVideo } from './nexora/creer.js';
import { buildMusic3Graph } from './graphs/music3.js';
import { reecrireImage } from './nexora/reecritureImage.js';
import { demarrerLectureReglages } from './nexora/reglagesSite.js';
import { lireJson } from './nexora/llm.js';
import { moderer } from './nexora/moderation.js';
import { KitMarqueSchema, POLICES, assainirSvg, contactsActifs, controlerLogo, couleursDePng, couleursDeSvg, decoderPng, paletteDepuisCouleurs, resumeMarque, variantePalette, verifierContrastes, type KitMarque } from './nexora/marketing/kit.js';
import { StoreKit } from './nexora/marketing/store.js';
import { FORMATS, lireSpec } from './nexora/marketing/spec.js';
import { GABARITS, construireSpec, gabaritsPour } from './nexora/marketing/modeles.js';
import { ghostscriptDisponible, rendre, type ResultatRendu } from './nexora/marketing/rendu.js';
import { devisMarketing, type ActionMarketing } from './nexora/marketing/devis.js';
import { idearLogos, lireBrief, proposer, type ClientPalier } from './nexora/marketing/assistant.js';
import { ecrirePublication, PLATEFORMES, type Plateforme } from './nexora/publication.js';
import { ecrireMusique } from './nexora/musique.js';
import { planifierMoteurs } from './nexora/registre.js';
import { compteCourant, territoireDuCompte } from './nexora/compte.js';
import { clientLlmCourant, ErreurLlm, type ClientLlm } from './nexora/llm.js';
import { clientPalier, LIBELLES_PALIER, estPalier, type Palier } from './nexora/niveaux.js';
import { palierDuRole, paliersDisponibles, palierSuivant } from './nexora/paliers.js';
import { coutJuge3dUsd, devisJuge3d, devisLlm, executerSousReservation, ErreurPlafondLlm, GrandLivreUsage, Releve, type BilanRun } from './nexora/usage.js';
import { clientAvecSecours, type FicheRealisation } from './nexora/realisateur.js';
import { BRIEFS_FILMS } from './nexora/bench/briefsFilms.js';
import { escalader, optionsPalier, type BriefFilm } from './nexora/montage/film.js';
import { accesOrganisation, configAuthDepuisEnv, monterAuthentification } from './nexora/auth.js';
import { actionEspace, espacePlein, espaceSite, marquerPlein } from './nexora/espace.js';
import { actionFacturation, type CreditsPrise, devisCredits, facturationSite, secondesGpuEstimees, tarifDepuisEnv } from './nexora/credits.js';
import { reecrireH3 } from './nexora/reecritureH3.js';
import { xmlFcp7 } from './nexora/projetExport.js';
import { demanderEffet, lireDemandeEffet } from './nexora/effets.js';
import { argsPcm, argsSilences, creationsPourStudio, decouperSousTitres, demanderAssistant, detecterTemps, lireDemandeAssistant, lireSilences, lireTranscription, silencesAvecMarge, TAUX_RYTHME } from './nexora/studio.js';
import { transcrireSurGpu } from './nexora/transcriptionGpu.js';
import { argsAvecMusique, argsExport, intentionDuPlan, lireStoryboard, planifierFilm, storyboardPourMontage, storyboardPourRefaire, storyboardProlonger, storyboardRaccord, type Storyboard } from './nexora/film.js';
import { avancerFilm, filmsEnAttente, initFilms, tournerFilm } from './nexora/filmMoteur.js';
import { lireCartons } from './nexora/cartons.js';
import { buildLtxGraph } from './graphs/ltx.js';
import { buildLtx25Graph, ltx25EffectiveSize, ltx25Mode, LTX25_FPS, snapFrames } from './graphs/ltx25.js';
import { applyPost } from './graphs/director.js';
import { advance, cleanScene, getPlan, initScenes, postBlockingReason, shootScene, shotsOf, startPlan, waitingCuts } from './scene.js';
import { buildStillsGraph } from './graphs/stills.js';
import { listUserLoras, pickLoras, type LoraFamily } from './loras.js';
import { buildDreamGraph, buildRedrawGraph, buildSharpenGraph, redrawBatch, type UpscaleSource } from './graphs/upscale.js';
import {
  CUTOUT_MAX_SECONDS, DREAM_CREATIVITY, REDRAW_HEIGHTS, REDRAW_MAX_SECONDS, clampEra, cutoutSize, dreamFrames, eraGrade, isRamp, restyleInstruction, restyleLook, restylePrompt,
  sharpenMaxSeconds, swapPrompt, upscaleSize, type UpscaleMode,
} from '../src/catalog.js';
import { EDIT_ANGLES_LORA, EDIT_LIGHTNING, EDIT_LIGHTNING_2509, buildEditGraph, editSize, expandLayout } from './graphs/edit.js';
import { buildMirrorGraph } from './graphs/mirror.js';
import { buildCutoutStillGraph, buildCutoutVideoGraph, type CutoutBackground, type CutoutMethod } from './graphs/cutout.js';
import { buildRestyleGraph, buildSwapGraph } from './graphs/restyle.js';
import { checkerPreview } from './cutout.js';
import { buildReshootGraph, buildReshootWarpPreviewGraph } from './graphs/reshoot.js';
import { buildExtendGraph, buildSoundGraph, buildSpeakGraph, buildTransitionGraph } from './graphs/ltxtools.js';
import { takes, projects, speed, preambles, takeWorkflows, cast as castDb, sessionsProducteur, projetsLongs, type CastKind } from './jobs.js';
import { analyserMedia } from './nexora/montage/analyse.js';
import { resoudrePersonnages } from './nexora/personnagesCast.js';
import { compteurProjet, corpsBrouillonDe, corpsFinalDe, prisesDuPlan, type PrisesDuPlan } from './nexora/prises.js';
import { aplatir, estimerProjet, intentionDuPlanProjet, ordreAssemblage, prochainLot, scenarioVersArbre, type ProjetLong, type PlanProjet } from './nexora/projet.js';
import { convertirEnPromptRef, decoupeFiche, promptFiche } from './nexora/personnages.js';
import { dureeTotaleS } from './nexora/montage/editplan.js';
import { rendreEditPlan } from './nexora/montage/rendu.js';
import { ameliorerMontage, briefDuFilm, type EtatMontageFilm, GENRES_MONTAGE, monterEnCode, vueMetriques } from './nexora/montage/producteur.js';
import type { DepsAgent } from './nexora/agent.js';
import { ajusterProposition, depassement, devisProduction, nouvelleSession, planVersStoryboard, tourProducteur, validerProposition, variante, type GenreVariante, type PlanProduction, type Proposition, type SessionProducteur } from './nexora/agent.js';
import { jugeDisponible } from './nexora/juge.js';
import { MESURES_OBJET_PC5, recetteMultivue } from './nexora/objet3d.js';
import { PRODUIT_3D } from '../src/produit3d.js';
import { analyser, cartesPbr, cibleTriangles, decimerGlb, EXTENSION_RELIEF, exporter, FORMATS_RELIEF, lireGlb, TAILLE_MM_DEFAUT, TYPE_MIME_RELIEF, type FormatRelief } from './nexora/relief.js';
import { TOURNETTE_JUGE, NOTE_MINIMALE, argsGif, indicesQuatreVues, jugerVuesObjet, plancheVuesDataUrl, type VerdictVues, prochaineEtapeTexte3D, decisionApresJuge, promptReferenceObjet, recetteObjet, secondesTexteVers3D, secondesObjet, type EtatTexte3D, type QualiteObjet } from './nexora/objet3d.js';
import {
  CAST_KINDS, MAX_REFS, allocate, isCastFile, castHeroFrame, composeInstruction, liveRefs, mentioned, plainText, refFrom, renameFiles, storeRef,
  setCastQueue, sheetPlan, type HeroOpts,
} from './cast.js';
import { buildCastVideoGraph } from './graphs/cast.js';
import { imageDims, saveToProject, safeShotName } from './files.js';
import { transcribe } from './whisper.js';
import { bundlesFor } from './models.js';
import { blockingReason, blockingReasonFor, clearPreflightCache, effectBlockingReason, preflight } from './preflight.js';
import { effectById, effectPrompt } from '../src/effects.js';
import { closePhoneSession, openPhoneSession, phoneSession } from './phone.js';
import { load as loadClip, measureLoop, planBridge, planRegen, planTrim, scoreWindow, videoInfo, type SeamMeasure } from './seam.js';
import { buildSeamBridgeGraph, buildSeamRegenGraph, buildSeamTrimGraph } from './graphs/seam.js';
import { buildHdrGraph } from './graphs/hdr.js';
import { OBJECT_QUALITY, TURNTABLE, buildTrellisGraph, type ObjectQuality } from './graphs/trellis.js';
import { collectHdr } from './hdr.js';
import { buildStageLookGraph, buildStageShotGraph, lookEditInstruction, lookPrompt } from './graphs/stage.js';
import { checkSize, ingestBlocking, rasterBlocking, stageLookFrame } from './stage.js';
import { cleanStageScene, lookSize, stageTier } from '../src/stage.js';
import { appTier, isRenderTier, parseTier, tierSizeOf, type TierApp } from '../src/renderTier.js';
import { currentTier, setTier, tierState } from './renderTier.js';
import { MIN_PASSWORD, installJudge, type JudgeState } from './judge.js';

if (config.judge.on && config.judge.password.length < MIN_PASSWORD) {
  console.error(`OPENFIELD_JUDGE is on, so OPENFIELD_JUDGE_PASSWORD must be set (${MIN_PASSWORD} characters or more). Not starting.`);
  process.exit(1);
}

const app = Fastify({ bodyLimit: 64 * 1024 * 1024 });
await app.register(websocket);
// Nexora : connexion unique au portail (OIDC). Sans configuration, poste local à compte unique.
const configAuth = configAuthDepuisEnv();
if (configAuth) monterAuthentification(app, configAuth);
/** Facturation des rendus : API du site avec la clé de l'organisation connectée ; aucune en poste local. */
function facturationPour(org: string | null | undefined) {
  if (!configAuth || !org) return null;
  return facturationSite(configAuth.siteUrl, () => accesOrganisation(org)?.key);
}
const facturationCourante = () => facturationPour(compteCourant()?.organisationId);
/** Valide ou libère les crédits des prises terminées (appelé par la réconciliation, idempotent). */
async function solderCredits() {
  for (const t of takes.list(null, 300)) {
    const s = JSON.parse(t.settings);
    const action = actionFacturation({ status: t.status, credits: s.nexoraCredits });
    if (!action) continue;
    // Plan d'un film encore en tournage : le film peut le relancer et lui transférer sa réservation ; on attend.
    if (action === 'liberer' && s.nexoraFilm && ['queued', 'rendering'].includes(takes.get(Number(s.nexoraFilm))?.status ?? '')) continue;
    const fac = facturationPour(t.organisation_id);
    if (!fac || !accesOrganisation(t.organisation_id)) continue; // en attente d'une reconnexion de l'organisation
    try {
      if (action === 'valider') await fac.valider(s.nexoraCredits.reservationId, s.nexoraCredits.credits);
      else await fac.liberer(s.nexoraCredits.reservationId);
      takes.patchSettings(t.id, { nexoraCredits: { ...s.nexoraCredits, etat: action === 'valider' ? 'validee' : 'liberee' } });
    } catch (e) {
      console.error(`[nexora] crédits de la prise ${t.id} :`, e instanceof Error ? e.message : e);
    }
  }
}
/** Compte l'espace des prises terminées (réconciliation, idempotent) ; marque l'organisation pleine si refus. */
async function compterEspace() {
  if (!configAuth) return;
  for (const t of takes.list(null, 300)) {
    const s = JSON.parse(t.settings);
    if (actionEspace({ status: t.status, output_path: t.output_path, espace: s.nexoraEspace }) !== 'compter') continue;
    const cle = accesOrganisation(t.organisation_id)?.key;
    if (!cle || !existsSync(t.output_path!)) continue;
    const octets = statSync(t.output_path!).size;
    try {
      const r = await espaceSite(configAuth.siteUrl, () => cle).enregistrer(octets);
      takes.patchSettings(t.id, { nexoraEspace: { octets, etat: r.ok ? 'compte' : 'depasse' } });
      marquerPlein(t.organisation_id, !r.ok);
    } catch (e) {
      console.error(`[nexora] espace de la prise ${t.id} :`, e instanceof Error ? e.message : e);
    }
  }
}
/** LLM de la requête : clé de l'organisation connectée, ou configuration du poste. */
const llmCourant = () => clientLlmCourant(compteCourant(), accesOrganisation);

/**
 * Client du réalisateur (rôle « redaction ») : palier du rôle (Expert par défaut, recherche/25 : 8,0/10 contre 5,4 pour
 * l'ancien réécrivain, 0,0055 $ la demande), secours sur le palier suivant puis sur Équilibré, chaque jeton au grand
 * livre. Sans clé de palier sur le poste : le LLM du poste. `rel` : relevé d'un run facturé (sinon un relevé au livre).
 */
function llmRedaction(rel?: Releve): ClientLlm | null {
  const p = palierDuRole('redaction');
  if (!p) return llmCourant();
  const compte = compteCourant();
  const releve = rel ?? new Releve({ run: randomUUID(), tache: 'realisation', utilisateur: compte?.utilisateurId, organisation: compte?.organisationId }, 0.1, livreUsage);
  const secours = [palierSuivant(p), p === 'equilibre' ? null : 'equilibre' as Palier].filter((x): x is Palier => !!x && x !== p);
  return clientAvecSecours([p, ...new Set(secours)].map((x) => clientPalier(x, { surveillant: releve, autoriserRepli: true })));
}

let judgeState: (() => JudgeState) | undefined;
if (config.judge.on) {
  // Judge mode: a password on every route replaces the loopback-only rule.
  judgeState = installJudge(app, { password: config.judge.password, cap: config.judge.cap, usageFile: join(config.dataDir, 'judge-usage.json') });
} else {
  // No auth by design (loopback only), so refuse requests whose Host is not this
  // machine. That stops a web page from reaching the API through DNS rebinding.
  const LOCAL_HOSTS = new Set(['127.0.0.1', 'localhost', '[::1]', config.host]);
  // and refuse requests a page on another site sends here: browsers attach Origin to those,
  // and a form or text/plain POST would otherwise reach a handler without a preflight
  const localOrigin = (o: string) => {
    try { const u = new URL(o); return LOCAL_HOSTS.has(u.hostname.toLowerCase()) || LOCAL_HOSTS.has(`[${u.hostname}]`); } catch { return false; }
  };
  app.addHook('onRequest', async (req, reply) => {
    const host = (req.headers.host ?? '').replace(/:\d+$/, '').toLowerCase();
    if (!LOCAL_HOSTS.has(host)) return reply.code(403).send({ error: 'OpenField only answers on this machine' });
    const origin = req.headers.origin;
    if (origin && origin !== 'null' && !localOrigin(origin)) return reply.code(403).send({ error: 'OpenField only answers its own pages' });
    if (origin === 'null' && req.method !== 'GET') return reply.code(403).send({ error: 'OpenField only answers its own pages' });
  });
}

/** Settings keys only the server writes. A request body must never set them: some are file paths we later serve. */
const SERVER_KEYS = ['alphaPath', 'hdr', 'hdrTag', 'seam', 'seamFix', 'output_path', 'outputPath', 'nexoraCredits'] as const;
function stripServerKeys(b: any): void {
  if (b && typeof b === 'object') for (const k of SERVER_KEYS) delete b[k];
}

/** Serve a side file only if it sits in the same folder as the take's own output. */
function besideOutput(outputPath: string | null | undefined, file: string | undefined): string | undefined {
  if (!outputPath || !file || !existsSync(file) || !existsSync(outputPath)) return undefined;
  return dirname(realpathSync(file)) === dirname(realpathSync(outputPath)) ? file : undefined;
}

// ---------- live relay ----------

/** Navigateurs connectés au direct, avec l'organisation de leur session (Nexora : rien ne passe d'une organisation à l'autre). */
const browsers = new Map<WebSocket, string>();
/** Organisation concernée par un message du direct, ou null pour un message sans donnée de client (file d'attente). */
function orgDuMessage(msg: any): string | null {
  if (msg?.take?.organisation_id) return msg.take.organisation_id;
  if (typeof msg?.promptId === 'string') return takes.byPrompt(msg.promptId)?.organisation_id ?? '?';
  return null;
}
let derniersDestinataires: WebSocket[] = [];
function broadcast(msg: unknown) {
  const s = JSON.stringify(msg);
  const org = orgDuMessage(msg);
  derniersDestinataires = [...browsers].filter(([, o]) => org === null || o === org).map(([ws]) => ws);
  for (const ws of derniersDestinataires) if (ws.readyState === 1) ws.send(s);
}
/** Image d'aperçu : elle suit son message « preview », donc mêmes destinataires. */
function broadcastBinary(buf: Buffer) {
  for (const ws of derniersDestinataires) if (ws.readyState === 1) ws.send(buf);
}

let lastProgressAt = 0;

eng.engine.on('progress', (p: { jobId: string; value: number; step: number | null; steps: number | null }) => {
  const now = Date.now();
  const step = p.step ?? Math.round(p.value * 100);
  const max = p.steps ?? 100;
  // Measure seconds/step for ETA (ignore first step: includes model load)
  if (lastProgressAt && p.step && p.step > 1) {
    const t = takes.byPrompt(p.jobId);
    if (t) {
      const s = JSON.parse(t.settings);
      const key = `${t.kind}|${s.width}x${s.height}|${s.lengthFrames ?? 0}`;
      const prev = speed.get(key);
      const sps = (now - lastProgressAt) / 1000;
      speed.set(key, prev ? prev * 0.7 + sps * 0.3 : sps);
    }
  }
  lastProgressAt = now;
  broadcast({ type: 'progress', promptId: p.jobId, value: step, max });
});

eng.engine.on('preview', ({ jobId, data }: { jobId: string; data: Buffer }) => {
  // The socket keeps order, so the browser pairs the next binary frame with this job.
  broadcast({ type: 'preview', promptId: jobId });
  broadcastBinary(data);
});

eng.engine.on('status', ({ jobId, status }: { jobId: string; status: string }) => {
  // the engine started this job: until then a take is waiting in the engine's line
  if (status === 'running') broadcast({ type: 'started', promptId: jobId });
  broadcast({ type: 'queue', remaining: takes.active().length });
});

eng.engine.on('finished', ({ jobId }: { jobId: string }) => void onPromptFinished(jobId));

async function onPromptFinished(promptId: string) {
  const take = takes.byPrompt(promptId);
  // A stopped take stays stopped: its job's late end (canceled, expired) is not news.
  if (!take || take.status === 'done' || take.status === 'stopped') return;
  try {
    const h = await eng.result(promptId);
    if (!h.done) return;
    if (!h.success || !h.output) {
      takes.fail(take.id, h.error || 'No output produced', !!h.canceled);
      broadcast({ type: 'take', take: takes.get(take.id) });
      nextInScene(take);
      return;
    }
    const out = { filename: h.output.name };
    const data = h.output.data;
    const s = JSON.parse(take.settings);
    const project = take.project_id ? projects.get(take.project_id) : undefined;
    const folder = project?.folder || config.outputDir;
    const ext = extname(out.filename).slice(1) || (take.kind === 'still' ? 'png' : 'mp4');
    // An upscale keeps its source's name: <shot>_<source seed>_UP.
    const path = await saveToProject(folder, s.shotName || 'shot', s.fileSeed ?? s.seed ?? 0, data, {
      ext,
      upres: take.kind === 'upres' || s.app === 'upscale',
      suffix: s.app === 'seam' ? '_LOOP' : s.app === 'hdr' ? '_HDR' : undefined,
    });
    await saveSidecars(path, h.extras ?? []);
    let shown = path;
    if (s.app === 'cutout' && ext === 'mov') {
      // ProRes 4444 is the deliverable; browsers cannot play it, so the take
      // shows a preview of the cut out over a checkerboard.
      shown = await checkerPreview(path);
      takes.patchSettings(take.id, { alphaPath: path });
    }
    takes.finish(take.id, shown, h.renderSeconds);
    broadcast({ type: 'take', take: takes.get(take.id) });
    nextInScene(take);
    // Seam check for loops (and the next fix if it is still visible), HDR downloads.
    void afterRender(take.id).catch((e) => console.error(`[openfield] after take ${take.id}:`, e instanceof Error ? e.message : e));
    // Voice transcript for videos, best-effort in the background
    if (take.kind !== 'still' && take.kind !== 'object') {
      transcribe(path).then((t) => {
        if (t) {
          takes.setTranscript(take.id, t);
          broadcast({ type: 'take', take: takes.get(take.id) });
        }
      });
    }
  } catch (e) {
    takes.fail(take.id, e instanceof Error ? e.message : 'post-processing failed');
    broadcast({ type: 'take', take: takes.get(take.id) });
    nextInScene(take);
  }
}

/**
 * Side outputs saved next to a take's file: an object's turntable
 * (<file>.turntable.mp4, also its poster) and its isolated subject
 * (<file>.subject.png). Best effort; the take stands without them.
 */
async function saveSidecars(path: string, extras: NonNullable<eng.JobResult['extras']>) {
  const { writeFile } = await import('fs/promises');
  for (const x of extras) {
    const ext = x.nodeId === 'turntable' ? 'mp4' : x.nodeId === 'subject' ? 'png' : null;
    if (!ext) continue;
    await writeFile(`${path}.${x.nodeId}.${ext}`, x.data).catch((e) => console.error(`[openfield] could not save the ${x.nodeId} of ${path}:`, e instanceof Error ? e.message : e));
  }
}

/** A Director scene shot (or its hero frame) settled: move its scene on. */
function nextInScene(take: { settings: string }) {
  const s = JSON.parse(take.settings);
  const cut = Number(s.sceneOf);
  if (cut) void advance(cut);
  const film = Number(s.nexoraFilm);
  if (film) void avancerFilm(film);
}

app.get('/live', { websocket: true }, (conn) => {
  browsers.set(conn, compteCourant()?.organisationId ?? 'local');
  conn.on('close', () => browsers.delete(conn));
});

// ---------- API ----------

app.get('/api/status', async () => {
  const [st, api, renderTier] = await Promise.all([comfy.getStatus(), eng.apiUp(), tierState()]);
  return {
    ...st,
    // Cloud target: the local ComfyUI server is irrelevant, the v2 API is the engine.
    up: eng.isLocal() ? st.up && api : api,
    api,
    target: eng.isLocal() ? 'local' : 'cloud',
    active: takes.active(),
    canLaunch: comfy.canLaunchEngine(),
    comfyUrl: config.comfyUrl,
    renderTier,
    judge: judgeState?.(),
  };
});

/** Machine-wide settings. renderTier: the video render size; source says where it came from. */
app.get('/api/settings', async () => ({ renderTier: await tierState() }));
app.put('/api/settings', async (req, reply) => {
  const b = (req.body ?? {}) as { renderTier?: unknown };
  if ('renderTier' in b) {
    if (b.renderTier !== null && !isRenderTier(b.renderTier)) return reply.code(400).send({ error: 'renderTier is 480p, 720p, 1080p, or null for the default' });
    setTier(b.renderTier);
  }
  return { renderTier: await tierState() };
});

app.post('/api/upload', async (req, reply) => {
  const { name, dataUrl } = req.body as { name: string; dataUrl: string };
  const m = /^data:([^;]+);base64,([\s\S]*)$/.exec(dataUrl || '');
  if (!m) return reply.code(400).send({ error: 'dataUrl required' });
  const sub = (m[1].split('/')[1] || 'png').replace(/[^a-z0-9-]/gi, '');
  // Audio and video MIME subtypes are not file extensions; LoadAudio and the
  // video loaders pick a decoder by extension.
  const ext = ({ mpeg: 'mp3', 'x-wav': 'wav', wave: 'wav', 'x-m4a': 'm4a', mp4a: 'm4a', quicktime: 'mov', 'x-flac': 'flac', 'gltf-binary': 'glb' } as Record<string, string>)[sub] ?? sub.replace(/-/g, '');
  const stored = await eng.uploadInput(`openfield_${Date.now()}_${safeShotName(name)}.${ext}`, Buffer.from(m[2], 'base64'), m[1]);
  return { name: stored };
});

// ---------- film it on your phone ----------
// The phone never talks to this server. phone.ts runs its own single-use LAN
// listener; we hand it a place to put the clip and relay its state on /live.

app.post('/api/phone/start', async (_req, reply) => {
  try {
    const info = await openPhoneSession({
      port: config.phonePort,
      host: config.phoneHost,
      onClip: async (clip) => ({
        token: await eng.uploadInput(`openfield_phone_${Date.now()}_${safeShotName(clip.name.replace(/\.[^.]+$/, ''))}.${clip.ext}`, clip.data, clip.mime),
        name: clip.name,
        bytes: clip.data.length,
      }),
      onState: (id, st) => broadcast({ type: 'phone', id, ...st }),
    });
    return info;
  } catch (e) {
    return reply.code(503).send({ error: e instanceof Error ? e.message : 'could not open the phone link' });
  }
});

app.post('/api/phone/stop', async (req) => {
  const id = (req.body as { id?: string } | undefined)?.id;
  if (!id || phoneSession()?.id === id) closePhoneSession('cancelled');
  return { ok: true };
});

app.get('/api/phone', async () => ({ session: phoneSession() }));

interface Built {
  graph: Record<string, unknown>;
  kind: string;
  /** Server-measured facts that replace what the client sent (sizes, frame counts). */
  settings?: Record<string, unknown>;
  parent?: number;
}

/** What the continue tools need to know about an uploaded clip or sound file. */
interface Probe { seconds: number; frames: number; w: number; h: number; audio: boolean; video: boolean }
const probes = new Map<string, Probe>();
async function probeInput(token: string): Promise<Probe> {
  const hit = probes.get(token);
  if (hit) return hit;
  const inp = await eng.readInput(token);
  if (!inp) throw new Error('That input is no longer on this machine. Add it again.');
  const { mkdtemp, writeFile, rm } = await import('fs/promises');
  const { tmpdir } = await import('os');
  const dir = await mkdtemp(join(tmpdir(), 'openfield-probe-'));
  const file = join(dir, `in${extname(inp.name) || '.bin'}`);
  try {
    await writeFile(file, inp.data);
    const ffprobe = config.ffprobeBin;
    const { execFile } = await import('child_process');
    const out = await new Promise<string>((res, rej) =>
      execFile(ffprobe, ['-v', 'error', '-show_entries', 'stream=codec_type,width,height,duration:format=duration', '-of', 'json', file], (e, o) => (e ? rej(e) : res(o))),
    );
    const d = JSON.parse(out);
    const streams: any[] = d.streams ?? [];
    const v = streams.find((x) => x.codec_type === 'video');
    const seconds = Number(v?.duration) || Number(d.format?.duration) || 0;
    const p: Probe = {
      seconds,
      frames: Math.floor(seconds * LTX25_FPS + 1e-6),
      w: v?.width ?? 0,
      h: v?.height ?? 0,
      audio: streams.some((x) => x.codec_type === 'audio'),
      video: !!v,
    };
    probes.set(token, p);
    return p;
  } finally {
    await rm(dir, { recursive: true, force: true });
  }
}

/**
 * A request's frame: its own width and height when it sends both, else the
 * render tier (Setup, OPENFIELD_RENDER_TIER or the GPU; a `resolution` field
 * overrides it for this request) at the source's shape, held at the app's
 * largest safe size (APP_MAX_TIER). 64-aligned for two-stage renders and
 * IC-LoRA guides, 32 for the single-stage continue tools.
 */
async function frameFor(b: any, app: TierApp, src: { w?: number; h?: number } | null | undefined, align: 32 | 64): Promise<{ width: number; height: number }> {
  const w = Number(b.width), h = Number(b.height);
  if (w > 0 && h > 0) return { width: w, height: h };
  const s = tierSizeOf(appTier(app, parseTier(b.resolution) ?? (await currentTier())), src?.w, src?.h, align);
  return { width: s.w, height: s.h };
}

/** Pixel size of an uploaded still, or null. */
async function stillDims(token: unknown): Promise<{ w: number; h: number } | null> {
  if (typeof token !== 'string' || !token) return null;
  const inp = await eng.readInput(token).catch(() => null);
  return inp ? imageDims(inp.data) : null;
}

/** Frame size of an uploaded clip, or null when it cannot be read. */
async function clipDims(token: unknown): Promise<{ w: number; h: number } | null> {
  if (typeof token !== 'string' || !token) return null;
  const p = await probeInput(token).catch(() => null);
  return p?.w && p.h ? { w: p.w, h: p.h } : null;
}

/**
 * Edit: Qwen-Image-Edit on 1 to 3 input images. The output keeps the first
 * image's aspect (or, for Expand, takes the target aspect), so its size is read
 * from the uploaded file's header. Returns the size so the take records it.
 */
async function editGraph(b: any, seed: number) {
  const images: string[] = Array.isArray(b.images) ? b.images.filter((x: unknown) => typeof x === 'string' && x).slice(0, 3) : [];
  if (!images.length) throw new Error('Edit needs an image');
  if (typeof b.instruction !== 'string' || !b.instruction.trim()) throw new Error('Edit needs an instruction');
  const src = await eng.readInput(images[0]);
  const dims = src ? imageDims(src.data) : null;
  if (!dims) throw new Error('Could not read the size of the image being edited (use PNG, JPEG or WebP)');
  const mp = Math.max(0.25, Math.min(2, Number(b.mp) || 1));
  const quality = b.quality === 'draft' ? 'draft' : 'quality';
  const steps = Number.isFinite(b.steps) ? Math.max(4, Math.min(50, Math.round(b.steps))) : undefined;
  // Optional LoRAs are used only when the engine lists them, so an install
  // without them still renders (on the base-model Lightning, without angles).
  const have = new Set(await comfy.comboOptions('LoraLoaderModelOnly', 'lora_name'));
  const lightning = have.has(EDIT_LIGHTNING_2509) ? EDIT_LIGHTNING_2509 : EDIT_LIGHTNING;
  const loras = (b.mode === 'angle' || b.mode === 'pushin') && have.has(EDIT_ANGLES_LORA) ? [{ name: EDIT_ANGLES_LORA, strength: 1 }] : [];
  const common = { images, instruction: b.instruction, seed, quality, steps, lightning, loras } as const;
  if (b.expand) {
    const aspect = Number(b.expand.aspect) || dims.w / dims.h;
    const lay = expandLayout(dims.w, dims.h, aspect, Number(b.expand.zoom) || 1, mp);
    return {
      graph: buildEditGraph({ ...common, width: lay.width, height: lay.height, pad: lay.pad }),
      // Where the original sits on the new canvas, for the before/after view.
      size: { width: lay.width, height: lay.height, inner: { x: lay.pad.left, y: lay.pad.top, w: lay.pad.inner.width, h: lay.pad.inner.height } },
    };
  }
  const size = editSize(dims.w, dims.h, mp);
  return {
    graph: buildEditGraph({
      ...common, width: size.width, height: size.height,
      mask: typeof b.mask === 'string' && b.mask ? b.mask : undefined,
    }),
    size,
  };
}

/**
 * A finished take as an input file: its output uploaded as an asset, with the
 * names the new take inherits. Shared by Cut out (and anything else that
 * starts from a take by id).
 */
async function stageTake(id: number): Promise<{ file: string; localPath: string; parent: number; shotName: string; fileSeed?: number }> {
  const src = takes.get(id);
  if (!src?.output_path) throw new Error(`take ${id} not found or unfinished`);
  if (!existsSync(src.output_path)) throw new Error(`take ${src.id}'s file is no longer on disk: ${src.output_path}`);
  const ext = extname(src.output_path).toLowerCase() || '.mp4';
  const data = await import('fs/promises').then((fs) => fs.readFile(src.output_path!));
  const file = await eng.uploadInput(`openfield_take_${src.id}${ext}`, data, ext === '.png' ? 'image/png' : 'video/mp4');
  const ss = JSON.parse(src.settings);
  return { file, localPath: src.output_path, parent: src.id, shotName: ss.shotName || src.shot_name, fileSeed: ss.fileSeed ?? ss.seed };
}

/**
 * Cut out (Remove background): a still or a clip, from a take or an upload.
 * Sizes and frame counts come from the real file.
 */
async function cutoutGraph(b: any): Promise<Built> {
  const background: CutoutBackground = ['color', 'blur', 'image'].includes(b.background) ? b.background : 'transparent';
  const bg = {
    background,
    color: typeof b.color === 'string' ? b.color : undefined,
    backgroundImage: background === 'image' ? (typeof b.backgroundImage === 'string' && b.backgroundImage ? b.backgroundImage : undefined) : undefined,
  };
  if (background === 'image' && !bg.backgroundImage) throw new Error('A new background needs a picture');
  let file: string;
  let localPath: string | null;
  let parent: number | undefined;
  let named: { shotName?: string; fileSeed?: number } = {};
  if (b.sourceTake) {
    const st = await stageTake(Number(b.sourceTake));
    ({ file, localPath, parent } = st);
    named = { shotName: `${st.shotName}_cutout`.slice(0, 60), fileSeed: st.fileSeed };
  } else {
    file = typeof b.image === 'string' && b.image ? b.image : typeof b.sourceVideo === 'string' ? b.sourceVideo : '';
    if (!file) throw new Error('Remove background needs a still or a clip');
    localPath = eng.inputPath(file);
    if (!localPath) throw new Error('the uploaded source is gone; add it again');
  }
  const m = await probeMedia(localPath);
  const common = { app: 'cutout', background, color: bg.color, backgroundImage: bg.backgroundImage, sourceKind: m.kind, sourceTake: parent, sourceWidth: m.w, sourceHeight: m.h, ...named };
  if (m.kind === 'image') {
    return {
      kind: 'still', parent,
      graph: buildCutoutStillGraph({ image: file, width: m.w, height: m.h, ...bg }),
      settings: { ...common, mode: 'matte', image: file, width: m.w, height: m.h },
    };
  }
  const mode: CutoutMethod = b.mode === 'hybrid' || b.mode === 'track' ? b.mode : 'matte';
  const size = cutoutSize(m.w, m.h);
  const cap = Math.floor(Math.min(CUTOUT_MAX_SECONDS, Number(b.seconds) || CUTOUT_MAX_SECONDS) * m.fps);
  const frames = Math.max(1, Math.min(m.frames || cap, cap));
  const withAudio = !!b.withAudio && m.audio;
  return {
    kind: 'video', parent,
    graph: buildCutoutVideoGraph({
      sourceVideo: file, width: size.w, height: size.h, frames, fps: m.fps, method: mode,
      subject: typeof b.subject === 'string' ? b.subject : undefined, withAudio, ...bg,
    }),
    settings: {
      ...common, mode, subject: b.subject || undefined, sourceVideo: file, width: size.w, height: size.h, fps: m.fps, frames,
      seconds: Math.round((frames / m.fps) * 10) / 10, withAudio,
    },
  };
}

/** The Lightning LoRA for 8-step edits: the 2509 one when ComfyUI lists it. */
async function editLightning(): Promise<string> {
  const have = new Set(await comfy.comboOptions('LoraLoaderModelOnly', 'lora_name'));
  return have.has(EDIT_LIGHTNING_2509) ? EDIT_LIGHTNING_2509 : EDIT_LIGHTNING;
}

/**
 * Restyle and Object swap (Mirror): an edited first frame carried through the
 * clip's motion. The page compiles the edit instruction and the shot prompt;
 * they are rebuilt here from the style and words when a caller leaves them out.
 */
async function motionEditGraph(b: any, seed: number): Promise<Built> {
  if (!b.sourceVideo) throw new Error(`${b.kind === 'swap' ? 'Object swap' : 'Restyle'} needs a source clip`);
  const quality = b.quality === 'quality' || (b.kind === 'swap' && b.quality !== 'draft') ? 'quality' : 'draft';
  const lightning = await editLightning();
  const { width, height } = await frameFor(b, b.kind === 'swap' ? 'swap' : 'restyle', await clipDims(b.sourceVideo), 64);
  if (b.kind === 'restyle') {
    const look = restyleLook(b.style, String(b.text ?? ''));
    if (!look && !b.instruction) throw new Error('Pick a style or describe the look');
    return {
      kind: 'video',
      graph: buildRestyleGraph({
        sourceVideo: b.sourceVideo,
        instruction: typeof b.instruction === 'string' && b.instruction ? b.instruction : restyleInstruction(look),
        prompt: typeof b.prompt === 'string' && b.prompt ? b.prompt : restylePrompt(look),
        negative: typeof b.negative === 'string' && b.negative ? b.negative : undefined,
        width, height, seconds: Math.max(1, Math.min(12, Number(b.seconds) || 5)), seed,
        control: b.control === 'edges' ? 'edges' : 'depth',
        guideStrength: Number.isFinite(b.guideStrength) ? b.guideStrength : undefined,
        lightning, quality, withAudio: !!b.withAudio,
      }),
      settings: { width, height },
    };
  }
  const target = String(b.target ?? '').trim();
  const replacement = String(b.replacement ?? '').trim();
  if (!target) throw new Error('Say what to replace');
  if (!replacement && !b.reference) throw new Error('Say what it becomes, or add a picture of it');
  const point = b.point && Number.isFinite(b.point.x) && Number.isFinite(b.point.y)
    ? { x: Math.max(0, Math.min(1, Number(b.point.x))), y: Math.max(0, Math.min(1, Number(b.point.y))) } : undefined;
  return {
    kind: 'video',
    graph: buildSwapGraph({
      sourceVideo: b.sourceVideo, target, point, replacement: replacement || 'the object in image 2',
      reference: typeof b.reference === 'string' && b.reference ? b.reference : undefined,
      prompt: typeof b.prompt === 'string' && b.prompt ? b.prompt : swapPrompt(replacement || 'the new object'),
      width, height, seconds: Math.max(1, Math.min(8, Number(b.seconds) || 4)), seed, lightning, quality,
    }),
    settings: { width, height },
  };
}

async function graphFor(b: any, seed: number): Promise<Built> {
  let graph: Record<string, unknown>;
  let kind: string;

  // Nexora : bande originale MiniMax Music 3 (recette « music3 », routée vers le moteur qui la porte).
  if (b.kind === 'musique') {
    return { kind: 'audio', graph: buildMusic3Graph({ description: String(b.description ?? ''), paroles: String(b.paroles ?? ''), dureeS: Number(b.dureeS) || 30, seed }) };
  }
  if (b.kind === 'upscale') return upscaleGraph(b, seed);
  if (b.kind === 'cutout') return cutoutGraph(b);
  if (b.kind === 'restyle' || b.kind === 'swap') return motionEditGraph(b, seed);
  if (b.kind === 'seam') return seamGraph(b, seed);
  if (b.kind === 'hdr') return hdrGraph(b, seed);
  if (b.kind === 'stage-look') return stageLookGraph(b, seed);
  if (b.kind === 'stage') return stageShotGraph(b, seed);
  if (b.kind === 'object') return objectGraph(b, seed);

  // Cast engines (resolveCast decided them from the @mentions).
  if (b.castEngine === 'sheet' && b.castSheet) {
    return {
      kind: 'video',
      graph: buildCastVideoGraph({
        prompt: b.prompt,
        negative: typeof b.negative === 'string' && b.negative ? b.negative : undefined,
        layout: b.castSheet,
        seconds: Math.max(1, Math.min(10, Number(b.seconds) || 5)),
        seed,
        withAudio: !!b.withAudio,
        loras: await pickLoras(b.loras, 'ltx', 'Video'),
      }),
    };
  }
  if (b.kind === 'still' && b.castEngine === 'compose') {
    const images: string[] = (Array.isArray(b.castImages) ? b.castImages : []).slice(0, 3);
    if (!images.length) throw new Error('No cast pictures to compose from');
    const have = new Set(await comfy.comboOptions('LoraLoaderModelOnly', 'lora_name'));
    const snap = (n: number) => Math.max(256, Math.round(n / 16) * 16);
    // Qwen-Image-Edit is happiest near 1 MP; keep the requested aspect.
    const ratio = (Number(b.width) || 1328) / (Number(b.height) || 752);
    const h = Math.sqrt(Math.min(1.3e6, (Number(b.width) || 1328) * (Number(b.height) || 752)) / ratio);
    const size = { width: snap(h * ratio), height: snap(h) };
    return {
      kind: 'still',
      graph: buildEditGraph({
        images, instruction: String(b.castInstruction ?? b.prompt ?? ''), ...size, seed,
        quality: b.quality === 'draft' ? 'draft' : 'quality',
        lightning: have.has(EDIT_LIGHTNING_2509) ? EDIT_LIGHTNING_2509 : EDIT_LIGHTNING,
        compose: true,
        loras: await pickLoras(b.loras, 'qwen', 'Image'),
      }),
      settings: size,
    };
  }

  if (b.kind === 'edit') {
    const e = await editGraph(b, seed);
    return { graph: e.graph, kind: 'still', settings: e.size };
  }

  if (b.kind === 'extend') {
    if (!b.sourceVideo) throw new Error('Extend needs a clip');
    const src = await probeInput(b.sourceVideo);
    if (!src.video || src.frames < 17) throw new Error('Extend needs a video clip of at least 1 second');
    const size = await frameFor(b, 'extend', src, 32);
    return {
      kind: 'video',
      graph: buildExtendGraph({
        prompt: b.prompt || '',
        negative: typeof b.negative === 'string' && b.negative ? b.negative : undefined,
        sourceVideo: b.sourceVideo,
        sourceFrames: Math.min(src.frames, 20 * LTX25_FPS),
        sourceHasAudio: src.audio,
        ...size,
        seconds: Math.max(1, Math.min(10, Number(b.seconds) || 3)),
        direction: b.direction === 'backward' ? 'backward' : 'forward',
        seed,
        withAudio: b.withAudio !== false,
      }),
      settings: size,
    };
  }
  if (b.kind === 'transition') {
    const end = async (video?: string, image?: string) => {
      if (video) {
        const p = await probeInput(video);
        return { e: { file: video, kind: 'video' as const, frames: Math.min(p.frames, 20 * LTX25_FPS), hasAudio: p.audio }, p };
      }
      if (image) return { e: { file: image, kind: 'image' as const } };
      throw new Error('Transition needs a take on each side');
    };
    const A = await end(b.startVideo, b.startImage);
    const B = await end(b.endVideo, b.endImage);
    const size = await frameFor(b, 'transition', A.p ?? B.p ?? (await stillDims(b.startImage)) ?? (await stillDims(b.endImage)), 32);
    return {
      kind: 'video',
      graph: buildTransitionGraph({
        // The page compiles the style chip and the user's words into the prompt.
        prompt: b.prompt || 'One continuous shot. The first scene fluidly morphs into the second without a cut.',
        a: A.e, b: B.e,
        ...size,
        seconds: Math.max(1, Math.min(6, Number(b.seconds) || 2)),
        seed,
        withAudio: b.withAudio ?? !!(A.e.hasAudio || (B.e as any).hasAudio),
      }),
      settings: size,
    };
  }
  if (b.kind === 'speak') {
    if (!b.startImage) throw new Error('Speak needs a face or a start frame');
    if (!b.audio) throw new Error('Speak needs a sound file');
    const a = await probeInput(b.audio);
    const start = Math.max(0, Number(b.audioStart) || 0);
    const left = Math.max(1, a.seconds - start);
    const size = await frameFor(b, 'speak', await stillDims(b.startImage), 64);
    return {
      kind: 'video',
      graph: buildSpeakGraph({
        prompt: b.prompt || 'A person speaks to the camera.',
        negative: typeof b.negative === 'string' && b.negative ? b.negative : undefined,
        image: b.startImage,
        audio: b.audio,
        audioStart: start,
        seconds: Math.max(1, Math.min(10, Number(b.seconds) || left, left)),
        ...size,
        seed,
      }),
      settings: size,
    };
  }
  if (b.kind === 'sound') {
    if (!b.sourceVideo) throw new Error('Add sound needs a clip');
    const src = await probeInput(b.sourceVideo);
    if (!src.video || src.frames < 9) throw new Error('Add sound needs a video clip');
    // The picture is only read, never redrawn, so encode it small: the sound comes out the same.
    const ratio = (src.w || 16) / (src.h || 9);
    const h = Math.sqrt(0.37e6 / ratio);
    return {
      kind: 'video',
      graph: buildSoundGraph({
        prompt: b.prompt || 'Natural ambient sound that matches the scene.',
        negative: typeof b.negative === 'string' && b.negative ? b.negative : undefined,
        sourceVideo: b.sourceVideo,
        sourceFrames: Math.min(src.frames, 20 * LTX25_FPS),
        width: h * ratio,
        height: h,
        seed,
      }),
    };
  }

  let size: { width: number; height: number } | undefined;
  if (b.kind === 'effect') {
    kind = 'video';
    const fx = effectById(b.effect);
    size = await frameFor(b, 'effects', fx?.input === 'still' ? await stillDims(b.startImage) : await clipDims(b.sourceVideo), 64);
    graph = buildEffectGraph({ ...b, ...size }, seed);
  } else if (b.kind === 'reshoot' || b.kind === 'reshoot-preview') {
    kind = 'video';
    if (!b.sourceVideo) throw new Error('Reshoot needs a source clip');
    size = await frameFor(b, 'reshoot', await clipDims(b.sourceVideo), 32);
    const common = {
      sourceVideo: b.sourceVideo,
      ...size,
      seconds: Math.max(1, Math.min(8, b.seconds || 4)),
      azimuth: Number(b.azimuth) || 0,
      elevation: Number(b.elevation) || 0,
      keyframes: Array.isArray(b.keyframes) ? b.keyframes : undefined,
      pivotDepth: Number.isFinite(b.pivotDepth) ? b.pivotDepth : undefined,
    };
    graph = b.kind === 'reshoot-preview'
      ? buildReshootWarpPreviewGraph(common)
      : buildReshootGraph({ ...common, prompt: b.prompt || '', seed, withAudio: !!b.withAudio });
  } else if (b.kind === 'mirror') {
    kind = 'video';
    if (!b.sourceVideo) throw new Error('Mirror needs a source clip');
    size = await frameFor(b, 'mirror', await clipDims(b.sourceVideo), 64);
    graph = buildMirrorGraph({
      prompt: b.prompt,
      negative: typeof b.negative === 'string' && b.negative ? b.negative : undefined,
      sourceVideo: b.sourceVideo,
      firstFrame: b.startImage || undefined,
      ...size,
      seconds: Math.max(1, Math.min(12, b.seconds || 5)),
      seed,
      control: b.control === 'depth' || b.control === 'edges' ? b.control : 'pose',
      guideStrength: Number.isFinite(b.guideStrength) ? b.guideStrength : undefined,
      withAudio: !!b.withAudio,
    });
  } else if (b.kind === 'still') {
    kind = 'still';
    const flux2 = b.model === 'flux2';
    graph = buildStillsGraph({
      model: flux2 ? 'flux2' : b.model === 'qwen21' ? 'qwen21' : 'qwen',
      quality: b.quality === 'draft' ? 'draft' : 'quality',
      prompt: b.prompt,
      negative: typeof b.negative === 'string' && b.negative ? b.negative : undefined,
      width: b.width || 1328,
      height: b.height || 752,
      seed,
      loras: await pickLoras(b.loras, flux2 ? 'flux2' : 'qwen', 'Image'),
      // FLUX.2 references: your own pictures first, then the cast's (resolveCast).
      refImages: flux2 ? flux2Refs(b) : undefined,
    });
  } else if (b.videoModel === 'ltx25') {
    kind = 'video';
    // LTX-2.5 loads its transformer / encoder / VAEs by fixed name, so there is
    // no checkpoint to pick. Supplying both a start and an end image switches
    // the builder to flf2v; passing the same file for both closes a loop.
    size = await frameFor(b, 'video', await stillDims(b.startImage), 64);
    graph = buildLtx25Graph({
      prompt: b.prompt,
      negative: typeof b.negative === 'string' && b.negative ? b.negative : undefined,
      ...size,
      seconds: Math.max(1, Math.min(20, b.seconds || 5)),
      seed,
      fps: b.fps || LTX25_FPS,
      startImage: b.startImage,
      endImage: b.endImage,
      withAudio: !!b.withAudio,
      videoCfg: b.videoCfg,
      audioCfg: b.audioCfg,
      transformer: typeof b.checkpoint === 'string' && b.checkpoint ? b.checkpoint : undefined,
      loras: (await pickLoras(b.loras, 'ltx', 'Video')).map((l) => ({ file: l.name, strength: l.strength })),
    });
  } else if (b.videoModel === 'ltx') {
    kind = 'video';
    if (!b.checkpoint) {
      throw new Error('LTX requires a checkpoint selection');
    }
    // Transformer-only files (SpiceModels quants) appear in the UNETLoader
    // enum; they load there and borrow VAE/audio-VAE from the donor checkpoint.
    const families = await comfy.listCheckpoints().catch(() => ({} as Record<string, string[]>));
    const modelIsUnet = (families['unets_all'] ?? []).includes(b.checkpoint);
    size = await frameFor(b, 'video', await stillDims(b.startImage), 64);
    graph = buildLtxGraph({
      prompt: b.prompt,
      ...size,
      seconds: Math.max(1, Math.min(10, b.seconds || 5)),
      seed,
      checkpoint: b.checkpoint,
      modelIsUnet,
      // Default: fine-tunes (unet-loaded) get dev sampling, official gets distilled
      sampling: b.sampling === 'dev' || b.sampling === 'distilled'
        ? b.sampling
        : modelIsUnet ? 'dev' : 'distilled',
      extraLora: typeof b.extraLora === 'string' && b.extraLora ? b.extraLora : undefined,
      extraLoraStrength: b.extraLoraStrength,
      startImage: b.startImage,
    });
  } else {
    kind = 'video';
    graph = buildH3Graph({
      prompt: b.prompt,
      width: b.width || 864,
      height: b.height || 480,
      lengthFrames: snapH3Length(b.lengthFrames || 124),
      seed,
      steps: b.steps || 20,
      startImage: b.startImage,
      endImage: b.endImage,
      refImages: b.refImages,
      refMode: b.videoModel === 'h3-max' && b.refMode === true,
      checkpoint: b.videoModel === 'h3-fast' ? CHECKPOINT_FASTH3 : typeof b.checkpoint === 'string' ? b.checkpoint : undefined,
      extraLora: typeof b.extraLora === 'string' && b.extraLora ? b.extraLora : undefined,
      extraLoraStrength: b.extraLoraStrength,
      // Turbo overrides steps/shift inside the builder; '' = full sampling.
      turbo: typeof b.h3Turbo === 'string' && b.h3Turbo ? b.h3Turbo : undefined,
      // House rule: no audio on visual loops. Opt in per shot for dialogue.
      withAudio: !!b.withAudio,
    });
  }

  const post = directorPost(b, graph);
  return { graph, kind, settings: size || post ? { ...size, ...post } : undefined };
}

/**
 * Director post passes on a still or an LTX-2.5 shot: the era grade (when an
 * era is set and the grade is on) and the speed ramp. Returns what the take
 * should record about them: the length after the ramp, and that it is silent.
 */
function directorPost(b: any, graph: Record<string, unknown>): Record<string, unknown> | undefined {
  const still = b.kind === 'still';
  const ltx = b.kind === 'video' && b.videoModel === 'ltx25';
  if (!still && !ltx) return undefined;
  const era = b.era == null || b.era === '' || !Number.isFinite(Number(b.era)) ? null : clampEra(Number(b.era));
  const grade = era != null && b.eraGrade !== false ? eraGrade(era) : undefined;
  const ramp = ltx && isRamp(b.ramp) && b.ramp !== 'linear' ? b.ramp : undefined;
  if (!grade && !ramp) return undefined;
  const fps = b.fps || LTX25_FPS;
  const frames = ltx ? snapFrames(Math.max(1, Math.min(20, b.seconds || 5)), fps) : undefined;
  const r = applyPost(graph as Record<string, any>, { grade, ramp, frames });
  return {
    era, eraGraded: !!grade,
    ...(ramp ? { ramp, outFrames: r.outFrames, outSeconds: Math.round(((r.outFrames ?? 0) / fps) * 10) / 10, rampSilent: r.silent } : {}),
  };
}

/**
 * Effects: the LoRA file, strength, trigger and negative come from the effect
 * definition (src/effects.ts), never from the request. Clip effects are
 * IC-LoRA video-to-video; still effects are image-to-video with a plain LoRA.
 */
function buildEffectGraph(b: any, seed: number): Record<string, unknown> {
  const fx = effectById(b.effect);
  if (!fx) throw new Error(`Unknown effect "${b.effect}"`);
  if (fx.input === 'clip' && !b.sourceVideo) throw new Error(`${fx.name} needs a source clip`);
  if (fx.input === 'still' && !b.startImage) throw new Error(`${fx.name} needs a still`);
  const prompt = typeof b.prompt === 'string' ? b.prompt : effectPrompt(fx, String(b.text ?? ''));
  const lora = { file: fx.lora, strength: fx.strength, trigger: fx.trigger };
  return buildLtx25Graph({
    prompt,
    negative: fx.negative,
    width: b.width,
    height: b.height,
    seconds: Math.max(1, Math.min(fx.maxSeconds, b.seconds || 5)),
    seed,
    startImage: fx.input === 'still' ? b.startImage : undefined,
    endImage: fx.input === 'still' && fx.loopable && b.loop ? b.startImage : undefined,
    withAudio: !!b.withAudio,
    ...(fx.ic ? { icLora: { ...lora, video: b.sourceVideo } } : { loras: [lora] }),
    filenamePrefix: `openfield/effect_${fx.id}`,
  });
}

/**
 * Keep the graph behind a take so it can be opened in ComfyUI later. Our own
 * copy is stored at once; the engine's record of what actually ran (with the
 * input filenames ComfyUI really has) replaces it as soon as it answers.
 */
async function recordWorkflow(takeId: number, jobId: string, graph: Record<string, unknown>) {
  try {
    takeWorkflows.set(takeId, await eng.withInputNames(graph), 'submitted');
    const ran = await eng.executedWorkflow(jobId);
    if (ran) takeWorkflows.set(takeId, ran, 'engine');
  } catch (e) {
    console.error(`[openfield] could not record the workflow for take ${takeId}:`, e instanceof Error ? e.message : e);
  }
}

app.post('/api/generate', async (req, reply) => generate(req.body as any, reply));

/**
 * Nexora Creative, parcours simple : une intention en français → prompt H3 écrit par le LLM cloud (réécrivain validé
 * par le guide officiel, repli conforme si le LLM manque) → même chemin de rendu que /api/generate.
 */
app.post('/api/nexora/creer', async (req, reply) => {
  let demande;
  try { demande = lireDemandeCreer(req.body); }
  catch (e) { return reply.code(400).send({ error: e instanceof Error ? e.message : 'demande invalide' }); }
  // Moteur choisi par le registre de capacités (licence et territoire d'abord, puis la qualité demandée).
  const moteur = moteurDuCompte(demande.qualite, besoinDe(demande));
  if (!moteur) {
    const plan = planifierMoteurs(besoinDe(demande), { territoire: territoireDuCompte(), recettes: recettesDuParc() });
    return reply.code(422).send({ error: `Aucun moteur ne peut faire cette vidéo pour ton compte : ${plan.exclus.map((e) => e.raison).join(' ; ')}.` });
  }
  const verdict = await moderer(`${demande.intention} ${demande.replique ?? ''}`, llmCourant(), (m) => app.log.warn(m));
  if (!verdict.ok) return reply.code(422).send({ error: verdict.raison, categorie: verdict.categorie });
  // Avec une photo de départ, le prompt suit le guide I2VA : il part de l'image et développe l'action.
  // Personnages @ : sur le moteur cinéma (Ref2VA), @nom joint les images du personnage ; ailleurs, seulement ses mots.
  const persos = moteur === 'h3-max' && !demande.image ? await resoudrePersonnages(demande.intention) : null;
  const entree = {
    intention: intentionAvecCamera(persos?.sujets.length ? { ...demande, intention: persos.texteClair } : demande), mode: (demande.image ? 'i2va' : 't2va') as 'i2va' | 't2va', dureeS: dureeEffective(demande),
    moteur, format: demande.format, ...(demande.replique ? { dialogues: [{ texte: demande.replique, langue: 'French' }] } : {}),
  };
  // Le réalisateur (recherche/25) écrit le prompt ; ses jetons sont réservés, mesurés et réglés comme ceux de l'agent.
  const palierRedaction = palierDuRole('redaction');
  let r: Awaited<ReturnType<typeof reecrireH3>>;
  let usageRedaction: { credits: number; usd: number; jetons: number; palier: string } | null = null;
  if (palierRedaction) {
    const compte = compteCourant();
    try {
      const { resultat, bilan } = await executerSousReservation(
        { fac: facturationCourante(), devis: devisLlm('realisation', palierRedaction, { livre: livreUsage, marge: 4 }), ctx: { run: randomUUID(), tache: 'realisation', utilisateur: compte?.utilisateurId, organisation: compte?.organisationId }, livre: livreUsage },
        (rel) => reecrireH3(entree, llmRedaction(rel)),
      );
      r = resultat;
      usageRedaction = { credits: bilan.factures, usd: bilan.totaux.coutUsd, jetons: bilan.totaux.entree + bilan.totaux.sortie, palier: palierRedaction };
    } catch (e) {
      if (e instanceof ErreurLlm && !(e instanceof ErreurPlafondLlm)) return reply.code(402).send({ error: e.message });
      r = await reecrireH3(entree, null);
    }
  } else r = await reecrireH3(entree, llmCourant());
  const corps: any = { ...corpsRendu(demande, r.prompt, moteur), intention: demande.intention, promptSource: r.source, moteur, nexoraAutoMusique: (req.body as any)?.musique === true };
  if (persos?.sujets.length) Object.assign(corps, { prompt: convertirEnPromptRef(r.prompt, persos.sujets), refImages: persos.jetons, personnages: persos.noms });
  if (typeof (req.body as any)?.projectId === 'number') corps.projectId = (req.body as any).projectId;
  const res = await generate(corps, reply);
  if (reply.sent || (res && (res as any).error)) return res;
  return { ...res, prompt: corps.prompt, source: r.source, tentatives: r.tentatives, moteur, ...comprehensionDe(r.fiche), ...(usageRedaction ? { usageRedaction } : {}) };
});

/** Ce que le réalisateur a compris, pour le client : résumé, choix faits sans demander, plans, variantes. */
function comprehensionDe(f: FicheRealisation | undefined) {
  if (!f) return {};
  return { comprehension: { compris: f.compris, famille: f.famille, hypotheses: f.hypotheses, variantes: f.variantes, plans: f.plans.map((p) => ({ debut: p.debut, cadrage: p.cadrage })) } };
}

/** Director, étape 1 : l'idée devient un storyboard (plans, caméra, durées, bible de continuité), sans rien tourner. */
app.post('/api/nexora/film/plan', async (req, reply) => {
  const b = (req.body ?? {}) as any;
  const intention = typeof b.intention === 'string' ? b.intention.trim() : '';
  if (!intention) return reply.code(400).send({ error: 'Décris le film que tu veux.' });
  const dureeCible = Math.max(10, Math.min(120, Number(b.duree) || 30));
  const verdict = await moderer(intention, llmCourant(), (m) => app.log.warn(m));
  if (!verdict.ok) return reply.code(422).send({ error: verdict.raison, categorie: verdict.categorie });
  return planifierFilm({ intention: intention.slice(0, 4000), dureeCible }, llmCourant());
});

/** Director, étape 2 : tourner le storyboard (éventuellement modifié par la personne) et l'assembler. */
app.post('/api/nexora/film/tourner', async (req, reply) => {
  const b = (req.body ?? {}) as any;
  let sb;
  try { sb = lireStoryboard(b.storyboard, 0); }
  catch (e) { return reply.code(400).send({ error: e instanceof Error ? e.message : 'storyboard invalide' }); }
  const demande = lireDemandeCreer({ intention: sb.titre, format: b.format, son: b.son, qualite: b.qualite });
  const moteur = moteurDuCompte(demande.qualite);
  if (!moteur) return reply.code(422).send({ error: REFUS_TERRITOIRE });
  const missing = await blockingReasonFor(eng.isLocal() && eng.recetteSurPrincipal(moteur), bundlesFor({ kind: 'video', videoModel: moteur }));
  if (missing) return reply.code(412).send({ error: missing });
  // Crédits : chaque plan réserve son devis avant le tournage ; les reprises automatiques sont offertes par Nexora.
  // Producteur : deux candidats par plan indépendant (juge visuel), cartons de texte, musique composée pendant le tournage.
  const candidats: 1 | 2 = b.candidats === 2 ? 2 : 1;
  const cartons = lireCartons(b.cartons);
  const fac = facturationCourante();
  const reservations: CreditsPrise[] = [];
  const reservationsCandidats: (CreditsPrise | undefined)[] = [];
  const toutes = () => [...reservations, ...reservationsCandidats.filter((x): x is CreditsPrise => !!x)];
  if (fac) {
    for (const p of sb.plans) {
      const corps = corpsRendu({ intention: p.resume, format: demande.format, duree: p.duree, son: demande.son, qualite: demande.qualite }, '', moteur);
      const n = candidats === 2 && !p.suite ? 2 : 1;
      for (let k = 0; k < n; k++) {
        const r = await fac.reserver({ idempotence: randomUUID(), credits: devisCredits(corps, tarifDepuisEnv()), libelle: `Nexora Creative · film « ${sb.titre.slice(0, 40)} »` });
        if (!r.ok) {
          for (const x of toutes()) await fac.liberer(x.reservationId).catch(() => {});
          return reply.code(402).send({ error: r.message });
        }
        const res: CreditsPrise = { reservationId: r.reservationId, credits: r.credits, etat: 'reservee' };
        if (k === 0) reservations.push(res); else reservationsCandidats[reservations.length - 1] = res;
      }
    }
  }
  try {
    const filmId = await tournerFilm(sb, { format: demande.format, son: demande.son, intention: String(b.intention ?? sb.titre), projectId: b.projectId ?? null, moteur, reservations, reservationsCandidats, qualite: demande.qualite, candidats, cartons }, llmRedaction());
    // Musique MiniMax-Music3 composée en parallèle (GB10) depuis le storyboard ; le film l'attend avant d'assembler.
    const envie = typeof b.musique?.envie === 'string' ? b.musique.envie.slice(0, 500) : b.musique === true ? '' : null;
    if (envie !== null && eng.moteursPour('music3').length) {
      try {
        const m = await ecrireMusique(sb, sb.dureeTotale, llmCourant(), envie || undefined);
        const [musiqueId] = await queueTakes({
          kind: 'musique', videoModel: 'music3', description: m.description, paroles: m.paroles, dureeS: Math.ceil(sb.dureeTotale + cartons.length * 2.5),
          app: 'nexora-musique', nexoraMusiqueDe: filmId, nexoraFilm: filmId, shotName: `${sb.titre.slice(0, 40)}_musique`,
          prompt: m.description, userPrompt: envie || 'Bande originale', promptSource: m.source, projectId: b.projectId ?? undefined,
        }, 1);
        takes.patchSettings(filmId, { musiquePrise: musiqueId });
      } catch (e) {
        app.log.warn(`musique du film ${filmId} non lancée : ${e instanceof Error ? e.message : e}`);
      }
    }
    return { filmId, take: takes.get(filmId), credits: toutes().reduce((n, r) => n + r.credits, 0) || undefined };
  } catch (e) {
    for (const x of toutes()) await fac?.liberer(x.reservationId).catch(() => {});
    return reply.code(400).send({ error: e instanceof Error ? e.message : 'tournage impossible' });
  }
});

/** Devis en crédits d'une création, avant de la lancer (null en poste local : rien n'est débité). */
app.post('/api/nexora/devis', async (req) => {
  const b = (req.body ?? {}) as any;
  const demande = lireDemandeCreer({ intention: 'devis', format: b.format, duree: b.duree, son: b.son, qualite: b.qualite, image: b.image });
  const moteur = moteurDuCompte(demande.qualite, besoinDe(demande));
  if (!moteur) return { credits: null, secondesEstimees: null, moteur: null, erreur: REFUS_TERRITOIRE };
  const corps = corpsRendu(demande, '', moteur);
  return { credits: configAuth ? devisCredits(corps, tarifDepuisEnv()) : null, secondesEstimees: secondesGpuEstimees(corps), moteur };
});

/**
 * Refaire un seul plan d'un film (description ou caméra retouchées) : une nouvelle version du film garde les prises des
 * autres plans, ne retourne que ce plan et ceux qui s'enchaînaient dessus, puis réassemble.
 */
app.post('/api/nexora/film/:id/refaire', async (req, reply) => {
  const film = takes.get(Number((req.params as any).id));
  const b = (req.body ?? {}) as any;
  if (!film) return reply.code(404).send({ error: 'Film introuvable.' });
  const s = JSON.parse(film.settings);
  if (!s.film || film.status === 'queued' || film.status === 'rendering') return reply.code(409).send({ error: 'Ce film est encore en tournage.' });
  let sb;
  try { sb = storyboardPourRefaire(s.storyboard, Number(b.plan), { description: b.description, camera: b.camera }); }
  catch (e) { return reply.code(400).send({ error: e instanceof Error ? e.message : 'plan invalide' }); }
  const moteur = s.moteur === 'h3-max' || s.moteur === 'h3-fast' ? s.moteur as MoteurVideo : moteurDuCompte(s.qualite);
  if (!moteur) return reply.code(422).send({ error: REFUS_TERRITOIRE });
  const fac = facturationCourante();
  const reservations: (CreditsPrise | undefined)[] = [];
  for (const p of sb.plans) {
    if (!fac || p.take) { reservations.push(undefined); continue; }
    const corps = corpsRendu({ intention: p.resume, format: s.format, duree: p.duree, son: !!s.son, qualite: s.qualite }, '', moteur);
    const r = await fac.reserver({ idempotence: randomUUID(), credits: devisCredits(corps, tarifDepuisEnv()), libelle: `Nexora Creative · plan refait « ${sb.titre.slice(0, 40)} »` });
    if (!r.ok) {
      for (const x of reservations) if (x) await fac.liberer(x.reservationId).catch(() => {});
      return reply.code(402).send({ error: r.message });
    }
    reservations.push({ reservationId: r.reservationId, credits: r.credits, etat: 'reservee' });
  }
  const filmId = await tournerFilm({ ...sb, titre: sb.titre }, { format: s.format, son: !!s.son, intention: s.prompt, projectId: film.project_id, moteur, reservations: reservations as CreditsPrise[], qualite: s.qualite }, llmRedaction());
  takes.patchSettings(filmId, { versionDe: film.id });
  void avancerFilm(filmId);
  return { filmId, take: takes.get(filmId) };
});

/**
 * Prolonger un clip ou raccorder deux clips (remplacent Extend et Transitions, qui reposaient sur LTX) : un petit film
 * dont les clips d'origine gardent leur prise ; seul le nouveau plan est tourné (MiniMax H3), contrôlé et facturé.
 */
async function lancerRaccord(req: FastifyRequest, reply: FastifyReply, r: { storyboard: Storyboard; format: FormatCreer; son: boolean; qualite: 'rapide' | 'max' }, intention: string) {
  if (intention) {
    const verdict = await moderer(intention, llmCourant(), (m) => app.log.warn(m));
    if (!verdict.ok) return reply.code(422).send({ error: verdict.raison, categorie: verdict.categorie });
  }
  const moteur = moteurDuCompte(r.qualite);
  if (!moteur) return reply.code(422).send({ error: REFUS_TERRITOIRE });
  const fac = facturationCourante();
  const reservations: (CreditsPrise | undefined)[] = [];
  for (const p of r.storyboard.plans) {
    if (!fac || p.take) { reservations.push(undefined); continue; }
    const corps = corpsRendu({ intention: p.resume, format: r.format, duree: p.duree, son: r.son, qualite: r.qualite }, '', moteur);
    const res = await fac.reserver({ idempotence: randomUUID(), credits: devisCredits(corps, tarifDepuisEnv()), libelle: `Nexora Creative · ${r.storyboard.titre.slice(0, 40)}` });
    if (!res.ok) {
      for (const x of reservations) if (x) await fac.liberer(x.reservationId).catch(() => {});
      return reply.code(402).send({ error: res.message });
    }
    reservations.push({ reservationId: res.reservationId, credits: res.credits, etat: 'reservee' });
  }
  const filmId = await tournerFilm(r.storyboard, { format: r.format, son: r.son, intention: intention || r.storyboard.titre, moteur, reservations: reservations as CreditsPrise[], qualite: r.qualite }, llmRedaction());
  takes.patchSettings(filmId, { app: 'nexora-raccord' });
  void avancerFilm(filmId);
  return { filmId };
}

app.post('/api/nexora/prolonger', async (req, reply) => {
  const b = (req.body ?? {}) as any;
  const t = takes.get(Number(b.take));
  if (!t) return reply.code(404).send({ error: 'Vidéo introuvable.' });
  try {
    const intention = typeof b.intention === 'string' ? b.intention.trim().slice(0, 1200) : '';
    return await lancerRaccord(req, reply, storyboardProlonger(t, { intention, duree: Number(b.duree) }), intention);
  } catch (e) {
    return reply.code(400).send({ error: e instanceof Error ? e.message : 'prolongement impossible' });
  }
});

app.post('/api/nexora/raccord', async (req, reply) => {
  const b = (req.body ?? {}) as any;
  const de = takes.get(Number(b.de)), vers = takes.get(Number(b.vers));
  if (!de || !vers) return reply.code(404).send({ error: 'Choisis deux vidéos.' });
  if (de.id === vers.id) return reply.code(400).send({ error: 'Choisis deux vidéos différentes.' });
  try {
    const intention = typeof b.intention === 'string' ? b.intention.trim().slice(0, 1200) : '';
    return await lancerRaccord(req, reply, storyboardRaccord(de, vers, { intention }), intention);
  } catch (e) {
    return reply.code(400).send({ error: e instanceof Error ? e.message : 'raccord impossible' });
  }
});

/** Moteurs du registre pour une demande : ceux qui conviennent (classés) et ceux qui sont exclus, avec la raison. */
app.post('/api/nexora/moteurs', async (req) => {
  const d = lireDemandeCreer({ ...(req.body as any), intention: 'x' });
  const r = planifierMoteurs(besoinDe(d), { territoire: territoireDuCompte() });
  return { retenus: r.retenus.map((m) => ({ id: m.id, nom: m.nom.fr, recette: m.recette, son: m.sortie.audio, affichage: m.licence.affichage ?? null })), exclus: r.exclus };
});

/** Montage d'un film sans nouveau rendu : nouvel ordre, plans retirés, coupe franche ou fondu enchaîné. */
app.post('/api/nexora/film/:id/montage', async (req, reply) => {
  const film = takes.get(Number((req.params as any).id));
  const b = (req.body ?? {}) as any;
  if (!film) return reply.code(404).send({ error: 'Film introuvable.' });
  const s = JSON.parse(film.settings);
  if (!s.film || film.status !== 'done') return reply.code(409).send({ error: 'Le film doit être terminé pour être remonté.' });
  let sb;
  try { sb = storyboardPourMontage(s.storyboard, Array.isArray(b.ordre) ? b.ordre.map(Number) : s.storyboard.plans.map((_: unknown, i: number) => i)); }
  catch (e) { return reply.code(400).send({ error: e instanceof Error ? e.message : 'montage invalide' }); }
  // Bande originale : une prise « musique » terminée de la même organisation (garde par takes.get), ou celle du film.
  let musique: string | undefined = typeof s.musique === 'string' ? s.musique : undefined;
  if (b.musique === null) musique = undefined;
  else if (b.musique !== undefined) {
    const m = takes.get(Number(b.musique));
    if (!m || m.status !== 'done' || !m.output_path || JSON.parse(m.settings).kind !== 'musique') return reply.code(400).send({ error: 'Cette musique n’est pas prête.' });
    musique = m.output_path;
  }
  const filmId = await tournerFilm(sb, { format: s.format, son: !!s.son, intention: s.prompt, projectId: film.project_id, moteur: s.moteur ?? 'h3-fast', qualite: s.qualite }, null);
  takes.patchSettings(filmId, { versionDe: film.id, transition: b.transition === 'fondu' ? 'fondu' : 'coupe', ...(musique ? { musique } : {}) });
  void avancerFilm(filmId);
  return { filmId };
});

/**
 * Bande originale d'un film terminé : le LLM écrit la description MiniMax Music 3 depuis le storyboard, la musique est
 * composée sur le moteur qui porte la recette « music3 ». Une fois prête, /montage avec { musique: <prise> } la mixe.
 */
app.post('/api/nexora/film/:id/musique', async (req, reply) => {
  const film = takes.get(Number((req.params as any).id));
  const b = (req.body ?? {}) as any;
  if (!film) return reply.code(404).send({ error: 'Film introuvable.' });
  const s = JSON.parse(film.settings);
  if (!s.film || film.status !== 'done') return reply.code(409).send({ error: 'Le film doit être terminé pour recevoir sa musique.' });
  if (!eng.moteursPour('music3').length) return reply.code(503).send({ error: 'Aucun moteur GPU ne compose de musique pour l’instant.' });
  const duree = Number(s.storyboard?.dureeTotale) || Number(s.seconds) || 30;
  const m = await ecrireMusique(s.storyboard, duree, llmCourant(), typeof b.envie === 'string' ? b.envie.slice(0, 500) : undefined);
  const [takeId] = await queueTakes({
    kind: 'musique', videoModel: 'music3', description: m.description, paroles: m.paroles, dureeS: Math.ceil(duree),
    app: 'nexora-musique', nexoraMusiqueDe: film.id, shotName: `${(film.shot_name || 'film').slice(0, 40)}_musique`,
    prompt: m.description, userPrompt: typeof b.envie === 'string' ? b.envie : 'Bande originale', promptSource: m.source,
    projectId: film.project_id ?? undefined,
  }, 1);
  return { takeId, source: m.source };
});

/**
 * Bande originale d'un clip simple (même moteur de musique que pour un film) : la musique est composée depuis la
 * phrase du clip ; /avec-musique la mixe ensuite sous les sons du clip, dans une nouvelle vidéo (le clip d'origine reste).
 */
app.post('/api/nexora/clip/:id/musique', async (req, reply) => {
  const clip = takes.get(Number((req.params as any).id));
  const b = (req.body ?? {}) as any;
  if (!clip || clip.kind !== 'video') return reply.code(404).send({ error: 'Vidéo introuvable.' });
  const s = JSON.parse(clip.settings);
  if (s.film || clip.status !== 'done' || !clip.output_path) return reply.code(409).send({ error: 'La vidéo doit être terminée.' });
  if (!eng.moteursPour('music3').length) return reply.code(503).send({ error: 'Aucun moteur GPU ne compose de musique pour l’instant.' });
  const duree = Math.max(5, Math.ceil(Number(s.lengthFrames || 124) / 24));
  const pseudo = { titre: String(s.intention ?? s.userPrompt ?? clip.shot_name ?? 'Clip').slice(0, 120), bible: { style: '', personnages: [], lieux: [] }, plans: [{ resume: String(s.intention ?? s.userPrompt ?? clip.shot_name ?? ''), description: '', duree, camera: '' }], dureeTotale: duree };
  if (s.nexoraMusiqueLance) return reply.code(409).send({ error: 'Une musique a déjà été lancée pour cette vidéo.' });
  takes.patchSettings(clip.id, { nexoraMusiqueLance: true });
  const m = await ecrireMusique(pseudo as any, duree, llmCourant(), typeof b.envie === 'string' ? b.envie.slice(0, 500) : undefined);
  const [takeId] = await queueTakes({
    kind: 'musique', videoModel: 'music3', description: m.description, paroles: m.paroles, dureeS: duree,
    app: 'nexora-musique', nexoraMusiqueDe: clip.id, shotName: `${(clip.shot_name || 'clip').slice(0, 40)}_musique`,
    prompt: m.description, userPrompt: typeof b.envie === 'string' ? b.envie : 'Musique', promptSource: m.source, projectId: clip.project_id ?? undefined,
  }, 1);
  return { takeId, source: m.source };
});

app.post('/api/nexora/clip/:id/avec-musique', async (req, reply) => {
  const clip = takes.get(Number((req.params as any).id));
  const m = takes.get(Number(((req.body ?? {}) as any).musique));
  if (!clip || !m || clip.status !== 'done' || m.status !== 'done' || !clip.output_path || !m.output_path || JSON.parse(m.settings).kind !== 'musique') {
    return reply.code(409).send({ error: 'La vidéo et la musique doivent être terminées.' });
  }
  const s = JSON.parse(clip.settings);
  const { execFile } = await import('child_process');
  const dureeS = await new Promise<number>((ok) =>
    execFile(config.ffprobeBin, ['-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', clip.output_path!], (err, out) => ok(err ? Math.round(Number(s.lengthFrames || 124) / 24 * 100) / 100 : Number(String(out).trim()) || 5)));
  const dossier = join(config.outputDir, 'clips-musique');
  mkdirSync(dossier, { recursive: true });
  const sortie = join(dossier, `clip_${clip.id}_musique_${Date.now()}.mp4`);
  await new Promise<void>((ok, ko) =>
    execFile(config.ffmpegBin, argsAvecMusique(clip.output_path!, m.output_path!, sortie, { dureeS, sonDuFilm: !!s.withAudio }), { maxBuffer: 1 << 24 }, (err, _o, stderr) =>
      err ? ko(new Error(`ffmpeg (musique) : ${String(stderr).split('\n').slice(-3).join(' ')}`)) : ok()))
    .catch((e) => { throw Object.assign(e, { statusCode: 500 }); });
  const id = takes.create({ project_id: clip.project_id, kind: 'video', shot_name: `${(clip.shot_name || 'clip').slice(0, 40)} + musique`, settings: { ...s, nexoraAvecMusique: true, versionDe: clip.id, musique: m.output_path, nexoraMusiqueDe: undefined } });
  takes.finish(id, sortie, 0);
  broadcast({ type: 'take', take: takes.get(id) });
  return { takeId: id };
});

/** Export professionnel d'un film terminé (ProRes 422 HQ + PCM, .mov). */
app.get('/api/nexora/film/:id/export', async (req, reply) => {
  const film = takes.get(Number((req.params as any).id));
  if (!film || !film.output_path || film.status !== 'done') return reply.code(404).send({ error: 'Film introuvable ou pas terminé.' });
  const dossier = join(config.outputDir, 'films', 'exports');
  mkdirSync(dossier, { recursive: true });
  const sortie = join(dossier, `film_${film.id}_prores.mov`);
  if (!existsSync(sortie)) {
    const { execFile } = await import('child_process');
    await new Promise<void>((ok, ko) => execFile(config.ffmpegBin, argsExport(film.output_path!, sortie, 'prores'), { maxBuffer: 1 << 24 }, (err) => (err ? ko(err) : ok())));
  }
  reply.header('content-type', 'video/quicktime');
  reply.header('content-disposition', `attachment; filename="${safeShotName(film.shot_name || 'film')}_prores.mov"`);
  return reply.send(createReadStream(sortie));
});

/**
 * « Monter » (harnais de montage, server/nexora/montage/) : les plans tournés d'un film + sa bande originale deviennent un
 * EditPlan (code seul), rendu en aperçu par le rendu ffmpeg du harnais. « Améliorer » = un tour critique → rustines.
 * L'état (brief, plan) vit dans <données>/montages/<film>-<n>.json ; l'aperçu à côté. Rien n'est dépensé.
 */
const dossierMontages = () => { const d = join(config.dataDir, 'montages'); mkdirSync(d, { recursive: true }); return d; };
const idMontage = (v: unknown) => (/^\d+-\d+$/.test(String(v)) ? String(v) : null);
async function rendreApercuMontage(etat: EtatMontageFilm, id: string) {
  const chemin = (src: string) => {
    const t = /^\d+$/.test(src) ? takes.get(Number(src)) : undefined;
    if (!t?.output_path || !existsSync(t.output_path)) throw new Error(`média ${src} introuvable`);
    return t.output_path;
  };
  const sources = Object.fromEntries(etat.brief.clips.map((c) => [c.id, { duree_s: c.duree_s }]));
  if (etat.brief.musique) sources[etat.brief.musique.id] = { duree_s: etat.brief.musique.duree_s };
  const sortie = join(dossierMontages(), `${id}.mp4`);
  const r = await rendreEditPlan(etat.plan, chemin, sortie, { apercu: true, ffmpeg: config.ffmpegBin, ctx: { inventaire: sources, duree_cible_s: etat.brief.duree_cible_s } });
  if (!r.ok) throw new Error(`plan invalide : ${r.erreurs.slice(0, 2).join(' ; ')}`);
  const lufs = (await analyserMedia(sortie, { ffmpeg: config.ffmpegBin, cache: false }).catch(() => null))?.loudness;
  return { dureeS: r.dureeS, sonie: lufs ? { lufs: lufs.integre_lufs, crete_db: lufs.crete_db } : null };
}
const vueMontage = (id: string, etat: EtatMontageFilm, rendu: { dureeS: number; sonie: unknown }, extra: object = {}) => ({
  id, film: etat.film, url: `/api/nexora/montage/${id}/apercu.mp4`, source: etat.source, tours: etat.tours, plafondTours: 2,
  genre: etat.plan.genre, format: etat.plan.format, ...rendu, metriques: vueMetriques(etat.plan, etat.brief), ...extra,
});
const lireEtatMontage = (id: string): EtatMontageFilm | null => { try { return JSON.parse(readFileSync(join(dossierMontages(), `${id}.json`), 'utf8')); } catch { return null; } };

app.post('/api/nexora/film/:id/monter', async (req, reply) => {
  const film = takes.get(Number((req.params as any).id));
  const b = (req.body ?? {}) as any;
  if (!film) return reply.code(404).send({ error: 'Film introuvable.' });
  const s = JSON.parse(film.settings);
  if (!s.film || film.status !== 'done') return reply.code(409).send({ error: 'Le film doit être terminé pour être monté.' });
  const genre = (GENRES_MONTAGE as readonly string[]).includes(b.genre) ? b.genre : 'pub';
  const ids: number[] = ((s.storyboard?.plans ?? []) as any[]).map((p) => p.take).filter((x): x is number => typeof x === 'number');
  const prises = ids.map((i) => takes.get(i)).filter((t): t is NonNullable<typeof t> => !!t && t.status === 'done' && !!t.output_path && existsSync(t.output_path));
  if (!prises.length) return reply.code(409).send({ error: 'Aucun plan tourné à monter.' });
  try {
    const clips = await Promise.all(prises.map(async (t) => ({ id: String(t.id), analyse: await analyserMedia(t.output_path!, { ffmpeg: config.ffmpegBin }) })));
    const m = typeof s.musiquePrise === 'number' ? takes.get(s.musiquePrise) : undefined;
    const musique = m?.status === 'done' && m.output_path && existsSync(m.output_path)
      ? { id: String(m.id), analyse: await analyserMedia(m.output_path, { ffmpeg: config.ffmpegBin }) } : undefined;
    const dureeCibleS = Number(b.duree) > 0 ? Number(b.duree) : undefined;
    const brief = briefDuFilm({ clips, musique, genre, format: s.format ?? '16:9', dureeCibleS, enonce: s.prompt ? String(s.prompt).slice(0, 300) : undefined });
    const etat = monterEnCode(brief, film.id);
    const n = readdirSync(dossierMontages()).filter((f) => f.startsWith(`${film.id}-`) && f.endsWith('.json')).length + 1;
    const id = `${film.id}-${n}`;
    const rendu = await rendreApercuMontage(etat, id);
    writeFileSync(join(dossierMontages(), `${id}.json`), JSON.stringify(etat));
    return vueMontage(id, etat, rendu, { musique: !!musique });
  } catch (e) {
    app.log.warn(`monter : ${e instanceof Error ? e.message : e}`);
    return reply.code(500).send({ error: `Le montage a échoué : ${e instanceof Error ? e.message.slice(0, 200) : 'erreur'}` });
  }
});

app.post('/api/nexora/montage/:mid/ameliorer', async (req, reply) => {
  const id = idMontage((req.params as any).mid);
  const etat = id ? lireEtatMontage(id) : null;
  if (!id || !etat || !takes.get(etat.film)) return reply.code(404).send({ error: 'Montage introuvable.' });
  if (etat.tours >= 2) return reply.code(409).send({ error: 'Deux tours d’amélioration au plus par montage : celui-ci est au maximum.' });
  const r = await ameliorerMontage(etat, llmCourant());
  try {
    const rendu = r.gardee ? await rendreApercuMontage(r.etat, id) : { dureeS: dureeTotaleS(r.etat.plan), sonie: null };
    writeFileSync(join(dossierMontages(), `${id}.json`), JSON.stringify(r.etat));
    return vueMontage(id, r.etat, rendu, { amelioration: { avant: r.avant, apres: r.apres, gardee: r.gardee, message: r.message } });
  } catch (e) {
    return reply.code(500).send({ error: `Le rendu a échoué : ${e instanceof Error ? e.message.slice(0, 200) : 'erreur'}` });
  }
});

app.get('/api/nexora/montage/:mid/apercu.mp4', async (req, reply) => {
  const id = idMontage((req.params as any).mid);
  const etat = id ? lireEtatMontage(id) : null;
  const f = id ? join(dossierMontages(), `${id}.mp4`) : '';
  if (!id || !etat || !takes.get(etat.film) || !existsSync(f)) return reply.code(404).send({ error: 'Aperçu introuvable.' });
  const size = statSync(f).size;
  const m = req.headers.range ? /bytes=(\d+)-(\d*)/.exec(req.headers.range) : null;
  if (m) {
    const start = parseInt(m[1], 10);
    const end = m[2] ? parseInt(m[2], 10) : size - 1;
    reply.code(206).headers({ 'Content-Range': `bytes ${start}-${end}/${size}`, 'Accept-Ranges': 'bytes', 'Content-Length': end - start + 1, 'Content-Type': 'video/mp4' });
    return reply.send(createReadStream(f, { start, end }));
  }
  reply.headers({ 'Content-Length': size, 'Content-Type': 'video/mp4', 'Accept-Ranges': 'bytes', 'Cache-Control': 'no-cache' });
  return reply.send(createReadStream(f));
});

/**
 * Prises par plan (vague 2) : brouillons rapides pour choisir, finale cinéma pour la prise gardée, compteur de coût du
 * projet qui inclut les prises écartées. Les prises ajoutées vivent dans le storyboard du film (plan.extra, plan.rejetees) ;
 * elles portent `prisesFilm` et `prisePlan`, jamais `nexoraFilm`, pour ne pas toucher à l'assemblage du film.
 */
function corpsDePrise(id: number) {
  const t = takes.get(id);
  if (!t) return undefined;
  const s = JSON.parse(t.settings);
  return { status: t.status, corps: { videoModel: s.videoModel, width: s.width, height: s.height, lengthFrames: s.lengthFrames } };
}
function vuePrisesFilm(film: { id: number; settings: string }) {
  const s = JSON.parse(film.settings);
  const plans = (s.storyboard?.plans ?? []) as any[];
  const parPlan = plans.map((p) => prisesDuPlan({ take: p.take, candidats: p.candidats, extra: p.extra, rejetees: p.rejetees } as PrisesDuPlan, corpsDePrise, tarifDepuisEnv()));
  return {
    film: film.id, creditsActifs: !!configAuth,
    plans: plans.map((p, i) => ({ plan: i + 1, resume: String(p.resume ?? ''), prises: parPlan[i] })),
    compteur: compteurProjet(parPlan),
  };
}
function filmTerminePour(id: unknown, reply: FastifyReply) {
  const film = takes.get(Number(id));
  if (!film) { reply.code(404).send({ error: 'Film introuvable.' }); return null; }
  const s = JSON.parse(film.settings);
  if (!s.film || !s.storyboard) { reply.code(409).send({ error: 'Ce n’est pas un film du Producteur.' }); return null; }
  return { film, s };
}
function majPlanStoryboard(filmId: number, n: number, f: (p: any) => void) {
  const s = JSON.parse(takes.get(filmId)!.settings);
  f(s.storyboard.plans[n]);
  takes.patchSettings(filmId, { storyboard: s.storyboard });
}
/** Réserve les crédits d'une prise ajoutée (portail) ; sans portail, rien. Renvoie un refus lisible ou la réservation. */
async function reserverPrise(corps: any, libelle: string): Promise<{ refus?: string; reservation?: CreditsPrise }> {
  const fac = facturationCourante();
  if (!fac) return {};
  const r = await fac.reserver({ idempotence: randomUUID(), credits: devisCredits(corps, tarifDepuisEnv()), libelle });
  return r.ok ? { reservation: { reservationId: r.reservationId, credits: r.credits, etat: 'reservee' } } : { refus: r.message };
}
async function lancerPrises(film: number, n: number, corps: any, nombre: number, extra: Record<string, unknown>, libelle: string) {
  const reservations: CreditsPrise[] = [];
  for (let k = 0; k < nombre; k++) {
    const r = await reserverPrise(corps, libelle);
    if (r.refus) { for (const x of reservations) await facturationCourante()?.liberer(x.reservationId).catch(() => {}); throw new Error(r.refus); }
    if (r.reservation) reservations.push(r.reservation);
  }
  const ids = await queueTakes({ ...corps, seed: corps.seed ?? Math.floor(Math.random() * 1e9) }, nombre);
  ids.forEach((id, k) => takes.patchSettings(id, { prisesFilm: film, prisePlan: n, ...extra, ...(reservations[k] ? { nexoraCredits: reservations[k] } : {}) }));
  return ids;
}

app.get('/api/nexora/film/:id/prises', async (req, reply) => {
  const f = filmTerminePour((req.params as any).id, reply);
  return f ? vuePrisesFilm(f.film) : undefined;
});

app.post('/api/nexora/film/:id/plan/:n/brouillon', async (req, reply) => {
  const f = filmTerminePour((req.params as any).id, reply);
  if (!f) return;
  const n = Number((req.params as any).n);
  const plan = f.s.storyboard.plans[n];
  if (!plan?.corps) return reply.code(409).send({ error: 'Ce plan n’a pas encore de rendu de référence.' });
  const nombre = Math.max(1, Math.min(2, Number((req.body as any)?.nombre) || 2));
  const rapide = corpsRendu({ intention: plan.resume, format: f.s.format, duree: plan.duree, son: !!f.s.son, qualite: 'rapide' }, plan.corps.prompt, 'h3-fast');
  try {
    const ids = await lancerPrises(f.film.id, n, corpsBrouillonDe(plan.corps, Math.floor(Math.random() * 1e9), { ...rapide, app: 'nexora-prise', shotName: `${f.s.storyboard.titre.slice(0, 24)}_plan${n + 1}_brouillon`, userPrompt: plan.resume }), nombre, { brouillon: true }, `Nexora Creative · brouillon plan ${n + 1}`);
    majPlanStoryboard(f.film.id, n, (p) => { p.extra = [...(p.extra ?? []), ...ids.map((take) => ({ take, brouillon: true }))]; });
  } catch (e) { return reply.code(402).send({ error: e instanceof Error ? e.message : 'Impossible de lancer les brouillons.' }); }
  return vuePrisesFilm(takes.get(f.film.id)!);
});

app.post('/api/nexora/film/:id/plan/:n/prise', async (req, reply) => {
  const f = filmTerminePour((req.params as any).id, reply);
  if (!f) return;
  const n = Number((req.params as any).n);
  const { take, action } = (req.body ?? {}) as { take?: number; action?: string };
  const plan = f.s.storyboard.plans[n];
  const connues = prisesDuPlan({ take: plan?.take, candidats: plan?.candidats, extra: plan?.extra, rejetees: plan?.rejetees }, corpsDePrise, tarifDepuisEnv());
  const prise = connues.find((x) => x.take === Number(take));
  if (!plan || !prise) return reply.code(404).send({ error: 'Cette prise n’appartient pas à ce plan.' });
  if (action === 'rejeter') {
    if (prise.retenue) return reply.code(409).send({ error: 'La prise gardée ne se rejette pas : garde-en une autre.' });
    majPlanStoryboard(f.film.id, n, (p) => { p.rejetees = [...new Set([...(p.rejetees ?? []), prise.take])]; });
    return vuePrisesFilm(takes.get(f.film.id)!);
  }
  if (action === 'finaliser') {
    const brouillon = takes.get(prise.take);
    if (!brouillon || brouillon.status !== 'done') return reply.code(409).send({ error: 'Le brouillon n’est pas terminé.' });
    const bs = JSON.parse(brouillon.settings);
    const corps = { ...corpsFinalDe({ ...bs, prompt: bs.prompt }, plan.corps), app: 'nexora-prise', shotName: `${f.s.storyboard.titre.slice(0, 24)}_plan${n + 1}_final`, userPrompt: plan.resume };
    try {
      const ids = await lancerPrises(f.film.id, n, corps, 1, { finalDe: prise.take }, `Nexora Creative · finale plan ${n + 1}`);
      majPlanStoryboard(f.film.id, n, (p) => { p.extra = [...(p.extra ?? []), { take: ids[0], brouillon: false, finalDe: prise.take }]; });
    } catch (e) { return reply.code(402).send({ error: e instanceof Error ? e.message : 'Impossible de lancer la finale.' }); }
    return vuePrisesFilm(takes.get(f.film.id)!);
  }
  if (action === 'garder') {
    if (prise.statut !== 'done') return reply.code(409).send({ error: 'Cette prise n’est pas terminée.' });
    // Nouvelle version du film avec cette prise à la place : seul l'assemblage est refait, rien n'est re-rendu.
    const sb = structuredClone(f.s.storyboard);
    sb.plans = sb.plans.map((p: any, i: number) => ({ ...p, suite: false, ...(i === n ? { take: prise.take } : {}) }));
    const moteur = (f.s.moteur ?? 'h3-fast') as MoteurVideo;
    const filmId = await tournerFilm(sb, { format: f.s.format, son: !!f.s.son, intention: f.s.prompt, projectId: f.film.project_id, moteur, qualite: f.s.qualite }, null);
    takes.patchSettings(filmId, { versionDe: f.film.id, taille: [Number(plan.corps?.width) || 1344, Number(plan.corps?.height) || 768], ...(typeof f.s.musique === 'string' ? { musique: f.s.musique } : {}), transition: f.s.transition === 'fondu' ? 'fondu' : 'coupe' });
    void avancerFilm(filmId);
    return { ...vuePrisesFilm(takes.get(f.film.id)!), filmId };
  }
  return reply.code(400).send({ error: 'Action inconnue : garder, rejeter ou finaliser.' });
});

/**
 * « Montre-moi » : une image (jeton d'envoi) attachée à un plan comme référence. « depart » : la vidéo part de cette
 * image (I2VA) ; « composition » : image de cadrage et de placement pour le moteur cinéma (Ref2VA, <Picture N>).
 * Le résultat est un brouillon de plus pour ce plan (pas de transfert vidéo → vidéo : H3 ne sait pas le faire).
 */
app.post('/api/nexora/film/:id/plan/:n/reference', async (req, reply) => {
  const f = filmTerminePour((req.params as any).id, reply);
  if (!f) return;
  const n = Number((req.params as any).n);
  const b = (req.body ?? {}) as { jeton?: string; role?: string };
  const plan = f.s.storyboard.plans[n];
  if (!plan) return reply.code(404).send({ error: 'Plan introuvable.' });
  if (typeof b.jeton !== 'string' || !/^asset:[0-9a-f-]{36}$/i.test(b.jeton) || !(await eng.readInput(b.jeton))) return reply.code(400).send({ error: 'Envoie d’abord l’image de référence.' });
  const role = b.role === 'composition' ? 'composition' : 'depart';
  const sb = f.s.storyboard as Storyboard;
  const persos = role === 'composition' ? await resoudrePersonnages(intentionDuPlan(sb, n)) : null;
  const dureeS = (plan.duree === 10 ? 243 : 124) / 24;
  const dialogues = plan.replique ? { dialogues: [{ texte: plan.replique, langue: 'French' }] } : {};
  const llm = llmRedaction();
  let corps: any;
  if (role === 'depart') {
    const r = await reecrireH3({ intention: `${intentionDuPlan(sb, n)}\nThe video starts exactly from the provided first frame and continues the action from it.`, mode: 'i2va', dureeS, ...dialogues }, llm);
    corps = { ...corpsRendu({ intention: plan.resume, format: f.s.format, duree: plan.duree, son: !!f.s.son, qualite: 'rapide' }, r.prompt, 'h3-fast'), startImage: b.jeton, brouillon: true };
  } else {
    if (!moteurDuCompte('max')) return reply.code(422).send({ error: 'La composition par image demande le moteur cinéma, indisponible ici.' });
    const r = await reecrireH3({ intention: persos?.sujets.length ? persos.texteClair : intentionDuPlan(sb, n), mode: 't2va', dureeS, ...dialogues }, llm);
    const base = corpsRendu({ intention: plan.resume, format: f.s.format, duree: plan.duree, son: !!f.s.son, qualite: 'max' }, r.prompt, 'h3-max');
    const jetons = [...(persos?.jetons ?? []), b.jeton].slice(0, 4);
    corps = { ...base, refImages: jetons, prompt: convertirEnPromptRef(r.prompt, persos?.sujets ?? [], { composition: jetons.length - (persos?.jetons.length ?? 0) }), personnages: persos?.noms };
    corps = corpsBrouillonDe(corps, Math.floor(Math.random() * 1e9), corps);
  }
  Object.assign(corps, { app: 'nexora-prise', shotName: `${sb.titre.slice(0, 24)}_plan${n + 1}_ref`, userPrompt: plan.resume });
  try {
    const ids = await lancerPrises(f.film.id, n, corps, 1, { brouillon: true, reference: role }, `Nexora Creative · référence plan ${n + 1}`);
    majPlanStoryboard(f.film.id, n, (p) => { p.extra = [...(p.extra ?? []), { take: ids[0], brouillon: true, reference: role }]; });
  } catch (e) { return reply.code(402).send({ error: e instanceof Error ? e.message : 'Impossible de lancer cette prise.' }); }
  return vuePrisesFilm(takes.get(f.film.id)!);
});

/**
 * Projets longs (vague 2, squelette du long métrage) : un scénario devient séquences → scènes → plans (code), la bible de
 * continuité (style, personnages, lieux) est injectée dans chaque plan, le coût du projet entier est estimé avant tout
 * rendu, et les plans partent par lots (la file des moteurs fait le reste). Aucune limite de longueur : 90 minutes = 1 080
 * plans de 5 s. Les plans tournés s'assemblent dans la timeline du Mode Studio (/api/nexora/projet/:id/creations).
 */
const idProjet = (v: unknown) => (/^[0-9a-f-]{36}$/i.test(String(v)) ? String(v) : null);
function synchroniserProjet(p: ProjetLong): ProjetLong {
  let change = false;
  for (const { plan } of aplatir(p)) {
    if (plan.etat !== 'en_cours' || typeof plan.take !== 'number') continue;
    const t = takes.get(plan.take);
    if (t?.status === 'done') { plan.etat = 'tourne'; change = true; }
    else if (t?.status === 'failed' || t?.status === 'stopped') { plan.etat = 'echec'; change = true; }
  }
  if (change) projetsLongs.save(p);
  return p;
}
const resumeProjet = (p: ProjetLong) => {
  const e = estimerProjet(p, tarifDepuisEnv());
  return { id: p.id, titre: p.titre, format: p.format, qualite: p.qualite, plans: e.plans, tournes: e.tournes, estimation: e, creditsActifs: !!configAuth };
};

app.get('/api/nexora/projets', async () => ({ projets: projetsLongs.list<ProjetLong>().map((p) => resumeProjet(synchroniserProjet(p))) }));

app.post('/api/nexora/projet', async (req, reply) => {
  const b = (req.body ?? {}) as any;
  const titre = typeof b.titre === 'string' ? b.titre.trim().slice(0, 120) : '';
  const scenario = typeof b.scenario === 'string' ? b.scenario.trim() : '';
  if (!titre) return reply.code(400).send({ error: 'Donne un titre au projet.' });
  if (scenario.length < 20) return reply.code(400).send({ error: 'Colle le scénario (au moins quelques lignes) : séquences, scènes (INT./EXT.) et paragraphes d’action.' });
  const verdict = await moderer(scenario.slice(0, 8000), llmCourant(), (m) => app.log.warn(m));
  if (!verdict.ok) return reply.code(422).send({ error: verdict.raison, categorie: verdict.categorie });
  const sequences = scenarioVersArbre(scenario, b.duree === 10 ? 10 : 5);
  if (!aplatir({ sequences } as ProjetLong).length) return reply.code(400).send({ error: 'Aucun plan trouvé dans ce scénario.' });
  const bible = b.bible ?? {};
  const p: ProjetLong = {
    id: randomUUID(), titre, scenario, cree: new Date().toISOString(),
    format: b.format === '9:16' || b.format === '1:1' ? b.format : '16:9', qualite: b.qualite === 'max' ? 'max' : 'rapide',
    bible: {
      style: String(bible.style ?? '').slice(0, 400), notes: String(bible.notes ?? '').slice(0, 800),
      // Les personnages @ de l'organisation entrent dans la bible : leurs images partent en Ref2VA à chaque plan qui les nomme.
      personnages: [...castDb.list().filter((m) => m.kind === 'character').map((m) => ({ nom: m.name, description: m.notes })), ...(Array.isArray(bible.personnages) ? bible.personnages.slice(0, 50).map((x: any) => ({ nom: String(x?.nom ?? '').slice(0, 60), description: String(x?.description ?? '').slice(0, 400) })).filter((x: any) => x.nom) : [])],
      lieux: (Array.isArray(bible.lieux) ? bible.lieux.slice(0, 100) : []).map((x: any) => ({ nom: String(x?.nom ?? '').slice(0, 60), description: String(x?.description ?? '').slice(0, 400) })).filter((x: any) => x.nom),
    },
    sequences,
  };
  projetsLongs.save(p);
  return { ...resumeProjet(p), arbre: p.sequences.map((s) => ({ id: s.id, titre: s.titre, scenes: s.scenes.map((c) => ({ id: c.id, titre: c.titre, plans: c.plans.length })) })), bible: p.bible };
});

app.get('/api/nexora/projet/:id', async (req, reply) => {
  const id = idProjet((req.params as any).id);
  const p = id ? projetsLongs.get<ProjetLong>(id) : undefined;
  if (!p) return reply.code(404).send({ error: 'Projet introuvable.' });
  synchroniserProjet(p);
  return { ...resumeProjet(p), bible: p.bible, arbre: p.sequences.map((s) => ({ id: s.id, titre: s.titre, scenes: s.scenes.map((c) => ({ id: c.id, titre: c.titre, plans: c.plans.map((x) => ({ id: x.id, resume: x.resume, duree: x.duree, etat: x.etat, take: x.take ?? null })) })) })) };
});

app.put('/api/nexora/projet/:id', async (req, reply) => {
  const id = idProjet((req.params as any).id);
  const p = id ? projetsLongs.get<ProjetLong>(id) : undefined;
  if (!p) return reply.code(404).send({ error: 'Projet introuvable.' });
  const b = (req.body ?? {}) as any;
  if (b.bible && typeof b.bible === 'object') {
    if (typeof b.bible.style === 'string') p.bible.style = b.bible.style.slice(0, 400);
    if (typeof b.bible.notes === 'string') p.bible.notes = b.bible.notes.slice(0, 800);
  }
  if (b.qualite === 'rapide' || b.qualite === 'max') p.qualite = b.qualite;
  projetsLongs.save(p);
  return resumeProjet(p);
});

/** Tourne le lot suivant (8 plans par défaut, 50 au plus par appel) : prompt H3 écrit avec la bible, personnages @ en Ref2VA. */
app.post('/api/nexora/projet/:id/lancer', async (req, reply) => {
  const id = idProjet((req.params as any).id);
  const p = id ? projetsLongs.get<ProjetLong>(id) : undefined;
  if (!p) return reply.code(404).send({ error: 'Projet introuvable.' });
  synchroniserProjet(p);
  const lot = prochainLot(p, Math.min(50, Number((req.body as any)?.taille) || 8));
  if (!lot.length) return reply.code(409).send({ error: 'Tous les plans sont déjà tournés ou en cours.' });
  const moteur = moteurDuCompte(p.qualite);
  if (!moteur) return reply.code(422).send({ error: REFUS_TERRITOIRE });
  const demandeDe = (x: PlanProjet) => ({ intention: x.resume, format: p.format, duree: x.duree, son: true, qualite: p.qualite });
  const cout = lot.reduce((n, x) => n + devisCredits(corpsRendu(demandeDe(x.plan), '', moteur), tarifDepuisEnv()), 0);
  const secondes = lot.reduce((n, x) => n + secondesGpuEstimees(corpsRendu(demandeDe(x.plan), '', moteur)), 0);
  const refus = depassement({ credits: configAuth ? cout : null, secondesGpu: secondes }, PLAFOND_PRODUCTEUR);
  if (refus) return reply.code(409).send({ error: `${refus} Lance un lot plus petit.`, cout, secondes });
  const llm = llmRedaction();
  const cast = castDb.list().filter((m) => m.kind === 'character');
  const lances: number[] = [];
  try {
    const textes = lot.map((x) => {
      let t = intentionDuPlanProjet(p, x);
      for (const m of cast) t = t.replace(new RegExp(`\\b${m.name.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')}\\b`, 'g'), `@${m.name}`);
      return t;
    });
    const persos = await Promise.all(textes.map((t) => (moteur === 'h3-max' ? resoudrePersonnages(t) : null)));
    const ecrits = await Promise.all(lot.map((x, i) => reecrireH3({ intention: persos[i]?.sujets.length ? persos[i]!.texteClair : textes[i].replace(/@/g, ''), mode: 't2va', dureeS: (x.plan.duree === 10 ? 243 : 124) / 24, ...(x.plan.replique ? { dialogues: [{ texte: x.plan.replique, langue: 'French' }] } : {}) }, llm)));
    for (let i = 0; i < lot.length; i++) {
      const x = lot[i];
      const corps: any = {
        ...corpsRendu(demandeDe(x.plan), ecrits[i].prompt, moteur),
        ...(persos[i]?.sujets.length ? { prompt: convertirEnPromptRef(ecrits[i].prompt, persos[i]!.sujets), refImages: persos[i]!.jetons, personnages: persos[i]!.noms } : {}),
        app: 'nexora-projet', userPrompt: x.plan.resume, projetLong: p.id, projetPlan: x.plan.id, promptSource: ecrits[i].source,
        shotName: `${p.titre.slice(0, 24)}_${x.plan.id}`,
      };
      const r = await reserverPrise(corps, `Nexora Creative · projet « ${p.titre.slice(0, 40)} » · ${x.plan.id}`);
      if (r.refus) { if (!lances.length) return reply.code(402).send({ error: r.refus }); break; }
      const [take] = await queueTakes(corps, 1);
      if (r.reservation) takes.patchSettings(take, { nexoraCredits: r.reservation });
      x.plan.take = take; x.plan.prises = [...(x.plan.prises ?? []), take]; x.plan.etat = 'en_cours';
      lances.push(take);
    }
  } finally {
    projetsLongs.save(p);
  }
  return { lances: lances.length, takes: lances, cout, secondes, projet: resumeProjet(p) };
});

app.get('/api/nexora/projet/:id/creations', async (req, reply) => {
  const id = idProjet((req.params as any).id);
  const p = id ? projetsLongs.get<ProjetLong>(id) : undefined;
  if (!p) return reply.code(404).send({ error: 'Projet introuvable.' });
  synchroniserProjet(p);
  return {
    creations: ordreAssemblage(p).map((x, i) => {
      const t = takes.get(x.take);
      return { id: x.take, genre: 'video', nom: `${String(i + 1).padStart(4, '0')} · ${x.sequence} · ${x.scene}`.slice(0, 120), url: `/api/media/${x.take}`, date: t?.created_at ?? '', dureeS: undefined };
    }),
  };
});

app.delete('/api/nexora/projet/:id', async (req, reply) => {
  const id = idProjet((req.params as any).id);
  if (!id || !projetsLongs.get(id)) return reply.code(404).send({ error: 'Projet introuvable.' });
  projetsLongs.delete(id);
  return { ok: true };
});

/** Projet de montage d'un film : plans MP4 + séquence FCP7 XML + storyboard Nexora, dans un ZIP. */
app.get('/api/nexora/film/:id/projet', async (req, reply) => {
  const film = takes.get(Number((req.params as any).id));
  if (!film || film.status !== 'done') return reply.code(404).send({ error: 'Film introuvable ou pas terminé.' });
  const s = JSON.parse(film.settings);
  if (!s.film) return reply.code(400).send({ error: 'Ce n’est pas un film.' });
  const { mkdtemp, copyFile, writeFile, rm } = await import('fs/promises');
  const { tmpdir } = await import('os');
  const dossier = await mkdtemp(join(tmpdir(), `nexora-projet-${film.id}-`));
  const plans: { fichier: string; images: number; nom: string }[] = [];
  let largeur = 832, hauteur = 480;
  for (const [i, p] of (s.storyboard.plans as any[]).entries()) {
    const t = p.take ? takes.get(p.take) : undefined;
    if (!t?.output_path || !existsSync(t.output_path)) return reply.code(409).send({ error: `Le plan ${i + 1} n’a plus de fichier.` });
    const nom = `plan${String(i + 1).padStart(2, '0')}.mp4`;
    await copyFile(t.output_path, join(dossier, nom));
    const m = await probeMedia(t.output_path);
    largeur = m.w; hauteur = m.h;
    plans.push({ fichier: nom, images: m.frames, nom: String(p.resume ?? nom) });
  }
  await writeFile(join(dossier, 'sequence-fcp7.xml'), xmlFcp7({ titre: s.storyboard.titre ?? film.shot_name, largeur, hauteur, son: !!s.son, plans }));
  await writeFile(join(dossier, 'projet-nexora.json'), JSON.stringify({ format: 'nexora.film/1', titre: s.storyboard.titre, storyboard: s.storyboard, transition: s.transition ?? 'coupe', moteur: s.moteur }, null, 2));
  await writeFile(join(dossier, 'LISEZMOI.txt'), 'Projet exporté de Nexora Creative.\n\nPremiere Pro : Fichier > Importer > sequence-fcp7.xml\nDaVinci Resolve : Fichier > Importer > Chronologie > sequence-fcp7.xml\nFinal Cut Pro : Fichier > Importer > XML (converti par l’outil 7toX si nécessaire)\nLes plans (planNN.mp4) doivent rester à côté du fichier XML.\n');
  const zip = join(dossier, 'projet.zip');
  const { execFile } = await import('child_process');
  await new Promise<void>((ok, ko) => execFile('zip', ['-q', '-0', '-j', zip, ...plans.map((x) => join(dossier, x.fichier)), join(dossier, 'sequence-fcp7.xml'), join(dossier, 'projet-nexora.json'), join(dossier, 'LISEZMOI.txt')], (err) => (err ? ko(err) : ok())));
  reply.header('content-type', 'application/zip');
  reply.header('content-disposition', `attachment; filename="${safeShotName(film.shot_name || 'film')}_projet.zip"`);
  const flux = createReadStream(zip);
  flux.on('close', () => void rm(dossier, { recursive: true, force: true }));
  return reply.send(flux);
});

app.get('/api/nexora/etat', async () => {
  const moteur = moteurDuCompte('rapide');
  return {
    llm: !!llmCourant() || Object.values(paliersDisponibles()).some(Boolean), paliers: paliersDisponibles(), moteur: moteur ? 'MiniMax H3' : null, son: !!moteur, territoire: territoireDuCompte(),
    cinema: moteurDuCompte('max') === 'h3-max', ...(moteur ? {} : { erreur: REFUS_TERRITOIRE }),
    image: modeleImage() ? (modeleImage() === 'qwen21' ? 'Qwen-Image-2.1' : 'Qwen-Image-2512') : null,
    musique: eng.recettesEnLigne().has('music3') ? 'MiniMax-Music3' : null,
    detourage: eng.moteurs.some((m) => !!m.detourageUrl),
    objet3d: eng.recettesEnLigne().has('objet-apercu') || eng.recettesEnLigne().has('*') ? { nom: PRODUIT_3D, formats: FORMATS_RELIEF, multivue: eng.moteursPour(recetteMultivue()).length > 0, vuesMax: Math.max(2, Math.min(4, Number(process.env.NEXORA_RELIEF_VUES_MAX) || 3)), apercu: true, qualite: eng.recettesEnLigne().has('objet-qualite') || eng.recettesEnLigne().has('*'), texte: !!modeleImage() || eng.recettesEnLigne().has('*') } : null,
  };
});

/**
 * Image de plan clé : une phrase → prompt d'image écrit par le LLM → Qwen-Image sur le GPU qui porte l'image (GB10).
 * Modèle : Qwen-Image-2.1 dès qu'il est en ligne, sinon Qwen-Image-2512 en repli.
 */
function modeleImage(): 'qwen21' | 'qwen' | null {
  const enLigne = eng.recettesEnLigne();
  return enLigne.has('qwen21') ? 'qwen21' : enLigne.has('qwen') ? 'qwen' : null;
}
app.post('/api/nexora/image', async (req, reply) => {
  const b = (req.body ?? {}) as any;
  const intention = typeof b.intention === 'string' ? b.intention.trim() : '';
  if (!intention) return reply.code(400).send({ error: 'Décris l’image que tu veux.' });
  if (intention.length > 4000) return reply.code(400).send({ error: 'Description trop longue (4 000 caractères au plus).' });
  const verdict = await moderer(intention, llmCourant(), (m) => app.log.warn(m));
  if (!verdict.ok) return reply.code(422).send({ error: verdict.raison, categorie: verdict.categorie });
  const format = b.format === '9:16' || b.format === '1:1' ? b.format : '16:9';
  const modele = modeleImage() ?? 'qwen21';
  const dims = modele === 'qwen21'
    ? { '16:9': [1792, 1024], '9:16': [1024, 1792], '1:1': [1536, 1536] }[format as '16:9']
    : { '16:9': [1328, 752], '9:16': [752, 1328], '1:1': [1024, 1024] }[format as '16:9'];
  const r = await reecrireImage(intention, llmCourant(), format);
  const nb = Math.max(1, Math.min(4, Number(b.nombre) || 1));
  const corps: any = {
    kind: 'still', model: modele, quality: b.qualite === 'rapide' ? 'draft' : 'quality',
    prompt: r.prompt, width: dims[0], height: dims[1], count: nb,
    intention, promptSource: r.source, app: 'nexora-image', shotName: intention.slice(0, 60),
  };
  const res = await generate(corps, reply);
  if (reply.sent || (res && (res as any).error)) return res;
  return { ...res, prompt: r.prompt, source: r.source, modele: modele === 'qwen21' ? 'Qwen-Image-2.1' : 'Qwen-Image-2512' };
});

/**
 * Mode 3D (TRELLIS.2 sur la GB10, recettes « objet-apercu » et « objet-qualite »).
 * Image → 3D passe par /api/generate (kind « object »). Texte → 3D : une image de référence propre (objet seul, fond uni)
 * par Qwen-Image, puis TRELLIS.2, puis le juge visuel note quatre côtés de l'objet ; une relance au plus si la note est basse.
 * L'avancement est piloté par le statut (GET) : idempotent et sans état en mémoire, un redémarrage ne perd rien.
 * Chaque prise GPU porte sa propre réservation de crédits, validée ou libérée par la boucle de réconciliation.
 */
app.post('/api/nexora/objet/devis', async (req) => {
  const b = (req.body ?? {}) as any;
  const q: QualiteObjet = b.qualite === 'quality' && b.source !== 'vues' ? 'quality' : 'draft';
  const multi = b.source === 'vues';
  const secondes = b.source === 'texte' ? secondesTexteVers3D(q) : multi ? MESURES_OBJET_PC5.multivue : secondesObjet(q);
  const t = tarifDepuisEnv();
  // Crédits sur la mesure de la GB10 (le client ne paie pas plus cher parce que le brouillon déborde sur un Turing) ; le temps
  // annoncé est celui du moteur que le routage choisirait maintenant.
  const recette = multi ? recetteMultivue() : recetteObjet(q);
  const moteur = eng.moteursPour(recette)[0];
  const sec = b.source === 'texte' ? secondes : (moteur?.secondes?.[recette] ?? secondes);
  const enFile = eng.moteursPour(recette).length > 1;
  return { secondesEstimees: sec, credits: configAuth ? Math.max(1, Math.ceil(secondes * t.creditsParSecondeGpu)) : null, recette, moteur: moteur ? { id: moteur.id, nom: moteur.nom } : null, debordement: q === 'draft' && enFile, produit: PRODUIT_3D };
});

/** Réserve le devis d'une prise GPU lancée par le serveur, puis la met en file. */
async function lancerPriseNexora(corps: any, libelle: string, devis: number): Promise<{ ok: true; takeId: number } | { ok: false; message: string }> {
  const fac = facturationCourante();
  let res: CreditsPrise | null = null;
  if (fac) {
    const r = await fac.reserver({ idempotence: randomUUID(), credits: devis, libelle });
    if (!r.ok) return { ok: false, message: r.message };
    res = { reservationId: r.reservationId, credits: r.credits, etat: 'reservee' };
  }
  try {
    const [takeId] = await queueTakes(corps, 1);
    if (res) takes.patchSettings(takeId, { nexoraCredits: res });
    return { ok: true, takeId };
  } catch (e) {
    if (res) await fac?.liberer(res.reservationId).catch(() => {});
    return { ok: false, message: e instanceof Error ? e.message : 'lancement impossible' };
  }
}

app.post('/api/nexora/objet/texte', async (req, reply) => {
  const b = (req.body ?? {}) as any;
  const intention = typeof b.intention === 'string' ? b.intention.trim() : '';
  if (intention.length < 3) return reply.code(400).send({ error: 'Décris l’objet que tu veux en 3D (une chaise en bois, un robot jouet…).' });
  if (intention.length > 1000) return reply.code(400).send({ error: 'Description trop longue (1 000 caractères au plus).' });
  const verdict = await moderer(intention, llmCourant(), (m) => app.log.warn(m));
  if (!verdict.ok) return reply.code(422).send({ error: verdict.raison, categorie: verdict.categorie });
  const qualite: QualiteObjet = b.qualite === 'quality' ? 'quality' : 'draft';
  const manque = await blockingReasonFor(eng.isLocal() && eng.recetteSurPrincipal(recetteObjet(qualite)), bundlesFor({ kind: 'object' }));
  if (manque) return reply.code(412).send({ error: manque });
  const modele = modeleImage() ?? 'qwen21';
  const corps: any = {
    kind: 'still', model: modele, quality: 'quality', prompt: promptReferenceObjet(intention), width: 1024, height: 1024, count: 1,
    intention, app: 'nexora-objet-ref', shotName: `objet_${intention.slice(0, 40)}`,
  };
  const res = await generate(corps, reply);
  if (reply.sent || (res && (res as any).error)) return res;
  const id = (res as any).takeIds[0] as number;
  const etat: EtatTexte3D = { phase: 'image', essai: 1, tentatives: [], notes: [] };
  takes.patchSettings(id, { objet3d: { intention, qualite, etat } });
  return { id, secondesEstimees: secondesTexteVers3D(qualite), credits: (res as any).credits };
});

const chaines3d = new Set<number>();

async function avancerTexte3D(id: number): Promise<void> {
  for (let tour = 0; tour < 5; tour++) {
    const t = takes.get(id);
    const o = t ? JSON.parse(t.settings).objet3d : null;
    if (!t || !o) return;
    const e = o.etat as EtatTexte3D;
    const derniere = e.tentatives[e.tentatives.length - 1];
    const etape = prochaineEtapeTexte3D(e, { image: t.status as any, objet: derniere ? (takes.get(derniere)?.status as any) : undefined });
    const ecrire = (patch: Record<string, unknown>) => takes.patchSettings(id, { objet3d: { ...o, ...patch, etat: { ...e, ...(patch.etat as object ?? {}) } } });
    if (etape.action === 'attendre') return;
    if (etape.action === 'echec') { ecrire({ erreur: etape.motif, etat: { phase: 'echec' } }); return; }
    if (etape.action === 'finir') { ecrire({ retenu: etape.retenu, etat: { phase: 'fini' } }); return; }
    if (etape.action === 'lancer-objet') {
      const q: QualiteObjet = o.qualite;
      const r = await lancerPriseNexora(
        { kind: 'object', app: 'nexora-objet', quality: q, sourceTake: id, removeBackground: true, tournette: TOURNETTE_JUGE.frames, ...(etape.essai > 1 ? { seed: Math.floor(Math.random() * 1e9) } : {}),
          shotName: `objet3d_${String(o.intention).slice(0, 30)}`, userPrompt: `3D : ${String(o.intention).slice(0, 80)}`, nexoraObjetDe: id },
        'Nexora Creative · objet 3D', Math.max(1, Math.ceil(secondesObjet(q) * tarifDepuisEnv().creditsParSecondeGpu)));
      if (!r.ok) { ecrire({ erreur: r.message, etat: { phase: 'echec' } }); return; }
      ecrire({ etat: { phase: 'objet', essai: etape.essai, tentatives: [...e.tentatives, r.takeId] } });
      continue;
    }
    // juger : quatre côtés tirés de la tournette, une note du juge ; sans juge ou sans tournette, l'objet est gardé tel quel
    const objet = takes.get(derniere);
    let note: { take: number; note: number } | null = null;
    let verdict: Awaited<ReturnType<typeof evaluerRelief>> = null;
    try {
      const tournette = objet?.output_path ? `${objet.output_path}.turntable.mp4` : '';
      if (tournette && existsSync(tournette)) {
        verdict = await evaluerRelief(derniere, String(o.intention), tournette);
      }
    } catch (err) {
      app.log.warn(`[objet3d] juge indisponible : ${err instanceof Error ? err.message : err}`);
    }
    if (verdict) note = { take: derniere, note: verdict.note };
    const decision = decisionApresJuge(e.essai, verdict);
    const jugements = [...(o.jugements ?? []), ...(verdict ? [{ take: derniere, ...verdict }] : [])];
    ecrire({ jugements, etat: { phase: 'jugement', notes: note ? [...e.notes, note] : e.notes } });
    if (decision === 'garder' && !note) { ecrire({ jugements, retenu: derniere, etat: { phase: 'fini', notes: e.notes } }); return; }
  }
}

app.get('/api/nexora/objet/:take', async (req, reply) => {
  const id = Number((req.params as any).take);
  const lire = () => { const t = takes.get(id); return t ? { t, o: JSON.parse(t.settings).objet3d } : null; };
  let cur = lire();
  if (!cur?.o) return reply.code(404).send({ error: 'Création 3D introuvable.' });
  if (cur.o.etat.phase !== 'fini' && cur.o.etat.phase !== 'echec' && !chaines3d.has(id)) {
    chaines3d.add(id);
    try { await avancerTexte3D(id); } finally { chaines3d.delete(id); }
    cur = lire()!;
  }
  const { t, o } = cur;
  const e = o.etat as EtatTexte3D;
  return {
    etat: e.phase, essai: e.essai, image: t.id, objet: e.phase === 'fini' ? o.retenu : e.tentatives[e.tentatives.length - 1] ?? null,
    notes: o.jugements ?? [], erreur: o.erreur ?? null, qualite: o.qualite, intention: o.intention,
  };
});

// ---------- Relief : rapport, exports, cartes PBR, GIF de la tournette, juge ----------

type PriseRelief = { id: number; glb: string; t: NonNullable<ReturnType<typeof takes.get>> };
function priseRelief(req: FastifyRequest, reply: FastifyReply): PriseRelief | null {
  const id = Number((req.params as any).take);
  const t = takes.get(id);
  if (!t?.output_path || !/\.glb$/i.test(t.output_path) || t.status !== 'done') { void reply.code(404).send({ error: `${PRODUIT_3D} : modèle introuvable ou pas encore prêt.` }); return null; }
  if (!existsSync(t.output_path)) { void reply.code(410).send({ error: 'Le fichier du modèle n’est plus sur le disque.' }); return null; }
  return { id, glb: t.output_path, t };
}
const execFichier = (bin: string, args: string[]) => new Promise<string>((ok, ko) => execFile(bin, args, { maxBuffer: 1 << 24 }, (e, o, err) => (e ? ko(new Error(String(err).slice(-300))) : ok(String(o)))));
const enCalculRelief = new Map<string, Promise<unknown>>();
/** Un calcul à la fois par fichier de sortie : deux demandes identiques partagent le même travail. */
function unSeulCalcul<T>(cle: string, travail: () => Promise<T>): Promise<T> {
  const en = enCalculRelief.get(cle) as Promise<T> | undefined;
  if (en) return en;
  const p = travail().finally(() => enCalculRelief.delete(cle));
  enCalculRelief.set(cle, p);
  return p;
}

app.get('/api/nexora/relief/:take/rapport', async (req, reply) => {
  const p = priseRelief(req, reply); if (!p) return;
  const q = req.query as any;
  const dir = `${p.glb}.relief`;
  mkdirSync(dir, { recursive: true });
  const octets = readFileSync(p.glb);
  const lire = async (cible: number | null) => {
    const fichier = join(dir, `rapport-${cible ?? 'plein'}.json`);
    if (existsSync(fichier)) return JSON.parse(readFileSync(fichier, 'utf8'));
    const r = await unSeulCalcul(fichier, async () => analyser(await lireGlb(cible ? await decimerGlb(octets, cible) : octets)));
    writeFileSync(fichier, JSON.stringify(r));
    return r;
  };
  const plein = await lire(null);
  const cible = cibleTriangles(q.faces, plein.triangles);
  const s = JSON.parse(p.t.settings ?? '{}');
  return {
    rapport: plein, decime: cible ? await lire(cible) : null, cible,
    formats: FORMATS_RELIEF, extensions: EXTENSION_RELIEF, tailleMm: TAILLE_MM_DEFAUT,
    // Les exports sont calculés par le serveur (CPU, quelques secondes) : aucun crédit GPU.
    credits: 0, juge: s.relief?.juge ?? null,
  };
});

app.get('/api/nexora/relief/:take/export', async (req, reply) => {
  const p = priseRelief(req, reply); if (!p) return;
  const q = req.query as any;
  const format = String(q.format ?? 'glb').toLowerCase() as FormatRelief;
  if (!FORMATS_RELIEF.includes(format)) return reply.code(400).send({ error: `Format inconnu : ${FORMATS_RELIEF.join(', ')}.` });
  const taille = Math.max(1, Math.min(2000, Number(q.taille) || TAILLE_MM_DEFAUT));
  const dir = `${p.glb}.relief`;
  mkdirSync(dir, { recursive: true });
  const octets = readFileSync(p.glb);
  const cible = cibleTriangles(q.faces, analyser(await lireGlb(octets)).triangles);
  const fichier = join(dir, `export-${format}-${cible ?? 'plein'}-${taille}.${EXTENSION_RELIEF[format]}`);
  if (!existsSync(fichier)) {
    const sortie = await unSeulCalcul(fichier, () => exporter(octets, format, { nom: `relief-${p.id}`, tailleMm: taille, cible }));
    writeFileSync(fichier, sortie);
  }
  reply.headers({ 'Content-Type': TYPE_MIME_RELIEF[format === 'obj' ? 'zip' : format], 'Content-Length': statSync(fichier).size, 'Content-Disposition': `attachment; filename="relief-${p.id}${cible ? `-${cible}` : ''}.${EXTENSION_RELIEF[format]}"` });
  return reply.send(createReadStream(fichier));
});

app.get('/api/nexora/relief/:take/cartes', async (req, reply) => {
  const p = priseRelief(req, reply); if (!p) return;
  const c = await cartesPbr(readFileSync(p.glb));
  return { cartes: c.map((x) => ({ nom: x.nom, mime: x.mime, largeur: x.largeur, octets: x.octets.length })) };
});
app.get('/api/nexora/relief/:take/cartes/:nom', async (req, reply) => {
  const p = priseRelief(req, reply); if (!p) return;
  const c = (await cartesPbr(readFileSync(p.glb))).find((x) => x.nom === (req.params as any).nom);
  if (!c) return reply.code(404).send({ error: 'Carte absente de ce modèle.' });
  reply.headers({ 'Content-Type': c.mime, 'Cache-Control': 'max-age=86400' });
  return reply.send(Buffer.from(c.octets));
});

/** GIF animé de la tournette (palette optimisée, 384 px de large) ; la vignette est l'affiche déjà servie par /api/poster/:id. */
app.get('/api/nexora/relief/:take/gif', async (req, reply) => {
  const p = priseRelief(req, reply); if (!p) return;
  const tournette = `${p.glb}.turntable.mp4`;
  if (!existsSync(tournette)) return reply.code(404).send({ error: 'Ce modèle n’a pas de tournette.' });
  const gif = `${p.glb}.relief/tournette.gif`;
  mkdirSync(dirname(gif), { recursive: true });
  if (!existsSync(gif)) await unSeulCalcul(gif, () => execFichier(config.ffmpegBin, argsGif(tournette, gif)));
  reply.headers({ 'Content-Type': 'image/gif', 'Content-Length': statSync(gif).size, 'Content-Disposition': `${(req.query as any).download ? 'attachment' : 'inline'}; filename="relief-${p.id}.gif"` });
  return reply.send(createReadStream(gif));
});

/**
 * Juge de Relief : quatre côtés de la tournette, une note de 0 à 10, les jetons mesurés un à un et facturés comme les autres
 * appels LLM (réservation au plafond du devis, règlement du réel, ligne au grand livre). Sans LLM : null, rien n'est dû.
 */
async function evaluerRelief(takeId: number, description: string, tournette: string): Promise<(VerdictVues & { credits: number }) | null> {
  const llm = llmCourant();
  if (!llm || !existsSync(tournette)) return null;
  let images: readonly number[] = TOURNETTE_JUGE.images;
  try {
    const n = Number((await execFichier(config.ffprobeBin, ['-v', 'error', '-select_streams', 'v:0', '-count_packets', '-show_entries', 'stream=nb_read_packets', '-of', 'csv=p=0', tournette])).trim());
    if (n >= 4) images = indicesQuatreVues(n);
  } catch { /* huit images par défaut */ }
  const planche = await plancheVuesDataUrl(config.ffmpegBin, tournette, `${tournette}.vues.jpg`, images);
  const compte = compteCourant();
  const t0 = Date.now();
  const { resultat, bilan } = await executerSousReservation(
    { fac: facturationCourante(), devis: devisJuge3d(), ctx: { run: randomUUID(), tache: 'juge3d', projet: String(takeId), utilisateur: compte?.utilisateurId, organisation: compte?.organisationId }, livre: livreUsage },
    async (rel) => {
      const v = await jugerVuesObjet(llm, description, planche);
      const u = v?.usage;
      if (u && u.entree + u.sortie > 0) {
        rel.apres({ role: 'juge3d', palier: 'direct', modele: u.modele, endpoint: 'passerelle', usage: { entree: u.entree, sortie: u.sortie, raisonnement: 0, coutFournisseurUsd: null }, coutUsd: coutJuge3dUsd(u), source: 'tarif', ms: Date.now() - t0, repli: false });
      }
      return v;
    },
  );
  return resultat ? { ...resultat, credits: bilan.totaux.credits } : null;
}

app.post('/api/nexora/relief/:take/juger', async (req, reply) => {
  const p = priseRelief(req, reply); if (!p) return;
  const tournette = `${p.glb}.turntable.mp4`;
  if (!existsSync(tournette)) return reply.code(404).send({ error: 'Pas de tournette à juger : refais le modèle.' });
  const s = JSON.parse(p.t.settings ?? '{}');
  const description = String(s.objet3d?.intention ?? (typeof s.userPrompt === 'string' && s.userPrompt.startsWith('3D: ') ? s.userPrompt.slice(4) : 'a 3D object reconstructed from one photo')).slice(0, 600);
  let v: Awaited<ReturnType<typeof evaluerRelief>>;
  try { v = await evaluerRelief(p.id, description, tournette); } catch (e) { return reply.code(502).send({ error: `Le juge n’a pas pu répondre (${e instanceof Error ? e.message : 'erreur'}).` }); }
  if (!v) return reply.code(503).send({ error: 'Aucun modèle vision n’est branché : le juge est indisponible.' });
  const juge = { note: v.note, defauts: v.defauts, raison: v.raison, modele: v.usage?.modele ?? null, jetons: v.usage ? v.usage.entree + v.usage.sortie : 0, credits: v.credits, le: new Date().toISOString() };
  takes.patchSettings(p.id, { relief: { ...(s.relief ?? {}), juge } });
  return { ...juge, relancer: v.note < NOTE_MINIMALE };
});

/**
 * Personnages @ (Soul ID) : « Créer un personnage » dessine une fiche standard avec Qwen-Image (fond gris, corps entier à
 * gauche, gros plan à droite) ; quand la prise est prête, la fiche est découpée en deux références et enregistrée comme
 * élément nommé (Cast, « character »). Le statut finalise de façon idempotente : un redémarrage ne perd rien.
 */
app.post('/api/nexora/personnage', async (req, reply) => {
  const b = (req.body ?? {}) as any;
  const nom = castName(b.nom);
  const description = typeof b.description === 'string' ? b.description.trim() : '';
  if (!NAME_OK.test(nom)) return reply.code(400).send({ error: 'Donne-lui un nom : lettres, chiffres et espaces, 40 caractères au plus.' });
  if (castDb.byName(nom)) return reply.code(409).send({ error: `Il existe déjà un élément nommé ${nom}.` });
  if (description.length < 8 || description.length > 600) return reply.code(400).send({ error: 'Décris le personnage (âge, visage, cheveux, tenue) en 8 à 600 caractères.' });
  const verdict = await moderer(description, llmCourant(), (m) => app.log.warn(m));
  if (!verdict.ok) return reply.code(422).send({ error: verdict.raison, categorie: verdict.categorie });
  // L'apparence est gardée en anglais : elle sert aux prompts H3 (subject_definitions) et à la fiche.
  let apparence = description;
  const llm = llmCourant();
  if (llm) {
    try {
      apparence = (await llm.completer('redaction', [
        { role: 'system', content: 'Translate and tighten this character description into one English sentence of at most 40 words (age, face, hair, build, outfit). Keep every detail, add nothing, no names, no preamble. Answer with the sentence only.' },
        { role: 'user', content: description },
      ], { temperature: 0.2, maxTokens: 300 })).trim().replace(/^["“]|["”]$/g, '').slice(0, 400);
    } catch { /* description brute */ }
  }
  const modele = modeleImage() ?? 'qwen21';
  const dims = modele === 'qwen21' ? [1792, 1024] : [1328, 752];
  const corps: any = {
    kind: 'still', model: modele, quality: 'quality', prompt: promptFiche(apparence), width: dims[0], height: dims[1], count: 1,
    app: 'nexora-personnage', shotName: `fiche_${nom}`.slice(0, 40), intention: description,
    personnage: { nom, apparence },
  };
  const res = await generate(corps, reply);
  if (reply.sent || (res && (res as any).error)) return res;
  return { takeId: (res as any).takeIds?.[0], nom, apparence };
});

app.get('/api/nexora/personnage/:take', async (req, reply) => {
  const t = takes.get(Number((req.params as any).take));
  const s = t ? JSON.parse(t.settings) : null;
  if (!t || !s?.personnage) return reply.code(404).send({ error: 'Fiche introuvable.' });
  if (typeof s.membre === 'number' && castDb.get(s.membre)) return { etat: 'pret', membre: castOut(castDb.get(s.membre)!) };
  if (t.status === 'failed' || t.status === 'stopped') return { etat: 'echec', erreur: t.error ?? 'Le dessin a échoué.' };
  if (t.status !== 'done' || !t.output_path || !existsSync(t.output_path)) return { etat: 'rendu' };
  try {
    const { nom, apparence } = s.personnage as { nom: string; apparence: string };
    if (castDb.byName(nom)) return reply.code(409).send({ error: `Il existe déjà un élément nommé ${nom}.` });
    const dims = imageDims(readFileSync(t.output_path)) ?? { w: 1792, h: 1024 };
    const d = decoupeFiche(dims.w, dims.h);
    const dossier = join(config.outputDir, 'films', 'images');
    mkdirSync(dossier, { recursive: true });
    const refs = [];
    for (const [nomVue, r] of [['corps', d.corps], ['visage', d.visage]] as const) {
      const fichier = join(dossier, `fiche_${t.id}_${nomVue}.png`);
      await new Promise<void>((ok, ko) => execFile(config.ffmpegBin, ['-y', '-i', t.output_path!, '-vf', `crop=${r[2]}:${r[3]}:${r[0]}:${r[1]}`, '-frames:v', '1', '-update', '1', fichier], (err, _o, e) => (err ? ko(new Error(String(e).split('\n').slice(-2).join(' '))) : ok())));
      refs.push(await storeRef(nom, readFileSync(fichier), `${nomVue}.png`));
    }
    const id = castDb.create({ name: nom, kind: 'character', refs, notes: String(apparence).slice(0, 1200) });
    takes.patchSettings(t.id, { membre: id });
    return { etat: 'pret', membre: castOut(castDb.get(id)!) };
  } catch (e) {
    return reply.code(500).send({ error: `Fiche non enregistrée : ${e instanceof Error ? e.message.slice(0, 160) : 'erreur'}` });
  }
});

/**
 * « Booster ma phrase » : le LLM réécrit l'idée de la personne en une description française plus riche et plus filmable
 * (sujet, caméra, lumière, ambiance, son), sans rien changer à ce qu'elle a voulu. La personne choisit de l'utiliser ou non.
 */
app.post('/api/nexora/ameliorer', async (req, reply) => {
  const b = (req.body ?? {}) as any;
  const intention = typeof b.intention === 'string' ? b.intention.trim() : '';
  if (!intention) return reply.code(400).send({ error: 'Écris d’abord une idée.' });
  const llm = llmCourant();
  if (!llm) return reply.code(503).send({ error: 'L’assistant d’écriture n’est pas branché sur ce poste.' });
  try {
    const brut = await llm.completer('boost', [
      { role: 'system', content: [
        'Tu es le directeur artistique de Nexora Creative. Réécris l’idée de l’utilisateur en français, en 2 à 4 phrases (90 mots au plus), plus vivante et plus filmable :',
        'sujet précis, action, décor, lumière, ambiance, mouvement de caméra et sons importants.',
        'Garde tous les sujets et toutes les intentions de l’utilisateur, n’en retire aucun, n’invente ni marque, ni personnage connu, ni texte à l’écran.',
        b.mode === 'image' ? 'C’est pour une image fixe : décris une seule image, pas de mouvement.' : 'C’est pour une vidéo de quelques secondes : une seule action claire.',
        'Réponds en JSON {"texte": "..."} et rien d’autre.',
      ].join(' ') },
      { role: 'user', content: intention },
    ], { json: true, temperature: 0.8 });
    const texte = String(lireJson<{ texte?: unknown }>(brut).texte ?? '').trim();
    if (texte.length < 20 || texte.length > 1200) throw new Error('réponse inutilisable');
    return { texte };
  } catch {
    return reply.code(502).send({ error: 'L’assistant n’a pas pu améliorer ta phrase. Réessaie.' });
  }
});

const IDEES_REPLI: Record<string, string[]> = {
  video: ['Un dragon d’obsidienne jaillit d’une mer de nuages d’orage et rugit vers la caméra.', 'Combat de karaté sur un toit trempé de pluie, la nuit, sous des lanternes rouges.', 'Une flotte de vaisseaux surgit de l’hyperespace au-dessus d’une planète à anneaux.', 'Publicité pour un café glacé : gouttes au ralenti, lumière dorée.'],
  image: ['Une guerrière en kimono noir face à un dragon sur une falaise, au crépuscule.', 'Affiche de film : un astronaute seul sur une plage de cendres sous deux lunes.', 'Un renard en papier découpé dans une forêt d’automne, lumière douce.', 'Une ville flottante au-dessus des nuages à l’aube.'],
  film: ['Un livreur à vélo voit une ville entière s’illuminer sur son passage, de l’aube à la nuit.', 'Une flotte surgit de l’hyperespace ; un duel éclate dans un temple au bord d’un volcan.'],
};
/** « Inspire-moi » : des idées neuves, courtes et filmables, écrites par le LLM (rôle « idées »). Repli : exemples fixes. */
app.post('/api/nexora/idees', async (req) => {
  const b = (req.body ?? {}) as any;
  const mode = b.mode === 'image' || b.mode === 'film' ? b.mode : 'video';
  const theme = typeof b.theme === 'string' ? b.theme.trim().slice(0, 200) : '';
  const llm = llmCourant();
  if (llm) {
    try {
      const brut = await llm.completer('idees', [
        { role: 'system', content: `Tu proposes 4 idées ${mode === 'image' ? 'd’images' : mode === 'film' ? 'de courts films' : 'de scènes vidéo de 5 secondes'} spectaculaires et variées, en français, une phrase de 25 mots au plus chacune, concrètes (sujet, action, décor, ambiance). Aucune marque, aucun personnage connu, aucune personne réelle. Réponds en JSON {"idees":["...","...","...","..."]}.` },
        { role: 'user', content: theme ? `Thème : ${theme}` : 'Surprends-moi.' },
      ], { json: true, temperature: 1 });
      const idees = (lireJson<{ idees?: unknown }>(brut).idees as unknown[] ?? []).map((x) => String(x).trim()).filter((x) => x.length > 10 && x.length < 300).slice(0, 4);
      if (idees.length >= 2) return { idees, source: 'llm' };
    } catch { /* repli */ }
  }
  return { idees: IDEES_REPLI[mode], source: 'repli' };
});

/** Texte de publication d'une création (titre, texte, hashtags) pour un réseau social. */
app.post('/api/nexora/publication', async (req, reply) => {
  const b = (req.body ?? {}) as any;
  const t = takes.get(Number(b.id));
  if (!t) return reply.code(404).send({ error: 'Création introuvable.' });
  const plateforme: Plateforme = b.plateforme in PLATEFORMES ? b.plateforme : 'instagram';
  const s = JSON.parse(t.settings);
  const idee = String(s.intention ?? s.userPrompt ?? t.shot_name ?? '');
  return ecrirePublication(idee, plateforme, b.langue === 'en' ? 'en' : 'fr', llmCourant());
});

/** Une image terminée devient l'image de départ d'une vidéo H3 : jeton d'entrée à passer à /api/nexora/creer. */
app.post('/api/nexora/image/:id/jeton', async (req, reply) => {
  const t = takes.get(Number((req.params as any).id));
  if (!t || t.kind !== 'still' || t.status !== 'done' || !t.output_path) return reply.code(409).send({ error: 'L’image doit être terminée.' });
  const data = readFileSync(t.output_path);
  const jeton = await eng.uploadInput(`nexora_cle_${t.id}_${Date.now()}.png`, data, 'image/png');
  return { jeton };
});

/** Parc de moteurs GPU (état, charge), pour le tableau de bord et les diagnostics. */
app.get('/api/nexora/moteurs-gpu', async () => eng.etatMoteurs());

// ---------------------------------------------------------------------------------------------------------------------
// Agent Producteur (server/nexora/agent.ts) : chat → plan → devis → validation d'un clic → exécution par les routes
// ordinaires du studio (app.inject, avec la session de la personne : même modération, licences, crédits et file).

const PLAFOND_PRODUCTEUR = {
  credits: Number(process.env.NEXORA_PRODUCTEUR_PLAFOND_CREDITS) > 0 ? Number(process.env.NEXORA_PRODUCTEUR_PLAFOND_CREDITS) : 400,
  secondes: (Number(process.env.NEXORA_PRODUCTEUR_PLAFOND_MINUTES) > 0 ? Number(process.env.NEXORA_PRODUCTEUR_PLAFOND_MINUTES) : 30) * 60,
};
const devisDuCompte = (p: PlanProduction) =>
  devisProduction(p, { moteur: moteurDuCompte(p.qualite) ?? 'h3-fast', creditsActifs: !!configAuth, tarif: tarifDepuisEnv() });

/** Appel interne d'une route du studio avec la session de la requête en cours. */
async function appelInterne(req: FastifyRequest, method: 'GET' | 'POST', url: string, payload?: unknown) {
  const headers: Record<string, string> = { 'content-type': 'application/json' };
  for (const h of ['cookie', 'authorization', 'host'] as const) if (typeof req.headers[h] === 'string') headers[h] = req.headers[h] as string;
  const r = await app.inject({ method, url, headers, ...(payload === undefined ? {} : { payload: JSON.stringify(payload) }) });
  const corps = r.body ? JSON.parse(r.body) : {};
  if (r.statusCode >= 400) throw Object.assign(new Error(corps?.error ?? `HTTP ${r.statusCode}`), { statusCode: r.statusCode });
  return corps;
}

/** Résumé d'un film pour l'agent et l'interface : plans, contrôle qualité, choix du juge, musique. */
function resumeFilm(id: number) {
  const f = takes.get(id);
  if (!f) return { erreur: 'film introuvable' };
  const s = JSON.parse(f.settings);
  const plans = ((s.storyboard?.plans ?? []) as any[]).map((p, i) => {
    const t = p.take ? takes.get(p.take) : undefined;
    return {
      plan: i + 1, resume: p.resume, etat: t?.status ?? 'en attente',
      ...(p.controle ? { controle: p.controle.ok ? 'ok' : p.controle.defauts } : {}),
      ...(p.jugement ? { juge: { prise: p.jugement.take, source: p.jugement.source, raison: p.jugement.raison } } : {}),
      ...(p.reprises ? { reprises: p.reprises } : {}),
    };
  });
  const m = typeof s.musiquePrise === 'number' ? takes.get(s.musiquePrise) : undefined;
  return {
    film: f.id, titre: s.storyboard?.titre ?? f.shot_name, etat: f.status, ...(f.error ? { erreur: f.error } : {}), format: s.format, qualite: s.qualite,
    plans, musique: m ? m.status : s.musique ? 'done' : null, cartons: (s.cartons ?? []).map((c: any) => c.texte),
    ...(f.status === 'done' ? { video: `/api/media/${f.id}` } : {}),
  };
}

const verrousProducteur = new Set<string>();
function sessionOu404(id: string, reply: FastifyReply): SessionProducteur | null {
  const s = sessionsProducteur.get<SessionProducteur>(id);
  if (!s) { reply.code(404).send({ error: 'Conversation introuvable.' }); return null; }
  return s;
}
/** Ce que voit le navigateur (sans l'historique brut du modèle). */
const vueSession = (s: SessionProducteur) => ({
  id: s.id, titre: s.titre, fil: s.fil, proposition: s.proposition, productions: s.productions.map((p) => ({ ...p, film: resumeFilm(p.filmId) })),
  plafond: PLAFOND_PRODUCTEUR, juge: jugeDisponible(), credits: !!configAuth,
  palier: s.palier ?? null, palierEffectif: palierDuRole('producteur', { projet: s.palier }), paliers: paliersDisponibles(), usage: s.usage ?? null,
});

app.get('/api/nexora/producteur', async () => ({ sessions: sessionsProducteur.list() }));
app.post('/api/nexora/producteur', async () => {
  const s = nouvelleSession();
  sessionsProducteur.save(s);
  return vueSession(s);
});
app.get('/api/nexora/producteur/:id', async (req, reply) => {
  const s = sessionOu404((req.params as any).id, reply);
  return s ? vueSession(s) : undefined;
});

const livreUsage = new GrandLivreUsage(join(config.dataDir, 'usage-llm.jsonl'));
function cumulerUsage(u: SessionProducteur['usage'], b: BilanRun, palier: Palier): NonNullable<SessionProducteur['usage']> {
  const t = b.totaux;
  return {
    appels: (u?.appels ?? 0) + t.appels, entree: (u?.entree ?? 0) + t.entree, sortie: (u?.sortie ?? 0) + t.sortie, raisonnement: (u?.raisonnement ?? 0) + t.raisonnement,
    usd: (u?.usd ?? 0) + t.coutUsd, creditsExacts: (u?.creditsExacts ?? 0) + t.credits, creditsFactures: (u?.creditsFactures ?? 0) + b.factures,
    dernier: { palier: LIBELLES_PALIER[palier], entree: t.entree, sortie: t.sortie, credits: Math.round(t.credits * 100) / 100, factures: b.factures, reserves: b.reserves },
  };
}

app.post('/api/nexora/producteur/:id/palier', async (req, reply) => {
  const s = sessionOu404(String((req.params as any).id), reply);
  if (!s) return;
  const v = ((req.body ?? {}) as any).palier;
  if (v !== null && !estPalier(v)) return reply.code(400).send({ error: 'Palier inconnu (eco, equilibre, expert).' });
  if (v && !paliersDisponibles()[v as Palier]) return reply.code(409).send({ error: `Le palier ${LIBELLES_PALIER[v as Palier]} n’est pas disponible sur ce serveur.` });
  if (v) s.palier = v; else delete s.palier;
  sessionsProducteur.save(s);
  return vueSession(s);
});

/** Devis LLM d'un palier pour une tâche (avant de lancer) : jetons, USD fournisseur, crédits, plafond réservé. */
app.get('/api/nexora/agent/devis', async (req) => {
  const q = req.query as any;
  const p: Palier = estPalier(q.palier) ? q.palier : palierDuRole('producteur') ?? 'expert';
  return { ...devisLlm(String(q.tache ?? 'film'), p, { livre: livreUsage }), libelle: LIBELLES_PALIER[p] };
});

/** Usage LLM du compte (grand livre) : par palier, avec totaux. */
app.get('/api/nexora/agent/usage', async () => {
  const l = livreUsage.lignes();
  return { total: livreUsage.total(), parPalier: Object.fromEntries((['eco', 'equilibre', 'expert'] as Palier[]).map((p) => [p, livreUsage.total({ palier: p })])), dernieres: l.slice(-20) };
});

/**
 * Agent monteur de bout en bout (tournage → montage), avec escalade automatique du moins cher au plus capable.
 * Corps : { briefId } d'un brief de la campagne, ou { enonce, genre, format, duree, bpm } ; { palier, escalade }.
 */
app.post('/api/nexora/agent/film', async (req, reply) => {
  const b = (req.body ?? {}) as any;
  const base = BRIEFS_FILMS.find((x) => x.id === b.briefId);
  const brief: BriefFilm = base ?? {
    id: `libre-${Date.now()}`, titre: String(b.titre ?? 'Film').slice(0, 80), enonce: String(b.enonce ?? '').slice(0, 1500), genre: ['pub', 'bande-annonce', 'explicatif', 'social'].includes(b.genre) ? b.genre : 'pub',
    format: ['9:16', '1:1'].includes(b.format) ? b.format : '16:9', duree_cible_s: Math.max(15, Math.min(60, Number(b.duree) || 30)), bpm: Math.max(70, Math.min(140, Number(b.bpm) || 100)), marque: String(b.marque ?? 'NEXORA').slice(0, 40), mots: [],
  };
  if (!brief.enonce) return reply.code(400).send({ error: 'Décris le film (enonce) ou donne un briefId.' });
  const depart = (estPalier(b.palier) ? b.palier : palierDuRole('tournage')) as Palier | null;
  if (!depart || !paliersDisponibles()[depart]) return reply.code(409).send({ error: 'Aucun palier LLM disponible sur ce serveur.' });
  const compte = compteCourant();
  const run = randomUUID();
  const devis = devisLlm('film', depart, { livre: livreUsage });
  // Plafond : le devis du palier de départ, multiplié par le nombre de paliers possibles si l'escalade est permise.
  const facteur = b.escalade === false ? 1 : 3;
  try {
    const { resultat, bilan } = await executerSousReservation(
      { fac: facturationCourante(), devis: { ...devis, creditsReserves: devis.creditsReserves * facteur, plafondUsd: devis.plafondUsd * facteur * 2 }, ctx: { run, tache: 'film', projet: brief.id, utilisateur: compte?.utilisateurId, organisation: compte?.organisationId }, livre: livreUsage },
      async (rel) => {
        const clients = Object.fromEntries((['eco', 'equilibre', 'expert'] as Palier[]).map((p) => [p, clientPalier(p, { surveillant: rel })])) as Record<Palier, ClientLlm>;
        return escalader(clients, depart, brief, { politique: (p) => optionsPalier(p), ordre: b.escalade === false ? [depart] : undefined });
      },
    );
    return {
      palierFinal: resultat.palierFinal, escalades: resultat.escalades, score: resultat.final.score, source: resultat.final.montage.source, tournage: resultat.final.tournage, plan: resultat.final.plan,
      usage: { ...bilan.totaux, reserves: bilan.reserves, factures: bilan.factures, liberes: bilan.liberes, creditsExacts: bilan.totaux.credits },
    };
  } catch (e) {
    return reply.code(502).send({ error: `L’agent n’a pas pu terminer (${e instanceof Error ? e.message : 'erreur'}).` });
  }
});

app.post('/api/nexora/producteur/:id/message', async (req, reply) => {
  const id = String((req.params as any).id);
  const texte = String(((req.body ?? {}) as any).texte ?? '').trim();
  if (!texte) return reply.code(400).send({ error: 'Écris ce que tu veux produire.' });
  const s = sessionOu404(id, reply);
  if (!s) return;
  if (verrousProducteur.has(id)) return reply.code(409).send({ error: 'Le Producteur réfléchit déjà à ta demande précédente.' });
  const verdict = await moderer(texte, llmCourant(), (m) => app.log.warn(m));
  if (!verdict.ok) return reply.code(422).send({ error: verdict.raison, categorie: verdict.categorie });
  verrousProducteur.add(id);
  try {
    const construireDeps = (llm: ClientLlm | null): DepsAgent => ({
      llm, devis: devisDuCompte, plafond: PLAFOND_PRODUCTEUR,
      marque: () => { const k = kitsMarque.lire(compteCourant()?.organisationId); return k ? resumeMarque(k) : ''; },
      personnages: {
        liste: () => {
          const l = castDb.list().filter((m) => m.kind === 'character');
          return l.length ? `Personnages disponibles : ${l.map((m) => `@${m.name} (${m.notes.slice(0, 90)})`).join(' ; ')}. Pour garder un personnage identique d'un plan à l'autre, écris @Nom dans la description du plan (le tournage passera en qualité cinéma).` : '';
        },
        cite: (t) => mentioned(t, castDb.list()).length > 0,
      },
      // Outils de montage (analyze_media, plan_edit, critique, revise) : un média du projet = une création terminée (id de prise).
      montage: {
        plafondCredits: PLAFOND_PRODUCTEUR.credits,
        analyser: async (ids) => Object.fromEntries(await Promise.all(ids.map(async (id) => {
          const t = /^\d+$/.test(id) ? takes.get(Number(id)) : undefined;
          if (!t?.output_path || t.status !== 'done' || !existsSync(t.output_path)) throw new Error(`média ${id} introuvable ou non terminé : donne l’id d’une création terminée`);
          return [id, await analyserMedia(t.output_path, { ffmpeg: config.ffmpegBin })] as const;
        }))),
      },
      outils: {
        etat_studio: async () => ({
          ...(await appelInterne(req, 'GET', '/api/nexora/etat')),
          juge_visuel: jugeDisponible() ? 'disponible (candidats: 2)' : 'non configuré (candidats: 1 seulement)',
          plafond: PLAFOND_PRODUCTEUR.credits && configAuth ? `${PLAFOND_PRODUCTEUR.credits} crédits` : `${PLAFOND_PRODUCTEUR.secondes / 60} min de calcul`,
        }),
        lister_creations: async () => takes.list(null, 12).map((t) => {
          const x = JSON.parse(t.settings);
          return { id: t.id, type: x.film ? 'film' : t.kind === 'still' ? 'image' : t.kind, titre: String(x.intention ?? x.userPrompt ?? t.shot_name).slice(0, 80), etat: t.status };
        }),
        voir_production: async (a: any) => resumeFilm(Number(a?.film)),
        devisPlan: async (film, plan) => {
          const f = takes.get(film);
          const x = f ? JSON.parse(f.settings) : null;
          const p = x?.storyboard?.plans?.[plan];
          if (!p) throw new Error(`le film ${film} n’a pas de plan ${plan + 1}`);
          return devisDuCompte({ titre: '', format: x.format, qualite: x.qualite ?? 'rapide', son: !!x.son, bible: x.storyboard.bible, plans: [{ ...p, suite: false }], musique: null, cartons: [], candidats: 1 });
        },
      },
    });
    // Palier choisi (projet > réglage > serveur) : le tour est mesuré jeton par jeton, réservé au plafond du devis, réglé
    // au réel. En cas d'échec du palier (point de terminaison saturé), un seul essai au palier supérieur.
    const palier = palierDuRole('producteur', { projet: s.palier });
    let apres: SessionProducteur;
    if (palier) {
      const compte = compteCourant();
      const lancer = (p: Palier) => executerSousReservation(
        { fac: facturationCourante(), devis: devisLlm('producteur', p, { livre: livreUsage }), ctx: { run: `${randomUUID()}-${p}`, tache: 'producteur', projet: id, utilisateur: compte?.utilisateurId, organisation: compte?.organisationId }, livre: livreUsage },
        (rel) => tourProducteur(s, texte, construireDeps(clientPalier(p, { surveillant: rel }))),
      );
      let r: Awaited<ReturnType<typeof lancer>>;
      let utilise = palier;
      try { r = await lancer(palier); } catch (e) {
        const suivant = e instanceof ErreurPlafondLlm ? null : palierSuivant(palier);
        if (!suivant) throw e;
        utilise = suivant; r = await lancer(suivant);
      }
      apres = r.resultat;
      apres.usage = cumulerUsage(s.usage, r.bilan, utilise);
    } else apres = await tourProducteur(s, texte, construireDeps(llmCourant()));
    sessionsProducteur.save(apres);
    return vueSession(apres);
  } catch (e) {
    return reply.code(502).send({ error: `Le Producteur n’a pas pu répondre (${e instanceof Error ? e.message : 'erreur'}). Réessaie.` });
  } finally {
    verrousProducteur.delete(id);
  }
});

/** Exécution d'une proposition validée : uniquement par les routes ordinaires (file, crédits, licences, modération). */
async function executerProposition(req: FastifyRequest, p: Proposition): Promise<{ filmId: number }> {
  if (p.genre === 'production') {
    const r = await appelInterne(req, 'POST', '/api/nexora/film/tourner', {
      storyboard: planVersStoryboard(p.plan), format: p.plan.format, son: p.plan.son, qualite: p.plan.qualite, intention: p.plan.titre,
      candidats: p.plan.candidats === 2 && jugeDisponible() ? 2 : 1, cartons: p.plan.cartons, ...(p.plan.musique ? { musique: p.plan.musique } : {}),
    });
    return { filmId: Number(r.filmId) };
  }
  if (p.genre === 'refaire') {
    const r = await appelInterne(req, 'POST', `/api/nexora/film/${p.film}/refaire`, { plan: p.plan, description: p.description, camera: p.camera });
    return { filmId: Number(r.filmId) };
  }
  const r = await appelInterne(req, 'POST', `/api/nexora/film/${p.film}/montage`, { ordre: p.ordre, transition: p.transition });
  return { filmId: Number(r.filmId) };
}

app.post('/api/nexora/producteur/:id/valider', async (req, reply) => {
  const id = String((req.params as any).id);
  const s = sessionOu404(id, reply);
  if (!s) return;
  if (verrousProducteur.has(id)) return reply.code(409).send({ error: 'Une action est déjà en cours.' });
  verrousProducteur.add(id);
  try {
    const apres = await validerProposition(s, String(((req.body ?? {}) as any).proposition ?? ''), { executer: (p) => executerProposition(req, p), plafond: PLAFOND_PRODUCTEUR });
    sessionsProducteur.save(apres);
    return vueSession(apres);
  } catch (e) {
    return reply.code((e as any)?.statusCode ?? 409).send({ error: e instanceof Error ? e.message : 'validation impossible' });
  } finally {
    verrousProducteur.delete(id);
  }
});

app.post('/api/nexora/producteur/:id/ajuster', async (req, reply) => {
  const s = sessionOu404(String((req.params as any).id), reply);
  if (!s) return;
  const b = (req.body ?? {}) as any;
  try {
    const apres = ajusterProposition(s, String(b.proposition ?? ''), b, devisDuCompte);
    sessionsProducteur.save(apres);
    return vueSession(apres);
  } catch (e) {
    return reply.code(409).send({ error: e instanceof Error ? e.message : 'ajustement impossible' });
  }
});

const VARIANTES: GenreVariante[] = ['format-16:9', 'format-9:16', 'format-1:1', 'nouvelle-prise', 'cinema', 'courte'];
app.post('/api/nexora/producteur/:id/variante', async (req, reply) => {
  const s = sessionOu404(String((req.params as any).id), reply);
  if (!s) return;
  const b = (req.body ?? {}) as any;
  if (!VARIANTES.includes(b.genre)) return reply.code(400).send({ error: 'Variante inconnue.' });
  try {
    const apres = variante(s, Number(b.film), b.genre, devisDuCompte);
    sessionsProducteur.save(apres);
    return vueSession(apres);
  } catch (e) {
    return reply.code(404).send({ error: e instanceof Error ? e.message : 'variante impossible' });
  }
});

/** Recettes des moteurs GPU du parc qui répondent. */
function recettesDuParc(): Set<string> {
  return eng.recettesEnLigne();
}

/** Recette d'une demande : ce qui décide du moteur GPU (H3 → RTX 5090 ; image et musique → GB10). */
function recetteDe(b: any): string | undefined {
  if (b?.kind === 'musique') return 'music3';
  if (b?.kind === 'object') return b.vues ? recetteMultivue() : recetteObjet(b.quality === 'quality' ? 'quality' : 'draft');
  if (b?.kind === 'still') return b.model === 'flux2' ? 'flux2' : b.model === 'qwen21' ? 'qwen21' : 'qwen';
  return typeof b?.videoModel === 'string' ? b.videoModel : undefined;
}

/** Moteur vidéo du compte courant pour une qualité donnée (null : territoire exclu ou inconnu). */
function moteurDuCompte(qualite: 'rapide' | 'max' = 'rapide', besoin?: Parameters<typeof choisirMoteur>[1]): MoteurVideo | null {
  return choisirMoteur(territoireDuCompte(), besoin, qualite, recettesDuParc());
}

const REFUS_TERRITOIRE = 'MiniMax H3 n’est pas offert dans le territoire de ton compte : sa licence exclut les États-Unis, l’Union européenne, le Royaume-Uni et la Corée du Sud.';

async function generate(b: any, reply: FastifyReply) {
  stripServerKeys(b);
  // Scene bookkeeping is set by the scene runner only; a recreated shot is a plain take.
  delete b.sceneOf; delete b.sceneIndex; delete b.sceneStep;
  if (b.cut) return reply.code(400).send({ error: 'A cut is made from its shots. Use /api/director/scene (Recreate in the app does).' });
  const status = eng.isLocal() ? await comfy.getStatus() : { up: true };
  if (status.up && !(await eng.ensureProxy())) {
    return reply.code(503).send({
      error: `Comfy API v2 is not answering at ${config.comfyBaseUrl}. Install comfy-api-proxy (pip install comfy-api-proxy) or set COMFY_BASE_URL.`,
    });
  }
  if (!status.up) {
    return reply.code(503).send({
      error: comfy.canLaunchEngine()
        ? 'ComfyUI is not running — press START ENGINE'
        : `ComfyUI is not answering at ${config.comfyUrl}. Start it, or set COMFY_URL / COMFY_LAUNCH in .env.`,
    });
  }

  // Say exactly which weights are missing rather than letting ComfyUI reject
  // the graph with a node id the user has never heard of.
  const missing = await blockingReasonFor(eng.isLocal() && eng.recetteSurPrincipal(recetteDe(b)), bundlesFor({ ...b, castEngine: castEngineFor(b) }));
  if (missing) return reply.code(412).send({ error: missing });
  const postMissing = eng.isLocal() ? await postBlockingReason(b) : null;
  if (postMissing) return reply.code(412).send({ error: postMissing });
  if (eng.isLocal() && b.kind === 'effect') {
    const fx = effectById(b.effect);
    const fxMissing = fx ? await effectBlockingReason(fx.bundle, fx.lora, fx.name) : null;
    if (fxMissing) return reply.code(412).send({ error: fxMissing });
  }

  if (Array.isArray(b.loras) && b.loras.length) {
    const fam = loraFamily(b);
    if (!fam) return reply.code(400).send({ error: 'Your own LoRAs work in Image and Video (LTX-2.5) for now.' });
    try { await pickLoras(b.loras, fam, b.kind === 'still' ? 'Image' : 'Video'); }
    catch (e) { return reply.code(400).send({ error: e instanceof Error ? e.message : 'bad LoRA' }); }
  }

  const orgEnCours = compteCourant()?.organisationId;
  if (configAuth && orgEnCours && espacePlein(orgEnCours)) {
    return reply.code(409).send({ error: 'Ton espace Nexora est plein : supprime des vidéos ou ajoute de l’espace dans ton compte pour continuer.' });
  }
  const count = Math.max(1, Math.min(8, Number(b.count) || 1));
  // Nexora : avec une session du portail, chaque prise réserve son devis en crédits avant de partir au moteur.
  const reservations: CreditsPrise[] = [];
  const fac = facturationCourante();
  if (fac) {
    const credits = devisCredits(b, tarifDepuisEnv());
    for (let i = 0; i < count; i++) {
      const r = await fac.reserver({ idempotence: randomUUID(), credits, libelle: `Nexora Creative · ${b.kind === 'still' ? 'image' : 'vidéo'}` });
      if (!r.ok) {
        for (const x of reservations) await fac.liberer(x.reservationId).catch(() => {});
        return reply.code(402).send({ error: r.message });
      }
      reservations.push({ reservationId: r.reservationId, credits: r.credits, etat: 'reservee' });
    }
  }
  try {
    const takeIds = await queueTakes(b, count);
    takeIds.forEach((id, i) => { if (reservations[i]) takes.patchSettings(id, { nexoraCredits: reservations[i] }); });
    if (b.projectId) projects.touch(b.projectId);
    return { takeIds, takeId: takeIds[0], credits: reservations.reduce((n, r) => n + r.credits, 0) || undefined };
  } catch (e) {
    for (const x of reservations) await fac?.liberer(x.reservationId).catch(() => {});
    return reply.code(400).send({ error: e instanceof Error ? e.message : 'bad request', takeIds: (e as any)?.takeIds });
  }
}

// ---------- cast ----------

/** The text a body's @mentions live in. */
const castField = (b: any) => (b.kind === 'edit' ? 'instruction' : 'prompt');
const isLtxShot = (b: any) => (b.kind === undefined || b.kind === 'video') && b.videoModel === 'ltx25';

/** FLUX.2 reads up to this many reference pictures per still (each is ~1 MP of latent). */
const FLUX2_REFS = 6;
const ownRefs = (b: any): string[] =>
  (Array.isArray(b.refImages) ? b.refImages : []).filter((x: unknown): x is string => typeof x === 'string' && !!x).slice(0, FLUX2_REFS);
/** A FLUX.2 still's references: the user's own, then the cast pictures resolveCast picked. */
const flux2Refs = (b: any): string[] => {
  const cast = b.castEngine === 'flux2ref' && Array.isArray(b.castImages) ? b.castImages : [];
  return [...ownRefs(b), ...cast].slice(0, FLUX2_REFS);
};

/** The model family an app's own LoRAs must match, or null where they do not apply. */
function loraFamily(b: any): LoraFamily | null {
  if (b.kind === 'still') return b.model === 'flux2' ? 'flux2' : 'qwen';
  if (isLtxShot(b)) return 'ltx';
  return null;
}

/** A hero frame this take waits for before it can be built. */
interface HeroPlan { castIds: number[]; shot: string; opts: HeroOpts; poseFrom?: string }

/** Hero frames are composed near 1 MP at the shot's aspect. */
function heroSize(w: number, h: number) {
  const ratio = (w || 16) / (h || 9);
  const hh = Math.sqrt(1e6 / ratio);
  const snap = (n: number) => Math.max(256, Math.round(n / 16) * 16);
  return { width: snap(hh * ratio), height: snap(hh) };
}

/**
 * Turn @mentions in a request into prompt words and engine inputs (see
 * server/cast.ts for the routing table). Returns the rewritten body, plus a
 * hero frame plan when the take needs a composed first frame before it runs.
 * The original text is kept as castSource, so Recreate resolves it afresh.
 */
async function resolveCast(input: any): Promise<{ body: any; hero?: HeroPlan }> {
  const b = { ...input };
  // A hero frame carries its pictures already.
  if (b.app === 'cast' && b.castEngine === 'compose') return { body: b };
  const key = castField(b);
  if (typeof b.castSource === 'string') b[key] = b.castSource;
  if (Array.isArray(b.castOwnImages)) b.images = b.castOwnImages;
  for (const k of ['castEngine', 'castImages', 'castInstruction', 'castSheet', 'castHeroTake', 'cast']) delete b[k];
  const text = typeof b[key] === 'string' ? b[key] : '';
  const all = castDb.list();
  const members = mentioned(text, all);
  if (!members.length) return { body: b };
  for (const m of members) m.refs = await liveRefs(m);
  b.castSource = text;
  b.cast = members.map((m) => m.id);
  const withRefs = members.filter((m) => m.refs.length);
  const words = () => {
    b.castEngine = 'words';
    b[key] = plainText(text, all);
    if (key === 'instruction') b.prompt = b.instruction;
    return { body: b };
  };
  if (!withRefs.length) return words();

  if (b.kind === 'still' && b.model === 'flux2') {
    // FLUX.2 reads the cast pictures as reference latents and renders the frame itself.
    const c = composeInstruction(text, allocate(withRefs, FLUX2_REFS - ownRefs(b).length), { offset: ownRefs(b).length, newFrame: true, all, nameless: true });
    Object.assign(b, { castEngine: 'flux2ref', castImages: c.images, prompt: c.instruction });
    return { body: b };
  }
  if (b.kind === 'still') {
    const c = composeInstruction(text, allocate(withRefs, 3), { newFrame: true, all });
    Object.assign(b, { castEngine: 'compose', castImages: c.images, castInstruction: c.instruction, prompt: c.instruction });
    return { body: b };
  }
  if (b.kind === 'edit') {
    const own: string[] = Array.isArray(b.images) ? b.images.filter((x: unknown) => typeof x === 'string' && x).slice(0, 3) : [];
    if (own.length >= 3 || b.expand) return words();
    const c = composeInstruction(text, allocate(withRefs, 3 - own.length), { offset: own.length, all });
    Object.assign(b, { castEngine: 'edit', castOwnImages: own, images: [...own, ...c.images], instruction: c.instruction, prompt: c.instruction });
    return { body: b };
  }
  if (isLtxShot(b) && !b.startImage && !b.endImage) {
    if (b.castMode === 'frame') {
      b.castEngine = 'frame';
      b.prompt = plainText(text, all);
      return { body: b, hero: { castIds: b.cast, shot: text, opts: { ...heroSize(b.width, b.height), seed: b.seed } } };
    }
    const plan = sheetPlan(text, withRefs, Number(b.width) || 768, Number(b.height) || 448, all);
    Object.assign(b, {
      castEngine: 'sheet', castSheet: plan.layout, prompt: plan.prompt,
      width: plan.layout.width, height: plan.layout.height,
      // The LoRA reads a reference of at least 121 frames: 5 seconds at 24 fps.
      seconds: Math.max(5, Math.min(10, Number(b.seconds) || 5)),
    });
    return { body: b };
  }
  if (b.kind === 'mirror' && !b.startImage && b.sourceVideo) {
    b.castEngine = 'frame';
    b.prompt = plainText(text, all);
    return { body: b, hero: { castIds: b.cast, shot: text, opts: heroSize(b.width, b.height), poseFrom: b.sourceVideo } };
  }
  if (b.kind === 'speak' && !b.startImage) {
    b.castEngine = 'frame';
    b.prompt = plainText(text, all);
    return {
      body: b,
      hero: { castIds: b.cast, shot: text, opts: { ...heroSize(b.width, b.height), framing: 'Head and shoulders, facing the camera, mouth closed and clearly visible, even light on the face.' } },
    };
  }
  return words();
}

/** Which cast engine a request will use, for the missing-weights check before queuing. */
function castEngineFor(b: any): string | undefined {
  const key = castField(b);
  const texts = [b.castSource ?? b[key], ...(Array.isArray(b.variants) ? b.variants.map((v: any) => v?.[key]) : [])]
    .filter((t): t is string => typeof t === 'string');
  const all = castDb.list();
  const ms = texts.flatMap((t) => mentioned(t, all)).filter((m) => m.refs.length);
  if (!ms.length) return undefined;
  if (b.kind === 'still') return b.model === 'flux2' ? 'flux2ref' : 'compose';
  if (isLtxShot(b) && !b.startImage && !b.endImage) return b.castMode === 'frame' ? 'frame' : 'sheet';
  if ((b.kind === 'mirror' || b.kind === 'speak') && !b.startImage) return 'frame';
  return undefined;
}

/** The first frame of an uploaded clip, uploaded as a still (Mirror's pose reference). */
async function firstFrame(token: string): Promise<string> {
  const inp = await eng.readInput(token);
  if (!inp) throw new Error('The clip is no longer on this machine. Add it again.');
  const { mkdtemp, writeFile, readFile, rm } = await import('fs/promises');
  const { tmpdir } = await import('os');
  const { execFile } = await import('child_process');
  const dir = await mkdtemp(join(tmpdir(), 'openfield-frame-'));
  try {
    const src = join(dir, `in${extname(inp.name) || '.mp4'}`);
    const out = join(dir, 'frame.png');
    await writeFile(src, inp.data);
    await new Promise<void>((res, rej) => execFile(config.ffmpegBin, ['-v', 'error', '-y', '-i', src, '-frames:v', '1', out], (e) => (e ? rej(e) : res())));
    return await eng.uploadInput(`openfield_pose_${Date.now()}.png`, await readFile(out), 'image/png');
  } finally {
    await rm(dir, { recursive: true, force: true });
  }
}

/** Submit a built graph for an existing take row. */
async function submitTake(takeId: number, built: Built) {
  // Nexora : la recette (videoModel) choisit le moteur GPU du parc ; parmi ceux qui la portent, le moins chargé.
  const recette = recetteDe(JSON.parse(takes.get(takeId)?.settings ?? '{}'));
  const moteur = eng.moteursPour(recette)[0]?.id ?? 'principal';
  const promptId = await eng.submit(built.graph, moteur);
  takes.setPrompt(takeId, promptId);
  // Cancelled while it was being submitted: the take stays stopped, so drop the job too.
  if (takes.get(takeId)?.status === 'stopped') await eng.cancel(promptId).catch(() => {});
  void recordWorkflow(takeId, promptId, built.graph);
  broadcast({ type: 'take', take: takes.get(takeId) });
}

/**
 * Build, record and submit takes. A request is either `count` takes of one
 * setup (each with the next seed), or a list of `variants` (the image apps: one
 * take per angle, shot, beat...), each overriding fields of the shared body. A
 * variant's take stores the merged body, so Recreate reruns just that one.
 * Throws with the ids queued so far.
 */
async function queueTakes(b: any, count: number): Promise<number[]> {
  const firstSeed = Number.isFinite(b.seed) ? b.seed : Math.floor(Math.random() * 1e9);
  const variants: Record<string, unknown>[] = Array.isArray(b.variants)
    ? b.variants.filter((v: unknown) => v && typeof v === 'object').slice(0, 9)
    : [];
  stripServerKeys(b);
  variants.forEach(stripServerKeys);
  const n = variants.length || count;
  const batch = variants.length ? `b${Date.now().toString(36)}` : undefined;
  const takeIds: number[] = [];
  let hero: Promise<{ takeId: number; token: string }> | undefined;
  // Stage: the blocking is drawn once and one look frame serves every take of the batch.
  let staged: Promise<any> | undefined;
  let look: Promise<{ takeId: number; token: string }> | undefined;
  for (let i = 0; i < n; i++) {
    const seed = firstSeed + i;
    const raw = variants.length ? { ...b, ...variants[i], variants: undefined, batch, batchIndex: i, batchSize: n }
      : { ...b, batch: undefined, batchIndex: undefined, batchSize: undefined };
    let one: any;
    let built: Built;
    try {
      const r = await resolveCast(raw);
      one = r.body;
      if (r.hero) {
        // The take waits for its hero frame; one frame serves the whole batch.
        hero ??= (async () => {
          const opts = { ...r.hero!.opts, projectId: b.projectId ?? null };
          if (r.hero!.poseFrom) opts.poseImage = await firstFrame(r.hero!.poseFrom);
          return castHeroFrame(r.hero!.castIds, r.hero!.shot, opts);
        })();
        takeIds.push(queueAfter(one, seed, hero, b.projectId ?? null, (body, h) => ({ ...body, startImage: h.token, castHeroTake: h.takeId })));
        continue;
      }
      if (one.kind === 'stage') {
        one = { ...(await (staged ??= prepareStage(one))), seed: one.seed, batch: one.batch, batchIndex: one.batchIndex, batchSize: one.batchSize };
        if (!one.lookImage) {
          const shot = one;
          look ??= stageLookFrame(queueTakes, { ...shot, seed, projectId: b.projectId });
          takeIds.push(queueAfter(one, seed, look, b.projectId ?? null, (body, h) => ({ ...body, lookImage: h.token, lookTake: h.takeId })));
          continue;
        }
      }
      built = await graphFor(one, seed);
    } catch (e) {
      throw Object.assign(e instanceof Error ? e : new Error('bad request'), { takeIds });
    }
    const takeId = takes.create({
      project_id: b.projectId ?? (built.parent ? takes.get(built.parent)?.project_id ?? null : null),
      kind: built.kind,
      shot_name: String(built.settings?.shotName ?? one.shotName ?? 'shot'),
      settings: { ...one, ...built.settings, seed, count: undefined },
      parent_take_id: built.parent,
    });
    try {
      takeIds.push(takeId);
      await submitTake(takeId, built);
    } catch (e) {
      takeIds.pop();
      takes.fail(takeId, e instanceof Error ? e.message : 'submit failed');
      broadcast({ type: 'take', take: takes.get(takeId) });
      throw Object.assign(e instanceof Error ? e : new Error('submit failed'), { takeIds });
    }
  }
  return takeIds;
}

/**
 * A take that needs a still first (a cast hero frame, a Stage look frame): its
 * row exists at once (queued, no engine job yet), and it is built and submitted
 * when the still is done. `apply` puts the still into the take's body.
 */
function queueAfter(
  one: any, seed: number, first: Promise<{ takeId: number; token: string }>, projectId: number | null,
  apply: (body: any, still: { takeId: number; token: string }) => any,
): number {
  const takeId = takes.create({ project_id: projectId, kind: 'video', shot_name: String(one.shotName ?? 'shot'), settings: { ...one, seed, count: undefined } });
  broadcast({ type: 'take', take: takes.get(takeId) });
  void (async () => {
    try {
      const h = await first;
      if (takes.get(takeId)?.status !== 'queued') return; // cancelled while waiting
      const body = apply(one, h);
      const built = await graphFor(body, seed);
      takes.setSettings(takeId, { ...body, ...built.settings, seed, count: undefined });
      await submitTake(takeId, built);
    } catch (e) {
      takes.fail(takeId, e instanceof Error ? e.message : 'the first frame failed');
      broadcast({ type: 'take', take: takes.get(takeId) });
    }
  })();
  return takeId;
}

interface MediaProbe { kind: 'video' | 'image'; w: number; h: number; fps: number; seconds: number; frames: number; audio: boolean }

/** Size, rate, length and whether there is a sound track, from ffprobe. */
async function probeMedia(path: string): Promise<MediaProbe> {
  const { execFile } = await import('child_process');
  const ffprobe = config.ffprobeBin;
  const out = await new Promise<string>((res, rej) =>
    execFile(ffprobe, ['-v', 'error', '-show_entries', 'stream=codec_type,width,height,r_frame_rate,nb_frames:format=duration,format_name', '-of', 'json', path],
      (err, stdout) => (err ? rej(new Error(`could not read the source file (${err.message.split('\n')[0]})`)) : res(stdout))),
  );
  const d = JSON.parse(out);
  const streams: any[] = d.streams ?? [];
  const v = streams.find((x) => x.codec_type === 'video');
  if (!v) throw new Error('the source has no picture');
  const fmt = String(d.format?.format_name ?? '');
  const image = /image2|png_pipe|jpeg_pipe|webp_pipe|bmp_pipe/.test(fmt);
  const [n, dd] = String(v.r_frame_rate ?? '24/1').split('/').map(Number);
  const fps = n && dd ? n / dd : 24;
  const seconds = Number(d.format?.duration) || 0;
  return {
    kind: image ? 'image' : 'video',
    w: v.width, h: v.height, fps: Math.round(fps * 1000) / 1000, seconds,
    frames: Number(v.nb_frames) || Math.round(seconds * fps),
    audio: streams.some((x) => x.codec_type === 'audio'),
  };
}

/**
 * Upscale app: stage the source (a finished take, or an uploaded file),
 * measure it, and build the graph for the chosen mode. Sizes are computed
 * here from the real file, with the same upscaleSize() the page shows.
 */
async function upscaleGraph(b: any, seed: number): Promise<Built> {
  const mode: UpscaleMode = b.mode === 'redraw' || b.mode === 'dream' ? b.mode : 'sharpen';
  let localPath: string;
  let file: string;
  let parent: number | undefined;
  let named: { shotName?: string; fileSeed?: number } = {};
  if (b.sourceTake) {
    const src = takes.get(Number(b.sourceTake));
    if (!src?.output_path) throw new Error(`take ${b.sourceTake} not found or unfinished`);
    if (!existsSync(src.output_path)) throw new Error(`take ${src.id}'s file is no longer on disk: ${src.output_path}`);
    localPath = src.output_path;
    const ext = extname(localPath).toLowerCase() || '.mp4';
    const data = await import('fs/promises').then((fs) => fs.readFile(localPath));
    file = await eng.uploadInput(`openfield_up_${src.id}${ext}`, data, ext === '.png' ? 'image/png' : 'video/mp4');
    parent = src.id;
    const ss = JSON.parse(src.settings);
    named = { shotName: b.shotName || ss.shotName || src.shot_name, fileSeed: ss.fileSeed ?? ss.seed };
  } else if (typeof b.source === 'string' && b.source) {
    const p = eng.inputPath(b.source);
    if (!p) throw new Error('the uploaded source is gone; add it again');
    localPath = p;
    file = b.source;
  } else {
    throw new Error('Upscale needs a source: a take or a file');
  }

  const m = await probeMedia(localPath);
  if (mode === 'dream' && m.kind === 'image') throw new Error('Dream upscales video. Use Sharpen or Redraw for a still.');
  const height = REDRAW_HEIGHTS.includes(Number(b.upHeight) as any) ? Number(b.upHeight) : REDRAW_HEIGHTS[0];
  const out = upscaleSize(mode, m.w, m.h, height);
  const source: UpscaleSource = { kind: m.kind, file, withAudio: m.kind === 'video' && m.audio, fps: m.fps };
  const kind = m.kind === 'image' ? 'still' : 'upres';
  const common = {
    app: 'upscale', mode, sourceKind: m.kind, sourceWidth: m.w, sourceHeight: m.h,
    width: out.w, height: out.h, upresOf: parent, sourceTake: parent, source: b.source || undefined, ...named,
  };

  if (mode === 'sharpen') {
    const model = b.model === 'ultrasharp' ? 'ultrasharp' : 'esrgan';
    const rife = m.kind === 'video' && !!b.rife;
    const cap = m.kind === 'video' ? Math.floor(sharpenMaxSeconds(m.w, m.h) * m.fps) : 0;
    const frames = m.kind === 'video' ? Math.min(m.frames, cap) : 1;
    return {
      graph: buildSharpenGraph({ source: { ...source, frameCap: m.kind === 'video' && m.frames > cap ? cap : 0 }, model, scale: out.w / m.w, rife }),
      kind, parent,
      settings: { ...common, model, rife, seconds: m.kind === 'video' ? Math.round((frames / m.fps) * 10) / 10 : undefined },
    };
  }

  if (mode === 'redraw') {
    const model = b.model === '7b' ? '7b' : '3b';
    const color = b.color === 'wavelet' || b.color === 'none' ? b.color : 'lab';
    const cap = m.kind === 'video' ? Math.floor(REDRAW_MAX_SECONDS * m.fps) : 0;
    const frames = m.kind === 'video' ? Math.min(m.frames, cap) : 1;
    // Frames per batch that fit beside the tiled VAE on a 32 GB card.
    const fit = (model === '7b' ? 21 : 33) * (height > 1080 ? 0.6 : 1);
    return {
      graph: buildRedrawGraph({
        source: { ...source, frameCap: m.kind === 'video' && m.frames > cap ? cap : 0 },
        model, resolution: Math.min(out.w, out.h), maxResolution: Math.max(out.w, out.h),
        batchSize: redrawBatch(frames, Math.floor(fit)), color, seed,
      }),
      kind, parent,
      settings: { ...common, model, color, upHeight: height, seconds: m.kind === 'video' ? Math.round((frames / m.fps) * 10) / 10 : undefined },
    };
  }

  const frames = dreamFrames(m.seconds);
  const creativity = Math.max(DREAM_CREATIVITY.min, Math.min(DREAM_CREATIVITY.max, Number.isFinite(b.creativity) ? Number(b.creativity) : DREAM_CREATIVITY.default));
  const prompt = typeof b.prompt === 'string' && b.prompt.trim() ? b.prompt.trim() : 'The same shot in sharp, rich, high-resolution detail.';
  return {
    graph: buildDreamGraph({
      source: { ...source, kind: 'video' }, prompt, creativity, width: out.w, height: out.h, frames, seed,
      negative: typeof b.negative === 'string' && b.negative ? b.negative : undefined,
    }),
    kind, parent,
    settings: { ...common, creativity, prompt, frames, seconds: Math.round((frames / 24) * 10) / 10 },
  };
}

// ---------- Relief (image to 3D; ex-Object) ----------

const ASSET_TOKEN_RE = /^asset:[0-9a-f-]{36}$/i;

/**
 * Image to 3D on TRELLIS.2: a still (an upload token or a still take) becomes
 * a textured GLB, plus a turntable mp4 and the isolated subject as sidecars.
 * Only tokens and take ids are accepted, never a path.
 */
async function objectGraph(b: any, seed: number): Promise<Built> {
  if (!eng.isLocal()) throw new Error('Make 3D collects its GLB from a local ComfyUI; it does not run on a cloud engine yet.');
  // Plusieurs vues (Pixal3D) : brouillon seulement, sur les moteurs qui portent ces poids.
  const multi = b.vues && typeof b.vues === 'object' ? b.vues : null;
  if (multi && !eng.moteursPour(recetteMultivue()).length) throw new Error(`${PRODUIT_3D} multi-image (Pixal3D) needs a GPU engine that declares the recipe ${recetteMultivue()}: none is configured.`);
  const quality: ObjectQuality = multi ? 'draft' : b.quality === 'quality' ? 'quality' : 'draft';
  const removeBackground = b.removeBackground !== false;
  let parent: number | undefined;
  let named: { shotName?: string } = {};
  const preparer = async (spec: { sourceTake?: unknown; image?: unknown }, premiere: boolean): Promise<string> => {
    if (spec.sourceTake) {
      const src = takes.get(Number(spec.sourceTake));
      if (!src?.output_path || src.status !== 'done') throw new Error(`take ${spec.sourceTake} not found or unfinished`);
      if (src.kind !== 'still') throw new Error(`Make 3D starts from a still; take ${src.id} is a ${src.kind === 'object' ? '3D model' : 'video'}.`);
      if (!existsSync(src.output_path)) throw new Error(`take ${src.id}'s file is no longer on disk: ${src.output_path}`);
      if (premiere) { parent = src.id; const ss = settingsOf(src); named = { shotName: b.shotName || ss.shotName || src.shot_name }; }
      return stageTakeFile(src, 'object');
    }
    if (typeof spec.image === 'string' && ASSET_TOKEN_RE.test(spec.image)) {
      const inp = await eng.readInput(spec.image);
      if (!inp) throw new Error('That image is no longer on this machine. Add it again.');
      if (!imageDims(inp.data)) throw new Error('Make 3D needs a PNG, JPEG or WebP still');
      return spec.image;
    }
    throw new Error('Make 3D needs a still: an uploaded image or a take');
  };
  const image = await preparer(b, true);
  const vues: { left?: string; back?: string; right?: string; fov?: number } | undefined = multi ? { fov: Number.isFinite(Number(multi.fov)) ? Number(multi.fov) : 20 } : undefined;
  if (multi && vues) {
    for (const cote of ['left', 'back', 'right'] as const) if (multi[cote]) vues[cote] = await preparer(multi[cote], false);
    const nb = 1 + (vues.left ? 1 : 0) + (vues.back ? 1 : 0) + (vues.right ? 1 : 0);
    if (nb < 2) throw new Error('Multi-image needs at least a second view (left, back or right).');
    // Mesuré le 04/11/2026 : 2 et 3 vues passent sur les GPU Turing (VM de 8 Go de RAM), 4 vues font tuer ComfyUI par le noyau (mémoire).
    const max = Math.max(2, Math.min(4, Number(process.env.NEXORA_RELIEF_VUES_MAX) || 3));
    if (nb > max) throw new Error(`${PRODUIT_3D} accepte ${max} vues au plus pour l’instant (mémoire des GPU Turing) : retire une vue.`);
  }
  const q = OBJECT_QUALITY[quality];
  return {
    kind: 'object', parent,
    graph: buildTrellisGraph({ image, seed, quality, removeBackground, ...(vues ? { vues } : {}), ...(Number.isFinite(Number(b.tournette)) ? { turntableFrames: Math.max(0, Math.min(TURNTABLE.frames, Math.floor(Number(b.tournette)))) } : {}) }),
    settings: {
      app: 'object', quality, removeBackground, image, sourceTake: parent, ...named, ...(vues ? { multiVue: Object.keys(vues).filter((k) => k !== 'fov').length + 1, moteur3d: 'pixal3d' } : {}),
      faces: q.faces, texture: q.texture, resolution: q.resolution,
      width: TURNTABLE.size, height: TURNTABLE.size,
    },
  };
}

// ---------- Director scenes ----------

initScenes({ queueTakes, broadcast, recordWorkflow, probeMedia });
initFilms({
  queueTakes, broadcast,
  televerser: (nom, data, type) => eng.uploadInput(nom, data, type),
  llmPour: (org) => clientLlmCourant(configAuth ? { organisationId: org } : null, accesOrganisation),
});

/** Start planning a scene into shots. Poll GET /api/director/plan/:id. */
app.post('/api/director/plan', async (req, reply) => {
  const b = (req.body ?? {}) as { scene?: string; shots?: number; planner?: string; seed?: number };
  const scene = String(b.scene ?? '').trim();
  if (!scene) return reply.code(400).send({ error: 'Write the scene first' });
  return startPlan(scene, { shots: Number(b.shots) || undefined, planner: b.planner, seed: Number.isFinite(b.seed) ? Number(b.seed) : undefined });
});

app.get('/api/director/plan/:id', async (req, reply) => {
  const p = getPlan(String((req.params as any).id));
  return p ?? reply.code(404).send({ error: 'no such plan (the server restarted?)' });
});

/** Shoot a scene: queue the shots that are not shot yet, then cut. Returns the cut take. */
app.post('/api/director/scene', async (req, reply) => {
  const b = (req.body ?? {}) as any;
  let r;
  const tier = parseTier(b.resolution) ?? (await currentTier());
  try { r = cleanScene(b, tier); } catch (e) { return reply.code(400).send({ error: e instanceof Error ? e.message : 'bad scene' }); }
  const status = eng.isLocal() ? await comfy.getStatus() : { up: true };
  if (!status.up || !(await eng.ensureProxy())) return reply.code(503).send({ error: 'The engine is not answering. Start ComfyUI first.' });
  if (eng.isLocal()) {
    const need = [...new Set([...bundlesFor({ kind: 'video', videoModel: 'ltx25' }), ...(r.heroFrames ? bundlesFor({ kind: 'still', model: r.imageModel }) : []),
      ...(r.shots.some((s) => s.cast?.length) ? bundlesFor({ kind: 'still', castEngine: 'compose' }) : []), 'ltx-tools'])];
    const missing = await blockingReason(need);
    if (missing) return reply.code(412).send({ error: missing });
    for (const s of r.shots) {
      const why = await postBlockingReason({ era: r.era, eraGrade: r.eraGrade, ramp: s.ramp ?? r.ramp });
      if (why) return reply.code(412).send({ error: why });
    }
  }
  try {
    const cutId = await shootScene(r);
    if (r.projectId) projects.touch(r.projectId);
    return { cutId, take: takes.get(cutId) };
  } catch (e) {
    return reply.code(400).send({ error: e instanceof Error ? e.message : 'could not shoot the scene' });
  }
});

// ---------- Seam Doctor ----------

type SeamFix = 'trim' | 'regen' | 'bridge' | 'reseed';
/**
 * Order the doctor tries fixes in when asked to fix a seam automatically. A
 * trim is free and keeps every original frame, so it goes first whenever one
 * closes; then the bridge; a re-render with a new seed is the last resort.
 * Measured on loops rendered at 832x448 (see CHANGELOG, Seam Doctor).
 */
const SEAM_ORDER: SeamFix[] = ['trim', 'regen', 'reseed'];
/** Re-noise level for a re-render across the wrap (measured, see CHANGELOG). */
const SEAM_REGEN_SIGMA = 0.65;

const settingsOf = (t: { settings: string }) => JSON.parse(t.settings) as Record<string, any>;

/** A take that is meant to loop: the Seamless loop tab, a looping effect, or a seam fix. */
function isLoopTake(s: Record<string, any>): boolean {
  return s.app === 'seam' || (!!s.startImage && s.startImage === s.endImage) || (s.app === 'effects' && !!s.loop);
}

/** A finished video take's file, checked. */
function finishedVideo(id: number) {
  const t = takes.get(id);
  if (!t?.output_path || t.status !== 'done') throw new Error(`take ${id} not found or unfinished`);
  if (t.kind === 'still' || /\.png$/i.test(t.output_path)) throw new Error(`take ${id} is a still, not a video`);
  if (!existsSync(t.output_path)) throw new Error(`take ${t.id}'s file is no longer on disk: ${t.output_path}`);
  return t;
}

/** Hand a finished take's file to the engine as an input. */
async function stageTakeFile(t: { id: number; output_path: string | null }, prefix: string): Promise<string> {
  const ext = extname(t.output_path!).toLowerCase() || '.mp4';
  const data = await import('fs/promises').then((fs) => fs.readFile(t.output_path!));
  return eng.uploadInput(`openfield_${prefix}_${t.id}${ext}`, data, ext === '.png' ? 'image/png' : 'video/mp4');
}

/** The loop a chain of seam fixes started from. */
function originOf(id: number): number {
  let t = takes.get(id);
  for (let i = 0; t && i < 20; i++) {
    const s = settingsOf(t);
    if (s.app !== 'seam' || !s.sourceTake) return t.id;
    t = takes.get(Number(s.sourceTake));
  }
  return t?.id ?? id;
}

/** Measure a take as a loop, store the result on it, and tell the browsers. */
async function measureTake(id: number): Promise<SeamMeasure> {
  const t = finishedVideo(id);
  const s = settingsOf(t);
  const splices = s.app !== 'seam' || !s.plan ? [] : s.mode === 'bridge' ? [s.plan.splice] : s.mode === 'regen' ? s.plan.splices : [];
  const m = await measureLoop(t.output_path!, splices);
  takes.patchSettings(id, { seam: m });
  broadcast({ type: 'take', take: takes.get(id) });
  return m;
}

async function seamGraph(b: any, seed: number): Promise<Built> {
  const src = finishedVideo(Number(b.sourceTake));
  const ss = settingsOf(src);
  const mode: 'trim' | 'regen' | 'bridge' = b.mode === 'trim' || b.mode === 'regen' ? b.mode : 'bridge';
  const clip = await loadClip(src.output_path!);
  const n = clip.tex.length;
  const before = scoreWindow(clip);
  const named = { shotName: b.shotName || ss.shotName || src.shot_name, fileSeed: ss.fileSeed ?? ss.seed };
  const common = {
    app: 'seam', mode, sourceTake: src.id, ...named,
    prompt: ss.prompt, userPrompt: ss.userPrompt, width: clip.w, height: clip.h, fps: clip.fps,
    before: { ratio: before.ratio, verdict: before.verdict },
  };
  if (mode === 'trim') {
    const plan = planTrim(clip);
    if (!plan) throw new Error('No trim of this clip closes the loop. Bridge the wrap instead.');
    const video = await stageTakeFile(src, 'seam');
    return {
      graph: buildSeamTrimGraph({ video, start: plan.start, frames: plan.frames, fps: clip.fps }),
      kind: 'video', parent: src.id,
      settings: { ...common, plan: { start: plan.start, frames: plan.frames, predicted: plan.predicted.ratio }, seconds: Math.round((plan.frames / clip.fps) * 10) / 10 },
    };
  }
  const prompt = typeof ss.prompt === 'string' && ss.prompt.trim() ? ss.prompt : 'The same shot, continuous natural motion.';
  const negative = typeof ss.negative === 'string' && ss.negative ? ss.negative : undefined;
  if (Math.max(clip.w, clip.h) > 1920) throw new Error('The bridge renders at the clip\'s own size, up to 1920 px on the long edge. Improve the seam before upscaling.');
  if (clip.w % 32 || clip.h % 32) throw new Error(`The bridge needs a frame size in multiples of 32; this clip is ${clip.w}x${clip.h}.`);
  if (mode === 'regen') {
    const plan = planRegen(n);
    const sigma = Number.isFinite(b.sigma) ? Math.max(0.2, Math.min(0.85, Number(b.sigma))) : SEAM_REGEN_SIGMA;
    const video = await stageTakeFile(src, 'seam');
    return {
      graph: buildSeamRegenGraph({ video, n, ...plan, width: clip.w, height: clip.h, fps: clip.fps, seed, prompt, negative, sigma }),
      kind: 'video', parent: src.id,
      settings: { ...common, plan, sigma, seconds: Math.round((n / clip.fps) * 10) / 10 },
    };
  }
  const plan = planBridge(n, clip.fps, Number(b.bridgeSeconds) || 1);
  const video = await stageTakeFile(src, 'seam');
  return {
    graph: buildSeamBridgeGraph({
      video, n, anchorA: plan.anchorA, anchorB: plan.anchorB, bridgeFrames: plan.bridgeFrames,
      width: clip.w, height: clip.h, fps: clip.fps, seed, prompt, negative,
      guideStrength: Number.isFinite(b.guideStrength) ? Math.max(0.1, Math.min(1, Number(b.guideStrength))) : undefined,
    }),
    kind: 'video', parent: src.id,
    settings: { ...common, plan, seconds: Math.round((n / clip.fps) * 10) / 10 },
  };
}

/**
 * Queue one fix of `fix` kind for the loop `rootId`. `next` is what the doctor
 * tries if this one still measures as a visible seam.
 */
async function queueSeamFix(rootId: number, fix: SeamFix, next: SeamFix[]): Promise<number[]> {
  const root = finishedVideo(rootId);
  const doctor = { root: rootId, next };
  if (fix === 'reseed') {
    // The original loop again with a new seed; measured like any loop when it lands.
    const origin = finishedVideo(originOf(rootId));
    const s = settingsOf(origin);
    if (!isLoopTake(s) || s.app === 'seam') throw new Error('Only a rendered loop can be re-rendered with a new seed.');
    const body = { ...s, seed: undefined, seam: undefined, hdr: undefined, seamFix: undefined, doctor: { ...doctor, root: origin.id } };
    return queueTakes(body, 1);
  }
  return queueTakes({ kind: 'seam', mode: fix, sourceTake: root.id, doctor, projectId: root.project_id ?? undefined }, 1);
}

/**
 * Fix a take's seam. `auto` measures first, then tries SEAM_ORDER: a trim
 * only when one is predicted to close, and each later step only if the one
 * before still measures as visible (afterRender follows the chain).
 */
async function startSeamFix(id: number, strategy: 'auto' | SeamFix) {
  const t = finishedVideo(id);
  const s = settingsOf(t);
  const before = s.seam ?? (await measureTake(id));
  if (strategy !== 'auto') return { fix: strategy, before, takeIds: await queueSeamFix(id, strategy, []) };
  if (before.verdict === 'seamless') return { fix: null, before, takeIds: [] as number[] };
  const order = [...SEAM_ORDER];
  if (!planTrim(await loadClip(t.output_path!))) order.splice(order.indexOf('trim'), 1);
  if (!isLoopTake(s) || s.app === 'seam') order.splice(order.indexOf('reseed'), 1);
  const [first, ...rest] = order;
  return { fix: first, before, takeIds: await queueSeamFix(id, first, rest) };
}

app.get('/api/takes/:id/seam', async (req, reply) => {
  try {
    return await measureTake(Number((req.params as any).id));
  } catch (e) {
    return reply.code(400).send({ error: e instanceof Error ? e.message : 'could not measure' });
  }
});

app.post('/api/takes/:id/fix-seam', async (req, reply) => {
  const id = Number((req.params as any).id);
  const b = (req.body ?? {}) as { strategy?: string };
  const strategy = (['trim', 'regen', 'bridge', 'reseed'] as const).find((x) => x === b.strategy) ?? 'auto';
  try {
    if (strategy !== 'trim' && eng.isLocal()) {
      const missing = await blockingReason(bundlesFor({ kind: 'seam', mode: 'bridge' }));
      if (missing) return reply.code(412).send({ error: missing });
    }
    return await startSeamFix(id, strategy);
  } catch (e) {
    return reply.code(400).send({ error: e instanceof Error ? e.message : 'could not fix the seam', takeIds: (e as any)?.takeIds });
  }
});

// ---------- Stage ----------
// A shot blocked in 3D (src/stage.ts) renders through LTX-2.5 Layout to Render.

const ASSET = /^asset:[0-9a-f-]{36}$/i;
const STAGE_INPUTS = ['clayVideo', 'depthVideo', 'depthImage', 'clayImage', 'lookImage'] as const;

/**
 * Make a Stage shot body ready to build: a clean scene, upload tokens only
 * (never a path), and the blocking drawn here when an agent sent just the scene.
 */
async function prepareStage(b: any): Promise<any> {
  const out = { ...b };
  if (out.scene !== undefined) out.scene = cleanStageScene(out.scene);
  // A model prop by take id must be a 3D take; the server draws it as its box either way.
  for (const p of out.scene?.props ?? []) {
    if (p.type !== 'glb' || !p.take) continue;
    const t = takes.get(p.take);
    if (!t || t.kind !== 'object') throw new Error(`prop ${p.label ?? p.id}: take ${p.take} is not a 3D model take`);
  }
  for (const k of STAGE_INPUTS) {
    if (out[k] === undefined || out[k] === null || out[k] === '') { delete out[k]; continue; }
    if (typeof out[k] !== 'string' || !ASSET.test(out[k])) throw new Error(`${k} must be an upload token (POST /api/upload or /api/stage/blocking)`);
  }
  if (!out.clayVideo) {
    if (!out.scene) throw new Error('Stage needs a blocked scene, or the clay clip from /api/stage/blocking');
    // The size asked for (a tier, or the older draft/final), else the machine-wide tier, held at Stage's cap.
    const tier = stageTier(out.resolution) ?? stageTier(out.quality) ?? appTier('stage', await currentTier());
    out.resolution = tier;
    delete out.quality;
    const t0 = Date.now();
    Object.assign(out, await rasterBlocking(out.scene, tier), { blockedOn: 'server' });
    console.log(`[openfield] stage blocking drawn on the CPU in ${((Date.now() - t0) / 1000).toFixed(1)}s`);
  }
  const ls = lookSize(out.scene?.aspect ?? '16:9');
  out.lookWidth = Number(out.lookWidth) || ls.w;
  out.lookHeight = Number(out.lookHeight) || ls.h;
  if (!out.lookImage && !out.depthImage) throw new Error('Stage needs a look frame, or the depth pass to make one from');
  return out;
}

/** The look frame: Z-Image Turbo on the depth pass, or Qwen-Image-Edit on the clay frame. */
async function stageLookGraph(b: any, seed: number): Promise<Built> {
  for (const k of ['depthImage', 'clayImage'] as const) {
    if (b[k] !== undefined && (typeof b[k] !== 'string' || !ASSET.test(b[k]))) throw new Error(`${k} must be an upload token`);
  }
  const snap16 = (v: unknown, d: number) => Math.max(256, Math.min(2048, Math.round((Number(v) || d) / 16) * 16));
  const ls = lookSize('16:9');
  const width = snap16(b.width, ls.w);
  const height = snap16(b.height, ls.h);
  const text = typeof b.prompt === 'string' && b.prompt.trim() ? b.prompt.trim() : 'A finished film still of this set.';
  if (b.engine === 'edit') {
    if (!b.clayImage) throw new Error('A look frame from the clay needs the clay frame');
    const images = [b.clayImage as string];
    let instruction = lookEditInstruction(text);
    // Cast members with pictures fill the free image slots, named in the instruction.
    const ids: number[] = Array.isArray(b.cast) ? b.cast.map(Number) : [];
    if (ids.length && typeof b.castSource === 'string') {
      const all = castDb.list();
      const members = ids.map((id) => all.find((m) => m.id === id)).filter((m): m is NonNullable<typeof m> => !!m);
      for (const m of members) m.refs = await liveRefs(m);
      const c = composeInstruction(b.castSource, allocate(members.filter((m) => m.refs.length), 2), { offset: 1, all });
      images.push(...c.images);
      instruction = lookEditInstruction(c.instruction);
    }
    const have = new Set(await comfy.comboOptions('LoraLoaderModelOnly', 'lora_name'));
    return {
      kind: 'still',
      graph: buildEditGraph({ images, instruction, width, height, seed, quality: 'draft', lightning: have.has(EDIT_LIGHTNING_2509) ? EDIT_LIGHTNING_2509 : EDIT_LIGHTNING }),
      settings: { width, height, compiledLook: instruction },
    };
  }
  if (!b.depthImage) throw new Error('A look frame needs the depth pass of the first frame');
  const figures = Array.isArray(b.scene?.props) ? b.scene.props.filter((x: any) => x?.type === 'figure').length : 0;
  const compiled = lookPrompt(text, figures);
  return {
    kind: 'still',
    graph: buildStageLookGraph({ depth: b.depthImage, prompt: compiled, width, height, seed }),
    settings: { width, height, compiledLook: compiled },
  };
}

/** The shot: the clay clip and the look frame through Layout to Render. */
async function stageShotGraph(b: any, seed: number): Promise<Built> {
  if (!b.clayVideo || !b.lookImage) throw new Error('A Stage shot needs its clay clip and a look frame');
  const clip = await probeInput(b.clayVideo);
  checkSize(clip.w, clip.h);
  const prompt = typeof b.prompt === 'string' && b.prompt.trim() ? b.prompt.trim() : 'A finished film shot.';
  return {
    kind: 'video',
    graph: buildStageShotGraph({ clay: b.clayVideo, height: clip.h, look: b.lookImage, prompt, seed, filenamePrefix: 'openfield/stage' }),
    settings: { width: clip.w, height: clip.h, seconds: Math.round(clip.seconds * 10) / 10, lengthFrames: b.frames },
  };
}

/** The page's WebGL blocking (clay + depth frames) becomes engine inputs. */
app.post('/api/stage/blocking', async (req, reply) => {
  try {
    const t0 = Date.now();
    const r = await ingestBlocking(req.body);
    return { ...r, took: Math.round((Date.now() - t0) / 100) / 10 };
  } catch (e) {
    return reply.code(400).send({ error: e instanceof Error ? e.message : 'could not read the blocking' });
  }
});

// ---------- Finish in HDR ----------

/** LTX's SDR-to-HDR pass holds the whole clip at once: keep it to what fits beside the model on a 32 GB card. */
const HDR_MAX_PIXELS = 1280 * 736;
const HDR_MAX_FRAMES = 241;

async function hdrGraph(b: any, seed: number): Promise<Built> {
  if (!eng.isLocal()) throw new Error('Finish in HDR collects its EXR frames from a local ComfyUI; it does not run on a cloud engine yet.');
  const src = finishedVideo(Number(b.sourceTake));
  const ss = settingsOf(src);
  const info = await videoInfo(src.output_path!);
  if (info.w * info.h > HDR_MAX_PIXELS) throw new Error(`Finish in HDR runs up to about 1280x720; this take is ${info.w}x${info.h}. Finish before upscaling.`);
  if (info.frames > HDR_MAX_FRAMES) throw new Error(`Finish in HDR runs up to ${HDR_MAX_FRAMES} frames (10 s); this take has ${info.frames}.`);
  const video = await stageTakeFile(src, 'hdr');
  const tag = `${src.id}_${Date.now().toString(36)}`;
  return {
    graph: buildHdrGraph({ video, frames: info.frames, loop: isLoopTake(ss), withAudio: info.audio, seed, tag }),
    kind: 'video', parent: src.id,
    settings: {
      app: 'hdr', sourceTake: src.id, hdrTag: tag, frames: info.frames, fps: info.fps, width: info.w, height: info.h,
      seconds: Math.round((info.frames / info.fps) * 10) / 10,
      shotName: b.shotName || ss.shotName || src.shot_name, fileSeed: ss.fileSeed ?? ss.seed,
      prompt: ss.prompt, userPrompt: ss.userPrompt,
    },
  };
}

/** Pull the HDR finish's EXRs and HLG master out of ComfyUI and write the downloads. */
async function finishHdr(id: number) {
  const t = finishedVideo(id);
  const s = settingsOf(t);
  try {
    const r = await collectHdr(s.hdrTag, s.frames, t.output_path!.replace(/\.[^.\/]+$/, ''));
    takes.patchSettings(id, { hdr: r });
  } catch (e) {
    takes.patchSettings(id, { hdr: { error: e instanceof Error ? e.message : String(e) } });
  }
  broadcast({ type: 'take', take: takes.get(id) });
}

/** Collect an HDR finish's files again (after a failed or partial collection). */
app.post('/api/takes/:id/collect-hdr', async (req, reply) => {
  const t = takes.get(Number((req.params as any).id));
  if (!t || settingsOf(t).app !== 'hdr') return reply.code(404).send({ error: 'not an HDR finish' });
  await finishHdr(t.id);
  return settingsOf(takes.get(t.id)!).hdr;
});

/** HDR downloads: exr (zip), hlg (HEVC .mov), prores (.mov). */
app.get('/api/takes/:id/file/:which', async (req, reply) => {
  const t = takes.get(Number((req.params as any).id));
  const hdr = t ? settingsOf(t).hdr : undefined;
  const which = String((req.params as any).which);
  const named: string | undefined = which === 'exr' ? hdr?.exrZip : which === 'hlg' ? hdr?.hlgMov : which === 'prores' ? hdr?.proresMov : undefined;
  if (named && !existsSync(named)) return reply.code(410).send({ error: `file no longer on disk: ${named}` });
  const path = besideOutput(t?.output_path, named);
  if (!path) return reply.code(404).send({ error: 'no such file for this take' });
  if (!existsSync(path)) return reply.code(410).send({ error: `file no longer on disk: ${path}` });
  reply.headers({
    'Content-Type': which === 'exr' ? 'application/zip' : 'video/quicktime',
    'Content-Length': statSync(path).size,
    'Content-Disposition': `attachment; filename="${path.split(/[/\\]/).pop()}"`,
  });
  return reply.send(createReadStream(path));
});

/** Everything that runs once a take's file is on disk. */
async function afterRender(id: number) {
  const t = takes.get(id);
  if (!t || t.status !== 'done') return;
  const s = settingsOf(t);
  if (s.app === 'hdr') await finishHdr(id);
  if (t.kind !== 'video' || !isLoopTake(s)) return;
  const m = await measureTake(id);
  if (m.verdict === 'seamless') return;
  if (s.doctor) {
    const [next, ...rest] = (s.doctor.next ?? []) as SeamFix[];
    if (next) await queueSeamFix(Number(s.doctor.root), next, rest);
  } else if (s.seamFix === 'auto') {
    await startSeamFix(id, 'auto');
  }
}

/**
 * Legacy one-click 2x (Sharpen) of a finished take. The Upscale app and the
 * MCP server use /api/generate with kind 'upscale'; this stays for old clients.
 */
app.post('/api/takes/:id/upres', async (req, reply) => {
  const b = (req.body ?? {}) as any;
  const id = Number((req.params as any).id);
  const missing = await blockingReasonFor(eng.isLocal(), bundlesFor({ kind: 'upscale', mode: 'sharpen', model: b.model === 'ultrasharp' ? 'ultrasharp' : 'esrgan' }));
  if (missing) return reply.code(412).send({ error: missing });
  try {
    const r = await queueTakes({ kind: 'upscale', mode: 'sharpen', sourceTake: id, model: b.model === 'ultrasharp' ? 'ultrasharp' : 'esrgan', rife: !!b.rife }, 1);
    return { takeId: r[0] };
  } catch (e) {
    return reply.code(400).send({ error: e instanceof Error ? e.message : 'submit failed' });
  }
});

app.post('/api/stop', async () => {
  for (const t of takes.active()) if (t.status === 'rendering' && t.prompt_id) await eng.cancel(t.prompt_id).catch(() => {});
  return { ok: true };
});

/** Cancel one take — interrupt if it's the live render, dequeue if waiting. */
app.post('/api/takes/:id/cancel', async (req, reply) => {
  const t = takes.get(Number((req.params as any).id));
  if (!t) return reply.code(404).send({ error: 'not found' });
  if (t.status !== 'rendering' && t.status !== 'queued') {
    return reply.code(400).send({ error: `take is ${t.status}` });
  }
  if (t.prompt_id) await eng.cancel(t.prompt_id).catch(() => {});
  takes.fail(t.id, 'cancelled', true);
  broadcast({ type: 'take', take: takes.get(t.id) });
  // A scene cut still waiting on its shots takes them down with it.
  if (!t.prompt_id && JSON.parse(t.settings).cut) {
    for (const s of shotsOf(t.id)) {
      if (s.status !== 'queued' && s.status !== 'rendering') continue;
      if (s.prompt_id) await eng.cancel(s.prompt_id).catch(() => {});
      takes.fail(s.id, 'cancelled with its scene', true);
      broadcast({ type: 'take', take: takes.get(s.id) });
    }
  }
  return { ok: true };
});

/** Nuke everything — pending queue and the live render. */
app.post('/api/queue/clear', async () => {
  const active = takes.active();
  await Promise.allSettled(active.filter((t) => t.prompt_id).map((t) => eng.cancel(t.prompt_id!)));
  await eng.cancelAll();
  for (const t of active) {
    takes.fail(t.id, 'queue cleared', true);
    broadcast({ type: 'take', take: takes.get(t.id) });
  }
  return { ok: true };
});

/** Start ComfyUI via the configured COMFY_LAUNCH command. */
app.post('/api/engine/start', async (_req, reply) => {
  if (!comfy.canLaunchEngine()) {
    return reply.code(501).send({
      error: 'No COMFY_LAUNCH command is configured — start ComfyUI yourself, or set one in .env (see .env.example).',
    });
  }
  const ok = await comfy.launchEngine();
  if (ok) clearPreflightCache(); // fresh engine may expose different weights
  return { ok };
});

/** What each feature needs on disk, and what is actually there. */
app.get('/api/preflight', async (req) => {
  const force = !!(req.query as any)?.refresh;
  return { bundles: await preflight(force) };
});

// ---------- style preambles ----------

app.get('/api/preambles', async () => preambles.list());

app.post('/api/preambles', async (req, reply) => {
  const { name, text } = (req.body ?? {}) as { name?: string; text?: string };
  if (!name?.trim() || !text?.trim()) return reply.code(400).send({ error: 'name and text required' });
  try {
    return { id: preambles.create(name.trim(), text.trim()) };
  } catch {
    return reply.code(409).send({ error: 'a preamble with that name already exists' });
  }
});

app.put('/api/preambles/:id', async (req, reply) => {
  const id = Number((req.params as any).id);
  if (!preambles.get(id)) return reply.code(404).send({ error: 'not found' });
  const { name, text } = (req.body ?? {}) as { name?: string; text?: string };
  try {
    preambles.update(id, { name: name?.trim(), text: text?.trim() });
  } catch {
    return reply.code(409).send({ error: 'a preamble with that name already exists' });
  }
  return preambles.get(id);
});

app.delete('/api/preambles/:id', async (req) => {
  preambles.delete(Number((req.params as any).id));
  return { ok: true };
});

// ---------- cast ----------
// Characters, props and places, @mentioned in any prompt (server/cast.ts).

type RefSource = { token?: string; takeId?: number };
/** Only an upload token or a take id; anything else (a file path) is refused. */
function refSources(v: unknown): RefSource[] | null {
  if (v === undefined) return [];
  if (!Array.isArray(v)) return null;
  const out: RefSource[] = [];
  for (const x of v) {
    if (!x || typeof x !== 'object') return null;
    const keys = Object.keys(x);
    if (keys.some((k) => k !== 'token' && k !== 'takeId')) return null;
    const { token, takeId } = x as RefSource;
    if (typeof token === 'string' && /^asset:[0-9a-f-]{36}$/i.test(token)) out.push({ token });
    else if (Number.isInteger(takeId) && takeId! > 0) out.push({ takeId });
    else return null;
  }
  return out;
}
const BAD_REFS = 'Cast pictures come from an upload token (POST /api/upload) or a take id';
const castName = (v: unknown) => (typeof v === 'string' ? v.trim().replace(/^@+/, '').replace(/\s+/g, ' ') : '');
/** Names become @mentions: letters, digits, spaces, - _ ' and dots, up to 40 characters. */
const NAME_OK = /^[\p{L}\p{N}][\p{L}\p{N} _'.-]{0,39}$/u;

function castOut(m: ReturnType<typeof castDb.get> & {}) {
  return { ...m, refs: m.refs.map((r, i) => ({ ...r, url: `/api/cast/${m.id}/ref/${i}?v=${encodeURIComponent(r.token)}` })) };
}

app.get('/api/cast', async () => castDb.list().map(castOut));

app.post('/api/cast', async (req, reply) => {
  const b = (req.body ?? {}) as { name?: string; kind?: string; notes?: string; refs?: RefSource[] };
  const name = castName(b.name);
  if (!NAME_OK.test(name)) return reply.code(400).send({ error: 'Give it a name: letters, numbers and spaces, up to 40 characters' });
  if (castDb.byName(name)) return reply.code(409).send({ error: `There is already a cast member called ${name}` });
  const kind = (CAST_KINDS as string[]).includes(String(b.kind)) ? (b.kind as CastKind) : 'character';
  const parsed = refSources(b.refs);
  if (!parsed) return reply.code(400).send({ error: BAD_REFS });
  const srcs = parsed.slice(0, MAX_REFS);
  if (!srcs.length) return reply.code(400).send({ error: 'Add at least one picture' });
  try {
    const refs = [];
    for (const r of srcs) refs.push(await refFrom(name, r));
    const id = castDb.create({ name, kind, refs, notes: String(b.notes ?? '').trim().slice(0, 1200) });
    return castOut(castDb.get(id)!);
  } catch (e) {
    return reply.code(400).send({ error: e instanceof Error ? e.message : 'could not save the pictures' });
  }
});

app.put('/api/cast/:id', async (req, reply) => {
  const m = castDb.get(Number((req.params as any).id));
  if (!m) return reply.code(404).send({ error: 'not found' });
  const b = (req.body ?? {}) as { name?: string; kind?: string; notes?: string; addRefs?: RefSource[]; removeRefs?: number[]; order?: number[] };
  const patch: Parameters<typeof castDb.update>[1] = {};
  if (b.name !== undefined) {
    const name = castName(b.name);
    if (!NAME_OK.test(name)) return reply.code(400).send({ error: 'Names are letters, numbers and spaces, up to 40 characters' });
    const clash = castDb.byName(name);
    if (clash && clash.id !== m.id) return reply.code(409).send({ error: `There is already a cast member called ${name}` });
    if (name !== m.name) { patch.name = name; patch.refs = await renameFiles(m, name); }
  }
  if (b.kind !== undefined && (CAST_KINDS as string[]).includes(b.kind)) patch.kind = b.kind as CastKind;
  if (b.notes !== undefined) patch.notes = String(b.notes).trim().slice(0, 1200);
  const adds = refSources(b.addRefs);
  if (!adds) return reply.code(400).send({ error: BAD_REFS });
  let refs = patch.refs ?? m.refs;
  if (Array.isArray(b.removeRefs)) refs = refs.filter((_, i) => !b.removeRefs!.includes(i));
  if (Array.isArray(b.order) && b.order.length === refs.length) refs = b.order.map((i) => refs[i]).filter(Boolean);
  try {
    for (const r of adds.slice(0, Math.max(0, MAX_REFS - refs.length))) {
      refs = [...refs, await refFrom(patch.name ?? m.name, r)];
    }
  } catch (e) {
    return reply.code(400).send({ error: e instanceof Error ? e.message : 'could not save the picture' });
  }
  if (!refs.length) return reply.code(400).send({ error: 'A cast member keeps at least one picture' });
  patch.refs = refs;
  castDb.update(m.id, patch);
  return castOut(castDb.get(m.id)!);
});

app.delete('/api/cast/:id', async (req) => {
  // The pictures stay on disk under <output>/Cast: deleting a member never deletes files.
  castDb.delete(Number((req.params as any).id));
  return { ok: true };
});

/** A cast picture, from our own copy on disk. */
app.get('/api/cast/:id/ref/:n', async (req, reply) => {
  const m = castDb.get(Number((req.params as any).id));
  const r = m?.refs[Number((req.params as any).n)];
  if (!r || !isCastFile(r.file)) return reply.code(404).send({ error: 'not found' });
  const ext = extname(r.file).toLowerCase();
  reply.header('Content-Type', ext === '.jpg' ? 'image/jpeg' : ext === '.webp' ? 'image/webp' : 'image/png').header('Cache-Control', 'max-age=86400');
  return reply.send(createReadStream(r.file));
});

/**
 * Compose a hero frame of cast members in a shot (Qwen-Image-Edit), as a still
 * take. Returns at once with the take id; the frame lands like any still.
 */
app.post('/api/cast/hero', async (req, reply) => {
  const b = (req.body ?? {}) as { castIds?: number[]; shot?: string; width?: number; height?: number; projectId?: number; seed?: number };
  const missing = await blockingReasonFor(eng.isLocal(), ['edit']);
  if (missing) return reply.code(412).send({ error: missing });
  const ids = (Array.isArray(b.castIds) ? b.castIds : []).map(Number).filter(Boolean);
  const shot = String(b.shot ?? '');
  if (!ids.length && !mentioned(shot).length) return reply.code(400).send({ error: 'Name at least one cast member' });
  const size = heroSize(Number(b.width) || 1328, Number(b.height) || 752);
  // castHeroFrame waits for the render; answer as soon as the take is queued.
  try {
    const takeId = await new Promise<number>((res, rej) => {
      castHeroFrame(ids, shot, { ...size, projectId: b.projectId ?? null, seed: b.seed, onQueued: res })
        .catch((e) => { rej(e); console.error('[openfield] hero frame failed:', e instanceof Error ? e.message : e); });
    });
    return { takeId };
  } catch (e) {
    return reply.code(400).send({ error: e instanceof Error ? e.message : 'the hero frame did not queue' });
  }
});

/** Your own LoRAs: every LoRA file the engine sees that no app loads by itself, with its model family. */
app.get('/api/loras', async () => ({ loras: await listUserLoras().catch(() => []) }));

/** Available checkpoints by model family + the current model card. */
app.get('/api/models', async () => {
  const checkpoints = await comfy.listCheckpoints().catch(() => ({}));
  return {
    checkpoints,
    card: {
      video: {
        name: 'MiniMax H3 (Hailuo 3)',
        checkpoints: 'FL2VA / Ref2VA · pruned fp8 · 20GB each',
        encoder: 'Qwen3VL-32B NVFP4 (15GB)',
        native: '24fps · 768px-class · 5-15s (17k+5 frame grid) · audio always on',
        strengths: 'dialogue/voice, held stillness, direction-following, refs',
        license: 'Community license EXCLUDES US, EU, UK and South Korea; experiments only until licensed',
      },
      ltx25: {
        name: 'LTX-2.5 (22B distilled)',
        checkpoints: 'int8-convrot 21GB · Gemma-4-12B-with-proj encoder 15GB',
        native: '24fps · t2v/i2v/flf2v · two-stage (half-res base → 2x refine) · 8+4 steps · audio optional',
        strengths: 'multishot consistency across cuts, FLF2V loop closure, cleaner motion (neural decoder VAE)',
        license: 'LTX-2.x community license — free commercial use under $10M ARR',
      },
      ltx: {
        name: 'LTX-Video 2.3 (22B)',
        checkpoints: 'SpiceModels fine-tunes via dropdown · Gemma-3-12B encoder',
        native: '25fps · two-stage (half-res base → 2x refine) · distilled 8+4 steps · audio',
        strengths: 'fast animation-tuned generation; community checkpoint/LoRA playground',
        license: 'LTX-2 community license — check per-checkpoint terms for fine-tunes',
      },
      stills: {
        qwen: 'Qwen-Image fp8 · Apache 2.0 · text/layout specialist',
        flux2: 'FLUX.2 dev fp8mixed 34GB · non-commercial dev license · photoreal lead',
      },
    },
  };
});

app.delete('/api/queue/:promptId', async (req) => {
  const promptId = (req.params as any).promptId as string;
  await eng.cancel(promptId).catch(() => {});
  const t = takes.byPrompt(promptId);
  if (t) {
    takes.fail(t.id, 'removed from queue', true);
    broadcast({ type: 'take', take: takes.get(t.id) });
  }
  return { ok: true };
});

app.get('/api/takes', async (req) => {
  const pid = (req.query as any).project ? Number((req.query as any).project) : null;
  return takes.list(pid, 500);
});

/**
 * The ComfyUI origins allowed to fetch a take's workflow cross-origin. ComfyUI
 * fetches the URL itself when a workflow link is dropped on its canvas.
 * 127.0.0.1 and localhost are the same machine but different origins.
 */
function comfyOrigins(): Set<string> {
  const u = new URL(config.comfyUrl);
  const out = new Set([u.origin]);
  for (const [a, b] of [['127.0.0.1', 'localhost'], ['localhost', '127.0.0.1']]) {
    if (u.hostname === a) out.add(u.origin.replace(a, b));
  }
  return out;
}

/**
 * The API-format ComfyUI workflow that produced a take, as a plain JSON file
 * that loads in ComfyUI by dropping it on the canvas. ?download=1 saves it.
 * Takes from before workflows were recorded are backfilled from the engine
 * while it still remembers the job.
 */
async function takeWorkflow(req: FastifyRequest, reply: FastifyReply) {
  const t = takes.get(Number((req.params as any).id));
  if (!t) return reply.code(404).send({ error: 'take not found' });
  let wf = takeWorkflows.get(t.id)?.graph;
  if (!wf && t.prompt_id) {
    const ran = await eng.executedWorkflow(t.prompt_id);
    if (ran) {
      takeWorkflows.set(t.id, ran, 'engine');
      wf = ran;
    }
  }
  if (!wf) return reply.code(404).send({ error: 'no workflow was recorded for this take, and the engine no longer has it' });
  const origin = req.headers.origin;
  if (origin && comfyOrigins().has(origin)) reply.header('Access-Control-Allow-Origin', origin).header('Vary', 'Origin');
  const fname = `openfield_take_${t.id}_${safeShotName(t.shot_name)}.json`;
  if ((req.query as any).download) reply.header('Content-Disposition', `attachment; filename="${fname}"`);
  // Exactly application/json: ComfyUI only treats a dropped link as a workflow
  // when its MIME is that or its name ends in .json. A Buffer body keeps
  // Fastify from appending "; charset=utf-8".
  reply.header('Content-Type', 'application/json');
  return reply.send(Buffer.from(JSON.stringify(wf, null, 2)));
}
app.get('/api/takes/:id/workflow', takeWorkflow);
// Same file under a filename, which is what ComfyUI shows when a link is dropped on it.
app.get('/api/takes/:id/workflow/:file', takeWorkflow);

app.post('/api/takes/:id/star', async (req) => {
  const id = Number((req.params as any).id);
  takes.star(id, !!(req.body as any)?.on);
  return takes.get(id);
});

app.delete('/api/takes/:id', async (req) => {
  const id = Number((req.params as any).id);
  const t = takes.get(id);
  // Nexora (portail) : supprimer efface aussi les fichiers du serveur et rend l'espace à l'organisation.
  if (configAuth && t) {
    const s = JSON.parse(t.settings);
    const fichiers = [t.output_path, s.alphaPath].filter((f): f is string => typeof f === 'string' && existsSync(f));
    const { unlink } = await import('fs/promises');
    for (const f of fichiers) await unlink(f).catch(() => {});
    if (s.nexoraEspace?.etat === 'compte' || s.nexoraEspace?.etat === 'depasse') {
      const cle = accesOrganisation(t.organisation_id)?.key;
      if (cle) {
        const r = await espaceSite(configAuth.siteUrl, () => cle).enregistrer(-s.nexoraEspace.octets).catch(() => null);
        if (r?.ok) marquerPlein(t.organisation_id, false);
      }
    }
  }
  takes.delete(id);
  return { ok: true };
});

app.get('/api/projects', async () => projects.list());
app.post('/api/projects', async (req, reply) => {
  const { name, folder } = req.body as any;
  if (!name || !folder) return reply.code(400).send({ error: 'name and folder required' });
  // takes are written under a project's folder, so it must live inside the output folder
  const root = resolve(config.outputDir);
  const dir = resolve(root, String(folder));
  if (dir !== root && !dir.startsWith(root + sep)) return reply.code(400).send({ error: 'A project folder must be inside the output folder' });
  return { id: projects.create(name, dir) };
});

/** Serve an uploaded input back to the browser (EDIT restores wells). */
app.get('/api/input-image/:name', async (req, reply) => {
  const name = String((req.params as any).name);
  const img = await eng.readInput(name);
  if (!img) return reply.code(404).send({ error: 'not found' });
  const ext = extname(img.name).toLowerCase();
  const AV: Record<string, string> = { '.glb': 'model/gltf-binary', '.mp4': 'video/mp4', '.mov': 'video/quicktime', '.webm': 'video/webm', '.wav': 'audio/wav', '.mp3': 'audio/mpeg', '.m4a': 'audio/mp4', '.flac': 'audio/flac', '.ogg': 'audio/ogg' };
  reply.header('Content-Type', AV[ext] ?? (ext === '.jpg' || ext === '.jpeg' ? 'image/jpeg' : ext === '.webp' ? 'image/webp' : 'image/png'));
  return reply.send(img.data);
});

/**
 * Poster frame for a take (grid thumbnails). Videos get a JPEG pulled from
 * 0.5s in, made on first request and cached next to the file; stills serve
 * the image itself.
 */
app.get('/api/poster/:id', async (req, reply) => {
  const t = takes.get(Number((req.params as any).id));
  if (!t?.output_path || !existsSync(t.output_path)) return reply.code(404).send({ error: 'not found' });
  if (t.output_path.endsWith('.png')) {
    reply.header('Content-Type', 'image/png').header('Cache-Control', 'max-age=86400');
    return reply.send(createReadStream(t.output_path));
  }
  // An object's poster is the first turntable frame (a three-quarter view), or
  // the isolated subject when there is no turntable.
  const model = isModelFile(t.output_path);
  if (model && !existsSync(`${t.output_path}.turntable.mp4`)) {
    const subject = `${t.output_path}.subject.png`;
    if (!existsSync(subject)) return reply.code(404).send({ error: 'no poster for this object' });
    reply.header('Content-Type', 'image/png').header('Cache-Control', 'max-age=3600');
    return reply.send(createReadStream(subject));
  }
  const from = model ? `${t.output_path}.turntable.mp4` : t.output_path;
  const poster = `${t.output_path}.poster.jpg`;
  if (!existsSync(poster)) {
    const { execFile } = await import('child_process');
    await new Promise<void>((res) =>
      execFile(config.ffmpegBin, ['-v', 'error', '-y', '-ss', model ? '0' : '0.5', '-i', from, '-frames:v', '1', '-vf', 'scale=640:-2', '-q:v', '4', poster], () => res()),
    );
    if (!existsSync(poster)) return reply.code(500).send({ error: 'poster extraction failed' });
  }
  reply.header('Content-Type', 'image/jpeg').header('Cache-Control', 'max-age=86400');
  return reply.send(createReadStream(poster));
});

/** Typical render time for a shot like this one, from past takes on this machine. */
app.get('/api/estimate', async (req) => {
  const q = req.query as any;
  const want = (t: any) => {
    const s = JSON.parse(t.settings);
    if (t.kind !== (q.kind === 'still' || q.kind === 'upres' || q.kind === 'object' ? q.kind : 'video')) return false;
    // Upscale takes only answer for the Upscale app, per mode.
    if ((s.app === 'upscale') !== (q.app === 'upscale')) return false;
    // Apps with their own pipeline (Remove background, Restyle, Swap) only answer for themselves.
    if (q.app && s.app !== q.app) return false;
    if (q.mode && s.mode !== q.mode) return false;
    if (q.model && (s.videoModel || s.model) !== q.model) return false;
    if (q.quality && s.quality && s.quality !== q.quality) return false;
    const px = (s.width || 0) * (s.height || 0);
    const qpx = Number(q.w) * Number(q.h);
    if (qpx && Math.abs(px - qpx) / qpx > 0.25) return false;
    if (q.seconds && s.seconds && Math.abs(s.seconds - Number(q.seconds)) > 1) return false;
    return true;
  };
  const secs = takes
    .list(null, 400)
    .filter((t) => t.status === 'done' && t.render_seconds && want(t))
    .map((t) => t.render_seconds!)
    .sort((a, b) => a - b);
  return { seconds: secs.length ? secs[Math.floor(secs.length / 2)] : null, samples: secs.length };
});

/** Unload models and free VRAM on the local engine. */
app.post('/api/free', async (_req, reply) => {
  if (!eng.isLocal()) return reply.code(400).send({ error: 'only for the local engine' });
  await fetch(`${config.comfyUrl}/free`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ unload_models: true, free_memory: true }),
  }).catch(() => null);
  return { ok: true };
});

const isModelFile = (p: string) => /\.(glb|gltf|obj)$/i.test(p);
const mediaMime = (p: string) => {
  const ext = extname(p).toLowerCase();
  return ({ '.png': 'image/png', '.jpg': 'image/jpeg', '.webp': 'image/webp', '.glb': 'model/gltf-binary', '.gltf': 'model/gltf+json', '.obj': 'model/obj', '.mov': 'video/quicktime', '.flac': 'audio/flac', '.mp3': 'audio/mpeg', '.wav': 'audio/wav', '.m4a': 'audio/mp4', '.ogg': 'audio/ogg', '.webm': 'video/webm' } as Record<string, string>)[ext] ?? 'video/mp4';
};

/**
 * An object take's sidecars: the turntable mp4 and the isolated subject the
 * model was built from.
 */
for (const side of ['turntable', 'subject'] as const) app.get(`/api/takes/:id/${side}`, async (req, reply) => {
  const t = takes.get(Number((req.params as any).id));
  if (!t?.output_path || !isModelFile(t.output_path)) return reply.code(404).send({ error: 'not an object take' });
  const path = `${t.output_path}.${side}.${side === 'turntable' ? 'mp4' : 'png'}`;
  if (!existsSync(path)) return reply.code(404).send({ error: `no ${side} for this take` });
  const size = statSync(path).size;
  const mime = side === 'turntable' ? 'video/mp4' : 'image/png';
  const range = req.headers.range;
  const m = range ? /bytes=(\d+)-(\d*)/.exec(range) : null;
  if (m) {
    const start = parseInt(m[1], 10);
    const end = m[2] ? parseInt(m[2], 10) : size - 1;
    reply.code(206).headers({ 'Content-Range': `bytes ${start}-${end}/${size}`, 'Accept-Ranges': 'bytes', 'Content-Length': end - start + 1, 'Content-Type': mime });
    return reply.send(createReadStream(path, { start, end }));
  }
  reply.headers({ 'Content-Length': size, 'Content-Type': mime, 'Accept-Ranges': 'bytes', 'Cache-Control': 'max-age=86400' });
  return reply.send(createReadStream(path));
});

/** Stream a take's media with Range support so the <video> tag can scrub.
 *  ?download=1 forces a save-dialog with the take's real filename.
 *  An Object take's media is its GLB (model/gltf-binary): this URL is the
 *  stable address a scene (the Stage, GLTFLoader) loads the prop from. */
app.get('/api/media/:id', async (req, reply) => {
  const t = takes.get(Number((req.params as any).id));
  if (!t?.output_path) return reply.code(404).send({ error: 'not found' });
  const alpha = (req.query as any).alpha ? besideOutput(t.output_path, JSON.parse(t.settings).alphaPath as string | undefined) : undefined;
  if ((req.query as any).alpha && !alpha) return reply.code(404).send({ error: 'this take has no alpha version' });
  const path = alpha ?? t.output_path;
  // The file lives outside OpenField, in a project folder the user owns — it can
  // be moved or deleted behind our back. Say so instead of throwing a 500.
  if (!existsSync(path)) return reply.code(410).send({ error: `file no longer on disk: ${path}` });
  const size = statSync(path).size;
  const mime = mediaMime(path);
  if ((req.query as any).download || alpha) {
    const fname = path.split(/[/\\]/).pop() || 'take';
    reply.headers({
      'Content-Type': mime,
      'Content-Length': size,
      'Content-Disposition': `attachment; filename="${fname}"`,
    });
    return reply.send(createReadStream(path));
  }
  const range = req.headers.range;
  if (range) {
    const m = /bytes=(\d+)-(\d*)/.exec(range);
    const start = m ? parseInt(m[1], 10) : 0;
    const end = m && m[2] ? parseInt(m[2], 10) : size - 1;
    reply
      .code(206)
      .headers({
        'Content-Range': `bytes ${start}-${end}/${size}`,
        'Accept-Ranges': 'bytes',
        'Content-Length': end - start + 1,
        'Content-Type': mime,
      });
    return reply.send(createReadStream(path, { start, end }));
  }
  reply.headers({ 'Content-Length': size, 'Content-Type': mime, 'Accept-Ranges': 'bytes' });
  return reply.send(createReadStream(path));
});

/**
 * Reconciliation, every 20s: make DB truth match engine truth. Finish takes
 * whose completion we missed and re-attach to jobs still running (e.g. after
 * a restart). Polling the job is authoritative; the event stream is a bonus.
 */
async function reconcile() {
  void eng.etatMoteurs();
  void solderCredits();
  void compterEspace();
  for (const id of waitingCuts()) void advance(id);
  for (const id of filmsEnAttente()) void avancerFilm(id);
  for (const t of takes.active()) {
    if (!t.prompt_id) continue;
    try {
      const h = await eng.result(t.prompt_id);
      if (h.done) void onPromptFinished(t.prompt_id);
      else await eng.reattach(t.prompt_id);
    } catch (e: any) {
      if (e?.name === 'NotFound' || e?.status === 404) {
        takes.fail(t.id, 'no longer known to the engine', true);
        broadcast({ type: 'take', take: takes.get(t.id) });
      }
      /* otherwise the engine is down; the status endpoint reports it */
    }
  }
}
setInterval(() => void reconcile(), 20_000);
// Réglages de l'administration du site (modèles et moteurs) : lus toutes les minutes quand le jeton du service est fourni.
if (process.env.NEXORA_SITE_URL && process.env.NEXORA_CREATIVE_SERVICE_TOKEN) {
  demarrerLectureReglages({ siteUrl: process.env.NEXORA_SITE_URL, jeton: process.env.NEXORA_CREATIVE_SERVICE_TOKEN, journal: (m) => console.log(`[nexora] ${m}`) });
}

// Cast hero frames are ordinary takes queued through the same path.
setCastQueue(queueTakes);
// A take still waiting on a hero frame when the server stopped can never run.
// Nexora : un film attend ses plans sans travail moteur propre ; il reprend par reconcile (avancerFilm), pas un orphelin.
for (const t of takes.orphans()) if (JSON.parse(t.settings).film !== true) takes.fail(t.id, 'interrupted: the server restarted while it waited for its hero frame', true);

// ---------------------------------------------------------------------------------------------------------------------
// Mode Studio (montage expert, éditeur FreeCut de mode-studio/) : créations, assistant, analyses. Voir server/nexora/studio.ts.

/** Sortie d'un programme (ffmpeg, Python) en Buffer, avec stderr ; rejette si le code de sortie n'est pas 0. */
async function executer(bin: string, args: string[], delaiMs = 300_000): Promise<{ stdout: Buffer; stderr: string }> {
  const { execFile } = await import('child_process');
  return new Promise((ok, ko) =>
    execFile(bin, args, { maxBuffer: 1 << 30, encoding: 'buffer', timeout: delaiMs }, (err, stdout, stderr) =>
      err ? ko(Object.assign(new Error(`${bin.split('/').pop()} : ${String(stderr).split('\n').slice(-3).join(' ')}`), { statusCode: 500 }))
        : ok({ stdout, stderr: String(stderr) })));
}

/** Une prise terminée de l'organisation dont le fichier existe encore, ou une réponse 404. */
function priseStudio(id: unknown, reply: FastifyReply) {
  const t = takes.get(Number(id));
  if (!t || t.status !== 'done' || !t.output_path || !existsSync(t.output_path)) {
    reply.code(404).send({ error: 'Ce média n’est pas une création Nexora disponible.' });
    return null;
  }
  return t;
}

app.get('/api/studio/creations', async () => ({ creations: creationsPourStudio(takes.list(null, 500) as any) }));

/**
 * Média d'une création pour le Mode Studio : le fichier d'origine, sauf les formats que l'éditeur ne lit pas (FLAC de
 * MiniMax-Music3), livrés en AAC 256 kb/s (.m4a), convertis une fois puis gardés en cache.
 */
app.get('/api/studio/media/:id', async (req, reply) => {
  const t = priseStudio((req.params as any).id, reply);
  if (!t) return;
  let chemin = t.output_path!;
  if (/\.flac$/i.test(chemin)) {
    const dossier = join(config.outputDir, 'mode-studio-cache');
    mkdirSync(dossier, { recursive: true });
    const m4a = join(dossier, `prise_${t.id}.m4a`);
    if (!existsSync(m4a)) await executer(config.ffmpegBin, ['-v', 'error', '-y', '-i', chemin, '-vn', '-c:a', 'aac', '-b:a', '256k', m4a]);
    chemin = m4a;
  }
  const nom = `${safeShotName(t.shot_name || `prise_${t.id}`)}${extname(chemin).toLowerCase()}`;
  reply.headers({ 'Content-Type': mediaMime(chemin), 'Content-Length': statSync(chemin).size, 'Content-Disposition': `attachment; filename="${nom}"` });
  return reply.send(createReadStream(chemin));
});

/** État d'une génération lancée depuis le Mode Studio ; la création, une fois prête, s'importe dans la timeline. */
app.get('/api/studio/prise/:id', async (req, reply) => {
  const t = takes.get(Number((req.params as any).id));
  if (!t) return reply.code(404).send({ error: 'Génération introuvable.' });
  return { statut: t.status, ...(t.error ? { erreur: t.error } : {}), creation: creationsPourStudio([t as any])[0] ?? null };
});

app.post('/api/studio/assistant', async (req, reply) => {
  let d;
  try { d = lireDemandeAssistant(req.body); }
  catch (e) { return reply.code(400).send({ error: e instanceof Error ? e.message : 'demande invalide' }); }
  try { return await demanderAssistant(d, llmCourant()); }
  catch (e) {
    app.log.warn(`assistant du Mode Studio : ${e instanceof Error ? e.message : e}`);
    return reply.code(502).send({ error: 'L’assistant n’a pas pu répondre. Réessaie dans un instant.' });
  }
});


// ---------- Mode Marketing (vague 2) : kit de marque, gabarits, propositions IA, rendu PDF/PNG ----------
const kitsMarque = new StoreKit(join(config.dataDir, 'marque'));
const dossierMarketing = join(config.dataDir, 'marketing');
const orgMarque = () => compteCourant()?.organisationId ?? null;
const kitOu409 = (reply: any): KitMarque | null => {
  const k = kitsMarque.lire(orgMarque());
  if (!k) { reply.code(409).send({ error: 'Renseigne d’abord ta marque (nom, logo, couleurs) : c’est elle qui habille chaque pièce.' }); return null; }
  return k;
};

app.get('/api/nexora/marque', async () => {
  const kit = kitsMarque.lire(orgMarque());
  return {
    kit, polices: POLICES.map(({ id, nom, genre }) => ({ id, nom, genre })),
    formats: Object.values(FORMATS).filter((f) => gabaritsPour(f.id).length || f.type === 'logo').map((f) => ({ id: f.id, nom: f.nom, largeur: f.largeur, hauteur: f.hauteur, fondPerdu: f.fondPerdu, faces: f.faces, gabarits: gabaritsPour(f.id).map((g) => ({ id: g.id, nom: g.nom, description: g.description })) })),
    controles: kit ? { contrastes: verifierContrastes(kit), logo: kit.logo.svg || kit.logo.png ? controlerLogo(kit.logo) : null, contacts: contactsActifs(kit.contact, kit.langue) } : null,
    cmjn: await ghostscriptDisponible(),
  };
});

app.put('/api/nexora/marque', { bodyLimit: 6_000_000 }, async (req, reply) => {
  const r = KitMarqueSchema.safeParse(req.body);
  if (!r.success) return reply.code(400).send({ error: r.error.issues.slice(0, 3).map((i) => `${i.path.join('.') || 'kit'} : ${i.message}`).join(' ; ') });
  const kit = r.data;
  try { if (kit.logo.svg) kit.logo.svg = assainirSvg(kit.logo.svg); } catch (e) { return reply.code(400).send({ error: e instanceof Error ? e.message : 'logo invalide' }); }
  kitsMarque.ecrire(orgMarque(), kit);
  return { kit, controles: { contrastes: verifierContrastes(kit), logo: kit.logo.svg || kit.logo.png ? controlerLogo(kit.logo) : null, contacts: contactsActifs(kit.contact, kit.langue) } };
});

/** Téléversement du logo (SVG ou PNG en base64) : assainissement, contrôles, couleurs dominantes et palette proposée. */
app.post('/api/nexora/marque/logo', { bodyLimit: 8_000_000 }, async (req, reply) => {
  const b = (req.body ?? {}) as { type?: string; donnees?: string };
  if (typeof b.donnees !== 'string' || b.donnees.length > 4_000_000) return reply.code(400).send({ error: 'Logo manquant ou trop gros (3 Mo au plus).' });
  try {
    if (b.type === 'svg') {
      const svg = assainirSvg(b.donnees);
      const logo = { svg };
      const dom = couleursDeSvg(svg);
      return { logo, controle: controlerLogo(logo), couleurs: dom, palette: paletteDepuisCouleurs(dom) };
    }
    const buf = Buffer.from(b.donnees, 'base64');
    const img = decoderPng(buf);
    const logo = { png: `data:image/png;base64,${buf.toString('base64')}`, largeurPx: img.w, hauteurPx: img.h };
    const dom = couleursDePng(buf);
    return { logo, controle: controlerLogo(logo), couleurs: dom, palette: paletteDepuisCouleurs(dom) };
  } catch (e) { return reply.code(400).send({ error: e instanceof Error ? e.message : 'logo illisible' }); }
});

app.post('/api/nexora/marketing/devis', async (req) => {
  const b = (req.body ?? {}) as any;
  const p: Palier = estPalier(b.palier) ? b.palier : palierDuRole('design') ?? 'eco';
  return { ...devisMarketing((['propositions', 'logos', 'variantes', 'rendu'].includes(b.action) ? b.action : 'propositions') as ActionMarketing, p, { livre: livreUsage }), libelle: LIBELLES_PALIER[p] };
});

/** Spec d'un gabarit (sans appel au modèle, gratuit) : changer de composition, de palette ou de texte en un clic. */
app.post('/api/nexora/marketing/spec', async (req, reply) => {
  const b = (req.body ?? {}) as any;
  const kit0 = kitOu409(reply);
  if (!kit0) return;
  try {
    const kit = variantePalette(kit0, ['inverse', 'sombre'].includes(b.palette) ? b.palette : 'defaut');
    return { spec: construireSpec(String(b.gabarit), String(b.format), kit, b.variables && typeof b.variables === 'object' ? b.variables : {}) };
  } catch (e) { return reply.code(400).send({ error: e instanceof Error ? e.message : 'spec invalide' }); }
});

/** Clients LLM du palier de départ puis des suivants (escalade), mesurés et réservés sous un même devis. */
async function avecPaliers<T>(action: ActionMarketing, tache: string, travail: (clients: ClientPalier[]) => Promise<T>): Promise<{ resultat: T; usage: { credits: number; usd: number; devisCredits: number; palier: Palier | null } }> {
  const depart = palierDuRole('design');
  const compte = compteCourant();
  const ordre: Palier[] = depart ? [depart, ...(['eco', 'equilibre', 'expert'] as Palier[]).filter((p) => p !== depart && paliersDisponibles()[p]).slice(0, 1)] : [];
  if (!depart) return { resultat: await travail([]), usage: { credits: 0, usd: 0, devisCredits: 0, palier: null } };
  const devis = devisMarketing(action, depart, { livre: livreUsage });
  const { resultat, bilan } = await executerSousReservation(
    { fac: facturationCourante(), devis: { ...devis.llm!, creditsReserves: devis.creditsReserves * 2, plafondUsd: devis.llm!.plafondUsd * 2 }, ctx: { run: randomUUID(), tache, utilisateur: compte?.utilisateurId, organisation: compte?.organisationId }, livre: livreUsage },
    (rel) => travail(ordre.map((p) => ({ palier: p, client: clientPalier(p, { surveillant: rel }) }))),
  );
  return { resultat, usage: { credits: bilan.totaux.credits, usd: bilan.totaux.coutUsd, devisCredits: devis.credits, palier: depart } };
}

app.post('/api/nexora/marketing/propositions', async (req, reply) => {
  const kit = kitOu409(reply);
  if (!kit) return;
  let brief;
  try { brief = lireBrief(req.body); } catch (e) { return reply.code(400).send({ error: e instanceof Error ? e.message : 'demande invalide' }); }
  const verdict = await moderer(brief.phrase, llmCourant(), (m) => app.log.warn(m));
  if (!verdict.ok) return reply.code(422).send({ error: verdict.raison, categorie: verdict.categorie });
  try {
    const { resultat, usage } = await avecPaliers('propositions', 'marketing_propositions', (clients) => proposer(brief, kit, clients));
    return { ...resultat, usage };
  } catch (e) {
    app.log.warn(`marketing propositions : ${e instanceof Error ? e.message : e}`);
    return reply.code(502).send({ error: e instanceof Error ? e.message : 'Les propositions n’ont pas pu être préparées.' });
  }
});

app.post('/api/nexora/marketing/logos', async (req, reply) => {
  const kit = kitOu409(reply);
  if (!kit) return;
  const idee = String(((req.body ?? {}) as any).idee ?? '').slice(0, 300);
  try {
    const { resultat, usage } = await avecPaliers('logos', 'marketing_logos', (clients) => idearLogos(kit, idee, clients));
    return { ...resultat, usage };
  } catch (e) { return reply.code(502).send({ error: e instanceof Error ? e.message : 'Les pistes de logo n’ont pas pu être préparées.' }); }
});

const nettoyerMarketing = () => {
  try {
    for (const d of readdirSync(dossierMarketing)) { const p = join(dossierMarketing, d); if (Date.now() - statSync(p).mtimeMs > 24 * 3600_000) rmSync(p, { recursive: true, force: true }); }
  } catch { /* dossier absent */ }
};

/** Rend une spec : PDF (impression avec traits de coupe, sans traits), PNG des faces, SVG de la face avant, contrôle préliminaire. */
app.post('/api/nexora/marketing/rendu', { bodyLimit: 16_000_000 }, async (req, reply) => {
  const kit = kitOu409(reply);
  if (!kit) return;
  const b = (req.body ?? {}) as any;
  let spec;
  try { spec = lireSpec(b.spec); } catch (e) { return reply.code(400).send({ error: e instanceof Error ? e.message : 'spec invalide' }); }
  const id = randomUUID().slice(0, 12), dossier = join(dossierMarketing, id);
  try {
    const cmjn = !!b.cmjn;
    const r: ResultatRendu = await rendre(spec, kit, { cmjn });
    mkdirSync(dossier, { recursive: true });
    const fichiers: { nom: string; url: string; octets: number; genre: string }[] = [];
    const ecrire = (nom: string, buf: Buffer, genre: string) => { writeFileSync(join(dossier, nom), buf); fichiers.push({ nom, url: `/api/nexora/marketing/fichier/${id}/${nom}`, octets: buf.length, genre }); };
    for (const p of r.pdfs) ecrire(`${spec.gabarit}-${p.variante}.pdf`, p.pdf, p.variante === 'impression' ? 'pdf-impression' : 'pdf-sans-traits');
    r.pngs.forEach((p, i) => ecrire(`${spec.gabarit}-${i + 1}-${p.face}.png`, p.png, 'png'));
    // SVG de la première face (pdftocairo, s'il est installé) : texte en contours, utile pour retoucher dans un autre outil.
    const sansTraits = join(dossier, `${spec.gabarit}-sans-traits.pdf`);
    const svg = await executer('pdftocairo', ['-svg', '-f', '1', '-l', '1', sansTraits, join(dossier, `${spec.gabarit}-avant.svg`)], 30_000).then(() => true, () => false);
    if (svg) { const nom = `${spec.gabarit}-avant.svg`; fichiers.push({ nom, url: `/api/nexora/marketing/fichier/${id}/${nom}`, octets: statSync(join(dossier, nom)).size, genre: 'svg' }); }
    nettoyerMarketing();
    return { id, fichiers, controle: r.controle, ms: r.ms, cmjn: r.pdfs[0]?.cmjn ?? false };
  } catch (e) {
    app.log.warn(`rendu marketing : ${e instanceof Error ? e.message : e}`);
    return reply.code(500).send({ error: 'Le rendu a échoué sur ce serveur (Chromium indisponible ?).' });
  }
});

app.get('/api/nexora/marketing/fichier/:id/:nom', async (req, reply) => {
  const { id, nom } = req.params as { id: string; nom: string };
  if (!/^[a-f0-9-]{12}$/.test(id) || !/^[\w.-]+$/.test(nom)) return reply.code(400).send({ error: 'fichier invalide' });
  const p = join(dossierMarketing, id, nom);
  if (!existsSync(p)) return reply.code(404).send({ error: 'Fichier expiré : relance le rendu.' });
  const type = nom.endsWith('.pdf') ? 'application/pdf' : nom.endsWith('.png') ? 'image/png' : 'image/svg+xml';
  return reply.header('content-type', type).header('content-disposition', `${req.url.includes('telecharger') ? 'attachment' : 'inline'}; filename="${nom}"`).send(createReadStream(p));
});

/** Bulle « Effet IA ici… » : phrase + contexte du clic → recette brute (validée et appliquée par le Mode Studio). */
app.post('/api/studio/effet', async (req, reply) => {
  let d;
  try { d = lireDemandeEffet(req.body); }
  catch (e) { return reply.code(400).send({ error: e instanceof Error ? e.message : 'demande invalide' }); }
  try { return await demanderEffet(d, llmCourant()); }
  catch (e) {
    app.log.warn(`bulle d'effet du Mode Studio : ${e instanceof Error ? e.message : e}`);
    return reply.code(502).send({ error: 'Le compilateur d’effets n’a pas pu répondre. Essaie une recette Nexora ou réessaie.' });
  }
});

app.get('/api/studio/silences/:id', async (req, reply) => {
  const t = priseStudio((req.params as any).id, reply);
  if (!t) return;
  const { stderr } = await executer(config.ffmpegBin, argsSilences(t.output_path!));
  const duree = /Duration:\s*(\d+):(\d+):([\d.]+)/.exec(stderr);
  const dureeS = duree ? Number(duree[1]) * 3600 + Number(duree[2]) * 60 + Number(duree[3]) : undefined;
  return { silences: silencesAvecMarge(lireSilences(stderr, dureeS)), dureeS };
});

app.get('/api/studio/rythme/:id', async (req, reply) => {
  const t = priseStudio((req.params as any).id, reply);
  if (!t) return;
  const { stdout } = await executer(config.ffmpegBin, argsPcm(t.output_path!));
  const pcm = new Float32Array(stdout.buffer, stdout.byteOffset, Math.floor(stdout.byteLength / 4));
  return detecterTemps(pcm, TAUX_RYTHME);
});

const PYTHON_TRANSCRIPTION = process.env.NEXORA_TRANSCRIPTION_PYTHON
  || join(process.env.HOME ?? '', 'nexora-creative-data/engine/transcription-venv/bin/python');
const transcriptions = new Map<number, Promise<unknown>>();
app.get('/api/studio/transcription/:id', async (req, reply) => {
  const t = priseStudio((req.params as any).id, reply);
  if (!t) return;
  const urlGpu = process.env.NEXORA_TRANSCRIPTION_URL;
  if (!urlGpu && !existsSync(PYTHON_TRANSCRIPTION)) return reply.code(503).send({ error: 'La transcription n’est pas installée sur ce serveur.' });
  // Une seule transcription à la fois par prise ; le résultat reste en mémoire le temps du processus.
  let p = transcriptions.get(t.id);
  if (!p) {
    p = (async () => {
      const { mkdtemp, rm } = await import('fs/promises');
      const { tmpdir } = await import('os');
      const dossier = await mkdtemp(join(tmpdir(), 'nexora-transcription-'));
      try {
        if (urlGpu) {
          let tr = null;
          try {
            const { stdout } = await executer(config.ffmpegBin, ['-v', 'error', '-i', t.output_path!, '-vn', '-ac', '1', '-ar', '16000', '-f', 'wav', '-']);
            tr = await transcrireSurGpu(stdout, { url: urlGpu, jeton: process.env.NEXORA_TRANSCRIPTION_TOKEN });
          } catch { /* Échec d'extraction pour le GPU : reprendre le chemin CPU. */ }
          if (tr !== null) return { ...tr, sousTitres: decouperSousTitres(tr), moteur: 'gpu' };
          if (!existsSync(PYTHON_TRANSCRIPTION)) throw Object.assign(new Error('La transcription n’est pas installée sur ce serveur.'), { statusCode: 503 });
        }
        const audio = join(dossier, 'a.f32');
        await executer(config.ffmpegBin, ['-v', 'error', '-y', '-i', t.output_path!, '-vn', '-ac', '1', '-ar', '16000', '-f', 'f32le', audio]);
        const { stdout } = await executer(PYTHON_TRANSCRIPTION, ['-I', join(ROOT, 'server/nexora/transcrire.py'), audio], 900_000);
        const tr = lireTranscription(stdout.toString('utf-8'));
        return { ...tr, sousTitres: decouperSousTitres(tr), moteur: 'cpu' };
      } finally {
        rm(dossier, { recursive: true, force: true }).catch(() => {});
      }
    })();
    transcriptions.set(t.id, p);
    p.catch(() => transcriptions.delete(t.id));
  }
  return p;
});

/** Musique libre pour le Mode Studio : une envie en français → description MiniMax Music 3 écrite par le LLM. */
app.post('/api/studio/musique', async (req, reply) => {
  const b = (req.body ?? {}) as any;
  const envie = typeof b.envie === 'string' ? b.envie.trim().slice(0, 500) : '';
  if (!envie) return reply.code(400).send({ error: 'Décris la musique que tu veux.' });
  if (!eng.moteursPour('music3').length) return reply.code(503).send({ error: 'Aucun moteur GPU ne compose de musique pour l’instant.' });
  const duree = Math.max(10, Math.min(240, Math.round(Number(b.dureeS) || 30)));
  const pseudo = { titre: envie.slice(0, 120), bible: { style: '', personnages: [], lieux: [] }, plans: [{ resume: envie, description: '', duree, camera: '' }], dureeTotale: duree };
  const m = await ecrireMusique(pseudo as any, duree, llmCourant(), envie);
  const [takeId] = await queueTakes({
    kind: 'musique', videoModel: 'music3', description: m.description, paroles: m.paroles, dureeS: duree,
    app: 'nexora-musique', shotName: envie.slice(0, 60), prompt: m.description, userPrompt: envie, promptSource: m.source,
  }, 1);
  return { takeId, source: m.source };
});

/** Les fichiers construits du Mode Studio (mode-studio/dist), servis sous /mode-studio/ avec l'isolation d'origine qu'il exige. */
const distStudio = join(ROOT, '..', 'mode-studio', 'dist');
if (existsSync(distStudio)) {
  app.addHook('onSend', async (req, reply) => {
    if (req.url.startsWith('/mode-studio')) {
      reply.header('Cross-Origin-Embedder-Policy', 'require-corp');
      reply.header('Cross-Origin-Opener-Policy', 'same-origin');
    }
  });
  await app.register(fastifyStatic, { root: distStudio, prefix: '/mode-studio/', decorateReply: false, wildcard: false });
  const pageStudio = readFileSync(join(distStudio, 'index.html'));
  app.get('/mode-studio/*', async (_req, reply) => reply.type('text/html').send(pageStudio));
} else {
  console.log('Mode Studio : mode-studio/dist absent (npm run build dans mode-studio/) ; /mode-studio/ ne sera pas servi.');
}

// In production the sidecar also serves the built UI, so the whole app is one
// port with no Vite in the picture. In dev, Vite serves it and proxies here.
if (config.serveStatic) {
  const dist = join(ROOT, 'dist');
  if (!existsSync(dist)) {
    console.error('No dist/ — run `npm run build` before `npm start`.');
    process.exit(1);
  }
  await app.register(fastifyStatic, { root: dist });
  // SPA fallback: anything not under /api or /live is the app shell.
  app.setNotFoundHandler((req, reply) => {
    if (req.url.startsWith('/api') || req.url.startsWith('/live')) {
      return reply.code(404).send({ error: 'not found' });
    }
    return reply.sendFile('index.html');
  });
}

// Détourage vidéo (SAM 2.1 + ViTMatte sur une machine GPU, recherche/22) : travaux asynchrones, isolation par organisation.
enregistrerDetourage(app, { dossierDonnees: config.dataDir, moteurs: () => eng.moteurs, facturation: (org) => facturationPour(org), nexora: !!configAuth, journal: (m) => app.log.warn(m) });

await app.listen({ port: config.port, host: config.host });
console.log(
  config.serveStatic
    ? `OpenField on http://${config.host}:${config.port}`
    : `OpenField server on http://${config.host}:${config.port} (UI: http://localhost:${config.uiPort} via vite)`
);
if (config.judge.on) console.log(`Judge mode: sign-in required, ${config.judge.cap} renders a day, draft limits on.`);
console.log(`ComfyUI: ${config.comfyUrl} · Comfy API v2: ${config.comfyBaseUrl}`);

// Engine autostart, only when the machine told us how. Never guesses.
if (comfy.canLaunchEngine()) {
  void comfy.launchEngine().then((ok) => {
    if (ok) clearPreflightCache();
    console.log(ok ? 'ComfyUI engine up' : 'ComfyUI engine did not start — use START ENGINE in the UI');
    if (ok) void eng.ensureProxy().then((up) => {
      console.log(up ? 'Comfy API v2 up' : `Comfy API v2 not answering at ${config.comfyBaseUrl}`);
      if (up) void reconcile();
    });
  });
} else {
  void eng.ensureProxy().then((up) => { if (up) void reconcile(); });
}
process.on('SIGINT', () => { eng.stopProxy(); closePhoneSession(); process.exit(0); });
process.on('SIGTERM', () => { eng.stopProxy(); closePhoneSession(); process.exit(0); });
