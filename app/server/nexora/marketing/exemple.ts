/** Entreprise fictive pour les échantillons et les tests : « Plomberie Source-Vive » (Sherbrooke). Aucune coordonnée réelle. */
import { KitMarqueSchema, type KitMarque } from './kit.js';

export const LOGO_EXEMPLE = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 300 90"><path d="M44 8C44 8 18 38 18 56a26 26 0 0 0 52 0C70 38 44 8 44 8Z" fill="#E07A2F"/><path d="M33 58a12 12 0 0 0 12 12" fill="none" stroke="#FBFAF7" stroke-width="5" stroke-linecap="round"/><text x="84" y="44" font-family="Fraunces, serif" font-weight="700" font-size="30" fill="#1F4E5F">Source-Vive</text><text x="85" y="68" font-family="Inter, sans-serif" font-weight="600" font-size="13" letter-spacing="4" fill="#1F4E5F">PLOMBERIE</text></svg>`;

export const KIT_EXEMPLE: KitMarque = KitMarqueSchema.parse({
  nom: 'Source-Vive',
  logo: { svg: LOGO_EXEMPLE },
  couleurs: { primaire: '#1F4E5F', secondaire: '#E6EEF0', accent: '#E07A2F', encre: '#14181B', papier: '#FBFAF7' },
  polices: { titre: 'fraunces', texte: 'inter' },
  ton: { adjectifs: ['chaleureux', 'fiable', 'simple'], interdits: ['meilleur', 'garanti', 'gratuit'] },
  contact: { entreprise: 'Plomberie Source-Vive', nom: 'Camille Tremblay', titre: 'Maîtresse plombière', adresse: '120, rue des Érables, Sherbrooke (Québec)', telephone: '819 555-0142', courriel: 'camille@source-vive.example', web: 'source-vive.example' },
  langue: 'fr',
});

export const TEXTE_EXEMPLE = {
  carte: { accroche: 'Chaque goutte à sa place.' },
  flyer: { accroche: 'Une plomberie qui coule de source.', sousTitre: 'Dépannage, rénovation et entretien à Sherbrooke et dans les environs, par une plombière licenciée.', point1: 'Intervention rapide, rendez-vous précis', point2: 'Prix annoncé avant de commencer', point3: 'Travail propre, chantier rangé', appel: 'Appelez-nous', offre: 'Soumission sur place' },
  accroche: { accroche: 'Désolée de vous avoir manquée !', sousTitre: 'Votre plombière est passée aujourd’hui dans le quartier.', point1: 'Fuites et robinets', point2: 'Chauffe-eau', point3: 'Salles de bain', appel: 'Rappelez-moi quand ça vous convient' },
};
