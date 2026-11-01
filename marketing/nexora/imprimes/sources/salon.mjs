// Support de salon : bannière rétractable 850 × 2000 mm, fond de stand 3 × 2,4 m (PDF à l'échelle 1:10), badge 4 × 3 po,
// tour de cou, signalisation de porte, accroche-porte.   bun imprimes/sources/salon.mjs
import { M, IM, ID, po, esc, lireCoordonnees, COORDONNEES, TEXTE } from "../../identite/sources/moteur.mjs";
import { join } from "node:path";
import { mkdirSync, existsSync } from "node:fs";

const c = lireCoordonnees(COORDONNEES);
const OUT = join(IM, "final", "salon"), HTML = join(IM, "sources", "html", "salon"), GEN = join(IM, "sources", "generees");
mkdirSync(OUT, { recursive: true }); mkdirSync(HTML, { recursive: true });
const image = (nom) => { const f = join(GEN, `${nom}-x4.jpg`); return M.htmlRel(HTML, existsSync(f) ? f : join(GEN, `${nom}.png`)); };
const imageGrande = () => existsSync(join(GEN, "aurore-large-16x9-x4.jpg")) || existsSync(join(GEN, "aurore-large-16x9.png")) ? image("aurore-large-16x9") : image("aurore-hero-9x16");
const bandeBas = (h, fond) => `<div style="position:absolute;left:0;right:0;bottom:0;height:${h + fond}mm;background:linear-gradient(to bottom,var(--b2) 0 25%,var(--b4) 25% 50%,var(--b5) 50% 75%,var(--b6) 75% 100%)"></div>`;
const nav = await M.navigateur();
const T = { fr: TEXTE.fr, en: TEXTE.en };
const css = ".t{font-family:Geist,sans-serif;font-weight:500;letter-spacing:-.03em;line-height:1.02}.m{font-family:'JetBrains Mono',monospace;text-transform:uppercase;letter-spacing:.06em;font-weight:500}";

// ------------------------------------------------------------------ bannière rétractable 850 × 2000 mm
for (const l of ["fr", "en"]) {
  const w = 850, h = 2000, fond = 5, u = w / 100;
  const U = (n) => `${(n * u).toFixed(2)}mm`;
  const t = T[l];
  const [l1, l2] = t.campagne.split(". ").map((x, i) => (i === 0 ? x + "." : x));
  const bandH = 66, cell = (w + 2 * fond) / 28, mh = cell * 9;
  const art = (surDesSecurite = false) => `<img src="${image("aurore-hero-9x16")}" style="position:absolute;inset:0;width:100%;height:100%;object-fit:cover;object-position:50% 35%">
<div style="position:absolute;left:0;right:0;bottom:0;height:${U(bandH)};background:var(--noir)"></div>
<div style="position:absolute;left:0;right:0;bottom:${U(bandH)};height:${mh}mm">${M.mosaique({ cols: 28, rows: 9, seed: 91, vers: "bottom", fade: 0.96, gap: 0.1, ancre: "xMidYMax" })}</div>${bandeBas(18, fond)}`;
  const corps = (securite) => `<div style="position:absolute;left:${U(8)};top:${U(9)}">${M.logo("sombre", "logo", `width:${U(52)};height:auto`)}</div>
<div class="t" style="position:absolute;left:${U(8)};bottom:${U(33)};color:var(--texte-clair);font-size:${U(10)}">${l1}<br>${l2}</div>
<div class="m" style="position:absolute;left:${U(8)};bottom:${U(27)};color:var(--orange-s);font-size:${U(2.2)}">${esc(t.quebec)}</div>
<div class="m" style="position:absolute;right:${U(8)};bottom:${U(27)};color:var(--gris);font-size:${U(2)}">${esc(c.site)}</div>
${securite ? `<div style="position:absolute;left:0;right:0;bottom:0;height:200mm;background:rgba(0,174,239,.25);border-top:1.5mm dashed #00AEEF;color:#fff;font:600 28mm sans-serif;padding:20mm">ZONE MASQUÉE PAR LE BOÎTIER (≈ 200 mm)</div><div style="position:absolute;left:0;right:0;top:0;height:60mm;background:rgba(0,174,239,.25);border-bottom:1.5mm dashed #00AEEF"></div>` : ""}`;
  const f = { w, h, fond };
  await M.produire(nav, { dossierHtml: HTML, nom: `banniere-${l}`, pages: [M.feuille({ ...f, nom: "banniere", fondArt: art(), corps: corps(false) })], taille: f, css, lang: l, pdf: join(OUT, `banniere-retractable-850x2000-${l}-fond-perdu.pdf`) });
  const f0 = { w, h, fond: 0 };
  await M.produire(nav, { dossierHtml: HTML, nom: `banniere-${l}-png`, pages: [M.feuille({ ...f0, fondArt: art(), corps: corps(false) })], taille: f0, css, lang: l, png: join(OUT, `banniere-retractable-850x2000-${l}.png`), dpi: 22 });
  await M.produire(nav, { dossierHtml: HTML, nom: `banniere-${l}-securite`, pages: [M.feuille({ ...f0, fondArt: art(), corps: corps(true) })], taille: f0, css, lang: l, png: join(OUT, `banniere-retractable-850x2000-${l}-zones-de-securite.png`), dpi: 22 });
}

// ------------------------------------------------------------------ fond de stand 3 × 2,4 m, PDF à l'échelle 1:10 (300 × 240 mm)
for (const l of ["fr", "en"]) {
  const w = 300, h = 240, fond = 5, u = w / 100, t = T[l];
  const U = (n) => `${(n * u).toFixed(2)}mm`;
  const [l1, l2] = t.campagne.split(". ").map((x, i) => (i === 0 ? x + "." : x));
  const art = `<img src="${imageGrande()}" style="position:absolute;inset:0;width:100%;height:100%;object-fit:cover;object-position:62% 50%">
<div style="position:absolute;left:0;top:0;bottom:0;width:${U(80)};background:linear-gradient(to right,rgba(10,10,14,.92) 0%,rgba(10,10,14,.8) 50%,rgba(10,10,14,0) 100%)"></div>${bandeBas(3, fond)}`;
  const corps = `<div style="position:absolute;left:${U(6)};top:${U(6)}">${M.logo("sombre", "logo", `width:${U(20)};height:auto`)}</div>
<div class="t" style="position:absolute;left:${U(6)};top:${U(24)};color:var(--texte-clair);font-size:${U(7.6)}">${l1}<br>${l2}</div>
<div class="m" style="position:absolute;left:${U(6)};bottom:${U(8)};color:var(--orange-s);font-size:${U(1.6)}">${esc(t.quebec)}</div>
<div class="m" style="position:absolute;right:${U(6)};bottom:${U(8)};color:var(--gris);font-size:${U(1.4)}">${esc(c.site)}</div>`;
  const f = { w, h, fond };
  await M.produire(nav, { dossierHtml: HTML, nom: `fond-stand-${l}`, pages: [M.feuille({ ...f, nom: "fond-stand 1:10", fondArt: art, corps })], taille: f, css, lang: l, pdf: join(OUT, `fond-de-stand-3x2.4m-echelle-1sur10-${l}.pdf`) });
  const f0 = { w, h, fond: 0 };
  await M.produire(nav, { dossierHtml: HTML, nom: `fond-stand-${l}-png`, pages: [M.feuille({ ...f0, fondArt: art.replace(/bottom:0;height:[\d.]+mm/, "bottom:0;height:0.9mm"), corps })], taille: f0, css, lang: l, png: join(OUT, `fond-de-stand-3x2.4m-${l}.png`), dpi: 200 });
}

// ------------------------------------------------------------------ badge 4 × 3 po + tour de cou
{
  const w = po(4), h = po(3), fond = 3;
  const variantes = [["equipe", "Équipe", "Team", true], ["visiteur", "Visiteur", "Visitor", false]];
  for (const [id, fr, en, sombre] of variantes) {
    for (const traits of [true, false]) {
      const f = { w, h, fond, traits };
      const bg = sombre ? "var(--noir)" : "var(--papier)", fg = sombre ? "var(--texte-clair)" : "var(--encre)", gr = sombre ? "var(--gris)" : "var(--gris-sombre)";
      const art = `<div style="position:absolute;inset:0;background:${bg}"></div><div style="position:absolute;left:0;right:0;bottom:0;height:${3.2 + fond}mm;background:linear-gradient(to right,var(--b2) 0 25%,var(--b4) 25% 50%,var(--b5) 50% 75%,var(--b6) 75% 100%)"></div>`;
      const corps = `<div style="position:absolute;left:7mm;top:7mm">${M.logo(sombre ? "sombre" : "clair", "logo", "width:30mm;height:auto")}</div>
<div class="m" style="position:absolute;right:7mm;top:8mm;font-size:8pt;color:${sombre ? "var(--orange-s)" : "var(--orange-c)"}">${fr} / ${en}</div>
<div style="position:absolute;left:7mm;right:7mm;top:25mm"><div class="m" style="font-size:5.6pt;color:${gr}">Nom / Name</div><div style="height:9mm;border-bottom:.4pt solid ${sombre ? "rgba(245,244,239,.5)" : "rgba(18,18,24,.5)"}"></div>
<div class="m" style="font-size:5.6pt;color:${gr};margin-top:4mm">Organisation / Organization</div><div style="height:8mm;border-bottom:.4pt solid ${sombre ? "rgba(245,244,239,.5)" : "rgba(18,18,24,.5)"}"></div></div>`;
      await M.produire(nav, { dossierHtml: HTML, nom: `badge-${id}${traits ? "" : "-s"}`, pages: [M.feuille({ ...f, nom: `badge-${id}`, fondArt: art, corps })], taille: f, css: css + `.trim{color:${fg}}`,
        pdf: traits ? join(OUT, `badge-4x3po-${id}-impression.pdf`) : undefined, png: !traits ? join(OUT, `badge-4x3po-${id}.png`) : undefined, dpi: 200 });
    }
  }
  // tour de cou 20 × 900 mm (le logo complet, lu dans le sens de la longueur)
  const lw = 20, lh = 900, lf = 3, f = { w: lw, h: lh, fond: lf };
  const logos = [0, 1, 2].map((i) => `<div style="position:absolute;left:50%;top:${95 + i * 290}mm;width:${70}mm;height:${lw - 6}mm;transform-origin:0 0;transform:translate(${-(lw - 6) / 2}mm,0) rotate(90deg) translate(0,${-(lw - 6) / 2 - 0}mm);">${M.logo("sombre", "logo", `width:70mm;height:auto`)}</div>`).join("");
  const art = `<div style="position:absolute;inset:0;background:var(--noir)"></div><div class="bande-x" style="position:absolute;left:0;top:0;bottom:0;width:${3 + lf}mm;background:linear-gradient(to bottom,var(--b2) 0 25%,var(--b4) 25% 50%,var(--b5) 50% 75%,var(--b6) 75% 100%);display:none"></div>`;
  await M.produire(nav, { dossierHtml: HTML, nom: "tour-de-cou", pages: [M.feuille({ ...f, nom: "tour de cou 20x900", fondArt: art, corps: logos })], taille: f, css,
    pdf: join(OUT, "tour-de-cou-20x900mm-fond-perdu.pdf") });
  await M.produire(nav, { dossierHtml: HTML, nom: "tour-de-cou-png", pages: [M.feuille({ w: lw, h: lh, fond: 0, fondArt: art, corps: logos })], taille: { w: lw, h: lh, fond: 0 }, css, png: join(OUT, "tour-de-cou-20x900mm.png"), dpi: 150 });
}

// ------------------------------------------------------------------ signalisation de porte (Lettre) et accroche-porte (3,5 × 8,5 po)
{
  const w = po(8.5), h = po(11), fond = 3;
  const panneaux = [
    ["bienvenue", ["Bienvenue.", "Welcome."], ["Entrez, c’est ouvert.", "Come in, we’re open."], false],
    ["seance", ["Séance en cours.", "Session in progress."], ["Merci de ne pas déranger.", "Please do not disturb."], true],
  ];
  for (const [id, [a, a2], [b, b2], sombre] of panneaux) {
    const mk = (traits, fond = 3) => {
      const f = { w, h, fond, traits };
      const bg = sombre ? "var(--noir)" : "var(--papier)", fg = sombre ? "var(--texte-clair)" : "var(--encre)", ac = sombre ? "var(--orange-s)" : "var(--orange-c)";
      const cols = 22, rows = Math.round(22 * (95 + fond) / (w + 2 * fond));
      const art = `<div style="position:absolute;inset:0;background:${bg}"></div><div style="position:absolute;left:0;right:0;top:0;height:${95 + fond}mm">${M.mosaique({ cols, rows, seed: sombre ? 14 : 15, vers: "top", fade: 0.97, gap: 0.1, ancre: "xMidYMin" })}</div>
<div style="position:absolute;left:0;right:0;bottom:0;height:${3.2 + fond}mm;background:linear-gradient(to right,var(--b2) 0 25%,var(--b4) 25% 50%,var(--b5) 50% 75%,var(--b6) 75% 100%)"></div>`;
      const corps = `<div style="position:absolute;left:18mm;right:18mm;top:128mm;color:${fg}"><div class="m" style="font-size:8pt;color:${ac}">Nexora AI</div>
<div class="t" style="font-size:54pt;margin-top:6mm">${a}</div><div class="t" style="font-size:54pt;color:${sombre ? "var(--gris)" : "var(--gris-sombre)"}">${a2}</div>
<div style="margin-top:12mm;font-size:17pt;line-height:1.4">${b}<br><span style="color:${sombre ? "var(--gris)" : "var(--gris-sombre)"}">${b2}</span></div></div>
<div style="position:absolute;left:18mm;bottom:18mm">${M.logo(sombre ? "sombre" : "clair", "logo", "width:44mm;height:auto")}</div>`;
      return { f, page: M.feuille({ ...f, nom: `signalisation-${id}`, fondArt: art, corps }) };
    };
    const pa = mk(true), pb = mk(false, 0);
    await M.produire(nav, { dossierHtml: HTML, nom: `porte-${id}`, pages: [pa.page], taille: pa.f, css, pdf: join(OUT, `signalisation-porte-${id}-lettre-impression.pdf`) });
    await M.produire(nav, { dossierHtml: HTML, nom: `porte-${id}-png`, pages: [pb.page], taille: pb.f, css, png: join(OUT, `signalisation-porte-${id}-lettre.png`), dpi: 80 });
  }

  // accroche-porte : 3,5 × 8,5 po, trou de 1,5 po (diamètre) avec fente ; page 3 = gabarit de découpe
  const dw = po(3.5), dh = po(8.5);
  for (const l of ["fr", "en"]) {
    const fr = l === "fr";
    const txtA = fr ? ["Entrez,", "c’est ouvert."] : ["Come in,", "we’re open."], txtB = fr ? ["Séance en cours.", "Merci de ne pas déranger."] : ["Session in progress.", "Please do not disturb."];
    const trou = (couleur) => `<svg viewBox="0 0 ${dw} ${dh}" style="position:absolute;inset:0;width:${dw}mm;height:${dh}mm" fill="none"><circle cx="${dw / 2}" cy="34" r="${po(1.5) / 2}" stroke="${couleur}" stroke-width=".3"/><path d="M${dw / 2} ${34 + po(1.5) / 2} V${dh * 0.3}" stroke="${couleur}" stroke-width=".3"/></svg>`;
    const f = { w: dw, h: dh, fond: 3, traits: true };
    const A = M.feuille({ ...f, nom: `accroche-porte-${l} recto`, fondArt: `<div style="position:absolute;inset:0;background:var(--noir)"></div><div style="position:absolute;left:0;right:0;bottom:0;height:62mm">${M.mosaique({ cols: 9, rows: 12, seed: 27, vers: "bottom", fade: 0.97, gap: 0.1, ancre: "xMidYMax" })}</div>`,
      corps: `<div style="position:absolute;left:8mm;top:78mm;color:var(--texte-clair)"><div class="m" style="font-size:6.4pt;color:var(--orange-s)">Nexora AI</div><div class="t" style="font-size:30pt;margin-top:4mm">${txtA[0]}<br>${txtA[1]}</div></div>
<div style="position:absolute;left:8mm;right:8mm;top:30mm;height:0"></div>` });
    const B = M.feuille({ ...f, nom: `accroche-porte-${l} verso`, fondArt: `<div style="position:absolute;inset:0;background:var(--papier)"></div><div style="position:absolute;left:0;right:0;bottom:0;height:${3.2 + 3}mm;background:linear-gradient(to right,var(--b2) 0 25%,var(--b4) 25% 50%,var(--b5) 50% 75%,var(--b6) 75% 100%)"></div>`,
      corps: `<div style="position:absolute;left:8mm;right:8mm;top:78mm"><div class="m" style="font-size:6.4pt;color:var(--orange-c)">Nexora AI</div><div class="t" style="font-size:25pt;margin-top:4mm">${txtB[0]}</div><div style="margin-top:6mm;font-size:12pt;color:var(--gris-sombre)">${txtB[1]}</div></div>
<div style="position:absolute;left:8mm;bottom:14mm">${M.logo("clair", "logo", "width:30mm;height:auto")}</div>` });
    const G = M.feuille({ ...f, nom: `accroche-porte-${l} gabarit de découpe`, fondArt: '<div style="position:absolute;inset:0;background:#fff"></div>',
      corps: `<div style="position:absolute;inset:0;outline:.4mm solid #EC008C"></div>${trou("#EC008C")}<div class="m" style="position:absolute;left:6mm;bottom:10mm;font-size:6pt;color:#EC008C">Découpe / Die line (spot) : trou Ø 1,5 po + fente</div>` });
    await M.produire(nav, { dossierHtml: HTML, nom: `accroche-${l}`, pages: [A, B, G], taille: f, css, lang: l, pdf: join(OUT, `accroche-porte-3.5x8.5po-${l}-impression.pdf`) });
    const f0 = { w: dw, h: dh, fond: 0 };
    const mkp = (fond, cls) => cls;
    await M.produire(nav, { dossierHtml: HTML, nom: `accroche-${l}-png`, pages: [
      M.feuille({ ...f0, fondArt: `<div style="position:absolute;inset:0;background:var(--noir)"></div><div style="position:absolute;left:0;right:0;bottom:0;height:62mm">${M.mosaique({ cols: 9, rows: 12, seed: 27, vers: "bottom", fade: 0.97, gap: 0.1, ancre: "xMidYMax" })}</div>`,
        corps: `<div style="position:absolute;left:8mm;top:78mm;color:var(--texte-clair)"><div class="m" style="font-size:6.4pt;color:var(--orange-s)">Nexora AI</div><div class="t" style="font-size:30pt;margin-top:4mm">${txtA[0]}<br>${txtA[1]}</div></div>${trou("rgba(245,244,239,.55)")}` }),
      M.feuille({ ...f0, fondArt: `<div style="position:absolute;inset:0;background:var(--papier)"></div><div style="position:absolute;left:0;right:0;bottom:0;height:3.2mm;background:linear-gradient(to right,var(--b2) 0 25%,var(--b4) 25% 50%,var(--b5) 50% 75%,var(--b6) 75% 100%)"></div>`,
        corps: `<div style="position:absolute;left:8mm;right:8mm;top:78mm"><div class="m" style="font-size:6.4pt;color:var(--orange-c)">Nexora AI</div><div class="t" style="font-size:25pt;margin-top:4mm">${txtB[0]}</div><div style="margin-top:6mm;font-size:12pt;color:var(--gris-sombre)">${txtB[1]}</div></div><div style="position:absolute;left:8mm;bottom:14mm">${M.logo("clair", "logo", "width:30mm;height:auto")}</div>${trou("rgba(18,18,24,.5)")}` })], taille: f0, css, lang: l,
      png: (i) => join(OUT, `accroche-porte-3.5x8.5po-${l}-${i === 0 ? "recto" : "verso"}.png`), dpi: 150 });
  }
}
await nav.close();
console.log("Salon terminé →", OUT);
