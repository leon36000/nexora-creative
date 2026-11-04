/**
 * Personnages @ (équivalent Soul ID) : une fiche de personnage dessinée par Qwen-Image (fond gris uni, corps entier à
 * gauche, gros plan à droite), découpée en deux références, enregistrée comme élément nommé (Cast, kind « character »).
 * `@nom` dans un prompt se résout vers cet élément ; en vidéo, les références partent dans MiniMax H3 Ref2VA
 * (point de contrôle ref2va de la recette « h3-max ») au format « full-reference » du guide officiel.
 */

import { STYLE_NEUTRE, styleNonPhotographiqueDemande } from './liveAction.js';

export const LARGEUR_FICHE = 1792;
export const HAUTEUR_FICHE = 1024;

/** Prompt Qwen-Image de la fiche standard ; `descriptionEn` décrit le personnage (apparence, tenue, âge). */
export function promptFiche(descriptionEn: string): string {
  const style = styleNonPhotographiqueDemande(descriptionEn)
    ? 'Crisp, consistent character reference sheet that preserves the requested illustrated or animated medium.'
    : 'Photorealistic, sharp focus, natural skin texture.';
  return [
    'Professional character reference sheet on a perfectly plain, uniform neutral grey studio background, soft even lighting, no shadows on the floor.',
    'The image is split in two equal side-by-side panels with the SAME character in both, identical face, hair, skin tone and outfit.',
    'LEFT panel: the full body, standing straight, facing the camera, arms relaxed, feet visible, head to toe in frame.',
    'RIGHT panel: a tight close-up portrait of the face and shoulders, looking at the camera, neutral expression.',
    `${style} No text, no labels, no logos, no watermark, no props, no other people.`,
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

/** Réserve une entrée à la composition et conserve chaque identité quand les quatre ports sont saturés. */
export function referencesAvecComposition(sujets: SujetRef[], jetons: string[], composition: string): { sujets: SujetRef[]; jetons: string[] } {
  const total = sujets.reduce((n, s) => n + s.images, 0);
  if (sujets.length > 3 || total !== jetons.length || sujets.some((s) => !Number.isInteger(s.images) || s.images < 1)) {
    throw new Error('Invalid subject references for composition (at most three subjects, matching image groups required)');
  }
  const reduire = total > 3;
  let offset = 0;
  const selection: string[] = [];
  const retenus = sujets.map((s) => {
    const images = reduire ? 1 : s.images;
    selection.push(...jetons.slice(offset, offset + images));
    offset += s.images;
    return { ...s, images };
  });
  return { sujets: retenus, jetons: [...selection, composition] };
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
  /** Style de la fiche, déplacé avant le premier plan en Ref2VA. */
  style?: string;
}

const minuscule = (t: string) => t.replace(/^\s*([A-Z])(?![A-Z])/, (m) => m.toLowerCase());

export function convertirEnPromptRef(prompt: string, sujets: SujetRef[], o: OptionsRef = {}): string {
  const texte = prompt.replace(/\r\n/g, '\n').trim();
  const iDesc = texte.indexOf('integrated_multimodal_description:');
  const iSon = texte.indexOf('overall_soundscape:');
  const iMus = texte.indexOf('non_diegetic_music:');
  if (iDesc < 0 || iSon < 0 || iMus < 0 || (!sujets.length && !o.composition)) return texte;
  let description = texte.slice(iDesc + 'integrated_multimodal_description:'.length, iSon).trim();
  // Les répliques et les textes visibles demandés restent intouchables, y compris leurs noms propres.
  const repliques: string[] = [];
  description = description.replace(/<d>[\s\S]*?<\/d>|"[^"\n]*"|«[^»\n]*»|“[^”\n]*”/g, (d) => { repliques.push(d); return `@@DIALOGUE${repliques.length - 1}@@`; });
  const son = texte.slice(iSon + 'overall_soundscape:'.length, iMus).trim();
  const musique = texte.slice(iMus + 'non_diegetic_music:'.length).trim() || 'N/A';

  // Le guide Ref2VA place le style avant le premier plan, sans changer la photographie choisie.
  const prefixe = description.match(/^\[Shot 1\]\s*([^.!?]+[.!?])\s*/)?.[1];
  const style = o.style?.trim().replace(/[.\s]+$/, '') || prefixe?.trim().replace(/[.\s]+$/, '') || STYLE_NEUTRE;
  if (o.style) {
    const debutStyle = new RegExp(`^(\\[Shot 1\\]\\s*)${echapper(o.style.trim().replace(/[.\s]+$/, ''))}[,.]?\\s*`, 'i');
    description = description.replace(debutStyle, '$1');
  } else if (prefixe) {
    description = description.replace(prefixe, '');
  }

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
  const shots = [...description.matchAll(/\[Shot (\d+)\]([\s\S]*?)(?=\[Shot \d+\]|$)/g)];
  const nbPlans = shots.length || 1;
  sujets.forEach((s, k) => {
    const label = `<Subject ${k + 1}>`;
    const presents = shots.filter((m) => m[2].includes(label)).map((m) => `[Shot ${m[1]}]`);
    if (presents.length) retenues.push(`${label} (appears in ${presents.join(', ')}): fully_preserved - the identity, face, hair, build and outfit of ${s.nom} from the reference pictures are retained.`);
  });
  description = description.replace(/@@DIALOGUE(\d+)@@/g, (_, n) => repliques[Number(n)]);
  const etiquettes = sujets.map((_, k) => `<Subject ${k + 1}>`).join(' and ');
  // « Montre-moi » : une image de composition n'est pas un sujet, c'est un ancrage de plan (guide §2.2, <Picture N>).
  const compo = Array.from({ length: o.composition ?? 0 }, (_, j) => `<Picture ${image + j + 1}>`);
  compo.forEach((c) => definitions.push(`${c} is a composition reference for [Shot 1], defining its viewpoint, framing and subject placement.`));
  compo.forEach((c) => retenues.push(`${c} ([Shot 1] composition): weak_reference - only the viewpoint, framing and placement are followed, not its content.`));
  return [
    'subject_definitions:', ...definitions, '',
    'summary:', `[reference generation] The target video shows ${etiquettes || 'the scene'} in ${nbPlans} shot${nbPlans > 1 ? 's' : ''}${etiquettes ? ', keeping each identity from its reference pictures' : ''}${compo.length ? `, following the composition of ${compo.join(' and ')}` : ''}.`, '',
    'retention_analysis:', ...retenues, '',
    'detailed_description:', `${style}.`, description, '',
    'overall_soundscape:', son, '',
    'non_diegetic_music:', musique,
  ].join('\n');
}

/** Garde-fou de forme du prompt full-reference (six champs dans l'ordre, étiquettes cohérentes). */
export function validerPromptRef(prompt: string, nbSujets: number, nbImages: number): string[] {
  const erreurs: string[] = [];
  if (!Number.isInteger(nbSujets) || nbSujets < 0 || nbSujets > 4) erreurs.push('nombre de sujets invalide (0 à 4)');
  if (!Number.isInteger(nbImages) || nbImages < 1 || nbImages > 4) erreurs.push('nombre d’images invalide (1 à 4)');
  const champs = ['subject_definitions:', 'summary:', 'retention_analysis:', 'detailed_description:', 'overall_soundscape:', 'non_diegetic_music:'];
  const pos = champs.map((c) => prompt.indexOf(c));
  champs.forEach((c, i) => { if (pos[i] < 0) erreurs.push(`champ « ${c.slice(0, -1)} » absent`); });
  if (pos.every((p) => p >= 0) && pos.some((p, i) => i > 0 && p <= pos[i - 1])) erreurs.push('champs dans le désordre');
  const definitions = pos[0] >= 0 ? prompt.slice(pos[0], pos[1] > pos[0] ? pos[1] : undefined) : '';
  const labels = new Set([...definitions.matchAll(/<(Subject|Picture) (\d+)>/g)].map((m) => m[0]));
  for (const m of prompt.matchAll(/<(Subject|Picture) (\d+)>/g)) {
    if (!labels.has(m[0])) erreurs.push(`${m[0]} sans définition ni source définie`);
    if (m[1] === 'Subject' && (Number(m[2]) < 1 || Number(m[2]) > nbSujets)) erreurs.push(`${m[0]} dépasse les ${nbSujets} sujets fournis`);
  }
  for (let k = 1; k <= nbSujets; k++) if (!prompt.includes(`<Subject ${k}>`)) erreurs.push(`<Subject ${k}> absent`);
  for (const m of prompt.matchAll(/<Picture (\d+)>/g)) if (Number(m[1]) < 1 || Number(m[1]) > nbImages) erreurs.push(`<Picture ${m[1]}> dépasse les ${nbImages} images fournies`);
  return erreurs;
}
