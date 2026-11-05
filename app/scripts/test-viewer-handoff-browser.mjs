import assert from 'node:assert/strict';
import { mkdir, rm } from 'node:fs/promises';
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import react from '@vitejs/plugin-react';
import { chromium } from 'playwright-core';
import { createServer } from 'vite';

const appRoot = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const tempRoot = resolve(appRoot, '..', `.viewer-handoff-browser-${process.pid}`);
const stillToken = 'asset:0123abcd-0123-4567-89ab-0123456789ab';
const importedToken = 'asset:1123abcd-0123-4567-89ab-0123456789ab';
const localImage = Buffer.from('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+/W7cAAAAASUVORK5CYII=', 'base64');

function deferred() {
  let release;
  const promise = new Promise((resolvePromise) => { release = resolvePromise; });
  return { promise, release };
}

function json(route, body) {
  return route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(body) });
}

const stats = { imageTokenRequests: 0, uploadRequests: 0, createBodies: [], externalRequests: [], unknownApi: [] };
let imageTokenGate = null;
let server;
let context;

try {
  await mkdir(tempRoot, { recursive: false });
  server = await createServer({
    configFile: false,
    root: appRoot,
    envDir: false,
    envFile: false,
    cacheDir: join(tempRoot, 'vite-cache'),
    plugins: [react()],
    logLevel: 'error',
    optimizeDeps: { noDiscovery: true, include: ['react', 'react-dom', 'react-dom/client'] },
    server: { host: '127.0.0.1', port: 0, strictPort: false, hmr: false, open: false },
  });
  await server.listen();
  const addr = server.httpServer.address();
  assert.ok(addr && typeof addr === 'object');
  const origin = `http://127.0.0.1:${addr.port}`;
  const launchOptions = {
    headless: true,
    args: [
      '--no-sandbox', '--disable-background-networking', '--disable-component-update', '--disable-default-apps',
      '--disable-sync', '--metrics-recording-only', '--no-first-run',
      '--host-resolver-rules=MAP * ~NOTFOUND, EXCLUDE 127.0.0.1',
    ],
  };
  if (process.env.NEXORA_TEST_CHROMIUM) launchOptions.executablePath = process.env.NEXORA_TEST_CHROMIUM;
  context = await chromium.launchPersistentContext(join(tempRoot, 'isolated-profile'), launchOptions);
  await context.route('**/*', async (route) => {
    const request = route.request();
    const url = new URL(request.url());
    if (url.origin !== origin) {
      stats.externalRequests.push(url.origin);
      await route.abort();
      return;
    }
    if (!url.pathname.startsWith('/api/')) {
      await route.continue();
      return;
    }

    if (url.pathname === '/api/takes' && request.method() === 'GET') return json(route, []);
    if (url.pathname === '/api/status' && request.method() === 'GET') return json(route, { up: true, active: [] });
    if (url.pathname === '/api/nexora/etat' && request.method() === 'GET') {
      return json(route, { llm: false, moteur: 'stub', son: true, territoire: 'CA', image: 'Qwen-Image', musique: null });
    }
    if (url.pathname === '/api/nexora/moteurs-gpu' && request.method() === 'GET') return json(route, []);
    if (url.pathname === '/api/nexora/devis' && request.method() === 'POST') {
      return json(route, { credits: 1, secondesEstimees: 5, moteur: 'h3-fast' });
    }
    if (url.pathname === '/api/nexora/image/42/jeton' && request.method() === 'POST') {
      stats.imageTokenRequests += 1;
      const gate = imageTokenGate;
      imageTokenGate = null;
      if (gate) await gate.promise;
      return json(route, { jeton: stillToken });
    }
    if (url.pathname === '/api/upload' && request.method() === 'POST') {
      stats.uploadRequests += 1;
      return json(route, { name: importedToken });
    }
    if (url.pathname === '/api/nexora/creer' && request.method() === 'POST') {
      stats.createBodies.push(request.postDataJSON());
      return json(route, { takeIds: [99], takeId: 99, prompt: 'stub prompt', source: 'repli', tentatives: 0, moteur: 'h3-fast' });
    }
    if (url.pathname === '/api/poster/42' && request.method() === 'GET') {
      return route.fulfill({ status: 200, contentType: 'image/png', body: localImage });
    }

    stats.unknownApi.push(`${request.method()} ${url.pathname}`);
    return json(route, {});
  });
  if (typeof context.routeWebSocket === 'function') {
    await context.routeWebSocket(`ws://127.0.0.1:${addr.port}/live`, (socket) => socket.close());
  }
  context.setDefaultTimeout(8000);
  context.setDefaultNavigationTimeout(8000);

  async function openPending(prompt, language = 'fr') {
    const gate = deferred();
    imageTokenGate = gate;
    const page = await context.newPage();
    page.on('pageerror', (error) => console.error(`Erreur React/browser: ${error.message}`));
    page.on('console', (message) => { if (message.type() === 'error') console.error(`Console browser: ${message.text()}`); });
    const conversionRequest = page.waitForRequest((request) => new URL(request.url()).pathname === '/api/nexora/image/42/jeton', { timeout: 8000 });
    const href = `${origin}/?mode=video&cle=42&intention=${encodeURIComponent(prompt)}`;
    await page.goto(href, { waitUntil: 'domcontentloaded' });
    if (language === 'en') await page.getByRole('group', { name: 'Langue du réalisateur' }).getByRole('button', { name: 'English', exact: true }).click();
    try {
      await conversionRequest;
    } catch (error) {
      console.error(`Aucun appel de conversion; DOM: ${(await page.locator('body').innerText()).slice(0, 1200)}`);
      throw error;
    }
    await page.waitForFunction(() => {
      const params = new URLSearchParams(location.search);
      return !params.has('cle') && !params.has('intention');
    });
    await page.locator('button.st-go').waitFor();
    const cta = page.locator('button.st-go');
    const ctaDisabled = await cta.isDisabled();
    const ctaText = await cta.innerText();
    if (!ctaDisabled) console.error(`CTA pendant la conversion: ${ctaText}; intention=${(await page.locator('textarea[aria-label="Description"]').inputValue()).length} caractères`);
    assert.equal(ctaDisabled, true, 'la création reste bloquée pendant la conversion');
    assert.match(ctaText, language === 'en' ? /Preparing keyframe/ : /Préparation du plan clé/);
    assert.equal(await page.locator('textarea[aria-label="Description"]').inputValue(), prompt);
    return {
      page, gate, cta,
      imageAlt: language === 'en' ? 'Starting image' : 'Image de départ',
      readyText: language === 'en' ? 'The video starts from this image.' : 'La vidéo part de cette image.',
    };
  }

  for (const [prompt, language] of [
    ['Une tasse de café se pose sur la table au lever du jour.', 'fr'],
    ['A coffee cup lands on the table at sunrise.', 'en'],
  ]) {
    const { page, gate, cta, readyText } = await openPending(prompt, language);
    gate.release();
    await page.getByText(readyText, { exact: true }).waitFor();
    await page.waitForFunction(() => {
      const button = document.querySelector('button.st-go');
      return button && !button.disabled && ['Animer avec H3', 'Animate with H3'].includes(button.textContent?.trim() ?? '');
    });
    const creationRequest = page.waitForRequest((request) => new URL(request.url()).pathname === '/api/nexora/creer');
    await cta.click();
    await creationRequest;
    const body = stats.createBodies.at(-1);
    assert.equal(body.intention, prompt, 'le prompt reste inchangé en français et en anglais');
    assert.equal(body.image, stillToken, 'la prise Viewer devient la première image H3');
    assert.equal(body.langueClient, language, 'la langue choisie est transmise au réalisateur');
    assert.equal(body.langueReplique, 'fr', 'la langue des répliques reste indépendante de la langue UI');
    await page.close();
  }

  {
    const { page, gate, readyText, imageAlt } = await openPending('A still already selected as the key frame.');
    gate.release();
    await page.getByText(readyText, { exact: true }).waitFor();
    const depart = page.getByRole('group', { name: 'Point de départ' });
    const keyFrame = depart.getByRole('button', { name: /Plan clé IA/ });
    await keyFrame.click();
    assert.equal(await page.locator(`img[alt="${imageAlt}"]`).count(), 1,
      'recliquer sur le départ déjà actif conserve la prise image');
    await page.close();
  }

  {
    const { page, gate } = await openPending('A language change does not stale an image handoff.');
    await page.getByRole('group', { name: 'Langue du réalisateur' }).getByRole('button', { name: 'English', exact: true }).click();
    gate.release();
    await page.getByText('The video starts from this image.', { exact: true }).waitFor();
    assert.equal(await page.locator('img[alt="Starting image"]').count(), 1,
      'le changement de langue préserve la conversion, qui ne dépend pas de la langue');
    await page.close();
  }

  {
    const { page, gate } = await openPending('A character steps forward.');
    await page.getByRole('tab', { name: 'Image' }).click();
    await page.locator('button[role="tab"][aria-selected="true"]').filter({ hasText: 'Image' }).waitFor();
    gate.release();
    await page.waitForTimeout(120);
    assert.equal(await page.locator('img[alt="Image de départ"]').count(), 0, 'un changement de mode invalide la conversion en attente');
    assert.equal(stats.createBodies.length, 2, 'aucune création H3 ne part après le changement de mode');
    await page.close();
  }

  {
    const { page, gate } = await openPending('Une scène reste en cours de route.');
    const depart = page.getByRole('group', { name: 'Point de départ' });
    await depart.getByRole('button', { name: /Texte seul/ }).click();
    gate.release();
    await page.waitForTimeout(120);
    assert.equal(await page.locator('img[alt="Image de départ"]').count(), 0, 'un changement de départ invalide la conversion en attente');
    await page.close();
  }

  {
    const { page, gate } = await openPending('A new photo replaces the pending take.');
    const depart = page.getByRole('group', { name: 'Point de départ' });
    await depart.getByRole('button', { name: /Ma photo/ }).click();
    await page.locator('input[type="file"]').setInputFiles({
      name: 'stub.png', mimeType: 'image/png', buffer: localImage,
    });
    await page.waitForFunction(() => document.querySelector('img[alt="Image de départ"]')?.src.startsWith('blob:'));
    gate.release();
    await page.waitForTimeout(120);
    assert.equal(await page.locator('img[alt="Image de départ"]').evaluate((img) => img.src.startsWith('blob:')), true,
      'la réponse de l’ancienne prise ne remplace pas la photo importée');
    const creationRequest = page.waitForRequest((request) => new URL(request.url()).pathname === '/api/nexora/creer');
    await page.locator('button.st-go').click();
    await creationRequest;
    assert.equal(stats.createBodies.at(-1).image, importedToken, 'H3 reçoit la nouvelle image importée');
    await page.close();
  }

  assert.equal(stats.imageTokenRequests, 7);
  assert.equal(stats.uploadRequests, 1);
  assert.deepEqual(stats.externalRequests, [], 'aucune requête hors loopback');
  assert.deepEqual(stats.unknownApi, [], 'toutes les API utilisées sont simulées explicitement');
  console.log('Parcours React FR/EN, conversion, sélections, annulations et création simulée : 7 scénarios réussis; aucun service moteur appelé.');
} finally {
  imageTokenGate?.release();
  await context?.close();
  await server?.close();
  await rm(tempRoot, { recursive: true, force: true });
}
