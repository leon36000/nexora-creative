/**
 * Catalogue Nexora Creative (français) : seulement ce qui fonctionne avec les moteurs du produit (MiniMax H3,
 * Qwen-Image, MiniMax-Music3, SAM 3, SeedVR2, TRELLIS.2). Les apps d'OpenField qui reposaient sur LTX-2.x (Mirror,
 * Reshoot, Effects, Stage, HDR, Swap, Speak, Add sound, Dream, Director LTX) ne sont pas listées : un bouton
 * « indisponible » est pire que pas de bouton. Extend et Transitions sont refaits sur H3 (Prolonger, Raccord).
 * Le catalogue d'origine (catalog.ts, APPS) reste intact pour le serveur MCP et ses vérifications.
 */
import { presetById, type AppDef } from '../catalog';

export const CATEGORIES_NEXORA = [
  { id: 'all', label: 'Tout' },
  { id: 'create', label: 'Créer' },
  { id: 'direct', label: 'Réaliser' },
  { id: 'transform', label: 'Retoucher' },
  { id: 'finish', label: 'Finir' },
] as const;

export const APPS_NEXORA: AppDef[] = [
  { id: 'producteur', name: 'Producteur IA', blurb: 'Un objectif en une phrase : l’IA découpe, chiffre, tourne, contrôle chaque plan et assemble.', route: '/', icon: 'sparkle', hue: 18, cat: 'create', badge: 'new', cover: 'golden', clip: '/apps/scene.mp4' },
  { id: 'video', name: 'Vidéo', blurb: 'Une phrase devient un plan MiniMax H3 avec son, avec ou sans image de départ.', route: '/?mode=video', icon: 'video', hue: 32, cat: 'create', badge: 'top', cover: 'embers', clip: '/apps/video.mp4' },
  { id: 'image', name: 'Image', blurb: 'Des images Qwen-Image d’une phrase ; anime celle que tu préfères en un clic.', route: '/?mode=image', icon: 'image', hue: 200, cat: 'create', cover: 'golden', clip: '/apps/image.mp4' },
  { id: 'film', name: 'Film', blurb: 'Une idée devient un storyboard relisible, tourné plan par plan et assemblé.', route: '/?mode=film', icon: 'film', hue: 18, cat: 'direct', cover: 'noir', clip: '/apps/director.mp4' },
  { id: 'parler', name: 'Faire parler', blurb: 'Ta photo et une réplique : le personnage dit la phrase, voix synchronisée par H3.', route: '/?mode=video&depart=photo', icon: 'person', hue: 12, cat: 'create', cover: 'handheld' },
  { id: 'prolonger', name: 'Prolonger', blurb: 'Continue un clip de 5 ou 10 s depuis sa dernière image, même lumière, même mouvement.', route: '/prolonger', icon: 'plus', hue: 24, cat: 'finish', badge: 'new', cover: 'aerial-pull', clip: '/apps/extend.mp4' },
  { id: 'raccord', name: 'Raccord', blurb: 'Relie deux clips par un plan de transition qui part de l’un et arrive sur l’autre.', route: '/prolonger?mode=raccord', icon: 'loop', hue: 300, cat: 'finish', badge: 'new', cover: 'whip-pan', clip: '/apps/transition.mp4' },
  { id: 'cast', name: 'Personnages', blurb: 'Enregistre un personnage, un objet ou un lieu et appelle-le avec @ dans tes images.', route: '/cast', icon: 'person', hue: 28, cat: 'direct', cover: 'handheld', clip: '/apps/cast.mp4' },
  { id: 'projet', name: 'Projet long', blurb: 'Un scénario, une bible de continuité, le coût du projet entier annoncé, un tournage par lots, montage dans le Mode Studio.', route: '/projet', icon: 'film', hue: 14, cat: 'direct', badge: 'new', cover: 'noir' },
  { id: 'edit', name: 'Retouche', blurb: 'Change une image d’une phrase ; peins un masque pour garder le reste intact.', route: '/edit', icon: 'wand', hue: 250, cat: 'transform', cover: 'ink-bloom' },
  { id: 'angle', name: 'Nouvel angle', blurb: 'La même scène vue d’autres positions de caméra.', route: '/edit?app=angle', icon: 'orbit', hue: 210, cat: 'transform', cover: 'orbit-right' },
  { id: 'coverage', name: 'Couverture', blurb: 'Neuf plans d’un même moment, du plan large au très gros plan.', route: '/edit?app=coverage', icon: 'grid', hue: 150, cat: 'direct', cover: 'truck-left' },
  { id: 'pushin', name: 'Rapprocher', blurb: 'La caméra avance vers le sujet, par étapes, jusqu’au détail.', route: '/edit?app=pushin', icon: 'search', hue: 40, cat: 'direct', cover: 'push-in' },
  { id: 'next', name: 'Moment suivant', blurb: 'Quatre suites possibles du moment, dans le même monde.', route: '/edit?app=next', icon: 'film', hue: 205, cat: 'direct', cover: 'storm' },
  { id: 'relight', name: 'Éclairage', blurb: 'Déplace la lumière et change sa couleur, une ambiance par résultat.', route: '/edit?app=relight', icon: 'light', hue: 38, cat: 'transform', cover: 'golden' },
  { id: 'expand', name: 'Agrandir le cadre', blurb: 'Passe à un autre format et peins ce qui était hors champ.', route: '/edit?app=expand', icon: 'aspect', hue: 220, cat: 'transform', cover: 'pull-back' },
  { id: 'cutout', name: 'Détourer', blurb: 'Sors le sujet d’une image ou d’un clip, sur fond transparent ou nouveau.', route: '/cutout', icon: 'cutout', hue: 120, cat: 'transform', cover: 'static' },
  { id: 'upscale', name: 'Netteté et taille', blurb: 'Rends une image ou un clip plus net et plus grand (Real-ESRGAN, SeedVR2).', route: '/upscale', icon: 'up', hue: 50, cat: 'finish', cover: 'rack-focus', clip: '/apps/upscale.mp4' },
  { id: 'object', name: 'Objet 3D', blurb: 'Une image devient un modèle 3D texturé, à tourner ou télécharger.', route: '/object', icon: 'cube', hue: 30, cat: 'create', cover: 'turntable', clip: '/apps/object.mp4' },
];

/** Modèles prêts à produire (façon Higgsfield) : un clic envoie l'objectif au Producteur, qui propose plan et devis. */
export interface ModeleProduction { id: string; nom: string; objectif: string; clip: string; cat: 'pub' | 'social' | 'film' }
export const MODELES: ModeleProduction[] = [
  { id: 'pub-commerce', nom: 'Pub de commerce local', cat: 'pub', clip: '/presets/golden.mp4', objectif: 'Une pub verticale de 15 s pour mon commerce de quartier : vitrine au matin, produit en gros plan, sourire du personnel, carton final avec le nom. Musique chaleureuse.' },
  { id: 'lancement-produit', nom: 'Lancement de produit', cat: 'pub', clip: '/presets/dolly-zoom.mp4', objectif: 'Un teaser de 15 s pour le lancement d’un nouveau produit : révélation dramatique en studio, lumière de contre-jour, gros plans sur les détails, carton « Bientôt disponible ». Format carré.' },
  { id: 'restaurant', nom: 'Plat signature', cat: 'social', clip: '/presets/embers.mp4', objectif: 'Une vidéo verticale de 10 s pour un restaurant : le plat signature au ralenti, vapeur, flammes en cuisine, réplique du chef « Goûtez-moi ça ». Musique rythmée.' },
  { id: 'immobilier', nom: 'Visite immobilière', cat: 'pub', clip: '/presets/crane-up.mp4', objectif: 'Une vidéo paysage de 20 s pour une propriété à vendre : façade au coucher du soleil en plan aérien, salon lumineux, cuisine, terrasse ; carton final « Visite sur rendez-vous ». Musique douce.' },
  { id: 'evenement', nom: 'Annonce d’événement', cat: 'social', clip: '/presets/neon-rain.mp4', objectif: 'Une annonce verticale de 15 s pour une soirée : foule sous des lumières néon, DJ, confettis au ralenti, carton avec la date. Musique électro énergique.' },
  { id: 'court-metrage', nom: 'Court métrage', cat: 'film', clip: '/presets/fog-roll.mp4', objectif: 'Un court film de 30 s : une renarde traverse une ville enneigée la nuit et découvre une lanterne magique, ambiance conte, musique orchestrale.' },
  { id: 'bande-annonce', nom: 'Bande-annonce épique', cat: 'film', clip: '/presets/aerial-pull.mp4', objectif: 'Une bande-annonce de 30 s en paysage : une flotte surgit au-dessus d’une planète, un pilote se prépare, un duel éclate ; cartons « Cet été » et titre. Musique épique.' },
  { id: 'bienvenue', nom: 'Vidéo de bienvenue', cat: 'social', clip: '/presets/handheld.mp4', objectif: 'Une vidéo de bienvenue de 10 s pour mon cabinet : accueil chaleureux, salle lumineuse, la professionnelle dit « Bienvenue, on prend soin de vous ». Paysage.' },
];

/** Mouvements de caméra cliquables du mode Vidéo (vignettes : public/presets/<id>.mp4). Texte : catalogue d'OpenField. */
const NOMS_CAMERA: Record<string, string> = {
  'push-in': 'Approche', 'pull-back': 'Recul révélateur', 'orbit-left': 'Orbite gauche', 'orbit-right': 'Orbite droite', 'crane-up': 'Grue montante',
  'truck-left': 'Travelling latéral', handheld: 'Caméra à l’épaule', static: 'Plan fixe', 'rack-focus': 'Bascule de point', 'dolly-zoom': 'Vertigo',
  'crash-zoom': 'Zoom choc', 'fpv-dive': 'Plongée drone', 'whip-pan': 'Panoramique filé', 'aerial-pull': 'Envol aérien', 'freeze-orbit': 'Temps figé', snorricam: 'Caméra harnais',
};
export const CAMERAS = Object.entries(NOMS_CAMERA).map(([id, nom]) => ({ id, nom, texte: presetById(id).text, clip: `/presets/${id}.mp4` }));
