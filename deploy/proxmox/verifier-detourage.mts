/**
 * Vérification de bout en bout du détourage en production, depuis la VM Creative : le client déployé
 * (server/nexora/detourage/client.ts), l'URL et le jeton de /etc/nexora/creative.env (lus ici, jamais affichés),
 * un vrai clip : santé, aperçu d'un clic, dépôt, travail complet, suivi, téléchargement de chaque export, nettoyage.
 *
 *   cd /srv/creative/app && sudo -u nexora node_modules/.bin/tsx ../verifier-detourage.mts <clip.mp4> <dossier_sortie> [mot en anglais]
 */
import { execFileSync } from 'node:child_process';
import { createReadStream, mkdirSync, readFileSync, statSync, writeFileSync } from 'node:fs';
import { join } from 'node:path';
import { clientDetourage } from './app/server/nexora/detourage/client.js';

const env = Object.fromEntries(readFileSync('/etc/nexora/creative.env', 'utf8').split('\n')
  .map((l) => l.match(/^(NEXORA_DETOURAGE_(?:URL|JETON)|FFMPEG_BIN|FFPROBE_BIN)=(.*)$/)).filter(Boolean).map((m) => [m![1], m![2].trim()]));
const [clip, sortie] = process.argv.slice(2);
mkdirSync(sortie, { recursive: true });
const ff = env.FFMPEG_BIN || 'ffmpeg';
const fp = env.FFPROBE_BIN || 'ffprobe';
const c = clientDetourage(env.NEXORA_DETOURAGE_URL, fetch, env.NEXORA_DETOURAGE_JETON);
const t0 = Date.now();
const s = (x: number) => `${((Date.now() - x) / 1000).toFixed(1)} s`;

const sante = await c.sante();
console.log('santé', JSON.stringify({ gpu: (sante.modeles as any)?.gpu, libre: (sante.modeles as any)?.memoire_gpu_libre_go }));
const image = execFileSync(ff, ['-v', 'error', '-i', clip, '-frames:v', '1', '-vf', 'scale=1280:-2', '-f', 'image2', '-c:v', 'png', '-'], { maxBuffer: 64 << 20 });
const clic: { imageB64: string; points: number[][] } = { imageB64: image.toString('base64'), points: [[0.47, 0.55, 1], [0.48, 0.22, 1], [0.1, 0.9, 0]] };
const apercu = await c.segmenter(clic);
writeFileSync(join(sortie, 'apercu-masque.png'), Buffer.from(apercu.masqueB64, 'base64'));
console.log('aperçu du clic', JSON.stringify({ score: apercu.score, aire: apercu.aire, secondes: apercu.secondes }));

const mot = process.argv[4];
if (mot) {
  const tx = await c.texte({ imageB64: clic.imageB64, texte: mot });
  console.log('sélection par texte', JSON.stringify({ mot, objets: tx.objets.map((o) => ({ score: o.score, boite: o.boite, aire: o.aire })), secondes: tx.secondes }));
  if (tx.objets[0]) clic.points = [[(tx.objets[0].boite[0] + tx.objets[0].boite[2]) / 2, (tx.objets[0].boite[1] + tx.objets[0].boite[3]) / 2, 1]];
}
const id = `verif${Date.now().toString(16)}`;
const info = await c.deposer(id, 'source.mp4', createReadStream(clip) as never, statSync(clip).size);
console.log('dépôt', JSON.stringify(info));
await c.lancer(id, {
  source: 'source.mp4', largeur_max: 1280, invites: [{ image: 0, points: clic.points }], matting: 'vitmatte-base', bande: 0.05,
  composite: { type: 'couleur', valeur: '#1aa36f' }, conserver_travail: false,
});
let e = await c.etat(id);
while (e && !['termine', 'erreur', 'annule', 'interrompu'].includes(e.etat)) {
  await new Promise((r) => setTimeout(r, 2000));
  e = await c.etat(id);
}
console.log('travail', e?.etat, s(t0), JSON.stringify((e?.mesures as any)?.temps_etapes_s));
if (e?.etat !== 'termine') process.exit(1);
for (const nom of ['alpha.zip', 'rgba16.zip', 'exr.zip', 'detourage-prores4444.mov', 'detourage-alpha.webm', 'matte.mp4', 'composite.mp4', 'apercu-echecs.mp4']) {
  const r = await c.sortie(id, nom);
  const b = Buffer.from(await r.arrayBuffer());
  writeFileSync(join(sortie, nom), b);
  let detail = '';
  if (/\.(mov|webm|mp4)$/.test(nom)) {
    detail = execFileSync(fp, ['-v', 'error', '-select_streams', 'v:0', '-show_entries', 'stream=codec_name,pix_fmt,width,height,nb_frames:stream_tags=alpha_mode', '-of', 'compact=p=0:nk=0', join(sortie, nom)]).toString().trim();
  }
  console.log('téléchargé', nom, `${(b.length / 1e6).toFixed(2)} Mo`, detail);
}
await c.supprimer(id);
console.log('nettoyé sur la machine GPU ; total', s(t0));
