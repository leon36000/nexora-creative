import { describe, expect, it } from 'vitest';
import type { ClientLlm } from './llm.js';
import { validerPromptH3 } from './promptH3.js';
import { lireFiche, realiser, verifierFiche, versH3, versImage } from './realisateur.js';
import { reecrireH3 } from './reecritureH3.js';

const FICHE = {
  compris: 'Une pub de cabane à sucre en trois plans.',
  famille: 'pub',
  hypotheses: ['Printemps, plein jour'],
  style: 'Live-action, cinematic, warm spring grade',
  personnages: [
    { id: 'P1', court: 'the grandmother in a red plaid shirt', apparence: 'woman in her late sixties, silver bun, red plaid flannel shirt', voix: 'warm, cheerful low female voice' },
    { id: 'P2', court: 'the little boy in a blue knit hat', apparence: 'six-year-old boy, rosy cheeks, blue knit hat' },
  ],
  plans: [
    { debut: 0, cadrage: 'wide', texte: 'a low-angle wide shot on a 24mm lens frames [P1] pouring golden maple syrup over a trench of snow while [P2] watches, the camera pushes in with small amplitude.' },
    { debut: 4, cadrage: 'close-up', texte: 'a tight close-up of the taffy, 85mm, as [P2] rolls it onto a wooden stick and laughs.' },
    { debut: 8, cadrage: 'medium', texte: 'a medium shot on a 35mm lens as [P1] turns to camera. [R1] She smiles.' },
  ],
  locuteurs: { R1: 'P1' },
  ambiance: 'Birdsong, crackling fire, crunching snow.',
  musique: 'Upbeat folk fiddle and acoustic guitar.',
  texteEcran: [],
  variantes: ['Version nocturne aux lanternes', 'Version 2D animée', 'Version drone au-dessus de l’érablière'],
};
const ENTREE = { intention: 'cabane a sucre familiale, tire sur la neige', mode: 't2va' as const, dureeS: 362 / 24, dialogues: [{ texte: 'Venez sucrer le bec en famille!', langue: 'French' }] };

const faux = (reponses: string[]): ClientLlm & { appels: number } => {
  const c = { appels: 0, async completer() { return reponses[Math.min(c.appels++, reponses.length - 1)]; } };
  return c;
};

describe('réalisateur', () => {
  it('compile une fiche en prompt H3 conforme au guide, réplique mot pour mot', () => {
    const f = lireFiche(FICHE);
    expect(verifierFiche(f, ENTREE)).toEqual([]);
    const p = versH3(f, ENTREE);
    expect(validerPromptH3(p, { mode: 't2va', dureeS: ENTREE.dureeS, dialogues: ['Venez sucrer le bec en famille!'] })).toEqual([]);
    expect(p).toContain('The grandmother in a red plaid shirt (S1) says in a warm, cheerful low female voice: <d>[French] Venez sucrer le bec en famille!</d>');
    expect(p).toContain('[Shot 2] At 00:04.000, the camera cuts to a tight close-up');
    expect(p).not.toMatch(/\[P\d\]|\[R\d\]/);
  });

  it('décrit un personnage en entier à sa première apparition seulement', () => {
    const p = versH3(lireFiche(FICHE), ENTREE);
    expect(p.match(/silver bun/g)).toHaveLength(1);
    expect(p.match(/little boy in a blue knit hat/g)!.length).toBeGreaterThanOrEqual(2);
  });

  it('refuse les plans trop courts, les marques, le texte non demandé et le français', () => {
    const f = lireFiche({ ...FICHE, plans: [{ debut: 0, texte: 'a wide shot of a lightsaber duel' }, { debut: 1, texte: 'a sign reading "OPEN" glows' }] });
    const e = verifierFiche(f, { ...ENTREE, dialogues: [] });
    expect(e.join(' ')).toMatch(/at least 2.5 s/);
    expect(e.join(' ')).toMatch(/lightsaber/);
    expect(e.join(' ')).toMatch(/"OPEN" was not requested/);
    const fr = lireFiche({ ...FICHE, plans: [{ debut: 0, texte: 'un plan large de la cabane avec la lumière du soleil sur la neige et des enfants dans la cour' }] });
    expect(verifierFiche(fr, { ...ENTREE, dialogues: [] }).join(' ')).toMatch(/English/);
  });

  it('répare une fiche refusée puis rend le prompt (deux appels)', async () => {
    const mauvaise = JSON.stringify({ ...FICHE, plans: [FICHE.plans[0]] }); // [R1] absent
    const llm = faux([mauvaise, JSON.stringify(FICHE)]);
    const r = await realiser(ENTREE, llm);
    expect(llm.appels).toBe(2);
    expect(r.historique[0].join(' ')).toMatch(/\[R1\]/);
    expect(r.fiche.compris).toMatch(/cabane/);
  });

  it('reecrireH3 retombe sur le réécrivain classique si le réalisateur échoue, et NEXORA_REALISATEUR=off le coupe', async () => {
    const r = await reecrireH3(ENTREE, faux(['pas du json']), 2);
    expect(r.fiche).toBeUndefined();
    expect(r.source).toBe('repli');
    const off = await reecrireH3(ENTREE, faux([JSON.stringify(FICHE)]), 1, { NEXORA_REALISATEUR: 'off' });
    expect(off.fiche).toBeUndefined();
  });

  it('donne aussi le dialecte image (plan clé Qwen) sans balise ni texte', () => {
    const t = versImage(lireFiche(FICHE), 1);
    expect(t).toMatch(/^Live-action, cinematic, warm spring grade, a single still frame:/);
    expect(t).not.toMatch(/\[P\d\]|\[R\d\]/);
    expect(t).toMatch(/No text, no logo/);
  });
});
