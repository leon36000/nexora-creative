// Facebook / Instagram Ads : 3 accroches × 4 formats × 2 langues, 2 carrousels de 5 cartes, annonces vidéo (plans fixes 6 s et 15 s).
import path from "node:path";
import { famille, C, TXT, OUTILS, outil, mosaique, grille, regle, cadre, grain, voile, logo, glyphe, pastille, bouton, esc, affiche, BARRES } from "../../social/sources/moteur/marque.mjs";
import { fondPhoto, fondMosaique, titre2, grilleOutils, lignes } from "../../social/sources/moteur/compo.mjs";
import { story } from "../../social/sources/moteur/modeles.mjs";
import { ACCROCHES, CARROUSELS, VIDEO6, VIDEO15 } from "./textes.mjs";

export const P = famille({ dossier: path.resolve(import.meta.dirname, "..") });
const LANGS = ["fr", "en"];
const FORMATS = { "1x1": [1080, 1080], "4x5": [1080, 1350], "paysage": [1200, 628], "9x16": [1080, 1920] };
const split = (s) => [s.split(". ")[0] + ".", s.split(". ").slice(1).join(". ")];
const titreAcc = (a, lang) => { const t = a.titre[lang]; return t.includes(". ") ? titre2(...split(t)) : esc(t); };

/** Rangée des huit glyphes, filet au-dessus et en dessous. */
function rangee({ x, y, w, size, k = 1 }) {
  const gap = (w - OUTILS.length * size) / (OUTILS.length - 1);
  return `<div style="position:absolute;left:${x}px;top:${y}px;width:${w}px;height:${size + 44 * k}px;border-top:1px solid rgba(245,244,239,.22);border-bottom:1px solid rgba(245,244,239,.22)">${OUTILS.map((o, i) => `<div style="position:absolute;left:${i * (size + gap)}px;top:${22 * k}px">${glyphe(o.id, { size })}</div>`).join("")}</div>`;
}

function fondAcc(a, fmt, w, h, k) {
  const vert = fmt === "9x16";
  if (a.id === "reve") return fondPhoto({ w, h, nom: vert ? "aurore-vertical" : fmt === "paysage" ? "aurore-foret" : "aurore-lac", pos: vert ? "50% 40%" : fmt === "paysage" ? "62% 40%" : "50% 50%", voiles: [fmt === "paysage" ? "gauche" : vert ? "bas2" : "bas"],
    mos: fmt === "paysage" ? { x: w * .62, y: 40, w: w * .38, h: h - 80, cell: 22 * k, seed: 801, toward: "right", fade: 1, opacity: .85 } : null });
  if (a.id === "quebec") return fondPhoto({ w, h, nom: vert ? "fleuve-vertical" : "fleuve-aube", pos: "50% 50%", voiles: [fmt === "paysage" ? "gauche" : vert ? "bas2" : "bas"] });
  // outils : mosaïque et rangée des huit glyphes
  const mos = { x: w * (fmt === "paysage" ? .55 : .35), y: 0, w: w * (fmt === "paysage" ? .45 : .65), h: fmt === "paysage" ? h : 200 * k, cell: (fmt === "paysage" ? 22 : 30) * k, seed: 810, toward: "right", fade: 1, opacity: .9 };
  return fondMosaique({ w, h, k, mos });
}

export function annonce(a, fmt, lang) {
  const [w, h] = FORMATS[fmt];
  const k = fmt === "paysage" ? 0.75 : w / 1080;
  let body;
  if (fmt === "9x16") {
    // story : zones de sécurité (250 px haut, 340 px bas) ; story() pose le logo à 250 px
    const base = a.id === "reve" ? { plan: { nom: "aurore-vertical", pos: "50% 40%", voiles: ["bas2"] } } : a.id === "quebec" ? { plan: { nom: "fleuve-vertical", pos: "50% 50%", voiles: ["bas2"] } } : { mos: [{ x: 400, y: 330, w: 680, h: 240, cell: 30, seed: 810, toward: "right", fade: 1, opacity: .9 }] };
    body = story({ lang, ...base, titre: titreAcc(a, lang) });
    if (a.id === "outils") body += rangee({ x: 80, y: 640, w: 920, size: 84 });
  } else {
    const fond = fondAcc(a, fmt, w, h, k) + (a.id === "outils" && fmt !== "paysage" ? rangee({ x: 80 * k, y: 270 * k, w: w - 160 * k, size: 84 * k, k }) : "");
    body = affiche({ w, h, lang, k, fond, titre: titreAcc(a, lang), titreTaille: Math.round((fmt === "paysage" ? 120 : 116) * k), largeurTexte: fmt === "paysage" ? .62 : .9, hauteurTitre: Math.round(h * .5), pied: fmt === "paysage" ? null : "quebec" });
  }
  return P.piece({ id: `annonce-${a.id}-${fmt}.${lang}`, sousDossier: `facebook-instagram/accroches/${a.id}`, w, h, lang, body });
}

/** Cartes de carrousel 1080×1080. */
function carte(kind, lang, c) {
  const w = 1080, h = 1080, m = 80, fr = lang === "fr", k = 1;
  const prog = (i, N = 5) => `<div style="position:absolute;left:${m}px;bottom:${m * .8}px;display:flex;gap:10px">${Array.from({ length: N }, (_, j) => `<i style="display:block;width:${j === i ? 44 : 14}px;height:14px;background:${j === i ? C.or : "rgba(245,244,239,.28)"}"></i>`).join("")}</div>`;
  const head = logo({ type: "complet", ton: "blanc", h: 40, x: m, y: m });
  const idx = c.cartes.indexOf(kind);
  const grosTitre = (t, s, bottom = 160, size = 104) => `<div style="position:absolute;left:${m}px;right:${m}px;bottom:${bottom}px;display:flex;flex-direction:column;gap:26px"><div class="aff" data-fit style="font-size:${size}px;max-height:${size * 3.2}px;overflow:hidden">${t}</div>${s ? `<div class="txt" data-fit style="font-size:36px;color:${C.gris};max-height:150px;overflow:hidden;max-width:860px">${esc(s)}</div>` : ""}</div>`;
  const bandeMos = (seed) => ({ x: w * .42, y: 0, w: w * .58, h: 168, cell: 28, seed, toward: "right", fade: 1, opacity: .85 });
  let b;
  if (kind === "accroche" && c === CARROUSELS.outils) b = fondPhoto({ w, h, nom: "aurore-lac", pos: "50% 50%", voiles: ["bas"], mos: bandeMos(821) }) + head + grosTitre(titre2(fr ? "Un compte." : "One account.", fr ? "Tous vos outils." : "All your tools."), fr ? "Huit outils, des crédits, un seul accès." : "Eight tools, credits, one access.") + prog(idx);
  else if (kind === "accroche") b = fondPhoto({ w, h, nom: "fleuve-aube", pos: "50% 50%", voiles: ["bas"], mos: bandeMos(822) }) + head + grosTitre(esc(TXT.quebec[lang]), fr ? "Chez vous ou au Québec." : "With you or in Québec.") + prog(idx);
  else if (["workstudio", "rag", "privacy"].includes(kind)) {
    const o = outil(kind);
    b = fondMosaique({ w, h, mos: bandeMos(830 + idx) }) + head + `<div style="position:absolute;left:${m}px;top:230px;display:flex;align-items:center;gap:30px">${glyphe(kind, { size: 170 })}<div style="display:flex;flex-direction:column;gap:14px"><div class="lib" style="font-size:28px;color:${C.orTxt}">${esc(o.etat[lang])}</div><div class="lib" style="font-size:32px">${esc(o.nom)}</div></div></div>` + grosTitre(lignes(o.titre[lang]), o.sous[lang], 160, 100) + prog(idx);
  } else if (kind === "sur-place") b = fondMosaique({ w, h, mos: bandeMos(841) }) + head + `<div class="lib" style="position:absolute;left:${m}px;top:250px;font-size:28px;color:${C.orTxt}">${fr ? "Sur place" : "On premises"}</div>` + grosTitre(titre2(fr ? "Chez vous." : "With you.", fr ? "Sous votre toit." : "Under your roof."), fr ? "Vos données restent sur votre serveur." : "Your data stays on your server.") + prog(idx);
  else if (kind === "heberge") b = fondPhoto({ w, h, nom: "salle-calcul", pos: "50% 50%", voiles: ["bas"], mos: bandeMos(842) }) + head + `<div class="lib" style="position:absolute;left:${m}px;top:250px;font-size:28px;color:${C.orTxt}">${fr ? "Hébergé" : "Hosted"}</div>` + grosTitre(titre2(fr ? "Au Québec." : "In Québec.", fr ? "Sauvegardes comprises." : "Backups included."), fr ? "Dans l’infrastructure de Nexora AI, située au Québec." : "In Nexora AI’s infrastructure, located in Québec.") + prog(idx);
  else if (kind === "entrainement") b = fondMosaique({ w, h, mos: bandeMos(843) }) + head + grosTitre(titre2(fr ? "Jamais pour entraîner" : "Never used to train", fr ? "un modèle." : "a model."), fr ? "Les données d’un client ne servent ni à entraîner ni à ajuster un modèle." : "A client’s data is never used to train or tune a model.") + prog(idx);
  else /* cta */ b = fondPhoto({ w, h, nom: "aurore-foret", pos: "60% 40%", voiles: ["bas"] }) + head + `<div style="position:absolute;left:${m}px;right:${m}px;bottom:160px;display:flex;flex-direction:column;gap:34px"><div class="aff" data-fit style="font-size:104px;max-height:260px;overflow:hidden">${titre2(...split(TXT.campagne[lang]))}</div><div>${bouton(TXT.diag[lang], { k: 1.25 })}</div></div>` + prog(idx);
  return b;
}
export function carrousels(lang) {
  const out = [];
  for (const [key, c] of Object.entries(CARROUSELS)) c.cartes.forEach((kind, i) => out.push(P.piece({ id: `carte-${i + 1}-sur-5-${kind}.${lang}`, sousDossier: `facebook-instagram/carrousels/${key}`, w: 1080, h: 1080, lang, body: carte(kind, lang, c) })));
  return out;
}

/** Plans fixes des annonces vidéo (6 s et 15 s), prêts pour l'animation : 1080×1920 et 1080×1080. */
function planVideo(plan, fmt, lang, texte) {
  const w = 1080, h = fmt === "9x16" ? 1920 : 1080, vert = fmt === "9x16";
  const fr = lang === "fr";
  const t = texte[lang];
  const titre = t.includes(". ") ? titre2(...split(t)) : esc(t);
  const m = 80;
  const Hh = (v, s) => (vert ? v : s);
  const bloc = (inner, bottom) => `<div style="position:absolute;left:${m}px;right:${m}px;bottom:${bottom}px;display:flex;flex-direction:column;gap:30px">${inner}</div>`;
  const head = vert ? `<div style="position:absolute;left:${m}px;top:250px">${logo({ type: "complet", ton: "blanc", h: 44 })}</div>` : logo({ type: "complet", ton: "blanc", h: 44, x: m, y: m });
  const bot = vert ? 370 : 150;
  const gros = (s) => `<div class="aff" data-fit style="font-size:${vert ? 132 : 120}px;max-height:${vert ? 520 : 380}px;overflow:hidden">${s}</div>`;
  let fond, extra = "";
  if (plan === "aurore") fond = fondPhoto({ w, h, nom: vert ? "aurore-vertical" : "aurore-lac", pos: "50% 45%", voiles: [vert ? "bas2" : "bas"] });
  else if (plan === "phare") fond = fondPhoto({ w, h, nom: vert ? "phare-vertical" : "phare", pos: "50% 45%", voiles: [vert ? "bas2" : "bas"] });
  else if (plan === "quebec") fond = fondPhoto({ w, h, nom: vert ? "fleuve-vertical" : "fleuve-aube", pos: "50% 50%", voiles: [vert ? "bas2" : "bas"] });
  else if (plan === "huit") { fond = fondMosaique({ w, h, mos: [{ x: w * .4, y: 0, w: w * .6, h: vert ? 520 : 300, cell: 30, seed: 851, toward: "right", fade: 1, opacity: .8 }] }); extra = rangee({ x: m, y: vert ? 640 : 340, w: w - 2 * m, size: 84 }); }
  else if (plan === "workstudio") { fond = fondMosaique({ w, h, mos: [{ x: w * .42, y: 0, w: w * .58, h: vert ? 900 : 560, cell: 32, seed: 852, toward: "right", fade: 1, opacity: .95 }] }); extra = `<div style="position:absolute;left:${m}px;top:${vert ? 560 : 260}px">${glyphe("workstudio", { size: vert ? 280 : 240 })}</div>`; }
  else if (plan === "privacy") fond = fondPhoto({ w, h, nom: vert ? "phare-vertical" : "phare", pos: "50% 45%", voiles: [vert ? "bas2" : "bas"] }), extra = `<div style="position:absolute;left:${m}px;top:${vert ? 560 : 260}px">${glyphe("privacy", { size: 240 })}</div>`;
  else /* fin */ { fond = fondMosaique({ w, h, mos: [{ x: w * .42, y: 0, w: w * .58, h: vert ? 420 : 260, cell: 32, seed: 853, toward: "right", fade: 1, opacity: .85 }] }); return fond + head + bloc(`<div class="aff" data-fit style="font-size:${vert ? 124 : 112}px;max-height:${vert ? 420 : 300}px;overflow:hidden">${titre2(...split(TXT.campagne[lang]))}</div><div>${bouton(TXT.diag[lang], { k: 1.3 })}</div>`, bot); }
  return fond + extra + head + bloc(gros(titre), bot);
}
export function videos(lang) {
  const out = [];
  for (const [dur, liste] of [["6s", VIDEO6], ["15s", VIDEO15]]) for (const fmt of ["9x16", "1x1"]) for (const s of liste)
    out.push(P.piece({ id: `plan-${String(s.n).padStart(2, "0")}-${s.plan}.${lang}`, sousDossier: `facebook-instagram/video-${dur}/${fmt}`, w: 1080, h: fmt === "9x16" ? 1920 : 1080, lang, body: planVideo(s.plan, fmt, lang, s.texte) }));
  return out;
}

export function toutAnnonces() {
  const out = [];
  for (const lang of LANGS) {
    for (const a of ACCROCHES) for (const f of Object.keys(FORMATS)) out.push(annonce(a, f, lang));
    out.push(...carrousels(lang), ...videos(lang));
  }
  return out;
}
