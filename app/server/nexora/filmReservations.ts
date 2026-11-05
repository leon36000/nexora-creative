export interface ReservationFilmOrpheline {
  filmId: number;
  reservationId: string;
}

/** SQL shared with the SQLite-memory regression test. Returns only reservations no take currently owns. */
export function selectionnerReservationsFilmOrphelines<T>(executer: (sql: string) => T[]): T[] {
  return executer(`
    SELECT DISTINCT t.id AS filmId,
      json_extract(p.value, '$.reservation.reservationId') AS reservationId
    FROM takes AS t
    JOIN json_each(t.settings, '$.storyboard.plans') AS p
    WHERE json_extract(t.settings, '$.film') = 1
      AND t.status IN ('failed', 'stopped')
      AND json_extract(p.value, '$.reservation.etat') = 'reservee'
      AND json_extract(p.value, '$.take') IS NULL
      AND json_extract(p.value, '$.reservation.reservationId') IS NOT NULL
      AND NOT EXISTS (
        SELECT 1
        FROM takes AS attachee
        WHERE json_extract(attachee.settings, '$.nexoraCredits.reservationId')
          = json_extract(p.value, '$.reservation.reservationId')
      )
    ORDER BY t.id, reservationId
  `);
}
