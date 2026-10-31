/**
 * Politique de licences de Nexora Creative : quels ensembles de modèles (server/models.ts) un service commercial
 * hébergé peut faire tourner, et pour quel territoire de compte.
 *
 * Échec fermé : un ensemble absent de la table est bloqué, un territoire inconnu ne reçoit pas H3.
 * Sources : ARCHITECTURE-NEXORA-CREATIVE.md §7 (licence MiniMax H3 I.5, V.4, AUP 1 ; licence LTX-2.x §2.1 et
 * annexe A point 20 ; FLUX.2 dev et 4x-UltraSharp non commerciaux).
 */

export type StatutLicence = 'permis' | 'territoire_exclu' | 'bloque';

export interface VerdictLicence {
  statut: StatutLicence;
  raison: string;
}

/** Union européenne (27), Royaume-Uni, Corée du Sud, États-Unis : « Excluded Territories » de la licence H3 (I.5). */
const EXCLUS_H3 = new Set([
  'AT', 'BE', 'BG', 'HR', 'CY', 'CZ', 'DK', 'EE', 'FI', 'FR', 'DE', 'GR', 'HU', 'IE', 'IT', 'LV', 'LT', 'LU', 'MT',
  'NL', 'PL', 'PT', 'RO', 'SK', 'SI', 'ES', 'SE', 'GB', 'KR', 'US',
]);

const LTX =
  'LTX-2.x : interdit dans un produit qui concurrence directement Lightricks (annexe A, point 20) et payant dès 10 M$ de revenus';
const NON_COMMERCIAL = 'licence non commerciale';

type Regle = { genre: 'permis' } | { genre: 'h3' } | { genre: 'bloque'; raison: string };

const REGLES: Record<string, Regle> = {
  qwen: { genre: 'permis' },
  edit: { genre: 'permis' },
  seedvr2: { genre: 'permis' },
  upres: { genre: 'permis' },
  cutout: { genre: 'permis' },
  sam3: { genre: 'permis' },
  'stage-look': { genre: 'permis' },
  trellis2: { genre: 'permis' },
  h3: { genre: 'h3' },
  'h3-fast': { genre: 'h3' },
  'h3-refs': { genre: 'h3' },
  'h3-turbo': { genre: 'h3' },
  flux2: { genre: 'bloque', raison: `FLUX.2 dev : ${NON_COMMERCIAL}` },
  'upres-ultrasharp': { genre: 'bloque', raison: `4x-UltraSharp : ${NON_COMMERCIAL} (CC BY-NC-SA 4.0)` },
  ltx25: { genre: 'bloque', raison: LTX },
  ltx23: { genre: 'bloque', raison: LTX },
  dream: { genre: 'bloque', raison: LTX },
  mirror: { genre: 'bloque', raison: LTX },
  reshoot: { genre: 'bloque', raison: `${LTX} (adaptation LTX-2.3)` },
  effects: { genre: 'bloque', raison: LTX },
  'effects-community': { genre: 'bloque', raison: LTX },
  cast: { genre: 'bloque', raison: LTX },
  'ltx-tools': { genre: 'bloque', raison: LTX },
  hdr: { genre: 'bloque', raison: LTX },
  swap: { genre: 'bloque', raison: LTX },
  stage: { genre: 'bloque', raison: LTX },
};

/** Verdict pour un ensemble de modèles et le territoire du compte (code pays ISO 3166-1 alpha-2, ou null s'il est inconnu). */
export function verdictLicence(bundleId: string, territoire: string | null): VerdictLicence {
  const regle = REGLES[bundleId];
  if (!regle) return { statut: 'bloque', raison: `ensemble « ${bundleId} » sans licence vérifiée` };
  if (regle.genre === 'bloque') return { statut: 'bloque', raison: regle.raison };
  if (regle.genre === 'permis') return { statut: 'permis', raison: 'licence permissive vérifiée' };
  const pays = territoire?.toUpperCase() ?? null;
  if (!pays || !/^[A-Z]{2}$/.test(pays) || pays === 'ZZ' || EXCLUS_H3.has(pays)) {
    return {
      statut: 'territoire_exclu',
      raison: 'MiniMax H3 : la licence exclut les États-Unis, l’Union européenne, le Royaume-Uni et la Corée du Sud',
    };
  }
  return { statut: 'permis', raison: 'MiniMax H3 : territoire autorisé' };
}

/** Une phrase en français pour l'utilisateur si au moins un ensemble est refusé, sinon null. */
export function refusLicence(bundleIds: string[], territoire: string | null): string | null {
  const raisons = [
    ...new Set(
      bundleIds.map((id) => verdictLicence(id, territoire)).filter((v) => v.statut !== 'permis').map((v) => v.raison),
    ),
  ];
  if (!raisons.length) return null;
  return `Ce rendu n'est pas disponible pour votre compte : ${raisons.join(' ; ')}.`;
}
