/**
 * Parcours simple « Créer » : une intention en français → prompt H3 écrit par le LLM → rendu MiniMax H3.
 * Ce module ne fait que lire la demande et préparer le corps de rendu ; la route de server/index.ts enchaîne.
 * Décision du fondateur (31/10/2026) : MiniMax H3 seul. « Rapide » = FastH3 8 étapes ; « max » = le point de contrôle
 * H3 complet du moteur cinéma (RTX 5090), à pleine résolution et pleines étapes.
 */
import { type Besoin, planifierMoteurs } from './registre.js';
import { checkpointMaxFL2VAExplicite } from '../graphs/h3.js';
import { lireLangueClient, type LangueClient } from '../../shared/creationLanguage.js';
import type { EntreeReecriture } from './reecritureH3.js';

export type FormatCreer = '16:9' | '9:16' | '1:1';
export type DureeCreer = 5 | 10 | 15;

export interface DemandeCreer {
  intention: string;
  format: FormatCreer;
  duree: DureeCreer;
  son: boolean;
  /** Profil : « rapide » (832×480, ≈ 85 s pour 5 s sur GB10) ou « max » (résolution native de H3, 1344×768). */
  qualite?: 'rapide' | 'max';
  /** Photo de départ (jeton d'entrée du moteur, `asset:<uuid>`) : la vidéo part de cette image. */
  image?: string;
  /** Réplique à faire dire (français), recopiée mot pour mot dans le prompt H3 : la voix est synchronisée à l'image. */
  replique?: string;
  /** Mouvement de caméra choisi parmi les vignettes (texte anglais du catalogue), ajouté à l'intention. */
  camera?: string;
  /** Language for the user-facing Director explanation; omitted keeps the historical LLM inference. */
  langueClient?: LangueClient;
  /** Spoken language of the optional line; independent from the UI/Director explanation language. */
  langueReplique?: LangueClient;
}

export type ErreurDemandeCreer = 'descriptionVide' | 'descriptionLongue';
export function messageErreurDemandeCreer(langue: LangueClient | undefined, erreur: ErreurDemandeCreer): string {
  const messages = {
    fr: {
      descriptionVide: 'Décris la vidéo que tu veux en une phrase ou plus.',
      descriptionLongue: 'Description trop longue (4 000 caractères au plus).',
    },
    en: {
      descriptionVide: 'Describe the video you want in one sentence or more.',
      descriptionLongue: 'Description is too long (4,000 characters maximum).',
    },
  };
  return messages[langue ?? 'fr'][erreur];
}

export type ErreurParcoursCreer = 'moteurIndisponible' | 'assistantRedaction' | 'creditsInsuffisants';
export function messageErreurParcoursCreer(langue: LangueClient | undefined, erreur: ErreurParcoursCreer): string {
  const messages = {
    fr: {
      moteurIndisponible: 'Aucun moteur ne peut faire cette vidéo pour ton compte.',
      assistantRedaction: 'L’assistant d’écriture n’a pas pu préparer la vidéo. Réessaie.',
      creditsInsuffisants: 'Il n’y a pas assez de crédits pour lancer cette vidéo.',
    },
    en: {
      moteurIndisponible: 'No video engine is available for this account and request.',
      assistantRedaction: 'The writing assistant could not prepare this video. Please try again.',
      creditsInsuffisants: 'There are not enough credits to start this video.',
    },
  };
  return messages[langue ?? 'fr'][erreur];
}

/** Point de contrôle FastH3 V2 distillé et quantifié NVFP4 (server/graphs/h3.ts, H3_DISTILLED_CHECKPOINTS). */
export const CHECKPOINT_FASTH3 = 'fastvideo_fasth3_8step_v2_pruned_nvfp4.safetensors';

/** Point de contrôle « cinéma » retenu le 02/11/2026 : 10Eros-Max × Singularity V2, turbo 8 étapes (famille ref2va). */
export const CHECKPOINT_H3_MAX = '10Eros_Max_h3_8stepTURBO_beta7_SingularityV2_ref2va_int8HQ.safetensors';

/**
 * Recette « h3-max » : point de contrôle H3 et nombre d'étapes, réglables par la configuration (ronde de comparaison
 * du 02/11/2026 : marketing/creative/video-v3/JOURNAL-V3.md). Un point de contrôle ref2va passe par le nœud de
 * référence, même sans image ; une photo de départ exige un checkpoint FL2VA pour garder son ancrage temporel.
 */
export function reglagesH3Max(env: NodeJS.ProcessEnv = process.env) {
  const checkpoint = env.NEXORA_H3_MAX_CHECKPOINT?.trim() || CHECKPOINT_H3_MAX;
  const etapes = Number(env.NEXORA_H3_MAX_ETAPES);
  return { checkpoint, etapes: Number.isInteger(etapes) && etapes >= 6 && etapes <= 60 ? etapes : 8, ref: /ref2va/i.test(checkpoint) };
}

const TAILLES: Record<'rapide' | 'max', Record<FormatCreer, { width: number; height: number }>> = {
  rapide: { '16:9': { width: 832, height: 480 }, '9:16': { width: 480, height: 832 }, '1:1': { width: 640, height: 640 } },
  max: { '16:9': { width: 1344, height: 768 }, '9:16': { width: 768, height: 1344 }, '1:1': { width: 1024, height: 1024 } },
};
const taille = (d: DemandeCreer) => TAILLES[d.qualite ?? 'rapide'][d.format];

/** Plus petite longueur de la grille H3 (124 + 17n) qui couvre la durée demandée. */
function imagesPour(dureeS: number): number {
  const n = Math.max(0, Math.ceil((dureeS * 24 - 124) / 17));
  return Math.min(362, 124 + 17 * n);
}

export function lireDemandeCreer(b: unknown): DemandeCreer {
  const o = (b ?? {}) as Record<string, unknown>;
  const langueClient = lireLangueClient(o.langueClient);
  const langueReplique = lireLangueClient(o.langueReplique);
  const intention = typeof o.intention === 'string' ? o.intention.trim() : '';
  if (!intention) throw new Error(messageErreurDemandeCreer(langueClient, 'descriptionVide'));
  if (intention.length > 4000) throw new Error(messageErreurDemandeCreer(langueClient, 'descriptionLongue'));
  const format: FormatCreer = o.format === '9:16' || o.format === '1:1' ? o.format : '16:9';
  const duree: DureeCreer = o.duree === 10 || o.duree === 15 ? o.duree : 5;
  const image = typeof o.image === 'string' && /^asset:[0-9a-f-]{36}$/i.test(o.image) ? o.image : undefined;
  const replique = typeof o.replique === 'string' ? o.replique.trim().slice(0, 300) : '';
  const camera = typeof o.camera === 'string' ? o.camera.trim().slice(0, 300) : '';
  return { intention, format, duree, son: o.son !== false, qualite: o.qualite === 'max' ? 'max' : 'rapide', ...(image ? { image } : {}), ...(replique ? { replique } : {}), ...(camera ? { camera } : {}), ...(langueClient ? { langueClient } : {}), ...(langueReplique ? { langueReplique } : {}) };
}

export function corpsRenduH3(d: DemandeCreer, prompt: string) {
  return {
    kind: 'video' as const,
    videoModel: 'h3-fast' as const,
    prompt,
    ...taille(d),
    lengthFrames: imagesPour(d.duree),
    steps: 8,
    checkpoint: CHECKPOINT_FASTH3,
    withAudio: d.son,
    shotName: d.intention.slice(0, 60),
    ...(d.image ? { startImage: d.image } : {}),
  };
}

/** Durée effective (s) du rendu, pour la ligne d'instruction et les horodatages du prompt. */
export function dureeEffective(d: DemandeCreer): number {
  return imagesPour(d.duree) / 24;
}

export type MoteurVideo = 'h3-fast' | 'h3-max';

/**
 * Moteur vidéo du compte : MiniMax H3, là où sa licence le permet (échec fermé : un territoire inconnu ou exclu ne
 * reçoit rien). « max » prend le moteur cinéma s'il est en ligne dans le parc, sinon FastH3 à pleine résolution.
 */
export function choisirMoteur(
  territoire: string | null,
  besoin: Besoin = { tache: 't2v', dureeS: 5, son: true },
  qualite: 'rapide' | 'max' = 'rapide',
  recettes?: Set<string>,
): MoteurVideo | null {
  const retenus = planifierMoteurs(besoin, { territoire, recettes }).retenus.map((m) => m.recette as MoteurVideo);
  if (qualite === 'max' && retenus.includes('h3-max')) return 'h3-max';
  return retenus.includes('h3-fast') ? 'h3-fast' : (retenus[0] ?? null);
}

/** Besoin d'une demande « Créer », pour le registre de capacités. */
export function besoinDe(d: DemandeCreer): Besoin {
  return { tache: d.image ? 'i2v' : 't2v', dureeS: imagesPour(d.duree) / 24, son: d.son };
}

/** Reject a max route whose configured reference model would silently become FastH3 with a first frame. */
export function ancrageMaxIndisponible(moteur: MoteurVideo, ancre: boolean, env: NodeJS.ProcessEnv = process.env): boolean {
  const reglage = reglagesH3Max(env);
  return moteur === 'h3-max' && ancre && (reglage.ref || !checkpointMaxFL2VAExplicite(reglage.checkpoint));
}

export function messageAncrageMax(langue: LangueClient | undefined): string {
  return langue === 'en'
    ? 'Maximum quality is unavailable with an anchored image on this engine. Try Fast quality if available, or remove the image.'
    : 'La qualité maximale est indisponible avec une image ancrée sur ce moteur. Essaie la qualité Rapide si disponible ou retire l’image.';
}

/** Corps de rendu pour le moteur choisi. */
export function corpsRendu(d: DemandeCreer, promptH3: string, moteur: MoteurVideo) {
  const base = corpsRenduH3(d, promptH3);
  if (moteur === 'h3-fast') return base;
  const m = reglagesH3Max();
  // Une photo exige FL2VA : repli FastH3 plein format si le checkpoint cinéma est Ref2VA.
  // Le nom de route h3-max reste le même ; un checkpoint FL2VA configuré est conservé avec ses étapes.
  if (d.image && m.ref) return { ...base, ...TAILLES.max[d.format], videoModel: 'h3-max' as const };
  // Le moteur cinéma est toujours à pleine résolution.
  return { ...base, ...TAILLES.max[d.format], videoModel: 'h3-max' as const, checkpoint: m.checkpoint, steps: m.etapes, ...(m.ref ? { refMode: true } : {}) };
}

/** Intention envoyée au réécrivain H3 : la phrase de la personne, puis le mouvement de caméra choisi. */
export function intentionAvecCamera(d: DemandeCreer): string {
  return d.camera ? `${d.intention}\nCamera movement: ${d.camera}` : d.intention;
}

/** Build the Director input at the creation route boundary, omitting locale when legacy detection is requested. */
export function entreeRealisateurCreation(d: DemandeCreer, options: {
  moteur: MoteurVideo;
  intention?: string;
  references?: EntreeReecriture['references'];
}): EntreeReecriture {
  const intention = options.intention ?? d.intention;
  return {
    intention: intentionAvecCamera({ ...d, intention }),
    mode: d.image ? 'i2va' : options.references?.sujets.length ? 'ref2va' : 't2va',
    ...(options.references?.sujets.length ? { references: options.references } : {}),
    dureeS: dureeEffective(d),
    moteur: options.moteur,
    format: d.format,
    ...(d.langueClient ? { langueClient: d.langueClient } : {}),
    ...(d.replique ? { dialogues: [{ texte: d.replique, langue: d.langueReplique === 'en' ? 'English' : 'French' }] } : {}),
  };
}
