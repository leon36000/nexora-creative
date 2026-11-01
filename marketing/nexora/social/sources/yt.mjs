// YouTube : bannière 2560×1440 (zone sûre 1546×423 au centre), 8 vignettes 1280×720, cartes de fin 1920×1080.
import path from "node:path";
import { C, TXT, OUTILS, outil, mosaique, grille, regle, cadre, grain, voile, logo, glyphe, pastille, bouton, esc, BARRES, coordonnees } from "./moteur/marque.mjs";
import { fondPhoto, fondMosaique, titre2, lignes } from "./moteur/compo.mjs";
import { PLAN } from "./moteur/modeles.mjs";
import { F } from "./fb.mjs";
const LANGS = ["fr", "en"];
const split = (s) => [s.split(". ")[0] + ".", s.split(". ").slice(1).join(". ")];

export function banniere(lang) {
  const w = 2560, h = 1440, [c1, c2] = split(TXT.campagne[lang]);
  const zx = (w - 1546) / 2, zy = (h - 423) / 2;
  const body = fondPhoto({ w, h, nom: "aurore-foret", pos: "50% 38%", voiles: ["centre", "vignette"], grainOp: .1,
    mos: [{ x: 0, y: h - 420, w: w, h: 420, cell: 40, seed: 501, toward: "bottom", fade: 1, opacity: .55 }] })
    + `<div style="position:absolute;left:${zx}px;top:${zy}px;width:1546px;height:423px;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:26px;text-align:center">
    ${logo({ type: "complet", ton: "blanc", h: 52, style: "position:static" })}
    <div class="aff" data-fit style="font-size:112px;max-height:240px;overflow:hidden">${titre2(c1, c2)}</div></div>`;
  return F.piece({ id: `banniere.${lang}`, sousDossier: "youtube", w, h, lang, body });
}

/** Vignettes : un titre énorme (4 à 5 mots), un glyphe, un plan. Lisibles à 168 px de large. */
export function vignettes(lang) {
  const w = 1280, h = 720, m = 64;
  return OUTILS.map((o, i) => {
    const photoSide = i % 2 === 0;
    const fond = photoSide
      ? fondPhoto({ w, h, nom: PLAN[o.id].nom, pos: PLAN[o.id].pos, voiles: ["gauche"], mos: { x: w * .6, y: 0, w: w * .4, h, cell: 28, seed: 510 + i, toward: "right", fade: 1, opacity: .85 } })
      : fondMosaique({ w, h, mos: { x: w * .64, y: 0, w: w * .36, h, cell: 28, seed: 520 + i, toward: "right", fade: 1 } });
    const body = `${fond}
      <div style="position:absolute;left:${m}px;top:${m}px">${pastille(o, lang, { k: .9, etat: false })}</div>
      <div style="position:absolute;right:${m}px;bottom:${m}px;background:${C.noir};padding:22px;border:1px solid rgba(245,244,239,.26)">${glyphe(o.id, { size: 150 })}</div>
      <div class="aff" data-fit style="position:absolute;left:${m}px;bottom:${m}px;width:${w * .62}px;font-size:124px;max-height:420px;overflow:hidden;line-height:.98">${lignes(o.titre[lang])}</div>`;
    return F.piece({ id: `vignette-${String(i + 1).padStart(2, "0")}-${o.id}.${lang}`, sousDossier: "youtube/vignettes", w, h, lang, body });
  });
}

/** Carte de fin 1920×1080 : deux emplacements vidéo et un d'abonnement (cadres de filets), texte hors des zones. */
export function carteFin(lang) {
  const w = 1920, h = 1080, fr = lang === "fr", [c1, c2] = split(TXT.campagne[lang]);
  const slot = (x, y, ww, hh, lib) => `${cadre({ x, y, w: ww, h: hh, k: 1.3, color: "rgba(245,244,239,.3)" })}<div class="lib" style="position:absolute;left:${x + 22}px;top:${y + 20}px;font-size:19px;color:${C.gris}">${esc(lib)}</div>`;
  const body = fondMosaique({ w, h, mos: [{ x: 0, y: h - 260, w, h: 260, cell: 36, seed: 531, toward: "bottom", fade: 1, opacity: .5 }] })
    + `${logo({ type: "complet", ton: "sombre", h: 44, x: 96, y: 84 })}
    <div class="aff" data-fit style="position:absolute;left:96px;top:190px;width:760px;font-size:104px;max-height:320px;overflow:hidden">${titre2(c1, c2)}</div>
    <div class="txt" style="position:absolute;left:96px;top:540px;font-size:34px;color:${C.gris};width:700px">${esc(TXT.signature[lang])}</div>
    ${slot(940, 170, 880, 495, fr ? "Emplacement : vidéo" : "Slot: video")}
    ${slot(940, 700, 420, 236, fr ? "Emplacement : vidéo" : "Slot: video")}
    ${slot(1400, 700, 420, 236, fr ? "Emplacement : abonnement" : "Slot: subscribe")}
    <div class="lib" style="position:absolute;left:96px;bottom:84px;font-size:21px;color:${C.gris}">${esc(coordonnees.site)}</div>`;
  return F.piece({ id: `carte-de-fin.${lang}`, sousDossier: "youtube", w, h, lang, body });
}
export function toutYoutube() { return LANGS.flatMap((l) => [banniere(l), ...vignettes(l), carteFin(l)]); }
