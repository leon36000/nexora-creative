/** Son mesuré des clips, calé sur les mêmes segments et la même ligne de temps que l’image. */
import { type EditPlan, lignedeTemps } from './editplan.js';
import { segmentsVitesse } from './retiming.js';

const FREQUENCE = 48000;

/** Chaîne WSOLA : aucun facteur > 2, qui ferait sauter des échantillons dans atempo. */
export function filtresTempo(vitesse: number): string {
  if (!Number.isFinite(vitesse) || vitesse <= 0) throw new RangeError('Vitesse audio invalide.');
  const facteurs: number[] = [];
  while (vitesse > 2) { facteurs.push(2); vitesse /= 2; }
  while (vitesse < 0.5) { facteurs.push(0.5); vitesse *= 2; }
  if (vitesse !== 1) facteurs.push(vitesse);
  return facteurs.map(f => `atempo=${f}`).join(',');
}

export function audioDesClips(plan: EditPlan, index: ReadonlyMap<string, number>): { filtres: string[]; pistes: string[] } {
  const filtres: string[] = [], pistes: string[] = [];
  const parImage = FREQUENCE / plan.fps;
  const { debuts, total } = lignedeTemps(plan);
  const fonduCoupe = Math.round(plan.audio.fondu_coupe_ms * FREQUENCE / 1000);
  plan.video.forEach((clip, i) => {
    const source = Object.hasOwn(plan.sources, clip.src) ? plan.sources[clip.src] : undefined;
    // L’absence de mesure conserve le comportement des anciens plans ; aucune piste supposée.
    if (source?.kind !== 'video' || source.a_audio !== true) return;
    const k = index.get(clip.src);
    if (k === undefined) throw new Error('Source audio du clip introuvable.');
    const morceaux: string[] = [];
    for (const [j, segment] of segmentsVitesse(clip).entries()) {
      const debut = segment.entree_f * parImage;
      const fin = (segment.entree_f + segment.source_f) * parImage;
      const longueur = segment.duree_f * parImage;
      const tempo = filtresTempo(segment.vitesse);
      const tempoFiltre = tempo ? `,${tempo}` : '';
      const nom = `sonclip${i}s${j}`;
      filtres.push(`[${k}:a]aresample=${FREQUENCE}:async=1:first_pts=0,aformat=sample_fmts=fltp:channel_layouts=stereo,atrim=start_sample=${debut}:end_sample=${fin},asetpts=N/SR/TB${tempoFiltre},apad=whole_len=${longueur},atrim=end_sample=${longueur},asetpts=N/SR/TB[${nom}]`);
      morceaux.push(`[${nom}]`);
    }
    const entreeTransition = i > 0 && clip.transition_in.type !== 'cut' ? clip.transition_in.duree_f * parImage : 0;
    const suivant = plan.video[i + 1];
    const sortieTransition = suivant && suivant.transition_in.type !== 'cut' ? suivant.transition_in.duree_f * parImage : 0;
    const longueur = clip.duree_f * parImage;
    const entree = Math.min(Math.floor(longueur / 2), Math.max(fonduCoupe, entreeTransition));
    const sortie = Math.min(Math.floor(longueur / 2), Math.max(fonduCoupe, sortieTransition));
    let fondus = '';
    if (entree) fondus += `,afade=t=in:ss=0:ns=${entree}`;
    if (sortie) fondus += `,afade=t=out:ss=${longueur - sortie}:ns=${sortie}`;
    const assemblage = morceaux.length > 1 ? `concat=n=${morceaux.length}:v=0:a=1` : 'anull';
    const nom = `sonclip${i}`;
    filtres.push(`${morceaux.join('')}${assemblage}${fondus},adelay=${debuts[i] * parImage}S:all=1,apad=whole_len=${total * parImage},atrim=end_sample=${total * parImage}[${nom}]`);
    pistes.push(nom);
  });
  return { filtres, pistes };
}
