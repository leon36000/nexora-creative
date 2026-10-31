/**
 * Prompts MiniMax H3 : ligne d'instruction et validateur déterministe, d'après le guide officiel
 * « Video Prompt Writing Guide (T2VA / I2VA / FL2VA / L2VA) » (vendor/minimax-h3-guides/). Un prompt refusé ici est
 * réparé avant tout appel GPU : une erreur de forme ne coûte jamais un rendu.
 */

export type ModeH3 = 't2va' | 'i2va' | 'fl2va' | 'l2va';

export interface ContexteH3 {
  mode: ModeH3;
  /** Durée effective de la vidéo, en secondes. */
  dureeS: number;
  /** Répliques fournies par l'utilisateur, à recopier mot pour mot dans <d>…</d>. */
  dialogues?: string[];
}

const CHAMPS = ['integrated_multimodal_description:', 'overall_soundscape:', 'non_diegetic_music:'] as const;

/** Ligne d'instruction exacte que le guide impose en tête du prompt (chaîne vide en T2VA). */
export function instructionH3(o: { mode: ModeH3; dureeS: number; dernierPlan: number }): string {
  const s = o.dureeS.toFixed(2);
  switch (o.mode) {
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

  const positions = CHAMPS.map((c) => texte.indexOf(c));
  CHAMPS.forEach((c, i) => {
    if (positions[i] < 0) erreurs.push(`champ « ${c.slice(0, -1)} » absent`);
  });
  if (positions.every((p) => p >= 0) && !(positions[0] < positions[1] && positions[1] < positions[2])) {
    erreurs.push('les trois champs ne sont pas dans l’ordre description, ambiance sonore, musique');
  }
  for (const m of texte.matchAll(/^([a-z][a-z_]+):/gm)) {
    if (!CHAMPS.includes(`${m[1]}:` as (typeof CHAMPS)[number])) {
      erreurs.push(`champ « ${m[1]} » inventé : le guide n’a que trois champs (le texte à l’écran va dans la description, entre guillemets)`);
    }
  }

  const description =
    positions[0] >= 0 ? texte.slice(positions[0], positions[1] > positions[0] ? positions[1] : undefined) : '';
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
  } else {
    const attendue = instructionH3({ mode: ctx.mode, dureeS: ctx.dureeS, dernierPlan: Math.max(1, plans.length) });
    if (premiereLigne !== attendue) erreurs.push(`ligne d’instruction ${ctx.mode.toUpperCase()} absente ou inexacte ; attendue : ${attendue}`);
    else if ((texte.split('\n')[1] ?? 'x').trim() !== '') erreurs.push('une ligne vide doit suivre la ligne d’instruction');
  }

  const blocs = [...texte.matchAll(/<d>\[[^\]]+\]\s*([\s\S]*?)<\/d>/g)].map((m) => m[1].trim());
  for (const replique of ctx.dialogues ?? []) {
    if (!blocs.some((b) => b === replique.trim())) erreurs.push(`réplique absente ou modifiée, à recopier mot pour mot : ${replique}`);
  }
  return erreurs;
}
