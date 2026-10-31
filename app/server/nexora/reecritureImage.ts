/**
 * Prompt d'image : transforme la phrase d'un débutant (français) en un long paragraphe anglais qui décrit l'image finie,
 * comme le « prompt enhancer » officiel de Qwen-Image. Le LLM propose, le code dispose : repli sur la phrase telle quelle.
 * Sert aussi au « plan clé » d'un film (l'image de départ que H3 anime ensuite).
 */
import { type ClientLlm, lireJson } from './llm.js';

export interface ResultatImage { prompt: string; source: 'llm' | 'repli' }

const SYSTEME = [
  'You are the image prompt writer of Nexora Creative. Turn the user idea (often in French) into ONE English paragraph of 80 to 160 words',
  'that describes the finished image as if you were looking at it: subject and its exact appearance, action or pose, setting, materials and textures,',
  'light and time of day, composition and lens, mood, colour grade. This image will be the first frame of a video, so keep a clear subject,',
  'a readable composition and room for camera movement.',
  'Rules: never add text, logos or watermarks to the image unless the user quoted them; never name real people, brands or film franchises, and avoid',
  'designs that imitate known characters; keep every subject the user named exactly as named.',
  'Answer with JSON {"prompt": "..."} and nothing else.',
].join(' ');

export function validerPromptImage(p: string): string[] {
  const erreurs: string[] = [];
  if (p.length < 40) erreurs.push('too short');
  if (p.length > 2500) erreurs.push('too long');
  if (/\((?:[^()]*\b(?:not applicable|note:|N\/A)\b[^()]*)\)/i.test(p)) erreurs.push('contains a meta remark');
  return erreurs;
}

export async function reecrireImage(intention: string, llm: ClientLlm | null, format = '16:9'): Promise<ResultatImage> {
  if (llm) {
    try {
      const brut = await llm.completer('redaction', [
        { role: 'system', content: SYSTEME },
        { role: 'user', content: JSON.stringify({ idee: intention, format }) },
      ], { json: true, temperature: 0.7 });
      const prompt = String(lireJson<{ prompt?: unknown }>(brut).prompt ?? '').trim();
      if (!validerPromptImage(prompt).length) return { prompt, source: 'llm' };
    } catch { /* repli */ }
  }
  return { prompt: intention.trim(), source: 'repli' };
}
