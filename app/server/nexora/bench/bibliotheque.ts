/**
 * Bibliothèque de plans déjà tournés (stade B de la campagne) : plaques H3 1344×768 de ~/nexora-creative-data, avec leur
 * contenu décrit en une phrase (tiré des prompts de tournage). Aucun texte ni logo dans ces plaques ; le carton neutre
 * est fabriqué par ffmpeg (fond d'encre de marque.json).
 */
import { homedir } from 'node:os';
import { join } from 'node:path';

const D = join(homedir(), 'nexora-creative-data');
const SURV = join(D, 'site-medias-travail/plans/surv'), REC = join(D, 'site-medias-travail/plans/recep'), HERO = join(D, 'site-medias-travail/plans/hero'), OPS = join(D, 'promo/v6/opsys/plaques');
const MUS = join(D, 'site-medias-travail/musique');

export interface Plaque { id: string; chemin: string; duree_s: number; description: string }
const p = (id: string, chemin: string, description: string, duree_s = 5.17): Plaque => ({ id, chemin, duree_s, description });

export const PLAQUES: Record<string, Plaque> = Object.fromEntries([
  p('murs', `${SURV}/murs-16x9-v1.mp4`, 'dark security monitoring room at night, huge curved wall of camera screens'),
  p('stockage', `${SURV}/stockage-16x9-v1.mp4`, 'macro on rows of video storage servers in a dark rack, blinking lights'),
  p('chaise', `${SURV}/chaise-16x9-v1.mp4`, 'empty black office chair at a desk in a dark room, nobody watching'),
  p('entrepot', `${SURV}/entrepot-16x9-v1.mp4`, 'static high-angle security-camera view of a warehouse at night'),
  p('stationnement', `${SURV}/stationnement-16x9-v1.mp4`, 'static high view of a parking lot from a pole camera'),
  p('alerte', `${SURV}/alerte-16x9-v3.mp4`, 'macro on a dark desk in a security booth, an alert lights up red'),
  p('intervention', `${SURV}/intervention-16x9-v1.mp4`, 'tracking shot behind a security guard in dark uniform walking to intervene'),
  p('rapport', `${SURV}/rapport-16x9-v1.mp4`, 'bright modern office in the morning, a person reads a report'),
  p('allee', `${HERO}/allee-16x9-v1.mp4`, 'smooth slow push-in along the central aisle of a vast data centre', 7.29),
  p('champ', `${HERO}/champ-16x9-v1.mp4`, 'CG night landscape of hills and a river made of luminous points, slow drift', 7.29),
  p('telephone', `${REC}/telephone-16x9-v1.mp4`, 'empty reception desk in an office lobby late at night, a phone lights up'),
  p('onde', `${REC}/onde-16x9-v1.mp4`, 'CG sound waveform of fine luminous lines in deep black space'),
  p('cliente', `${REC}/cliente-16x9-v1.mp4`, 'evening in a warm modern kitchen, a woman on a call'),
  p('texto', `${REC}/texto-16x9-v1.mp4`, 'macro on a smartphone face up on a dark wooden table at night, a message arrives'),
  p('transfert', `${REC}/transfert-16x9-v1.mp4`, 'bright modern office in daytime, a call is handed over to a colleague'),
  p('course', `${OPS}/l1-course-max.mp4`, 'runner seen from behind jogging along a riverside path at blue dawn, mist'),
  p('appel', `${OPS}/m1-appel-rapide.mp4`, 'smartphone face up on a dark kitchen counter at night, screen glowing blue'),
  p('maison', `${OPS}/m3-maison-max.mp4`, 'Quebec suburban house at blue hour, light snow on the lawn'),
  p('dejeuner', `${OPS}/l2-dejeuner-rapide.mp4`, 'father and young child at a breakfast table at sunrise, seen from behind'),
  p('camion', `${OPS}/m4-camion-rapide.mp4`, 'white work pickup with a ladder rack leaving a driveway at dawn, exhaust vapour'),
  p('depot', `${OPS}/m6-entrepot-rapide.mp4`, 'small contractor warehouse at night, tall shelves of coils and boxes'),
  p('bureau', `${OPS}/m5-bureau-rapide.mp4`, 'minimalist home-office desk at night, closed laptop, pen and blank sheet under one lamp'),
  p('terrasse', `${OPS}/l3-terrasse-rapide.mp4`, 'man seen from behind on a lakeside dock at golden hour with a coffee'),
  p('photo', `${OPS}/m7-photo-rapide.mp4`, 'close-up of gloved hands photographing freshly installed siding with a phone'),
  p('porte', `${OPS}/m2-porte-rapide.mp4`, 'homeowner opening the front door to a contractor at dusk, warm light spilling out'),
  p('matin', `${OPS}/m9-matin-rapide.mp4`, 'kitchen island at 7 am, steaming coffee next to a phone with a soft blue glow'),
  p('hockey', `${OPS}/l4-hockey-max.mp4`, 'father in the stands of a small community hockey arena at night, children playing'),
].map((x) => [x.id, x]));

export interface FilmBibliotheque { brief: string; plaques: string[]; musique: string; enonceAjout: string }
export const FILMS_BIBLIOTHEQUE: FilmBibliotheque[] = [
  { brief: 'reception', plaques: ['telephone', 'onde', 'cliente', 'texto', 'transfert', 'appel', 'matin', 'bureau', 'porte', 'dejeuner'], musique: `${MUS}/recep-v1.flac`, enonceAjout: '' },
  { brief: 'surveillance', plaques: ['murs', 'stockage', 'chaise', 'entrepot', 'stationnement', 'alerte', 'intervention', 'rapport', 'allee'], musique: `${MUS}/surv-v2.flac`, enonceAjout: '' },
  { brief: 'opsys', plaques: ['course', 'appel', 'maison', 'dejeuner', 'camion', 'depot', 'bureau', 'terrasse', 'photo', 'porte', 'matin', 'hockey'], musique: join(D, 'promo/v6/opsys/audio/opsys-musique-71.flac'), enonceAjout: '' },
];
