import { describe, expect, it } from 'vitest';
import { bundlesFor } from '../models.js';
import { verdictLicence } from './licences.js';
import { corpsRenduH3, lireDemandeCreer } from './creer.js';

describe('demande « Créer » (parcours simple)', () => {
  it('valide et complète la demande', () => {
    expect(lireDemandeCreer({ intention: '  un chat astronaute  ' })).toEqual({
      intention: 'un chat astronaute', format: '16:9', duree: 5, son: true,
    });
    expect(() => lireDemandeCreer({ intention: '' })).toThrow(/Décris/);
    expect(() => lireDemandeCreer({ intention: 'x'.repeat(4001) })).toThrow(/long/);
    expect(lireDemandeCreer({ intention: 'a', format: '9:16', duree: 10, son: false })).toMatchObject({ format: '9:16', duree: 10, son: false });
    expect(lireDemandeCreer({ intention: 'a', format: '4:3', duree: 7 })).toMatchObject({ format: '16:9', duree: 5 });
  });

  it('produit un rendu FastH3 sur la grille d’images de H3, en multiples de 32', () => {
    for (const format of ['16:9', '9:16', '1:1'] as const) {
      for (const duree of [5, 10, 15] as const) {
        const c = corpsRenduH3({ intention: 'a', format, duree, son: true }, 'PROMPT');
        expect((c.lengthFrames - 124) % 17).toBe(0);
        expect(c.lengthFrames / 24).toBeGreaterThanOrEqual(duree - 0.25);
        expect(c.lengthFrames).toBeLessThanOrEqual(362);
        expect(c.width % 32).toBe(0);
        expect(c.height % 32).toBe(0);
        expect(c).toMatchObject({ kind: 'video', videoModel: 'h3-fast', prompt: 'PROMPT', withAudio: true, steps: 8 });
      }
    }
    expect(corpsRenduH3({ intention: 'a', format: '9:16', duree: 5, son: false }, 'P')).toMatchObject({ width: 480, height: 832 });
  });

  it('demande l’ensemble FastH3, soumis à la règle de territoire H3', () => {
    expect(bundlesFor({ kind: 'video', videoModel: 'h3-fast' })).toEqual(['h3-fast']);
    expect(verdictLicence('h3-fast', 'CA').statut).toBe('permis');
    expect(verdictLicence('h3-fast', 'US').statut).toBe('territoire_exclu');
  });
});
