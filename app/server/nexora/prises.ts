/**
 * Prises par plan et compteur de coût du projet (ce qui se vend dans les démos de Higgsfield : on voit ce que coûtent
 * aussi les prises écartées). Une prise est brouillon (FastH3, 832×480, rapide) ou finale (cinéma, pleine résolution) ;
 * le brouillon sert à choisir, la finale ne part que pour une prise gardée. Pur : la lecture des prises est injectée.
 */
import { devisCredits, secondesGpuEstimees, type CorpsDevis } from './credits.js';

export type StatutPrise = 'queued' | 'running' | 'done' | 'failed' | 'stopped';

export interface LecturePrise {
  status: string;
  /** Paramètres de rendu de la prise (largeur, hauteur, images, recette) : le coût s'en déduit. */
  corps: CorpsDevis;
}

/** État des prises d'un plan, tel que stocké dans le storyboard du film. */
export interface PrisesDuPlan {
  /** Prise retenue pour l'assemblage. */
  take?: number;
  /** Candidats du juge visuel (« 2 prises par plan »). */
  candidats?: number[];
  /** Prises ajoutées à la main : brouillons rapides et finales cinéma. */
  extra?: { take: number; brouillon: boolean; finalDe?: number }[];
  rejetees?: number[];
}

export interface PriseVue {
  take: number;
  statut: StatutPrise;
  brouillon: boolean;
  finalDe?: number;
  retenue: boolean;
  rejetee: boolean;
  /** Crédits et secondes de calcul de cette prise : 0 si elle a échoué (un échec technique n'est pas facturé). */
  credits: number;
  secondes: number;
}

const STATUTS: StatutPrise[] = ['queued', 'running', 'done', 'failed', 'stopped'];

export function prisesDuPlan(p: PrisesDuPlan, lire: (id: number) => LecturePrise | undefined, tarif: { creditsParSecondeGpu: number }): PriseVue[] {
  const ids = [...new Set([...(p.candidats ?? []), ...(p.take !== undefined ? [p.take] : []), ...(p.extra ?? []).map((x) => x.take)])];
  const rejetees = new Set(p.rejetees ?? []);
  return ids.flatMap((id): PriseVue[] => {
    const t = lire(id);
    if (!t) return [];
    const extra = p.extra?.find((x) => x.take === id);
    const statut = (STATUTS as string[]).includes(t.status) ? (t.status as StatutPrise) : 'queued';
    const facture = statut !== 'failed' && statut !== 'stopped';
    return [{
      take: id, statut, brouillon: !!extra?.brouillon, ...(extra?.finalDe ? { finalDe: extra.finalDe } : {}),
      retenue: p.take === id, rejetee: rejetees.has(id) && p.take !== id,
      credits: facture ? devisCredits(t.corps, tarif) : 0, secondes: facture ? secondesGpuEstimees(t.corps) : 0,
    }];
  });
}

export interface Compteur {
  credits: number;
  secondes: number;
  prises: number;
  /** Part du coût des prises écartées (rejetées, ou brouillons non finalisés) : le coût de l'exploration. */
  ecartees: { credits: number; secondes: number; prises: number };
  brouillons: number;
}

/** Une prise est « écartée » quand elle n'est pas dans le film final : rejetée, non retenue, ou brouillon. */
export function compteurProjet(plans: PriseVue[][]): Compteur {
  const c: Compteur = { credits: 0, secondes: 0, prises: 0, ecartees: { credits: 0, secondes: 0, prises: 0 }, brouillons: 0 };
  for (const prises of plans) {
    const aRetenue = prises.some((p) => p.retenue);
    for (const p of prises) {
      if (p.statut === 'failed' || p.statut === 'stopped') continue;
      c.credits += p.credits; c.secondes += p.secondes; c.prises++;
      if (p.brouillon) c.brouillons++;
      if (!p.retenue && (aRetenue || p.rejetee || p.brouillon)) { c.ecartees.credits += p.credits; c.ecartees.secondes += p.secondes; c.ecartees.prises++; }
    }
  }
  return c;
}

type Corps = Record<string, any>;

/** Ce qui rattache une prise au film (assemblage, contrôle qualité, réservation) ne se copie jamais sur une prise ajoutée. */
const SANS_FILM = { nexoraFilm: undefined, nexoraPlan: undefined, nexoraCredits: undefined, promptSource: undefined, take: undefined, corps: undefined, attente: undefined } as const;

const RAPIDE = (w: number, h: number): [number, number] => (w === h ? [640, 640] : w > h ? [832, 480] : [480, 832]);
const CINEMA = (w: number, h: number): [number, number] => (w === h ? [1024, 1024] : w > h ? [1344, 768] : [768, 1344]);

/**
 * Brouillon d'un plan : même description, résolution basse, graine nouvelle (on explore). Un plan qui porte des références
 * (personnage @, image de composition) reste sur le point de contrôle ref2va à basse résolution : FastH3 ne lit pas les
 * références ; sans références, c'est la recette rapide FastH3.
 */
export function corpsBrouillonDe(base: Corps, graine: number, rapideBase: Corps): Corps {
  if (base.refImages?.length) {
    // Le nœud de référence H3 exige des côtés multiples de 64 (832×480 est refusé à la validation) : 768×448.
    const [rw, rh]: [number, number] = base.width === base.height ? [640, 640] : base.width > base.height ? [768, 448] : [448, 768];
    return { ...base, ...SANS_FILM, width: rw, height: rh, seed: graine, brouillon: true };
  }
  const [w, h] = RAPIDE(base.width, base.height);
  return { ...rapideBase, ...SANS_FILM, prompt: base.prompt, width: w, height: h, seed: graine, brouillon: true, ...(base.startImage ? { startImage: base.startImage } : {}) };
}

/**
 * Finale d'une prise de brouillon gardée : la recette cinéma du plan avec la graine et le prompt du brouillon ; si le
 * brouillon portait des références (ou une image de départ), on garde son corps et on passe seulement à pleine résolution.
 */
export function corpsFinalDe(brouillon: Corps, cinemaDuPlan: Corps): Corps {
  if (brouillon.refImages?.length || brouillon.startImage) {
    const [w, h] = CINEMA(brouillon.width, brouillon.height);
    return { ...brouillon, ...SANS_FILM, width: w, height: h, brouillon: undefined };
  }
  return { ...cinemaDuPlan, ...SANS_FILM, prompt: brouillon.prompt, seed: brouillon.seed, brouillon: undefined };
}
