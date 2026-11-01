// Affiches Nexora AI : 7 compositions × (fr, en) × 3 formats (18 × 24 po, 24 × 36 po, A2), PDF avec fond perdu + PNG.
//   bun imprimes/sources/affiches.mjs [id…]      ids : heros famille quebec typo creative code workstudio
// Les images viennent de sources/generees/<nom>-x4.jpg (Qwen-Image-2.1 + Real-ESRGAN, sans texte) ; le texte et le logo sont posés en code.
import { M, IM, ID, po, esc, lireCoordonnees, COORDONNEES, C, TEXTE } from "../../identite/sources/moteur.mjs";
import { join } from "node:path";
import { mkdirSync, readFileSync, existsSync } from "node:fs";

const c = lireCoordonnees(COORDONNEES);
const OUT = join(IM, "final", "affiches"), HTML = join(IM, "sources", "html", "affiches"), GEN = join(IM, "sources", "generees");
mkdirSync(OUT, { recursive: true }); mkdirSync(HTML, { recursive: true });
const FORMATS = [["18x24po", po(18), po(24), po(0.125)], ["24x36po", po(24), po(36), po(0.125)], ["A2", 420, 594, 3]];
const veut = process.argv.slice(2);
const image = (nom) => { const f = join(GEN, `${nom}-x4.jpg`); return existsSync(f) ? f : join(GEN, `${nom}.png`); };

// Verrouillage de produit en ligne : symbole + nom (fichier source de identite/final/verrouillages)
function verrou(id, lang, mode, style = "") {
  const o = M.OUTILS.find((x) => x.id === id);
  const suffixe = lang === "en" && o.nomEn !== o.nom ? "-en" : "";
  const f = join(ID, "final", "verrouillages", "svg-texte-editable", `nexora-${id}${suffixe}-horizontal-${mode}.svg`);
  return readFileSync(f, "utf8").replace(/<defs>.*?<\/defs>/s, "").replace(/ role="img" aria-label="[^"]*"/, ' aria-hidden="true"').replace("<svg ", `<svg style="${style}" `);
}
const bande = (u, fond) => `<div style="position:absolute;left:0;right:0;bottom:0;height:${1.5 * u + fond}mm;background:linear-gradient(to bottom,var(--b2) 0 25%,var(--b4) 25% 50%,var(--b5) 50% 75%,var(--b6) 75% 100%)"></div>`;
const txt = {
  fr: { hero1: "Rêvez grand.", hero2: "Gardez le contrôle.", quebec: ["IA souveraine", "au Québec."], quebecMono: "IA souveraine au Québec", famille: ["La famille", "Nexora."], etat: "État", ouvrir: "Un compte, des crédits, tous les outils." },
  en: { hero1: "Dream big.", hero2: "Stay in control.", quebec: ["Sovereign AI,", "made in Québec."], quebecMono: "Sovereign AI, made in Québec", famille: ["The Nexora", "family."], etat: "Status", ouvrir: "One account, shared credits, every tool." },
};
const SERIE = {
  creative: { img: "creative-atelier-9x16", fr: ["Peignez", "avec la lumière."], en: ["Paint", "with light."], pos: "50% 55%" },
  code: { img: "code-pont-9x16", fr: ["Construisez", "le pont."], en: ["Build", "the bridge."], pos: "50% 38%" },
  workstudio: { img: "workstudio-flux-9x16", fr: ["Faites couler", "le travail."], en: ["Let the work", "flow."], pos: "50% 8%" },
};

function composer(id, lang, w, h, fond) {
  const u = (n) => `${(n * w / 100).toFixed(3)}mm`; // unité : 1 % de la largeur
  const t = txt[lang];
  const mono = (n, extra = "") => `font-size:${u(n)};${extra}`;
  const marge = 7;
  const siteLigne = `<div class="mono" style="${mono(1.35)};color:var(--gris);position:absolute;right:${u(marge)};bottom:${u(8)}">${esc(c.site)}</div>`;
  const logoHaut = `<div style="position:absolute;left:${u(marge)};top:${u(marge)}">${M.logo("sombre", "logo", `width:${u(24)};height:auto`)}</div>`;
  const cote = (n) => (n * w) / 100;

  if (id === "heros") {
    const bandH = 41; // % de la largeur
    const cell = (w + 2 * fond) / 44, mh = cote(15), rows = Math.round(mh / cell);
    const art = `<img src="${M.htmlRel(HTML, image("aurore-hero-9x16"))}" style="position:absolute;inset:0;width:100%;height:100%;object-fit:cover;object-position:50% 48%">
<div style="position:absolute;left:0;right:0;bottom:0;height:${u(bandH)};background:var(--noir)"></div>
<div style="position:absolute;left:0;right:0;bottom:${u(bandH)};height:${mh}mm">${M.mosaique({ cols: 44, rows, seed: 41, vers: "bottom", fade: 0.96, gap: 0.1, ancre: "xMidYMax" })}</div>
${bande(w / 100, fond)}`;
    const corps = `${logoHaut}
<div class="geist" style="position:absolute;left:${u(marge)};bottom:${u(16)};color:var(--texte-clair);font-size:${u(9.4)};line-height:1.02">${t.hero1}<br>${t.hero2}</div>
<div class="mono" style="${mono(1.5)};position:absolute;left:${u(marge)};bottom:${u(8)};color:var(--orange-s)">${t.quebecMono}</div>${siteLigne}`;
    return { art, corps };
  }
  if (id === "quebec") {
    const art = `<img src="${M.htmlRel(HTML, image("quebec-fleuve-9x16"))}" style="position:absolute;inset:0;width:100%;height:100%;object-fit:cover;object-position:50% 72%">
<div style="position:absolute;left:0;right:0;bottom:0;height:${u(36)};background:linear-gradient(to top,rgba(10,10,14,.9),rgba(10,10,14,0))"></div>${bande(w / 100, fond)}`;
    const corps = `<div class="mono" style="${mono(1.5)};position:absolute;left:${u(marge)};top:${u(marge + 0.5)};color:var(--orange-s)">Nexora AI</div>
<div class="geist" style="position:absolute;left:${u(marge)};top:${u(marge + 4.4)};color:var(--texte-clair);font-size:${u(9.4)};line-height:1.02">${t.quebec[0]}<br>${t.quebec[1]}</div>
<div style="position:absolute;left:${u(marge)};bottom:${u(9)}">${M.logo("sombre", "logo", `width:${u(24)};height:auto`)}</div>
<div style="position:absolute;right:${u(marge)};bottom:${u(9)};width:${u(40)};text-align:right;color:var(--texte-clair);font-size:${u(1.7)};line-height:1.4">${esc(TEXTE[lang].signature)}</div>`;
    return { art, corps };
  }
  if (id === "famille") {
    const cells = M.OUTILS.map((o, i) => {
      const etat = TEXTE[lang].etats[o.etat];
      const sq = o.etat === "disponible" ? "background:var(--orange)" : o.etat === "bientot" ? "background:var(--gris)" : "border:.2mm solid var(--gris)";
      return `<div style="background:var(--surface);padding:${u(2.2)};display:flex;flex-direction:column;position:relative;min-height:0;overflow:hidden">
<div style="position:relative;width:${u(4.6)};height:${u(4.6)}">${M.mosaique({ cols: 5, rows: 5, seed: i * 7 + 3, palette: o.palette, fade: 0, gap: 0.1, vers: "center" })}</div>
<div class="geist" style="color:var(--texte-clair);font-size:${u(3)};margin-top:${u(1.8)};line-height:1.08">${esc(lang === "en" ? o.nomEn : o.nom)}</div>
<div style="color:var(--gris);font-size:${u(1.55)};margin-top:${u(0.6)};line-height:1.35">${esc(lang === "en" ? o.tagEn : o.tag)}</div>
<div class="mono" style="margin-top:auto;padding-top:${u(1.6)};color:var(--texte-clair);font-size:${u(1.3)};display:flex;align-items:center;gap:${u(0.9)}"><i style="display:inline-block;width:${u(1.1)};height:${u(1.1)};${sq}"></i>${etat}</div></div>`;
    }).join("");
    const art = `<div style="position:absolute;inset:0;background:var(--noir)"></div><div class="grille" style="--pas:${u(6.4)};--e:.2mm;--g:rgba(245,244,239,.05);--masque:radial-gradient(80% 60% at 50% 30%,#000 20%,transparent 80%)"></div>${bande(w / 100, fond)}`;
    const corps = `<div class="mono" style="${mono(1.4)};position:absolute;left:${u(marge)};top:${u(marge)};color:var(--orange-s)">${t.ouvrir}</div>
<div class="geist" style="position:absolute;left:${u(marge)};top:${u(marge + 3.6)};color:var(--texte-clair);font-size:${u(8.2)};line-height:1.02">${t.famille[0]}<br>${t.famille[1]}</div>
<div style="position:absolute;left:${u(marge)};right:${u(marge)};top:${u(marge + 22)};bottom:${u(19)};display:grid;grid-template-columns:1fr 1fr;grid-template-rows:repeat(4,1fr);gap:${u(0.14)};background:rgba(245,244,239,.22);border:${u(0.14)} solid rgba(245,244,239,.22)">${cells}</div>
<div style="position:absolute;left:${u(marge)};bottom:${u(7.5)}">${M.logo("sombre", "logo", `width:${u(22)};height:auto`)}</div>${siteLigne}`;
    return { art, corps };
  }
  if (id === "typo") {
    const S = 48, sx = (100 - S) / 2, sy = 0.38 * (h / w * 100) - S / 2; // symbole : S % de la largeur, centré
    const Wa = w + 2 * fond, Ha = h + 2 * fond, cell = Wa / 40, rows = Math.round(Ha / cell), cols = 40;
    const zone = (0.2 * S + 1.2) * w / 100; // zone de protection (0,2 x la hauteur du symbole) + une marge
    const sxmm = fond + sx * w / 100, symm = fond + sy * w / 100, tmm = (S * w) / 100;
    const texteBas = { x0: fond + marge * w / 100 - cell, x1: fond + w - marge * w / 100 + cell, y0: fond + h - 36 * w / 100, y1: Ha };
    const etendue = 20 * w / 100; // la mosaïque se dissout sur cette distance en s'éloignant du symbole
    const keep = (k) => {
      const cx = (k.col + 0.5) * cell, cy = (k.row + 0.5) * (Ha / rows);
      const dx = Math.max(sxmm - zone - cx, 0, cx - (sxmm + tmm + zone)), dy = Math.max(symm - zone - cy, 0, cy - (symm + tmm + zone));
      const inZ = cx > sxmm - zone && cx < sxmm + tmm + zone && cy > symm - zone && cy < symm + tmm + zone;
      if (inZ) return false;
      const d = Math.hypot(dx, dy), p = Math.min(1, d / etendue);
      if (M.hash(k.col, k.row, 313) > p ** 0.5) return false;
      if (cy > texteBas.y0 && cx > texteBas.x0 && cx < texteBas.x1) return false;
      return true;
    };
    const art = `<div style="position:absolute;inset:0;background:var(--noir)"></div>${M.mosaique({ cols, rows, seed: 63, vers: "bords", fade: 0.7, gap: 0.09, keep, ancre: "xMidYMid" })}${bande(w / 100, fond)}`;
    const corps = `<div style="position:absolute;left:${u(sx)};top:${u(sy)};">${M.symbole("sombre", "symbole", `width:${u(S)};height:${u(S)}`)}</div>
<div class="geist" style="position:absolute;left:${u(marge)};bottom:${u(14.5)};color:var(--texte-clair);font-size:${u(6.4)};line-height:1.04">${t.hero1}<br>${t.hero2}</div>
<div class="mono" style="${mono(1.4)};position:absolute;left:${u(marge)};bottom:${u(7.2)};color:var(--orange-s)">Nexora AI · ${t.quebecMono}</div>`;
    return { art, corps };
  }
  // série « un outil, une image »
  const s = SERIE[id], o = M.OUTILS.find((x) => x.id === id);
  const art = `<img src="${M.htmlRel(HTML, image(s.img))}" style="position:absolute;inset:0;width:100%;height:100%;object-fit:cover;object-position:${s.pos}">
<div style="position:absolute;left:0;right:0;bottom:0;height:${u(34)};background:linear-gradient(to top,rgba(10,10,14,.92),rgba(10,10,14,0))"></div>
<div style="position:absolute;left:0;right:0;top:0;height:${u(34)};background:linear-gradient(to bottom,rgba(10,10,14,.78),rgba(10,10,14,0))"></div>${bande(w / 100, fond)}`;
  const corps = `<div class="mono" style="${mono(1.5)};position:absolute;left:${u(marge)};top:${u(marge + 0.4)};color:var(--orange-s)">${esc(lang === "en" ? o.tagEn : o.tag)}</div>
<div class="geist" style="position:absolute;left:${u(marge)};top:${u(marge + 4.6)};color:var(--texte-clair);font-size:${u(9.2)};line-height:1.02">${s[lang][0]}<br>${s[lang][1]}</div>
<div style="position:absolute;left:${u(marge)};bottom:${u(9.5)}">${verrou(id, lang, "sombre", `width:${u(52)};height:auto`)}</div>
<div class="mono" style="${mono(1.4)};position:absolute;left:${u(marge)};bottom:${u(5.8)};color:var(--gris)">${TEXTE[lang].etat} : ${TEXTE[lang].etats[o.etat]}</div>${siteLigne}`;
  return { art, corps };
}

const IDS = ["heros", "famille", "quebec", "typo", "creative", "code", "workstudio"];
const nav = await M.navigateur();
for (const id of IDS.filter((x) => !veut.length || veut.includes(x))) {
  mkdirSync(join(OUT, id), { recursive: true });
  for (const lang of ["fr", "en"]) for (const [fmt, w, h, fond] of FORMATS) {
    const nom = `affiche-${id}-${lang}-${fmt}`;
    { const { art, corps } = composer(id, lang, w, h, fond); const f = { w, h, fond };
      await M.produire(nav, { dossierHtml: HTML, nom, pages: [M.feuille({ ...f, nom, fondArt: art, corps })], taille: f, lang, pdf: join(OUT, id, `${nom}-fond-perdu.pdf`) }); }
    { const { art, corps } = composer(id, lang, w, h, 0); const f = { w, h, fond: 0 };
      await M.produire(nav, { dossierHtml: HTML, nom: nom + "-png", pages: [M.feuille({ ...f, fondArt: art, corps })], taille: f, lang, png: join(OUT, id, `${nom}.png`), dpi: 100 }); }
    console.log("  ", nom);
  }
}
await nav.close();
