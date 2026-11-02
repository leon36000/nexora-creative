import { afterEach, describe, expect, it } from 'vitest';
import { appliquerReglagesLlm, clientLlmDepuisEnv, modelePour } from './llm.js';

afterEach(() => appliquerReglagesLlm(null));

describe('modèle LLM par rôle', () => {
  const env = { NEXORA_LLM_MODELE: 'poste/defaut', NEXORA_LLM_MODELE_BOOST: 'poste/boost' } as NodeJS.ProcessEnv;
  it('suit l’ordre : réglage du site pour le rôle, variable du rôle, réglage du site par défaut, variable par défaut', () => {
    expect(modelePour('redaction', env)).toBe('poste/defaut');
    expect(modelePour('boost', env)).toBe('poste/boost');
    appliquerReglagesLlm({ defaut: 'site/defaut' });
    expect(modelePour('redaction', env)).toBe('site/defaut');
    expect(modelePour('boost', env)).toBe('poste/boost');
    appliquerReglagesLlm({ defaut: 'site/defaut', roles: { boost: 'site/boost' } });
    expect(modelePour('boost', env)).toBe('site/boost');
  });
  it('le juge a un modèle vision par défaut, remplaçable par rôle, jamais écrasé par le modèle général', () => {
    expect(modelePour('juge', env)).toBe('qwen/qwen3.8-27b');
    expect(modelePour('juge', { ...env, NEXORA_LLM_MODELE_JUGE: 'poste/vision' } as NodeJS.ProcessEnv)).toBe('poste/vision');
    appliquerReglagesLlm({ defaut: 'site/defaut' });
    expect(modelePour('juge', env)).toBe('qwen/qwen3.8-27b');
  });
  it('sans aucun réglage, aucun modèle', () => {
    expect(modelePour('idees', {} as NodeJS.ProcessEnv)).toBeNull();
  });
});

describe('appel avec outils (agent Producteur)', () => {
  const env = { NEXORA_LLM_BASE_URL: 'http://passerelle/v1', NEXORA_LLM_CLE: 'k', NEXORA_LLM_MODELE: 'm/defaut' } as NodeJS.ProcessEnv;
  it('envoie les outils et lit les appels de fonction (arguments JSON)', async () => {
    let envoye: any;
    const f = (async (_u: string, init: any) => {
      envoye = JSON.parse(init.body);
      return new Response(JSON.stringify({ choices: [{ message: { content: null, tool_calls: [{ id: 'c1', type: 'function', function: { name: 'devis', arguments: '{"plans":2}' } }] } }], usage: { prompt_tokens: 10, completion_tokens: 5 } }));
    }) as unknown as typeof fetch;
    const llm = clientLlmDepuisEnv(env, f)!;
    const r = await llm.completerAvecOutils!('producteur', [{ role: 'user', content: 'pub' }], [{ nom: 'devis', description: 'd', parametres: { type: 'object', properties: {} } }], { maxTokens: 500 });
    expect(envoye.tools[0]).toEqual({ type: 'function', function: { name: 'devis', description: 'd', parameters: { type: 'object', properties: {} } } });
    expect(envoye.max_tokens).toBe(500);
    expect(r.appels).toEqual([{ id: 'c1', nom: 'devis', arguments: { plans: 2 } }]);
    expect(r.texte).toBe('');
    expect(r.jetons).toBe(15);
  });
  it('des arguments illisibles deviennent un objet vide marqué, sans planter', async () => {
    const f = (async () => new Response(JSON.stringify({ choices: [{ message: { content: 'ok', tool_calls: [{ id: 'c2', function: { name: 'x', arguments: '{oups' } }] } }] }))) as unknown as typeof fetch;
    const r = await clientLlmDepuisEnv(env, f)!.completerAvecOutils!('producteur', [{ role: 'user', content: 'a' }], []);
    expect(r.appels[0]).toEqual({ id: 'c2', nom: 'x', arguments: {}, illisible: true });
    expect(r.texte).toBe('ok');
  });
});
