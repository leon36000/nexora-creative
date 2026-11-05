/**
 * Crédits des rendus GPU (docs/INTEGRATION-NEXORA.md §1). Devis fixe annoncé avant le tournage, réservé au grand livre
 * de l'organisation par l'API du site, validé quand la prise réussit, libéré si elle échoue ou est arrêtée. Le suivi se
 * fait par la boucle de réconciliation (toutes les 20 s) : idempotent, et il survit à un redémarrage.
 * Les tarifs sont une **proposition** à valider par le fondateur ; ils vivent dans la configuration.
 */

import { MESURES_OBJET_PC5, secondesObjet } from './objet3d.js';

/** Secondes de calcul mesurées sur le DGX Spark GB10 (recherche/08), par moteur, nombre d'images et taille. */
const MESURES_GB10: Record<string, Record<string, number>> = {
  // FastH3 : DGX Spark GB10 (anciennes mesures) ; RTX 5090 (31/10/2026) : 5 s en 832×480 en 23 s à chaud, 40 s à froid.
  'h3-fast': { '124@832x480': 30 },
  // Moteur cinéma, RTX 5090 de pc1 : H3 non distillé int8, 24 étapes (banc du 31/10/2026).
  // 02/11/2026 : point de contrôle 10Eros-Max × Singularity V2 (8 étapes) en mode référence : 129 s mesurés (deux prises réelles) ;
  // brouillon ref2va 768×448 : 28,7 s. L'ancienne mesure du H3 complet 24 étapes était de 290 s.
  'h3-max': { '124@1344x768': 129, '124@768x448': 29 },
};

export interface CorpsDevis { kind?: string; quality?: string; videoModel?: string; lengthFrames?: number; frames?: number; width?: number; height?: number; vues?: unknown }

/**
 * Temps GPU estimé : la mesure quand elle existe ; sinon extrapolation depuis la mesure de référence du moteur
 * (croissance plus que linéaire avec la longueur et avec le nombre de pixels, comme mesuré : ×2,7 pour 2× la durée,
 * ×4 pour 2,6× les pixels).
 */
export function secondesGpuEstimees(c: CorpsDevis): number {
  // Mode 3D (TRELLIS.2 sur la GB10) : secondes mesurées par détail, indépendantes de la taille de l'image.
  if (c.kind === 'object') return c.vues ? MESURES_OBJET_PC5.multivue : secondesObjet(c.quality === 'quality' ? 'quality' : 'draft');
  const images = Number(c.lengthFrames ?? c.frames ?? 124);
  const w = c.width ?? 832;
  const h = c.height ?? 480;
  const mesures = MESURES_GB10[c.videoModel ?? ''] ?? {};
  const exacte = mesures[`${images}@${w}x${h}`] ?? mesures[`${images}@${h}x${w}`];
  if (exacte) return exacte;
  const reference = c.videoModel === 'h3-max' ? { s: 129, images: 124, w: 1344, h: 768 } : { s: 30, images: 124, w: 832, h: 480 };
  const pixels = (w * h) / (reference.w * reference.h);
  // Un brouillon à basse résolution coûte moins : plancher à 0,2 de la référence (mesure : 0,22 à 768×448).
  return Math.round(reference.s * (images / reference.images) ** 1.45 * Math.max(0.2 ** (1 / 1.45), pixels) ** 1.45);
}

export function devisCredits(c: CorpsDevis, tarif: { creditsParSecondeGpu: number }): number {
  return Math.max(1, Math.ceil(secondesGpuEstimees(c) * tarif.creditsParSecondeGpu));
}

export function tarifDepuisEnv(env: NodeJS.ProcessEnv = process.env) {
  const v = Number(env.NEXORA_CREDITS_PAR_SECONDE_GPU);
  return { creditsParSecondeGpu: Number.isFinite(v) && v > 0 ? v : 0.5 };
}

/** « transferee » : la réservation est passée à la prise qui relance ce plan après une panne (ni validée ni libérée ici). */
export interface CreditsPrise { reservationId: string; credits: number; etat: 'reservee' | 'validee' | 'liberee' | 'transferee' }

export function actionFacturation(t: { status: string; credits?: CreditsPrise }): 'valider' | 'liberer' | null {
  if (!t.credits || t.credits.etat !== 'reservee') return null;
  if (t.status === 'done') return 'valider';
  if (t.status === 'failed' || t.status === 'stopped') return 'liberer';
  return null;
}

export type Reservation = { ok: true; reservationId: string; credits: number } | { ok: false; message: string };

export interface Facturation {
  reserver(r: { idempotence: string; credits: number; libelle: string }): Promise<Reservation>;
  valider(reservationId: string, credits: number): Promise<void>;
  liberer(reservationId: string): Promise<void>;
}

/** API de crédits du site, appelée avec la clé /v1 de l'organisation (la même que celle du LLM). */
export function facturationSite(
  siteUrl: string,
  cle: () => string | undefined,
  f: typeof fetch = fetch,
  jetonService: () => string | undefined = () => undefined,
): Facturation {
  const poster = async (chemin: string, corps: unknown) => {
    const k = cle();
    if (!k) throw new Error('organisation sans accès Nexora : reconnecte-toi');
    const service = jetonService();
    if (!service || service.length < 32) throw new Error('service Creative sans authentification Nexora');
    return f(`${siteUrl}/api/creative/credits/${chemin}`, {
      method: 'POST',
      headers: {
        'content-type': 'application/json',
        authorization: `Bearer ${k}`,
        'x-nexora-creative-service-token': service,
      },
      body: JSON.stringify(corps),
      signal: AbortSignal.timeout(15_000),
    });
  };
  return {
    async reserver({ idempotence, credits, libelle }) {
      const r = await poster('reserve', { idempotencyKey: idempotence, credits, label: libelle });
      const corps = (await r.json().catch(() => ({}))) as any;
      if (r.ok && typeof corps.reservationId === 'string') return { ok: true, reservationId: corps.reservationId, credits: Number(corps.credits ?? credits) };
      return { ok: false, message: corps?.error?.message ?? corps?.message ?? `Réservation de crédits refusée (HTTP ${r.status}).` };
    },
    async valider(reservationId, credits) {
      const r = await poster('settle', { reservationId, credits });
      if (!r.ok) throw new Error(`validation des crédits : HTTP ${r.status}`);
    },
    async liberer(reservationId) {
      const r = await poster('release', { reservationId });
      if (!r.ok) throw new Error(`libération des crédits : HTTP ${r.status}`);
    },
  };
}
