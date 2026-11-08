import { describe, expect, it } from 'vitest';
import { spawnSync } from 'node:child_process';
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

  it('termine aussi sur de grandes suites incomplètes dans un enfant borné', () => {
    const moduleUrl = new URL('./dialoguesH3.ts', import.meta.url).href;
    const programme = `
      import { extraireDialoguesH3 } from ${JSON.stringify(moduleUrl)};
      const cas = ['<d>['.repeat(250000), '<d>[French]'.repeat(100000), '<d>[French]' + ' '.repeat(1000000)];
      for (const texte of cas) {
        if (extraireDialoguesH3(texte).length !== 0) throw new Error('Bloc incomplet accepté');
      }
      console.log('ok');
    `;
    const enfant = spawnSync(process.execPath, ['--input-type=module', '-e', programme], { env: {}, timeout: 5000, encoding: 'utf8' });
    expect(enfant.error).toBeUndefined();
    expect(enfant.status).toBe(0);
    expect(enfant.stdout.trim()).toBe('ok');
  }, 10000);
});
