// Film V6 : capture d'un VRAI « Booster ma phrase » dans le Creative de la branche (UI 37170). Rien n'est simulé :
// les mots sont tapés dans le champ, le LLM de production réécrit, la version boostée est lue dans la page.
// La version boostée sert ensuite, telle quelle, d'intention au rendu (images clés puis vidéo) : le plan du film est bien
// celui qu'aurait obtenu le client.
//
// Usage : node capturer_boost.mjs <dossier> "<mots tapés>" [video|image]   (SANS_BOOST=1 : saisie seule)
// Sortie : <dossier>/NNNN-<etape>.jpg (3200×1800), <dossier>/boost.json {mots, boost, secondes}, journal.jsonl
import { chromium } from '../../../mode-studio/node_modules/playwright/index.mjs';
import { mkdirSync, writeFileSync, appendFileSync } from 'node:fs';
import { join } from 'node:path';

const [dossier, mots, mode = 'video'] = process.argv.slice(2);
const URL = process.env.UI ?? 'http://127.0.0.1:37170/';
mkdirSync(dossier, { recursive: true });
const journal = (o) => appendFileSync(join(dossier, 'journal.jsonl'), JSON.stringify({ t: Date.now() / 1000, ...o }) + '\n');
let n = 0;
const nav = await chromium.launch({ executablePath: process.env.CHROME ?? `${process.env.HOME}/.cache/ms-playwright/chromium-1248/chrome-linux-arm64/chrome` });
const page = await nav.newPage({ viewport: { width: 1600, height: 900 }, deviceScaleFactor: 2 });
const cliche = async (etiquette) => {
  const f = join(dossier, `${String(n++).padStart(4, '0')}-${etiquette}.jpg`);
  await page.screenshot({ path: f, type: 'jpeg', quality: 95 });
  journal({ image: f, etiquette });
};
const attendre = (ms) => new Promise((r) => setTimeout(r, ms));

await page.goto(URL, { waitUntil: 'networkidle' });
await page.getByRole('tab', { name: mode === 'image' ? 'Image' : 'Vidéo' }).click();
await attendre(800);
const champ = page.getByLabel('Description');
await champ.click();
for (let i = 0; i < 4; i++) { await cliche('vide'); await attendre(120); }
for (const c of mots) {
  await champ.press(c === ' ' ? 'Space' : c).catch(() => champ.type(c));
  await cliche('saisie');
}
for (let i = 0; i < 4; i++) { await cliche('saisie-fin'); await attendre(120); }
if (process.env.SANS_BOOST) { console.log(JSON.stringify({ mots })); await nav.close(); process.exit(0); }
const bouton = page.getByRole('button', { name: /Booster ma phrase/ });
await bouton.hover(); await cliche('survol');
const t0 = Date.now();
await bouton.click();
const sugg = page.locator('.st-suggestion');
while (!(await sugg.isVisible().catch(() => false)) && Date.now() - t0 < 180000) { await cliche('reflexion'); await attendre(150); }
const secondes = (Date.now() - t0) / 1000;
for (let i = 0; i < 8; i++) { await cliche('boost'); await attendre(150); }
const boost = (await sugg.locator('p').innerText()).trim();
writeFileSync(join(dossier, 'boost.json'), JSON.stringify({ mots, mode, boost, secondes }, null, 1));
const utiliser = page.getByRole('button', { name: 'Utiliser cette version' });
await utiliser.hover(); await cliche('utiliser-survol');
await utiliser.click(); await attendre(400);
for (let i = 0; i < 4; i++) { await cliche('utilisee'); await attendre(150); }
journal({ etape: 'fin', secondes, boost });
console.log(JSON.stringify({ mots, boost, secondes }));
await nav.close();
