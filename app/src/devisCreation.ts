/** Quote identity: changes make previous results unusable in the same render. */
export function cleDevisCreation(mode: string, format: string, duree: number, son: boolean, qualite: string, image: string | undefined, langue: string): string {
  return JSON.stringify([mode, format, duree, son, qualite, image ?? null, langue]);
}

/** Invalidate in-flight responses synchronously before changing photo or quality. */
export class ControleDevis {
  private version = 0;
  invalider(): void { this.version++; }
  jeton(): number { return this.version; }
  accepte(jeton: number): boolean { return this.version === jeton; }
}
