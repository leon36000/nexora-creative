import { describe, expect, it } from 'vitest';
import { validerEditPlan, type EditPlan } from './editplan.js';

type Media = 'video' | 'musique' | 'voix';
const paths: Record<Media, string> = {
  video: 'video.0.src',
  musique: 'audio.musique.src',
  voix: 'audio.voix.0.src',
};
const absentSourceRule: Record<Media, string> = {
  video: 'source_connue',
  musique: 'source_connue',
  voix: 'source_audio',
};

function planPour(media: Media, id = 'media', propre = true): EditPlan {
  const sources: Record<string, { kind: 'video' | 'audio'; duree_f: number }> = {
    a: { kind: 'video', duree_f: 240 },
    b: { kind: 'video', duree_f: 240 },
  };
  if (propre) Object.defineProperty(sources, id, { value: { kind: media === 'video' ? 'video' : 'audio', duree_f: 240 }, enumerable: true, configurable: true });
  const plan: EditPlan = {
    version: 1, fps: 24, format: '16:9', sources: sources as EditPlan['sources'],
    video: [
      { id: 'p1', src: media === 'video' ? id : 'a', entree_f: 0, duree_f: 48, vitesse: 1, transition_in: { type: 'cut', duree_f: 0 } },
      { id: 'p2', src: 'b', entree_f: 0, duree_f: 72, vitesse: 1, transition_in: { type: 'cut', duree_f: 0 } },
    ],
    audio: {
      ...(media === 'musique' ? { musique: { src: id, entree_f: 0, duree_f: 48, gain_db: -8, fondu_in_f: 0, fondu_out_f: 0 } } : {}),
      voix: media === 'voix' ? [{ src: id, debut_f: 0, entree_f: 0, duree_f: 24, gain_db: 0 }] : [],
      ducking: { actif: false, profondeur_db: 0 }, cible_lufs: -14, crete_db: -1, fondu_coupe_ms: 30,
    },
    textes: [], generations: [],
  };
  return plan;
}

function inventaire(media?: Media, id = 'media'): Record<string, { duree_s: number }> {
  const entrees: [string, { duree_s: number }][] = [['a', { duree_s: 10 }], ['b', { duree_s: 10 }]];
  if (media) entrees.push([id, { duree_s: 10 }]);
  return Object.fromEntries(entrees);
}

describe('présence propre des sources et de l’inventaire', () => {
  it.each((['video', 'musique', 'voix'] as const))('refuse %s déclarée dans le plan mais absente de l’inventaire', (media) => {
    const rapport = validerEditPlan(planPour(media, 'toString'), { inventaire: inventaire() });
    expect(rapport.erreurs).toEqual(expect.arrayContaining([
      expect.objectContaining({ regle: 'source_autorisee', chemin: paths[media] }),
    ]));
  });

  it.each((['video', 'musique', 'voix'] as const))('accepte %s toString quand source et inventaire en sont des propriétés propres', (media) => {
    const rapport = validerEditPlan(planPour(media, 'toString'), { inventaire: inventaire(media, 'toString') });
    expect(rapport.ok).toBe(true);
  });

  it.each([
    ['video', 'toString'], ['video', '__proto__'], ['musique', 'toString'], ['voix', 'toString'],
  ] as const)('ne traite pas la source %s héritée %s comme une déclaration, même sans inventaire', (media, id) => {
    const rapport = validerEditPlan(planPour(media, id, false));
    expect(rapport.erreurs).toEqual(expect.arrayContaining([
      expect.objectContaining({ regle: absentSourceRule[media], chemin: paths[media] }),
    ]));
  });

  it('distingue une source non déclarée d’une source déclarée mais absente du contexte', () => {
    const ctxAvecCleToString = inventaire('video', 'toString');
    const sourceAbsente = validerEditPlan(planPour('video', 'toString', false), { inventaire: ctxAvecCleToString });
    const contexteAbsent = validerEditPlan(planPour('video', 'toString', true), { inventaire: inventaire() });
    expect(sourceAbsente.erreurs).toEqual(expect.arrayContaining([
      expect.objectContaining({ regle: 'source_connue', chemin: paths.video }),
    ]));
    expect(sourceAbsente.erreurs.some((e) => e.regle === 'source_autorisee' && e.chemin === paths.video)).toBe(false);
    expect(contexteAbsent.erreurs).toEqual(expect.arrayContaining([
      expect.objectContaining({ regle: 'source_autorisee', chemin: paths.video }),
    ]));
  });

  it.each((['video', 'musique', 'voix'] as const))('refuse %s avec une entrée propre mais nulle dans l’inventaire', (media) => {
    const inventaireMalformed = inventaire();
    Object.defineProperty(inventaireMalformed, 'media', { value: null, enumerable: true, configurable: true });
    const rapport = validerEditPlan(planPour(media), { inventaire: inventaireMalformed });
    expect(rapport.erreurs).toEqual(expect.arrayContaining([
      expect.objectContaining({ regle: 'source_autorisee', chemin: paths[media] }),
    ]));
  });

  it('ne restreint pas une source déclarée quand aucun inventaire n’est fourni', () => {
    expect(validerEditPlan(planPour('voix')).ok).toBe(true);
  });
});
