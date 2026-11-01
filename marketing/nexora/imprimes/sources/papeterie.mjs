// Papeterie Nexora AI : papier à en-tête (Lettre, A4), enveloppes (DL, #10), carte de remerciement 5 × 7 po,
// facture / soumission, étiquette d'expédition, signature courriel. Tout se régénère depuis coordonnees.json.
//   bun imprimes/sources/papeterie.mjs [--coordonnees chemin.json] [--url-images https://…/images]
import { M, IM, po, esc, lireCoordonnees, slugPersonne, COORDONNEES, C } from "../../identite/sources/moteur.mjs";
import { join, resolve } from "node:path";
import { mkdirSync, writeFileSync, copyFileSync, existsSync } from "node:fs";

const arg = (k, d) => { const i = process.argv.indexOf(k); return i > 0 ? process.argv[i + 1] : d; };
const c = lireCoordonnees(resolve(arg("--coordonnees", COORDONNEES)));
const URL_IMAGES = arg("--url-images", null);
const OUT = join(IM, "final", "papeterie");
const HTML = join(IM, "sources", "html", "papeterie");
mkdirSync(OUT, { recursive: true }); mkdirSync(HTML, { recursive: true });

const LIB = {
  fr: { courriel: "Courriel", tel: "Tél.", web: "Web", adr: "Adresse", entreprise: "Nexora AI" },
  en: { courriel: "Email", tel: "Tel.", web: "Web", adr: "Address", entreprise: "Nexora AI" },
};
const CSS = `
.page{background:var(--papier);color:var(--encre)}
.lib{font-size:6pt;color:var(--gris-sombre)}
.txt{font-size:8.6pt;line-height:1.45}
.pied{position:absolute;left:0;right:0;bottom:0;display:grid;gap:4mm}
.pied .col{min-width:0}
.pied .lib{display:block;margin-bottom:.6mm}
.pied .val{display:block;font-size:7.4pt;line-height:1.3;overflow-wrap:anywhere}
.filet{height:0;border-top:.3pt solid rgba(18,18,24,.35)}
.mini-bande{width:12mm;height:3.2mm;background:linear-gradient(to bottom,var(--b2) 0 25%,var(--b4) 25% 50%,var(--b5) 50% 75%,var(--b6) 75% 100%)}
`;
const pied = (lang) => {
  const L = LIB[lang];
  return `<div class="pied" style="grid-template-columns:repeat(${[c.adresse, c.courriel_general, c.telephone, c.site].filter((b) => b && !/^\s*$/.test(b)).length || 1}, 1fr)">
${[[L.adr, c.adresse], [L.courriel, c.courriel_general], [L.tel, c.telephone], [L.web, c.site]].filter(([, b]) => b && !/^\s*$/.test(b)).map(([a, b]) => `<div class="col"><span class="lib mono">${a}</span><span class="val">${esc(b)}</span></div>`).join("\n")}</div>`;
};
const nav = await M.navigateur();
const P = (nom, opts) => M.produire(nav, { dossierHtml: HTML, ...opts, nom });

// ------------------------------------------------------------------------------------------- papier à en-tête
for (const [fmt, w, h] of [["lettre", po(8.5), po(11)], ["a4", 210, 297]]) {
  for (const lang of ["fr", "en"]) {
    const corps = `<div style="position:absolute;left:20mm;right:20mm;top:16mm;bottom:15mm">
${M.logo("clair", "logo", "width:42mm;height:auto")}
<div style="margin-top:6mm" class="filet"></div>
${pied(lang).replace('class="pied"', 'class="pied" style="grid-template-columns:1.3fr 1fr 1fr 1fr;"')}
<div style="position:absolute;left:0;bottom:19mm" class="mini-bande"></div>
</div>`;
    const f = { w, h, fond: 0 };
    await P(`papier-en-tete-${fmt}-${lang}`, { pages: [M.feuille({ ...f, corps })], css: CSS, taille: f, lang,
      pdf: join(OUT, `papier-en-tete-${fmt}-${lang}.pdf`), png: join(OUT, `papier-en-tete-${fmt}-${lang}.png`), dpi: 100 });
  }
}

// ------------------------------------------------------------------------------------------- enveloppes
const adresseRetour = `<div class="txt" style="font-size:7.6pt;line-height:1.4;margin-top:2.4mm"><b style="font-weight:600">Nexora AI</b>${[c.adresse, c.courriel_general, c.site].filter((b) => b && !/^\s*$/.test(b)).map((b) => `<br>${esc(b)}`).join("")}</div>`;
for (const [nom, w, h] of [["dl", 220, 110], ["no10", po(9.5), po(4.125)]]) {
  const f = { w, h, fond: 3, traits: true };
  const face = M.feuille({ ...f, nom: `enveloppe-${nom} face`, fondArt: '<div style="position:absolute;inset:0;background:var(--papier)"></div>',
    corps: `<div style="position:absolute;left:12mm;top:11mm">${M.logo("clair", "logo", "width:30mm;height:auto")}${adresseRetour}</div>
<div style="position:absolute;left:12mm;bottom:8mm"><div class="mini-bande"></div></div>` });
  const cols = 60, rows = Math.round(60 * (h + 6) / (w + 6));
  const dos = M.feuille({ ...f, nom: `enveloppe-${nom} dos (rabat)`, fondArt: `<div style="position:absolute;inset:0;background:var(--noir)"></div><div class="grille" style="--pas:6mm;--g:rgba(245,244,239,.07);--masque:linear-gradient(to right,#000,transparent 70%)"></div>${M.mosaique({ cols: 70, rows: Math.round(70 * (h + 6) / (w + 6)), seed: 5, vers: "right", fade: 0.97, gap: 0.09, keep: (x) => x.col >= 26, ancre: "xMaxYMid" })}`,
    corps: `<div style="position:absolute;left:12mm;bottom:11mm">${M.symbole("sombre", "symbole", "width:15mm;height:15mm")}</div>` });
  const ff = { ...f };
  await P(`enveloppe-${nom}`, { pages: [face, dos], css: CSS, taille: ff,
    pdf: join(OUT, `enveloppe-${nom}-impression.pdf`), png: (i) => join(OUT, `enveloppe-${nom}-${i === 0 ? "face" : "dos"}.png`), dpi: 100 });
}

// ------------------------------------------------------------------------------------------- carte de remerciement 5 x 7 po
for (const lang of ["fr", "en"]) {
  const w = po(5), h = po(7), f = { w, h, fond: 3, traits: true };
  const mot = lang === "fr" ? "Merci." : "Thank you.";
  const face = M.feuille({ ...f, nom: `carte-remerciement-${lang} recto`,
    fondArt: `<div style="position:absolute;inset:0;background:var(--noir)"></div><div class="grille" style="--pas:6.35mm;--g:rgba(245,244,239,.07);--masque:linear-gradient(to bottom,#000,transparent 65%)"></div>${M.mosaique({ cols: 22, rows: 31, seed: 9, vers: "top", fade: 0.97, gap: 0.09, keep: (x) => x.row <= 17, ancre: "xMidYMin" })}`,
    corps: `<div style="position:absolute;left:12mm;bottom:15mm;color:var(--texte-clair)"><div class="geist" style="font-size:46pt">${mot}</div></div>
<div style="position:absolute;right:12mm;bottom:15.4mm">${M.symbole("sombre", "symbole", "width:11mm;height:11mm")}</div>` });
  const dos = M.feuille({ ...f, nom: `carte-remerciement-${lang} verso`, fondArt: '<div style="position:absolute;inset:0;background:var(--papier)"></div>',
    corps: `<div style="position:absolute;left:14mm;top:14mm;right:14mm;bottom:12mm">${M.logo("clair", "logo", "width:36mm;height:auto")}
<div style="position:absolute;left:0;right:0;bottom:0">${pied(lang).replace('class="pied"', 'class="pied" style="position:static;grid-template-columns:1fr 1fr"')}</div></div>` });
  await P(`carte-remerciement-${lang}`, { pages: [face, dos], css: CSS, taille: f, lang,
    pdf: join(OUT, `carte-remerciement-5x7-${lang}-impression.pdf`), png: (i) => join(OUT, `carte-remerciement-5x7-${lang}-${i === 0 ? "recto" : "verso"}.png`), dpi: 100 });
}

// ------------------------------------------------------------------------------------------- facture / soumission
const FAC = {
  fr: { titre: "Facture", titre2: "Soumission", no: "N°", date: "Date", ech: "Échéance / valide jusqu’au", client: "Client", nomc: "Nom", adr: "Adresse", mail: "Courriel", desc: "Description", qte: "Qté", pu: "Prix unitaire", mont: "Montant", st: "Sous-total", tps: "TPS", tvq: "TVQ", tot: "Total", notes: "Notes et conditions", ntps: "N° TPS", ntvq: "N° TVQ", ref: "Référence" },
  en: { titre: "Invoice", titre2: "Quote", no: "No.", date: "Date", ech: "Due / valid until", client: "Client", nomc: "Name", adr: "Address", mail: "Email", desc: "Description", qte: "Qty", pu: "Unit price", mont: "Amount", st: "Subtotal", tps: "GST", tvq: "QST", tot: "Total", notes: "Notes and terms", ntps: "GST no.", ntvq: "QST no.", ref: "Reference" },
};
for (const [fmt, w, h] of [["lettre", po(8.5), po(11)], ["a4", 210, 297]]) {
  for (const lang of ["fr", "en"]) {
    const T = FAC[lang];
    const champ = (lib, extra = "") => `<div style="${extra}"><span class="lib mono">${lib}</span><div style="border-bottom:.4pt solid rgba(18,18,24,.4);height:6.4mm"></div></div>`;
    const lignes = Array.from({ length: 11 }, () => `<tr><td></td><td></td><td></td><td></td></tr>`).join("");
    const corps = `<div style="position:absolute;left:18mm;right:18mm;top:15mm;bottom:14mm">
<div style="display:flex;justify-content:space-between;align-items:flex-start">${M.logo("clair", "logo", "width:40mm;height:auto")}
<div style="text-align:right"><div class="geist" style="font-size:26pt;line-height:1">${T.titre} <span style="color:var(--gris-sombre)">/</span> ${T.titre2}</div>
<div class="mono" style="font-size:6pt;margin-top:2mm;color:var(--gris-sombre)">☐ ${T.titre} &nbsp;&nbsp; ☐ ${T.titre2}</div></div></div>
<div style="display:grid;grid-template-columns:1fr 1fr 1.3fr;gap:5mm;margin-top:9mm">${champ(T.no)}${champ(T.date)}${champ(T.ech)}</div>
<div style="display:grid;grid-template-columns:1fr 1fr;gap:5mm 8mm;margin-top:5mm">
<div style="grid-column:1/3"><span class="lib mono" style="color:var(--orange-c)">${T.client}</span></div>
${champ(T.nomc)}${champ(T.mail)}${champ(T.adr, "grid-column:1/3")}</div>
<table style="width:100%;border-collapse:collapse;margin-top:8mm;font-size:8pt">
<thead><tr>${[[T.desc, "52%", "left"], [T.qte, "10%", "right"], [T.pu, "19%", "right"], [T.mont, "19%", "right"]].map(([t, wd, a]) => `<th class="mono" style="width:${wd};text-align:${a};font-size:5.8pt;padding:2mm 1.5mm;border-top:.9pt solid var(--encre);border-bottom:.4pt solid var(--encre);font-weight:500">${t}</th>`).join("")}</tr></thead>
<tbody>${lignes}</tbody></table>
<style>.trim table tbody td{height:7.8mm;border-bottom:.3pt solid rgba(18,18,24,.28)}</style>
<div style="display:grid;grid-template-columns:1fr 62mm;gap:8mm;margin-top:6mm">
<div><span class="lib mono">${T.notes}</span><div style="margin-top:1.6mm;border:.3pt solid rgba(18,18,24,.35);height:30mm"></div>
<div style="display:grid;grid-template-columns:1fr 1fr;gap:5mm;margin-top:4mm">${champ(T.ntps)}${champ(T.ntvq)}</div></div>
<div>${[T.st, T.tps, T.tvq].map((t) => `<div style="display:flex;justify-content:space-between;align-items:flex-end;height:7mm;border-bottom:.3pt solid rgba(18,18,24,.3)"><span class="lib mono" style="margin:0">${t}</span></div>`).join("")}
<div style="display:flex;justify-content:space-between;align-items:flex-end;height:9mm;border-bottom:.9pt solid var(--encre);margin-top:1.5mm"><span class="mono" style="font-size:7pt">${T.tot}</span></div></div></div>
<div style="position:absolute;left:0;right:0;bottom:0">${pied(lang).replace('class="pied"', 'class="pied" style="position:static;grid-template-columns:1.3fr 1fr 1fr 1fr"')}</div></div>`;
    const f = { w, h, fond: 0 };
    await P(`facture-${fmt}-${lang}`, { pages: [M.feuille({ ...f, corps })], css: CSS, taille: f, lang,
      pdf: join(OUT, `facture-soumission-${fmt}-${lang}.pdf`), png: join(OUT, `facture-soumission-${fmt}-${lang}.png`), dpi: 100 });
  }
}

// ------------------------------------------------------------------------------------------- étiquette d'expédition 4 x 6 po
{
  const w = po(4), h = po(6), f = { w, h, fond: 0 };
  const zone = (lib, hh, extra = "") => `<div style="border:.5pt solid var(--encre);padding:2.2mm 2.8mm;${extra}"><span class="lib mono" style="color:var(--encre)">${lib}</span><div style="height:${hh}"></div></div>`;
  const corps = `<div style="position:absolute;inset:0;background:var(--papier)"></div>
<div style="position:absolute;left:0;right:0;top:0;height:17mm;background:var(--noir);display:flex;align-items:center;padding:0 5mm">${M.logo("sombre", "logo", "width:34mm;height:auto")}</div>
<div class="bande-x" style="position:absolute;left:0;right:0;top:17mm;height:1.6mm"></div>
<div style="position:absolute;left:5mm;right:5mm;top:23mm;display:grid;gap:3mm">
<div style="border:.5pt solid var(--encre);padding:2.2mm 2.8mm"><span class="lib mono" style="color:var(--encre)">Expéditeur / From</span><div class="txt" style="font-size:7.4pt;margin-top:1mm">Nexora AI${c.adresse && !/^\s*$/.test(c.adresse) ? `<br>${esc(c.adresse)}` : ""}</div></div>
${zone("Destinataire / To", "36mm")}
<div style="display:grid;grid-template-columns:1fr 1fr;gap:3mm">${zone("N° commande / Order no.", "7mm")}${zone("Poids / Weight", "7mm")}</div>
${zone("Code de suivi / Tracking", "20mm", "border-style:dashed")}
</div>
<div class="mono" style="position:absolute;left:5mm;bottom:4mm;font-size:5.4pt;color:var(--gris-sombre)">${esc(c.site)}</div>`;
  await P("etiquette-expedition-4x6", { pages: [M.feuille({ ...f, corps })], css: CSS, taille: f,
    pdf: join(OUT, "etiquette-expedition-4x6.pdf"), png: join(OUT, "etiquette-expedition-4x6.png"), dpi: 150 });
}

// ------------------------------------------------------------------------------------------- signature courriel (HTML compatible clients)
const sigDir = join(OUT, "signature-courriel"); mkdirSync(join(sigDir, "images"), { recursive: true });
{ // images à héberger : symbole (2x) pour la signature
  const cp = (a, b) => copyFileSync(join(M.ID, "final", "logos", "png", a), join(sigDir, "images", b));
  if (existsSync(join(M.ID, "final", "logos", "png", "nexora-ai-symbole-clair-256px.png"))) {
    cp("nexora-ai-symbole-clair-256px.png", "nexora-ai-symbole-signature.png");
    cp("nexora-ai-logo-clair-512px.png", "nexora-ai-logo-signature.png");
  }
}
c.personnes.forEach((p, i) => {
  const slug = slugPersonne(p, i);
  for (const lang of ["fr", "en"]) {
    const en = lang === "en";
    const titre = en ? (p.titre_en || p.titre) : p.titre;
    const L = en ? { c: "Email", t: "Tel.", w: "Web" } : { c: "Courriel", t: "Tél.", w: "Web" };
    const courriel = p.courriel || c.courriel_general, tel = p.telephone || c.telephone;
    const base = URL_IMAGES ? URL_IMAGES.replace(/\/$/, "") + "/" : "images/";
    const F = "font-family:Arial,Helvetica,sans-serif;";
    const html = `<!-- Signature Nexora AI (${lang}) pour ${esc(p.nom)}. Images à héberger : ${base}nexora-ai-symbole-signature.png (largeur affichée 56 px). -->
<table cellpadding="0" cellspacing="0" border="0" role="presentation" style="border-collapse:collapse;${F}color:#121218;">
<tr>
<td valign="top" style="padding:0 16px 0 0;"><img src="${base}nexora-ai-symbole-signature.png" width="56" height="56" alt="Nexora AI" style="display:block;border:0;width:56px;height:56px;"></td>
<td valign="top" style="border-left:1px solid #D9D8D0;padding:0 0 0 16px;">
<div style="${F}font-size:16px;line-height:20px;font-weight:bold;color:#121218;">${esc(p.nom)}</div>
<div style="${F}font-size:13px;line-height:18px;color:#54545F;">${esc(titre)}</div>
<table cellpadding="0" cellspacing="0" border="0" role="presentation" style="border-collapse:collapse;margin:8px 0 8px 0;"><tr>
<td width="18" height="4" bgcolor="#FFB11A" style="font-size:0;line-height:0;">&nbsp;</td><td width="18" height="4" bgcolor="#FF5A1F" style="font-size:0;line-height:0;">&nbsp;</td><td width="18" height="4" bgcolor="#E0341C" style="font-size:0;line-height:0;">&nbsp;</td><td width="18" height="4" bgcolor="#B01A3C" style="font-size:0;line-height:0;">&nbsp;</td></tr></table>
<div style="${F}font-size:12px;line-height:18px;color:#121218;"><span style="color:#54545F;">${L.c}&nbsp;</span>${esc(courriel)}<br>${tel && !/^\s*$/.test(tel) ? `<span style="color:#54545F;">${L.t}&nbsp;</span>${esc(tel)}<br>` : ""}<span style="color:#54545F;">${L.w}&nbsp;</span>${esc(c.site)}</div>
<div style="${F}font-size:11px;line-height:16px;color:#54545F;padding-top:6px;">${esc(en ? c.signature_en : c.signature)}</div>
</td></tr></table>`;
    writeFileSync(join(sigDir, `signature-${slug}-${lang}.html`), html);
    const txt = `${p.nom}\n${titre}\nNexora AI\n${L.c}: ${courriel}\n${tel && !/^\s*$/.test(tel) ? `${L.t}: ${tel}\n` : ""}${L.w}: ${c.site}\n${en ? c.signature_en : c.signature}\n`;
    writeFileSync(join(sigDir, `signature-${slug}-${lang}.txt`), txt);
  }
});
// aperçu des signatures (page d'essai à fond blanc, 2x)
for (const [i, p] of c.personnes.entries()) {
  const slug = slugPersonne(p, i);
  for (const lang of ["fr", "en"]) {
    const frag = (await import("node:fs")).readFileSync(join(sigDir, `signature-${slug}-${lang}.html`), "utf8");
    const f = join(HTML, `signature-${slug}-${lang}-apercu.html`);
    M.ecrire(f, `<!doctype html><meta charset="utf-8"><body style="margin:0;background:#fff"><div class="page" style="padding:28px 32px;width:640px;box-sizing:border-box">${frag.replace(/src="images\//g, `src="${M.htmlRel(HTML, join(sigDir, "images")) }/`)}</div>`);
    await M.rendre(nav, { fichierHtml: f, png: join(sigDir, `signature-${slug}-${lang}.png`), dpi: 192, selecteur: ".page", largeurPx: 640 });
  }
}
await nav.close();
console.log("Papeterie terminée →", OUT);
