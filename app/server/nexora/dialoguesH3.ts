export interface DialogueH3 { langue: string; texte: string }

/** Délimiteurs fixes et curseur croissant : un suffixe incomplet n'est parcouru qu'une fois. */
export function extraireDialoguesH3(texte: string): DialogueH3[] {
  const ouverture = '<d>[';
  const fermeture = '</d>';
  const blocs: DialogueH3[] = [];
  let position = 0;
  while (position < texte.length) {
    const debut = texte.indexOf(ouverture, position);
    if (debut < 0) break;
    const debutLangue = debut + ouverture.length;
    const finLangue = texte.indexOf(']', debutLangue);
    if (finLangue < 0) break;
    if (finLangue === debutLangue) {
      position = finLangue + 1;
      continue;
    }
    const debutTexte = finLangue + 1;
    const finTexte = texte.indexOf(fermeture, debutTexte);
    if (finTexte < 0) break;
    blocs.push({ langue: texte.slice(debutLangue, finLangue), texte: texte.slice(debutTexte, finTexte).trim() });
    position = finTexte + fermeture.length;
  }
  return blocs;
}
