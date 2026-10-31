import { describe, expect, it } from 'vitest';
import { buildH3Graph, H3_DISTILLED_CHECKPOINTS } from './h3.js';

type Node = { class_type: string; inputs: Record<string, unknown> };

const base = { prompt: 'un phare au crépuscule', width: 832, height: 480, lengthFrames: 124, seed: 7, steps: 20 };

describe('graphe H3 avec un point de contrôle FastH3 V2 distillé', () => {
  const nom = 'fastvideo_fasth3_8step_v2_pruned_nvfp4.safetensors';

  it('est déclaré avec ses réglages d’échantillonnage', () => {
    expect(H3_DISTILLED_CHECKPOINTS[nom]).toEqual({ steps: 8, shiftVideo: 10, shiftAudio: 3 });
  });

  it('charge ce fichier, 8 étapes, décalage sigma 10/3, sans LoRA', () => {
    const g = buildH3Graph({ ...base, checkpoint: nom }) as Record<string, Node>;
    expect(g.u.inputs.unet_name).toBe(nom);
    expect(g.lora).toBeUndefined();
    expect(g.shift.inputs).toMatchObject({ model: ['u', 0], shift_video: 10, shift_audio: 3 });
    expect(g.sched.inputs).toMatchObject({ model: ['shift', 0], steps: 8 });
    expect(g.guider.inputs.model).toEqual(['shift', 0]);
  });

  it('ignore un préréglage turbo (LoRA) incompatible avec un modèle déjà distillé', () => {
    const g = buildH3Graph({ ...base, checkpoint: nom, turbo: 'v11-4' }) as Record<string, Node>;
    expect(g.lora).toBeUndefined();
    expect(g.sched.inputs.steps).toBe(8);
  });

  it('garde le comportement d’origine sans point de contrôle distillé', () => {
    const g = buildH3Graph(base) as Record<string, Node>;
    expect(g.u.inputs.unet_name).toBe('minimax_h3_fl2va_pruned_fp8_scaled.safetensors');
    expect(g.shift).toBeUndefined();
    expect(g.sched.inputs.steps).toBe(20);
  });
});
