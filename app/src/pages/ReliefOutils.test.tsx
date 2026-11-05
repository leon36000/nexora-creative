import { describe, expect, it, vi } from 'vitest';
import { renderToStaticMarkup } from 'react-dom/server';
import type { RapportMaillage } from '../api';

vi.mock('../Viewer', () => ({ recreate: vi.fn() }));
vi.mock('../store', () => ({ toast: vi.fn() }));
vi.mock('../ui', () => ({ Icon: () => null }));
import { EtatAnalyseMaillage, ResumeMaillage } from './ReliefOutils';

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
  it('rend le rapport de topologie dans les deux langues', () => {
    const r = { ...base, aretesOuvertes: 3, etanche: false, avertissements: ['3 arêtes ouvertes : le modèle n’est pas étanche (impression 3D : à réparer).'] };
    const fr = renderToStaticMarkup(<ResumeMaillage r={r} langue="fr" />);
    const en = renderToStaticMarkup(<ResumeMaillage r={r} langue="en" />);
    expect(fr).toContain('3 arêtes ouvertes');
    expect(en).toContain('3 open edges');
    expect(en).toContain('vertices');
    expect(en).not.toContain('arêtes');
  });
  it.each([
    ['fr', 'L’analyse n’a pas abouti', 'Internal Server Error'],
    ['en', 'The analysis did not finish', 'Maillage invalide'],
  ] as const)('affiche un état d’échec localisé sans détail serveur (%s)', (langue, message, detail) => {
    const html = renderToStaticMarkup(<EtatAnalyseMaillage rapport={null} loading={false} failed langue={langue} />);
    expect(html).toContain(message);
    expect(html).not.toContain(detail);
  });
  it('affiche clairement l’état de chargement', () => {
    const html = renderToStaticMarkup(<EtatAnalyseMaillage rapport={null} loading failed={false} langue="en" />);
    expect(html).toContain('Analyzing the mesh');
    expect(html).toContain('role="status"');
  });
});
