import assert from 'node:assert/strict';
import { mkdtemp, rm } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import react from '@vitejs/plugin-react';
import { chromium } from 'playwright-core';
import { createServer } from 'vite';

const appRoot = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const tempRoot = await mkdtemp(join(tmpdir(), 'nexora-creer-photo-'));
const photoToken = 'asset:2123abcd-0123-4567-89ab-0123456789ab';
const photo = Buffer.from('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+/W7cAAAAASUVORK5CYII=', 'base64');
const stats = { uploads: [], creates: [], externalRequests: [], unknownApi: [] };
let server;
let context;

function json(route, body) {
  return route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(body) });
}

try {
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
    if (!url.pathname.startsWith('/api/')) return route.continue();

    if (url.pathname === '/api/takes' && request.method() === 'GET') return json(route, []);
    if (url.pathname === '/api/status' && request.method() === 'GET') return json(route, { up: true, active: [] });
    if (url.pathname === '/api/nexora/etat' && request.method() === 'GET') {
      return json(route, { llm: false, moteur: 'stub', son: true, territoire: 'CA', image: 'Qwen-Image', musique: null });
    }
    if (url.pathname === '/api/nexora/moteurs-gpu' && request.method() === 'GET') return json(route, []);
    if (url.pathname === '/api/nexora/devis' && request.method() === 'POST') {
      return json(route, { credits: 1, secondesEstimees: 5, moteur: 'h3-fast' });
    }
    if (url.pathname === '/api/upload' && request.method() === 'POST') {
      const body = request.postDataJSON();
      stats.uploads.push(body);
      return json(route, { name: photoToken });
    }
    if (url.pathname === '/api/nexora/creer' && request.method() === 'POST') {
      stats.creates.push(request.postDataJSON());
      return json(route, { takeIds: [99], takeId: 99, prompt: 'stub prompt', source: 'repli', tentatives: 0, moteur: 'h3-fast' });
    }

    stats.unknownApi.push(`${request.method()} ${url.pathname}`);
    return json(route, {});
  });
  if (typeof context.routeWebSocket === 'function') {
    await context.routeWebSocket(`ws://127.0.0.1:${addr.port}/live`, (socket) => socket.close());
  }
  context.setDefaultTimeout(8000);
  context.setDefaultNavigationTimeout(8000);

  for (const language of ['fr', 'en']) {
    const page = await context.newPage();
    page.on('pageerror', (error) => console.error(`Browser error: ${error.message}`));
    await page.goto(`${origin}/?mode=video`, { waitUntil: 'domcontentloaded' });
    if (language === 'en') {
      await page.getByRole('group', { name: 'Langue du réalisateur' }).getByRole('button', { name: 'English', exact: true }).click();
    }

    const copy = language === 'en'
      ? { startPoint: 'Starting point', photoMode: 'My photo', photoRequired: 'Upload a photo before starting the video.', description: 'Description', imageAlt: 'Starting image' }
      : { startPoint: 'Point de départ', photoMode: 'Ma photo', photoRequired: 'Téléverse une photo avant de lancer la vidéo.', description: 'Description', imageAlt: 'Image de départ' };
    const prompt = language === 'en' ? 'A red car crosses a quiet city street at sunrise.' : 'Une voiture rouge traverse une rue calme au lever du soleil.';
    const textarea = page.getByRole('textbox', { name: copy.description });
    await textarea.fill(prompt);
    const creationsBefore = stats.creates.length;
    await page.getByRole('group', { name: copy.startPoint }).getByRole('button', { name: new RegExp(copy.photoMode) }).click();

    const cta = page.locator('button.st-go');
    await textarea.press('Control+Enter');
    await page.waitForTimeout(120);
    assert.equal(stats.creates.length, creationsBefore, `${language}: Ctrl+Entrée ne doit pas envoyer une génération texte`);
    await page.getByText(copy.photoRequired, { exact: true }).waitFor();
    assert.equal(await cta.isDisabled(), true, `${language}: le bouton est bloqué sans photo`);

    await page.locator('input[type="file"]').setInputFiles({ name: 'photo.png', mimeType: 'image/png', buffer: photo });
    await page.locator(`img[alt="${copy.imageAlt}"]`).waitFor();
    await page.waitForFunction(() => {
      const button = document.querySelector('button.st-go');
      return button && !button.disabled;
    });
    assert.equal(await page.getByText(copy.photoRequired, { exact: true }).count(), 0, `${language}: l’indication disparaît après import`);

    const creationRequest = page.waitForRequest((request) => new URL(request.url()).pathname === '/api/nexora/creer');
    await cta.click();
    await creationRequest;
    assert.equal(stats.creates.length, creationsBefore + 1, `${language}: une seule génération autorisée après import`);
    assert.equal(stats.creates.at(-1).intention, prompt, `${language}: la description est préservée`);
    assert.equal(stats.creates.at(-1).image, photoToken, `${language}: le payload contient la photo téléversée`);
    await page.close();
  }

  assert.equal(stats.uploads.length, 2, 'les deux photos de test sont téléversées au stub');
  assert.deepEqual(stats.externalRequests, [], 'le navigateur n’a accédé qu’au serveur loopback');
  assert.deepEqual(stats.unknownApi, [], 'les appels API du parcours sont tous simulés');
  console.log('Creer FR/EN : génération bloquée sans photo par bouton et Ctrl+Entrée, puis payload image vérifié après import simulé.');
} finally {
  await context?.close();
  await server?.close();
  await rm(tempRoot, { recursive: true, force: true });
}
