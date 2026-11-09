// @vitest-environment jsdom
import { act, useState } from 'react';
import type { LangueClient } from '../../shared/creationLanguage';
import { createRoot, type Root } from 'react-dom/client';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

const mocks = vi.hoisted(() => ({
  nexoraEtat: vi.fn(),
  objetDevis: vi.fn(),
  generate: vi.fn(),
}));

vi.mock('../api', () => ({
  api: {
    nexoraEtat: mocks.nexoraEtat,
    objetDevis: mocks.objetDevis,
    generate: mocks.generate,
    objetTexte: vi.fn(),
    objetTexteEtat: vi.fn(),
  },
  downloadUrl: () => '', mediaUrl: () => '', posterUrl: () => '', subjectUrl: () => '', uploadFile: vi.fn(),
}));
vi.mock('../router', () => ({ useRoute: () => ({ params: new URLSearchParams() }), navigate: vi.fn(), setParams: vi.fn() }));
vi.mock('../SourcePick', () => ({
  SourceSlot: ({ label, value, onChange }: { label: string; value: { name: string } | null; onChange: (s: unknown) => void }) => (
    <div data-testid={`slot-${label}`}>
      <span>{label}</span>
      {value
        ? <><span data-testid={`selected-${label}`}>{value.name}</span><button type="button" aria-label={`Retirer ${label}`} onClick={() => onChange(null)}>Retirer</button></>
        : <button type="button" aria-label={`Ajouter ${label}`} onClick={() => onChange({ token: `token-${label}`, kind: 'image', url: `/${label}.png`, name: label, w: 100, h: 100, seconds: 0 })}>Choisir</button>}
    </div>
  ),
  loadFile: vi.fn(), useTakeParam: vi.fn(),
}));
vi.mock('../store', () => ({
  definirMessageEchecPriseMesh: () => () => {},
  inFeed: () => true,
  isModel: () => false,
  settingsOf: () => ({}),
  toast: vi.fn(),
  useStore: (select: (state: unknown) => unknown) => select({ takes: [] }),
}));
vi.mock('../ui', () => ({
  Icon: () => null, MediaCard: () => null, Spill: () => null, Switch: () => null,
  Stepper: ({ value, onChange, labels }: { value: number; onChange: (n: number) => void; labels: { decrease: string; increase: string } }) => (
    <div data-testid="stepper"><button type="button" aria-label={labels.decrease} onClick={() => onChange(value - 1)}>−</button><output>{value}</output><button type="button" aria-label={labels.increase} onClick={() => onChange(value + 1)}>+</button></div>
  ),
  fmtSeconds: (seconds: number) => `${seconds}s`, presetClip: () => '/preset.mp4', useEstimate: () => null,
}));
vi.mock('../Viewer', () => ({ default: () => null, recreate: vi.fn(), remove: vi.fn() }));
vi.mock('../drop', () => ({ usePageDrop: vi.fn() }));
vi.mock('./ReliefOutils', () => ({ default: () => null }));

import ObjectPage, { EtapesTexte } from './Object';

let container: HTMLDivElement;
let root: Root;

beforeEach(() => {
  (globalThis as typeof globalThis & { IS_REACT_ACT_ENVIRONMENT: boolean }).IS_REACT_ACT_ENVIRONMENT = true;
  mocks.nexoraEtat.mockReset();
  mocks.objetDevis.mockReset().mockResolvedValue({ secondesEstimees: 20, credits: 7 });
  mocks.generate.mockReset().mockResolvedValue({ takeIds: [99] });
  container = document.createElement('div');
  document.body.append(container);
});

afterEach(async () => {
  if (root) await act(async () => { root.unmount(); });
  container.remove();
});

function ObjectHarness() {
  const [langue, setLangue] = useState<LangueClient>('fr');
  return <ObjectPage langue={langue} onLangueChange={setLangue} />;
}

async function mount() {
  root = createRoot(container);
  await act(async () => { root.render(<ObjectHarness />); });
  await act(async () => { await Promise.resolve(); });
}

function button(text: string) {
  return [...container.querySelectorAll('button')].find((b) => b.textContent?.includes(text));
}

async function click(target: Element | undefined | null) {
  expect(target).toBeTruthy();
  await act(async () => { (target as HTMLElement).click(); await Promise.resolve(); });
}

async function enterViews() {
  await click(button('Multi-vues'));
  await act(async () => { await Promise.resolve(); });
}

async function addSource(label: string) {
  await click(container.querySelector(`[aria-label="Ajouter ${label}"]`));
}

function slot(label: string) { return container.querySelector(`[data-testid="slot-${label}"]`); }

describe('repli texte vers 3D', () => {
  it.each([
    ['fr', 'La deuxième tentative a échoué. Le premier modèle est conservé.'],
    ['en', 'The second attempt failed. The first model was kept.'],
  ] as const)('explique le repli en %s', async (langue, message) => {
    root = createRoot(container);
    const e = { etat: 'fini' as const, essai: 2, image: 1, objet: 11, notes: [], erreur: null,
      avertissement: 'relance-echouee' as const, qualite: 'draft' as const, intention: 'chaise' };
    await act(async () => { root.render(<EtapesTexte e={e} langue={langue} />); });
    expect(container.querySelector('[role="status"]')?.textContent).toBe(message);
  });
});

describe('langue Mesh partagée avec App', () => {
  it('reçoit la langue de l’enveloppe et ne modifie pas le payload de génération', async () => {
    const onLangueChange = vi.fn();
    root = createRoot(container);
    await act(async () => { root.render(<ObjectPage langue="en" onLangueChange={onLangueChange} />); });
    await act(async () => { await Promise.resolve(); });

    const selecteur = container.querySelector('[role="group"][aria-label="Interface language"]');
    expect(selecteur?.querySelector('button[aria-pressed="true"]')?.textContent).toBe('English');
    await click(selecteur?.querySelector('button'));
    expect(onLangueChange).toHaveBeenCalledWith('fr');

    await click(container.querySelector('[aria-label="Add an image"]') ?? container.querySelector('[aria-label="Ajouter Image"]'));
    await click(container.querySelector<HTMLButtonElement>('button.generate'));
    const payload = mocks.generate.mock.calls[0][0];
    expect(payload.userPrompt).toBe('3D from Image');
    expect(payload.langueClient).toBeUndefined();
  });
});

describe('limite multivue réelle du serveur dans ObjectPage', () => {
  it.each([2, 3, 4])('réserve la face et n’offre que %i vues au total', async (max) => {
    mocks.nexoraEtat.mockResolvedValue({ objet3d: { multivue: true, vuesMax: max } });
    await mount();
    await enterViews();
    expect(slot('Vue de face')).toBeTruthy();

    await addSource('Vue de face');
    await addSource('Vue de gauche');
    if (max >= 3) await addSource('Vue de dos');
    if (max >= 4) await addSource('Vue de droite');

    const emptyOptional = ['Vue de gauche', 'Vue de dos', 'Vue de droite'].filter((label) => !container.querySelector(`[data-testid="selected-${label}"]`));
    for (const label of emptyOptional) expect(slot(label)).toBeFalsy();
    const create = container.querySelector<HTMLButtonElement>('button.generate');
    expect(create?.disabled).toBe(false);
    await click(create);
    expect(mocks.generate).toHaveBeenCalledOnce();
    const sent = mocks.generate.mock.calls[0][0];
    expect(sent.count).toBe(1);
    expect(Object.values(sent.vues).filter(Boolean).length + 1).toBe(max);
    await act(async () => { await Promise.resolve(); });
  });

  it('garde la face obligatoire visible même si une vue latérale est choisie en premier', async () => {
    mocks.nexoraEtat.mockResolvedValue({ objet3d: { multivue: true, vuesMax: 2 } });
    await mount();
    await enterViews();
    await addSource('Vue de gauche');
    expect(slot('Vue de face')).toBeTruthy();
    expect(container.querySelector('[aria-label="Ajouter Vue de face"]')).toBeTruthy();
    expect(slot('Vue de dos')).toBeFalsy();
    expect(slot('Vue de droite')).toBeFalsy();
  });

  it('utilise le minimum sûr et signale une limite serveur indisponible', async () => {
    mocks.nexoraEtat.mockRejectedValue(new Error('HTTP 503 internal detail'));
    await mount();
    await enterViews();
    expect(container.textContent).toContain('Limite du serveur non confirmée');
    expect(container.textContent).not.toContain('HTTP 503');
    await addSource('Vue de face');
    await addSource('Vue de gauche');
    expect(container.querySelector<HTMLButtonElement>('button.generate')?.disabled).toBe(false);
    expect(slot('Vue de dos')).toBeFalsy();
    expect(slot('Vue de droite')).toBeFalsy();
  });

  it.each([false, null])('refuse la multivue si le serveur ne la déclare pas disponible (%s)', async (objet3d) => {
    mocks.nexoraEtat.mockResolvedValue({ objet3d: objet3d === null ? null : { multivue: false, vuesMax: 3 } });
    await mount();
    await enterViews();
    await addSource('Vue de face');
    await addSource('Vue de gauche');
    expect(container.querySelector('[role="alert"]')?.textContent).toContain('La reconstruction multivue n’est pas disponible');
    expect(container.querySelector<HTMLButtonElement>('button.generate')?.disabled).toBe(true);
    expect(mocks.generate).not.toHaveBeenCalled();
  });

  it('préserve les vues choisies si la limite baisse et permet de corriger la face sans les effacer', async () => {
    mocks.nexoraEtat.mockResolvedValueOnce({ objet3d: { multivue: true, vuesMax: 4 } })
      .mockResolvedValueOnce({ objet3d: { multivue: true, vuesMax: 2 } });
    await mount();
    await enterViews();
    await addSource('Vue de gauche');
    await addSource('Vue de dos');
    await click(button('Image → 3D'));
    await enterViews();

    expect(container.querySelector('[role="alert"]')?.textContent).toContain('dépasse la limite actuelle de 2 vues');
    expect(container.querySelector('[data-testid="selected-Vue de gauche"]')).toBeTruthy();
    expect(container.querySelector('[data-testid="selected-Vue de dos"]')).toBeTruthy();
    expect(container.querySelector('[aria-label="Ajouter Vue de face"]')).toBeTruthy();
    expect(container.querySelector<HTMLButtonElement>('button.generate')?.disabled).toBe(true);

    await addSource('Vue de face');
    expect(container.querySelector('[data-testid="selected-Vue de face"]')).toBeTruthy();
    expect(container.querySelector('[data-testid="selected-Vue de gauche"]')).toBeTruthy();
    expect(container.querySelector('[data-testid="selected-Vue de dos"]')).toBeTruthy();
    expect(container.querySelector<HTMLButtonElement>('button.generate')?.disabled).toBe(true);

    await click(container.querySelector('[aria-label="Retirer Vue de dos"]'));
    expect(container.querySelector('[data-testid="selected-Vue de gauche"]')).toBeTruthy();
    expect(container.querySelector('[data-testid="selected-Vue de face"]')).toBeTruthy();
    expect(container.querySelector('[role="alert"]')).toBeFalsy();
    expect(container.querySelector<HTMLButtonElement>('button.generate')?.disabled).toBe(false);
  });

  it('masque le Stepper en multivue, compte une seule génération et conserve le nombre en mode image', async () => {
    mocks.nexoraEtat.mockResolvedValue({ objet3d: { multivue: true, vuesMax: 3 } });
    await mount();
    await addSource('Image');
    const stepper = container.querySelector('[data-testid="stepper"]');
    expect(stepper?.querySelector('output')?.textContent).toBe('1');
    await click(stepper?.querySelector('[aria-label="Augmenter le nombre de prises"]'));
    await click(container.querySelector('[aria-label="Augmenter le nombre de prises"]'));
    expect(container.querySelector('[data-testid="stepper"] output')?.textContent).toBe('3');
    expect(container.querySelector('button.generate')?.textContent).toContain('21 crédits');

    await enterViews();
    expect(container.querySelector('[data-testid="stepper"]')).toBeFalsy();
    expect(container.querySelector('button.generate')?.textContent).toContain('7 crédits');
    expect(container.querySelector('button.generate')?.textContent).toContain('≈ 20s');

    await click(button('Image → 3D'));
    expect(container.querySelector('[data-testid="stepper"] output')?.textContent).toBe('3');
    expect(container.querySelector('button.generate')?.textContent).toContain('21 crédits');
  });

  it('masque le devis image périmé pendant le chargement du devis multivue', async () => {
    let terminerDevis!: (devis: { secondesEstimees: number; credits: number }) => void;
    mocks.nexoraEtat.mockResolvedValue({ objet3d: { multivue: true, vuesMax: 3 } });
    mocks.objetDevis.mockReset()
      .mockResolvedValueOnce({ secondesEstimees: 20, credits: 11 })
      .mockImplementationOnce(() => new Promise((resolve) => { terminerDevis = resolve; }));
    await mount();
    await addSource('Image');
    await click(container.querySelector('[aria-label="Augmenter le nombre de prises"]'));
    await click(container.querySelector('[aria-label="Augmenter le nombre de prises"]'));
    expect(container.querySelector('button.generate')?.textContent).toContain('33 crédits');

    await click(button('Multi-vues'));
    expect(container.querySelector('button.generate')?.textContent).not.toContain('33 crédits');
    expect(container.querySelector('button.generate')?.textContent).not.toContain('11 crédits');
    expect(container.querySelector('button.generate')?.textContent).toContain('Estimation indisponible');
    await click(button('English'));
    expect(container.querySelector('button.generate')?.textContent).toContain('Estimate unavailable');
    expect(container.querySelector('button.generate')?.textContent).not.toContain('TRELLIS.2');
    await click(button('Français'));

    await act(async () => { terminerDevis({ secondesEstimees: 25, credits: 9 }); });
    expect(container.querySelector('button.generate')?.textContent).toContain('9 crédits');
    expect(container.querySelector('button.generate')?.textContent).toContain('≈ 25s');
  });
});
