// Actifs graphiques du gabarit PowerPoint : mosaïques et pastilles en PNG transparents (générées par le moteur, graine fixe).
import { M, IM } from "../../../identite/sources/moteur.mjs";
import { join } from "node:path";
import { mkdirSync } from "node:fs";
const OUT = join(IM, "sources", "presentation", "actifs"), HTML = join(IM, "sources", "html", "presentation");
mkdirSync(OUT, { recursive: true }); mkdirSync(HTML, { recursive: true });
const nav = await M.navigateur();
const css = "html,body,.page{background:transparent!important}";
const mm = (px) => (px / 96) * 25.4;
async function mosa(nom, wPx, hPx, opts) {
  const w = mm(wPx), h = mm(hPx), f = { w, h, fond: 0 };
  await M.produire(nav, { dossierHtml: HTML, nom, pages: [M.feuille({ ...f, fondArt: M.mosaique({ ...opts, ancre: opts.ancre || "xMidYMid" }) })], taille: f, css, png: join(OUT, nom + ".png"), dpi: 192, transparent: true });
}
// diapositive 13,333 x 7,5 po = 1280 x 720 px CSS ; PNG à 2x
await mosa("mosaique-titre", 640, 720, { cols: 16, rows: 18, seed: 3, vers: "right", fade: 0.96, gap: 0.09, keep: (c) => c.col >= 3, ancre: "xMaxYMid" });
await mosa("mosaique-section", 1280, 240, { cols: 64, rows: 12, seed: 8, vers: "bottom", fade: 0.97, gap: 0.1, ancre: "xMidYMax" });
await mosa("mosaique-fin", 560, 720, { cols: 14, rows: 18, seed: 12, vers: "right", fade: 0.96, gap: 0.09, keep: (c) => c.col >= 2, ancre: "xMaxYMid" });
for (const [i, o] of M.OUTILS.entries()) await mosa(`pastille-${o.id}`, 120, 120, { cols: 5, rows: 5, seed: i * 7 + 3, palette: o.palette, fade: 0, gap: 0.1, vers: "center" });
await nav.close();
