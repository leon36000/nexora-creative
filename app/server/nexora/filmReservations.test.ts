import Database from 'better-sqlite3';
import { expect, it } from 'vitest';
import { selectionnerFilmsAvecReservationsEnAttente } from './filmReservations.js';

const ligneFilm = (id: number, reservationId: string) => JSON.stringify({
  film: true,
  storyboard: { plans: [{ suite: true, reservation: { reservationId, credits: 60, etat: 'reservee' } }] },
});

it('exclut de la reprise une réservation déjà attachée à une prise, même si le film ne connaît pas encore son ID', () => {
  const db = new Database(':memory:');
  try {
    db.exec('CREATE TABLE takes (id INTEGER PRIMARY KEY, status TEXT NOT NULL, settings TEXT NOT NULL)');
    const ajouter = db.prepare('INSERT INTO takes (id, status, settings) VALUES (?, ?, ?)');
    ajouter.run(1, 'failed', ligneFilm(1, 'reservee-active'));
    ajouter.run(2, 'rendering', JSON.stringify({ nexoraCredits: { reservationId: 'reservee-active', etat: 'reservee' } }));
    ajouter.run(3, 'stopped', ligneFilm(3, 'reservee-terminee'));
    ajouter.run(4, 'done', JSON.stringify({ nexoraCredits: { reservationId: 'reservee-terminee', etat: 'reservee' } }));
    ajouter.run(5, 'failed', ligneFilm(5, 'reservee-libre'));

    const lignes = selectionnerFilmsAvecReservationsEnAttente((sql) => db.prepare(sql).all() as { id: number }[]);
    expect(lignes.map((x) => x.id)).toEqual([5]);
  } finally {
    db.close();
  }
});
