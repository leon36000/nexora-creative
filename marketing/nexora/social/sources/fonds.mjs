// Arrière-plans : visioconférence 1920×1080 (4 ambiances, avec et sans symbole discret), fonds d'écran ordinateur 3840×2160 (6)
// et téléphone 1290×2796 (6). Calmes au centre, sans texte : ils restent beaux derrière une fenêtre ou un visage.
import fs from "node:fs";
import path from "node:path";
import { C, SRC, logo, grille, regle, grain, voile, mosaique } from "./moteur/marque.mjs";
import { fondPhoto, fondMosaique } from "./moteur/compo.mjs";
import { F } from "./fb.mjs";

// utilise la version agrandie (×4 Real-ESRGAN, nom-4k) si elle existe
const nom4k = (n) => (fs.existsSync(path.join(SRC, "generees", `${n}-4k.png`)) ? `${n}-4k` : n);

export function visio() {
  const w = 1920, h = 1080;
  const amb = [
    ["aurore", () => fondPhoto({ w, h, nom: "aurore-lac", pos: "50% 50%", voiles: ["vignette"], filtre: "blur(1.2px) brightness(1.35)", grainOp: .1 })],
    ["atelier", () => fondPhoto({ w, h, nom: "atelier", pos: "50% 55%", voiles: ["vignette"], filtre: "blur(2px) brightness(1.15)", grainOp: .1 })],
    ["ville", () => fondPhoto({ w, h, nom: "ville-crepuscule", pos: "50% 60%", voiles: ["vignette"], filtre: "blur(1.5px) brightness(1.3)", grainOp: .1 })],
    ["mosaique", () => fondMosaique({ w, h, grid: true, lueur: "radial-gradient(60% 70% at 50% 120%,rgba(255,90,31,.18),transparent 70%)", mos: [
      { x: 0, y: 0, w: 420, h, cell: 30, seed: 701, toward: "left", fade: 1, opacity: .75 },
      { x: w - 420, y: 0, w: 420, h, cell: 30, seed: 702, toward: "right", fade: 1, opacity: .75 }] })],
  ];
  const out = [];
  for (const [id, f] of amb) {
    out.push(F.piece({ id: `visio-${id}`, sousDossier: "fonds/visioconference", w, h, body: f(), fit: false }));
    out.push(F.piece({ id: `visio-${id}-symbole`, sousDossier: "fonds/visioconference", w, h, body: f() + `<div style="opacity:.9">${id === "mosaique" ? logo({ type: "symbole", ton: "blanc", h: 52, x: (w - 52) / 2, bottom: 56 }) : logo({ type: "symbole", ton: "blanc", h: 52, right: 64, bottom: 64 })}</div>`, fit: false }));
  }
  return out;
}
export function bureau() {
  const w = 3840, h = 2160;
  const list = [
    ["aurore-foret", () => fondPhoto({ w, h, nom: nom4k("aurore-foret"), pos: "50% 45%", voiles: ["vignette"], grainOp: .1 })],
    ["aurore-lac", () => fondPhoto({ w, h, nom: nom4k("aurore-lac"), pos: "50% 50%", voiles: ["vignette"], grainOp: .1 })],
    ["fleuve-aube", () => fondPhoto({ w, h, nom: nom4k("fleuve-aube"), pos: "50% 50%", voiles: ["vignette"], grainOp: .1 })],
    ["ville-crepuscule", () => fondPhoto({ w, h, nom: nom4k("ville-crepuscule"), pos: "50% 55%", voiles: ["vignette"], grainOp: .1 })],
    ["cabane-neige", () => fondPhoto({ w, h, nom: nom4k("cabane-neige"), pos: "50% 55%", voiles: ["vignette"], grainOp: .1, filtre: "brightness(1.35)" })],
    ["mosaique-braise", () => fondMosaique({ w, h, gridSize: 96, ruler: false, mos: [{ x: 0, y: 0, w: w, h: h * .5, cell: 48, seed: 711, toward: "bottom", fade: 1, opacity: .85 }], lueur: "radial-gradient(50% 60% at 50% 110%,rgba(255,90,31,.14),transparent 70%)" })],
  ];
  return list.map(([id, f]) => F.piece({ id: `ordinateur-${id}`, sousDossier: "fonds/ordinateur", w, h, body: f(), fit: false }));
}
export function telephone() {
  const w = 1290, h = 2796;
  const list = [
    ["aurore", () => fondPhoto({ w, h, nom: nom4k("aurore-vertical"), pos: "50% 50%", voiles: ["vignette"], grainOp: .1 })],
    ["phare", () => fondPhoto({ w, h, nom: nom4k("phare-vertical"), pos: "16% 50%", voiles: ["vignette"], grainOp: .1 })],
    ["ville", () => fondPhoto({ w, h, nom: nom4k("ville-vertical"), pos: "50% 50%", voiles: ["vignette"], grainOp: .1 })],
    ["foret-neige", () => fondPhoto({ w, h, nom: nom4k("foret-vertical"), pos: "12% 50%", voiles: ["vignette"], grainOp: .1 })],
    ["fleuve", () => fondPhoto({ w, h, nom: nom4k("fleuve-vertical"), pos: "50% 50%", voiles: ["vignette"], grainOp: .1 })],
    ["mosaique", () => fondMosaique({ w, h, gridSize: 86, mos: [{ x: 0, y: h * .45, w, h: h * .55, cell: 44, seed: 721, toward: "bottom", fade: 1, opacity: .9 }] })],
  ];
  return list.map(([id, f]) => F.piece({ id: `telephone-${id}`, sousDossier: "fonds/telephone", w, h, body: f(), fit: false }));
}
export function toutFonds() { return [...visio(), ...bureau(), ...telephone()]; }
