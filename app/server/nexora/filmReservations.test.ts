import Database from 'better-sqlite3';
import { expect, it } from 'vitest';
import { libererReservationsFilmEchoue, type StoryboardAvecReservations } from './filmAncrage.js';
import { selectionnerReservationsFilmOrphelines } from './filmReservations.js';

const ligneFilm = (...reservationIds: string[]) => JSON.stringify({
  film: true,
  storyboard: { plans: reservationIds.map((reservationId) => ({ suite: true, reservation: { reservationId, credits: 60, etat: 'reservee' } })) },
});

it('ne libère que l’ID orphelin lorsqu’un même film a aussi une réservation attachée à une prise', async () => {
  const db = new Database(':memory:');
  try {
    db.exec('CREATE TABLE takes (id INTEGER PRIMARY KEY, status TEXT NOT NULL, settings TEXT NOT NULL)');
    const ajouter = db.prepare('INSERT INTO takes (id, status, settings) VALUES (?, ?, ?)');
    ajouter.run(1, 'failed', ligneFilm('orpheline-A', 'attachee-B'));
    ajouter.run(2, 'rendering', JSON.stringify({ nexoraCredits: { reservationId: 'attachee-B', etat: 'reservee' } }));
    ajouter.run(3, 'stopped', ligneFilm('reservee-terminee-C'));
    ajouter.run(4, 'done', JSON.stringify({ nexoraCredits: { reservationId: 'reservee-terminee-C', etat: 'reservee' } }));
    ajouter.run(5, 'failed', ligneFilm('orpheline-D'));

    const lignes = selectionnerReservationsFilmOrphelines((sql) => db.prepare(sql).all() as { filmId: number; reservationId: string }[]);
    expect(lignes).toEqual([
      { filmId: 1, reservationId: 'orpheline-A' },
      { filmId: 5, reservationId: 'orpheline-D' },
    ]);

    const storyboard = {
      titre: 'Deux suites',
      dureeTotale: 15,
      plans: [
        { resume: 'Départ', description: 'Départ', duree: 5 },
        { resume: 'Suite A', description: 'Suite A', duree: 5, suite: true, reservation: { reservationId: 'orpheline-A', credits: 60, etat: 'reservee' } },
        { resume: 'Suite B', description: 'Suite B', duree: 5, suite: true, reservation: { reservationId: 'attachee-B', credits: 60, etat: 'reservee' } },
      ],
    } as StoryboardAvecReservations;
    const liberees: string[] = [];
    const resultat = await libererReservationsFilmEchoue(storyboard, { async liberer(id) { liberees.push(id); } }, new Set(lignes.filter((x) => x.filmId === 1).map((x) => x.reservationId)));
    expect(liberees).toEqual(['orpheline-A']);
    expect(resultat.storyboard.plans[1].reservation?.etat).toBe('liberee');
    expect(resultat.storyboard.plans[2].reservation?.etat).toBe('reservee');
  } finally {
    db.close();
  }
});
