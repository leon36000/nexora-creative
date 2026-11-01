/**
 * Nexora Creative : les créations de la personne (vidéos MiniMax H3, images Qwen-Image, musiques MiniMax-Music3),
 * posées d'un clic sur la timeline, et la génération directe d'un nouveau média depuis le Mode Studio.
 */
import { memo, useCallback, useEffect, useState } from 'react'
import { Film, Image as ImageIcon, Loader2, Music, Plus, RefreshCw, Wand2 } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Textarea } from '@/components/ui/textarea'
import { cn } from '@/shared/ui/cn'
import { nexora, type Creation, type GenreCreation } from './api'
import { executerAction, importerCreation, poserALaTete } from './timeline'

const GENRES: { id: GenreCreation; nom: string; icone: typeof Film; moteur: string }[] = [
  { id: 'video', nom: 'Vidéos', icone: Film, moteur: 'MiniMax H3' },
  { id: 'image', nom: 'Images', icone: ImageIcon, moteur: 'Qwen-Image' },
  { id: 'musique', nom: 'Musiques', icone: Music, moteur: 'MiniMax-Music3' },
]

function Apercu({ c }: { c: Creation }) {
  // Aperçu par la route des médias, qui sert les plages d'octets (lecture partielle des vidéos).
  const src = `/api/media/${c.id}`
  if (c.genre === 'image')
    return <img src={src} alt="" loading="lazy" className="h-full w-full object-cover" />
  if (c.genre === 'video') {
    return (
      <video
        src={`${src}#t=1`}
        preload="metadata"
        muted
        playsInline
        className="h-full w-full object-cover"
      />
    )
  }
  return (
    <div className="flex h-full w-full items-center justify-center bg-gradient-to-br from-primary/30 to-secondary">
      <Music className="h-6 w-6 text-primary" />
    </div>
  )
}

export const CreationsPanel = memo(function CreationsPanel() {
  const [genre, setGenre] = useState<GenreCreation>('video')
  const [creations, setCreations] = useState<Creation[] | null>(null)
  const [erreur, setErreur] = useState<string | null>(null)
  const [enCours, setEnCours] = useState<number | null>(null)
  const [idee, setIdee] = useState('')
  const [generation, setGeneration] = useState<string | null>(null)

  const charger = useCallback(async () => {
    setErreur(null)
    try {
      setCreations(await nexora.creations())
    } catch (e) {
      setErreur(e instanceof Error ? e.message : String(e))
    }
  }, [])

  useEffect(() => {
    void charger()
  }, [charger])

  const poser = async (c: Creation) => {
    setEnCours(c.id)
    setErreur(null)
    try {
      poserALaTete(await importerCreation(c))
    } catch (e) {
      setErreur(e instanceof Error ? e.message : String(e))
    } finally {
      setEnCours(null)
    }
  }

  const generer = async () => {
    const intention = idee.trim()
    if (!intention || generation) return
    setErreur(null)
    setGeneration('Envoi au parc GPU…')
    try {
      const type =
        genre === 'video'
          ? 'generer_video'
          : genre === 'image'
            ? 'generer_image'
            : 'generer_musique'
      await executerAction({ type, intention, envie: intention }, setGeneration)
      setIdee('')
      void charger()
    } catch (e) {
      setErreur(e instanceof Error ? e.message : String(e))
    } finally {
      setGeneration(null)
    }
  }

  const visibles = (creations ?? []).filter((c) => c.genre === genre)
  const moteur = GENRES.find((g) => g.id === genre)!.moteur

  return (
    <div className="flex h-full min-h-0 flex-col">
      <div className="flex items-center gap-1 border-b border-border p-2">
        {GENRES.map(({ id, nom, icone: Icone }) => (
          <button
            key={id}
            type="button"
            onClick={() => setGenre(id)}
            className={cn(
              'flex items-center gap-1.5 rounded-md px-2.5 py-1.5 text-xs transition-colors',
              genre === id
                ? 'bg-primary text-primary-foreground'
                : 'text-muted-foreground hover:bg-accent',
            )}
          >
            <Icone className="h-3.5 w-3.5" /> {nom}
          </button>
        ))}
        <Button
          variant="ghost"
          size="icon"
          className="ml-auto h-7 w-7"
          onClick={() => void charger()}
          aria-label="Actualiser"
        >
          <RefreshCw className="h-3.5 w-3.5" />
        </Button>
      </div>

      <div className="space-y-2 border-b border-border p-3">
        <Textarea
          value={idee}
          onChange={(e) => setIdee(e.target.value)}
          onKeyDown={(e) => e.stopPropagation()}
          placeholder={
            genre === 'musique'
              ? 'Ex. : musique épique, cordes et percussions, montée finale'
              : 'Décris le plan en une phrase, en français'
          }
          aria-label="Décris ce qu’il faut créer"
          rows={2}
          className="text-sm"
        />
        <Button
          size="sm"
          className="w-full gap-1.5"
          disabled={!idee.trim() || !!generation}
          onClick={() => void generer()}
        >
          {generation ? (
            <Loader2 className="h-3.5 w-3.5 animate-spin" />
          ) : (
            <Wand2 className="h-3.5 w-3.5" />
          )}
          {generation ?? `Créer avec ${moteur} et poser à la tête de lecture`}
        </Button>
      </div>

      {erreur && (
        <div className="mx-3 mt-2 rounded-md bg-destructive/15 px-3 py-2 text-xs text-destructive">
          {erreur}
        </div>
      )}

      <div className="min-h-0 flex-1 overflow-y-auto p-3">
        {creations === null && !erreur && (
          <div className="flex items-center gap-2 text-xs text-muted-foreground">
            <Loader2 className="h-3.5 w-3.5 animate-spin" /> Chargement de tes créations…
          </div>
        )}
        {creations !== null && !visibles.length && (
          <p className="text-xs text-muted-foreground">
            Aucune création de ce genre pour l’instant. Décris-en une ci-dessus.
          </p>
        )}
        <div className="grid grid-cols-2 gap-2">
          {visibles.map((c) => (
            <button
              key={c.id}
              type="button"
              onClick={() => void poser(c)}
              disabled={enCours !== null}
              title={`${c.nom}\nCliquer pour poser à la tête de lecture`}
              className="group overflow-hidden rounded-md border border-border text-left transition-colors hover:border-primary disabled:opacity-60"
            >
              <div className="relative aspect-video bg-black">
                <Apercu c={c} />
                <div className="absolute inset-0 flex items-center justify-center bg-black/50 opacity-0 transition-opacity group-hover:opacity-100">
                  {enCours === c.id ? (
                    <Loader2 className="h-5 w-5 animate-spin" />
                  ) : (
                    <Plus className="h-5 w-5" />
                  )}
                </div>
                {c.dureeS && (
                  <span className="absolute bottom-1 right-1 rounded bg-black/70 px-1 text-[10px] text-white">
                    {c.dureeS} s
                  </span>
                )}
              </div>
              <div className="line-clamp-2 px-2 py-1.5 text-[11px] leading-snug text-muted-foreground">
                {c.nom}
              </div>
            </button>
          ))}
        </div>
      </div>
      <div className="border-t border-border px-3 py-2 text-[10px] text-muted-foreground">
        Moteurs : MiniMax H3 · Qwen-Image · MiniMax-Music3
      </div>
    </div>
  )
})
