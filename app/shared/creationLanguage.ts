/** Explicit language for the Director creation flow. `undefined` keeps legacy language detection. */
export type LangueClient = 'fr' | 'en';

export function lireLangueClient(value: unknown): LangueClient | undefined {
  return value === 'fr' || value === 'en' ? value : undefined;
}
