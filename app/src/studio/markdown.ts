/**
 * Mini-Markdown du fil du Producteur : gras, italique, code en ligne, listes à puces ou numérotées, paragraphes.
 * Pas de HTML : le résultat est un arbre de données que React rend en nœuds, donc rien n'est injecté.
 */
export type Ligne = { t: 'texte' | 'gras' | 'italique' | 'code'; v: string };
export type Bloc =
  | { type: 'p'; lignes: Ligne[][] }
  | { type: 'ul' | 'ol'; items: Ligne[][] };

export function analyserLigne(s: string): Ligne[] {
  const out: Ligne[] = [];
  const re = /\*\*([^*]+?)\*\*|__([^_]+?)__|`([^`]+?)`|(?<![*\w])\*([^*\s][^*]*?)\*(?![*\w])|(?<![_\w])_([^_\s][^_]*?)_(?![_\w])/g;
  let i = 0;
  for (let m = re.exec(s); m; m = re.exec(s)) {
    if (m.index > i) out.push({ t: 'texte', v: s.slice(i, m.index) });
    if (m[1] !== undefined || m[2] !== undefined) out.push({ t: 'gras', v: m[1] ?? m[2] });
    else if (m[3] !== undefined) out.push({ t: 'code', v: m[3] });
    else out.push({ t: 'italique', v: m[4] ?? m[5] });
    i = m.index + m[0].length;
  }
  if (i < s.length) out.push({ t: 'texte', v: s.slice(i) });
  return out;
}

export function analyserMarkdown(texte: string): Bloc[] {
  const blocs: Bloc[] = [];
  for (const brut of texte.replace(/\r/g, '').split('\n')) {
    const l = brut.trim();
    if (!l) { blocs.push({ type: 'p', lignes: [] }); continue; }
    const puce = /^[-*•]\s+(.*)$/.exec(l);
    const num = /^\d+[.)]\s+(.*)$/.exec(l);
    const titre = /^#{1,6}\s+(.*)$/.exec(l);
    const dernier = blocs[blocs.length - 1];
    if (titre) { blocs.push({ type: 'p', lignes: [[{ t: 'gras', v: titre[1] }]] }); continue; }
    if (puce || num) {
      const type = num ? 'ol' : 'ul';
      const item = analyserLigne((num ?? puce)![1]);
      if (dernier && dernier.type === type) dernier.items.push(item);
      else blocs.push({ type, items: [item] });
      continue;
    }
    if (dernier && dernier.type === 'p' && dernier.lignes.length) dernier.lignes.push(analyserLigne(l));
    else blocs.push({ type: 'p', lignes: [analyserLigne(l)] });
  }
  return blocs.filter((b) => b.type !== 'p' || b.lignes.length);
}
