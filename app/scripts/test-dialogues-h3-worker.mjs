import { parentPort } from 'node:worker_threads';
import { extraireDialoguesH3 } from '../server/nexora/dialoguesH3.ts';

if (!parentPort) throw new Error('Ce contrôle doit être exécuté dans son worker de test.');
const cas = ['<d>['.repeat(250000), '<d>[French]'.repeat(100000), '<d>[French]' + ' '.repeat(1000000)];
for (const texte of cas) {
  if (extraireDialoguesH3(texte).length !== 0) throw new Error('Bloc incomplet accepté');
}
parentPort.postMessage('ok');
