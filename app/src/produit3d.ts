/**
 * Nom du mode 3D de Nexora Creative : UN seul endroit. La marque produit changera plus tard, il suffit alors de
 * modifier PRODUIT_3D ; l'interface, les outils MCP et les messages du serveur le lisent ici (« Relief » en français et en anglais).
 */
export const PRODUIT_3D = 'Relief';
/** Adresse du mode ; `/object` reste un alias (anciens liens, Viewer, MCP). */
export const ROUTE_3D = '/relief';
export const ROUTE_3D_ALIAS = '/object';
/** Vrai si le chemin ouvre le mode 3D (nouvelle adresse ou alias). */
export const estRoute3D = (chemin: string) => chemin === ROUTE_3D || chemin === ROUTE_3D_ALIAS;
