/**
 * Les 8 briefs de la campagne « trois paliers » (écrits par le chef de projet). Épique, cinématographique, rythmé,
 * français du Québec, aucune promesse invérifiable, aucun nom de marque ni mention NVIDIA ; les textes sont posés en
 * code et le carton final porte la marque lue dans marque.json (le nom de l'entreprise va changer).
 */
import { readFileSync } from 'node:fs';
import { join } from 'node:path';
import type { BriefFilm } from '../montage/film.js';

const MARQUE = (() => {
  try { return String(JSON.parse(readFileSync(join(import.meta.dirname, '../../../../marketing/nexora/campagne-films/marque.json'), 'utf8')).marque ?? 'NEXORA'); } catch { return 'NEXORA'; }
})();
const STYLE = 'Style : épique, cinématographique, rythmé ; français du Québec ; aucune promesse que nous ne pouvons prouver ; ni nom de marque ni mention de fabricant ; textes posés en code ; carton final neutre portant la marque.';

const b = (id: string, titre: string, genre: BriefFilm['genre'], duree: number, bpm: number, mots: string[], enonce: string, film?: string): BriefFilm =>
  ({ id, titre, genre, format: '16:9', duree_cible_s: duree, bpm, marque: MARQUE, mots, enonce: `${enonce} ${STYLE}`, ...(film ? { film } : {}) });

export const BRIEFS_FILMS: BriefFilm[] = [
  b('workstudio', 'WorkStudio', 'bande-annonce', 36, 100, ['agents', 'equipe', 'travail', 'workstudio'], 'WorkStudio, épique et rythmé, PAS un tutoriel (le film précédent ressemblait à une capture d\'écran commentée) : faire sentir une équipe d\'agents qui travaille pour vous, grand dénouement, interface minimale, coupes sur la grille musicale.', 'workstudio'),
  b('nexora', 'Nexora, l\'entreprise', 'bande-annonce', 45, 96, ['environnement', 'navigateur', 'agents', 'documents', 'workflows'], 'Nexora, l\'entreprise : tout l\'environnement de travail IA dans le navigateur (agent de code, documents, flux de travail, studio de création), avec des agents qui peuvent aussi utiliser la puissance de votre propre ordinateur.'),
  b('creative', 'Creative', 'pub', 30, 110, ['creative', 'publicite', 'phrase', 'video', 'studio'], 'Creative : une phrase devient une publicité terminée.'),
  b('reception', 'Réception virtuelle', 'pub', 36, 100, ['reception', 'appels', 'courriels', 'textos', 'nuit'], 'Réception virtuelle : appels, courriels et textos reçus et traités jour et nuit.'),
  b('surveillance', 'Surveillance IA', 'pub', 36, 86, ['surveillance', 'video', 'camera', 'alerte', 'temps', 'reel'], 'Surveillance IA : personne ne regarde des milliers d\'heures de vidéo, nos IA le font, en temps réel.', 'surveillance'),
  b('infra', 'Infrastructure IA', 'pub', 40, 92, ['infrastructure', 'serveur', 'station', 'machine', 'installe', 'baies'], 'Infrastructure IA : machine IA compacte, station de travail IA, baies de serveurs installées chez vous.'),
  b('modeles', 'Modèles et API', 'pub', 30, 120, ['modeles', 'api', 'cle', 'catalogue'], 'Modèles et API : une seule clé, tous les modèles.', 'modeles'),
  b('opsys', 'OPSYS-AI', 'bande-annonce', 40, 88, ['agent', 'departements', 'humains', 'approuvent', 'opsys'], 'OPSYS-AI : un agent qui travaille à votre place, dix départements (M1 à M10), les humains approuvent.', 'opsys'),
];
