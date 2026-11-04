// Captures de la vague 2 (mode Marketing) : node scripts/marketing-captures.mjs <urlUI> <sortie>
import { chromium } from 'playwright-core';
const [url = 'http://localhost:3260', sortie = '../marketing/creative/captures-v3'] = process.argv.slice(2);
const b = await chromium.launch();
const shot = (p, n, o = {}) => p.screenshot({ path: `${sortie}/vague2-${n}.jpg`, type: 'jpeg', quality: 82, ...o });
for (const [nom, w, h] of [['bureau', 1360, 900], ['mobile-375', 375, 812]]) {
  const ctx = await b.newContext({ viewport: { width: w, height: h }, deviceScaleFactor: nom === 'bureau' ? 1 : 2 });
  const p = await ctx.newPage();
  await p.goto(`${url}/marketing?onglet=marque`); await p.waitForSelector('.mk-grid');
  await shot(p, `${nom}-1-marque`, { fullPage: true });
  await p.goto(`${url}/marketing?onglet=creer`); await p.waitForSelector('.mk-pieces');
  await p.fill('textarea', 'carte d’affaires pour une plombière à Sherbrooke, ton chaleureux');
  await p.click('text=Proposer 3 compositions');
  await p.waitForSelector('.mk-prop', { timeout: 90000 });
  await p.waitForFunction(() => document.querySelectorAll('.mk-thumb img').length >= 3, null, { timeout: 30000 });
  await shot(p, `${nom}-2-propositions`, { fullPage: true });
  await p.locator('.mk-prop').nth(0).click(); await p.waitForSelector('.mk-view img');
  await p.waitForTimeout(800);
  await shot(p, `${nom}-3-edition`, { fullPage: true });
  if (nom === 'bureau') {
    await p.click('.mk-faces button >> nth=1'); await p.waitForTimeout(900); await shot(p, `${nom}-4-verso`, { fullPage: true });
    await p.click('text=Panneau expert'); await p.click('text=Version sombre'); await p.waitForTimeout(1200); await shot(p, `${nom}-5-expert-sombre`, { fullPage: true });
  } else {
    const dbl = await p.evaluate(() => document.documentElement.scrollWidth - window.innerWidth);
    console.log('débordement horizontal à 375 px :', dbl, 'px');
  }
  await ctx.close();
}
await b.close();
