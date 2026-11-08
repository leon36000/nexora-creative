// @ts-expect-error jsdom is pinned in the private runtime; its package omits TS declarations.
import { JSDOM } from 'jsdom';
import { afterEach, describe, expect, it, vi } from 'vitest';
import type { MattePointageProps } from './MattePointage';

const dom = new JSDOM('<!doctype html><html><body></body></html>', { url: 'http://matte.test/' });
for (const name of ['window', 'document', 'HTMLElement', 'HTMLButtonElement', 'Event', 'MouseEvent', 'KeyboardEvent', 'navigator']) {
  Object.defineProperty(globalThis, name, { configurable: true, writable: true, value: (dom.window as any)[name] });
}
(globalThis as any).IS_REACT_ACT_ENVIRONMENT = true;

const [{ act, createElement }, { createRoot }, component] = await Promise.all([
  import('react'), import('react-dom/client'), import('./MattePointage'),
]);
const MattePointage = component.MattePointage;
const pages: { container: HTMLDivElement; root: ReturnType<typeof createRoot> }[] = [];

async function mount(props: MattePointageProps) {
  const container = document.createElement('div');
  document.body.appendChild(container);
  const root = createRoot(container);
  pages.push({ container, root });
  await act(async () => { root.render(createElement(MattePointage, props)); });
  return container;
}

afterEach(async () => {
  for (const page of pages.splice(0)) {
    await act(async () => { page.root.unmount(); });
    page.container.remove();
  }
  vi.restoreAllMocks();
});

describe('MattePointage', () => {
  it('expose la position et les instructions, puis ajuste la cible par pas entiers', async () => {
    const container = await mount({ disabled: false, onPoint: vi.fn(), label: (x, y) => `Cible x ${x}, y ${y}`, help: 'Flèches puis Entrée.' });
    const target = container.querySelector('button')!;
    const helpId = target.getAttribute('aria-describedby')!;
    expect(target.getAttribute('aria-label')).toBe('Cible x 50, y 50');
    expect(document.getElementById(helpId)?.textContent).toBe('Flèches puis Entrée.');

    await act(async () => { target.focus(); target.dispatchEvent(new dom.window.KeyboardEvent('keydown', { key: 'ArrowRight', bubbles: true })); });
    await act(async () => { target.dispatchEvent(new dom.window.KeyboardEvent('keydown', { key: 'ArrowDown', shiftKey: true, bubbles: true })); });
    expect(target.getAttribute('aria-label')).toBe('Cible x 51, y 60');
  });

  it('ajoute une fois au clavier, indique un point négatif avec Maj, et respecte disabled', async () => {
    const onPoint = vi.fn();
    const container = await mount({ disabled: false, onPoint, label: (x, y) => `${x},${y}`, help: 'Aide.' });
    const target = container.querySelector('button')!;
    await act(async () => { target.focus(); });
    await act(async () => { target.dispatchEvent(new dom.window.KeyboardEvent('keydown', { key: 'ArrowLeft', bubbles: true })); });
    await act(async () => { target.dispatchEvent(new dom.window.KeyboardEvent('keydown', { key: 'Enter', bubbles: true })); });
    await act(async () => { target.dispatchEvent(new dom.window.KeyboardEvent('keydown', { key: 'Enter', repeat: true, bubbles: true })); });
    await act(async () => { target.dispatchEvent(new dom.window.KeyboardEvent('keydown', { key: ' ', shiftKey: true, bubbles: true })); });
    expect(onPoint.mock.calls).toEqual([[0.49, 0.5, false], [0.49, 0.5, true]]);

    const disabled = await mount({ disabled: true, onPoint, label: () => 'Désactivé', help: 'Aide.' });
    const disabledTarget = disabled.querySelector('button')!;
    await act(async () => { disabledTarget.dispatchEvent(new dom.window.KeyboardEvent('keydown', { key: 'Enter', bubbles: true })); });
    expect(disabledTarget.disabled).toBe(true);
    expect(onPoint).toHaveBeenCalledTimes(2);
  });

  it('borne la cible à 0–100, ne pointe pas pendant le déplacement et accepte Alt+Entrée négatif', async () => {
    const onPoint = vi.fn();
    const container = await mount({ disabled: false, onPoint, label: (x, y) => `${x},${y}`, help: 'Aide.' });
    const target = container.querySelector('button')!;
    await act(async () => { target.focus(); });
    await act(async () => {
      for (let i = 0; i < 5; i++) target.dispatchEvent(new dom.window.KeyboardEvent('keydown', { key: 'ArrowLeft', shiftKey: true, bubbles: true }));
      target.dispatchEvent(new dom.window.KeyboardEvent('keydown', { key: 'ArrowLeft', bubbles: true }));
    });
    expect(target.getAttribute('aria-label')).toBe('0,50');
    await act(async () => {
      for (let i = 0; i < 10; i++) target.dispatchEvent(new dom.window.KeyboardEvent('keydown', { key: 'ArrowRight', shiftKey: true, bubbles: true }));
      target.dispatchEvent(new dom.window.KeyboardEvent('keydown', { key: 'ArrowRight', repeat: true, bubbles: true }));
    });
    expect(target.getAttribute('aria-label')).toBe('100,50');
    expect(onPoint).not.toHaveBeenCalled();
    await act(async () => { target.dispatchEvent(new dom.window.KeyboardEvent('keydown', { key: 'Enter', altKey: true, bubbles: true })); });
    expect(onPoint.mock.calls).toEqual([[1, 0.5, true]]);
  });

  it('convertit clic et clic droit en coordonnées normalisées', async () => {
    const onPoint = vi.fn();
    const container = await mount({ disabled: false, onPoint, label: () => 'Cible', help: 'Aide.' });
    const target = container.querySelector('button')!;
    vi.spyOn(target, 'getBoundingClientRect').mockReturnValue({ left: 10, top: 20, right: 110, bottom: 220, width: 100, height: 200, x: 10, y: 20, toJSON: () => ({}) } as DOMRect);
    await act(async () => { target.dispatchEvent(new dom.window.MouseEvent('click', { bubbles: true, clientX: 35, clientY: 170, detail: 1 })); });
    await act(async () => { target.dispatchEvent(new dom.window.MouseEvent('contextmenu', { bubbles: true, clientX: 60, clientY: 120 })); });
    expect(onPoint.mock.calls).toEqual([[0.25, 0.75, false], [0.5, 0.5, true]]);
  });

  it('permet une activation assistive au point courant', async () => {
    const onPoint = vi.fn();
    const container = await mount({ disabled: false, onPoint, label: () => 'Cible', help: 'Aide.' });
    const target = container.querySelector('button')!;
    await act(async () => { target.dispatchEvent(new dom.window.MouseEvent('click', { bubbles: true, detail: 0 })); });
    expect(onPoint.mock.calls).toEqual([[0.5, 0.5, false]]);
  });

  it('ignore un pointeur sur une scène de taille nulle et un clic désactivé', async () => {
    const onPoint = vi.fn();
    const enabled = await mount({ disabled: false, onPoint, label: () => 'Cible', help: 'Aide.' });
    const target = enabled.querySelector('button')!;
    vi.spyOn(target, 'getBoundingClientRect').mockReturnValue({ left: 0, top: 0, right: 0, bottom: 0, width: 0, height: 0, x: 0, y: 0, toJSON: () => ({}) } as DOMRect);
    await act(async () => {
      target.dispatchEvent(new dom.window.MouseEvent('click', { bubbles: true, clientX: 0, clientY: 0, detail: 1 }));
      target.dispatchEvent(new dom.window.MouseEvent('contextmenu', { bubbles: true, clientX: 0, clientY: 0 }));
    });
    expect(onPoint).not.toHaveBeenCalled();

    const disabled = await mount({ disabled: true, onPoint, label: () => 'Désactivé', help: 'Aide.' });
    const disabledTarget = disabled.querySelector('button')!;
    vi.spyOn(disabledTarget, 'getBoundingClientRect').mockReturnValue({ left: 0, top: 0, right: 100, bottom: 100, width: 100, height: 100, x: 0, y: 0, toJSON: () => ({}) } as DOMRect);
    await act(async () => { disabledTarget.dispatchEvent(new dom.window.MouseEvent('click', { bubbles: true, clientX: 50, clientY: 50, detail: 1 })); });
    expect(disabledTarget.disabled).toBe(true);
    expect(onPoint).not.toHaveBeenCalled();
  });
});
