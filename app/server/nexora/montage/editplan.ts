/**
 * EditPlan v1 : le contrat unique du montage (recherche/13 §5.1, recherche/14 §3). Une liste de décisions typée,
 * jamais de commande shell ni de texte libre ; durées en IMAGES entières (aucune dérive de flottants aux coupes).
 * Le LLM propose un EditPlan, le code le valide (`validerEditPlan`) et le rend : un plan invalide n'est jamais rendu.
 *
 * Conventions :
 *  - `duree_f` d'un plan vidéo = durée à l'écran (en images de sortie) ; il consomme `duree_f × vitesse` images de la
 *    source à partir de `entree_f`. Une transition `fondu`/`dip`/`glisse` de `duree_f` images chevauche le plan précédent :
 *    durée de la séquence = Σ duree_f − Σ transition_in.duree_f.
 *  - `mots` d'une source (images, [début, fin[) : aucune coupe ne tombe à l'intérieur d'un mot (marge 30 ms).
 */
import { z } from 'zod';

export const FORMATS = ['16:9', '9:16', '1:1'] as const;
export const GENRES = ['pub', 'bande-annonce', 'explicatif', 'social'] as const;
export const TRANSITIONS = ['cut', 'fondu', 'dip', 'glisse'] as const;
export type Format = (typeof FORMATS)[number];
export type Genre = (typeof GENRES)[number];

export const FONDU_AUDIO_MS_MIN = 30;
export const VITESSE_MIN = 0.25;
export const VITESSE_MAX = 4;
export const DUREE_PLAN_MIN_S = 0.1;
export const MAX_PLANS_VIDEO = 80;
export const MAX_DUREE_S = 180;

const imagesPos = z.number().int().min(1).max(200_000);
const imagesNonNeg = z.number().int().min(0).max(200_000);

const Source = z.object({
  kind: z.enum(['video', 'audio', 'image']),
  duree_f: imagesPos.optional().describe('durée connue de la source, en images au fps du plan'),
  chemin: z.string().max(400).optional(),
  mots: z.array(z.tuple([imagesNonNeg, imagesNonNeg])).max(2000).optional().describe('intervalles de parole [début, fin[ en images'),
});

const Transition = z.object({ type: z.enum(TRANSITIONS), duree_f: imagesNonNeg });

const PlanVideo = z.object({
  id: z.string().min(1).max(40),
  src: z.string().min(1).max(40),
  entree_f: imagesNonNeg.describe('image d’entrée dans la source'),
  duree_f: imagesPos.describe('durée à l’écran, en images'),
  vitesse: z.number().min(VITESSE_MIN).max(VITESSE_MAX).default(1),
  rampe: z.object({ de: z.number().min(VITESSE_MIN).max(VITESSE_MAX), a: z.number().min(VITESSE_MIN).max(VITESSE_MAX) }).optional().describe('rampe de vitesse linéaire sur le plan (remplace vitesse)'),
  transition_in: Transition.default({ type: 'cut', duree_f: 0 }),
  zoom: z.object({ de: z.number().min(1).max(1.6), a: z.number().min(1).max(1.6) }).optional(),
  section: z.string().max(30).optional(),
  pourquoi: z.string().max(160).optional(),
});

const Musique = z.object({
  src: z.string().min(1).max(40),
  entree_f: imagesNonNeg.default(0),
  duree_f: imagesPos.optional().describe('durée jouée ; par défaut jusqu’à la fin de la séquence'),
  gain_db: z.number().min(-40).max(6).default(-8),
  fondu_in_f: imagesNonNeg.default(0),
  fondu_out_f: imagesNonNeg.default(0),
});

const Voix = z.object({ src: z.string().min(1).max(40), debut_f: imagesNonNeg, entree_f: imagesNonNeg.default(0), duree_f: imagesPos, gain_db: z.number().min(-30).max(6).default(0) });

const Texte = z.object({
  texte: z.string().min(1).max(200),
  debut_f: imagesNonNeg,
  duree_f: imagesPos,
  style: z.enum(['titre', 'sous-titre', 'carton', 'bas']).default('titre'),
  position: z.enum(['haut', 'centre', 'bas']).default('bas'),
  taille_pct: z.number().min(1).max(30).default(6).describe('hauteur du texte en % de la hauteur de l’image'),
});

const Generation = z.object({
  description: z.string().min(1).max(300),
  duree_s: z.union([z.literal(5), z.literal(10)]),
  moteur: z.enum(['h3', 'qwen', 'music3']).default('h3'),
}).describe('plan manquant à tourner (sous devis) ; le montage ne dépense jamais lui-même');

export const EditPlanSchema = z.object({
  version: z.literal(1),
  fps: z.union([z.literal(24), z.literal(25), z.literal(30)]),
  format: z.enum(FORMATS),
  genre: z.enum(GENRES).optional(),
  titre: z.string().max(120).optional(),
  sources: z.record(z.string().min(1).max(40), Source),
  video: z.array(PlanVideo).min(1).max(MAX_PLANS_VIDEO),
  audio: z.object({
    musique: Musique.optional(),
    voix: z.array(Voix).max(60).default([]),
    ducking: z.object({ actif: z.boolean(), profondeur_db: z.number().min(0).max(30) }).default({ actif: false, profondeur_db: 0 }),
    cible_lufs: z.number().min(-23).max(-9).default(-14),
    crete_db: z.number().min(-6).max(0).default(-1),
    fondu_coupe_ms: z.number().min(0).max(500).default(FONDU_AUDIO_MS_MIN),
  }).default({ voix: [], ducking: { actif: false, profondeur_db: 0 }, cible_lufs: -14, crete_db: -1, fondu_coupe_ms: FONDU_AUDIO_MS_MIN }),
  textes: z.array(Texte).max(40).default([]),
  generations: z.array(Generation).max(12).default([]),
  metadonnees: z.object({ modele: z.string().max(80).optional(), savoir: z.array(z.string().max(60)).max(12).optional() }).optional(),
});
export type EditPlan = z.infer<typeof EditPlanSchema>;
export type PlanVideo = EditPlan['video'][number];
export type TexteEdit = EditPlan['textes'][number];

/** Une règle violée, en une phrase pour que le modèle corrige (champ `indice` = mémoire de fonction d'AMD). */
export interface Violation { regle: string; chemin: string; message: string; indice?: string }
export interface RapportValidation { ok: boolean; erreurs: Violation[]; avertissements: Violation[]; plan?: EditPlan }

export interface ContexteValidation {
  /** Médias disponibles : id → durée en secondes ; une source du plan absente de cette liste est refusée. */
  inventaire?: Record<string, { duree_s: number }>;
  duree_cible_s?: number;
}

export const framesDe = (s: number, fps: number) => Math.round(s * fps);
export const secondesDe = (f: number, fps: number) => f / fps;

/** Durée mesurée si elle est exploitable, sans remplacer une mesure inconnue par zéro. */
function dureeSourceEnFrames(declareeF: number | undefined, mesureeS: unknown, fps: number): number | undefined {
  if (typeof mesureeS !== 'number' || !Number.isFinite(mesureeS) || mesureeS <= 0) return declareeF;
  const mesureeF = framesDe(mesureeS, fps);
  if (!Number.isFinite(mesureeF)) return declareeF;
  return declareeF === undefined ? mesureeF : Math.min(declareeF, mesureeF);
}

/** Début de chaque plan vidéo sur la ligne de temps (images) et durée totale. */
export function lignedeTemps(plan: Pick<EditPlan, 'video'>): { debuts: number[]; fins: number[]; total: number } {
  const debuts: number[] = [];
  const fins: number[] = [];
  let curseur = 0;
  plan.video.forEach((c, i) => {
    const rec = i > 0 && c.transition_in.type !== 'cut' ? c.transition_in.duree_f : 0;
    const d = curseur - rec;
    debuts.push(d);
    fins.push(d + c.duree_f);
    curseur = d + c.duree_f;
  });
  return { debuts, fins, total: curseur };
}

/** Images de la source consommées par un plan. */
export function consommation(c: PlanVideo): number {
  const v = c.rampe ? (c.rampe.de + c.rampe.a) / 2 : c.vitesse;
  return Math.round(c.duree_f * v);
}

export function dureeTotaleS(plan: EditPlan): number {
  return lignedeTemps(plan).total / plan.fps;
}

const V = (regle: string, chemin: string, message: string, indice?: string): Violation => ({ regle, chemin, message, ...(indice ? { indice } : {}) });

/** Valide un objet quelconque : schéma Zod puis invariants de montage. Ne lève jamais. */
export function validerEditPlan(brut: unknown, ctx: ContexteValidation = {}): RapportValidation {
  const lu = EditPlanSchema.safeParse(brut);
  if (!lu.success) {
    const erreurs = lu.error.issues.slice(0, 12).map((i) => V('schema', i.path.join('.') || '(racine)', i.message, 'Respecte exactement le schéma EditPlan v1 ; durées en images entières.'));
    return { ok: false, erreurs, avertissements: [] };
  }
  const plan = lu.data;
  const erreurs: Violation[] = [];
  const avert: Violation[] = [];
  const { fps } = plan;

  const ids = new Set<string>();
  plan.video.forEach((c, i) => {
    const ch = `video.${i}`;
    if (ids.has(c.id)) erreurs.push(V('id_unique', `${ch}.id`, `identifiant de plan en double : ${c.id}`));
    ids.add(c.id);
    const src = plan.sources[c.src];
    if (!src) { erreurs.push(V('source_connue', `${ch}.src`, `source inconnue : ${c.src}`, 'Déclare la source dans `sources` avec le même identifiant que dans l’inventaire.')); return; }
    if (src.kind === 'audio') erreurs.push(V('source_video', `${ch}.src`, `${c.src} est un audio, pas une vidéo`));
    const inv = ctx.inventaire?.[c.src];
    if (ctx.inventaire && !inv) erreurs.push(V('source_autorisee', `${ch}.src`, `${c.src} n’est pas dans l’inventaire du projet`));
    if (c.duree_f / fps < DUREE_PLAN_MIN_S) erreurs.push(V('duree_min', `${ch}.duree_f`, `plan de ${c.duree_f} images : au moins ${Math.ceil(DUREE_PLAN_MIN_S * fps)}`));
    const conso = consommation(c);
    const dureeSrc = dureeSourceEnFrames(src.duree_f, inv?.duree_s, fps);
    if (src.kind === 'video' && dureeSrc !== undefined && c.entree_f + conso > dureeSrc) {
      erreurs.push(V('dans_la_source', `${ch}`, `le plan ${c.id} lit les images ${c.entree_f} à ${c.entree_f + conso} de ${c.src}, qui n’en a que ${dureeSrc}`, 'Réduis duree_f ou entree_f (ou la vitesse), ou choisis une source plus longue.'));
    }
    if (c.rampe && c.vitesse !== 1) avert.push(V('rampe_ignore_vitesse', `${ch}.vitesse`, 'rampe et vitesse donnés : la rampe l’emporte'));
    // Aucune coupe dans un mot : entrée et sortie dans la source tombent hors des intervalles de parole (marge 30 ms).
    if (src.mots?.length) {
      const marge = Math.ceil(0.03 * fps);
      for (const [pt, nom] of [[c.entree_f, 'entrée'], [c.entree_f + conso, 'sortie']] as const) {
        const dedans = src.mots.find(([a0, b0]) => pt > a0 - marge && pt < b0 + marge);
        if (dedans) {
          const apres = dedans[1] + marge;
          const avant = Math.max(0, dedans[0] - marge);
          erreurs.push(V('pas_de_coupe_dans_un_mot', `${ch}`, `la ${nom} du plan ${c.id} (image ${pt}) tombe dans un mot [${dedans[0]}, ${dedans[1]}[ (marge 30 ms comprise)`, `Place la coupe à l’image ${apres} (après le mot) ou ${avant} (avant), dans un silence.`));
        }
      }
    }
    if (i > 0) {
      const t = c.transition_in;
      if (t.type !== 'cut') {
        const precedent = plan.video[i - 1];
        if (t.duree_f < 1) erreurs.push(V('transition_duree', `${ch}.transition_in`, `transition ${t.type} sans durée`));
        if (t.duree_f > Math.floor(Math.min(c.duree_f, precedent.duree_f) / 2)) {
          erreurs.push(V('transition_duree', `${ch}.transition_in`, `transition de ${t.duree_f} images : au plus la moitié du plus court des deux plans (${Math.floor(Math.min(c.duree_f, precedent.duree_f) / 2)})`));
        }
      } else if (t.duree_f !== 0) avert.push(V('cut_sans_duree', `${ch}.transition_in`, 'une coupe sèche n’a pas de durée'));
    } else if (c.transition_in.type !== 'cut' && c.transition_in.duree_f > 0) {
      avert.push(V('premiere_transition', `${ch}.transition_in`, 'la transition du premier plan est ignorée'));
    }
  });

  const { total } = lignedeTemps(plan);
  if (total / fps > MAX_DUREE_S) erreurs.push(V('duree_max', 'video', `séquence de ${(total / fps).toFixed(1)} s : ${MAX_DUREE_S} s au plus`));
  if (ctx.duree_cible_s !== undefined) {
    const ecart = Math.abs(total / fps - ctx.duree_cible_s) / ctx.duree_cible_s;
    if (ecart > 0.05) erreurs.push(V('duree_cible', 'video', `durée ${(total / fps).toFixed(1)} s au lieu de ${ctx.duree_cible_s} s (±5 %)`, `Vise ${Math.round(ctx.duree_cible_s * fps)} images au total ; ajuste le dernier plan.`));
  }

  const a = plan.audio;
  const m = a.musique;
  if (m) {
    const s = plan.sources[m.src];
    if (!s) erreurs.push(V('source_connue', 'audio.musique.src', `source musique inconnue : ${m.src}`));
    else if (s.kind !== 'audio') erreurs.push(V('source_audio', 'audio.musique.src', `${m.src} n’est pas un audio`));
    else if (ctx.inventaire && !ctx.inventaire[m.src]) erreurs.push(V('source_autorisee', 'audio.musique.src', `${m.src} n’est pas dans l’inventaire du projet`));
    const dureeJouee = m.duree_f ?? total - 0;
    const dureeSrc = s ? dureeSourceEnFrames(s.duree_f, ctx.inventaire?.[m.src]?.duree_s, fps) : undefined;
    if (dureeSrc !== undefined && m.entree_f + dureeJouee > dureeSrc) erreurs.push(V('dans_la_source', 'audio.musique', `la musique lit au-delà de sa fin (${m.entree_f + dureeJouee} > ${dureeSrc} images)`, 'Donne duree_f ≤ durée de la piste − entree_f.'));
    if (m.fondu_in_f + m.fondu_out_f > dureeJouee) erreurs.push(V('fondus_musique', 'audio.musique', 'les fondus de la musique dépassent sa durée'));
  }
  a.voix.forEach((v, i) => {
    const s = plan.sources[v.src];
    if (!s || s.kind !== 'audio') erreurs.push(V('source_audio', `audio.voix.${i}.src`, `voix : source audio inconnue ${v.src}`));
    if (v.debut_f + v.duree_f > total) erreurs.push(V('dans_la_sequence', `audio.voix.${i}`, 'la voix dépasse la fin de la séquence'));
    // Borne de source : la plus courte durée connue, déclarée ou mesurée ; aucune durée connue → pas de borne inventée.
    if (s?.kind === 'audio') {
      const inv = ctx.inventaire?.[v.src];
      const dureeSrc = dureeSourceEnFrames(s.duree_f, inv?.duree_s, fps);
      if (dureeSrc !== undefined && v.entree_f + v.duree_f > dureeSrc) {
        erreurs.push(V('dans_la_source', `audio.voix.${i}`, `la voix lit les images ${v.entree_f} à ${v.entree_f + v.duree_f} de ${v.src}, qui n’en a que ${dureeSrc}`, 'Réduis duree_f ou entree_f, ou choisis une source plus longue.'));
      }
    }
  });
  if (a.voix.length && m && (!a.ducking.actif || a.ducking.profondeur_db < 6)) {
    erreurs.push(V('ducking', 'audio.ducking', 'une voix sur une musique exige un ducking actif d’au moins 6 dB', 'audio.ducking = {"actif": true, "profondeur_db": 10}'));
  }
  if (a.fondu_coupe_ms < FONDU_AUDIO_MS_MIN) erreurs.push(V('fondu_audio_30ms', 'audio.fondu_coupe_ms', `fondu audio de ${a.fondu_coupe_ms} ms à chaque coupe : au moins ${FONDU_AUDIO_MS_MIN} ms`, 'fondu_coupe_ms = 30'));

  plan.textes.forEach((t, i) => {
    const ch = `textes.${i}`;
    if (t.debut_f + t.duree_f > total) erreurs.push(V('texte_dans_la_sequence', ch, `le texte « ${t.texte.slice(0, 20)} » dépasse la fin de la séquence (${t.debut_f + t.duree_f} > ${total} images)`));
    const lignes = t.texte.split('\n');
    if (lignes.length > 2 || lignes.some((l) => [...l].length > 42)) erreurs.push(V('texte_lignes', ch, 'deux lignes de 42 caractères au plus', 'Raccourcis ou découpe le texte en deux textes successifs.'));
  });
  const unite = new Set(plan.video.map((c) => c.src));
  for (const [id, s] of Object.entries(plan.sources)) if (!unite.has(id) && id !== m?.src && !a.voix.some((v) => v.src === id)) avert.push(V('source_inutilisee', `sources.${id}`, `source ${id} déclarée mais non utilisée`));
  return { ok: erreurs.length === 0, erreurs, avertissements: avert, plan };
}

/** Phrase unique pour renvoyer les violations au modèle (une réparation, puis repli). */
export function messageErreurs(r: RapportValidation): string {
  return r.erreurs.map((e) => `- [${e.regle}] ${e.chemin} : ${e.message}${e.indice ? ` → ${e.indice}` : ''}`).join('\n');
}
