import { describe, expect, it } from 'vitest';
import { BRIEFS } from '../bench/briefs.js';
import { type DepsAgent, nouvelleSession, tourProducteur, OUTILS_PRODUCTEUR } from '../agent.js';
import type { ClientLlm, ReponseOutils } from '../llm.js';
import type { AnalyseMedia } from './analyse.js';
import { briefDepuisAnalyses, motsDepuisSilences } from './outils.js';

const b = BRIEFS.find((x) => x.id === 'pub-b')!;
const analyses: Record<string, AnalyseMedia> = {
  ...Object.fromEntries(b.clips.map((c) => [c.id, { empreinte: c.id, duree_s: c.duree_s, a_video: true, a_audio: false, coupes_s: c.coupes_s ?? [], silences_s: [], energie: [], bpm: 0, battues_s: [], onsets_s: [] }])),
  musique: { empreinte: 'mu', duree_s: b.musique!.duree_s, a_video: false, a_audio: true, coupes_s: [], silences_s: [], energie: b.musique!.energie, bpm: b.musique!.bpm, battues_s: b.musique!.battues_s, onsets_s: [] },
};
const appel = (nom: string, args: Record<string, unknown>, id: string): ReponseOutils => ({ texte: '', appels: [{ id, nom, arguments: args }], jetons: 10 });
const fin = (t = 'Fait.'): ReponseOutils => ({ texte: t, appels: [], jetons: 5 });
function llmQuiRejoue(tours: ReponseOutils[]): ClientLlm & { vus: string[] } {
  let i = 0; const f = { vus: [] as string[], completer: async () => '{}', completerAvecOutils: async (_r: unknown, m: any[]) => { f.vus.push(JSON.stringify(m.at(-1))); return tours[Math.min(i++, tours.length - 1)]; } };
  return f;
}
const demande = { brief: b.enonce, genre: 'pub', format: '9:16', duree_cible_s: 20, medias: b.clips.map((c) => c.id), musique: 'musique', textes: b.textes_imposes };
const deps = (llm: ClientLlm, extra: Partial<DepsAgent> = {}): DepsAgent => ({
  llm, devis: () => ({ credits: 0, secondesGpu: 0, minutes: 1, rendus: 0, plans: 0, musique: false, candidats: 1 }), plafond: { credits: 500, secondes: 1800 }, outils: {},
  montage: { analyser: async (ids) => Object.fromEntries(ids.map((i) => { if (!analyses[i]) throw new Error(`média ${i} hors projet`); return [i, analyses[i]]; })), plafondCredits: 100 }, ...extra,
});

describe('outils de montage du Producteur', () => {
  it('exposent exactement analyze_media, plan_edit, critique, revise en plus des outils de production', () => {
    const noms = OUTILS_PRODUCTEUR.map((o) => o.nom);
    for (const n of ['analyze_media', 'plan_edit', 'critique', 'revise']) expect(noms).toContain(n);
    expect(OUTILS_PRODUCTEUR.find((o) => o.nom === 'plan_edit')!.parametres).toHaveProperty('properties.duree_cible_s');
  });
  it('analyse → plan (repli sur montage_auto si le modèle ne livre rien de valide) → critique → révision gardée seulement sans perte', async () => {
    const llm = llmQuiRejoue([
      appel('analyze_media', { medias: ['m1', 'musique'] }, 'a'),
      appel('plan_edit', demande, 'b'),
      appel('critique', {}, 'c'),
      appel('revise', { rustines: [{ op: 'regler_audio', cible_lufs: -20 }] }, 'd'), // fait baisser le score : refusée
      appel('revise', { rustines: [{ op: 'regler_plan', id: 'p1', entree_f: 999999 }] }, 'e'), // invalide : refusée
      fin('Montage prêt.'),
    ]);
    const s = await tourProducteur(nouvelleSession(), 'monte ma pub', deps(llm, { maxEtapes: 8 }));
    expect(s.montage?.source).toBe('repli');
    expect(s.montage?.tours).toBe(1);
    expect(s.montage?.plan.audio.cible_lufs).toBe(-14);
    const vus = llm.vus.join('\n');
    expect(vus).toContain('tempo'); expect(vus).toContain('score'); expect(vus).toContain('rustines refusées'); expect(vus).toContain('invalide');
    expect(s.fil.at(-1)?.texte).toBe('Montage prêt.');
  });
  it('plafonne les tours critique à 2 et refuse critique/revise sans montage', async () => {
    const llm = llmQuiRejoue([appel('critique', {}, 'x'), appel('plan_edit', demande, 'a'), appel('critique', {}, 'b'), appel('critique', {}, 'c'), appel('critique', {}, 'd'), fin()]);
    const s = await tourProducteur(nouvelleSession(), 'x', deps(llm, { maxEtapes: 8 }));
    expect(s.montage?.tours).toBe(2);
    expect(llm.vus.join('\n')).toContain('aucun montage en cours');
    expect(llm.vus.join('\n')).toContain('2 tours critique/revise au plus');
  });
  it('refuse les médias hors projet et les outils sans accès aux médias', async () => {
    const s = await tourProducteur(nouvelleSession(), 'x', deps(llmQuiRejoue([appel('analyze_media', { medias: ['secret'] }, 'a'), fin()])));
    expect(s.messages.some((m) => m.role === 'tool' && m.content.includes('hors projet'))).toBe(true);
    const sans = await tourProducteur(nouvelleSession(), 'x', deps(llmQuiRejoue([appel('plan_edit', demande, 'a'), fin()]), { montage: undefined }));
    expect(sans.messages.some((m) => m.role === 'tool' && m.content.includes('indisponibles'))).toBe(true);
  });
  it('brief depuis les analyses : mots de la voix = complément des silences', () => {
    expect(motsDepuisSilences(10, [[2, 3], [6, 7]])).toEqual([[0, 2], [3, 6], [7, 10]]);
    const br = briefDepuisAnalyses({ brief: 'x', genre: 'pub', format: '9:16', duree_cible_s: 20, medias: ['m1'], musique: 'musique' }, analyses);
    expect(br.clips[0].id).toBe('m1'); expect(br.musique?.bpm).toBe(b.musique!.bpm);
    expect(() => briefDepuisAnalyses({ brief: 'x', genre: 'pub', format: '9:16', duree_cible_s: 20, medias: ['musique'] }, analyses)).toThrow(/pas une vidéo/);
  });
});
