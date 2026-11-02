/**
 * Compétences des rôles LLM (recherche/06 §6.2, voie A) : des procédures courtes et versionnées, écrites dans
 * `server/nexora/competences/<nom>.md` (en-tête name, version, roles, description), ajoutées au message système des
 * rôles qui les déclarent. Ce sont des textes : le serveur n'exécute jamais rien de ce qu'ils contiennent.
 * Stables d'un appel à l'autre, donc cachables par la passerelle ; plafond de ~8 000 jetons par rôle (vérifié par test).
 */
import { readdirSync, readFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';
import type { RoleLlm } from './llm.js';

export interface Competence {
  nom: string;
  version: number;
  roles: string[];
  description: string;
  texte: string;
}

const DOSSIER = join(dirname(fileURLToPath(import.meta.url)), 'competences');

export function lireCompetence(source: string, fichier: string): Competence {
  const m = source.match(/^---\n([\s\S]*?)\n---\n?([\s\S]*)$/);
  if (!m) throw new Error(`${fichier} : en-tête --- absent`);
  const champs = Object.fromEntries(
    m[1].split('\n').map((l) => l.match(/^(\w+):\s*(.*)$/)).filter((x): x is RegExpMatchArray => !!x).map((x) => [x[1], x[2].trim()]),
  );
  const roles = (champs.roles ?? '').replace(/^\[|\]$/g, '').split(',').map((r) => r.trim()).filter(Boolean);
  const version = Number(champs.version);
  if (!champs.name || !Number.isInteger(version) || version < 1 || !roles.length) throw new Error(`${fichier} : name, version et roles sont obligatoires`);
  return { nom: champs.name, version, roles, description: champs.description ?? '', texte: m[2].trim() };
}

let cache: Competence[] | null = null;
export function listeCompetences(): Competence[] {
  cache ??= readdirSync(DOSSIER).filter((f) => f.endsWith('.md')).sort().map((f) => lireCompetence(readFileSync(join(DOSSIER, f), 'utf8'), f));
  return cache;
}

/** Texte à ajouter au message système d'un rôle (vide s'il n'a aucune compétence). */
export function competencesPour(role: RoleLlm): string {
  return listeCompetences()
    .filter((c) => c.roles.includes(role))
    .map((c) => `[compétence ${c.nom} v${c.version}]\n${c.texte}`)
    .join('\n\n');
}

/** Message système = consignes du rôle + ses compétences. */
export function avecCompetences(role: RoleLlm, consignes: string): string {
  const c = competencesPour(role);
  return c ? `${consignes}\n\n${c}` : consignes;
}
