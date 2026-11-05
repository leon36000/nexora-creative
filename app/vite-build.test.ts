import { describe, expect, it, vi } from 'vitest';

vi.mock('vite', () => ({ defineConfig: (fn: unknown) => fn, loadEnv: vi.fn(() => ({ OPENFIELD_PORT: '4321' })) }));
vi.mock('@vitejs/plugin-react', () => ({ default: () => ({ name: 'react-factice' }) }));

import { loadEnv } from 'vite';
import configuration from './vite.config.js';

const configurer = configuration as unknown as (context: { command: 'serve' | 'build'; mode: string }) => {
  envDir?: false; server: { proxy: Record<string, { target: string }> };
};

describe('configuration Vite', () => {
  it('en build ne charge pas les fichiers env et utilise l’environnement explicite', () => {
    vi.mocked(loadEnv).mockClear();
    const cfg = configurer({ command: 'build', mode: 'production' });
    expect(loadEnv).not.toHaveBeenCalled();
    expect(cfg.envDir).toBe(false);
  });

  it('en développement conserve la lecture de configuration prévue', () => {
    vi.mocked(loadEnv).mockClear();
    const cfg = configurer({ command: 'serve', mode: 'development' });
    expect(loadEnv).toHaveBeenCalledOnce();
    expect(cfg.server.proxy['/api'].target).toContain(':4321');
  });
});
