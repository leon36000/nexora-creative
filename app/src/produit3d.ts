/**
 * Nom du mode 3D de Nexora Creative : UN seul endroit. Le nom actuel est « Nexora Mesh » (ancien nom « Relief »,
 * ancré à l'origine sur l'app Object) ; pour rebaptiser le produit, il suffit de modifier PRODUIT_3D (et, si l'adresse
 * change, ROUTE_3D). L'interface, les outils MCP et les messages du serveur le lisent ici, en français et en anglais.
 */
export const PRODUIT_3D = 'Nexora Mesh';
/** Forme courte pour des noms de fichiers ou un shotName (jamais affichée telle quelle). */
export const PRODUIT_3D_SLUG = 'mesh';
/** Adresse du mode ; `/relief` (ancien nom) et `/object` (origine) restent des alias pour les anciens liens. */
export const ROUTE_3D = '/mesh';
export const ROUTE_3D_ALIAS_RELIEF = '/relief';
export const ROUTE_3D_ALIAS = '/object';
/** Vrai si le chemin ouvre le mode 3D (adresse actuelle ou anciens alias). */
export const estRoute3D = (chemin: string) => chemin === ROUTE_3D || chemin === ROUTE_3D_ALIAS_RELIEF || chemin === ROUTE_3D_ALIAS;
