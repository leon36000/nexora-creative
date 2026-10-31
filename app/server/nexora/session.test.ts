import { describe, expect, it } from 'vitest';
import { lireSession, signerSession } from './session.js';

const SECRET = 'un-secret-de-test-assez-long-pour-hmac-sha256-0123456789';
const charge = { o: 'org-a', u: 'user-1', t: 'CA' as string | null, e: 2_000_000_000_000 };

describe('témoin de session signé', () => {
  it('relit une session valide', () => {
    expect(lireSession(signerSession(charge, SECRET), SECRET, 1_900_000_000_000)).toEqual(charge);
  });

  it('refuse une session expirée, falsifiée, signée avec un autre secret ou mal formée', () => {
    const v = signerSession(charge, SECRET);
    expect(lireSession(v, SECRET, 2_000_000_000_001)).toBeNull();
    const [corps, sig] = v.split('.');
    const autre = Buffer.from(JSON.stringify({ ...charge, o: 'org-b' })).toString('base64url');
    expect(lireSession(`${autre}.${sig}`, SECRET, 0)).toBeNull();
    expect(lireSession(`${corps}.${sig.slice(0, -2)}xx`, SECRET, 0)).toBeNull();
    expect(lireSession(v, `${SECRET}-autre`, 0)).toBeNull();
    for (const x of ['', 'abc', 'a.b.c', '.', `${corps}.`]) expect(lireSession(x, SECRET, 0)).toBeNull();
  });

  it('exige un secret d’au moins 32 caractères', () => {
    expect(() => signerSession(charge, 'court')).toThrow(/32/);
  });
});
