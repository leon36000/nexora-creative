// @ts-expect-error jsdom 26 is pinned as a runtime test dependency but does not bundle TypeScript declarations.
import { JSDOM } from 'jsdom';
import { afterEach, afterAll, beforeEach, describe, expect, it, vi } from 'vitest';
import type { ComponentType } from 'react';
import type { Root } from 'react-dom/client';

const dom = new JSDOM('<!doctype html><html><body></body></html>', { url: 'http://matte.test/' });
for (const name of ['window', 'document', 'HTMLElement', 'HTMLMediaElement', 'HTMLVideoElement', 'HTMLInputElement', 'Event', 'MouseEvent', 'ProgressEvent', 'File', 'Blob', 'navigator']) {
  Object.defineProperty(globalThis, name, { configurable: true, writable: true, value: (dom.window as any)[name] });
}
const [{ act, createElement }, { createRoot }, afterModule] = await Promise.all([
  import('react'), import('react-dom/client'), import('./Detourage'),
]);
const After = afterModule.default;

type Job = {
  id: string; nom: string; etat: string; etape: string; progression: number; message: string;
  source: { largeur: number; hauteur: number; fps: number; duree: number } | null;
  devis: { secondes: number; credits: number | null } | null; mesures: any; sorties: any;
};
type HttpResult = { __http: true; status: number; body: unknown };
type RequestRecord = { method: string; path: string; body: string; signal?: AbortSignal };
type Backend = {
  list?: () => unknown | Promise<unknown>;
  create?: (name: string) => unknown | Promise<unknown>;
  remove?: (id: string) => unknown | Promise<unknown>;
  poll?: (id: string, signal?: AbortSignal) => unknown | Promise<unknown>;
  action?: (id: string, action: string) => unknown | Promise<unknown>;
};

const BASE = '/api/nexora/detourage';
const http = (status: number, body: unknown = {}): HttpResult => ({ __http: true, status, body });
const isHttp = (x: unknown): x is HttpResult => !!x && typeof x === 'object' && (x as HttpResult).__http === true;
const response = (body: unknown, status = 200) => ({ ok: status >= 200 && status < 300, status, json: async () => body });
const job = (id: string, nom = id, etat = 'depose', source: Job['source'] = null): Job => ({
  id, nom, etat, etape: etat, progression: 0.25, message: etat, source,
  devis: null, mesures: null, sorties: null,
});
const sourceA = { largeur: 1920, hauteur: 1080, fps: 25, duree: 5 };
const sourceB = { largeur: 1280, hauteur: 720, fps: 25, duree: 6 };
const caps = { rapide: { disponible: true, moteur: { nom: 'fake-cpu' } }, pro: { disponible: false, description: 'bientôt' }, limites: { secondesMax: 120 } };

function deferred<T>() {
  let resolve!: (value: T) => void;
  let reject!: (reason?: unknown) => void;
  const promise = new Promise<T>((res, rej) => { resolve = res; reject = rej; });
  return { promise, resolve, reject };
}

function installBackend(backend: Backend = {}) {
  const requests: RequestRecord[] = [];
  const fetchMock = vi.fn(async (input: RequestInfo | URL, init: RequestInit = {}) => {
    const url = new URL(String(input), 'http://matte.test');
    const method = (init.method ?? 'GET').toUpperCase();
    const path = url.pathname;
    const req: RequestRecord = { method, path, body: typeof init.body === 'string' ? init.body : '', signal: init.signal ?? undefined };
    requests.push(req);
    let result: unknown;
    if (path === BASE + '/capacites' && method === 'GET') result = caps;
    else if (path === BASE + '/travaux' && method === 'GET') result = backend.list ? await backend.list() : [];
    else if (path === BASE + '/travaux' && method === 'POST') {
      const data = JSON.parse(req.body || '{}');
      result = backend.create ? await backend.create(String(data.nom ?? '')) : job(String(data.nom ?? 'new').toLowerCase(), String(data.nom ?? 'new'));
    } else {
      const match = path.match(/^\/api\/nexora\/detourage\/travaux\/([^/]+)(?:\/([^/]+))?$/);
      if (!match) result = {};
      else if (method === 'GET' && !match[2]) result = backend.poll ? await backend.poll(match[1], req.signal) : job(match[1], match[1], 'en_cours', sourceA);
      else if (method === 'DELETE' && !match[2]) result = backend.remove ? await backend.remove(match[1]) : {};
      else if (method === 'POST' && match[2]) result = backend.action ? await backend.action(match[1], match[2]) : job(match[1], match[1], match[2] === 'annuler' ? 'interrompu' : 'en_cours', sourceA);
      else result = {};
    }
    if (isHttp(result)) return response(result.body, result.status);
    return response(result);
  });
  vi.stubGlobal('fetch', fetchMock);
  return { requests, fetchMock };
}

class FakeXHR {
  static instances: FakeXHR[] = [];
  upload: { onprogress: ((e: ProgressEvent) => void) | null } = { onprogress: null };
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

type Page = { container: HTMLDivElement; root: Root; close: () => Promise<void> };
const pages: Page[] = [];
let createUrlDescriptor: PropertyDescriptor | undefined;
let revokeUrlDescriptor: PropertyDescriptor | undefined;
let pauseDescriptor: PropertyDescriptor | undefined;

async function mount(Component: ComponentType) {
  const container = document.createElement('div');
  document.body.appendChild(container);
  const root = createRoot(container);
  const page: Page = {
    container, root,
    close: async () => {
      await act(async () => { root.unmount(); await Promise.resolve(); });
      container.remove();
    },
  };
  pages.push(page);
  await act(async () => { root.render(createElement(Component)); await Promise.resolve(); });
  return page;
}

async function waitUntil(predicate: () => boolean, label: string, timeoutMs = 2500) {
  const end = Date.now() + timeoutMs;
  while (!predicate() && Date.now() < end) {
    await act(async () => { await new Promise((resolve) => setTimeout(resolve, 10)); });
  }
  if (!predicate()) throw new Error('Timed out waiting for: ' + label);
}

function matchingRequests(requests: RequestRecord[], method: string, suffix: string) {
  return requests.filter((r) => r.method === method && r.path.endsWith(suffix));
}

function fileInput(page: Page) {
  const input = page.container.querySelector('input[type="file"]') as HTMLInputElement | null;
  if (!input) throw new Error('video file input not rendered');
  return input;
}

async function chooseFile(page: Page, name: string) {
  const prior = FakeXHR.instances.length;
  const file = new File([name], name + '.mp4', { type: 'video/mp4' });
  const input = fileInput(page);
  Object.defineProperty(input, 'files', { configurable: true, value: [file] });
  await act(async () => { input.dispatchEvent(new Event('change', { bubbles: true })); await Promise.resolve(); });
  await waitUntil(() => FakeXHR.instances.length > prior, 'XHR upload for ' + name);
  const xhr = FakeXHR.instances[prior];
  if (xhr.body !== file) throw new Error('XHR body does not match selected file');
  return { file, xhr };
}

async function finishUpload(page: Page, xhr: FakeXHR, result: Job) {
  await act(async () => { xhr.succeed(result); await new Promise((resolve) => setTimeout(resolve, 0)); });
  const src = 'blob:' + (xhr.body as File).name;
  await waitUntil(() => page.container.querySelector('video')?.getAttribute('src') === src && page.container.textContent?.includes(String(result.source?.largeur ?? -1) + '×' + String(result.source?.hauteur ?? -1)), 'successful upload reflected in DOM');
}

async function createUploadedPage(Component: ComponentType, id: string, name: string, state = 'depose', dimensions = sourceA) {
  const page = await mount(Component);
  await waitUntil(() => matchingRequests(currentRequests, 'GET', '/capacites').length === 1, 'capability response');
  const { xhr } = await chooseFile(page, name);
  await finishUpload(page, xhr, job(id, name, state, dimensions));
  return page;
}

let currentRequests: RequestRecord[] = [];

async function clickButton(page: Page, pattern: RegExp, label: string) {
  const button = Array.from(page.container.querySelectorAll('button')).find((b) => pattern.test(b.textContent ?? ''));
  if (!button) throw new Error('button not found: ' + label + ' in ' + page.container.textContent?.slice(0, 500));
  await act(async () => { button.click(); await new Promise((resolve) => setTimeout(resolve, 0)); });
}

async function selectOnePoint(page: Page) {
  const video = page.container.querySelector('video');
  if (!video?.parentElement) throw new Error('video is not visible');
  const surface = video.parentElement.querySelector('button[aria-describedby]') as HTMLButtonElement | null;
  if (!surface) throw new Error('pointing target is not visible');
  Object.defineProperty(surface, 'getBoundingClientRect', { configurable: true, value: () => ({ x: 0, y: 0, left: 0, top: 0, width: 100, height: 100, right: 100, bottom: 100, toJSON() {} }) });
  await act(async () => { surface.dispatchEvent(new MouseEvent('click', { bubbles: true, clientX: 50, clientY: 50 })); await Promise.resolve(); });
  await waitUntil(() => pointCount(page) === 1, 'one point selection');
}

function countPointMarkers(stage: Element | null) {
  return Array.from(stage?.querySelectorAll('span') ?? []).filter((el) => (el as HTMLElement).style.width === '12px').length;
}

function pointCount(page: Page) {
  return countPointMarkers(page.container.querySelector('video')?.parentElement ?? null);
}

async function clickDelete(page: Page) {
  await clickButton(page, /supprimer|delete/i, 'delete');
}

beforeEach(() => {
  FakeXHR.instances = [];
  currentRequests = [];
  (globalThis as any).IS_REACT_ACT_ENVIRONMENT = true;
  vi.stubGlobal('XMLHttpRequest', FakeXHR);
  vi.stubGlobal('confirm', vi.fn(() => true));
  createUrlDescriptor = Object.getOwnPropertyDescriptor(URL, 'createObjectURL');
  revokeUrlDescriptor = Object.getOwnPropertyDescriptor(URL, 'revokeObjectURL');
  Object.defineProperty(URL, 'createObjectURL', { configurable: true, value: (f: File) => 'blob:' + f.name });
  Object.defineProperty(URL, 'revokeObjectURL', { configurable: true, value: vi.fn() });
  pauseDescriptor = Object.getOwnPropertyDescriptor(HTMLMediaElement.prototype, 'pause');
  Object.defineProperty(HTMLMediaElement.prototype, 'pause', { configurable: true, value: vi.fn() });
});

afterEach(async () => {
  for (const page of pages.splice(0)) await page.close();
  vi.unstubAllGlobals();
  if (createUrlDescriptor) Object.defineProperty(URL, 'createObjectURL', createUrlDescriptor); else delete (URL as any).createObjectURL;
  if (revokeUrlDescriptor) Object.defineProperty(URL, 'revokeObjectURL', revokeUrlDescriptor); else delete (URL as any).revokeObjectURL;
  if (pauseDescriptor) Object.defineProperty(HTMLMediaElement.prototype, 'pause', pauseDescriptor); else delete (HTMLMediaElement.prototype as any).pause;
  delete (globalThis as any).IS_REACT_ACT_ENVIRONMENT;
});

afterAll(() => dom.window.close());

function backendAndRequests(backend: Backend = {}) {
  const installed = installBackend(backend);
  currentRequests = installed.requests;
  return installed;
}

describe('Matte UI — candidate WIP (expected green)', () => {
  it('shows and retries a failed initial jobs-list request without creating a job', async () => {
    let lists = 0;
    const { requests } = backendAndRequests({ list: () => { lists++; if (lists === 1) throw new Error('offline'); return []; } });
    const page = await mount(After);
    await waitUntil(() => lists === 1, 'first jobs list request');
    await waitUntil(() => !!page.container.querySelector('[role="alert"]'), 'visible list error');
    await clickButton(page, /réessayer|retry/i, 'list retry');
    await waitUntil(() => lists === 2, 'retry jobs list request');
    expect(matchingRequests(requests, 'POST', '/travaux')).toHaveLength(0);
    await waitUntil(() => !page.container.querySelector('[role="alert"]'), 'list error cleared after retry');
  });

  it('preserves job A and its selection when DELETE is refused', async () => {
    const { requests } = backendAndRequests({ remove: () => http(409, { error: 'refusé' }) });
    const page = await createUploadedPage(After, 'a', 'A');
    await selectOnePoint(page);
    await clickDelete(page);
    await waitUntil(() => matchingRequests(requests, 'DELETE', '/a').length === 1, 'delete request');
    expect(page.container.querySelector('video')?.getAttribute('src')).toBe('blob:A.mp4');
    expect(page.container.textContent).toContain('1920×1080');
    expect(pointCount(page)).toBe(1);
  });

  it('shows list failure after DELETE success without restoring the deleted job', async () => {
    let lists = 0;
    const { requests } = backendAndRequests({
      list: () => { lists++; if (lists > 2) throw new Error('refresh offline'); return []; },
    });
    const page = await createUploadedPage(After, 'a', 'A');
    await waitUntil(() => lists === 2, 'post-upload jobs list refresh');
    await selectOnePoint(page);
    await clickDelete(page);
    await waitUntil(() => matchingRequests(requests, 'DELETE', '/a').length === 1, 'delete request');
    await waitUntil(() => lists === 3, 'post-delete list refresh');
    await waitUntil(() => !!page.container.querySelector('[role="alert"]'), 'visible post-delete refresh error');
    expect(page.container.querySelector('video')).toBeNull();
    expect(page.container.textContent).not.toContain('1920×1080');
  });

  it('keeps job A and its selection when B upload fails', async () => {
    backendAndRequests();
    const page = await createUploadedPage(After, 'a', 'A');
    await selectOnePoint(page);
    const { xhr } = await chooseFile(page, 'B');
    xhr.fail();
    await act(async () => { await new Promise((resolve) => setTimeout(resolve, 0)); });
    expect(page.container.querySelector('video')?.getAttribute('src')).toBe('blob:A.mp4');
    expect(page.container.textContent).toContain('1920×1080');
    expect(pointCount(page)).toBe(1);
  });

  it('ignores an older import that completes after the newer import', async () => {
    const createA = deferred<unknown>();
    const createB = deferred<unknown>();
    const { requests } = backendAndRequests({ create: (name) => name === 'A' ? createA.promise : createB.promise });
    const page = await mount(After);
    await waitUntil(() => !fileInput(page).disabled, 'enabled file input');
    const input = fileInput(page);
    const fileA = new File(['A'], 'A.mp4', { type: 'video/mp4' });
    const fileB = new File(['B'], 'B.mp4', { type: 'video/mp4' });
    Object.defineProperty(input, 'files', { configurable: true, value: [fileA] });
    await act(async () => { input.dispatchEvent(new Event('change', { bubbles: true })); });
    await waitUntil(() => matchingRequests(requests, 'POST', '/travaux').length === 1, 'create A');
    Object.defineProperty(input, 'files', { configurable: true, value: [fileB] });
    await act(async () => { input.dispatchEvent(new Event('change', { bubbles: true })); });
    await waitUntil(() => matchingRequests(requests, 'POST', '/travaux').length === 2, 'create B');
    createB.resolve(job('b', 'B'));
    await waitUntil(() => FakeXHR.instances.some((x) => (x.body as File | null)?.name === 'B.mp4'), 'B XHR created');
    const xhrB = FakeXHR.instances.find((x) => (x.body as File | null)?.name === 'B.mp4')!;
    await finishUpload(page, xhrB, job('b', 'B', 'depose', sourceB));
    createA.resolve(job('a', 'A'));
    await act(async () => { await new Promise((resolve) => setTimeout(resolve, 0)); });
    expect(FakeXHR.instances.some((x) => (x.body as File | null)?.name === 'A.mp4')).toBe(false);
    expect(page.container.querySelector('video')?.getAttribute('src')).toBe('blob:B.mp4');
    expect(page.container.textContent).toContain('1280×720');
  });

  it('does not overlap polls and ignores a late A response after B is imported', async () => {
    const poll = deferred<unknown>();
    const { requests } = backendAndRequests({
      poll: () => poll.promise,
      action: (id, action) => action === 'annuler' ? job(id, 'A', 'interrompu', sourceA) : job(id, 'A', 'en_cours', sourceA),
    });
    const page = await createUploadedPage(After, 'a', 'A', 'en_cours');
    await waitUntil(() => matchingRequests(requests, 'GET', '/a').length === 1, 'first poll of A', 3000);
    await act(async () => { await new Promise((resolve) => setTimeout(resolve, 1600)); });
    expect(matchingRequests(requests, 'GET', '/a')).toHaveLength(1);
    const firstPoll = matchingRequests(requests, 'GET', '/a')[0];
    await clickButton(page, /^Annuler$/, 'cancel current job');
    expect(firstPoll.signal?.aborted).toBe(true);
    const { xhr } = await chooseFile(page, 'B');
    await finishUpload(page, xhr, job('b', 'B', 'depose', sourceB));
    poll.resolve(job('a', 'A', 'termine', sourceA));
    await act(async () => { await new Promise((resolve) => setTimeout(resolve, 0)); });
    expect(page.container.querySelector('video')?.getAttribute('src')).toBe('blob:B.mp4');
    expect(page.container.textContent).toContain('1280×720');
  });

  it('aborts the current poll when the page unmounts', async () => {
    const poll = deferred<unknown>();
    const { requests } = backendAndRequests({ poll: () => poll.promise });
    const page = await createUploadedPage(After, 'a', 'A', 'en_cours');
    await waitUntil(() => matchingRequests(requests, 'GET', '/a').length === 1, 'poll request', 3000);
    const signal = matchingRequests(requests, 'GET', '/a')[0].signal;
    await page.close();
    expect(signal?.aborted).toBe(true);
    poll.resolve(job('a', 'A', 'termine', sourceA));
  });

  it('switches to English without resetting source or selection or issuing a job POST', async () => {
    const { requests } = backendAndRequests();
    const page = await createUploadedPage(After, 'a', 'A');
    await selectOnePoint(page);
    const postsBefore = matchingRequests(requests, 'POST', '/travaux').length;
    await clickButton(page, /^English$/, 'English language');
    expect(page.container.querySelector('video')?.getAttribute('src')).toBe('blob:A.mp4');
    expect(pointCount(page)).toBe(1);
    expect(matchingRequests(requests, 'POST', '/travaux')).toHaveLength(postsBefore);
  });
});
