import { describe, expect, it } from 'vite-plus/test'
import { GPU_EFFECT_REGISTRY } from '@/infrastructure/gpu-effects/registry'
import { catalogueCompact, catalogueEffets } from './catalogue'
import {
  ajusterIntensite,
  RecetteInvalide,
  recetteVersOps,
  validerRecette,
  type ContexteRecette,
} from './recette'
import { PHRASES_CANON, RECETTES_LOCALES, recetteLocale } from './recettes-locales'

const catalogue = catalogueEffets()
const ctx: ContexteRecette = {
  fps: 30,
  debut: 6060, // 3 min 22 s à 30 i/s
  dureeParDefaut: 60,
  dureeMax: 900,
  element: { id: 'clip-1', type: 'video', from: 6000, durationInFrames: 300 },
}

describe('catalogue des effets (généré depuis le registre GPU)', () => {
  it('contient chaque effet du registre, sans en inventer', () => {
    const ids = new Set(catalogue.map((e) => e.id))
    for (const id of GPU_EFFECT_REGISTRY.keys()) expect(ids.has(id)).toBe(true)
    expect(ids.size).toBe(GPU_EFFECT_REGISTRY.size)
  })

  it('garde les bornes des paramètres numériques et écarte les paramètres non pilotables', () => {
    const vhs = catalogue.find((e) => e.id === 'gpu-vhs')!
    expect(vhs.params.noise).toMatchObject({ type: 'number', min: 0, max: 1 })
    for (const e of catalogue)
      for (const p of Object.values(e.params)) expect(['number', 'boolean', 'select', 'color']).toContain(p.type)
  })

  it('tient dans un prompt court', () => {
    const texte = catalogueCompact(catalogue)
    expect(texte).toContain('gpu-vhs')
    expect(texte.length).toBeLessThan(16_000)
  })
})

describe('validation de la recette (le code dispose)', () => {
  it('borne les paramètres, écarte les effets et paramètres inconnus, en le disant', () => {
    const { recette, avertissements } = validerRecette(
      {
        resume: 'VHS',
        etapes: [
          {
            kind: 'gpu_stack',
            effets: [
              { gpu: 'gpu-vhs', params: { noise: 9, inexistant: 3 } },
              { gpu: 'gpu-hologramme', params: {} },
            ],
          },
        ],
      },
      'vhs',
      catalogue,
      ctx,
    )
    const pile = recette.etapes[0]!
    expect(pile.kind).toBe('gpu_stack')
    if (pile.kind !== 'gpu_stack') return
    expect(pile.effets).toHaveLength(1)
    expect(pile.effets[0]!.params.noise).toBe(1)
    expect(pile.effets[0]!.params).not.toHaveProperty('inexistant')
    expect(avertissements.join(' ')).toMatch(/gpu-hologramme/)
    expect(recette.devis).toEqual({ palier: 'P0', credits: 0 })
  })

  it('refuse une recette vide ou sans étape exécutable', () => {
    expect(() => validerRecette({ etapes: [] }, 'x', catalogue, ctx)).toThrow(RecetteInvalide)
    expect(() =>
      validerRecette({ etapes: [{ kind: 'shader', code: 'boom' }] }, 'x', catalogue, ctx),
    ).toThrow(RecetteInvalide)
  })

  it('cale la portée sur des images entières dans la durée permise', () => {
    const { recette } = validerRecette(
      { portee: { debutS: 202.37, dureeS: 99 }, etapes: [{ kind: 'volume', db: -6 }] },
      'baisse le son',
      catalogue,
      ctx,
    )
    expect(Number.isInteger(recette.portee.debut)).toBe(true)
    expect(recette.portee.debut).toBe(Math.round(202.37 * 30))
    expect(recette.portee.duree).toBe(ctx.dureeMax)
  })

  it('borne le volume et le texte', () => {
    const { recette } = validerRecette(
      { etapes: [{ kind: 'volume', db: -200 }, { kind: 'texte', texte: 'x'.repeat(300) }] },
      'p',
      catalogue,
      ctx,
    )
    const [v, t] = recette.etapes
    expect(v).toMatchObject({ kind: 'volume', db: -60 })
    expect(t!.kind === 'texte' && t!.texte.length).toBe(80)
  })
})

describe('recettes Nexora locales (instantanées, 0 jeton) : canon et banc', () => {
  it('chaque recette locale est valide contre le vrai registre, sans avertissement', () => {
    for (const r of RECETTES_LOCALES) {
      const { avertissements } = validerRecette(r.recette, r.nom, catalogue, ctx)
      expect(avertissements, r.nom).toEqual([])
    }
  })

  it('reconnaît au moins 90 % des phrases du banc', () => {
    const reconnues = PHRASES_CANON.filter((p) => recetteLocale(p) !== null)
    expect(PHRASES_CANON.length).toBeGreaterThanOrEqual(30)
    expect(reconnues.length / PHRASES_CANON.length).toBeGreaterThanOrEqual(0.9)
  })

  it('« look film des années 80 » donne une pile de 4 effets', () => {
    const r = recetteLocale('Look film des années 80')!
    const { recette } = validerRecette(r.recette, 'look', catalogue, ctx)
    const pile = recette.etapes.find((e) => e.kind === 'gpu_stack')
    expect(pile?.kind === 'gpu_stack' && pile.effets.length).toBe(4)
  })

  it('ne reconnaît pas une phrase hors catalogue (elle ira au LLM)', () => {
    expect(recetteLocale('enlève le lampadaire à gauche')).toBeNull()
  })
})

describe('traduction en opérations FreeCut', () => {
  it('portée « plage » : une couche d’ajustement sur la piste d’effets, au point du clic', () => {
    const r = recetteLocale('vhs')!
    const { recette } = validerRecette(r.recette, 'vhs', catalogue, ctx)
    const ops = recetteVersOps(recette, { ...ctx, pisteEffets: 'piste-fx', pisteTextes: 'piste-tx' })
    expect(ops).toHaveLength(1)
    const item = ops[0]!.item as Record<string, any>
    expect(ops[0]!.op).toBe('addItem')
    expect(item).toMatchObject({ type: 'adjustment', trackId: 'piste-fx', from: 6060, durationInFrames: 60 })
    expect(item.effects[0].effect).toMatchObject({ type: 'gpu-effect', gpuEffectType: 'gpu-vhs' })
  })

  it('portée « clip » : effets posés sur le clip lui-même ; volume et texte suivent', () => {
    const { recette } = validerRecette(
      {
        portee: { kind: 'clip' },
        etapes: [
          { kind: 'gpu_stack', effets: [{ gpu: 'gpu-grayscale' }] },
          { kind: 'volume', db: -12 },
          { kind: 'texte', texte: 'Fin', position: 'haut' },
        ],
      },
      'p',
      catalogue,
      ctx,
    )
    expect(recette.portee).toMatchObject({ kind: 'clip', debut: 6000, duree: 300 })
    const ops = recetteVersOps(recette, { ...ctx, pisteEffets: 'fx', pisteTextes: 'tx' })
    expect(ops.map((o) => o.op)).toEqual(['addEffect', 'updateItem', 'addText'])
    expect(ops[0]).toMatchObject({ itemId: 'clip-1', gpuEffectType: 'gpu-grayscale' })
    expect(ops[2]).toMatchObject({ trackId: 'tx', from: 6000, verticalAlign: 'top' })
  })

  it('sans élément sonore, le volume est écarté avec un avertissement', () => {
    const { recette, avertissements } = validerRecette(
      { etapes: [{ kind: 'volume', db: -6 }, { kind: 'gpu_stack', effets: [{ gpu: 'gpu-sepia' }] }] },
      'p',
      catalogue,
      { ...ctx, element: undefined },
    )
    expect(recette.etapes.map((e) => e.kind)).toEqual(['gpu_stack'])
    expect(avertissements.join(' ')).toMatch(/volume/)
  })
})

describe('plus fort / plus doux (même recette, pas un nouveau départ)', () => {
  it('éloigne ou rapproche chaque paramètre de sa valeur neutre, dans les bornes', () => {
    const { recette } = validerRecette(
      { etapes: [{ kind: 'gpu_stack', effets: [{ gpu: 'gpu-vhs', params: { noise: 0.6 } }] }] },
      'p',
      catalogue,
      ctx,
    )
    const fort = ajusterIntensite(recette, 1.5, catalogue)
    const doux = ajusterIntensite(recette, 0.5, catalogue)
    const valeur = (r: typeof recette) =>
      r.etapes[0]!.kind === 'gpu_stack' ? (r.etapes[0]!.effets[0]!.params.noise as number) : NaN
    // défaut 0,25 : 0,25 + (0,6 - 0,25) × 1,5 = 0,775 ; × 0,5 = 0,425
    expect(valeur(fort)).toBeCloseTo(0.775)
    expect(valeur(doux)).toBeCloseTo(0.425)
    expect(valeur(ajusterIntensite(recette, 10, catalogue))).toBe(1)
    expect(valeur(recette)).toBe(0.6)
  })
})
