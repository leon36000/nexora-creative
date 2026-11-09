const CHAMP = 'detailed_description:';
const PREMIER_PLAN = '[Shot 1]';

/** Le style doit contenir au moins un caractère avant le premier crochet du champ. */
export function styleAvantPremierPlanRef(texte: string): boolean {
  let curseur = 0;
  while (curseur < texte.length) {
    const debut = texte.indexOf(CHAMP, curseur);
    if (debut < 0) return false;
    const contenu = debut + CHAMP.length;
    const crochet = texte.indexOf('[', contenu);
    if (crochet < 0) return false;
    if (crochet > contenu && texte.startsWith(PREMIER_PLAN, crochet)) return true;
    // Les autres occurrences du champ avant ce crochet échouent au même endroit.
    curseur = crochet + 1;
  }
  return false;
}
