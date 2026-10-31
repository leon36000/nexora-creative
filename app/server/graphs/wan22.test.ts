import { describe, expect, it } from 'vitest';
import { buildWan22Graph, imagesWan, promptWanDepuisH3, WAN22_MODELS } from './wan22.js';

type Node = { class_type: string; inputs: Record<string, unknown> };

describe('graphe Wan 2.2 TI2V-5B (gabarit officiel ComfyUI)', () => {
  it('reprend les réglages du gabarit : 20 étapes, CFG 5, uni_pc, décalage 8, 24 i/s', () => {
    const g = buildWan22Graph({ prompt: 'a red car', width: 832, height: 480, frames: 121, seed: 3 }) as Record<string, Node>;
    expect(g.u.inputs.unet_name).toBe(WAN22_MODELS.unet);
    expect(g.c.inputs).toMatchObject({ clip_name: WAN22_MODELS.clip, type: 'wan' });
    expect(g.shift.inputs.shift).toBe(8);
    expect(g.ks.inputs).toMatchObject({ steps: 20, cfg: 5, sampler_name: 'uni_pc', scheduler: 'simple', seed: 3, denoise: 1 });
    expect(g.lat.inputs).toMatchObject({ width: 832, height: 480, length: 121, batch_size: 1 });
    expect(g.vid.inputs.fps).toBe(24);
    expect(g.neg.inputs.text).toBeTruthy();
  });

  it('prend une image de départ quand elle est fournie (image vers vidéo)', () => {
    const g = buildWan22Graph({ prompt: 'p', width: 832, height: 480, frames: 121, seed: 1, startImage: 'depart.png' }) as Record<string, Node>;
    expect(g.img.inputs.image).toBe('depart.png');
    expect(g.lat.inputs.start_image).toEqual(['img', 0]);
  });

  it('cale la durée sur la grille 4n+1 de Wan', () => {
    expect(imagesWan(5)).toBe(121);
    expect((imagesWan(10) - 1) % 4).toBe(0);
    expect(imagesWan(10)).toBeGreaterThanOrEqual(240);
  });

  it('tire un prompt Wan d’un prompt H3 structuré', () => {
    const h3 = `integrated_multimodal_description: [Shot 1] Live-action, a red car. The woman (S1) says: <d>[French] Bonjour.</d> [Shot 2] At 00:03.000, the camera cuts to a close-up.

overall_soundscape: Waves.

non_diegetic_music: N/A`;
    const w = promptWanDepuisH3(h3);
    expect(w).toMatch(/^Live-action, a red car\./);
    expect(w).not.toMatch(/Shot|<d>|overall_soundscape|non_diegetic|\(S1\)/);
    expect(w).toMatch(/the camera cuts to a close-up/);
  });
});
