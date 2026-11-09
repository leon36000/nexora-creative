// @vitest-environment jsdom
import { act } from 'react';
import { createRoot, type Root } from 'react-dom/client';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
vi.mock('../Viewer', () => ({ recreate: vi.fn() }));
vi.mock('../store', () => ({ toast: vi.fn() }));
vi.mock('../ui', () => ({ Icon: () => null }));
import ReliefOutils, { TelechargementUsdz } from './ReliefOutils';
import type { Take } from '../api';

let conteneur: HTMLDivElement, root: Root;
beforeEach(() => {
  (globalThis as typeof globalThis & { IS_REACT_ACT_ENVIRONMENT: boolean }).IS_REACT_ACT_ENVIRONMENT = true;
  conteneur = document.createElement('div'); document.body.appendChild(conteneur); root = createRoot(conteneur);
});
afterEach(async () => { await act(async () => root.unmount()); conteneur.remove(); vi.unstubAllGlobals(); vi.restoreAllMocks(); });

describe('export USDZ', () => {
  it.each([
    ['fr', 'Ce modèle contient des éléments', 'Télécharger le GLB original'],
    ['en', 'This model contains elements', 'Download the original GLB'],
  ] as const)('explique le refus en %s et propose le GLB original', async (langue, texte, lien) => {
    const requete = vi.fn().mockResolvedValue({ ok: false, status: 400 }); vi.stubGlobal('fetch', requete);
    await act(async () => { root.render(<TelechargementUsdz url="/export?format=usdz" takeId={42} langue={langue} />); });
    await act(async () => { conteneur.querySelector('a')!.dispatchEvent(new MouseEvent('click', { bubbles: true, cancelable: true })); });
    expect(requete).toHaveBeenCalledWith('/export?format=usdz', expect.objectContaining({ method: 'HEAD' }));
    expect(conteneur.querySelector('[role="alert"]')?.textContent).toContain(texte);
    const original = [...conteneur.querySelectorAll('a')].find((a) => a.textContent?.includes(lien));
    expect(original?.getAttribute('href')).toBe('/api/nexora/relief/42/export?format=glb');
  });
  it('distingue une panne de préparation du refus de compatibilité', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ ok: false, status: 503, headers: new Headers() }));
    await act(async () => { root.render(<TelechargementUsdz url="/export" takeId={42} langue="en" />); });
    await act(async () => { conteneur.querySelector('a')!.dispatchEvent(new MouseEvent('click', { bubbles: true, cancelable: true })); });
    expect(conteneur.querySelector('[role="alert"]')?.textContent).toContain('Could not prepare');
    expect(conteneur.querySelector('[role="alert"]')?.textContent).not.toContain('does not yet support');
  });
  it('déclenche le téléchargement natif après préparation réussie', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ ok: true, status: 200, headers: new Headers({ 'content-type': 'model/vnd.usdz+zip' }) }));
    let lien: HTMLAnchorElement | undefined;
    const clic = vi.spyOn(HTMLAnchorElement.prototype, 'click').mockImplementation(function (this: HTMLAnchorElement) { lien = this; });
    await act(async () => { root.render(<TelechargementUsdz url="/export?format=usdz" takeId={42} langue="en" />); });
    await act(async () => { conteneur.querySelector('a')!.dispatchEvent(new MouseEvent('click', { bubbles: true, cancelable: true })); });
    expect(clic).toHaveBeenCalledTimes(1);
    expect(lien?.getAttribute('href')).toBe('/export?format=usdz');
    expect(lien?.hasAttribute('download')).toBe(true);
  });
  it('refuse une page HTML de connexion répondant 200', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ ok: true, status: 200, headers: new Headers({ 'content-type': 'text/html' }) }));
    const clic = vi.spyOn(HTMLAnchorElement.prototype, 'click').mockImplementation(() => {});
    await act(async () => { root.render(<TelechargementUsdz url="/export" takeId={42} langue="en" />); });
    await act(async () => { conteneur.querySelector('a')!.dispatchEvent(new MouseEvent('click', { bubbles: true, cancelable: true })); });
    expect(conteneur.querySelector('[role="alert"]')?.textContent).toContain('Could not prepare');
    expect(clic).not.toHaveBeenCalled();
  });
  it('ne télécharge pas un résultat périmé après changement de modèle', async () => {
    let finir!: (v: { ok: boolean; status: number }) => void;
    const requete = vi.fn().mockReturnValue(new Promise((resolve) => { finir = resolve; })); vi.stubGlobal('fetch', requete);
    const clic = vi.spyOn(HTMLAnchorElement.prototype, 'click');
    await act(async () => { root.render(<TelechargementUsdz url="/ancien" takeId={42} langue="fr" />); });
    await act(async () => { conteneur.querySelector('a')!.dispatchEvent(new MouseEvent('click', { bubbles: true, cancelable: true })); });
    await act(async () => { root.render(<TelechargementUsdz url="/nouveau" takeId={43} langue="fr" />); });
    await act(async () => { finir({ ok: true, status: 200 }); });
    expect((requete.mock.calls[0][1].signal as AbortSignal).aborted).toBe(true);
    expect(clic).not.toHaveBeenCalled();
  });
});


describe('rapport Mesh avec limite d’instances', () => {
  it('affiche chargement, limite et GLB actif, puis reprend après changement de cible', async () => {
    let resolveFirst!: (response: Response) => void, resolveSecond!: (response: Response) => void;
    const first = new Promise<Response>((resolve) => { resolveFirst = resolve; });
    const second = new Promise<Response>((resolve) => { resolveSecond = resolve; });
    const calls: string[] = [];
    const errorLog = vi.spyOn(console, 'error').mockImplementation(() => {});
    vi.stubGlobal('fetch', vi.fn((input: RequestInfo | URL) => {
      const url = String(input); calls.push(url);
      if (url.includes('/cartes')) return Promise.resolve(new Response(JSON.stringify({ cartes: [] }), { status: 200 }));
      if (url.includes('/rapport?')) return second;
      if (url.includes('/rapport')) return first;
      throw new Error(`unexpected request ${url}`);
    }));
    const take = { id: 42, status: 'done', kind: 'object', settings: '{}', output_path: 'fixture.glb' } as Take;
    await act(async () => { root.render(<ReliefOutils take={take} langue="en" />); });
    expect(conteneur.textContent).toContain('Analyzing the mesh');
    await act(async () => { resolveFirst(new Response(JSON.stringify({ error: 'Unprocessable Entity', code: 'MESH_INSTANCE_LIMIT', message: 'limit' }), { status: 422 })); });
    expect(conteneur.querySelector('[role="alert"]')?.textContent).toContain('exceeds the capacity');
    const link = [...conteneur.querySelectorAll('a')].find((a) => a.textContent?.includes('Download the original GLB'));
    expect(link?.getAttribute('href')).toBe('/api/nexora/relief/42/export?format=glb');
    expect(link?.hasAttribute('download')).toBe(true);
    const button = [...conteneur.querySelectorAll('button')].find((element) => element.textContent === '100 k');
    expect(button).toBeTruthy();
    await act(async () => { button!.dispatchEvent(new MouseEvent('click', { bubbles: true })); });
    expect(conteneur.textContent).toContain('Analyzing the mesh');
    const rapport = { sommets: 3, triangles: 1, degeneres: 0, aretesOuvertes: 3, aretesNonVariete: 0, composantes: 1, etanche: false, taille: [1, 1, 0], volume: null, avertissements: [] };
    await act(async () => { resolveSecond(new Response(JSON.stringify({ rapport, decime: null, compatibiliteObj: { compatible: true, code: null } }), { status: 200 })); });
    expect(conteneur.querySelector('[role="alert"]')).toBeNull();
    expect(conteneur.textContent).toContain('1 triangles');
    expect(calls.some((url) => url.endsWith('/rapport?faces=100000'))).toBe(true);
    errorLog.mockRestore();
  });
});

describe('cible de simplification et résultat réel', () => {
  it.each([
    ['fr', 'Cible de triangles (approximative)', 'Résultat après simplification', 'Analyse du maillage'],
    ['en', 'Target triangles (approximate)', 'Result after simplification', 'Analyzing the mesh'],
  ] as const)('indique la cible puis le nombre réellement obtenu en %s', async (langue, cibleLabel, resultatLabel, chargement) => {
    let finir!: (response: Response) => void;
    const attente = new Promise<Response>((resolve) => { finir = resolve; });
    const rapport = { sommets: 100, triangles: 399146, degeneres: 0, aretesOuvertes: 0, aretesNonVariete: 0, composantes: 1, etanche: true, taille: [1, 1, 1], volume: 1, avertissements: [] };
    vi.stubGlobal('fetch', vi.fn((input: RequestInfo | URL) => {
      const url = String(input);
      if (url.includes('/cartes')) return Promise.resolve(new Response(JSON.stringify({ cartes: [] }), { status: 200 }));
      if (url.includes('/rapport?')) return attente;
      if (url.includes('/rapport')) return Promise.resolve(new Response(JSON.stringify({ rapport, decime: null, cible: null, juge: null, compatibiliteObj: { compatible: true, code: null } }), { status: 200 }));
      throw new Error(`unexpected request ${url}`);
    }));
    const take = { id: 42, status: 'done', kind: 'object', settings: '{}', output_path: 'fixture.glb' } as Take;
    await act(async () => { root.render(<ReliefOutils take={take} langue={langue} />); });
    expect(conteneur.textContent).toContain(cibleLabel);
    const button = [...conteneur.querySelectorAll('button')].find((element) => element.textContent === '5 k');
    await act(async () => { button!.dispatchEvent(new MouseEvent('click', { bubbles: true })); });
    expect(conteneur.textContent).toContain(chargement);
    expect(conteneur.querySelector('a[href*="format=glb"][href*="faces="]')).toBeNull();
    expect(conteneur.textContent).not.toContain(resultatLabel);
    const decime = { ...rapport, triangles: 13185 };
    await act(async () => { finir(new Response(JSON.stringify({ rapport, decime, cible: 5000, juge: null, compatibiliteObj: { compatible: true, code: null } }), { status: 200 })); });
    expect(conteneur.textContent).toContain(resultatLabel);
    const count = new Intl.NumberFormat(langue === 'fr' ? 'fr-CA' : 'en-CA').format(13185);
    expect(conteneur.textContent).toContain(count + ' triangles');
    expect(conteneur.querySelector('a[href*="format=glb"][href*="faces=5000"]')).not.toBeNull();
  });
  it('précise quand la cible dépasse le modèle et ne provoque aucune réduction', async () => {
    const rapport = { sommets: 3, triangles: 1, degeneres: 0, aretesOuvertes: 3, aretesNonVariete: 0, composantes: 1, etanche: false, taille: [1, 1, 0], volume: null, avertissements: [] };
    vi.stubGlobal('fetch', vi.fn((input: RequestInfo | URL) => Promise.resolve(new Response(JSON.stringify(String(input).includes('/cartes') ? { cartes: [] } : { rapport, decime: null, cible: null, juge: null, compatibiliteObj: { compatible: true, code: null } }), { status: 200 }))));
    const take = { id: 42, status: 'done', kind: 'object', settings: '{}', output_path: 'fixture.glb' } as Take;
    await act(async () => { root.render(<ReliefOutils take={take} langue="en" />); });
    const button = [...conteneur.querySelectorAll('button')].find((element) => element.textContent === '5 k');
    await act(async () => { button!.dispatchEvent(new MouseEvent('click', { bubbles: true })); });
    expect(conteneur.textContent).toContain('Full model: no reduction needed');
    expect(conteneur.textContent).toContain('1 triangles');
  });
});

describe('changement de cible pendant le calcul', () => {
  it('ignore le résultat périmé et attend le résultat de la cible courante', async () => {
    let finir5!: (v: Response) => void, finir10!: (v: Response) => void;
    const pending5 = new Promise<Response>((resolve) => { finir5 = resolve; });
    const pending10 = new Promise<Response>((resolve) => { finir10 = resolve; });
    const rapport = { sommets: 100, triangles: 399146, degeneres: 0, aretesOuvertes: 0, aretesNonVariete: 0, composantes: 1, etanche: true, taille: [1, 1, 1], volume: 1, avertissements: [] };
    const response = (n: number) => new Response(JSON.stringify({ rapport, decime: { ...rapport, triangles: n }, cible: n, juge: null, compatibiliteObj: { compatible: true, code: null } }), { status: 200 });
    vi.stubGlobal('fetch', vi.fn((input: RequestInfo | URL) => {
      const url = String(input);
      if (url.includes('/cartes')) return Promise.resolve(new Response(JSON.stringify({ cartes: [] }), { status: 200 }));
      if (url.includes('faces=5000')) return pending5;
      if (url.includes('faces=10000')) return pending10;
      return Promise.resolve(response(399146));
    }));
    const take = { id: 42, status: 'done', kind: 'object', settings: '{}', output_path: 'fixture.glb' } as Take;
    await act(async () => { root.render(<ReliefOutils take={take} langue="en" />); });
    for (const label of ['5 k', '10 k']) {
      const button = [...conteneur.querySelectorAll('button')].find((element) => element.textContent === label)!;
      await act(async () => { button.dispatchEvent(new MouseEvent('click', { bubbles: true })); });
    }
    await act(async () => { finir5(response(13185)); });
    expect(conteneur.textContent).toContain('Analyzing the mesh');
    expect(conteneur.textContent).not.toContain('13,185 triangles');
    expect(conteneur.querySelector('a[href*="format=glb"][href*="faces="]')).toBeNull();
    await act(async () => { finir10(response(15000)); });
    expect(conteneur.textContent).toContain('15,000 triangles');
    expect(conteneur.querySelector('a[href*="format=glb"][href*="faces=10000"]')).not.toBeNull();
  });
});

describe('retour à une cible précédente', () => {
  it('attend une nouvelle analyse avant de réactiver son export', async () => {
    let terminer!: (v: Response) => void;
    const nouveau5 = new Promise<Response>((resolve) => { terminer = resolve; });
    const attente10 = new Promise<Response>(() => {});
    const rapport = { sommets: 100, triangles: 399146, degeneres: 0, aretesOuvertes: 0, aretesNonVariete: 0, composantes: 1, etanche: true, taille: [1, 1, 1], volume: 1, avertissements: [] };
    const response = () => new Response(JSON.stringify({ rapport, decime: { ...rapport, triangles: 13185 }, cible: 5000, juge: null, compatibiliteObj: { compatible: true, code: null } }), { status: 200 });
    let nombre5 = 0;
    vi.stubGlobal('fetch', vi.fn((input: RequestInfo | URL) => {
      const url = String(input);
      if (url.includes('/cartes')) return Promise.resolve(new Response(JSON.stringify({ cartes: [] }), { status: 200 }));
      if (url.includes('faces=5000')) return ++nombre5 === 1 ? Promise.resolve(response()) : nouveau5;
      if (url.includes('faces=10000')) return attente10;
      return Promise.resolve(response());
    }));
    const take = { id: 42, status: 'done', kind: 'object', settings: '{}', output_path: 'fixture.glb' } as Take;
    await act(async () => { root.render(<ReliefOutils take={take} langue="en" />); });
    const click = async (label: string) => {
      const button = [...conteneur.querySelectorAll('button')].find((element) => element.textContent === label)!;
      await act(async () => { button.dispatchEvent(new MouseEvent('click', { bubbles: true })); });
    };
    await click('5 k');
    expect(conteneur.textContent).toContain('13,185 triangles');
    await click('10 k');
    await click('5 k');
    expect(conteneur.textContent).toContain('Analyzing the mesh');
    expect(conteneur.textContent).not.toContain('13,185 triangles');
    expect(conteneur.querySelector('a[href*="format=glb"][href*="faces="]')).toBeNull();
    await act(async () => { terminer(response()); });
    expect(conteneur.textContent).toContain('13,185 triangles');
  });
});
