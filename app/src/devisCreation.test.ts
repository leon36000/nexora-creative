import { describe, expect, it } from 'vitest';
import { cleDevisCreation, ControleDevis } from './devisCreation';

describe('identité du devis', () => {
  it('rend un devis précédent immédiatement périmé après changement de photo ou qualité', () => {
    const key = cleDevisCreation('video', '16:9', 5, true, 'max', undefined, 'fr');
    expect(cleDevisCreation('video', '16:9', 5, true, 'max', 'new-photo', 'fr')).not.toBe(key);
    expect(cleDevisCreation('video', '16:9', 5, true, 'rapide', undefined, 'fr')).not.toBe(key);
  });
  it('ignore une ancienne réponse après changement puis retour au réglage initial', () => {
    const c = new ControleDevis();
    const premiere = c.jeton();
    c.invalider();
    c.invalider();
    expect(c.accepte(premiere)).toBe(false);
    expect(c.accepte(c.jeton())).toBe(true);
  });
});
