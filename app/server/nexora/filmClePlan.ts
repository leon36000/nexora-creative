import { createHash } from 'node:crypto';
import type { PlanFilm, Storyboard } from './film.js';

/** Identité conservatrice d'un plan dans son contexte de film, sans graine ni état de prise. */
export function clePlanFilm(sb: Storyboard, plan: PlanFilm, contexte: { moteur: string; format: string; son: boolean; qualite?: string; projectId?: number | null; intention: string; references?: string[]; ancre?: number | null }): string {
  // La graine aléatoire n'existe pas encore à ce stade ; aucune valeur éphémère n'est incluse.
  const contenu = [contexte.moteur, contexte.format, contexte.son, contexte.qualite ?? null, contexte.projectId ?? null, contexte.intention, contexte.references ?? [], contexte.ancre ?? null,
    sb.bible.style, sb.bible.personnages, sb.bible.lieux, plan.resume, plan.description, plan.camera, plan.duree, plan.replique ?? null, plan.suite === true];
  if (sb.langue === 'en') contenu.push('langue:en');
  return createHash('sha256').update(JSON.stringify(contenu)).digest('hex');
}

export class PlanDejaEnCours extends Error {
  constructor(public readonly takeId: number, public readonly filmId: number, public readonly plan: number) {
    super('Ce plan possède déjà une prise en cours ou une soumission indéterminée ; vérifie-la avant de réessayer.');
  }
}

/** Transaction SQLite IMMEDIATE : vérification et insertion sont sérialisées entre processus. */
export function creerPriseSiPlanLibre<T>(db: { transaction: (fn: () => T) => { immediate: () => T }; prepare: (sql: string) => { get: (...args: any[]) => unknown } }, organisation: string, cle: string, filmId: number, creer: () => T): T {
  return db.transaction(() => {
    const conflit = db.prepare(`SELECT id, json_extract(settings, '$.nexoraFilm') AS film, json_extract(settings, '$.nexoraPlan') AS plan FROM takes WHERE organisation_id = ? AND json_valid(settings)
      AND json_extract(settings, '$.nexoraClePlan') = ?
      AND COALESCE(json_extract(settings, '$.nexoraFilm'), 0) <> ?
      AND (status IN ('queued', 'rendering') OR json_extract(settings, '$.nexoraSoumission') = 'indeterminee') LIMIT 1`).get(organisation, cle, filmId) as { id: number; film: number; plan: number } | undefined;
    if (conflit) throw new PlanDejaEnCours(conflit.id, conflit.film, conflit.plan);
    return creer();
  }).immediate();
}
