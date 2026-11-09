import { describe, expect, it, vi } from 'vitest';
import { renderToStaticMarkup } from 'react-dom/server';
import type { RapportMaillage } from '../api';

vi.mock('../Viewer', () => ({ recreate: vi.fn() }));
vi.mock('../store', () => ({ toast: vi.fn() }));
vi.mock('../ui', () => ({ Icon: () => null }));
import { CartesPbr, EtatAnalyseMaillage, LienExportMesh, ResumeMaillage } from './ReliefOutils';

const base: RapportMaillage = {
  sommets: 4, triangles: 4, degeneres: 0, aretesOuvertes: 0, aretesNonVariete: 0,
  composantes: 1, etanche: true, taille: [1, 1, 1], volume: 1 / 6, avertissements: [],
};

describe('cartes PBR multi-matériaux', () => {
  const cartes = [
    { nom: 'couleur', materiaux: [{ index: 1, nom: 'Rouge' }] },
    { nom: 'couleur-2', materiaux: [{ index: 2, nom: 'Bleu' }, { index: 3, nom: '' }] },
  ];
  it.each([['fr', 'Couleur 2', 'Matériaux 2 · Bleu, 3'], ['en', 'Color 2', 'Materials 2 · Bleu, 3']] as const)(
    'identifie cartes et matériaux en %s sans changer les URLs', (langue, carte, details) => {
      const html = renderToStaticMarkup(<CartesPbr cartes={cartes} takeId={42} langue={langue} />);
      expect(html).toContain('/api/nexora/relief/42/cartes/couleur"');
      expect(html).toContain('/api/nexora/relief/42/cartes/couleur-2"');
      expect(html).toContain(carte);
      expect(html).toContain(details);
    },
  );
  it('affiche une ancienne réponse sans liste de matériaux', () => {
    const html = renderToStaticMarkup(<CartesPbr cartes={[{ nom: 'couleur' }]} takeId={42} langue="en" />);
    expect(html).toContain('Color');
    expect(html).not.toContain('Material');
  });
});

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


describe('compatibilité de téléchargement OBJ', () => {
  it.each([
    ['fr', 'Télécharger le GLB original'],
    ['en', 'Download the original GLB'],
  ] as const)('désactive le téléchargement incompatible en %s tout en gardant GLB', (langue, message) => {
    const incompatibilite = { compatible: false, code: 'OBJ_UNSUPPORTED' as const };
    const obj = renderToStaticMarkup(<LienExportMesh format="obj" url="/obj?faces=500" takeId={42} compatibilite={incompatibilite} rapportRecu rapportEchoue={false} langue={langue} />);
    expect(obj).toContain(message);
    expect(obj).toContain('href="/api/nexora/relief/42/export?format=glb"');
    expect(obj).not.toContain('faces=500');
    expect(obj).not.toContain('format=obj');
    const glb = renderToStaticMarkup(<LienExportMesh format="glb" url="/glb" takeId={42} compatibilite={incompatibilite} rapportRecu rapportEchoue={false} langue={langue} />);
    expect(glb).toContain('href="/glb"');
  });
  it.each([
    ['fr', 'Compatibilité OBJ non vérifiée', 'Télécharger le GLB original'],
    ['en', 'OBJ compatibility could not be verified', 'Download the original GLB'],
  ] as const)('annonce une compatibilité absente après réception du rapport en %s', (langue, message, conseil) => {
    const html = renderToStaticMarkup(<LienExportMesh format="obj" url="/obj?faces=500" takeId={42} compatibilite={undefined} rapportRecu rapportEchoue={false} langue={langue} />);
    expect(html).toContain(message);
    expect(html).toContain(conseil);
    expect(html).toContain('href="/api/nexora/relief/42/export?format=glb"');
    expect(html).not.toContain('faces=500');
    expect(html).not.toContain('format=obj');
    expect(html).not.toContain('role="status"');
  });
  it('attend un rapport pour OBJ et autorise un objet compatible', () => {
    const props = { format: 'obj' as const, url: '/obj', takeId: 42, rapportRecu: false, rapportEchoue: false, langue: 'en' as const };
    expect(renderToStaticMarkup(<LienExportMesh {...props} compatibilite={undefined} />)).not.toContain('href=');
    expect(renderToStaticMarkup(<LienExportMesh {...props} compatibilite={{ compatible: true, code: null }} />)).toContain('href="/obj"');
  });
});
