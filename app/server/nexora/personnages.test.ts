import { describe, expect, it } from 'vitest';
import { convertirEnPromptRef, decoupeFiche, promptFiche, validerPromptRef } from './personnages.js';

const T2VA = `integrated_multimodal_description: [Shot 1] Cinematic. Mara walks along a rainy street, camera tracking at shoulder height. (S1) says <d>[French] Bonsoir.</d> [Shot 2] At 00:03.000, a close-up of Mara smiling under a streetlight.

overall_soundscape: Rain on asphalt.

non_diegetic_music: N/A`;

describe('personnages @ : fiche et prompt Ref2VA', () => {
  it('la fiche demande un fond gris uni, un corps entier et un gros plan, sans texte', () => {
    const p = promptFiche('a woman in her thirties, short red hair, green coat');
    expect(p).toMatch(/neutral grey/);
    expect(p).toMatch(/full body/);
    expect(p).toMatch(/close-up/);
    expect(p).toMatch(/No text/);
    expect(p).toContain('short red hair');
  });
  it('découpe la fiche en deux moitiés de taille paire', () => {
    const d = decoupeFiche(1792, 1024);
    expect(d.corps).toEqual([0, 0, 896, 1024]);
    expect(d.visage).toEqual([896, 0, 896, 1024]);
  });
  it('convertit un prompt T2VA valide en six champs, le nom devient <Subject 1>', () => {
    const p = convertirEnPromptRef(T2VA, [{ nom: 'Mara', apparence: 'a woman with short red hair and a green coat', images: 2 }]);
    expect(validerPromptRef(p, 1, 2)).toEqual([]);
    expect(p).toContain('<Subject 1> is Mara, a woman with short red hair and a green coat, shown in <Picture 1> and <Picture 2> (full body and close-up).');
    expect(p).not.toContain('Mara, A woman');
    expect(p).toContain('[Shot 1] Cinematic. <Subject 1> walks');
    expect(p).toContain('a close-up of <Subject 1> smiling');
    expect(p).toContain('(appears in [Shot 1], [Shot 2]): fully_preserved');
    expect(p).toContain('<d>[French] Bonsoir.</d>');
    expect(p).not.toContain('integrated_multimodal_description');
  });
  it('un personnage non cité est ajouté au premier plan ; deux personnages numérotent leurs images', () => {
    const p = convertirEnPromptRef(T2VA, [
      { nom: 'Mara', apparence: 'red hair', images: 2 },
      { nom: 'Theo', apparence: 'a tall man in a grey suit', images: 2 },
    ]);
    expect(p).toContain('<Subject 2> is Theo, a tall man in a grey suit, shown in <Picture 3> and <Picture 4>');
    expect(p).toContain('[Shot 1] <Subject 2>, a tall man in a grey suit, is in frame.');
    expect(validerPromptRef(p, 2, 4)).toEqual([]);
    expect(validerPromptRef(p, 2, 3)).toContain('<Picture 4> dépasse les 3 images fournies');
  });
  it('« montre-moi » : une image de composition devient un <Picture N> d’ancrage de plan, avec ou sans personnage', () => {
    const p = convertirEnPromptRef(T2VA, [{ nom: 'Mara', apparence: 'Red hair', images: 2 }], { composition: 1 });
    expect(p).toContain('<Picture 3> is a composition reference for [Shot 1], defining its viewpoint, framing and subject placement.');
    expect(p).toContain('<Picture 3> ([Shot 1] composition): weak_reference');
    expect(validerPromptRef(p, 1, 3)).toEqual([]);
    const seul = convertirEnPromptRef(T2VA, [], { composition: 1 });
    expect(seul).toContain('<Picture 1> is a composition reference');
    expect(seul).toContain('following the composition of <Picture 1>');
  });
  it('un prompt qui n’a pas la forme T2VA est rendu tel quel', () => {
    expect(convertirEnPromptRef('n’importe quoi', [{ nom: 'Mara', apparence: '', images: 1 }])).toBe('n’importe quoi');
  });
});
