import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import type { LiveEvents, Take } from './api';

const captured = vi.hoisted(() => ({ events: null as LiveEvents | null }));
vi.mock('./api', () => ({
  api: {
    takes: vi.fn().mockResolvedValue([]),
    status: vi.fn().mockResolvedValue({ up: true, active: [] }),
  },
  connectLive: vi.fn((events: LiveEvents) => { captured.events = events; return () => {}; }),
}));

import { connectLive } from './api';
import { definirMessageEchecPriseMesh, getState, startLive } from './store';

const failedTake: Take = {
  id: 9, created_at: '', project_id: null, kind: 'object', shot_name: 'mesh', prompt_id: 'p9',
  status: 'failed', settings: '{}', output_path: null, render_seconds: null, transcript: null, starred: 0,
  error: 'synthetic technical detail',
};

describe('notification d’échec contextualisée Mesh', () => {
  beforeEach(() => {
    captured.events = null;
    vi.mocked(connectLive).mockClear();
    vi.useFakeTimers();
    vi.stubGlobal('window', { setTimeout: () => 1, clearTimeout: () => {} });
  });
  afterEach(() => {
    vi.unstubAllGlobals();
    vi.useRealTimers();
  });

  it('localise les échecs des modèles seulement puis conserve le repli historique', async () => {
    const retirer = definirMessageEchecPriseMesh(() => 'Cette prise n’a pas abouti. Réessaie.');
    startLive();
    await Promise.resolve();
    const events = captured.events;
    expect(events).not.toBeNull();
    events!.onTake(failedTake);
    expect(getState().toast?.text).toBe('Cette prise n’a pas abouti. Réessaie.');
    expect(getState().toast?.text).not.toContain('synthetic technical detail');

    events!.onTake({ ...failedTake, id: 10, kind: 'video', error: 'video detail' });
    expect(getState().toast?.text).toBe('Render failed: video detail');

    retirer();
    events!.onTake({ ...failedTake, id: 11, error: 'legacy detail' });
    expect(getState().toast?.text).toBe('Render failed: legacy detail');
  });
});
