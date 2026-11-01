/**
 * Nexora Creative : traduction des commandes de l'assistant (en secondes, en français) vers les opérations d'édition de
 * FreeCut (en images, src/headless/edit-op-support.ts). Pure et sans store : testée seule.
 *
 * Conventions FreeCut reprises ici : trimStart positif raccourcit par le début, trimEnd négatif raccourcit par la fin ;
 * le volume est en dB (-60 à +12).
 */
import type { EditOp } from '@/headless/edit-op-support'
import type { Commande } from './api'

export interface ContexteTraduction {
  fps: number
  /** Hauteur du canevas, pour placer un texte en haut ou en bas. */
  hauteur: number
}

const nombre = (v: unknown): number | undefined =>
  typeof v === 'number' && Number.isFinite(v) ? v : undefined
const texte = (v: unknown): string | undefined =>
  typeof v === 'string' && v.trim() ? v.trim() : undefined

const STYLES_TRANSITION = new Set([
  'fade',
  'dissolve',
  'wipe',
  'slide',
  'iris',
  'glitch',
  'lightLeakBurn',
  'blurDissolve',
  'smoothCut',
])

/** Champs qu'une commande « modifier » peut changer : style de texte, volume et nom. */
const CHAMPS_MODIFIABLES = new Set([
  'text',
  'color',
  'fontSize',
  'fontFamily',
  'fontWeight',
  'fontStyle',
  'letterSpacing',
  'textAlign',
  'verticalAlign',
  'lineHeight',
  'backgroundColor',
  'stroke',
  'textShadow',
  'volume',
  'label',
])

export class CommandeInvalide extends Error {}

function exiger<T>(v: T | undefined, message: string): T {
  if (v === undefined) throw new CommandeInvalide(message)
  return v
}

/** Une commande Nexora devient une opération FreeCut (ou une erreur lisible si un champ manque). */
export function traduireCommande(c: Commande, ctx: ContexteTraduction): EditOp {
  const images = (s: number) => Math.max(0, Math.round(s * ctx.fps))
  const duree = (s: number) => Math.max(1, Math.round(s * ctx.fps))
  switch (c.commande) {
    case 'texte': {
      const position = c.position === 'haut' ? 'top' : c.position === 'milieu' ? 'middle' : 'bottom'
      return {
        op: 'addText',
        text: exiger(texte(c.texte), 'texte : il manque le texte'),
        from: images(nombre(c.debutS) ?? 0),
        durationInFrames: duree(nombre(c.dureeS) ?? 3),
        fontSize: nombre(c.taille) ?? Math.round(ctx.hauteur / 14),
        color: texte(c.couleur) ?? '#ffffff',
        ...(c.gras === true ? { fontWeight: 'bold' } : {}),
        textAlign: 'center',
        verticalAlign: position,
        label: (texte(c.texte) ?? 'Texte').slice(0, 40),
        ...(texte(c.piste) ? { trackId: texte(c.piste) } : {}),
      }
    }
    case 'deplacer':
      return {
        op: 'moveItem',
        id: exiger(texte(c.id), 'deplacer : il manque l’élément'),
        from: images(exiger(nombre(c.debutS), 'deplacer : il manque debutS')),
        ...(texte(c.piste) ? { trackId: texte(c.piste) } : {}),
      }
    case 'supprimer': {
      const ids = Array.isArray(c.ids)
        ? c.ids.filter((x): x is string => typeof x === 'string')
        : []
      if (!ids.length) throw new CommandeInvalide('supprimer : aucun élément')
      return { op: 'removeItems', ids }
    }
    case 'couper':
      return {
        op: 'split',
        id: exiger(texte(c.id), 'couper : il manque l’élément'),
        frame: images(exiger(nombre(c.aS), 'couper : il manque aS')),
      }
    case 'raccourcirDebut':
      return {
        op: 'trimStart',
        id: exiger(texte(c.id), 'raccourcirDebut : il manque l’élément'),
        amount: images(Math.abs(exiger(nombre(c.s), 'raccourcirDebut : il manque s'))),
      }
    case 'raccourcirFin':
      return {
        op: 'trimEnd',
        id: exiger(texte(c.id), 'raccourcirFin : il manque l’élément'),
        amount: -images(Math.abs(exiger(nombre(c.s), 'raccourcirFin : il manque s'))),
      }
    case 'volume':
      return {
        op: 'updateItem',
        id: exiger(texte(c.id), 'volume : il manque l’élément'),
        updates: {
          volume: Math.max(-60, Math.min(12, exiger(nombre(c.db), 'volume : il manque db'))),
        },
      }
    case 'transition': {
      const style = texte(c.style)
      return {
        op: 'addTransition',
        leftClipId: exiger(texte(c.gaucheId), 'transition : il manque le clip de gauche'),
        rightClipId: exiger(texte(c.droiteId), 'transition : il manque le clip de droite'),
        type: 'crossfade',
        durationInFrames: duree(nombre(c.dureeS) ?? 0.5),
        ...(style && STYLES_TRANSITION.has(style) ? { presentation: style } : {}),
      }
    }
    case 'ajouterClip':
      return {
        op: 'addClip',
        mediaId: exiger(texte(c.mediaId), 'ajouterClip : il manque le média'),
        from: images(nombre(c.debutS) ?? 0),
        ...(nombre(c.dureeS) !== undefined ? { durationInFrames: duree(nombre(c.dureeS)!) } : {}),
        ...(texte(c.piste) ? { trackId: texte(c.piste) } : {}),
      }
    case 'modifier': {
      const champs = (c.champs ?? {}) as Record<string, unknown>
      const updates = Object.fromEntries(
        Object.entries(champs).filter(([k]) => CHAMPS_MODIFIABLES.has(k)),
      )
      if (!Object.keys(updates).length)
        throw new CommandeInvalide('modifier : aucun champ modifiable')
      return {
        op: 'updateItem',
        id: exiger(texte(c.id), 'modifier : il manque l’élément'),
        updates,
      }
    }
    default:
      throw new CommandeInvalide(
        `commande inconnue : ${String((c as { commande?: unknown }).commande)}`,
      )
  }
}

// ---------------------------------------------------------------------------------------------------------------------
// Calculs des actions d'IA (purs) : temps de la source → temps de la timeline.

/** Ce qu'il faut d'un clip pour convertir un temps de sa source en temps de timeline. */
export interface ClipSource {
  from: number
  durationInFrames: number
  sourceStart?: number
  sourceFps?: number
  speed?: number
}

/** Temps de la source (s) → image de timeline, ou null s'il tombe hors de la partie visible du clip. */
export function sourceVersTimeline(clip: ClipSource, sourceS: number, fps: number): number | null {
  const sourceFps = clip.sourceFps && clip.sourceFps > 0 ? clip.sourceFps : fps
  const debutSourceS = (clip.sourceStart ?? 0) / sourceFps
  const vitesse = clip.speed && clip.speed > 0 ? clip.speed : 1
  const image = clip.from + ((sourceS - debutSourceS) / vitesse) * fps
  if (image < clip.from - 0.5 || image > clip.from + clip.durationInFrames + 0.5) return null
  return Math.round(image)
}

/**
 * Plages de silence (en secondes de la source) → plages d'images à retirer du clip, triées de la fin vers le début
 * (on coupe en partant de la fin pour que les identifiants de gauche restent valides).
 */
export function plagesARetirer(
  clip: ClipSource,
  silences: { debutS: number; finS: number }[],
  fps: number,
): { debut: number; fin: number }[] {
  const fin = clip.from + clip.durationInFrames
  return silences
    .map((s) => {
      const a = sourceVersTimeline(clip, s.debutS, fps) ?? (s.debutS <= 0 ? clip.from : null)
      const b = sourceVersTimeline(clip, s.finS, fps) ?? (s.finS > s.debutS ? fin : null)
      if (a === null || b === null) return null
      return { debut: Math.max(clip.from, a), fin: Math.min(fin, b) }
    })
    .filter(
      (p): p is { debut: number; fin: number } => !!p && p.fin - p.debut >= Math.round(fps * 0.2),
    )
    .sort((x, y) => y.debut - x.debut)
}

/**
 * Montage au rythme : chaque clip est raccourci pour finir sur le dernier temps de la musique qu'il atteint (sans
 * descendre sous minS), puis les clips sont recollés bout à bout. Ne fait que raccourcir : aucun clip ne déborde.
 */
export function calageSurTemps(
  clips: { id: string; from: number; durationInFrames: number }[],
  temps: number[],
  fps: number,
  minS = 0.5,
): { id: string; from: number; durationInFrames: number }[] {
  const tempsImages = temps.map((t) => Math.round(t * fps)).sort((a, b) => a - b)
  const ordonnes = [...clips].sort((a, b) => a.from - b.from)
  const sortie: { id: string; from: number; durationInFrames: number }[] = []
  // Au-delà du dernier temps (plus une période), la musique est finie : les plans gardent leur durée.
  const periode =
    tempsImages.length > 1
      ? (tempsImages[tempsImages.length - 1]! - tempsImages[0]!) / (tempsImages.length - 1)
      : 0
  const finMusique = (tempsImages[tempsImages.length - 1] ?? -Infinity) + periode
  let curseur = ordonnes[0]?.from ?? 0
  for (const c of ordonnes) {
    const minimum = curseur + Math.round(minS * fps)
    const finVoulue = curseur + c.durationInFrames
    const candidats =
      finVoulue <= finMusique ? tempsImages.filter((t) => t >= minimum && t <= finVoulue) : []
    const finChoisie = candidats.length ? candidats[candidats.length - 1]! : finVoulue
    sortie.push({ id: c.id, from: curseur, durationInFrames: finChoisie - curseur })
    curseur = finChoisie
  }
  return sortie
}
