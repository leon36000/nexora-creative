import { describe, expect, it } from 'vitest';
import { type EditPlan, validerEditPlan } from './editplan.js';

const plan = (): EditPlan => ({
  version: 1, fps: 24, format: '16:9', genre: 'pub',
  sources: { a: { kind: 'video', duree_f: 240, mots: [[50, 70]] }, b: { kind: 'video', duree_f: 240 }, mus: { kind: 'audio', duree_f: 960 } },
  video: [
    { id: 'p1', src: 'a', entree_f: 0, duree_f: 48, vitesse: 1, transition_in: { type: 'cut', duree_f: 0 } },
    { id: 'p2', src: 'b', entree_f: 24, duree_f: 72, vitesse: 1, transition_in: { type: 'fondu', duree_f: 10 } },
  ],
  audio: { musique: { src: 'mus', entree_f: 0, duree_f: 110, gain_db: -8, fondu_in_f: 7, fondu_out_f: 36 }, voix: [], ducking: { actif: false, profondeur_db: 0 }, cible_lufs: -14, crete_db: -1, fondu_coupe_ms: 30 },
  textes: [{ texte: 'Une phrase courte.', debut_f: 12, duree_f: 36, style: 'titre', position: 'bas', taille_pct: 6 }],
  generations: [],
});
const avecVoix = (entree_f: number, dureeSource?: number): EditPlan => {
  const p = plan();
  p.sources.v = { kind: 'audio', ...(dureeSource === undefined ? {} : { duree_f: dureeSource }) };
  p.audio.voix = [{ src: 'v', debut_f: 24, entree_f, duree_f: 80, gain_db: 0 }];
  p.audio.ducking = { actif: true, profondeur_db: 10 };
  return p;
};
const inventaire = { a: { duree_s: 10 }, b: { duree_s: 10 }, mus: { duree_s: 40 }, v: { duree_s: 5 } };

describe('Bornes de la source voix', () => {
  it('accepte une voix qui se termine exactement à la fin de sa source', () => {
    expect(validerEditPlan(avecVoix(40, 120)).ok).toBe(true);
  });
  it('refuse de lire au-delà de la source même si la voix reste dans la séquence', () => {
    const p = avecVoix(50, 120);
    expect(p.audio.voix[0].debut_f + p.audio.voix[0].duree_f).toBeLessThanOrEqual(110);
    const r = validerEditPlan(p);
    expect(r.ok).toBe(false);
    expect(r.erreurs.some((e) => e.regle === 'dans_la_source' && e.chemin === 'audio.voix.0')).toBe(true);
    expect(r.erreurs.some((e) => e.regle === 'dans_la_sequence')).toBe(false);
  });
  it('utilise la durée de l’inventaire si celle du plan est absente', () => {
    expect(validerEditPlan(avecVoix(40), { inventaire }).ok).toBe(true);
    const r = validerEditPlan(avecVoix(50), { inventaire });
    expect(r.ok).toBe(false);
    expect(r.erreurs.some((e) => e.regle === 'dans_la_source' && e.chemin === 'audio.voix.0')).toBe(true);
    expect(r.erreurs.some((e) => e.regle === 'dans_la_sequence')).toBe(false);
  });
  it('n’invente pas de durée si aucune n’est connue', () => {
    expect(validerEditPlan(avecVoix(50)).ok).toBe(true);
  });
});
