import assert from 'node:assert/strict';
import { mkdtemp, readFile } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import react from '@vitejs/plugin-react';
import { chromium } from 'playwright-core';
import { createServer } from 'vite';

const appRoot = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const tempRoot = await mkdtemp(join(tmpdir(), 'nexora-mesh-switch-race-'));
console.log(`Dossier du test : ${tempRoot}`);
let server, context, resolveA, resolveB, resolveA2, aStarted2, resolveFailure, failureStarted, aCount = 0;
let aStarted;
const judgeStarted = new Promise((resolvePromise) => { aStarted = resolvePromise; });
const waitA = new Promise((resolvePromise) => { resolveA = resolvePromise; });
const waitB = new Promise((resolvePromise) => { resolveB = resolvePromise; });
const waitA2 = new Promise((resolvePromise) => { resolveA2 = resolvePromise; });
const judgeStarted2 = new Promise((resolvePromise) => { aStarted2 = resolvePromise; });
const failureWait = new Promise((resolvePromise) => { resolveFailure = resolvePromise; });
const failureRequestStarted = new Promise((resolvePromise) => { failureStarted = resolvePromise; });
try {
  const fixture = {
    name: 'fixture-mesh-switch',
    resolveId(id) { if (id === 'virtual:mesh-switch') return '\0mesh-switch'; },
    async load(id) {
      if (process.env.NEXORA_MESH_BASELINE && id.split('?')[0] === resolve(appRoot, 'src/pages/ReliefOutils.tsx')) {
        return readFile(process.env.NEXORA_MESH_BASELINE, 'utf8');
      }
      if (id !== '\0mesh-switch') return;
      return `import React, {useState} from 'react';
import {createRoot} from 'react-dom/client';
import ReliefOutils from '/src/pages/ReliefOutils.tsx';
import {getState} from '/src/store.ts';
window.__meshToast = () => getState().toast;
function Fixture() {
  const [id, setId] = useState(101);
  return React.createElement(React.Fragment, null,
    React.createElement('button', {onClick: () => setId(101)}, 'Modèle A'),
    React.createElement('button', {onClick: () => setId(202)}, 'Modèle B'),
    React.createElement(ReliefOutils, {take: {id, status:'done'}}));
}
createRoot(document.getElementById('root')).render(React.createElement(React.StrictMode, null, React.createElement(Fixture)));`;
    },
    configureServer(vite) {
      vite.middlewares.use('/__mesh-switch', (_req, res) => {
        res.setHeader('Content-Type', 'text/html');
        res.end('<!doctype html><html><body><div id="root"></div><script type="module" src="/@id/__x00__mesh-switch"></script></body></html>');
      });
    },
  };
  server = await createServer({
    configFile: false, root: appRoot, envDir: false, envFile: false,
    cacheDir: join(tempRoot, 'vite-cache'), plugins: [react(), fixture], logLevel: 'error',
    optimizeDeps: { noDiscovery: true, include: ['react', 'react-dom', 'react-dom/client'] },
    server: { host: '127.0.0.1', port: 0, strictPort: false, hmr: false, open: false },
  });
  await server.listen();
  const address = server.httpServer.address();
  assert.ok(address && typeof address === 'object');
  const origin = `http://127.0.0.1:${address.port}`;
  const executablePath = process.env.NEXORA_TEST_CHROMIUM;
  assert.ok(executablePath, 'NEXORA_TEST_CHROMIUM requis');
  context = await chromium.launchPersistentContext(join(tempRoot, 'profil'), {
    executablePath, headless: true,
    args: ['--no-sandbox', '--disable-background-networking', '--disable-sync', '--no-first-run', '--host-resolver-rules=MAP * ~NOTFOUND, EXCLUDE 127.0.0.1'],
  });
  const external = [];
  await context.route('**/*', async (route) => {
    const u = new URL(route.request().url());
    if (u.origin !== origin) { external.push(u.origin); return route.abort(); }
    if (!u.pathname.startsWith('/api/')) return route.continue();
    const json = (body) => route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(body) });
    if (/\/rapport$/.test(u.pathname)) return json({ rapport: null, decime: null, juge: null });
    if (u.pathname === '/api/nexora/relief/101/cartes') return json({ cartes: [{ nom: 'alpha-A' }] });
    if (u.pathname === '/api/nexora/relief/202/cartes') { await waitB; return json({ cartes: [{ nom: 'beta-B' }] }); }
    if (u.pathname === '/api/nexora/relief/101/juger') {
      aCount++;
      if (aCount === 1) { aStarted(); await waitA; return json({ note: 2, raison: 'jugement A', defauts: [] }); }
      if (aCount === 2) { aStarted2(); await waitA2; return json({ note: 1, raison: 'ancien retour A', defauts: [] }); }
      if (aCount === 4) { failureStarted(); await failureWait; return route.fulfill({status: 500, contentType: 'application/json', body: JSON.stringify({error:'Erreur de A'})}); }
      return json({ note: 9, raison: 'nouveau jugement A', defauts: [] });
    }
    if (u.pathname === '/api/nexora/relief/202/juger') return json({ note: 8, raison: 'jugement B', defauts: [] });
    if (u.pathname.includes('/cartes/')) return route.fulfill({status: 404, body: ''});
    return json({});
  });
  context.setDefaultTimeout(8000);
  const page = await context.newPage();
  await page.goto(`${origin}/__mesh-switch`, { waitUntil: 'domcontentloaded' });
  await page.getByText('alpha-A', { exact: true }).waitFor();
  await page.getByRole('button', { name: 'STL', exact: true }).click();
  await page.getByRole('button', { name: '20 k', exact: true }).click();
  await page.getByRole('button', { name: 'Faire juger sur quatre côtés' }).click();
  await judgeStarted;
  await page.getByRole('button', { name: 'Modèle B' }).click();
  await page.screenshot({ path: join(tempRoot, 'apres-bascule-B.png') });
  assert.equal(await page.getByText('alpha-A', { exact: true }).count(), 0, 'Les cartes du modèle A doivent disparaître immédiatement sur B');
  assert.equal(await page.getByRole('button', { name: 'STL', exact: true }).getAttribute('class'), 'on', 'Le format choisi reste sélectionné');
  assert.equal(await page.getByRole('button', { name: '20 k', exact: true }).getAttribute('class'), 'on', 'Le nombre de faces choisi reste sélectionné');
  assert.equal(await page.getByRole('button', { name: 'Faire juger sur quatre côtés' }).isEnabled(), true, 'B ne doit pas hériter du jugement en cours de A');
  resolveA();
  await page.waitForTimeout(250);
  assert.equal(await page.getByText('jugement A', { exact: true }).count(), 0, 'La réponse tardive de A ne doit pas être affichée pour B');
  resolveB();
  await page.getByText('beta-B', { exact: true }).waitFor();
  await page.getByRole('button', { name: 'Faire juger sur quatre côtés' }).click();
  await page.getByText('jugement B', { exact: true }).waitFor();
  // Une ancienne demande A ne doit pas écraser une nouvelle demande après A → B → A.
  await page.getByRole('button', { name: 'Modèle A' }).click();
  await page.getByRole('button', { name: 'Faire juger sur quatre côtés' }).click();
  await judgeStarted2;
  await page.getByRole('button', { name: 'Modèle B' }).click();
  await page.getByRole('button', { name: 'Modèle A' }).click();
  await page.getByRole('button', { name: 'Faire juger sur quatre côtés' }).click();
  await page.getByText('nouveau jugement A', { exact: true }).waitFor();
  resolveA2();
  await page.waitForTimeout(250);
  assert.equal(await page.getByText('ancien retour A', { exact: true }).count(), 0, 'Un ancien jugement de A ne doit pas écraser un nouveau après retour sur A');
  assert.equal(await page.getByText('nouveau jugement A', { exact: true }).count(), 1);
  // Une erreur d'une fiche fermée ne doit pas déclencher de toast sur une autre.
  await page.getByRole('button', { name: 'Modèle B' }).click();
  await page.getByRole('button', { name: 'Modèle A' }).click();
  await page.getByRole('button', { name: 'Faire juger sur quatre côtés' }).click();
  await failureRequestStarted;
  await page.getByRole('button', { name: 'Modèle B' }).click();
  resolveFailure();
  await page.waitForTimeout(250);
  assert.equal(await page.evaluate(() => window.__meshToast()), null, 'Une erreur tardive de A ne doit pas afficher de toast sur B');
  assert.deepEqual(external, [], 'aucune requête hors loopback');
  console.log(`Mesh : cartes et jugement restent liés au modèle actif ; données et profil du test conservés sous ${tempRoot}`);
} finally {
  resolveA?.(); resolveB?.(); resolveA2?.(); resolveFailure?.();
  await context?.close();
  await server?.close();
}
