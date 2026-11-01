// X : en-tête 1500×500 et 4 images 1600×900.
import path from "node:path";
import { C, TXT, OUTILS, outil, mosaique, grille, regle, cadre, grain, voile, logo, glyphe, pastille, bouton, esc } from "./moteur/marque.mjs";
import { fondPhoto, fondMosaique, titre2, grilleOutils } from "./moteur/compo.mjs";
import { F } from "./fb.mjs";
const LANGS = ["fr", "en"];
const split = (s) => [s.split(". ")[0] + ".", s.split(". ").slice(1).join(". ")];

export function entete(lang) {
  const w = 1500, h = 500, [c1, c2] = split(TXT.campagne[lang]);
  // la photo de profil recouvre le bas gauche (x < 400, y > 300) : tout reste à droite
  const body = fondPhoto({ w, h, nom: "aurore-foret", pos: "50% 30%", voiles: ["gauche"], grainOp: .1, mos: { x: 0, y: 0, w: 420, h, cell: 24, seed: 401, toward: "left", fade: 1, opacity: .85 } })
    + `<div style="position:absolute;left:470px;top:0;height:${h}px;width:880px;display:flex;flex-direction:column;justify-content:center;gap:24px">
    ${logo({ type: "complet", ton: "blanc", h: 34, style: "position:static" })}
    <div class="aff" data-fit style="font-size:84px;max-height:190px;overflow:hidden">${titre2(c1, c2)}</div>
    <div class="lib" style="font-size:18px;color:${C.gris}">${esc(TXT.quebecCourt[lang])}</div></div>`;
  return F.piece({ id: `entete.${lang}`, sousDossier: "x", w, h, lang, body });
}
export function images(lang) {
  const w = 1600, h = 900, m = 90, fr = lang === "fr", [c1, c2] = split(TXT.campagne[lang]);
  const txt = (t, s, kick, ww = .58) => `<div style="position:absolute;left:${m}px;bottom:${m + 20}px;width:${w * ww}px;display:flex;flex-direction:column;gap:26px">${kick ? `<div class="lib" style="font-size:30px;color:${C.orTxt}">${esc(kick)}</div>` : ""}<div class="aff" data-fit style="font-size:108px;max-height:340px;overflow:hidden">${t}</div>${s ? `<div class="txt" data-fit style="font-size:42px;color:${C.gris};max-height:140px;overflow:hidden">${esc(s)}</div>` : ""}</div>`;
  const head = logo({ type: "complet", ton: "blanc", h: 42, x: m, y: m });
  return [
    fondPhoto({ w, h, nom: "aurore-foret", pos: "60% 40%", voiles: ["gauche"], mos: { x: w * .6, y: 120, w: w * .4, h: 480, cell: 30, seed: 411, toward: "right", fade: 1, opacity: .9 } }) + head + txt(titre2(c1, c2), TXT.quebec[lang]),
    fondMosaique({ w, h }) + head + grilleOutils({ x: w * .5, y: 130, w: w * .5 - m, h: h - 260, cols: 2, k: 1.1, lang, glyph: 66, horizontal: true, label: 30 }) + txt(titre2(fr ? "Un compte." : "One account.", fr ? "Tous vos outils." : "All your tools."), fr ? "Huit outils, des crédits, un seul accès." : "Eight tools, credits, one access.", null, .42),
    fondPhoto({ w, h, nom: "fleuve-aube", pos: "50% 50%", voiles: ["gauche"] }) + head + txt(esc(TXT.quebec[lang]), fr ? "Chez vous ou au Québec. Jamais utilisées pour entraîner un modèle." : "With you or in Québec. Never used to train a model."),
    fondPhoto({ w, h, nom: "phare", pos: "50% 50%", voiles: ["gauche"] }) + head + txt(esc(outil("privacy").titre[lang]), outil("privacy").sous[lang], outil("privacy").nom),
  ].map((b, i) => F.piece({ id: `image-${i + 1}-sur-4.${lang}`, sousDossier: "x", w, h, lang, body: b }));
}
export function toutX() { return LANGS.flatMap((l) => [entete(l), ...images(l)]); }
