// Film « Modèles et API » : captures RÉELLES de la page /modeles du site en ligne (rien n'est retouché).
// Accès : relais local vers la VM du site par le nœud Proxmox (socat TCP-LISTEN:18081 → ssh pc5-proxmox nc 192.168.1.121 80),
// en-tête X-Forwarded-Proto: https ; pc6 ne résout pas les noms ts.net. Fenêtre 1600×900 à 2x (3200×1800).
// Écrit <dossier>/NNNN-<étiquette>.jpg et rects.json (rectangles des éléments, fractions de la capture : pour les cadrages du brief).
// Usage : node capturer.mjs <dossier>
import { chromium } from '../../../../../mode-studio/node_modules/playwright/index.mjs';
import { mkdirSync, writeFileSync } from 'node:fs';
import { join } from 'node:path';

const dossier = process.argv[2];
mkdirSync(dossier, { recursive: true });
const BASE = 'http://127.0.0.1:18081';
const nav = await chromium.launch({ executablePath: `${process.env.HOME}/.cache/ms-playwright/chromium-1248/chrome-linux-arm64/chrome` });
const ctx = await nav.newContext({ viewport: { width: 1600, height: 900 }, deviceScaleFactor: 2, locale: 'fr-CA',
  extraHTTPHeaders: { 'X-Forwarded-Proto': 'https' } });
const page = await ctx.newPage();
let n = 0;
const cliche = async (et) => page.screenshot({ path: join(dossier, `${String(n++).padStart(4, '0')}-${et}.jpg`), type: 'jpeg', quality: 92 });
const rect = (loc) => loc.evaluate((e) => { const r = e.getBoundingClientRect(); return [r.x / innerWidth, r.y / innerHeight, r.width / innerWidth, r.height / innerHeight]; });
const rects = {};
await page.goto(`${BASE}/modeles`, { waitUntil: 'networkidle' });
await page.waitForTimeout(2500);
await cliche('hero');
// une seule capture pleine page (l'en-tête collant n'apparaît qu'en haut) ; les rectangles sont en fractions du document
await page.evaluate(() => window.scrollTo(0, document.body.scrollHeight)); await page.waitForTimeout(800);
await page.evaluate(() => window.scrollTo(0, 0)); await page.waitForTimeout(1500);
const doc = await page.evaluate(() => [document.documentElement.scrollWidth, document.documentElement.scrollHeight]);
const rd = (loc) => loc.evaluate((e) => { const r = e.getBoundingClientRect(); const W = document.documentElement.scrollWidth, H = document.documentElement.scrollHeight;
  return [r.x / W, (r.y + scrollY) / H, r.width / W, r.height / H]; });
rects.document = doc;
rects.titre_hero = await rd(page.locator('h1').first());
rects.prix = await rd(page.getByText('Prix en dollars canadiens', { exact: true }).first());
rects.hebergement = await rd(page.getByText('Hébergement affiché', { exact: true }).first());
rects.catalogue = await rd(page.getByText('Les modèles, leurs prix et leurs benchmarks.'));
rects.filtres = await rd(page.getByText('Filtrez par catégorie', { exact: false }).first());
rects.statut = await rd(page.getByText('Le catalogue est en cours de préparation', { exact: false }).first());
await page.screenshot({ path: join(dossier, '0000-page.jpg'), type: 'jpeg', quality: 92, fullPage: true });
writeFileSync(join(dossier, 'rects.json'), JSON.stringify(rects, null, 1));
await nav.close();
