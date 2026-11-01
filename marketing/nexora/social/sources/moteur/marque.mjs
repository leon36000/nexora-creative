// Moteur de gabarits Nexora AI : jetons de marque, mosaïque, grille, règle, bande braise, cadre de filets, pastilles
// d'outils, logos officiels (jamais modifiés), mise en page « affiche » et rendu Playwright.
// Partagé par social/ et publicite/. Tout est déterministe (graines fixes) : mêmes sources, mêmes images.
import fs from "node:fs";
import path from "node:path";

export const SRC = path.resolve(import.meta.dirname, ".."); // social/sources
export const NEXORA = path.resolve(SRC, "../.."); // marketing/nexora

/* ------------------------------------------------------------------ jetons */
export const C = {
  noir: "#0A0A0E", surface: "#121218", papier: "#FBFBF8", creme: "#F3F2EC", clair: "#F5F4EF", gris: "#A8A8B6",
  or: "#FF5A1F", orTxt: "#FF7A45", orClair: "#B53A0A", nuit: "#11112A",
};
export const PALETTES = {
  braise: ["#ffd37a", "#ffb11a", "#ff8a1f", "#ff5a1f", "#e0341c", "#b01a3c"],
  nuit: ["#1b1b2c", "#232338", "#2c2c47", "#36365a", "#44446f", "#565688"],
  or: ["#fff3c4", "#ffe58a", "#ffd44d", "#ffc01f", "#f5a30b", "#d98505"],
  ciel: ["#e1eeff", "#bcd7ff", "#8fbbff", "#5f9aff", "#3b74f2", "#2a54c4"],
};
export const BARRES = ["#FFB11A", "#FF5A1F", "#E0341C", "#B01A3C"];

export const coordonnees = JSON.parse(fs.readFileSync(path.join(NEXORA, "coordonnees.json"), "utf8"));
export const esc = (s) => String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");

/* ------------------------------------------------------------------ textes de marque */
export const TXT = {
  campagne: { fr: "Rêvez grand. Gardez le contrôle.", en: "Dream big. Stay in control." },
  signature: { fr: "L’IA qui travaille pour votre entreprise. Sous votre contrôle.", en: "AI that works for your business. Under your control." },
  quebec: { fr: "IA souveraine au Québec.", en: "Sovereign AI, made in Québec." },
  quebecCourt: { fr: "IA souveraine au Québec", en: "Sovereign AI, made in Québec" },
  famille: { fr: "Un compte. Des crédits. Tous les outils.", en: "One account. Credits. Every tool." },
  diag: { fr: "Planifier un diagnostic", en: "Book a diagnostic" },
  solutions: { fr: "Voir les solutions", en: "See the solutions" },
  attente: { fr: "Rejoindre la liste d’attente", en: "Join the waitlist" },
};

/* Les huit outils : noms exacts, état réel lu dans web/src/i18n/apps.ts (aucun outil « disponible » en libre-service ;
   WorkStudio livré avec démonstration sur demande ; VPS en préparation), accroche « rêve d'abord ». */
export const OUTILS = [
  { id: "workstudio", nom: "Nexora WorkStudio", court: "WorkStudio", etat: { fr: "Démonstration sur demande", en: "Demo on request" }, cta: "diag",
    titre: { fr: "Décrivez-le. Il prend forme.", en: "Describe it. It takes shape." },
    sous: { fr: "Des agents et des flux de travaux, en français, que vous relisez avant qu’ils agissent.", en: "Agents and workflows, in plain language, that you review before they act." },
    alt: { fr: "Quatre nœuds reliés, symbole d’un flux de travaux", en: "Four linked nodes, a symbol for a workflow" } },
  { id: "code", nom: "Nexora Code", court: "Code", etat: { fr: "Bientôt", en: "Coming soon" }, cta: "attente",
    titre: { fr: "Codez sans rien installer.", en: "Code without installing a thing." },
    sous: { fr: "Un agent de code dans un environnement hébergé, relié à votre compte.", en: "A coding agent in a hosted environment, linked to your account." },
    alt: { fr: "Deux chevrons de code en pixels", en: "Two code chevrons in pixels" } },
  { id: "rag", nom: "Nexora RAG", court: "RAG", etat: { fr: "Bientôt", en: "Coming soon" }, cta: "attente",
    titre: { fr: "Vos documents répondent.", en: "Your documents answer back." },
    sous: { fr: "Une base que l’IA interroge, sources à l’appui.", en: "A knowledge base the AI queries, with its sources." },
    alt: { fr: "Un document en pixels", en: "A document in pixels" } },
  { id: "bot", nom: "Nexora Bot", court: "Bot", etat: { fr: "Bientôt", en: "Coming soon" }, cta: "attente",
    titre: { fr: "Un bot sous votre toit.", en: "A bot under your roof." },
    sous: { fr: "Relié à votre compte Nexora, avec les modèles que vous choisissez.", en: "Linked to your Nexora account, with the models you choose." },
    alt: { fr: "Une bulle de conversation en pixels", en: "A chat bubble in pixels" } },
  { id: "creative", nom: "Nexora Creative", court: "Creative", etat: { fr: "Plus tard", en: "Later" }, cta: "attente",
    titre: { fr: "Imaginez. Voyez. Entendez.", en: "Imagine. See. Hear." },
    sous: { fr: "Image, son et vidéo pour votre marketing, avec l’IA.", en: "Image, sound and video for your marketing, with AI." },
    alt: { fr: "Un cadre d’image en pixels avec un soleil", en: "A picture frame in pixels with a sun" } },
  { id: "webpilot", nom: "Nexora WebPilot", court: "WebPilot", etat: { fr: "Bientôt", en: "Coming soon" }, cta: "attente",
    titre: { fr: "Le Web, lu pour vous.", en: "The web, read for you." },
    sous: { fr: "Chercher, lire, explorer, puis agir sur des pages.", en: "Search, read, explore, then act on pages." },
    alt: { fr: "Un curseur en pixels", en: "A cursor in pixels" } },
  { id: "privacy", nom: "Nexora Privacy Router", court: "Privacy Router", etat: { fr: "Bientôt", en: "Coming soon" }, cta: "attente",
    titre: { fr: "Vous décidez de ce qui sort.", en: "You decide what leaves." },
    sous: { fr: "La confidentialité est incluse, jamais payante.", en: "Privacy is included, never an add-on." },
    alt: { fr: "Un cadenas en pixels", en: "A padlock in pixels" } },
  { id: "vps", nom: "VPS au Québec", court: "VPS", etat: { fr: "En préparation", en: "In preparation" }, cta: "diag",
    titre: { fr: "Votre serveur. Votre territoire.", en: "Your server. Your territory." },
    sous: { fr: "Des serveurs privés virtuels au Québec, avec l’application de votre choix.", en: "Virtual private servers in Québec, with the app of your choice." },
    alt: { fr: "Deux serveurs empilés en pixels", en: "Two stacked servers in pixels" } },
];
export const outil = (id) => OUTILS.find((o) => o.id === id);

/* Glyphes 7×7 (X = orange signal, o = os) : une icône par outil, bâtie comme la marque, en pixels. */
const GLYPHES = {
  workstudio: ["XX...XX", "XX...XX", "..o.o..", "...X...", "..o.o..", "XX...XX", "XX...XX"],
  code: [".......", "..X.X..", ".X...X.", "X..o..X", ".X...X.", "..X.X..", "......."],
  rag: ["XXXXX..", "X...XX.", "X...X.X", "X.o.XXX", "X.....X", "X.XXX.X", "XXXXXXX"],
  bot: ["XXXXXXX", "X.....X", "X.XXX.X", "X.....X", "X.XoX.X", "XXXXXXX", "..XX..."],
  creative: ["XXXXXXX", "X...o.X", "X.....X", "X..X..X", "X.XXX.X", "XXXXXXX", "......."],
  webpilot: ["X......", "XX.....", "XXX....", "XXXX...", "XXXXX..", "XXXo...", "..XX..."],
  privacy: ["..XXX..", ".X...X.", ".X...X.", "XXXXXXX", "XXXoXXX", "XXXoXXX", "XXXXXXX"],
  vps: ["XXXXXXX", "X....oX", "XXXXXXX", ".......", "XXXXXXX", "X....oX", "XXXXXXX"],
};
// glyphes corrigés pour qu'aucun ne ressemble au logo : voir glyphe()
export function glyphe(id, { size = 56, fill = C.or, accent = C.clair, gap = 0.12, style = "" } = {}) {
  const g = GLYPHES[id];
  const n = g.length, m = g[0].length;
  const c = size / Math.max(n, m);
  let d1 = "", d2 = "";
  const s = c * (1 - gap), off = (c * gap) / 2;
  g.forEach((row, y) => [...row].forEach((ch, x) => {
    if (ch === ".") return;
    const p = `M${(x * c + off).toFixed(2)} ${(y * c + off).toFixed(2)}h${s.toFixed(2)}v${s.toFixed(2)}h${(-s).toFixed(2)}z`;
    if (ch === "X") d1 += p; else d2 += p;
  }));
  return `<svg xmlns="http://www.w3.org/2000/svg" width="${size}" height="${size}" viewBox="0 0 ${size} ${size}" aria-hidden="true" style="${style}" shape-rendering="crispEdges"><path d="${d1}" fill="${fill}"/><path d="${d2}" fill="${accent}"/></svg>`;
}

/* ------------------------------------------------------------------ mosaïque (port de web/src/components/brand/mosaic.tsx) */
function hash(col, row, seed) {
  let h = Math.imul(col + 1, 73856093) ^ Math.imul(row + 1, 19349663) ^ Math.imul(seed + 1, 83492791);
  h = Math.imul(h ^ (h >>> 15), 2246822507);
  h = Math.imul(h ^ (h >>> 13), 3266489909);
  return ((h ^ (h >>> 16)) >>> 0) / 4294967296;
}
function progress(col, row, cols, rows, toward) {
  const x = cols > 1 ? col / (cols - 1) : 0.5, y = rows > 1 ? row / (rows - 1) : 0.5;
  switch (toward) {
    case "right": return x; case "left": return 1 - x; case "bottom": return y; case "top": return 1 - y;
    case "bottomright": return (x + y) / 2; case "topright": return (x + 1 - y) / 2;
    case "bottomleft": return (1 - x + y) / 2; case "topleft": return (2 - x - y) / 2;
    default: return Math.max(0, 1 - Math.hypot((x - 0.5) * 2, (y - 0.5) * 2) / 1.2);
  }
}
export function cellules({ cols, rows, seed, tiers, toward, fade }) {
  const out = [];
  for (let row = 0; row < rows; row++) for (let col = 0; col < cols; col++) {
    const noise = hash(col, row, seed);
    const t = progress(col, row, cols, rows, toward);
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
/** Mosaïque en SVG, positionnée en absolu. toward = côté où elle est pleine ; elle se dissout vers l'opposé. */
export function mosaique({ x = 0, y = 0, w, h, cell = 24, seed = 1, toward = "right", fade = 1, gap = 0.14, palette = "braise", keep, opacity = 1, blur = 0, style = "", sparks = [] }) {
  const cols = Math.ceil(w / cell), rows = Math.ceil(h / cell);
  const ramp = PALETTES[palette];
  const inset = gap / 2, side = n2(1 - gap);
  const sq = (c, r) => `M${n2(c + inset)} ${n2(r + inset)}h${side}v${side}h${-side}z`;
  const cells = cellules({ cols, rows, seed, tiers: ramp.length, toward, fade }).filter((c) => (keep ? keep(c, { cols, rows }) : true));
  const layers = ramp.map((color, tier) => {
    const d = cells.filter((c) => c.tier === tier).map((c) => sq(c.col, c.row)).join("");
    return d ? `<path d="${d}" fill="${color}"/>` : "";
  }).join("");
  const sp = sparks.map(([c, r]) => `<path d="${sq(c, r)}" fill="${C.clair}"/>`).join("");
  return `<svg aria-hidden="true" shape-rendering="crispEdges" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${cols} ${rows}" width="${cols * cell}" height="${rows * cell}" style="position:absolute;left:${x}px;top:${y}px;opacity:${opacity};${blur ? `filter:blur(${blur}px);` : ""}${style}">${layers}${sp}</svg>`;
}

/* ------------------------------------------------------------------ composants */
export function grille({ size = 64, opacity = 0.09, mask = "radial-gradient(70% 90% at 50% 40%, #000 25%, transparent 78%)", style = "" } = {}) {
  return `<div aria-hidden="true" style="position:absolute;inset:0;background-image:linear-gradient(to right,rgba(245,244,239,${opacity}) 1px,transparent 1px),linear-gradient(to bottom,rgba(245,244,239,${opacity}) 1px,transparent 1px);background-size:${size}px ${size}px;background-position:center top;-webkit-mask-image:${mask};mask-image:${mask};${style}"></div>`;
}
export function regle({ w, x = 0, y = 0, k = 1, side = "bottom", opacity = 1, color = "245,244,239" } = {}) {
  const long = 64 * k, short = 8 * k, hh = 10 * k;
  return `<div aria-hidden="true" style="position:absolute;left:${x}px;${side}:${y}px;width:${w}px;height:${hh}px;background-image:linear-gradient(to right,rgba(${color},${0.32 * opacity}) 1px,transparent 1px),linear-gradient(to right,rgba(${color},${0.16 * opacity}) 1px,transparent 1px);background-size:${long}px ${hh}px,${short}px ${hh / 2}px;background-position:left bottom,left bottom;background-repeat:repeat-x"></div>`;
}
/** Bande braise : quatre barres franches. horizontale par défaut. */
export function bande({ x = 0, y = 0, w, h, vertical = false, style = "" }) {
  const bars = BARRES.map((c) => `<i style="flex:1;background:${c};display:block"></i>`).join("");
  return `<div aria-hidden="true" style="position:absolute;left:${x}px;top:${y}px;width:${w}px;height:${h}px;display:flex;flex-direction:${vertical ? "row" : "column"};${style}">${bars}</div>`;
}
/** Cadre de filets (1 px) avec un petit carré à chaque angle. */
export function cadre({ x = 0, y = 0, w, h, k = 1, color = "rgba(245,244,239,.22)", carre = 8, sq = C.clair }) {
  const s = carre * k;
  const corner = (l, t) => `<i style="position:absolute;left:${l}px;top:${t}px;width:${s}px;height:${s}px;background:${sq};display:block"></i>`;
  return `<div aria-hidden="true" style="position:absolute;left:${x}px;top:${y}px;width:${w}px;height:${h}px;border:${Math.max(1, Math.round(k))}px solid ${color}">${corner(-s / 2 - 0.5, -s / 2 - 0.5)}${corner(w - s / 2 - 1.5, -s / 2 - 0.5)}${corner(-s / 2 - 0.5, h - s / 2 - 1.5)}${corner(w - s / 2 - 1.5, h - s / 2 - 1.5)}</div>`;
}
export function grain(opacity = 0.07) {
  return `<div aria-hidden="true" style="position:absolute;inset:0;background-image:url(__ASSETS__ressources/grain.png);background-size:256px 256px;mix-blend-mode:overlay;opacity:${opacity};pointer-events:none"></div>`;
}
/** Image générée en plan de fond. pos = point focal ; filtres optionnels. */
// Plans pas encore générés : on retombe sur le plan le plus proche (la bibliothèque se remplit au fil du GPU partagé).
const REPLI = { phare: "aurore-lac", "phare-vertical": "phare", "cabane-neige": "aurore-foret", "salle-calcul": "ville-crepuscule", "carres-flottants": "atelier",
  "bureau-nuit": "atelier", "montagne-aube": "fleuve-aube", "aurore-vertical": "aurore-foret", "ville-vertical": "ville-crepuscule", "foret-vertical": "aurore-foret",
  "fleuve-vertical": "fleuve-aube", "braises-montantes": "atelier", "mosaique-vertical": "atelier", "pont-lumiere": "ville-crepuscule", "pont-vertical": "ville-crepuscule" };
const CLAIR = { "carres-flottants": "brightness(1.9) contrast(1.1)", atelier: "brightness(1.7) contrast(1.05)", "aurore-lac": "brightness(1.25)" };
export const existe = (nom) => fs.existsSync(path.join(SRC, "generees", `${nom}.png`));
export const resoudre = (nom) => { let n = nom; for (let i = 0; i < 3 && !existe(n) && REPLI[n]; i++) n = REPLI[n]; return n; };
export function photo(nom, { pos = "50% 50%", scale = 1, filter = "", x = 0, y = 0, w, h, style = "" } = {}) {
  nom = resoudre(nom);
  if (!filter && CLAIR[nom]) filter = CLAIR[nom];
  const sz = scale === 1 ? "cover" : `${scale * 100}% auto`;
  return `<div aria-hidden="true" style="position:absolute;left:${x}px;top:${y}px;${w ? `width:${w}px;` : "right:0;"}${h ? `height:${h}px;` : "bottom:0;"}background:url(__ASSETS__generees/${nom}.png) ${pos}/${sz} no-repeat;${filter ? `filter:${filter};` : ""}${style}"></div>`;
}
export function voile(css, style = "") {
  return `<div aria-hidden="true" style="position:absolute;inset:0;background:${css};${style}"></div>`;
}
const LOGOS = {
  complet: { sombre: "nexora-ai-logo-sombre.svg", clair: "nexora-ai-logo.svg", blanc: "nexora-ai-logo-blanc.svg", noir: "nexora-ai-logo-noir.svg", ratio: 285.55 / 52 },
  symbole: { sombre: "nexora-ai-symbole-sombre.svg", clair: "nexora-ai-symbole.svg", blanc: "nexora-ai-symbole-blanc.svg", noir: "nexora-ai-symbole-noir.svg", ratio: 1 },
};
/** Logo officiel (fichier SVG copié tel quel). type : complet | symbole ; ton : sombre (sur noir) | clair | blanc | noir. */
export function logo({ type = "complet", ton = "sombre", w, h, x, y, style = "", alt = "Nexora AI", right, bottom }) {
  const L = LOGOS[type];
  if (w && !h) h = w / L.ratio;
  if (h && !w) w = h * L.ratio;
  const pos = [x != null ? `left:${x}px` : "", y != null ? `top:${y}px` : "", right != null ? `right:${right}px` : "", bottom != null ? `bottom:${bottom}px` : ""].filter(Boolean).join(";");
  return `<img src="__ASSETS__logos/${L[ton]}" alt="${esc(alt)}" width="${Math.round(w)}" height="${Math.round(h)}" style="display:block;${pos ? `position:absolute;${pos};` : ""}${style}">`;
}
/** Pastille d'outil : glyphe + nom (mono) + état. Rectangle à angle franc, filet de 1 px. */
export function pastille(o, lang, { k = 1, etat = true, fond = "rgba(10,10,14,.55)" } = {}) {
  const t = typeof o === "string" ? outil(o) : o;
  const g = glyphe(t.id, { size: 30 * k });
  return `<div style="display:inline-flex;align-items:center;gap:${14 * k}px;padding:${11 * k}px ${18 * k}px ${11 * k}px ${14 * k}px;border:${Math.max(1, k)}px solid rgba(245,244,239,.26);border-radius:${4 * k}px;background:${fond};backdrop-filter:blur(${6 * k}px)">${g}<span class="lib" style="font-size:${19 * k}px;color:${C.clair};white-space:nowrap">${esc(t.nom)}</span>${etat ? `<span class="lib" style="font-size:${15 * k}px;color:${C.orTxt};white-space:nowrap;padding-left:${14 * k}px;border-left:${Math.max(1, k)}px solid rgba(245,244,239,.22)">${esc(t.etat[lang])}</span>` : ""}</div>`;
}
export function bouton(label, { k = 1, style = "" } = {}) {
  return `<div style="display:inline-flex;align-items:center;gap:${14 * k}px;background:${C.or};color:${C.noir};font:600 ${26 * k}px/1 Inter,system-ui,sans-serif;padding:${22 * k}px ${30 * k}px;border-radius:${6 * k}px;letter-spacing:-0.01em;${style}">${esc(label)}<svg width="${20 * k}" height="${20 * k}" viewBox="0 0 20 20" aria-hidden="true" shape-rendering="crispEdges"><path d="M2 9h12V7h2v2h2v2h-2v2h-2v-2H2zM12 5h2v2h-2zm0 8h2v2h-2z" fill="${C.noir}"/></svg></div>`;
}

/* ------------------------------------------------------------------ page */
const FIT = `<script>(function(){function fit(){document.querySelectorAll('[data-fit]').forEach(function(el){var s=parseFloat(getComputedStyle(el).fontSize),min=s*.45;while((el.scrollHeight>el.clientHeight+s*.3||el.scrollWidth>el.clientWidth+1)&&s>min){s*=.96;el.style.fontSize=s+'px'}})}(document.fonts&&document.fonts.ready?document.fonts.ready:Promise.resolve()).then(fit)})();</script>`;
export const CSS = `
@font-face{font-family:Geist;src:url(__ASSETS__polices/geist-latin-wght-normal.woff2) format("woff2");font-weight:100 900}
@font-face{font-family:Inter;src:url(__ASSETS__polices/inter-latin-wght-normal.woff2) format("woff2");font-weight:100 900}
@font-face{font-family:"JetBrains Mono";src:url(__ASSETS__polices/jetbrains-mono-latin-wght-normal.woff2) format("woff2");font-weight:100 800}
*{box-sizing:border-box;margin:0;padding:0}
body{background:${C.noir};color:${C.clair};-webkit-font-smoothing:antialiased;font-family:Inter,system-ui,sans-serif}
.aff{font-family:Geist,Inter,system-ui,sans-serif;font-weight:500;letter-spacing:-.03em;line-height:1.02;text-wrap:balance;color:${C.clair}}
.lib{font-family:"JetBrains Mono",ui-monospace,monospace;font-weight:500;text-transform:uppercase;letter-spacing:.06em;line-height:1.4}
.txt{font-family:Inter,system-ui,sans-serif;line-height:1.45;text-wrap:pretty}
.p{position:relative;overflow:hidden;background:${C.noir}}
.abs{position:absolute}
`;

/** Document HTML complet. assets : préfixe relatif vers social/sources/. */
export function page({ w, h, body, css = "", assets = "../", title = "Nexora AI", lang = "fr", fit = true, transparent = false }) {
  const html = `<!doctype html><html lang="${lang}"><head><meta charset="utf-8"><title>${esc(title)}</title><style>${CSS}html,body{width:${w}px;height:${h}px;overflow:hidden}${transparent ? "html,body,.p{background:transparent!important}" : ""}${css}</style></head><body><div class="p" style="width:${w}px;height:${h}px">${body}</div>${fit ? FIT : ""}</body></html>`;
  return html.replaceAll("__ASSETS__", assets);
}

/* ------------------------------------------------------------------ mise en page « affiche » */
/**
 * Gabarit général : fond (photo / mosaïque / plein), en-tête (logo + pastille), bloc de texte ancré en bas ou en haut,
 * pied (logo ou ligne Québec), tout dimensionné sur l'unité k. Retourne le corps HTML.
 */
export function affiche({ w, h, lang, k, fond, kicker, titre, sous, pastilleOutil, cta, cadreFilets = false, logoTon = "blanc", logoType = "complet",
  m, titreTaille, sousTaille, bas = true, entete = true, pied = "quebec", largeurTexte = 0.86, hauteurTitre, reglage = true, mosaicOpt }) {
  m = m ?? Math.round(80 * k);
  const parts = [];
  parts.push(fond || "");
  if (cadreFilets) parts.push(cadre({ x: m * 0.55, y: m * 0.55, w: w - m * 1.1, h: h - m * 1.1, k: Math.max(1, k * 1) }));
  if (entete) {
    parts.push(logo({ type: logoType, ton: logoTon, h: 44 * k, x: m, y: m }));
    if (pastilleOutil) parts.push(`<div style="position:absolute;right:${m}px;top:${m - 8 * k}px">${pastille(pastilleOutil, lang, { k: 1.55 * k, etat: false })}</div>`);
  }
  const tT = titreTaille ?? Math.round(120 * k), sT = sousTaille ?? Math.round(40 * k);
  const po = pastilleOutil ? (typeof pastilleOutil === "string" ? outil(pastilleOutil) : pastilleOutil) : null;
  if (po && !kicker) kicker = po.etat[lang];
  const bloc = `<div style="position:absolute;left:${m}px;${bas ? `bottom:${pied ? m + 84 * k : m}px` : `top:${m + 110 * k}px`};width:${Math.round(w * largeurTexte - m)}px;display:flex;flex-direction:column;gap:${26 * k}px">
    ${kicker ? `<div class="lib" style="font-size:${32 * k}px;color:${C.orTxt}">${esc(kicker)}</div>` : ""}
    <div class="aff" data-fit style="font-size:${tT}px;max-height:${hauteurTitre ?? Math.round(h * 0.36)}px;overflow:hidden;">${titre}</div>
    ${sous ? `<div class="txt" data-fit style="font-size:${sT}px;color:${C.gris};max-width:${Math.round(w * 0.82)}px;max-height:${sT * 3.4}px;overflow:hidden">${esc(sous)}</div>` : ""}
    ${cta ? `<div style="margin-top:${10 * k}px">${bouton(cta, { k: k * 0.9 })}</div>` : ""}
  </div>`;
  parts.push(bloc);
  if (pied) {
    parts.push(`<div class="lib" style="position:absolute;left:${m}px;right:${m}px;bottom:${m * 0.8}px;display:flex;justify-content:space-between;align-items:center;font-size:${30 * k}px;color:${C.gris}"><span>${esc(TXT.quebecCourt[lang])}</span><span style="display:flex;gap:${6 * k}px">${BARRES.map((c) => `<i style="display:block;width:${34 * k}px;height:${8 * k}px;background:${c}"></i>`).join("")}</span></div>`);
  }
  return parts.join("");
}

/* ------------------------------------------------------------------ rendu */
import { chromium } from "/home/pc6/Desktop/NexoraSite/web/node_modules/@playwright/test/index.mjs";

/**
 * pieces : [{ id, w, h, html, out (png|jpg), htmlDir, scale?, quality? }]. Écrit le HTML source puis le rend.
 * Réutilise un navigateur et traite `conc` pages en parallèle.
 */
export async function rendre(pieces, { conc = 4, quiet = false } = {}) {
  const browser = await chromium.launch();
  let i = 0, ok = 0;
  const errors = [];
  async function worker() {
    const ctx = await browser.newContext({ deviceScaleFactor: 1 });
    while (i < pieces.length) {
      const p = pieces[i++];
      try {
        fs.mkdirSync(path.dirname(p.out), { recursive: true });
        const htmlPath = p.htmlPath;
        fs.mkdirSync(path.dirname(htmlPath), { recursive: true });
        fs.writeFileSync(htmlPath, p.html);
        const page = await ctx.newPage();
        await page.setViewportSize({ width: p.w, height: p.h });
        await page.goto("file://" + htmlPath, { waitUntil: "load" });
        await page.evaluate(() => document.fonts.ready);
        await page.waitForTimeout(p.wait ?? 60);
        const overflow = await page.evaluate(() => {
          const bad = [];
          document.querySelectorAll("[data-fit]").forEach((el) => { const fs = parseFloat(getComputedStyle(el).fontSize); if (el.scrollHeight > el.clientHeight + fs * 0.3 + 2 || el.scrollWidth > el.clientWidth + 2) bad.push(el.textContent.slice(0, 40)); });
          return bad;
        });
        if (overflow.length) errors.push(`${p.id} : texte qui déborde (${overflow.join(" | ")})`);
        const jpg = /\.jpe?g$/i.test(p.out);
        await page.screenshot({ path: p.out, type: jpg ? "jpeg" : "png", quality: jpg ? p.quality ?? 88 : undefined, omitBackground: !!p.transparent, animations: p.statique ? "disabled" : "allow", clip: { x: 0, y: 0, width: p.w, height: p.h } });
        await page.close();
        ok++;
        if (!quiet && ok % 20 === 0) console.log(`  ${ok}/${pieces.length}`);
      } catch (e) {
        errors.push(`${p.id} : ${e.message}`);
      }
    }
    await ctx.close();
  }
  await Promise.all(Array.from({ length: conc }, worker));
  await browser.close();
  return { ok, errors };
}

/** Contexte d'une famille : où écrire le HTML, les PNG, et le préfixe des ressources. */
export function famille({ dossier }) {
  const htmlDir = path.join(dossier, "sources", "html");
  const finalDir = path.join(dossier, "final");
  return {
    htmlDir, finalDir,
    piece({ id, sousDossier = "", w, h, body, css = "", lang = "fr", title, ext = "png", fit = true, wait, finalDirOverride, transparent = false }) {
      const htmlPath = path.join(htmlDir, sousDossier, `${id}.html`);
      const assets = path.relative(path.dirname(htmlPath), SRC) + "/";
      const html = page({ w, h, body, css, lang, title: title ?? id, assets, fit, transparent });
      return { id, w, h, html, out: path.join(finalDirOverride ?? finalDir, sousDossier, `${id}.${ext}`), htmlPath, wait, transparent };
    },
  };
}

/** Planche-contact : grille de vignettes étiquetées (PIL via Python, plus simple et rapide). */
export const lh = (lang, o) => o[lang];

/** PDF vectoriel multipage : assemble les pièces (même dossier de HTML) en un seul document, une page par pièce. */
export async function rendrePdf({ pieces, out, w, h }) {
  const first = pieces[0].html;
  const style = first.match(/<style>([\s\S]*?)<\/style>/)[1];
  const head = first.match(/<head>[\s\S]*?<\/head>/)[0].replace(/<style>[\s\S]*?<\/style>/, "");
  const bodies = pieces.map((p) => p.html.match(/<body>([\s\S]*?)<script>/)[1]).join("");
  const html = `<!doctype html><html lang="fr">${head.replace("</head>", `<style>${style}html,body{height:auto;overflow:visible}@page{size:${w}px ${h}px;margin:0}.p{break-after:page;page-break-after:always}.p:last-child{break-after:auto;page-break-after:auto}</style></head>`)}<body>${bodies}${FIT}</body></html>`;
  const htmlPath = pieces[0].htmlPath.replace(/\.html$/, "-pdf.html");
  fs.writeFileSync(htmlPath, html);
  const browser = await chromium.launch();
  const page = await browser.newPage();
  await page.goto("file://" + htmlPath, { waitUntil: "load" });
  await page.evaluate(() => document.fonts.ready);
  await page.waitForTimeout(150);
  fs.mkdirSync(path.dirname(out), { recursive: true });
  await page.pdf({ path: out, width: `${w}px`, height: `${h}px`, printBackground: true, margin: { top: 0, right: 0, bottom: 0, left: 0 } });
  await browser.close();
  return out;
}
