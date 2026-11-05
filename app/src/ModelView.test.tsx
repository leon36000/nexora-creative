import { describe, expect, it } from 'vitest';
import { renderToStaticMarkup } from 'react-dom/server';
import { ModelViewUnavailable } from './ModelView';

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
});
