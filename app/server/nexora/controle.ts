/**
 * Contrôle qualité déterministe d'une prise, avant tout juge par IA (la littérature montre les juges VLM peu fiables
 * sur les artefacts : recherche/07). ffmpeg mesure la durée, les passages noirs, l'image figée et le volume ; le code
 * décide. Un plan refusé est repris automatiquement par le Director avec une autre graine (filmMoteur.ts).
 */
import { execFile } from 'node:child_process';

export interface Mesures {
  duree: number;
  noirS: number;
  figeS: number;
  volumeMoyenDb: number | null;
  volumeMaxDb: number | null;
}

export interface Verdict {
  ok: boolean;
  defauts: string[];
}

export function argsControle(fichier: string, son: boolean): string[] {
  return [
    '-hide_banner', '-nostats', '-i', fichier,
    '-vf', 'blackdetect=d=0.4:pix_th=0.08,freezedetect=n=-60dB:d=1.5',
    ...(son ? ['-af', 'volumedetect'] : ['-an']),
    '-f', 'null', '-',
  ];
}

export function analyserSortieFfmpeg(sortie: string): Mesures {
  const d = sortie.match(/Duration: (\d+):(\d+):(\d+(?:\.\d+)?)/);
  const duree = d ? Number(d[1]) * 3600 + Number(d[2]) * 60 + Number(d[3]) : 0;
  const noirS = [...sortie.matchAll(/black_duration:(\d+(?:\.\d+)?)/g)].reduce((n, m) => n + Number(m[1]), 0);
  // Une image figée jusqu'à la fin n'a pas de freeze_end : elle court jusqu'à la durée totale.
  const debuts = [...sortie.matchAll(/freeze_start: (\d+(?:\.\d+)?)/g)].map((m) => Number(m[1]));
  const fins = [...sortie.matchAll(/freeze_end: (\d+(?:\.\d+)?)/g)].map((m) => Number(m[1]));
  const figeS = debuts.reduce((n, debut, i) => n + ((fins[i] ?? duree) - debut), 0);
  const vm = sortie.match(/mean_volume: (-?\d+(?:\.\d+)?) dB/);
  const vx = sortie.match(/max_volume: (-?\d+(?:\.\d+)?) dB/);
  const arrondi = (x: number) => Math.round(x * 100) / 100;
  return {
    duree: arrondi(duree),
    noirS: arrondi(noirS),
    figeS: arrondi(figeS),
    volumeMoyenDb: vm ? Number(vm[1]) : null,
    volumeMaxDb: vx ? Number(vx[1]) : null,
  };
}

export function verdictControle(m: Mesures, attendu: { dureeAttendue: number; sonAttendu: boolean }): Verdict {
  const defauts: string[] = [];
  if (Math.abs(m.duree - attendu.dureeAttendue) > 0.5) defauts.push(`durée ${m.duree} s au lieu de ${attendu.dureeAttendue.toFixed(2)} s`);
  if (m.noirS > Math.min(1, m.duree * 0.2)) defauts.push(`image noire pendant ${m.noirS} s`);
  if (m.figeS > Math.max(1.5, m.duree * 0.4)) defauts.push(`image figée pendant ${m.figeS} s`);
  if (attendu.sonAttendu) {
    if (m.volumeMaxDb === null) defauts.push('piste son absente');
    else if (m.volumeMaxDb < -45) defauts.push(`son quasi silencieux (crête ${m.volumeMaxDb} dB)`);
  }
  return { ok: defauts.length === 0, defauts };
}

export function controlerFichier(ffmpeg: string, fichier: string, attendu: { dureeAttendue: number; sonAttendu: boolean }): Promise<Mesures & Verdict> {
  return new Promise((ok, ko) =>
    execFile(ffmpeg, argsControle(fichier, attendu.sonAttendu), { maxBuffer: 1 << 24 }, (err, _o, stderr) => {
      if (err) return ko(new Error(`contrôle impossible : ${String(stderr).split('\n').slice(-2).join(' ')}`));
      const m = analyserSortieFfmpeg(String(stderr));
      ok({ ...m, ...verdictControle(m, attendu) });
    }),
  );
}
