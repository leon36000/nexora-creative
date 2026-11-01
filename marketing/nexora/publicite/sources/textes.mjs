// Textes des annonces (fr-CA / en-CA) et limites de caractères des plateformes. Un contrôle (verifier) échoue si une limite saute.
// Limites : Meta titre 40, texte principal 125 avant « voir plus », description 30 ; Google display titre court 30, titre long 90, description 90.
import { TXT, OUTILS, outil } from "../../social/sources/moteur/marque.mjs";

export const LIMITES = { titre: 40, principal: 125, description: 30 };

/** Trois accroches. cta : diag | solutions | attente (états réels lus dans web/src/i18n/apps.ts : aucun outil n'est vendu en libre-service). */
export const ACCROCHES = [
  { id: "reve", cta: "diag",
    titre: { fr: "Rêvez grand. Gardez le contrôle.", en: "Dream big. Stay in control." },
    principal: { fr: "L’IA qui travaille pour votre entreprise. Sous votre contrôle. Parlons de votre projet, sans engagement.", en: "AI that works for your business. Under your control. Let’s talk about your project, no commitment." },
    description: { fr: "IA souveraine au Québec", en: "Sovereign AI, made in Québec" },
    boutonMeta: { fr: "Nous contacter", en: "Contact us" } },
  { id: "outils", cta: "attente",
    titre: { fr: "Un compte. Tous vos outils.", en: "One account. All your tools." },
    principal: { fr: "Huit outils d’IA, des crédits, un seul accès. L’état de chacun est écrit en toutes lettres : rien n’est promis d’avance.", en: "Eight AI tools, credits, one access. The status of each is spelled out: nothing is promised in advance." },
    description: { fr: "Rejoignez la liste d’attente", en: "Join the waitlist" },
    boutonMeta: { fr: "S’inscrire", en: "Sign up" } },
  { id: "quebec", cta: "solutions",
    titre: { fr: "IA souveraine au Québec.", en: "Sovereign AI, made in Québec." },
    principal: { fr: "Vos données restent chez vous ou au Québec. Jamais utilisées pour entraîner un modèle.", en: "Your data stays with you or in Québec. Never used to train a model." },
    description: { fr: "Voir les solutions", en: "See the solutions" },
    boutonMeta: { fr: "En savoir plus", en: "Learn more" } },
];

export const CARROUSELS = {
  outils: { // carrousel A : un compte, tous vos outils
    titre: { fr: "Un compte, des outils", en: "One account, many tools" },
    principal: { fr: "Un compte, des crédits, huit outils. Voyez l’état de chacun avant de vous engager.", en: "One account, credits, eight tools. See the status of each before you commit." },
    cartes: ["accroche", "workstudio", "rag", "privacy", "cta"],
  },
  quebec: { // carrousel B : le contrôle
    titre: { fr: "Vous gardez le contrôle", en: "You stay in control" },
    principal: { fr: "Sur place ou hébergé au Québec : vos données restent là où vous les mettez.", en: "On premises or hosted in Québec: your data stays where you put it." },
    cartes: ["accroche", "sur-place", "heberge", "entrainement", "cta"],
  },
};

/** Annonces vidéo : plans fixes numérotés, avec durée, mouvement suggéré et texte. */
export const VIDEO6 = [
  { n: 1, t: "0 à 2 s", plan: "aurore", texte: { fr: "Rêvez grand.", en: "Dream big." }, mouvement: "Poussée lente de 4 %, les carrés de la mosaïque s’allument un à un." },
  { n: 2, t: "2 à 4 s", plan: "phare", texte: { fr: "Gardez le contrôle.", en: "Stay in control." }, mouvement: "Le faisceau du phare balaie de gauche à droite (translation de 6 %)." },
  { n: 3, t: "4 à 6 s", plan: "fin", texte: { fr: "Planifier un diagnostic", en: "Book a diagnostic" }, mouvement: "Le logo apparaît sans mouvement ; le bouton s’allume ; tenue de 1,5 s." },
];
export const VIDEO15 = [
  { n: 1, t: "0 à 2,5 s", plan: "aurore", texte: { fr: "Rêvez grand.", en: "Dream big." }, mouvement: "Poussée lente de 4 %." },
  { n: 2, t: "2,5 à 5 s", plan: "huit", texte: { fr: "Un compte. Tous vos outils.", en: "One account. All your tools." }, mouvement: "Les huit glyphes s’allument en cascade, de gauche à droite." },
  { n: 3, t: "5 à 7,5 s", plan: "workstudio", texte: { fr: "Décrivez-le. Il prend forme.", en: "Describe it. It takes shape." }, mouvement: "La mosaïque se rassemble autour du glyphe." },
  { n: 4, t: "7,5 à 10 s", plan: "privacy", texte: { fr: "Vous décidez de ce qui sort.", en: "You decide what leaves." }, mouvement: "Faisceau du phare, balayage lent." },
  { n: 5, t: "10 à 12,5 s", plan: "quebec", texte: { fr: "IA souveraine au Québec.", en: "Sovereign AI, made in Québec." }, mouvement: "Brume qui dérive vers la droite." },
  { n: 6, t: "12,5 à 15 s", plan: "fin", texte: { fr: "Planifier un diagnostic", en: "Book a diagnostic" }, mouvement: "Logo fixe ; le bouton s’allume ; tenue de 2 s." },
];

export function verifier() {
  const err = [];
  for (const a of ACCROCHES) for (const l of ["fr", "en"]) {
    if ([...a.titre[l]].length > LIMITES.titre) err.push(`${a.id}.${l} titre ${[...a.titre[l]].length} > ${LIMITES.titre}`);
    if ([...a.principal[l]].length > LIMITES.principal) err.push(`${a.id}.${l} principal ${[...a.principal[l]].length} > ${LIMITES.principal}`);
    if ([...a.description[l]].length > LIMITES.description) err.push(`${a.id}.${l} description ${[...a.description[l]].length} > ${LIMITES.description}`);
  }
  for (const [k, c] of Object.entries(CARROUSELS)) for (const l of ["fr", "en"]) {
    if ([...c.titre[l]].length > LIMITES.titre) err.push(`carrousel ${k}.${l} titre`);
    if ([...c.principal[l]].length > LIMITES.principal) err.push(`carrousel ${k}.${l} principal ${[...c.principal[l]].length}`);
  }
  return err;
}
