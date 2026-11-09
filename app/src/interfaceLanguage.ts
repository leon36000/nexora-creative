import type { LangueClient } from '../shared/creationLanguage.js';
import { estRoute3D } from './produit3d.js';

export const LANGUE_INTERFACE_CLE = 'nexora.interfaceLanguage';

type LibellesNavigation = {
  navLabel: string;
  create: string;
  marketing: string;
  library: string;
  explore: string;
  studioMode: string;
  studioTitle: string;
  workshop: string;
  video: string;
  image: string;
  film: string;
  edit: string;
  allTools: string;
  newBadge: string;
  settings: string;
  settingsTitle: string;
  pageTitles: Record<string, string>;
  appNames: Record<string, string>;
  gpu: {
    online: string;
    offline: string;
    roles: Record<string, string>;
    tasks: (count: number) => string;
  };
};

const COPY: Record<LangueClient, LibellesNavigation> = {
  fr: {
    navLabel: 'Navigation principale',
    create: 'Créer',
    marketing: 'Marketing',
    library: 'Bibliothèque',
    explore: 'Explorer',
    studioMode: 'Mode Studio',
    studioTitle: 'Montage expert assisté par l’IA',
    workshop: 'Atelier',
    video: 'Vidéo',
    image: 'Image',
    film: 'Film',
    edit: 'Retouche',
    allTools: 'Tous les outils',
    newBadge: 'Nouveau',
    settings: 'Réglages',
    settingsTitle: 'Modèles et réglages',
    pageTitles: { '/image': 'Image', '/edit': 'Retouche', '/video': 'Vidéo', '/apps': 'Outils' },
    appNames: {
      parler: 'Faire parler',
      prolonger: 'Prolonger',
      raccord: 'Raccord',
      cast: 'Personnages',
      projet: 'Projet long',
      cutout: 'Détourer',
      upscale: 'Netteté et taille',
    },
    gpu: {
      online: 'en ligne',
      offline: 'hors ligne',
      roles: { principal: 'Image · Musique', rtx5090: 'MiniMax H3' },
      tasks: (count) => `${count} tâche${count > 1 ? 's' : ''}`,
    },
  },
  en: {
    navLabel: 'Main navigation',
    create: 'Create',
    marketing: 'Marketing',
    library: 'Library',
    explore: 'Explore',
    studioMode: 'Studio Mode',
    studioTitle: 'AI-assisted expert editing',
    workshop: 'Workshop',
    video: 'Video',
    image: 'Image',
    film: 'Film',
    edit: 'Edit',
    allTools: 'All tools',
    newBadge: 'New',
    settings: 'Settings',
    settingsTitle: 'Models and settings',
    pageTitles: { '/image': 'Image', '/edit': 'Edit', '/video': 'Video', '/apps': 'Tools' },
    appNames: {
      parler: 'Make it speak',
      prolonger: 'Extend',
      raccord: 'Transition',
      cast: 'Characters',
      projet: 'Long-form project',
      cutout: 'Cut out',
      upscale: 'Upscale',
    },
    gpu: {
      online: 'online',
      offline: 'offline',
      roles: { principal: 'Image · Music', rtx5090: 'MiniMax H3' },
      tasks: (count) => `${count} task${count === 1 ? '' : 's'}`,
    },
  },
};

export function libellesNavigation(langue: LangueClient): LibellesNavigation {
  return COPY[langue];
}

/** Les noms de produits fournis par le catalogue restent canoniques et ne sont pas traduits ici. */
export function nomAppNavigation(id: string, nomCanonique: string, langue: LangueClient): string {
  return COPY[langue].appNames[id] ?? nomCanonique;
}

function stockageLocal(): Pick<Storage, 'getItem' | 'setItem'> | null {
  try {
    return typeof window === 'undefined' ? null : window.localStorage;
  } catch {
    return null;
  }
}

export function lireLangueInterface(storage: Pick<Storage, 'getItem' | 'setItem'> | null = stockageLocal()): LangueClient {
  try {
    return storage?.getItem(LANGUE_INTERFACE_CLE) === 'en' ? 'en' : 'fr';
  } catch {
    return 'fr';
  }
}

export function enregistrerLangueInterface(
  langue: LangueClient,
  storage: Pick<Storage, 'getItem' | 'setItem'> | null = stockageLocal(),
): void {
  try {
    storage?.setItem(LANGUE_INTERFACE_CLE, langue);
  } catch {
    // L’interface reste utilisable si le navigateur bloque le stockage local.
  }
}

export function langueContenuPrincipal(path: string, langueInterface: LangueClient): LangueClient {
  return estRoute3D(path) ? langueInterface : 'fr';
}

export function attributLangueDocument(langue: LangueClient): 'fr-CA' | 'en-CA' {
  return langue === 'en' ? 'en-CA' : 'fr-CA';
}
