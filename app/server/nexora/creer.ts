/**
 * Parcours simple « Créer » : une intention en français → prompt H3 écrit par le LLM → rendu FastH3.
 * Ce module ne fait que lire la demande et préparer le corps de rendu ; la route (server/nexora/routes.ts) enchaîne.
 */

export type FormatCreer = '16:9' | '9:16' | '1:1';
export type DureeCreer = 5 | 10 | 15;

export interface DemandeCreer {
  intention: string;
  format: FormatCreer;
  duree: DureeCreer;
  son: boolean;
}

/** Point de contrôle FastH3 V2 distillé et quantifié NVFP4 (server/graphs/h3.ts, H3_DISTILLED_CHECKPOINTS). */
export const CHECKPOINT_FASTH3 = 'fastvideo_fasth3_8step_v2_pruned_nvfp4.safetensors';

const TAILLES: Record<FormatCreer, { width: number; height: number }> = {
  '16:9': { width: 832, height: 480 },
  '9:16': { width: 480, height: 832 },
  '1:1': { width: 640, height: 640 },
};

/** Plus petite longueur de la grille H3 (124 + 17n) qui couvre la durée demandée. */
function imagesPour(dureeS: number): number {
  const n = Math.max(0, Math.ceil((dureeS * 24 - 124) / 17));
  return Math.min(362, 124 + 17 * n);
}

export function lireDemandeCreer(b: unknown): DemandeCreer {
  const o = (b ?? {}) as Record<string, unknown>;
  const intention = typeof o.intention === 'string' ? o.intention.trim() : '';
  if (!intention) throw new Error('Décris la vidéo que tu veux en une phrase ou plus.');
  if (intention.length > 4000) throw new Error('Description trop longue (4 000 caractères au plus).');
  const format: FormatCreer = o.format === '9:16' || o.format === '1:1' ? o.format : '16:9';
  const duree: DureeCreer = o.duree === 10 || o.duree === 15 ? o.duree : 5;
  return { intention, format, duree, son: o.son !== false };
}

export function corpsRenduH3(d: DemandeCreer, prompt: string) {
  return {
    kind: 'video' as const,
    videoModel: 'h3-fast' as const,
    prompt,
    ...TAILLES[d.format],
    lengthFrames: imagesPour(d.duree),
    steps: 8,
    checkpoint: CHECKPOINT_FASTH3,
    withAudio: d.son,
    shotName: d.intention.slice(0, 60),
  };
}

/** Durée effective (s) du rendu, pour la ligne d'instruction et les horodatages du prompt. */
export function dureeEffective(d: DemandeCreer): number {
  return imagesPour(d.duree) / 24;
}
