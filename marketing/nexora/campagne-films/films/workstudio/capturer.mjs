// Film WorkStudio : capture d'une VRAIE exécution du workflow « Tri du courrier entrant » sur la VM 203 (rien n'est simulé).
// Fenêtre 2240×1260 à 2x (4480×2520) : les blocs restent lisibles une fois recadrés (16:9 et 9:16).
// Accès : relais TLS local (socat 127.0.0.1:8443 → 192.168.1.123:80) + règle d'hôte de Chromium, témoins de session lus dans
// un fichier privé hors dépôt (voir PLAN.md, « Filmer WorkStudio »). Images + journal.jsonl horodaté.
// Usage : node capturer.mjs <dossier> <temoins.json> <id-workflow>
import { chromium } from '../../../../../mode-studio/node_modules/playwright/index.mjs';
import { readFileSync, mkdirSync, appendFileSync } from 'node:fs';
import { join } from 'node:path';

const [dossier, temoins, wf] = process.argv.slice(2);
const ESPACE = '2c6a3931-c0e3-4a3f-b3f8-9bb7f517f45a';
const BASE = 'https://studio.nexora.ai';
mkdirSync(dossier, { recursive: true });
const nav = await chromium.launch({ executablePath: `${process.env.HOME}/.cache/ms-playwright/chromium-1248/chrome-linux-arm64/chrome`,
  args: ['--host-resolver-rules=MAP studio.nexora.ai:443 127.0.0.1:8443'] });
const ctx = await nav.newContext({ ignoreHTTPSErrors: true, viewport: { width: 2240, height: 1260 }, deviceScaleFactor: 2, locale: 'fr-CA' });
await ctx.addCookies(JSON.parse(readFileSync(temoins, 'utf8')));
const page = await ctx.newPage();
const T0 = Date.now();
let n = 0;
const journal = (o) => appendFileSync(join(dossier, 'journal.jsonl'), JSON.stringify({ t: (Date.now() - T0) / 1000, ...o }) + '\n');
const cliche = async (etiquette) => {
  const f = join(dossier, `${String(n++).padStart(4, '0')}-${etiquette}.jpg`);
  await page.screenshot({ path: f, type: 'jpeg', quality: 90 });
  journal({ image: f, etiquette });
};
const attendre = (ms) => new Promise((r) => setTimeout(r, ms));
const rafale = async (etiquette, ms) => { const fin = Date.now() + ms; while (Date.now() < fin) await cliche(etiquette); };
const texte = () => page.locator('body').innerText().catch(() => '');

// 1. l'éditeur, canevas plein (barre latérale repliée, vue ajustée)
await page.goto(`${BASE}/workspace/${ESPACE}/w/${wf}`, { waitUntil: 'networkidle' }).catch(() => {});
await attendre(3000);
await page.getByText('Mode avancé', { exact: true }).click(); await attendre(1500);
await page.getByRole('button', { name: 'Réduire la barre latérale' }).first().click().catch(() => {}); await attendre(800);
await page.getByRole('button', { name: 'Ajuster à la vue' }).click().catch(() => {}); await attendre(1500);
await rafale('repos', 1500);
const go = page.getByRole('button', { name: 'Exécuter', exact: true }).first();
await go.hover(); await rafale('survol', 600);
// 2. exécution : les blocs s'allument un à un jusqu'à la pause de validation
await go.click(); journal({ etape: 'executer' });
const t1 = Date.now();
let url = null;
while (Date.now() - t1 < 120000) {
  await cliche('execution');
  const m = (await texte()).match(/https:\/\/studio\.nexora\.ai\/resume\/[0-9a-f-]+\/[0-9a-f-]+/);
  if (m) { url = m[0]; break; }
}
journal({ etape: 'pause', secondes: (Date.now() - t1) / 1000 });
await rafale('pause', 2500);
// 3. la page de validation : lire le brouillon, choisir « vrai », reprendre
await page.goto(url, { waitUntil: 'networkidle' }).catch(() => {}); await attendre(1500);
await rafale('validation', 2000);
await page.getByText('Sélectionnez vrai ou faux').click(); await attendre(500); await cliche('choix');
await page.getByRole('option', { name: /vrai/i }).first().click().catch(async () => { await page.getByText(/^vrai$/i).first().click(); });
await attendre(400); await rafale('choisi', 800);
const reprendre = page.getByRole('button', { name: /Reprendre/ });
await reprendre.hover(); await rafale('reprendre-survol', 500);
await reprendre.click(); journal({ etape: 'reprise' });
await rafale('reprise', 3000);
// (la suite de l'exécution après « Reprendre » échoue sur cette instance : erreur de validation à la reprise, voir PLAN.md ;
//  le film s'arrête donc sur le clic d'accord et le badge « Reprise en cours », sans montrer d'envoi.)
await page.goto(`${BASE}/workspace/${ESPACE}/w/${wf}`, { waitUntil: 'networkidle' }).catch(() => {}); await attendre(3000);
// 5. étendue : la vue « Étapes » du même workflow, puis des modèles PME réels
await page.getByText('Étapes', { exact: true }).first().click().catch(() => {}); await attendre(1500); await rafale('etapes', 1200);
await page.mouse.wheel(0, 700); await attendre(800); await rafale('etapes-bas', 800);
const r = await page.evaluate(async (e) => (await (await fetch('/api/workflows?workspaceId=' + e)).json()).data, ESPACE);
for (const nom of ['Revue de contrat', 'Extraction d’une facture fournisseur', 'Qualification d’un prospect', 'Rapport de ventes mensuel', 'Réponse à un appel d’offres']) {
  const w = r.find((x) => x.name === nom); if (!w) continue;
  await page.goto(`${BASE}/workspace/${ESPACE}/w/${w.id}`, { waitUntil: 'networkidle' }).catch(() => {}); await attendre(2500);
  await page.getByText('Mode avancé', { exact: true }).click().catch(() => {}); await attendre(1000);
  await page.getByRole('button', { name: 'Ajuster à la vue' }).click().catch(() => {}); await attendre(1200);
  await rafale('modele', 700); journal({ etape: 'modele', nom });
}
await nav.close();
