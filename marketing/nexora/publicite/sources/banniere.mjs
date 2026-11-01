// Bannières Web IAB (Google Display) : 9 formats × 2 concepts (rêve ; outil) × 2 langues, en HTML5 animé léger (CSS) et en PNG statique.
// Chaque bannière est un index.html autonome (police, logo officiel, image et mosaïque intégrés), avec clickTag et meta ad.size.
import fs from "node:fs";
import path from "node:path";
import { SRC, C, BARRES, TXT, mosaique, glyphe, esc, rendre } from "../../social/sources/moteur/marque.mjs";

const RACINE = path.resolve(import.meta.dirname, "..");
const IMG = path.join(import.meta.dirname, "bannieres-img");
const b64 = (f) => fs.readFileSync(f).toString("base64");
const FONT = b64(path.join(SRC, "polices", "geist-latin-wght-normal.woff2"));
const logoUri = (f) => `data:image/svg+xml;base64,${b64(path.join(SRC, "logos", f))}`;
export const TAILLES = [[300, 250], [336, 280], [728, 90], [970, 250], [160, 600], [300, 600], [320, 50], [320, 100], [468, 60]];
const split = (s) => [s.split(". ")[0] + ".", s.split(". ").slice(1).join(". ")];

const CONCEPTS = {
  reve: { l1: { fr: "Rêvez grand.", en: "Dream big." }, l2: { fr: "Gardez le contrôle.", en: "Stay in control." }, cta: { fr: "Planifier un diagnostic", en: "Book a diagnostic" }, court: { fr: "Planifier", en: "Book" } },
  outil: { l1: { fr: "Décrivez-le.", en: "Describe it." }, l2: { fr: "Il prend forme.", en: "It takes shape." }, cta: { fr: "Voir les solutions", en: "See the solutions" }, court: { fr: "Voir", en: "See" } },
};

/** Géométrie par format : tout en pixels, lisible (texte ≥ 11 px), logo complet ≥ 110 px sinon symbole seul. */
function mise(w, h) {
  const id = `${w}x${h}`;
  const P = {
    "300x250": { kind: "rect", p: 16, t: 31, cta: 13, bh: 32, logoW: 112 },
    "336x280": { kind: "rect", p: 18, t: 35, cta: 14, bh: 34, logoW: 116 },
    "300x600": { kind: "tall", p: 20, t: 44, cta: 15, bh: 40, logoW: 120 },
    "160x600": { kind: "sky", p: 12, t: 22, cta: 12, bh: 46, logoW: 112 },
    "728x90": { kind: "lead", p: 14, t: 25, cta: 14, bh: 38, logoW: 110 },
    "970x250": { kind: "bill", p: 28, t: 46, cta: 17, bh: 48, logoW: 140 },
    "468x60": { kind: "ban", p: 10, t: 15, cta: 12, bh: 34, sym: 30 },
    "320x100": { kind: "mob", p: 12, t: 21, cta: 12, bh: 28, sym: 30 },
    "320x50": { kind: "mini", p: 8, t: 13, cta: 11, bh: 34, sym: 30 },
  };
  return { id, ...P[id] };
}

function html(concept, w, h, lang) {
  const c = CONCEPTS[concept], g = mise(w, h);
  const l1 = c.l1[lang], l2 = c.l2[lang], cta = c.cta[lang];
  const photo = concept === "reve" ? `data:image/jpeg;base64,${b64(path.join(IMG, `aurore-${w}x${h}.jpg`))}` : null;
  const p = g.p;
  const horiz = ["lead", "bill", "ban", "mini"].includes(g.kind);
  const small = ["ban", "mini", "mob"].includes(g.kind);
  const logo = small
    ? `<img class="lg" alt="Nexora AI" src="${logoUri("nexora-ai-symbole-blanc.svg")}" width="${g.sym}" height="${g.sym}">`
    : `<img class="lg" alt="Nexora AI" src="${logoUri("nexora-ai-logo-blanc.svg")}" width="${g.logoW}" height="${Math.round(g.logoW / (285.55 / 52))}">`;
  // mosaïque : jamais sous le texte ; placée dans la zone libre du format
  const mos = {
    rect: { x: w * .46, y: 0, w: w * .54, h: h * .42 }, tall: { x: w * .3, y: 0, w: w * .7, h: h * .34 }, sky: { x: 0, y: h * .17, w, h: h * .3 },
    lead: { x: w * .56, y: 0, w: w * .17, h }, bill: { x: w * .46, y: 0, w: w * .3, h }, ban: null, mob: { x: w - 70, y: 0, w: 70, h }, mini: null,
  }[g.kind];
  const cell = Math.max(8, Math.round(Math.min(w, h) / 16));
  const mosSvg = mos ? mosaique({ ...mos, cell, seed: concept === "reve" ? 7 : 12, toward: g.kind === "sky" ? "bottom" : "right", fade: 1, opacity: concept === "reve" ? .95 : 1, style: "pointer-events:none" }) : "";
  const glyph = concept === "outil" && ["rect", "tall"].includes(g.kind) ? glyphe("workstudio", { size: g.kind === "bill" ? 110 : g.kind === "tall" ? 96 : 50 }) : "";
  const btn = g.kind === "sky" ? `<span class="bt">${esc(cta)}</span>` : g.kind === "mini"
    ? `<span class="bt bt-mini" aria-label="${esc(cta)}">${esc(c.court[lang])} &rarr;</span>`
    : `<span class="bt">${esc(cta)}<svg width="${g.cta}" height="${g.cta}" viewBox="0 0 20 20" aria-hidden="true" shape-rendering="crispEdges"><path d="M2 9h12V7h2v2h2v2h-2v2h-2v-2H2zM12 5h2v2h-2zm0 8h2v2h-2z" fill="#0A0A0E"/></svg></span>`;
  const txt = `<div class="hd"><span class="l1">${esc(l1)}</span><br><span class="l2">${esc(l2)}</span></div>`;
  // positions
  let lay = "";
  const R = (s) => (lay += s);
  if (g.kind === "rect" || g.kind === "tall") {
    R(`.lg{left:${p}px;top:${p}px}.gl{left:${p}px;top:${g.kind === "tall" ? 120 : 56}px}.hd{left:${p}px;bottom:${p + g.bh + 14}px;width:${w - 2 * p}px}.bt{left:${p}px;bottom:${p}px}`);
  } else if (g.kind === "sky") {
    R(`.lg{left:${p}px;top:${p}px}.hd{left:${p}px;top:${h * .5}px;width:${w - 2 * p}px}.bt{left:${p}px;bottom:${p}px;width:${w - 2 * p}px;white-space:normal;text-align:left;height:${g.bh + 8}px;line-height:1.15}`);
  } else if (g.kind === "lead") {
    R(`.lg{left:${p}px;top:${(h - 20) / 2}px}.hd{left:${p + 134}px;top:${(h - g.t * 2.1) / 2}px;white-space:nowrap}.bt{right:${p}px;top:${(h - g.bh) / 2}px}`);
  } else if (g.kind === "bill") {
    R(`.lg{left:${p}px;top:${p}px}.gl{left:${w * .5 + 70}px;top:${(h - 110) / 2}px}.hd{left:${p}px;bottom:${p + 8}px;width:${w * .5 - 2 * p}px}.bt{right:${p}px;top:${(h - g.bh) / 2}px}`);
  } else if (g.kind === "ban") {
    R(`.lg{left:${p}px;top:${(h - g.sym) / 2}px}.hd{left:${p + g.sym + 12}px;top:${(h - g.t * 2.1) / 2}px;white-space:nowrap}.bt{right:${p}px;top:${(h - g.bh) / 2}px}`);
  } else if (g.kind === "mob") {
    R(`.lg{left:${p}px;top:${p}px}.hd{left:${p + 40}px;top:${p}px;white-space:nowrap}.bt{left:${p + 40}px;bottom:${p}px}`);
  } else { // mini
    R(`.lg{left:${p}px;top:${(h - g.sym) / 2 + 1}px;width:${g.sym - 6}px;height:${g.sym - 6}px}.hd{left:${p + g.sym + 4}px;top:${(h - g.t * 2.1) / 2}px;white-space:nowrap}.bt{right:${p}px;top:${(h - g.bh) / 2}px}`);
  }
  const css = `
@font-face{font-family:G;src:url(data:font/woff2;base64,${FONT}) format("woff2");font-weight:100 900}
*{box-sizing:border-box;margin:0;padding:0}html,body{width:${w}px;height:${h}px;overflow:hidden;background:#0A0A0E}
#c{display:block;position:relative;width:${w}px;height:${h}px;overflow:hidden;text-decoration:none;cursor:pointer;border:1px solid #2a2a33;background:#0A0A0E;font-family:-apple-system,"Segoe UI",Helvetica,Arial,sans-serif}
#c>*{position:absolute}
.ph{inset:0;width:100%;height:100%;object-fit:cover;animation:zoom 8s ease-out both}
.vl{inset:0;background:${concept === "reve" ? (["tall", "sky", "rect", "mob"].includes(g.kind) ? "linear-gradient(180deg,rgba(10,10,14,.15) 0%,rgba(10,10,14,.35) 40%,rgba(10,10,14,.92) 100%)" : "linear-gradient(90deg,rgba(10,10,14,.94) 0%,rgba(10,10,14,.78) 45%,rgba(10,10,14,.15) 100%)") : "radial-gradient(70% 90% at 90% 0%,rgba(255,90,31,.20),transparent 70%)"}}
.hd{font-family:G,"Helvetica Neue",Arial,sans-serif;font-weight:500;letter-spacing:-.03em;line-height:1.04;color:#F5F4EF;font-size:${g.t}px;animation:up .6s .15s ease-out both}
.l2{color:#FF7A45;display:inline-block;animation:up .6s .9s ease-out both}
.bt{display:inline-flex;align-items:center;gap:8px;background:#FF5A1F;color:#0A0A0E;font-weight:600;font-size:${g.cta}px;line-height:1.1;padding:0 ${Math.round(g.cta * 1.1)}px;height:${g.bh}px;border-radius:5px;white-space:nowrap;animation:up .5s 1.7s ease-out both,pulse 1s 3.4s ease-in-out 2}
.bt-mini{padding:0 10px;height:34px}
.lg{animation:fade .6s ease-out both}
.mo{animation:fade 1s .3s ease-out both}
.gl{animation:up .6s .5s ease-out both}
.bar{left:0;right:0;bottom:0;height:3px;display:flex}.bar i{flex:1}
${lay}
@keyframes up{from{opacity:0;transform:translateY(10px)}}
@keyframes fade{from{opacity:0}}
@keyframes zoom{from{transform:scale(1)}to{transform:scale(1.06)}}
@keyframes pulse{50%{filter:brightness(1.18)}}
@media (prefers-reduced-motion:reduce){*{animation:none!important}}`;
  return `<!doctype html><html lang="${lang}"><head><meta charset="utf-8"><meta name="ad.size" content="width=${w},height=${h}"><title>Nexora AI ${concept} ${w}x${h}</title><style>${css}</style></head><body>
<a id="c" href="#" onclick="window.open(window.clickTag||'#','_blank');return false" aria-label="${esc(l1 + " " + l2 + " " + cta)}">
${photo ? `<img class="ph" alt="" src="${photo}">` : ""}<div class="vl"></div>${mosSvg ? mosSvg.replace("<svg ", '<svg class="mo" ') : ""}${glyph ? `<div class="gl">${glyph}</div>` : ""}${logo}${txt}${btn}<div class="bar">${BARRES.map((b) => `<i style="background:${b}"></i>`).join("")}</div>
</a><script>var clickTag="";</script></body></html>`;
}

export function toutBannieres() {
  const out = [];
  for (const concept of Object.keys(CONCEPTS)) for (const lang of ["fr", "en"]) for (const [w, h] of TAILLES) {
    const nom = `${concept}-${w}x${h}.${lang}`;
    const dir = path.join(RACINE, "final", "display", "html5", nom);
    out.push({ id: nom, w, h, html: html(concept, w, h, lang), htmlPath: path.join(dir, "index.html"), out: path.join(RACINE, "final", "display", "png", `${nom}.png`), statique: true, wait: 300 });
  }
  return out;
}
