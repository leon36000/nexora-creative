import { readFileSync } from 'node:fs';
import { runInNewContext } from 'node:vm';
import { join } from 'node:path';
import ts from 'typescript';
import { expect, it, vi } from 'vitest';

function route(exporterProres: (...args: any[]) => Promise<string>) {
  const src = readFileSync(new URL('../index.ts', import.meta.url), 'utf8');
  const ast = ts.createSourceFile('index.ts', src, ts.ScriptTarget.Latest, true, ts.ScriptKind.TS);
  let callback: ts.Expression | undefined;
  const visiter = (n: ts.Node) => {
    if (ts.isCallExpression(n) && n.expression.getText(ast) === 'app.get' && n.arguments[0]?.getText(ast) === "'/api/nexora/film/:id/export'") callback = n.arguments[1];
    ts.forEachChild(n, visiter);
  };
  visiter(ast); if (!callback) throw new Error('route absente');
  const code = ts.transpileModule(`globalThis.handler = ${callback.getText(ast)}`, { compilerOptions: { target: ts.ScriptTarget.ES2022 } }).outputText;
  const envoyer = vi.fn((stream: unknown) => stream);
  const reply = { header: vi.fn().mockReturnThis(), send: envoyer };
  const contexte = { exporterProres, takes: { get: () => ({ id: 1, status: 'done', output_path: '/synthetique/input.mp4', shot_name: 'essai' }) }, config: { outputDir: '/synthetique' }, join, createReadStream: (p: string) => p, safeShotName: (s: string) => s };
  runInNewContext(code, contexte);
  return { handler: (contexte as typeof contexte & { handler: (req: unknown, reply: unknown) => Promise<unknown> }).handler, reply, envoyer };
}

it('la route attend le fichier publié avant reply.send', async () => {
  let finir!: (p: string) => void;
  const r = route(() => new Promise<string>((resolve) => { finir = resolve; }));
  const resultat = r.handler({ params: { id: 1 } }, r.reply);
  await Promise.resolve(); expect(r.envoyer).not.toHaveBeenCalled();
  finir('/synthetique/complet.mov'); await resultat;
  expect(r.envoyer).toHaveBeenCalledWith('/synthetique/complet.mov');
});

it('la route ne sert rien si la production échoue', async () => {
  const r = route(async () => { throw new Error('échec synthétique'); });
  await expect(r.handler({ params: { id: 1 } }, r.reply)).rejects.toThrow('échec synthétique');
  expect(r.envoyer).not.toHaveBeenCalled();
});
