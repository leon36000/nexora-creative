import { describe, expect, it } from 'vitest';
import type { ClientLlm } from './llm.js';
import { argsAssemblage, argsExport, intentionDuPlan, lireStoryboard, planifierFilm, storyboardPourMontage, storyboardPourRefaire } from './film.js';

const brut = {
  titre: 'La métamorphose',
  bible: { style: 'Live-action, cinematic, dusk, purple sky', personnages: [{ nom: 'Robot', description: 'silver giant robot with blue eyes' }], lieux: [{ nom: 'Parking', description: 'wet asphalt lot at dusk' }] },
  plans: [
    { resume: 'La voiture garée', description: 'A silver sports car parked on a wet lot', duree: 5, camera: 'slow push in' },
    { resume: 'La transformation', description: 'The car unfolds into a giant robot', duree: 10, camera: 'arc shot with large amplitude' },
    { resume: 'Le robot se dresse', description: 'The robot stands and its eyes ignite', duree: 7, camera: 'low-angle static shot' },
  ],
};

describe('storyboard du Director', () => {
  it('normalise les plans (durées 5 ou 10 s, textes nettoyés) et calcule la durée totale', () => {
    const s = lireStoryboard(brut, 20);
    expect(s.plans.map((p) => p.duree)).toEqual([5, 10, 5]);
    expect(s.dureeTotale).toBe(20);
    expect(s.titre).toBe('La métamorphose');
  });

  it('borne le nombre de plans et refuse un storyboard vide', () => {
    const beaucoup = { ...brut, plans: Array.from({ length: 20 }, (_, i) => ({ resume: `p${i}`, description: `d${i}`, duree: 5, camera: '' })) };
    expect(lireStoryboard(beaucoup, 60).plans.length).toBe(12);
    expect(() => lireStoryboard({ plans: [] }, 20)).toThrow();
    expect(() => lireStoryboard({ plans: [{ resume: '', description: '', duree: 5 }] }, 20)).toThrow();
  });

  it('porte la bible de continuité dans l’intention de chaque plan', () => {
    const s = lireStoryboard(brut, 20);
    const t = intentionDuPlan(s, 1);
    expect(t).toMatch(/Live-action, cinematic/);
    expect(t).toMatch(/silver giant robot/);
    expect(t).toMatch(/The car unfolds/);
    expect(t).toMatch(/arc shot/);
  });

  it('demande au LLM un storyboard et retombe sur un découpage simple sinon', async () => {
    const llm: ClientLlm = { completer: async () => JSON.stringify(brut) };
    const r = await planifierFilm({ intention: 'ma voiture devient un robot', dureeCible: 20 }, llm);
    expect(r.source).toBe('llm');
    expect(r.storyboard.plans).toHaveLength(3);
    const casse: ClientLlm = { completer: async () => 'non' };
    const r2 = await planifierFilm({ intention: 'ma voiture devient un robot', dureeCible: 20 }, casse);
    expect(r2.source).toBe('repli');
    expect(r2.storyboard.plans.length).toBeGreaterThanOrEqual(1);
    expect(r2.storyboard.dureeTotale).toBeGreaterThanOrEqual(15);
  });

  it('assemble les plans avec ffmpeg en une vidéo H.264 + AAC', () => {
    const a = argsAssemblage(['/a.mp4', '/b.mp4'], '/sortie.mp4', true);
    expect(a.join(' ')).toMatch(/concat=n=2:v=1:a=1/);
    expect(a).toContain('libx264');
    expect(a.at(-1)).toBe('/sortie.mp4');
    expect(argsAssemblage(['/a.mp4'], '/s.mp4', false).join(' ')).toMatch(/concat=n=1:v=1:a=0/);
  });

  it('lit l’enchaînement « suite » d’un plan sur le précédent, jamais sur le premier', () => {
    const s = lireStoryboard({ ...brut, plans: brut.plans.map((p, i) => ({ ...p, suite: i !== 1 })) }, 20);
    expect(s.plans.map((p) => !!p.suite)).toEqual([false, false, true]);
  });

  it('demande au réalisateur de marquer les plans qui prolongent le précédent', async () => {
    let consignes = '';
    const llm: ClientLlm = { completer: async (_r, m) => { consignes = m[0].content; return JSON.stringify(brut); } };
    await planifierFilm({ intention: 'x', dureeCible: 20 }, llm);
    expect(consignes).toMatch(/"suite"/);
  });
});

describe('refaire un seul plan d’un film', () => {
  const tourne = {
    ...lireStoryboard({ ...brut, plans: [...brut.plans, { resume: 'Fin', description: 'The robot walks away', duree: 5, camera: 'wide', suite: true }] }, 25),
  };
  tourne.plans = tourne.plans.map((p, i) => ({ ...p, take: 100 + i }));

  it('garde les prises des autres plans et vide celle du plan refait', () => {
    const r = storyboardPourRefaire(tourne, 0, {});
    expect(r.plans.map((p) => p.take)).toEqual([undefined, 101, 102, 103]);
  });

  it('refait aussi les plans enchaînés qui partaient de son image', () => {
    const r = storyboardPourRefaire(tourne, 2, { description: 'The robot kneels instead' });
    expect(r.plans.map((p) => p.take)).toEqual([100, 101, undefined, undefined]);
    expect(r.plans[2].description).toBe('The robot kneels instead');
  });

  it('refuse un numéro de plan inexistant', () => {
    expect(() => storyboardPourRefaire(tourne, 9, {})).toThrow();
  });
});

describe('montage sans nouveau rendu', () => {
  const sb = lireStoryboard(brut, 20);
  sb.plans = sb.plans.map((p, i) => ({ ...p, take: 200 + i }));

  it('réordonne et retire des plans en gardant leurs prises', () => {
    const m = storyboardPourMontage(sb, [2, 0]);
    expect(m.plans.map((p) => p.take)).toEqual([202, 200]);
    expect(m.dureeTotale).toBe(10);
    expect(m.plans.every((p) => !p.suite)).toBe(true);
  });

  it('refuse un ordre vide, en double ou hors du film', () => {
    expect(() => storyboardPourMontage(sb, [])).toThrow();
    expect(() => storyboardPourMontage(sb, [0, 0])).toThrow();
    expect(() => storyboardPourMontage(sb, [5])).toThrow();
  });

  it('assemble en fondu enchaîné image et son, aux bons décalages', () => {
    const a = argsAssemblage(['/a.mp4', '/b.mp4', '/c.mp4'], '/s.mp4', true, { transition: 'fondu', durees: [5, 5, 5], fondu: 0.5 }).join(' ');
    expect(a).toMatch(/xfade=transition=fade:duration=0.5:offset=4.5/);
    expect(a).toMatch(/xfade=transition=fade:duration=0.5:offset=9/);
    expect(a).toMatch(/acrossfade=d=0.5/);
  });

  it('exporte en ProRes 422 HQ pour les logiciels de montage', () => {
    const a = argsExport('/f.mp4', '/f.mov', 'prores').join(' ');
    expect(a).toMatch(/prores_ks/);
    expect(a).toMatch(/-profile:v 3/);
    expect(a).toMatch(/pcm_s16le/);
  });
});

