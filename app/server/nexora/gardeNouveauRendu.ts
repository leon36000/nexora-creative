import { checkpointMaxFL2VAExplicite } from '../graphs/h3.js';

type Corps = Record<string, unknown>;

/**
 * Branches non-H3 de graphFor. Une nouvelle branche exige une mise à jour ici :
 * le test de contrat compare les comparaisons explicites du répartiteur. La
 * couverture lexicale ne détecte pas toutes les réécritures possibles.
 * Ce garde s'applique aux nouvelles requêtes externes, pas aux suites de films.
 */
export const GENRES_NON_H3 = Object.freeze([
  'musique', 'upscale', 'cutout', 'restyle', 'swap', 'seam', 'hdr', 'stage-look', 'stage', 'object',
  'edit', 'extend', 'transition', 'speak', 'sound', 'effect', 'reshoot', 'reshoot-preview', 'mirror', 'still',
]);
const AUTRES_GENRES = new Set<string>(GENRES_NON_H3);

export type RefusNouveauRendu = 'INVALID_KIND' | 'H3_MAX_ANCHOR_UNAVAILABLE';

/** Apply only to a new external request, before generate or its reservations. */
export function raisonRefusNouveauRendu(input: unknown): RefusNouveauRendu | null {
  if (!input || typeof input !== 'object' || Array.isArray(input)) return null;
  const b = input as Corps;
  const variants = Array.isArray(b.variants)
    ? b.variants.filter((v): v is Corps => !!v && typeof v === 'object' && !Array.isArray(v)).slice(0, 9)
    : [];
  const corps = variants.length ? variants.map((v) => ({ ...b, ...v })) : [b];
  for (const c of corps) {
    if (c.videoModel !== 'h3-max') continue;
    if (typeof c.kind === 'string' && AUTRES_GENRES.has(c.kind)) continue;
    if (c.kind != null && c.kind !== 'video') return 'INVALID_KIND';
    if ((c.startImage || c.endImage) && !checkpointMaxFL2VAExplicite(c.checkpoint)) return 'H3_MAX_ANCHOR_UNAVAILABLE';
  }
  return null;
}

export function nouveauRenduAncreMaxInvalide(input: unknown): boolean {
  return raisonRefusNouveauRendu(input) !== null;
}

/** Invoke the downstream helper only after all submitted variants pass the guard. */
export function avecGardeNouveauRendu<T, U>(input: unknown, accepter: () => T, refuser: (raison: RefusNouveauRendu) => U): T | U {
  const raison = raisonRefusNouveauRendu(input);
  return raison ? refuser(raison) : accepter();
}
