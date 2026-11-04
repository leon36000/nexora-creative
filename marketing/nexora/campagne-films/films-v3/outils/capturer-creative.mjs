// Film V5 Creative : session RÉELLE du Producteur (VM 202, tunnel 127.0.0.1:13161), rien de simulé.
// Flux d'images CDP (jpeg) pendant les gestes + captures PNG 3840×2160 aux états clés + journal horodaté.
import { chromium } from '/home/pc6/Desktop/Nexora Creative/mode-studio/node_modules/playwright/index.mjs';
import { mkdirSync, writeFileSync, appendFileSync } from 'node:fs';
import { join } from 'node:path';
const D = process.argv[2]; const BASE = 'http://127.0.0.1:13161';
const OBJ = process.argv[3];
mkdirSync(join(D, 'flux'), { recursive: true });
const J = (o) => { appendFileSync(join(D, 'journal.jsonl'), JSON.stringify({ t: Date.now() / 1000, ...o }) + '\n'); console.log(JSON.stringify(o)); };
const nav = await chromium.launch({ executablePath: `${process.env.HOME}/.cache/ms-playwright/chromium-1248/chrome-linux-arm64/chrome` });
const ctx = await nav.newContext({ viewport: { width: 1920, height: 1080 }, deviceScaleFactor: 2, locale: 'fr-CA' });
const p = await ctx.newPage();
const cdp = await ctx.newCDPSession(p);
let n = 0, rec = null;
cdp.on('Page.screencastFrame', async (e) => {
  if (rec) { const k = n++; writeFileSync(join(D, 'flux', `${rec}-${String(k).padStart(5, '0')}.jpg`), Buffer.from(e.data, 'base64'));
    appendFileSync(join(D, 'flux.jsonl'), JSON.stringify({ seq: rec, f: k, t: e.metadata.timestamp }) + '\n'); }
  cdp.send('Page.screencastFrameAck', { sessionId: e.sessionId }).catch(() => {});
});
const film = async (nom) => { rec = nom; n = 0; await cdp.send('Page.startScreencast', { format: 'jpeg', quality: 92, maxWidth: 3840, maxHeight: 2160, everyNthFrame: 1 }); J({ debut: nom }); };
const coupe = async () => { await cdp.send('Page.stopScreencast').catch(() => {}); J({ fin: rec }); rec = null; };
const shot = async (nom) => { await p.screenshot({ path: join(D, nom + '.png') }); J({ capture: nom }); };
const dort = (ms) => new Promise((r) => setTimeout(r, ms));

await p.goto(BASE + '/', { waitUntil: 'networkidle' });
const nouv = p.getByRole('button', { name: 'Nouvelle' });
if (await nouv.isEnabled().catch(() => false)) { await nouv.click(); await dort(800); }
await shot('c01-accueil');
await film('frappe');
const zone = p.getByLabel('Message au Producteur');
await zone.click(); await dort(400);
await zone.pressSequentially(OBJ, { delay: 38 });
await dort(700);
await p.getByRole('button', { name: 'Envoyer' }).click();
J({ geste: 'envoyer' });
await p.locator('[aria-label="Plan proposé"]').waitFor({ timeout: 240000 });
await dort(2500);
await coupe();
await shot('c02-plan');
// deux prises par plan : le juge garde la meilleure
const deux = p.getByRole('button', { name: /2 prises par plan/ });
if (await deux.isEnabled().catch(() => false)) { await film('prises'); await deux.click(); J({ geste: 'deux-prises' }); await dort(4000); await coupe(); }
await shot('c03-devis');
await film('lancer');
await p.getByRole('button', { name: 'Valider et lancer' }).click(); J({ geste: 'valider' });
await dort(6000); await coupe();
await shot('c04-lance');
// suivi : une capture toutes les 20 s jusqu'à « Prêt »
let k = 0; const t0 = Date.now();
while (Date.now() - t0 < 50 * 60000) {
  await dort(20000); k++;
  await shot(`suivi-${String(k).padStart(3, '0')}`);
  const pret = await p.locator('.pr-prod .st-etiq', { hasText: 'Prêt' }).count();
  const echec = await p.locator('.pr-prod .st-etiq', { hasText: 'Échec' }).count();
  if (pret || echec) { J({ etat: pret ? 'pret' : 'echec' }); break; }
}
await dort(3000);
await shot('c05-pret');
const html = await p.locator('.pr-prod').first().innerText().catch(() => '');
writeFileSync(join(D, 'production.txt'), html);
const lien = await p.locator('.pr-variantes a[download]').first().getAttribute('href').catch(() => null);
J({ media: lien });
await film('ouvrir');
await p.getByRole('button', { name: 'Plans et montage' }).first().click().catch(() => {});
await dort(5000); await shot('c06-montage'); await dort(9000); await coupe();
await shot('c07-montage-b');
await p.goto(BASE + '/mode-studio/', { waitUntil: 'networkidle' }).catch(() => {});
await dort(5000); await shot('c08-mode-studio');
await nav.close();
