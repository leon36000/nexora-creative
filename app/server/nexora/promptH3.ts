/**
 * Prompts MiniMax H3 : ligne d'instruction et validateur déterministe, d'après le guide officiel
 * « Video Prompt Writing Guide (T2VA / I2VA / FL2VA / L2VA) » (vendor/minimax-h3-guides/). Un prompt refusé ici est
 * réparé avant tout appel GPU : une erreur de forme ne coûte jamais un rendu.
 */

import { type SujetRef, validerPromptRef } from './personnages.js';

export type ModeH3 = 't2va' | 'i2va' | 'fl2va' | 'l2va' | 'ref2va';

export interface ContexteH3 {
  mode: ModeH3;
  /** Durée effective de la vidéo, en secondes. */
  dureeS: number;
  /** Répliques fournies par l'utilisateur, à recopier mot pour mot dans <d>…</d>. */
  dialogues?: string[];
  /** Langue explicitement demandée pour chaque réplique ; distincte de la langue UI. */
  dialoguesAvecLangue?: { texte: string; langue: string }[];
  references?: { sujets: SujetRef[]; composition?: number };
}

const CHAMPS = ['integrated_multimodal_description:', 'overall_soundscape:', 'non_diegetic_music:'] as const;

/** Ligne d'instruction exacte que le guide impose en tête du prompt (chaîne vide en T2VA). */
export function instructionH3(o: { mode: ModeH3; dureeS: number; dernierPlan: number }): string {
  const s = o.dureeS.toFixed(2);
  switch (o.mode) {
    case 'ref2va':
    case 't2va':
      return '';
    case 'i2va':
      return 'For the target video, at 0.00 seconds into the target video, <Picture 1> (from [Shot 1]) is fully referenced.';
    case 'fl2va':
      return `How the reference pictures align with the target video — Picture 1 (from Shot 1) aligns with the 0.00-second mark of the target video; Picture 2 (from Shot ${o.dernierPlan}) aligns with the ${s}-second mark of the target video.`;
    case 'l2va':
      return `How the reference pictures align with the target video — <Picture 1> (from [Shot ${o.dernierPlan}]) aligns with the ${s}-second mark of the target video.`;
  }
}

/** Liste des écarts au guide, en français ; vide si le prompt est conforme. */
export function validerPromptH3(prompt: string, ctx: ContexteH3): string[] {
  const erreurs: string[] = [];
  const texte = prompt.replace(/\r\n/g, '\n').trim();

  const ref = ctx.mode === 'ref2va';
  const champs: readonly string[] = ref ? ['subject_definitions:', 'summary:', 'retention_analysis:', 'detailed_description:', 'overall_soundscape:', 'non_diegetic_music:'] : CHAMPS;
  const positions = champs.map((c) => texte.indexOf(c));
  champs.forEach((c, i) => {
    if (positions[i] < 0) erreurs.push(`champ « ${c.slice(0, -1)} » absent`);
  });
  if (positions.every((p) => p >= 0) && positions.some((p, i) => i > 0 && p <= positions[i - 1])) {
    erreurs.push('champs dans le mauvais ordre : description, ambiance sonore, musique');
  }
  for (const m of texte.matchAll(/^([a-z][a-z_]+):/gm)) {
    if (!champs.includes(`${m[1]}:`)) {
      erreurs.push(`champ « ${m[1]} » inventé : champ hors du dialecte sélectionné (le texte à l’écran va dans la description, entre guillemets)`);
    }
  }

  const iDescription = ref ? 3 : 0;
  const description = positions[iDescription] >= 0 ? texte.slice(positions[iDescription], positions[iDescription + 1] > positions[iDescription] ? positions[iDescription + 1] : undefined) : '';
  if (ref) {
    const sujets = ctx.references?.sujets ?? [];
    const nbImages = sujets.reduce((n, s) => n + s.images, 0) + (ctx.references?.composition ?? 0);
    erreurs.push(...validerPromptRef(texte, sujets.length, nbImages));
    if (!texte.startsWith('subject_definitions:')) erreurs.push('en Ref2VA, commencer par subject_definitions:');
    if (!/summary:\s*\[reference generation\]/.test(texte)) erreurs.push('summary doit commencer par [reference generation]');
    if (!/detailed_description:\s*[^[]+\[Shot 1\]/.test(texte)) erreurs.push('le style doit précéder [Shot 1] en Ref2VA');
  }
  const plans = [...description.matchAll(/\[Shot (\d+)\]\s*(At (\d{2}):(\d{2})\.(\d{3}),)?/g)];
  if (!plans.length) erreurs.push('aucun plan « [Shot 1] » dans la description');
  plans.forEach((m, i) => {
    if (Number(m[1]) !== i + 1) erreurs.push(`numéros de plans non consécutifs : [Shot ${m[1]}] en position ${i + 1}`);
  });
  if (plans[0]?.[2]) erreurs.push('[Shot 1] ne doit pas porter d’horodatage');
  let precedent = 0;
  for (const m of plans.slice(1)) {
    if (!m[2]) {
      erreurs.push(`[Shot ${m[1]}] doit commencer par « At MM:SS.mmm, »`);
      continue;
    }
    const t = Number(m[3]) * 60 + Number(m[4]) + Number(m[5]) / 1000;
    if (t <= precedent) erreurs.push(`horodatage de [Shot ${m[1]}] non strictement croissant (${m[2]})`);
    if (t >= ctx.dureeS) erreurs.push(`horodatage de [Shot ${m[1]}] hors de la durée de ${ctx.dureeS.toFixed(2)} s`);
    precedent = t;
  }

  const premiereLigne = texte.split('\n')[0] ?? '';
  if (ctx.mode === 't2va') {
    if (!premiereLigne.startsWith('integrated_multimodal_description: [Shot 1]')) {
      erreurs.push('en T2VA, le prompt commence directement par « integrated_multimodal_description: [Shot 1] »');
    }
  } else if (!ref) {
    const attendue = instructionH3({ mode: ctx.mode, dureeS: ctx.dureeS, dernierPlan: Math.max(1, plans.length) });
    if (premiereLigne !== attendue) erreurs.push(`ligne d’instruction ${ctx.mode.toUpperCase()} absente ou inexacte ; attendue : ${attendue}`);
    else if ((texte.split('\n')[1] ?? 'x').trim() !== '') erreurs.push('une ligne vide doit suivre la ligne d’instruction');
  }

  const blocs = [...texte.matchAll(/<d>\[([^\]]+)\]\s*([\s\S]*?)<\/d>/g)].map((m) => ({ langue: m[1], texte: m[2].trim() }));
  for (const replique of ctx.dialogues ?? []) {
    if (!blocs.some((b) => b.texte === replique.trim())) erreurs.push(`réplique absente ou modifiée, à recopier mot pour mot : ${replique}`);
  }
  const disponibles = [...blocs];
  for (const replique of ctx.dialoguesAvecLangue ?? []) {
    const i = disponibles.findIndex((b) => b.texte === replique.texte.trim() && b.langue === replique.langue);
    if (i < 0) erreurs.push(`langue ou texte de la réplique incorrect : ${replique.texte}`);
    else disponibles.splice(i, 1);
  }
  if (ctx.dialoguesAvecLangue !== undefined) {
    const ouvertures = (texte.match(/<d>/g) ?? []).length;
    const fermetures = (texte.match(/<\/d>/g) ?? []).length;
    if (ouvertures !== blocs.length || fermetures !== blocs.length) erreurs.push('balises de réplique mal formées');
    for (const bloc of disponibles) erreurs.push(`réplique en trop ou langue incorrecte : ${bloc.texte}`);
  }
  return erreurs;
}
