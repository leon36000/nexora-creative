// Cartes d'affaires : une carte par personne de coordonnees.json.
//   bun imprimes/sources/generer-cartes.mjs [--coordonnees chemin.json] [--sortie dossier] [--seulement slug]
//   (ou ./imprimes/generer-cartes avec les mêmes options)
// Sorties (dossier imprimes/final/cartes/<slug>/) :
//   carte-<slug>-<variante>-impression.pdf  : recto, verso, calque de vernis ; fond perdu 3 mm et traits de coupe
//   carte-<slug>-<variante>-sans-traits.pdf : mêmes pages, fond perdu 3 mm, sans traits
//   carte-<slug>-recto.png, carte-<slug>-verso-<variante>.png : prévisualisation 300 dpi à la taille finale (88,9 × 50,8 mm)
// variantes : fr, en, braise-fr, braise-en.   Calque de vernis commun : vernis/carte-vernis.svg et .pdf
import { M, IM, po, lireCoordonnees, slugPersonne, COORDONNEES } from "../../identite/sources/moteur.mjs";
import { W, H, FOND, CSS_CARTE, rectoArt, rectoCorps, versoArt, versoCorps, versoBande, vernisCorps, vernisSvgCoupe } from "./cartes.mjs";
import { join, resolve } from "node:path";
import { existsSync, mkdirSync, renameSync } from "node:fs";
import { execFileSync } from "node:child_process";
// Texte tracé en contours (gs -dNoOutputFonts) : aucune police à embarquer chez l'imprimeur (les cartes n'ont aucune image raster).
function tracer(pdf) { try { const t = pdf + ".tmp"; execFileSync("gs", ["-q", "-dNOPAUSE", "-dBATCH", "-sDEVICE=pdfwrite", "-dNoOutputFonts", "-dCompatibilityLevel=1.6", `-sOutputFile=${t}`, pdf]); renameSync(t, pdf); } catch { /* gs absent : on garde le PDF aux polices intégrées */ } }

const arg = (k, d) => { const i = process.argv.indexOf(k); return i > 0 ? process.argv[i + 1] : d; };
const coordPath = resolve(arg("--coordonnees", COORDONNEES));
const sortie = resolve(arg("--sortie", join(IM, "final", "cartes")));
const seul = arg("--seulement", null);
const HTML = join(IM, "sources", "html", "cartes");
mkdirSync(HTML, { recursive: true });
const c = lireCoordonnees(coordPath);
const nav = await M.navigateur();

const VARIANTES = [["fr", "fr", false], ["en", "en", false], ["braise-fr", "fr", true], ["braise-en", "en", true]];
const base = { w: W, h: H, fond: FOND };
const pageRecto = (traits, nom) => M.feuille({ ...base, traits, nom, fondArt: rectoArt(), corps: rectoCorps() });
const pageVerso = (p, langue, braise, traits, nom) => M.feuille({ ...base, traits, nom, fondArt: versoArt(braise) + versoBande(braise), corps: versoCorps(p, c, langue, braise) });
const pageVernis = (traits, nom) => M.feuille({ ...base, traits, nom: nom + " · VERNIS SÉLECTIF (100 % noir)", fondArt: '<div style="position:absolute;inset:0;background:#fff"></div>', corps: vernisCorps() });

// Calque de vernis commun
{
  const vd = join(sortie, "vernis"); mkdirSync(vd, { recursive: true });
  M.ecrire(join(vd, "carte-vernis.svg"), vernisSvgCoupe());
  await M.produire(nav, { dossierHtml: HTML, nom: "carte-vernis", pages: [pageVernis(true, "carte-vernis")], taille: { ...base, traits: true }, pdf: join(vd, "carte-vernis.pdf") });
  tracer(join(vd, "carte-vernis.pdf"));
}

const personnes = c.personnes.map((p, i) => ({ p, slug: slugPersonne(p, i) })).filter((x) => !seul || x.slug === seul);
for (const { p, slug } of personnes) {
  console.log("Carte :", slug);
  const dir = join(sortie, slug); mkdirSync(dir, { recursive: true });
  for (const [nomVar, langue, braise] of VARIANTES) {
    const nom = `carte-${slug}-${nomVar}`;
    for (const traits of [true, false]) {
      await M.produire(nav, {
        dossierHtml: HTML, nom: `${nom}${traits ? "-impression" : "-sans-traits"}`,
        pages: [pageRecto(traits, nom + " recto"), pageVerso(p, langue, braise, traits, nom + " verso"), ...(traits ? [pageVernis(true, nom)] : [])],
        css: CSS_CARTE, taille: { ...base, traits }, lang: langue,
        pdf: join(dir, `${nom}-${traits ? "impression" : "sans-traits"}.pdf`),
      });
      tracer(join(dir, `${nom}-${traits ? "impression" : "sans-traits"}.pdf`));
    }
    // PNG 300 dpi à la taille finale (sans fond perdu)
    const f = { w: W, h: H, fond: 0 };
    await M.produire(nav, {
      dossierHtml: HTML, nom: `${nom}-apercu`, pages: [M.feuille({ ...f, fondArt: versoArt(braise) + versoBande(braise, 0), corps: versoCorps(p, c, langue, braise) })], css: CSS_CARTE, taille: f, lang: langue,
      png: join(dir, `carte-${slug}-verso-${nomVar}.png`), dpi: 300,
    });
  }
  await M.produire(nav, { dossierHtml: HTML, nom: "carte-recto-apercu", pages: [M.feuille({ w: W, h: H, fond: 0, fondArt: rectoArt(), corps: rectoCorps() })], css: CSS_CARTE, taille: { w: W, h: H, fond: 0 }, png: join(dir, `carte-${slug}-recto.png`), dpi: 300 });
}
await nav.close();
console.log("Cartes terminées →", sortie);
