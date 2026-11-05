import type { LangueClient } from '../shared/creationLanguage';

export const MESH_COPY = {
  fr: {
    language: 'Langue',
    intro: 'Une image, plusieurs vues ou une phrase deviennent un modèle 3D texturé : à tourner, à exporter (GLB, OBJ, STL, 3MF, USDZ) ou à poser dans une scène. Le calcul utilise nos GPU.',
    startingPoint: 'Point de départ', imageTo3d: 'Image → 3D', multiView: 'Multi-vues', textTo3d: 'Texte → 3D',
    object: 'L’objet', objectDescription: 'Une chaise en bois clair aux pieds fuselés, un robot jouet en métal rouge…',
    text3dIntro: 'Crée d’abord une photo de produit de l’objet seul, reconstruit-le en 3D, puis vérifie ses quatre côtés. Une relance au maximum si le contrôle est sévère.',
    frontView: 'Vue de face', image: 'Image', addFrontView: 'Ajoute une image de face', frontViewHint: 'Un seul sujet, visible en entier, sur fond uni donne les meilleurs résultats.',
    leftView: 'Vue de gauche', backView: 'Vue de dos', rightView: 'Vue de droite', optional: ' (facultatif)',
    addLeftView: 'Ajoute une vue de gauche', addBackView: 'Ajoute une vue de dos', addRightView: 'Ajoute une vue de droite',
    sameObjectLeft: 'Le même objet, vu de son côté gauche.', sameObjectBack: 'Le même objet, vu de derrière.', sameObjectRight: 'Le même objet, vu de son côté droit.',
    multiViewInfo: (max: number) => `Ajoute au moins une autre vue du même objet. Jusqu’à ${max} vues selon la limite actuelle du serveur. Brouillon seulement.`,
    viewLimitLoading: 'Vérification de la limite de vues auprès du serveur…',
    viewLimitUnavailable: (max: number) => `Limite du serveur non confirmée. La sélection est limitée à ${max} vues pour le moment.`,
    viewLimitExceeded: (max: number) => `Cette sélection dépasse la limite actuelle de ${max} vues. Retire une vue avant de continuer.`,
    multiViewUnavailable: 'La reconstruction multivue n’est pas disponible sur ce serveur.',
    estimateUnavailable: 'Estimation indisponible',
    detail: 'Détail', draft: 'Brouillon', high: 'Haute qualité', credits: 'crédits', decreaseCount: 'Réduire le nombre de prises', increaseCount: 'Augmenter le nombre de prises', draftInfo: 'Jusqu’à 150 000 faces, textures 2K. Environ 40 secondes sur GB10. Vérifie la forme ici.',
    highInfo: 'Jusqu’à 400 000 faces, textures 4K, normales et occlusion ambiante précalculées. Environ 3 minutes sur GB10.',
    original: 'Original', cutout: 'Détouré', cutoutAlt: 'Sujet détouré, sans arrière-plan', removeBackground: 'Retirer l’arrière-plan',
    removeBackgroundAgain: 'Retirer l’arrière-plan de nouveau', removingBackground: 'Suppression de l’arrière-plan…',
    useThisCutout: 'La 3D reprend exactement ce détourage.', useOriginal: 'La 3D utilise l’image originale.',
    cutFirst: 'Détourer d’abord le sujet', cutoutBehavior: 'BiRefNet repère le sujet et enlève l’arrière-plan.',
    transparencyBehavior: 'Utilise la transparence de l’image. Désactive cette option seulement pour un PNG déjà détouré.',
    eachTakeNewSeed: 'Chaque prise utilise une nouvelle graine.',
    create3d: 'Créer en 3D', inProgress: 'En cours…', buildingModels: (n: number) => `${n} modèle${n > 1 ? 's' : ''} en construction`,
    modelFromViews: (n: number) => `Modèle depuis ${n} vues`,
    loading: 'Chargement…', uploadFailure: 'Impossible de charger cette image. Réessaie.', takeFailure: 'Impossible de charger cette prise. Réessaie.',
    requestFailure: 'La demande n’a pas abouti. Vérifie la source et réessaie.', backgroundFailure: 'Impossible de retirer l’arrière-plan. Réessaie.',
    animationFailure: 'Impossible de préparer cette vue pour une animation. Attends que le modèle soit chargé, puis réessaie.',
    emptyTitle: 'en volume', addStill: 'Ajouter une image', addStillHelp: 'Ou choisis Créer en 3D sur une image de la bibliothèque.',
    chooseDetail: 'Choisir le détail', chooseDetailHelp: 'Brouillon pour vérifier la forme, haute qualité pour conserver le modèle.',
    turnModel: 'Faire tourner', turnModelHelp: 'Fais-le pivoter, télécharge le GLB ou place-le dans une scène.',
    models: 'Modèles', downloadGlb: 'Télécharger GLB', modelViewerUnavailable: 'Ce navigateur ne peut pas afficher le modèle. Télécharge le GLB pour l’ouvrir ailleurs.', modelLoading: 'Chargement du modèle…', modelViewerLabel: 'Aperçu 3D du modèle', modelTriangles: (n: string) => `${n} triangles`, modelLooks: 'Apparence du modèle', modelSubject: 'Image source du modèle', recreate: 'Recréer', recreateSent: 'Demande de recréation envoyée.',
    recreateUnconfirmed: 'Impossible de confirmer l’envoi de la demande de recréation. Vérifie tes prises avant de réessayer.', delete: 'Supprimer',
    from: 'Depuis', textured: 'Texturé', clay: 'Argile', wire: 'Fil de fer',
    facesAndTextures: (quality: string, faces: string, px: string) => `${quality} · jusqu’à ${faces} faces · textures ${px}`,
    open: 'Ouvrir', animateInVideo: 'Animer en vidéo', darkStudio: 'Studio sombre', lightStudio: 'Studio clair', blueNight: 'Nuit bleue',
    capture: 'Capture…', animateWithH3: 'Animer avec H3', viewNotReady: 'La vue 3D n’est pas prête.',
    textReferenceImage: 'Image de référence', textModel: 'Modèle 3D', textCheck: 'Contrôle sur quatre côtés', secondAttempt: ' (2e essai)',
    judge: 'Juge', failed: 'Échec.', judgeUnavailable: 'Le juge n’a pas répondu.', retryWithNewSeed: 'Refaire avec une autre graine',
    languageSwitch: 'Langue de l’interface', french: 'Français', english: 'English',
    cardStep: 'Étape', cardRendering: 'Rendu en cours', cardWaiting: 'En attente du moteur', cardQueued: 'En file d’attente',
    cardFailed: 'Échec de la prise', cardFailedHelp: 'Cette prise n’a pas abouti. Vérifie la source et réessaie.', cardPlans: 'plans', cardVideo: 'vidéo',
    cardSeamless: 'Sans raccord', cardSeam: 'Raccord visible', cardSeamTitle: (ratio: number) => `Point de raccord : ${ratio}× un pas d’image`,
    reportLoading: 'Analyse du maillage…', reportFailure: 'L’analyse n’a pas abouti. Les exports de cette section sont indisponibles. Réessaie plus tard.',
    exportUnavailable: 'Export indisponible', export: 'Exporter', exportFormat: 'Format d’export', numberOfFaces: 'Nombre de faces', vertices: 'sommets',
    helpGlb: 'Le modèle tel quel, textures PBR comprises (web, Stage, Blender, jeux).',
    helpObj: 'Un zip : .obj, .mtl et la texture de couleur (logiciels 3D).',
    helpStl: 'Sans couleur, en millimètres, posé à plat : impression 3D.',
    help3mf: 'Sans couleur, en millimètres : trancheurs récents (Bambu, Prusa, Cura).',
    helpUsdz: 'Apple : Quick Look, Vision Pro, Reality Composer.',
    serverNoCredits: 'Calculé par le serveur : 0 crédit. La décimation garde les textures.',
    pbrMaps: 'Cartes PBR', openMap: (name: string) => `Ouvrir la carte « ${name} »`, mapAlt: (name: string) => `Carte ${name}`,
    turntable: 'Tournette', animatedGif: 'GIF animé', qualityCheck: 'Contrôle qualité',
    readyToUse: 'prêt à l’emploi', usable: 'utilisable', redo: 'à refaire',
    judgeLoading: 'Le juge examine les quatre vues…', judgeFourSides: 'Faire juger les quatre vues',
    reportMesh: 'Rapport du maillage', summaryClosed: 'Arêtes fermées', summaryInconsistent: 'Arêtes fermées · orientation incohérente',
    summaryOpen: (n: string) => `Non étanche (${n} arêtes ouvertes)`, summaryNotWatertight: 'Non étanche',
    summaryComponents: (n: string, plural: boolean) => `${n} composante${plural ? 's' : ''}`,
    warningEmpty: 'Maillage vide.', warningOpenEdges: (n: string) => `${n} arêtes ouvertes : le modèle n’est pas étanche (impression 3D : à réparer).`,
    warningNonManifold: (n: string) => `${n} arêtes partagées par plus de deux faces (non-variété).`,
    warningDegenerate: (n: string) => `${n} triangles dégénérés.`, warningBadOrientation: 'Volume non calculé : orientation incohérente des faces.',
    warningMultipleSolids: 'Volume non calculé : plusieurs composantes fermées peuvent représenter des solides distincts ou des cavités imbriquées.',
    warningDisconnected: (n: string) => `${n} morceaux séparés (fragments flottants possibles).`, unknownWarning: 'Détail supplémentaire sur le maillage indisponible.',
  },
  en: {
    language: 'Language',
    intro: 'Turn an image, several views, or a sentence into a textured 3D model. Rotate it, export it (GLB, OBJ, STL, 3MF, USDZ), or place it in a scene. Processing uses our GPUs.',
    startingPoint: 'Starting point', imageTo3d: 'Image → 3D', multiView: 'Multiple views', textTo3d: 'Text → 3D',
    object: 'The object', objectDescription: 'A light-wood chair with tapered legs, a red metal toy robot…',
    text3dIntro: 'First, create a clean product photo of the object, reconstruct it in 3D, then check four sides. At most one retry if the check is strict.',
    frontView: 'Front view', image: 'Image', addFrontView: 'Add a front view', frontViewHint: 'One subject, fully in frame, against a plain background works best.',
    leftView: 'Left view', backView: 'Back view', rightView: 'Right view', optional: ' (optional)',
    addLeftView: 'Add a left view', addBackView: 'Add a back view', addRightView: 'Add a right view',
    sameObjectLeft: 'The same object, viewed from its left side.', sameObjectBack: 'The same object, viewed from behind.', sameObjectRight: 'The same object, viewed from its right side.',
    multiViewInfo: (max: number) => `Add at least one more view of the same object. Up to ${max} views under the current server limit. Draft only.`,
    viewLimitLoading: 'Checking the view limit with the server…',
    viewLimitUnavailable: (max: number) => `The server limit could not be confirmed. For now, selection is limited to ${max} views.`,
    viewLimitExceeded: (max: number) => `This selection exceeds the current limit of ${max} views. Remove a view to continue.`,
    multiViewUnavailable: 'Multi-view reconstruction is unavailable on this server.',
    estimateUnavailable: 'Estimate unavailable',
    detail: 'Detail level', draft: 'Draft', high: 'High quality', credits: 'credits', decreaseCount: 'Reduce the number of takes', increaseCount: 'Increase the number of takes', draftInfo: 'Up to 150,000 faces, 2K textures. About 40 seconds on GB10. Check the shape here.',
    highInfo: 'Up to 400,000 faces, 4K textures, baked normal and ambient-occlusion maps. About 3 minutes on GB10.',
    original: 'Original', cutout: 'Cut out', cutoutAlt: 'Subject with the background removed', removeBackground: 'Remove background',
    removeBackgroundAgain: 'Remove the background again', removingBackground: 'Removing the background…',
    useThisCutout: '3D uses this exact cutout.', useOriginal: '3D uses the original image.',
    cutFirst: 'Cut out the subject first', cutoutBehavior: 'BiRefNet finds the subject and removes the background.',
    transparencyBehavior: 'Uses the image’s transparency. Turn this off only for a PNG that is already cut out.',
    eachTakeNewSeed: 'Each take uses a new seed.',
    create3d: 'Create in 3D', inProgress: 'In progress…', buildingModels: (n: number) => `Building ${n} model${n === 1 ? '' : 's'}`,
    modelFromViews: (n: number) => `Model from ${n} views`,
    loading: 'Loading…', uploadFailure: 'Could not load this image. Try again.', takeFailure: 'Could not load this take. Try again.',
    requestFailure: 'The request could not be completed. Check the source and try again.', backgroundFailure: 'Could not remove the background. Try again.',
    animationFailure: 'Could not prepare this view for animation. Wait for the model to load, then try again.',
    emptyTitle: 'in 3D', addStill: 'Add an image', addStillHelp: 'Or choose Create in 3D on an image in the Library.',
    chooseDetail: 'Choose the detail level', chooseDetailHelp: 'Use Draft to check the shape, High quality for the keeper.',
    turnModel: 'Turn it', turnModelHelp: 'Drag to orbit, download the GLB, or place it in a scene.',
    models: 'Models', downloadGlb: 'Download GLB', modelViewerUnavailable: 'This browser could not show the model. Download the GLB to open it elsewhere.', modelLoading: 'Loading the model…', modelViewerLabel: '3D model preview', modelTriangles: (n: string) => `${n} triangles`, modelLooks: 'Model appearance', modelSubject: 'Source image for the model', recreate: 'Recreate', recreateSent: 'Recreation request submitted.',
    recreateUnconfirmed: 'Could not confirm whether the recreation request was submitted. Check your takes before trying again.', delete: 'Delete',
    from: 'From', textured: 'Textured', clay: 'Clay', wire: 'Wireframe',
    facesAndTextures: (quality: string, faces: string, px: string) => `${quality} · up to ${faces} faces · ${px} textures`,
    open: 'Open', animateInVideo: 'Animate in video', darkStudio: 'Dark studio', lightStudio: 'Light studio', blueNight: 'Blue night',
    capture: 'Capturing…', animateWithH3: 'Animate with H3', viewNotReady: 'The 3D view is not ready.',
    textReferenceImage: 'Reference image', textModel: '3D model', textCheck: 'Four-side check', secondAttempt: ' (second attempt)',
    judge: 'Judge', failed: 'Failed.', judgeUnavailable: 'The judge did not respond.', retryWithNewSeed: 'Retry with a new seed',
    languageSwitch: 'Interface language', french: 'Français', english: 'English',
    cardStep: 'Step', cardRendering: 'Rendering', cardWaiting: 'Waiting for the engine', cardQueued: 'Queued',
    cardFailed: 'Take failed', cardFailedHelp: 'This take could not be completed. Check the source and try again.', cardPlans: 'shots', cardVideo: 'video',
    cardSeamless: 'Seamless', cardSeam: 'Visible seam', cardSeamTitle: (ratio: number) => `Loop point: ${ratio}× a frame step`,
    reportLoading: 'Analyzing the mesh…', reportFailure: 'The analysis did not finish. Exports in this section are unavailable. Try again later.',
    exportUnavailable: 'Export unavailable', export: 'Export', exportFormat: 'Export format', numberOfFaces: 'Number of faces', vertices: 'vertices',
    helpGlb: 'The model as-is, including PBR textures (web, Stage, Blender, games).',
    helpObj: 'A zip with .obj, .mtl, and the color texture (3D software).',
    helpStl: 'No color, millimeters, laid flat: for 3D printing.',
    help3mf: 'No color, millimeters: for recent slicers (Bambu, Prusa, Cura).',
    helpUsdz: 'Apple: Quick Look, Vision Pro, Reality Composer.',
    serverNoCredits: 'Calculated on the server: 0 credits. Decimation preserves textures.',
    pbrMaps: 'PBR maps', openMap: (name: string) => `Open “${name}” map`, mapAlt: (name: string) => `${name} map`,
    turntable: 'Turntable', animatedGif: 'Animated GIF', qualityCheck: 'Quality check',
    readyToUse: 'ready to use', usable: 'usable', redo: 'redo',
    judgeLoading: 'The judge is checking four views…', judgeFourSides: 'Judge the four views',
    reportMesh: 'Mesh report', summaryClosed: 'Closed edges', summaryInconsistent: 'Closed edges · inconsistent orientation',
    summaryOpen: (n: string) => `Not watertight (${n} open edges)`, summaryNotWatertight: 'Not watertight',
    summaryComponents: (n: string, plural: boolean) => `${n} component${plural ? 's' : ''}`,
    warningEmpty: 'Empty mesh.', warningOpenEdges: (n: string) => `${n} open edges: the model is not watertight (repair before 3D printing).`,
    warningNonManifold: (n: string) => `${n} edges are shared by more than two faces (non-manifold).`,
    warningDegenerate: (n: string) => `${n} degenerate triangles.`, warningBadOrientation: 'Volume not calculated: face orientation is inconsistent.',
    warningMultipleSolids: 'Volume not calculated: multiple closed components may be separate solids or nested cavities.',
    warningDisconnected: (n: string) => `${n} disconnected components (possible floating fragments).`, unknownWarning: 'Additional mesh detail is unavailable.',
  },
} as const;

export type MeshCopy = typeof MESH_COPY.fr;
export function meshCopy(langue: LangueClient): MeshCopy {
  return MESH_COPY[langue] as MeshCopy;
}

export function meshNumber(value: number, langue: LangueClient): string {
  return value.toLocaleString(langue === 'fr' ? 'fr-CA' : 'en-CA');
}

const WARNING_ORIENTATION = 'Volume non calculé : orientation incohérente des faces.';

export function avertissementMaillage(texte: string, langue: LangueClient): string {
  const c = meshCopy(langue);
  if (texte === 'Maillage vide.') return c.warningEmpty;
  if (texte === WARNING_ORIENTATION) return c.warningBadOrientation;
  if (texte === 'Volume non calculé : plusieurs composantes fermées peuvent représenter des solides distincts ou des cavités imbriquées.') return c.warningMultipleSolids;
  let m = /^(\d+) arêtes ouvertes :/.exec(texte);
  if (m) return c.warningOpenEdges(meshNumber(Number(m[1]), langue));
  m = /^(\d+) arêtes partagées par plus de deux faces/.exec(texte);
  if (m) return c.warningNonManifold(meshNumber(Number(m[1]), langue));
  m = /^(\d+) triangles dégénérés\./.exec(texte);
  if (m) return c.warningDegenerate(meshNumber(Number(m[1]), langue));
  m = /^(\d+) morceaux séparés/.exec(texte);
  if (m) return c.warningDisconnected(meshNumber(Number(m[1]), langue));
  return c.unknownWarning;
}
