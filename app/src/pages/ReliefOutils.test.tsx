import { describe, expect, it, vi } from 'vitest';
import { renderToStaticMarkup } from 'react-dom/server';
import type { RapportMaillage } from '../api';

vi.mock('../Viewer', () => ({ recreate: vi.fn() }));
vi.mock('../store', () => ({ toast: vi.fn() }));
vi.mock('../ui', () => ({ Icon: () => null }));
import { ResumeMaillage } from './ReliefOutils';

const base: RapportMaillage = {
  sommets: 4, triangles: 4, degeneres: 0, aretesOuvertes: 0, aretesNonVariete: 0,
  composantes: 1, etanche: true, taille: [1, 1, 1], volume: 1 / 6, avertissements: [],
};

describe('rapport du maillage', () => {
  it('décrit les arêtes fermées sans promettre une impression prête', () => {
    const html = renderToStaticMarkup(<ResumeMaillage r={base} />);
    expect(html).toContain('Arêtes fermées');
    expect(html).not.toContain('prêt à imprimer');
  });
  it('signale une orientation incohérente sans indicateur de succès', () => {
    const r = { ...base, volume: null, avertissements: ['Volume non calculé : orientation incohérente des faces.'] };
    const html = renderToStaticMarkup(<ResumeMaillage r={r} />);
    expect(html).toContain('orientation incohérente');
    expect(html).not.toContain('--ok');
  });
});
