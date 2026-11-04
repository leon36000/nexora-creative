/**
 * Banc du « LLM qui booste le tout » : 32 demandes réalistes, écrites à l'arrache comme un client les tape (fautes,
 * québécois, flou, majuscules, sans ponctuation). Chaque demande garde ce que le client a choisi dans l'interface
 * (durée, format) ; `doit` liste ce qu'un bon prompt ne peut pas perdre (contrôlé par le juge, jamais montré au LLM).
 */
export interface DemandeBanc {
  id: string;
  famille: 'pub' | 'film' | 'vfx' | 'produit' | 'cours' | 'social' | 'clip';
  intention: string;
  duree: 5 | 10 | 15;
  format: '16:9' | '9:16' | '1:1';
  replique?: string;
  /** Éléments que le prompt final doit garder (pour le juge). */
  doit: string[];
}

export const DEMANDES: DemandeBanc[] = [
  // Publicités
  { id: 'pub-poutine', famille: 'pub', duree: 10, format: '9:16', intention: 'pub pour ma cantine a levis, poutine qui coule du fromage en grain, faut que ca donne faim', doit: ['poutine', 'fromage en grains qui fond ou coule', 'casse-croûte / cantine', 'appétissant'] },
  { id: 'pub-garage', famille: 'pub', duree: 10, format: '16:9', intention: 'garage de mecanique a sherbrooke on change les pneus dhiver vite fait bien fait, un char qui rentre dans le garage pis ressort', doit: ['garage de mécanique', 'pneus d’hiver', 'une voiture entre puis ressort', 'rapidité'] },
  { id: 'pub-cafe-glace', famille: 'pub', duree: 5, format: '9:16', intention: 'cafe glacé caramel, gouttes, lumiere dorée, ca doit etre beau comme starbucks mais pas starbucks', doit: ['café glacé caramel', 'gouttes', 'lumière dorée', 'aucune marque'] },
  { id: 'pub-fleuriste', famille: 'pub', duree: 10, format: '1:1', intention: 'fleuriste fete des meres bouquet de pivoines roses, une madame sourit quand on lui donne', doit: ['bouquet de pivoines roses', 'une femme reçoit le bouquet et sourit', 'fleuriste'] },
  { id: 'pub-salle-sport', famille: 'pub', duree: 10, format: '9:16', intention: 'gym ouvert 24h, un gars qui fait du deadlift a 3h du matin, motivant, sueur, lumiere neon', doit: ['soulevé de terre', 'la nuit (3 h)', 'sueur', 'néons', 'motivant'] },
  { id: 'pub-cabane', famille: 'pub', duree: 15, format: '16:9', intention: 'cabane a sucre familiale, tire sur la neige, des enfants rient, feu de bois, ambiance printemps au quebec', replique: 'Venez sucrer le bec en famille!', doit: ['tire d’érable sur la neige', 'enfants qui rient', 'feu de bois', 'printemps québécois', 'réplique mot pour mot'] },
  // Films (plusieurs plans dans une génération)
  { id: 'film-detective', famille: 'film', duree: 15, format: '16:9', intention: 'film noir un detective sous la pluie trouve une lettre sur un cadavre, il regarde au loin, suspense', doit: ['détective', 'pluie, nuit', 'lettre trouvée sur un corps', 'il regarde au loin', 'plusieurs plans cohérents'] },
  { id: 'film-retrouvailles', famille: 'film', duree: 10, format: '16:9', intention: 'deux vieux amis se retrouve dans une gare apres 30 ans, ils se serrent dans les bras, emotion', replique: 'T’as pas changé, mon vieux.', doit: ['deux hommes âgés', 'gare', 'accolade', 'émotion', 'réplique mot pour mot'] },
  { id: 'film-foret', famille: 'film', duree: 15, format: '16:9', intention: 'une ptite fille perdue dans la foret la nuit voit des lucioles qui la guide vers sa maison', doit: ['petite fille', 'forêt la nuit', 'lucioles qui la guident', 'maison au bout', 'plusieurs plans, même fillette'] },
  { id: 'film-western', famille: 'film', duree: 10, format: '16:9', intention: 'duel western midi soleil deux cowboys main sur le revolver, gros plan sur les yeux', doit: ['deux cow-boys', 'midi, plein soleil', 'mains sur les revolvers', 'gros plan sur les yeux'] },
  { id: 'film-cuisine', famille: 'film', duree: 10, format: '9:16', intention: 'grand mere qui fait des tourtieres dans sa cuisine, sa petite fille l aide, chaleureux', doit: ['grand-mère', 'tourtières', 'petite-fille qui aide', 'cuisine chaleureuse'] },
  // Effets spéciaux
  { id: 'vfx-dragon-chateau', famille: 'vfx', duree: 10, format: '16:9', intention: 'un dragon noir enorme qui crache du feu sur un chateau medieval, les soldats courent, epique', doit: ['dragon noir énorme', 'crache du feu', 'château médiéval', 'soldats qui fuient', 'épique'] },
  { id: 'vfx-dragon-ville', famille: 'vfx', duree: 5, format: '16:9', intention: 'dragon qui atterit sur le pont jacques cartier a montreal la nuit', doit: ['dragon', 'atterrit sur un grand pont', 'Montréal la nuit'] },
  { id: 'vfx-explosion-usine', famille: 'vfx', duree: 5, format: '16:9', intention: 'grosse explosion d une usine abandonée, boule de feu, debris, onde de choc, ralenti', doit: ['usine abandonnée', 'boule de feu', 'débris', 'onde de choc', 'ralenti'] },
  { id: 'vfx-hero-explosion', famille: 'vfx', duree: 5, format: '16:9', intention: 'le heros marche vers la camera pendant que ca explose en arriere de lui il se retourne pas', doit: ['héros qui marche vers la caméra', 'explosion derrière lui', 'il ne se retourne pas'] },
  { id: 'vfx-bataille-spatiale', famille: 'vfx', duree: 10, format: '16:9', intention: 'bataille spatiale enorme des centaines de vaisseaux, lasers, un croiseur explose au dessus d une planete', doit: ['bataille spatiale', 'nombreux vaisseaux', 'tirs laser', 'un croiseur explose', 'au-dessus d’une planète'] },
  { id: 'vfx-chasseur', famille: 'vfx', duree: 5, format: '16:9', intention: 'cockpit d un chasseur spatial, le pilote esquive des asteroides, vue de l interieur', doit: ['cockpit de chasseur spatial', 'pilote', 'esquive des astéroïdes', 'vue intérieure'] },
  { id: 'vfx-sabre', famille: 'vfx', duree: 10, format: '16:9', intention: 'duel au sabre laser entre un chevalier en robe brune et un sith rouge dans une usine en feu', doit: ['duel d’épées d’énergie', 'combattant en robe brune', 'adversaire à lame rouge', 'usine en feu', 'aucune marque ni personnage protégé'] },
  { id: 'vfx-sabre-pluie', famille: 'vfx', duree: 5, format: '9:16', intention: 'samourai avec un sabre lumineux bleu sous la pluie neon, il coupe une goute en deux', doit: ['samouraï', 'sabre lumineux bleu', 'pluie, néons', 'tranche une goutte'] },
  { id: 'vfx-tsunami', famille: 'vfx', duree: 5, format: '16:9', intention: 'vague geante tsunami qui arrive sur new york, les gens courent', doit: ['vague géante', 'grande ville côtière', 'des gens qui fuient'] },
  { id: 'vfx-robot', famille: 'vfx', duree: 10, format: '16:9', intention: 'robot geant de 50 metres qui se reveille dans le port de quebec, brume matinale', doit: ['robot géant (50 m)', 'se réveille', 'port de Québec', 'brume du matin'] },
  // Produits
  { id: 'prod-montre', famille: 'produit', duree: 5, format: '1:1', intention: 'montre de luxe en or qui tourne sur elle meme fond noir reflets', doit: ['montre de luxe en or', 'tourne sur elle-même', 'fond noir', 'reflets'] },
  { id: 'prod-parfum', famille: 'produit', duree: 5, format: '9:16', intention: 'flacon de parfum dans l eau, eclaboussures, rose, tres haut de gamme', doit: ['flacon de parfum', 'eau, éclaboussures', 'rose', 'haut de gamme'] },
  { id: 'prod-soulier', famille: 'produit', duree: 5, format: '16:9', intention: 'running shoe blanc qui explose en morceau pis se reconstruit', doit: ['chaussure de course blanche', 'se décompose en morceaux', 'se reconstruit'] },
  { id: 'prod-biere', famille: 'produit', duree: 5, format: '9:16', intention: 'canette de biere de micro brasserie qui sort d un lac gelé, givre, condensation', doit: ['canette de bière', 'sort d’un lac gelé', 'givre', 'condensation'] },
  // Cours et explications
  { id: 'cours-volcan', famille: 'cours', duree: 10, format: '16:9', intention: 'expliquer aux enfants comment un volcan erupte, coupe du volcan, magma qui monte', doit: ['coupe d’un volcan', 'magma qui monte', 'éruption', 'clair pour des enfants'] },
  { id: 'cours-cellule', famille: 'cours', duree: 10, format: '16:9', intention: 'video pour mon cours de bio: dans une cellule, les mitochondries produisent de l energie', doit: ['intérieur d’une cellule', 'mitochondries', 'production d’énergie', 'pédagogique'] },
  { id: 'cours-prof', famille: 'cours', duree: 10, format: '16:9', intention: 'une prof devant un tableau qui explique le theoreme de pythagore', replique: 'Le carré de l’hypoténuse est égal à la somme des carrés des deux autres côtés.', doit: ['enseignante', 'tableau', 'théorème de Pythagore', 'réplique mot pour mot'] },
  // Réseaux sociaux
  { id: 'social-chat', famille: 'social', duree: 5, format: '9:16', intention: 'mon chat qui fait du skate tiktok drole', doit: ['chat', 'planche à roulettes', 'drôle', 'vertical'] },
  { id: 'social-unboxing', famille: 'social', duree: 10, format: '9:16', intention: 'unboxing d un telephone, mains, reaction wow, style influenceuse', doit: ['déballage d’un téléphone', 'mains', 'réaction émerveillée', 'style influenceuse'] },
  { id: 'social-texte', famille: 'social', duree: 5, format: '9:16', intention: 'video pour insta avec ecrit "SOLDES -50%" en gros sur une vitrine de boutique de vetements', doit: ['vitrine de boutique de vêtements', 'texte exact « SOLDES -50% »'] },
  // Clip musical
  { id: 'clip-rap', famille: 'clip', duree: 10, format: '9:16', intention: 'clip rap dans une ruelle de montreal l hiver, fumée, gars en doudoune qui rap face a la camera', doit: ['rappeur en doudoune', 'ruelle de Montréal l’hiver', 'fumée / vapeur', 'face caméra'] },
];
