/**
 * Détourage vidéo : validation des réglages envoyés par l'interface et traduction vers les paramètres du serveur de
 * détourage (outils/detourage/serveur.py). Les clics sont normalisés (0..1) : ils ne dépendent pas de la résolution.
 */
import { z } from 'zod';

const unite = z.number().min(0).max(1);
export const InviteSchema = z.object({
  /** Numéro de l'image (0 = première image de la plage traitée). */
  image: z.number().int().min(0).max(1_000_000),
  /** [x, y, étiquette] : 1 = « ceci fait partie du sujet », 0 = « ceci n'en fait pas partie ». */
  points: z.array(z.tuple([unite, unite, z.union([z.literal(0), z.literal(1)])])).max(64).default([]),
  boite: z.tuple([unite, unite, unite, unite]).nullable().optional(),
}).refine((i) => i.points.length > 0 || !!i.boite, { message: 'Un clic ou une boîte est nécessaire sur chaque image choisie.' });

export const FondSchema = z.discriminatedUnion('type', [
  z.object({ type: z.literal('couleur'), valeur: z.string().regex(/^#[0-9a-fA-F]{6}$/, 'Couleur #RRGGBB attendue.') }),
  z.object({ type: z.literal('image'), fichier: z.string().regex(/^[a-zA-Z0-9._-]{1,80}$/) }),
  z.object({ type: z.literal('video'), fichier: z.string().regex(/^[a-zA-Z0-9._-]{1,80}$/) }),
  z.object({ type: z.literal('flou') }),
]);

export const SortiesSchema = z.object({
  png16: z.boolean().default(true), rgba16: z.boolean().default(true), exr: z.boolean().default(true),
  prores: z.boolean().default(true), webm: z.boolean().default(true), matte: z.boolean().default(true), apercu: z.boolean().default(true),
}).default({ png16: true, rgba16: true, exr: true, prores: true, webm: true, matte: true, apercu: true });

export const ParamsSchema = z.object({
  /** « rapide » : SAM 3.1 + ViTMatte (mesuré). « pro » : LTX-2.5 Alpha-Gen, pas encore intégré à Creative. */
  palier: z.enum(['rapide', 'pro']).default('rapide'),
  /** « suivi » : aperçu du suivi seul (rapide), « complet » : matting, stabilisation et exports. */
  mode: z.enum(['suivi', 'complet']).default('complet'),
  invites: z.array(InviteSchema).min(1).max(200),
  debutS: z.number().min(0).max(36_000).default(0),
  dureeS: z.number().min(0.2).max(36_000).nullable().default(null),
  largeurMax: z.number().int().min(256).max(3840).default(1920),
  segment: z.object({ taille: z.number().int().min(8).max(240).default(96), recouvrement: z.number().int().min(2).max(48).default(12) })
    .default({ taille: 96, recouvrement: 12 }).refine((s) => s.recouvrement < s.taille, { message: 'Le recouvrement doit être plus petit que le segment.' }),
  /** SAM 3.1 seulement (SAM 2.1 est retiré) : la sélection se fait par clics, boîte ou mot. */
  sam: z.enum(['sam3.1']).default('sam3.1'),
  /** ViTMatte base + bande de 5 % : meilleur réglage mesuré sur vérité terrain (recherche/22 §9, fourrure et fumée). */
  matting: z.enum(['vitmatte-small', 'vitmatte-base', 'aucun']).default('vitmatte-base'),
  /** Largeur de la zone incertaine du trimap, en fraction du petit côté (0,015 = ancien réglage). */
  bande: z.number().min(0.005).max(0.1).default(0.05),
  lissage: z.number().min(0).max(1.5).default(1),
  sorties: SortiesSchema,
  composite: FondSchema.nullable().default(null),
}).refine((p) => !(p.palier === 'pro' && p.mode === 'suivi'), { message: 'Le palier pro n’a pas d’aperçu de suivi.' });

export type ParamsDetourage = z.infer<typeof ParamsSchema>;

/** Traduit les réglages de l'interface vers les paramètres du serveur Python (noms de la chaîne de traitement). */
export function versParamsMoteur(p: ParamsDetourage): Record<string, unknown> {
  return {
    source: 'source.mp4', largeur_max: p.largeurMax, debut_s: p.debutS, duree_s: p.dureeS,
    invites: p.invites.map((i) => ({ image: i.image, points: i.points, boite: i.boite ?? null })),
    segment: p.segment, sam: p.sam, matting: p.matting, bande: p.bande, lissage: p.lissage,
    etapes: p.mode === 'suivi' ? ['suivi'] : ['suivi', 'matting', 'sorties'],
    sorties: p.sorties, composite: p.composite, conserver_travail: true,
  };
}

/** Temps GPU estimé (secondes) d'un travail « rapide », d'après les mesures de recherche/22 (GB10, 720p ≈ 0,9 Mpx). */
export function secondesEstimees(p: ParamsDetourage, fps = 24, secondesSource = 5, mesure?: { parImageMpx?: number; fixe?: number }): number {
  const duree = p.dureeS ?? secondesSource;
  const images = Math.max(1, Math.round(duree * fps));
  const mpx = (p.largeurMax * Math.round(p.largeurMax * 9 / 16)) / 1e6;
  const parImageMpx = mesure?.parImageMpx ?? 0.85; // s par image et par mégapixel, étapes complètes
  const facteur = p.mode === 'suivi' ? 0.45 : 1;
  return Math.ceil((mesure?.fixe ?? 8) + images * Math.max(0.12, mpx) * parImageMpx * facteur);
}
