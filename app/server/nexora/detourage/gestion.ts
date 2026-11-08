/**
 * Détourage vidéo : cycle de vie des travaux (asynchrones, avec progression, annulation, reprise et nettoyage).
 *
 * Un travail vit sur la machine GPU (son dossier de travail y reste) ; ici on tient le registre, par organisation :
 * personne ne voit, ne lance, n'annule ni ne supprime le travail d'une autre organisation. Les crédits sont réservés au
 * lancement, validés à la fin réussie, libérés si le travail échoue ou est annulé (idempotent : un état terminal est
 * soldé une seule fois). Le registre est un fichier JSON écrit de façon atomique.
 */
import { randomBytes } from 'node:crypto';
import { mkdirSync, readFileSync, renameSync, writeFileSync } from 'node:fs';
import { dirname } from 'node:path';
import type { Facturation } from '../credits.js';
import type { ClientDetourage, EtatMoteur, InfoSource } from './client.js';

export type EtatTravail = 'depose' | 'en_attente' | 'en_cours' | 'termine' | 'erreur' | 'annule' | 'interrompu';
const TERMINAUX: ReadonlySet<EtatTravail> = new Set(['termine', 'erreur', 'annule']);
const ACTIFS: ReadonlySet<EtatTravail> = new Set(['en_cours', 'en_attente']);
const REPRENABLES: ReadonlySet<EtatTravail> = new Set(['interrompu', 'erreur', 'annule']);

export interface TravailDetourage {
  id: string;
  organisation: string;
  utilisateur: string;
  nom: string;
  moteurId: string;
  creeLe: number;
  majLe: number;
  etat: EtatTravail;
  etape: string;
  progression: number;
  message: string;
  params?: Record<string, unknown>;
  devis?: { secondes: number; credits: number | null };
  credits?: {
    reservationId: string; credits: number; etat: 'reservee' | 'validee' | 'liberee';
    /** Intention persistée avant l'appel : un nouvel état moteur ne change pas un règlement à réessayer. */
    reglement?: 'valider' | 'liberer';
  };
  mesures?: Record<string, unknown>;
  sorties?: EtatMoteur['sorties'];
  /** Fichiers déposés (source, fond) : octets. */
  fichiers: Record<string, number>;
  /** Caractéristiques de la source mesurées par le moteur (jamais déclarées par le client). */
  source?: InfoSource;
}

export interface OptionsDetourage {
  /** Chemin du registre JSON. */
  registre: string;
  /** Moteur et client pour un palier ; `null` si aucun moteur ne le propose. */
  moteur: (palier: string, moteurId?: string) => { id: string; client: ClientDetourage } | null;
  /** Client d'un moteur déjà choisi (pour suivre un travail existant). */
  clientDe: (moteurId: string) => ClientDetourage | null;
  facturation?: (organisation: string) => Facturation | null;
  maintenant?: () => number;
  ttl?: { termineMs: number; deposeMs: number };
}

export class ErreurDetourage extends Error {
  constructor(message: string, readonly code = 400) { super(message); }
}

const ETATS_TRAVAIL: ReadonlySet<string> = new Set<EtatTravail>(['depose', 'en_attente', 'en_cours', 'termine', 'erreur', 'annule', 'interrompu']);

function objet(v: unknown): v is Record<string, unknown> {
  return v !== null && typeof v === 'object' && !Array.isArray(v);
}
function nombreFini(v: unknown): v is number { return typeof v === 'number' && Number.isFinite(v); }

function creditsValides(c: unknown): boolean {
  if (!objet(c) || typeof c.reservationId !== 'string' || !c.reservationId || !nombreFini(c.credits)) return false;
  if (c.etat !== 'reservee' && c.etat !== 'validee' && c.etat !== 'liberee') return false;
  return c.reglement === undefined || c.reglement === 'valider' || c.reglement === 'liberer';
}

/** Conserve les champs inconnus et les options historiques; contrôle les invariants du cycle de vie. */
function travailValide(v: unknown): v is TravailDetourage {
  if (!objet(v)) return false;
  if (['id', 'organisation', 'moteurId'].some((k) => typeof v[k] !== 'string' || v[k] === '')) return false;
  if (['utilisateur', 'nom', 'etape', 'message'].some((k) => typeof v[k] !== 'string')) return false;
  if (!nombreFini(v.creeLe) || !nombreFini(v.majLe) || !nombreFini(v.progression)) return false;
  if (typeof v.etat !== 'string' || !ETATS_TRAVAIL.has(v.etat)) return false;
  if (!objet(v.fichiers) || Object.values(v.fichiers).some((n) => !nombreFini(n))) return false;
  return v.credits === undefined || creditsValides(v.credits);
}

function chargerRegistre(chemin: string): Map<string, TravailDetourage> {
  let texte: string;
  try { texte = readFileSync(chemin, 'utf8'); }
  catch (e) {
    if ((e as NodeJS.ErrnoException | null)?.code === 'ENOENT') return new Map();
    throw e;
  }
  const contenu: unknown = JSON.parse(texte);
  if (!Array.isArray(contenu)) throw new Error('Registre invalide.');
  const travaux = new Map<string, TravailDetourage>();
  for (const t of contenu) {
    if (!travailValide(t) || travaux.has(t.id)) throw new Error('Registre invalide.');
    travaux.set(t.id, t);
  }
  return travaux;
}

export class Detourage {
  private travaux = new Map<string, TravailDetourage>();
  private readonly operations = new Set<string>();
  private readonly registreIndisponible: boolean;
  private readonly now: () => number;
  private readonly ttl: { termineMs: number; deposeMs: number };

  constructor(private readonly o: OptionsDetourage) {
    this.now = o.maintenant ?? Date.now;
    this.ttl = o.ttl ?? { termineMs: 48 * 3600_000, deposeMs: 7 * 24 * 3600_000 };
    let charge: Map<string, TravailDetourage> | null = null;
    try { charge = chargerRegistre(o.registre); } catch { /* conserver le fichier original pour récupération */ }
    this.registreIndisponible = charge === null;
    if (charge !== null) this.travaux = charge;
    // Au redémarrage de ce serveur, ce qui était « en cours » est resuivi auprès de la machine GPU (qui seule sait).
  }

  private verifierRegistre() {
    if (this.registreIndisponible) throw new ErreurDetourage('Le registre du détourage est indisponible. Réessaie plus tard.', 503);
  }

  private sauver() {
    this.verifierRegistre();
    mkdirSync(dirname(this.o.registre), { recursive: true });
    const tmp = `${this.o.registre}.tmp`;
    writeFileSync(tmp, JSON.stringify([...this.travaux.values()]));
    renameSync(tmp, this.o.registre);
  }

  private possede(org: string, id: string): TravailDetourage {
    this.verifierRegistre();
    const t = this.travaux.get(id);
    if (!t || t.organisation !== org) throw new ErreurDetourage('Travail introuvable.', 404); // même réponse : on ne révèle pas l'existence
    return t;
  }

  /** Une mutation par travail dans cette instance, dès avant le premier await. */
  private async modifier<T>(org: string, id: string, faire: (t: TravailDetourage) => Promise<T>): Promise<T> {
    const t = this.possede(org, id);
    if (this.operations.has(id)) throw new ErreurDetourage('Déjà en cours.', 409);
    this.operations.add(id);
    try { return await faire(t); }
    finally { this.operations.delete(id); }
  }

  lister(org: string): TravailDetourage[] {
    this.verifierRegistre();
    return [...this.travaux.values()].filter((t) => t.organisation === org).sort((a, b) => b.creeLe - a.creeLe);
  }

  obtenir(org: string, id: string): TravailDetourage { return this.possede(org, id); }

  creer(org: string, utilisateur: string, nom: string, palier = 'rapide'): TravailDetourage {
    this.verifierRegistre();
    const m = this.o.moteur(palier);
    if (!m) throw new ErreurDetourage(palier === 'pro' ? 'Le détourage pro n’est pas encore disponible.' : 'Aucun moteur de détourage en ligne.', 503);
    const t: TravailDetourage = {
      id: randomBytes(12).toString('hex'), organisation: org, utilisateur, nom: nom.slice(0, 120) || 'Sans titre', moteurId: m.id,
      creeLe: this.now(), majLe: this.now(), etat: 'depose', etape: 'dépôt', progression: 0, message: 'En attente de la vidéo', fichiers: {},
    };
    this.travaux.set(t.id, t);
    this.sauver();
    return t;
  }

  /** Envoie la source ou le fond vers la machine GPU (flux ou tampon) et l'inscrit dans le registre. */
  async deposer(org: string, id: string, nom: 'source.mp4' | `fond-${string}`, flux: Parameters<ClientDetourage['deposer']>[2], octets?: number) {
    return this.modifier(org, id, async (t) => {
      if (t.etat !== 'depose' && !TERMINAUX.has(t.etat)) throw new ErreurDetourage('Le travail est en cours : attends sa fin ou annule-le.', 409);
      const c = this.o.clientDe(t.moteurId);
      if (!c) throw new ErreurDetourage('Le moteur de ce travail est hors ligne.', 503);
      const info = await c.deposer(id, nom, flux, octets);
      if (nom === 'source.mp4' && info) t.source = info;
      t.fichiers[nom] = octets ?? 0;
      t.majLe = this.now();
      this.sauver();
      return t;
    });
  }

  async lancer(org: string, id: string, params: Record<string, unknown>, devis?: { secondes: number; credits: number | null }, libelle = 'Détourage vidéo') {
    return this.lancerInterne(org, id, params, devis, libelle, false);
  }

  private async lancerInterne(org: string, id: string, params: Record<string, unknown>, devis: { secondes: number; credits: number | null } | undefined, libelle: string, reprise: boolean) {
    return this.modifier(org, id, async (t) => {
      if (ACTIFS.has(t.etat)) throw new ErreurDetourage('Déjà en cours.', 409);
      if (!t.fichiers['source.mp4']) throw new ErreurDetourage('Dépose d’abord la vidéo.', 409);
      const c = this.o.clientDe(t.moteurId);
      if (!c) throw new ErreurDetourage('Le moteur de ce travail est hors ligne.', 503);
      if (t.etat !== 'depose' && !(t.credits?.etat === 'reservee' && t.credits.reglement)) {
        await this.actualiserTravail(org, t, true);
        if (ACTIFS.has(t.etat)) throw new ErreurDetourage('Déjà en cours.', 409);
      }
      if (reprise && !REPRENABLES.has(t.etat)) throw new ErreurDetourage('Ce travail n’est plus interrompu.', 409);
      if (t.credits?.etat === 'reservee') await this.reglerCredits(org, t);
      t.credits = undefined;
      const fac = this.o.facturation?.(org) ?? null;
      if (fac && devis?.credits) {
        const r = await fac.reserver({ idempotence: randomBytes(12).toString('hex'), credits: devis.credits, libelle });
        if (!r.ok) throw new ErreurDetourage(r.message, 402);
        t.credits = { reservationId: r.reservationId, credits: r.credits, etat: 'reservee' };
      }
      // Le nouvel essai ne doit jamais hériter de l'état « terminé » de la prise précédente.
      Object.assign(t, { params, devis, etat: 'depose', etape: 'lancement', message: 'Lancement en cours', majLe: this.now() });
      try { this.sauver(); } // conserver l'identifiant avant d'appeler le moteur
      catch (e) {
        t.etat = 'erreur';
        t.message = 'Le lancement a été retenu : registre indisponible.';
        if (t.credits?.etat === 'reservee') t.credits.reglement = 'liberer';
        throw e;
      }
      try {
        await c.lancer(id, params);
      } catch (e) {
        Object.assign(t, { etat: 'erreur', etape: 'lancement', message: 'Le lancement a échoué.', majLe: this.now() });
        if (t.credits?.etat === 'reservee') t.credits.reglement = 'liberer';
        this.sauver();
        try { await this.reglerCredits(org, t); }
        catch {
          t.message = 'Le lancement a échoué. Le règlement des crédits reste en attente.';
          this.sauver();
        }
        throw e;
      }
      Object.assign(t, { params, devis, etat: 'en_attente', etape: 'file', progression: 0, message: 'En file', majLe: this.now(), mesures: undefined, sorties: undefined });
      this.sauver();
      return t;
    });
  }

  /** Interroge la machine GPU, met à jour le registre, solde les crédits si l'état est terminal. */
  async actualiser(org: string, id: string): Promise<TravailDetourage> {
    const t = this.possede(org, id);
    // Une lecture concurrente ne règle jamais des crédits pendant une autre mutation.
    if (this.operations.has(id)) return t;
    return this.modifier(org, id, (travail) => this.actualiserTravail(org, travail));
  }

  private async actualiserTravail(org: string, t: TravailDetourage, stricte = false): Promise<TravailDetourage> {
    if (t.credits?.etat === 'reservee' && t.credits.reglement) {
      // Le résultat ancien du moteur ne doit pas changer le règlement déjà décidé.
      await this.solder(org, t);
      this.sauver();
      return t;
    }
    if (t.etat === 'depose' || !stricte && TERMINAUX.has(t.etat) && t.credits?.etat !== 'reservee') return t;
    const c = this.o.clientDe(t.moteurId);
    if (!c) {
      if (stricte) throw new ErreurDetourage('Le moteur de ce travail est hors ligne.', 503);
      t.message = 'Moteur hors ligne : la progression reprendra à son retour.'; return t;
    }
    let e: EtatMoteur | null;
    try { e = await c.etat(t.id); } catch {
      if (stricte) throw new ErreurDetourage('Le moteur est injoignable. Réessaie plus tard.', 503);
      t.message = 'Moteur injoignable : nouvelle tentative au prochain appel.'; return t;
    }
    if (!e) {
      Object.assign(t, { etat: 'erreur', message: 'Le moteur a perdu ce travail (dossier supprimé).', majLe: this.now() });
    } else {
      Object.assign(t, { etat: e.etat as EtatTravail, etape: e.etape ?? t.etape, progression: e.progression ?? t.progression, message: e.message ?? '', majLe: this.now() });
      if (e.mesures) t.mesures = e.mesures;
      if (e.sorties) t.sorties = e.sorties;
    }
    await this.solder(org, t);
    this.sauver();
    return t;
  }

  private async solder(org: string, t: TravailDetourage) {
    if (!TERMINAUX.has(t.etat) && !t.credits?.reglement) return;
    try { await this.reglerCredits(org, t); }
    catch { /* le prochain appel réessaie le même identifiant */ }
  }

  /** Ne retire une réservation qu'après confirmation du site ; un travail terminé est facturé. */
  private async reglerCredits(org: string, t: TravailDetourage) {
    if (t.credits?.etat !== 'reservee') return;
    const credits = t.credits;
    if (credits.reglement !== undefined && credits.reglement !== 'valider' && credits.reglement !== 'liberer') {
      throw new ErreurDetourage('Le règlement des crédits est invalide.', 503);
    }
    if (!credits.reglement) {
      credits.reglement = t.etat === 'termine' ? 'valider' : 'liberer';
    }
    this.sauver(); // même une tentative précédente interrompue doit être persistée avant l'appel
    const fac = this.o.facturation?.(org) ?? null;
    if (!fac) throw new ErreurDetourage('Le règlement des crédits reste en attente. Réessaie plus tard.', 503);
    const termine = credits.reglement === 'valider';
    try {
      if (termine) await fac.valider(credits.reservationId, credits.credits);
      else await fac.liberer(credits.reservationId);
    } catch { throw new ErreurDetourage('Le règlement des crédits reste en attente. Réessaie plus tard.', 503); }
    credits.etat = termine ? 'validee' : 'liberee';
    t.majLe = this.now();
    this.sauver();
  }

  async annuler(org: string, id: string): Promise<TravailDetourage> {
    return this.modifier(org, id, (t) => this.annulerTravail(org, t));
  }

  private async annulerTravail(org: string, t: TravailDetourage): Promise<TravailDetourage> {
    if (TERMINAUX.has(t.etat) || t.etat === 'depose') return t;
    await this.o.clientDe(t.moteurId)?.annuler(t.id).catch(() => {});
    return this.actualiserTravail(org, t);
  }

  /** Reprise : relance les mêmes réglages ; le moteur saute ce qui est déjà calculé (suivi, matting) grâce à ses clés. */
  async reprendre(org: string, id: string): Promise<TravailDetourage> {
    const t = this.possede(org, id);
    if (!t.params) throw new ErreurDetourage('Rien à reprendre : lance d’abord le travail.', 409);
    if (!REPRENABLES.has(t.etat)) throw new ErreurDetourage('Ce travail n’est pas interrompu.', 409);
    return this.lancerInterne(org, id, t.params, t.devis, 'Détourage vidéo (reprise)', true);
  }

  /** Supprime le travail et tout son dossier sur la machine GPU (fichiers temporaires, séquences, vidéos). */
  async supprimer(org: string, id: string) {
    return this.modifier(org, id, async (t) => {
      const c = this.o.clientDe(t.moteurId);
      if (!c) throw new ErreurDetourage('Le moteur de ce travail est hors ligne.', 503);
      if (t.etat !== 'depose' && !(t.credits?.etat === 'reservee' && t.credits.reglement)) await this.actualiserTravail(org, t, true);
      if (ACTIFS.has(t.etat)) await this.annulerTravail(org, t);
      if (ACTIFS.has(t.etat)) throw new ErreurDetourage('Attends l’arrêt du travail avant de le supprimer.', 409);
      await this.reglerCredits(org, t);
      await c.supprimer(id);
      this.travaux.delete(id);
      this.sauver();
    });
  }

  /** Nettoyage périodique : travaux terminés/échoués trop anciens, dépôts jamais lancés. Retourne les identifiants supprimés. */
  async nettoyer(): Promise<string[]> {
    if (this.registreIndisponible) return []; // minuteur : aucun rejet ni nettoyage d’un registre non chargé
    const maintenant = this.now();
    const sortis: string[] = [];
    for (const t of [...this.travaux.values()]) {
      const age = maintenant - t.majLe;
      const vieux = (TERMINAUX.has(t.etat) && age > this.ttl.termineMs) || ((t.etat === 'depose' || t.etat === 'interrompu') && age > this.ttl.deposeMs);
      if (!vieux) continue;
      try { await this.supprimer(t.organisation, t.id); sortis.push(t.id); } catch { /* retenté au prochain passage */ }
    }
    return sortis;
  }
}
