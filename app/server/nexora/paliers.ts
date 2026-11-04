/**
 * Choix du palier (Éco / Équilibré / Expert) par rôle et par projet. Ordre : le projet (session) > le réglage du site
 * pour le rôle (valeur « palier:eco ») > la variable NEXORA_PALIER_<ROLE> > NEXORA_PALIER > le défaut du rôle.
 * Défauts (recherche/19, mesurés) : tournage et montage partent d'Éco avec la mémoire allumée et escaladent d'eux-mêmes
 * (0,92 pour 0,0007 $ le film) ; le Producteur, qui converse et appelle des outils, part d'Expert (Argon Flex, ≈ 0,01 $
 * le tour) ; Équilibré est le palier de repli le moins cher quand Éco échoue.
 */
import { type RoleLlm, reglagesLlmCourants } from './llm.js';
import { type Palier, PALIERS, estPalier, palierDisponible } from './niveaux.js';

export const PALIER_PAR_DEFAUT: Partial<Record<RoleLlm, Palier>> = { tournage: 'eco', montage: 'eco', monteur: 'eco', design: 'eco', producteur: 'expert' };

export function palierDuRole(role: RoleLlm, o: { projet?: Palier | null; env?: NodeJS.ProcessEnv; reglages?: Partial<Record<RoleLlm, string>> } = {}): Palier | null {
  const env = o.env ?? process.env;
  const reglage = (o.reglages ?? reglagesLlmCourants().roles)[role]?.replace(/^palier:/, '');
  const choix = [o.projet, reglage, env[`NEXORA_PALIER_${role.toUpperCase()}`], env.NEXORA_PALIER, PALIER_PAR_DEFAUT[role]].find((x) => estPalier(x)) as Palier | undefined;
  if (!choix) return null;
  // Un palier sans clé sur ce serveur laisse la place au premier palier disponible, du plus économique au plus capable.
  return palierDisponible(choix, env) ? choix : PALIERS.find((p) => palierDisponible(p, env)) ?? null;
}

export const paliersDisponibles = (env: NodeJS.ProcessEnv = process.env) => Object.fromEntries(PALIERS.map((p) => [p, palierDisponible(p, env)])) as Record<Palier, boolean>;

/** Palier suivant dans l'escalade (le moins cher d'abord), ou null. */
export const palierSuivant = (p: Palier, env: NodeJS.ProcessEnv = process.env): Palier | null => PALIERS.slice(PALIERS.indexOf(p) + 1).find((x) => palierDisponible(x, env)) ?? null;
