import { describe, expect, it } from 'vitest';
import { bundlesFor } from '../models.js';
import { verdictLicence } from './licences.js';
import { choisirMoteur, corpsRendu, corpsRenduH3, lireDemandeCreer } from './creer.js';

describe('demande « Créer » (parcours simple)', () => {
  it('valide et complète la demande', () => {
    expect(lireDemandeCreer({ intention: '  un chat astronaute  ' })).toEqual({
      intention: 'un chat astronaute', format: '16:9', duree: 5, son: true, qualite: 'rapide',
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

describe('choix du moteur selon la licence et le territoire', () => {
  it('prend H3 au Canada et Wan 2.2 dans les territoires exclus par H3 ou inconnus', () => {
    expect(choisirMoteur('CA')).toBe('h3-fast');
    expect(choisirMoteur('US')).toBe('wan22');
    expect(choisirMoteur('FR')).toBe('wan22');
    expect(choisirMoteur(null)).toBe('wan22');
  });

  it('prépare un rendu Wan sans son, sur sa grille 4n+1, avec un prompt descriptif', () => {
    const h3 = 'integrated_multimodal_description: [Shot 1] Cinematic, a fox runs.\n\noverall_soundscape: wind.\n\nnon_diegetic_music: N/A';
    const c = corpsRendu({ intention: 'renard', format: '16:9', duree: 5, son: true }, h3, 'wan22');
    expect(c).toMatchObject({ kind: 'video', videoModel: 'wan22', withAudio: false, frames: 121, width: 832, height: 480 });
    expect(c.prompt).toBe('Cinematic, a fox runs.');
    expect(corpsRendu({ intention: 'renard', format: '16:9', duree: 5, son: true }, h3, 'h3-fast')).toMatchObject({ videoModel: 'h3-fast', withAudio: true });
  });
});

describe('partir d’une photo (image vers vidéo)', () => {
  const jeton = 'asset:0123abcd-0123-4567-89ab-0123456789ab';
  it('accepte seulement un jeton d’entrée du moteur', () => {
    expect(lireDemandeCreer({ intention: 'a', image: jeton }).image).toBe(jeton);
    expect(lireDemandeCreer({ intention: 'a', image: '../../etc/passwd' }).image).toBeUndefined();
    expect(lireDemandeCreer({ intention: 'a', image: 'asset:x' }).image).toBeUndefined();
  });

  it('passe la photo en première image, pour H3 comme pour Wan', () => {
    const d = lireDemandeCreer({ intention: 'ma voiture', image: jeton });
    expect(corpsRendu(d, 'P', 'h3-fast')).toMatchObject({ startImage: jeton });
    expect(corpsRendu(d, 'integrated_multimodal_description: [Shot 1] x', 'wan22')).toMatchObject({ startImage: jeton });
    expect(corpsRendu(lireDemandeCreer({ intention: 'b' }), 'P', 'h3-fast')).not.toHaveProperty('startImage');
  });
});

describe('profils Rapide et Qualité maximale', () => {
  it('Rapide par défaut (832×480), Qualité en résolution native de H3 (1344×768), multiples de 32', () => {
    expect(lireDemandeCreer({ intention: 'a' }).qualite).toBe('rapide');
    const q = lireDemandeCreer({ intention: 'a', qualite: 'max' });
    expect(q.qualite).toBe('max');
    expect(corpsRendu(q, 'P', 'h3-fast')).toMatchObject({ width: 1344, height: 768 });
    expect(corpsRendu({ ...q, format: '9:16' }, 'P', 'h3-fast')).toMatchObject({ width: 768, height: 1344 });
    expect(corpsRendu({ ...q, format: '1:1' }, 'P', 'h3-fast')).toMatchObject({ width: 1024, height: 1024 });
    expect(corpsRendu(lireDemandeCreer({ intention: 'a' }), 'P', 'h3-fast')).toMatchObject({ width: 832, height: 480 });
  });
});

