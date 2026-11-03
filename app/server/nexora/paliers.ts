/**
 * Choix du palier (Éco / Équilibré / Expert) par rôle et par projet. Ordre : le projet (session) > le réglage du site
 * pour le rôle (valeur « palier:eco ») > la variable NEXORA_PALIER_<ROLE> > NEXORA_PALIER > le défaut du rôle.
 * Défauts : voir recherche/19 (mesurés sur la campagne). Les trois modèles sont puissants : Expert (Argon Flex) est
 * assez bon marché pour servir de défaut ; Éco est le premier essai de l'escalade.
 */
import { type RoleLlm, reglagesLlmCourants } from './llm.js';
import { type Palier, PALIERS, estPalier, palierDisponible } from './niveaux.js';

export const PALIER_PAR_DEFAUT: Partial<Record<RoleLlm, Palier>> = { tournage: 'expert', montage: 'expert', producteur: 'expert', monteur: 'expert' };

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
