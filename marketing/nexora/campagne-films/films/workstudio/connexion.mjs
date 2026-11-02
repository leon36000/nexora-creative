// Ouvre UNE session WorkStudio (le mot de passe est lu sur la VM, jamais affiché) et écrit les témoins dans un fichier privé hors dépôt.
// Usage : node connexion.mjs <temoins.json>   (connexion limitée à quelques essais par minute : réutiliser le fichier)
import { chromium } from '../../../../../mode-studio/node_modules/playwright/index.mjs';
import { execFileSync } from 'node:child_process';
import { writeFileSync, chmodSync } from 'node:fs';
const mdp = execFileSync('ssh', ['nexora-workstudio', 'sudo cat /srv/nexora/secrets-workstudio/compte_test_admin_mdp'], { encoding: 'utf8' }).trim();
const nav = await chromium.launch({ executablePath: `${process.env.HOME}/.cache/ms-playwright/chromium-1248/chrome-linux-arm64/chrome`,
  args: ['--host-resolver-rules=MAP studio.nexora.ai:443 127.0.0.1:8443'] });
const ctx = await nav.newContext({ ignoreHTTPSErrors: true });
const page = await ctx.newPage();
await page.goto('https://studio.nexora.ai/login', { waitUntil: 'domcontentloaded' }).catch(() => {});
const r = await page.evaluate(async ([e, p]) => {
  const x = await fetch('/api/auth/sign-in/email', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ email: e, password: p }) });
  return x.status;
}, ['essai-admin@nexora.test', mdp]);
console.log('statut connexion', r);
if (r === 200) { writeFileSync(process.argv[2], JSON.stringify(await ctx.cookies())); chmodSync(process.argv[2], 0o600); }
await nav.close();
