/**
 * Modules de mémoire réutilisables par le montage et (plus tard) par l'écriture de films (recherche/20).
 *
 * 1. `MemoireProfesseur` : AMD proprement dit (agent-memory-distillation.github.io) : trajectoires RÉUSSIES d'un
 *    professeur (Claude Opus 5.5) sur des briefs d'APPRENTISSAGE seulement (`memoire/professeur/*.json`), distillées en
 *    trois niveaux : workflow (prose, top-1 par brief), sous-tâches (une par phase du film : description + bloc de code,
 *    top-1 par phase) et fonction (indice + exemple valide, injecté SEULEMENT quand le validateur refuse).
 * 2. `BanqueStrategies` : façon ReasoningBank (arXiv 2509.25140) : l'élève juge lui-même sa trajectoire (sans vérité
 *    terrain), puis en tire ≤ 3 stratégies {titre, description, contenu} depuis ses réussites ET ses échecs ; récupération
 *    top-1, injection dans le message système ; consolidation par simple ajout (dédoublonnée, plafonnée).
 * Le savoir est du texte et du JSON : jamais exécuté. Aucune donnée d'un brief de test n'entre ici (banc scellé).
 */
import { existsSync, readFileSync, readdirSync, writeFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { type ClientLlm, lireJson } from '../llm.js';
import type { Violation } from './editplan.js';
import type { BriefFilm, ExemplaireTournage, Tournage } from './film.js';
import type { ListeMontage } from './liste.js';
import { indicesFonction } from './memoire.js';
import type { Brief } from './types.js';

const DOSSIER = join(dirname(fileURLToPath(import.meta.url)), '../memoire');
const MOTS = (t: string) => new Set(t.toLowerCase().normalize('NFD').replace(/[̀-ͯ]/g, '').split(/[^a-z0-9]+/).filter((w) => w.length > 3));
const recouvrement = (a: Set<string>, b: Set<string>) => [...a].filter((w) => b.has(w)).length;
const f1 = (x: number) => (Math.round(x * 100) / 100).toString().replace('.', ',');

/** Interface commune : ce qu'un module de mémoire apporte AVANT l'exécution et SUR ERREUR. */
export interface ModuleMemoire {
  nom: string;
  /** Bloc injecté au début du message utilisateur (proactif). */
  avant?(etape: 'tournage' | 'montage', b: BriefFilm, bm?: Brief): string;
  /** Bloc ajouté au message système (ReasoningBank injecte là). */
  systeme?(etape: 'tournage' | 'montage', b: BriefFilm): string;
  /** Exemplaire de tournage (k = 1). */
  tournage?(b: BriefFilm): ExemplaireTournage | null;
  /** Indices joints au message d'erreur du validateur (réactif). */
  surErreur?(etape: 'tournage' | 'montage', v: Violation[]): string[];
}

/** Compose plusieurs modules (C + D = E) : blocs concaténés, indices réunis, premier exemplaire trouvé. */
export function composer(...ms: (ModuleMemoire | null | undefined)[]): ModuleMemoire | undefined {
  const l = ms.filter((m): m is ModuleMemoire => !!m);
  if (!l.length) return undefined;
  if (l.length === 1) return l[0];
  return {
    nom: l.map((m) => m.nom).join('+'),
    avant: (e, b, bm) => l.map((m) => m.avant?.(e, b, bm) ?? '').join(''),
    systeme: (e, b) => l.map((m) => m.systeme?.(e, b) ?? '').filter(Boolean).join('\n\n'),
    tournage: (b) => l.map((m) => m.tournage?.(b) ?? null).find(Boolean) ?? null,
    surErreur: (e, v) => [...new Set(l.flatMap((m) => m.surErreur?.(e, v) ?? []))],
  };
}

// ---------------------------------------------------------------------------------------------------------------------
// 1. AMD : mémoire du professeur à trois niveaux

export type Phase = 'accroche' | 'montee' | 'respiration' | 'apogee' | 'resolution' | 'carton';
export interface TrajectoireProfesseur {
  id: string; version: number; professeur: string; partition: 'apprentissage';
  brief: Pick<BriefFilm, 'id' | 'titre' | 'genre' | 'format' | 'duree_cible_s' | 'bpm' | 'mots' | 'enonce'>;
  workflow: string; tournage: Tournage; liste: { gain_db?: number; plans: (ListeMontage['plans'][number] & { phase: Phase })[] };
}

const ROLE_PHASE: Record<Phase, string> = {
  accroche: 'Accroche : capter avant 3 s, un texte court qui couvre aussi le plan suivant',
  montee: 'Montée : une idée par plan, textes très courts',
  respiration: 'Respiration : un plan large plus long, sans texte, juste avant l\'apogée',
  apogee: 'Apogée : plans les plus courts, sans texte, nouveaux passages de sources déjà vues',
  resolution: 'Résolution : la promesse, un texte sur deux plans',
  carton: 'Carton : marque mot pour mot, fondu',
};

export function chargerTrajectoires(dossier = join(DOSSIER, 'professeur')): TrajectoireProfesseur[] {
  if (!existsSync(dossier)) return [];
  return readdirSync(dossier).filter((f) => f.endsWith('.json')).sort().map((f) => JSON.parse(readFileSync(join(dossier, f), 'utf8')) as TrajectoireProfesseur);
}

/** Remplace les jetons typés par les valeurs du brief (le professeur écrit `<MARQUE>`, `<DUREE_S>`). */
export const instancier = (t: string, b: Pick<BriefFilm, 'marque' | 'duree_cible_s'>) => t.replace(/<MARQUE>/g, b.marque).replace(/<DUREE_S>/g, String(b.duree_cible_s));

/** Liste du professeur prête à compiler pour SON brief d'apprentissage (contrôle de santé). */
export function listeDuProfesseur(t: TrajectoireProfesseur, marque: string): ListeMontage {
  return { gain_db: t.liste.gain_db ?? -8, plans: t.liste.plans.map(({ phase: _p, ...p }) => ({ tr: 'cut', ...p, texte: p.texte ? instancier(p.texte, { marque, duree_cible_s: t.brief.duree_cible_s }) : undefined })) as ListeMontage['plans'] };
}

/** Sous-tâche distillée : les lignes d'une phase, sources anonymisées (<SRC_A>…), durée des sources et place du texte annotées. */
export function sousTache(t: TrajectoireProfesseur, phase: Phase): string | null {
  const plans = t.liste.plans;
  const idx = plans.map((p, i) => [p, i] as const).filter(([p]) => p.phase === phase);
  if (!idx.length) return null;
  const debut = plans.slice(0, idx[0][1]).reduce((s, p) => s + p.dur, 0);
  const fin = debut + idx.reduce((s, [p]) => s + p.dur, 0);
  const alias = new Map<string, string>();
  const nom = (src: string) => (src === 'carton' ? 'carton' : (alias.get(src) ?? (alias.set(src, `<SRC_${String.fromCharCode(65 + alias.size)}>`), alias.get(src)!)));
  const dureeSrc = (src: string) => { const k = Number(src.slice(1)) - 1; const p = t.tournage.plans[k]; return src === 'carton' ? 8 : p ? (p.duree === 10 ? 10.2 : 5.1) : 5.1; };
  const lignes = idx.map(([p]) => {
    const o: Record<string, unknown> = { src: nom(p.src), in: p.in ?? 0, dur: p.dur };
    if (p.tr && p.tr !== 'cut') o.tr = p.tr;
    if (p.texte) o.texte = p.texte;
    const notes = [`source de ${f1(dureeSrc(p.src))} s, lit ${f1(p.in ?? 0)}→${f1((p.in ?? 0) + p.dur)}`];
    if (p.texte && p.texte !== '<MARQUE>') notes.push(`${[...p.texte].length} caractères`);
    return `${JSON.stringify(o)}   // ${notes.join(', ')}`;
  });
  return `${ROLE_PHASE[phase]} (${f1(debut)}-${f1(fin)} s, ${idx.length} plan${idx.length > 1 ? 's' : ''}) :\n${lignes.join('\n')}`;
}

export class MemoireProfesseur implements ModuleMemoire {
  nom = 'amd-professeur';
  trajectoires: TrajectoireProfesseur[];
  constructor(o: { trajectoires?: TrajectoireProfesseur[]; dossier?: string } = {}) { this.trajectoires = o.trajectoires ?? chargerTrajectoires(o.dossier); }
  /** Note de proximité d'une trajectoire pour un brief : genre (4) + durée proche (≤ 1,5) + mots (≤ 2). */
  private note(t: TrajectoireProfesseur, b: Pick<BriefFilm, 'genre' | 'duree_cible_s' | 'enonce' | 'mots'>): number {
    const proche = 1.5 * Math.max(0, 1 - Math.abs(Math.log(t.brief.duree_cible_s / b.duree_cible_s)) / Math.log(2));
    return (t.brief.genre === b.genre ? 4 : 0) + proche + Math.min(2, 0.7 * recouvrement(MOTS(`${b.enonce} ${b.mots.join(' ')}`), MOTS(`${t.brief.enonce} ${t.brief.mots.join(' ')}`)));
  }
  meilleure(b: BriefFilm, exclure: (t: TrajectoireProfesseur) => boolean = () => false): TrajectoireProfesseur | null {
    return this.trajectoires.filter((t) => t.brief.id !== b.id && !exclure(t)).map((t) => [t, this.note(t, b)] as const).sort((x, y) => y[1] - x[1])[0]?.[0] ?? null;
  }
  tournage(b: BriefFilm): ExemplaireTournage | null {
    const t = this.meilleure(b);
    return t ? { id: `tournage-${t.id}`, version: t.version, genre: [t.brief.genre], description: t.brief.titre, mots_cles: t.brief.mots, sortie: t.tournage } : null;
  }
  avant(etape: 'tournage' | 'montage', b: BriefFilm): string {
    if (etape !== 'montage') return '';
    const t = this.meilleure(b);
    if (!t) return '';
    // Sous-tâches : pour CHAQUE phase, le segment top-1 parmi les trajectoires du même genre (k = 1 par sous-tâche).
    const memeGenre = this.trajectoires.filter((x) => x.brief.genre === b.genre && x.brief.id !== b.id);
    const phases: Phase[] = ['accroche', 'montee', 'respiration', 'apogee', 'resolution', 'carton'];
    const segs = phases.map((ph) => {
      const source = [t, ...memeGenre.filter((x) => x !== t)].find((x) => x.liste.plans.some((p) => p.phase === ph));
      return source ? sousTache(source, ph) : null;
    }).filter(Boolean);
    return `[savoir-faire du professeur, film « ${t.brief.titre} » : imite la méthode, jamais le sujet ni les mots]\n${instancier(t.workflow, b)}\n\n[sous-tâches du professeur, une par phase : les <SRC_x> sont à remplacer par TES sources ; vérifie in + dur ≤ durée de TA source]\n${segs.map((s) => instancier(s!, b)).join('\n\n')}\n\n`;
  }
  surErreur(etape: 'tournage' | 'montage', v: Violation[]): string[] {
    return indicesFonction(etape === 'montage' ? 'liste_montage' : 'tournage', v);
  }
}

// ---------------------------------------------------------------------------------------------------------------------
// 2. ReasoningBank : stratégies tirées par l'élève de ses réussites ET de ses échecs

export interface Strategie {
  id: string; titre: string; description: string; contenu: string; etape: 'tournage' | 'montage';
  /** Provenance : brief d'apprentissage, palier, verdict du juge (l'élève lui-même), score en code (pour l'étalonnage seulement). */
  source: { brief: string; genre: string; mots: string[]; palier: string; verdict: 'succes' | 'echec'; scoreCode?: number };
}

export interface TraceEleve {
  brief: BriefFilm; palier: string; tournage: Tournage | null; liste: unknown;
  /** Journal du validateur : refus successifs (règles et messages), réparations du code, repli. */
  journal: string[]; premierCoup: boolean; source: 'llm' | 'repli'; scoreCode: number;
}

const resumeTrace = (t: TraceEleve) => [
  `BRIEF : ${t.brief.enonce}`,
  `Genre ${t.brief.genre}, ${t.brief.duree_cible_s} s.`,
  `PLANS TOURNÉS : ${t.tournage ? t.tournage.plans.map((p, i) => `s${i + 1} ${p.duree === 10 ? '10,2' : '5,1'} s ${p.resume}`).join(' | ') : '(tournage invalide)'}`,
  `LISTE DE MONTAGE FINALE : ${JSON.stringify(t.liste)?.slice(0, 2500) ?? '(aucune)'}`,
  `JOURNAL DU VALIDATEUR : ${t.journal.length ? t.journal.join(' / ').slice(0, 1500) : 'accepté du premier coup'}`,
  `ISSUE : ${t.source === 'llm' ? (t.premierCoup ? 'liste acceptée du premier coup' : 'liste acceptée après réparations') : 'liste refusée, le code a monté un repli'}`,
].join('\n');

/** Juge de ReasoningBank : l'élève lui-même, température 0, sans vérité terrain (seulement le journal d'exécution). */
export async function jugerTrace(llm: ClientLlm, t: TraceEleve): Promise<{ succes: boolean; raison: string }> {
  const txt = await llm.completer('juge', [
    { role: 'system', content: 'Tu évalues le travail d\'un agent monteur vidéo. Réponds uniquement par du JSON {"succes":true|false,"raison":"…"}.' },
    { role: 'user', content: `${resumeTrace(t)}\n\nLe film répond-il au brief (accroche, rythme, textes courts et justes, carton de marque) SANS avoir dépendu du repli du code ? succes = true seulement si c'est une réussite nette.` },
  ], { json: true, temperature: 0, maxTokens: 1500 });
  const o = lireJson<{ succes?: unknown; raison?: unknown }>(txt);
  return { succes: o.succes === true, raison: String(o.raison ?? '').slice(0, 300) };
}

/** Extraction de ReasoningBank : ≤ 3 stratégies généralisables, de la réussite (ce qui marche) ou de l'échec (le piège et sa parade). */
export async function extraireStrategies(llm: ClientLlm, t: TraceEleve, verdict: { succes: boolean; raison: string }): Promise<Strategie[]> {
  const consigne = verdict.succes
    ? 'Cette trajectoire est une RÉUSSITE. Tire au plus 3 stratégies réutilisables sur d\'autres films (ce qui a fait marcher le tournage ou le montage).'
    : 'Cette trajectoire est un ÉCHEC. Tire au plus 3 leçons : le piège précis, pourquoi il arrive, et la parade concrète à appliquer la prochaine fois.';
  const txt = await llm.completer('juge', [
    { role: 'system', content: 'Tu distilles l\'expérience d\'un agent monteur en mémoire. Réponds uniquement par du JSON {"strategies":[{"titre":"…","description":"une phrase","contenu":"2 à 4 phrases concrètes","etape":"tournage|montage"}]}. Aucune donnée propre à ce brief (ni sujet, ni texte, ni identifiant de source) : des règles générales.' },
    { role: 'user', content: `${resumeTrace(t)}\nVERDICT : ${verdict.succes ? 'réussite' : 'échec'} — ${verdict.raison}\n\n${consigne}` },
  ], { json: true, temperature: 0, maxTokens: 2000 });
  const o = lireJson<{ strategies?: unknown[] }>(txt);
  return (Array.isArray(o.strategies) ? o.strategies : []).slice(0, 3).flatMap((x: any, k) => {
    const titre = String(x?.titre ?? '').trim().slice(0, 100), contenu = String(x?.contenu ?? '').trim().slice(0, 700);
    if (!titre || !contenu) return [];
    return [{ id: `rb-${t.palier}-${t.brief.id}-${Date.now().toString(36)}-${k}`, titre, description: String(x?.description ?? '').slice(0, 240), contenu, etape: x?.etape === 'tournage' ? 'tournage' : 'montage', source: { brief: t.brief.id, genre: t.brief.genre, mots: t.brief.mots, palier: t.palier, verdict: verdict.succes ? 'succes' : 'echec', scoreCode: t.scoreCode } } as Strategie];
  });
}

export class BanqueStrategies implements ModuleMemoire {
  nom = 'reasoningbank';
  constructor(public items: Strategie[] = [], public o: { k?: number; plafond?: number } = {}) {}
  static lire(fichier: string): BanqueStrategies { return new BanqueStrategies(existsSync(fichier) ? (JSON.parse(readFileSync(fichier, 'utf8')) as Strategie[]) : []); }
  ecrire(fichier: string): void { writeFileSync(fichier, JSON.stringify(this.items, null, 1)); }
  /** Consolidation de ReasoningBank : simple ajout ; titre déjà présent pour la même étape = ignoré ; plafond (les plus anciens sortent). */
  ajouter(s: Strategie[]): number {
    let n = 0;
    for (const x of s) {
      if (this.items.some((y) => y.etape === x.etape && y.titre.toLowerCase() === x.titre.toLowerCase())) continue;
      this.items.push(x); n++;
    }
    const plafond = this.o.plafond ?? 200;
    if (this.items.length > plafond) this.items = this.items.slice(-plafond);
    return n;
  }
  /** Top-k (k = 1 par défaut, résultat de ReasoningBank comme d'AMD) : genre + recouvrement de mots avec l'énoncé. */
  recuperer(b: Pick<BriefFilm, 'genre' | 'enonce' | 'mots'>, etape: 'tournage' | 'montage', k = this.o.k ?? 1): Strategie[] {
    const mb = MOTS(`${b.enonce} ${b.mots.join(' ')}`);
    return this.items.filter((s) => s.etape === etape)
      .map((s) => [s, (s.source.genre === b.genre ? 2 : 0) + 0.5 * recouvrement(mb, MOTS(`${s.titre} ${s.description} ${s.contenu} ${s.source.mots.join(' ')}`)) + (s.source.verdict === 'echec' ? 0.25 : 0)] as const)
      .sort((x, y) => y[1] - x[1]).slice(0, k).map(([s]) => s);
  }
  systeme(etape: 'tournage' | 'montage', b: BriefFilm): string {
    const r = this.recuperer(b, etape);
    return r.length ? `Mémoire de tes expériences passées (applique-la si elle s'y prête) :\n${r.map((s) => `- ${s.titre} : ${s.description} ${s.contenu}`).join('\n')}` : '';
  }
}
