import { linkSync, mkdirSync, mkdtempSync, statSync, writeFileSync } from 'node:fs';
import { join, resolve } from 'node:path';
import { executerBorne } from './executionBornee.js';

/** Identité locale observée ; ne garantit pas une synchronisation entre processus. */
function signatureSource(path: string): string {
  const s = statSync(path, { bigint: true });
  if (!s.isFile()) throw new Error('La source doit être un fichier.');
  return [s.dev, s.ino, s.size, s.mtimeNs, s.ctimeNs].join(':');
}

type Encoder = (source: string, provisoire: string) => Promise<void>;
type Valider = (provisoire: string, source: string) => Promise<void>;

/** Les exports historiques restent intacts et ne sont pas considérés valides. */
export function creerExportProres(encoder: Encoder, valider: Valider) {
  const actifs = new Map<string, Promise<string>>();
  const termines = new Map<string, { chemin: string; signature: string }>();
  return async (filmId: number, source: string, parent: string): Promise<string> => {
    source = resolve(source); parent = resolve(parent);
    const signature = signatureSource(source);
    const cle = JSON.stringify([filmId, source, parent, signature]);
    const ancien = termines.get(cle);
    if (ancien) {
      try { if (signatureSource(ancien.chemin) === ancien.signature) return ancien.chemin; } catch { /* relancer */ }
      termines.delete(cle);
    }
    const actif = actifs.get(cle);
    if (actif) return actif;
    const travail = (async () => {
      mkdirSync(parent, { recursive: true });
      const dossier = mkdtempSync(join(parent, `film_${filmId}_prores_`));
      const provisoire = join(dossier, 'provisoire.mov');
      const publie = join(dossier, 'complet.mov');
      let phase = 'encodage';
      try {
        await encoder(source, provisoire);
        phase = 'validation';
        await valider(provisoire, source);
        phase = 'source';
        if (signatureSource(source) !== signature) throw new Error('La source a changé pendant l’export.');
        phase = 'publication';
        linkSync(provisoire, publie); // atomique, refuse un chemin existant ; conserve l’essai.
        termines.set(cle, { chemin: publie, signature: signatureSource(publie) });
        return publie;
      } catch (e) {
        try { writeFileSync(join(dossier, 'ECHEC.json'), JSON.stringify({ etat: 'echec', phase }), { flag: 'wx' }); } catch { /* ne masque pas l’erreur initiale */ }
        throw e;
      }
    })();
    actifs.set(cle, travail);
    try { return await travail; } finally { actifs.delete(cle); }
  };
}

type Flux = { codec_type?: string; codec_name?: string; profile?: string; pix_fmt?: string; width?: number; height?: number };
type Rapport = { format?: { duration?: string }; streams?: Flux[] };

type Chronologie = { images: number; debut: number; fin: number; derniereDuree: number };

/** Sonde les images décodées en flux : mémoire bornée, sans dépendre de stream.duration. */
async function chronologieVideo(fichier: string, ffprobe: string, delaiMs: number): Promise<Chronologie> {
  let reste = '', images = 0, debut = NaN, precedent = NaN, derniereDuree = NaN;
  const nombre = (v: string | undefined) => { const n = v?.trim(); return n && /^-?\d+(?:\.\d+)?(?:e[+-]?\d+)?$/i.test(n) ? Number(n) : NaN; };
  const ligne = (texte: string) => {
    if (!texte.trim()) return;
    const champs = new Map(texte.split('|').filter(Boolean).map((champ) => { const i = champ.indexOf('='); return [champ.slice(0, i), champ.slice(i + 1)]; }));
    const date = nombre(champs.get('best_effort_timestamp_time'));
    const duree = [nombre(champs.get('duration_time')), nombre(champs.get('pkt_duration_time'))].find((n) => Number.isFinite(n) && n > 0) ?? NaN;
    if (!Number.isFinite(date) || (images && date < precedent)) throw new Error('Dates vidéo invalides.');
    if (!images) debut = date;
    precedent = date; derniereDuree = duree; images++;
  };
  const recevoir = (bloc: Buffer) => {
    reste += bloc.toString('utf8');
    let fin: number;
    while ((fin = reste.indexOf('\n')) >= 0) { ligne(reste.slice(0, fin)); reste = reste.slice(fin + 1); }
    if (reste.length > 4096) throw new Error('Ligne vidéo excessive.');
  };
  await executerBorne(ffprobe, ['-v', 'error', '-select_streams', 'v:0', '-show_frames',
    '-show_entries', 'frame=best_effort_timestamp_time,pkt_duration_time,duration_time:frame_side_data=', '-of', 'compact=p=0:nk=0', fichier], delaiMs, recevoir);
  if (reste) ligne(reste);
  // Sans durée de dernière image, ne pas présenter une extrapolation comme une mesure.
  if (!images || !Number.isFinite(derniereDuree) || derniereDuree <= 0) throw new Error('Durée de la dernière image non vérifiable.');
  return { images, debut, fin: precedent + derniereDuree, derniereDuree };
}

/** Compare les durées décodées, pas les cadences ou nombres de frames d'une source VFR normalisée. */
export function verifierChronologies(source: Chronologie, sortie: Chronologie): void {
  const valide = (c: Chronologie) => Number.isSafeInteger(c.images) && c.images > 0 &&
    Number.isFinite(c.debut) && Number.isFinite(c.fin) && c.fin > c.debut &&
    Number.isFinite(c.derniereDuree) && c.derniereDuree > 0;
  if (!valide(source) || !valide(sortie)) throw new Error('Chronologie vidéo invalide ou non vérifiable.');
  const dureeSource = source.fin - source.debut, dureeSortie = sortie.fin - sortie.debut;
  const tolerance = Math.min(0.25, Math.max(0.05, source.derniereDuree / 2, sortie.derniereDuree / 2));
  if (!source.images || !sortie.images || !Number.isFinite(dureeSource) || dureeSource <= 0 ||
      !Number.isFinite(dureeSortie) || dureeSortie <= 0 || Math.abs(dureeSortie - dureeSource) > tolerance) {
    throw new Error('Le contrôle temporel du flux vidéo ProRes a échoué.');
  }
}

/** Contrôle les métadonnées et le temps des images décodées, sans juger leur contenu visuel. */
export async function verifierProres(provisoire: string, source: string, ffprobe: string): Promise<void> {
  const echeance = performance.now() + 60_000;
  const tempsRestant = () => { const restant = echeance - performance.now(); if (restant <= 0) throw new Error('Délai de contrôle ProRes dépassé.'); return restant; };
  const lire = async (fichier: string): Promise<Rapport> => {
    const stdout = await executerBorne(ffprobe,
      ['-v', 'error', '-show_entries', 'format=duration:stream=codec_type,codec_name,profile,pix_fmt,width,height', '-of', 'json', fichier], tempsRestant());
    return JSON.parse(stdout) as Rapport;
  };
  const entree = await lire(source);
  const sortie = await lire(provisoire);
  verifierRapports(entree, sortie);
  const sourceVideo = await chronologieVideo(source, ffprobe, tempsRestant());
  const sortieVideo = await chronologieVideo(provisoire, ffprobe, tempsRestant());
  verifierChronologies(sourceVideo, sortieVideo);
}

export function verifierRapports(entree: Rapport, sortie: Rapport): void {
  const video = sortie.streams?.find((s) => s.codec_type === 'video');
  const audioRequis = entree.streams?.some((s) => s.codec_type === 'audio');
  const audio = sortie.streams?.find((s) => s.codec_type === 'audio');
  const dureeSource = Number(entree.format?.duration), dureeSortie = Number(sortie.format?.duration);
  const tolerance = Math.max(0.25, dureeSource * 0.02);
  if (!video || video.codec_name !== 'prores' || video.profile !== 'HQ' || video.pix_fmt !== 'yuv422p10le' || !video.width || !video.height ||
      (audioRequis && audio?.codec_name !== 'pcm_s16le') || !Number.isFinite(dureeSource) || dureeSource <= 0 ||
      !Number.isFinite(dureeSortie) || dureeSortie <= 0 || Math.abs(dureeSortie - dureeSource) > tolerance) {
    throw new Error('Le contrôle de l’export ProRes a échoué.');
  }
}
