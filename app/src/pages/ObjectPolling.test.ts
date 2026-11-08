import { readFileSync } from 'node:fs';
import { runInNewContext } from 'node:vm';
import ts from 'typescript';
import { afterEach, describe, expect, it, vi } from 'vitest';

/** Exécute le callback réellement passé à useEffect pour la chaîne texte, sans navigateur ni réseau. */
function effetPolling(api: { objetTexteEtat: ReturnType<typeof vi.fn> }) {
  const source = readFileSync(new URL('./Object.tsx', import.meta.url), 'utf8');
  const ast = ts.createSourceFile('Object.tsx', source, ts.ScriptTarget.Latest, true, ts.ScriptKind.TSX);
  let callback: ts.Expression | undefined;
  const visiter = (node: ts.Node) => {
    if (ts.isCallExpression(node) && node.expression.getText(ast) === 'useEffect' && node.arguments.length === 2) {
      const deps = node.arguments[1];
      if (ts.isArrayLiteralExpression(deps) && deps.elements.map((x) => x.getText(ast)).join(',') === 'chaineId,c') callback = node.arguments[0];
    }
    ts.forEachChild(node, visiter);
  };
  visiter(ast);
  if (!callback) throw new Error('Effet de polling introuvable');
  const code = ts.transpileModule(`globalThis.effet = ${callback.getText(ast)};`, { compilerOptions: { target: ts.ScriptTarget.ES2022 } }).outputText;
  const contexte = { api, chaineId: 42, c: { requestFailure: 'erreur' }, setChaine: vi.fn(), setSelected: vi.fn(), toast: vi.fn(), setTimeout, clearTimeout };
  runInNewContext(code, contexte);
  return (contexte as typeof contexte & { effet: () => () => void }).effet;
}

describe('polling texte Mesh', () => {
  afterEach(() => vi.useRealTimers());

  it('annule le délai de l’ancienne langue avant de relancer avec la nouvelle', async () => {
    vi.useFakeTimers();
    const api = { objetTexteEtat: vi.fn().mockResolvedValue({ etat: 'image' }) };
    const effet = effetPolling(api);
    const retirerFrancais = effet();
    await vi.advanceTimersByTimeAsync(0);
    retirerFrancais();
    const retirerAnglais = effet();
    await vi.advanceTimersByTimeAsync(2500);
    expect(api.objetTexteEtat).toHaveBeenCalledTimes(3); // FR initial, EN initial, EN suivant
    retirerAnglais();
  });

  it('ne demande plus de statut après démontage', async () => {
    vi.useFakeTimers();
    const api = { objetTexteEtat: vi.fn().mockResolvedValue({ etat: 'image' }) };
    const retirer = effetPolling(api)();
    await vi.advanceTimersByTimeAsync(0);
    retirer();
    await vi.advanceTimersByTimeAsync(2500);
    expect(api.objetTexteEtat).toHaveBeenCalledTimes(1);
  });
});
