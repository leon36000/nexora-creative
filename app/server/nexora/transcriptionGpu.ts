import { lireTranscription, type Transcription } from './studio.js';

/** Transcription distante ; une erreur laisse le serveur reprendre le chemin CPU. */
export async function transcrireSurGpu(
  audioWav: Buffer | Uint8Array,
  opts: { url: string; jeton?: string; delaiMs?: number; fetchImpl?: typeof fetch },
): Promise<Transcription | null> {
  const controleur = new AbortController();
  const delai = setTimeout(() => controleur.abort(), opts.delaiMs ?? 600_000);
  try {
    const corps = new FormData();
    corps.append('file', new Blob([new Uint8Array(audioWav)], { type: 'audio/wav' }), 'audio.wav');
    corps.append('language', 'fr');
    const reponse = await (opts.fetchImpl ?? fetch)(`${opts.url.replace(/\/+$/, '')}/transcrire`, {
      method: 'POST',
      headers: opts.jeton ? { authorization: `Bearer ${opts.jeton}` } : undefined,
      body: corps,
      signal: controleur.signal,
    });
    if (reponse.status !== 200) return null;
    return lireTranscription(await reponse.text());
  } catch {
    return null;
  } finally {
    clearTimeout(delai);
  }
}
