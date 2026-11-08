import { describe, expect, it, vi } from 'vitest';
import { renderToStaticMarkup } from 'react-dom/server';

vi.mock('./drop', () => ({ useDropZone: () => ({ over: false, props: {} }) }));
vi.mock('./pages/Mirror', () => ({ DropWell: ({ title, sub }: { title: string; sub: string }) => <div><span>{title}</span><span>{sub}</span></div> }));
vi.mock('./store', () => ({ isImage: () => false, isModel: () => false, settingsOf: () => ({}), toast: vi.fn(), useStore: (select: (s: any) => unknown) => select({ takes: [] }) }));
vi.mock('./api', () => ({ mediaUrl: () => '', posterUrl: () => '', takeAsInput: vi.fn(), uploadFile: vi.fn() }));
vi.mock('./ui', () => ({ Icon: () => null }));

import { SourceSlot } from './SourcePick';

describe('SourceSlot Mesh', () => {
  const props = { label: 'Image', value: null, onChange: () => {}, accept: ['image' as const], title: 'Add a still', sub: 'One subject' };

  it('localise les libellés FR et EN', () => {
    const fr = renderToStaticMarkup(<SourceSlot {...props} langue="fr" />);
    const en = renderToStaticMarkup(<SourceSlot {...props} langue="en" />);
    expect(fr).toContain('Image');
    expect(en).toContain('Add a still');
  });

  it('garde les libellés historiques quand aucune langue n’est fournie', () => {
    const html = renderToStaticMarkup(<SourceSlot {...props} />);
    expect(html).toContain('Add a still');
    expect(html).not.toContain('Ajouter une image');
  });

  it('localise le bouton de retrait et préserve son aria-label historique', () => {
    const value = { token: 't', kind: 'image' as const, url: '/image.png', name: 'photo', w: 100, h: 100, seconds: 0 };
    const fr = renderToStaticMarkup(<SourceSlot {...props} value={value} langue="fr" />);
    const en = renderToStaticMarkup(<SourceSlot {...props} value={value} langue="en" />);
    const legacy = renderToStaticMarkup(<SourceSlot {...props} value={value} />);
    expect(fr).toContain('aria-label="Retirer la source"');
    expect(en).toContain('aria-label="Remove source"');
    expect(legacy).toContain('aria-label="remove"');
  });
});
