import { describe, expect, it, vi } from 'vitest';
import { createHash } from 'node:crypto';
import { mkdtempSync, readFileSync, writeFileSync } from 'node:fs';
import { join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { comparerAmd2 } from './appariementAmd2.js';
import * as statistiques from './stats.js';
import * as childProcess from 'node:child_process';

vi.mock('node:child_process', async (importOriginal) => {
  const original = await importOriginal<typeof import('node:child_process')>();
  return { ...original, spawnSync: vi.fn(original.spawnSync) };
});

const corpus = fileURLToPath(new URL('./corpus-amd-v2/corpus.json', import.meta.url));
const sha = (data: Uint8Array | string) => createHash('sha256').update(data).digest('hex');

describe('comparaison AMD v2 — notes synthétiques', () => {
  it('valide le protocole et compare 10 briefs, pas 20 répétitions', () => {
    if (!process.env.TMPDIR) throw new Error('TMPDIR explicite requis');
    const dir = mkdtempSync(join(process.env.TMPDIR, 'amd2-paires-'));
    const briefs = (JSON.parse(readFileSync(corpus, 'utf8')) as { briefs: { id: string; split: string }[] }).briefs;
    const protocole = { corpus_sha256: sha(readFileSync(corpus)), split_attendu: { construction: 30, validation: 10, test: 10 },
      eleve: 'fixture-eleve', memoires: { reference: 'c'.repeat(64), candidate: 'd'.repeat(64) }, repetitions_attendues: [1, 2] };
    const fichierProtocole = join(dir, 'protocole.json');
    const brut = JSON.stringify(protocole); writeFileSync(fichierProtocole, brut);
    const observations = briefs.filter((b) => b.split === 'test').flatMap((b) => [1, 2].flatMap((rep) =>
      ['reference', 'candidate'].map((condition) => ({ brief_id: b.id, condition, repetition: rep, seed: rep,
        score: condition === 'reference' ? .4 : .6, evidence_sha256: 'a'.repeat(64) }))));
    const fichierObservations = join(dir, 'observations.json');
    writeFileSync(fichierObservations, JSON.stringify({ protocole_sha256: sha(brut), observations }));
    const resultat = comparerAmd2(corpus, fichierProtocole, fichierObservations, sha(brut));
    expect(resultat.comparaison.n).toBe(10);
    expect(resultat.comparaison.delta).toBeCloseTo(.2);
    expect(resultat.preparation.nombre_campagnes_test).toBe(2);
    expect(resultat.preparation.statut).toBe('paires_pretes_sans_promotion');
    const calcul = vi.spyOn(statistiques, 'compareApparie');
    writeFileSync(fichierObservations, JSON.stringify({ protocole_sha256: sha(brut), observations: observations.filter((o) => o.repetition === 1) }));
    expect(() => comparerAmd2(corpus, fichierProtocole, fichierObservations, sha(brut))).toThrow(/incomplètes/);
    expect(() => comparerAmd2(corpus, join(dir, 'absent.json'), fichierObservations, sha(brut))).toThrow(/refusée/);
    expect(() => comparerAmd2('\0', fichierProtocole, fichierObservations, sha(brut))).toThrow();
    expect(calcul).not.toHaveBeenCalled();
    const processus = vi.mocked(childProcess.spawnSync).mockReturnValueOnce({ error: new Error('échec synthétique'), status: null, stderr: '', stdout: '' } as never);
    expect(() => comparerAmd2(corpus, fichierProtocole, fichierObservations, sha(brut))).toThrow(/erreur du processus/);
    expect(calcul).not.toHaveBeenCalled();
    processus.mockReset();
    calcul.mockRestore();
  });
});
