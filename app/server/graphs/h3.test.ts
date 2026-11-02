import { describe, expect, it } from 'vitest';
import { buildH3Graph, H3_DISTILLED_CHECKPOINTS } from './h3.js';

type Node = { class_type: string; inputs: Record<string, unknown> };

const base = { prompt: 'un phare au crépuscule', width: 832, height: 480, lengthFrames: 124, seed: 7, steps: 20 };

describe('graphe H3 avec un point de contrôle FastH3 V2 distillé', () => {
  const nom = 'fastvideo_fasth3_8step_v2_pruned_nvfp4.safetensors';

  it('est déclaré avec ses réglages d’échantillonnage', () => {
    expect(H3_DISTILLED_CHECKPOINTS[nom]).toEqual({ family: 'fl2va', steps: 8, shiftVideo: 10, shiftAudio: 3 });
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

describe('graphe H3 avec le point de contrôle cinéma 10Eros-Max × Singularity (ref2va, turbo 8 étapes)', () => {
  const nom = '10Eros_Max_h3_8stepTURBO_beta7_SingularityV2_ref2va_int8HQ.safetensors';

  it('passe par le nœud de référence avec 8 étapes, décalage 12/3 et euler', () => {
    const g = buildH3Graph({ ...base, width: 1344, height: 768, checkpoint: nom, refMode: true }) as Record<string, Node>;
    expect(g.u.inputs.unet_name).toBe(nom);
    expect(g.gen.class_type).toBe('MiniMaxH3ReferenceToVideo');
    expect(g.shift.inputs).toMatchObject({ shift_video: 12, shift_audio: 3 });
    expect(g.sched.inputs).toMatchObject({ model: ['shift', 0], steps: 8 });
    expect(g.sampler.inputs.sampler_name).toBe('euler');
  });

  it('prend la photo de départ comme première référence', () => {
    const g = buildH3Graph({ ...base, checkpoint: nom, refMode: true, startImage: 'depart.png' }) as Record<string, Node>;
    expect(g.ref0.inputs.image).toBe('depart.png');
    expect(g.gen.inputs['ref_images.ref_image_0']).toEqual(['ref0', 0]);
  });

  it('n’est pas appliqué hors de sa famille (graphe fl2va)', () => {
    const g = buildH3Graph({ ...base, checkpoint: nom }) as Record<string, Node>;
    expect(g.u.inputs.unet_name).toBe('minimax_h3_fl2va_pruned_fp8_scaled.safetensors');
  });
});
