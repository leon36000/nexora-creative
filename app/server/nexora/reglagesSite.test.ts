import { afterEach, describe, expect, it } from 'vitest';
import { moteurs, moteursPour } from '../engine.js';
import { appliquerReglagesLlm, modelePour } from './llm.js';
import { appliquerReglagesSite, lireReglagesSite, type ReglagesSite } from './reglagesSite.js';

const idsEnv = moteurs.map((m) => m.id); // les moteurs que l'environnement du poste définit
const reponse = (corps: unknown, status = 200) => (async () => new Response(JSON.stringify(corps), { status })) as unknown as typeof fetch;

const config = (): ReglagesSite => ({
  configured: true,
  updatedAt: '2026-10-31T12:00:00.000Z',
  llm: { default: 'glm-5.3', roles: { moderation: 'nexora-local-8b' } },
  engines: [
    { id: 'rtx5090', label: 'RTX 5090', kind: 'local', baseUrl: 'http://10.0.0.5:8189/', comfyUrl: 'http://10.0.0.5:8188', recipes: ['h3-fast', 'h3-max'] },
    { id: 'comfy-cloud', label: 'Comfy Cloud', kind: 'cloud', baseUrl: 'https://cloud.comfy.org', comfyUrl: 'https://cloud.comfy.org', recipes: ['qwen'], apiKey: 'CLE-CLOUD' },
  ],
});

afterEach(() => appliquerReglagesSite({ configured: false }));

describe('lecture des réglages du site', () => {
  it('envoie le jeton du service et rend la configuration, ou « rien de configuré »', async () => {
    let vu = '';
    const f = (async (_u: string, init: RequestInit) => { vu = String((init.headers as Record<string, string>).authorization); return new Response(JSON.stringify(config())); }) as unknown as typeof fetch;
    expect(await lireReglagesSite('https://site.example/', 'jeton-service', f)).toMatchObject({ configured: true });
    expect(vu).toBe('Bearer jeton-service');
    expect(await lireReglagesSite('https://site.example', 'j', reponse({ configured: false }))).toEqual({ configured: false });
  });

  it('site injoignable, jeton refusé ou réponse illisible : null (on garde les derniers réglages)', async () => {
    expect(await lireReglagesSite('https://site.example', 'j', reponse({ error: 'unauthorized' }, 401))).toBeNull();
    expect(await lireReglagesSite('https://site.example', 'j', (async () => { throw new Error('réseau'); }) as unknown as typeof fetch)).toBeNull();
    expect(await lireReglagesSite('https://site.example', 'j', (async () => new Response('pas du json')) as unknown as typeof fetch)).toBeNull();
  });
});

describe('application des réglages', () => {
  it('applique le modèle LLM par rôle (avant l’environnement) et les moteurs, le moteur principal restant en tête', () => {
    moteurs[0].recettes = ['qwen21', 'qwen', 'flux2', 'music3']; // comme le poste de développement : le principal ne porte pas H3
    const r = appliquerReglagesSite(config());
    expect(r).toEqual({ moteurs: 2, ignores: [] });
    expect(modelePour('moderation', { NEXORA_LLM_MODELE: 'poste' } as NodeJS.ProcessEnv)).toBe('nexora-local-8b');
    expect(modelePour('boost', { NEXORA_LLM_MODELE: 'poste' } as NodeJS.ProcessEnv)).toBe('glm-5.3');
    expect(moteurs[0].id).toBe('principal');
    expect(moteurs.map((m) => m.id)).toEqual(expect.arrayContaining(['rtx5090', 'comfy-cloud']));
    expect(moteursPour('h3-fast')[0].id).toBe('rtx5090');
    expect(moteurs.find((m) => m.id === 'rtx5090')?.baseUrl).toBe('http://10.0.0.5:8189');
    expect(moteurs.find((m) => m.id === 'comfy-cloud')?.cle).toBe('CLE-CLOUD');
  });

  it('ignore et signale un moteur cloud dont la clé est illisible, au lieu de l’appeler sans clé', () => {
    const c = config();
    c.engines[1] = { ...c.engines[1], apiKey: undefined, keyError: 'secret_unavailable' };
    const msgs: string[] = [];
    expect(appliquerReglagesSite(c, (m) => msgs.push(m))).toEqual({ moteurs: 1, ignores: ['comfy-cloud'] });
    expect(moteurs.some((m) => m.id === 'comfy-cloud')).toBe(false);
    expect(msgs[0]).toMatch(/comfy-cloud/);
    expect(msgs.join()).not.toMatch(/CLE-CLOUD/);
  });

  it('« rien de configuré » rétablit l’environnement du poste', () => {
    appliquerReglagesSite(config());
    appliquerReglagesSite({ configured: false });
    expect(modelePour('boost', {} as NodeJS.ProcessEnv)).toBeNull();
    expect(moteurs.map((m) => m.id)).toEqual(idsEnv);
    expect(moteurs.some((m) => m.id === 'comfy-cloud')).toBe(false);
    appliquerReglagesLlm(null);
  });
});
