// Promo V4 : capture d'une VRAIE session du Producteur IA (serveur de développement du studio, interface sur 37160).
// Rien n'est simulé : la phrase est tapée dans l'interface, le Producteur (LLM) répond, le devis vient du code, le tournage
// part sur les vrais moteurs (H3 « Qualité cinéma », 2 prises jugées). Les images servent au montage (recadrages en code).
//
// Usage : node capturer.mjs <dossier> "<phrase>"   (Playwright de mode-studio/node_modules)
//   Phase 1 : saisie (une image toutes les 2 touches), réponse, plan, réglages (Paysage, 2 prises, Qualité cinéma).
//   Puis attend le fichier <dossier>/GO (porte : l'animatique doit avoir été validée) avant de cliquer « Valider et lancer ».
//   Phase 2 : suivi du tournage (une image à chaque changement, au moins toutes les 20 s), puis « Plans et montage ».
import { chromium } from '../../../mode-studio/node_modules/playwright/index.mjs';
import { mkdirSync, existsSync, writeFileSync, appendFileSync } from 'node:fs';
import { join } from 'node:path';

const [dossier, phrase] = process.argv.slice(2);
const URL = process.env.UI ?? 'http://127.0.0.1:37160/';
mkdirSync(dossier, { recursive: true });
const journal = (o) => appendFileSync(join(dossier, 'journal.jsonl'), JSON.stringify({ t: Date.now() / 1000, ...o }) + '\n');
let n = 0;
const navigateur = await chromium.launch({ executablePath: process.env.CHROME ?? `${process.env.HOME}/.cache/ms-playwright/chromium-1248/chrome-linux-arm64/chrome` });
const page = await navigateur.newPage({ viewport: { width: 1600, height: 900 }, deviceScaleFactor: 2 });
const cliche = async (etiquette) => {
  const f = join(dossier, `${String(n++).padStart(4, '0')}-${etiquette}.jpg`);
  await page.screenshot({ path: f, type: 'jpeg', quality: 92 });
  journal({ image: f, etiquette });
};
const attendre = (ms) => new Promise((r) => setTimeout(r, ms));

await page.goto(URL, { waitUntil: 'networkidle' });
const nouvelle = page.getByRole('button', { name: 'Nouvelle', exact: true });
if (await nouvelle.isEnabled().catch(() => false)) { await nouvelle.click(); await attendre(1500); }
const champ = page.getByLabel('Message au Producteur');
await champ.click();
for (let i = 0; i < 6; i++) { await cliche('vide'); await attendre(250); }
for (let i = 0; i < phrase.length; i++) {
  await champ.press(phrase[i] === ' ' ? 'Space' : phrase[i]).catch(() => champ.type(phrase[i]));
  if (i % 2 === 1 || i === phrase.length - 1) await cliche('saisie');
}
await attendre(400); await cliche('saisie-fin');
await page.getByRole('button', { name: 'Envoyer', exact: true }).click();
const t0 = Date.now();
const go = page.getByRole('button', { name: 'Valider et lancer' });
while (!(await go.isVisible().catch(() => false)) && Date.now() - t0 < 180000) { await cliche('reflexion'); await attendre(300); }
for (let i = 0; i < 4; i++) { await cliche('plan'); await attendre(300); }
journal({ etape: 'plan', secondes: (Date.now() - t0) / 1000, texte: await page.locator('.st-galerie').innerText().catch(() => '') });
for (const [nom, etiq] of [['Paysage', 'format'], ['2 prises par plan', 'prises'], ['Qualité cinéma', 'cinema']]) {
  const b = page.getByRole('button', { name: new RegExp(nom) }).first();
  if (await b.isEnabled().catch(() => false)) {
    if (nom === 'Paysage' || (await b.getAttribute('aria-pressed')) !== 'true') { await b.hover(); await cliche(etiq + '-survol'); await b.click(); }
    await attendre(1200); await cliche(etiq);
  } else journal({ etape: 'bouton-indisponible', nom });
}
journal({ etape: 'devis', texte: await page.locator('.st-galerie').innerText().catch(() => '') });
await go.hover(); await cliche('valider-survol');
writeFileSync(join(dossier, 'PHASE1-OK'), '');
console.log('phase 1 terminée ; en attente de', join(dossier, 'GO'));
while (!existsSync(join(dossier, 'GO'))) await attendre(5000);

await go.click();
const t1 = Date.now();
let avant = '', dernier = 0;
const fini = page.getByRole('button', { name: 'Télécharger' });
while (Date.now() - t1 < 90 * 60000) {
  const txt = await page.locator('.st-galerie').innerText().catch(() => '');
  if (txt !== avant || Date.now() - dernier > 20000) { await cliche('tournage'); avant = txt; dernier = Date.now(); journal({ etape: 'tournage', texte: txt }); }
  if (await fini.isVisible().catch(() => false)) break;
  await attendre(3000);
}
await attendre(2000); await cliche('pret');
journal({ etape: 'pret', secondes: (Date.now() - t1) / 1000, texte: await page.locator('.st-galerie').innerText().catch(() => '') });
const plans = page.getByRole('button', { name: 'Plans et montage' }).first();
if (await plans.isVisible().catch(() => false)) { await plans.click(); await attendre(4000); await cliche('plans-montage'); await page.mouse.wheel(0, 600); await attendre(1500); await cliche('plans-montage-2'); }
writeFileSync(join(dossier, 'PHASE2-OK'), '');
await navigateur.close();
