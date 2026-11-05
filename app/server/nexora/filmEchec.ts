import type { CreditsPrise, Facturation } from './credits.js';
import { PlanDejaEnCours } from './filmClePlan.js';

export type PriseLancee = { plan: number; takeId: number };
export type AttachementEnAttente = PriseLancee & { reservationId?: string };
export const soumissionIndeterminee = (settings: { nexoraSoumission?: unknown }): boolean => settings.nexoraSoumission === 'indeterminee';

/** Conserve le message d'origine et les prises effectivement retrouvées après un lancement partiel. */
export class EchecTournage extends Error {
  constructor(cause: unknown, public readonly filmId: number, public readonly prises: PriseLancee[], public readonly reservationsConservees: string[], public readonly attachementsEnAttente: AttachementEnAttente[]) {
    super(cause instanceof Error ? cause.message : String(cause), { cause });
  }
}

/** Libère une seule fois les réservations non associées à une prise lancée. */
export async function resultatEchecTournage(e: unknown, reservations: CreditsPrise[], fac: Pick<Facturation, 'liberer'> | null, marquerLiberee?: (filmId: number, reservationId: string) => void) {
  const conservees = new Set(e instanceof EchecTournage ? e.reservationsConservees : []);
  const dejaVues = new Set<string>();
  const enAttente: string[] = [];
  const marquageEnAttente: string[] = [];
  for (const r of reservations) {
    if (dejaVues.has(r.reservationId) || conservees.has(r.reservationId)) continue;
    dejaVues.add(r.reservationId);
    if (!fac) { enAttente.push(r.reservationId); continue; }
    try { await fac.liberer(r.reservationId); }
    catch { enAttente.push(r.reservationId); continue; }
    try { if (e instanceof EchecTournage) marquerLiberee?.(e.filmId, r.reservationId); }
    catch { marquageEnAttente.push(r.reservationId); }
  }
  return {
    error: e instanceof Error ? e.message : 'tournage impossible',
    ...(e instanceof EchecTournage ? { filmId: e.filmId, prises: e.prises } : {}),
    ...(e instanceof EchecTournage && e.cause instanceof PlanDejaEnCours ? { conflit: { takeId: e.cause.takeId, filmId: e.cause.filmId, plan: e.cause.plan } } : {}),
    ...(e instanceof EchecTournage && e.attachementsEnAttente.length ? { attachementsEnAttente: e.attachementsEnAttente } : {}),
    ...(enAttente.length ? { reservationsEnAttente: enAttente } : {}),
    ...(marquageEnAttente.length ? { marquageEnAttente } : {}),
  };
}
