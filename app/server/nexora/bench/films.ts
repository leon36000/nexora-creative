/**
 * Stade B de la campagne : pour 3 briefs et chaque palier, le modèle compose le film sur la bibliothèque de plaques
 * déjà tournées (N candidats, le meilleur score en code gagne), puis le rendu ffmpeg (textes en code, carton neutre).
 *   npx tsx server/nexora/bench/films.ts --etiquette a1 [--candidats 3] [--paliers eco,equilibre,expert] [--briefs reception,...]
 * Sortie : ~/nexora-creative-data/promo/montage/Test-agents-<palier>-<brief>-16x9-fr.mp4
 */
import { execFileSync } from 'node:child_process';
import { appendFileSync, copyFileSync, existsSync, mkdirSync, readFileSync, statSync, writeFileSync } from 'node:fs';
import { homedir } from 'node:os';
import { join } from 'node:path';
import { versMusique, analyserMedia, ffmpegParDefaut } from '../montage/analyse.js';
import { briefDeMontage, MemoireFilm, runFilm } from '../montage/film.js';
import { rendreEditPlan } from '../montage/rendu.js';
import { clientPalier, PALIERS, type Palier } from '../niveaux.js';
import { GrandLivreUsage, Releve } from '../usage.js';
import { BRIEFS_FILMS } from './briefsFilms.js';
import { FILMS_BIBLIOTHEQUE, PLAQUES } from './bibliotheque.js';
import { chargerCles, type Essai } from './campagne.js';

const arg = (n: string, d: string) => { const i = process.argv.indexOf(`--${n}`); return i >= 0 ? process.argv[i + 1] : d; };

async function main() {
  chargerCles();
  const etiquette = arg('etiquette', 'a1');
  const candidats = Number(arg('candidats', '3'));
  const paliers = arg('paliers', PALIERS.join(',')).split(',') as Palier[];
  const ids = arg('briefs', FILMS_BIBLIOTHEQUE.map((f) => f.brief).join(',')).split(',');
  const travail = join(homedir(), 'nexora-creative-data/work/tests-agents', `${etiquette}-films`);
  const finals = join(homedir(), 'nexora-creative-data/promo/montage');
  mkdirSync(travail, { recursive: true });
  const ffmpeg = ffmpegParDefaut();
  const livre = new GrandLivreUsage(join(travail, 'usage.jsonl'));

  // Mémoire d'arrivée : graines + plans appris à la campagne du stade A.
  const memoire = new MemoireFilm();
  const reg = join(homedir(), 'nexora-creative-data/work/tests-agents', etiquette, 'registre.jsonl');
  if (existsSync(reg)) for (const l of readFileSync(reg, 'utf8').split('\n').filter(Boolean)) {
    const e = JSON.parse(l) as Essai;
    const b = BRIEFS_FILMS.find((x) => x.id === e.brief);
    if (b && e.memoire !== 'v0' && e.source === 'llm' && e.plan) memoire.apprendre(b, e.palier, e.plan as any, e.tournage as any, e.score);
  }
  // Carton neutre : fond d'encre (marque.json), 8 s, 1344×768.
  const carton = join(travail, 'carton-neutre.mp4');
  if (!existsSync(carton)) execFileSync(ffmpeg, ['-y', '-v', 'error', '-f', 'lavfi', '-i', 'color=c=0x08080a:s=1344x768:r=24:d=8', '-c:v', 'libx264', '-pix_fmt', 'yuv420p', carton]);

  const rapport: any[] = [];
  for (const f of FILMS_BIBLIOTHEQUE.filter((x) => ids.includes(x.brief))) {
    const b = BRIEFS_FILMS.find((x) => x.id === f.brief)!;
    const mus = await analyserMedia(f.musique, { ffmpeg });
    const clips = f.plaques.map((id) => ({ id, duree_s: PLAQUES[id].duree_s, description: PLAQUES[id].description }));
    const bm = briefDeMontage(b, clips, versMusique('musique', mus));
    bm.fps = 24;
    await Promise.all(paliers.map(async (p) => {
      const essais: { run: Awaited<ReturnType<typeof runFilm>>; usd: number; credits: number }[] = [];
      for (let k = 0; k < candidats; k++) {
        const rel = new Releve({ run: `film-${etiquette}-${p}-${b.id}-${k}`, tache: 'film', projet: b.id }, 0.5, livre);
        try {
          const run = await runFilm(clientPalier(p, { surveillant: rel }), p, b, { memoire, reparations: 2, sansTournage: bm });
          essais.push({ run, usd: rel.coutUsd, credits: rel.totaux.credits });
          console.error(`${p} ${b.id} cand ${k + 1}: score ${run.score.toFixed(3)} ${run.montage.source} ${rel.coutUsd.toFixed(4)} USD`);
        } catch (e) { console.error(`${p} ${b.id} cand ${k + 1} : ${e instanceof Error ? e.message : e}`); }
      }
      if (!essais.length) return;
      const gagnant = essais.reduce((m, x) => (x.run.score > m.run.score ? x : m));
      const dossier = join(travail, `${p}-${b.id}`);
      mkdirSync(dossier, { recursive: true });
      const chemin = (src: string) => (src === 'carton' ? carton : src === 'musique' ? f.musique : PLAQUES[src].chemin);
      const sortie = join(dossier, `Test-agents-${p}-${b.id}-16x9-fr.mp4`);
      const r = await rendreEditPlan(gagnant.run.plan, chemin, sortie, { ffmpeg, taille: [1280, 720] });
      if (!r.ok) { console.error(`rendu ${p} ${b.id} : ${r.erreurs.join(' ; ')}`); return; }
      mkdirSync(finals, { recursive: true });
      const final = join(finals, `Test-agents-${p}-${b.id}-16x9-fr.mp4`);
      copyFileSync(sortie, final);
      writeFileSync(join(dossier, 'gagnant.json'), JSON.stringify({ plan: gagnant.run.plan, liste: gagnant.run.montage.liste, scores: essais.map((x) => x.run.score) }, null, 1));
      rapport.push({ palier: p, brief: b.id, score: gagnant.run.score, scores: essais.map((x) => +x.run.score.toFixed(3)), usdTotal: essais.reduce((s, x) => s + x.usd, 0), usdGagnant: gagnant.usd, creditsGagnant: gagnant.credits, final, octets: statSync(final).size, dureeS: r.dureeS, metriques: gagnant.run.metriques });
      appendFileSync(join(travail, 'films.jsonl'), JSON.stringify(rapport[rapport.length - 1]) + '\n');
    }));
  }
  console.log(JSON.stringify(rapport, null, 1));
}
main().catch((e) => { console.error(e instanceof Error ? e.message : String(e)); process.exit(1); });
