import { describe, expect, it } from 'vitest';
import { once } from 'node:events';
import { Worker } from 'node:worker_threads';
import { extraireDialoguesH3 } from './dialoguesH3.js';

describe('blocs de dialogue H3', () => {
  it('conserve langues, répliques et ordre, en retirant les blancs du texte', () => {
    expect(extraireDialoguesH3('<d>[French] \tÇa y est.\n</d> puis <d>[English]\uFEFFLet’s go. </d>')).toEqual([
      { langue: 'French', texte: 'Ça y est.' }, { langue: 'English', texte: 'Let’s go.' },
    ]);
    expect(extraireDialoguesH3('<d>[ 日本語 ] 🎬\u0085 </d>')).toEqual([{ langue: ' 日本語 ', texte: '🎬\u0085' }]);
  });

  it('garde les doublons et les textes vides pour la validation du contexte', () => {
    expect(extraireDialoguesH3('<d>[French] </d><d>[French]Oui</d><d>[French]Oui</d>')).toEqual([
      { langue: 'French', texte: '' }, { langue: 'French', texte: 'Oui' }, { langue: 'French', texte: 'Oui' },
    ]);
  });

  it('ignore les langues vides et retrouve le bloc suivant', () => {
    expect(extraireDialoguesH3('<d>[] Ignoré</d><d>[English]Go.</d>')).toEqual([{ langue: 'English', texte: 'Go.' }]);
  });

  it('ne fabrique pas de bloc lorsque des délimiteurs manquent', () => {
    for (const texte of ['', '<d>', '<d>[French', '<d>[French] sans fermeture', '</d>']) {
      expect(extraireDialoguesH3(texte)).toEqual([]);
    }
    expect(extraireDialoguesH3('<d>[French]Oui</d><d>[English]incomplet')).toEqual([{ langue: 'French', texte: 'Oui' }]);
  });

  it('termine aussi sur de grandes suites incomplètes dans un worker borné', async () => {
    const worker = new Worker(new URL('../../scripts/test-dialogues-h3-worker.mjs', import.meta.url), {
      env: {}, resourceLimits: { maxOldGenerationSizeMb: 64 },
    });
    try {
      const [resultat] = await once(worker, 'message', { signal: AbortSignal.timeout(5000) });
      expect(resultat).toBe('ok');
    } finally {
      await worker.terminate();
    }
  }, 10000);
});
