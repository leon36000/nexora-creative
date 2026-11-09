/** Découpage d'un plan validé : mêmes bornes de source pour le validateur et le rendu. */
import { consommation, type PlanVideo } from './editplan.js';

export interface SegmentVitesse {
  entree_f: number;
  duree_f: number;
  source_f: number;
  vitesse: number;
}

const MAX_SEGMENTS = 6;

function suitLeSens(avant: SegmentVitesse, apres: SegmentVitesse, sens: number): boolean {
  const difference = apres.source_f * avant.duree_f - avant.source_f * apres.duree_f;
  return sens === 0 ? difference === 0 : sens * difference >= 0;
}

function essayerRampe(plan: PlanVideo, nombre: number, sourceTotale: number): SegmentVitesse[] | null {
  const { de, a } = plan.rampe!;
  const sens = Math.sign(a - de);
  const segments: SegmentVitesse[] = [];
  let sortieAvant = 0;
  let sourceAvant = 0;
  for (let i = 1; i <= nombre; i++) {
    const sortieApres = Math.round(plan.duree_f * i / nombre);
    const sourceApres = i === nombre ? sourceTotale
      : Math.round(de * sortieApres + (a - de) * sortieApres * sortieApres / (2 * plan.duree_f));
    const duree = sortieApres - sortieAvant;
    const source = sourceApres - sourceAvant;
    // Une frontière arrondie peut ne consommer aucune image : fusionner les morceaux.
    if (duree <= 0 || source <= 0) return null;
    const segment = { entree_f: plan.entree_f + sourceAvant, duree_f: duree, source_f: source, vitesse: source / duree };
    const precedent = segments.at(-1);
    if (precedent && !suitLeSens(precedent, segment, sens)) return null;
    segments.push(segment);
    sortieAvant = sortieApres;
    sourceAvant = sourceApres;
  }
  return segments;
}

/** Les anciennes séquences à vitesse constante gardent leur vitesse déclarée. */
export function segmentsVitesse(plan: PlanVideo): SegmentVitesse[] {
  const source = consommation(plan);
  if (source < 1) throw new RangeError('Le plan doit consommer au moins une image source.');
  const unique = { entree_f: plan.entree_f, duree_f: plan.duree_f, source_f: source, vitesse: plan.rampe ? source / plan.duree_f : plan.vitesse };
  if (!plan.rampe) return [unique];
  for (let nombre = Math.min(MAX_SEGMENTS, plan.duree_f, source); nombre >= 2; nombre--) {
    const segments = essayerRampe(plan, nombre, source);
    if (segments) return segments;
  }
  return [unique];
}
