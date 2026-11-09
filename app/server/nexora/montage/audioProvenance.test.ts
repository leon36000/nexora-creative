import { describe, it, expect } from 'vitest';
import { type AnalyseMedia, versClip } from './analyse.js';
import { briefDuFilm, monterEnCode } from './producteur.js';
import { montageAuto } from './auto.js';
import type { Brief } from './types.js';

const analyse = (a_audio: boolean): AnalyseMedia => ({ empreinte: 'fixture', duree_s: 2, a_video: true, a_audio, coupes_s: [], silences_s: [], energie: [], bpm: 0, battues_s: [], onsets_s: [] });
describe('présence audio mesurée dans le montage', () => {
  it.each([true, false])('propage la mesure %s de l’analyse au plan réellement rendu', a_audio => {
    const a = analyse(a_audio);
    expect(versClip('s', a).a_audio).toBe(a_audio);
    const brief = briefDuFilm({ clips: [{ id: 's', analyse: a }], genre: 'pub', format: '16:9' });
    const etat = monterEnCode(brief, 1);
    expect(etat.plan.sources.s.a_audio).toBe(a_audio);
  });
  it.each([true, false, undefined])('réserve le premier plan sonore mesuré %s face à la musique', a_audio => {
    const brief: Brief = { id: 'mix', partition: 'test', genre: 'pub', format: '16:9', fps: 24, duree_cible_s: 2, enonce: 'Montage', textes_imposes: [], clips: [{ id: 's', duree_s: 2, ...(a_audio === undefined ? {} : { a_audio }) }], musique: { id: 'm', duree_s: 2, bpm: 120, battues_s: [], energie: [] } };
    const plan = montageAuto(brief);
    expect(plan.audio.ducking.actif).toBe(a_audio === true);
    expect(plan.audio.musique?.gain_db).toBe(a_audio === true ? -14 : -8);
  });
  it('ne suppose pas de son pour un brief historique sans mesure', () => {
    const brief: Brief = { id: 'historique', partition: 'test', genre: 'pub', format: '16:9', fps: 24, duree_cible_s: 2, enonce: 'Montage', textes_imposes: [], clips: [{ id: 's', duree_s: 2 }] };
    expect(Object.hasOwn(montageAuto(brief).sources.s, 'a_audio')).toBe(false);
  });
});
