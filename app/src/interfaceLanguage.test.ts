import { describe, expect, it } from 'vitest';
import {
  LANGUE_INTERFACE_CLE, enregistrerLangueInterface, lireLangueInterface, libellesNavigation,
  nomAppNavigation, attributLangueDocument, langueContenuPrincipal,
} from './interfaceLanguage';

function stockageTest(initial: Record<string, string> = {}) {
  const values = new Map(Object.entries(initial));
  return {
    getItem: (key: string) => values.get(key) ?? null,
    setItem: (key: string, value: string) => { values.set(key, value); },
  };
}

describe('langue partagée de l’interface', () => {
  it('utilise le français par défaut et restaure seulement une valeur persistée reconnue', () => {
    expect(lireLangueInterface(stockageTest())).toBe('fr');
    expect(lireLangueInterface(stockageTest({ [LANGUE_INTERFACE_CLE]: 'en' }))).toBe('en');
    expect(lireLangueInterface(stockageTest({ [LANGUE_INTERFACE_CLE]: 'fr-CA' }))).toBe('fr');
  });

  it('persiste le choix sans changer les noms canoniques des produits', () => {
    const storage = stockageTest();
    enregistrerLangueInterface('en', storage);
    expect(lireLangueInterface(storage)).toBe('en');
    expect(nomAppNavigation('prolonger', 'Prolonger', 'en')).toBe('Extend');
    expect(nomAppNavigation('object', 'Nexora Mesh', 'en')).toBe('Nexora Mesh');
    expect(nomAppNavigation('detourage', 'Nexora Matte', 'en')).toBe('Nexora Matte');
  });

  it('retombe sur le français si localStorage.getItem échoue', () => {
    const storage = {
      getItem: () => { throw new Error('storage unavailable'); },
      setItem: () => {},
    };
    expect(lireLangueInterface(storage)).toBe('fr');
  });

  it('garde l’interface utilisable si localStorage.setItem échoue', () => {
    const storage = {
      getItem: () => null,
      setItem: () => { throw new Error('storage unavailable'); },
    };
    expect(() => enregistrerLangueInterface('en', storage)).not.toThrow();
  });

  it('fournit des libellés et un attribut de document cohérents pour FR/EN', () => {
    expect(libellesNavigation('fr').navLabel).toBe('Navigation principale');
    expect(libellesNavigation('en').navLabel).toBe('Main navigation');
    expect(attributLangueDocument('fr')).toBe('fr-CA');
    expect(attributLangueDocument('en')).toBe('en-CA');
    expect(langueContenuPrincipal('/mesh', 'en')).toBe('en');
    expect(langueContenuPrincipal('/object', 'en')).toBe('en');
    expect(langueContenuPrincipal('/relief', 'en')).toBe('en');
    expect(langueContenuPrincipal('/library', 'en')).toBe('fr');
  });
});
