import { describe, expect, it, vi } from 'vitest';
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
import Viewer from './Viewer';

function view() { return renderToStaticMarkup(<Viewer takeId={42} onClose={() => {}} onStep={() => {}} />); }

describe('actions Viewer et routes Nexora actives', () => {
  it('retire les actions sans outil et préserve les autres actions d’image', () => {
    fixture.take = { id: 42, kind: 'still', status: 'done', settings: '{}' };
    const html = view();
    expect(html).not.toContain('>Speak<');
    expect(html).not.toContain('Use as Stage look frame');
    expect(html).not.toContain('>Add effect<');
    expect(html).toContain('>Make 3D<');
    expect(html).toContain('>Animate<');
    expect(html).toContain('>Remove background<');
    expect(html).toContain('>As end frame<');
  });
  it('préserve Source still et retire le lien Stage pour un objet', () => {
    fixture.take = { id: 42, kind: 'object', status: 'done', settings: JSON.stringify({ sourceTake: 7 }) };
    const html = view();
    expect(html).toContain('>Source still<');
    expect(html).not.toContain('Use in Stage');
    expect(html).toContain('Download GLB');
  });
});
