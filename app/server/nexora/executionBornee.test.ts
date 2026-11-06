import { expect, it } from 'vitest';
import { executerBorne } from './executionBornee.js';

it('conserve la sortie et signale un code non nul', async () => {
  await expect(executerBorne(process.execPath, ['-e', 'process.stdout.write("ok")'], 5000)).resolves.toBe('ok');
  await expect(executerBorne(process.execPath, ['-e', 'process.exit(7)'], 5000)).rejects.toThrow('code 7');
});

it('borne l’attente et ne prétend pas certifier l’arrêt', async () => {
  const debut = Date.now();
  await expect(executerBorne(process.execPath, ['-e', 'setTimeout(()=>{},4000)'], 50)).rejects.toThrow('arrêt de l’enfant non confirmé');
  expect(Date.now() - debut).toBeLessThan(3000);
});

it('traite un flux long par blocs et refuse une erreur du consommateur', async () => {
  let total = 0;
  await expect(executerBorne(process.execPath, ['-e', 'process.stdout.write(Buffer.alloc(1100000, 65))'], 5000, (bloc) => { total += bloc.length; })).resolves.toBe('');
  expect(total).toBe(1100000);
  await expect(executerBorne(process.execPath, ['-e', 'process.stdout.write("x")'], 5000, () => { throw new Error('synthetique'); })).rejects.toThrow('Flux de sortie invalide');
});
