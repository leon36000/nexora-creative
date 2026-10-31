import { describe, expect, it } from 'vitest';
import { MANIFESTES, Manifeste, planifierMoteurs } from './registre.js';

describe('registre de capacités', () => {
  it('chaque manifeste est valide, avec licence et ensembles de modèles déclarés', () => {
    for (const m of MANIFESTES) expect(() => Manifeste.parse(m), m.id).not.toThrow();
    expect(MANIFESTES.map((m) => m.id).sort()).toEqual(['minimax/fasth3-v2-nvfp4', 'wan/2.2-ti2v-5b']);
  });

  it('refuse un manifeste incomplet (licence absente)', () => {
    const { licence: _l, ...sans } = MANIFESTES[0] as Record<string, unknown>;
    expect(() => Manifeste.parse(sans)).toThrow();
  });
});

describe('planificateur : filtres durs, puis classement', () => {
  const base = { tache: 't2v' as const, dureeS: 5, son: true };

  it('au Canada, H3 passe devant Wan (qualité, son natif)', () => {
    const r = planifierMoteurs(base, { territoire: 'CA' });
    expect(r.retenus.map((m) => m.id)).toEqual(['minimax/fasth3-v2-nvfp4', 'wan/2.2-ti2v-5b']);
  });

  it('aux États-Unis, H3 est exclu par sa licence, avec la raison', () => {
    const r = planifierMoteurs(base, { territoire: 'US' });
    expect(r.retenus.map((m) => m.id)).toEqual(['wan/2.2-ti2v-5b']);
    expect(r.exclus.find((e) => e.id === 'minimax/fasth3-v2-nvfp4')?.raison).toMatch(/territoire/);
  });

  it('une tâche non prise en charge exclut le moteur', () => {
    const r = planifierMoteurs({ ...base, tache: 'r2v' }, { territoire: 'CA' });
    expect(r.retenus).toEqual([]);
    expect(r.exclus.every((e) => /tâche/.test(e.raison))).toBe(true);
  });

  it('une durée hors limites exclut le moteur', () => {
    const r = planifierMoteurs({ ...base, dureeS: 20 }, { territoire: 'CA' });
    expect(r.retenus.map((m) => m.id)).not.toContain('minimax/fasth3-v2-nvfp4');
  });

  it('un ensemble de modèles absent du moteur exclut le manifeste', () => {
    const r = planifierMoteurs(base, { territoire: 'CA', ensemblesPrets: new Set(['wan22']) });
    expect(r.retenus.map((m) => m.id)).toEqual(['wan/2.2-ti2v-5b']);
    expect(r.exclus[0].raison).toMatch(/installé/);
  });
});
