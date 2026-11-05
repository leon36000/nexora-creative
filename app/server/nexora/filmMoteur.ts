/**
 * Tournage et assemblage des films du Director (voir film.ts pour la planification). Même patron que les coupes de
 * scène d'OpenField (server/scene.ts) : une prise « film » porte l'état dans ses réglages ; chaque plan est une prise
 * ordinaire étiquetée `nexoraFilm` ; quand un plan se termine, `avancerFilm` regarde s'il peut assembler.
 */
import { execFile } from 'node:child_process';
import { existsSync, mkdirSync, readFileSync, writeFileSync } from 'node:fs';
import { join } from 'node:path';
import { config } from '../config.js';
import { takes, type Take } from '../jobs.js';
import { corpsRendu, type DemandeCreer, type MoteurVideo } from './creer.js';
import { avecCompte } from './compte.js';
import { argsCarton, fichierAss, type Carton } from './cartons.js';
import { controlerFichier } from './controle.js';
import { choisirCandidat, jugerCandidats, plancheDataUrl } from './juge.js';
import type { CreditsPrise } from './credits.js';
import { resoudrePersonnages } from './personnagesCast.js';
import { argsAssemblage, argsAvecMusique, intentionDuPlan, type PlanFilm, type Storyboard } from './film.js';
import type { ClientLlm } from './llm.js';
import { reecrireH3 } from './reecritureH3.js';
import { encoderSurGpu } from './encodageGpu.js';
import { dossierFilmUnique, sansEcrasement } from './filmSorties.js';
import { erreurAncrageMaxFilm } from './filmAncrage.js';

export interface DepsFilm {
  queueTakes: (b: any, count: number) => Promise<number[]>;
  broadcast: (msg: unknown) => void;
  /** Téléverse une image d'entrée au moteur (dernière image d'un plan) ; rend son jeton. */
  televerser: (nom: string, data: Buffer, type: string) => Promise<string>;
  /** LLM de l'organisation du film, hors requête (plans enchaînés écrits pendant le tournage). */
  llmPour: (organisationId: string) => ClientLlm | null;
}
let deps: DepsFilm;
export const initFilms = (d: DepsFilm) => { deps = d; };

const reglages = (t: Take) => JSON.parse(t.settings) as Record<string, any>;
const pousser = (id: number) => deps.broadcast({ type: 'take', take: takes.get(id) });

export async function tournerFilm(
  sb: Storyboard,
  opts: {
    format: DemandeCreer['format']; son: boolean; intention: string; projectId?: number | null; moteur: MoteurVideo; reservations?: CreditsPrise[]; qualite?: 'rapide' | 'max';
    /** 2 : deux prises par plan indépendant, le juge visuel garde la meilleure (juge.ts). */
    candidats?: 1 | 2;
    /** Réservations de la seconde prise de chaque plan (même index que les plans). */
    reservationsCandidats?: (CreditsPrise | undefined)[];
    /** Cartons de texte posés en code au début ou à la fin du film. */
    cartons?: Carton[];
  },
  llm: ClientLlm | null,
): Promise<number> {
  const erreurAncrage = erreurAncrageMaxFilm(opts.moteur, sb);
  if (erreurAncrage) throw new Error(erreurAncrage);
  const filmId = takes.create({
    project_id: opts.projectId ?? null,
    kind: 'video',
    shot_name: sb.titre.slice(0, 40),
    settings: {
      app: 'nexora-film', film: true, storyboard: sb, format: opts.format, qualite: opts.qualite ?? 'rapide', son: opts.son, moteur: opts.moteur,
      prompt: opts.intention, userPrompt: sb.titre, seconds: sb.dureeTotale, shotName: sb.titre.slice(0, 40),
      ...(opts.candidats === 2 ? { candidats: 2 } : {}), ...(opts.cartons?.length ? { cartons: opts.cartons } : {}),
    },
  });
  pousser(filmId);
  try {
    // Les prompts des plans indépendants s'écrivent en parallèle, puis leurs rendus partent dans l'ordre. Un plan
    // « suite » attend la fin du précédent : il partira de sa dernière image (voir lancerSuite).
    // Personnages @ : un plan qui cite @nom part en Ref2VA (moteur cinéma) avec les images du personnage.
    const persos = await Promise.all(sb.plans.map((p, i) => (p.suite || p.take || opts.moteur !== 'h3-max' ? null : resoudrePersonnages(intentionDuPlan(sb, i)))));
    const prompts = await Promise.all(
      sb.plans.map((p, i) => (p.suite || p.take ? null : reecrireH3({ intention: persos[i]?.sujets.length ? persos[i]!.texteClair : intentionDuPlan(sb, i), mode: persos[i]?.sujets.length ? 'ref2va' : 't2va', ...(persos[i]?.sujets.length ? { references: { sujets: persos[i]!.sujets } } : {}), dureeS: dureePlan(p), moteur: opts.moteur, format: opts.format, ...dialoguesDe(p) }, llm))),
    );
    for (let i = 0; i < sb.plans.length; i++) {
      const p = sb.plans[i];
      const ecrit = prompts[i];
      if (p.take) continue; // version refaite d'un film : ce plan garde sa prise
      if (!ecrit) {
        majPlan(filmId, i, { attente: 'image_precedente', reservation: opts.reservations?.[i] });
        continue;
      }
      const corps = {
        ...corpsRendu({ intention: p.resume, format: opts.format, duree: p.duree, son: opts.son, qualite: opts.qualite }, ecrit.prompt, opts.moteur),
        ...(persos[i]?.sujets.length ? { refImages: persos[i]!.jetons, personnages: persos[i]!.noms } : {}),
        app: 'nexora-film', userPrompt: p.resume, nexoraFilm: filmId, nexoraPlan: i, promptSource: ecrit.source,
        shotName: `${sb.titre.slice(0, 28)}_plan${i + 1}`, projectId: opts.projectId ?? undefined,
      };
      const n = opts.candidats === 2 ? 2 : 1;
      const ids = await deps.queueTakes(corps, n);
      if (opts.reservations?.[i]) takes.patchSettings(ids[0], { nexoraCredits: opts.reservations[i] });
      if (ids[1] && opts.reservationsCandidats?.[i]) takes.patchSettings(ids[1], { nexoraCredits: opts.reservationsCandidats[i] });
      majPlan(filmId, i, { take: ids[0], corps, ...(ids.length > 1 ? { candidats: ids } : {}) });
    }
  } catch (e) {
    takes.fail(filmId, `Les plans n'ont pas pu partir au tournage : ${e instanceof Error ? e.message : e}`);
    pousser(filmId);
    throw e;
  }
  return filmId;
}

/** Réplique d'un plan pour le réécrivain H3 (voix française synchronisée). */
const dialoguesDe = (p: PlanFilm) => (p.replique ? { dialogues: [{ texte: p.replique, langue: 'French' }] } : {});

/** Durée effective d'un plan sur la grille de H3 (5 s → 124 images, 10 s → 243). */
const dureePlan = (p: PlanFilm) => (p.duree === 10 ? 243 : 124) / 24;

/**
 * Plan enchaîné : la dernière image du plan précédent devient sa première image (H3 en image vers vidéo, I2VA), ce qui
 * garde sujets, lieu et lumière identiques d'un plan à l'autre. Tourne hors requête, dans l'organisation du film.
 */
async function lancerSuite(film: Take, i: number, precedent: string) {
  const s = reglages(film);
  const sb = s.storyboard as Storyboard;
  const moteur = s.moteur ?? 'h3-fast';
  const erreurAncrage = erreurAncrageMaxFilm(moteur, sb);
  if (erreurAncrage) throw new Error(erreurAncrage);
  const p = sb.plans[i] as PlanFilm & { reservation?: CreditsPrise };
  const dossier = join(config.outputDir, 'films', 'images');
  mkdirSync(dossier, { recursive: true });
  const image = join(dossier, `film_${film.id}_plan${i}_depart.png`);
  await new Promise<void>((ok, ko) =>
    execFile(config.ffmpegBin, ['-y', '-sseof', '-0.25', '-i', precedent, '-frames:v', '1', '-update', '1', image], (err, _o, stderr) =>
      err ? ko(new Error(`dernière image du plan ${i} : ${String(stderr).split('\n').slice(-2).join(' ')}`)) : ok()),
  );
  const jeton = await deps.televerser(`nexora_film_${film.id}_plan${i}.png`, readFileSync(image), 'image/png');
  const org = takes.organisationDe(film.id) ?? 'local';
  // Raccord : le plan va aussi vers la première image du plan suivant (H3 première + dernière image, FL2VA).
  let fin: string | undefined;
  const suivant = (p as PlanFilm & { raccord?: boolean }).raccord ? sb.plans[i + 1]?.take : undefined;
  const fichierSuivant = suivant ? takes.get(suivant)?.output_path : undefined;
  if (fichierSuivant && existsSync(fichierSuivant)) {
    const imageFin = join(dossier, `film_${film.id}_plan${i}_arrivee.png`);
    await new Promise<void>((ok, ko) =>
      execFile(config.ffmpegBin, ['-y', '-i', fichierSuivant, '-frames:v', '1', '-update', '1', imageFin], (err, _o, stderr) =>
        err ? ko(new Error(`première image du plan ${i + 2} : ${String(stderr).split('\n').slice(-2).join(' ')}`)) : ok()),
    );
    fin = await deps.televerser(`nexora_film_${film.id}_plan${i}_fin.png`, readFileSync(imageFin), 'image/png');
  }
  const ecrit = await reecrireH3({
    intention: fin
      ? `${intentionDuPlan(sb, i)}\nThe video starts exactly from the provided first frame and ends exactly on the provided last frame: one continuous move that links them.`
      : `${intentionDuPlan(sb, i)}\nThe video starts exactly from the provided first frame, which is the last frame of the previous shot: continue the same action seamlessly from it.`,
    mode: fin ? 'fl2va' : 'i2va',
    dureeS: dureePlan(p),
    moteur,
    format: s.format,
    ...dialoguesDe(p),
  }, deps.llmPour(org));
  const corps = {
    ...corpsRendu({ intention: p.resume, format: s.format, duree: p.duree, son: !!s.son, qualite: s.qualite, image: jeton }, ecrit.prompt, moteur),
    startImage: jeton,
    ...(fin ? { endImage: fin } : {}),
    app: 'nexora-film', userPrompt: p.resume, nexoraFilm: film.id, nexoraPlan: i, promptSource: ecrit.source,
    shotName: `${sb.titre.slice(0, 28)}_plan${i + 1}`, projectId: film.project_id ?? undefined,
  };
  const [id] = await avecCompte({ organisationId: org, utilisateurId: 'nexora-director', territoire: null }, () => deps.queueTakes(corps, 1));
  if (p.reservation) takes.patchSettings(id, { nexoraCredits: p.reservation });
  majPlan(film.id, i, { take: id, corps, attente: undefined });
}

function majPlan(filmId: number, i: number, patch: Record<string, unknown>) {
  const s = reglages(takes.get(filmId)!);
  s.storyboard.plans[i] = { ...s.storyboard.plans[i], ...patch };
  takes.setSettings(filmId, s);
  pousser(filmId);
}

const verrous = new Map<number, Promise<void>>();
/** Fait avancer un film ; sérialisé par film car plusieurs plans peuvent finir en même temps. */
export function avancerFilm(filmId: number): Promise<void> {
  const avant = verrous.get(filmId) ?? Promise.resolve();
  const suite = avant.then(() => etape(filmId)).catch((e) => {
    const t = takes.get(filmId);
    if (t && t.status === 'queued') { takes.fail(filmId, e instanceof Error ? e.message : 'assemblage impossible'); pousser(filmId); }
  });
  verrous.set(filmId, suite);
  return suite;
}

async function etape(filmId: number) {
  const film = takes.get(filmId);
  if (!film || film.status !== 'queued') return;
  const s = reglages(film);
  const sb = s.storyboard as Storyboard;
  const fichiers: string[] = [];
  for (const [i, p] of sb.plans.entries()) {
    if (!p.take) {
      // Un plan enchaîné part quand le précédent est rendu et contrôlé (les plans sont parcourus dans l'ordre).
      if (p.suite && i > 0 && fichiers.length === i) await lancerSuite(film, i, fichiers[i - 1]);
      return;
    }
    const t = takes.get(p.take);
    if (!t) throw new Error(`Plan ${i + 1} : sa prise a été supprimée`);
    // Deux candidats : on attend les deux, le contrôle qualité puis le juge visuel choisissent la prise du plan.
    const cands = (p as any).candidats as number[] | undefined;
    if (cands?.length === 2 && !(p as any).jugement) {
      const prises = cands.map((id) => takes.get(id));
      if (prises.some((x) => !x || x.status === 'queued' || x.status === 'rendering')) return;
      const choix = await departager(filmId, i, sb, prises as Take[]);
      majPlan(filmId, i, { take: choix.take, jugement: choix });
      return avancerFilmPlusTard(filmId);
    }
    // Panne du moteur pendant un plan : on le relance (même prompt, même graine) jusqu'à 2 fois avant d'abandonner le film.
    const relances = Number((p as any).relances ?? 0);
    if (t.status === 'failed' && (p as any).corps && relances < 2) {
      const org = takes.organisationDe(filmId) ?? 'local';
      let id: number;
      try {
        [id] = await avecCompte({ organisationId: org, utilisateurId: 'nexora-director', territoire: null }, () => deps.queueTakes({ ...(p as any).corps }, 1));
      } catch (e) {
        // Moteur encore à terre : le plan attend ; la réconciliation (toutes les 20 s) refait cette étape.
        majPlan(filmId, i, { attenteMoteur: e instanceof Error ? e.message : 'moteur indisponible' });
        return;
      }
      const credits = JSON.parse(t.settings).nexoraCredits;
      if (credits) takes.patchSettings(id, { nexoraCredits: credits }), takes.patchSettings(t.id, { nexoraCredits: { ...credits, etat: 'transferee' } });
      majPlan(filmId, i, { take: id, relances: relances + 1, panne: t.error ?? 'échec', attenteMoteur: undefined });
      return;
    }
    if (t.status === 'failed' || t.status === 'stopped') throw new Error(`Plan ${i + 1} : ${t.status}${t.error ? ` (${t.error})` : ''}`);
    if (t.status !== 'done' || !t.output_path || !existsSync(t.output_path)) return;
    const plan = p as PlanFilm & { corps?: Record<string, any>; controle?: { ok: boolean; defauts: string[]; duree?: number }; reprises?: number };
    if (!plan.controle) {
      const images = Number(plan.corps?.lengthFrames ?? plan.corps?.frames);
      const c = await controlerFichier(config.ffmpegBin, t.output_path, {
        dureeAttendue: Number.isFinite(images) && images > 0 ? images / 24 : plan.duree,
        sonAttendu: !!plan.corps?.withAudio,
      });
      plan.controle = { ok: c.ok, defauts: c.defauts, duree: c.duree };
      majPlan(filmId, i, { controle: plan.controle });
      // Correction automatique, budget d'une reprise par plan : même prompt, autre graine.
      if (!c.ok && (plan.reprises ?? 0) < 1 && plan.corps) {
        // Hors requête (fin de rendu côté moteur) : la reprise doit naître dans l'organisation du film.
        const org = takes.organisationDe(filmId) ?? 'local';
        const [id] = await avecCompte({ organisationId: org, utilisateurId: 'nexora-director', territoire: null }, () =>
          deps.queueTakes({ ...plan.corps!, seed: Math.floor(Math.random() * 1e9) }, 1));
        majPlan(filmId, i, { take: id, reprises: (plan.reprises ?? 0) + 1, controle: undefined, controleRefuse: { take: t.id, defauts: c.defauts } });
        return;
      }
    }
    fichiers.push(t.output_path);
  }
  // Bande originale composée en même temps que les plans (Producteur) : on l'attend avant d'assembler.
  if (typeof s.musiquePrise === 'number' && typeof s.musique !== 'string') {
    const m = takes.get(s.musiquePrise);
    if (m && (m.status === 'queued' || m.status === 'rendering')) return;
    if (m?.status === 'done' && m.output_path && existsSync(m.output_path)) s.musique = m.output_path;
    takes.patchSettings(filmId, { musique: s.musique ?? null });
  }
  const dossier = join(config.outputDir, 'films');
  mkdirSync(dossier, { recursive: true });
  const dossierRendu = dossierFilmUnique(dossier, filmId);
  const cartons = (Array.isArray(s.cartons) ? s.cartons : []) as Carton[];
  const durees = sb.plans.map((p) => Number((p as any).controle?.duree) || dureePlan(p));
  if (cartons.length) {
    const m = await new Promise<string>((ok) => execFile(config.ffprobeBin, ['-v', 'error', '-select_streams', 'v:0', '-show_entries', 'stream=width,height', '-of', 'csv=p=0', fichiers[0]], (e, o) => ok(e ? '' : String(o).trim())));
    const [w, h] = m.split(',').map(Number);
    if (w > 0 && h > 0) {
      const debut: string[] = [], fin: string[] = [];
      for (const [k, c] of cartons.entries()) {
        const dureeS = c.position === 'debut' ? 2 : 2.5;
        const base = join(dossierRendu, `carton${k}`);
        mkdirSync(join(config.outputDir, 'films'), { recursive: true });
        writeFileSync(`${base}.ass`, fichierAss(c.texte, { w, h, dureeS }), { flag: 'wx' });
        await new Promise<void>((ok, ko) => execFile(config.ffmpegBin, sansEcrasement(argsCarton(`${base}.ass`, `${base}.mp4`, { w, h, dureeS, son: !!s.son, dossierPolices: dossierPolices() })), { maxBuffer: 1 << 24 }, (err, _o, stderr) =>
          err ? ko(new Error(`carton : ${String(stderr).split('\n').slice(-2).join(' ')}`)) : ok()));
        (c.position === 'debut' ? debut : fin).push(`${base}.mp4`);
        (c.position === 'debut' ? durees.unshift.bind(durees) : durees.push.bind(durees))(dureeS);
      }
      fichiers.unshift(...debut);
      fichiers.push(...fin);
    }
  }
  takes.patchSettings(filmId, { assemblage: 'en_cours' });
  pousser(filmId);
  const sortie = join(dossierRendu, 'film.mp4');
  const t0 = Date.now();
  const assemblage = {
    transition: s.transition === 'fondu' ? 'fondu' as const : 'coupe' as const,
    durees, fondu: 0.5, son: !!s.son,
  };
  const taille = Array.isArray(s.taille) && s.taille.length === 2
    ? [Number(s.taille[0]), Number(s.taille[1])] as [number, number] : undefined;
  const gpu = await encoderSurGpu(fichiers, sortie, { codec: 'h264', profil: 'livraison', taille, assemblage });
  if (!gpu) await new Promise<void>((ok, ko) =>
    execFile(config.ffmpegBin, sansEcrasement(argsAssemblage(fichiers, sortie, !!s.son, { ...assemblage, taille })), { maxBuffer: 1 << 24 }, (err, _o, stderr) =>
      err ? ko(new Error(`ffmpeg : ${String(stderr).split('\n').slice(-3).join(' ')}`)) : ok()),
  );
  let final = sortie;
  // Bande originale MiniMax-Music3 choisie pour cette version du film : mixée sous les sons des plans.
  if (typeof s.musique === 'string' && existsSync(s.musique)) {
    final = sortie.replace(/\.mp4$/, '_musique.mp4');
    const duree = durees.reduce((n, d) => n + d, 0) - (s.transition === 'fondu' ? 0.5 * (fichiers.length - 1) : 0);
    await new Promise<void>((ok, ko) =>
      execFile(config.ffmpegBin, sansEcrasement(argsAvecMusique(sortie, s.musique, final, { dureeS: duree, sonDuFilm: !!s.son })), { maxBuffer: 1 << 24 }, (err, _o, stderr) =>
        err ? ko(new Error(`ffmpeg (musique) : ${String(stderr).split('\n').slice(-3).join(' ')}`)) : ok()),
    );
  }
  takes.finish(filmId, final, (Date.now() - t0) / 1000);
  const dureeReelle = durees.reduce((n, d) => n + d, 0) - (s.transition === 'fondu' ? 0.5 * (fichiers.length - 1) : 0);
  takes.patchSettings(filmId, { assemblage: 'fait', planTakes: sb.plans.map((p) => p.take), seconds: Math.round(dureeReelle * 10) / 10 });
  pousser(filmId);
}

/** Films en attente de plans, pour la reprise après redémarrage. */
export function filmsEnAttente(): number[] {
  return takes.active().filter((t) => reglages(t).film === true).map((t) => t.id);
}

/** Dossier des polices des cartons (DejaVu, présent sur le poste et sur la VM ; réglable). */
function dossierPolices(): string | undefined {
  const d = process.env.NEXORA_POLICES_CARTONS?.trim() || '/usr/share/fonts/truetype/dejavu';
  return existsSync(d) ? d : undefined;
}

/** Une étape de plus tout de suite (le plan vient de recevoir sa prise gagnante). */
function avancerFilmPlusTard(filmId: number) {
  setTimeout(() => void avancerFilm(filmId), 0);
}

/** Contrôle qualité des deux prises puis juge visuel ; renvoie la prise gardée et pourquoi. */
async function departager(filmId: number, i: number, sb: Storyboard, prises: Take[]) {
  const plan = sb.plans[i] as PlanFilm & { corps?: Record<string, any> };
  const images = Number(plan.corps?.lengthFrames);
  const dureeAttendue = Number.isFinite(images) && images > 0 ? images / 24 : plan.duree;
  const evals = await Promise.all(prises.map(async (t) => {
    if (t.status !== 'done' || !t.output_path || !existsSync(t.output_path)) return { take: t.id, controleOk: false };
    const c = await controlerFichier(config.ffmpegBin, t.output_path, { dureeAttendue, sonAttendu: !!plan.corps?.withAudio }).catch(() => null);
    return { take: t.id, controleOk: !!c?.ok };
  }));
  let verdict = null;
  if (evals.every((e) => e.controleOk)) {
    const org = takes.organisationDe(filmId) ?? 'local';
    const dossier = join(config.outputDir, 'films', 'images');
    mkdirSync(dossier, { recursive: true });
    try {
      const planches = await Promise.all(prises.map((t, k) => plancheDataUrl(config.ffmpegBin, t.output_path!, dureeAttendue, join(dossier, `film_${filmId}_plan${i}_cand${k}.jpg`))));
      verdict = await jugerCandidats(deps.llmPour(org), intentionDuPlan(sb, i), planches);
    } catch { /* planche impossible : le code choisit seul */ }
  }
  return { ...choisirCandidat(evals, verdict), notes: verdict?.notes, candidats: prises.map((t) => t.id) };
}
