// Planche-contact : bun planche.mjs sortie.png colonnes hauteurCase fichier1.png fichier2.png ...
// Les .pdf sont rastérisés (page 1 à 40 dpi) avant. Utilisée pour apercu.png de chaque famille.
import { M } from "./moteur.mjs";
import { tmpdir } from "node:os";
import { join, basename } from "node:path";
import { mkdirSync } from "node:fs";
const [sortie, colonnes, hauteur, ...fichiers] = process.argv.slice(2);
const tmp = join(M.ID, "sources", "html"); mkdirSync(tmp, { recursive: true });
const nav = await M.navigateur();
const images = fichiers.map((f, i) => {
  if (f.endsWith(".pdf")) { const p = join(tmp, `_pl${i}`); M.pdfVersPng(f, p, 50); return { fichier: p + "-1.png", nom: basename(f) }; }
  return { fichier: f, nom: basename(f) };
});
await M.planche(nav, { images, sortie, colonnes: +colonnes, hauteurCase: +hauteur, largeur: +(process.env.LARGEUR || 2000), dossierTmp: tmp });
await nav.close();
