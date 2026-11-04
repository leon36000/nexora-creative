/** Recette mesurée dans recherche/26. Les contrôles lexicaux sont des garde-fous, pas une note de réalisme. */
export const MOTS_RENDU_INTERDITS = [
  'cinematic', 'epic', 'glowing', 'incandescent', 'majestic', 'dramatic lighting', 'hyper-detailed',
  'ultra-detailed', '8k', 'render', 'cgi', 'unreal', 'concept art', 'teal and orange', 'vibrant', 'stunning',
  'volumetric',
] as const;

const echapper = (s: string) => s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&').replace(/[- ]/g, '[-\\s]+');
const interdit = new RegExp(`\\b(?:${MOTS_RENDU_INTERDITS.map(echapper).join('|')})\\b`, 'gi');

/** Même intention que le négatif du rapport, sans répéter les déclencheurs au sein du conditionnement positif.
 * H3 utilise BasicGuider (CFG 1), sans entrée négative : cette exclusion reste une phrase de prose du guide. */
export const NEGATIF_LIVE_ACTION = 'Avoid synthetic imagery, game-like aesthetics, painted backdrops, airbrushed skin, smooth plastic surfaces, excessive saturation, artificial halos, exaggerated contrast, toy-like scale and rigidly symmetric framing.';
export const STYLE_LIVE_ACTION = 'Live-action footage photographed on an ARRI Alexa 35 sensor with a Cooke S4 50mm lens, natural exposure, fine film grain, slight halation and lens imperfections';
export const STYLE_NEUTRE = 'A clear, consistent visual style suited to the request';

const STYLE_ANIME = /\b(?:2d(?:[- ]animated?)?|3d\s+(?:animated?|animation|cg|cgi|render|character|model|scene|film|video)|animated?\s+(?:film|movie|video|short|series|scene|character)|cartoon(?:ish)?|anime|manga|claymation|stop[- ]motion|motion design|cgi|computer[- ]generated|illustration|illustrated|hand[- ]drawn|drawn animation|dessin(?:s)? animé|dessin d['’]animation|film d['’]animation|vidéo d['’]animation|animation\s+(?:2d|3d|cgi)|(?:style|look)\s+(?:cartoon|anime|manga|illustration|claymation)|video[- ]game (?:style|look)|game[- ]like style|game[- ]art(?: style)?|(?:style|look) (?:de )?jeu vidéo|graphismes? de jeu vidéo|jeu vidéo(?:que)?)(?=$|[^\p{L}\p{N}_])/iu;
const STYLE_PHOTO = /\b(?:live[- ]action|photoreal(?:istic|isme)?|photoréalistes?|photoréalisme|photographic(?:ally)?|photographique|prises? de vues? réelles?|filmée? en réel|shot on film|real footage)(?![\p{L}\p{N}_])/iu;
const NEGATION_STYLE = /(?:\b(?:not|no|never|without|non|pas|sans|aucun|aucune|ne)\b|\bdon['’]t\b)(?:[\s\p{L}'’:-]{0,28})$/iu;
const NEGATION_PHOTO = /\b(?:not|no|without|non|pas|sans)\s+(?:a\s+|the\s+|de\s+|du\s+|d['’])?(?:live[- ]action|photoreal(?:istic|isme)?|photoréaliste|photoréalisme|photographic|photographique|prises? de vues? réelles?)\b/i;
const PROMO = /\b(?:pub|ad|ads|advert|advertisement|advertising|commercial|promo(?:tional|tionnel(?:le)?|tion)?|publicit(?:é|e|aire)?|annonce publicitaire|vidéo promo|film promo)(?![\p{L}\p{N}_])/iu;

/**
 * Détecte un style non photographique explicitement demandé. Les verbes « animer une photo » et les mentions
 * d'« animation d'un vrai acteur » ne sont pas des choix de dessin animé; un mot nié ne compte pas non plus.
 */
export function styleNonPhotographiqueDemande(texte: string): boolean {
  for (const m of texte.matchAll(new RegExp(STYLE_ANIME.source, STYLE_ANIME.flags + 'g'))) {
    const avant = texte.slice(Math.max(0, m.index! - 30), m.index!);
    if (!NEGATION_STYLE.test(avant)) return true;
  }
  return false;
}

/** La photographie est le défaut des pubs/produits; tout style visuel explicitement demandé reste prioritaire. */
export function requiertPhotographie(
  famille: string | undefined,
  intention: string,
  consignes: readonly string[] = [],
): boolean {
  const brief = [intention, ...consignes].join('\n');
  if (styleNonPhotographiqueDemande(brief) || NEGATION_PHOTO.test(brief)) return false;
  if (STYLE_PHOTO.test(brief)) return true;
  return famille === 'pub' || famille === 'produit' || PROMO.test(brief);
}

/** Mouvement, repères d'échelle et conception spatiale originale s'appliquent à tout style visuel. */
export const REGLES_ACTION = [
  'MOTION: preserve the action the client asked for. Describe a clear start, change or impact, and result over time; use one main action and one camera move per shot; show weight, contact and consequences when relevant. Never replace movement with a static tableau.',
  'SCALE: keep the main subject readable. For oversized creatures, vehicles or effects, include a concrete scale reference such as people, a building, a cockpit window or a familiar object. A distant flock must not replace a large hero subject.',
  'SPACE SUBJECTS: keep spacecraft purpose-built and original; do not replace a requested spacecraft with a real military aircraft, naval vessel, aircraft carrier or battleship. Apply photographic lighting and exposure rules only when the photographic recipe below applies.',
].join('\n');

export const REGLES_LIVE_ACTION = [
  'CONDITIONAL PHOTO RECIPE: use this only for promotional ads or product films by default, or when the client explicitly requests photographic/live-action imagery. A clearly requested visual medium takes precedence in every family: preserve 2D/3D animation, anime, cartoons, illustration, stop-motion, claymation, or a game-art style. “Animate this photo” and “animation of a real actor” describe motion or a subject, not an animated visual style.',
  'Name a real camera (ARRI Alexa 35, Arricam LT, Sony Venice), a real lens family AND focal length (Cooke S4 50mm, Zeiss Supreme 35mm), and film stock (Kodak Vision3 500T) or a sensor in style. Each shot names its lens/focal length, motivated practical light and tangible materials.',
  'Use natural exposure, visible fine film grain, soft lens imperfections, slight halation, focus breathing and natural motion blur from a 180-degree shutter. Choose coherent equipment, exposure and practical light for the scene; never copy a production-still instruction into moving footage.',
  `For photographic promo footage only, avoid this synthetic-look vocabulary in visual fields: ${MOTS_RENDU_INTERDITS.join(', ')}. Translate the requested impact into physical light, materials and action. Dialogue and explicitly requested on-screen words stay verbatim.`,
  'For photographic space footage, use real space photography: hard direct sunlight, deep black shadows and realistic exposure; if Earth is visible, preserve its real cloud systems, blue limb and curvature. Use worn spacecraft metal and plausible size cues. No haze or sound propagating through vacuum; sound can come from a cockpit or a score.',
  NEGATIF_LIVE_ACTION,
].join('\n');

/** Répliques et texte visible explicitement demandé ne sont pas des instructions de style. */
export function horsParoles(t: string): string {
  return t.replace(/<d>[\s\S]*?<\/d>/g, '').replace(/"[^"\n]*"/g, '');
}

export function motsRenduInterdits(t: string): string[] {
  return [...new Set(horsParoles(t).match(interdit)?.map((m) => m.toLowerCase()) ?? [])];
}

/** Filet du repli hors ligne : préserver les verbes et objets, retirer uniquement les qualificatifs de synthèse. */
export function nettoyerRepli(t: string, photographique = true): string {
  const equivalents: [RegExp, string][] = [
    [/\b(lightsabers?|sabres? laser)\b/gi, 'energy blade'],
    [/\b(jedi|sith|darth|star ?wars)\b/gi, 'original space knight'],
    [/\b(starbucks|tim hortons?|mcdonald'?s)\b/gi, 'local coffee shop'],
    [/\b(nike|adidas|stetson)\b/gi, 'unbranded clothing'],
    [/\b(coca-?cola|pepsi)\b/gi, 'unbranded soda'],
    [/\b(iphone|samsung)\b/gi, 'unbranded phone'],
    [/\b(rolex)\b/gi, 'unbranded wristwatch'],
    [/\b(ferrari)\b/gi, 'unbranded sports car'],
    [/\b(marvel|avengers|disney|pixar|pok[eé]mon|harry potter|batman|superman|spider-?man|iron ?man|transformers?|godzilla|lego)\b/gi, 'original fictional character'],
  ];
  const styleNettoye = photographique ? t.replace(interdit, '') : t;
  return equivalents.reduce((s, [re, vers]) => s.replace(re, vers), styleNettoye)
    .replace(/\s+/g, ' ').trim();
}

export function estSpatial(intention: string): boolean {
  return /\b(space(?:ship|craft| station)?|orbit\w*|astronaut\w*|vaisseau\w*|spatial\w*|espace|cosmos|lune|moon)\b/i.test(intention);
}

/** Vérification du texte compilé, partagée avec le banc sans GPU. */
export function verifierRecetteLiveAction(
  t: string,
  intention: string,
  famille?: string,
  consignes: readonly string[] = [],
): string[] {
  if (!requiertPhotographie(famille, intention, consignes)) return [];
  const p = horsParoles(t);
  const erreurs = motsRenduInterdits(p).map((m) => `forbidden visual word "${m}": replace it with physical photographic detail`);
  const exigences: [RegExp, string][] = [
    [/live[- ]action/i, 'live-action photography'],
    [/\b(ARRI|Arricam|Alexa|Sony Venice|Panavision|RED (?:V|K)|Canon|Blackmagic)\b/i, 'a named real camera'],
    [/\b(Cooke|Zeiss|Leica|Angenieux|Angénieux|Panavision|Canon|Nikkor|Sigma)\b/i, 'a named lens family'],
    [/\b\d{2,3}\s?mm\b/i, 'a focal length'],
    [/\b(Kodak|Vision3|film stock|sensor)\b/i, 'film stock or a sensor'],
    [/\bgrain\b/i, 'photographic grain'],
    [/\b(halation|lens imperfections|focus breathing|lens breathing|chromatic aberration)\b/i, 'a restrained lens imperfection'],
  ];
  for (const [re, label] of exigences) if (!re.test(p)) erreurs.push(`include ${label}`);
  if (estSpatial(intention)) {
    if (!/\b(hard|direct|unfiltered)\b[^.]{0,45}\b(sunlight|sun|solar)\b/i.test(p)) erreurs.push('space: use hard direct sunlight and deep black shadows');
    if (/\b(earth|terre)\b/i.test(intention) && !/\bEarth\b/.test(p)) erreurs.push('space: preserve real Earth with correct curvature and clouds');
  }
  return erreurs;
}

/** Garde-fous d'identité du sujet spatial, indépendants du médium (photo, animation ou illustration). */
export function verifierVaisseauxOriginaux(t: string, intention: string): string[] {
  if (!estSpatial(intention)) return [];
  const p = horsParoles(t);
  const erreurs: string[] = [];
  if (!/\b(original|purpose-built|unique|invented)\b/i.test(p)) erreurs.push('space: use original purpose-built spacecraft designs');
  if (/\b(battleships?|aircraft carriers?|naval ships?|F[- ]?(?:16|18|22|35)|B[- ]?2|warships?)\b/i.test(p)) {
    erreurs.push('space: replace real military aircraft and naval vessels with original spacecraft');
  }
  return erreurs;
}
