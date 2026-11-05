import { expect, it } from 'vitest';
import { CHECKPOINT_FASTH3, corpsRendu, lireDemandeCreer } from './creer.js';
import { lireStoryboard } from './film.js';
import { erreurAncrageMaxFilm, libererReservationsFilmEchoue, type StoryboardAvecReservations } from './filmAncrage.js';
import type { Facturation } from './credits.js';

const CHECKPOINT_REF2VA = '10Eros_Max_h3_8stepTURBO_beta7_SingularityV2_ref2va_int8HQ.safetensors';
const CHECKPOINT_FL2VA = 'minimax_h3_fl2va_pruned_fp8_scaled.safetensors';
const jeton = 'asset:01234567-89ab-cdef-0123-456789abcdef';

function storyboard(suite = true): StoryboardAvecReservations {
  return lireStoryboard({
    titre: 'Une scène en deux plans',
    plans: [
      { resume: 'Départ', description: 'Une voiture démarre.', duree: 5 },
      { resume: 'Suite', description: 'La voiture accélère.', duree: 5, suite },
    ],
  }, 10) as StoryboardAvecReservations;
}

it('refuse le Max ancré avec Ref2VA et préserve le repli FastH3', () => {
  const sb = storyboard();
  expect(sb.plans[1].suite).toBe(true);
  expect(erreurAncrageMaxFilm('h3-max', sb, { NEXORA_H3_MAX_CHECKPOINT: CHECKPOINT_REF2VA })).toMatch(/qualité maximale.*image ancrée/);
  expect(erreurAncrageMaxFilm('h3-fast', sb, { NEXORA_H3_MAX_CHECKPOINT: CHECKPOINT_REF2VA })).toBeNull();

  const demande = lireDemandeCreer({ intention: 'La voiture accélère.', image: jeton, qualite: 'max' });
  expect(() => corpsRendu(demande, 'The car continues accelerating.', 'h3-max', { NEXORA_H3_MAX_CHECKPOINT: CHECKPOINT_REF2VA })).toThrow(/qualité maximale.*image ancrée/);
  expect(corpsRendu(demande, 'The car continues accelerating.', 'h3-fast', { NEXORA_H3_MAX_CHECKPOINT: CHECKPOINT_REF2VA }))
    .toMatchObject({ videoModel: 'h3-fast', checkpoint: CHECKPOINT_FASTH3, startImage: jeton, width: 1344, height: 768 });
});

it('permet le moteur Max avec une suite seulement quand un checkpoint FL2VA explicite est configuré', () => {
  const sb = storyboard();
  const env = { NEXORA_H3_MAX_CHECKPOINT: CHECKPOINT_FL2VA };
  expect(erreurAncrageMaxFilm('h3-max', sb, env)).toBeNull();
  expect(corpsRendu(lireDemandeCreer({ intention: 'La voiture accélère.', image: jeton, qualite: 'max' }), 'P', 'h3-max', env))
    .toMatchObject({ videoModel: 'h3-max', checkpoint: CHECKPOINT_FL2VA, startImage: jeton });
});

it('ne refuse pas une suite déjà tournée quand seule une autre prise du film sera refaite', () => {
  const sb = storyboard();
  sb.plans[1].take = 42;
  expect(erreurAncrageMaxFilm('h3-max', sb, { NEXORA_H3_MAX_CHECKPOINT: CHECKPOINT_REF2VA })).toBeNull();
});

it('autorise le storyboard de repli sans suite même avec le point de contrôle Ref2VA par défaut', () => {
  expect(erreurAncrageMaxFilm('h3-max', storyboard(false), { NEXORA_H3_MAX_CHECKPOINT: CHECKPOINT_REF2VA })).toBeNull();
});

it('conserve une réservation existante après échec de libération et la solde à la reprise', async () => {
  const sb = storyboard();
  sb.plans[1].reservation = { reservationId: 'reservation-suite-1', credits: 65, etat: 'reservee' };
  let echouer = true;
  const appels: string[] = [];
  const fac: Pick<Facturation, 'liberer'> = {
    async liberer(id) { appels.push(id); if (echouer) throw new Error('site de crédits indisponible'); },
  };

  const premiere = await libererReservationsFilmEchoue(sb, fac);
  expect(premiere.enAttente).toEqual(['reservation-suite-1']);
  expect(premiere.storyboard.plans[1].reservation?.etat).toBe('reservee');

  echouer = false;
  const reprise = await libererReservationsFilmEchoue(premiere.storyboard, fac);
  expect(reprise.liberees).toEqual(['reservation-suite-1']);
  expect(reprise.storyboard.plans[1].reservation?.etat).toBe('liberee');
  expect(appels).toEqual(['reservation-suite-1', 'reservation-suite-1']);
});

it('rejoue sans effet une libération après crash avant la persistance de son état local', async () => {
  const sb = storyboard();
  sb.plans[1].reservation = { reservationId: 'reservation-suite-rejeu', credits: 65, etat: 'reservee' };
  const liberees = new Set<string>();
  let appels = 0;
  const fac: Pick<Facturation, 'liberer'> = {
    async liberer(id) {
      appels++;
      liberees.add(id); // Le grand livre Nexora rejoue la même libération sans nouvelle écriture.
    },
  };

  const premierEssai = await libererReservationsFilmEchoue(sb, fac);
  expect(premierEssai.liberees).toEqual(['reservation-suite-rejeu']);
  // Simule un arrêt après le succès distant, avant patchSettings du storyboard : on repart de l'état DB initial.
  const apresRedemarrage = await libererReservationsFilmEchoue(sb, fac);
  expect(apresRedemarrage.liberees).toEqual(['reservation-suite-rejeu']);
  expect(apresRedemarrage.storyboard.plans[1].reservation?.etat).toBe('liberee');
  expect(appels).toBe(2);
  expect([...liberees]).toEqual(['reservation-suite-rejeu']);
});

it('ne tente pas de libérer la réservation déjà attachée à une prise lancée', async () => {
  const sb = storyboard();
  sb.plans[1].take = 42;
  sb.plans[1].reservation = { reservationId: 'reservation-en-cours', credits: 65, etat: 'reservee' };
  const liberer = async () => { throw new Error('ne doit pas être appelé'); };
  const resultat = await libererReservationsFilmEchoue(sb, { liberer });
  expect(resultat.liberees).toEqual([]);
  expect(resultat.enAttente).toEqual([]);
  expect(resultat.storyboard.plans[1].reservation?.etat).toBe('reservee');
});
