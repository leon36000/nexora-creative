/**
 * Nexora Creative : la bulle « Effet IA ici… » (clic droit sur un clip ou un vide de piste). Une phrase → une recette
 * (maison et instantanée si le code la reconnaît, sinon compilée par le LLM) → appliquée en direct, un seul Ctrl+Z.
 * Ensuite : Plus fort / Plus doux (la même recette), Avant/Après (par l'historique), Annuler, Garder.
 */
import { useCallback, useEffect, useLayoutEffect, useRef, useState } from 'react'
import { Loader2, Minus, Plus, Sparkles, Undo2, X } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { cn } from '@/shared/ui/cn'
import { nexora } from '../api'
import {
  appliquerRecette,
  catalogue,
  contexteDuClic,
  defaire,
  fpsCourant,
  refaire,
  useBulleEffetStore,
  type OuvertureBulle,
} from './appliquer'
import { ajusterIntensite, resumeRecette, validerRecette, type ContexteRecette, type EffectRecipe } from './recette'
import { PUCES, recetteLocale } from './recettes-locales'

const timecode = (frame: number, fps: number) => {
  const s = frame / fps
  const m = Math.floor(s / 60)
  return `${m}:${String(Math.floor(s % 60)).padStart(2, '0')}`
}

type Portee = 'deux' | 'cinq' | 'clip'

interface Appliquee {
  recette: EffectRecipe
  ctx: ContexteRecette
  source: 'locale' | 'ia'
  avertissements: string[]
  avant: boolean
}

function Bulle({ ouverture, fermer }: { ouverture: OuvertureBulle; fermer: () => void }) {
  const [phrase, setPhrase] = useState('')
  const [portee, setPortee] = useState<Portee>(ouverture.itemId ? 'clip' : 'deux')
  const [enCours, setEnCours] = useState(false)
  const [erreur, setErreur] = useState<string | null>(null)
  const [appliquee, setAppliquee] = useState<Appliquee | null>(null)
  const boite = useRef<HTMLDivElement>(null)
  const champ = useRef<HTMLInputElement>(null)
  const [pos, setPos] = useState({ left: ouverture.x, top: ouverture.y })
  const ctxBase = contexteDuClic(ouverture)
  const fps = ctxBase.fps

  useLayoutEffect(() => {
    const r = boite.current?.getBoundingClientRect()
    if (!r) return
    setPos({
      left: Math.max(8, Math.min(ouverture.x, window.innerWidth - r.width - 8)),
      top: Math.max(8, Math.min(ouverture.y - r.height - 12, window.innerHeight - r.height - 8)),
    })
  }, [ouverture.x, ouverture.y, appliquee, erreur])

  useEffect(() => champ.current?.focus(), [])

  const porteeBrute = useCallback(
    (p: Portee) =>
      p === 'clip' ? { kind: 'clip' } : { kind: 'plage', dureeS: p === 'cinq' ? 5 : 2, debutS: ctxBase.debut / fps },
    [ctxBase.debut, fps],
  )

  const lancer = useCallback(
    async (texte: string) => {
      const p = texte.trim()
      if (!p || enCours) return
      setErreur(null)
      // Une nouvelle phrase remplace l'effet précédent de la même bulle (un seul pas d'annulation au total).
      if (appliquee && !appliquee.avant) defaire()
      setAppliquee(null)
      const ctx = contexteDuClic(ouverture)
      try {
        const locale = recetteLocale(p)
        let brute: unknown
        let source: 'locale' | 'ia' = 'locale'
        if (locale) brute = { ...locale.recette, portee: porteeBrute(portee) }
        else {
          setEnCours(true)
          source = 'ia'
          const item = ctx.element
          const r = await nexora.effet(p, catalogue().compact, {
            tS: ctx.debut / fps,
            fps,
            ...(item ? { element: { type: item.type, dureeS: item.durationInFrames / fps } } : {}),
          })
          // La portée choisie dans la bulle prime sur celle du modèle.
          brute = { ...r, portee: porteeBrute(portee) }
          if (!r.etapes.length) throw new Error(r.resume || 'Je ne sais pas encore faire cet effet.')
        }
        const { recette, avertissements } = validerRecette(brute, p, catalogue().catalogue, ctx)
        const bilan = appliquerRecette(recette, ctx)
        if (!bilan.faites) throw new Error(bilan.erreurs[0] ?? 'Rien n’a pu être appliqué.')
        setAppliquee({ recette, ctx, source, avertissements: [...avertissements, ...bilan.erreurs], avant: false })
      } catch (e) {
        setErreur(e instanceof Error ? e.message : String(e))
      } finally {
        setEnCours(false)
      }
    },
    [appliquee, enCours, fps, ouverture, portee, porteeBrute],
  )

  const intensite = (facteur: number) => {
    if (!appliquee) return
    if (!appliquee.avant) defaire()
    const recette = ajusterIntensite(appliquee.recette, facteur, catalogue().catalogue)
    appliquerRecette(recette, appliquee.ctx)
    setAppliquee({ ...appliquee, recette, avant: false })
  }

  const basculer = () => {
    if (!appliquee) return
    if (appliquee.avant) refaire()
    else defaire()
    setAppliquee({ ...appliquee, avant: !appliquee.avant })
  }

  const annuler = () => {
    if (appliquee && !appliquee.avant) defaire()
    fermer()
  }

  return (
    <div
      ref={boite}
      role="dialog"
      aria-label="Effet IA ici"
      data-testid="bulle-effet"
      className="fixed z-[200] w-[340px] rounded-lg border border-border bg-popover p-3 text-popover-foreground shadow-xl"
      style={{ left: pos.left, top: pos.top }}
      onKeyDown={(e) => {
        if (e.key === 'Escape') {
          e.stopPropagation()
          fermer()
        }
      }}
    >
      <div className="mb-2 flex items-center gap-2 text-sm font-medium">
        <Sparkles className="h-4 w-4 text-primary" />
        Effet IA ici · {timecode(ctxBase.debut, fps)}
        <button type="button" aria-label="Fermer" className="ml-auto text-muted-foreground hover:text-foreground" onClick={fermer}>
          <X className="h-4 w-4" />
        </button>
      </div>
      <form
        onSubmit={(e) => {
          e.preventDefault()
          void lancer(phrase)
        }}
        className="flex gap-2"
      >
        <Input
          ref={champ}
          value={phrase}
          onChange={(e) => setPhrase(e.target.value)}
          placeholder="Ex. : look film des années 80"
          aria-label="Décris l’effet"
          className="h-8 text-sm"
        />
        <Button type="submit" size="sm" disabled={!phrase.trim() || enCours}>
          {enCours ? <Loader2 className="h-4 w-4 animate-spin" /> : 'Créer'}
        </Button>
      </form>
      <div className="mt-2 flex flex-wrap gap-1">
        {PUCES.map((p) => (
          <button
            key={p}
            type="button"
            className="rounded-full border border-border px-2 py-0.5 text-xs hover:bg-accent"
            onClick={() => {
              setPhrase(p)
              void lancer(p)
            }}
          >
            {p}
          </button>
        ))}
      </div>
      <div className="mt-2 flex items-center gap-1 text-xs text-muted-foreground" role="radiogroup" aria-label="Portée">
        Portée :
        {(
          [
            ['deux', '2 s'],
            ['cinq', '5 s'],
            ...(ouverture.itemId ? [['clip', 'Ce clip'] as const] : []),
          ] as const
        ).map(([v, l]) => (
          <button
            key={v}
            type="button"
            role="radio"
            aria-checked={portee === v}
            className={cn('rounded px-1.5 py-0.5', portee === v ? 'bg-primary text-primary-foreground' : 'hover:bg-accent')}
            onClick={() => setPortee(v)}
          >
            {l}
          </button>
        ))}
      </div>
      {enCours && <p className="mt-2 text-xs text-muted-foreground">Le compilateur d’effets réfléchit…</p>}
      {erreur && <p className="mt-2 text-xs text-destructive">{erreur}</p>}
      {appliquee && (
        <div className="mt-3 border-t border-border pt-2">
          <p className="text-xs font-medium">{appliquee.recette.resume}</p>
          <p className="text-xs text-muted-foreground">
            {resumeRecette(appliquee.recette, fpsCourant())} ·{' '}
            {appliquee.source === 'locale' ? 'recette Nexora, 0 jeton' : 'compilé par l’IA'}
          </p>
          {appliquee.avertissements.length > 0 && (
            <p className="mt-1 text-[11px] text-amber-500">{appliquee.avertissements.slice(0, 2).join(' ; ')}</p>
          )}
          <div className="mt-2 flex flex-wrap gap-1">
            <Button size="sm" variant="outline" className="h-7 px-2 text-xs" onClick={() => intensite(0.6)} disabled={appliquee.avant}>
              <Minus className="mr-1 h-3 w-3" /> Plus doux
            </Button>
            <Button size="sm" variant="outline" className="h-7 px-2 text-xs" onClick={() => intensite(1.5)} disabled={appliquee.avant}>
              <Plus className="mr-1 h-3 w-3" /> Plus fort
            </Button>
            <Button size="sm" variant="outline" className="h-7 px-2 text-xs" onClick={basculer} aria-pressed={appliquee.avant}>
              {appliquee.avant ? 'Après' : 'Avant'}
            </Button>
            <Button size="sm" variant="ghost" className="h-7 px-2 text-xs" onClick={annuler}>
              <Undo2 className="mr-1 h-3 w-3" /> Annuler
            </Button>
            <Button size="sm" className="ml-auto h-7 px-3 text-xs" onClick={() => {
              if (appliquee.avant) refaire()
              fermer()
            }}>
              Garder
            </Button>
          </div>
        </div>
      )}
    </div>
  )
}

/** Hôte unique, monté par l'éditeur. */
export function BulleEffetHote() {
  const ouverte = useBulleEffetStore((s) => s.ouverte)
  const fermer = useBulleEffetStore((s) => s.fermer)
  if (!ouverte) return null
  return <Bulle key={`${ouverte.x}:${ouverte.y}:${ouverte.itemId ?? ''}`} ouverture={ouverte} fermer={fermer} />
}
