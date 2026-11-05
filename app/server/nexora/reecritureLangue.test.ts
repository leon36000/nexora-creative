import { expect, it } from 'vitest';
import { reecrireH3Classique } from './reecritureH3.js';
import { STYLE_LIVE_ACTION } from './liveAction.js';

it.each([
  ['French', 'English', 'On y va.'],
  ['English', 'French', 'Let us go.'],
] as const)('refuse la langue %s faussement étiquetée %s sans changer la réplique', async (attendue, erronee, texte) => {
  const prompt = `integrated_multimodal_description: [Shot 1] ${STYLE_LIVE_ACTION}, a wide shot of a red car. The camera performs an arc shot at slow speed around it. A character says: <d>[${erronee}] ${texte}</d>\n\noverall_soundscape: Waves and wind.\n\nnon_diegetic_music: N/A`;
  const llm = { completer: async () => JSON.stringify({ prompt }) };
  const r = await reecrireH3Classique({ intention: 'ma voiture rouge au bord de la mer, la caméra tourne autour', mode:'t2va', dureeS:5.17, dialogues:[{texte, langue:attendue}] }, llm, 1);
  expect(r.source).toBe('repli');
  expect(r.prompt).toContain(`<d>[${attendue}] ${texte}</d>`);
});

it.each([
  ['fr', 'English', 'Let’s go!'],
  ['en', 'French', 'Où vas-tu ?'],
] as const)('accepte une interface %s et une réplique explicitement %s', async (langueClient, langue, texte) => {
  const prompt = `integrated_multimodal_description: [Shot 1] ${STYLE_LIVE_ACTION}, a wide shot of a red car. The camera performs an arc shot at slow speed around it. A character says: <d>[${langue}] ${texte}</d>\n\noverall_soundscape: Waves and wind.\n\nnon_diegetic_music: N/A`;
  const llm = { completer: async () => JSON.stringify({ prompt }) };
  const r = await reecrireH3Classique({ intention: 'ma voiture rouge au bord de la mer, la caméra tourne autour', mode:'t2va', dureeS:5.17, langueClient, dialogues:[{texte, langue}] }, llm, 1);
  expect(r.source).toBe('llm'); expect(r.prompt).toContain(`<d>[${langue}] ${texte}</d>`);
});

it('refuse toute altération des accents et de la ponctuation', async () => {
  const prompt = `integrated_multimodal_description: [Shot 1] ${STYLE_LIVE_ACTION}, a wide shot of a red car. The camera performs an arc shot at slow speed around it. A character says: <d>[French] Ou vas-tu!</d>\n\noverall_soundscape: Waves and wind.\n\nnon_diegetic_music: N/A`;
  const r = await reecrireH3Classique({ intention:'ma voiture rouge au bord de la mer, la caméra tourne autour', mode:'t2va', dureeS:5.17, dialogues:[{texte:'Où vas-tu ?', langue:'French'}] }, {completer:async()=>JSON.stringify({prompt})}, 1);
  expect(r.source).toBe('repli'); expect(r.prompt).toContain('<d>[French] Où vas-tu ?</d>');
});

it('exige chaque paire langue et texte même pour deux textes identiques', async () => {
  const { validerPromptH3 } = await import('./promptH3.js');
  const prompt = 'integrated_multimodal_description: [Shot 1] <d>[French] Oui.</d>\n\noverall_soundscape: N/A\n\nnon_diegetic_music: N/A';
  const ctx = { mode:'t2va' as const, dureeS:5, dialogues:['Oui.','Oui.'], dialoguesAvecLangue:[{texte:'Oui.',langue:'French'},{texte:'Oui.',langue:'English'}] };
  expect(validerPromptH3(prompt,ctx).some(e=>e.includes('langue ou texte'))).toBe(true);
  const correct = prompt.replace('</d>','</d> <d>[English] Oui.</d>');
  expect(validerPromptH3(correct,ctx)).toEqual([]);
  expect(validerPromptH3(correct.replace('</d>','</d> <d>[French] Oui.</d>'),ctx).some(e=>e.includes('réplique en trop'))).toBe(true);
});

it('refuse une réplique supplémentaire distincte si la liste est explicite', async () => {
  const { validerPromptH3 } = await import('./promptH3.js');
  const prompt = 'integrated_multimodal_description: [Shot 1] <d>[French] Où vas-tu ?</d> <d>[English] Invented line.</d>\n\noverall_soundscape: N/A\n\nnon_diegetic_music: N/A';
  const ctx = { mode:'t2va' as const, dureeS:5, dialogues:['Où vas-tu ?'], dialoguesAvecLangue:[{texte:'Où vas-tu ?',langue:'French'}] };
  expect(validerPromptH3(prompt,ctx).some(e=>e.includes('réplique en trop'))).toBe(true);
  expect(validerPromptH3(prompt.replace(' <d>[English] Invented line.</d>',''),ctx)).toEqual([]);
});

it('une liste explicite vide interdit toute réplique, le contexte historique reste inchangé', async () => {
  const { validerPromptH3 } = await import('./promptH3.js');
  const prompt = 'integrated_multimodal_description: [Shot 1] <d>[English] Hello!</d>\n\noverall_soundscape: N/A\n\nnon_diegetic_music: N/A';
  expect(validerPromptH3(prompt,{mode:'t2va',dureeS:5,dialoguesAvecLangue:[]}).some(e=>e.includes('réplique en trop'))).toBe(true);
  expect(validerPromptH3(prompt,{mode:'t2va',dureeS:5})).toEqual([]);
});

it('refuse les balises de réplique sans langue ou non fermées si la liste est explicite', async () => {
  const { validerPromptH3 } = await import('./promptH3.js');
  const envelopper = (bloc: string) => `integrated_multimodal_description: [Shot 1] ${bloc}\n\noverall_soundscape: N/A\n\nnon_diegetic_music: N/A`;
  for (const bloc of ['<d>Une réplique sans langue</d>', '<d>[French] Non fermé', '</d>', '<d>[French] Bonjour <d>[English] Hello</d></d>']) {
    expect(validerPromptH3(envelopper(bloc),{mode:'t2va',dureeS:5,dialoguesAvecLangue:[]}).some(e=>e.includes('balises de réplique mal formées'))).toBe(true);
  }
});
