import { describe, expect, it, vi } from 'vitest';
import { bundlesFor } from '../models.js';
import { verdictLicence } from './licences.js';
import { choisirMoteur, corpsRendu, corpsRenduH3, entreeRealisateurCreation, lireDemandeCreer } from './creer.js';

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

  it('transmet la langue choisie au réalisateur, et omet le champ historique si absent', () => {
    const anglais = lireDemandeCreer({ intention: 'A dragon lands', langueClient: 'en', langueReplique: 'en', replique: 'Here we go.' });
    expect(anglais.langueClient).toBe('en');
    expect(entreeRealisateurCreation(anglais, { moteur: 'h3-fast' })).toMatchObject({
      langueClient: 'en', mode: 't2va', dialogues: [{ texte: 'Here we go.', langue: 'English' }],
    });

    const historique = lireDemandeCreer({ intention: 'Un dragon atterrit', replique: 'On y va.' });
    expect(historique).not.toHaveProperty('langueClient');
    expect(entreeRealisateurCreation(historique, { moteur: 'h3-fast' })).toMatchObject({
      mode: 't2va', dialogues: [{ texte: 'On y va.', langue: 'French' }],
    });
    expect(entreeRealisateurCreation(historique, { moteur: 'h3-fast' })).not.toHaveProperty('langueClient');

    const interfaceAnglaiseRepliqueFrancaise = lireDemandeCreer({ intention: 'A dragon lands', langueClient: 'en', langueReplique: 'fr', replique: 'Bonjour.' });
    expect(entreeRealisateurCreation(interfaceAnglaiseRepliqueFrancaise, { moteur: 'h3-fast' })).toMatchObject({
      langueClient: 'en', dialogues: [{ texte: 'Bonjour.', langue: 'French' }],
    });
  });

  it('traduit les erreurs de saisie uniquement quand une langue est choisie', () => {
    expect(() => lireDemandeCreer({ intention: '', langueClient: 'en' })).toThrow('Describe the video you want in one sentence or more.');
    expect(() => lireDemandeCreer({ intention: 'x'.repeat(4001), langueClient: 'en' })).toThrow('Description is too long (4,000 characters maximum).');
    expect(() => lireDemandeCreer({ intention: '' })).toThrow('Décris la vidéo que tu veux en une phrase ou plus.');
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

describe('choix du moteur : MiniMax H3 seul, selon la licence, le territoire et la qualité', () => {
  const parc = new Set(['h3-fast', 'h3-max']);
  it('H3 au Canada ; rien dans les territoires exclus ou inconnus (échec fermé, pas de repli)', () => {
    expect(choisirMoteur('CA')).toBe('h3-fast');
    expect(choisirMoteur('US')).toBeNull();
    expect(choisirMoteur('FR')).toBeNull();
    expect(choisirMoteur(null)).toBeNull();
  });

  it('« max » va au moteur cinéma s’il est dans le parc, sinon FastH3 à pleine résolution', () => {
    expect(choisirMoteur('CA', undefined, 'max', parc)).toBe('h3-max');
    expect(choisirMoteur('CA', undefined, 'rapide', parc)).toBe('h3-fast');
    expect(choisirMoteur('CA', undefined, 'max', new Set(['h3-fast']))).toBe('h3-fast');
    expect(choisirMoteur('US', undefined, 'max', parc)).toBeNull();
  });

  it('le moteur cinéma rend en 1344×768 avec son point de contrôle et ses étapes', () => {
    const c = corpsRendu({ intention: 'renard', format: '16:9', duree: 5, son: true, qualite: 'rapide' }, 'P', 'h3-max');
    expect(c).toMatchObject({ videoModel: 'h3-max', width: 1344, height: 768, withAudio: true, steps: 8, refMode: true });
    expect(c.checkpoint).toBe('10Eros_Max_h3_8stepTURBO_beta7_SingularityV2_ref2va_int8HQ.safetensors');
    expect(corpsRendu({ intention: 'renard', format: '16:9', duree: 5, son: true }, 'P', 'h3-fast')).toMatchObject({ videoModel: 'h3-fast', withAudio: true, steps: 8 });
  });
});

describe('partir d’une photo (image vers vidéo)', () => {
  const jeton = 'asset:0123abcd-0123-4567-89ab-0123456789ab';
  it('accepte seulement un jeton d’entrée du moteur', () => {
    expect(lireDemandeCreer({ intention: 'a', image: jeton }).image).toBe(jeton);
    expect(lireDemandeCreer({ intention: 'a', image: '../../etc/passwd' }).image).toBeUndefined();
    expect(lireDemandeCreer({ intention: 'a', image: 'asset:x' }).image).toBeUndefined();
  });

  it('conserve le checkpoint FL2VA et les étapes configurés pour une photo max', () => {
    vi.stubEnv('NEXORA_H3_MAX_CHECKPOINT', 'minimax_h3_fl2va_pruned_fp8_scaled.safetensors');
    vi.stubEnv('NEXORA_H3_MAX_ETAPES', '20');
    try {
      const d = lireDemandeCreer({ intention: 'ma voiture', image: jeton, qualite: 'max' });
      const c = corpsRendu(d, 'P', 'h3-max');
      expect(c).toMatchObject({ checkpoint: 'minimax_h3_fl2va_pruned_fp8_scaled.safetensors', steps: 20, videoModel: 'h3-max', width: 1344, height: 768, startImage: jeton });
      expect(c).not.toHaveProperty('refMode');
    } finally {
      vi.unstubAllEnvs();
    }
  });

  it('passe la photo en première image, sur les deux moteurs H3', () => {
    const d = lireDemandeCreer({ intention: 'ma voiture', image: jeton });
    expect(corpsRendu(d, 'P', 'h3-fast')).toMatchObject({ startImage: jeton });
    expect(corpsRendu(d, 'P', 'h3-max')).toMatchObject({ startImage: jeton, checkpoint: 'fastvideo_fasth3_8step_v2_pruned_nvfp4.safetensors', width: 1344, height: 768 });
    expect(corpsRendu(d, 'P', 'h3-max')).not.toHaveProperty('refMode');
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


describe('mouvement de caméra choisi en un clic', () => {
  it('est lu, borné, et ajouté à l’intention envoyée au réécrivain H3', async () => {
    const { lireDemandeCreer, intentionAvecCamera } = await import('./creer.js');
    const d = lireDemandeCreer({ intention: 'Un café fume', camera: 'The camera pushes in slowly.' + 'x'.repeat(400) });
    expect(d.camera?.length).toBe(300);
    expect(intentionAvecCamera(lireDemandeCreer({ intention: 'Un café fume', camera: 'The camera pushes in.' }))).toBe('Un café fume\nCamera movement: The camera pushes in.');
    expect(intentionAvecCamera(lireDemandeCreer({ intention: 'Un café fume' }))).toBe('Un café fume');
  });
});
