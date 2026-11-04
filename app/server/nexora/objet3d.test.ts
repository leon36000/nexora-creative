import { describe, expect, it } from 'vitest';
import {
  RECETTES_OBJET, TOURNETTE_JUGE, argsPlancheVues, decisionApresJuge, lireVerdictVues, prochaineEtapeTexte3D,
  promptReferenceObjet, recetteObjet, secondesObjet, secondesTexteVers3D,
} from './objet3d.js';
import { devisCredits, secondesGpuEstimees } from './credits.js';

describe('recettes 3D', () => {
  it('une recette par détail, routée comme les autres recettes du parc', () => {
    expect(recetteObjet('draft')).toBe('objet-apercu');
    expect(recetteObjet('quality')).toBe('objet-qualite');
    expect(Object.values(RECETTES_OBJET)).toEqual(['objet-apercu', 'objet-qualite', 'objet-multivue']);
  });
  it('temps GPU mesuré sur la GB10 : l’aperçu est bien plus court que la qualité', () => {
    expect(secondesObjet('draft')).toBeLessThan(60);
    expect(secondesObjet('quality')).toBeGreaterThan(secondesObjet('draft') * 3);
  });
  it('texte → 3D = image de référence + objet + tournette de contrôle', () => {
    expect(secondesTexteVers3D('draft')).toBeGreaterThan(secondesObjet('draft'));
  });
  it('le devis en crédits suit les secondes mesurées', () => {
    expect(secondesGpuEstimees({ kind: 'object', quality: 'draft' })).toBe(secondesObjet('draft'));
    expect(devisCredits({ kind: 'object', quality: 'quality' }, { creditsParSecondeGpu: 0.5 })).toBe(Math.ceil(secondesObjet('quality') * 0.5));
    // Les vidéos gardent leur calcul d'origine.
    expect(secondesGpuEstimees({ videoModel: 'h3-max', lengthFrames: 124, width: 1344, height: 768 })).toBe(129);
  });
});

describe('prompt de référence', () => {
  it('impose un seul objet, entier, sur fond neutre, sans texte', () => {
    const p = promptReferenceObjet('une chaise en bois');
    expect(p).toContain('une chaise en bois');
    expect(p.toLowerCase()).toMatch(/single object/);
    expect(p.toLowerCase()).toMatch(/plain white/);
    expect(p.toLowerCase()).toMatch(/no text/);
  });
  it('coupe une description trop longue', () => {
    expect(promptReferenceObjet('x'.repeat(5000)).length).toBeLessThan(1200);
  });
});

describe('juge sur 4 vues', () => {
  it('lit une note et des défauts', () => {
    const v = lireVerdictVues('{"note": 8, "defauts": ["dessous flou"], "raison": "Propre."}');
    expect(v).toEqual({ note: 8, defauts: ['dessous flou'], raison: 'Propre.' });
  });
  it('borne la note et tolère un bloc de code', () => {
    expect(lireVerdictVues('```json\n{"note": 42}\n```')?.note).toBe(10);
    expect(lireVerdictVues('{"note": -3}')?.note).toBe(0);
  });
  it('refuse une réponse sans note', () => {
    expect(lireVerdictVues('pas de json')).toBeNull();
    expect(lireVerdictVues('{"raison": "ok"}')).toBeNull();
  });
  it('relance une fois seulement quand la note est basse', () => {
    expect(decisionApresJuge(1, { note: 4, defauts: [], raison: '' })).toBe('relancer');
    expect(decisionApresJuge(2, { note: 4, defauts: [], raison: '' })).toBe('garder');
    expect(decisionApresJuge(1, { note: 7, defauts: [], raison: '' })).toBe('garder');
    expect(decisionApresJuge(1, null)).toBe('garder');
  });
  it('planche : quatre images de la tournette, une sur deux', () => {
    const a = argsPlancheVues('/t/m.glb.turntable.mp4', '/t/p.jpg', TOURNETTE_JUGE.images);
    const vf = a[a.indexOf('-vf') + 1];
    expect(vf).toContain('eq(n,0)+eq(n,2)+eq(n,4)+eq(n,6)');
    expect(vf).toContain('tile=2x2');
    expect(a[a.length - 1]).toBe('/t/p.jpg');
  });
});

describe('texte → 3D : prochaine étape', () => {
  const base = { phase: 'image' as const, essai: 1, notes: [] as { take: number; note: number }[], tentatives: [] as number[] };
  it('attend l’image tant qu’elle n’est pas prête', () => {
    expect(prochaineEtapeTexte3D(base, { image: 'running' })).toEqual({ action: 'attendre' });
  });
  it('lance l’objet quand l’image est prête', () => {
    expect(prochaineEtapeTexte3D(base, { image: 'done' })).toEqual({ action: 'lancer-objet', essai: 1 });
  });
  it('échoue proprement si l’image échoue', () => {
    expect(prochaineEtapeTexte3D(base, { image: 'failed' }).action).toBe('echec');
  });
  it('juge l’objet terminé, attend sinon', () => {
    const s = { ...base, phase: 'objet' as const, tentatives: [11] };
    expect(prochaineEtapeTexte3D(s, { image: 'done', objet: 'running' })).toEqual({ action: 'attendre' });
    expect(prochaineEtapeTexte3D(s, { image: 'done', objet: 'done' })).toEqual({ action: 'juger' });
  });
  it('une relance quand le juge est sévère, puis on garde la meilleure', () => {
    const s1 = { phase: 'jugement' as const, essai: 1, tentatives: [11], notes: [{ take: 11, note: 3 }] };
    expect(prochaineEtapeTexte3D(s1, { image: 'done' })).toEqual({ action: 'lancer-objet', essai: 2 });
    const s2 = { phase: 'jugement' as const, essai: 2, tentatives: [11, 12], notes: [{ take: 11, note: 5 }, { take: 12, note: 3 }] };
    expect(prochaineEtapeTexte3D(s2, { image: 'done' })).toEqual({ action: 'finir', retenu: 11 });
  });
  it('garde l’objet sans note quand le juge est absent', () => {
    const s = { phase: 'jugement' as const, essai: 1, tentatives: [11], notes: [] };
    expect(prochaineEtapeTexte3D(s, { image: 'done' })).toEqual({ action: 'finir', retenu: 11 });
  });
  it('un objet qui échoue : échec avec le motif', () => {
    const s = { ...base, phase: 'objet' as const, tentatives: [11] };
    expect(prochaineEtapeTexte3D(s, { image: 'done', objet: 'failed' }).action).toBe('echec');
  });
});

describe('Relief : vues et GIF', () => {
  it('quatre vues régulièrement espacées d’une tournette de n images', async () => {
    const { indicesQuatreVues, argsGif } = await import('./objet3d.js');
    expect(indicesQuatreVues(32)).toEqual([0, 8, 16, 24]);
    expect(indicesQuatreVues(8)).toEqual([0, 2, 4, 6]);
    expect(indicesQuatreVues(2)).toHaveLength(4);
    expect(argsGif('a.mp4', 'b.gif').slice(-1)[0]).toBe('b.gif');
    expect(argsGif('a.mp4', 'b.gif').join(' ')).toContain('palettegen');
  });
});
