import { afterEach, describe, expect, it } from 'vitest';
import { appliquerReglagesLlm, modelePour } from './llm.js';

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
  it('sans aucun réglage, aucun modèle', () => {
    expect(modelePour('idees', {} as NodeJS.ProcessEnv)).toBeNull();
  });
});
