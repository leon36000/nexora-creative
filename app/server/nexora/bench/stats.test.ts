import { describe, expect, it } from 'vitest';
import { BRIEFS } from './briefs.js';
import { compareApparie, icMoyenne } from './stats.js';

describe('banc : statistiques et briefs', () => {
  it('12 briefs : 6 apprentissage, 3 validation, 3 test, 4 genres × 3', () => {
    const c = (f: (b: (typeof BRIEFS)[number]) => string) => BRIEFS.reduce<Record<string, number>>((m, b) => ({ ...m, [f(b)]: (m[f(b)] ?? 0) + 1 }), {});
    expect(c((b) => b.partition)).toEqual({ apprentissage: 6, validation: 3, test: 3 });
    expect(c((b) => b.genre)).toEqual({ pub: 3, 'bande-annonce': 3, explicatif: 3, social: 3 });
    expect(new Set(BRIEFS.map((b) => b.id)).size).toBe(12);
  });
  it('comparaison appariée : un gain net a un IC strictement positif, un bruit centré non', () => {
    const a: Record<string, number[]> = {}, b: Record<string, number[]> = {}, c: Record<string, number[]> = {};
    for (let i = 0; i < 12; i++) { a[`x${i}`] = [0.5, 0.52, 0.48]; b[`x${i}`] = [0.7 + (i % 3) * 0.01, 0.71, 0.69]; c[`x${i}`] = [0.5 + (i % 2 ? 0.05 : -0.05), 0.5, 0.5]; }
    const gain = compareApparie(a, b);
    expect(gain.delta).toBeGreaterThan(0.19); expect(gain.ic95[0]).toBeGreaterThan(0.15);
    const bruit = compareApparie(a, c);
    expect(bruit.ic95[0]).toBeLessThan(0.02); expect(bruit.ic95[1]).toBeGreaterThan(-0.02);
    expect(icMoyenne(a)[0]).toBeCloseTo(0.5);
  });
});
