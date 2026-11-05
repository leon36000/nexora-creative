import assert from 'node:assert/strict';
import { mkdtemp, rm } from 'node:fs/promises';
import { join } from 'node:path';
import { tmpdir } from 'node:os';
import { fileURLToPath } from 'node:url';
import { dirname, resolve } from 'node:path';
import react from '@vitejs/plugin-react';
import { chromium } from 'playwright-core';
import { createServer } from 'vite';

const appRoot = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const tempRoot = await mkdtemp(join(tmpdir(), 'nexora-matte-preview-race-'));
const pngMasque = 'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+/W7cAAAAASUVORK5CYII=';
let resolvePreview;
let previewStartedResolve;
const previewStarted = new Promise((resolvePromise) => { previewStartedResolve = resolvePromise; });
let server;
let context;

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
  const address = server.httpServer.address();
  assert.ok(address && typeof address === 'object');
  const origin = `http://127.0.0.1:${address.port}`;
  const executablePath = process.env.NEXORA_TEST_CHROMIUM;
  assert.ok(executablePath, 'NEXORA_TEST_CHROMIUM doit désigner le binaire Chromium isolé');
  context = await chromium.launchPersistentContext(join(tempRoot, 'isolated-profile'), {
    executablePath,
    headless: true,
    args: ['--no-sandbox', '--disable-background-networking', '--disable-sync', '--no-first-run', '--host-resolver-rules=MAP * ~NOTFOUND, EXCLUDE 127.0.0.1'],
  });
  const externalRequests = [];
  await context.route('**/*', async (route) => {
    const request = route.request();
    const url = new URL(request.url());
    if (url.origin !== origin) {
      externalRequests.push(url.origin);
      await route.abort();
      return;
    }
    if (!url.pathname.startsWith('/api/')) {
      await route.continue();
      return;
    }
    if (url.pathname === '/api/nexora/detourage/capacites' && request.method() === 'GET') {
      return route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({
        rapide: { disponible: true, moteur: { nom: 'stub' } }, pro: { disponible: false, description: 'hors test' }, limites: { secondesMax: 120 },
      }) });
    }
    if (url.pathname === '/api/nexora/detourage/travaux' && request.method() === 'GET') {
      return route.fulfill({ status: 200, contentType: 'application/json', body: '[]' });
    }
    if (url.pathname === '/api/nexora/detourage/travaux' && request.method() === 'POST') {
      return route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({
        id: 'testmatte01', nom: 'test', etat: 'depose', etape: 'depot', progression: 0, message: 'En attente', source: null, devis: null, mesures: null, sorties: null,
      }) });
    }
    if (url.pathname === '/api/nexora/detourage/travaux/testmatte01/source' && request.method() === 'PUT') {
      await request.postDataBuffer();
      return route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({
        id: 'testmatte01', nom: 'test', etat: 'depose', etape: 'depot', progression: 0, message: 'Vidéo prête',
        source: { largeur: 320, hauteur: 240, fps: 10, duree: 2 }, devis: null, mesures: null, sorties: null,
      }) });
    }
    if (url.pathname === '/api/nexora/detourage/apercu' && request.method() === 'POST') {
      previewStartedResolve();
      await new Promise((resolvePromise) => { resolvePreview = resolvePromise; });
      return route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ masqueB64: pngMasque, aire: 0.5, secondes: 0.1 }) });
    }
    if (url.pathname === '/api/status' && request.method() === 'GET') {
      return route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ up: true, active: [] }) });
    }
    if (url.pathname === '/api/takes' && request.method() === 'GET') {
      return route.fulfill({ status: 200, contentType: 'application/json', body: '[]' });
    }
    if (url.pathname === '/api/nexora/moteurs-gpu' && request.method() === 'GET') {
      return route.fulfill({ status: 200, contentType: 'application/json', body: '[]' });
    }
    return route.fulfill({ status: 200, contentType: 'application/json', body: '{}' });
  });
  if (typeof context.routeWebSocket === 'function') {
    context.routeWebSocket(`ws://127.0.0.1:${address.port}/live`, (socket) => socket.close());
  }
  context.setDefaultTimeout(8000);

  const page = await context.newPage();
  page.on('pageerror', (error) => console.error(`Erreur navigateur : ${error.message}`));
  page.on('console', (message) => { if (message.type() === 'error') console.error(`Console navigateur : ${message.text()}`); });
  await page.goto(`${origin}/detourage`, { waitUntil: 'domcontentloaded' });

  const videoBytes = await page.evaluate(async () => {
    const canvas = document.createElement('canvas');
    canvas.width = 320; canvas.height = 240;
    const ctx = canvas.getContext('2d');
    const stream = canvas.captureStream(10);
    const recorder = new MediaRecorder(stream, { mimeType: 'video/webm;codecs=vp8' });
    const chunks = [];
    recorder.ondataavailable = (event) => { if (event.data.size) chunks.push(event.data); };
    recorder.start();
    for (let i = 0; i < 20; i++) {
      ctx.fillStyle = i < 10 ? '#223344' : '#445566';
      ctx.fillRect(0, 0, canvas.width, canvas.height);
      await new Promise((resolvePromise) => setTimeout(resolvePromise, 50));
    }
    const stopped = new Promise((resolvePromise) => { recorder.onstop = resolvePromise; });
    recorder.stop();
    await stopped;
    stream.getTracks().forEach((track) => track.stop());
    return Array.from(new Uint8Array(await new Blob(chunks, { type: recorder.mimeType }).arrayBuffer()));
  });
  assert.ok(videoBytes.length > 1000, 'la vidéo de test synthétique est décodée');
  await page.locator('input[type="file"]').first().setInputFiles({ name: 'test.webm', mimeType: 'video/webm', buffer: Buffer.from(videoBytes) });
  const video = page.locator('video').first();
  await page.waitForFunction(() => {
    const v = document.querySelector('video');
    return !!v && v.readyState >= 1 && Number.isFinite(v.duration) && v.duration > 0.5;
  }).catch(async (error) => {
    console.error(`DOM après import : ${(await page.locator('body').innerText()).slice(0, 1600)}`);
    console.error(`Vidéo : ${JSON.stringify(await page.locator('video').evaluateAll((nodes) => nodes.map((v) => ({ readyState: v.readyState, duration: v.duration, error: v.error?.message ?? null, src: v.src }))))}`);
    throw error;
  });

  await video.click({ position: { x: 100, y: 100 } });
  await previewStarted;
  await video.evaluate((element) => { element.currentTime = 0.5; });
  await page.waitForFunction(() => Math.round(document.querySelector('video').currentTime * 10) === 5);
  await page.waitForTimeout(100);
  resolvePreview();
  await page.waitForTimeout(250);
  assert.equal(await page.getByText(/Masque\s*:/).count(), 0, 'la réponse différée de l’image 0 ne doit pas marquer l’image 5');
  assert.deepEqual(externalRequests, [], 'aucune requête hors loopback');
  console.log('Matte : une prévisualisation différée sur A est écartée après déplacement vers B; APIs simulées, réseau externe bloqué.');
} finally {
  resolvePreview?.();
  await context?.close();
  await server?.close();
  await rm(tempRoot, { recursive: true, force: true });
}
