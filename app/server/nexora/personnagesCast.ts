/**
 * Colle entre les personnages @ (Cast) et les rendus H3 : repère les @mentions d'un texte, remplace chaque mention par
 * « Nom (apparence) » pour le réécrivain, et rend les références (corps entier, gros plan) à joindre au rendu Ref2VA.
 * Deux personnages au plus par plan (quatre images : le nœud H3 de référence n'en lit pas plus ici).
 */
import { liveRefs, mentioned, plainText } from '../cast.js';
import { cast as castDb } from '../jobs.js';
import type { SujetRef } from './personnages.js';

export const MAX_PERSONNAGES_PAR_PLAN = 2;
const IMAGES_PAR_PERSONNAGE = 2;

export interface PersonnagesResolus {
  /** Texte avec « Nom (apparence) » à la première mention, utilisé pour réécrire le prompt. */
  texteClair: string;
  sujets: SujetRef[];
  /** Jetons d'entrée du moteur, dans l'ordre des <Picture N>. */
  jetons: string[];
  /** Identifiants de fichiers durables, indépendants d'un jeton de téléversement renouvelé. */
  fichiers: string[];
  noms: string[];
}

export async function resoudrePersonnages(texte: string): Promise<PersonnagesResolus | null> {
  if (!texte.includes('@')) return null;
  const tous = castDb.list();
  const membres = mentioned(texte, tous).slice(0, MAX_PERSONNAGES_PAR_PLAN);
  if (!membres.length) return null;
  const sujets: SujetRef[] = [];
  const jetons: string[] = [];
  const fichiers: string[] = [];
  for (const m of membres) {
    const refs = (await liveRefs(m)).slice(0, IMAGES_PAR_PERSONNAGE);
    if (!refs.length) continue;
    sujets.push({ nom: m.name, apparence: m.notes.trim(), images: refs.length });
    jetons.push(...refs.map((r) => r.token));
    fichiers.push(...refs.map((r) => r.file));
  }
  if (!sujets.length) return { texteClair: plainText(texte, tous), sujets: [], jetons: [], fichiers: [], noms: [] };
  return { texteClair: plainText(texte, tous), sujets, jetons, fichiers, noms: sujets.map((s) => s.nom) };
}
