/** Préparation stricte AMD v2 puis calcul existant, sans jugement ni promotion. */
import * as childProcess from 'node:child_process';
import { fileURLToPath } from 'node:url';
import { compareApparie, type Paire } from './stats.js';

interface Preparation {
  statut: 'paires_pretes_sans_promotion';
  corpus_sha256: string;
  protocole_sha256: string;
  observations_sha256: string;
  nombre_briefs_test: number;
  nombre_campagnes_test: number;
  reference: Record<string, number[]>;
  candidate: Record<string, number[]>;
  [key: string]: unknown;
}

/** Le protocole est épinglé par un SHA fourni indépendamment des observations. */
export function comparerAmd2(corpus: string, protocole: string, observations: string, shaProtocole: string): { preparation: Preparation; comparaison: Paire } {
  const script = fileURLToPath(new URL('./corpus-amd-v2/apparier.py', import.meta.url));
  const execution = childProcess.spawnSync('/usr/bin/python3', [script, corpus, protocole, observations, '--sha-protocole', shaProtocole], {
    encoding: 'utf8', maxBuffer: 8 * 1024 * 1024, timeout: 30_000,
    env: { PATH: '/usr/bin:/bin', PYTHONDONTWRITEBYTECODE: '1', PYTHONNOUSERSITE: '1' },
  });
  if (execution.error || execution.status !== 0) throw new Error('Préparation AMD v2 refusée : ' + (execution.stderr?.trim() || 'erreur du processus'));
  const preparation = JSON.parse(execution.stdout) as Preparation;
  const comparaison = compareApparie(preparation.reference, preparation.candidate);
  if (comparaison.n !== preparation.nombre_briefs_test) throw new Error('Nombre de briefs appariés incohérent');
  return { preparation, comparaison };
}
