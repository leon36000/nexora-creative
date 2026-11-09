/** Types partagés du harnais de montage : brief, inventaire analysé, bandes de durée de plan par genre. */
import type { Format, Genre } from './editplan.js';

export interface ClipInfo {
  id: string;
  duree_s: number;
  /** Présence d’un flux audio mesurée dans la source vidéo; absent pour les briefs historiques/non mesurés. */
  a_audio?: boolean;
  description?: string;
  /** Coupes de plan internes à la source (s) : un plan monté ne les traverse pas. */
  coupes_s?: number[];
  /** Intervalles de parole (s) : aucune coupe dedans. */
  mots?: [number, number][];
}
export interface MusiqueInfo {
  id: string;
  duree_s: number;
  bpm: number;
  /** Temps forts (s). */
  battues_s: number[];
  /** Énergie par fenêtre de 0,5 s, 0 à 1. */
  energie: number[];
}
export interface VoixInfo { id: string; duree_s: number; mots?: [number, number][] }

export interface Brief {
  id: string;
  partition: 'apprentissage' | 'validation' | 'test';
  genre: Genre;
  format: Format;
  duree_cible_s: number;
  fps: 24 | 25 | 30;
  enonce: string;
  textes_imposes: string[];
  clips: ClipInfo[];
  musique?: MusiqueInfo;
  voix?: VoixInfo;
}

/** Bande de durée de plan (s) par genre : [mini, maxi] ; le rythme suit l'énergie à l'intérieur de la bande. */
export const BANDES: Record<Genre, [number, number]> = {
  pub: [1.2, 3.5],
  'bande-annonce': [0.6, 4.0],
  explicatif: [2.5, 7.0],
  social: [0.8, 2.5],
};
export const COUPE_MIN_S = 0.5;
export const FENETRE_ENERGIE_S = 0.5;

/** Énergie (0 à 1) à l'instant t, par interpolation de la courbe à pas de 0,5 s. */
export function energieA(energie: number[], t: number): number {
  if (!energie.length) return 0.5;
  const x = Math.max(0, t / FENETRE_ENERGIE_S);
  const i = Math.min(energie.length - 1, Math.floor(x));
  const j = Math.min(energie.length - 1, i + 1);
  return energie[i] + (energie[j] - energie[i]) * (x - Math.floor(x));
}
