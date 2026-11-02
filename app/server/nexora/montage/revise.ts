/**
 * `revise` : applique des rustines typées (par identifiant de plan) à un EditPlan, puis REVALIDE. Le LLM ne réécrit pas
 * le plan entier : il corrige les identifiants signalés par `critique` (recherche/13 §4 n°5). Un plan qui deviendrait
 * invalide est refusé avec les violations, l'original reste intact.
 */
import { z } from 'zod';
import { type ContexteValidation, type EditPlan, type Violation, validerEditPlan } from './editplan.js';

const int = z.number().int();
const PatchPlan = z.object({ id: z.string(), entree_f: int.min(0).optional(), duree_f: int.min(1).optional(), vitesse: z.number().optional(), transition_in: z.object({ type: z.enum(['cut', 'fondu', 'dip', 'glisse']), duree_f: int.min(0) }).optional(), zoom: z.object({ de: z.number(), a: z.number() }).nullable().optional(), src: z.string().optional() });
export const PatchSchema = z.discriminatedUnion('op', [
  PatchPlan.extend({ op: z.literal('regler_plan') }),
  z.object({ op: z.literal('echanger'), a: z.string(), b: z.string() }),
  z.object({ op: z.literal('supprimer'), id: z.string() }),
  z.object({ op: z.literal('inserer_apres'), apres: z.string().nullable(), plan: z.unknown() }),
  z.object({ op: z.literal('regler_texte'), index: int.min(0), texte: z.string().optional(), debut_f: int.min(0).optional(), duree_f: int.min(1).optional(), taille_pct: z.number().optional(), position: z.enum(['haut', 'centre', 'bas']).optional() }),
  z.object({ op: z.literal('ajouter_texte'), texte: z.unknown() }),
  z.object({ op: z.literal('supprimer_texte'), index: int.min(0) }),
  z.object({ op: z.literal('regler_audio'), musique: z.record(z.string(), z.unknown()).optional(), ducking: z.object({ actif: z.boolean(), profondeur_db: z.number() }).optional(), cible_lufs: z.number().optional(), crete_db: z.number().optional(), fondu_coupe_ms: z.number().optional() }),
]);
export type Patch = z.infer<typeof PatchSchema>;
export const MAX_RUSTINES = 12;

export type ResultatRevision = { ok: true; plan: EditPlan; appliquees: number; avertissements: Violation[] } | { ok: false; erreurs: Violation[]; message: string };

export function reviser(plan: EditPlan, rustines: unknown, ctx: ContexteValidation = {}): ResultatRevision {
  const liste = z.array(PatchSchema).max(MAX_RUSTINES).safeParse(rustines);
  if (!liste.success) {
    const message = `rustines illisibles : ${liste.error.issues.slice(0, 3).map((i) => `${i.path.join('.')} ${i.message}`).join(' ; ')}`;
    return { ok: false, erreurs: [{ regle: 'rustine', chemin: 'rustines', message }], message };
  }
  const p = structuredClone(plan) as any;
  for (const r of liste.data) {
    const i = 'id' in r ? p.video.findIndex((c: any) => c.id === r.id) : -1;
    switch (r.op) {
      case 'regler_plan': {
        if (i < 0) return echec(`plan inconnu : ${r.id}`);
        const { op: _o, id: _i, ...champs } = r;
        for (const [k, v] of Object.entries(champs)) { if (v === null) delete p.video[i][k]; else if (v !== undefined) p.video[i][k] = v; }
        break;
      }
      case 'echanger': {
        const a = p.video.findIndex((c: any) => c.id === r.a), b = p.video.findIndex((c: any) => c.id === r.b);
        if (a < 0 || b < 0) return echec(`plan inconnu dans l’échange ${r.a}/${r.b}`);
        [p.video[a], p.video[b]] = [p.video[b], p.video[a]];
        break;
      }
      case 'supprimer':
        if (i < 0) return echec(`plan inconnu : ${r.id}`);
        p.video.splice(i, 1);
        break;
      case 'inserer_apres': {
        const pos = r.apres === null ? 0 : p.video.findIndex((c: any) => c.id === r.apres) + 1;
        if (r.apres !== null && pos === 0) return echec(`plan inconnu : ${r.apres}`);
        p.video.splice(pos, 0, r.plan);
        break;
      }
      case 'regler_texte': {
        const t = p.textes[r.index];
        if (!t) return echec(`texte ${r.index} inconnu`);
        for (const [k, v] of Object.entries(r)) if (k !== 'op' && k !== 'index' && v !== undefined) t[k] = v;
        break;
      }
      case 'ajouter_texte': p.textes.push(r.texte); break;
      case 'supprimer_texte': if (!p.textes[r.index]) return echec(`texte ${r.index} inconnu`); p.textes.splice(r.index, 1); break;
      case 'regler_audio': {
        if (r.musique) p.audio.musique = { ...(p.audio.musique ?? {}), ...r.musique };
        for (const k of ['ducking', 'cible_lufs', 'crete_db', 'fondu_coupe_ms'] as const) if (r[k] !== undefined) p.audio[k] = r[k];
        break;
      }
    }
  }
  const v = validerEditPlan(p, ctx);
  if (!v.ok) return { ok: false, erreurs: v.erreurs, message: `le plan révisé est invalide :\n${v.erreurs.map((e) => `- [${e.regle}] ${e.chemin} : ${e.message}`).join('\n')}` };
  return { ok: true, plan: v.plan!, appliquees: liste.data.length, avertissements: v.avertissements };
}
const echec = (message: string): ResultatRevision => ({ ok: false, erreurs: [{ regle: 'rustine', chemin: 'rustines', message }], message });
