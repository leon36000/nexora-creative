import { describe, expect, it } from 'vitest';
import { clientPalier } from './niveaux.js';

describe('efforts des paliers montage', () => {
  it('conserve les efforts en mode outils et au repli Argon', async () => {
    const corps: any[] = [];
    const f = async (_url: any, init: any) => {
      const c = JSON.parse(init.body); corps.push(c);
      if (c.provider?.order[0] === 'google-ai-studio/flex') return new Response('{}', {status: 429});
      return new Response(JSON.stringify({choices: [{message: {content: 'ok'}, finish_reason: 'stop'}], usage: {prompt_tokens: 1, completion_tokens: 1}}), {status: 200});
    };
    const env = {NEXORA_LLM_CLE_DEEPINFRA: 'factice', NEXORA_LLM_CLE_OPENROUTER: 'factice'} as any;
    for (const palier of ['eco','equilibre','expert'] as const) {
      await clientPalier(palier,{env,f:f as any,tentatives:1,autoriserRepli:true,attendre:async()=>{}}).completerAvecOutils!('monteur',[{role:'user',content:'test'}],[]);
    }
    expect(corps.map(c => c.reasoning_effort ?? c.reasoning?.effort)).toEqual([100,'max','high','high']);
    expect(corps.map(c => c.max_tokens)).toEqual([2000,6000,4000,4000]);
    expect(corps[2].provider).toEqual({order:['google-ai-studio/flex'],allow_fallbacks:false});
    expect(corps[3].provider).toEqual({order:['google-vertex/global'],allow_fallbacks:false});
  });
  it('transmet au HTTP simulé les corps et garde le routage Flex et son repli autorisé', async () => {
    const corps: any[]=[];
    const f = async (_url: any, init: any) => {
      const c=JSON.parse(init.body);corps.push(c);
      if(c.provider?.order[0]==='google-ai-studio/flex') return new Response('{}',{status:429});
      return new Response(JSON.stringify({choices:[{message:{content:'ok'}}],usage:{prompt_tokens:1,completion_tokens:1}}),{status:200});
    };
    const env={NEXORA_LLM_CLE_DEEPINFRA:'factice',NEXORA_LLM_CLE_OPENROUTER:'factice'} as any;
    for(const palier of ['eco','equilibre','expert'] as const) await clientPalier(palier,{env,f:f as any,tentatives:1,autoriserRepli:true,attendre:async()=>{}}).completer('monteur',[{role:'user',content:'test'}]);
    expect(corps.map(c=>c.reasoning_effort ?? c.reasoning?.effort)).toEqual([100,'max','high','high']);
    expect(corps[2].provider).toEqual({order:['google-ai-studio/flex'],allow_fallbacks:false});
    expect(corps[3].provider).toEqual({order:['google-vertex/global'],allow_fallbacks:false});
    expect(corps.map(c=>c.max_tokens)).toEqual([8000,8000,8000,8000]);
  });
});
