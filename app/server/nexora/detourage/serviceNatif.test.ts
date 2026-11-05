import { afterEach, describe, expect, it, vi } from 'vitest';

afterEach(() => { vi.unstubAllEnvs(); vi.resetModules(); });

describe('service natif et réglages Comfy', () => {
  it('préserve le service explicite quand le site remplace les recettes du moteur principal', async () => {
    vi.stubEnv('NEXORA_DETOURAGE_URL', 'http://127.0.0.1:1234');
    vi.stubEnv('NEXORA_DETOURAGE_JETON', 'jeton-factice');
    vi.resetModules();
    const eng = await import('../../engine.js');
    eng.appliquerMoteurs([{ id: 'principal', nom: 'GB10', comfyUrl: 'http://127.0.0.1:1111', baseUrl: 'http://127.0.0.1:2222', recettes: ['qwen21', 'music3'] }]);
    expect(eng.moteurs[0].recettes).toEqual(['qwen21', 'music3']);
    expect(eng.serviceDetourageNatif()).toEqual({ id: 'detourage-natif', nom: 'Détourage natif', detourageUrl: 'http://127.0.0.1:1234', detourageJeton: 'jeton-factice' });
  });

  it('ne crée aucun service natif sans URL', async () => {
    vi.stubEnv('NEXORA_DETOURAGE_URL', '');
    vi.stubEnv('NEXORA_DETOURAGE_JETON', '');
    vi.resetModules();
    const eng = await import('../../engine.js');
    expect(eng.serviceDetourageNatif()).toBeUndefined();
  });
});
