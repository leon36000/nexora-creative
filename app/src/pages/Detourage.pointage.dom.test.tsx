// @ts-expect-error jsdom is pinned in the private runtime; its package omits TS declarations.
import { JSDOM } from 'jsdom';
import { afterEach, describe, expect, it, vi } from 'vitest';
import type { Root } from 'react-dom/client';

const dom = new JSDOM('<!doctype html><html><body></body></html>', { url: 'http://matte.test/' });
for (const name of ['window', 'document', 'Node', 'HTMLElement', 'HTMLMediaElement', 'HTMLVideoElement', 'HTMLInputElement', 'HTMLCanvasElement', 'Event', 'MouseEvent', 'KeyboardEvent', 'File', 'Blob', 'navigator']) {
  Object.defineProperty(globalThis, name, { configurable: true, writable: true, value: (dom.window as any)[name] });
}
(globalThis as any).IS_REACT_ACT_ENVIRONMENT = true;
let nextBlob = 0;
Object.defineProperty(dom.window.URL, 'createObjectURL', { configurable: true, value: () => `blob:matte-keyboard-test-${++nextBlob}` });
Object.defineProperty(dom.window.URL, 'revokeObjectURL', { configurable: true, value: () => {} });
vi.stubGlobal('URL', dom.window.URL);

const [{ act, createElement }, { createRoot }, componentModule] = await Promise.all([
  import('react'), import('react-dom/client'), import('./Detourage'),
]);
const Detourage = componentModule.default;
const BASE = '/api/nexora/detourage';
type Job = { id: string; nom: string; etat: string; etape: string; progression: number; message: string;
  source: { largeur: number; hauteur: number; fps: number; duree: number } | null; devis: null; mesures: null; sorties: null };
type Page = { container: HTMLDivElement; root: Root };
const pages: Page[] = [];

const job = (id: string, source: Job['source'] = null): Job => ({ id, nom: 'essai', etat: 'depose', etape: 'depose', progression: 0, message: '', source, devis: null, mesures: null, sorties: null });
const capabilities = { rapide: { disponible: true, moteur: { nom: 'test-cpu' } }, pro: { disponible: false, description: '' }, limites: { secondesMax: 120 } };
const found = { objets: [{ masqueB64: 'dGVzdA==', score: 0.92, boite: [0.2, 0.1, 0.6, 0.9], aire: 0.3 }], secondes: 0.04 };

class FakeXHR {
  static instances: FakeXHR[] = [];
  upload = { onprogress: null as ((e: ProgressEvent) => void) | null };
  onload: ((e?: ProgressEvent) => void) | null = null;
  onerror: ((e?: ProgressEvent) => void) | null = null;
  status = 0;
  responseText = '';
  open(_method: string, _url: string) {}
  setRequestHeader(_name: string, _value: string) {}
  send(_body: Blob) { FakeXHR.instances.push(this); }
  succeed(body: unknown) { this.status = 201; this.responseText = JSON.stringify(body); this.onload?.(); }
}

async function waitUntil(predicate: () => boolean) {
  const end = Date.now() + 3000;
  while (!predicate() && Date.now() < end) await act(async () => { await new Promise((resolve) => setTimeout(resolve, 5)); });
  if (!predicate()) throw new Error('Timed out waiting for Matte DOM state.');
}

afterEach(async () => {
  for (const page of pages.splice(0)) {
    await act(async () => { page.root.unmount(); });
    page.container.remove();
  }
  vi.unstubAllGlobals();
  vi.restoreAllMocks();
  FakeXHR.instances = [];
});

describe('Detourage pointage accessible', () => {
  it('ajoute par clavier avec coordonnées annoncées, garde le mode Retirer et expose les objets trouvés comme boutons', async () => {
    FakeXHR.instances = [];
    vi.stubGlobal('XMLHttpRequest', FakeXHR);
    const requests: string[] = [];
    vi.stubGlobal('fetch', vi.fn(async (input: RequestInfo | URL, init: RequestInit = {}) => {
      const url = new dom.window.URL(String(input), 'http://matte.test');
      const method = (init.method ?? 'GET').toUpperCase();
      requests.push(`${method} ${url.pathname}`);
      let body: unknown = {};
      if (url.pathname === BASE + '/capacites') body = capabilities;
      else if (url.pathname === BASE + '/travaux' && method === 'GET') body = [];
      else if (url.pathname === BASE + '/travaux' && method === 'POST') body = job('job-1');
      else if (url.pathname === BASE + '/texte') body = found;
      return { ok: true, status: 200, json: async () => body };
    }));
    vi.spyOn(dom.window.HTMLMediaElement.prototype, 'pause').mockImplementation(() => {});
    vi.spyOn(dom.window.HTMLCanvasElement.prototype, 'getContext').mockReturnValue({ drawImage: vi.fn() } as unknown as CanvasRenderingContext2D);
    vi.spyOn(dom.window.HTMLCanvasElement.prototype, 'toDataURL').mockReturnValue('data:image/jpeg;base64,dGVzdA==');

    const container = document.createElement('div');
    document.body.appendChild(container);
    const root = createRoot(container);
    pages.push({ container, root });
    await act(async () => { root.render(createElement(Detourage)); await Promise.resolve(); });

    const upload = container.querySelector('input[type="file"][accept="video/*"]') as HTMLInputElement;
    Object.defineProperty(upload, 'files', { configurable: true, value: [new File(['clip'], 'clip.mp4', { type: 'video/mp4' })] });
    await act(async () => { upload.dispatchEvent(new dom.window.Event('change', { bubbles: true })); await Promise.resolve(); });
    await waitUntil(() => FakeXHR.instances.length === 1);
    await act(async () => { FakeXHR.instances[0].succeed(job('job-1', { largeur: 640, hauteur: 480, fps: 25, duree: 12 })); await Promise.resolve(); });

    const video = container.querySelector('video') as HTMLVideoElement;
    Object.defineProperty(video, 'videoWidth', { configurable: true, value: 0 });
    Object.defineProperty(video, 'videoHeight', { configurable: true, value: 0 });
    const target = [...container.querySelectorAll('button')].find((b) => b.getAttribute('aria-label')?.startsWith('Cible de pointage')) as HTMLButtonElement;
    expect(target).toBeTruthy();
    expect(target.disabled).toBe(false);
    expect(target.parentElement?.querySelector('video')).toBe(video);
    const stage = video.parentElement!;
    expect(stage.hasAttribute('tabindex')).toBe(false);
    expect(stage.querySelector('button[aria-describedby]')).toBe(target);
    const help = document.getElementById(target.getAttribute('aria-describedby')!)!;
    expect(help.textContent).toContain('Flèches');
    expect(help.textContent).toContain('Maj : 10 %');
    expect(help.textContent).toContain('Alt + Entrée/Espace');
    const english = [...container.querySelectorAll('button')].find((b) => b.textContent?.trim() === 'English') as HTMLButtonElement;
    await act(async () => { english.click(); });
    expect(target.getAttribute('aria-label')).toBe('Pointing target, x 50%, y 50%');
    const englishHelp = document.getElementById(target.getAttribute('aria-describedby')!)?.textContent ?? '';
    expect(englishHelp).toContain('Arrow keys');
    expect(englishHelp).toContain('Alt + Enter/Space');
    const french = [...container.querySelectorAll('button')].find((b) => b.textContent?.trim() === 'Français') as HTMLButtonElement;
    await act(async () => { french.click(); });
    expect(target.getAttribute('aria-label')).toBe('Cible de pointage, x 50 %, y 50 %');

    await act(async () => { target.focus(); target.dispatchEvent(new dom.window.KeyboardEvent('keydown', { key: 'ArrowRight', bubbles: true })); });
    expect(document.activeElement).toBe(target);
    expect(target.getAttribute('aria-label')).toBe('Cible de pointage, x 51 %, y 50 %');
    expect(requests.some((r) => r.endsWith('/apercu'))).toBe(false);
    await act(async () => { target.dispatchEvent(new dom.window.KeyboardEvent('keydown', { key: 'Enter', bubbles: true })); });
    let points = [...stage.querySelectorAll('span')].filter((el) => (el as HTMLElement).style.width === '12px');
    expect(points).toHaveLength(1);
    expect((points[0] as HTMLElement).style.background).toBe('rgb(53, 224, 138)');

    const remove = [...container.querySelectorAll('button')].find((b) => b.textContent?.trim() === '− Retirer') as HTMLButtonElement;
    await act(async () => { remove.click(); });
    await act(async () => { target.focus(); target.dispatchEvent(new dom.window.KeyboardEvent('keydown', { key: 'Enter', bubbles: true })); });
    points = [...stage.querySelectorAll('span')].filter((el) => (el as HTMLElement).style.width === '12px');
    expect(points).toHaveLength(2);
    expect((points[1] as HTMLElement).style.background).toBe('rgb(255, 77, 94)');

    Object.defineProperty(video, 'videoWidth', { configurable: true, value: 640 });
    Object.defineProperty(video, 'videoHeight', { configurable: true, value: 480 });
    const searchText = container.querySelector('#mot-detourage') as HTMLInputElement;
    const valueSetter = Object.getOwnPropertyDescriptor(dom.window.HTMLInputElement.prototype, 'value')!.set!;
    valueSetter.call(searchText, 'person');
    await act(async () => { searchText.dispatchEvent(new dom.window.Event('input', { bubbles: true })); searchText.dispatchEvent(new dom.window.Event('change', { bubbles: true })); });
    const search = [...container.querySelectorAll('button')].find((b) => b.textContent?.trim() === 'Chercher') as HTMLButtonElement;
    await act(async () => { search.click(); await Promise.resolve(); });
    await waitUntil(() => !!container.querySelector('button[aria-label="Choisir cet objet (score 0.92)"]'));
    const result = container.querySelector('button[aria-label="Choisir cet objet (score 0.92)"]') as HTMLButtonElement;
    expect(result.type).toBe('button');
    expect(result.tabIndex).toBe(0);
    expect(target.compareDocumentPosition(result) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
    await act(async () => { result.focus(); });
    expect(document.activeElement).toBe(result);
    await act(async () => { result.click(); });
    expect(container.querySelector('button[aria-label="Choisir cet objet (score 0.92)"]')).toBeNull();
    expect([...stage.querySelectorAll('div')].some((el) => (el as HTMLElement).style.border === '2px dashed rgb(53, 224, 138)')).toBe(true);
  });
});
