import { describe, expect, it } from 'vitest';
import { renderToStaticMarkup } from 'react-dom/server';
import ModelView, { ModelViewUnavailable } from './ModelView';

describe('message d’indisponibilité du visualiseur de modèle', () => {
  it.each([
    ['fr', 'Ce navigateur ne peut pas afficher le modèle. Télécharge le GLB pour l’ouvrir ailleurs.'],
    ['en', 'This browser could not show the model. Download the GLB to open it elsewhere.'],
  ] as const)('affiche un message localisé sans détail technique en %s', (langue, message) => {
    const html = renderToStaticMarkup(<ModelViewUnavailable langue={langue} />);
    expect(html).toContain(message);
    expect(html).not.toContain('HTTP');
  });

  it('garde le texte anglais historique pour les autres usages sans langue', () => {
    expect(renderToStaticMarkup(<ModelViewUnavailable />)).toContain('This browser could not show the model. Download the GLB to open it elsewhere.');
  });

  it.each([
    ['fr', 'Aperçu 3D du modèle', 'Chargement du modèle…'],
    ['en', '3D model preview', 'Loading the model…'],
  ] as const)('localise le titre et l’état de chargement (%s)', (langue, label, message) => {
    const html = renderToStaticMarkup(<ModelView src="/modele.glb" langue={langue} />);
    expect(html).toContain(`aria-label="${label}"`);
    expect(html).toContain(`role="status"`);
    expect(html).toContain(message);
  });

  it('garde l’état de chargement anglais historique sans langue', () => {
    const html = renderToStaticMarkup(<ModelView src="/model.glb" />);
    expect(html).not.toContain('aria-label="3D model preview"');
    expect(html).toContain('Loading the model...');
  });
});
