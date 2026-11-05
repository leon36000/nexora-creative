/** Canonical names of Nexora products. Keep route and API identifiers separate. */
export const NEXORA_BRAND = 'Nexora' as const;

export const NEXORA_PRODUCT_NAMES = {
  mesh: `${NEXORA_BRAND} Mesh`,
  matte: `${NEXORA_BRAND} Matte`,
  director: `${NEXORA_BRAND} Director`,
  producer: `${NEXORA_BRAND} Producer`,
  studio: `${NEXORA_BRAND} Studio`,
  sync: `${NEXORA_BRAND} Sync`,
  voice: `${NEXORA_BRAND} Voice`,
  score: `${NEXORA_BRAND} Score`,
  fx: `${NEXORA_BRAND} FX`,
  finish: `${NEXORA_BRAND} Finish`,
  critic: `${NEXORA_BRAND} Critic`,
  scribe: `${NEXORA_BRAND} Scribe`,
  campaign: `${NEXORA_BRAND} Campaign`,
  connect: `${NEXORA_BRAND} Connect`,
  platform: `${NEXORA_BRAND} Platform`,
} as const;

export type NexoraProductKey = keyof typeof NEXORA_PRODUCT_NAMES;
export type NexoraProductName = (typeof NEXORA_PRODUCT_NAMES)[NexoraProductKey];
