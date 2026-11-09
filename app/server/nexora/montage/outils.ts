/**
 * Les quatre outils typés de montage du Producteur (`analyze_media`, `plan_edit`, `critique`, `revise`), avec leurs
 * garde-fous, hors de agent.ts pour garder celui-ci lisible. Le même registre sert l'agent (Zod → JSON Schema) et le
 * serveur MCP (mcp/server.ts) : Claude peut ainsi enseigner l'élève dans le format exact qu'il lira.
 *
 * Garde-fous (code, jamais prompt) : un plan invalide n'est jamais gardé (validateur) ; `plan_edit` retombe sur
 * `montage_auto` à tout échec ; au plus 2 tours critique → revise par montage ; une révision n'est gardée que si le
 * score en code ne baisse pas ; les plans à tourner (generations) sont plafonnés en crédits et rien ne se dépense ici ;
 * seuls les médias du projet (résolus par `deps.analyser`) sont lisibles.
 */
import { z } from 'zod';
import type { ClientLlm } from '../llm.js';
import type { AnalyseMedia } from './analyse.js';
import { critiquer } from './critique.js';
import { type EditPlan, FORMATS, GENRES, dureeTotaleS, framesDe } from './editplan.js';
import { coutCredits, mesurer } from './metriques.js';
import { planifierMontage } from './planifier.js';
import { MAX_RUSTINES, reviser } from './revise.js';
import type { Brief, ClipInfo } from './types.js';
import { vueTexte } from './analyse.js';

export const MAX_TOURS_CRITIQUE = 2;

export interface EtatMontage { brief: Brief; plan: EditPlan; tours: number; source: 'llm' | 'repli'; score: number }
export interface DepsMontage {
  /** Analyse (avec cache) des médias du projet par identifiant ; refuse tout identifiant hors projet. */
  analyser: (medias: string[]) => Promise<Record<string, AnalyseMedia>>;
  /** Plafond de crédits pour les plans à tourner demandés par un montage. */
  plafondCredits: number;
}

const idMedia = z.string().min(1).max(40).regex(/^[\w.-]+$/, 'identifiant de média du projet');
export const SCHEMAS_MONTAGE = {
  analyze_media: z.object({ medias: z.array(idMedia).min(1).max(8).describe('identifiants de médias du projet (vidéos, musique, voix)') }),
  plan_edit: z.object({
    brief: z.string().min(3).max(600).describe('ce que doit être le montage, en français'),
    genre: z.enum(GENRES), format: z.enum(FORMATS),
    duree_cible_s: z.number().min(5).max(120),
    medias: z.array(idMedia).min(1).max(12).describe('vidéos à monter'),
    musique: idMedia.optional(), voix: idMedia.optional(),
    textes: z.array(z.string().min(1).max(84)).max(6).optional().describe('textes imposés, posés mot pour mot'),
  }),
  critique: z.object({}),
  revise: z.object({ rustines: z.array(z.record(z.string(), z.unknown())).min(1).max(MAX_RUSTINES).describe('opérations regler_plan, echanger, supprimer, inserer_apres, regler_texte, ajouter_texte, supprimer_texte, regler_audio') }),
} as const;

export const DEFINITIONS_MONTAGE = [
  { nom: 'analyze_media', description: 'Vue compacte de médias du projet : durée, coupes de plan, silences, sonie, tempo, temps forts, énergie. Gratuit, en cache.', schema: SCHEMAS_MONTAGE.analyze_media },
  { nom: 'plan_edit', description: 'Brief + médias → EditPlan v1 valide (montage sur la musique, textes, audio). Retombe sur le montage automatique si le modèle échoue. Gratuit : ne rend rien, ne dépense rien.', schema: SCHEMAS_MONTAGE.plan_edit },
  { nom: 'critique', description: 'Mesures en code du montage courant (rythme vs énergie, coupes sur temps forts, doublons, texte, audio, crédits) avec écarts typés et indices. 2 tours au plus.', schema: SCHEMAS_MONTAGE.critique },
  { nom: 'revise', description: 'Applique des rustines (par id de plan) au montage courant ; revalide ; refusé si le plan devient invalide ou si le score baisse.', schema: SCHEMAS_MONTAGE.revise },
] as const;

/** Intervalles de parole = complément des silences. */
export function motsDepuisSilences(dureeS: number, silences: [number, number][]): [number, number][] {
  const mots: [number, number][] = [];
  let t = 0;
  for (const [a, b] of [...silences].sort((x, y) => x[0] - y[0])) { if (a - t > 0.1) mots.push([Math.round(t * 100) / 100, Math.round(a * 100) / 100]); t = Math.max(t, b); }
  if (dureeS - t > 0.1) mots.push([Math.round(t * 100) / 100, Math.round(dureeS * 100) / 100]);
  return mots;
}

export function briefDepuisAnalyses(a: z.infer<typeof SCHEMAS_MONTAGE.plan_edit>, an: Record<string, AnalyseMedia>): Brief {
  const clips: ClipInfo[] = a.medias.map((id) => {
    const x = an[id];
    if (!x?.a_video) throw new Error(`${id} n’est pas une vidéo du projet`);
    return { id, duree_s: x.duree_s, a_audio: x.a_audio, coupes_s: x.coupes_s };
  });
  const m = a.musique ? an[a.musique] : undefined;
  if (a.musique && !m?.a_audio) throw new Error(`${a.musique} n’est pas un média audio du projet`);
  const v = a.voix ? an[a.voix] : undefined;
  if (a.voix && !v?.a_audio) throw new Error(`${a.voix} n’est pas un média audio du projet`);
  return {
    id: 'projet', partition: 'test', genre: a.genre, format: a.format, duree_cible_s: a.duree_cible_s, fps: 24, enonce: a.brief, textes_imposes: a.textes ?? [], clips,
    ...(m ? { musique: { id: a.musique!, duree_s: m.duree_s, bpm: m.bpm, battues_s: m.battues_s, energie: m.energie } } : {}),
    ...(v ? { voix: { id: a.voix!, duree_s: v.duree_s, mots: motsDepuisSilences(v.duree_s, v.silences_s) } } : {}),
  };
}

/** Résumé compact d'un plan pour le modèle : un plan par ligne, les identifiants sont ce que `revise` manipule. */
export function resumePlan(p: EditPlan): string {
  return [
    `${p.video.length} plans, ${dureeTotaleS(p).toFixed(1)} s (${framesDe(dureeTotaleS(p), p.fps)} images à ${p.fps} i/s)`,
    ...p.video.map((c) => `${c.id} ${c.src} entree ${c.entree_f} duree ${c.duree_f}${c.vitesse !== 1 ? ` x${c.vitesse}` : ''}${c.transition_in.type !== 'cut' ? ` ${c.transition_in.type}${c.transition_in.duree_f}` : ''}`),
    ...p.textes.map((t, i) => `texte ${i}: « ${t.texte.slice(0, 30)} » ${t.debut_f}+${t.duree_f}`),
  ].join('\n');
}

export async function executerOutilMontage(
  etat: EtatMontage | undefined, nom: string, args: Record<string, unknown>, deps: { llm: ClientLlm | null; montage?: DepsMontage },
): Promise<{ etat: EtatMontage | undefined; resultat: unknown }> {
  const d = deps.montage;
  if (!d) return { etat, resultat: { erreur: 'outils de montage indisponibles sur ce poste' } };
  switch (nom) {
    case 'analyze_media': {
      const a = SCHEMAS_MONTAGE.analyze_media.parse(args);
      const an = await d.analyser(a.medias);
      return { etat, resultat: { medias: Object.entries(an).map(([id, x]) => vueTexte(id, x)) } };
    }
    case 'plan_edit': {
      const a = SCHEMAS_MONTAGE.plan_edit.parse(args);
      const brief = briefDepuisAnalyses(a, await d.analyser([...a.medias, ...(a.musique ? [a.musique] : []), ...(a.voix ? [a.voix] : [])]));
      const r = await planifierMontage(deps.llm, brief, { memoire: true, reparations: 1, tours: 0, maxAppels: 3 });
      let plan = r.plan;
      const notes = [...r.notes];
      if (coutCredits(plan) > d.plafondCredits) { plan = { ...plan, generations: [] }; notes.push(`plans à tourner retirés : au-dessus du plafond de ${d.plafondCredits} crédits`); }
      const m = mesurer(plan, brief);
      const e: EtatMontage = { brief, plan, tours: 0, source: r.source, score: m.composite };
      return { etat: e, resultat: { ok: true, source: r.source, score: m.composite, credits: m.credits, plan: resumePlan(plan), ecarts: m.ecarts.slice(0, 5).map((x) => `${x.clip ?? ''} ${x.message} → ${x.indice}`), notes: notes.slice(0, 3) } };
    }
    case 'critique': {
      if (!etat) return { etat, resultat: { erreur: 'aucun montage en cours : appelle plan_edit d’abord' } };
      if (etat.tours >= MAX_TOURS_CRITIQUE) return { etat, resultat: { erreur: `${MAX_TOURS_CRITIQUE} tours critique/revise au plus par montage : garde le plan actuel` } };
      const c = await critiquer(etat.plan, etat.brief);
      return { etat: { ...etat, tours: etat.tours + 1, score: c.composite }, resultat: { score: c.composite, resume: c.resume } };
    }
    case 'revise': {
      if (!etat) return { etat, resultat: { erreur: 'aucun montage en cours : appelle plan_edit d’abord' } };
      const a = SCHEMAS_MONTAGE.revise.parse(args);
      const ctx = { inventaire: Object.fromEntries([...etat.brief.clips.map((c) => [c.id, { duree_s: c.duree_s }] as const), ...(etat.brief.musique ? [[etat.brief.musique.id, { duree_s: etat.brief.musique.duree_s }] as const] : []), ...(etat.brief.voix ? [[etat.brief.voix.id, { duree_s: etat.brief.voix.duree_s }] as const] : [])]), duree_cible_s: etat.brief.duree_cible_s };
      const r = reviser(etat.plan, a.rustines, ctx);
      if (!r.ok) return { etat, resultat: { erreur: r.message } };
      const apres = mesurer(r.plan, etat.brief);
      if (apres.composite < etat.score - 1e-9) return { etat, resultat: { erreur: `rustines refusées : le score baisserait (${etat.score.toFixed(3)} → ${apres.composite.toFixed(3)})` } };
      return { etat: { ...etat, plan: r.plan, score: apres.composite }, resultat: { ok: true, score: apres.composite, plan: resumePlan(r.plan) } };
    }
    default:
      return { etat, resultat: { erreur: `outil de montage inconnu : ${nom}` } };
  }
}
export const NOMS_OUTILS_MONTAGE: ReadonlySet<string> = new Set(DEFINITIONS_MONTAGE.map((x) => x.nom));
