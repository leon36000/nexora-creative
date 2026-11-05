/** Canonical names of Nexora products. Keep route and API identifiers separate. */
export const NEXORA_PRODUCT_NAMES = {
  mesh: 'Nexora Mesh',
  matte: 'Matte',
  director: 'Director',
  producer: 'Producer',
  studio: 'Studio',
  sync: 'Sync',
  voice: 'Voice',
  score: 'Score',
  fx: 'FX',
  finish: 'Finish',
  critic: 'Critic',
  scribe: 'Scribe',
  campaign: 'Campaign',
  connect: 'Connect',
  platform: 'Platform',
} as const;

export type NexoraProductKey = keyof typeof NEXORA_PRODUCT_NAMES;
export type NexoraProductName = (typeof NEXORA_PRODUCT_NAMES)[NexoraProductKey];
