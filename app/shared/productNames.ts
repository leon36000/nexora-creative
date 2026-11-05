/** Canonical names of Nexora products. Keep route and API identifiers separate. */
export const NEXORA_PRODUCT_NAMES = {
  mesh: 'Nexora Mesh',
  matte: 'Nexora Matte',
  director: 'Nexora Director',
  producer: 'Nexora Producer',
  studio: 'Nexora Studio',
  sync: 'Nexora Sync',
  voice: 'Nexora Voice',
  score: 'Nexora Score',
  fx: 'Nexora FX',
  finish: 'Nexora Finish',
  critic: 'Nexora Critic',
  scribe: 'Nexora Scribe',
  campaign: 'Nexora Campaign',
  connect: 'Nexora Connect',
  platform: 'Nexora Platform',
} as const;

export type NexoraProductKey = keyof typeof NEXORA_PRODUCT_NAMES;
export type NexoraProductName = (typeof NEXORA_PRODUCT_NAMES)[NexoraProductKey];
