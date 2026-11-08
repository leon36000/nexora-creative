// @vitest-environment jsdom
/**
 * Repro : la boucle de suivi Texte → 3D d'ObjectPage doit s'arrêter sur un état
 * terminal (fini / echec), même si le changement de langue relance l'effet.
 */
import { act } from 'react';
import { createRoot, type Root } from 'react-dom/client';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

const mocks = vi.hoisted(() => ({
  nexoraEtat: vi.fn(),
  objetDevis: vi.fn(),
  generate: vi.fn(),
  objetTexte: vi.fn(),
  objetTexteEtat: vi.fn(),
  toast: vi.fn(),
}));

vi.mock('../api', () => ({
  api: {
    nexoraEtat: mocks.nexoraEtat,
    objetDevis: mocks.objetDevis,
    generate: mocks.generate,
    objetTexte: mocks.objetTexte,
    objetTexteEtat: mocks.objetTexteEtat,
  },
  downloadUrl: () => '', mediaUrl: () => '', posterUrl: () => '', subjectUrl: () => '', uploadFile: vi.fn(),
}));
vi.mock('../router', () => ({ useRoute: () => ({ params: new URLSearchParams() }), navigate: vi.fn(), setParams: vi.fn() }));
vi.mock('../SourcePick', () => ({
  SourceSlot: () => null,
  loadFile: vi.fn(), useTakeParam: vi.fn(),
}));
vi.mock('../store', () => ({
  definirMessageEchecPriseMesh: () => () => {},
  inFeed: () => true,
  isModel: () => false,
  settingsOf: () => ({}),
  toast: mocks.toast,
  useStore: (select: (state: unknown) => unknown) => select({ takes: [] }),
}));
vi.mock('../ui', () => ({
  Icon: () => null, MediaCard: () => null, Spill: () => null, Switch: () => null,
  Stepper: () => null,
  fmtSeconds: (seconds: number) => `${seconds}s`, presetClip: () => '/preset.mp4', useEstimate: () => null,
}));
vi.mock('../Viewer', () => ({ default: () => null, recreate: vi.fn(), remove: vi.fn() }));
vi.mock('../drop', () => ({ usePageDrop: vi.fn() }));
vi.mock('./ReliefOutils', () => ({ default: () => null }));

import ObjectPage from './Object';

let container: HTMLDivElement;
let root: Root | null = null;

beforeEach(() => {
  (globalThis as typeof globalThis & { IS_REACT_ACT_ENVIRONMENT: boolean }).IS_REACT_ACT_ENVIRONMENT = true;
  mocks.nexoraEtat.mockReset().mockResolvedValue({});
  mocks.objetDevis.mockReset().mockResolvedValue({ secondesEstimees: 20, credits: 7 });
  mocks.generate.mockReset().mockResolvedValue({ takeIds: [99] });
  mocks.objetTexte.mockReset().mockResolvedValue({ id: 42 });
  mocks.objetTexteEtat.mockReset();
  mocks.toast.mockReset();
  container = document.createElement('div');
  document.body.append(container);
});

afterEach(async () => {
  if (root) { const r = root; root = null; await act(async () => { r.unmount(); }); }
  container.remove();
  vi.useRealTimers();
});

function button(text: string) {
  return [...container.querySelectorAll('button')].find((b) => b.textContent?.includes(text));
}

async function click(target: Element | undefined | null) {
  expect(target).toBeTruthy();
  await act(async () => { (target as HTMLElement).click(); await Promise.resolve(); });
}

/** Monte la page, passe en Texte → 3D, saisit l'intention, lance la création et attend le premier sondage. */
async function lancerTexte() {
  root = createRoot(container);
  await act(async () => { root!.render(<ObjectPage />); });
  await act(async () => { await Promise.resolve(); });
  await click(button('Texte → 3D'));
  // Ignore le devis éventuellement relancé par le changement de mode.
  mocks.objetDevis.mockClear();
  const champ = container.querySelector<HTMLTextAreaElement>('textarea');
  expect(champ).toBeTruthy();
  await act(async () => {
    const setter = Object.getOwnPropertyDescriptor(HTMLTextAreaElement.prototype, 'value')!.set!;
    setter.call(champ, 'une chaise en bois');
    champ!.dispatchEvent(new Event('input', { bubbles: true }));
    await Promise.resolve();
  });
  await click(container.querySelector('button.generate'));
  expect(mocks.objetTexte).toHaveBeenCalledOnce();
  // Laisse tomber la promesse d'objetTexte puis le premier tour de sonde.
  await act(async () => { await Promise.resolve(); await Promise.resolve(); });
  expect(mocks.objetTexteEtat).toHaveBeenCalledTimes(1);
  // Horloge factice ensuite : un état terminal ne doit pas armer de nouveau tour.
  vi.useFakeTimers();
}

async function changerLangue(target: 'English' | 'Français') {
  const b = button(target);
  expect(b).toBeTruthy();
  await act(async () => { (b as HTMLElement).click(); await Promise.resolve(); });
  // Laisse le tour relancé par le re-rendu (bug actuel) ou par une nouvelle
  // chaîne (correctif) aller au bout avant de compter.
  await act(async () => { await Promise.resolve(); await Promise.resolve(); });
  const avant = mocks.objetTexteEtat.mock.calls.length;
  await act(async () => { await vi.advanceTimersByTimeAsync(3000); await Promise.resolve(); });
  // Un état terminal ne doit jamais réarmer de sonde après le re-rendu.
  // (Sous le bug actuel, l'effet relancé a déjà re-sondé sans attendre la minuterie.)
  expect(mocks.objetTexteEtat.mock.calls.length).toBe(avant);
}

describe('boucle de suivi Texte → 3D : arrêt sur état terminal', () => {
  it('fini avec objet : plus aucune requête après un changement FR → EN', async () => {
    mocks.objetTexteEtat.mockResolvedValue({ etat: 'fini', essai: 1, image: 1, objet: 11, notes: [], erreur: null, qualite: 'draft', intention: 'chaise' });
    await lancerTexte();
    await changerLangue('English');
    expect(mocks.objetTexteEtat).toHaveBeenCalledTimes(1);
  });

  it('fini sans objet : plus aucune requête après FR → EN puis EN → FR', async () => {
    mocks.objetTexteEtat.mockResolvedValue({ etat: 'fini', essai: 1, image: 1, objet: null, notes: [], erreur: null, qualite: 'draft', intention: 'chaise' });
    await lancerTexte();
    expect(container.querySelector('[role="alert"]')?.textContent).toContain('Échec.');
    expect(mocks.toast).toHaveBeenCalledTimes(1);
    await changerLangue('English');
    await changerLangue('Français');
    expect(mocks.objetTexteEtat).toHaveBeenCalledTimes(1);
    expect(mocks.toast).toHaveBeenCalledTimes(1);
  });

  it('echec : plus aucune requête après un changement FR → EN', async () => {
    mocks.objetTexteEtat.mockResolvedValue({ etat: 'echec', essai: 1, image: 1, objet: null, notes: [], erreur: 'boom', qualite: 'draft', intention: 'chaise' });
    await lancerTexte();
    await changerLangue('English');
    expect(mocks.objetTexteEtat).toHaveBeenCalledTimes(1);
    expect(mocks.toast).toHaveBeenCalledTimes(1);
  });

  it('continue à suivre une chaîne active lors du changement de langue', async () => {
    const base = { essai: 1, image: 1, objet: null, notes: [], erreur: null, qualite: 'draft', intention: 'chaise' };
    mocks.objetTexteEtat.mockResolvedValueOnce({ ...base, etat: 'image' }).mockResolvedValue({ ...base, etat: 'fini', objet: 11 });
    await lancerTexte();
    await click(button('English'));
    expect(mocks.objetTexteEtat).toHaveBeenCalledTimes(2);
    expect(mocks.toast).not.toHaveBeenCalled();
  });

  it('ignore une réponse tardive de la chaîne précédente après une nouvelle création', async () => {
    const base = { essai: 1, image: 1, objet: null, notes: [], erreur: null, qualite: 'draft', intention: 'chaise' };
    let terminerPremiere!: (e: typeof base & { etat: string }) => void;
    mocks.objetTexte.mockReset().mockResolvedValueOnce({ id: 42 }).mockResolvedValueOnce({ id: 43 });
    mocks.objetTexteEtat.mockImplementationOnce(() => new Promise((resolve) => { terminerPremiere = resolve; }))
      .mockResolvedValueOnce({ ...base, etat: 'fini', objet: 11 })
      .mockResolvedValue({ ...base, etat: 'image' });
    await lancerTexte();
    await click(button('English'));
    expect(mocks.objetTexteEtat.mock.calls.map(([id]) => id)).toEqual([42, 42]);
    await click(container.querySelector('button.generate'));
    expect(mocks.objetTexteEtat.mock.calls.map(([id]) => id)).toEqual([42, 42, 43]);
    await act(async () => { terminerPremiere({ ...base, etat: 'echec' }); await Promise.resolve(); });
    expect(mocks.toast).not.toHaveBeenCalled();
    expect(container.querySelector('[role="alert"]')).toBeNull();
  });

  it('ignore une réponse tardive et ne programme plus de suivi après démontage', async () => {
    let terminer!: (e: { etat: string }) => void;
    mocks.objetTexteEtat.mockImplementation(() => new Promise((resolve) => { terminer = resolve; }));
    await lancerTexte();
    const r = root!; root = null;
    await act(async () => { r.unmount(); });
    await act(async () => { terminer({ etat: 'echec' }); await Promise.resolve(); await vi.advanceTimersByTimeAsync(5000); });
    expect(mocks.objetTexteEtat).toHaveBeenCalledTimes(1);
    expect(mocks.toast).not.toHaveBeenCalled();
  });
});
