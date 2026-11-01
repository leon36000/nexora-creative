// Cartes d'affaires Nexora AI : 3,5 × 2 po (88,9 × 50,8 mm), fond perdu 3 mm. Gabarits partagés (utilisés par generer-cartes.mjs).
import { M, C, po, esc, symboleBrut } from "../../identite/sources/moteur.mjs";

export const W = po(3.5), H = po(2), FOND = 3;
export const CSS_CARTE = `
.recto .sym{position:absolute;left:9mm;top:${(H - 25) / 2}mm;width:25mm;height:25mm}
.recto .regle{position:absolute;left:9mm;bottom:5.2mm;width:30mm;--pas:.5mm;--h:1.6mm;--e:.12mm}
.recto .grille{--pas:4.4mm;--e:.1mm;--g:rgba(245,244,239,.07);--masque:linear-gradient(to right,#000 0,transparent 70%)}
.verso{color:var(--encre)}
.verso .nom{font-size:14.5pt;letter-spacing:-.03em}
.verso .titre{font-size:7.6pt;line-height:1.25;margin-top:1.2mm;color:var(--gris-sombre)}
.verso .coord{position:absolute;left:6mm;right:11mm;bottom:5.6mm;display:grid;grid-template-columns:1fr 1fr;gap:2mm 4mm}
.verso .coord div{min-width:0}
.verso .lib{display:block;font-size:5.4pt;color:var(--gris-sombre);margin-bottom:.4mm}
.verso .val{display:block;font-size:7pt;line-height:1.25;color:var(--encre);overflow-wrap:anywhere}
.verso .filet{position:absolute;left:6mm;right:11mm;height:0;border-top:.25pt solid rgba(18,18,24,.3)}
.verso .logo{position:absolute;left:6mm;top:5.2mm;width:24mm;height:auto}
.verso .tete{position:absolute;left:6mm;top:15.6mm;right:11mm}
.verso .carres{position:absolute;right:11mm;top:5.2mm;display:flex;gap:.7mm}
.verso .carres i{display:block;width:1.2mm;height:1.2mm;background:var(--orange-c)}
.verso .bande{position:absolute;right:0;top:0;bottom:0;width:${5 + FOND}mm}
.braise{color:var(--noir)}
.braise .titre,.braise .lib{color:var(--noir)}
.braise .val{color:var(--noir)}
.braise .filet{border-top-color:rgba(10,10,14,.55)}
.braise .lib{opacity:.8}
.braise .carres i{background:var(--noir)}
.braise .bande{background:var(--noir)}
`;

export function rectoArt() {
  const bw = W + 2 * FOND, bh = H + 2 * FOND;
  // mosaïque : cellules carrées d'environ 2,1 mm, pleine au bord droit, qui se dissout vers la gauche (graine fixe)
  const cols = 45, rows = 27;
  const mosa = M.mosaique({ cols, rows, seed: 17, vers: "right", fade: 0.96, gap: 0.09, keep: (c) => c.col >= 17, ancre: "xMaxYMid" });
  return `<div style="position:absolute;inset:0;background:var(--noir)"></div><div class="grille"></div>${mosa}`;
}
export function rectoCorps() {
  return `<div class="recto" style="position:absolute;inset:0">${M.symbole("sombre", "sym")}<div class="regle"></div></div>`;
}
export const rectoClasse = "recto";

function valeurs(p, c, langue) {
  const g = (a, b) => (a && !/^\s*$/.test(a) ? a : b);
  const en = langue === "en";
  return {
    nom: p.nom,
    titre: en ? g(p.titre_en, p.titre) : p.titre,
    courriel: g(p.courriel, c.courriel_general),
    tel: g(p.telephone, c.telephone),
    site: c.site,
    adresse: c.adresse,
    lib: en ? { c: "Email", t: "Tel.", s: "Web", a: "Address" } : { c: "Courriel", t: "Tél.", s: "Web", a: "Adresse" },
  };
}
export function versoArt(braise) {
  const fond = braise ? "var(--orange)" : "var(--papier)";
  return `<div style="position:absolute;inset:0;background:${fond}"></div>`;
}
export function versoCorps(p, c, langue, braise = false) {
  const v = valeurs(p, c, langue);
  const logoV = braise ? "noir" : "clair";
  return `<div class="verso ${braise ? "braise" : ""}" style="position:absolute;inset:0">
${M.logo(logoV, "logo")}
<div class="tete"><div class="nom geist">${esc(v.nom)}</div><div class="titre">${esc(v.titre)}</div></div>
<div class="filet" style="top:30.4mm"></div>
<div class="coord">
<div><span class="lib mono">${v.lib.c}</span><span class="val">${esc(v.courriel)}</span></div>
<div><span class="lib mono">${v.lib.t}</span><span class="val">${esc(v.tel)}</span></div>
<div><span class="lib mono">${v.lib.s}</span><span class="val">${esc(v.site)}</span></div>
<div><span class="lib mono">${v.lib.a}</span><span class="val">${esc(v.adresse)}</span></div>
</div></div>`;
}
/** Bande de quatre barres sur le bord droit du verso (déborde dans le fond perdu, haut, bas et droite). */
export function versoBande(braise, fond = FOND) {
  if (braise) return "";
  return `<div class="bande-x" style="position:absolute;right:0;top:0;bottom:0;width:${5 + fond}mm;background:linear-gradient(to bottom,var(--b2) 0 25%,var(--b4) 25% 50%,var(--b5) 50% 75%,var(--b6) 75% 100%)"></div>`;
}

/** Calque de vernis sélectif : le symbole seul, en noir 100 %, à sa position exacte (mm, repère de la zone de coupe). */
export function vernisGeometrie() {
  const t = 25, x = 9, y = (H - t) / 2, k = t / 52;
  const inner = symboleBrut("noir").trim().replace(/^<svg[^>]*>/, "").replace(/<\/svg>$/, "").replace(/fill="#000000"/g, 'fill="#000"');
  return { x, y, t, k, inner };
}
export function vernisSvgCoupe() {
  const g = vernisGeometrie();
  return `<svg xmlns="http://www.w3.org/2000/svg" xmlns:inkscape="http://www.inkscape.org/namespaces/inkscape" viewBox="${-FOND} ${-FOND} ${W + 2 * FOND} ${H + 2 * FOND}" width="${W + 2 * FOND}mm" height="${H + 2 * FOND}mm">
<g id="fond-perdu" inkscape:groupmode="layer" inkscape:label="repere (ne pas imprimer)"><rect x="${-FOND}" y="${-FOND}" width="${W + 2 * FOND}" height="${H + 2 * FOND}" fill="none" stroke="#00AEEF" stroke-width=".1" stroke-dasharray="1 .6"/><rect x="0" y="0" width="${W}" height="${H}" fill="none" stroke="#EC008C" stroke-width=".1"/></g>
<g id="vernis" inkscape:groupmode="layer" inkscape:label="vernis (100 % noir, vernis sélectif)"><g transform="translate(${g.x - 6 * g.k} ${g.y - 6 * g.k}) scale(${g.k})">${g.inner}</g></g>
</svg>`;
}
export function vernisCorps() {
  const g = vernisGeometrie();
  return `<svg viewBox="0 0 ${W} ${H}" style="position:absolute;inset:0;width:${W}mm;height:${H}mm"><g transform="translate(${g.x - 6 * g.k} ${g.y - 6 * g.k}) scale(${g.k})">${g.inner}</g></svg>`;
}
