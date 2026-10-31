/**
 * Textes de publication : titre, description et hashtags pour partager une création sur un réseau social, écrits par
 * le LLM (rôle « publication ») à partir de la phrase de la personne. Mentions obligatoires ajoutées par le code, jamais
 * par le LLM : « généré par IA » (AUP de H3, point 12) et les outils utilisés.
 */
import { type ClientLlm, lireJson } from './llm.js';

export type Plateforme = 'tiktok' | 'instagram' | 'youtube' | 'linkedin' | 'x';
export const PLATEFORMES: Record<Plateforme, { nom: string; limite: number; conseil: string }> = {
  tiktok: { nom: 'TikTok', limite: 150, conseil: 'accroche en une ligne, 3 à 5 hashtags' },
  instagram: { nom: 'Instagram Reels', limite: 300, conseil: 'une phrase d’accroche, 5 à 8 hashtags' },
  youtube: { nom: 'YouTube Shorts', limite: 100, conseil: 'titre court et clair, description de 2 lignes' },
  linkedin: { nom: 'LinkedIn', limite: 600, conseil: 'ton professionnel, 3 hashtags, une idée à retenir' },
  x: { nom: 'X', limite: 250, conseil: 'très court, 1 ou 2 hashtags' },
};

export interface Publication { titre: string; texte: string; hashtags: string[]; mention: string; source: 'llm' | 'repli' }

const MENTION = 'Généré par IA avec Nexora Creative (MiniMax H3).';

export function publicationDeRepli(idee: string): Publication {
  const base = idee.trim().replace(/\s+/g, ' ');
  return { titre: base.length > 60 ? `${base.slice(0, 57)}…` : base, texte: base.slice(0, 200), hashtags: ['#IA', '#NexoraCreative'], mention: MENTION, source: 'repli' };
}

export function nettoyerHashtags(h: unknown): string[] {
  if (!Array.isArray(h)) return [];
  return [...new Set(h.map((x) => String(x).trim().replace(/^#*/, '#').replace(/[^\p{L}\p{N}_#]/gu, '')).filter((x) => x.length > 2 && x.length <= 30))].slice(0, 10);
}

export async function ecrirePublication(idee: string, plateforme: Plateforme, langue: 'fr' | 'en', llm: ClientLlm | null): Promise<Publication> {
  if (!llm) return publicationDeRepli(idee);
  const p = PLATEFORMES[plateforme];
  try {
    const brut = await llm.completer('publication', [
      { role: 'system', content: [
        `Tu écris le texte de publication d’une courte vidéo pour ${p.nom} (${p.conseil}), en ${langue === 'en' ? 'anglais' : 'français québécois'}.`,
        `Le texte (hors hashtags) fait ${p.limite} caractères au plus. Accroche forte, concrète, sans exagération ni promesse fausse ;`,
        'ne cite aucune marque ni personne réelle ; n’écris pas la mention « généré par IA », elle est ajoutée ensuite.',
        'Réponds en JSON {"titre":"...","texte":"...","hashtags":["#..."]}.',
      ].join(' ') },
      { role: 'user', content: idee.slice(0, 2000) },
    ], { json: true, temperature: 0.8 });
    const r = lireJson<{ titre?: unknown; texte?: unknown; hashtags?: unknown }>(brut);
    const titre = String(r.titre ?? '').trim().slice(0, 100);
    const texte = String(r.texte ?? '').trim().slice(0, p.limite);
    if (!titre || !texte) throw new Error('réponse incomplète');
    return { titre, texte, hashtags: nettoyerHashtags(r.hashtags), mention: MENTION, source: 'llm' };
  } catch {
    return publicationDeRepli(idee);
  }
}
