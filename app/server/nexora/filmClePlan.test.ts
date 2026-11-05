import Database from 'better-sqlite3';
import { expect, it } from 'vitest';
import { clePlanFilm, creerPriseSiPlanLibre } from './filmClePlan.js';
import { lireStoryboard } from './film.js';
import { mkdtempSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';

it('une identité stable distingue les paramètres du plan', () => {
  const sb = lireStoryboard({ titre: 'test', plans: [{ resume: 'un', description: 'un' }] }, 5);
  const base = { moteur: 'h3-fast', format: '16:9', son: true, intention: 'film' };
  expect(clePlanFilm(sb, sb.plans[0], base)).toBe(clePlanFilm(sb, sb.plans[0], { ...base }));
  expect(clePlanFilm(sb, sb.plans[0], base)).not.toBe(clePlanFilm(sb, sb.plans[0], { ...base, moteur: 'h3-max' }));
  expect(clePlanFilm(sb, sb.plans[0], base)).not.toBe(clePlanFilm(sb, sb.plans[0], { ...base, references: ['autre-image'] }));
  expect(clePlanFilm(sb, sb.plans[0], base)).not.toBe(clePlanFilm(sb, sb.plans[0], { ...base, son: false }));
  expect(clePlanFilm(sb, sb.plans[0], base)).not.toBe(clePlanFilm(sb, sb.plans[0], { ...base, format: '9:16' }));
  expect(clePlanFilm(sb, sb.plans[0], base)).not.toBe(clePlanFilm(sb, sb.plans[0], { ...base, projectId: 2 }));
  expect(clePlanFilm(sb, sb.plans[0], base)).not.toBe(clePlanFilm(sb, sb.plans[0], { ...base, ancre: 42 }));
  expect(clePlanFilm(sb, sb.plans[0], base)).not.toBe(clePlanFilm(sb, { ...sb.plans[0], duree: 10 }, base));
  expect(clePlanFilm(sb, sb.plans[0], base)).not.toBe(clePlanFilm({ ...sb, bible: { ...sb.bible, style: 'autre' } }, sb.plans[0], base));
});

it('bloque la même clé dans la même organisation, conserve candidats du même film et isole les organisations', () => {
  const db = new Database(':memory:');
  db.exec('CREATE TABLE takes (id INTEGER PRIMARY KEY, organisation_id TEXT, status TEXT, settings TEXT)');
  const insert = (org: string, film: number, statut = 'queued', soumission = 'indeterminee') => () => db.prepare('INSERT INTO takes (organisation_id, status, settings) VALUES (?, ?, ?)').run(org, statut, JSON.stringify({ nexoraFilm: film, nexoraPlan: 0, nexoraClePlan: 'cle', nexoraSoumission: soumission }));
  creerPriseSiPlanLibre(db, 'org-a', 'cle', 1, insert('org-a', 1));
  creerPriseSiPlanLibre(db, 'org-a', 'cle', 1, insert('org-a', 1));
  expect(() => creerPriseSiPlanLibre(db, 'org-a', 'cle', 2, insert('org-a', 2))).toThrow(/déjà une prise/);
  expect(() => creerPriseSiPlanLibre(db, 'org-b', 'cle', 2, insert('org-b', 2))).not.toThrow();
  db.prepare("UPDATE takes SET status='done', settings=json_set(settings, '$.nexoraSoumission', 'confirmee') WHERE organisation_id='org-a'").run();
  expect(() => creerPriseSiPlanLibre(db, 'org-a', 'cle', 3, insert('org-a', 3))).not.toThrow();
  db.close();
});

it('sérialise deux connexions SQLite avant toute seconde insertion', () => {
  const chemin = join(mkdtempSync(join(tmpdir(), 'director-lock-')), 'essai.db');
  const a = new Database(chemin), b = new Database(chemin);
  a.exec('CREATE TABLE takes (id INTEGER PRIMARY KEY, organisation_id TEXT, status TEXT, settings TEXT)');
  b.pragma('busy_timeout = 1');
  a.exec('BEGIN IMMEDIATE');
  a.prepare('INSERT INTO takes (organisation_id, status, settings) VALUES (?, ?, ?)').run('org', 'queued', JSON.stringify({ nexoraFilm: 1, nexoraPlan: 0, nexoraClePlan: 'cle', nexoraSoumission: 'indeterminee' }));
  const creer = () => b.prepare('INSERT INTO takes (organisation_id, status, settings) VALUES (?, ?, ?)').run('org', 'queued', '{}');
  expect(() => creerPriseSiPlanLibre(b, 'org', 'cle', 2, creer)).toThrow();
  a.exec('COMMIT');
  expect(() => creerPriseSiPlanLibre(b, 'org', 'cle', 2, creer)).toThrow(/déjà une prise/);
  expect((b.prepare('SELECT COUNT(*) AS n FROM takes').get() as { n: number }).n).toBe(1);
  a.close(); b.close();
});
