/**
 * Tournage et assemblage des films du Director (voir film.ts pour la planification). Même patron que les coupes de
 * scène d'OpenField (server/scene.ts) : une prise « film » porte l'état dans ses réglages ; chaque plan est une prise
 * ordinaire étiquetée `nexoraFilm` ; quand un plan se termine, `avancerFilm` regarde s'il peut assembler.
 */
import { execFile } from 'node:child_process';
import { existsSync, mkdirSync } from 'node:fs';
import { join } from 'node:path';
import { config } from '../config.js';
import { takes, type Take } from '../jobs.js';
import { corpsRendu, type DemandeCreer, type MoteurVideo } from './creer.js';
import { controlerFichier } from './controle.js';
import { argsAssemblage, intentionDuPlan, type PlanFilm, type Storyboard } from './film.js';
import type { ClientLlm } from './llm.js';
import { reecrireH3 } from './reecritureH3.js';

export interface DepsFilm {
  queueTakes: (b: any, count: number) => Promise<number[]>;
  broadcast: (msg: unknown) => void;
}
let deps: DepsFilm;
export const initFilms = (d: DepsFilm) => { deps = d; };

const reglages = (t: Take) => JSON.parse(t.settings) as Record<string, any>;
const pousser = (id: number) => deps.broadcast({ type: 'take', take: takes.get(id) });

export async function tournerFilm(
  sb: Storyboard,
  opts: { format: DemandeCreer['format']; son: boolean; intention: string; projectId?: number | null; moteur: MoteurVideo },
  llm: ClientLlm | null,
): Promise<number> {
  const filmId = takes.create({
    project_id: opts.projectId ?? null,
    kind: 'video',
    shot_name: sb.titre.slice(0, 40),
    settings: {
      app: 'nexora-film', film: true, storyboard: sb, format: opts.format, son: opts.son && opts.moteur === 'h3-fast', moteur: opts.moteur,
      prompt: opts.intention, userPrompt: sb.titre, seconds: sb.dureeTotale, shotName: sb.titre.slice(0, 40),
    },
  });
  pousser(filmId);
  try {
    // Les prompts des plans s'écrivent en parallèle (quelques secondes chacun), puis les rendus partent dans l'ordre.
    const prompts = await Promise.all(
      sb.plans.map((p, i) => reecrireH3({ intention: intentionDuPlan(sb, i), mode: 't2va', dureeS: p.duree === 10 ? 243 / 24 : 124 / 24 }, llm)),
    );
    for (let i = 0; i < sb.plans.length; i++) {
      const p = sb.plans[i];
      const corps = {
        ...corpsRendu({ intention: p.resume, format: opts.format, duree: p.duree, son: opts.son }, prompts[i].prompt, opts.moteur),
        app: 'nexora-film', userPrompt: p.resume, nexoraFilm: filmId, nexoraPlan: i, promptSource: prompts[i].source,
        shotName: `${sb.titre.slice(0, 28)}_plan${i + 1}`, projectId: opts.projectId ?? undefined,
      };
      const [id] = await deps.queueTakes(corps, 1);
      majPlan(filmId, i, { take: id, corps });
    }
  } catch (e) {
    takes.fail(filmId, `Les plans n'ont pas pu partir au tournage : ${e instanceof Error ? e.message : e}`);
    pousser(filmId);
    throw e;
  }
  return filmId;
}

function majPlan(filmId: number, i: number, patch: Record<string, unknown>) {
  const s = reglages(takes.get(filmId)!);
  s.storyboard.plans[i] = { ...s.storyboard.plans[i], ...patch };
  takes.setSettings(filmId, s);
  pousser(filmId);
}

const verrous = new Map<number, Promise<void>>();
/** Fait avancer un film ; sérialisé par film car plusieurs plans peuvent finir en même temps. */
export function avancerFilm(filmId: number): Promise<void> {
  const avant = verrous.get(filmId) ?? Promise.resolve();
  const suite = avant.then(() => etape(filmId)).catch((e) => {
    const t = takes.get(filmId);
    if (t && t.status === 'queued') { takes.fail(filmId, e instanceof Error ? e.message : 'assemblage impossible'); pousser(filmId); }
  });
  verrous.set(filmId, suite);
  return suite;
}

async function etape(filmId: number) {
  const film = takes.get(filmId);
  if (!film || film.status !== 'queued') return;
  const s = reglages(film);
  const sb = s.storyboard as Storyboard;
  const fichiers: string[] = [];
  for (const [i, p] of sb.plans.entries()) {
    if (!p.take) return; // pas encore en file
    const t = takes.get(p.take);
    if (!t) throw new Error(`Plan ${i + 1} : sa prise a été supprimée`);
    if (t.status === 'failed' || t.status === 'stopped') throw new Error(`Plan ${i + 1} : ${t.status}${t.error ? ` (${t.error})` : ''}`);
    if (t.status !== 'done' || !t.output_path || !existsSync(t.output_path)) return;
    const plan = p as PlanFilm & { corps?: Record<string, any>; controle?: { ok: boolean; defauts: string[] }; reprises?: number };
    if (!plan.controle) {
      const images = Number(plan.corps?.lengthFrames ?? plan.corps?.frames);
      const c = await controlerFichier(config.ffmpegBin, t.output_path, {
        dureeAttendue: Number.isFinite(images) && images > 0 ? images / 24 : plan.duree,
        sonAttendu: !!plan.corps?.withAudio,
      });
      plan.controle = { ok: c.ok, defauts: c.defauts };
      majPlan(filmId, i, { controle: plan.controle });
      // Correction automatique, budget d'une reprise par plan : même prompt, autre graine.
      if (!c.ok && (plan.reprises ?? 0) < 1 && plan.corps) {
        const [id] = await deps.queueTakes({ ...plan.corps, seed: Math.floor(Math.random() * 1e9) }, 1);
        majPlan(filmId, i, { take: id, reprises: (plan.reprises ?? 0) + 1, controle: undefined, controleRefuse: { take: t.id, defauts: c.defauts } });
        return;
      }
    }
    fichiers.push(t.output_path);
  }
  takes.patchSettings(filmId, { assemblage: 'en_cours' });
  pousser(filmId);
  const dossier = join(config.outputDir, 'films');
  mkdirSync(dossier, { recursive: true });
  const sortie = join(dossier, `film_${filmId}_${Date.now()}.mp4`);
  const t0 = Date.now();
  await new Promise<void>((ok, ko) =>
    execFile(config.ffmpegBin, argsAssemblage(fichiers, sortie, !!s.son), { maxBuffer: 1 << 24 }, (err, _o, stderr) =>
      err ? ko(new Error(`ffmpeg : ${String(stderr).split('\n').slice(-3).join(' ')}`)) : ok()),
  );
  takes.finish(filmId, sortie, (Date.now() - t0) / 1000);
  takes.patchSettings(filmId, { assemblage: 'fait', planTakes: sb.plans.map((p) => p.take) });
  pousser(filmId);
}

/** Films en attente de plans, pour la reprise après redémarrage. */
export function filmsEnAttente(): number[] {
  return takes.active().filter((t) => reglages(t).film === true).map((t) => t.id);
}
