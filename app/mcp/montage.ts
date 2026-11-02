/**
 * Outils MCP du harnais de montage : Claude (le professeur) pilote EXACTEMENT les mêmes fonctions que l'élève (GLM) lit :
 * même EditPlan v1, même validateur, mêmes métriques, mêmes rustines (recherche/14 §3). Aucune conversion entre
 * l'enseignement et l'usage. Tout est local et gratuit (ffmpeg seul) ; rien ne dépense de crédits.
 * `montage_proposer_exemplaire` n'écrit que dans memoire/propositions/ (file de relecture) : le savoir actif ne change
 * que par revue de diff (anti-empoisonnement, recherche/14 §7).
 */
import { mkdirSync, writeFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';
import type { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js';
import { z } from 'zod';
import { analyserMedia, vueTexte } from '../server/nexora/montage/analyse.ts';
import { montageAuto } from '../server/nexora/montage/auto.ts';
import { critiquer } from '../server/nexora/montage/critique.ts';
import { EditPlanSchema, FORMATS, GENRES, validerEditPlan } from '../server/nexora/montage/editplan.ts';
import { chargerMemoire, recupererSavoir } from '../server/nexora/montage/memoire.ts';
import { briefDepuisAnalyses } from '../server/nexora/montage/outils.ts';
import { rendreEditPlan } from '../server/nexora/montage/rendu.ts';
import { reviser } from '../server/nexora/montage/revise.ts';

type Enveloppe = { content: { type: 'text'; text: string }[]; isError?: boolean };
const RO = { readOnlyHint: true, openWorldHint: false } as const;
const ECRIT = { readOnlyHint: false, destructiveHint: false, openWorldHint: false } as const;

const contexte = {
  brief: z.string().min(3).describe('énoncé du montage, en français'),
  genre: z.enum(GENRES), format: z.enum(FORMATS), duree_cible_s: z.number().min(5).max(120),
  medias: z.record(z.string(), z.string()).describe('identifiant -> chemin local des vidéos à monter, ex. {"m1": "/chemin/a.mp4"}'),
  musique: z.record(z.string(), z.string()).optional().describe('{"musique": "/chemin/piste.flac"} (un seul)'),
  voix: z.record(z.string(), z.string()).optional().describe('{"voix": "/chemin/voix.wav"} (un seul)'),
  textes: z.array(z.string()).optional().describe('textes imposés, mot pour mot'),
};
type Contexte = { brief: string; genre: (typeof GENRES)[number]; format: (typeof FORMATS)[number]; duree_cible_s: number; medias: Record<string, string>; musique?: Record<string, string>; voix?: Record<string, string>; textes?: string[] };

async function briefDe(c: Contexte) {
  const chemins = { ...c.medias, ...(c.musique ?? {}), ...(c.voix ?? {}) };
  const analyses = Object.fromEntries(await Promise.all(Object.entries(chemins).map(async ([id, f]) => [id, await analyserMedia(f)] as const)));
  const brief = briefDepuisAnalyses({ brief: c.brief, genre: c.genre, format: c.format, duree_cible_s: c.duree_cible_s, medias: Object.keys(c.medias), musique: c.musique && Object.keys(c.musique)[0], voix: c.voix && Object.keys(c.voix)[0], textes: c.textes }, analyses);
  return { brief, chemins, analyses };
}

export function enregistrerMontage(server: McpServer, text: (v: unknown) => any, safe: <A>(fn: (a: A, extra: any) => Promise<{ content: any[] }>) => (a: A, extra: any) => Promise<any>): void {
  const reg = server.registerTool.bind(server) as (...a: unknown[]) => void;
  const plan = z.record(z.string(), z.unknown()).describe('EditPlan v1 (JSON, durées en images entières)');

  reg('montage_analyze_media', {
    title: 'Montage : analyser des médias', description: 'Vue compacte (durée, coupes de plan, silences, sonie, tempo, temps forts, énergie) de fichiers locaux ; ffmpeg seul, gratuit, en cache.',
    inputSchema: { fichiers: z.record(z.string(), z.string()).describe('identifiant -> chemin local') }, annotations: RO,
  }, safe(async (a: { fichiers: Record<string, string> }) => ({ content: [text(await Promise.all(Object.entries(a.fichiers).map(async ([id, f]) => vueTexte(id, await analyserMedia(f)))))] })));

  reg('montage_auto', {
    title: 'Montage : base déterministe (montage_auto)', description: 'Clips + musique + énergie → EditPlan v1 valide, sans modèle : le plancher de qualité et le repli de l’élève. À prendre comme point de départ.',
    inputSchema: contexte, annotations: RO,
  }, safe(async (a: Contexte) => { const { brief } = await briefDe(a); return { content: [text(montageAuto(brief))] }; }));

  reg('montage_valider', {
    title: 'Montage : valider et mesurer un EditPlan', description: 'Valide (schéma + invariants) puis mesure en code (rythme vs énergie, coupes sur temps forts, doublons, texte, audio, crédits) ; rend les écarts typés avec indices. Même fonction que `critique` de l’élève.',
    inputSchema: { ...contexte, plan }, annotations: RO,
  }, safe(async (a: Contexte & { plan: Record<string, unknown> }) => {
    const { brief } = await briefDe(a);
    const v = validerEditPlan(a.plan);
    if (!v.ok) return { content: [text({ valide: false, erreurs: v.erreurs })] };
    const c = await critiquer(v.plan, brief);
    return { content: [text({ valide: true, score: c.composite, metriques: Object.fromEntries(Object.entries(c.metriques.metriques).map(([k, m]) => [k, m.score])), credits: c.metriques.credits, resume: c.resume, avertissements: v.avertissements })] };
  }));

  reg('montage_revise', {
    title: 'Montage : appliquer des rustines', description: 'regler_plan, echanger, supprimer, inserer_apres, regler_texte, ajouter_texte, supprimer_texte, regler_audio (par id de plan) ; revalide ; rend le plan révisé et son score.',
    inputSchema: { ...contexte, plan, rustines: z.array(z.record(z.string(), z.unknown())).max(12) }, annotations: RO,
  }, safe(async (a: Contexte & { plan: Record<string, unknown>; rustines: unknown[] }) => {
    const { brief } = await briefDe(a);
    const base = EditPlanSchema.parse(a.plan);
    const inventaire = Object.fromEntries([...brief.clips.map((c) => [c.id, { duree_s: c.duree_s }] as const)]);
    const r = reviser(base, a.rustines, { inventaire: { ...inventaire, ...(brief.musique ? { [brief.musique.id]: { duree_s: brief.musique.duree_s } } : {}), ...(brief.voix ? { [brief.voix.id]: { duree_s: brief.voix.duree_s } } : {}) }, duree_cible_s: a.duree_cible_s });
    if (!r.ok) return { content: [text({ ok: false, erreurs: r.erreurs })] };
    const c = await critiquer(r.plan, brief);
    return { content: [text({ ok: true, score: c.composite, plan: r.plan })] };
  }));

  reg('montage_rendre', {
    title: 'Montage : rendre un EditPlan (ffmpeg)', description: 'Valide puis rend un EditPlan v1 en MP4 (coupes, fondus, rampes, zoom, texte, musique, voix, ducking, −14 LUFS). `apercu` : demi-définition, rapide. Aucun crédit.',
    inputSchema: { plan, medias: z.record(z.string(), z.string()).describe('identifiant de source -> chemin local (vidéos, musique, voix)'), sortie: z.string().describe('chemin du MP4'), apercu: z.boolean().default(true) }, annotations: ECRIT,
  }, safe(async (a: { plan: Record<string, unknown>; medias: Record<string, string>; sortie: string; apercu: boolean }) => {
    const r = await rendreEditPlan(a.plan, (src) => { const f = a.medias[src]; if (!f) throw new Error(`source sans fichier : ${src}`); return f; }, a.sortie, { apercu: a.apercu });
    return { content: [text(r)] };
  }));

  reg('montage_savoir', {
    title: 'Montage : savoir récupéré pour un brief', description: 'La recette et l’UNIQUE exemplaire que l’élève recevrait pour ce brief (k = 1) ; sert à vérifier ce que la mémoire lui montre.',
    inputSchema: { brief: z.string(), genre: z.enum(GENRES), format: z.enum(FORMATS), duree_cible_s: z.number() }, annotations: RO,
  }, safe(async (a: { brief: string; genre: (typeof GENRES)[number]; format: (typeof FORMATS)[number]; duree_cible_s: number }) => {
    const s = recupererSavoir({ enonce: a.brief, genre: a.genre, format: a.format, duree_cible_s: a.duree_cible_s });
    return { content: [text({ versions: s.versions, recette: s.recette?.texte, exemplaire: s.segment && { id: s.segment.id, description: s.segment.description }, total_exemplaires: chargerMemoire().segments.length })] };
  }));

  reg('montage_proposer_exemplaire', {
    title: 'Montage : proposer un exemplaire à la relecture', description: 'Le professeur propose un montage réussi comme exemplaire : validé, anonymisé par le relecteur, écrit dans memoire/propositions/ (statut a_relire). N’entre dans le savoir actif que par revue de diff.',
    inputSchema: { id: z.string().regex(/^[a-z0-9-]{3,60}$/), genre: z.array(z.enum(GENRES)).min(1), format: z.array(z.enum(FORMATS)).min(1), etiquette: z.string().max(60), description: z.string().max(400), mots_cles: z.array(z.string()).max(20), origine: z.string().max(200), plan }, annotations: ECRIT,
  }, safe(async (a: { id: string; genre: string[]; format: string[]; etiquette: string; description: string; mots_cles: string[]; origine: string; plan: Record<string, unknown> }) => {
    const v = validerEditPlan(a.plan);
    if (!v.ok) return { content: [text({ ecrit: false, erreurs: v.erreurs })] };
    const dossier = join(dirname(fileURLToPath(import.meta.url)), '../server/nexora/memoire/propositions');
    mkdirSync(dossier, { recursive: true });
    const fichier = join(dossier, `${a.id}.json`);
    writeFileSync(fichier, JSON.stringify({ id: a.id, version: 1, genre: a.genre, format: a.format, etiquette: a.etiquette, origine: a.origine, description: a.description, mots_cles: a.mots_cles, statut: 'a_relire', extrait_edl: v.plan }, null, 1) + '\n');
    return { content: [text({ ecrit: true, fichier, suite: 'relire le diff, remplacer les valeurs concrètes par des jetons, puis déplacer dans memoire/segments/' })] };
  }));
}
export type { Enveloppe };
