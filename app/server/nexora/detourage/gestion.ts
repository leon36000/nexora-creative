/**
 * Détourage vidéo : cycle de vie des travaux (asynchrones, avec progression, annulation, reprise et nettoyage).
 *
 * Un travail vit sur la machine GPU (son dossier de travail y reste) ; ici on tient le registre, par organisation :
 * personne ne voit, ne lance, n'annule ni ne supprime le travail d'une autre organisation. Les crédits sont réservés au
 * lancement, validés à la fin réussie, libérés si le travail échoue ou est annulé (idempotent : un état terminal est
 * soldé une seule fois). Le registre est un fichier JSON écrit de façon atomique.
 */
import { randomBytes } from 'node:crypto';
import { existsSync, mkdirSync, readFileSync, renameSync, writeFileSync } from 'node:fs';
import { dirname } from 'node:path';
import type { Facturation } from '../credits.js';
import type { ClientDetourage, EtatMoteur, InfoSource } from './client.js';

export type EtatTravail = 'depose' | 'en_attente' | 'en_cours' | 'termine' | 'erreur' | 'annule' | 'interrompu';
const TERMINAUX: ReadonlySet<EtatTravail> = new Set(['termine', 'erreur', 'annule']);

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
  credits?: { reservationId: string; credits: number; etat: 'reservee' | 'validee' | 'liberee' };
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

export class Detourage {
  private travaux = new Map<string, TravailDetourage>();
  private readonly now: () => number;
  private readonly ttl: { termineMs: number; deposeMs: number };

  constructor(private readonly o: OptionsDetourage) {
    this.now = o.maintenant ?? Date.now;
    this.ttl = o.ttl ?? { termineMs: 48 * 3600_000, deposeMs: 7 * 24 * 3600_000 };
    if (existsSync(o.registre)) {
      try {
        for (const t of JSON.parse(readFileSync(o.registre, 'utf8')) as TravailDetourage[]) this.travaux.set(t.id, t);
      } catch { /* registre illisible : on repart à vide, les dossiers GPU se nettoient par TTL côté machine */ }
    }
    // Au redémarrage de ce serveur, ce qui était « en cours » est resuivi auprès de la machine GPU (qui seule sait).
  }

  private sauver() {
    mkdirSync(dirname(this.o.registre), { recursive: true });
    const tmp = `${this.o.registre}.tmp`;
    writeFileSync(tmp, JSON.stringify([...this.travaux.values()]));
    renameSync(tmp, this.o.registre);
  }

  private possede(org: string, id: string): TravailDetourage {
    const t = this.travaux.get(id);
    if (!t || t.organisation !== org) throw new ErreurDetourage('Travail introuvable.', 404); // même réponse : on ne révèle pas l'existence
    return t;
  }

  lister(org: string): TravailDetourage[] {
    return [...this.travaux.values()].filter((t) => t.organisation === org).sort((a, b) => b.creeLe - a.creeLe);
  }

  obtenir(org: string, id: string): TravailDetourage { return this.possede(org, id); }

  creer(org: string, utilisateur: string, nom: string, palier = 'rapide'): TravailDetourage {
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
    const t = this.possede(org, id);
    if (t.etat !== 'depose' && !TERMINAUX.has(t.etat)) throw new ErreurDetourage('Le travail est en cours : attends sa fin ou annule-le.', 409);
    const c = this.o.clientDe(t.moteurId);
    if (!c) throw new ErreurDetourage('Le moteur de ce travail est hors ligne.', 503);
    const info = await c.deposer(id, nom, flux, octets);
    if (nom === 'source.mp4' && info) t.source = info;
    t.fichiers[nom] = octets ?? 0;
    t.majLe = this.now();
    this.sauver();
    return t;
  }

  async lancer(org: string, id: string, params: Record<string, unknown>, devis?: { secondes: number; credits: number | null }, libelle = 'Détourage vidéo') {
    const t = this.possede(org, id);
    if (t.etat === 'en_cours' || t.etat === 'en_attente') throw new ErreurDetourage('Déjà en cours.', 409);
    if (!t.fichiers['source.mp4']) throw new ErreurDetourage('Dépose d’abord la vidéo.', 409);
    const c = this.o.clientDe(t.moteurId);
    if (!c) throw new ErreurDetourage('Le moteur de ce travail est hors ligne.', 503);
    const fac = this.o.facturation?.(org) ?? null;
    if (t.credits?.etat === 'reservee') await fac?.liberer(t.credits.reservationId).catch(() => {}); // relance : l'ancien devis est rendu
    t.credits = undefined;
    if (fac && devis?.credits) {
      const r = await fac.reserver({ idempotence: randomBytes(12).toString('hex'), credits: devis.credits, libelle });
      if (!r.ok) throw new ErreurDetourage(r.message, 402);
      t.credits = { reservationId: r.reservationId, credits: r.credits, etat: 'reservee' };
    }
    try {
      await c.lancer(id, params);
    } catch (e) {
      if (t.credits) { await fac?.liberer(t.credits.reservationId).catch(() => {}); t.credits.etat = 'liberee'; }
      throw e;
    }
    Object.assign(t, { params, devis, etat: 'en_attente', etape: 'file', progression: 0, message: 'En file', majLe: this.now(), mesures: undefined, sorties: undefined });
    this.sauver();
    return t;
  }

  /** Interroge la machine GPU, met à jour le registre, solde les crédits si l'état est terminal. */
  async actualiser(org: string, id: string): Promise<TravailDetourage> {
    const t = this.possede(org, id);
    if (t.etat === 'depose' || TERMINAUX.has(t.etat) && t.credits?.etat !== 'reservee') return t;
    const c = this.o.clientDe(t.moteurId);
    if (!c) { t.message = 'Moteur hors ligne : la progression reprendra à son retour.'; return t; }
    let e: EtatMoteur | null;
    try { e = await c.etat(id); } catch { t.message = 'Moteur injoignable : nouvelle tentative au prochain appel.'; return t; }
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
    if (t.credits?.etat !== 'reservee') return;
    const fac = this.o.facturation?.(org) ?? null;
    if (!fac) return;
    try {
      if (t.etat === 'termine') { await fac.valider(t.credits.reservationId, t.credits.credits); t.credits.etat = 'validee'; }
      else if (t.etat === 'erreur' || t.etat === 'annule') { await fac.liberer(t.credits.reservationId); t.credits.etat = 'liberee'; }
    } catch { /* le prochain appel réessaie : valider et liberer sont idempotents côté site */ }
  }

  async annuler(org: string, id: string): Promise<TravailDetourage> {
    const t = this.possede(org, id);
    if (TERMINAUX.has(t.etat) || t.etat === 'depose') return t;
    await this.o.clientDe(t.moteurId)?.annuler(id).catch(() => {});
    return this.actualiser(org, id);
  }

  /** Reprise : relance les mêmes réglages ; le moteur saute ce qui est déjà calculé (suivi, matting) grâce à ses clés. */
  async reprendre(org: string, id: string): Promise<TravailDetourage> {
    const t = this.possede(org, id);
    if (!t.params) throw new ErreurDetourage('Rien à reprendre : lance d’abord le travail.', 409);
    if (t.etat !== 'interrompu' && t.etat !== 'erreur' && t.etat !== 'annule') throw new ErreurDetourage('Ce travail n’est pas interrompu.', 409);
    return this.lancer(org, id, t.params, t.devis, 'Détourage vidéo (reprise)');
  }

  /** Supprime le travail et tout son dossier sur la machine GPU (fichiers temporaires, séquences, vidéos). */
  async supprimer(org: string, id: string) {
    const t = this.possede(org, id);
    if (t.etat === 'en_cours' || t.etat === 'en_attente') await this.annuler(org, id).catch(() => {});
    if (t.credits?.etat === 'reservee') { await (this.o.facturation?.(org) ?? null)?.liberer(t.credits.reservationId).catch(() => {}); }
    await this.o.clientDe(t.moteurId)?.supprimer(id).catch(() => {});
    this.travaux.delete(id);
    this.sauver();
  }

  /** Nettoyage périodique : travaux terminés/échoués trop anciens, dépôts jamais lancés. Retourne les identifiants supprimés. */
  async nettoyer(): Promise<string[]> {
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
