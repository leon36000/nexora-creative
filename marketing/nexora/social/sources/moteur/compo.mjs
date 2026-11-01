// Compositions réutilisables : fonds (photo, mosaïque, aurore), bandeaux, titres. Au-dessus de marque.mjs.
import { C, BARRES, TXT, OUTILS, outil, mosaique, grille, regle, bande, cadre, grain, photo, voile, logo, glyphe, pastille, bouton, esc } from "./marque.mjs";

export const VOILES = {
  bas: "linear-gradient(180deg,rgba(10,10,14,.30) 0%,rgba(10,10,14,0) 26%,rgba(10,10,14,.72) 66%,#0A0A0E 100%)",
  bas2: "linear-gradient(180deg,rgba(10,10,14,.0) 0%,rgba(10,10,14,.0) 38%,rgba(10,10,14,.82) 72%,#0A0A0E 100%)",
  haut: "linear-gradient(0deg,rgba(10,10,14,.30) 0%,rgba(10,10,14,0) 26%,rgba(10,10,14,.72) 66%,#0A0A0E 100%)",
  gauche: "linear-gradient(90deg,#0A0A0E 0%,rgba(10,10,14,.86) 34%,rgba(10,10,14,.25) 68%,rgba(10,10,14,0) 100%)",
  droite: "linear-gradient(270deg,#0A0A0E 0%,rgba(10,10,14,.86) 34%,rgba(10,10,14,.25) 68%,rgba(10,10,14,0) 100%)",
  centre: "radial-gradient(70% 90% at 50% 52%,rgba(10,10,14,.62) 0%,rgba(10,10,14,.30) 70%,rgba(10,10,14,.5) 100%)",
  plein: "rgba(10,10,14,.52)",
  vignette: "radial-gradient(120% 120% at 50% 50%,rgba(10,10,14,0) 50%,rgba(10,10,14,.7) 100%)",
  aucun: "transparent",
};

/** Fond photographique : plan généré, voile(s) de lisibilité, mosaïque optionnelle, grain. */
export function fondPhoto({ w, h, nom, pos = "50% 50%", scale = 1, voiles = ["bas"], mos = [], grainOp = 0.09, filtre = "", base = C.noir }) {
  const vs = voiles.map((v) => voile(VOILES[v] ?? v)).join("");
  const ms = (Array.isArray(mos) ? mos : [mos]).filter(Boolean).map((m) => mosaique(m)).join("");
  return `<div aria-hidden="true" style="position:absolute;inset:0;background:${base}"></div>${photo(nom, { pos, scale, filter: filtre })}${vs}${ms}${grain(grainOp)}`;
}
/** Fond « code seul » : noir profond, lueur braise douce, grille de mesure, mosaïque. */
export function fondMosaique({ w, h, k = 1, mos = [], lueur = "radial-gradient(60% 70% at 85% 10%,rgba(255,90,31,.20),transparent 70%),radial-gradient(50% 60% at 0% 110%,rgba(74,135,255,.10),transparent 70%)", grid = true, gridSize = 64, ruler = false, grainOp = 0.07, base = C.noir, gridMask }) {
  const ms = (Array.isArray(mos) ? mos : [mos]).filter(Boolean).map((m) => mosaique(m)).join("");
  return `<div aria-hidden="true" style="position:absolute;inset:0;background:${base}"></div>${voile(lueur)}${grid ? grille({ size: gridSize * k, opacity: 0.07, ...(gridMask ? { mask: gridMask } : {}) }) : ""}${ms}${ruler ? regle({ w, k, side: "bottom", y: 0 }) : ""}${grain(grainOp)}`;
}

/** Titre en deux temps : la seconde phrase en orange de texte (jamais sur la mosaïque). */
export const titre2 = (a, b) => `<span style="white-space:nowrap">${esc(a).replace(/\n/g, "<br>")}</span><br><span style="color:${C.orTxt};white-space:nowrap">${esc(b)}</span>`;
export const br = (s) => esc(s).replace(/\n/g, "<br>");

/** Grille des huit glyphes (pastilles carrées) : « un compte, tous vos outils ». */
export function grilleOutils({ x, y, w, h, cols = 4, k = 1, lang, libelle = true, ligne = "rgba(245,244,239,.2)", glyph = 56, horizontal = false, label = 20 }) {
  const rows = Math.ceil(OUTILS.length / cols);
  const cw = w / cols, ch = h / rows;
  const cells = OUTILS.map((o, i) => {
    const cx = (i % cols) * cw, cy = Math.floor(i / cols) * ch;
    const inner = horizontal
      ? `<div style="display:flex;align-items:center;gap:${24 * k}px;height:100%">${glyphe(o.id, { size: glyph * k })}${libelle ? `<div class="lib" style="font-size:${label * k}px;color:${C.clair};line-height:1.2">${esc(o.court)}</div>` : ""}</div>`
      : `${glyphe(o.id, { size: glyph * k })}${libelle ? `<div class="lib" style="font-size:${label * k}px;color:${C.clair};line-height:1.2">${esc(o.court)}</div>` : ""}`;
    return `<div style="position:absolute;left:${cx}px;top:${cy}px;width:${cw}px;height:${ch}px;border-right:${i % cols === cols - 1 ? 0 : 1}px solid ${ligne};border-bottom:${Math.floor(i / cols) === rows - 1 ? 0 : 1}px solid ${ligne};display:flex;flex-direction:column;align-items:flex-start;justify-content:${horizontal ? "center" : "space-between"};padding:${22 * k}px">${inner}</div>`;
  }).join("");
  return `<div style="position:absolute;left:${x}px;top:${y}px;width:${w}px;height:${h}px;border:1px solid ${ligne}">${cells}</div>`;
}

/** Met chaque phrase sur sa ligne (« Décrivez-le. Il prend forme. » devient deux lignes). */
export const lignes = (t) => esc(t).replace(/\. (?=[A-ZÉÈÀÂÎÔ])/g, ".<br>");
