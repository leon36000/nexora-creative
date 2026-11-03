/**
 * Nexora Creative : la recette d'un « Effet IA ici… » (EffectRecipe v1, tranche v0 de recherche/17 §A1.4).
 *
 * Le modèle propose une recette ; ce module dispose : catalogue fermé (généré depuis le registre GPU), bornes de chaque
 * paramètre, portée en images entières, plafonds, puis traduction en opérations FreeCut appliquées en un seul pas
 * d'annulation. Familles de la v0 : `gpu_stack` (pile d'effets WebGPU), `volume`, `texte`. Tout est P0 : gratuit,
 * aperçu direct dans le moniteur. Pur et sans store : testé seul.
 */
import type { EditOp } from '@/headless/edit-op-support'
import { getGpuEffectDefaultParams } from '@/infrastructure/gpu-effects/registry'
import { indexCatalogue, type EffetCatalogue } from './catalogue'

export type ValeurParam = number | boolean | string

export interface EffetPile {
  gpu: string
  params: Record<string, ValeurParam>
}

export type EtapeRecette =
  | { kind: 'gpu_stack'; effets: EffetPile[] }
  | { kind: 'volume'; db: number }
  | { kind: 'texte'; texte: string; position: 'haut' | 'milieu' | 'bas' }

export interface PorteeRecette {
  kind: 'plage' | 'clip'
  /** Première image (timeline). */
  debut: number
  /** Durée en images. */
  duree: number
  itemId?: string
}

export interface EffectRecipe {
  version: 1
  prompt: string
  resume: string
  portee: PorteeRecette
  etapes: EtapeRecette[]
  devis: { palier: 'P0'; credits: 0 }
}

export interface ElementCible {
  id: string
  type: string
  from: number
  durationInFrames: number
}

export interface ContexteRecette {
  fps: number
  /** Image du clic (repli : tête de lecture). */
  debut: number
  dureeParDefaut: number
  dureeMax: number
  element?: ElementCible
  hauteur?: number
}

export class RecetteInvalide extends Error {}

export const MAX_EFFETS = 8
export const MAX_ETAPES = 4
const MAX_TEXTE = 80

const fini = (v: unknown): v is number => typeof v === 'number' && Number.isFinite(v)
const borne = (v: number, min?: number, max?: number) =>
  Math.min(max ?? Infinity, Math.max(min ?? -Infinity, v))

function validerParams(
  brut: unknown,
  effet: EffetCatalogue,
  avert: string[],
): Record<string, ValeurParam> {
  const params: Record<string, ValeurParam> = {}
  if (!brut || typeof brut !== 'object') return params
  for (const [cle, v] of Object.entries(brut as Record<string, unknown>)) {
    const p = effet.params[cle]
    if (!p) {
      avert.push(`${effet.id} : paramètre « ${cle} » inconnu, ignoré`)
      continue
    }
    if (p.type === 'number' && fini(v)) params[cle] = borne(v, p.min, p.max)
    else if (p.type === 'boolean' && typeof v === 'boolean') params[cle] = v
    else if (p.type === 'select' && typeof v === 'string' && p.options?.includes(v)) params[cle] = v
    else if (p.type === 'color' && typeof v === 'string' && /^#[0-9a-f]{6}$/i.test(v)) params[cle] = v
    else avert.push(`${effet.id} : valeur de « ${cle} » invalide, ignorée`)
  }
  return params
}

function validerPortee(brute: unknown, ctx: ContexteRecette): PorteeRecette {
  const b = (brute ?? {}) as Record<string, unknown>
  if (b.kind === 'clip' && ctx.element) {
    return {
      kind: 'clip',
      debut: ctx.element.from,
      duree: ctx.element.durationInFrames,
      itemId: ctx.element.id,
    }
  }
  const debut = fini(b.debutS) ? Math.max(0, Math.round(b.debutS * ctx.fps)) : ctx.debut
  const duree = fini(b.dureeS) ? Math.round(b.dureeS * ctx.fps) : ctx.dureeParDefaut
  return {
    kind: 'plage',
    debut,
    duree: borne(duree, 1, ctx.dureeMax),
    ...(ctx.element ? { itemId: ctx.element.id } : {}),
  }
}

/** Valide une recette brute (LLM ou recette locale) contre le catalogue ; lève RecetteInvalide si rien n'est exécutable. */
export function validerRecette(
  brute: unknown,
  prompt: string,
  catalogue: EffetCatalogue[],
  ctx: ContexteRecette,
): { recette: EffectRecipe; avertissements: string[] } {
  const b = (brute ?? {}) as Record<string, unknown>
  const index = indexCatalogue(catalogue)
  const avert: string[] = []
  const etapes: EtapeRecette[] = []
  let effetsPoses = 0
  const sonore = !!ctx.element && ['video', 'audio'].includes(ctx.element.type)

  for (const e of (Array.isArray(b.etapes) ? b.etapes : []).slice(0, MAX_ETAPES)) {
    const etape = (e ?? {}) as Record<string, unknown>
    if (etape.kind === 'gpu_stack') {
      const effets: EffetPile[] = []
      for (const f of Array.isArray(etape.effets) ? etape.effets : []) {
        const fx = (f ?? {}) as Record<string, unknown>
        const def = typeof fx.gpu === 'string' ? index.get(fx.gpu) : undefined
        if (!def) {
          avert.push(`effet « ${String(fx.gpu)} » absent du catalogue, ignoré`)
          continue
        }
        if (effetsPoses >= MAX_EFFETS) {
          avert.push(`plus de ${MAX_EFFETS} effets : ${def.id} ignoré`)
          continue
        }
        effets.push({ gpu: def.id, params: validerParams(fx.params, def, avert) })
        effetsPoses++
      }
      if (effets.length) etapes.push({ kind: 'gpu_stack', effets })
    } else if (etape.kind === 'volume') {
      if (!sonore) avert.push('volume : aucun clip sonore sous le clic, ignoré')
      else if (fini(etape.db)) etapes.push({ kind: 'volume', db: borne(etape.db, -60, 12) })
      else avert.push('volume : valeur en dB manquante, ignoré')
    } else if (etape.kind === 'texte') {
      const texte = typeof etape.texte === 'string' ? etape.texte.trim().slice(0, MAX_TEXTE) : ''
      if (!texte) avert.push('texte : vide, ignoré')
      else {
        const position =
          etape.position === 'haut' || etape.position === 'milieu' ? etape.position : 'bas'
        etapes.push({ kind: 'texte', texte, position })
      }
    } else {
      avert.push(`étape « ${String(etape.kind)} » inconnue de la v0, ignorée`)
    }
  }

  if (!etapes.length)
    throw new RecetteInvalide(
      avert[0] ?? 'Aucune étape exécutable : décris un look, un effet, un texte ou un volume.',
    )
  const resume =
    typeof b.resume === 'string' && b.resume.trim()
      ? b.resume.trim().slice(0, 120)
      : prompt.trim().slice(0, 60)
  return {
    recette: {
      version: 1,
      prompt: prompt.slice(0, 300),
      resume,
      portee: validerPortee(b.portee, ctx),
      etapes,
      devis: { palier: 'P0', credits: 0 },
    },
    avertissements: avert,
  }
}

/** Valeur « neutre » d'un paramètre pour « plus fort / plus doux » : le défaut, ou l'autre borne s'il est à un bout. */
function neutre(p: EffetCatalogue['params'][string]): number {
  const d = p.defaut as number
  if (p.max !== undefined && d === p.max && p.min !== undefined) return p.min
  return d
}

/** « Plus fort » (facteur > 1) ou « plus doux » (< 1) : la même recette, chaque réglage éloigné ou rapproché du neutre. */
export function ajusterIntensite(
  recette: EffectRecipe,
  facteur: number,
  catalogue: EffetCatalogue[],
): EffectRecipe {
  const index = indexCatalogue(catalogue)
  return {
    ...recette,
    etapes: recette.etapes.map((e) => {
      if (e.kind === 'gpu_stack')
        return {
          ...e,
          effets: e.effets.map((fx) => {
            const def = index.get(fx.gpu)
            const params = { ...fx.params }
            for (const [cle, v] of Object.entries(params)) {
              const p = def?.params[cle]
              if (!p || p.type !== 'number' || typeof v !== 'number') continue
              const n = neutre(p)
              params[cle] = borne(n + (v - n) * facteur, p.min, p.max)
            }
            return { ...fx, params }
          }),
        }
      if (e.kind === 'volume') return { ...e, db: borne(e.db * facteur, -60, 12) }
      return e
    }),
  }
}

export interface PistesRecette {
  /** Piste vidéo au-dessus des plans qui porte les couches d'ajustement. */
  pisteEffets: string
  pisteTextes: string
}

/** Recette validée → opérations FreeCut (à appliquer dans `enUnePas`). */
export function recetteVersOps(
  recette: EffectRecipe,
  ctx: ContexteRecette & PistesRecette,
): EditOp[] {
  const { portee } = recette
  const ops: EditOp[] = []
  for (const e of recette.etapes) {
    if (e.kind === 'gpu_stack') {
      const effets = e.effets.map((fx) => ({
        type: 'gpu-effect' as const,
        gpuEffectType: fx.gpu,
        params: { ...getGpuEffectDefaultParams(fx.gpu), ...fx.params },
      }))
      if (portee.kind === 'clip' && portee.itemId) {
        for (const effet of effets)
          ops.push({
            op: 'addEffect',
            itemId: portee.itemId,
            gpuEffectType: effet.gpuEffectType,
            params: effet.params,
          })
      } else {
        ops.push({
          op: 'addItem',
          item: {
            id: crypto.randomUUID(),
            type: 'adjustment',
            trackId: ctx.pisteEffets,
            from: portee.debut,
            durationInFrames: portee.duree,
            label: `Effet IA · ${recette.resume}`.slice(0, 60),
            effects: effets.map((effect) => ({ id: crypto.randomUUID(), effect, enabled: true })),
            effectOpacity: 1,
          },
        })
      }
    } else if (e.kind === 'volume' && portee.itemId) {
      ops.push({ op: 'updateItem', id: portee.itemId, updates: { volume: e.db } })
    } else if (e.kind === 'texte') {
      const hauteur = ctx.hauteur ?? 1080
      ops.push({
        op: 'addText',
        text: e.texte,
        from: portee.debut,
        durationInFrames: portee.duree,
        trackId: ctx.pisteTextes,
        fontSize: Math.round(hauteur / 14),
        color: '#ffffff',
        textAlign: 'center',
        verticalAlign: e.position === 'haut' ? 'top' : e.position === 'milieu' ? 'middle' : 'bottom',
        label: e.texte.slice(0, 40),
      })
    }
  }
  return ops
}

/** Une ligne pour la bulle : ce que la recette va faire, et ce qu'elle coûte. */
export function resumeRecette(recette: EffectRecipe, fps: number): string {
  const effets = recette.etapes.reduce(
    (n, e) => n + (e.kind === 'gpu_stack' ? e.effets.length : 0),
    0,
  )
  const morceaux: string[] = []
  if (effets)
    morceaux.push(
      recette.portee.kind === 'clip'
        ? `${effets} effet${effets > 1 ? 's' : ''} sur le clip`
        : `${effets} effet${effets > 1 ? 's' : ''} sur une couche d’ajustement de ${(recette.portee.duree / fps).toFixed(1).replace('.', ',')} s`,
    )
  for (const e of recette.etapes) {
    if (e.kind === 'volume') morceaux.push(`volume ${e.db > 0 ? '+' : ''}${Math.round(e.db)} dB`)
    if (e.kind === 'texte') morceaux.push(`texte « ${e.texte.slice(0, 24)} »`)
  }
  return `${morceaux.join(' + ')} · gratuit, aperçu direct`
}
