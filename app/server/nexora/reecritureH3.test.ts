import { describe, expect, it } from 'vitest';
import type { ClientLlm, MessageLlm } from './llm.js';
import { reecrireH3Classique, remarquesParasites, texteEcranNonDemande } from './reecritureH3.js';

const bon = `integrated_multimodal_description: [Shot 1] Live-action, cinematic, a wide shot of a red car. The camera performs an arc shot at slow speed around it.

overall_soundscape: Waves and wind.

non_diegetic_music: N/A`;

function faux(reponses: string[]): ClientLlm & { appels: MessageLlm[][] } {
  const appels: MessageLlm[][] = [];
  return {
    appels,
    async completer(_role, messages) {
      appels.push([...messages]);
      const r = reponses.shift();
      if (r === undefined) throw new Error('plus de réponse');
      return r;
    },
  };
}

const entree = { intention: 'ma voiture rouge au bord de la mer, la caméra tourne autour', mode: 't2va' as const, dureeS: 5.17 };

describe('réécrivain H3', () => {
  it('donne le guide officiel au LLM et rend un prompt conforme', async () => {
    const llm = faux([JSON.stringify({ prompt: bon })]);
    const r = await reecrireH3Classique(entree, llm);
    expect(r.prompt).toBe(bon);
    expect(r.source).toBe('llm');
    expect(r.tentatives).toBe(1);
    expect(llm.appels[0][0].content).toMatch(/Arc Shot/);
    expect(llm.appels[0][1].content).toMatch(/ma voiture rouge/);
  });

  it('renvoie les erreurs du validateur au LLM pour réparation', async () => {
    const llm = faux([JSON.stringify({ prompt: 'n’importe quoi' }), JSON.stringify({ prompt: bon })]);
    const r = await reecrireH3Classique(entree, llm);
    expect(r.tentatives).toBe(2);
    expect(r.prompt).toBe(bon);
    expect(llm.appels[1].at(-1)?.content).toMatch(/overall_soundscape/);
  });

  it('retombe sur un prompt minimal conforme si le LLM échoue ou est absent', async () => {
    const r1 = await reecrireH3Classique(entree, faux(['pas du json', 'toujours pas', 'non']));
    expect(r1.source).toBe('repli');
    expect(r1.prompt).toMatch(/^integrated_multimodal_description: \[Shot 1\]/);
    const r2 = await reecrireH3Classique(entree, null);
    expect(r2.source).toBe('repli');
    expect(r2.erreurs).toEqual([]);
  });

  it('protège les répliques de l’utilisateur', async () => {
    const llm = faux([JSON.stringify({ prompt: bon }), JSON.stringify({ prompt: bon }), JSON.stringify({ prompt: bon })]);
    const r = await reecrireH3Classique({ ...entree, dialogues: [{ texte: 'On y va.', langue: 'French' }] }, llm);
    expect(r.source).toBe('repli');
    expect(r.prompt).toContain('<d>[French] On y va.</d>');
  });
});

describe('texte à l’écran non demandé', () => {
  const avecEnseigne = bon.replace('around it.', 'around it. A neon sign reading "Ruelle Néon" glows on the wall.');
  it('repère un texte affiché que la personne n’a pas demandé', () => {
    expect(texteEcranNonDemande(avecEnseigne, 'une moto dans une ruelle néon')).toEqual(['Ruelle Néon']);
    expect(texteEcranNonDemande(avecEnseigne, 'une enseigne « Ruelle Néon » au mur')).toEqual([]);
    expect(texteEcranNonDemande(bon, 'une voiture')).toEqual([]);
  });

  it('fait réécrire le prompt pour retirer ce texte', async () => {
    const llm = faux([JSON.stringify({ prompt: avecEnseigne }), JSON.stringify({ prompt: bon })]);
    const r = await reecrireH3Classique({ ...entree, intention: 'une moto dans une ruelle néon' }, llm);
    expect(r.prompt).toBe(bon);
    expect(llm.appels[1].at(-1)?.content).toMatch(/Ruelle Néon/);
  });
});


describe('remarques parasites', () => {
  it('repère une note adressée au modèle et la fait retirer', async () => {
    const parasite = bon.replace('a red car.', 'a red car (S1 is not applicable; she does not speak).');
    expect(remarquesParasites(parasite)).toHaveLength(1);
    expect(remarquesParasites(bon)).toEqual([]);
    const llm = faux([JSON.stringify({ prompt: parasite }), JSON.stringify({ prompt: bon })]);
    const r = await reecrireH3Classique(entree, llm);
    expect(r.prompt).toBe(bon);
    expect(r.tentatives).toBe(2);
  });
});
