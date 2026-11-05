import { expect, it, vi } from 'vitest';
import { creerVerificationArrets, statutTerminalConfirme } from './reconciliationArrets.js';
import { readFileSync } from 'node:fs';
import ts from 'typescript';

it('parcourt équitablement des lots bornés et conserve erreurs, non-terminaux et appels bloqués', async () => {
  const restants = new Set(Array.from({ length: 15 }, (_, i) => i + 1));
  const confirmer = vi.fn((id: number) => { restants.delete(id); });
  const lire = vi.fn((apres: number, limite: number) => [...restants].filter((id) => id > apres).slice(0, limite).map((id) => ({ id, prompt_id: `p${id}` })));
  const etat = vi.fn(async (prompt: string) => {
    if (prompt === 'p2') return false;
    if (prompt === 'p3') throw new Error('moteur inaccessible');
    if (prompt === 'p4') return new Promise<boolean>(() => {});
    return true;
  });
  const verifier = creerVerificationArrets(lire, etat, confirmer, 5);
  for (let i = 0; i < 8; i++) await verifier();
  expect([...restants].sort((a, b) => a - b)).toEqual([2, 3, 4]);
  expect(etat.mock.calls.filter(([p]) => p === 'p4')).toHaveLength(1);
  expect(lire.mock.calls.every(([, limite]) => limite === 10)).toBe(true);
  expect(statutTerminalConfirme('expired')).toBe(false);
  expect(statutTerminalConfirme('running')).toBe(false);
  expect(statutTerminalConfirme('cancelled')).toBe(true);
});

it('lit uniquement le moteur connu avec un signal borné et refuse expired ou moteur disparu', async () => {
  const texte = readFileSync(new URL('../engine.ts', import.meta.url), 'utf8');
  const source = ts.createSourceFile('engine.ts', texte, ts.ScriptTarget.Latest, true, ts.ScriptKind.TS);
  const fn = source.statements.find((n) => ts.isFunctionDeclaration(n) && n.name?.text === 'etatTerminalConfirme');
  if (!fn) throw new Error('lecture moteur introuvable');
  const js = ts.transpileModule(fn.getText(source).replace(/^export\s+/, ''), { compilerOptions: { target: ts.ScriptTarget.ES2022, module: ts.ModuleKind.None } }).outputText;
  let statut = 'expired';
  const getJob = vi.fn(async (_id: string, opts: { signal: AbortSignal }) => { expect(opts.signal).toBeInstanceOf(AbortSignal); return { status: statut }; });
  class ComfyLow { getJob = getJob; }
  const deps = { jobMoteur: new Map([['job', 'gpu-a'], ['absent', 'gpu-retire']]), moteurs: [{ id: 'gpu-a', baseUrl: 'http://fictif' }], lecturesJobs: new Map(), ComfyLow, config: {}, statutTerminalConfirme };
  const lire = new Function(...Object.keys(deps), `${js}; return etatTerminalConfirme;`)(...Object.values(deps));
  expect(await lire('job')).toBe(false);
  statut = 'succeeded';
  expect(await lire('job')).toBe(true);
  expect(await lire('absent')).toBe(false);
  expect(await lire('inconnu')).toBe(false);
  expect(getJob).toHaveBeenCalledTimes(2);
});

it('interrompt la lecture SDK fictive quand le signal de quatre secondes expire', async () => {
  const texte = readFileSync(new URL('../engine.ts', import.meta.url), 'utf8');
  const source = ts.createSourceFile('engine.ts', texte, ts.ScriptTarget.Latest, true, ts.ScriptKind.TS);
  const fn = source.statements.find((n) => ts.isFunctionDeclaration(n) && n.name?.text === 'etatTerminalConfirme');
  if (!fn) throw new Error('lecture moteur introuvable');
  const js = ts.transpileModule(fn.getText(source).replace(/^export\s+/, ''), { compilerOptions: { target: ts.ScriptTarget.ES2022, module: ts.ModuleKind.None } }).outputText;
  const getJob = vi.fn((_id: string, opts: { signal: AbortSignal }) => new Promise((_resolve, reject) => {
    opts.signal.addEventListener('abort', () => reject(new Error('lecture interrompue')), { once: true });
  }));
  class ComfyLow { getJob = getJob; }
  const deps = { jobMoteur: new Map([['job', 'gpu-a']]), moteurs: [{ id: 'gpu-a', baseUrl: 'http://fictif' }], lecturesJobs: new Map(), ComfyLow, config: {}, statutTerminalConfirme };
  const lire = new Function(...Object.keys(deps), `${js}; return etatTerminalConfirme;`)(...Object.values(deps));
  await expect(lire('job')).rejects.toThrow('lecture interrompue');
  expect(getJob).toHaveBeenCalledOnce();
}, 10000);
