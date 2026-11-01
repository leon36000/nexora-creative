// Aperçus PNG de pages HTML : bun apercus_html.mjs sortie.png largeur fichier.html [hauteur_max]
import { chromium } from "/home/pc6/Desktop/NexoraSite/web/node_modules/@playwright/test/index.mjs";
const [out, w, file, hmax] = process.argv.slice(2);
const b = await chromium.launch();
const p = await b.newPage({ viewport: { width: +w, height: 900 } });
await p.goto("file://" + file); await p.waitForTimeout(500);
await p.screenshot({ path: out, fullPage: !(hmax && +hmax > 0), ...(hmax && +hmax > 0 ? { clip: { x: 0, y: 0, width: +w, height: +hmax } } : {}) });
await b.close();
