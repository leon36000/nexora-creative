/**
 * Compte Nexora de la requête en cours. Le serveur d'OpenField était mono-utilisateur ; Nexora Creative porte le
 * compte (organisation, utilisateur, territoire) dans un contexte asynchrone posé à l'entrée de chaque requête,
 * pour que les vérifications profondes (licences, crédits, espace) le lisent sans changer chaque signature.
 */
import { AsyncLocalStorage } from 'node:async_hooks';

export interface CompteNexora {
  organisationId: string;
  utilisateurId: string;
  /** Code pays ISO 3166-1 alpha-2 du compte, ou null s'il n'est pas établi. */
  territoire: string | null;
}

const contexte = new AsyncLocalStorage<CompteNexora>();

export function avecCompte<T>(compte: CompteNexora, fn: () => T): T {
  return contexte.run(compte, fn);
}

export function compteCourant(): CompteNexora | null {
  return contexte.getStore() ?? null;
}

/**
 * Territoire du compte en cours. Hors requête (scripts, installation locale), `NEXORA_TERRITOIRE` sert de valeur
 * pour le poste ; sans elle le territoire est inconnu, ce qui ferme H3.
 */
export function territoireDuCompte(): string | null {
  const compte = compteCourant();
  if (compte) return compte.territoire;
  return process.env.NEXORA_TERRITOIRE?.trim() || null;
}
