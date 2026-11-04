/**
 * Facturation de chaque jeton du monteur : mesure, prix client, grand livre d'usage, devis, réservation, règlement.
 *
 *  prix client (crédits) = coût fournisseur USD × marge × taux USD→CAD × 100   (1 crédit = 1 ¢ CA)
 *  constantes de la passerelle du site : marge 1,10 et taux 1,4025 (NexoraSite/docs/catalogue-deepinfra.md) ; configurables.
 *
 * Cycle d'un run : devis (estimation d'après le palier, la tâche et l'historique) → RÉSERVATION du plafond dur → les
 * appels sont mesurés un par un et refusés au-delà du plafond → RÈGLEMENT du réel (arrondi au crédit supérieur) → le
 * reste de la réservation est libéré. Sur un poste sans crédits rien n'est débité, mais chaque chiffre est enregistré.
 */
import { appendFileSync, existsSync, mkdirSync, readFileSync } from 'node:fs';
import { dirname } from 'node:path';
import type { Facturation } from './credits.js';
import { ErreurLlm, type RoleLlm } from './llm.js';
import { ADAPTATEURS, type AppelMesure, type Palier, type Surveillant, PALIERS } from './niveaux.js';

export interface TarifClient { marge: number; usdVersCad: number; creditsParCad: number }
export function tarifClientDepuisEnv(env: NodeJS.ProcessEnv = process.env): TarifClient {
  const v = (k: string, d: number) => { const x = Number(env[k]); return Number.isFinite(x) && x > 0 ? x : d; };
  return { marge: v('NEXORA_LLM_MARGE', 1.1), usdVersCad: v('NEXORA_USD_CAD', 1.4025), creditsParCad: v('NEXORA_CREDITS_PAR_CAD', 100) };
}

/** Crédits (fractionnaires) d'un coût fournisseur en USD. */
export const creditsExacts = (usd: number, t: TarifClient = tarifClientDepuisEnv()) => usd * t.marge * t.usdVersCad * t.creditsParCad;
/** Crédits facturés : arrondis au supérieur, au moins 1 dès qu'un jeton a été consommé. */
export const creditsFactures = (usd: number, t: TarifClient = tarifClientDepuisEnv()) => (usd > 0 ? Math.max(1, Math.ceil(creditsExacts(usd, t) - 1e-9)) : 0);

export interface ContexteUsage { utilisateur?: string; organisation?: string; projet?: string; run: string; tache: string }
export interface LigneUsage extends ContexteUsage {
  ts: string; role: RoleLlm; palier: Palier; modele: string; endpoint: string; repli: boolean;
  entree: number; sortie: number; raisonnement: number; coutUsd: number; source: 'fournisseur' | 'tarif'; credits: number; ms: number;
}

/** Grand livre d'usage : un fichier JSONL (une ligne par appel). Sans chemin, en mémoire seulement. */
export class GrandLivreUsage {
  private lignesMem: LigneUsage[] = [];
  constructor(private chemin?: string) {
    if (chemin && existsSync(chemin)) this.lignesMem = readFileSync(chemin, 'utf8').split('\n').filter(Boolean).map((l) => JSON.parse(l) as LigneUsage);
  }
  enregistrer(l: LigneUsage): void {
    this.lignesMem.push(l);
    if (this.chemin) { mkdirSync(dirname(this.chemin), { recursive: true }); appendFileSync(this.chemin, JSON.stringify(l) + '\n'); }
  }
  lignes(f: Partial<Pick<LigneUsage, 'run' | 'projet' | 'organisation' | 'utilisateur' | 'palier' | 'tache'>> = {}): LigneUsage[] {
    return this.lignesMem.filter((l) => Object.entries(f).every(([k, v]) => v === undefined || (l as any)[k] === v));
  }
  total(f: Parameters<GrandLivreUsage['lignes']>[0] = {}): Totaux { return totaliser(this.lignes(f)); }
}

export interface Totaux { appels: number; entree: number; sortie: number; raisonnement: number; coutUsd: number; credits: number }
export function totaliser(l: Pick<LigneUsage, 'entree' | 'sortie' | 'raisonnement' | 'coutUsd' | 'credits'>[]): Totaux {
  return l.reduce((t: Totaux, x) => ({ appels: t.appels + 1, entree: t.entree + x.entree, sortie: t.sortie + x.sortie, raisonnement: t.raisonnement + x.raisonnement, coutUsd: t.coutUsd + x.coutUsd, credits: t.credits + x.credits }), { appels: 0, entree: 0, sortie: 0, raisonnement: 0, coutUsd: 0, credits: 0 });
}

export class ErreurPlafondLlm extends ErreurLlm {}

/** Relevé d'un run : mesure chaque appel, tient le grand livre, refuse l'appel suivant au-delà du plafond dur. */
export class Releve implements Surveillant {
  readonly lignes: LigneUsage[] = [];
  constructor(readonly ctx: ContexteUsage, readonly plafondUsd: number, private livre?: GrandLivreUsage, private tarif: TarifClient = tarifClientDepuisEnv()) {}
  get coutUsd() { return this.lignes.reduce((s, l) => s + l.coutUsd, 0); }
  get totaux() { return totaliser(this.lignes); }
  avant(): void {
    if (this.coutUsd >= this.plafondUsd) throw new ErreurPlafondLlm(`plafond de dépense atteint (${this.coutUsd.toFixed(4)} USD ≥ ${this.plafondUsd.toFixed(4)})`);
  }
  apres(a: AppelMesure): void {
    const l: LigneUsage = {
      ...this.ctx, ts: new Date().toISOString(), role: a.role, palier: a.palier, modele: a.modele, endpoint: a.endpoint, repli: a.repli,
      entree: a.usage.entree, sortie: a.usage.sortie, raisonnement: a.usage.raisonnement, coutUsd: a.coutUsd, source: a.source,
      credits: creditsExacts(a.coutUsd, this.tarif), ms: a.ms,
    };
    this.lignes.push(l);
    this.livre?.enregistrer(l);
  }
  /** Crédits à régler pour ce run (entier). */
  get creditsAFacturer() { return creditsFactures(this.coutUsd, this.tarif); }
}

// ---------------------------------------------------------------------------------------------------------------------
// Devis

/** Jetons typiques d'une tâche (mesurés sur la campagne ; repli quand l'historique est trop mince). */
export const JETONS_TACHE: Record<string, { entree: number; sortie: number }> = {
  tournage: { entree: 2600, sortie: 1700 },
  montage: { entree: 4200, sortie: 2300 },
  film: { entree: 6800, sortie: 4000 },
  producteur: { entree: 9000, sortie: 1800 },
  marketing_propositions: { entree: 2400, sortie: 1700 },
  marketing_logos: { entree: 1700, sortie: 3600 },
  marketing_variantes: { entree: 1900, sortie: 900 },
};

export interface Devis { tache: string; palier: Palier; entree: number; sortie: number; usd: number; credits: number; creditsReserves: number; plafondUsd: number; source: 'historique' | 'tables' }

/**
 * Devis d'une tâche : moyenne de l'historique du même palier et de la même tâche si on a au moins 3 runs, sinon les
 * jetons typiques. Réservation = devis × 2 (réparations et un tour d'escalade), plafond dur = la réservation.
 */
export function devisLlm(tache: string, palier: Palier, o: { livre?: GrandLivreUsage; tarif?: TarifClient; marge?: number } = {}): Devis {
  const a = ADAPTATEURS[palier];
  const tarif = o.tarif ?? tarifClientDepuisEnv();
  let entree = JETONS_TACHE[tache]?.entree ?? 4000, sortie = JETONS_TACHE[tache]?.sortie ?? 2500, source: Devis['source'] = 'tables';
  const h = o.livre?.lignes({ palier, tache });
  const runs = h ? [...new Set(h.map((l) => l.run))] : [];
  if (h && runs.length >= 3) {
    entree = Math.round(h.reduce((s, l) => s + l.entree, 0) / runs.length);
    sortie = Math.round(h.reduce((s, l) => s + l.sortie, 0) / runs.length);
    source = 'historique';
  }
  const usd = (entree * a.prixEntreeUsdM + sortie * a.prixSortieUsdM) / 1e6;
  const plafondUsd = usd * (o.marge ?? 2);
  return { tache, palier, entree, sortie, usd, credits: creditsFactures(usd, tarif), creditsReserves: creditsFactures(plafondUsd, tarif), plafondUsd, source };
}

export interface BilanRun { reservationId: string | null; reserves: number; factures: number; liberes: number; totaux: Totaux }

/**
 * Exécute `travail` sous réservation. Sans facturation (poste local), le plafond et les mesures s'appliquent, rien n'est
 * débité. Si la réservation est refusée, le travail ne démarre pas. Toujours : règlement du réel, libération du reste.
 */
export async function executerSousReservation<T>(
  o: { fac: Facturation | null; devis: Devis; ctx: ContexteUsage; livre?: GrandLivreUsage; tarif?: TarifClient },
  travail: (releve: Releve) => Promise<T>,
): Promise<{ resultat: T; bilan: BilanRun }> {
  const tarif = o.tarif ?? tarifClientDepuisEnv();
  let reservationId: string | null = null;
  if (o.fac) {
    const r = await o.fac.reserver({ idempotence: `llm-${o.ctx.run}`, credits: o.devis.creditsReserves, libelle: `Agent ${o.devis.tache} (${o.devis.palier})` });
    if (!r.ok) throw new ErreurLlm(r.message);
    reservationId = r.reservationId;
  }
  const releve = new Releve(o.ctx, o.devis.plafondUsd, o.livre, tarif);
  try {
    const resultat = await travail(releve);
    return { resultat, bilan: await regler(o.fac, reservationId, o.devis.creditsReserves, releve) };
  } catch (e) {
    // Les jetons déjà consommés restent dus ; la réservation n'est jamais laissée ouverte.
    await regler(o.fac, reservationId, o.devis.creditsReserves, releve).catch(() => {});
    throw e;
  }
}

async function regler(fac: Facturation | null, reservationId: string | null, reserves: number, r: Releve): Promise<BilanRun> {
  const factures = Math.min(reserves, r.creditsAFacturer);
  if (fac && reservationId) {
    if (factures > 0) await fac.valider(reservationId, factures); else await fac.liberer(reservationId);
  }
  return { reservationId, reserves: fac ? reserves : 0, factures: fac ? factures : 0, liberes: fac ? reserves - factures : 0, totaux: r.totaux };
}

export const PALIERS_ORDRE = PALIERS;
