import { describe, expect, it } from 'vitest';
import { consommation, EditPlanSchema, validerEditPlan, type PlanVideo } from './editplan.js';
import { segmentsVitesse } from './retiming.js';
import { commandeRendu } from './rendu.js';

const planPour = (overrides: Partial<PlanVideo> = {}): PlanVideo => ({
  id: 'plan-test',
  src: 'source-test',
  entree_f: 17,
  duree_f: 36,
  vitesse: 1,
  transition_in: { type: 'cut', duree_f: 0 },
  ...overrides,
});

describe('segmentsVitesse', () => {
  it('préserve la vitesse déclarée pour les plans constants', () => {
    for (const vitesse of [0.25, 0.5, 1, 2, 4]) {
      const plan = planPour({ duree_f: 36, vitesse });
      const segments = segmentsVitesse(plan);

      expect(segments).toHaveLength(1);
      expect(segments[0]).toEqual({
        entree_f: plan.entree_f,
        duree_f: plan.duree_f,
        source_f: consommation(plan),
        vitesse,
      });
    }
  });

  it('conserve exactement les totaux source et sortie sur les durées frontières', () => {
    for (const duree_f of [3, 5, 7, 36]) {
      const plan = planPour({ duree_f, rampe: { de: 0.5, a: 2 } });
      const segments = segmentsVitesse(plan);

      expect(segments.reduce((total, segment) => total + segment.source_f, 0)).toBe(consommation(plan));
      expect(segments.reduce((total, segment) => total + segment.duree_f, 0)).toBe(plan.duree_f);
    }
  });

  it('ne produit aucun segment vide aux frontières d’arrondi', () => {
    for (const duree_f of [3, 5, 7, 36]) {
      const segments = segmentsVitesse(planPour({ duree_f, rampe: { de: 0.5, a: 2 } }));

      expect(segments.length).toBeGreaterThan(0);
      expect(segments.every((segment) => segment.duree_f > 0 && segment.source_f > 0)).toBe(true);
    }
  });

  it('place les intervalles source à la suite et couvre exactement la source consommée', () => {
    for (const duree_f of [3, 5, 7, 36]) {
      const plan = planPour({ entree_f: 23, duree_f, rampe: { de: 0.5, a: 2 } });
      const segments = segmentsVitesse(plan);

      expect(segments[0]?.entree_f).toBe(plan.entree_f);
      for (let index = 1; index < segments.length; index++) {
        expect(segments[index]!.entree_f).toBe(segments[index - 1]!.entree_f + segments[index - 1]!.source_f);
      }
      const dernier = segments[segments.length - 1]!;
      expect(dernier.entree_f + dernier.source_f).toBe(plan.entree_f + consommation(plan));
    }
  });

  it('limite à six segments même pour les rampes longues', () => {
    for (const duree_f of [36, 100]) {
      const segments = segmentsVitesse(planPour({ duree_f, rampe: { de: 0.25, a: 4 } }));

      expect(segments.length).toBeGreaterThan(0);
      expect(segments.length).toBeLessThanOrEqual(6);
    }
  });

  it('fait croître les vitesses d’une rampe ascendante', () => {
    const segments = segmentsVitesse(planPour({ duree_f: 36, rampe: { de: 0.5, a: 2 } }));

    expect(segments.length).toBeGreaterThan(1);
    expect(segments[0]!.vitesse).toBeLessThan(segments[segments.length - 1]!.vitesse);
  });

  it('inverse la tendance pour une rampe descendante', () => {
    const segments = segmentsVitesse(planPour({ duree_f: 36, rampe: { de: 2, a: 0.5 } }));

    expect(segments.length).toBeGreaterThan(1);
    expect(segments[0]!.vitesse).toBeGreaterThan(segments[segments.length - 1]!.vitesse);
  });

  it.each([[0.7, 1.3], [1.3, 0.7], [0.25, 0.25]])('ne renverse pas localement la rampe %s → %s', (de, a) => {
    for (let duree_f = 3; duree_f <= 100; duree_f++) {
      const segments = segmentsVitesse(planPour({ duree_f, rampe: { de, a } }));
      for (let i = 1; i < segments.length; i++) {
        const difference = segments[i].source_f * segments[i - 1].duree_f - segments[i - 1].source_f * segments[i].duree_f;
        if (de === a) expect(difference).toBe(0);
        else expect(Math.sign(a - de) * difference).toBeGreaterThanOrEqual(0);
      }
    }
  });

  it('reste déterministe, compact et exact de 3 à 100 images', () => {
    for (let duree_f = 3; duree_f <= 100; duree_f++) {
      const plan = planPour({ duree_f, entree_f: 5, rampe: { de: 0.25, a: 4 } });
      const segments = segmentsVitesse(plan);

      expect(segmentsVitesse(plan)).toEqual(segments);
      expect(segments.length).toBeGreaterThan(0);
      expect(segments.length).toBeLessThanOrEqual(6);
      expect(segments.every((segment) => segment.duree_f > 0 && segment.source_f > 0)).toBe(true);
      expect(segments.reduce((total, segment) => total + segment.duree_f, 0)).toBe(duree_f);
      expect(segments.reduce((total, segment) => total + segment.source_f, 0)).toBe(consommation(plan));
      for (let index = 1; index < segments.length; index++) {
        expect(segments[index]!.entree_f).toBe(segments[index - 1]!.entree_f + segments[index - 1]!.source_f);
      }
    }
  });

  it('fusionne les morceaux dont la source arrondie serait vide', () => {
    const plan = planPour({ duree_f: 4, rampe: { de: 0.25, a: 1 } });
    const segments = segmentsVitesse(plan);
    expect(segments.every(s => s.source_f > 0 && s.duree_f > 0)).toBe(true);
    expect(segments.reduce((n, s) => n + s.source_f, 0)).toBe(3);
    expect(segments.reduce((n, s) => n + s.duree_f, 0)).toBe(4);
  });

  it('ne modifie pas le plan ni la rampe fournis', () => {
    const plan = planPour({ rampe: Object.freeze({ de: 0.25, a: 0.25 }), duree_f: 3 });
    Object.freeze(plan);
    expect(segmentsVitesse(plan)).toHaveLength(1);
  });

  it('refuse un appel direct qui ne consomme aucune image', () => {
    expect(() => segmentsVitesse(planPour({ duree_f: 1, vitesse: 0.25 }))).toThrow(RangeError);
  });

  it.each([3, 5])('borne aussi les lectures de la commande réelle pour %i images', duree_f => {
    const c = planPour({ entree_f: 0, duree_f, rampe: { de: 0.5, a: 2 } });
    const source = consommation(c);
    const plan = EditPlanSchema.parse({ version: 1, fps: 24, format: '16:9', sources: { 'source-test': { kind: 'video', duree_f: source } }, video: [c] });
    expect(validerEditPlan(plan).ok).toBe(true);
    const cmd = commandeRendu(plan, () => '/source.mp4', '/sortie.mp4');
    const graph = cmd.args[cmd.args.indexOf('-filter_complex') + 1];
    const lectures = [...graph.matchAll(/trim=start_frame=(\d+):end_frame=(\d+)/g)];
    expect(lectures.length).toBeGreaterThan(0);
    expect(lectures.every(m => Number(m[2]) > Number(m[1]) && Number(m[2]) <= source)).toBe(true);
    expect(graph).toContain(`trim=end_frame=${duree_f}[c0]`);
  });
});
