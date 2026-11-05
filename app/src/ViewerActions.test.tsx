import { beforeEach, describe, expect, it, vi } from 'vitest';
import { renderToStaticMarkup } from 'react-dom/server';

const fixture = vi.hoisted(() => ({ take: { id: 42, kind: 'still', status: 'done', settings: '{}' } }));
vi.mock('./router', () => ({ navigate: vi.fn() }));
vi.mock('./store', () => ({
  useStore: (select: (s: unknown) => unknown) => select({ takes: [fixture.take] }),
  getState: () => ({ takes: [fixture.take] }),
  settingsOf: (take: { settings: string }) => JSON.parse(take.settings),
  isImage: (take: { kind: string }) => take.kind === 'still',
  isModel: (take: { kind: string }) => take.kind === 'object',
  refreshTakes: vi.fn(), setHandoff: vi.fn(), toast: vi.fn(),
}));
vi.mock('./ui', () => ({ Icon: () => null, Spill: () => null }));
vi.mock('./castStore', () => ({ useCast: () => [] }));
vi.mock('./pages/Cast', () => ({ SaveToCast: () => null }));
import { navigate } from './router';
import { setHandoff, toast } from './store';
import { api, type Take } from './api';
import Viewer, { animate, recreate } from './Viewer';

function view(langue?: 'fr' | 'en') { return renderToStaticMarkup(<Viewer takeId={42} onClose={() => {}} onStep={() => {}} langue={langue} />); }

beforeEach(() => {
  vi.mocked(navigate).mockClear();
  vi.mocked(setHandoff).mockClear();
  vi.mocked(toast).mockClear();
});

describe('actions Viewer et routes Nexora actives', () => {
  it('retire les actions sans outil et préserve les autres actions d’image', () => {
    fixture.take = { id: 42, kind: 'still', status: 'done', settings: '{}' };
    const html = view();
    expect(html).not.toContain('>Speak<');
    expect(html).not.toContain('Use as Stage look frame');
    expect(html).not.toContain('>Add effect<');
    expect(html).toContain('>Make 3D<');
    expect(html).toContain('>Animate<');
    expect(html).not.toContain('>Make a loop<');
    expect(html).toContain('>Remove background<');
    expect(html).not.toContain('>As end frame<');
  });
  it('préserve Source still et retire le lien Stage pour un objet', () => {
    fixture.take = { id: 42, kind: 'object', status: 'done', settings: JSON.stringify({ sourceTake: 7 }) };
    const html = view();
    expect(html).toContain('>Source still<');
    expect(html).not.toContain('Use in Stage');
    expect(html).toContain('Download GLB');
  });

  it.each([
    ['fr', 'Recréer'],
    ['en', 'Recreate'],
  ] as const)('localise le bouton Recreate du Viewer en %s', (langue, label) => {
    fixture.take = { id: 42, kind: 'object', status: 'done', settings: '{}' };
    expect(view(langue)).toContain(`>${label}<`);
  });

  it('ne propose pas Animate tant que la prise image n’est pas terminée', () => {
    fixture.take = { id: 42, kind: 'still', status: 'queued', settings: '{}' };
    expect(view()).not.toContain('>Animate<');
  });

  it.each([
    ['français', 'Une tasse de café se pose sur la table au lever du jour.'],
    ['anglais', 'A coffee cup lands on the table at sunrise.'],
  ])('ouvre le parcours H3 en conservant la prise et le prompt en %s', (_langue, intention) => {
    fixture.take = { id: 42, kind: 'still', status: 'done', settings: JSON.stringify({ userPrompt: intention }) };
    animate(fixture.take as unknown as Take);
    const href = vi.mocked(navigate).mock.calls[0][0];
    const url = new URL(href, 'http://nexora.local');
    expect(url.searchParams.get('mode')).toBe('video');
    expect(url.searchParams.get('cle')).toBe('42');
    expect(url.searchParams.get('intention')).toBe(intention);
    expect(setHandoff).not.toHaveBeenCalled();
  });

  it.each([
    ['fr', 'Demande de recréation envoyée.'],
    ['en', 'Recreation request submitted.'],
  ] as const)('localise le succès de recréation dans l’interface %s', async (langue, message) => {
    const generate = vi.spyOn(api, 'generate').mockResolvedValue(undefined as never);
    const take = { id: 42, kind: 'object', status: 'done', settings: JSON.stringify({ seed: 1071, prompt: 'test' }) } as unknown as Take;

    await recreate(take, { langue });

    expect(generate).toHaveBeenCalledWith({ prompt: 'test' });
    expect(toast).toHaveBeenCalledWith(message);
    generate.mockRestore();
  });

  it.each([
    ['fr', 'Impossible de confirmer l’envoi de la demande de recréation. Vérifie tes prises avant de réessayer.'],
    ['en', 'Could not confirm whether the recreation request was submitted. Check your takes before trying again.'],
  ] as const)('masque les détails réseau et signale une confirmation impossible en %s', async (langue, message) => {
    const generate = vi.spyOn(api, 'generate').mockRejectedValue(new Error('HTTP 503 détail synthétique'));
    const take = { id: 42, kind: 'object', status: 'done', settings: JSON.stringify({ seed: 1071, prompt: 'test' }) } as unknown as Take;

    await recreate(take, { langue });

    expect(toast).toHaveBeenCalledWith(message, true);
    expect(vi.mocked(toast).mock.calls.flat().join(' ')).not.toContain('HTTP 503');
    generate.mockRestore();
  });

  it('conserve les messages historiques des autres usages sans langue Mesh', async () => {
    const generate = vi.spyOn(api, 'generate').mockRejectedValue(new Error('legacy detail'));
    const take = { id: 42, kind: 'still', status: 'done', settings: JSON.stringify({ seed: 1071, prompt: 'test' }) } as unknown as Take;

    await recreate(take);

    expect(toast).toHaveBeenCalledWith('legacy detail', true);
    generate.mockRestore();
  });
});
