// Identité : exports des logos officiels (inchangés), photos de profil, verrouillages de produit, icônes.
//   bun identite/sources/construire-identite.mjs [logos|profils|verrouillages|icones]...
import { M, ID, LOGOS, RAPPORT_LOGO, C, esc } from "./moteur.mjs";
import { copyFileSync, mkdirSync, readdirSync, readFileSync, writeFileSync, existsSync, rmSync } from "node:fs";
import { join } from "node:path";
import { execFileSync } from "node:child_process";

const FINAL = join(ID, "final");
const TMP = join(ID, "sources", "html");
mkdirSync(TMP, { recursive: true });
const quoi = new Set(process.argv.slice(2));
const veut = (k) => quoi.size === 0 || quoi.has(k);
const nav = await M.navigateur();
const LARGEURS = [256, 512, 1024, 2048, 4096];

let _n = 0;
async function ouvrir(page, html) {
  const f = join(TMP, `_page${_n++ % 4}.html`); writeFileSync(f, html);
  await page.goto("file://" + f); await page.evaluate(() => document.fonts.ready);
}
async function pageVide(largeur, hauteur, html, dpi = 96) {
  const ctx = await nav.newContext({ viewport: { width: largeur, height: hauteur }, deviceScaleFactor: dpi / 96 });
  const page = await ctx.newPage();
  await ouvrir(page, `<!doctype html><meta charset="utf-8"><style>${M.cssPolices(TMP)}html,body{margin:0;background:transparent}svg{display:block}</style>${html}`);
  return { ctx, page };
}
async function png(page, chemin, transparent = true) { mkdirSync(join(chemin, ".."), { recursive: true }); await page.screenshot({ path: chemin, omitBackground: transparent }); }

// ---------------------------------------------------------------------------------------------------------------
if (veut("logos")) {
  console.log("Logos : copie des SVG officiels, PNG, PDF…");
  const dsvg = join(FINAL, "logos", "svg"); mkdirSync(dsvg, { recursive: true });
  for (const f of readdirSync(LOGOS).filter((x) => x.endsWith(".svg"))) copyFileSync(join(LOGOS, f), join(dsvg, f));
  const dapp = join(dsvg, "app"); mkdirSync(dapp, { recursive: true });
  for (const f of readdirSync(join(LOGOS, "app"))) copyFileSync(join(LOGOS, "app", f), join(dapp, f));

  // PNG transparents : logo complet et symbole, 4 variantes, 5 largeurs
  for (const [genre, brut, rapport] of [["logo", M.logo, RAPPORT_LOGO], ["symbole", M.symbole, 1]]) {
    for (const v of ["clair", "sombre", "noir", "blanc"]) {
      for (const L of LARGEURS) {
        const H = Math.round(L / rapport);
        const { ctx, page } = await pageVide(L, H, brut(v, "x", `width:${L}px;height:${H}px`));
        await png(page, join(FINAL, "logos", "png", `nexora-ai-${genre}-${v}-${L}px.png`));
        await ctx.close();
      }
      // PDF vectoriel (100 mm de large pour le logo, 40 mm pour le symbole)
      const Wmm = genre === "logo" ? 100 : 40, Hmm = Wmm / rapport;
      const { ctx, page } = await pageVide(800, 400, `<style>@page{size:${Wmm}mm ${Hmm}mm;margin:0}</style>${brut(v, "x", `width:${Wmm}mm;height:${Hmm}mm`)}`);
      mkdirSync(join(FINAL, "logos", "pdf"), { recursive: true });
      await page.pdf({ path: join(FINAL, "logos", "pdf", `nexora-ai-${genre}-${v}.pdf`), width: `${Wmm}mm`, height: `${Hmm}mm`, printBackground: true, pageRanges: "1" });
      await ctx.close();
    }
  }
  // Sur fond (zone de protection de 10,4 unités respectée) : sombre, clair, crème ; logo et symbole
  const fonds = [["sombre", C.noir, "sombre"], ["clair", C.papier, "clair"], ["creme", C.creme, "clair"]];
  for (const [genre, rapport, ink] of [["logo", RAPPORT_LOGO, 52 * RAPPORT_LOGO], ["symbole", 1, 52]]) {
    for (const [nomFond, couleur, variante] of fonds) {
      const z = 10.4, wU = ink + 2 * z, hU = 52 + 2 * z;
      for (const L of [1024, 2048]) {
        const H = Math.round(L * hU / wU), k = L / wU;
        const svg = (genre === "logo" ? M.logo : M.symbole)(variante, "x", `position:absolute;left:${z * k}px;top:${z * k}px;width:${ink * k}px;height:${52 * k}px`);
        const { ctx, page } = await pageVide(L, H, `<div style="position:relative;width:${L}px;height:${H}px;background:${couleur}">${svg}</div>`);
        await png(page, join(FINAL, "logos", "png", `nexora-ai-${genre}-sur-${nomFond}-${L}px.png`), false);
        await ctx.close();
      }
      const Wm = genre === "logo" ? 120 : 50, Hm = Wm * hU / wU, km = Wm / wU;
      const svg = (genre === "logo" ? M.logo : M.symbole)(variante, "x", `position:absolute;left:${z * km}mm;top:${z * km}mm;width:${ink * km}mm;height:${52 * km}mm`);
      const { ctx, page } = await pageVide(600, 300, `<div style="position:relative;width:${Wm}mm;height:${Hm}mm;background:${couleur};-webkit-print-color-adjust:exact">${svg}</div>`);
      await page.pdf({ path: join(FINAL, "logos", "pdf", `nexora-ai-${genre}-sur-${nomFond}.pdf`), width: `${Wm}mm`, height: `${Hm}mm`, printBackground: true, pageRanges: "1" });
      await ctx.close();
    }
  }
}

// ---------------------------------------------------------------------------------------------------------------
if (veut("profils")) {
  console.log("Photos de profil…");
  const V = [
    ["noir", C.noir, "sombre"], ["orange-symbole-noir", C.orange, "noir"], ["orange-symbole-blanc", C.orange, "blanc"], ["creme", C.creme, "clair"], ["papier", C.papier, "clair"],
  ];
  const S = 1080, t = Math.round(S * 0.44);
  for (const [nom, fond, v] of V) {
    const svg = M.symbole(v, "x", `position:absolute;left:${(S - t) / 2}px;top:${(S - t) / 2}px;width:${t}px;height:${t}px`);
    const html = `<div style="position:relative;width:${S}px;height:${S}px;background:${fond}">${svg}</div>`;
    const { ctx, page } = await pageVide(S, S, html);
    await png(page, join(FINAL, "profils", `profil-${nom}-1080.png`), false);
    // aperçu du recadrage en cercle (pour le contrôle visuel)
    await page.evaluate(() => { document.body.style.background = "#555"; document.body.firstElementChild.style.borderRadius = "50%"; });
    await png(page, join(TMP, `_cercle-${nom}.png`), false);
    await ctx.close();
  }
  // SVG source des profils (symbole officiel dans un carré 1080)
  for (const [nom, fond, v] of V) {
    const brut = M.symboleBrut(v).trim();
    const inner = brut.replace(/^<svg[^>]*>/, "").replace(/<\/svg>$/, "");
    const k = t / 52, ox = (S - t) / 2;
    writeFileSync(join(FINAL, "profils", `profil-${nom}.svg`),
      `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${S} ${S}" width="${S}" height="${S}"><rect width="${S}" height="${S}" fill="${fond}"/><g transform="translate(${ox - 6 * k} ${ox - 6 * k}) scale(${k})">${inner}</g></svg>`);
  }
}

// ---------------------------------------------------------------------------------------------------------------
if (veut("verrouillages")) {
  console.log("Verrouillages de produit…");
  // Géométrie en unités du logo (symbole 6..58, baseline du logotype à y=50, hauteur des capitales 36, interlettrage -0,03 em)
  const TAILLE = 51, ESP = -0.03 * TAILLE, DEBUT = 76.36; // x du début du texte dans le logo officiel
  const { ctx, page } = await pageVide(800, 200, `<canvas id=c></canvas>`);
  await page.evaluate(() => document.fonts.load('500 51px Geist'));
  const mesurer = (txt) => page.evaluate(([t, taille, esp]) => {
    const c = document.getElementById("c").getContext("2d"); c.font = `500 ${taille}px Geist`; c.letterSpacing = `${esp}px`;
    const m = c.measureText(t); return { adv: m.width, droite: m.actualBoundingBoxRight, gauche: m.actualBoundingBoxLeft };
  }, [txt, TAILLE, ESP]);
  const lock = {};
  for (const o of M.OUTILS) {
    for (const [langue, nom] of [["fr", o.nom], ["en", o.nomEn]]) {
      if (langue === "en" && o.nomEn === o.nom) continue;
      const m = await mesurer(nom);
      const droite = DEBUT + m.droite; // bord droit de l'encre
      lock[`${o.id}-${langue}`] = { nom, droite };
      for (const [mode, couleur, vs] of [["sombre", C.texteClair, "sombre"], ["clair", C.encre, "clair"]]) {
        const sym = M.symboleBrut(vs).trim().replace(/^<svg[^>]*>/, "").replace(/<\/svg>$/, "");
        const W = Math.ceil((droite - 6 + 0.5) * 100) / 100;
        const svgTexte = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="6 6 ${W} 52" role="img" aria-label="${esc(nom)}">${sym}<text x="${DEBUT}" y="50" font-family="Geist, sans-serif" font-weight="500" font-size="${TAILLE}" letter-spacing="${ESP}" fill="${couleur}">${esc(nom)}</text></svg>`;
        const base = `${o.id}${langue === "en" && o.nomEn !== o.nom ? "-en" : ""}-horizontal-${mode}`;
        writeFileSync(join(TMP, `${base}.src.svg`), svgTexte);
        lock[base] = { W, svgTexte, couleur, nom, mode, sym };
      }
    }
  }
  await ctx.close();
  // 1) PNG (texte en Geist via @font-face, rendu Chromium) ; 2) PDF → contours (gs) → SVG (pdftocairo) pour des SVG sans police
  const dsvg = join(FINAL, "verrouillages", "svg"), dpng = join(FINAL, "verrouillages", "png"), dsrc = join(FINAL, "verrouillages", "svg-texte-editable");
  for (const d of [dsvg, dpng, dsrc]) mkdirSync(d, { recursive: true });
  const police64 = readFileSync(join(M.POLICES, "geist-latin-wght-normal.woff2")).toString("base64");
  for (const [base, d] of Object.entries(lock)) {
    if (!d.svgTexte) continue;
    const L = 2048, H = Math.round((L * 52) / d.W);
    const { ctx, page } = await pageVide(L, H, d.svgTexte.replace("<svg ", `<svg style="width:${L}px;height:${H}px" `));
    await page.evaluate(() => document.fonts.ready);
    await png(page, join(dpng, `nexora-${base}-2048px.png`));
    // pdf d'une seule page à la taille exacte (mm)
    const Wmm = 160, Hmm = (160 * 52) / d.W;
    const pdfTmp = join(TMP, `_${base}.pdf`);
    await ouvrir(page, `<!doctype html><meta charset="utf-8"><style>${M.cssPolices(TMP)}@page{size:${Wmm}mm ${Hmm}mm;margin:0}html,body{margin:0}svg{display:block;width:${Wmm}mm;height:${Hmm}mm}</style>${d.svgTexte}`);
    await page.pdf({ path: pdfTmp, width: `${Wmm}mm`, height: `${Hmm}mm`, printBackground: true, pageRanges: "1" });
    await ctx.close();
    const out = join(TMP, `_${base}-o.pdf`);
    execFileSync("gs", ["-q", "-dNOPAUSE", "-dBATCH", "-sDEVICE=pdfwrite", "-dNoOutputFonts", `-sOutputFile=${out}`, pdfTmp]);
    const svgOut = join(dsvg, `nexora-${base}.svg`);
    execFileSync("pdftocairo", ["-svg", out, svgOut]);
    // SVG éditable (texte + police Geist intégrée en base64)
    writeFileSync(join(dsrc, `nexora-${base}.svg`), d.svgTexte.replace("<svg ", `<svg `).replace(">", `><defs><style>@font-face{font-family:"Geist";font-weight:100 900;src:url(data:font/woff2;base64,${police64}) format("woff2")}</style></defs>`));
    rmSync(pdfTmp); rmSync(out);
  }
}

// ---------------------------------------------------------------------------------------------------------------
if (veut("icones")) {
  console.log("Bannière d’icône 1024…");
  const brut = readFileSync(join(LOGOS, "app", "tuile-apple.svg"), "utf8");
  const { ctx, page } = await pageVide(1024, 1024, brut.replace("<svg ", `<svg style="width:1024px;height:1024px" `));
  await png(page, join(FINAL, "icones", "icone-application-1024.png"), false);
  await ctx.close();
  const brutP = readFileSync(join(LOGOS, "app", "tuile-petite.svg"), "utf8");
  const r2 = await pageVide(1024, 1024, brutP.replace("<svg ", `<svg style="width:1024px;height:1024px" `));
  await png(r2.page, join(FINAL, "icones", "icone-tuile-arrondie-1024.png"), true);
  await r2.ctx.close();
  const r3 = await pageVide(1024, 1024, readFileSync(join(LOGOS, "app", "tuile-maskable.svg"), "utf8").replace("<svg ", `<svg style="width:1024px;height:1024px" `));
  await png(r3.page, join(FINAL, "icones", "icone-maskable-1024.png"), false);
  await r3.ctx.close();
  // Bannière d'icône : tuile noire + symbole, sur toute la largeur (1024 x 1024 carrée ; sert de visuel d'application)
  const r4 = await pageVide(1024, 1024, `<div style="position:relative;width:1024px;height:1024px;background:${C.noir};overflow:hidden">${M.mosaique({ cols: 16, rows: 16, seed: 21, vers: [1, 1], fade: 0.92, gap: 0.08, keep: (c) => !(c.col >= 3 && c.col <= 12 && c.row >= 3 && c.row <= 12) })}${M.symbole("sombre", "x", "position:absolute;left:282px;top:282px;width:460px;height:460px")}</div>`);
  await png(r4.page, join(FINAL, "icones", "banniere-icone-1024.png"), false);
  await r4.ctx.close();
}
await nav.close();
console.log("Terminé.");
