// Images Open Graph 1200×630 pour les pages principales du site (fr-CA et en-CA).
import path from "node:path";
import { famille, C, TXT, mosaique, grille, regle, grain, voile, logo, glyphe, esc, OUTILS } from "../../social/sources/moteur/marque.mjs";
import { fondPhoto, fondMosaique, titre2, grilleOutils } from "../../social/sources/moteur/compo.mjs";
const P = famille({ dossier: path.resolve(import.meta.dirname, "..") });

const PAGES = [
  { id: "accueil", kicker: { fr: "Nexora AI", en: "Nexora AI" }, l1: { fr: "L’IA qui travaille\npour votre entreprise.", en: "AI that works\nfor your business." }, big: 1, l2: { fr: "Sous votre contrôle.", en: "Under your control." }, sous: { fr: "IA souveraine au Québec.", en: "Sovereign AI, made in Québec." }, vis: "photo" },
  { id: "solutions", kicker: { fr: "Solutions", en: "Solutions" }, l1: { fr: "Bâties pour", en: "Built for" }, l2: { fr: "votre métier.", en: "your business." }, sous: { fr: "Configurées après un diagnostic, avec vous.", en: "Configured with you, after a diagnostic." }, vis: "mosaique", seed: 3 },
  { id: "apps", kicker: { fr: "Nexora Apps", en: "Nexora Apps" }, l1: { fr: "Un compte.", en: "One account." }, l2: { fr: "Tous vos outils.", en: "All your tools." }, sous: { fr: "L’état de chacun, écrit en toutes lettres.", en: "The status of each, spelled out plainly." }, vis: "huit" },
  { id: "creative", kicker: { fr: "Nexora Creative", en: "Nexora Creative" }, l1: { fr: "Imaginez. Voyez.", en: "Imagine. See." }, l2: { fr: "Entendez.", en: "Hear." }, sous: { fr: "Image, son et vidéo pour votre marketing. Étape ultérieure.", en: "Image, sound and video for your marketing. A later stage." }, vis: "glyphe", glyph: "creative", seed: 5 },
  { id: "vps", kicker: { fr: "VPS au Québec", en: "VPS in Québec" }, l1: { fr: "Votre serveur.", en: "Your server." }, l2: { fr: "Votre territoire.", en: "Your territory." }, sous: { fr: "Serveurs privés virtuels, avec l’application de votre choix.", en: "Virtual private servers, with the app of your choice." }, vis: "salle", palette: "or", seed: 7 },
  { id: "modeles", kicker: { fr: "Modèles et API", en: "Models and API" }, l1: { fr: "Une seule passerelle", en: "One gateway" }, l2: { fr: "vers les modèles.", en: "to the models." }, sous: { fr: "La résidence des données est affichée.", en: "Data residency is shown for each model." }, vis: "mosaique", palette: "ciel", seed: 9 },
  { id: "tarifs", kicker: { fr: "Tarifs", en: "Pricing" }, l1: { fr: "Des crédits,", en: "Credits," }, l2: { fr: "clairement.", en: "made clear." }, sous: { fr: "L’abonnement, les crédits et ce qu’ils couvrent.", en: "The subscription, the credits and what they cover." }, vis: "mosaique", seed: 11 },
  { id: "contact", kicker: { fr: "Contact", en: "Contact" }, l1: { fr: "Planifier", en: "Book" }, l2: { fr: "un diagnostic.", en: "a diagnostic." }, sous: { fr: "Parlons de votre projet, sans engagement.", en: "Let’s talk about your project, no commitment." }, vis: "photo2" },
];

export function og(pg, lang) {
  const w = 1200, h = 630, m = 72;
  let fond;
  if (pg.vis === "photo") fond = fondPhoto({ w, h, nom: "aurore-foret", pos: "62% 40%", voiles: ["gauche"], mos: { x: w * .62, y: 90, w: w * .38, h: 440, cell: 26, seed: 21, toward: "right", fade: 1, opacity: .9 } });
  else if (pg.vis === "photo2") fond = fondPhoto({ w, h, nom: "ville-crepuscule", pos: "50% 60%", voiles: ["gauche"], mos: { x: w * .62, y: 90, w: w * .38, h: 440, cell: 26, seed: 23, toward: "right", fade: 1, opacity: .85 } });
  else if (pg.vis === "salle") fond = fondPhoto({ w, h, nom: "salle-calcul", pos: "50% 50%", voiles: ["gauche"], mos: { x: w * .62, y: 90, w: w * .38, h: 440, cell: 26, seed: pg.seed, toward: "right", fade: 1, palette: "or", opacity: .85 } });
  else if (pg.vis === "huit") fond = fondMosaique({ w, h }) + grilleOutils({ x: w * .56, y: 100, w: w * .44 - m, h: h - 200, cols: 2, k: .8, lang, glyph: 50, horizontal: true, label: 21 });
  else if (pg.vis === "glyphe") fond = fondMosaique({ w, h, mos: { x: w * .5, y: 0, w: w * .5, h, cell: 28, seed: pg.seed, toward: "right", fade: 1 } }) + `<div style="position:absolute;right:${m}px;top:${(h - 300) / 2}px;width:300px;height:300px;background:${C.noir};border:1px solid rgba(245,244,239,.26);display:flex;align-items:center;justify-content:center">${glyphe(pg.glyph, { size: 190 })}</div>`;
  else fond = fondMosaique({ w, h, mos: { x: w * .5, y: 0, w: w * .5, h, cell: 28, seed: pg.seed, toward: "right", fade: 1, palette: pg.palette ?? "braise" } });
  const body = `${fond}${regle({ w, k: 1, side: "bottom" })}${logo({ type: "complet", ton: "blanc", h: 40, x: m, y: m })}
  <div style="position:absolute;left:${m}px;bottom:${m + 18}px;width:${w * .58}px;display:flex;flex-direction:column;gap:22px">
    <div class="lib" style="font-size:22px;color:${C.orTxt}">${esc(pg.kicker[lang])}</div>
    <div class="aff" data-fit style="font-size:${pg.big ? 66 : 74}px;max-height:${pg.big ? 270 : 240}px;overflow:hidden">${titre2(pg.l1[lang], pg.l2[lang])}</div>
    <div class="txt" data-fit style="font-size:28px;color:${C.gris};max-height:84px;overflow:hidden">${esc(pg.sous[lang])}</div>
  </div>`;
  return P.piece({ id: `og-${pg.id}.${lang}`, sousDossier: "og", w, h, lang, body, title: `${pg.kicker[lang]} | Nexora AI` });
}
export function toutOg() { return PAGES.flatMap((p) => ["fr", "en"].map((l) => og(p, l))); }
