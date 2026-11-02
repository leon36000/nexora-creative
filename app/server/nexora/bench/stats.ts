/** Statistiques du banc : comparaison appariée par brief, IC à 95 % par bootstrap groupé par brief (graine fixe). */
export function moyenne(x: number[]): number { return x.length ? x.reduce((s, v) => s + v, 0) / x.length : 0; }

function prng(graine: number) {
  let a = graine >>> 0;
  return () => { a = (a + 0x6d2b79f5) >>> 0; let t = a; t = Math.imul(t ^ (t >>> 15), t | 1); t ^= t + Math.imul(t ^ (t >>> 7), t | 61); return ((t ^ (t >>> 14)) >>> 0) / 4294967296; };
}

export interface Paire { delta: number; ic95: [number, number]; n: number; p_positif: number }

/**
 * `a` et `b` : brief → scores des répétitions. Différence B − A moyennée par brief (appariement), puis bootstrap sur les
 * BRIEFS (unité d'échantillonnage) ; la part de rééchantillons où le gain est > 0 sert de p unilatéral approché.
 */
export function compareApparie(a: Record<string, number[]>, b: Record<string, number[]>, iterations = 5000, graine = 7): Paire {
  const ids = Object.keys(a).filter((k) => b[k]?.length && a[k]?.length);
  const d = ids.map((k) => moyenne(b[k]) - moyenne(a[k]));
  const r = prng(graine);
  const m: number[] = [];
  for (let i = 0; i < iterations; i++) { let s = 0; for (let j = 0; j < d.length; j++) s += d[Math.floor(r() * d.length)]; m.push(s / d.length); }
  m.sort((x, y) => x - y);
  return { delta: moyenne(d), ic95: [m[Math.floor(iterations * 0.025)] ?? 0, m[Math.floor(iterations * 0.975)] ?? 0], n: ids.length, p_positif: m.filter((v) => v > 0).length / iterations };
}

/** IC95 bootstrap de la moyenne d'un bras (moyennes par brief). */
export function icMoyenne(par: Record<string, number[]>, iterations = 5000, graine = 11): [number, number, number] {
  const v = Object.values(par).map(moyenne);
  const r = prng(graine);
  const m: number[] = [];
  for (let i = 0; i < iterations; i++) { let s = 0; for (let j = 0; j < v.length; j++) s += v[Math.floor(r() * v.length)]; m.push(s / v.length); }
  m.sort((x, y) => x - y);
  return [moyenne(v), m[Math.floor(iterations * 0.025)] ?? 0, m[Math.floor(iterations * 0.975)] ?? 0];
}
