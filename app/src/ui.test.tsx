import { describe, expect, it, vi } from 'vitest';
import { renderToStaticMarkup } from 'react-dom/server';
import type { Take } from './api';

vi.mock('./store', () => ({
  isActive: (take: Take) => take.status === 'queued' || take.status === 'rendering',
  isImage: () => false,
  isModel: () => false,
  refreshStatus: vi.fn(),
  settingsOf: (take: Take) => JSON.parse(take.settings),
  toast: vi.fn(),
  useStore: (select: (s: any) => unknown) => select({ progress: {}, started: { prompt: true }, preview: null, status: { active: [], queueRemaining: 0 }, takes: [], toast: null }),
}));

import { MediaCard, Stepper } from './ui';

const take = (status: Take['status'], error?: string): Take => ({
  id: 41, project_id: null, kind: 'object', status, shot_name: 'sample', output_path: null, prompt_id: 'prompt', error: error ?? null,
  settings: JSON.stringify({ width: 1024, height: 1024 }), created_at: '', render_seconds: null, transcript: null, starred: 0,
});

describe('MediaCard locale option', () => {
  it.each([
    ['fr', 'Rendu en cours', 'Cette prise'],
    ['en', 'Rendering', 'This take'],
  ] as const)('localise l’état actif en %s', (langue, rendering, failed) => {
    const active = renderToStaticMarkup(<MediaCard take={take('rendering')} langue={langue} />);
    const inactive = renderToStaticMarkup(<MediaCard take={take('failed', 'synthetic technical failure')} langue={langue} />);
    expect(active).toContain(rendering);
    expect(inactive).toContain(failed);
    expect(inactive).not.toContain('synthetic technical failure');
  });

  it('préserve le rendu d’erreur historique sans prop langue', () => {
    const html = renderToStaticMarkup(<MediaCard take={take('failed', 'synthetic technical failure')} />);
    expect(html).toContain('synthetic technical failure');
  });

  it('localise les commandes du compteur et garde leur valeur par défaut', () => {
    const localized = renderToStaticMarkup(<Stepper value={2} min={1} max={4} onChange={() => {}} labels={{ decrease: 'Moins de prises', increase: 'Plus de prises' }} />);
    const legacy = renderToStaticMarkup(<Stepper value={2} min={1} max={4} onChange={() => {}} />);
    expect(localized).toContain('aria-label="Moins de prises"');
    expect(localized).toContain('aria-label="Plus de prises"');
    expect(legacy).toContain('aria-label="fewer"');
    expect(legacy).toContain('aria-label="more"');
  });
});
