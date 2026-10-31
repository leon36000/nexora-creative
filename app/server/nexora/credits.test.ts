import { describe, expect, it } from 'vitest';
import { actionFacturation, devisCredits, facturationSite, secondesGpuEstimees } from './credits.js';

describe('devis en crédits d’un rendu', () => {
  it('estime le temps GPU depuis les mesures du GB10 et le convertit en crédits entiers', () => {
    expect(secondesGpuEstimees({ videoModel: 'h3-fast', lengthFrames: 124, width: 832, height: 480 })).toBe(85);
    expect(secondesGpuEstimees({ videoModel: 'h3-fast', lengthFrames: 243, width: 832, height: 480 })).toBe(230);
    expect(secondesGpuEstimees({ videoModel: 'h3-fast', lengthFrames: 124, width: 1344, height: 768 })).toBe(340);
    expect(secondesGpuEstimees({ videoModel: 'h3-fast', lengthFrames: 124, width: 768, height: 1344 })).toBe(340);
    const cinq = devisCredits({ videoModel: 'h3-fast', lengthFrames: 124, width: 832, height: 480 }, { creditsParSecondeGpu: 0.5 });
    expect(cinq).toBe(43);
    expect(Number.isInteger(devisCredits({ videoModel: 'wan22', frames: 121, width: 832, height: 480 }, { creditsParSecondeGpu: 0.5 }))).toBe(true);
  });

  it('coûte plus cher pour plus de pixels', () => {
    const petit = devisCredits({ videoModel: 'h3-fast', lengthFrames: 124, width: 832, height: 480 }, { creditsParSecondeGpu: 1 });
    const grand = devisCredits({ videoModel: 'h3-fast', lengthFrames: 124, width: 1344, height: 768 }, { creditsParSecondeGpu: 1 });
    expect(grand).toBeGreaterThan(petit);
  });
});

describe('suite de la facturation d’une prise', () => {
  const reserve = { reservationId: 'r1', credits: 43, etat: 'reservee' as const };
  it('valide au succès, libère à l’échec ou à l’arrêt, ne refait rien ensuite', () => {
    expect(actionFacturation({ status: 'done', credits: reserve })).toBe('valider');
    expect(actionFacturation({ status: 'failed', credits: reserve })).toBe('liberer');
    expect(actionFacturation({ status: 'stopped', credits: reserve })).toBe('liberer');
    expect(actionFacturation({ status: 'rendering', credits: reserve })).toBeNull();
    expect(actionFacturation({ status: 'done', credits: { ...reserve, etat: 'validee' as const } })).toBeNull();
    expect(actionFacturation({ status: 'done', credits: undefined })).toBeNull();
    // Plan relancé après une panne : la réservation suit la nouvelle prise, l'ancienne ne la libère pas.
    expect(actionFacturation({ status: 'failed', credits: { ...reserve, etat: 'transferee' as const } })).toBeNull();
  });
});

describe('API de crédits du site Nexora', () => {
  it('réserve, valide et libère avec la clé de l’organisation ; 402 devient un refus lisible', async () => {
    const appels: { url: string; corps: any; auth: string | null }[] = [];
    const f = (async (url: string, init: RequestInit) => {
      const corps = JSON.parse(String(init.body));
      appels.push({ url, corps, auth: new Headers(init.headers).get('authorization') });
      if (url.endsWith('/reserve') && corps.credits > 1000) {
        return new Response(JSON.stringify({ error: { code: 'insufficient_quota', message: 'Il ne vous reste plus de crédits.' } }), { status: 402 });
      }
      return new Response(JSON.stringify(url.endsWith('/reserve') ? { reservationId: 'res-1', credits: corps.credits } : { ok: true }), { status: 200 });
    }) as unknown as typeof fetch;
    const fac = facturationSite('https://site.test', () => 'nxk_cle', f);
    expect(await fac.reserver({ idempotence: 'k1', credits: 43, libelle: 'Nexora Creative · vidéo' })).toEqual({ ok: true, reservationId: 'res-1', credits: 43 });
    expect(await fac.reserver({ idempotence: 'k2', credits: 5000, libelle: 'x' })).toEqual({ ok: false, message: 'Il ne vous reste plus de crédits.' });
    await fac.valider('res-1', 43);
    await fac.liberer('res-2');
    expect(appels.map((a) => a.url)).toEqual([
      'https://site.test/api/creative/credits/reserve', 'https://site.test/api/creative/credits/reserve',
      'https://site.test/api/creative/credits/settle', 'https://site.test/api/creative/credits/release',
    ]);
    expect(appels.every((a) => a.auth === 'Bearer nxk_cle')).toBe(true);
    expect(appels[0].corps).toEqual({ idempotencyKey: 'k1', credits: 43, label: 'Nexora Creative · vidéo' });
  });
});
