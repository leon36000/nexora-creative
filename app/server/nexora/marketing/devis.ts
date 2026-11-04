/**
 * Devis du mode Marketing, calculé par le code avant toute dépense. Le rendu (Chromium sur le serveur) ne coûte aucun
 * crédit ; seuls les appels au modèle de langage sont facturés, au prix du palier (Éco d'abord, escalade possible).
 * Les images de fond Qwen-Image se commandent dans l'outil Image (son propre devis) et s'importent ensuite dans la pièce.
 */
import { devisLlm, type Devis, type GrandLivreUsage } from '../usage.js';
import type { Palier } from '../niveaux.js';

export type ActionMarketing = 'propositions' | 'logos' | 'variantes' | 'rendu';
export interface DevisMarketing { action: ActionMarketing; palier: Palier; credits: number; creditsReserves: number; usd: number; llm: Devis | null; note: string }

export function devisMarketing(action: ActionMarketing, palier: Palier, o: { livre?: GrandLivreUsage } = {}): DevisMarketing {
  if (action === 'rendu') return { action, palier, credits: 0, creditsReserves: 0, usd: 0, llm: null, note: 'Le rendu PDF/PNG est calculé sur le serveur : aucun crédit.' };
  const llm = devisLlm(`marketing_${action}`, palier, o);
  return { action, palier, credits: llm.credits, creditsReserves: llm.creditsReserves, usd: llm.usd, llm, note: 'Texte écrit par le modèle de langage ; le rendu et les exports sont gratuits.' };
}
