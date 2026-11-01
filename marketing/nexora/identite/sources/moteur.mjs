// Moteur de gabarits partagé de la direction artistique Nexora AI (identité, imprimés, social, publicité…).
//
// HTML/CSS/SVG rendu par Chromium (Playwright) en PNG et en PDF vectoriel. Tout part des logos officiels
// (jamais modifiés), des polices Geist / Inter / JetBrains Mono (fichiers locaux) et de la charte.
//
// Utilisation (bun) :
//   import { M } from "../../identite/sources/moteur.mjs";
//   const nav = await M.navigateur();
//   await M.rendre(nav, { html, dossierHtml, nom, pdf: "x.pdf", png: "x.png", largeurMm, hauteurMm, dpi: 300 });
//   await nav.close();
import { chromium } from "/home/pc6/Desktop/NexoraSite/web/node_modules/@playwright/test/index.mjs";
import { readFileSync, writeFileSync, mkdirSync, existsSync } from "node:fs";
import { dirname, join, relative, resolve } from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";
import { execFileSync } from "node:child_process";

const ICI = dirname(fileURLToPath(import.meta.url));
export const RACINE = resolve(ICI, "../.."); // .../marketing/nexora
export const ID = join(RACINE, "identite");
export const IM = join(RACINE, "imprimes");
export const POLICES = join(ICI, "polices");
export const LOGOS = join(ICI, "logos");
export const COORDONNEES = (() => { // --coordonnees f.json, ou NEXORA_COORDONNEES, ou coordonnees.json de la racine
  const i = process.argv.indexOf("--coordonnees");
  return i > 0 && process.argv[i + 1] ? resolve(process.argv[i + 1]) : process.env.NEXORA_COORDONNEES ? resolve(process.env.NEXORA_COORDONNEES) : join(RACINE, "coordonnees.json");
})();

// ---------------------------------------------------------------------------------------------------------------
// Couleurs de la charte (identique à globals.css du site)
export const C = {
  noir: "#0A0A0E", surface: "#121218", surface2: "#1B1B24", papier: "#FBFBF8", creme: "#F3F2EC", sable: "#E4E2D9",
  texteClair: "#F5F4EF", gris: "#A8A8B6", grisSombre: "#54545F", encre: "#121218",
  orange: "#FF5A1F", orangeSombre: "#FF7A45", orangeClair: "#B53A0A", nuit: "#11112A",
  braise: ["#FFD37A", "#FFB11A", "#FF8A1F", "#FF5A1F", "#E0341C", "#B01A3C"],
};
export const PALETTES = {
  braise: C.braise,
  ciel: ["#e1eeff", "#bcd7ff", "#8fbbff", "#5f9aff", "#3b74f2", "#2a54c4"],
  or: ["#fff3c4", "#ffe58a", "#ffd44d", "#ffc01f", "#f5a30b", "#d98505"],
  menthe: ["#def7ea", "#b4edd2", "#86e0b7", "#57cf98", "#34b27a", "#238d5f"],
  nuit: ["#1b1b2c", "#232338", "#2c2c47", "#36365a", "#44446f", "#565688"],
};

// ---------------------------------------------------------------------------------------------------------------
// Logos officiels : lus tels quels. On ne touche qu'à l'élément racine (classe, taille), jamais à la géométrie.
const VARIANTES_LOGO = {
  clair: "nexora-ai-logo.svg", sombre: "nexora-ai-logo-sombre.svg", noir: "nexora-ai-logo-noir.svg", blanc: "nexora-ai-logo-blanc.svg",
};
const VARIANTES_SYMBOLE = {
  clair: "nexora-ai-symbole.svg", sombre: "nexora-ai-symbole-sombre.svg", noir: "nexora-ai-symbole-noir.svg", blanc: "nexora-ai-symbole-blanc.svg",
};
export const logoBrut = (v) => readFileSync(join(LOGOS, VARIANTES_LOGO[v]), "utf8");
export const symboleBrut = (v) => readFileSync(join(LOGOS, VARIANTES_SYMBOLE[v]), "utf8");
const habille = (svg, cls, style) =>
  svg.replace(/ role="img" aria-label="[^"]*"/, ' aria-hidden="true"').replace("<svg ", `<svg class="${cls}" ${style ? `style="${style}" ` : ""}`);
/** Logo complet (viewBox 6 6 285.55 52, rapport 5,49). `v` : clair (sur fond clair) | sombre | noir | blanc. */
export const logo = (v, cls = "logo", style = "") => habille(logoBrut(v), cls, style);
/** Symbole seul (viewBox 6 6 52 52). */
export const symbole = (v, cls = "symbole", style = "") => habille(symboleBrut(v), cls, style);
export const RAPPORT_LOGO = 285.55 / 52;

// ---------------------------------------------------------------------------------------------------------------
// Mosaïque : port fidèle de web/src/components/brand/mosaic.tsx (mêmes hachage, dissolution et rampes).
export function hash(col, row, seed) {
  let h = Math.imul(col + 1, 73856093) ^ Math.imul(row + 1, 19349663) ^ Math.imul(seed + 1, 83492791);
  h = Math.imul(h ^ (h >>> 15), 2246822507);
  h = Math.imul(h ^ (h >>> 13), 3266489909);
  return ((h ^ (h >>> 16)) >>> 0) / 4294967296;
}
function avancee(col, row, cols, rows, vers) {
  const x = cols > 1 ? col / (cols - 1) : 0.5;
  const y = rows > 1 ? row / (rows - 1) : 0.5;
  if (Array.isArray(vers)) { // direction libre [dx, dy] : 1 côté plein, 0 côté qui se dissout
    const [dx, dy] = vers; const n = Math.hypot(dx, dy) || 1;
    const t = ((x - 0.5) * dx + (y - 0.5) * dy) / n; // -0.5..0.5 environ
    const m = (Math.abs(dx) + Math.abs(dy)) / (2 * n);
    return Math.max(0, Math.min(1, 0.5 + t / (2 * m)));
  }
  switch (vers) {
    case "right": return x; case "left": return 1 - x; case "bottom": return y; case "top": return 1 - y;
    case "center": return Math.max(0, 1 - Math.hypot((x - 0.5) * 2, (y - 0.5) * 2) / 1.2);
    case "bords": return Math.min(1, Math.hypot((x - 0.5) * 2, (y - 0.5) * 2) / 1.1) ** 1.2;
    default: return x;
  }
}
export function cellules({ cols, rows, seed = 1, tiers = 6, vers = "right", fade = 0.9 }) {
  const out = [];
  for (let row = 0; row < rows; row++) for (let col = 0; col < cols; col++) {
    const noise = hash(col, row, seed);
    const t = avancee(col, row, cols, rows, vers);
    const v = 0.82 * t * fade + (1 - fade) * 0.5 + (noise - 0.5) * 0.7;
    if (fade > 0) {
      const keep = 0.03 + 0.92 * (t ** 1.7 * fade + (1 - fade));
      if (hash(col, row, seed + 101) > keep || v <= 0.2) continue;
    }
    out.push({ col, row, tier: Math.max(0, Math.min(tiers - 1, Math.floor(v * tiers))) });
  }
  return out;
}
const n2 = (x) => Number(x.toFixed(2));
/**
 * Mosaïque SVG. `cols` x `rows` cellules carrées ; l'élément s'adapte à son conteneur (slice).
 * keep(cellule) -> false retire la cellule (laisser respirer un texte, protéger le logo).
 * `taille` : si fourni, largeur/hauteur de l'élément (css). `ancre` : alignement du slice.
 */
export function mosaique({ cols = 36, rows = 18, seed = 1, palette = "braise", vers = "right", fade = 0.9, gap = 0.07, keep, cls = "mosaique", ancre = "xMidYMid" } = {}) {
  const ramp = PALETTES[palette];
  const cs = cellules({ cols, rows, seed, tiers: ramp.length, vers, fade }).filter((c) => (keep ? keep(c) : true));
  const inset = gap / 2, side = n2(1 - gap);
  const sq = (c, r) => `M${n2(c + inset)} ${n2(r + inset)}h${side}v${side}h${-side}z`;
  const couches = ramp.map((color, tier) => {
    const l = cs.filter((c) => c.tier === tier);
    return l.length ? `<path fill="${color}" d="${l.map((c) => sq(c.col, c.row)).join("")}"/>` : "";
  }).join("");
  return `<svg class="${cls}" viewBox="0 0 ${cols} ${rows}" preserveAspectRatio="${ancre} slice" shape-rendering="crispEdges" aria-hidden="true">${couches}</svg>`;
}

// ---------------------------------------------------------------------------------------------------------------
// CSS de base : polices locales, jetons de la charte, composants (règle, grille, bande braise, étiquette mono).
export function cssPolices(depuis) {
  const u = (f) => relative(depuis, join(POLICES, f)).split("\\").join("/");
  return `
@font-face{font-family:"Geist";src:url("${u("geist-latin-wght-normal.woff2")}") format("woff2");font-weight:100 900;font-style:normal}
@font-face{font-family:"Inter";src:url("${u("inter-latin-wght-normal.woff2")}") format("woff2");font-weight:100 900;font-style:normal}
@font-face{font-family:"JetBrains Mono";src:url("${u("jetbrains-mono-latin-wght-normal.woff2")}") format("woff2");font-weight:100 800;font-style:normal}`;
}
export const CSS_BASE = `
:root{--noir:${C.noir};--surface:${C.surface};--papier:${C.papier};--creme:${C.creme};--sable:${C.sable};--texte-clair:${C.texteClair};
--gris:${C.gris};--encre:${C.encre};--gris-sombre:${C.grisSombre};--orange:${C.orange};--orange-s:${C.orangeSombre};--orange-c:${C.orangeClair};--nuit:${C.nuit};
--b1:${C.braise[0]};--b2:${C.braise[1]};--b3:${C.braise[2]};--b4:${C.braise[3]};--b5:${C.braise[4]};--b6:${C.braise[5]}}
*{box-sizing:border-box;margin:0;padding:0}
html,body{-webkit-print-color-adjust:exact;print-color-adjust:exact}
body{font-family:"Inter",system-ui,sans-serif;color:var(--encre);font-feature-settings:"cv11","ss03";text-rendering:geometricPrecision;-webkit-font-smoothing:antialiased}
svg{display:block}
.geist{font-family:"Geist","Inter",sans-serif;font-weight:500;letter-spacing:-.03em;line-height:1.05}
.mono{font-family:"JetBrains Mono",monospace;text-transform:uppercase;letter-spacing:.06em;font-weight:500;line-height:1.4}
.mosaique{position:absolute;inset:0;width:100%;height:100%}
/* bande braise : quatre barres franches */
.bande{background:linear-gradient(to bottom,var(--b2) 0 25%,var(--b4) 25% 50%,var(--b5) 50% 75%,var(--b6) 75% 100%)}
.bande-x{background:linear-gradient(to right,var(--b2) 0 25%,var(--b4) 25% 50%,var(--b5) 50% 75%,var(--b6) 75% 100%)}
/* règle graduée : trait toutes les 8 unités, plus haut toutes les 64 (en mm si --pas est donné en mm) */
.regle{height:var(--h,2.6mm);background-image:linear-gradient(to right,var(--c,rgba(245,244,239,.55)) var(--e,.25mm),transparent var(--e,.25mm)),linear-gradient(to right,var(--c2,rgba(245,244,239,.2)) var(--e,.25mm),transparent var(--e,.25mm));background-size:calc(var(--pas,2mm)*8) 100%,var(--pas,2mm) 50%;background-position:left bottom;background-repeat:repeat-x}
/* grille de mesure */
.grille{position:absolute;inset:0;background-image:linear-gradient(to right,var(--g,rgba(245,244,239,.12)) var(--e,.2mm),transparent var(--e,.2mm)),linear-gradient(to bottom,var(--g,rgba(245,244,239,.12)) var(--e,.2mm),transparent var(--e,.2mm));background-size:var(--pas,8mm) var(--pas,8mm);background-position:center top;-webkit-mask-image:var(--masque,radial-gradient(70% 90% at 50% 40%,#000 25%,transparent 78%));mask-image:var(--masque,radial-gradient(70% 90% at 50% 40%,#000 25%,transparent 78%))}
.carre{display:inline-block;background:var(--orange)}
`;

// ---------------------------------------------------------------------------------------------------------------
// Feuille d'impression : fond perdu + traits de coupe. Dimensions en mm. Le contenu du `corps` est positionné dans
// la zone de coupe (trim) ; `fondArt` couvre toute la zone de fond perdu.
export const MM_PAR_PO = 25.4;
export const po = (x) => x * MM_PAR_PO;
export function feuille({ w, h, fond = 3, traits = false, nom = "", fondArt = "", corps = "", cls = "", style = "" }) {
  const s = traits ? 8 : 0;
  const W = w + 2 * (fond + s), H = h + 2 * (fond + s);
  const bw = w + 2 * fond, bh = h + 2 * fond;
  let reperes = "";
  if (traits) {
    const t = s + fond; const L = [];
    const a = 1.5, b = s - 0.8; // longueur du trait : de a à b depuis le bord de la feuille
    for (const [x, y] of [[t, t], [W - t, t], [t, H - t], [W - t, H - t]]) {
      const sx = x < W / 2 ? 1 : -1, sy = y < H / 2 ? 1 : -1;
      const x0 = sx > 0 ? a : W - a, x1 = sx > 0 ? b : W - b, y0 = sy > 0 ? a : H - a, y1 = sy > 0 ? b : H - b;
      L.push(`<line x1="${x0}" y1="${y}" x2="${x1}" y2="${y}"/><line x1="${x}" y1="${y0}" x2="${x}" y2="${y1}"/>`);
    }
    reperes = `<svg class="reperes" viewBox="0 0 ${W} ${H}" style="position:absolute;inset:0;width:${W}mm;height:${H}mm" fill="none" stroke="#000" stroke-width=".18">${L.join("")}</svg>
<div class="mono" style="position:absolute;left:${t + 2}mm;right:${t + 2}mm;bottom:1.4mm;font-size:4.6pt;color:#000;letter-spacing:.04em;white-space:nowrap;overflow:hidden;text-overflow:ellipsis">NEXORA AI · ${nom} · fond perdu ${fond} mm</div>`;
  }
  return `<section class="page ${cls}" style="width:${W}mm;height:${H}mm;${style}">
<div class="art" style="position:absolute;left:${s}mm;top:${s}mm;width:${bw}mm;height:${bh}mm;overflow:hidden">
<div class="fond-art" style="position:absolute;inset:0">${fondArt}</div>
<div class="trim" style="position:absolute;left:${fond}mm;top:${fond}mm;width:${w}mm;height:${h}mm">${corps}</div>
</div>${reperes}</section>`;
}
export const tailleFeuille = ({ w, h, fond = 3, traits = false }) => {
  const s = traits ? 8 : 0; return { w: w + 2 * (fond + s), h: h + 2 * (fond + s) };
};

// ---------------------------------------------------------------------------------------------------------------
// Document HTML complet
export function document_({ titre = "Nexora AI", css = "", pages = "", dossier, tailles = null, lang = "fr" }) {
  // tailles : [{nom, w, h}] pour @page nommées ; sinon une seule page, `pageMm`.
  const nommees = (tailles || []).map((t) => `@page ${t.nom}{size:${t.w}mm ${t.h}mm;margin:0}.p-${t.nom}{page:${t.nom}}`).join("\n");
  return `<!doctype html><html lang="${lang}"><head><meta charset="utf-8"><title>${titre}</title><style>
${cssPolices(dossier)}
${CSS_BASE}
${nommees}
html,body{margin:0;background:#fff}
.page{position:relative;overflow:hidden;break-after:page;page-break-after:always;background:#fff}
.page:last-child{break-after:auto;page-break-after:auto}
${css}
</style></head><body>${pages}</body></html>`;
}

// ---------------------------------------------------------------------------------------------------------------
// Rendu
export async function navigateur() { return chromium.launch({ args: ["--font-render-hinting=none", "--disable-lcd-text"] }); }
export function ecrire(chemin, contenu) { mkdirSync(dirname(chemin), { recursive: true }); writeFileSync(chemin, contenu); return chemin; }
/**
 * Rend un document HTML (déjà écrit sur disque) :
 *  pdf: chemin de sortie (taille de la première feuille, ou @page), png: chemin (ou fonction (i)=>chemin pour chaque
 *  `.page`), dpi: résolution du PNG (CSS 96 px/po), selecteur: éléments à photographier (défaut ".page").
 *  pdfMm: {w,h} taille de page du PDF si non fournie par @page.
 */
export async function rendre(nav, { fichierHtml, pdf, png, dpi = 150, selecteur = ".page", largeurPx = 1200, pdfOptions = {}, transparent = false, fondPng }) {
  const ctx = await nav.newContext({ viewport: { width: Math.round(largeurPx), height: 900 }, deviceScaleFactor: dpi / 96 });
  const page = await ctx.newPage();
  const erreurs = [];
  page.on("console", (m) => { if (m.type() === "error") erreurs.push(m.text()); });
  page.on("pageerror", (e) => erreurs.push(String(e)));
  await page.goto(pathToFileURL(fichierHtml).href, { waitUntil: "load" });
  await page.evaluate(() => document.fonts.ready);
  await page.evaluate(async () => { await Promise.all([...document.images].map((i) => i.decode().catch(() => {}))); });
  if (png) {
    const els = page.locator(selecteur); const k = await els.count();
    for (let i = 0; i < k; i++) {
      const chemin = typeof png === "function" ? png(i) : (k === 1 ? png : png.replace(/(\.png)$/, `-${i + 1}$1`));
      if (!chemin) continue;
      mkdirSync(dirname(chemin), { recursive: true });
      await els.nth(i).screenshot({ path: chemin, omitBackground: transparent });
    }
  }
  if (pdf) {
    mkdirSync(dirname(pdf), { recursive: true });
    await page.emulateMedia({ media: "print" });
    await page.pdf({ path: pdf, printBackground: true, preferCSSPageSize: true, ...pdfOptions });
  }
  await ctx.close();
  if (erreurs.length) console.warn("  ! console :", [...new Set(erreurs)].slice(0, 3).join(" | "));
}

/**
 * Produit un document de feuilles identiques : écrit le HTML, rend le PDF (vectoriel) et/ou les PNG.
 * pages : tableau de chaînes `feuille(...)` (même taille) ; taille : {w,h,fond,traits} de ces feuilles.
 */
export async function produire(nav, { dossierHtml, nom, pages, css = "", taille, pdf, png, dpi = 150, lang = "fr", transparent = false }) {
  const t = tailleFeuille(taille);
  const html = document_({ titre: nom, dossier: dossierHtml, lang, css: `@page{size:${t.w}mm ${t.h}mm;margin:0}\n${css}`, pages: pages.join("\n") });
  const f = join(dossierHtml, `${nom}.html`); ecrire(f, html);
  await rendre(nav, { fichierHtml: f, pdf, png, dpi, largeurPx: Math.ceil(t.w / 25.4 * 96), transparent });
  return f;
}
/** Rastérise un PDF avec poppler (contrôle visuel des PDF, planches-contact). */
export function pdfVersPng(pdf, prefixe, dpi = 60) { mkdirSync(dirname(prefixe), { recursive: true }); execFileSync("pdftoppm", ["-r", String(dpi), "-png", pdf, prefixe]); }

/** Planche-contact : assemble des images (PNG) dans une grille étiquetée. */
export async function planche(nav, { images, sortie, colonnes = 4, largeur = 1800, fond = "#0A0A0E", legende = true, hauteurCase = 360, dossierTmp }) {
  const case_ = Math.floor((largeur - (colonnes + 1) * 16) / colonnes);
  const cases = images.map((im) => {
    const p = typeof im === "string" ? { fichier: im, nom: im.split("/").pop() } : im;
    return `<figure><div class="v"><img src="${pathToFileURL(p.fichier).href}"></div>${legende ? `<figcaption>${p.nom}</figcaption>` : ""}</figure>`;
  }).join("");
  const html = `<!doctype html><meta charset="utf-8"><style>
${cssPolices(dossierTmp)}
body{margin:0;background:${fond};padding:16px;font-family:'JetBrains Mono',monospace;color:#A8A8B6}
.g{display:grid;grid-template-columns:repeat(${colonnes},${case_}px);gap:16px}
figure{margin:0}.v{height:${hauteurCase}px;background:#17171f;display:flex;align-items:center;justify-content:center;border:1px solid rgba(245,244,239,.14)}
.v img{max-width:100%;max-height:100%;display:block}
figcaption{font-size:10px;letter-spacing:.06em;text-transform:uppercase;margin-top:6px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
</style><div class="g">${cases}</div>`;
  const f = join(dossierTmp, "_planche.html"); ecrire(f, html);
  const ctx = await nav.newContext({ viewport: { width: largeur, height: 800 }, deviceScaleFactor: 1 });
  const page = await ctx.newPage();
  await page.goto(pathToFileURL(f).href, { waitUntil: "load" });
  await page.evaluate(async () => { await Promise.all([...document.images].map((i) => i.decode().catch(() => {}))); });
  await page.screenshot({ path: sortie, fullPage: true });
  await ctx.close();
}

// ---------------------------------------------------------------------------------------------------------------
// Coordonnées : une seule source, coordonnees.json. Les marqueurs «à compléter…» s'affichent tels quels.
export function lireCoordonnees(chemin = COORDONNEES) { return JSON.parse(readFileSync(chemin, "utf8")); }
export const estMarqueur = (s) => typeof s === "string" && /^«.*»$/.test(s.trim());
export function slugPersonne(p, i) {
  if (!p.nom || estMarqueur(p.nom)) return `personne-${i + 1}`;
  return p.nom.normalize("NFD").replace(/[\u0300-\u036f]/g, "").toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "") || `personne-${i + 1}`;
}
export const esc = (s) => String(s ?? "").replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");
export const htmlRel = (depuis, fichier) => relative(depuis, fichier).split("\\").join("/");

// ---------------------------------------------------------------------------------------------------------------
// Contenu de marque (textes validés, brief §1 et pages du site). Rien d'autre que ce qui existe déjà.
export const TEXTE = {
  fr: {
    signature: "L’IA qui travaille pour votre entreprise. Sous votre contrôle.",
    campagne: "Rêvez grand. Gardez le contrôle.",
    quebec: "IA souveraine au Québec.",
    famille: "Un compte, des crédits, tous les outils.",
    donnees: "Vos données restent chez vous ou au Québec. Jamais utilisées pour entraîner un modèle.",
    etats: { disponible: "Disponible", bientot: "Bientôt", plus_tard: "Plus tard" },
    etat: "État",
  },
  en: {
    signature: "AI that works for your business. Under your control.",
    campagne: "Dream big. Stay in control.",
    quebec: "Sovereign AI, made in Québec.",
    famille: "One account, shared credits, every tool.",
    donnees: "Your data stays with you or in Quebec. Never used to train a model.",
    etats: { disponible: "Available", bientot: "Soon", plus_tard: "Later" },
    etat: "Status",
  },
};
/** Les huit outils de la famille (noms exacts). État lu dans web/src/i18n/apps.ts et product-family.tsx (01/11/2026). */
export const OUTILS = [
  { id: "workstudio", nom: "Nexora WorkStudio", nomEn: "Nexora WorkStudio", etat: "disponible", palette: "braise",
    tag: "Agents et flux de travaux", tagEn: "Agents and workflows",
    phrase: "Concevez des agents et des flux de travaux, en français, avec vos outils et vos documents.",
    phraseEn: "Design agents and workflows with your own tools and documents.",
    points: ["Des agents qui utilisent vos outils.", "Un Copilote qui prépare le flux, que vous relisez.", "Des réponses fondées sur vos documents."],
    pointsEn: ["Agents that use your tools.", "A Copilot that drafts the workflow for you to review.", "Answers grounded in your documents."] },
  { id: "code", nom: "Nexora Code", nomEn: "Nexora Code", etat: "bientot", palette: "ciel",
    tag: "Agent de code hébergé", tagEn: "Hosted coding agent",
    phrase: "Un agent de code qui comprend, modifie et teste du code avec vous, sur nos serveurs.",
    phraseEn: "A code agent that reads, changes and tests code with you, on our servers.",
    points: ["Un environnement par personne, hébergé : rien à installer.", "Relié à votre compte Nexora.", "Prévu pour passer par Privacy Router."],
    pointsEn: ["One hosted environment per person: nothing to install.", "Tied to your Nexora account.", "Planned to go through Privacy Router."] },
  { id: "rag", nom: "Nexora RAG", nomEn: "Nexora RAG", etat: "bientot", palette: "menthe",
    tag: "Vos documents, interrogeables", tagEn: "Your documents, searchable",
    phrase: "Vos documents deviennent une base que l’IA interroge, sources à l’appui.",
    phraseEn: "Your documents become a base that AI queries, with sources to back it up.",
    points: ["Une base créée en un clic, avec sa clé d’API.", "Chaque réponse montre ses sources.", "Prévue pour se relier à Nexora Code, à un bot ou à un autre outil."],
    pointsEn: ["A base created in one click, with its API key.", "Every answer shows its sources.", "Connects to Nexora Code, a bot or another tool."] },
  { id: "bot", nom: "Nexora Bot", nomEn: "Nexora Bot", etat: "bientot", palette: "or",
    tag: "Un bot relié à votre compte", tagEn: "A bot tied to your account",
    phrase: "Un bot qui se connecte à votre compte Nexora, sans configuration de modèle.",
    phraseEn: "A bot that connects to your Nexora account, with no model setup.",
    points: ["Fonctionne avec votre abonnement ou vos recharges.", "Code prévu ouvert, pour l’installer vous-même.", "Relié à Nexora RAG, il connaîtra vos documents."],
    pointsEn: ["Works with your subscription or top-ups.", "Code planned as open source, to install yourself.", "Connected to Nexora RAG, it will know your documents."] },
  { id: "creative", nom: "Nexora Creative", nomEn: "Nexora Creative", etat: "plus_tard", palette: "braise",
    tag: "Image, son et vidéo", tagEn: "Image, sound and video",
    phrase: "Des outils d’image, de son et de vidéo pour le marketing, avec l’IA.",
    phraseEn: "Image, sound and video tools for marketing, with AI.",
    points: ["Création et retouche d’images.", "Voix, musique et sons.", "Montage et génération de vidéos."],
    pointsEn: ["Image creation and retouching.", "Voice, music and sounds.", "Video editing and generation."] },
  { id: "webpilot", nom: "Nexora WebPilot", nomEn: "Nexora WebPilot", etat: "bientot", palette: "ciel",
    tag: "Recherche et navigation Web", tagEn: "Web search and browsing",
    phrase: "Une API pour chercher, lire et explorer le Web, puis naviguer et agir sur des pages.",
    phraseEn: "An API to search, read and explore the web, then navigate and act on pages.",
    points: ["Recherche, lecture et exploration de sites.", "Sessions de navigateur pour agir sur des pages.", "Vendue à l’usage, comme un modèle."],
    pointsEn: ["Search, reading and site exploration.", "Browser sessions to act on pages.", "Sold by usage, like a model."] },
  { id: "privacy-router", nom: "Privacy Router", nomEn: "Privacy Router", etat: "bientot", palette: "menthe",
    tag: "Confidentialité incluse", tagEn: "Privacy included",
    phrase: "La couche de protection commune : elle contrôle ce qui sort, selon la politique de votre organisation.",
    phraseEn: "The shared protection layer: it controls what leaves, according to your organization’s policy.",
    points: ["Incluse par défaut, jamais payante.", "Trois niveaux de politique par organisation.", "Un journal des décisions, sans le contenu."],
    pointsEn: ["Included by default, never paid.", "Three policy levels per organization.", "A log of decisions, without the content."] },
  { id: "vps", nom: "VPS au Québec", nomEn: "VPS in Quebec", etat: "bientot", palette: "or",
    tag: "Serveurs privés virtuels", tagEn: "Virtual private servers",
    phrase: "Un serveur à vous, au Québec, pour vos agents et vos outils d’IA.",
    phraseEn: "A server of your own, in Quebec, for your AI agents and tools.",
    points: ["Hébergé au Québec.", "Accès SSH par clé.", "Des applications prêtes à installer."],
    pointsEn: ["Hosted in Quebec.", "SSH key access.", "Ready-to-install applications."] },
];
export const M = {
  RACINE, ID, IM, POLICES, LOGOS, C, PALETTES, logo, symbole, logoBrut, symboleBrut, RAPPORT_LOGO, mosaique, cellules, hash, cssPolices, CSS_BASE,
  feuille, tailleFeuille, document_, navigateur, ecrire, rendre, produire, pdfVersPng, planche, lireCoordonnees, estMarqueur, slugPersonne, esc, htmlRel, TEXTE, OUTILS, po,
};
export default M;
