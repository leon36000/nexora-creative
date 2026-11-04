// Film V6 : captures réelles des autres modes de Creative (Marketing, Bibliothèque, Mode Studio, musique).
// Usage : node capturer_pages.mjs <dossier> marketing "<phrase>" | bibliotheque | studio | page <chemin> [defilement]
import { chromium } from '../../../mode-studio/node_modules/playwright/index.mjs';
import { mkdirSync, appendFileSync } from 'node:fs';
import { join } from 'node:path';

const [dossier, quoi, arg, arg2] = process.argv.slice(2);
const BASE = process.env.UI ?? 'http://127.0.0.1:37170';
mkdirSync(dossier, { recursive: true });
const journal = (o) => appendFileSync(join(dossier, 'journal.jsonl'), JSON.stringify({ t: Date.now() / 1000, ...o }) + '\n');
let n = 0;
const nav = await chromium.launch({
  executablePath: process.env.CHROME ?? `${process.env.HOME}/.cache/ms-playwright/chromium-1248/chrome-linux-arm64/chrome`,
  args: ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--autoplay-policy=no-user-gesture-required'],
});
const page = await nav.newPage({ viewport: { width: 1600, height: 900 }, deviceScaleFactor: 2 });
const cliche = async (etiquette) => {
  const f = join(dossier, `${String(n++).padStart(4, '0')}-${etiquette}.jpg`);
  await page.screenshot({ path: f, type: 'jpeg', quality: 95 });
  journal({ image: f, etiquette });
};
const attendre = (ms) => new Promise((r) => setTimeout(r, ms));

if (quoi === 'marketing') {
  await page.goto(BASE + '/marketing?onglet=creer', { waitUntil: 'networkidle' });
  await attendre(1500); await cliche('page');
  if (await page.getByText('Commence par renseigner ta marque').isVisible().catch(() => false)) {
    // kit de marque d'essai (poste de développement) : un studio de cinéma fictif
    await page.goto(BASE + '/marketing?onglet=marque', { waitUntil: 'networkidle' }); await attendre(1000);
    await page.getByLabel('Nom de la marque').fill(arg2 || 'Studio Braise');
    await cliche('marque');
    await page.getByRole('button', { name: 'Enregistrer ma marque' }).click(); await attendre(2500);
    await page.goto(BASE + '/marketing?onglet=creer', { waitUntil: 'networkidle' }); await attendre(1500); await cliche('page');
  }
  const affiche = page.getByRole('radio', { name: /Affiche/ });
  if (await affiche.isVisible().catch(() => false)) { await affiche.click(); await attendre(500); }
  const champ = page.locator('textarea').first();
  await champ.click();
  for (const c of arg) { await champ.press(c === ' ' ? 'Space' : c).catch(() => champ.type(c)); await cliche('saisie'); }
  await page.getByRole('button', { name: /Proposer 3 compositions/ }).click();
  const t0 = Date.now();
  while (!(await page.locator('.mk-prop').first().isVisible().catch(() => false)) && Date.now() - t0 < 600000) { await cliche('attente'); await attendre(2000); }
  for (let i = 0; i < 6; i++) { await attendre(500); await cliche('propositions'); }
  await page.locator('.mk-prop').first().click(); await attendre(3000);
  for (let i = 0; i < 6; i++) { await attendre(500); await cliche('retouche'); }
} else if (quoi === 'bibliotheque') {
  await page.goto(BASE + '/library', { waitUntil: 'networkidle' });
  await attendre(4000);
  for (let i = 0; i < 24; i++) { await cliche('mur'); await page.mouse.wheel(0, 140); await attendre(250); }
} else if (quoi === 'page') {
  await page.goto(BASE + arg, { waitUntil: 'networkidle' });
  await attendre(5000);
  for (let i = 0; i < 12; i++) { await cliche('page'); if (arg2) await page.mouse.wheel(0, Number(arg2)); await attendre(400); }
}
console.log(JSON.stringify({ images: n }));
await nav.close();
