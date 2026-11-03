/**
 * Nexora Creative : la bulle d'effet branchée sur les vrais stores de l'éditeur (état d'ouverture, contexte du clic,
 * application en un seul pas d'annulation, avant/après par l'historique).
 */
import { create } from 'zustand'
import { applyOp } from '@/headless/edit-ops'
import { useItemsStore } from '@/features/timeline/stores/items-store'
import { useTimelineSettingsStore } from '@/features/timeline/stores/timeline-settings-store'
import { useTimelineCommandStore } from '@/features/timeline/stores/timeline-command-store'
import { usePlaybackStore } from '@/shared/state/playback'
import { useProjectStore } from '@/features/editor/deps/projects'
import { enUnePas, pisteDeTexte } from '../timeline'
import { catalogueCompact, catalogueEffets, type EffetCatalogue } from './catalogue'
import { recetteVersOps, type ContexteRecette, type EffectRecipe } from './recette'

export interface OuvertureBulle {
  x: number
  y: number
  /** Image du clic ; repli : tête de lecture. */
  frame?: number
  itemId?: string
}

interface EtatBulle {
  ouverte: OuvertureBulle | null
  ouvrir: (o: OuvertureBulle) => void
  fermer: () => void
}

export const useBulleEffetStore = create<EtatBulle>((set) => ({
  ouverte: null,
  ouvrir: (o) => set({ ouverte: o }),
  fermer: () => set({ ouverte: null }),
}))

let cache: { catalogue: EffetCatalogue[]; compact: string } | null = null
export function catalogue() {
  if (!cache) {
    const c = catalogueEffets()
    cache = { catalogue: c, compact: catalogueCompact(c) }
  }
  return cache
}

export const fpsCourant = () => useTimelineSettingsStore.getState().fps || 30

/** Contexte de la recette : image du clic, élément visé, durées permises. */
export function contexteDuClic(o: OuvertureBulle): ContexteRecette {
  const fps = fpsCourant()
  const item = o.itemId ? useItemsStore.getState().itemById[o.itemId] : undefined
  const tete = usePlaybackStore.getState().currentFrame
  let debut = Math.max(0, Math.round(o.frame ?? tete))
  // Sur un clip : au point du clic s'il est dans le clip, sinon au début du clip.
  if (item && (debut < item.from || debut >= item.from + item.durationInFrames)) debut = item.from
  return {
    fps,
    debut,
    dureeParDefaut: Math.round(2 * fps),
    dureeMax: Math.round(60 * fps),
    hauteur: useProjectStore.getState().currentProject?.metadata?.height ?? 1080,
    ...(item
      ? { element: { id: item.id, type: item.type, from: item.from, durationInFrames: item.durationInFrames } }
      : {}),
  }
}

/** Piste « Effets IA » en haut de la pile, libre sur [debut, debut + duree[ (créée si besoin). */
function pisteEffets(debut: number, duree: number): string {
  const { tracks, items } = useItemsStore.getState()
  const libre = [...tracks]
    .filter((t) => !t.isGroup && !t.locked && (t.kind ?? 'video') === 'video' && t.name === 'Effets IA')
    .sort((a, b) => a.order - b.order)
    .find(
      (t) =>
        !items.some(
          (i) => i.trackId === t.id && i.from < debut + duree && i.from + i.durationInFrames > debut,
        ),
    )
  if (libre) return libre.id
  const { trackId } = applyOp({ op: 'addTrack', kind: 'video' }) as { trackId: string }
  useItemsStore
    .getState()
    .setTracks(
      useItemsStore.getState().tracks.map((t) => (t.id === trackId ? { ...t, name: 'Effets IA' } : t)),
    )
  return trackId
}

/** Applique la recette en un seul pas d'annulation ; renvoie le nombre d'opérations faites et les erreurs. */
export function appliquerRecette(recette: EffectRecipe, ctx: ContexteRecette) {
  const erreurs: string[] = []
  let faites = 0
  enUnePas(`Effet IA : ${recette.resume}`, () => {
    const { debut, duree } = recette.portee
    const aBesoinDeCouche = recette.portee.kind === 'plage' && recette.etapes.some((e) => e.kind === 'gpu_stack')
    const aBesoinDeTexte = recette.etapes.some((e) => e.kind === 'texte')
    const ops = recetteVersOps(recette, {
      ...ctx,
      pisteEffets: aBesoinDeCouche ? pisteEffets(debut, duree) : '',
      pisteTextes: aBesoinDeTexte ? pisteDeTexte(debut, duree, 'Titres') : '',
    })
    for (const op of ops) {
      try {
        applyOp(op)
        faites++
      } catch (e) {
        erreurs.push(e instanceof Error ? e.message : String(e))
      }
    }
  })
  return { faites, erreurs }
}

/** Défait la dernière application (pour Annuler, ou avant de réappliquer « plus fort / plus doux »). */
export const defaire = () => useTimelineCommandStore.getState().undo()
export const refaire = () => useTimelineCommandStore.getState().redo()

export { catalogueCompact }
