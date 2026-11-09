import { describe, expect, it, vi } from 'vitest';
import { type ContexteValidation, type EditPlan, validerEditPlan } from './editplan.js';
import { ameliorerMontage } from './producteur.js';
import type { ClientLlm } from '../llm.js';
import type { EtatMontageFilm } from './producteur.js';
import type { Brief } from './types.js';

const observation = vi.hoisted(() => ({ contextes: [] as unknown[], revisions: [] as boolean[] }));

vi.mock('../competences.js', () => ({ avecCompetences: (_role: string, consignes: string) => consignes }));
vi.mock('./critique.js', () => ({
  critiquer: async () => ({ metriques: { porte: true }, ecarts: [{ gravite: 'mineur', message: 'essai', indice: 'essai' }], composite: 0.5, resume: 'essai' }),
}));
vi.mock('./metriques.js', () => ({ mesurer: () => ({ composite: 0.5 }) }));
vi.mock('./revise.js', async (importOriginal) => {
  const original = await importOriginal<typeof import('./revise.js')>();
  return {
    ...original,
    reviser: (...args: Parameters<typeof original.reviser>) => {
      observation.contextes.push(args[2]);
      const resultat = original.reviser(...args);
      observation.revisions.push(resultat.ok);
      return resultat;
    },
  };
});

function etatAvecVoix(): EtatMontageFilm {
  const plan = {
    version: 1,
    fps: 24,
    format: '16:9',
    sources: { clip: { kind: 'video', duree_f: 24 }, voice: { kind: 'audio' } },
    video: [{ id: 'p1', src: 'clip', entree_f: 0, duree_f: 24, vitesse: 1, transition_in: { type: 'cut', duree_f: 0 } }],
    audio: { voix: [{ src: 'voice', debut_f: 0, entree_f: 0, duree_f: 24, gain_db: 0 }], ducking: { actif: false, profondeur_db: 0 }, cible_lufs: -14, crete_db: -1, fondu_coupe_ms: 30 },
    textes: [],
    generations: [],
  } as EditPlan;
  const brief: Brief = {
    id: 'film', partition: 'test', genre: 'pub', format: '16:9', duree_cible_s: 1, fps: 24,
    enonce: 'Essai local avec voix', textes_imposes: [], clips: [{ id: 'clip', duree_s: 1 }], voix: { id: 'voice', duree_s: 1 },
  };
  return { film: 1, brief, plan, source: 'code', tours: 0, score: 0.5 };
}

function planAvecVoix(): EditPlan {
  return etatAvecVoix().plan;
}

describe('Inventaire source de la voix dans le Producteur', () => {
  it('refuse une source voix absente d’un inventaire explicite', () => {
    const plan = planAvecVoix();
    const rapport = validerEditPlan(plan, { inventaire: { clip: { duree_s: 1 } } });
    expect(rapport.ok).toBe(false);
    expect(rapport.erreurs).toEqual(expect.arrayContaining([
      expect.objectContaining({ regle: 'source_autorisee', chemin: 'audio.voix.0.src' }),
    ]));
  });

  it('garde le comportement sans inventaire explicite', () => {
    expect(validerEditPlan(planAvecVoix()).ok).toBe(true);
  });

  it('ne traite pas une propriété héritée comme une entrée d’inventaire', () => {
    const plan = planAvecVoix();
    Object.defineProperty(plan.sources, 'toString', { value: plan.sources.voice, enumerable: true, configurable: true });
    delete plan.sources.voice;
    plan.audio.voix[0]!.src = 'toString';
    const rapport = validerEditPlan(plan, { inventaire: { clip: { duree_s: 1 } } });
    expect(rapport.erreurs).toEqual(expect.arrayContaining([
      expect.objectContaining({ regle: 'source_autorisee', chemin: 'audio.voix.0.src' }),
    ]));
  });

  it('inclut la source voix quand le Producteur revalide ses rustines', async () => {
    observation.contextes.length = 0;
    observation.revisions.length = 0;
    const llm: ClientLlm = {
      completer: async () => JSON.stringify({ rustines: [{ op: 'regler_plan', id: 'p1', duree_f: 24 }] }),
    };
    const resultat = await ameliorerMontage(etatAvecVoix(), llm);
    expect(observation.contextes).toHaveLength(1);
    const ctx = observation.contextes[0] as ContexteValidation;
    expect(Object.hasOwn(ctx.inventaire ?? {}, 'voice')).toBe(true);
    expect(observation.revisions).toEqual([true]);
    expect(resultat.message).not.toContain('source_autorisee');
  });
});
