/**
 * Nom du mode 3D de Nexora Creative : UN seul endroit. Le nom actuel est « Nexora Mesh » (ancien nom « Relief »,
 * ancré à l'origine sur l'app Object) ; son nom vient de la source centrale `shared/productNames.ts`. PRODUIT_3D reste
 * l'alias consommé par l'interface, le serveur et les outils MCP ; ROUTE_3D garde l'adresse technique.
 */
import { NEXORA_PRODUCT_NAMES } from '../shared/productNames.js';

export const PRODUIT_3D = NEXORA_PRODUCT_NAMES.mesh;
/** Forme courte pour des noms de fichiers ou un shotName (jamais affichée telle quelle). */
export const PRODUIT_3D_SLUG = 'mesh';
/** Adresse du mode ; `/relief` (ancien nom) et `/object` (origine) restent des alias pour les anciens liens. */
export const ROUTE_3D = '/mesh';
export const ROUTE_3D_ALIAS_RELIEF = '/relief';
export const ROUTE_3D_ALIAS = '/object';
/** Vrai si le chemin ouvre le mode 3D (adresse actuelle ou anciens alias). */
export const estRoute3D = (chemin: string) => chemin === ROUTE_3D || chemin === ROUTE_3D_ALIAS_RELIEF || chemin === ROUTE_3D_ALIAS;
