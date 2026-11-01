/**
 * Nexora Creative : appels du Mode Studio au serveur Creative (même origine, sous /api).
 * Voir app/server/nexora/studio.ts pour les contrats.
 */

export type GenreCreation = 'video' | 'image' | 'musique'

export interface Creation {
  id: number
  genre: GenreCreation
  nom: string
  url: string
  date: string
  dureeS?: number
}

export type NomCommande =
  | 'texte'
  | 'deplacer'
  | 'supprimer'
  | 'couper'
  | 'raccourcirDebut'
  | 'raccourcirFin'
  | 'volume'
  | 'transition'
  | 'ajouterClip'
  | 'modifier'
export type Commande = Record<string, unknown> & { commande: NomCommande }

export type NomAction =
  | 'silences'
  | 'sous_titres'
  | 'rythme'
  | 'generer_video'
  | 'generer_image'
  | 'generer_musique'
export type Action = Record<string, unknown> & { type: NomAction }

export interface ReponseAssistant {
  reponse: string
  commandes: Commande[]
  actions: Action[]
}

export interface Plage {
  debutS: number
  finS: number
}

export interface LigneSousTitre {
  texte: string
  debutS: number
  finS: number
}

export interface MessageChat {
  role: 'user' | 'assistant'
  content: string
}

async function appel<T>(url: string, init?: RequestInit): Promise<T> {
  const r = await fetch(url, {
    ...init,
    headers: { 'content-type': 'application/json', ...(init?.headers ?? {}) },
  })
  const corps = (await r.json().catch(() => ({}))) as { error?: string }
  if (!r.ok) throw new Error(corps.error ?? `Erreur du serveur (HTTP ${r.status})`)
  return corps as T
}

const poster = <T>(url: string, corps: unknown) =>
  appel<T>(url, { method: 'POST', body: JSON.stringify(corps) })

export const nexora = {
  creations: () =>
    appel<{ creations: Creation[] }>('/api/studio/creations').then((r) => r.creations),
  assistant: (demande: string, etat: unknown, historique: MessageChat[]) =>
    poster<ReponseAssistant>('/api/studio/assistant', { demande, etat, historique }),
  silences: (takeId: number) =>
    appel<{ silences: Plage[]; dureeS?: number }>(`/api/studio/silences/${takeId}`),
  rythme: (takeId: number) =>
    appel<{ bpm: number; temps: number[] }>(`/api/studio/rythme/${takeId}`),
  transcription: (takeId: number) =>
    appel<{ langue: string; sousTitres: LigneSousTitre[] }>(`/api/studio/transcription/${takeId}`),
  prise: (takeId: number) =>
    appel<{ statut: string; erreur?: string; creation: Creation | null }>(
      `/api/studio/prise/${takeId}`,
    ),
  creerVideo: (intention: string, duree: 5 | 10, format: '16:9' | '9:16' | '1:1') =>
    poster<{ takeId: number }>('/api/nexora/creer', { intention, duree, format, son: true }),
  creerImage: (intention: string, format: '16:9' | '9:16' | '1:1') =>
    poster<{ takeIds: number[]; takeId?: number }>('/api/nexora/image', { intention, format }),
  creerMusique: (envie: string, dureeS: number) =>
    poster<{ takeId: number }>('/api/studio/musique', { envie, dureeS }),
}

/** Attend qu'une génération se termine (rendu sur le parc GPU), en signalant l'attente. */
export async function attendrePrise(
  takeId: number,
  surAttente?: (secondes: number) => void,
  delaiMaxS = 1800,
): Promise<Creation> {
  const debut = Date.now()
  for (;;) {
    const p = await nexora.prise(takeId)
    if (p.statut === 'done' && p.creation) return p.creation
    if (p.statut === 'failed' || p.statut === 'stopped') {
      throw new Error(p.erreur ? `Le rendu a échoué : ${p.erreur}` : 'Le rendu a échoué.')
    }
    const ecoule = (Date.now() - debut) / 1000
    if (ecoule > delaiMaxS)
      throw new Error('Le rendu prend trop de temps ; il reste dans tes créations.')
    surAttente?.(Math.round(ecoule))
    await new Promise((ok) => setTimeout(ok, 4000))
  }
}
