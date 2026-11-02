/**
 * Agent « Producteur » de Nexora Creative (feuille de route R9) : la personne écrit un objectif, l'agent propose un plan
 * de production (plans H3, bible de continuité, musique, réplique, cartons de texte), le code en calcule le devis, la
 * personne valide d'un clic, et l'exécution passe par les routes ordinaires du studio (file de rendus, crédits,
 * licences, modération) : jamais à côté.
 *
 * Garde-fous, tous dans le code et pas dans le prompt :
 *  - le LLM n'a AUCUN outil qui dépense : `proposer_production` et `refaire_plan` ne font que préparer une proposition ;
 *    seule `validerProposition` (appelée par un clic de la personne) exécute, une seule fois par proposition ;
 *  - plafond de dépense par proposition (crédits, ou secondes de GPU sur un poste sans crédits) ;
 *  - boucle bornée : `maxEtapes` appels au modèle par message, budget de jetons par session, historique tronqué ;
 *  - procédures versionnées (server/nexora/competences/*.md), pas de chaînes en dur.
 */
import { randomUUID } from 'node:crypto';
import { z } from 'zod';
import { avecCompetences } from './competences.js';
import { lireCartons, type Carton } from './cartons.js';
import { corpsRendu, type MoteurVideo } from './creer.js';
import { devisCredits, secondesGpuEstimees } from './credits.js';
import { MAX_PLANS, type Storyboard } from './film.js';
import type { ClientLlm, DefinitionOutil, MessageLlm } from './llm.js';
import { DEFINITIONS_MONTAGE, executerOutilMontage, type DepsMontage, type EtatMontage } from './montage/outils.js';

// ---------------------------------------------------------------------------------------------------------------------
// Plan de production

export interface PlanProduction {
  titre: string;
  format: '16:9' | '9:16' | '1:1';
  qualite: 'rapide' | 'max';
  son: boolean;
  bible: Storyboard['bible'];
  plans: { resume: string; description: string; camera: string; duree: 5 | 10; suite?: boolean; replique?: string }[];
  musique: { envie: string } | null;
  cartons: Carton[];
  /** 2 : deux prises par plan indépendant, le juge visuel garde la meilleure (coût doublé pour ces plans). */
  candidats: 1 | 2;
}

export const DUREE_MAX_S = 120;
const txt = (v: unknown, max: number) => (typeof v === 'string' ? v.trim().slice(0, max) : '');
const entites = (v: unknown) =>
  (Array.isArray(v) ? v : []).map((e: any) => ({ nom: txt(e?.nom, 80), description: txt(e?.description, 600) })).filter((e) => e.nom || e.description).slice(0, 8);

/** Lit (et borne) un plan proposé par le LLM ou renvoyé par le navigateur. Lève une erreur lisible s'il est inutilisable. */
export function lirePlanProduction(o: unknown): PlanProduction {
  const b = (o ?? {}) as Record<string, any>;
  const plans = (Array.isArray(b.plans) ? b.plans : [])
    .map((p: any) => ({
      resume: txt(p?.resume, 160),
      description: txt(p?.description, 1200),
      camera: txt(p?.camera, 300),
      duree: (Number(p?.duree) >= 8 ? 10 : 5) as 5 | 10,
      ...(p?.suite === true ? { suite: true } : {}),
      ...(txt(p?.replique, 200) ? { replique: txt(p?.replique, 200) } : {}),
    }))
    .filter((p: { description: string; resume: string }) => p.description || p.resume)
    .map((p: any) => ({ ...p, description: p.description || p.resume, resume: p.resume || p.description.slice(0, 80) }));
  if (!plans.length) throw new Error('Le plan doit contenir au moins un plan tourné.');
  if (plans.length > MAX_PLANS) throw new Error(`${MAX_PLANS} plans au plus.`);
  const duree = plans.reduce((n: number, p: { duree: number }) => n + p.duree, 0);
  if (duree > DUREE_MAX_S) throw new Error(`Durée totale de ${duree} s : ${DUREE_MAX_S} s au plus.`);
  delete plans[0].suite;
  const envie = txt(b.musique?.envie ?? (typeof b.musique === 'string' ? b.musique : ''), 300);
  return {
    titre: txt(b.titre, 120) || 'Sans titre',
    format: b.format === '9:16' || b.format === '1:1' ? b.format : '16:9',
    qualite: b.qualite === 'max' ? 'max' : 'rapide',
    son: b.son !== false,
    bible: { style: txt(b.bible?.style, 600), personnages: entites(b.bible?.personnages), lieux: entites(b.bible?.lieux) },
    plans,
    musique: envie ? { envie } : null,
    cartons: lireCartons(b.cartons),
    candidats: Number(b.candidats) >= 2 ? 2 : 1,
  };
}

export function planVersStoryboard(p: PlanProduction): Storyboard {
  return {
    titre: p.titre,
    bible: p.bible,
    plans: p.plans.map((x) => ({ ...x })),
    dureeTotale: p.plans.reduce((n, x) => n + x.duree, 0),
  };
}

// ---------------------------------------------------------------------------------------------------------------------
// Devis

export interface Devis {
  /** null sur un poste sans crédits (développement, installation locale). */
  credits: number | null;
  /** Estimation en crédits, toujours renseignée : sur un poste sans portail, rien n'est débité mais le coût réel est visible. */
  creditsEstimes: number;
  /** Temps de calcul vidéo estimé (s), tous rendus confondus. */
  secondesGpu: number;
  /** Temps d'attente estimé (min), écriture des prompts et assemblage compris. */
  minutes: number;
  rendus: number;
  plans: number;
  musique: boolean;
  candidats: 1 | 2;
}

export function devisProduction(p: PlanProduction, o: { moteur: MoteurVideo; creditsActifs: boolean; tarif: { creditsParSecondeGpu: number } }): Devis {
  let credits = 0;
  let secondes = 0;
  let rendus = 0;
  for (const x of p.plans) {
    const corps = corpsRendu({ intention: x.resume, format: p.format, duree: x.duree, son: p.son, qualite: p.qualite }, '', o.moteur);
    const n = p.candidats === 2 && !x.suite ? 2 : 1;
    rendus += n;
    credits += n * devisCredits(corps, o.tarif);
    secondes += n * secondesGpuEstimees(corps);
  }
  return {
    credits: o.creditsActifs ? credits : null,
    creditsEstimes: credits,
    secondesGpu: secondes,
    minutes: Math.max(1, Math.ceil((secondes + 15 * p.plans.length + 30) / 60)),
    rendus, plans: p.plans.length, musique: !!p.musique, candidats: p.candidats,
  };
}

/** Phrase de refus si le devis dépasse le plafond, sinon null. */
export function depassement(d: Pick<Devis, 'credits' | 'secondesGpu'>, plafond: { credits: number; secondes: number }): string | null {
  if (d.credits !== null && d.credits > plafond.credits) return `Devis de ${d.credits} crédits : au-dessus du plafond de ${plafond.credits} crédits par production.`;
  if (d.credits === null && d.secondesGpu > plafond.secondes) return `Environ ${Math.ceil(d.secondesGpu / 60)} min de calcul : au-dessus du plafond de ${Math.round(plafond.secondes / 60)} min par production.`;
  return null;
}

// ---------------------------------------------------------------------------------------------------------------------
// Session

export type Proposition =
  | { id: string; genre: 'production'; plan: PlanProduction; devis: Devis; base?: number }
  | { id: string; genre: 'refaire'; film: number; plan: number; description?: string; camera?: string; devis: Devis }
  | { id: string; genre: 'remontage'; film: number; ordre: number[]; transition: 'coupe' | 'fondu'; devis: Devis };

export interface Bulle { de: 'personne' | 'producteur' | 'systeme'; texte: string; date: string; proposition?: string; production?: number }
export interface Production { filmId: number; plan?: PlanProduction; lanceLe: string; genre?: Proposition['genre'] }

export interface SessionProducteur {
  id: string;
  titre: string;
  messages: MessageLlm[];
  fil: Bulle[];
  proposition: Proposition | null;
  productions: Production[];
  jetons: number;
  /** Montage en cours (outils de montage : plan_edit, critique, revise). */
  montage?: EtatMontage;
}

export function nouvelleSession(): SessionProducteur {
  return { id: randomUUID(), titre: 'Nouvelle production', messages: [], fil: [], proposition: null, productions: [], jetons: 0 };
}

const maintenant = () => new Date().toISOString();
const bulle = (s: SessionProducteur, b: Omit<Bulle, 'date'>) => { s.fil.push({ ...b, date: maintenant() }); s.fil = s.fil.slice(-80); };

// ---------------------------------------------------------------------------------------------------------------------
// Outils vus par le modèle

const schemaPlan = z.object({
  titre: z.string().describe('Titre court, en français'),
  format: z.enum(['16:9', '9:16', '1:1']),
  qualite: z.enum(['rapide', 'max']).describe('rapide par défaut ; max = H3 complet, 10× plus long'),
  son: z.boolean().describe('son natif H3 (bruitages, voix)'),
  bible: z.object({
    style: z.string(),
    personnages: z.array(z.object({ nom: z.string(), description: z.string() })),
    lieux: z.array(z.object({ nom: z.string(), description: z.string() })),
  }).describe('ce qui doit rester identique d’un plan à l’autre, en anglais'),
  plans: z.array(z.object({
    resume: z.string().describe('phrase courte en français pour l’interface'),
    description: z.string().describe('le plan, en anglais, concret et visuel ; jamais de texte ni de logo à l’écran'),
    camera: z.string(),
    duree: z.union([z.literal(5), z.literal(10)]),
    suite: z.boolean().optional().describe('prolonge le plan précédent depuis sa dernière image'),
    replique: z.string().optional().describe('ce qu’un personnage dit dans ce plan (français), voix synchronisée'),
  })).min(1).max(MAX_PLANS),
  musique: z.object({ envie: z.string() }).nullable().describe('bande originale MiniMax-Music3 ; null pour aucune'),
  cartons: z.array(z.object({ texte: z.string().max(80), position: z.enum(['debut', 'fin']) })).max(3).describe('texte posé en code : titre, slogan, appel à l’action'),
  candidats: z.union([z.literal(1), z.literal(2)]).optional().describe('2 = deux prises par plan, le juge garde la meilleure (coût ×2)'),
});

const definitions: { nom: string; description: string; schema: z.ZodType }[] = [
  { nom: 'etat_studio', description: 'Moteurs en ligne (vidéo, image, musique), territoire, juge visuel disponible ou non.', schema: z.object({}) },
  { nom: 'proposer_production', description: 'Propose un plan de production complet ; le code renvoie le devis. Ne lance rien : la personne valide.', schema: schemaPlan },
  { nom: 'lister_creations', description: 'Les 12 dernières créations de la personne (id, type, titre, état).', schema: z.object({}) },
  { nom: 'voir_production', description: 'État d’un film lancé : plans tournés, contrôle qualité, choix du juge.', schema: z.object({ film: z.number().int() }) },
  { nom: 'refaire_plan', description: 'Prépare la reprise d’un seul plan d’un film terminé (devis à valider).', schema: z.object({ film: z.number().int(), plan: z.number().int().min(1).describe('numéro du plan, à partir de 1'), description: z.string().optional(), camera: z.string().optional() }) },
  { nom: 'remonter', description: 'Prépare un nouveau montage d’un film terminé, sans nouveau rendu (ordre des plans, plans retirés, fondu).', schema: z.object({ film: z.number().int(), ordre: z.array(z.number().int().min(1)).min(1), transition: z.enum(['coupe', 'fondu']).optional() }) },
];

export const OUTILS_PRODUCTEUR: DefinitionOutil[] = [...definitions, ...DEFINITIONS_MONTAGE].map((d) => {
  const js = z.toJSONSchema(d.schema) as Record<string, unknown>;
  delete js.$schema;
  return { nom: d.nom, description: d.description, parametres: js };
});

// ---------------------------------------------------------------------------------------------------------------------
// Boucle

export interface DepsAgent {
  llm: ClientLlm | null;
  /** Devis d'un plan (moteur du compte, tarif, crédits actifs ou non) : calculé par le code, jamais par le LLM. */
  devis: (p: PlanProduction) => Devis;
  plafond: { credits: number; secondes: number };
  /** Outils de lecture (sans dépense) : etat_studio, lister_creations, voir_production, devis_plan. */
  outils: Partial<Record<'etat_studio' | 'lister_creations' | 'voir_production', (args: any) => Promise<unknown>>> & {
    devisPlan?: (film: number, plan: number) => Promise<Devis>;
  };
  /** Personnages @ de l'organisation : la liste est donnée au modèle, et un plan qui en cite un passe en qualité cinéma (Ref2VA). */
  personnages?: { liste: () => string; cite: (texte: string) => boolean };
  /** Médias du projet pour les outils de montage ; absent = outils indisponibles. */
  montage?: DepsMontage;
  maxEtapes?: number;
  maxJetonsSession?: number;
}

const CONSIGNES = 'Tu pilotes Nexora Creative pour la personne. Utilise les outils ; réponds en français, brièvement.';
const MAX_HISTORIQUE = 24;
const MAX_RESULTAT = 2500;

/** Garde les derniers messages, en coupant sur un message de la personne (jamais au milieu d'un appel d'outil). */
export function tronquer(m: MessageLlm[], max = MAX_HISTORIQUE): MessageLlm[] {
  if (m.length <= max) return m;
  let debut = m.length - max;
  while (debut < m.length && m[debut].role !== 'user') debut++;
  return m.slice(debut);
}

export async function tourProducteur(session: SessionProducteur, message: string, deps: DepsAgent): Promise<SessionProducteur> {
  const s: SessionProducteur = structuredClone(session);
  const demande = message.trim().slice(0, 4000);
  bulle(s, { de: 'personne', texte: demande });
  if (s.titre === 'Nouvelle production') s.titre = demande.slice(0, 60);
  if (!deps.llm?.completerAvecOutils) {
    bulle(s, { de: 'systeme', texte: 'Le Producteur n’est pas disponible : aucun modèle de langage n’est branché sur ce poste.' });
    return s;
  }
  if (s.jetons >= (deps.maxJetonsSession ?? 200_000)) {
    bulle(s, { de: 'systeme', texte: 'Cette conversation a atteint sa limite. Ouvre une nouvelle production pour continuer.' });
    return s;
  }
  s.messages = tronquer([...s.messages, { role: 'user', content: demande }]);
  const propositionAvant = s.proposition?.id;
  const max = deps.maxEtapes ?? 6;
  let reponse = '';
  for (let etape = 0; etape < max; etape++) {
    // Les modèles qui raisonnent consomment une partie du plafond avant de répondre : 6 000 jetons au plus par étape.
    const r = await deps.llm.completerAvecOutils('producteur', [{ role: 'system', content: avecCompetences('producteur', deps.personnages?.liste() ? `${CONSIGNES}\n${deps.personnages.liste()}` : CONSIGNES) }, ...s.messages], OUTILS_PRODUCTEUR, { maxTokens: 6000 });
    s.jetons += r.jetons;
    if (!r.appels.length && !r.texte.trim()) {
      // Réponse vide (raisonnement coupé) : une relance courte, comptée dans les étapes.
      s.messages.push({ role: 'user', content: 'Continue : appelle l’outil voulu ou réponds en 2 à 4 phrases.' });
      continue;
    }
    s.messages.push({ role: 'assistant', content: r.texte, ...(r.appels.length ? { appels: r.appels } : {}) });
    if (!r.appels.length) { reponse = r.texte.trim(); break; }
    for (const a of r.appels) {
      let resultat: unknown;
      try {
        resultat = a.illisible ? { erreur: 'arguments illisibles : renvoie un objet JSON valide' } : await executerOutil(s, a.nom, a.arguments, deps);
      } catch (e) {
        resultat = { erreur: e instanceof Error ? e.message : String(e) };
      }
      const texte = JSON.stringify(resultat) ?? 'null';
      s.messages.push({ role: 'tool', appelId: a.id, content: texte.length > MAX_RESULTAT ? `${texte.slice(0, MAX_RESULTAT)}…` : texte });
    }
  }
  const nouvelle = s.proposition && s.proposition.id !== propositionAvant ? s.proposition.id : undefined;
  if (!reponse) reponse = nouvelle ? 'J’ai préparé le plan ci-dessous. Valide le devis pour lancer le tournage.' : 'Je n’ai pas pu terminer. Reformule ta demande en une phrase.';
  bulle(s, { de: 'producteur', texte: reponse.slice(0, 3000), ...(nouvelle ? { proposition: nouvelle } : {}) });
  s.messages = tronquer(s.messages);
  return s;
}

async function executerOutil(s: SessionProducteur, nom: string, args: Record<string, unknown>, deps: DepsAgent): Promise<unknown> {
  switch (nom) {
    case 'proposer_production': {
      const plan = lirePlanProduction(args);
      // Un personnage @ cité dans un plan exige la qualité cinéma : seul le moteur Ref2VA lit ses images de référence.
      if (deps.personnages && plan.plans.some((x) => deps.personnages!.cite(`${x.resume} ${x.description}`))) plan.qualite = 'max';
      const devis = deps.devis(plan);
      const refus = depassement(devis, deps.plafond);
      if (refus) return { erreur: `${refus} Raccourcis (moins de plans, qualité rapide, un seul candidat) et propose à nouveau.`, devis };
      s.proposition = { id: randomUUID(), genre: 'production', plan, devis };
      return { ok: true, devis, note: 'Proposition affichée à la personne avec un bouton de validation.' };
    }
    case 'refaire_plan': {
      const film = Number(args.film), plan = Number(args.plan) - 1;
      if (!s.productions.some((p) => p.filmId === film)) return { erreur: `le film ${film} n’appartient pas à cette production` };
      const devis = deps.outils.devisPlan ? await deps.outils.devisPlan(film, plan) : null;
      if (!devis) return { erreur: 'devis impossible pour ce plan' };
      s.proposition = { id: randomUUID(), genre: 'refaire', film, plan, description: txt(args.description, 1200) || undefined, camera: txt(args.camera, 300) || undefined, devis };
      return { ok: true, devis };
    }
    case 'remonter': {
      const film = Number(args.film);
      if (!s.productions.some((p) => p.filmId === film)) return { erreur: `le film ${film} n’appartient pas à cette production` };
      const ordre = (Array.isArray(args.ordre) ? args.ordre : []).map((x) => Number(x) - 1);
      const devis: Devis = { credits: 0, creditsEstimes: 0, secondesGpu: 0, minutes: 1, rendus: 0, plans: ordre.length, musique: false, candidats: 1 };
      s.proposition = { id: randomUUID(), genre: 'remontage', film, ordre, transition: args.transition === 'fondu' ? 'fondu' : 'coupe', devis };
      return { ok: true, devis, note: 'montage sans nouveau rendu' };
    }
    case 'analyze_media':
    case 'plan_edit':
    case 'critique':
    case 'revise': {
      const r = await executerOutilMontage(s.montage, nom, args, deps);
      s.montage = r.etat;
      return r.resultat;
    }
    case 'etat_studio':
    case 'lister_creations':
    case 'voir_production': {
      const f = deps.outils[nom];
      if (!f) return { erreur: 'outil indisponible' };
      return f(args);
    }
    default:
      return { erreur: `outil inconnu : ${nom}` };
  }
}

// ---------------------------------------------------------------------------------------------------------------------
// Validation (clic de la personne) et variantes en un clic

export async function validerProposition(
  session: SessionProducteur,
  id: string,
  deps: { executer: (p: Proposition) => Promise<{ filmId: number }>; plafond: { credits: number; secondes: number } },
): Promise<SessionProducteur> {
  const s: SessionProducteur = structuredClone(session);
  const p = s.proposition;
  if (!p || p.id !== id) throw new Error('Cette proposition n’est plus valable : demande un nouveau devis.');
  const refus = depassement(p.devis, deps.plafond);
  if (refus) throw new Error(refus);
  // La proposition est retirée avant l'exécution : un double clic ne peut pas dépenser deux fois.
  s.proposition = null;
  const { filmId } = await deps.executer(p);
  s.productions.push({ filmId, lanceLe: maintenant(), genre: p.genre, ...(p.genre === 'production' ? { plan: p.plan } : {}) });
  bulle(s, { de: 'systeme', texte: p.genre === 'remontage' ? 'Nouveau montage en cours (aucun nouveau rendu).' : 'Tournage lancé. Le film s’assemble tout seul à la fin.', production: filmId });
  return s;
}

export type GenreVariante = 'format-16:9' | 'format-9:16' | 'format-1:1' | 'nouvelle-prise' | 'cinema' | 'courte';

/** Variante en un clic d'une production lancée : un nouveau devis à valider, sans appel au LLM. */
export function variante(session: SessionProducteur, filmId: number, genre: GenreVariante, devis: (p: PlanProduction) => Devis): SessionProducteur {
  const s: SessionProducteur = structuredClone(session);
  const prod = [...s.productions].reverse().find((p) => p.filmId === filmId);
  const base = prod?.plan ?? [...s.productions].reverse().find((p) => p.plan)?.plan;
  if (!prod || !base) throw new Error('Production introuvable dans cette conversation.');
  if (genre === 'courte') {
    // Version courte : le premier plan et les deux derniers (là où sont le produit et l'appel à l'action), sans rendu.
    const n = base.plans.length;
    const ordre = n <= 3 ? [0, n - 1].filter((v, i, a) => a.indexOf(v) === i) : [0, n - 2, n - 1];
    s.proposition = { id: randomUUID(), genre: 'remontage', film: filmId, ordre, transition: 'coupe', devis: { credits: 0, creditsEstimes: 0, secondesGpu: 0, minutes: 1, rendus: 0, plans: ordre.length, musique: false, candidats: 1 } };
  } else {
    const plan: PlanProduction = structuredClone(base);
    if (genre.startsWith('format-')) plan.format = genre.slice(7) as PlanProduction['format'];
    if (genre === 'cinema') plan.qualite = 'max';
    s.proposition = { id: randomUUID(), genre: 'production', plan, devis: devis(plan), base: filmId };
  }
  const libelles: Record<GenreVariante, string> = {
    'format-16:9': 'Variante paysage (16:9)', 'format-9:16': 'Variante verticale (9:16)', 'format-1:1': 'Variante carrée (1:1)',
    'nouvelle-prise': 'Nouvelle prise du même plan', cinema: 'Version qualité cinéma (H3 complet)', courte: 'Version courte, sans nouveau rendu',
  };
  bulle(s, { de: 'producteur', texte: `${libelles[genre]} : voici le devis.`, proposition: s.proposition!.id });
  return s;
}

/** Réglages modifiables d'un clic sur la carte du devis (sans repasser par le LLM). */
export function ajusterProposition(
  session: SessionProducteur, id: string,
  r: { candidats?: number; qualite?: string; format?: string; son?: boolean; musique?: boolean },
  devis: (p: PlanProduction) => Devis,
): SessionProducteur {
  const s: SessionProducteur = structuredClone(session);
  const p = s.proposition;
  if (!p || p.id !== id || p.genre !== 'production') throw new Error('Cette proposition n’est plus valable.');
  const plan = structuredClone(p.plan);
  if (r.candidats !== undefined) plan.candidats = r.candidats >= 2 ? 2 : 1;
  if (r.qualite === 'rapide' || r.qualite === 'max') plan.qualite = r.qualite;
  if (r.format === '16:9' || r.format === '9:16' || r.format === '1:1') plan.format = r.format;
  if (typeof r.son === 'boolean') plan.son = r.son;
  if (r.musique === false) plan.musique = null;
  if (r.musique === true && !plan.musique) plan.musique = { envie: '' };
  s.proposition = { ...p, id: randomUUID(), plan, devis: devis(plan) };
  return s;
}
