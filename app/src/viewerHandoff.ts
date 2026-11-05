/** Link an existing still take to the active H3 image-to-video flow. */
let fallbackHandoffSequence = 0;

export function videoFromStillHref(takeId: number, prompt?: string): string | null {
  if (!Number.isSafeInteger(takeId) || takeId <= 0) return null;
  const handoffId = globalThis.crypto?.randomUUID?.() ?? `${Date.now().toString(36)}-${++fallbackHandoffSequence}`;
  const params = new URLSearchParams({ mode: 'video', cle: String(takeId), handoff: handoffId });
  if (typeof prompt === 'string' && prompt.trim()) params.set('intention', prompt.slice(0, 4000));
  return `/?${params.toString()}`;
}

export function readVideoStillHandoff(mode: string, params: URLSearchParams): { takeId: number; handoffId?: string; intention?: string } | null {
  if (mode !== 'video') return null;
  const takeId = Number(params.get('cle'));
  if (!Number.isSafeInteger(takeId) || takeId <= 0) return null;
  const intention = params.get('intention');
  const handoffId = params.get('handoff');
  return {
    takeId,
    ...(handoffId ? { handoffId: handoffId.slice(0, 80) } : {}),
    ...(intention === null ? {} : { intention: intention.slice(0, 4000) }),
  };
}

export function isCurrentVideoHandoff(epoch: number, currentEpoch: number, expectedRoute: string, currentRoute: string): boolean {
  return epoch === currentEpoch && expectedRoute === currentRoute;
}
