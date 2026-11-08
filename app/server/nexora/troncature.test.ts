import { describe, expect, it, vi } from 'vitest';
import { clientPalier, type AppelMesure } from './niveaux.js';

const env = { NEXORA_LLM_CLE_DEEPINFRA: 'factice' } as any;
const messages = [{ role: 'user' as const, content: 'test' }];
const response = (message: unknown, finish_reason: string) => async () => new Response(JSON.stringify({
  choices: [{ message, finish_reason }], usage: { prompt_tokens: 9, completion_tokens: 24, completion_tokens_details: { reasoning_tokens: 19 } },
}), { status: 200 });
const outil = (argumentsTexte: string) => ({ content: '', tool_calls: [{ id: 't1', function: { name: 'couper', arguments: argumentsTexte } }] });

describe('troncature fournisseur', () => {
  it('refuse le texte partiel même non vide', async () => {
    const c = clientPalier('eco', { env, f: response({ content: 'texte incomplet' }, 'length') as any });
    await expect(c.completer('monteur', messages)).rejects.toThrow(/tronqu/);
  });
  it.each(['{"debut":1}', '{"debut":'])('refuse un appel outil tronqué même avec JSON %s', async (args) => {
    const c = clientPalier('eco', { env, f: response(outil(args), 'length') as any });
    await expect(c.completerAvecOutils!('monteur', messages, [])).rejects.toThrow(/tronqu/);
  });
  it.each(['texte', 'outils'])('comptabilise une fois les jetons malgré la troncature %s', async (mode) => {
    const avant = vi.fn(), apres = vi.fn((_mesure: AppelMesure) => {});
    const c = clientPalier('eco', { env, f: response({content:'partiel'}, 'length') as any, surveillant: { avant, apres } });
    const appel = mode === 'texte' ? c.completer('monteur', messages) : c.completerAvecOutils!('monteur', messages, []);
    await expect(appel).rejects.toThrow(/tronqu/);
    expect(avant).toHaveBeenCalledTimes(1); expect(apres).toHaveBeenCalledTimes(1);
    expect(apres.mock.calls[0][0].usage).toMatchObject({ entree: 9, sortie: 24, raisonnement: 19 });
  });
  it('préserve le texte et les outils complets', async () => {
    const c = clientPalier('eco', { env, f: response({content:'texte complet'}, 'stop') as any });
    expect(await c.completer('monteur', messages)).toBe('texte complet');
    const o = clientPalier('eco', { env, f: response(outil('{"debut":1}'), 'tool_calls') as any });
    expect((await o.completerAvecOutils!('monteur', messages, [])).appels[0]).toMatchObject({nom:'couper',arguments:{debut:1}});
  });
});
