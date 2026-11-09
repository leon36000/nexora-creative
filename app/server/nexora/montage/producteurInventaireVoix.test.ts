import { describe, expect, it } from 'vitest';
import { validerEditPlan, type EditPlan } from './editplan.js';
import { inventaireDuBrief } from './producteur.js';
import type { Brief } from './types.js';

const brief: Brief = {
  id: 'film', partition: 'test', genre: 'explicatif', format: '16:9', duree_cible_s: 1, fps: 24,
  enonce: 'Essai avec une voix existante', textes_imposes: [],
  clips: [{ id: 'clip', duree_s: 1 }],
  musique: { id: 'music', duree_s: 1, bpm: 120, battues_s: [], energie: [] },
  voix: { id: 'voice', duree_s: 1 },
};
const plan: EditPlan = {
  version: 1, fps: 24, format: '16:9', genre: 'explicatif',
  sources: { clip: { kind: 'video', duree_f: 24 }, music: { kind: 'audio', duree_f: 24 }, voice: { kind: 'audio', duree_f: 24 } },
  video: [{ id: 'p1', src: 'clip', entree_f: 0, duree_f: 24, vitesse: 1, transition_in: { type: 'cut', duree_f: 0 } }],
  audio: { musique: { src: 'music', entree_f: 0, duree_f: 24, gain_db: -8, fondu_in_f: 0, fondu_out_f: 0 },
    voix: [{ src: 'voice', debut_f: 0, entree_f: 0, duree_f: 24, gain_db: 0 }],
    ducking: { actif: true, profondeur_db: 8 }, cible_lufs: -14, crete_db: -1, fondu_coupe_ms: 30 },
  textes: [], generations: [],
};

describe('inventaireDuBrief pour l’aperçu du montage', () => {
  it('inclut clips, musique et voix, puis autorise le plan vocal correspondant', () => {
    const inventaire = inventaireDuBrief(brief);
    expect(inventaire).toEqual({ clip: { duree_s: 1 }, music: { duree_s: 1 }, voice: { duree_s: 1 } });
    const rapport = validerEditPlan(plan, { inventaire, duree_cible_s: 1 });
    expect(rapport.ok).toBe(true);
    expect(rapport.erreurs).toEqual([]);
  });

  it('n’autorise pas une voix absente du brief', () => {
    const sansVoix = { ...brief, voix: undefined };
    const rapport = validerEditPlan(plan, { inventaire: inventaireDuBrief(sansVoix), duree_cible_s: 1 });
    expect(rapport.ok).toBe(false);
    expect(rapport.erreurs).toEqual(expect.arrayContaining([
      expect.objectContaining({ regle: 'source_autorisee', chemin: 'audio.voix.0.src' }),
    ]));
  });

  it.each(['musique', 'voix'] as const)('conserve une entrée %s dont l’identifiant est __proto__', (media) => {
    const cas = media === 'musique'
      ? { ...brief, musique: { ...brief.musique!, id: '__proto__' } }
      : { ...brief, voix: { ...brief.voix!, id: '__proto__' } };
    const inventaire = inventaireDuBrief(cas);
    expect(Object.hasOwn(inventaire, '__proto__')).toBe(true);
    expect(Object.getPrototypeOf(inventaire)).toBe(Object.prototype);
    expect(inventaire['__proto__']).toEqual({ duree_s: 1 });
  });
});
