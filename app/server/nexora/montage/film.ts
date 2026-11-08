/**
 * Agent monteur « trois paliers » : du brief au film. Deux appels courts, rien d'autre :
 *   1. tournage : liste de plans à tourner et prompts vidéo (rôle `tournage`), validée avec valeur attendue et réparation ;
 *   2. montage  : liste de montage compacte en secondes (rôle `montage`), compilée et validée par le code.
 * Un exemplaire (k = 1) et une recette par niveau (AMD), repli déterministe `montageAuto`, escalade vers le palier
 * suivant quand le validateur refuse ou que le score en code est bas, dans un plafond de dépense.
 */
import { readdirSync, readFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { avecCompetences } from '../competences.js';
import { type ClientLlm, lireJson } from '../llm.js';
import { type Palier, PALIERS } from '../niveaux.js';
import { ErreurPlafondLlm } from '../usage.js';
import { montageAuto } from './auto.js';
import { type EditPlan, type Violation, framesDe } from './editplan.js';
import { type ListeMontage, listeVersPlan, maxCaracteres, planVersListe, reparerListe, validerListe } from './liste.js';
import { type Recette, type Segment, chargerMemoire, noteSegment } from './memoire.js';
import { mesurer } from './metriques.js';
import { MemoireProfesseur, type ModuleMemoire } from './memoires.js';
import type { Brief } from './types.js';

export interface BriefFilm {
  id: string; titre: string; enonce: string; genre: Brief['genre']; format: Brief['format']; duree_cible_s: number; fps?: 24 | 25 | 30;
  bpm: number; /** Texte imposé du carton final : la marque (marque.json). */ marque: string; /** Mot-clés pour retrouver un exemplaire. */ mots: string[];
  /** Identifiant du film d'origine des graines à exclure (anti-fuite). */ film?: string;
}

export interface Tournage { titre: string; style: string; plans: { resume: string; prompt: string; camera?: string; duree: 5 | 10 }[]; musique?: string }

// ---------------------------------------------------------------------------------------------------------------------
// Mémoire : graines du professeur + apprentissage en cours de campagne

export interface ExemplaireTournage { id: string; version: number; genre: string[]; description: string; mots_cles: string[]; sortie: Tournage }

const MOTS = (t: string) => new Set(t.toLowerCase().normalize('NFD').replace(/[̀-ͯ]/g, '').split(/[^a-z0-9]+/).filter((w) => w.length > 3));

export class MemoireFilm {
  segments: Segment[];
  tournages: ExemplaireTournage[];
  recettes: Recette[];
  constructor(o: { segments?: Segment[]; tournages?: ExemplaireTournage[] } = {}) {
    const m = chargerMemoire();
    this.segments = [...(o.segments ?? m.segments)];
    this.recettes = m.recettes;
    this.tournages = [...(o.tournages ?? chargerTournages())];
  }
  /** Un exemplaire de montage (k = 1) et la recette du genre, hors exemplaires interdits. */
  montage(b: Pick<Brief, 'genre' | 'format' | 'duree_cible_s' | 'enonce'>, exclure: (id: string) => boolean = () => false) {
    const segment = this.segments.filter((s) => !exclure(s.id)).map((s) => [s, noteSegment(s, b)] as const).sort((x, y) => y[1] - x[1])[0]?.[0] ?? null;
    return { segment, recette: this.recettes.find((r) => r.genres.includes(b.genre)) ?? null };
  }
  tournage(b: BriefFilm, exclure: (id: string) => boolean = () => false): ExemplaireTournage | null {
    const mb = MOTS(`${b.enonce} ${b.mots.join(' ')}`);
    const note = (e: ExemplaireTournage) => (e.genre.includes(b.genre) ? 3 : 0) + Math.min(2, [...mb].filter((w) => e.mots_cles.some((k) => MOTS(k).has(w))).length * 0.7);
    return this.tournages.filter((e) => !exclure(e.id)).map((e) => [e, note(e)] as const).sort((x, y) => y[1] - x[1])[0]?.[0] ?? null;
  }
  /** Croissance : un plan réussi devient un exemplaire (remplace celui du même brief et palier s'il est meilleur). */
  apprendre(b: BriefFilm, palier: Palier, plan: EditPlan, tournage: Tournage | null, score: number, seuil = 0.85): boolean {
    if (score < seuil) return false;
    const id = `seg-appris-${b.id}-${palier}`;
    const ancien = this.segments.find((s) => s.id === id) as (Segment & { score?: number }) | undefined;
    if (ancien && (ancien.score ?? 0) >= score) return false;
    this.segments = this.segments.filter((s) => s.id !== id);
    this.segments.push({ id, version: 1, genre: [b.genre], format: [b.format], etiquette: `appris_${palier}`, origine: `campagne:${b.id}`, description: `${b.titre} (${b.duree_cible_s} s), plan appris au palier ${palier}, score ${score.toFixed(3)}.`, mots_cles: b.mots, extrait_edl: plan, score } as Segment);
    if (tournage) {
      const tid = `tournage-appris-${b.id}-${palier}`;
      this.tournages = this.tournages.filter((e) => e.id !== tid);
      this.tournages.push({ id: tid, version: 1, genre: [b.genre], description: b.titre, mots_cles: b.mots, sortie: tournage });
    }
    return true;
  }
  copie(): MemoireFilm { return new MemoireFilm({ segments: this.segments, tournages: this.tournages }); }
}

function chargerTournages(): ExemplaireTournage[] {
  const d = join(dirname(fileURLToPath(import.meta.url)), '../memoire/tournages');
  return readdirSync(d).filter((f) => f.endsWith('.json')).sort().map((f) => JSON.parse(readFileSync(join(d, f), 'utf8')) as ExemplaireTournage);
}

/** Exclusion anti-fuite : les graines du film dont le brief est tiré, et les exemplaires appris sur le même brief. */
export const exclusionPour = (b: BriefFilm) => (id: string) => (!!b.film && id.includes(`-${b.film}-`)) || id.includes(`-appris-${b.id}-`) || id.startsWith(`seg-appris-${b.id}-`) || id.startsWith(`tournage-appris-${b.id}-`);

// ---------------------------------------------------------------------------------------------------------------------
// Appel JSON avec validateur : au plus `reparations` réparations, violations avec valeur attendue et correction

export interface SortieJson<T> { valeur: T | null; premierCoup: boolean; appels: number; brutes: string[]; erreurs: Violation[]; notes: string[]; /** Refus successifs du validateur (règles), pour la mémoire. */ journal: string[] }

export async function appelerValide<T>(
  llm: ClientLlm, role: 'tournage' | 'montage', messages: { role: 'system' | 'user' | 'assistant'; content: string }[],
  valider: (brut: unknown) => { ok: true; valeur: T } | { ok: false; erreurs: Violation[] },
  o: { reparations: number; maxTokens: number; temperature?: number; /** Mémoire de fonction (réactive) : indices joints au refus. */ indices?: (v: Violation[]) => string[] },
): Promise<SortieJson<T>> {
  const sortie: SortieJson<T> = { valeur: null, premierCoup: false, appels: 0, brutes: [], erreurs: [], notes: [], journal: [] };
  for (let essai = 0; essai <= o.reparations; essai++) {
    let texte: string;
    try {
      sortie.appels++;
      texte = await llm.completer(role, messages, { json: true, temperature: o.temperature ?? 0.4, maxTokens: o.maxTokens });
    } catch (e) { if (e instanceof ErreurPlafondLlm) throw e; sortie.notes.push(`appel en échec : ${e instanceof Error ? e.message : String(e)}`); return sortie; }
    sortie.brutes.push(texte);
    messages.push({ role: 'assistant', content: texte });
    let r: ReturnType<typeof valider>;
    try { r = valider(lireJson<unknown>(texte)); } catch (e) { r = { ok: false, erreurs: [{ regle: 'schema', chemin: '(racine)', message: `JSON illisible : ${e instanceof Error ? e.message : String(e)}`, indice: 'Réponds par un seul objet JSON.' }] }; }
    if (r.ok) { sortie.valeur = r.valeur; sortie.premierCoup = essai === 0; sortie.erreurs = []; return sortie; }
    sortie.erreurs = r.erreurs;
    sortie.journal.push(r.erreurs.slice(0, 8).map((e) => `${e.regle} (${e.message})`).join(' ; '));
    const ind = o.indices?.(r.erreurs) ?? [];
    messages.push({ role: 'user', content: `Le validateur refuse :\n${r.erreurs.slice(0, 8).map((e) => `- [${e.regle}] ${e.chemin} : ${e.message}${e.indice ? ` → ${e.indice}` : ''}`).join('\n')}${ind.length ? `\nRappels du professeur :\n${ind.map((x) => `- ${x}`).join('\n')}` : ''}\nRenvoie le JSON COMPLET corrigé.` });
  }
  return sortie;
}

// ---------------------------------------------------------------------------------------------------------------------
// Tournage

const INTERDITS = /\b(logo|logos|caption|captions|subtitle|subtitles|watermark|nvidia|geforce|netflix|marvel|disney|pixar|star wars|apple|google|openai|chatgpt|amazon|tesla|coca[- ]cola)\b|(?<!no |without )\b(text|texts|typography|lettering|slogan)\b/i;
const FRANCAIS = /\b(le|la|les|une|des|avec|dans|sur|pour|qui|est|très|aux|du)\b/gi;

export function validerTournage(brut: unknown, b: BriefFilm): { ok: true; valeur: Tournage } | { ok: false; erreurs: Violation[] } {
  const o = (brut ?? {}) as any;
  const e: Violation[] = [];
  const plans = Array.isArray(o.plans) ? o.plans : [];
  if (!plans.length) return { ok: false, erreurs: [{ regle: 'schema', chemin: 'plans', message: 'liste de plans absente', indice: 'Fournis "plans": [{resume, prompt, camera, duree}].' }] };
  const t: Tournage = {
    titre: String(o.titre ?? '').slice(0, 100) || b.titre, style: String(o.style ?? '').slice(0, 300),
    plans: plans.map((p: any) => ({ resume: String(p?.resume ?? '').slice(0, 160), prompt: String(p?.prompt ?? '').trim(), camera: String(p?.camera ?? '').slice(0, 200), duree: (Number(p?.duree) >= 8 ? 10 : 5) as 5 | 10 })).slice(0, 16),
    musique: typeof o.musique === 'string' ? o.musique.slice(0, 300) : undefined,
  };
  const besoin = Math.ceil((b.duree_cible_s - 4.5) / 4);
  const utile = t.plans.reduce((s, p) => s + Math.min(p.duree, 4), 0);
  if (t.plans.length < besoin) e.push({ regle: 'nombre_de_plans', chemin: 'plans', message: `${t.plans.length} plans de matière : le film de ${b.duree_cible_s} s en exige au moins ${besoin}`, indice: `Écris au moins ${besoin} plans (2 à 4 s de chacun sont montés).` });
  if (t.plans.length > 14) e.push({ regle: 'nombre_de_plans', chemin: 'plans', message: `${plans.length} plans : 14 au plus`, indice: 'Garde les 14 plus forts.' });
  void utile;
  const vus = new Set<string>();
  t.plans.forEach((p, i) => {
    const ch = `plans.${i}`;
    const mots = p.prompt.split(/\s+/).filter(Boolean);
    if (mots.length < 15 || mots.length > 70) e.push({ regle: 'longueur_prompt', chemin: `${ch}.prompt`, message: `${mots.length} mots`, indice: 'Entre 20 et 55 mots : sujet, lieu, lumière, mouvement.' });
    const m = p.prompt.match(INTERDITS);
    if (m) e.push({ regle: 'interdit_dans_le_prompt', chemin: `${ch}.prompt`, message: `« ${m[0]} » : texte, logo, marque ou franchise dans le prompt`, indice: 'Retire-le : les textes se posent en code, aucune marque ni franchise ne se génère.' });
    if ((p.prompt.match(FRANCAIS) ?? []).length >= 3) e.push({ regle: 'prompt_en_anglais', chemin: `${ch}.prompt`, message: 'le prompt semble écrit en français', indice: 'Réécris le prompt en anglais (le résumé reste en français).' });
    const cle = mots.slice(0, 6).join(' ').toLowerCase();
    if (vus.has(cle)) e.push({ regle: 'plans_distincts', chemin: `${ch}.prompt`, message: 'début identique à un autre plan', indice: 'Change le sujet ou l\'échelle du plan.' });
    vus.add(cle);
    if (!p.resume) e.push({ regle: 'schema', chemin: `${ch}.resume`, message: 'résumé absent', indice: 'Une phrase courte en français.' });
  });
  return e.length ? { ok: false, erreurs: e } : { ok: true, valeur: t };
}

function blocTournage(ex: ExemplaireTournage | null): string {
  if (!ex) return '';
  return `[exemplaire d'un autre film : imite la STRUCTURE (progression, échelles, concision), jamais le sujet]\n${JSON.stringify(ex.sortie)}\n\n`;
}

export async function tournerPlans(llm: ClientLlm, b: BriefFilm, o: { memoire?: MemoireFilm; module?: ModuleMemoire; reparations?: number } = {}): Promise<SortieJson<Tournage>> {
  const ex = o.module?.tournage?.(b) ?? (o.memoire ? o.memoire.tournage(b, exclusionPour(b)) : null);
  const sys = o.module?.systeme?.('tournage', b);
  const messages = [
    { role: 'system' as const, content: avecCompetences('tournage', 'Tu es le chef de plateau de Nexora Creative. Tu réponds uniquement par du JSON.') + (sys ? `\n\n${sys}` : '') },
    { role: 'user' as const, content: `${blocTournage(ex)}${o.module?.avant?.('tournage', b) ?? ''}BRIEF : ${b.enonce}\nGenre ${b.genre}, format ${b.format}, durée du film ${b.duree_cible_s} s (carton final de la marque en plus de la matière, posé en code).\nÉcris la liste des plans.` },
  ];
  return appelerValide(llm, 'tournage', messages, (x) => validerTournage(x, b), { reparations: o.reparations ?? 2, maxTokens: 5000, temperature: 0.7, indices: o.module?.surErreur ? (v) => o.module!.surErreur!('tournage', v) : undefined });
}

// ---------------------------------------------------------------------------------------------------------------------
// Montage

/** Courbe d'énergie synthétique d'une bande-annonce ou d'une pub (montée, apogée aux 2/3, retombée). */
export function energieSynthetique(genre: Brief['genre'], dureeS: number): number[] {
  const n = Math.ceil(dureeS * 2);
  return Array.from({ length: n }, (_, i) => {
    const x = i / Math.max(1, n - 1);
    const base = genre === 'bande-annonce' ? (x < 0.15 ? 0.2 + x : x < 0.65 ? 0.35 + (x - 0.15) * 1.2 : x < 0.8 ? 1 : 0.35) : x < 0.1 ? 0.5 : x < 0.7 ? 0.5 + (x - 0.1) * 0.7 : x < 0.85 ? 0.95 : 0.3;
    return Math.round(Math.max(0, Math.min(1, base + (i % 4 === 0 ? 0.06 : 0))) * 1000) / 1000;
  });
}

export function briefDeMontage(b: BriefFilm, clips: Brief['clips'], musique?: Brief['musique']): Brief {
  const dureeMus = b.duree_cible_s + 6;
  const per = 60 / b.bpm;
  return {
    id: b.id, partition: 'test', genre: b.genre, format: b.format, duree_cible_s: b.duree_cible_s, fps: b.fps ?? 24, enonce: b.enonce, textes_imposes: [b.marque],
    clips: [...clips, { id: 'carton', duree_s: 8, description: 'carton neutre sombre, sans image : porte le texte final de la marque' }],
    musique: musique ?? { id: 'musique', duree_s: dureeMus, bpm: b.bpm, battues_s: Array.from({ length: Math.ceil(dureeMus / per) }, (_, k) => Math.round((0.1 + k * per) * 1000) / 1000), energie: energieSynthetique(b.genre, dureeMus) },
  };
}

/** Clips d'un tournage (stade A, sans GPU) : une prise = une source de 5,1 s ou 10,2 s. */
export const clipsDuTournage = (t: Tournage): Brief['clips'] => t.plans.map((p, i) => ({ id: `s${i + 1}`, duree_s: p.duree === 10 ? 10.2 : 5.1, description: p.resume }));

function vueMontage(b: Brief): string {
  const m = b.musique!;
  const gr = m.energie.slice(0, Math.ceil(b.duree_cible_s * 2)).map((v) => Math.round(v * 9)).join('');
  return [
    `BRIEF : ${b.enonce}`,
    `Genre ${b.genre}, format ${b.format}, durée cible EXACTE ${b.duree_cible_s} s. Texte imposé du dernier plan (carton), mot pour mot : ${JSON.stringify(b.textes_imposes[0])}`,
    'SOURCES (id : durée en s — contenu) :', ...b.clips.map((c) => `- ${c.id} : ${c.duree_s} s — ${c.description ?? ''}`),
    `MUSIQUE ${m.bpm} BPM, un temps fort toutes les ${(60 / m.bpm).toFixed(2)} s (le code aimante tes coupes). Énergie 0-9 par demi-seconde : ${gr}`,
  ].join('\n');
}

function blocMontage(s: { segment: Segment | null; recette: Recette | null }): string {
  const p: string[] = [];
  if (s.recette) p.push(`[recette ${s.recette.nom}]\n${s.recette.texte}`);
  if (s.segment) p.push(`[exemplaire d'un autre film : imite la STRUCTURE et le rythme, pas les sources ni les mots]\n${JSON.stringify(planVersListe(s.segment.extrait_edl))}`);
  return p.length ? `${p.join('\n\n')}\n\n` : '';
}

export interface ResultatMontage { plan: EditPlan; liste: ListeMontage | null; source: 'llm' | 'repli'; premierCoup: boolean; appels: number; brutes: string[]; notes: string[]; erreurs: Violation[]; journal?: string[]; reparePar?: 'code' }

export interface OptionsMontage {
  savoir?: { segment: Segment | null; recette: Recette | null }; reparations?: number;
  /** Module de mémoire (AMD professeur, ReasoningBank…) et le brief de film pour le récupérer. */
  module?: ModuleMemoire; brief?: BriefFilm;
  /** Meilleur-de-n : n chaînes indépendantes, la meilleure note en code l'emporte (juge gratuit). */
  candidats?: number;
  /** Harnais décomposé : structure (sources, durées, phases) puis textes à budget de caractères calculé par le code. */
  decompose?: boolean; temperature?: number;
}

/** Réparations mécaniques du code sur la dernière réponse, puis repli `montageAuto`. */
function finir(bm: Brief, s: SortieJson<unknown>, dernier: unknown, repli: (n: string[], s?: Partial<SortieJson<unknown>>) => ResultatMontage): ResultatMontage {
  try {
    const rep = dernier ? reparerListe(dernier, bm) : null;
    const r = rep ? listeVersPlan(rep.liste, bm) : null;
    if (rep && r?.ok) {
      r.plan.metadonnees = { modele: 'liste', savoir: [] };
      return { plan: r.plan, liste: r.liste, source: 'llm', premierCoup: false, appels: s.appels, brutes: s.brutes, notes: [...s.notes, `réparé par le code : ${rep.faits.join(' ; ')}`], erreurs: [], journal: s.journal, reparePar: 'code' };
    }
  } catch { /* repli ci-dessous */ }
  return repli([...s.notes, `liste invalide après ${s.appels} appel(s) : ${s.erreurs.slice(0, 3).map((e) => e.regle).join(', ')}`], s);
}

export async function monterListe(llm: ClientLlm | null, bm: Brief, o: OptionsMontage = {}): Promise<ResultatMontage> {
  const repli = (notes: string[], s?: Partial<SortieJson<unknown>>): ResultatMontage => ({ plan: montageAuto(bm), liste: null, source: 'repli', premierCoup: false, appels: s?.appels ?? 0, brutes: s?.brutes ?? [], notes, erreurs: s?.erreurs ?? [], journal: s?.journal ?? [] });
  if (!llm) return repli(['aucun LLM']);
  if ((o.candidats ?? 1) > 1) {
    const n = o.candidats!;
    const rs = await Promise.all(Array.from({ length: n }, () => monterListe(llm, bm, { ...o, candidats: 1, temperature: o.temperature ?? 0.8 })));
    const note = (r: ResultatMontage) => (r.source === 'llm' ? 1 + mesurer(r.plan, bm).composite - (r.reparePar ? 0.5 : 0) : 0);
    const best = rs.reduce((a, r) => (note(r) > note(a) ? r : a), rs[0]);
    return { ...best, appels: rs.reduce((s, r) => s + r.appels, 0), premierCoup: rs.some((r) => r.premierCoup), notes: [...best.notes, `meilleur de ${n} (${rs.filter((r) => r.source === 'llm').length} valides)`] };
  }
  const sys = o.brief ? o.module?.systeme?.('montage', o.brief) : '';
  const prefixe = `${blocMontage(o.savoir ?? { segment: null, recette: null })}${o.brief ? (o.module?.avant?.('montage', o.brief, bm) ?? '') : ''}`;
  const indices = o.module?.surErreur ? (v: Violation[]) => o.module!.surErreur!('montage', v) : undefined;
  const systeme = avecCompetences('montage', 'Tu es le monteur de Nexora Creative. Tu réponds uniquement par du JSON.') + (sys ? `\n\n${sys}` : '');
  if (o.decompose) return monterDecompose(llm, bm, systeme, prefixe, indices, o, repli);
  const messages = [
    { role: 'system' as const, content: systeme },
    { role: 'user' as const, content: `${prefixe}${vueMontage(bm)}\nRéponds par la liste de montage JSON.` },
  ];
  let obtenu: { plan: EditPlan; liste: ListeMontage } | null = null;
  const s = await appelerValide(llm, 'montage', messages, (x) => { const r = listeVersPlan(x, bm); if (r.ok) { obtenu = { plan: r.plan, liste: r.liste }; return { ok: true as const, valeur: r.plan }; } return r; }, { reparations: o.reparations ?? 2, maxTokens: 4500, temperature: o.temperature ?? 0.4, indices });
  if (!s.valeur || !obtenu) {
    let dernier: unknown = null;
    try { dernier = s.brutes.length ? lireJson<unknown>(s.brutes[s.brutes.length - 1]) : null; } catch { /* illisible */ }
    return finir(bm, s, dernier, repli);
  }
  const o2 = obtenu as { plan: EditPlan; liste: ListeMontage };
  o2.plan.metadonnees = { modele: 'liste', savoir: [] };
  return { plan: o2.plan, liste: o2.liste, source: 'llm', premierCoup: s.premierCoup, appels: s.appels, brutes: s.brutes, notes: s.notes, erreurs: [], journal: s.journal };
}

// ---------------------------------------------------------------------------------------------------------------------
// Harnais décomposé (plan puis remplissage) : le modèle ne fait jamais l'arithmétique des passages ni des caractères

type Structure = { plans: { src: string; dur: number; phase?: string }[]; gain_db?: number };

/** Le code choisit les passages (in) : chaque réemploi d'une source reprend après le passage précédent, sinon au début. */
export function structureVersListe(st: Structure, bm: Brief): ListeMontage {
  const duree = new Map(bm.clips.map((c) => [c.id, c.duree_s] as const));
  const fin = new Map<string, number>();
  const plans = (Array.isArray(st?.plans) ? st.plans : []).map((p) => {
    const src = String(p?.src ?? ''), d = duree.get(src) ?? 0;
    let dur = Math.max(0.3, Number(p?.dur) || 2);
    if (src === 'carton') return { src, in: 0, dur, tr: 'fondu' as const, texte: bm.textes_imposes[0] };
    if (d) dur = Math.min(dur, Math.floor(d * 10) / 10);
    const f = fin.get(src) ?? 0;
    const entree = f + dur <= d ? f : Math.max(0, Math.floor((d - dur) * 100) / 100);
    fin.set(src, entree + dur);
    return { src, in: Math.round(entree * 100) / 100, dur, tr: 'cut' as const };
  });
  if (plans.length && plans[plans.length - 1].src !== 'carton' && duree.has('carton')) {
    const reste = Math.max(3, bm.duree_cible_s - plans.reduce((s, p) => s + p.dur, 0));
    plans.push({ src: 'carton', in: 0, dur: Math.round(Math.min(5, reste) * 100) / 100, tr: 'fondu', texte: bm.textes_imposes[0] });
  }
  return { plans, gain_db: typeof st?.gain_db === 'number' ? st.gain_db : -8 } as ListeMontage;
}

async function monterDecompose(
  llm: ClientLlm, bm: Brief, systeme: string, prefixe: string, indices: ((v: Violation[]) => string[]) | undefined, o: OptionsMontage,
  repli: (n: string[], s?: Partial<SortieJson<unknown>>) => ResultatMontage,
): Promise<ResultatMontage> {
  // Étape 1 : structure. Seules les règles de structure sont contrôlées (pas de texte encore).
  const STRUCT = new Set(['schema', 'source_connue', 'meme_source', 'bande_de_duree', 'duree_cible', 'accroche', 'dans_la_source']);
  let liste: ListeMontage | null = null;
  const m1 = [
    { role: 'system' as const, content: systeme },
    { role: 'user' as const, content: `${prefixe}${vueMontage(bm)}\nÉTAPE 1 sur 2 — la STRUCTURE seulement, sans aucun texte ni point d'entrée (le code choisit les passages et pose le carton) :\n{"plans":[{"src":"s1","dur":1.8,"phase":"accroche"}],"gain_db":-8}\nphase = accroche | montee | respiration | apogee | resolution | carton ; termine par {"src":"carton","dur":3.8,"phase":"carton"}.` },
  ];
  const s1 = await appelerValide(llm, 'montage', m1, (x) => {
    const l = structureVersListe(x as Structure, bm);
    const v = validerListe(l, bm);
    const e = v.erreurs.filter((z) => STRUCT.has(z.regle));
    if (e.length) return { ok: false as const, erreurs: e };
    liste = l; return { ok: true as const, valeur: l };
  }, { reparations: o.reparations ?? 2, maxTokens: 2500, temperature: o.temperature ?? 0.4, indices });
  if (!liste) {
    let dernier: unknown = null;
    try { dernier = s1.brutes.length ? structureVersListe(lireJson<Structure>(s1.brutes[s1.brutes.length - 1]), bm) : null; } catch { /* illisible */ }
    return finir(bm, s1, dernier, repli);
  }
  const base = liste as ListeMontage;
  // Étape 2 : textes, avec le budget de caractères de chaque plan calculé par le code.
  const desc = new Map(bm.clips.map((c) => [c.id, c.description ?? ''] as const));
  let t = 0;
  const lignes = base.plans.map((p, i) => { const l = `${i}. ${f2(t)}-${f2(t + p.dur)} s, ${p.src} (${desc.get(p.src)?.slice(0, 60)}) : ${p.src === 'carton' ? `CARTON (texte imposé déjà posé)` : `${maxCaracteres(p.dur)} caractères au plus s'il est seul ; plus si les plans suivants n'ont pas de texte`}`; t += p.dur; return l; });
  const m2 = [
    { role: 'system' as const, content: systeme },
    { role: 'user' as const, content: `${prefixe}BRIEF : ${bm.enonce}\nÉTAPE 2 sur 2 — les TEXTES posés sur ce montage (déjà validé) :\n${lignes.join('\n')}\nÉcris 4 à 7 textes de 2 à 5 mots, français du Québec, un par idée, le premier sur le plan 0, aucun pendant l'apogée ni sur le carton. Compte les caractères.\n{"textes":[{"i":0,"texte":"…"}]}` },
  ];
  let finale: { plan: EditPlan; liste: ListeMontage } | null = null;
  const fusion = (x: any): ListeMontage => {
    const l = { ...base, plans: base.plans.map((p) => ({ ...p })) } as ListeMontage;
    for (const e of Array.isArray(x?.textes) ? x.textes : []) { const i = Number(e?.i); if (Number.isInteger(i) && l.plans[i] && l.plans[i].src !== 'carton' && typeof e?.texte === 'string' && e.texte.trim()) l.plans[i].texte = e.texte.trim().slice(0, 120); }
    return l;
  };
  const s2 = await appelerValide(llm, 'montage', m2, (x) => {
    const r = listeVersPlan(fusion(x), bm);
    if (r.ok) { finale = { plan: r.plan, liste: r.liste }; return { ok: true as const, valeur: r.plan }; }
    return { ok: false as const, erreurs: r.erreurs.map((e) => ({ ...e, indice: e.chemin.startsWith('plans.') ? `${e.indice ?? ''} (textes : {"i":${e.chemin.split('.')[1]},"texte":"…"})` : e.indice })) };
  }, { reparations: o.reparations ?? 2, maxTokens: 1500, temperature: o.temperature ?? 0.4, indices });
  const s: SortieJson<unknown> = { ...s2, appels: s1.appels + s2.appels, brutes: [...s1.brutes, ...s2.brutes], notes: [...s1.notes, ...s2.notes], journal: [...s1.journal, ...s2.journal], premierCoup: s1.premierCoup && s2.premierCoup };
  if (!finale) {
    let dernier: unknown = base;
    try { if (s2.brutes.length) dernier = fusion(lireJson<unknown>(s2.brutes[s2.brutes.length - 1])); } catch { /* garde la structure */ }
    return finir(bm, s, dernier, repli);
  }
  const fz = finale as { plan: EditPlan; liste: ListeMontage };
  fz.plan.metadonnees = { modele: 'liste', savoir: [] };
  return { plan: fz.plan, liste: fz.liste, source: 'llm', premierCoup: s.premierCoup, appels: s.appels, brutes: s.brutes, notes: s.notes, erreurs: [], journal: s.journal };
}
const f2 = (x: number) => (Math.round(x * 10) / 10).toString();

// ---------------------------------------------------------------------------------------------------------------------
// Run complet et escalade

export interface RunFilm {
  palier: Palier; tournage: Tournage | null; tournageValide: boolean; tournagePremierCoup: boolean; montage: ResultatMontage;
  score: number; porte: boolean; ecarts: number; appels: number; metriques: Record<string, number>; plan: EditPlan;
}

export interface OptionsRun { memoire?: MemoireFilm; reparations?: number; sansTournage?: Brief; module?: ModuleMemoire; candidats?: number; decompose?: boolean }

/** Un run à UN palier : tournage (sauf bibliothèque de plans fournie) puis montage, score en code. */
export async function runFilm(llm: ClientLlm, palier: Palier, b: BriefFilm, o: OptionsRun = {}): Promise<RunFilm> {
  let tournage: Tournage | null = null, tValide = true, tPremier = true, appels = 0;
  let bm: Brief;
  if (o.sansTournage) bm = o.sansTournage;
  else {
    const t = await tournerPlans(llm, b, { memoire: o.memoire, module: o.module, reparations: o.reparations });
    appels += t.appels;
    tournage = t.valeur; tValide = !!t.valeur; tPremier = t.premierCoup;
    // Tournage invalide après réparations : le monteur travaille sur la matière que le modèle a produite, ou s'arrête.
    if (!t.valeur) {
      const repli = montageAuto(briefDeMontage(b, [{ id: 's1', duree_s: 10, description: 'plan' }, { id: 's2', duree_s: 10, description: 'plan' }, { id: 's3', duree_s: 10, description: 'plan' }]));
      const bm0 = briefDeMontage(b, [{ id: 's1', duree_s: 10, description: 'plan' }, { id: 's2', duree_s: 10, description: 'plan' }, { id: 's3', duree_s: 10, description: 'plan' }]);
      const m = mesurer(repli, bm0);
      return { palier, tournage: null, tournageValide: false, tournagePremierCoup: false, montage: { plan: repli, liste: null, source: 'repli', premierCoup: false, appels: 0, brutes: [], notes: ['tournage invalide'], erreurs: t.erreurs }, score: 0, porte: false, ecarts: m.ecarts.length, appels, metriques: {}, plan: repli };
    }
    bm = briefDeMontage(b, clipsDuTournage(t.valeur));
  }
  const savoir = o.memoire ? o.memoire.montage(bm, exclusionPour(b)) : undefined;
  const m = await monterListe(llm, bm, { savoir, reparations: o.reparations, module: o.module, brief: b, candidats: o.candidats, decompose: o.decompose });
  appels += m.appels;
  const r = mesurer(m.plan, bm);
  return {
    palier, tournage, tournageValide: tValide, tournagePremierCoup: tPremier, montage: m, appels,
    // Score « brut » : un repli ne compte pas comme un succès du modèle.
    score: m.source === 'llm' ? r.composite : 0, porte: r.porte, ecarts: r.ecarts.length,
    metriques: Object.fromEntries(Object.entries(r.metriques).map(([k, v]) => [k, v.score])), plan: m.plan,
  };
}

/**
 * Politique par palier, mesurée le 03/11/2026 (recherche/20, banc scellé de 8 briefs × 3) : Éco et Équilibré montent avec la
 * mémoire du PROFESSEUR (AMD : workflow + sous-tâches + indices de fonction) et le harnais DÉCOMPOSÉ (structure puis textes) :
 * Éco 0,914 au lieu de 0,832, 0 % de repli, 96 % de listes valides du premier coup, −34 % de coût ; Équilibré à égalité de note,
 * 100 % du premier coup. Expert garde la mémoire existante (la mémoire du professeur y baisse la note en code de 0,025).
 * `NEXORA_HARNAIS_FILM=v3` rend l'ancien comportement (mémoire existante partout).
 */
export function optionsPalier(p: Palier, env: NodeJS.ProcessEnv = process.env): OptionsRun {
  if (env.NEXORA_HARNAIS_FILM === 'v3' || p === 'expert') return { memoire: new MemoireFilm() };
  return { module: professeur(), decompose: true };
}
let profCache: MemoireProfesseur | null = null;
const professeur = () => (profCache ??= new MemoireProfesseur());

export interface ResultatEscalade { runs: RunFilm[]; final: RunFilm; palierFinal: Palier; escalades: number }

/**
 * Escalade : on essaie le palier le moins cher ; si le plan n'est pas du modèle, si le tournage est invalide ou si le score
 * est sous le seuil, on passe au suivant. S'arrête au plafond de dépense (`ErreurPlafondLlm` levée par le relevé).
 */
export async function escalader(
  clients: Record<Palier, ClientLlm>, depart: Palier, b: BriefFilm, o: OptionsRun & { seuil?: number; ordre?: readonly Palier[]; /** Options propres à chaque palier (mémoire, harnais), appliquées par-dessus `o`. */ politique?: (p: Palier) => OptionsRun } = {},
): Promise<ResultatEscalade> {
  const paliers = o.ordre ?? PALIERS;
  const debut = paliers.indexOf(depart);
  if (debut < 0) throw new RangeError('Le palier de départ est absent de l’ordre d’escalade.');
  const ordre = paliers.slice(debut);
  const runs: RunFilm[] = [];
  for (const p of ordre) {
    let r: RunFilm;
    try { r = await runFilm(clients[p], p, b, { ...o, ...(o.politique?.(p) ?? {}) }); } catch (e) {
      if (e instanceof ErreurPlafondLlm && runs.length > 0) break;
      throw e;
    }
    runs.push(r);
    if (r.montage.source === 'llm' && r.tournageValide && r.score >= (o.seuil ?? 0.85)) break;
  }
  const final = runs.reduce((best, r) => (r.score > best.score ? r : best), runs[0]);
  return { runs, final, palierFinal: final.palier, escalades: runs.length - 1 };
}

export const imagesDe = framesDe;
