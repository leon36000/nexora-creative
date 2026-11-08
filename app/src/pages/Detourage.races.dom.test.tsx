// @ts-expect-error jsdom 26 is pinned as a runtime test dependency but does not bundle TypeScript declarations.
import { JSDOM } from 'jsdom';
import { afterAll, afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import type { Root } from 'react-dom/client';

const dom = new JSDOM('<!doctype html><html><body></body></html>', { url: 'http://matte.test/' });
for (const name of ['window', 'document', 'HTMLElement', 'HTMLMediaElement', 'HTMLVideoElement', 'HTMLInputElement', 'HTMLCanvasElement', 'Event', 'MouseEvent', 'ProgressEvent', 'File', 'Blob', 'navigator']) {
  Object.defineProperty(globalThis, name, { configurable: true, writable: true, value: (dom.window as any)[name] });
}

const [{ act, createElement }, { createRoot }, componentModule] = await Promise.all([import('react'), import('react-dom/client'), import('./Detourage')]);
const Detourage = componentModule.default;

const BASE = '/api/nexora/detourage';
type Job = {
  id: string; nom: string; etat: string; etape: string; progression: number; message: string;
  source: { largeur: number; hauteur: number; fps: number; duree: number } | null;
  devis: null; mesures: null; sorties: null;
};
type HttpResult = { __http: true; status: number; body: unknown };
type Backend = {
  create?: (name: string) => unknown | Promise<unknown>;
  action?: (id: string, action: string) => unknown | Promise<unknown>;
  search?: () => unknown | Promise<unknown>;
};
type RequestRecord = { method: string; path: string; body: string };
type Page = { container: HTMLDivElement; root: Root; close: () => Promise<void> };

const http = (status: number, body: unknown = {}): HttpResult => ({ __http: true, status, body });
const isHttp = (x: unknown): x is HttpResult => !!x && typeof x === 'object' && (x as HttpResult).__http === true;
const response = (body: unknown, status = 200) => ({ ok: status >= 200 && status < 300, status, json: async () => body });
const sourceA = { largeur: 1920, hauteur: 1080, fps: 25, duree: 5 };
const sourceB = { largeur: 1280, hauteur: 720, fps: 25, duree: 6 };
const job = (id: string, nom = id, etat = 'depose', source: Job['source'] = null): Job => ({
  id, nom, etat, etape: etat, progression: 0.25, message: etat, source,
  devis: null, mesures: null, sorties: null,
});

function deferred<T>() {
  let resolve!: (value: T) => void;
  let reject!: (reason?: unknown) => void;
  const promise = new Promise<T>((res, rej) => { resolve = res; reject = rej; });
  return { promise, resolve, reject };
}

class FakeXHR {
  static instances: FakeXHR[] = [];
  upload = { onprogress: null as ((e: ProgressEvent) => void) | null };
  onload: ((e?: ProgressEvent) => void) | null = null;
  onerror: ((e?: ProgressEvent) => void) | null = null;
  status = 0;
  responseText = '';
  method = '';
  url = '';
  body: Blob | null = null;
  open(method: string, url: string) { this.method = method; this.url = url; }
  setRequestHeader(_name: string, _value: string) {}
  send(body: Blob) { this.body = body; FakeXHR.instances.push(this); }
  succeed(result: unknown, status = 201) { this.status = status; this.responseText = JSON.stringify(result); this.onload?.(); }
  fail() { this.onerror?.(); }
}

let requests: RequestRecord[] = [];
let pages: Page[] = [];
let createUrlDescriptor: PropertyDescriptor | undefined;
let revokeUrlDescriptor: PropertyDescriptor | undefined;
let pauseDescriptor: PropertyDescriptor | undefined;
let canvasContextDescriptor: PropertyDescriptor | undefined;
let canvasDataDescriptor: PropertyDescriptor | undefined;

function installBackend(backend: Backend = {}) {
  requests = [];
  const fetchMock = vi.fn(async (input: RequestInfo | URL, init: RequestInit = {}) => {
    const url = new URL(String(input), 'http://matte.test');
    const method = (init.method ?? 'GET').toUpperCase();
    const path = url.pathname;
    const req: RequestRecord = { method, path, body: typeof init.body === 'string' ? init.body : '' };
    requests.push(req);
    let result: unknown;
    if (path === BASE + '/capacites' && method === 'GET') result = { rapide: { disponible: true, moteur: { nom: 'fake-cpu' } }, pro: { disponible: false, description: 'bientôt' }, limites: { secondesMax: 120 } };
    else if (path === BASE + '/travaux' && method === 'GET') result = [];
    else if (path === BASE + '/travaux' && method === 'POST') {
      const data = JSON.parse(req.body || '{}');
      const name = String(data.nom ?? 'new');
      result = backend.create ? await backend.create(name) : job(name.toLowerCase(), name);
    } else if (path === BASE + '/texte' && method === 'POST') result = backend.search ? await backend.search() : { objets: [], secondes: 0 };
    else {
      const match = path.match(/^\/api\/nexora\/detourage\/travaux\/([^/]+)(?:\/([^/]+))?$/);
      if (!match) result = {};
      else if (method === 'POST' && match[2]) result = backend.action ? await backend.action(match[1], match[2]) : job(match[1], match[1], match[2] === 'annuler' ? 'interrompu' : 'en_cours', sourceA);
      else result = {};
    }
    if (isHttp(result)) return response(result.body, result.status);
    return response(result);
  });
  vi.stubGlobal('fetch', fetchMock);
  return { requests, fetchMock };
}

async function mount() {
  const container = document.createElement('div');
  document.body.appendChild(container);
  const root = createRoot(container);
  const page: Page = {
    container, root,
    close: async () => { await act(async () => { root.unmount(); await Promise.resolve(); }); container.remove(); },
  };
  pages.push(page);
  await act(async () => { root.render(createElement(Detourage)); await Promise.resolve(); });
  return page;
}

async function waitUntil(predicate: () => boolean, label: string, timeoutMs = 3000) {
  const end = Date.now() + timeoutMs;
  while (!predicate() && Date.now() < end) await act(async () => { await new Promise((resolve) => setTimeout(resolve, 10)); });
  if (!predicate()) throw new Error('Timed out waiting for: ' + label);
}

function videoInput(page: Page) {
  const input = page.container.querySelector('input[type="file"][accept="video/*"]') as HTMLInputElement | null;
  if (!input) throw new Error('video input missing');
  return input;
}

async function uploadVideo(page: Page, name: string, result: Job) {
  const prior = FakeXHR.instances.length;
  const file = new File([name], name + '.mp4', { type: 'video/mp4' });
  const input = videoInput(page);
  Object.defineProperty(input, 'files', { configurable: true, value: [file] });
  await act(async () => { input.dispatchEvent(new Event('change', { bubbles: true })); await Promise.resolve(); });
  await waitUntil(() => FakeXHR.instances.length > prior, `XHR for ${name}`);
  const xhr = FakeXHR.instances[prior];
  expect(xhr.body).toBe(file);
  await act(async () => { xhr.succeed(result); await new Promise((resolve) => setTimeout(resolve, 0)); });
  await waitUntil(() => page.container.querySelector('video')?.getAttribute('src') === 'blob:' + file.name && page.container.textContent?.includes(`${result.source?.largeur}×${result.source?.hauteur}`), `${name} is current in DOM`);
  return xhr;
}

async function uploadedPage(name: string, result: Job) {
  const page = await mount();
  await waitUntil(() => requests.some((r) => r.method === 'GET' && r.path === BASE + '/capacites'), 'capability response');
  await uploadVideo(page, name, result);
  return page;
}

async function clickButton(page: Page, pattern: RegExp, label: string) {
  const button = Array.from(page.container.querySelectorAll('button')).find((b) => pattern.test(b.textContent ?? ''));
  if (!button) throw new Error(`button missing: ${label}; text=${page.container.textContent?.slice(0, 500)}`);
  await act(async () => { button.click(); await new Promise((resolve) => setTimeout(resolve, 0)); });
  return button;
}

async function clickLaunch(page: Page) {
  const button = page.container.querySelector('button.accent') as HTMLButtonElement | null;
  if (!button) throw new Error('launch button missing');
  await act(async () => { button.click(); await new Promise((resolve) => setTimeout(resolve, 0)); });
  return button;
}

async function selectOnePoint(page: Page) {
  const video = page.container.querySelector('video');
  if (!video?.parentElement) throw new Error('video not visible');
  const surface = video.parentElement.querySelector('button[aria-describedby]') as HTMLButtonElement | null;
  if (!surface) throw new Error('pointing target not visible');
  Object.defineProperty(surface, 'getBoundingClientRect', { configurable: true, value: () => ({ x: 0, y: 0, left: 0, top: 0, width: 100, height: 100, right: 100, bottom: 100, toJSON() {} }) });
  await act(async () => { surface.dispatchEvent(new MouseEvent('click', { bubbles: true, clientX: 50, clientY: 50 })); await Promise.resolve(); });
  await waitUntil(() => countPointMarkers(video.parentElement) === 1, 'one point');
}

function countPointMarkers(stage: Element | null) {
  return Array.from(stage?.querySelectorAll('span') ?? []).filter((el) => (el as HTMLElement).style.width === '12px').length;
}

function allowVideoCapture(page: Page) {
  const video = page.container.querySelector('video');
  if (!video) throw new Error('video missing for capture');
  Object.defineProperty(video, 'videoWidth', { configurable: true, value: 640 });
  Object.defineProperty(video, 'videoHeight', { configurable: true, value: 360 });
}

async function startSearch(page: Page) {
  const input = page.container.querySelector('#mot-detourage') as HTMLInputElement | null;
  if (!input) throw new Error('search text input missing');
  const setter = Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value')?.set;
  if (!setter) throw new Error('native input value setter missing');
  setter.call(input, 'person');
  await act(async () => { input.dispatchEvent(new Event('input', { bubbles: true })); input.dispatchEvent(new Event('change', { bubbles: true })); await new Promise((resolve) => setTimeout(resolve, 0)); });
  const searchButton = Array.from(page.container.querySelectorAll('button')).find((b) => /^Chercher$/.test(b.textContent ?? '')) as HTMLButtonElement | undefined;
  if (searchButton?.disabled) throw new Error(`search button remained disabled after input; input=${input.value}`);
  await clickButton(page, /^Chercher$/, 'search');
  await waitUntil(() => requests.some((r) => r.method === 'POST' && r.path === BASE + '/texte'), 'text search request');
}

beforeEach(() => {
  pages = [];
  requests = [];
  FakeXHR.instances = [];
  (globalThis as any).IS_REACT_ACT_ENVIRONMENT = true;
  vi.stubGlobal('XMLHttpRequest', FakeXHR);
  vi.stubGlobal('confirm', vi.fn(() => true));
  createUrlDescriptor = Object.getOwnPropertyDescriptor(URL, 'createObjectURL');
  revokeUrlDescriptor = Object.getOwnPropertyDescriptor(URL, 'revokeObjectURL');
  Object.defineProperty(URL, 'createObjectURL', { configurable: true, value: (f: File) => 'blob:' + f.name });
  Object.defineProperty(URL, 'revokeObjectURL', { configurable: true, value: vi.fn() });
  pauseDescriptor = Object.getOwnPropertyDescriptor(HTMLMediaElement.prototype, 'pause');
  Object.defineProperty(HTMLMediaElement.prototype, 'pause', { configurable: true, value: vi.fn() });
  canvasContextDescriptor = Object.getOwnPropertyDescriptor(HTMLCanvasElement.prototype, 'getContext');
  canvasDataDescriptor = Object.getOwnPropertyDescriptor(HTMLCanvasElement.prototype, 'toDataURL');
  Object.defineProperty(HTMLCanvasElement.prototype, 'getContext', { configurable: true, value: () => ({ drawImage: vi.fn() }) });
  Object.defineProperty(HTMLCanvasElement.prototype, 'toDataURL', { configurable: true, value: () => 'data:image/jpeg;base64,Zm9v' });
});

afterEach(async () => {
  for (const page of pages.splice(0)) await page.close();
  vi.unstubAllGlobals();
  if (createUrlDescriptor) Object.defineProperty(URL, 'createObjectURL', createUrlDescriptor); else delete (URL as any).createObjectURL;
  if (revokeUrlDescriptor) Object.defineProperty(URL, 'revokeObjectURL', revokeUrlDescriptor); else delete (URL as any).revokeObjectURL;
  if (pauseDescriptor) Object.defineProperty(HTMLMediaElement.prototype, 'pause', pauseDescriptor); else delete (HTMLMediaElement.prototype as any).pause;
  if (canvasContextDescriptor) Object.defineProperty(HTMLCanvasElement.prototype, 'getContext', canvasContextDescriptor); else delete (HTMLCanvasElement.prototype as any).getContext;
  if (canvasDataDescriptor) Object.defineProperty(HTMLCanvasElement.prototype, 'toDataURL', canvasDataDescriptor); else delete (HTMLCanvasElement.prototype as any).toDataURL;
  delete (globalThis as any).IS_REACT_ACT_ENVIRONMENT;
});

afterAll(() => dom.window.close());

describe('Matte DOM — v2 async race regressions', () => {
  it('ignores a late launch response for A after B imports successfully', async () => {
    const launchA = deferred<unknown>();
    const { requests } = installBackend({ action: (_id, action) => action === 'lancer' ? launchA.promise : {} });
    const page = await uploadedPage('A', job('a', 'A', 'depose', sourceA));
    await selectOnePoint(page);
    await clickLaunch(page);
    await waitUntil(() => requests.some((r) => r.method === 'POST' && r.path.endsWith('/a/lancer')), 'launch A request');

    await uploadVideo(page, 'B', job('b', 'B', 'depose', sourceB));
    launchA.resolve(job('a', 'A', 'termine', sourceA));
    await act(async () => { await new Promise((resolve) => setTimeout(resolve, 0)); });

    expect(page.container.querySelector('video')?.getAttribute('src')).toBe('blob:B.mp4');
    expect(page.container.textContent).toContain('1280×720');
    expect(page.container.textContent).not.toContain('1920×1080');
  });

  it('does not restore A after a pending resume is refused and B imports', async () => {
    const resumeA = deferred<unknown>();
    const { requests } = installBackend({ action: (_id, action) => action === 'reprendre' ? resumeA.promise : {} });
    const page = await uploadedPage('A', job('a', 'A', 'interrompu', sourceA));
    await clickButton(page, /reprendre/i, 'resume A');
    await waitUntil(() => requests.some((r) => r.method === 'POST' && r.path.endsWith('/a/reprendre')), 'resume A request');

    await uploadVideo(page, 'B', job('b', 'B', 'depose', sourceB));
    resumeA.reject(new Error('refusé'));
    await act(async () => { await new Promise((resolve) => setTimeout(resolve, 0)); });

    expect(page.container.querySelector('video')?.getAttribute('src')).toBe('blob:B.mp4');
    expect(page.container.textContent).toContain('1280×720');
    expect(page.container.textContent).not.toContain('1920×1080');
  });

  it('does not apply a late background upload for A to the new B job', async () => {
    installBackend();
    const page = await uploadedPage('A', job('a', 'A', 'depose', sourceA));
    const backgroundSection = Array.from(page.container.querySelectorAll('.rail-section')).find((e) => /4\s*·\s*Fond/.test(e.textContent ?? ''));
    const imageButton = Array.from(backgroundSection?.querySelectorAll('button') ?? []).find((b) => b.textContent?.trim() === 'Image');
    if (!imageButton) throw new Error('background image selector missing');
    await act(async () => { imageButton.click(); await Promise.resolve(); });
    const bgInput = page.container.querySelector('input[type="file"][accept="image/*,video/*"]') as HTMLInputElement | null;
    if (!bgInput) throw new Error('background file input missing');
    const prior = FakeXHR.instances.length;
    const file = new File(['background'], 'background.png', { type: 'image/png' });
    Object.defineProperty(bgInput, 'files', { configurable: true, value: [file] });
    await act(async () => { bgInput.dispatchEvent(new Event('change', { bubbles: true })); await Promise.resolve(); });
    await waitUntil(() => FakeXHR.instances.length > prior, 'background XHR');
    const backgroundXhr = FakeXHR.instances[prior];
    expect(backgroundXhr.url).toContain('/travaux/a/fond');

    await uploadVideo(page, 'B', job('b', 'B', 'depose', sourceB));
    await act(async () => { backgroundXhr.succeed({ fond: 'fond-a.png' }); await new Promise((resolve) => setTimeout(resolve, 0)); });

    expect(page.container.querySelector('video')?.getAttribute('src')).toBe('blob:B.mp4');
    expect(page.container.textContent).toContain('1280×720');
    expect(page.container.textContent).not.toContain('fond déposé');
  });

  it('does not let an old search finally clear B’s newer launch state', async () => {
    const searchA = deferred<unknown>();
    const launchB = deferred<unknown>();
    const { requests } = installBackend({
      search: () => searchA.promise,
      action: (id, action) => id === 'b' && action === 'lancer' ? launchB.promise : {},
    });
    const page = await uploadedPage('A', job('a', 'A', 'depose', sourceA));
    allowVideoCapture(page);
    await startSearch(page);

    await uploadVideo(page, 'B', job('b', 'B', 'depose', sourceB));
    allowVideoCapture(page);
    await selectOnePoint(page);
    const launchButton = await clickLaunch(page);
    await waitUntil(() => requests.some((r) => r.method === 'POST' && r.path.endsWith('/b/lancer')), 'launch B request');
    expect(launchButton.textContent).toContain('Lancement');

    searchA.resolve({ objets: [], secondes: 0 });
    await act(async () => { await new Promise((resolve) => setTimeout(resolve, 0)); });
    const currentLaunch = page.container.querySelector('button.accent') as HTMLButtonElement | null;
    expect(currentLaunch).not.toBeNull();
    expect(currentLaunch?.disabled).toBe(true);
    expect(currentLaunch?.textContent).toContain('Lancement');

    launchB.resolve(job('b', 'B', 'termine', sourceB));
    await act(async () => { await new Promise((resolve) => setTimeout(resolve, 0)); });
  });
});
