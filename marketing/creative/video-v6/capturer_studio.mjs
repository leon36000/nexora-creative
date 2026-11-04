// Film V6 : capture du Mode Studio réel : nouveau projet, import de rushes du film, glisser sur la timeline.
// Usage : node capturer_studio.mjs <dossier> <video1> [video2 …]
import { chromium } from '../../../mode-studio/node_modules/playwright/index.mjs';
import { mkdirSync } from 'node:fs';
import { join } from 'node:path';
const [dossier, ...videos] = process.argv.slice(2);
mkdirSync(dossier, { recursive: true });
let n = 0;
const nav = await chromium.launch({ executablePath: `${process.env.HOME}/.cache/ms-playwright/chromium-1248/chrome-linux-arm64/chrome`, args: ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader'] });
const page = await nav.newPage({ viewport: { width: 1600, height: 900 }, deviceScaleFactor: 2 });
const cliche = async (e) => page.screenshot({ path: join(dossier, `${String(n++).padStart(4, '0')}-${e}.jpg`), type: 'jpeg', quality: 95 });
const attendre = (ms) => new Promise((r) => setTimeout(r, ms));
await page.goto('http://127.0.0.1:37170/mode-studio/', { waitUntil: 'networkidle' });
await attendre(1500);
await page.getByRole('button', { name: /Créer votre premier projet|Nouveau projet/ }).first().click();
await attendre(1500);
await page.getByPlaceholder('Saisissez le nom du projet...').fill('Trois mots');
await attendre(300); await cliche('nouveau');
const creer = page.getByRole('button', { name: /^Créer|Create/ }).last();
if (await creer.isVisible().catch(() => false)) { await creer.click(); }
await attendre(4000); for (let i = 0; i < 6; i++) { await cliche('editeur'); await attendre(300); }
if (!videos.length) { await nav.close(); process.exit(0); }
const inp = page.locator('input[type=file]').first();
await inp.setInputFiles(videos);
await attendre(12000); await cliche('medias');
// glisser chaque média de la bibliothèque sur la timeline
const cartes = page.locator('[draggable=true]');
const nb = await cartes.count();
const piste = page.locator('[data-track-id], .timeline-track, [class*=track]').first();
const pb = await piste.boundingBox().catch(() => null);
for (let i = 0; i < Math.min(nb, videos.length); i++) {
  const c = await cartes.nth(i).boundingBox().catch(() => null);
  if (!c || !pb) break;
  await page.mouse.move(c.x + c.width / 2, c.y + c.height / 2); await page.mouse.down();
  await page.mouse.move(pb.x + 40 + i * 220, pb.y + pb.height / 2, { steps: 12 }); await page.mouse.up();
  await attendre(1500); await cliche('timeline');
}
for (let i = 0; i < 6; i++) { await attendre(500); await cliche('fin'); }
console.log(await page.locator('body').innerText().then((t) => t.slice(0, 1200)));
await nav.close();
