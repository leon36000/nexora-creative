import { describe, expect, it } from 'vitest';
import type { ClientLlm } from './llm.js';
import { validerPromptH3 } from './promptH3.js';
import { lireFiche, realiser, verifierFiche, versH3, versImage } from './realisateur.js';
import { reecrireH3 } from './reecritureH3.js';
import { MOTS_RENDU_INTERDITS, NEGATIF_LIVE_ACTION, STYLE_LIVE_ACTION, motsRenduInterdits } from './liveAction.js';

const FICHE = {
  compris: 'Une pub de cabane à sucre en trois plans.',
  famille: 'pub',
  hypotheses: ['Printemps, plein jour'],
  style: STYLE_LIVE_ACTION,
  personnages: [
    { id: 'P1', court: 'the grandmother in a red plaid shirt', apparence: 'woman in her late sixties, silver bun, red plaid flannel shirt', voix: 'warm, cheerful low female voice' },
    { id: 'P2', court: 'the little boy in a blue knit hat', apparence: 'six-year-old boy, rosy cheeks, blue knit hat' },
  ],
  plans: [
    { debut: 0, cadrage: 'wide', texte: 'a low-angle wide shot on a 24mm Cooke S4 lens frames [P1] in the foreground pouring golden maple syrup over a trench of snow while [P2] watches, the camera pushes in with small amplitude under sunlight.' },
    { debut: 4, cadrage: 'close-up', texte: 'a tight close-up on an 85mm Cooke S4 lens of the taffy as [P2] rolls it onto a wooden stick and laughs in daylight.' },
    { debut: 8, cadrage: 'medium', texte: 'a medium shot on a 35mm Cooke S4 lens as [P1] turns to camera, sunlight on her flannel shirt. [R1] She smiles.' },
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
  it.each(MOTS_RENDU_INTERDITS)('fait réparer le déclencheur de synthèse %s', (mot) => {
    const f = lireFiche({ ...FICHE, style: `${STYLE_LIVE_ACTION}, ${mot}` });
    expect(verifierFiche(f, ENTREE).join(' ')).toContain('forbidden visual word');
  });

  it.each(['un dragon noir y passe devant la tour pis y se pose', 'a black dragon flies past the tower then lands'])('comprend FR/EN et garde la sortie H3 anglaise : %s', async (intention) => {
    const r = await realiser({ ...ENTREE, intention }, faux([JSON.stringify(FICHE)]));
    expect(motsRenduInterdits(r.prompt)).toEqual([]);
    expect(r.prompt).toContain('ARRI Alexa 35');
    expect(r.prompt).toContain('Cooke S4 50mm');
    expect(r.prompt).toContain(NEGATIF_LIVE_ACTION);
    expect(r.prompt).not.toContain(intention);
  });

  it('demande les explications en anglais quand la personne choisit en, sans traduire le prompt technique H3', async () => {
    let demandeLlm = '';
    const fiche = {
      ...FICHE,
      compris: 'A family maple-syrup ad with three clear shots.',
      hypotheses: ['Bright spring daylight.'],
      variantes: ['A lantern-lit evening version.', 'A hand-drawn 2D version.', 'An aerial view of the sugar shack.'],
    };
    const llm: ClientLlm = { async completer(_role, messages) {
      const contenu = messages[1].content;
      demandeLlm = typeof contenu === 'string' ? contenu : contenu.map((partie) => partie.type === 'text' ? partie.text : '').join('');
      return JSON.stringify(fiche);
    } };
    const entree = { ...ENTREE, langueClient: 'en' as const, dialogues: [{ texte: 'Come enjoy maple taffy with us!', langue: 'English' }] };
    const r = await realiser(entree, llm);
    expect(JSON.parse(demandeLlm)).toMatchObject({ langue_client: 'en' });
    expect(r.fiche.compris).toBe('A family maple-syrup ad with three clear shots.');
    expect(r.prompt).toContain('a low-angle wide shot on a 24mm Cooke S4 lens');
    expect(r.prompt).not.toContain('A family maple-syrup ad');
  });

  it('répare un nom protégé et ne réintroduit pas les consignes brutes de l’interface', async () => {
    const f = { ...FICHE, plans: [{ ...FICHE.plans[0], texte: 'a medium shot on a 50mm Cooke S4 lens of a Jedi lifting a lightsaber, then striking under practical rain-soaked street lamps.' }] };
    const e = { ...ENTREE, intention: 'un Jedi comme Star Wars', consignes: ['epic cinematic Unreal 8K'], dialogues: [] };
    const llm = faux([JSON.stringify(f), JSON.stringify({ ...f, plans: [{ ...f.plans[0], texte: 'a medium shot on a 50mm Cooke S4 lens of an original hooded knight lifting an energy blade, then striking under practical rain-soaked street lamps.' }] })]);
    const r = await realiser(e, llm);
    expect(llm.appels).toBe(2);
    expect(r.prompt).not.toMatch(/Jedi|lightsaber|Star Wars|Unreal|8K|epic|cinematic/i);
    expect(r.prompt).toContain('lifting an energy blade, then striking');
  });

  it('refuse une recette manquante même après la dernière réparation', async () => {
    const f = { ...FICHE, style: 'Live-action, cinematic' };
    await expect(realiser(ENTREE, faux([JSON.stringify(f)]), 1)).rejects.toThrow(/forbidden visual word/);
  });

  it('refuse le spectacle trop éloigné et sans repère d’échelle', () => {
    const f = lireFiche({ ...FICHE, famille: 'vfx', plans: [{ debut: 0, texte: 'a distant dragon flies then lands far away.' }] });
    const erreurs = verifierFiche(f, { ...ENTREE, dialogues: [] }).join(' ');
    expect(erreurs).toContain('keep the hero large');
    expect(erreurs).toContain('scale cue');
  });

  it('préserve une Terre réelle, le soleil dur et un dessin spatial original, refuse les navires militaires', () => {
    const e = { ...ENTREE, intention: 'film promo photoréaliste : bataille spatiale en orbite de la Terre', dialogues: [] };
    const base = { ...FICHE, famille: 'vfx', plans: [{ debut: 0, texte: 'a medium shot on a 50mm Cooke S4 lens of an original spacecraft in the foreground, crew windows give scale; it banks then passes real Earth with curved blue limb and clouds, under hard direct sunlight and deep black shadows, scratched metal catching the sun.' }] };
    expect(verifierFiche(lireFiche(base), e)).toEqual([]);
    const mauvaise = lireFiche({ ...base, plans: [{ debut: 0, texte: base.plans[0].texte.replace('original spacecraft', 'battleship').replace('hard direct sunlight', 'soft light') }] });
    expect(verifierFiche(mauvaise, e).join(' ')).toMatch(/hard direct sunlight/);
    expect(verifierFiche(mauvaise, e).join(' ')).toMatch(/military/);
  });

  it('respecte une animation demandée dans une pub et ne lui ajoute pas le négatif photo', async () => {
    const animation = {
      ...FICHE,
      famille: 'pub',
      style: '2D hand-drawn animation with textured watercolor backgrounds',
      personnages: [],
      plans: [{ debut: 0, cadrage: 'medium', texte: 'a medium animated view of a steaming bowl of poutine as a fork lifts the cheese curds, then the owner laughs; warm colors and a lively hand-drawn line keep the food readable.' }],
      variantes: ['Nighttime stop-motion at the counter', 'A playful 3D animation', 'A paper-cutout short'],
    };
    const e = { ...ENTREE, intention: 'pub de poutine en dessin animé 2D', dialogues: [], dureeS: 124 / 24, consignes: ['Visual style: 2D cel animation'] };
    let messages: any[] = [];
    const llm: ClientLlm = { async completer(_role, m) { messages = m; return JSON.stringify(animation); } };
    const r = await realiser(e, llm);
    expect(verifierFiche(r.fiche, e)).toEqual([]);
    expect(r.prompt).toContain('2D hand-drawn animation');
    expect(r.prompt).not.toContain(NEGATIF_LIVE_ACTION);
    expect(messages[0].content).toContain('preserve 2D/3D animation, anime, cartoons, illustration, stop-motion, claymation');
  });

  it.each(['an anime scene for a coffee ad', 'an anime battle in a coffee ad'])('does not apply the photo recipe to an anime medium: %s', async (intention) => {
    const animation = {
      ...FICHE,
      style: '2D hand-drawn anime with inked outlines and painted backgrounds',
    };
    const r = await realiser({ ...ENTREE, intention, dialogues: [] }, faux([JSON.stringify(animation)]));
    expect(r.prompt).toContain('hand-drawn anime');
    expect(r.prompt).not.toContain(STYLE_LIVE_ACTION);
    expect(r.prompt).not.toContain(NEGATIF_LIVE_ACTION);
  });

  it.each(['t2va', 'i2va', 'fl2va', 'l2va', 'ref2va'] as const)('compile %s avec chronologie et dialogues intacts', (mode) => {
    const references = mode === 'ref2va' ? { sujets: [], composition: 1 } : undefined;
    const e = { ...ENTREE, mode, references };
    const prompt = versH3(lireFiche(FICHE), e);
    expect(validerPromptH3(prompt, { ...e, dialogues: ENTREE.dialogues.map((d) => d.texte) })).toEqual([]);
    expect(prompt).toContain('At 00:04.000');
    expect(prompt).toContain('<d>[French] Venez sucrer le bec en famille!</d>');
    expect(motsRenduInterdits(prompt)).toEqual([]);
    if (mode === 'ref2va') {
      expect(prompt).toMatch(/^subject_definitions:/);
      expect(prompt).toContain('<Picture 1>');
      expect(prompt).toContain('detailed_description:');
    }
  });

  it('garde le dialogue du client verbatim même quand il contient un qualificatif interdit au visuel', () => {
    const e = { ...ENTREE, dialogues: [{ texte: 'That was epic!', langue: 'English' }] };
    const p = versH3(lireFiche(FICHE), e);
    expect(p).toContain('<d>[English] That was epic!</d>');
    expect(motsRenduInterdits(p)).toEqual([]);
  });
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
    expect(t).toMatch(/^Live-action footage.*a single still frame:/);
    expect(t).not.toMatch(/\[P\d\]|\[R\d\]/);
    expect(t).toMatch(/No text, no logo/);
  });
});
