// TikTok : profil et trois couvertures 1080×1920.
import { C, TXT, outil, mosaique, esc } from "./moteur/marque.mjs";
import { titre2 } from "./moteur/compo.mjs";
import { story } from "./moteur/modeles.mjs";
import { F, profil } from "./fb.mjs";
const LANGS = ["fr", "en"];
const split = (s) => [s.split(". ")[0] + ".", s.split(". ").slice(1).join(". ")];
export function couvertures(lang) {
  const [a, b] = split(TXT.campagne[lang]), fr = lang === "fr";
  const defs = [
    ["01-reve", { lang, plan: { nom: "aurore-vertical", pos: "50% 40%", voiles: ["bas2"] }, titre: titre2(a, b), kicker: fr ? "Le lancement" : "The launch" }],
    ["02-un-compte", { lang, mos: [{ x: 480, y: 0, w: 600, h: 380, cell: 30, seed: 7, toward: "right", fade: 1, opacity: .8 }], titre: titre2(fr ? "Un compte." : "One account.", fr ? "Tous vos outils." : "All your tools."), sous: fr ? "Huit outils, un seul accès." : "Eight tools, one access.", grilleHuit: true }],
    ["03-creative", { lang, plan: { nom: "braises-montantes", pos: "50% 50%", voiles: ["bas2"] }, pastilleOutil: outil("creative"), titre: esc(outil("creative").titre[lang]), sous: outil("creative").sous[lang] }],
  ];
  return defs.map(([id, s]) => F.piece({ id: `couverture-${id}.${lang}`, sousDossier: "tiktok", w: 1080, h: 1920, lang, body: story(s) }));
}
export function toutTiktok() { return [profil("profil", "tiktok"), ...LANGS.flatMap(couvertures)]; }
