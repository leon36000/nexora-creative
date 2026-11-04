import { lireLangueClient, type LangueClient } from '../../shared/creationLanguage.js';

export { lireLangueClient };
export type { LangueClient };
export type ModeIdeesCreation = 'video' | 'image' | 'film';

export function messageErreurRendu(langue: LangueClient | undefined, fr: string, en: string, legacy = fr): string {
  return langue === undefined ? legacy : langue === 'en' ? en : fr;
}

const IDEES_FR: Record<ModeIdeesCreation, string[]> = {
  video: ['Un dragon d’obsidienne jaillit d’une mer de nuages d’orage et rugit vers la caméra.', 'Combat de karaté sur un toit trempé de pluie, la nuit, sous des lanternes rouges.', 'Une flotte de vaisseaux surgit de l’hyperespace au-dessus d’une planète à anneaux.', 'Publicité pour un café glacé : gouttes au ralenti, lumière dorée.'],
  image: ['Une guerrière en kimono noir face à un dragon sur une falaise, au crépuscule.', 'Affiche de film : un astronaute seul sur une plage de cendres sous deux lunes.', 'Un renard en papier découpé dans une forêt d’automne, lumière douce.', 'Une ville flottante au-dessus des nuages à l’aube.'],
  film: ['Un livreur à vélo voit une ville entière s’illuminer sur son passage, de l’aube à la nuit.', 'Une flotte surgit de l’hyperespace ; un duel éclate dans un temple au bord d’un volcan.'],
};
const IDEES_EN: Record<ModeIdeesCreation, string[]> = {
  video: ['An obsidian dragon bursts from a storm cloud sea and roars toward the camera.', 'A karate fight on a rain-soaked rooftop at night, lit by red lanterns.', 'A fleet of original ships emerges above a ringed planet.', 'An iced-coffee ad: condensation in slow motion, warm golden light.'],
  image: ['A warrior in a black kimono faces a dragon on a cliff at dusk.', 'A film poster: one astronaut on an ash-covered beach beneath two moons.', 'A paper-cut fox in an autumn forest, lit softly.', 'A floating city above the clouds at dawn.'],
  film: ['A bicycle courier discovers a whole city lighting up along the route from dawn to night.', 'A fleet emerges from hyperspace; a duel breaks out in a temple beside a volcano.'],
};

export function ideesRepliCreation(mode: ModeIdeesCreation, langue: LangueClient | undefined): string[] {
  return langue === 'en' ? IDEES_EN[mode] : IDEES_FR[mode];
}

export function consignesAmeliorationCreation(langue: LangueClient | undefined, mode: ModeIdeesCreation): string {
  if (langue !== 'en') {
    return [
      'Tu es le directeur artistique de Nexora Creative. Réécris l’idée de l’utilisateur en français, en 2 à 4 phrases (90 mots au plus), plus vivante et plus filmable :',
      'sujet précis, action, décor, lumière, ambiance, mouvement de caméra et sons importants.',
      'Garde tous les sujets et toutes les intentions de l’utilisateur, n’en retire aucun, n’invente ni marque, ni personnage connu, ni texte à l’écran.',
      mode === 'image' ? 'C’est pour une image fixe : décris une seule image, pas de mouvement.' : 'C’est pour une vidéo de quelques secondes : une seule action claire.',
      'Réponds en JSON {"texte": "..."} et rien d’autre.',
    ].join(' ');
  }
  return [
    'You are the creative director of Nexora Creative. Rewrite the user’s idea in English in 2 to 4 sentences (90 words maximum), making it vivid and easy to film:',
    'name a clear subject, action, setting, light, mood, camera movement, and important sounds.',
    'Keep every subject and intention; do not remove anything or invent a brand, known character, or on-screen text.',
    mode === 'image' ? 'This is a still image: describe one image, with no movement.' : 'This is a short video: describe one clear action.',
    'Return only JSON {"texte":"..."}.',
  ].join(' ');
}

export function erreurAmeliorationCreation(langue: LangueClient | undefined, type: 'ideeVide' | 'llmAbsent' | 'echec'): string {
  if (langue === 'en') return ({
    ideeVide: 'Write an idea first.',
    llmAbsent: 'The writing assistant is not connected on this server.',
    echec: 'The writing assistant could not improve your prompt. Please try again.',
  })[type];
  return ({
    ideeVide: 'Écris d’abord une idée.',
    llmAbsent: 'L’assistant d’écriture n’est pas branché sur ce poste.',
    echec: 'L’assistant n’a pas pu améliorer ta phrase. Réessaie.',
  })[type];
}

export type ErreurImageCreation = 'descriptionVide' | 'descriptionLongue';
export function erreurImageCreation(langue: LangueClient | undefined, type: ErreurImageCreation): string {
  if (langue === 'en') return ({
    descriptionVide: 'Describe the image you want.',
    descriptionLongue: 'Description is too long (4,000 characters maximum).',
  })[type];
  return ({
    descriptionVide: 'Décris l’image que tu veux.',
    descriptionLongue: 'Description trop longue (4 000 caractères au plus).',
  })[type];
}
