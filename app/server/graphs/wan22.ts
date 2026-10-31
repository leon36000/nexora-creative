/**
 * Nexora : graphe Wan 2.2 TI2V-5B (Apache-2.0), second moteur vidéo à licence propre. Il sert de repli pour les comptes
 * hors du territoire de MiniMax H3 et prouve que le studio ne dépend d'aucun modèle unique. Réglages repris du gabarit
 * officiel ComfyUI `video_wan2_2_5B_ti2v` : 20 étapes, CFG 5, uni_pc / simple, ModelSamplingSD3 décalage 8, 24 i/s.
 * Pas de son : Wan 2.2 ne génère que l'image.
 */

export const WAN22_MODELS = {
  unet: 'wan2.2_ti2v_5B_fp16.safetensors',
  clip: 'umt5_xxl_fp8_e4m3fn_scaled.safetensors',
  vae: 'wan2.2_vae.safetensors',
};

/** Prompt négatif officiel du gabarit (en chinois, tel que Wan l'a appris). */
const NEGATIF =
  '色调艳丽，过曝，静态，细节模糊不清，字幕，风格，作品，画作，画面，静止，整体发灰，最差质量，低质量，JPEG压缩残留，丑陋的，残缺的，多余的手指，画得不好的手部，画得不好的脸部，畸形的，毁容的，形态畸形的肢体，手指融合，静止不动的画面，杂乱的背景，三条腿，背景人很多，倒着走';

export interface Wan22Params {
  prompt: string;
  width: number;
  height: number;
  frames: number;
  seed: number;
  steps?: number;
  startImage?: string;
}

/** Wan attend 4n+1 images ; 24 i/s. */
export function imagesWan(secondes: number): number {
  return Math.round((secondes * 24) / 4) * 4 + 1;
}

/** Wan lit un paragraphe descriptif : on garde la description visuelle du prompt H3, sans balises ni champs sonores. */
export function promptWanDepuisH3(h3: string): string {
  const debut = h3.indexOf('integrated_multimodal_description:');
  const fin = h3.indexOf('overall_soundscape:');
  const corps = debut >= 0 ? h3.slice(debut + 'integrated_multimodal_description:'.length, fin > debut ? fin : undefined) : h3;
  return corps
    .replace(/\[Shot \d+\]\s*(At \d{2}:\d{2}\.\d{3},\s*)?/g, '')
    .replace(/<d>[\s\S]*?<\/d>/g, '')
    .replace(/\s*\(S\d+(,S\d+)*\)/g, '')
    .replace(/\b(says|shouts|whispers|sings)( in an off-screen voiceover)?:\s*/g, '')
    .replace(/\s+/g, ' ')
    .trim();
}

export function buildWan22Graph(p: Wan22Params): Record<string, unknown> {
  const g: Record<string, unknown> = {
    u: { class_type: 'UNETLoader', inputs: { unet_name: WAN22_MODELS.unet, weight_dtype: 'default' } },
    shift: { class_type: 'ModelSamplingSD3', inputs: { model: ['u', 0], shift: 8 } },
    c: { class_type: 'CLIPLoader', inputs: { clip_name: WAN22_MODELS.clip, type: 'wan', device: 'default' } },
    v: { class_type: 'VAELoader', inputs: { vae_name: WAN22_MODELS.vae } },
    pos: { class_type: 'CLIPTextEncode', inputs: { clip: ['c', 0], text: p.prompt } },
    neg: { class_type: 'CLIPTextEncode', inputs: { clip: ['c', 0], text: NEGATIF } },
    lat: {
      class_type: 'Wan22ImageToVideoLatent',
      inputs: { vae: ['v', 0], width: p.width, height: p.height, length: p.frames, batch_size: 1 },
    },
    ks: {
      class_type: 'KSampler',
      inputs: {
        model: ['shift', 0], positive: ['pos', 0], negative: ['neg', 0], latent_image: ['lat', 0],
        seed: p.seed, steps: p.steps ?? 20, cfg: 5, sampler_name: 'uni_pc', scheduler: 'simple', denoise: 1,
      },
    },
    dec: { class_type: 'VAEDecode', inputs: { samples: ['ks', 0], vae: ['v', 0] } },
    vid: { class_type: 'CreateVideo', inputs: { images: ['dec', 0], fps: 24 } },
    save: { class_type: 'SaveVideo', inputs: { video: ['vid', 0], filename_prefix: 'nexora/wan22', format: 'auto', codec: 'auto' } },
  };
  if (p.startImage) {
    g.img = { class_type: 'LoadImage', inputs: { image: p.startImage } };
    (g.lat as { inputs: Record<string, unknown> }).inputs.start_image = ['img', 0];
  }
  return g;
}
