import { describe, expect, it } from 'vitest';
import { analyserLigne, analyserMarkdown } from './markdown.js';

describe('mini-Markdown du Producteur', () => {
  it('le gras ne laisse aucun astérisque', () => {
    const l = analyserLigne('Voici **le plan** et *l’idée* puis `code`.');
    expect(l.map((x) => x.t)).toEqual(['texte', 'gras', 'texte', 'italique', 'texte', 'code', 'texte']);
    expect(l.map((x) => x.v).join('')).not.toContain('*');
  });
  it('listes à puces et numérotées, paragraphes séparés', () => {
    const b = analyserMarkdown('Intro **x**\n\n- un\n- deux\n1. a\n2. b\n\nFin');
    expect(b.map((x) => x.type)).toEqual(['p', 'ul', 'ol', 'p']);
    expect((b[1] as any).items).toHaveLength(2);
  });
  it('un titre devient une ligne en gras, du HTML reste du texte', () => {
    const b = analyserMarkdown('## Plan\n<b>x</b>');
    expect((b[0] as any).lignes[0][0]).toEqual({ t: 'gras', v: 'Plan' });
    expect((b[0] as any).lignes[1][0].v).toBe('<b>x</b>');
  });
  it('une étoile seule (multiplication) est conservée', () => {
    expect(analyserLigne('2 * 3 = 6')[0].v).toBe('2 * 3 = 6');
  });
});
