/**
 * Nexora Creative : recettes « maison » de la bulle d'effet. Une phrase courante (« VHS », « look film des années 80 »)
 * est reconnue par le code et appliquée tout de suite, sans appel au LLM (0 jeton, 0 attente). Ce sont aussi les
 * recettes canon du banc : chacune est validée contre le vrai registre GPU par les tests.
 */
export interface RecetteLocale {
  nom: string
  /** Puce proposée dans la bulle. */
  puce?: string
  motifs: RegExp[]
  recette: { resume: string; etapes: unknown[] }
}

const pile = (resume: string, effets: { gpu: string; params?: Record<string, unknown> }[]) => ({
  resume,
  etapes: [{ kind: 'gpu_stack', effets }],
})

export const RECETTES_LOCALES: RecetteLocale[] = [
  {
    nom: 'Look film années 80',
    puce: 'Look film années 80',
    motifs: [/annees? ?(19)?80/, /\b80'?s\b/, /eighties/, /look (film )?retro/, /retro/],
    recette: pile('Look film années 80', [
      { gpu: 'gpu-temperature', params: { temperature: 0.25, tint: 0.05 } },
      { gpu: 'gpu-saturation', params: { amount: 0.8 } },
      { gpu: 'gpu-grain', params: { amount: 0.18, size: 1.4 } },
      { gpu: 'gpu-vignette', params: { amount: 0.45, softness: 0.7 } },
    ]),
  },
  {
    nom: 'VHS',
    puce: 'VHS',
    motifs: [/\bvhs\b/, /cassette/, /magnetoscope/, /camescope/],
    recette: pile('Cassette VHS', [
      { gpu: 'gpu-vhs', params: { bleed: 0.6, waviness: 0.4, noise: 0.35, scanline: 0.45 } },
      { gpu: 'gpu-saturation', params: { amount: 0.85 } },
    ]),
  },
  {
    nom: 'Noir et blanc contrasté',
    puce: 'Noir et blanc',
    motifs: [/noir (et|&) blanc/, /\bn ?(&|et) ?b\b/, /monochrome/, /niveaux de gris/, /black (and|&) white/],
    recette: pile('Noir et blanc contrasté', [
      { gpu: 'gpu-grayscale', params: { amount: 1 } },
      { gpu: 'gpu-contrast', params: { amount: 1.35 } },
    ]),
  },
  {
    nom: 'Vieux film sépia',
    motifs: [/sepia/, /vieux film/, /film ancien/, /ancien/, /annees? ?(19)?(20|30|40)/, /muet/],
    recette: pile('Vieux film sépia', [
      { gpu: 'gpu-sepia', params: { amount: 0.85 } },
      { gpu: 'gpu-grain', params: { amount: 0.3, size: 1.8 } },
      { gpu: 'gpu-vignette', params: { amount: 0.7, softness: 0.6 } },
    ]),
  },
  {
    nom: 'Glitch numérique',
    puce: 'Glitch',
    motifs: [/glitch/, /bug (numerique|video)/, /datamosh/, /parasite/, /piratage|hack/],
    recette: pile('Glitch numérique', [
      { gpu: 'gpu-block-glitch', params: { coverage: 0.35, intensity: 0.7 } },
      { gpu: 'gpu-rgb-split', params: { amount: 0.02 } },
      { gpu: 'gpu-color-glitch', params: { intensity: 0.5 } },
    ]),
  },
  {
    nom: 'Flou doux',
    motifs: [/\bflou\b(?! de mouvement| de vitesse)/, /floute/, /\bblur\b/, /mise au point ratee/],
    recette: pile('Flou doux', [{ gpu: 'gpu-gaussian-blur', params: { radius: 12 } }]),
  },
  {
    nom: 'Flou de mouvement',
    motifs: [/flou de (mouvement|vitesse)/, /motion blur/, /vitesse folle/],
    recette: pile('Flou de mouvement', [{ gpu: 'gpu-motion-blur', params: { amount: 0.12 } }]),
  },
  {
    nom: 'Zoom choc',
    motifs: [/zoom (choc|rapide|flou)/, /coup de zoom/, /effet de zoom/],
    recette: pile('Zoom choc', [{ gpu: 'gpu-zoom-blur', params: { amount: 0.45 } }]),
  },
  {
    nom: 'Rêve doux',
    puce: 'Rêve',
    motifs: [/\breve\b/, /onirique/, /souvenir/, /flash ?back/, /nostalgi/],
    recette: pile('Rêve doux', [
      { gpu: 'gpu-glow', params: { amount: 1.8, threshold: 0.45, radius: 30 } },
      { gpu: 'gpu-exposure', params: { exposure: 0.25 } },
      { gpu: 'gpu-saturation', params: { amount: 0.75 } },
      { gpu: 'gpu-vignette', params: { amount: 0.35, softness: 0.9 } },
    ]),
  },
  {
    nom: 'Halo lumineux',
    puce: 'Halo lumineux',
    motifs: [/halo/, /\bglow\b/, /\beclat\b/, /briller|brillant/, /bloom/, /lumieres? douces?/],
    recette: pile('Halo lumineux', [
      { gpu: 'gpu-glow', params: { amount: 2, threshold: 0.55, radius: 25 } },
    ]),
  },
  {
    nom: 'Chaud, heure dorée',
    puce: 'Heure dorée',
    motifs: [/chaud/, /heure doree/, /\bdoree?\b/, /coucher de soleil/, /golden hour/, /\bete\b/],
    recette: pile('Heure dorée', [
      { gpu: 'gpu-temperature', params: { temperature: 0.45 } },
      { gpu: 'gpu-vibrance', params: { amount: 0.3 } },
      { gpu: 'gpu-glow', params: { amount: 0.8, threshold: 0.7 } },
    ]),
  },
  {
    nom: 'Froid, bleuté',
    motifs: [/froid/, /bleu(te)?/, /hiver/, /glacial/],
    recette: pile('Froid bleuté', [
      { gpu: 'gpu-temperature', params: { temperature: -0.45 } },
      { gpu: 'gpu-saturation', params: { amount: 0.85 } },
    ]),
  },
  {
    nom: 'Nuit, sombre',
    motifs: [/\bnuit\b/, /(?<!trop )\bsombre/, /assombri/, /baisse la lumiere/, /moins lumineux/, /nocturne/],
    recette: pile('Nuit', [
      { gpu: 'gpu-exposure', params: { exposure: -0.8 } },
      { gpu: 'gpu-temperature', params: { temperature: -0.3 } },
      { gpu: 'gpu-vignette', params: { amount: 0.6 } },
    ]),
  },
  {
    nom: 'Plus de punch',
    puce: 'Plus de punch',
    motifs: [/punch/, /contraste/, /plus vif/, /eclatant/, /couleurs? (vives|qui petent)/, /(?<!de)sature/],
    recette: pile('Plus de punch', [
      { gpu: 'gpu-contrast', params: { amount: 1.25 } },
      { gpu: 'gpu-vibrance', params: { amount: 0.4 } },
    ]),
  },
  {
    nom: 'Délavé',
    motifs: [/delave/, /terne/, /desature/, /pastel/],
    recette: pile('Délavé', [
      { gpu: 'gpu-saturation', params: { amount: 0.5 } },
      { gpu: 'gpu-contrast', params: { amount: 0.85 } },
    ]),
  },
  {
    nom: 'Vieil écran cathodique',
    motifs: [/\bcrt\b/, /cathodique/, /vieil? (ecran|televiseur|tele)/, /arcade/],
    recette: pile('Écran cathodique', [
      { gpu: 'gpu-crt', params: { curvature: 0.4, scanlines: 0.5, vignette: 0.4 } },
    ]),
  },
  {
    nom: 'Lignes de balayage',
    motifs: [/lignes? de balayage/, /scanlines?/, /ecran de surveillance/, /camera de surveillance/],
    recette: pile('Lignes de balayage', [
      { gpu: 'gpu-scanlines', params: { density: 6, opacity: 0.45 } },
      { gpu: 'gpu-grayscale', params: { amount: 0.6 } },
    ]),
  },
  {
    nom: 'Pixels',
    motifs: [/pixel/, /8 ?bits?/, /jeu video retro/, /censure/],
    recette: pile('Pixels', [{ gpu: 'gpu-pixelate', params: { size: 16 } }]),
  },
  {
    nom: 'Affiche (postérisation)',
    motifs: [/posteri/, /pop art/, /bande dessinee|bd\b|comic/],
    recette: pile('Postérisation', [
      { gpu: 'gpu-posterize', params: { levels: 5 } },
      { gpu: 'gpu-contrast', params: { amount: 1.2 } },
    ]),
  },
  {
    nom: 'Kaléidoscope',
    motifs: [/kaleidoscope/, /psychedeli/, /miroir/],
    recette: pile('Kaléidoscope', [{ gpu: 'gpu-kaleidoscope', params: { segments: 8 } }]),
  },
  {
    nom: 'Ondulation',
    motifs: [/ondul/, /\bondes?\b/, /\bvagues?\b/, /chaleur|mirage/, /sous l'?eau/, /\bivre\b|vertige/],
    recette: pile('Ondulation', [
      { gpu: 'gpu-wave', params: { amplitudeX: 0.015, amplitudeY: 0.015, frequencyX: 6 } },
    ]),
  },
  {
    nom: 'Aberration chromatique',
    motifs: [/aberration/, /chromatique/, /rgb ?split/, /dedoubl/],
    recette: pile('Aberration chromatique', [{ gpu: 'gpu-rgb-split', params: { amount: 0.015 } }]),
  },
  {
    nom: 'Grain de pellicule',
    motifs: [/grain/, /pellicule/, /argentique/, /16 ?mm|35 ?mm/],
    recette: pile('Grain de pellicule', [
      { gpu: 'gpu-grain', params: { amount: 0.22, size: 1.6 } },
      { gpu: 'gpu-vignette', params: { amount: 0.3 } },
    ]),
  },
  {
    nom: 'Vignettage',
    motifs: [/vignett/, /coins sombres/, /bords sombres/],
    recette: pile('Vignettage', [{ gpu: 'gpu-vignette', params: { amount: 0.7, softness: 0.6 } }]),
  },
  {
    nom: 'Plus lumineux',
    motifs: [/plus (clair|lumineux)/, /eclaircir|eclaircis/, /trop sombre/, /surexpos/],
    recette: pile('Plus lumineux', [{ gpu: 'gpu-exposure', params: { exposure: 0.5 } }]),
  },
  {
    nom: 'Couleurs inversées',
    motifs: [/invers(e|er) les couleurs/, /negatif/, /couleurs inversees/],
    recette: pile('Négatif', [{ gpu: 'gpu-invert' }]),
  },
]

const normaliser = (s: string) =>
  s
    .toLowerCase()
    .normalize('NFD')
    .replace(/[̀-ͯ]/g, '')
    .replace(/\s+/g, ' ')
    .trim()

/** La recette maison qui correspond à la phrase, ou null (la phrase ira au LLM). */
export function recetteLocale(phrase: string): RecetteLocale | null {
  const p = normaliser(phrase)
  if (!p) return null
  return RECETTES_LOCALES.find((r) => r.motifs.some((m) => m.test(p))) ?? null
}

export const PUCES = RECETTES_LOCALES.filter((r) => r.puce).map((r) => r.puce!)

/** Banc de phrases françaises (recherche/17 §E) : ≥ 90 % doivent être reconnues par le code. */
export const PHRASES_CANON = [
  'look film des années 80',
  'fais un style VHS',
  'effet cassette vidéo',
  'noir et blanc contrasté',
  'passe en N&B',
  'comme un vieux film',
  'sépia',
  'transition glitch',
  'effet glitch numérique',
  'un flou doux',
  'flou de mouvement rapide',
  'zoom choc',
  'ambiance de rêve',
  'flashback',
  'halo doux sur les lumières',
  'ajoute un glow',
  'heure dorée',
  'coucher de soleil chaud',
  'ambiance froide et bleutée',
  'fais la nuit',
  'baisse la lumière',
  'plus de punch',
  'plus de contraste',
  'couleurs délavées',
  'vieil écran cathodique',
  'caméra de surveillance',
  'pixelise le visage',
  'style bande dessinée',
  'kaléidoscope psychédélique',
  'effet de chaleur, mirage',
  'aberration chromatique',
  'grain de pellicule 16 mm',
  'vignettage',
  "c'est trop sombre",
  'négatif',
  'onde de choc',
]
