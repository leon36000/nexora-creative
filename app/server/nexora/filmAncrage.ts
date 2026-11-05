import { ancrageMaxIndisponible, messageAncrageMax, type MoteurVideo } from './creer.js';
import type { CreditsPrise, Facturation } from './credits.js';
import type { PlanFilm, Storyboard } from './film.js';

type PlanAvecReservation = PlanFilm & { reservation?: CreditsPrise };
export type StoryboardAvecReservations = Omit<Storyboard, 'plans'> & { plans: PlanAvecReservation[] };

/** A continued film shot starts from the preceding shot's last frame (H3 image-to-video). */
export function filmRequiertAncre(storyboard: Storyboard): boolean {
  return storyboard.plans.some((plan, i) => i > 0 && plan.suite === true && plan.take == null);
}

/** Returns the localized product error when a film would need an unsupported H3 Max temporal anchor. */
export function erreurAncrageMaxFilm(
  moteur: MoteurVideo,
  storyboard: Storyboard,
  env: NodeJS.ProcessEnv = process.env,
): string | null {
  return filmRequiertAncre(storyboard) && ancrageMaxIndisponible(moteur, true, env)
    ? messageAncrageMax(undefined)
    : null;
}

/**
 * A failed or stopped film can still own reservations for suite shots that never became takes.
 * Keep failed releases on the storyboard so the normal reconciliation can retry them later.
 */
export async function libererReservationsFilmEchoue(
  storyboard: StoryboardAvecReservations,
  facturation: Pick<Facturation, 'liberer'> | null,
): Promise<{ storyboard: StoryboardAvecReservations; liberees: string[]; enAttente: string[] }> {
  const plans = storyboard.plans.map((plan) => ({ ...plan }));
  const liberees: string[] = [];
  const enAttente: string[] = [];

  for (const plan of plans) {
    const reservation = plan.reservation;
    if (plan.take != null || reservation?.etat !== 'reservee') continue;
    if (!facturation) {
      enAttente.push(reservation.reservationId);
      continue;
    }
    try {
      await facturation.liberer(reservation.reservationId);
      plan.reservation = { ...reservation, etat: 'liberee' };
      liberees.push(reservation.reservationId);
    } catch {
      enAttente.push(reservation.reservationId);
    }
  }

  return { storyboard: { ...storyboard, plans }, liberees, enAttente };
}
