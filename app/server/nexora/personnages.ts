/**
 * Personnages @ (équivalent Soul ID) : une fiche de personnage dessinée par Qwen-Image (fond gris uni, corps entier à
 * gauche, gros plan à droite), découpée en deux références, enregistrée comme élément nommé (Cast, kind « character »).
 * `@nom` dans un prompt se résout vers cet élément ; en vidéo, les références partent dans MiniMax H3 Ref2VA
 * (point de contrôle ref2va de la recette « h3-max ») au format « full-reference » du guide officiel.
 */

export const LARGEUR_FICHE = 1792;
export const HAUTEUR_FICHE = 1024;

/** Prompt Qwen-Image de la fiche standard ; `descriptionEn` décrit le personnage (apparence, tenue, âge). */
export function promptFiche(descriptionEn: string): string {
  return [
    'Professional character reference sheet on a perfectly plain, uniform neutral grey studio background, soft even lighting, no shadows on the floor.',
    'The image is split in two equal side-by-side panels with the SAME character in both, identical face, hair, skin tone and outfit.',
    'LEFT panel: the full body, standing straight, facing the camera, arms relaxed, feet visible, head to toe in frame.',
    'RIGHT panel: a tight close-up portrait of the face and shoulders, looking at the camera, neutral expression.',
    'Photorealistic, sharp focus, natural skin texture. No text, no labels, no logos, no watermark, no props, no other people.',
    `The character: ${descriptionEn.trim()}`,
  ].join(' ');
}

/** Découpe de la fiche en deux références : [corps entier, gros plan] (rectangles x, y, largeur, hauteur). */
export function decoupeFiche(w = LARGEUR_FICHE, h = HAUTEUR_FICHE): { corps: [number, number, number, number]; visage: [number, number, number, number] } {
  const moitie = Math.floor(w / 2 / 2) * 2;
  return { corps: [0, 0, moitie, h], visage: [w - moitie, 0, moitie, h] };
}

export interface SujetRef {
  nom: string;
  /** Apparence en anglais (notes de l'élément), reprise dans la définition du sujet. */
  apparence: string;
  /** Nombre d'images de référence de ce sujet (1 ou 2). */
  images: number;
}

const echapper = (s: string) => s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');

/**
 * Transforme un prompt H3 texte→vidéo valide (champs integrated_multimodal_description / overall_soundscape /
 * non_diegetic_music) en prompt « full-reference » du guide : subject_definitions, summary, retention_analysis,
 * detailed_description, overall_soundscape, non_diegetic_music. Le nom du personnage devient son étiquette <Subject N> ;
 * s'il n'est pas cité dans un plan, l'étiquette est ajoutée au premier plan. Pur et déterministe.
 */
export interface OptionsRef {
  /** Images de composition ajoutées après celles des personnages : <Picture N> « montre-moi » (cadrage, point de vue, placement). */
  composition?: number;
}

const minuscule = (t: string) => t.replace(/^\s*([A-Z])(?![A-Z])/, (m) => m.toLowerCase());

export function convertirEnPromptRef(prompt: string, sujets: SujetRef[], o: OptionsRef = {}): string {
  const texte = prompt.replace(/\r\n/g, '\n').trim();
  const iDesc = texte.indexOf('integrated_multimodal_description:');
  const iSon = texte.indexOf('overall_soundscape:');
  const iMus = texte.indexOf('non_diegetic_music:');
  if (iDesc < 0 || iSon < 0 || iMus < 0 || (!sujets.length && !o.composition)) return texte;
  let description = texte.slice(iDesc + 'integrated_multimodal_description:'.length, iSon).trim();
  const son = texte.slice(iSon + 'overall_soundscape:'.length, iMus).trim();
  const musique = texte.slice(iMus + 'non_diegetic_music:'.length).trim() || 'N/A';

  let image = 0;
  const definitions: string[] = [];
  const retenues: string[] = [];
  sujets.forEach((s, k) => {
    const label = `<Subject ${k + 1}>`;
    const pics = Array.from({ length: s.images }, (_, j) => `<Picture ${image + j + 1}>`);
    image += s.images;
    const montre = pics.length === 1 ? pics[0] : `${pics.slice(0, -1).join(', ')} and ${pics[pics.length - 1]}`;
    definitions.push(`${label} is ${s.nom}${s.apparence ? `, ${minuscule(s.apparence).replace(/[.\s]+$/, '')}` : ''}, shown in ${montre}${pics.length > 1 ? ' (full body and close-up)' : ''}.`);
    const re = new RegExp(`\\b${echapper(s.nom)}\\b`, 'gi');
    if (re.test(description)) {
      description = description.replace(new RegExp(`\\b${echapper(s.nom)}\\b`, 'gi'), label);
    } else {
      description = description.replace(/\[Shot 1\]\s*/, `[Shot 1] ${label}, ${s.apparence ? minuscule(s.apparence).replace(/[.\s]+$/, '') : s.nom}, is in frame. `);
    }
  });
  // Style d'ouverture : une ou deux phrases avant [Shot 1] (guide, §5.2).
  const avantPlan = description.indexOf('[Shot 1]');
  const style = 'The target video is in a cinematic, photorealistic style with natural lighting.';
  if (avantPlan > 0) description = description.slice(avantPlan);
  const nbPlans = [...description.matchAll(/\[Shot (\d+)\]/g)].length || 1;
  const plans = Array.from({ length: nbPlans }, (_, i) => `[Shot ${i + 1}]`).join(', ');
  sujets.forEach((s, k) => {
    retenues.push(`<Subject ${k + 1}> (appears in ${plans}): fully_preserved - the identity, face, hair, build and outfit of ${s.nom} from the reference pictures are retained.`);
  });
  const etiquettes = sujets.map((_, k) => `<Subject ${k + 1}>`).join(' and ');
  // « Montre-moi » : une image de composition n'est pas un sujet, c'est un ancrage de plan (guide §2.2, <Picture N>).
  const compo = Array.from({ length: o.composition ?? 0 }, (_, j) => `<Picture ${image + j + 1}>`);
  compo.forEach((c) => definitions.push(`${c} is a composition reference for [Shot 1], defining its viewpoint, framing and subject placement.`));
  compo.forEach((c) => retenues.push(`${c} ([Shot 1] composition): weak_reference - only the viewpoint, framing and placement are followed, not its content.`));
  return [
    'subject_definitions:', ...definitions, '',
    'summary:', `[reference generation] The target video shows ${etiquettes || 'the scene'} in ${nbPlans} shot${nbPlans > 1 ? 's' : ''}${etiquettes ? ', keeping each identity from its reference pictures' : ''}${compo.length ? `, following the composition of ${compo.join(' and ')}` : ''}.`, '',
    'retention_analysis:', ...retenues, '',
    'detailed_description:', style, description, '',
    'overall_soundscape:', son, '',
    'non_diegetic_music:', musique,
  ].join('\n');
}

/** Garde-fou de forme du prompt full-reference (six champs dans l'ordre, étiquettes cohérentes). */
export function validerPromptRef(prompt: string, nbSujets: number, nbImages: number): string[] {
  const erreurs: string[] = [];
  const champs = ['subject_definitions:', 'summary:', 'retention_analysis:', 'detailed_description:', 'overall_soundscape:', 'non_diegetic_music:'];
  const pos = champs.map((c) => prompt.indexOf(c));
  champs.forEach((c, i) => { if (pos[i] < 0) erreurs.push(`champ « ${c.slice(0, -1)} » absent`); });
  if (pos.every((p) => p >= 0) && pos.some((p, i) => i > 0 && p <= pos[i - 1])) erreurs.push('champs dans le désordre');
  for (let k = 1; k <= nbSujets; k++) if (!prompt.includes(`<Subject ${k}>`)) erreurs.push(`<Subject ${k}> absent`);
  for (const m of prompt.matchAll(/<Picture (\d+)>/g)) if (Number(m[1]) > nbImages) erreurs.push(`<Picture ${m[1]}> dépasse les ${nbImages} images fournies`);
  return erreurs;
}
