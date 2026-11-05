import { mkdtempSync } from 'node:fs';
import { join } from 'node:path';

/** Une opération reçoit son propre répertoire créé atomiquement ; les essais restent conservés. */
export function dossierFilmUnique(parent: string, filmId: number): string {
  return mkdtempSync(join(parent, `film_${filmId}_`));
}

/** Les générateurs existants utilisent -y ; ce parcours refuse toute destination préexistante. */
export function sansEcrasement(args: string[]): string[] {
  if (args[0] !== '-y') throw new Error('Option ffmpeg inattendue');
  return ['-n', ...args.slice(1)];
}
