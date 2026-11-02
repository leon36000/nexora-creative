import { describe, expect, it } from 'vitest';
import { compteurProjet, corpsBrouillonDe, corpsFinalDe, prisesDuPlan, type LecturePrise } from './prises.js';

const tarif = { creditsParSecondeGpu: 0.5 };
const rapide = { videoModel: 'h3-fast', width: 832, height: 480, lengthFrames: 124 };
const cinema = { videoModel: 'h3-max', width: 1344, height: 768, lengthFrames: 124 };
const base: Record<number, LecturePrise> = {
  1: { status: 'done', corps: cinema }, 2: { status: 'done', corps: cinema }, 3: { status: 'done', corps: rapide },
  4: { status: 'failed', corps: cinema }, 5: { status: 'running', corps: rapide },
};
const lire = (id: number) => base[id];

describe('prises par plan et compteur de projet', () => {
  it('liste candidats, prise retenue et ajouts, sans doublon, avec leur coût', () => {
    const v = prisesDuPlan({ take: 1, candidats: [1, 2], extra: [{ take: 3, brouillon: true }, { take: 4, brouillon: false }], rejetees: [2] }, lire, tarif);
    expect(v.map((x) => x.take)).toEqual([1, 2, 3, 4]);
    expect(v.find((x) => x.take === 1)).toMatchObject({ retenue: true, rejetee: false, credits: 65 });
    expect(v.find((x) => x.take === 2)).toMatchObject({ retenue: false, rejetee: true });
    expect(v.find((x) => x.take === 3)).toMatchObject({ brouillon: true, credits: 15 });
    expect(v.find((x) => x.take === 4)).toMatchObject({ statut: 'failed', credits: 0 });
  });
  it('le compteur compte aussi les prises rejetées et les brouillons, séparément', () => {
    const v = prisesDuPlan({ take: 1, candidats: [1, 2], extra: [{ take: 3, brouillon: true }, { take: 5, brouillon: true }], rejetees: [2] }, lire, tarif);
    const c = compteurProjet([v]);
    expect(c.prises).toBe(4); // la prise 4 échouée n'est pas facturée
    expect(c.credits).toBe(65 + 65 + 15 + 15);
    expect(c.ecartees).toEqual({ credits: 65 + 15 + 15, secondes: expect.any(Number), prises: 3 });
    expect(c.brouillons).toBe(2);
  });
  it('sans prise retenue, seuls rejetées et brouillons comptent comme écartées', () => {
    const c = compteurProjet([prisesDuPlan({ candidats: [1, 2], rejetees: [2] }, lire, tarif)]);
    expect(c.ecartees.prises).toBe(1);
  });
  it('une prise inconnue est ignorée', () => {
    expect(prisesDuPlan({ take: 99 }, lire, tarif)).toEqual([]);
  });
  it('brouillon : FastH3 basse résolution sans références, ref2va basse résolution avec références', () => {
    const rapide = { videoModel: 'h3-fast', checkpoint: 'fast.safetensors', steps: 8 };
    const sans = corpsBrouillonDe({ videoModel: 'h3-max', width: 1344, height: 768, prompt: 'P', seed: 1 }, 42, rapide);
    expect(sans).toMatchObject({ videoModel: 'h3-fast', width: 832, height: 480, seed: 42, prompt: 'P', brouillon: true });
    const avec = corpsBrouillonDe({ videoModel: 'h3-max', width: 768, height: 1344, prompt: 'P', refImages: ['asset:a'], refMode: true }, 7, rapide);
    expect(avec).toMatchObject({ videoModel: 'h3-max', width: 448, height: 768, refImages: ['asset:a'], seed: 7 });
  });
  it('une prise ajoutée ne porte jamais les marques du film (assemblage, réservation)', () => {
    const base = { videoModel: 'h3-max', width: 1344, height: 768, prompt: 'P', refImages: ['a'], nexoraFilm: 373, nexoraPlan: 0, nexoraCredits: { reservationId: 'r' }, promptSource: 'llm' };
    const b = corpsBrouillonDe(base, 1, {});
    expect(b.nexoraFilm).toBeUndefined(); expect(b.nexoraPlan).toBeUndefined(); expect(b.nexoraCredits).toBeUndefined();
    const f = corpsFinalDe({ ...b, width: 768, height: 448, seed: 5 }, base);
    expect(f.nexoraFilm).toBeUndefined();
  });
  it('finale : recette cinéma du plan avec la graine du brouillon ; un brouillon à références garde son corps', () => {
    const cinema = { videoModel: 'h3-max', width: 1344, height: 768, prompt: 'FINAL', seed: 1, steps: 8 };
    expect(corpsFinalDe({ videoModel: 'h3-fast', width: 832, height: 480, prompt: 'P', seed: 42 }, cinema)).toMatchObject({ videoModel: 'h3-max', width: 1344, prompt: 'P', seed: 42 });
    expect(corpsFinalDe({ videoModel: 'h3-max', width: 832, height: 480, refImages: ['asset:a'], seed: 9, prompt: 'R' }, cinema)).toMatchObject({ width: 1344, height: 768, refImages: ['asset:a'], seed: 9, prompt: 'R' });
  });
});
