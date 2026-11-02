/**
 * Mémoire de montage « à la AMD » (recherche/14 §4), tranche 1 : fichiers versionnés sous server/nexora/memoire/ ;
 *  - recettes/<genre>.md   : niveau workflow, prose courte (récupérée par genre) ;
 *  - segments/<id>.json    : niveau sous-tâche, exemplaire EditPlan réel (récupéré par brief) ;
 *  - fonctions/<outil>.json: niveau fonction, appel valide + pièges, injecté SEULEMENT sur erreur de validation.
 * Récupération : UN seul exemplaire (k = 1, résultat AMD), par filtre structuré + recouvrement de mots-clés ; aucun
 * vecteur en tranche 1. Le savoir est du texte et du JSON : le serveur n'exécute jamais rien de ce qu'il contient.
 */
import { readFileSync, readdirSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { type EditPlan, type Violation, dureeTotaleS, validerEditPlan } from './editplan.js';
import { lireCompetence } from '../competences.js';
import type { Brief } from './types.js';

const DOSSIER = join(dirname(fileURLToPath(import.meta.url)), '../memoire');

export interface Segment { id: string; version: number; genre: string[]; format: string[]; etiquette: string; origine: string; description: string; mots_cles: string[]; extrait_edl: EditPlan; statut?: 'actif' | 'desactive' }
export interface Recette { nom: string; version: number; genres: string[]; texte: string }
export interface Fonction { outil: string; version: number; exemple: unknown; pieges: { regle: string; indice: string }[] }

let cache: { segments: Segment[]; recettes: Recette[]; fonctions: Fonction[] } | null = null;
export function chargerMemoire(dossier = DOSSIER): { segments: Segment[]; recettes: Recette[]; fonctions: Fonction[] } {
  if (dossier === DOSSIER && cache) return cache;
  const lire = (sous: string, ext: string) => readdirSync(join(dossier, sous)).filter((f) => f.endsWith(ext)).sort();
  const segments = lire('segments', '.json').map((f) => JSON.parse(readFileSync(join(dossier, 'segments', f), 'utf8')) as Segment).filter((s) => s.statut !== 'desactive');
  const recettes = lire('recettes', '.md').map((f) => {
    const c = lireCompetence(readFileSync(join(dossier, 'recettes', f), 'utf8').replace(/^genres:/m, 'roles:'), f);
    return { nom: c.nom, version: c.version, genres: c.roles, texte: c.texte };
  });
  const fonctions = lire('fonctions', '.json').map((f) => JSON.parse(readFileSync(join(dossier, 'fonctions', f), 'utf8')) as Fonction);
  const m = { segments, recettes, fonctions };
  if (dossier === DOSSIER) cache = m;
  return m;
}

const mots = (t: string) => new Set(t.toLowerCase().normalize('NFD').replace(/[̀-ͯ]/g, '').split(/[^a-z0-9]+/).filter((w) => w.length > 3));

/** Note d'un exemplaire pour un brief : genre (4) + format (1,5) + durée proche (≤ 1,5) + mots-clés (≤ 2). */
export function noteSegment(s: Segment, b: Pick<Brief, 'genre' | 'format' | 'duree_cible_s' | 'enonce'>): number {
  const dur = dureeTotaleS(s.extrait_edl);
  const proche = 1.5 * Math.max(0, 1 - Math.abs(Math.log(dur / b.duree_cible_s)) / Math.log(3));
  const brief = mots(b.enonce);
  const cles = new Set(s.mots_cles.flatMap((k) => [...mots(k)]));
  const commun = [...brief].filter((w) => cles.has(w)).length;
  return (s.genre.includes(b.genre) ? 4 : 0) + (s.format.includes(b.format) ? 1.5 : 0) + proche + Math.min(2, commun * 0.7);
}

export interface Savoir { recette: Recette | null; segment: Segment | null; versions: string[] }

/** UN exemplaire et UNE recette pour le brief ; `exclure` retire les exemplaires interdits (anti-fuite du banc). */
export function recupererSavoir(b: Pick<Brief, 'genre' | 'format' | 'duree_cible_s' | 'enonce'>, o: { exclure?: string[]; dossier?: string } = {}): Savoir {
  const m = chargerMemoire(o.dossier);
  const segment = m.segments.filter((s) => !o.exclure?.includes(s.id)).map((s) => [s, noteSegment(s, b)] as const).sort((x, y) => y[1] - x[1])[0]?.[0] ?? null;
  const recette = m.recettes.find((r) => r.genres.includes(b.genre)) ?? null;
  return { recette, segment, versions: [...(recette ? [`${recette.nom}@${recette.version}`] : []), ...(segment ? [`${segment.id}@${segment.version}`] : [])] };
}

/** Bloc de contexte injecté au début du message (cachable : stable pour un même genre et un même exemplaire). */
export function blocSavoir(s: Savoir): string {
  const parts: string[] = [];
  if (s.recette) parts.push(`[recette ${s.recette.nom} v${s.recette.version}]\n${s.recette.texte}`);
  if (s.segment) parts.push(`[exemplaire ${s.segment.id} v${s.segment.version} : ${s.segment.description}]\nIdentifiants de sources et textes d'un autre projet : imite la STRUCTURE et le rythme, pas les valeurs.\n${JSON.stringify(s.segment.extrait_edl)}`);
  return parts.join('\n\n');
}

/** Mémoire de fonction : indices des règles violées, joints au message d'erreur (réactif, jamais en amont). */
export function indicesFonction(outil: string, violations: Violation[], dossier?: string): string[] {
  const f = chargerMemoire(dossier).fonctions.find((x) => x.outil === outil);
  if (!f) return [];
  const regles = new Set(violations.map((v) => v.regle));
  const pieges = f.pieges.filter((p) => regles.has(p.regle)).map((p) => p.indice);
  return regles.size && pieges.length ? [...pieges, `Exemple valide : ${JSON.stringify(f.exemple).slice(0, 1200)}`] : pieges;
}

/** Contrôle de santé du savoir : chaque exemplaire doit être un EditPlan valide. */
export const exemplairesInvalides = (): string[] => chargerMemoire().segments.filter((s) => !validerEditPlan(s.extrait_edl).ok).map((s) => s.id);
