/**
 * Nexora Creative : catalogue des effets que la bulle « Effet IA ici… » peut utiliser, généré à chaque chargement depuis
 * le registre WebGPU de FreeCut (il ne peut donc pas dériver du moteur). Seuls les paramètres qu'un modèle peut régler
 * sans éditeur dédié sont gardés (nombre, booléen, liste, couleur), avec leurs bornes.
 */
import { GPU_EFFECT_REGISTRY } from '@/infrastructure/gpu-effects/registry'
import type { GpuEffectDefinition } from '@/infrastructure/gpu-effects/types'

export interface ParamCatalogue {
  type: 'number' | 'boolean' | 'select' | 'color'
  defaut: number | boolean | string
  min?: number
  max?: number
  options?: string[]
}

export interface EffetCatalogue {
  id: string
  nom: string
  categorie: string
  params: Record<string, ParamCatalogue>
}

const PILOTABLES = new Set(['number', 'boolean', 'select', 'color'])

export function catalogueEffets(
  registre: Map<string, GpuEffectDefinition> = GPU_EFFECT_REGISTRY,
): EffetCatalogue[] {
  return [...registre.values()].map((e) => ({
    id: e.id,
    nom: e.name,
    categorie: e.category,
    params: Object.fromEntries(
      Object.entries(e.params)
        .filter(([, p]) => PILOTABLES.has(p.type))
        .map(([cle, p]) => [
          cle,
          {
            type: p.type as ParamCatalogue['type'],
            defaut: p.default,
            ...(p.min !== undefined ? { min: p.min } : {}),
            ...(p.max !== undefined ? { max: p.max } : {}),
            ...(p.options ? { options: p.options.map((o) => o.value) } : {}),
          },
        ]),
    ),
  }))
}

const court = (n: number) => String(Math.round(n * 1000) / 1000)

/** Une ligne par effet, lisible par un LLM : « gpu-vhs (stylize) : noise 0..1=0.25, … ». */
export function catalogueCompact(catalogue: EffetCatalogue[]): string {
  return catalogue
    .map((e) => {
      const params = Object.entries(e.params)
        .map(([cle, p]) => {
          if (p.type === 'number')
            return `${cle} ${p.min !== undefined ? court(p.min) : ''}..${p.max !== undefined ? court(p.max) : ''}=${court(p.defaut as number)}`
          if (p.type === 'select') return `${cle} [${(p.options ?? []).join('|')}]`
          return `${cle} ${p.type}`
        })
        .join(', ')
      return `${e.id} (${e.categorie}) : ${params}`
    })
    .join('\n')
}

export function indexCatalogue(catalogue: EffetCatalogue[]): Map<string, EffetCatalogue> {
  return new Map(catalogue.map((e) => [e.id, e]))
}
