// @vitest-environment jsdom
import { act, createElement, StrictMode, useState } from 'react';
import { createRoot, type Root } from 'react-dom/client';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

const h = vi.hoisted(() => ({
  store: { takes: [] as any[] },
  takeAsInput: vi.fn(),
  mediaUrl: vi.fn((id: number) => `https://mesh.invalid/api/media/${id}`),
  toast: vi.fn(),
  setParams: vi.fn(),
}));

vi.mock('./api', () => ({
  mediaUrl: h.mediaUrl,
  posterUrl: vi.fn(),
  takeAsInput: h.takeAsInput,
  uploadFile: vi.fn(),
}));
vi.mock('./store', () => ({
  isImage: (take: any) => take.kind === 'image',
  isModel: vi.fn(() => false),
  settingsOf: (take: any) => take.settings ?? {},
  toast: h.toast,
  useStore: (select: (state: any) => unknown) => select(h.store),
}));
vi.mock('./router', () => ({ setParams: h.setParams }));
vi.mock('./drop', () => ({ useDropZone: () => ({ over: false, props: {} }) }));
vi.mock('./pages/Mirror', () => ({ DropWell: () => null }));
vi.mock('./ui', () => ({ Icon: () => null }));

import { useTakeParam, type Source } from './SourcePick';

type Deferred<T> = {
  promise: Promise<T>;
  resolve: (value: T) => void;
  reject: (reason: unknown) => void;
};
type CallbackEvent = { takeId: number | undefined; langue: string };
type Langue = 'fr' | 'en';

function deferred<T>(): Deferred<T> {
  let resolve!: (value: T) => void;
  let reject!: (reason: unknown) => void;
  const promise = new Promise<T>((res, rej) => {
    resolve = res;
    reject = rej;
  });
  return { promise, resolve, reject };
}

const take = (id: number) => ({
  id,
  kind: 'image',
  output_path: `take-${id}.png`,
  settings: { userPrompt: `prompt-${id}` },
});

const flush = async () => {
  await Promise.resolve();
  await Promise.resolve();
  await new Promise<void>((resolve) => setTimeout(resolve, 0));
};

let root: Root | undefined;
let container: HTMLDivElement | undefined;
let callbackEvents: CallbackEvent[] = [];

function Page(props: { id: string | null; langue: Langue }) {
  const [last, setLast] = useState('none');
  const errorMessage = props.langue === 'fr' ? 'Échec FR' : 'Failed EN';

  useTakeParam(
    props.id,
    (source: Source) => {
      callbackEvents.push({ takeId: source.takeId, langue: props.langue });
      h.setParams({ take: null });
      setLast(`${source.takeId}:${props.langue}`);
    },
    errorMessage,
  );

  return createElement('output', null, last);
}

async function render(id: string | null, langue: Langue, strict = false) {
  await act(async () => {
    const child = createElement(Page, { id, langue });
    root!.render(strict ? createElement(StrictMode, null, child) : child);
    await flush();
  });
}

async function resolve(deferredValue: Deferred<string>, value: string) {
  await act(async () => {
    deferredValue.resolve(value);
    await flush();
  });
}

async function reject(deferredValue: Deferred<string>, error: Error) {
  await act(async () => {
    deferredValue.reject(error);
    await flush();
  });
}

function setup() {
  container = document.createElement('div');
  document.body.appendChild(container);
  root = createRoot(container);
  callbackEvents = [];
}

beforeEach(() => {
  h.store.takes = [];
  h.takeAsInput.mockReset();
  h.mediaUrl.mockClear();
  h.toast.mockClear();
  h.setParams.mockClear();

  class ImmediateImage {
    naturalWidth = 320;
    naturalHeight = 180;
    onload: ((event: Event) => void) | null = null;
    onerror: ((event: Event) => void) | null = null;

    set src(_value: string) {
      queueMicrotask(() => this.onload?.(new Event('load')));
    }
  }

  vi.stubGlobal('Image', ImmediateImage);
  (globalThis as any).IS_REACT_ACT_ENVIRONMENT = true;
  setup();
});

afterEach(async () => {
  if (root) await act(async () => root!.unmount());
  root = undefined;
  container?.remove();
  container = undefined;
  vi.unstubAllGlobals();
});

describe('useTakeParam race contracts', () => {
  it('keeps one normal success across loaded, takes, and language rerenders', async () => {
    const pending = deferred<string>();
    h.store.takes = [take(1)];
    h.takeAsInput.mockReturnValue(pending.promise);

    await render('1', 'fr');
    h.store.takes = [take(1), take(2)];
    await render('1', 'en');

    expect(h.takeAsInput.mock.calls.map((call) => call[0])).toEqual([1]);
    await resolve(pending, 'token-A');

    expect(callbackEvents.map((event) => event.takeId)).toEqual([1]);
    expect(container!.querySelector('output')?.textContent).toMatch(/^1:/);
    expect(h.setParams.mock.calls).toEqual([[{ take: null }]]);
  });

  it('A→B→A accepts only the latest A request', async () => {
    const firstA = deferred<string>();
    const pendingB = deferred<string>();
    const lastA = deferred<string>();
    let aCalls = 0;
    h.store.takes = [take(1), take(2)];
    h.takeAsInput.mockImplementation((id: number) => {
      if (id === 1) return ++aCalls === 1 ? firstA.promise : lastA.promise;
      return pendingB.promise;
    });

    await render('1', 'fr');
    await render('2', 'en');
    await render('1', 'en');
    expect(h.takeAsInput.mock.calls.map((call) => call[0])).toEqual([1, 2, 1]);

    await resolve(lastA, 'token-A-latest');
    expect(callbackEvents).toEqual([{ takeId: 1, langue: 'en' }]);
    await resolve(pendingB, 'token-B-stale');
    await resolve(firstA, 'token-A-old');

    expect(callbackEvents).toEqual([{ takeId: 1, langue: 'en' }]);
    expect(container!.querySelector('output')?.textContent).toBe('1:en');
    expect(h.setParams.mock.calls).toEqual([[{ take: null }]]);
  });

  it('invalidates A through an absent B and reloads A when it returns', async () => {
    const firstA = deferred<string>();
    const lastA = deferred<string>();
    let aCalls = 0;
    h.store.takes = [take(1)];
    h.takeAsInput.mockImplementation(() => (++aCalls === 1 ? firstA.promise : lastA.promise));

    await render('1', 'fr');
    h.store.takes = [take(1)];
    await render('2', 'en');
    await resolve(firstA, 'token-A-before-detour');
    expect(callbackEvents).toEqual([]);
    expect(h.setParams).not.toHaveBeenCalled();

    h.store.takes = [take(1)];
    await render('1', 'en');
    expect(h.takeAsInput.mock.calls.map((call) => call[0])).toEqual([1, 1]);
    await resolve(lastA, 'token-A-after-detour');
    expect(callbackEvents).toEqual([{ takeId: 1, langue: 'en' }]);
  });

  it('uses the latest callback after a language rerender during success', async () => {
    const pending = deferred<string>();
    h.store.takes = [take(1)];
    h.takeAsInput.mockReturnValue(pending.promise);

    await render('1', 'fr');
    h.store.takes = [take(1), take(2)];
    await render('1', 'en');
    await resolve(pending, 'token-A');

    expect(callbackEvents).toEqual([{ takeId: 1, langue: 'en' }]);
    expect(h.setParams.mock.calls).toEqual([[{ take: null }]]);
  });

  it('uses the latest localized message after a language rerender during rejection', async () => {
    const pending = deferred<string>();
    h.store.takes = [take(2)];
    h.takeAsInput.mockReturnValue(pending.promise);

    await render('2', 'fr');
    h.store.takes = [take(2), take(3)];
    await render('2', 'en');
    await reject(pending, new Error('backend detail'));

    expect(h.toast).toHaveBeenCalledWith('Failed EN', true);
  });

  it('does not call back or clear ?take after unmount', async () => {
    const pending = deferred<string>();
    h.store.takes = [take(1)];
    h.takeAsInput.mockReturnValue(pending.promise);
    await render('1', 'en');

    await act(async () => root!.unmount());
    root = undefined;
    await resolve(pending, 'token-after-unmount');

    expect(callbackEvents).toEqual([]);
    expect(h.setParams).not.toHaveBeenCalled();
  });

  it('ignores the superseded valid StrictMode request before the current one resolves', async () => {
    const oldRequest = deferred<string>();
    const currentRequest = deferred<string>();
    const pending = [oldRequest, currentRequest];
    h.store.takes = [take(1)];
    h.takeAsInput.mockImplementation(() => pending.shift()!.promise);

    await render('1', 'en', true);
    expect(h.takeAsInput.mock.calls.map((call) => call[0])).toEqual([1, 1]);
    await resolve(oldRequest, 'token-old');

    expect(callbackEvents).toEqual([]);
    expect(h.setParams).not.toHaveBeenCalled();
    expect(h.toast).not.toHaveBeenCalled();

    await resolve(currentRequest, 'token-current');
    expect(callbackEvents).toEqual([{ takeId: 1, langue: 'en' }]);
    expect(h.setParams.mock.calls).toEqual([[{ take: null }]]);
    expect(h.toast).not.toHaveBeenCalled();
  });

  it('ignores the superseded rejected StrictMode request before the current one rejects', async () => {
    const oldRequest = deferred<string>();
    const currentRequest = deferred<string>();
    const pending = [oldRequest, currentRequest];
    h.store.takes = [take(1)];
    h.takeAsInput.mockImplementation(() => pending.shift()!.promise);

    await render('1', 'fr', true);
    expect(h.takeAsInput.mock.calls.map((call) => call[0])).toEqual([1, 1]);
    await reject(oldRequest, new Error('stale backend detail'));

    expect(callbackEvents).toEqual([]);
    expect(h.setParams).not.toHaveBeenCalled();
    expect(h.toast).not.toHaveBeenCalled();

    await reject(currentRequest, new Error('current backend detail'));
    expect(callbackEvents).toEqual([]);
    expect(h.setParams).not.toHaveBeenCalled();
    expect(h.toast.mock.calls).toEqual([['Échec FR', true]]);
  });
});
