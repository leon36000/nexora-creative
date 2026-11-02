// Appel d'API interne de WorkStudio depuis le navigateur connecté (outil de préparation du film). Usage : node api.mjs <temoins> <script.js>
import { chromium } from '../../../../../mode-studio/node_modules/playwright/index.mjs';
import { readFileSync } from 'node:fs';
const [temoins, script] = process.argv.slice(2);
const nav = await chromium.launch({ executablePath: `${process.env.HOME}/.cache/ms-playwright/chromium-1248/chrome-linux-arm64/chrome`,
  args: ['--host-resolver-rules=MAP studio.nexora.ai:443 127.0.0.1:8443'] });
const ctx = await nav.newContext({ ignoreHTTPSErrors: true });
await ctx.addCookies(JSON.parse(readFileSync(temoins, 'utf8')));
const page = await ctx.newPage();
await page.goto('https://studio.nexora.ai/api/auth/get-session', { waitUntil: 'domcontentloaded' });
console.log(JSON.stringify(await page.evaluate(new Function(`return (async () => { ${readFileSync(script, 'utf8')} })()`)), null, 1));
await nav.close();
