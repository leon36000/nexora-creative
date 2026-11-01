/**
 * Nexora Creative : l'assistant de montage du Mode Studio. La personne dit ce qu'elle veut en français ; l'assistant
 * répond, applique ses commandes en un seul pas d'annulation et lance les actions d'IA (silences, sous-titres, rythme,
 * génération) en montrant où il en est.
 */
import { memo, useCallback, useEffect, useRef, useState } from 'react'
import { Loader2, Send, Sparkles, Undo2 } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Textarea } from '@/components/ui/textarea'
import { cn } from '@/shared/ui/cn'
import { useTimelineCommandStore } from '@/features/timeline/stores/timeline-command-store'
import { nexora, type MessageChat } from './api'
import { appliquerCommandes, etatPourAssistant, executerAction } from './timeline'

interface Bulle {
  role: 'user' | 'assistant'
  texte: string
  detail?: string[]
  annulable?: boolean
}

const SUGGESTIONS = [
  'Coupe les silences',
  'Ajoute des sous-titres',
  'Monte les plans au rythme de la musique',
  'Ajoute un titre « The interview » au début',
  'Mets un fondu entre chaque plan',
  'Génère un plan d’ouverture : survol d’une jungle au lever du soleil',
]

export const AssistantPanel = memo(function AssistantPanel() {
  const [bulles, setBulles] = useState<Bulle[]>([
    {
      role: 'assistant',
      texte:
        'Bonjour ! Dis-moi ce que tu veux faire sur ton montage : je coupe, je place, je sous-titre, je cale sur la musique, et je génère les plans qui manquent. Chaque demande s’annule d’un coup.',
    },
  ])
  const [saisie, setSaisie] = useState('')
  const [occupe, setOccupe] = useState<string | null>(null)
  const fil = useRef<HTMLDivElement>(null)
  const peutAnnuler = useTimelineCommandStore((s) => s.canUndo)

  useEffect(() => {
    fil.current?.scrollTo({ top: fil.current.scrollHeight, behavior: 'smooth' })
  }, [bulles, occupe])

  const ajouter = (b: Bulle) => setBulles((x) => [...x, b])

  const envoyer = useCallback(
    async (texte: string) => {
      const demande = texte.trim()
      if (!demande || occupe) return
      setSaisie('')
      ajouter({ role: 'user', texte: demande })
      setOccupe('Je regarde ta timeline…')
      const historique: MessageChat[] = bulles
        .slice(1)
        .map((b) => ({ role: b.role, content: b.texte }))
      try {
        const r = await nexora.assistant(demande, etatPourAssistant(), historique)
        const detail: string[] = []
        let annulable = false
        if (r.commandes.length) {
          const bilan = appliquerCommandes(r.commandes, demande.slice(0, 60))
          annulable = bilan.faites > 0
          if (bilan.erreurs.length) detail.push(...bilan.erreurs.map((e) => `Non appliqué : ${e}`))
        }
        ajouter({ role: 'assistant', texte: r.reponse, detail, annulable })
        for (const a of r.actions) {
          try {
            const fait = await executerAction(a, setOccupe)
            ajouter({ role: 'assistant', texte: fait, annulable: true })
          } catch (e) {
            ajouter({ role: 'assistant', texte: e instanceof Error ? e.message : String(e) })
          }
        }
      } catch (e) {
        ajouter({ role: 'assistant', texte: e instanceof Error ? e.message : String(e) })
      } finally {
        setOccupe(null)
      }
    },
    [bulles, occupe],
  )

  return (
    <div className="flex h-full min-h-0 flex-col">
      <div className="flex items-center gap-2 border-b border-border px-3 py-2">
        <Sparkles className="h-4 w-4 text-primary" />
        <span className="text-sm font-semibold">Assistant de montage</span>
        <Button
          variant="ghost"
          size="sm"
          className="ml-auto h-7 gap-1 px-2 text-xs"
          disabled={!peutAnnuler || !!occupe}
          onClick={() => useTimelineCommandStore.getState().undo()}
          title="Annuler la dernière modification (Ctrl+Z)"
        >
          <Undo2 className="h-3.5 w-3.5" /> Annuler
        </Button>
      </div>

      <div ref={fil} className="min-h-0 flex-1 space-y-2 overflow-y-auto p-3" aria-live="polite">
        {bulles.map((b, i) => (
          <div
            key={i}
            className={cn(
              'max-w-[92%] rounded-lg px-3 py-2 text-sm leading-relaxed',
              b.role === 'user'
                ? 'ml-auto bg-primary text-primary-foreground'
                : 'bg-secondary text-secondary-foreground',
            )}
          >
            {b.texte}
            {b.detail?.map((d, j) => (
              <div key={j} className="mt-1 text-xs opacity-75">
                {d}
              </div>
            ))}
          </div>
        ))}
        {occupe && (
          <div className="flex items-center gap-2 text-xs text-muted-foreground">
            <Loader2 className="h-3.5 w-3.5 animate-spin" /> {occupe}
          </div>
        )}
      </div>

      <div className="flex flex-wrap gap-1.5 px-3 pb-2">
        {SUGGESTIONS.map((s) => (
          <button
            key={s}
            type="button"
            disabled={!!occupe}
            onClick={() => void envoyer(s)}
            className="rounded-full border border-border px-2.5 py-1 text-[11px] text-muted-foreground transition-colors hover:border-primary hover:text-foreground disabled:opacity-50"
          >
            {s}
          </button>
        ))}
      </div>

      <form
        className="flex items-end gap-2 border-t border-border p-3"
        onSubmit={(e) => {
          e.preventDefault()
          void envoyer(saisie)
        }}
      >
        <Textarea
          value={saisie}
          onChange={(e) => setSaisie(e.target.value)}
          onKeyDown={(e) => {
            // Entrée envoie, Maj+Entrée va à la ligne ; les raccourcis de l'éditeur ne voient pas la frappe.
            e.stopPropagation()
            if (e.key === 'Enter' && !e.shiftKey) {
              e.preventDefault()
              void envoyer(saisie)
            }
          }}
          placeholder="Ex. : coupe les silences et ajoute des sous-titres"
          aria-label="Demande à l’assistant de montage"
          rows={2}
          className="min-h-[44px] text-sm"
        />
        <Button
          type="submit"
          size="icon"
          disabled={!saisie.trim() || !!occupe}
          aria-label="Envoyer"
        >
          <Send className="h-4 w-4" />
        </Button>
      </form>
    </div>
  )
})
