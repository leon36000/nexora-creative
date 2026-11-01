/**
 * Nexora Creative : le Mode Studio vu par l'assistant. Résumé de la timeline pour le LLM, application des commandes en un
 * seul pas d'annulation, actions d'IA (silences, sous-titres, rythme, génération) sur les vrais stores de l'éditeur.
 */
import type { MediaMetadata } from '@/types/storage'
import type { TimelineItem } from '@/types/timeline'
import { applyOp } from '@/headless/edit-ops'
import { useItemsStore } from '@/features/timeline/stores/items-store'
import { useTimelineSettingsStore } from '@/features/timeline/stores/timeline-settings-store'
import { useTimelineCommandStore } from '@/features/timeline/stores/timeline-command-store'
import { captureSnapshot } from '@/features/timeline/stores/commands/snapshot'
import {
  moveItems,
  rippleDeleteItems,
  splitItem,
  trimItemEnd,
  trimItemStart,
  updateItem,
} from '@/features/timeline/stores/timeline-actions'
import { useMediaLibraryStore } from '@/features/media-library/stores/media-library-store'
import { usePlaybackStore } from '@/shared/state/playback'
import { useSelectionStore } from '@/shared/state/selection'
import { useProjectStore } from '@/features/editor/deps/projects'
import { attendrePrise, nexora, type Action, type Commande, type Creation } from './api'
import { calageSurTemps, plagesARetirer, traduireCommande } from './commandes'

const fps = () => useTimelineSettingsStore.getState().fps || 30
const arrondi = (s: number) => Math.round(s * 100) / 100

// ---------------------------------------------------------------------------------------------------------------------
// Médias Nexora : quel média de la bibliothèque vient de quelle création (pour les analyses côté serveur).

const CLE_LIENS = 'nexora-mode-studio:medias'

function liens(): Record<string, number> {
  try {
    return JSON.parse(localStorage.getItem(CLE_LIENS) ?? '{}') as Record<string, number>
  } catch {
    return {}
  }
}

function lier(mediaId: string, takeId: number): void {
  try {
    localStorage.setItem(CLE_LIENS, JSON.stringify({ ...liens(), [mediaId]: takeId }))
  } catch {
    // Stockage indisponible : les analyses de ce média ne seront simplement pas proposées.
  }
}

export const priseDuMedia = (mediaId: string | undefined): number | undefined =>
  mediaId ? liens()[mediaId] : undefined

/** Importe une création Nexora dans la bibliothèque du projet (ou retrouve celle déjà importée). */
export async function importerCreation(c: Creation): Promise<MediaMetadata> {
  const deja = Object.entries(liens()).find(([, take]) => take === c.id)?.[0]
  const existant = deja ? useMediaLibraryStore.getState().mediaById[deja] : undefined
  if (existant) return existant
  // L'import de FreeCut exige une adresse absolue : celle de la création, sur le même serveur.
  const importes = await useMediaLibraryStore
    .getState()
    .importMediaFromUrl(new URL(c.url, location.origin).href)
  const media = importes[0]
  if (!media) throw new Error(`« ${c.nom.slice(0, 40)} » n’a pas pu être importé.`)
  lier(media.id, c.id)
  return media
}

/**
 * Pose un média sur sa piste principale (la première piste vidéo ou audio libre de verrou) : à la tête de lecture si la
 * place est libre, sinon à la suite du dernier élément de cette piste — cliquer plusieurs créations les monte bout à bout.
 */
export function poserALaTete(media: MediaMetadata): string[] {
  const genre = media.mimeType.startsWith('audio/') ? 'audio' : 'video'
  const dureeImages = Math.max(1, Math.round((media.duration || 5) * fps()))
  const { tracks, items } = useItemsStore.getState()
  const tete = usePlaybackStore.getState().currentFrame
  const libreA = (trackId: string, debut: number) =>
    !items.some(
      (i) =>
        i.trackId === trackId &&
        i.from < debut + dureeImages &&
        i.from + i.durationInFrames > debut,
    )
  const candidates = [...tracks]
    .sort((a, b) => a.order - b.order)
    .filter((t) => !t.isGroup && !t.locked && (t.kind ?? 'video') === genre)
  let piste = candidates[0]
  let debut = tete
  if (genre === 'audio') {
    // Une musique ou un son va sur une piste audio libre à la tête de lecture (pas sur les sons liés des plans).
    piste = candidates.find((t) => libreA(t.id, tete))
  } else if (piste && !libreA(piste.id, tete)) {
    debut = Math.max(
      ...items.filter((i) => i.trackId === piste!.id).map((i) => i.from + i.durationInFrames),
    )
  }
  return enUnePas(`Ajouter ${media.fileName}`, () => {
    const trackId =
      piste?.id ?? (applyOp({ op: 'addTrack', kind: genre }) as { trackId: string }).trackId
    const r = applyOp({ op: 'addClip', mediaId: media.id, from: debut, trackId }) as {
      created: { id: string }[]
    }
    return r.created.map((c) => c.id)
  })
}

// ---------------------------------------------------------------------------------------------------------------------
// État envoyé à l'assistant

export function etatPourAssistant() {
  const f = fps()
  const { tracks, items } = useItemsStore.getState()
  const medias = useMediaLibraryStore.getState().mediaItems
  const projet = useProjectStore.getState().currentProject
  return {
    fps: f,
    canevas: {
      largeur: projet?.metadata?.width ?? 1920,
      hauteur: projet?.metadata?.height ?? 1080,
    },
    teteS: arrondi(usePlaybackStore.getState().currentFrame / f),
    selection: useSelectionStore.getState().selectedItemIds,
    pistes: [...tracks]
      .filter((t) => !t.isGroup)
      .sort((a, b) => a.order - b.order)
      .map((t) => ({
        id: t.id,
        nom: t.name,
        genre: t.kind ?? 'video',
        muette: t.muted || undefined,
      })),
    elements: [...items]
      .sort((a, b) => a.from - b.from)
      .slice(0, 400)
      .map((i) => ({
        id: i.id,
        type: i.type,
        piste: i.trackId,
        debutS: arrondi(i.from / f),
        dureeS: arrondi(i.durationInFrames / f),
        nom: i.label,
        ...(i.type === 'text' ? { texte: (i as { text?: string }).text } : {}),
        ...(i.mediaId ? { mediaId: i.mediaId } : {}),
        ...('volume' in i && typeof i.volume === 'number' && i.volume !== 0
          ? { db: i.volume }
          : {}),
        ...(i.linkedGroupId ? { lie: i.linkedGroupId.slice(0, 8) } : {}),
      })),
    medias: medias.slice(0, 100).map((m) => ({
      mediaId: m.id,
      nom: m.fileName,
      type: m.mimeType.split('/')[0],
      dureeS: m.duration ? arrondi(m.duration) : undefined,
      nexora: priseDuMedia(m.id) !== undefined || undefined,
    })),
  }
}

// ---------------------------------------------------------------------------------------------------------------------
// Une demande = un seul pas d'annulation

/**
 * Exécute `action` puis remplace les entrées d'annulation qu'elle a créées par une seule, nommée : un Ctrl+Z défait
 * toute la demande faite à l'assistant.
 */
export function enUnePas<T>(nom: string, action: () => T): T {
  const avant = captureSnapshot()
  const longueur = useTimelineCommandStore.getState().undoStack.length
  try {
    return action()
  } finally {
    const pile = useTimelineCommandStore.getState().undoStack
    if (pile.length > longueur) {
      useTimelineCommandStore.setState({
        undoStack: [
          ...pile.slice(0, longueur),
          {
            command: { type: 'NEXORA_ASSISTANT', payload: { nom } },
            beforeSnapshot: avant,
            timestamp: Date.now(),
          },
        ],
        redoStack: [],
        canUndo: true,
        canRedo: false,
      })
    }
  }
}

export interface Bilan {
  faites: number
  erreurs: string[]
}

export function appliquerCommandes(commandes: Commande[], nom: string): Bilan {
  const projet = useProjectStore.getState().currentProject
  const ctx = { fps: fps(), hauteur: projet?.metadata?.height ?? 1080 }
  const bilan: Bilan = { faites: 0, erreurs: [] }
  enUnePas(nom, () => {
    for (const c of commandes) {
      try {
        const op = traduireCommande(c, ctx)
        // Un texte sans piste va sur une piste de titres au-dessus des plans (sinon FreeCut le repousse après eux).
        if (op.op === 'addText' && !op.trackId) {
          op.trackId = pisteDeTexte(op.from as number, op.durationInFrames as number, 'Titres')
        }
        if (op.op === 'addTransition') {
          preparerPoignees(
            op.leftClipId as string,
            op.rightClipId as string,
            op.durationInFrames as number,
          )
        }
        applyOp(op)
        bilan.faites++
      } catch (e) {
        bilan.erreurs.push(e instanceof Error ? e.message : String(e))
      }
    }
  })
  return bilan
}

// ---------------------------------------------------------------------------------------------------------------------
// Pistes et déplacements qui respectent les éléments liés

/** Une piste vidéo qui ne porte que des textes et qui est libre sur [debut, debut + duree[, ou une nouvelle en haut. */
export function pisteDeTexte(debut: number, duree: number, nom: string): string {
  const { tracks, items } = useItemsStore.getState()
  const libre = [...tracks]
    .filter((t) => !t.isGroup && !t.locked && (t.kind ?? 'video') === 'video')
    .sort((a, b) => a.order - b.order)
    .find((t) => {
      const surPiste = items.filter((i) => i.trackId === t.id)
      return (
        surPiste.length > 0 &&
        surPiste.every((i) => i.type === 'text') &&
        !surPiste.some((i) => i.from < debut + duree && i.from + i.durationInFrames > debut)
      )
    })
  if (libre) return libre.id
  const { trackId } = applyOp({ op: 'addTrack', kind: 'video' }) as { trackId: string }
  useItemsStore
    .getState()
    .setTracks(
      useItemsStore.getState().tracks.map((t) => (t.id === trackId ? { ...t, name: nom } : t)),
    )
  return trackId
}

/** L'élément et ses compagnons liés (vidéo et son d'un même plan). */
function avecLies(id: string): TimelineItem[] {
  const { items, itemById } = useItemsStore.getState()
  const item = itemById[id]
  if (!item) return []
  return item.linkedGroupId ? items.filter((i) => i.linkedGroupId === item.linkedGroupId) : [item]
}

/**
 * Décale de `delta` images tout ce qui commence à partir de `depuis` sur les pistes de l'élément et de ses liés : le
 * montage reste synchronisé (images et sons) quand on referme un trou.
 */
function decalerLaSuite(id: string, depuis: number, delta: number): void {
  if (!delta) return
  const pistes = new Set(avecLies(id).map((i) => i.trackId))
  const aDeplacer = useItemsStore
    .getState()
    .items.filter((i) => pistes.has(i.trackId) && i.from >= depuis)
    .map((i) => ({ id: i.id, from: Math.max(0, i.from + delta) }))
  if (aDeplacer.length) moveItems(aDeplacer)
}

/**
 * Un fondu a besoin de matière avant et après la coupe. Des plans posés en entier n'en ont pas : on prend la moitié de
 * la durée du fondu à la fin du plan de gauche et au début du plan de droite, puis on recolle la suite (comme le fait
 * un logiciel de montage quand la matière manque). La séquence raccourcit de la durée du fondu.
 */
function preparerPoignees(gaucheId: string, droiteId: string, duree: number): void {
  const { itemById } = useItemsStore.getState()
  const gauche = itemById[gaucheId]
  const droite = itemById[droiteId]
  if (!gauche || !droite) return
  const reserveApres =
    (gauche.sourceDuration ?? 0) - (gauche.sourceEnd ?? gauche.sourceDuration ?? 0)
  const reserveAvant = droite.sourceStart ?? 0
  const moitie = Math.ceil(duree / 2)
  if (reserveApres >= moitie && reserveAvant >= moitie) return
  trimItemEnd(gaucheId, -moitie)
  trimItemStart(droiteId, moitie)
  const finGauche = gauche.from + gauche.durationInFrames - moitie
  const debutDroite = useItemsStore.getState().itemById[droiteId]?.from ?? droite.from + moitie
  decalerLaSuite(droiteId, debutDroite, finGauche - debutDroite)
}

// ---------------------------------------------------------------------------------------------------------------------
// Actions d'IA

type Rapport = (texte: string) => void

const estMedia = (i: TimelineItem): i is TimelineItem & { mediaId: string } =>
  (i.type === 'video' || i.type === 'audio') && !!i.mediaId

/** Clips visés : les ids demandés, sinon la sélection, sinon tous les clips audio/vidéo ; un seul par groupe lié. */
function clipsVises(ids: unknown): (TimelineItem & { mediaId: string })[] {
  const { items, itemById } = useItemsStore.getState()
  const demandes = Array.isArray(ids) ? ids.filter((x): x is string => typeof x === 'string') : []
  const selection = useSelectionStore.getState().selectedItemIds
  const base = demandes.length
    ? demandes.map((id) => itemById[id]).filter((i): i is TimelineItem => !!i)
    : selection.length
      ? selection.map((id) => itemById[id]).filter((i): i is TimelineItem => !!i)
      : items
  const vus = new Set<string>()
  return base.filter(estMedia).filter((i) => {
    const cle = i.linkedGroupId ?? i.id
    if (vus.has(cle)) return false
    vus.add(cle)
    return true
  })
}

async function couperSilences(a: Action, rapport: Rapport): Promise<string> {
  const clips = clipsVises(a.ids).filter((c) => priseDuMedia(c.mediaId) !== undefined)
  if (!clips.length)
    return 'Aucun clip Nexora à analyser : importe tes créations depuis l’onglet Créations.'
  const analyses: { clip: (typeof clips)[number]; silences: { debutS: number; finS: number }[] }[] =
    []
  for (const c of clips) {
    rapport(`J’écoute « ${c.label} »…`)
    analyses.push({ clip: c, silences: (await nexora.silences(priseDuMedia(c.mediaId)!)).silences })
  }
  let retires = 0
  enUnePas('Couper les silences', () => {
    const aRetirer: string[] = []
    for (const { clip, silences } of analyses) {
      let courant = clip.id
      for (const p of plagesARetirer(clip, silences, fps())) {
        const droite = splitItem(courant, p.fin)
        const gauche = splitItem(droite ? droite.leftItem.id : courant, p.debut)
        if (!gauche) continue
        aRetirer.push(gauche.rightItem.id)
        courant = gauche.leftItem.id
        retires++
      }
    }
    if (aRetirer.length) rippleDeleteItems(aRetirer)
  })
  return retires
    ? `${retires} silence${retires > 1 ? 's' : ''} retiré${retires > 1 ? 's' : ''}.`
    : 'Aucun silence à retirer.'
}

async function poserSousTitres(a: Action, rapport: Rapport): Promise<string> {
  const clips = clipsVises(a.ids).filter((c) => priseDuMedia(c.mediaId) !== undefined)
  if (!clips.length)
    return 'Aucun clip Nexora à transcrire : importe tes créations depuis l’onglet Créations.'
  const f = fps()
  const hauteur = useProjectStore.getState().currentProject?.metadata?.height ?? 1080
  const lignes: { texte: string; from: number; duree: number }[] = []
  for (const c of clips) {
    rapport(`Je transcris « ${c.label} »… (quelques secondes par minute de son)`)
    const { sousTitres } = await nexora.transcription(priseDuMedia(c.mediaId)!)
    const sourceFps = c.sourceFps && c.sourceFps > 0 ? c.sourceFps : f
    const debutSourceS = (c.sourceStart ?? 0) / sourceFps
    const vitesse = c.speed && c.speed > 0 ? c.speed : 1
    for (const l of sousTitres) {
      const from = Math.round(c.from + ((l.debutS - debutSourceS) / vitesse) * f)
      const fin = Math.round(c.from + ((l.finS - debutSourceS) / vitesse) * f)
      const borneFin = Math.min(fin, c.from + c.durationInFrames)
      const borneDebut = Math.max(from, c.from)
      if (borneFin - borneDebut >= Math.round(f * 0.3))
        lignes.push({ texte: l.texte, from: borneDebut, duree: borneFin - borneDebut })
    }
  }
  if (!lignes.length) return 'Je n’ai entendu aucune parole à sous-titrer.'
  enUnePas('Sous-titres automatiques', () => {
    const { trackId } = applyOp({ op: 'addTrack', kind: 'video' }) as { trackId: string }
    useItemsStore
      .getState()
      .setTracks(
        useItemsStore
          .getState()
          .tracks.map((t) => (t.id === trackId ? { ...t, name: 'Sous-titres' } : t)),
      )
    for (const l of lignes) {
      const { id } = applyOp({
        op: 'addText',
        trackId,
        text: l.texte,
        label: l.texte.slice(0, 40),
        from: l.from,
        durationInFrames: l.duree,
        fontSize: Math.round(hauteur / 18),
        fontWeight: 'bold',
        color: '#ffffff',
        textAlign: 'center',
        verticalAlign: 'bottom',
      }) as { id: string }
      updateItem(id, { stroke: { width: 4, color: '#000000' } } as Partial<TimelineItem>)
    }
  })
  return `${lignes.length} sous-titre${lignes.length > 1 ? 's' : ''} posé${lignes.length > 1 ? 's' : ''} sur la piste « Sous-titres ».`
}

async function monterAuRythme(a: Action, rapport: Rapport): Promise<string> {
  const { items, itemById } = useItemsStore.getState()
  const musique =
    (typeof a.musiqueId === 'string' ? itemById[a.musiqueId] : undefined) ??
    items.find(
      (i) => i.type === 'audio' && !i.linkedGroupId && priseDuMedia(i.mediaId) !== undefined,
    )
  if (!musique || !estMedia(musique) || priseDuMedia(musique.mediaId) === undefined) {
    return 'Il me faut une musique Nexora seule sur une piste audio (onglet Créations, ou « génère une musique »).'
  }
  rapport('Je repère les temps de la musique…')
  const { bpm, temps } = await nexora.rythme(priseDuMedia(musique.mediaId)!)
  if (!temps.length) return 'Je n’ai pas trouvé de rythme net dans cette musique.'
  const f = fps()
  const tempsTimeline = temps
    .map(
      (t) =>
        (musique.from +
          ((t - (musique.sourceStart ?? 0) / (musique.sourceFps || f)) / (musique.speed || 1)) *
            f) /
        f,
    )
    .filter((t) => t >= 0)
  // La piste vidéo la plus chargée porte le montage principal.
  const parPiste = new Map<string, TimelineItem[]>()
  for (const i of items)
    if (i.type === 'video' || i.type === 'image')
      parPiste.set(i.trackId, [...(parPiste.get(i.trackId) ?? []), i])
  const principaux = [...parPiste.values()].sort((x, y) => y.length - x.length)[0] ?? []
  if (principaux.length < 2)
    return 'Il faut au moins deux plans sur la piste vidéo pour monter au rythme.'
  const calage = calageSurTemps(principaux, tempsTimeline, f)
  enUnePas('Monter au rythme de la musique', () => {
    for (const c of calage) {
      const avant = useItemsStore.getState().itemById[c.id]
      if (!avant) continue
      // Le raccourci et le déplacement emmènent le son lié du plan.
      if (c.durationInFrames < avant.durationInFrames)
        trimItemEnd(c.id, c.durationInFrames - avant.durationInFrames)
      const delta = c.from - avant.from
      if (delta)
        moveItems(avecLies(c.id).map((i) => ({ id: i.id, from: Math.max(0, i.from + delta) })))
    }
  })
  return `${calage.length} plans recalés sur les temps de la musique (${Math.round(bpm)} BPM).`
}

async function generer(a: Action, rapport: Rapport): Promise<string> {
  const intention = String(a.intention ?? a.envie ?? '').trim()
  if (!intention) return 'Dis-moi ce que tu veux que je crée.'
  const format = a.format === '9:16' || a.format === '1:1' ? a.format : '16:9'
  let takeId: number
  let quoi: string
  if (a.type === 'generer_video') {
    takeId = (await nexora.creerVideo(intention, a.duree === 10 ? 10 : 5, format)).takeId
    quoi = 'Plan vidéo (MiniMax H3)'
  } else if (a.type === 'generer_image') {
    const r = await nexora.creerImage(intention, format)
    takeId = r.takeId ?? r.takeIds[0]!
    quoi = 'Image (Qwen-Image)'
  } else {
    takeId = (await nexora.creerMusique(intention, Number(a.dureeS) || 30)).takeId
    quoi = 'Musique (MiniMax-Music3)'
  }
  const creation = await attendrePrise(takeId, (s) => rapport(`${quoi} : rendu en cours… ${s} s`))
  const media = await importerCreation(creation)
  poserALaTete(media)
  return `${quoi} : prêt et posé à la tête de lecture.`
}

export async function executerAction(a: Action, rapport: Rapport): Promise<string> {
  switch (a.type) {
    case 'silences':
      return couperSilences(a, rapport)
    case 'sous_titres':
      return poserSousTitres(a, rapport)
    case 'rythme':
      return monterAuRythme(a, rapport)
    case 'generer_video':
    case 'generer_image':
    case 'generer_musique':
      return generer(a, rapport)
  }
}

// Développement seulement : accès de recette aux fonctions de l'assistant sur les stores de l'application.
if (import.meta.env.DEV) {
  Object.assign(window, {
    __nexoraStudio: {
      appliquerCommandes,
      executerAction,
      etatPourAssistant,
      importerCreation,
      poserALaTete,
    },
  })
}
