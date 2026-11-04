// Film V6 : capture d'un VRAI « Texte → 3D » dans Relief (le mode 3D de Creative, TRELLIS.2 sur la GB10).
// Phase 1 : saisie et lancement ; attente du modèle (le serveur dessine une photo produit, reconstruit, juge 4 côtés).
// Phase 2 : le modèle fini est tourné à la souris et photographié en trois rendus : fil de fer, argile, texturé.
// Usage : node capturer_relief.mjs <dossier> "<objet>" [Draft|High]
import { chromium } from '../../../mode-studio/node_modules/playwright/index.mjs';
import { mkdirSync, appendFileSync } from 'node:fs';
import { join } from 'node:path';

const [dossier, objet, detail = 'High'] = process.argv.slice(2);
const URL = (process.env.UI ?? 'http://127.0.0.1:37170') + '/relief';
mkdirSync(dossier, { recursive: true });
const journal = (o) => appendFileSync(join(dossier, 'journal.jsonl'), JSON.stringify({ t: Date.now() / 1000, ...o }) + '\n');
let n = 0;
const nav = await chromium.launch({
  executablePath: process.env.CHROME ?? `${process.env.HOME}/.cache/ms-playwright/chromium-1248/chrome-linux-arm64/chrome`,
  args: ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader'],
});
const page = await nav.newPage({ viewport: { width: 1600, height: 900 }, deviceScaleFactor: 2 });
const cliche = async (etiquette) => {
  const f = join(dossier, `${String(n++).padStart(4, '0')}-${etiquette}.jpg`);
  await page.screenshot({ path: f, type: 'jpeg', quality: 95 });
  journal({ image: f, etiquette });
};
const attendre = (ms) => new Promise((r) => setTimeout(r, ms));

await page.goto(URL, { waitUntil: 'networkidle' });
if (process.env.VOIR) {
  // modèle déjà fait (prise VOIR) : on l'ouvre dans la vue principale de Relief
  await attendre(2000);
  await page.goto(URL + '?take=' + process.env.VOIR, { waitUntil: 'networkidle' }); await attendre(3000);
  const carte = page.locator('.grid.dense > *').first();
  if (!(await page.locator('.object-focus canvas').isVisible().catch(() => false))) await carte.click().catch(() => {});
} else {
await page.getByRole('button', { name: 'Texte → 3D' }).click();
await attendre(500);
const champ = page.getByLabel('Description de l’objet');
await champ.click();
for (const c of objet) { await champ.press(c === ' ' ? 'Space' : c).catch(() => champ.type(c)); await cliche('saisie'); }
const b = page.getByRole('button', { name: detail, exact: true });
if (await b.isVisible().catch(() => false)) { await b.click(); await attendre(300); }
await cliche('reglage');
await page.getByRole('button', { name: /Créer en 3D/ }).click();
}
const t0 = Date.now();
let dernier = 0;
const focus = page.locator('.object-focus canvas');
while (!(await focus.isVisible().catch(() => false)) && Date.now() - t0 < 40 * 60000) {
  if (Date.now() - dernier > 15000) { await cliche('attente'); dernier = Date.now(); }
  await attendre(2000);
}
journal({ etape: 'modele', secondes: (Date.now() - t0) / 1000 });
await attendre(4000);
const boite = await focus.boundingBox();
for (const look of ['Wire', 'Clay', 'Textured']) {
  await page.getByRole('button', { name: look, exact: true }).click();
  await attendre(1500);
  // un tour lent à la souris : 36 vues
  const cx = boite.x + boite.width / 2, cy = boite.y + boite.height / 2;
  await page.mouse.move(cx, cy); await page.mouse.down();
  for (let i = 0; i < 36; i++) { await page.mouse.move(cx + (i + 1) * 9, cy, { steps: 2 }); await cliche(`tour-${look.toLowerCase()}`); }
  await page.mouse.up();
}
await page.locator('.object-focus').screenshot({ path: join(dossier, 'focus-final.png') });
console.log(JSON.stringify({ secondes: (Date.now() - t0) / 1000, images: n }));
await nav.close();
