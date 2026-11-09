// @vitest-environment jsdom
import { act, useState } from 'react';
import { createRoot, type Root } from 'react-dom/client';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import type { LangueClient } from '../shared/creationLanguage';

const mocks = vi.hoisted(() => ({ moteurs: vi.fn() }));
vi.mock('./api', () => ({ api: { nexoraMoteursGpu: mocks.moteurs } }));

import { GlobalNavigation, type LienNavigation } from './GlobalNavigation';
import { Moteurs } from './studio/Moteurs';
import { MeshLanguageSwitch } from './pages/MeshLanguageSwitch';
import { attributLangueDocument, langueContenuPrincipal, nomAppNavigation } from './interfaceLanguage';

const liens = (langue: LangueClient): LienNavigation[] => [
  { id: 'marketing', to: '/marketing', label: nomAppNavigation('marketing', 'Nexora Campaign', langue), badge: 'new' },
  { id: 'prolonger', to: '/prolonger', label: nomAppNavigation('prolonger', 'Prolonger', langue), badge: 'new' },
  { id: 'detourage', to: '/detourage', label: nomAppNavigation('detourage', 'Nexora Matte', langue) },
  { id: 'object', to: '/mesh', label: nomAppNavigation('object', 'Nexora Mesh', langue) },
];

let host: HTMLDivElement;
let root: Root;

function Harness() {
  const [langue, setLangue] = useState<LangueClient>('fr');
  const [path, setPath] = useState('/mesh');
  const langueContenu = langueContenuPrincipal(path, langue);
  return (
    <>
      <GlobalNavigation langue={langue} path={path} params={new URLSearchParams()} apps={liens(langue)}>
        <Moteurs langue={langue} />
      </GlobalNavigation>
      <main lang={attributLangueDocument(langueContenu)}>{path === '/library' ? 'Bibliothèque en français' : 'Mesh content'}</main>
      <button type="button" onClick={() => setPath('/library')}>Open library</button>
      <MeshLanguageSwitch langue={langue} onChange={setLangue} />
    </>
  );
}

beforeEach(() => {
  (globalThis as typeof globalThis & { IS_REACT_ACT_ENVIRONMENT: boolean }).IS_REACT_ACT_ENVIRONMENT = true;
  mocks.moteurs.mockReset().mockResolvedValue([{ id: 'principal', nom: 'PC principal', recettes: ['music3'], enLigne: true, enCours: 1 }]);
  host = document.createElement('div');
  document.body.append(host);
});

afterEach(async () => {
  if (root) await act(async () => { root.unmount(); });
  host.remove();
});

async function mount() {
  root = createRoot(host);
  await act(async () => { root.render(<Harness />); });
  await act(async () => { await Promise.resolve(); });
}

async function click(label: string) {
  const button = [...host.querySelectorAll('button')].find((item) => item.textContent === label);
  expect(button).toBeTruthy();
  await act(async () => { (button as HTMLButtonElement).click(); await Promise.resolve(); });
}

describe('navigation partagée avec la langue Mesh', () => {
  it('commence en français, puis le sélecteur Mesh met à jour tout le header et la puce GPU', async () => {
    await mount();
    expect(host.querySelector('nav')?.getAttribute('aria-label')).toBe('Navigation principale');
    expect(host.querySelector('nav')?.textContent).toContain('Bibliothèque');
    expect(host.querySelector('.st-atelier summary')?.textContent).toContain('Atelier');
    expect(host.querySelector('.st-menu')?.textContent).toContain('Nouveau');
    expect(host.querySelector('.st-gpu')?.getAttribute('title')).toContain('en ligne, 1 tâche');
    expect(host.querySelector('.st-gpu .long')?.textContent).toBe('Image · Musique');

    await click('English');
    expect(host.querySelector('header')?.getAttribute('lang')).toBe('en-CA');
    expect(host.querySelector('nav')?.getAttribute('aria-label')).toBe('Main navigation');
    expect(host.querySelector('nav')?.textContent).toContain('Library');
    expect(host.querySelector('nav')?.textContent).not.toContain('Bibliothèque');
    expect(host.querySelector('.st-atelier summary')?.textContent).toContain('Workshop');
    expect(host.querySelector('.st-menu')?.textContent).toContain('All tools');
    expect(host.querySelector('.st-menu')?.textContent).toContain('Extend');
    expect(host.querySelector('.st-menu')?.textContent).toContain('New');
    expect(host.querySelector('.st-menu')?.textContent).toContain('Nexora Mesh');
    expect(host.querySelector('.st-gpu')?.getAttribute('title')).toContain('online, 1 task');
    expect(host.querySelector('.st-gpu .long')?.textContent).toBe('Image · Music');
    expect(host.querySelector('.st-brand')?.textContent).toContain('Nexora');
    expect(host.querySelector('.st-brand')?.textContent).toContain('Creative');
  });

  it('garde la page legacy en français quand le shell reste en anglais', async () => {
    await mount();
    await click('English');
    await click('Open library');
    expect(host.querySelector('header')?.getAttribute('lang')).toBe('en-CA');
    expect(host.querySelector('nav')?.getAttribute('aria-label')).toBe('Main navigation');
    expect(host.querySelector('main')?.getAttribute('lang')).toBe('fr-CA');
    expect(host.querySelector('main')?.textContent).toBe('Bibliothèque en français');
  });

  it('repasse le header au français sans modifier les destinations des liens', async () => {
    await mount();
    await click('English');
    await click('Français');
    expect(host.querySelector('nav')?.getAttribute('aria-label')).toBe('Navigation principale');
    expect(host.querySelector('.st-menu a[href="/prolonger"]')?.textContent).toContain('Prolonger');
    expect(host.querySelector('.st-menu a[href="/mesh"]')?.textContent).toBe('Nexora Mesh');
  });
});
