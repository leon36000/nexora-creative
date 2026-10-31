import { describe, expect, it } from 'vitest';
import { actionEspace, espaceSite } from './espace.js';

describe('espace disque de l’organisation (contrat recordStorageUsage du site)', () => {
  it('compte une prise terminée une seule fois', () => {
    expect(actionEspace({ status: 'done', output_path: '/a.mp4', espace: undefined })).toBe('compter');
    expect(actionEspace({ status: 'done', output_path: '/a.mp4', espace: { octets: 10, etat: 'compte' } })).toBeNull();
    expect(actionEspace({ status: 'rendering', output_path: null, espace: undefined })).toBeNull();
    expect(actionEspace({ status: 'failed', output_path: null, espace: undefined })).toBeNull();
  });

  it('envoie le delta en octets avec la clé de l’organisation ; quota dépassé devient un refus lisible', async () => {
    const corps: any[] = [];
    const f = (async (url: string, init: RequestInit) => {
      const b = JSON.parse(String(init.body));
      corps.push({ url, b, auth: new Headers(init.headers).get('authorization') });
      if (b.deltaBytes > 1e9) return new Response(JSON.stringify({ error: { code: 'quota_exceeded', message: 'Votre espace est plein.' } }), { status: 409 });
      return new Response(JSON.stringify({ ok: true }), { status: 200 });
    }) as unknown as typeof fetch;
    const e = espaceSite('https://site.test', () => 'nxk_k', f);
    expect(await e.enregistrer(5_000_000)).toEqual({ ok: true });
    expect(await e.enregistrer(2e9)).toEqual({ ok: false, message: 'Votre espace est plein.' });
    expect(await e.enregistrer(-5_000_000)).toEqual({ ok: true });
    expect(corps.map((c) => c.b.deltaBytes)).toEqual([5_000_000, 2e9, -5_000_000]);
    expect(corps.every((c) => c.url === 'https://site.test/api/creative/storage' && c.auth === 'Bearer nxk_k')).toBe(true);
  });
});
