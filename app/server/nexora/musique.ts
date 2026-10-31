/**
 * Bande originale d'un film : le LLM écrit la description structurée attendue par MiniMax Music 3 (Global Metadata →
 * Vocal Details → Arrangement, guide officiel « music-caption-rewriter ») à partir du storyboard, de son ambiance et
 * de sa durée ; un repli déterministe garantit qu'une musique est toujours possible sans LLM.
 */
import type { Storyboard } from './film.js';
import { type ClientLlm, lireJson } from './llm.js';

export interface DemandeMusique { description: string; paroles: string; dureeS: number; source: 'llm' | 'repli' }

const BALISES = /^\s*(\[[A-Za-z -]+\]|\([^)]*\))?\s*$/;

/** Paroles purement instrumentales : seulement des balises de section et des vocalises entre parenthèses. */
export function parolesInstrumentales(p: string): boolean {
  return p.split('\n').every((l) => BALISES.test(l));
}

export function musiqueDeRepli(sb: Storyboard, dureeS: number): DemandeMusique {
  return {
    description: `Global Metadata: Cinematic orchestral film score for "${sb.titre}", ${Math.round(dureeS)} seconds, building from a quiet opening to a powerful climax and a clean ending. Polished modern film-score production, wide stereo.

Vocal Details: Instrumental, no lyrics.

Arrangement: Intro with soft strings and a low drone; build with ostinato strings and percussion; climax with full orchestra, brass and drums; outro resolving softly.`,
    paroles: '[Intro]\n\n[Build]\n\n[Climax]\n\n[Outro]',
    dureeS,
    source: 'repli',
  };
}

export async function ecrireMusique(sb: Storyboard, dureeS: number, llm: ClientLlm | null, envie?: string): Promise<DemandeMusique> {
  if (!llm) return musiqueDeRepli(sb, dureeS);
  try {
    const brut = await llm.completer('musique', [
      {
        role: 'system',
        content: [
          'You are the music supervisor of Nexora Creative. Write the music description for MiniMax Music 3 that scores this film.',
          'The description has exactly three paragraphs starting with "Global Metadata:", "Vocal Details:" and "Arrangement:".',
          'Global Metadata: genre, BPM, key, emotional progression over the film duration, production profile.',
          'Vocal Details: "Instrumental, no lyrics" unless the user explicitly asks for a song.',
          'Arrangement: instruments and how each section evolves, aligned with the shots of the storyboard.',
          'Never name real artists, songs or film franchises.',
          'Answer with JSON {"description": "...", "paroles": "..."} where paroles holds only section tags such as [Intro], [Build], [Drop], [Climax], [Outro] on their own lines (and optional wordless vocalises in parentheses).',
        ].join('\n'),
      },
      {
        role: 'user',
        content: JSON.stringify({
          titre: sb.titre, bible: sb.bible, duree_secondes: Math.round(dureeS), envie_de_la_personne: envie ?? null,
          plans: sb.plans.map((p) => ({ resume: p.resume, duree: p.duree })),
        }),
      },
    ], { json: true, temperature: 0.6 });
    const r = lireJson<{ description?: unknown; paroles?: unknown }>(brut);
    const description = String(r.description ?? '').trim();
    const paroles = String(r.paroles ?? '').trim() || '[Instrumental]';
    const ok = /Global Metadata:/.test(description) && /Arrangement:/.test(description) && description.length < 4000;
    if (ok && (envie || parolesInstrumentales(paroles))) return { description, paroles, dureeS, source: 'llm' };
  } catch { /* repli */ }
  return musiqueDeRepli(sb, dureeS);
}
