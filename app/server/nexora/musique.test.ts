import { describe, expect, it } from 'vitest';
import { buildMusic3Graph, MUSIC3_MODELS } from '../graphs/music3.js';
import { argsAvecMusique, type Storyboard } from './film.js';
import type { ClientLlm } from './llm.js';
import { ecrireMusique, parolesInstrumentales } from './musique.js';

const sb: Storyboard = {
  titre: 'Crimson Rising', bible: { style: 'épique', personnages: [{ nom: 'Kira', description: 'guerrière en kimono noir' }], lieux: [] }, dureeTotale: 20,
  plans: [{ resume: 'le dragon jaillit', description: 'x', duree: 10, camera: 'travelling' }, { resume: 'la guerrière', description: 'y', duree: 10, camera: 'arc' }],
} as unknown as Storyboard;
const llm = (r: string): ClientLlm => ({ async completer() { return r; } });

describe('bande originale MiniMax Music 3', () => {
  it('suit le gabarit officiel ComfyUI (encodeur Music3, latent de la durée, 30 étapes, CFG 1,7)', () => {
    const g = buildMusic3Graph({ description: 'Global Metadata: epic', paroles: '', dureeS: 62, seed: 4 }) as Record<string, any>;
    expect(g.c.inputs).toMatchObject({ clip_name: MUSIC3_MODELS.clip, type: 'minimax' });
    expect(g.enc.inputs).toMatchObject({ lyrics: '[Instrumental]', max_duration: 62, cfg_scale: 1.7 });
    expect(g.lat.inputs.seconds).toEqual(['enc', 1]);
    expect(g.ks.inputs).toMatchObject({ steps: 30, cfg: 1.7, sampler_name: 'euler', negative: ['neg', 0] });
  });

  it('garde une description LLM conforme et instrumentale', async () => {
    const bon = JSON.stringify({ description: 'Global Metadata: epic.\n\nVocal Details: Instrumental.\n\nArrangement: drums.', paroles: '[Intro]\n\n[Climax]\n(Ahh)' });
    expect((await ecrireMusique(sb, 20, llm(bon))).source).toBe('llm');
  });

  it('retombe sur une description sûre si le LLM invente des paroles ou répond mal', async () => {
    const chante = JSON.stringify({ description: 'Global Metadata: pop.\n\nArrangement: guitar.', paroles: '[Verse]\nI love you baby' });
    expect((await ecrireMusique(sb, 20, llm(chante))).source).toBe('repli');
    expect((await ecrireMusique(sb, 20, llm('pas du json'))).source).toBe('repli');
    const r = await ecrireMusique(sb, 20, null);
    expect(r.description).toMatch(/Crimson Rising/);
    expect(parolesInstrumentales(r.paroles)).toBe(true);
  });

  it('mixe la musique sous les sons du film et normalise à −14 LUFS', () => {
    const a = argsAvecMusique('film.mp4', 'musique.flac', 'sortie.mp4', { dureeS: 20, sonDuFilm: true });
    const f = a[a.indexOf('-filter_complex') + 1];
    expect(f).toMatch(/afade=t=out:st=18\.50/);
    expect(f).toMatch(/volume=-8dB/);
    expect(f).toMatch(/loudnorm=I=-14/);
    expect(a).toContain('copy');
  });
});
