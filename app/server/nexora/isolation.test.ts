import { mkdtempSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { beforeAll, describe, expect, it } from 'vitest';

// Base SQLite jetable : jobs.ts ouvre sa base à l'import, dans OPENFIELD_DATA.
process.env.OPENFIELD_DATA = mkdtempSync(join(tmpdir(), 'nexora-isolation-'));

let jobs: typeof import('../jobs.js');
let compte: typeof import('./compte.js');
beforeAll(async () => {
  jobs = await import('../jobs.js');
  compte = await import('./compte.js');
});

const A = { organisationId: 'org-a', utilisateurId: 'ua', territoire: 'CA' };
const B = { organisationId: 'org-b', utilisateurId: 'ub', territoire: 'US' };
const prise = (nom: string) => ({ project_id: null, kind: 'video', shot_name: nom, settings: { prompt: nom } });

describe('isolation des données entre organisations', () => {
  it('une organisation ne voit, ne lit, n’étoile ni ne supprime les prises d’une autre', () => {
    const idA = compte.avecCompte(A, () => jobs.takes.create(prise('secret de A')));
    const idB = compte.avecCompte(B, () => jobs.takes.create(prise('secret de B')));
    compte.avecCompte(A, () => {
      expect(jobs.takes.list(null).map((t) => t.id)).toEqual([idA]);
      expect(jobs.takes.get(idB)).toBeUndefined();
      jobs.takes.star(idB, true);
      jobs.takes.delete(idB);
    });
    compte.avecCompte(B, () => {
      const b = jobs.takes.get(idB);
      expect(b?.shot_name).toBe('secret de B');
      expect(b?.starred).toBe(0);
      expect(jobs.takes.organisationDe(idB)).toBe('org-b');
    });
  });

  it('le moteur (hors requête) voit toutes les prises pour les terminer', () => {
    const ids = jobs.takes.active().map((t) => t.id);
    expect(ids.length).toBeGreaterThanOrEqual(2);
  });

  it('personnages et projets : même nom permis dans deux organisations, invisibles entre elles', () => {
    const ca = compte.avecCompte(A, () => jobs.cast.create({ name: 'Robot', kind: 'character', refs: [], notes: 'A' }));
    const cb = compte.avecCompte(B, () => jobs.cast.create({ name: 'Robot', kind: 'character', refs: [], notes: 'B' }));
    compte.avecCompte(A, () => {
      expect(jobs.cast.list().map((c) => c.id)).toEqual([ca]);
      expect(jobs.cast.byName('Robot')?.notes).toBe('A');
      expect(jobs.cast.get(cb)).toBeUndefined();
    });
    const pa = compte.avecCompte(A, () => jobs.projects.create('Pub', '/tmp/a'));
    compte.avecCompte(B, () => {
      jobs.projects.create('Pub', '/tmp/b');
      expect(jobs.projects.get(pa)).toBeUndefined();
      expect((jobs.projects.list() as { name: string }[]).length).toBe(1);
    });
  });
});
