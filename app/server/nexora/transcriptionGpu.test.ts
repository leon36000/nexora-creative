import { afterEach, describe, expect, it, vi } from 'vitest';
import { transcrireSurGpu } from './transcriptionGpu.js';

const url = 'http://gpu.test:8190';
const audio = Buffer.from([82, 73, 70, 70]);
const transcription = {
  langue: 'fr',
  phrases: [{ texte: 'Bonjour.', debutS: 0.1, finS: 1.2, mots: [{ mot: 'Bonjour.', debutS: 0.1, finS: 1.2 }] }],
};

afterEach(() => vi.useRealTimers());

describe('transcription GPU', () => {
  it('envoie le WAV en multipart, la langue et le jeton facultatif, puis valide la réponse', async () => {
    const fetchImpl = vi.fn<typeof fetch>(async (_url, options) => {
      expect(_url).toBe(`${url}/transcrire`);
      expect(options?.method).toBe('POST');
      expect(options?.headers).toEqual({ authorization: 'Bearer jeton-factice' });
      expect(options?.signal).toBeInstanceOf(AbortSignal);
      const corps = options?.body as FormData;
      expect(corps.get('language')).toBe('fr');
      const fichier = corps.get('file') as File;
      expect(fichier.name).toBe('audio.wav');
      expect(fichier.type).toBe('audio/wav');
      expect(Buffer.from(await fichier.arrayBuffer())).toEqual(audio);
      return new Response(JSON.stringify({
        ...transcription,
        phrases: [...transcription.phrases, { texte: 'invalide', debutS: 1, finS: 0 }],
      }));
    });
    await expect(transcrireSurGpu(audio, { url: `${url}/`, jeton: 'jeton-factice', fetchImpl })).resolves.toEqual(transcription);
    expect(fetchImpl).toHaveBeenCalledOnce();
  });

  it('accepte une transcription sans phrase, sans analyser la durée de l’audio', async () => {
    const fetchImpl = vi.fn<typeof fetch>(async (_url, options) => {
      expect(options?.headers).toBeUndefined();
      return new Response('{"langue":"fr","phrases":[]}');
    });
    await expect(transcrireSurGpu(new Uint8Array(100_000), { url, fetchImpl })).resolves.toEqual({ langue: 'fr', phrases: [] });
  });

  it.each([500, 201, 204])('renvoie null pour HTTP %s', async (status) => {
    const fetchImpl = vi.fn<typeof fetch>(async () => new Response(null, { status }));
    await expect(transcrireSurGpu(audio, { url, fetchImpl })).resolves.toBeNull();
  });

  it('renvoie null si le réseau est coupé', async () => {
    const fetchImpl = vi.fn<typeof fetch>(async () => { throw new TypeError('Réseau coupé'); });
    await expect(transcrireSurGpu(audio, { url, fetchImpl })).resolves.toBeNull();
  });

  it('renvoie null pour un JSON invalide', async () => {
    const fetchImpl = vi.fn<typeof fetch>(async () => new Response('pas du JSON'));
    await expect(transcrireSurGpu(audio, { url, fetchImpl })).resolves.toBeNull();
  });

  it.each([undefined, 25])('annule la requête au délai prévu (%s ms)', async (delaiMs) => {
    vi.useFakeTimers();
    let signal: AbortSignal | undefined;
    const fetchImpl = vi.fn<typeof fetch>((_url, options) => new Promise((_ok, ko) => {
      signal = options?.signal ?? undefined;
      signal?.addEventListener('abort', () => ko(new Error('Délai dépassé')), { once: true });
    }));
    const resultat = transcrireSurGpu(audio, { url, delaiMs, fetchImpl });
    await vi.advanceTimersByTimeAsync((delaiMs ?? 600_000) - 1);
    expect(signal?.aborted).toBe(false);
    await vi.advanceTimersByTimeAsync(1);
    await expect(resultat).resolves.toBeNull();
    expect(signal?.aborted).toBe(true);
    expect(vi.getTimerCount()).toBe(0);
  });

  it('libère le délai après une réponse réussie', async () => {
    vi.useFakeTimers();
    const fetchImpl = vi.fn<typeof fetch>(async () => new Response(JSON.stringify(transcription)));
    await transcrireSurGpu(audio, { url, fetchImpl });
    expect(vi.getTimerCount()).toBe(0);
  });
});
