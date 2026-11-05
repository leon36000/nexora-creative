import { afterEach, expect, it } from 'vitest';
import { mkdtempSync, readdirSync, readFileSync, rmSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { dossierFilmUnique, sansEcrasement } from './filmSorties.js';
import { argsAssemblage, argsAvecMusique } from './film.js';
import { argsCarton } from './cartons.js';

const parents: string[] = [];
afterEach(() => { for (const p of parents.splice(0)) rmSync(p, { recursive: true, force: true }); });
it('isole les rendus concurrents d’un même film et préserve les vidéos existantes', async () => {
  const parent = mkdtempSync(join(tmpdir(), 'film-sorties-')); parents.push(parent);
  const precedent = join(parent, 'film_7_ancien.mp4');
  writeFileSync(precedent, 'précédent');
  const dirs = await Promise.all(Array.from({ length: 20 }, async () => dossierFilmUnique(parent, 7)));
  expect(new Set(dirs).size).toBe(20);
  for (const [i, dir] of dirs.entries()) writeFileSync(join(dir, 'film.mp4'), `rendu-${i}`, { flag: 'wx' });
  expect(readFileSync(precedent, 'utf8')).toBe('précédent');
  expect(readdirSync(parent)).toHaveLength(21);
});
it('refuse les écrasements ffmpeg pour assemblage, musique et cartons', () => {
  const assemblage = argsAssemblage(['clip.mp4'], 'film.mp4', false);
  const musique = argsAvecMusique('film.mp4', 'musique.wav', 'mix.mp4', { dureeS: 1, sonDuFilm: false });
  const carton = argsCarton('texte.ass', 'carton.mp4', { w: 640, h: 360, dureeS: 2, son: false });
  for (const args of [assemblage, musique, carton]) {
    expect(sansEcrasement(args)).toEqual(['-n', ...args.slice(1)]);
  }
  expect(() => sansEcrasement(['-i', 'clip.mp4'])).toThrow();
});
