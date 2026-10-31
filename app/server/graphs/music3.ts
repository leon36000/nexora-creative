/**
 * Nexora : graphe MiniMax Music 3 (bande originale d'un film), d'après le gabarit officiel ComfyUI
 * `audio_minimax_music_3` : encodeur texte Music3 (description + paroles) → latent audio de la durée prévue →
 * KSampler 30 étapes, CFG 1,7, euler/simple → décodeur Flow-VAE « dav », 32 kHz stéréo.
 * Licence MiniMax-Music3 Community : pas d'exclusion de territoire ; afficher « MiniMax-Music3 » dans l'interface.
 */
export const MUSIC3_MODELS = {
  dit: 'minimax_music3_dit_int8_convrot.safetensors',
  clip: 'minimax_music3_text_encoder_pruned_int8_convrot.safetensors',
  vae: 'minimax_music3_dav.safetensors',
};

export interface Music3Params {
  /** Description structurée : Global Metadata → Vocal Details → Arrangement (guide officiel). */
  description: string;
  /** Paroles avec balises de section ; « [Instrumental] » seul pour une musique sans voix. */
  paroles: string;
  dureeS: number;
  seed: number;
  etapes?: number;
}

export function buildMusic3Graph(p: Music3Params): Record<string, unknown> {
  return {
    u: { class_type: 'UNETLoader', inputs: { unet_name: MUSIC3_MODELS.dit, weight_dtype: 'default' } },
    c: { class_type: 'CLIPLoader', inputs: { clip_name: MUSIC3_MODELS.clip, type: 'minimax', device: 'default' } },
    v: { class_type: 'VAELoader', inputs: { vae_name: MUSIC3_MODELS.vae } },
    enc: {
      class_type: 'MiniMaxMusic3TextEncode',
      inputs: {
        clip: ['c', 0], caption: p.description, lyrics: p.paroles || '[Instrumental]', seed: p.seed,
        max_duration: Math.max(5, Math.min(300, p.dureeS)), cfg_scale: 1.7, top_k: 50,
      },
    },
    neg: { class_type: 'ConditioningZeroOut', inputs: { conditioning: ['enc', 0] } },
    lat: { class_type: 'EmptyMiniMaxMusic3LatentAudio', inputs: { seconds: ['enc', 1], batch_size: 1 } },
    ks: {
      class_type: 'KSampler',
      inputs: {
        model: ['u', 0], seed: p.seed, steps: p.etapes ?? 30, cfg: 1.7, sampler_name: 'euler', scheduler: 'simple',
        positive: ['enc', 0], negative: ['neg', 0], latent_image: ['lat', 0], denoise: 1,
      },
    },
    dec: { class_type: 'VAEDecodeAudio', inputs: { samples: ['ks', 0], vae: ['v', 0] } },
    save: { class_type: 'SaveAudio', inputs: { audio: ['dec', 0], filename_prefix: 'nexora/musique' } },
  };
}
