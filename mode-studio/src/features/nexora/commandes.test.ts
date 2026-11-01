import { describe, expect, it } from 'vitest'
import {
  CommandeInvalide,
  calageSurTemps,
  plagesARetirer,
  sourceVersTimeline,
  traduireCommande,
} from './commandes'

const ctx = { fps: 30, hauteur: 1080 }

describe('traduction des commandes de l’assistant', () => {
  it('convertit les secondes en images et garde les conventions de FreeCut', () => {
    expect(traduireCommande({ commande: 'couper', id: 'a', aS: 2.5 }, ctx)).toEqual({
      op: 'split',
      id: 'a',
      frame: 75,
    })
    expect(traduireCommande({ commande: 'raccourcirDebut', id: 'a', s: 1 }, ctx)).toMatchObject({
      op: 'trimStart',
      amount: 30,
    })
    expect(traduireCommande({ commande: 'raccourcirFin', id: 'a', s: 1 }, ctx)).toMatchObject({
      op: 'trimEnd',
      amount: -30,
    })
  })

  it('pose un texte centré, en bas par défaut, à une taille lisible', () => {
    expect(
      traduireCommande(
        { commande: 'texte', texte: 'Bonjour', debutS: 1, dureeS: 2, gras: true },
        ctx,
      ),
    ).toMatchObject({
      op: 'addText',
      text: 'Bonjour',
      from: 30,
      durationInFrames: 60,
      fontSize: 77,
      fontWeight: 'bold',
      textAlign: 'center',
      verticalAlign: 'bottom',
    })
  })

  it('borne le volume et filtre les champs modifiables', () => {
    expect(traduireCommande({ commande: 'volume', id: 'a', db: 40 }, ctx)).toMatchObject({
      updates: { volume: 12 },
    })
    expect(
      traduireCommande(
        { commande: 'modifier', id: 't', champs: { color: '#ff0000', trackId: 'x' } },
        ctx,
      ),
    ).toEqual({ op: 'updateItem', id: 't', updates: { color: '#ff0000' } })
  })

  it('refuse une commande incomplète avec un message lisible', () => {
    expect(() => traduireCommande({ commande: 'deplacer', id: 'a' }, ctx)).toThrow(CommandeInvalide)
    expect(() => traduireCommande({ commande: 'supprimer', ids: [] }, ctx)).toThrow(/aucun élément/)
  })

  it('ne transmet un style de transition que s’il est connu', () => {
    expect(
      traduireCommande(
        { commande: 'transition', gaucheId: 'a', droiteId: 'b', style: 'glitch' },
        ctx,
      ),
    ).toMatchObject({ presentation: 'glitch', durationInFrames: 15 })
    expect(
      traduireCommande({ commande: 'transition', gaucheId: 'a', droiteId: 'b', style: 'x' }, ctx),
    ).not.toHaveProperty('presentation')
  })
})

describe('temps de la source vers la timeline', () => {
  const clip = { from: 300, durationInFrames: 150, sourceStart: 48, sourceFps: 24, speed: 1 }

  it('tient compte du début rogné de la source', () => {
    expect(sourceVersTimeline(clip, 2, 30)).toBe(300)
    expect(sourceVersTimeline(clip, 4, 30)).toBe(360)
    expect(sourceVersTimeline(clip, 10, 30)).toBeNull()
  })

  it('donne les plages de silence à retirer, de la fin vers le début', () => {
    const plages = plagesARetirer(
      clip,
      [
        { debutS: 2.5, finS: 3 },
        { debutS: 5, finS: 5.1 },
        { debutS: 6, finS: 9 },
      ],
      30,
    )
    expect(plages).toEqual([
      { debut: 420, fin: 450 },
      { debut: 315, fin: 330 },
    ])
  })
})

describe('montage au rythme', () => {
  it('raccourcit chaque clip jusqu’au dernier temps qu’il atteint et recolle les clips', () => {
    const r = calageSurTemps(
      [
        { id: 'b', from: 100, durationInFrames: 100 },
        { id: 'a', from: 0, durationInFrames: 100 },
      ],
      [1, 2, 3, 4, 5, 6],
      30,
    )
    expect(r).toEqual([
      { id: 'a', from: 0, durationInFrames: 90 },
      { id: 'b', from: 90, durationInFrames: 90 },
    ])
  })

  it('laisse intacts les plans qui finissent après la fin de la musique', () => {
    const r = calageSurTemps(
      [
        { id: 'a', from: 0, durationInFrames: 146 },
        { id: 'b', from: 146, durationInFrames: 155 },
      ],
      [0.6, 1.2, 1.8, 2.4, 3, 3.6, 4.2, 4.8, 5.4, 6],
      30,
    )
    expect(r).toEqual([
      { id: 'a', from: 0, durationInFrames: 144 },
      { id: 'b', from: 144, durationInFrames: 155 },
    ])
  })

  it('garde la durée d’un clip qu’aucun temps n’atteint', () => {
    expect(calageSurTemps([{ id: 'a', from: 0, durationInFrames: 10 }], [5], 30)).toEqual([
      { id: 'a', from: 0, durationInFrames: 10 },
    ])
  })
})
