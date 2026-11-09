/**
 * « Monter » dans le Producteur : un film tourné (plans + bande originale) devient un EditPlan, rendu en aperçu.
 * Base = `montageAuto` (code seul, gratuit, déterministe : le banc a montré qu'un LLM ne le bat pas sur les métriques) ;
 * « Améliorer » = un seul tour critique → rustines par le LLM, gardé seulement si le score en code monte.
 * Rien ne se dépense ici : aucun plan à tourner n'est demandé.
 */
import { avecCompetences } from '../competences.js';
import { type ClientLlm, lireJson } from '../llm.js';
import type { AnalyseMedia } from './analyse.js';
import { montageAuto } from './auto.js';
import { critiquer } from './critique.js';
import { type EditPlan, type Format, type Genre, dureeTotaleS } from './editplan.js';
import { mesurer, type RapportMetriques } from './metriques.js';
import { reviser } from './revise.js';
import type { Brief } from './types.js';
import { versClip, versMusique } from './analyse.js';

export const GENRES_MONTAGE: readonly Genre[] = ['pub', 'bande-annonce', 'explicatif', 'social'];

export interface EtatMontageFilm {
  film: number;
  brief: Brief;
  plan: EditPlan;
  source: 'code' | 'llm';
  tours: number;
  score: number;
}

export interface VueMetriques {
  score: number;
  rythme: number; battues: number; doublons: number; texte: number; audio: number;
  ecarts: { gravite: string; message: string; indice: string }[];
  plans: number; dureeS: number; dureeMoyennePlanS: number; coupesParMinute: number; bpm: number | null; credits: number;
}

/** Sources mesurées d'un brief, utilisées par le validateur du plan et le rendu. */
export function inventaireDuBrief(brief: Brief): Record<string, { duree_s: number }> {
  return Object.fromEntries([
    ...brief.clips.map((c) => [c.id, { duree_s: c.duree_s }] as const),
    ...(brief.musique ? [[brief.musique.id, { duree_s: brief.musique.duree_s }] as const] : []),
    ...(brief.voix ? [[brief.voix.id, { duree_s: brief.voix.duree_s }] as const] : []),
  ]);
}

/** Brief d'un film tourné : les plans sont les clips (ids = ids de prises), la bande originale est la musique. */
export function briefDuFilm(o: {
  clips: { id: string; analyse: AnalyseMedia }[]; musique?: { id: string; analyse: AnalyseMedia };
  genre: Genre; format: Format; dureeCibleS?: number; enonce?: string; textes?: string[];
}): Brief {
  const somme = o.clips.reduce((s, c) => s + c.analyse.duree_s, 0);
  const cible = Math.max(2, Math.min(o.dureeCibleS ?? somme, 600));
  return {
    id: 'film', partition: 'test', genre: o.genre, format: o.format, duree_cible_s: Math.round(cible * 10) / 10, fps: 24,
    enonce: o.enonce ?? 'Monter les plans du film sur la musique.', textes_imposes: o.textes ?? [],
    clips: o.clips.map((c) => versClip(c.id, c.analyse)),
    ...(o.musique ? { musique: versMusique(o.musique.id, o.musique.analyse) } : {}),
  };
}

export function monterEnCode(brief: Brief, film: number): EtatMontageFilm {
  const plan = montageAuto(brief);
  return { film, brief, plan, source: 'code', tours: 0, score: mesurer(plan, brief).composite };
}

export function vueMetriques(plan: EditPlan, brief: Brief): VueMetriques {
  const m: RapportMetriques = mesurer(plan, brief);
  const d = dureeTotaleS(plan);
  return {
    score: m.composite,
    rythme: m.metriques.rythme.score, battues: m.metriques.battues.score, doublons: m.metriques.doublons.score, texte: m.metriques.texte.score, audio: m.metriques.audio.score,
    ecarts: m.ecarts.slice(0, 6).map((e) => ({ gravite: e.gravite, message: e.message, indice: e.indice })),
    plans: plan.video.length, dureeS: Math.round(d * 100) / 100,
    dureeMoyennePlanS: Math.round((d / Math.max(1, plan.video.length)) * 100) / 100,
    coupesParMinute: Math.round(((plan.video.length - 1) / Math.max(1, d)) * 60 * 10) / 10,
    bpm: brief.musique?.bpm ?? null, credits: m.credits,
  };
}

export interface ResultatAmelioration { etat: EtatMontageFilm; avant: number; apres: number; gardee: boolean; message: string }

/** Un tour critique → rustines. Sans LLM, ou si rien ne s'améliore, le plan est rendu inchangé avec la raison. */
export async function ameliorerMontage(etat: EtatMontageFilm, llm: ClientLlm | null): Promise<ResultatAmelioration> {
  const avant = etat.score;
  const inchange = (message: string): ResultatAmelioration => ({ etat: { ...etat, tours: etat.tours + 1 }, avant, apres: avant, gardee: false, message });
  const c = await critiquer(etat.plan, etat.brief);
  if (!c.metriques.porte || !c.ecarts.length || c.composite >= 0.97) return inchange('Le montage passe déjà toutes les mesures : rien à corriger.');
  if (!llm) return inchange('Aucun LLM branché : le montage automatique reste tel quel.');
  const ctx = { inventaire: inventaireDuBrief(etat.brief), duree_cible_s: etat.brief.duree_cible_s };
  try {
    const messages: { role: 'system' | 'user' | 'assistant'; content: string }[] = [
      { role: 'system', content: avecCompetences('monteur', 'Tu es le monteur de Nexora Creative. Tu réponds uniquement par du JSON.') },
      { role: 'user', content: `Plan courant :\n${etat.plan.video.map((v) => `${v.id} ${v.src} entree ${v.entree_f} duree ${v.duree_f}`).join('\n')}\nDurée des sources (images à ${etat.brief.fps} i/s) : ${etat.brief.clips.map((x) => `${x.id}=${Math.floor(x.duree_s * etat.brief.fps)}`).join(', ')}\n\nCritique mesurée :\n${c.resume}\n\nCorrige avec au plus 8 rustines, JSON seul : {"rustines":[{"op":"regler_plan","id":"p3","duree_f":30}]}. Opérations : regler_plan{id,entree_f,duree_f,vitesse}, echanger{a,b}, supprimer{id}. Si tu raccourcis un plan, rallonge un autre du même nombre d'images. Un plan ne peut pas lire au-delà de la fin de sa source.` },
    ];
    let refus = '';
    // Un essai, plus une réparation avec le message du validateur : c'est encore un seul tour d'amélioration.
    for (let essai = 0; essai < 2; essai++) {
      const texte = await llm.completer('monteur', messages, { json: true, temperature: 0.2, maxTokens: 4000 });
      messages.push({ role: 'assistant', content: texte });
      let rustines: unknown;
      try { rustines = lireJson<{ rustines?: unknown }>(texte).rustines; } catch { refus = 'réponse illisible'; break; }
      const rev = reviser(etat.plan, rustines, ctx);
      if (!rev.ok) {
        refus = rev.message.replace(/\s+/g, ' ').slice(0, 160);
        messages.push({ role: 'user', content: `Le validateur refuse tes rustines : ${rev.message}\nRenvoie des rustines corrigées, JSON seul.` });
        continue;
      }
      const apres = mesurer(rev.plan, etat.brief).composite;
      if (apres <= avant) return inchange(`Les rustines du modèle n’améliorent pas les mesures (${avant.toFixed(3)} → ${apres.toFixed(3)}) : montage conservé.`);
      return { etat: { ...etat, plan: rev.plan, source: 'llm', tours: etat.tours + 1, score: apres }, avant, apres, gardee: true, message: `Amélioré : ${avant.toFixed(3)} → ${apres.toFixed(3)}.` };
    }
    return inchange(`Rustines refusées par le validateur : ${refus}. Montage conservé.`);
  } catch (e) {
    return inchange(`Le modèle n’a pas répondu (${e instanceof Error ? e.message.slice(0, 80) : 'erreur'}) : montage conservé.`);
  }
}
