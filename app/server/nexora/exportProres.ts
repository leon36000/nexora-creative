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

/** Contrôle les métadonnées, sans prétendre décoder chaque image. */
export async function verifierProres(provisoire: string, source: string, ffprobe: string): Promise<void> {
  const lire = async (fichier: string): Promise<Rapport> => {
    const stdout = await executerBorne(ffprobe,
      ['-v', 'error', '-show_entries', 'format=duration:stream=codec_type,codec_name,profile,pix_fmt,width,height', '-of', 'json', fichier], 60_000);
    return JSON.parse(stdout) as Rapport;
  };
  const entree = await lire(source);
  const sortie = await lire(provisoire);
  verifierRapports(entree, sortie);
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
