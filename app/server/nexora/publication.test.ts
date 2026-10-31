import { describe, expect, it } from 'vitest';
import type { ClientLlm } from './llm.js';
import { ecrirePublication, nettoyerHashtags, publicationDeRepli } from './publication.js';

const llm = (r: string): ClientLlm => ({ async completer() { return r; } });

describe('texte de publication', () => {
  it('garde la réponse du LLM, borne la longueur à la plateforme et ajoute toujours la mention IA', async () => {
    const p = await ecrirePublication('un dragon', 'x', 'fr', llm(JSON.stringify({ titre: 'Le dragon', texte: 'a'.repeat(500), hashtags: ['IA', '#dragon', 'mauvais tag!!'] })));
    expect(p.source).toBe('llm');
    expect(p.texte).toHaveLength(250);
    expect(p.hashtags).toEqual(['#IA', '#dragon', '#mauvaistag']);
    expect(p.mention).toMatch(/Généré par IA/);
  });

  it('retombe sur un texte simple, avec la mention, sans LLM ou si la réponse est incomplète', async () => {
    expect((await ecrirePublication('un dragon', 'tiktok', 'fr', null)).source).toBe('repli');
    expect((await ecrirePublication('un dragon', 'tiktok', 'fr', llm('{"titre":"","texte":""}'))).source).toBe('repli');
    expect(publicationDeRepli('x'.repeat(300)).titre.length).toBeLessThanOrEqual(60);
    expect(publicationDeRepli('x').mention).toMatch(/MiniMax H3/);
  });

  it('nettoie les hashtags : doublons, longueur, nombre', () => {
    expect(nettoyerHashtags(['#a', 'a', '#bb', 'x'.repeat(40)])).toEqual(['#bb']);
    expect(nettoyerHashtags('pas une liste')).toEqual([]);
  });
});
