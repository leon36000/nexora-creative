// Dépliant 3 volets (Lettre), dépliant A5 plié (A4 paysage) et fiches d'une page des huit outils (fr + en).
//   bun imprimes/sources/depliants.mjs [trois-volets|a5|fiches]
import { M, IM, ID, po, esc, lireCoordonnees, COORDONNEES, TEXTE } from "../../identite/sources/moteur.mjs";
import { join } from "node:path";
import { mkdirSync, readFileSync, existsSync } from "node:fs";

const c = lireCoordonnees(COORDONNEES);
const OUT = join(IM, "final", "depliants"), HTML = join(IM, "sources", "html", "depliants"), GEN = join(IM, "sources", "generees");
mkdirSync(OUT, { recursive: true }); mkdirSync(HTML, { recursive: true });
const veut = (k) => process.argv.length < 3 || process.argv.includes(k);
const image = (nom) => { const f = join(GEN, `${nom}-x4.jpg`); return M.htmlRel(HTML, existsSync(f) ? f : join(GEN, `${nom}.png`)); };
const pt = (x) => `calc(${x}pt * var(--s,1))`;

const R = {
  fr: {
    intro: "De la gestion de vos demandes à l’automatisation de vos opérations, Nexora AI conçoit des systèmes IA adaptés à votre métier. Un compte, des crédits, tous vos outils.",
    famille: "La famille Nexora", tous: TEXTE.fr.famille, cta: "Planifier un diagnostic", ctaMono: "Écrivez-nous", donnees: TEXTE.fr.donnees, donneesLib: "Vos données",
    lib: { c: "Courriel", t: "Tél.", w: "Web", a: "Adresse" }, ficheLib: "Fiche produit", etat: "État", signature: TEXTE.fr.signature, campagne: TEXTE.fr.campagne, quebec: TEXTE.fr.quebec,
    notes: { disponible: "Livré et utilisable aujourd’hui.", bientot: "En préparation. Aucune date n’est annoncée.", plus_tard: "Prévu à une étape ultérieure. Aucune date n’est annoncée." },
    pointsLib: "Ce qu’il faut savoir", lecture: "Un compte, des crédits, tous les outils.",
  },
  en: {
    intro: "From managing your requests to automating your operations, Nexora AI designs AI systems tailored to your trade. One account, your credits, all your tools.",
    famille: "The Nexora family", tous: TEXTE.en.famille, cta: "Book an assessment", ctaMono: "Write to us", donnees: TEXTE.en.donnees, donneesLib: "Your data",
    lib: { c: "Email", t: "Tel.", w: "Web", a: "Address" }, ficheLib: "Product sheet", etat: "Status", signature: TEXTE.en.signature, campagne: TEXTE.en.campagne, quebec: TEXTE.en.quebec,
    notes: { disponible: "Shipped and usable today.", bientot: "In preparation. No date is announced.", plus_tard: "Planned for a later stage. No date is announced." },
    pointsLib: "What to know", lecture: "One account, shared credits, every tool.",
  },
};
const nomOutil = (o, l) => (l === "en" ? o.nomEn : o.nom);
const css = `
.t{font-family:"Geist",sans-serif;font-weight:500;letter-spacing:-.03em;line-height:1.05}
.m{font-family:"JetBrains Mono",monospace;text-transform:uppercase;letter-spacing:.06em;font-weight:500;line-height:1.4}
.lt{font-size:${pt(6)}}
.panneau{position:absolute;top:0;bottom:0;overflow:hidden}
.filet{border-top:.25pt solid rgba(18,18,24,.3)}.filet-c{border-top:.25pt solid rgba(245,244,239,.28)}
.sq{display:inline-block;width:1.6mm;height:1.6mm;margin-right:1.2mm;vertical-align:baseline}
`;
const carreEtat = (e) => `<i class="sq" style="${e === "disponible" ? "background:var(--orange)" : e === "bientot" ? "background:var(--gris-sombre)" : "border:.25mm solid var(--gris-sombre)"}"></i>`;
const carreEtatS = (e) => `<i class="sq" style="${e === "disponible" ? "background:var(--orange)" : e === "bientot" ? "background:var(--gris)" : "border:.25mm solid var(--gris)"}"></i>`;
const coordBloc = (l, sombre = false) => {
  const L = R[l].lib, col = sombre ? "var(--gris)" : "var(--gris-sombre)", v = sombre ? "var(--texte-clair)" : "var(--encre)";
  return [[L.c, c.courriel_general], [L.t, c.telephone], [L.w, c.site], [L.a, c.adresse]].map(([a, b]) => `<div style="margin-top:2.2mm"><div class="m lt" style="color:${col}">${a}</div><div style="font-size:${pt(8.4)};color:${v};line-height:1.3;overflow-wrap:anywhere">${esc(b)}</div></div>`).join("");
};
function verrou(id, lang, mode, style = "") {
  const o = M.OUTILS.find((x) => x.id === id);
  const suf = lang === "en" && o.nomEn !== o.nom ? "-en" : "";
  const f = join(ID, "final", "verrouillages", "svg-texte-editable", `nexora-${id}${suf}-horizontal-${mode}.svg`);
  return readFileSync(f, "utf8").replace(/<defs>.*?<\/defs>/s, "").replace(/ role="img" aria-label="[^"]*"/, ' aria-hidden="true"').replace("<svg ", `<svg style="${style}" `);
}

// ---------------------------------------------------------------- blocs de panneau (largeur pw mm, échelle s)
const bloc = {
  donnees: (l, pw, s) => `<div style="--s:${s};padding:12mm 10mm"><div class="m lt" style="color:var(--orange-c)">${R[l].donneesLib}</div>
<div class="t" style="font-size:${pt(19)};margin-top:5mm;color:var(--encre)">${esc(R[l].donnees)}</div>
<div style="position:absolute;left:10mm;bottom:12mm;right:10mm" class="filet"><div style="margin-top:3mm;font-size:${pt(8)};color:var(--gris-sombre);line-height:1.45">${esc(R[l].tous)}</div></div></div>`,
  contact: (l, pw, s, intro = false) => `<div style="--s:${s};padding:12mm 10mm">${M.logo("clair", "logo", `width:${pw * 0.46}mm;height:auto`)}
<div style="margin-top:9mm;font-size:${pt(9.4)};line-height:1.45;color:var(--encre)">${esc(R[l].signature)}</div>
${intro ? `<div style="margin-top:4mm;font-size:${pt(8.8)};line-height:1.55;color:var(--gris-sombre)">${esc(R[l].intro)}</div>` : ""}
<div style="margin-top:${intro ? 9 : 4}mm">${coordBloc(l)}</div>
<div style="position:absolute;left:10mm;bottom:12mm;width:14mm;height:4mm;background:linear-gradient(to bottom,var(--b2) 0 25%,var(--b4) 25% 50%,var(--b5) 50% 75%,var(--b6) 75% 100%)"></div></div>`,
  intro: (l, pw, s) => `<div style="--s:${s};padding:12mm 10mm"><div class="m lt" style="color:var(--orange-c)">Nexora AI · ${esc(R[l].quebec)}</div>
<div class="t" style="font-size:${pt(21)};margin-top:6mm;color:var(--encre)">${esc(R[l].signature)}</div>
<div style="margin-top:8mm;font-size:${pt(9.6)};line-height:1.55;color:var(--gris-sombre)">${esc(R[l].intro)}</div>
<div style="position:absolute;left:10mm;bottom:12mm;right:10mm" class="filet"><div class="m lt" style="margin-top:3mm;color:var(--gris-sombre)">${esc(R[l].campagne)}</div></div></div>`,
  famille: (l, pw, s) => `<div style="--s:${s};padding:12mm 10mm"><div class="m lt" style="color:var(--orange-c)">${R[l].famille}</div>
<div style="margin-top:4mm">${M.OUTILS.map((o, i) => `<div class="filet" style="display:grid;grid-template-columns:${6 * s}mm 1fr;gap:3mm;padding:${3.1 * s}mm 0;align-items:center">
<div style="position:relative;width:${6 * s}mm;height:${6 * s}mm">${M.mosaique({ cols: 5, rows: 5, seed: i * 7 + 3, palette: o.palette, fade: 0, gap: 0.1, vers: "center" })}</div>
<div><div class="t" style="font-size:${pt(11.4)};color:var(--encre)">${esc(nomOutil(o, l))}</div><div style="font-size:${pt(7.6)};color:var(--gris-sombre);margin-top:.4mm">${esc(l === "en" ? o.tagEn : o.tag)}</div>
<div class="m" style="font-size:${pt(5.8)};margin-top:.8mm;color:var(--encre)">${carreEtat(o.etat)}${TEXTE[l].etats[o.etat]}</div></div></div>`).join("")}</div></div>`,
  cta: (l, pw, s) => `<div style="--s:${s};padding:0 10mm;color:var(--texte-clair)"><div class="m lt" style="color:var(--orange-s)">${esc(R[l].ctaMono)}</div>
<div class="t" style="font-size:${pt(24)};margin-top:5mm">${esc(R[l].cta)}.</div>
<div style="margin-top:5mm">${coordBloc(l, true)}</div></div>`,
  couverture: (l, pw, s, hp) => `<div style="--s:${s};position:absolute;inset:0"><div style="position:absolute;left:10mm;top:10mm">${M.logo("sombre", "logo", `width:${pw * 0.5}mm;height:auto`)}</div>
<div class="t" style="position:absolute;left:10mm;right:8mm;bottom:15mm;font-size:${pt(23)};color:var(--texte-clair)">${esc(R[l].campagne).replace(". ", ".<br>")}</div>
<div class="m" style="position:absolute;left:10mm;bottom:9mm;font-size:${pt(6)};color:var(--orange-s)">${esc(R[l].quebec)}</div></div>`,
};
const coverArt = (l, x, pw, fond, h, extL = 0, extR = 0) => {
  const bandH = h * 0.4, cell = (pw + extL + extR) / 12;
  return `<div style="position:absolute;left:${x - extL}mm;top:0;bottom:0;width:${pw + extL + extR}mm;overflow:hidden">
<img src="${image("aurore-hero-9x16")}" style="position:absolute;inset:0;width:100%;height:100%;object-fit:cover;object-position:50% 40%">
<div style="position:absolute;left:0;right:0;bottom:0;height:${bandH}mm;background:var(--noir)"></div>
<div style="position:absolute;left:0;right:0;bottom:${bandH}mm;height:${cell * 4}mm">${M.mosaique({ cols: 12, rows: 4, seed: 12, vers: "bottom", fade: 0.96, gap: 0.1, ancre: "xMidYMax" })}</div></div>`;
};

// ---------------------------------------------------------------- dépliant 3 volets, Lettre (paysage 11 × 8,5 po)
async function troisVolets(nav) {
  const W = po(11), H = po(8.5), pw = W / 3;
  for (const l of ["fr", "en"]) {
    for (const [mode, fond, traits] of [["impression", 3, true], ["ecran", 0, false]]) {
      const f = { w: W, h: H, fond, traits };
      const ext = fond;
      const bg = (x, w, couleur, eL, eR) => `<div style="position:absolute;left:${x - eL + fond}mm;top:0;bottom:0;width:${w + eL + eR}mm;background:${couleur}"></div>`;
      const pan = (i, html) => `<div class="panneau" style="left:${i * pw}mm;width:${pw}mm">${html}</div>`;
      // extérieur : [rabat][dos][couverture]
      const ext1 = M.feuille({ ...f, nom: `trois-volets-${l} extérieur`,
        fondArt: bg(0, pw, "var(--papier)", fond, 0) + bg(pw, pw, "var(--creme)", 0, 0) + coverArt(l, 2 * pw + fond, pw, fond, H + 2 * fond, 0, fond),
        corps: pan(0, bloc.donnees(l, pw, 1)) + pan(1, bloc.contact(l, pw, 1)) + pan(2, bloc.couverture(l, pw, 1, H)) });
      const int = M.feuille({ ...f, nom: `trois-volets-${l} intérieur`,
        fondArt: bg(0, pw, "var(--papier)", fond, 0) + bg(pw, pw, "var(--creme)", 0, 0) + bg(2 * pw, pw, "var(--noir)", 0, fond)
          + `<div style="position:absolute;left:${2 * pw + fond}mm;top:0;bottom:0;width:${pw + fond}mm;overflow:hidden">${M.mosaique({ cols: 14, rows: 22, seed: 33, vers: "top", fade: 0.97, gap: 0.1, keep: (k) => k.row <= 7, ancre: "xMidYMin" })}</div>`,
        corps: pan(0, bloc.intro(l, pw, 1)) + pan(1, bloc.famille(l, pw, 1)) + `<div class="panneau" style="left:${2 * pw}mm;width:${pw}mm"><div style="position:absolute;left:0;right:0;top:${H * 0.36}mm">${bloc.cta(l, pw, 1)}</div><div style="position:absolute;left:10mm;bottom:12mm">${M.logo("sombre", "logo", `width:${pw * 0.46}mm;height:auto`)}</div></div>` });
      await M.produire(nav, { dossierHtml: HTML, nom: `trois-volets-${l}-${mode}`, pages: [ext1, int], css, taille: f, lang: l,
        pdf: join(OUT, `depliant-3-volets-lettre-${l}-${mode}.pdf`) });
    }
  }
}

// ---------------------------------------------------------------- dépliant A5 (A4 paysage plié en deux)
async function a5(nav) {
  const W = 297, H = 210, pw = W / 2;
  for (const l of ["fr", "en"]) for (const [mode, fond, traits] of [["impression", 3, true], ["ecran", 0, false]]) {
    const f = { w: W, h: H, fond, traits };
    const pan = (i, html) => `<div class="panneau" style="left:${i * pw}mm;width:${pw}mm">${html}</div>`;
    const bg = (x, w, couleur, eL, eR) => `<div style="position:absolute;left:${x - eL + fond}mm;top:0;bottom:0;width:${w + eL + eR}mm;background:${couleur}"></div>`;
    const ext = M.feuille({ ...f, nom: `a5-${l} extérieur`, fondArt: bg(0, pw, "var(--creme)", fond, 0) + coverArt(l, pw + fond, pw, fond, H + 2 * fond, 0, fond),
      corps: pan(0, bloc.contact(l, pw, 1.18, true)) + pan(1, bloc.couverture(l, pw, 1.3, H)) });
    const int = M.feuille({ ...f, nom: `a5-${l} intérieur`, fondArt: bg(0, pw, "var(--creme)", fond, 0) + bg(pw, pw, "var(--noir)", 0, fond)
      + `<div style="position:absolute;left:${pw + fond}mm;top:0;bottom:0;width:${pw + fond}mm;overflow:hidden">${M.mosaique({ cols: 20, rows: 28, seed: 57, vers: "top", fade: 0.97, gap: 0.1, keep: (k) => k.row <= 8, ancre: "xMidYMin" })}</div>`,
      corps: pan(0, bloc.famille(l, pw, 1.12)) + `<div class="panneau" style="left:${pw}mm;width:${pw}mm"><div style="position:absolute;left:0;right:0;top:${H * 0.42}mm">${bloc.cta(l, pw, 1.18)}</div><div style="position:absolute;left:12mm;bottom:14mm">${M.logo("sombre", "logo", `width:${pw * 0.4}mm;height:auto`)}</div></div>` });
    await M.produire(nav, { dossierHtml: HTML, nom: `a5-${l}-${mode}`, pages: [ext, int], css, taille: f, lang: l, pdf: join(OUT, `depliant-a5-plie-${l}-${mode}.pdf`) });
  }
}

// ---------------------------------------------------------------- fiches d'une page (Lettre)
async function fiches(nav) {
  const W = po(8.5), H = po(11);
  mkdirSync(join(OUT, "fiches"), { recursive: true });
  for (const o of M.OUTILS) for (const l of ["fr", "en"]) for (const [mode, fond, traits] of [["ecran", 0, false], ["impression", 3, true]]) {
    const f = { w: W, h: H, fond, traits }, t = R[l];
    const hh = 96;
    const art = `<div style="position:absolute;left:0;right:0;top:0;height:${hh + fond}mm;background:var(--noir)"></div><div class="grille" style="height:${hh + fond}mm;--pas:8mm;--g:rgba(245,244,239,.06);--masque:linear-gradient(to right,#000,transparent 60%)"></div>
<div style="position:absolute;left:0;right:0;top:0;height:${hh + fond}mm">${M.mosaique({ cols: 44, rows: Math.round(44 * (hh + fond) / (W + 2 * fond)), seed: 70 + M.OUTILS.indexOf(o), vers: "right", fade: 0.96, gap: 0.09, keep: (k) => k.col >= 28, ancre: "xMaxYMid" })}</div>
<div class="bande-x" style="position:absolute;left:0;right:0;top:${hh + fond}mm;height:1.6mm"></div><div style="position:absolute;inset:${hh + fond + 1.6}mm 0 0 0;background:var(--papier)"></div>`;
    const corps = `<div class="m" style="position:absolute;left:16mm;top:14mm;font-size:6.4pt;color:var(--orange-s)">Nexora AI · ${t.ficheLib}</div>
<div style="position:absolute;left:16mm;top:${hh - 34}mm">${verrou(o.id, l, "sombre", `width:96mm;height:auto`)}</div>
<div class="m" style="position:absolute;left:16mm;top:${hh - 12}mm;font-size:6.4pt;color:var(--gris)">${esc(l === "en" ? o.tagEn : o.tag)}</div>
<div style="position:absolute;left:16mm;right:16mm;top:${hh + 14}mm">
<div class="t" style="font-size:26pt;color:var(--encre);max-width:170mm;text-wrap:balance">${esc(l === "en" ? o.phraseEn : o.phrase)}</div>
<div style="margin-top:9mm">${(l === "en" ? o.pointsEn : o.points).map((p, i) => `<div class="filet" style="display:grid;grid-template-columns:12mm 1fr;padding:4.6mm 0;align-items:baseline"><div class="m" style="font-size:6.8pt;color:var(--orange-c)">0${i + 1}</div><div style="font-size:12.5pt;line-height:1.4">${esc(p)}</div></div>`).join("")}<div class="filet"></div></div></div>
<div style="position:absolute;left:16mm;right:16mm;bottom:46mm;display:grid;grid-template-columns:30mm 1fr;border:.3pt solid rgba(18,18,24,.4)">
<div class="m" style="font-size:6.4pt;padding:3.4mm 4mm;border-right:.3pt solid rgba(18,18,24,.4);color:var(--gris-sombre)">${t.etat}</div>
<div style="padding:3mm 4mm"><div class="m" style="font-size:8pt;color:var(--encre)">${carreEtat(o.etat)}${TEXTE[l].etats[o.etat]}</div><div style="font-size:8.6pt;color:var(--gris-sombre);margin-top:1mm">${esc(t.notes[o.etat])}</div></div></div>
<div style="position:absolute;left:16mm;right:16mm;bottom:14mm;display:grid;grid-template-columns:1.2fr 1fr 1fr 1fr;gap:4mm" class="filet"><div style="padding-top:3mm">${M.logo("clair", "logo", "width:30mm;height:auto")}</div>
${[[t.lib.c, c.courriel_general], [t.lib.t, c.telephone], [t.lib.w, c.site]].map(([a, b]) => `<div style="padding-top:3mm"><div class="m" style="font-size:5.6pt;color:var(--gris-sombre)">${a}</div><div style="font-size:7.4pt;overflow-wrap:anywhere">${esc(b)}</div></div>`).join("")}</div>`;
    const nom = `fiche-${o.id}-${l}`;
    await M.produire(nav, { dossierHtml: HTML, nom: `${nom}-${mode}`, pages: [M.feuille({ ...f, nom, fondArt: art, corps })], css, taille: f, lang: l,
      pdf: join(OUT, "fiches", `fiche-${o.id}-${l}-${mode === "ecran" ? "" : "impression-"}`.replace(/-$/, "") + ".pdf"), png: mode === "ecran" ? join(OUT, "fiches", `fiche-${o.id}-${l}.png`) : undefined, dpi: 80 });
  }
}

const nav = await M.navigateur();
if (veut("trois-volets")) { await troisVolets(nav); console.log("3 volets ok"); }
if (veut("a5")) { await a5(nav); console.log("A5 ok"); }
if (veut("fiches")) { await fiches(nav); console.log("fiches ok"); }
await nav.close();
