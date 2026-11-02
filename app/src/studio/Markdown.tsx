import type { Ligne } from './markdown';
import { analyserMarkdown } from './markdown';

const rendreLigne = (l: Ligne[]) => l.map((x, i) => x.t === 'gras' ? <strong key={i}>{x.v}</strong> : x.t === 'italique' ? <em key={i}>{x.v}</em> : x.t === 'code' ? <code key={i}>{x.v}</code> : <span key={i}>{x.v}</span>);

/** Texte du Producteur rendu en nœuds React (aucun HTML injecté). */
export function Markdown({ texte }: { texte: string }) {
  return (
    <div className="pr-md">
      {analyserMarkdown(texte).map((b, i) => b.type === 'p'
        ? <p key={i}>{b.lignes.map((l, j) => <span key={j}>{j > 0 && <br />}{rendreLigne(l)}</span>)}</p>
        : b.type === 'ul'
          ? <ul key={i}>{b.items.map((it, j) => <li key={j}>{rendreLigne(it)}</li>)}</ul>
          : <ol key={i}>{b.items.map((it, j) => <li key={j}>{rendreLigne(it)}</li>)}</ol>)}
    </div>
  );
}
