import { describe, expect, it } from 'vitest';
import { BUNDLES } from '../models.js';
import { refusLicence, verdictLicence } from './licences.js';

describe('politique de licences Nexora', () => {
  it('bloque LTX et tout ce qui en dérive (clause de produit concurrent)', () => {
    for (const id of ['ltx25', 'ltx23', 'dream', 'mirror', 'reshoot', 'effects', 'effects-community', 'cast', 'ltx-tools', 'hdr', 'swap', 'stage']) {
      expect(verdictLicence(id, 'CA').statut, id).toBe('bloque');
    }
  });

  it('bloque les modèles non commerciaux', () => {
    expect(verdictLicence('flux2', 'CA').statut).toBe('bloque');
    expect(verdictLicence('upres-ultrasharp', 'CA').statut).toBe('bloque');
  });

  it('permet H3 au Canada et le refuse dans les territoires exclus par sa licence', () => {
    for (const id of ['h3', 'h3-refs', 'h3-turbo']) {
      expect(verdictLicence(id, 'CA').statut).toBe('permis');
      for (const pays of ['US', 'GB', 'KR', 'FR', 'DE', 'IE']) {
        expect(verdictLicence(id, pays).statut, `${id} ${pays}`).toBe('territoire_exclu');
      }
    }
  });

  it('refuse H3 quand le territoire du compte est inconnu (échec fermé)', () => {
    expect(verdictLicence('h3', null).statut).toBe('territoire_exclu');
    expect(verdictLicence('h3', 'zz').statut).toBe('territoire_exclu');
  });

  it('refuse un ensemble inconnu (échec fermé)', () => {
    expect(verdictLicence('inconnu', 'CA').statut).toBe('bloque');
  });

  it('classe chaque ensemble d’OpenField, sans oubli', () => {
    for (const b of BUNDLES) expect(() => verdictLicence(b.id, 'CA')).not.toThrow();
    const permis = BUNDLES.filter((b) => verdictLicence(b.id, 'CA').statut === 'permis').map((b) => b.id).sort();
    expect(permis).toEqual(['cutout', 'edit', 'h3', 'h3-fast', 'h3-refs', 'h3-turbo', 'qwen', 'sam3', 'seedvr2', 'stage-look', 'trellis2', 'upres'].sort());
  });

  it('donne une phrase en français qui nomme la raison, ou null', () => {
    expect(refusLicence(['qwen', 'h3'], 'CA')).toBeNull();
    expect(refusLicence(['h3'], 'US')).toMatch(/MiniMax H3/);
    expect(refusLicence(['ltx25'], 'CA')).toMatch(/LTX/);
  });
});

describe('territoire du compte', () => {
  it('lit le compte de la requête avant la valeur du poste', async () => {
    const { avecCompte, territoireDuCompte } = await import('./compte.js');
    process.env.NEXORA_TERRITOIRE = 'CA';
    expect(territoireDuCompte()).toBe('CA');
    avecCompte({ organisationId: 'o', utilisateurId: 'u', territoire: 'US' }, () => {
      expect(territoireDuCompte()).toBe('US');
      expect(refusLicence(['h3'], territoireDuCompte())).toMatch(/MiniMax H3/);
    });
    delete process.env.NEXORA_TERRITOIRE;
    expect(territoireDuCompte()).toBeNull();
  });
});

describe('Qwen-Image-2.1 : licence de recherche, réservée au mode démonstration', () => {
  it('est bloqué par défaut, permis seulement avec NEXORA_MODE_DEMO=1, et jamais sans règle', () => {
    const avant = process.env.NEXORA_MODE_DEMO;
    try {
      delete process.env.NEXORA_MODE_DEMO;
      expect(verdictLicence('qwen21', 'CA').statut).toBe('bloque');
      expect(verdictLicence('qwen21', 'CA').raison).toMatch(/licence de recherche/);
      process.env.NEXORA_MODE_DEMO = '1';
      expect(verdictLicence('qwen21', 'CA').statut).toBe('permis');
      process.env.NEXORA_MODE_DEMO = 'oui';
      expect(verdictLicence('qwen21', 'CA').statut).toBe('bloque');
    } finally {
      if (avant === undefined) delete process.env.NEXORA_MODE_DEMO; else process.env.NEXORA_MODE_DEMO = avant;
    }
  });
});
