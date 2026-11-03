// Film « Modèles et API » : parcours RÉEL de la page /modeles (français) ou /en/modeles (anglais) du site en ligne, enregistré en
// flux d'images (CDP screencast, 2880×1620) avec le journal horodaté des gestes (positions du curseur, clics, repères).
// Rien n'est simulé ni retouché. Accès : relais local socat 127.0.0.1:18081 → ssh pc5-proxmox nc 192.168.1.121 80 (pc6 ne résout pas
// les noms ts.net), en-tête X-Forwarded-Proto: https.
// Usage : node capturer.mjs <dossier> [fr,en]   → <dossier>/<langue>/frames/NNNNNN.jpg, frames.jsonl, journal.jsonl
import { chromium } from '../../../../../mode-studio/node_modules/playwright/index.mjs';
import { mkdirSync, writeFileSync, appendFileSync } from 'node:fs';
import { join } from 'node:path';

const dossier = process.argv[2];
const BASE = 'http://127.0.0.1:18081';
const VP = { width: 1600, height: 900 };
const L = {
  fr: { chemin: '/modeles', loc: 'fr-CA', parcourir: 'Parcourir le catalogue', copier: 'Copier', appliquer: 'Appliquer', recherche: 'qwen',
        tri: 'Prix d’entrée croissant', api: /^Utiliser l’API$/, bench: /^Benchmarks$/, fiche: 'a[aria-label^="Voir la fiche"]' },
  en: { chemin: '/en/modeles', loc: 'en-CA', parcourir: 'Browse the catalogue', copier: 'Copy', appliquer: 'Apply', recherche: 'qwen',
        tri: 'Input price: low to high', api: /^Use the API$/, bench: /^Benchmarks$/, fiche: 'a[aria-label^="View the page"]' },
};
const nav = await chromium.launch({ executablePath: `${process.env.HOME}/.cache/ms-playwright/chromium-1248/chrome-linux-arm64/chrome` });
const dort = (ms) => new Promise((r) => setTimeout(r, ms));

for (const lg of (process.argv[3] ?? 'fr,en').split(',')) {
  const s = L[lg];
  const rep = join(dossier, lg);
  mkdirSync(join(rep, 'frames'), { recursive: true });
  writeFileSync(join(rep, 'frames.jsonl'), ''); writeFileSync(join(rep, 'journal.jsonl'), '');
  const ctx = await nav.newContext({ viewport: VP, deviceScaleFactor: 2, locale: s.loc, extraHTTPHeaders: { 'X-Forwarded-Proto': 'https' } });
  await ctx.grantPermissions(['clipboard-read', 'clipboard-write'], { origin: BASE }).catch(() => {});
  // l'en-tête collant du site (nom de marque, qui va changer) est masqué ; il garde sa place, rien d'autre n'est modifié
  await ctx.addInitScript(() => { const st = document.createElement('style'); st.textContent = 'header{visibility:hidden!important}'; document.addEventListener('DOMContentLoaded', () => document.head.appendChild(st)); });
  const page = await ctx.newPage();
  const cdp = await ctx.newCDPSession(page);
  let n = 0;
  cdp.on('Page.screencastFrame', async (e) => {
    const k = n++;
    writeFileSync(join(rep, 'frames', `${String(k).padStart(6, '0')}.jpg`), Buffer.from(e.data, 'base64'));
    appendFileSync(join(rep, 'frames.jsonl'), JSON.stringify({ f: k, t: e.metadata.timestamp }) + '\n');
    cdp.send('Page.screencastFrameAck', { sessionId: e.sessionId }).catch(() => {});
  });
  const J = (o) => appendFileSync(join(rep, 'journal.jsonl'), JSON.stringify({ t: Date.now() / 1000, ...o }) + '\n');
  let mx = 800, my = 450;
  const aller = async (x, y, nom, pas = 22) => {  // déplacement lissé de la souris, chaque position est journalisée
    const x0 = mx, y0 = my;
    for (let i = 1; i <= pas; i++) {
      const u = i / pas, e = u < 0.5 ? 2 * u * u : 1 - Math.pow(-2 * u + 2, 2) / 2;
      mx = x0 + (x - x0) * e; my = y0 + (y - y0) * e;
      await page.mouse.move(mx, my);
      J({ pos: nom, x: +(mx / VP.width).toFixed(4), y: +(my / VP.height).toFixed(4) });
      await dort(14);
    }
  };
  const pointer = async (loc, nom, dx = 0.5, dy = 0.5) => {
    const b = await loc.boundingBox();
    await aller(b.x + b.width * dx, b.y + b.height * dy, nom);
  };
  const clic = async (loc, nom, dx = 0.5, dy = 0.5) => {
    await pointer(loc, nom, dx, dy); await dort(120);
    J({ clic: nom }); await loc.click({ position: undefined, force: true, timeout: 5000 }).catch(() => {});
  };
  const defiler = async (y, ms) => {  // défilement lissé réel
    await page.evaluate(([y1, d]) => new Promise((ok) => { const y0 = scrollY, t0 = performance.now();
      const pas = (t) => { const u = Math.min(1, (t - t0) / d), e = u < 0.5 ? 4 * u * u * u : 1 - Math.pow(-2 * u + 2, 3) / 2; scrollTo(0, y0 + (y1 - y0) * e); u < 1 ? requestAnimationFrame(pas) : ok(); };
      requestAnimationFrame(pas); }), [y, ms]);
  };
  const versCatalogue = async () => { await page.evaluate(() => scrollTo(0, document.getElementById('catalogue').getBoundingClientRect().top + scrollY - 0)); };
  const compte = async () => (await page.locator('body').innerText()).match(/\d+ (modèles?|models?) (sur|of) \d+/)?.[0];

  await cdp.send('Page.startScreencast', { format: 'jpeg', quality: 88, maxWidth: 2880, maxHeight: 1620, everyNthFrame: 1 });
  J({ marque: 'debut' });
  await page.goto(BASE + s.chemin, { waitUntil: 'domcontentloaded' });
  await page.waitForLoadState('networkidle'); J({ marque: 'hero' });
  await dort(3200); J({ marque: 'hero_fin' });
  // 1. « Parcourir le catalogue »
  await clic(page.getByText(s.parcourir, { exact: true }).first(), 'parcourir');
  await dort(1500); J({ marque: 'cat' }); J({ compte: await compte() });
  await dort(500);
  // 2. pastille « Code » (navigation côté client : le formulaire garde son ancien état ; on recharge la page, même état affiché,
  // pour que les envois suivants du formulaire gardent la pastille ; le rechargement est coupé au montage : repères c_fin / c_res2)
  const code = page.getByRole('link', { name: /^Code\s*\d+/ }).first();
  await pointer(code, 'code'); await dort(150); J({ clic: 'code', marque: 'c_go' }); await code.click();
  await page.waitForURL(/etiquette=code/); await page.waitForLoadState('networkidle'); await versCatalogue(); await dort(250); J({ marque: 'c_res' }); J({ compte: await compte() });
  await dort(1300);
  J({ marque: 'c_fin' }); await page.reload({ waitUntil: 'networkidle' }); await versCatalogue(); await dort(300); J({ marque: 'c_res2' }); J({ compte: await compte() });
  // 3. recherche : on tape, on valide
  const champ = page.locator('input[name=q]').first();
  await pointer(champ, 'champ'); await champ.click(); J({ clic: 'champ' }); await dort(250);
  J({ marque: 'tape' });
  await page.keyboard.type(s.recherche, { delay: 130 }); await dort(350);
  J({ marque: 'tape_fin' }); J({ clic: 'entree' });
  await page.keyboard.press('Enter');
  await page.waitForURL(/q=qwen/); await page.waitForLoadState('networkidle'); await versCatalogue(); await dort(250); J({ marque: 'q_res' }); J({ compte: await compte() });
  await dort(1300);
  // 4. tri par prix d'entrée croissant
  const tri = page.locator('select[name=tri]').first();
  await pointer(tri, 'tri'); J({ clic: 'tri' }); await dort(200);
  await tri.selectOption({ label: s.tri }); await dort(350);
  const ok = page.getByRole('button', { name: s.appliquer }).first();
  await pointer(ok, 'appliquer'); await dort(120); J({ clic: 'appliquer', marque: 't_go' }); await ok.click();
  await page.waitForURL(/tri=prix-entree/); await page.waitForLoadState('networkidle'); await versCatalogue(); await dort(250); J({ marque: 't_res' }); J({ compte: await compte(), url: page.url() });
  await dort(1500);
  // 5. la fiche du premier modèle
  const carte = page.locator(s.fiche).first();
  J({ premier: await carte.getAttribute('aria-label') });
  await pointer(carte, 'fiche', 0.5, 0.5); await dort(150); J({ clic: 'fiche', marque: 'f_go' }); await carte.click();
  await page.waitForURL(/\/modeles\/nexora\//); await page.waitForLoadState('networkidle'); await dort(350); J({ marque: 'f_res' });
  await dort(2800);
  const h = (re) => page.getByRole('heading', { name: re }).first();
  const posY = async (loc, marge) => (await loc.evaluate((e) => e.getBoundingClientRect().top + scrollY)) - marge;
  J({ marque: 'defile_bench' }); await defiler(await posY(h(s.bench), 70), 1100); J({ marque: 'bench' }); await dort(1700);
  J({ marque: 'defile_api' }); await defiler(await posY(h(s.api), 70), 1200); J({ marque: 'api' }); await dort(1500);
  const cop = page.getByRole('button', { name: s.copier }).first();
  await pointer(cop, 'copier'); await dort(150); J({ clic: 'copier' }); await cop.click(); J({ marque: 'copie' });
  await dort(1600); J({ marque: 'fin' });
  await cdp.send('Page.stopScreencast'); await dort(300);
  console.log(lg, 'images', n);
  await ctx.close();
}
await nav.close();
