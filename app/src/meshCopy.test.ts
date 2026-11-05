import { describe, expect, it } from 'vitest';
import { avertissementMaillage, meshCopy } from './meshCopy';

describe('copy Mesh bilingue', () => {
  it('fournit les libellés de départ FR et EN', () => {
    expect(meshCopy('fr').imageTo3d).toBe('Image → 3D');
    expect(meshCopy('en').imageTo3d).toBe('Image → 3D');
    expect(meshCopy('fr').requestFailure).toContain('Vérifie');
    expect(meshCopy('en').requestFailure).toContain('Check the source');
  });

  it('traduit les avertissements connus et masque les chaînes inconnues', () => {
    expect(avertissementMaillage('4 triangles dégénérés.', 'en')).toBe('4 degenerate triangles.');
    expect(avertissementMaillage('diagnostic technique arbitraire', 'en')).toBe(meshCopy('en').unknownWarning);
    expect(avertissementMaillage('diagnostic technique arbitraire', 'fr')).toBe(meshCopy('fr').unknownWarning);
  });
});
