import { describe, expect, it } from 'vitest';
import { buildTrellisGraph, PIXAL3D_ENCODER, PIXAL3D_MODEL } from './trellis.js';

const base = { image: 'a.png', seed: 1, quality: 'draft' as const, removeBackground: true };
describe('graphe Relief', () => {
  it('une image : TRELLIS.2 et son conditionnement', () => {
    const g = buildTrellisGraph(base) as any;
    expect(g.cond.class_type).toBe('Trellis2Conditioning');
    expect(g.unet.inputs.unet_name).toMatch(/trellis_2/);
    expect(g.img_left).toBeUndefined();
  });
  it('plusieurs vues : Pixal3D, chaque vue détourée et branchée au bon côté', () => {
    const g = buildTrellisGraph({ ...base, vues: { left: 'l.png', back: 'b.png', fov: 24 } }) as any;
    expect(g.cond.class_type).toBe('Pixal3DMultiViewConditioning');
    expect(g.unet.inputs.unet_name).toBe(PIXAL3D_MODEL);
    expect(g.dino.inputs.clip_name).toBe(PIXAL3D_ENCODER);
    expect(g.cond.inputs.fov).toBe(24);
    expect(g.cond.inputs.front).toEqual(['crop', 0]);
    expect(g.cond.inputs.left).toEqual(['crop_left', 0]);
    expect(g.cond.inputs.back).toEqual(['crop_back', 0]);
    expect(g.cond.inputs.right).toBeUndefined();
    expect(g.bg_left.inputs.image).toEqual(['img_left', 0]);
  });
  it('vues avec leur propre transparence : pas de détourage', () => {
    const g = buildTrellisGraph({ ...base, removeBackground: false, vues: { right: 'r.png' } }) as any;
    expect(g.bg_right).toBeUndefined();
    expect(g.alpha_right.class_type).toBe('InvertMask');
    expect(g.cond.inputs.right).toEqual(['crop_right', 0]);
  });
});
