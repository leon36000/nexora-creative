import { readFileSync } from 'node:fs';
import { runInNewContext } from 'node:vm';
import ts from 'typescript';
import { expect, it, vi } from 'vitest';

/** Extrait le callback de route original ; toutes les dépendances et soumissions sont factices. */
function preparer(langue: 'fr' | 'en' | undefined, role: 'depart' | 'composition') {
  const texte = readFileSync(new URL('../index.ts', import.meta.url), 'utf8');
  const ast = ts.createSourceFile('index.ts', texte, ts.ScriptTarget.Latest, true, ts.ScriptKind.TS);
  let callback: ts.Expression | undefined;
  const visiter = (n: ts.Node) => {
    if (ts.isCallExpression(n) && n.expression.getText(ast) === 'app.post' && n.arguments[0]?.getText(ast) === "'/api/nexora/film/:id/plan/:n/reference'") callback = n.arguments[1];
    ts.forEachChild(n, visiter);
  };
  visiter(ast); if (!callback) throw new Error('route de référence absente');
  const code = ts.transpileModule(`globalThis.handler = ${callback.getText(ast)}`, { compilerOptions: { target: ts.ScriptTarget.ES2022 } }).outputText;
  const ecrire = vi.fn(async (_entree: unknown, _llm: unknown) => ({ prompt: 'factice' }));
  const replique = langue === 'en' ? 'Let’s go!' : 'Où vas-tu ?';
  const contexte = {
    filmTerminePour: () => ({ film: {id:1}, s: {storyboard: {langue,titre:'Essai',plans:[{replique,resume:'test',duree:5}]},format:'16:9',son:true} }),
    eng:{readInput:async()=>true}, resoudrePersonnages:async()=>null, intentionDuPlan:()=> 'A person walks.',
    llmRedaction:()=>null, reecrireH3:ecrire, corpsRendu:()=>({}), moteurDuCompte:()=>true,
    referencesAvecComposition:()=>({sujets:[],jetons:[]}), corpsBrouillonDe:(x:unknown)=>x,
    lancerPrises:async()=>[12], majPlanStoryboard:()=>{}, takes:{get:()=>({})}, vuePrisesFilm:()=>({ok:true}),
  };
  runInNewContext(code, contexte);
  const handler = (contexte as typeof contexte & {handler:(req:unknown,reply:unknown)=>Promise<unknown>}).handler;
  return { ecrire, replique, lancer:()=>handler({params:{id:1,n:0},body:{role,jeton:'asset:00000000-0000-0000-0000-000000000000'}},{code:()=>({send:()=>{ throw new Error('erreur de route'); }})}) };
}

it.each([['en','depart','English','h3-fast'],['en','composition','English','h3-max'],['fr','depart','French','h3-fast'],[undefined,'composition','French','h3-max']] as const)('référence %s / %s garde langue et moteur', async (langue,role,attendue,moteur) => {
  const f=preparer(langue,role); await f.lancer();
  expect(f.ecrire).toHaveBeenCalledTimes(1);
  expect(f.ecrire.mock.calls[0][0]).toMatchObject({moteur, format:'16:9', langueClient:langue ?? 'fr', dialogues:[{texte:f.replique,langue:attendue}]});
});
