/**
 * Mode « 3D » de Nexora Creative (image → 3D et texte → 3D), sur TRELLIS.2 : recettes, temps GPU mesurés, prompt de
 * référence, juge sur 4 vues et machine à états du texte → 3D. Tout ce qui est ici est pur (testé sans moteur) ; le
 * câblage est dans server/index.ts. Rapport : recherche/18-creative-3d-facon-meshy.md ; mesures : docs/RESSOURCES.md.
 */
import { execFile } from 'node:child_process';
import { readFile, rm } from 'node:fs/promises';
import { avecCompetences } from './competences.js';
import { type ClientLlm, type MessageLlm, lireJson } from './llm.js';

export type QualiteObjet = 'draft' | 'quality';

/**
 * Recettes déclarées par un moteur GPU (NEXORA_MOTEUR_RECETTES ou NEXORA_MOTEURS_GPU). Le moteur principal déclare « * » par
 * défaut ; un parc à listes explicites doit y ajouter ces deux noms sur la GB10 : seul moteur qui porte TRELLIS.2.
 * ComfyUI doit y rester figé à la version 0.43.2 (noms de nœuds relevés le 03/11/2026).
 */
export const RECETTES_OBJET = { draft: 'objet-apercu', quality: 'objet-qualite', multi: 'objet-multivue' } as const;
/** Multi-images (Pixal3D, poids sur la VM GPU de pc5) : une recette à part, jamais sur la GB10 qui n'a pas ces poids. */
export const recetteMultivue = () => RECETTES_OBJET.multi;
export const recetteObjet = (q: QualiteObjet) => RECETTES_OBJET[q === 'quality' ? 'quality' : 'draft'];

/**
 * Secondes de calcul mesurées sur la GB10 (DGX Spark, ComfyUI 0.43.2, TRELLIS.2 int8, chaise en chêne, 03/11/2026,
 * sans tournette) : aperçu 38 s à chaud (46 s à froid), qualité 162 s ; image de référence Qwen-Image-2.1 : 24 s.
 */
export const MESURES_OBJET_GB10 = { draft: 38, quality: 162, reference: 24, tournetteJuge: 12 } as const;

export function secondesObjet(q: QualiteObjet): number {
  return MESURES_OBJET_GB10[q === 'quality' ? 'quality' : 'draft'];
}
/** Texte → 3D : image de référence, objet et tournette courte qui sert au juge. */
export function secondesTexteVers3D(q: QualiteObjet): number {
  return MESURES_OBJET_GB10.reference + secondesObjet(q) + MESURES_OBJET_GB10.tournetteJuge;
}

/** Tournette de contrôle du texte → 3D : 8 images, le juge voit les images 0, 2, 4 et 6 (quatre côtés de l'objet). */
export const TOURNETTE_JUGE = { frames: 8, images: [0, 2, 4, 6] } as const;

/** Prompt d'image pour un objet seul, entier et net sur fond uni : ce que TRELLIS.2 reconstruit le mieux. */
export function promptReferenceObjet(intention: string): string {
  const sujet = intention.trim().replace(/\s+/g, ' ').slice(0, 600);
  return `${sujet}. Product photo of a single object, centered, the whole object visible with some margin, seen from a three-quarter front angle, plain white seamless background, soft even studio light, sharp detail, natural materials, no text, no logo, no watermark, no people, no hands, no other objects.`;
}

export interface UsageJuge { modele: string; entree: number; sortie: number }
export interface VerdictVues { note: number; defauts: string[]; raison: string; usage?: UsageJuge }

/** Quatre images régulièrement espacées d'une tournette de `n` images (le tour complet, vu de quatre côtés). */
export function indicesQuatreVues(n: number): number[] {
  if (!Number.isFinite(n) || n < 4) return [0, 0, 0, 0].map((_, i) => Math.min(i, Math.max(0, Math.floor(n) - 1)));
  return [0, 1, 2, 3].map((i) => Math.floor((i * n) / 4));
}

/** Réponse du juge (JSON) : note de 0 à 10, défauts relevés, une phrase. */
export function lireVerdictVues(texte: string): VerdictVues | null {
  try {
    const o = lireJson<Record<string, unknown>>(texte);
    if (o.note === undefined || o.note === null || !Number.isFinite(Number(o.note))) return null;
    return {
      note: Math.max(0, Math.min(10, Math.round(Number(o.note)))),
      defauts: Array.isArray(o.defauts) ? o.defauts.map((d) => String(d).slice(0, 120)).slice(0, 6) : [],
      raison: String(o.raison ?? '').trim().slice(0, 200),
    };
  } catch {
    return null;
  }
}

/** Note en dessous de laquelle on refait un essai (une seule relance). */
export const NOTE_MINIMALE = 6;

export function decisionApresJuge(essai: number, v: VerdictVues | null): 'garder' | 'relancer' {
  if (!v || essai >= 2) return 'garder';
  return v.note < NOTE_MINIMALE ? 'relancer' : 'garder';
}

/** GIF animé de la tournette : palette optimisée, 384 px de large, 16 images par seconde. */
export function argsGif(video: string, sortie: string): string[] {
  return ['-y', '-v', 'error', '-i', video, '-vf', 'fps=16,scale=384:-1:flags=lanczos,split[a][b];[a]palettegen=max_colors=128[p];[b][p]paletteuse=dither=bayer:bayer_scale=4', '-loop', '0', sortie];
}

/** Arguments ffmpeg : les images voulues de la tournette posées en grille 2×2 (JPEG). */
export function argsPlancheVues(video: string, sortie: string, images: readonly number[]): string[] {
  const sel = images.map((n) => `eq(n,${n})`).join('+');
  return ['-y', '-v', 'error', '-i', video, '-vf', `select='${sel}',scale=448:-2,tile=2x2`, '-frames:v', '1', '-q:v', '5', sortie];
}

// ---- texte → 3D : machine à états ----

export interface EtatTexte3D {
  phase: 'image' | 'objet' | 'jugement' | 'fini' | 'echec';
  /** Numéro de l'essai en cours (1, puis 2 après la relance). */
  essai: number;
  /** Prises « objet » lancées, dans l'ordre. */
  tentatives: number[];
  /** Notes du juge par prise. */
  notes: { take: number; note: number }[];
}
export type StatutPrise3D = 'queued' | 'running' | 'done' | 'failed' | 'stopped';
export type EtapeTexte3D =
  | { action: 'attendre' }
  | { action: 'lancer-objet'; essai: number }
  | { action: 'juger' }
  | { action: 'finir'; retenu: number }
  | { action: 'echec'; motif: string };

/** Décide la suite du texte → 3D d'après l'état gardé et les statuts lus sur les prises. */
export function prochaineEtapeTexte3D(e: EtatTexte3D, vu: { image: StatutPrise3D; objet?: StatutPrise3D }): EtapeTexte3D {
  if (e.phase === 'fini' || e.phase === 'echec') return { action: 'attendre' };
  if (e.phase === 'image') {
    if (vu.image === 'failed' || vu.image === 'stopped') return { action: 'echec', motif: 'L’image de référence n’a pas abouti.' };
    return vu.image === 'done' ? { action: 'lancer-objet', essai: 1 } : { action: 'attendre' };
  }
  if (e.phase === 'objet') {
    if (vu.objet === 'failed' || vu.objet === 'stopped') return { action: 'echec', motif: 'Le modèle 3D n’a pas abouti.' };
    return vu.objet === 'done' ? { action: 'juger' } : { action: 'attendre' };
  }
  // jugement rendu : relancer une fois ou finir avec la meilleure prise
  const dernier = e.tentatives[e.tentatives.length - 1];
  const noteDernier = e.notes.find((n) => n.take === dernier)?.note;
  if (noteDernier !== undefined && noteDernier < NOTE_MINIMALE && e.essai < 2) return { action: 'lancer-objet', essai: e.essai + 1 };
  const meilleure = [...e.notes].sort((a, b) => b.note - a.note)[0];
  return { action: 'finir', retenu: meilleure?.take ?? dernier };
}

// ---- parties qui touchent au disque et au LLM (non testées sans moteur) ----

/** Planche 2×2 de quatre côtés de l'objet, tirée de la tournette, en data URL pour le message multimodal. */
export async function plancheVuesDataUrl(ffmpeg: string, tournette: string, sortie: string, images: readonly number[] = TOURNETTE_JUGE.images): Promise<string> {
  await new Promise<void>((ok, ko) => execFile(ffmpeg, argsPlancheVues(tournette, sortie, images), (e, _o, err) => (e ? ko(new Error(String(err).slice(-200))) : ok())));
  try {
    return `data:image/jpeg;base64,${(await readFile(sortie)).toString('base64')}`;
  } finally {
    await rm(sortie, { force: true });
  }
}

/** Le juge note l'objet 3D d'après quatre côtés. Sans LLM, ou en cas de panne : null (l'objet est gardé tel quel). */
export async function jugerVuesObjet(llm: ClientLlm | null, description: string, planche: string): Promise<VerdictVues | null> {
  if (!llm) return null;
  let usage: UsageJuge = { modele: '', entree: 0, sortie: 0 };
  for (let essai = 0; essai < 2; essai++) {
    try {
      const appel = { json: true, temperature: 0, maxTokens: 2000 };
      const messages = [
        { role: 'system', content: avecCompetences('juge', 'You are the visual judge of Nexora Creative.') },
        { role: 'user', content: [
          { type: 'text', text: `A 3D model was generated from this request: "${description.slice(0, 600)}".\nThe image shows four sides of the model (front-left, back-left, back-right, front-right of a turntable), rendered flat-lit.\nJudge it as a usable 3D asset: is it one coherent object matching the request, with consistent geometry from every side (no melted or missing parts, no duplicated limbs or legs, no floating fragments), clean surfaces and plausible textures? Answer with JSON only: {"note": 0-10 integer, "defauts": [up to 4 short strings], "raison": "one sentence"}. 8+ means ready to use, 6-7 usable, under 6 broken.` },
          { type: 'image_url', image_url: { url: planche } },
        ] },
      ] as MessageLlm[];
      const mesure = llm.completerMesure ? await llm.completerMesure('juge3d', messages, appel) : null;
      const brut = mesure ? mesure.texte : await llm.completer('juge3d', messages, appel);
      if (mesure) usage = { modele: mesure.modele, entree: usage.entree + mesure.entree, sortie: usage.sortie + mesure.sortie };
      const v = lireVerdictVues(brut);
      if (v) return { ...v, usage };
    } catch { /* deuxième essai puis null */ }
  }
  return null;
}
