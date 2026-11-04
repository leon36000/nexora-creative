// Film V6 : capture d'un VRAI détourage vidéo dans Creative (page /detourage, serveur SAM 2.1 + ViTMatte de la GB10).
// Import d'un rush du film, clics sur les sujets (masque en direct), fond = un autre rush du film, détourage complet,
// puis les trois vues (Damier, Matte, Nouveau fond) ; les sorties du travail sont téléchargées pour l'avant/après.
// Usage : node capturer_detourage.mjs <dossier> <video.mp4> <fond.mp4|png> "<x1,y1;x2,y2…>" (coordonnées 0..1)
import { chromium } from '../../../mode-studio/node_modules/playwright/index.mjs';
import { mkdirSync, appendFileSync, writeFileSync } from 'node:fs';
import { join } from 'node:path';

const [dossier, source, fond, clics] = process.argv.slice(2);
const BASE = process.env.UI ?? 'http://127.0.0.1:37170';
mkdirSync(dossier, { recursive: true });
const journal = (o) => appendFileSync(join(dossier, 'journal.jsonl'), JSON.stringify({ t: Date.now() / 1000, ...o }) + '\n');
let n = 0, travail = null;
const nav = await chromium.launch({ executablePath: process.env.CHROME ?? `${process.env.HOME}/.cache/ms-playwright/chromium-1248/chrome-linux-arm64/chrome` });
const page = await nav.newPage({ viewport: { width: 1600, height: 900 }, deviceScaleFactor: 2 });
page.on('response', (r) => { const m = /\/api\/nexora\/detourage\/travaux\/([\w-]+)/.exec(r.url()); if (m) travail = m[1]; });
const cliche = async (etiquette) => {
  const f = join(dossier, `${String(n++).padStart(4, '0')}-${etiquette}.jpg`);
  await page.screenshot({ path: f, type: 'jpeg', quality: 95 });
  journal({ image: f, etiquette });
};
const attendre = (ms) => new Promise((r) => setTimeout(r, ms));

await page.goto(BASE + '/detourage', { waitUntil: 'networkidle' });
await attendre(1000); await cliche('page');
await page.locator('input[type=file]').first().setInputFiles(source);
const video = page.locator('main video').first();
await video.waitFor({ state: 'visible', timeout: 120000 });
await attendre(2500); await cliche('importee');
const b = await video.boundingBox();
for (const p of clics.split(';')) {
  const [x, y] = p.split(',').map(Number);
  await page.mouse.click(b.x + x * b.width, b.y + y * b.height);
  for (let i = 0; i < 6; i++) { await attendre(250); await cliche('masque'); }
}
await page.getByRole('button', { name: 'Détourage complet' }).click();
await page.getByRole('button', { name: 'Image', exact: true }).click();
await attendre(400);
await page.locator('input[type=file]').nth(1).setInputFiles(fond);
await attendre(3000); await cliche('fond');
await page.getByRole('button', { name: 'Lancer le détourage' }).click();
const t0 = Date.now(); let dernier = 0;
const damier = page.getByRole('button', { name: 'Damier', exact: true });
while (!(await damier.isVisible().catch(() => false)) && Date.now() - t0 < 30 * 60000) {
  if (Date.now() - dernier > 10000) { await cliche('calcul'); dernier = Date.now(); }
  await attendre(1500);
}
journal({ etape: 'termine', secondes: (Date.now() - t0) / 1000, travail });
for (const v of ['Damier', 'Matte', 'Nouveau fond']) {
  await page.getByRole('button', { name: v, exact: true }).click();
  for (let i = 0; i < 10; i++) { await attendre(200); await cliche('vue-' + v.toLowerCase().replace(' ', '-')); }
}
writeFileSync(join(dossier, 'travail.json'), JSON.stringify({ travail, secondes: (Date.now() - t0) / 1000 }));
console.log(JSON.stringify({ travail, secondes: (Date.now() - t0) / 1000 }));
await nav.close();
