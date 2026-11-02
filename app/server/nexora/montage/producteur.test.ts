import { describe, expect, it } from 'vitest';
import type { ClientLlm } from '../llm.js';
import type { AnalyseMedia } from './analyse.js';
import { validerEditPlan } from './editplan.js';
import { ameliorerMontage, briefDuFilm, monterEnCode, vueMetriques } from './producteur.js';

const video = (d: number): AnalyseMedia => ({ empreinte: 'x', duree_s: d, a_video: true, a_audio: true, coupes_s: [], silences_s: [], energie: [], bpm: 0, battues_s: [], onsets_s: [] });
const musique = (d: number, bpm = 120): AnalyseMedia => ({
  empreinte: 'm', duree_s: d, a_video: false, a_audio: true, coupes_s: [], silences_s: [], bpm,
  energie: Array.from({ length: Math.ceil(d * 2) }, (_, i) => (i % 8 < 4 ? 0.3 : 0.8)),
  battues_s: Array.from({ length: Math.floor(d / 0.5) }, (_, i) => i * 0.5), onsets_s: [],
});
const brief = () => briefDuFilm({
  clips: ['101', '102', '103', '104'].map((id) => ({ id, analyse: video(5) })),
  musique: { id: '200', analyse: musique(20) }, genre: 'pub', format: '9:16', dureeCibleS: 15,
});

describe('Monter dans le Producteur', () => {
  it('construit un EditPlan valide en code seul, déterministe, sur la durée cible', () => {
    const a = monterEnCode(brief(), 7);
    const b = monterEnCode(brief(), 7);
    expect(a.plan).toEqual(b.plan);
    const v = validerEditPlan(a.plan, { inventaire: { '101': { duree_s: 5 }, '102': { duree_s: 5 }, '103': { duree_s: 5 }, '104': { duree_s: 5 }, '200': { duree_s: 20 } } });
    expect(v.erreurs).toEqual([]);
    const m = vueMetriques(a.plan, a.brief);
    expect(m.dureeS).toBeGreaterThan(13.5);
    expect(m.dureeS).toBeLessThan(16.5);
    expect(m.score).toBeGreaterThan(0.6);
    expect(m.bpm).toBe(120);
  });
  it('sans LLM ou avec un LLM qui répond n’importe quoi, le montage reste inchangé', async () => {
    const e = monterEnCode(brief(), 7);
    const sans = await ameliorerMontage(e, null);
    expect(sans.etat.plan).toEqual(e.plan);
    const fou: ClientLlm = { completer: async () => 'pas du json' };
    const r = await ameliorerMontage(e, fou);
    expect(r.gardee).toBe(false);
    expect(r.etat.plan).toEqual(e.plan);
    expect(r.etat.tours).toBe(1);
  });
  it('une rustine qui invalide le plan ou baisse le score est refusée', async () => {
    const e = monterEnCode(brief(), 7);
    const llm: ClientLlm = { completer: async () => JSON.stringify({ rustines: [{ op: 'regler_plan', id: e.plan.video[0].id, duree_f: 3 }] }) };
    const r = await ameliorerMontage(e, llm);
    if (r.gardee) expect(r.apres).toBeGreaterThan(r.avant); else expect(r.etat.plan).toEqual(e.plan);
  });
});
