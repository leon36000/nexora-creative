/**
 * Crédits des rendus GPU (docs/INTEGRATION-NEXORA.md §1). Devis fixe annoncé avant le tournage, réservé au grand livre
 * de l'organisation par l'API du site, validé quand la prise réussit, libéré si elle échoue ou est arrêtée. Le suivi se
 * fait par la boucle de réconciliation (toutes les 20 s) : idempotent, et il survit à un redémarrage.
 * Les tarifs sont une **proposition** à valider par le fondateur ; ils vivent dans la configuration.
 */

/** Secondes de calcul mesurées sur le DGX Spark GB10 (recherche/08), à 832×480. */
const MESURES_GB10: Record<string, Record<number, number>> = {
  'h3-fast': { 124: 85, 243: 230 },
};

export interface CorpsDevis { videoModel?: string; lengthFrames?: number; frames?: number; width?: number; height?: number }

/** Temps GPU estimé : mesure quand elle existe, sinon extrapolation (croissance plus que linéaire avec la longueur). */
export function secondesGpuEstimees(c: CorpsDevis): number {
  const images = Number(c.lengthFrames ?? c.frames ?? 124);
  const pixels = ((c.width ?? 832) * (c.height ?? 480)) / (832 * 480);
  const mesures = MESURES_GB10[c.videoModel ?? ''] ?? {};
  const base = mesures[images] ?? (c.videoModel === 'wan22' ? 90 : 85) * (images / 124) ** 1.45;
  return Math.round(base * Math.max(1, pixels) ** 1.2);
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
export function facturationSite(siteUrl: string, cle: () => string | undefined, f: typeof fetch = fetch): Facturation {
  const poster = async (chemin: string, corps: unknown) => {
    const k = cle();
    if (!k) throw new Error('organisation sans accès Nexora : reconnecte-toi');
    return f(`${siteUrl}/api/creative/credits/${chemin}`, {
      method: 'POST',
      headers: { 'content-type': 'application/json', authorization: `Bearer ${k}` },
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
