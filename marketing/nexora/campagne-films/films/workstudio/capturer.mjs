// Film WorkStudio : captures de VRAIES exécutions du workflow « Tri du courrier entrant » (VM 203). Rien n'est simulé.
// Deux langues d'interface (fr-CA, en-CA : l'application change de langue d'après l'en-tête Accept-Language) et deux courriels
// entrants différents par langue : 4 exécutions complètes (exécution → pause de validation → accord humain → reprise → envoi
// vers la boîte de test Mailpit). Fenêtre 2240×1260 à 2x (4480×2520), images + journal.jsonl (horodatage et positions des clics).
// Accès : relais TLS local socat 127.0.0.1:8443 → 192.168.1.123:80 + règle d'hôte de Chromium (origine et témoins `Secure` exacts) ;
// tunnel SSH vers Mailpit (interface 8025) sur 127.0.0.1:18025. Témoins : fichier privé hors dépôt (node connexion.mjs <fichier>).
// Usage : node capturer.mjs <dossier> <temoins.json> <id-workflow-fr>[,<id-workflow-en>]
import { chromium } from '../../../../../mode-studio/node_modules/playwright/index.mjs';
import { readFileSync, mkdirSync, appendFileSync } from 'node:fs';
import { execFileSync } from 'node:child_process';
import { join, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const ICI = dirname(fileURLToPath(import.meta.url));
const [dossier, temoins, ids] = process.argv.slice(2);
const WF = { fr: ids.split(',')[0], en: ids.split(',')[1] };
const ESPACE = '2c6a3931-c0e3-4a3f-b3f8-9bb7f517f45a';
const BASE = 'https://studio.nexora.ai';
const MAILPIT = 'http://127.0.0.1:18025';
const VP = { width: 2240, height: 1260 };
const PETIT = { width: 1300, height: 900 };
const PORTRAIT = { width: 780, height: 1040 };  // mêmes pages, fenêtre étroite : captures propres au film vertical (images_v)  // pages de validation et boîte de test : même cadrage 16:9, texte plus gros dans l'image
mkdirSync(dossier, { recursive: true });
const nav = await chromium.launch({ executablePath: `${process.env.HOME}/.cache/ms-playwright/chromium-1248/chrome-linux-arm64/chrome`,
  args: ['--host-resolver-rules=MAP studio.nexora.ai:443 127.0.0.1:8443'] });
const attendre = (ms) => new Promise((r) => setTimeout(r, ms));
const T0 = Date.now();
const journal = (o) => appendFileSync(join(dossier, 'journal.jsonl'), JSON.stringify({ t: (Date.now() - T0) / 1000, ...o }) + '\n');
const L = {
  fr: { avance: /^Mode avancé$/, replier: /Réduire la barre latérale/, ajuster: /Ajuster à la vue/, exec: /^Exécuter$/, choix: /Sélectionnez vrai ou faux/,
        vrai: /^vrai$/i, reprendre: /Reprendre l/, etapes: /^Étapes$/ },
  en: { avance: /^Advanced mode$/, replier: /Collapse sidebar/, ajuster: /Fit to View/, exec: /^Run$/, choix: /Select true or false/,
        vrai: /^true$/i, reprendre: /Resume Execution/, etapes: /^Steps$/ },
};

for (const lg of (process.env.LANGUES ?? 'fr,en').split(',')) {
  const s = L[lg];
  const ctx = await nav.newContext({ ignoreHTTPSErrors: true, viewport: VP, deviceScaleFactor: 2, locale: lg === 'fr' ? 'fr-CA' : 'en-CA' });
  await ctx.addCookies(JSON.parse(readFileSync(temoins, 'utf8')));
  const page = await ctx.newPage();
  let n = 0, pre = '';
  const cliche = async (et) => {
    const f = join(dossier, `${pre}-${String(n++).padStart(4, '0')}-${et}.jpg`);
    await page.screenshot({ path: f, type: 'jpeg', quality: 86 });
    journal({ image: f, etiquette: `${pre}-${et}` });
  };
  const rafale = async (et, ms) => { const fin = Date.now() + ms; let k = 0; while (Date.now() < fin) { await cliche(et); k++; } return k; };
  const texte = () => page.locator('body').innerText().catch(() => '');
  const pointer = async (loc, nom) => {  // déplace la souris, note la position (fraction de la fenêtre) pour dessiner le curseur
    const b = await loc.boundingBox();
    const x = b.x + b.width / 2, y = b.y + b.height / 2; const vp = page.viewportSize();
    await page.mouse.move(x, y, { steps: 14 });
    journal({ pos: nom, x: +(x / vp.width).toFixed(4), y: +(y / vp.height).toFixed(4) });
  };
  const mettreAJour = async (c) => {  // remet le workflow dans son état de départ avec le courriel n° c
    const etat = execFileSync('python3', [join(ICI, 'workflow.py'), 'json', lg, String(c)], { encoding: 'utf8', maxBuffer: 1 << 24 });
    await page.goto(`${BASE}/workspace/${ESPACE}/w/${WF[lg]}`, { waitUntil: 'domcontentloaded' }).catch(() => {});
    const r = await page.evaluate(async ([id, corps]) => (await fetch(`/api/workflows/${id}/state`, { method: 'PUT', headers: { 'Content-Type': 'application/json' }, body: corps })).status, [WF[lg], etat]);
    if (r !== 200) throw new Error('mise à jour de l\'état : ' + r);
  };
  const viderBoite = () => fetch(`${MAILPIT}/api/v1/messages`, { method: 'DELETE' });
  const nbCourriels = async () => (await (await fetch(`${MAILPIT}/api/v1/messages`)).json()).total;

  for (const c of (process.env.CYCLES ?? '1,2').split(',').map(Number)) {  // CYCLES=0 : seulement l'étendue (étapes, blocs ajoutés)
    pre = `${lg}${c}`; n = 0;
    if (c > 0) {
      await page.setViewportSize(VP);
    await viderBoite();
      await mettreAJour(c);
      // 1. l'éditeur, canevas plein
      await page.goto(`${BASE}/workspace/${ESPACE}/w/${WF[lg]}`, { waitUntil: 'networkidle' }).catch(() => {});
      await attendre(2500);
      await page.getByText(s.avance).click(); await attendre(1200);
      await page.getByRole('button', { name: s.replier }).first().click().catch(() => {}); await attendre(700);
      await page.getByRole('button', { name: s.ajuster }).click().catch(() => {}); await attendre(1500);
      await rafale('repos', 700);
      const go = page.getByRole('button', { name: s.exec }).first();
      await pointer(go, 'executer'); await rafale('survol', 350);
      // 2. exécution réelle : les blocs s'allument un à un jusqu'à la pause de validation
      await go.click(); journal({ etape: 'executer', c: pre });
      const t1 = Date.now();
      let url = null, nExec = 0;
      while (Date.now() - t1 < 90000) {
        await cliche('exec'); nExec++;
        const m = (await texte()).match(/https:\/\/studio\.nexora\.ai\/resume\/[0-9a-f-]+\/[0-9a-f-]+/);
        if (m) { url = m[0]; break; }
      }
      journal({ etape: 'pause', secondes: (Date.now() - t1) / 1000, images: nExec });
      await rafale('pause', 900);
      // 3. la page de validation : lire le brouillon, choisir « vrai », reprendre
      await page.setViewportSize(PETIT);
    await page.goto(url, { waitUntil: 'networkidle' }).catch(() => {}); await attendre(1200);
      await rafale('val', 900);
      const liste = page.getByText(s.choix);
      await pointer(liste, 'liste'); await liste.click(); await attendre(450); await rafale('choix', 500);
      const opt = page.getByText(s.vrai).first();
      await pointer(opt, 'option'); await opt.click(); await attendre(350); await rafale('choisi', 600);
      const rep = page.getByRole('button', { name: s.reprendre });
      await pointer(rep, 'reprendre'); await rafale('survol-reprendre', 500);
      const nAvant = await nbCourriels();
      // fenêtre étroite (film vertical) : on rouvre la liste, on rechoisit « vrai », puis on clique ici ; les images larges de la reprise suivent
      await page.setViewportSize(PORTRAIT); await attendre(700);
      await rafale('pval', 400);
      const liste2 = page.getByText(s.vrai).first();
      await pointer(liste2, 'pliste'); await liste2.click(); await attendre(450); await rafale('pchoix', 500);
      const opt2 = page.getByText(s.vrai).last();
      await pointer(opt2, 'poption'); await opt2.click(); await attendre(350); await rafale('pchoisi', 500);
      await pointer(rep, 'preprendre'); await rafale('psurvol', 400);
      await rep.click(); journal({ etape: 'reprise', c: pre });
      await rafale('preprise', 500);
      await page.setViewportSize(PETIT);
      await rafale('reprise', 1200);
      // 4. attendre le courriel réel dans la boîte de test (jusqu'à 60 s)
      const t2 = Date.now();
      while (Date.now() - t2 < 60000 && (await nbCourriels()) <= nAvant) await attendre(300);
      journal({ etape: 'courriel-recu', secondes: (Date.now() - t2) / 1000 });
      await attendre(1500);
      // 5. les journaux d'exécution : la ligne « Réussi », puis le détail
      await page.setViewportSize(VP);
    await page.goto(`${BASE}/workspace/${ESPACE}/logs`, { waitUntil: 'networkidle' }).catch(() => {}); await attendre(2500);
      await rafale('jrn', 500);
      const ligne = page.locator('tbody tr, [role=row]').nth(1);
      await pointer(ligne, 'ligne'); await ligne.click(); await attendre(1800); await rafale('jrnd', 600);
      const trace = page.getByText(/^Trace$/).first();
      await pointer(trace, 'trace'); await trace.click().catch(() => {}); await attendre(1500); await rafale('trace', 600);
      // 6. la boîte de test : le courriel est arrivé
      await page.setViewportSize(PETIT);
    await page.goto(MAILPIT + '/', { waitUntil: 'networkidle' }).catch(() => {}); await attendre(1500);
      await rafale('mp', 500);
      const msg = page.locator('.message, a.list-group-item').first();
      await pointer(msg, 'message'); await msg.click(); await attendre(1500); await rafale('mpm', 600);
      await page.setViewportSize(PORTRAIT); await attendre(800); await rafale('vmpm', 600);
    }
    if (c === 2 || c === 0) {
      // 7. l'étendue (une seule fois par langue) : la vue « Étapes », puis des blocs ajoutés à la main (glisser-déposer réel)
      await page.setViewportSize(VP); await mettreAJour(1);
      await page.goto(`${BASE}/workspace/${ESPACE}/w/${WF[lg]}`, { waitUntil: 'networkidle' }).catch(() => {}); await attendre(2500);
      await page.getByText(s.avance).click().catch(() => {}); await attendre(1000);
      pre = `${lg}x`; n = 0;
      await page.getByText(/^(Barre d.outils|Toolbar)$/).first().click().catch(() => {});
      await page.getByText(s.etapes).first().click().catch(() => {}); await attendre(1500); await rafale('etapes', 1000);
      await page.mouse.wheel(0, 500); await attendre(700); await rafale('etapes-bas', 700);
      await page.getByText(s.avance).click().catch(() => {}); await attendre(1200);
      await page.getByRole('button', { name: s.replier }).first().click().catch(() => {}); await attendre(700);
      await page.getByRole('button', { name: s.ajuster }).click().catch(() => {}); await attendre(1500);
      await rafale('blocs-repos', 500);
      for (const [etiq, x, y] of [['Agent', 760, 820], ['Fonction', 1280, 820]]) {
        const nom = lg === 'en' && etiq === 'Fonction' ? 'Function' : etiq;
        await page.getByText(/^(Barre d.outils|Toolbar)$/).first().click().catch(() => {}); await attendre(400);
        const tuile = page.getByText(nom, { exact: true }).last(); await tuile.scrollIntoViewIfNeeded().catch(() => {}); const b = await tuile.boundingBox();
        await page.mouse.move(b.x + 20, b.y + 8); await page.mouse.down();
        await page.mouse.move(x, y, { steps: 22 }); await attendre(250); await page.mouse.up();
        journal({ pos: 'bloc-' + etiq, x: +(x / VP.width).toFixed(4), y: +(y / VP.height).toFixed(4) });
        await attendre(400); await rafale('blocs-' + etiq, 400);
        await page.getByRole('button', { name: s.ajuster }).click().catch(() => {}); await attendre(1000); await rafale('blocs-' + etiq + '-vue', 500);
      }
      await mettreAJour(1);  // rend le workflow à son état de départ
    }
    console.log(pre, 'ok');
  }
  await ctx.close();
}
await nav.close();
