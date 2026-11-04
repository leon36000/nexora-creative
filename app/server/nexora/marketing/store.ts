/** Stockage du kit de marque : un fichier JSON par organisation (ou « local » sur un poste sans compte). */
import { existsSync, mkdirSync, readFileSync, renameSync, writeFileSync } from 'node:fs';
import { join } from 'node:path';
import { KitMarqueSchema, type KitMarque } from './kit.js';

export const idOrganisation = (org?: string | null) => (org ?? 'local').replace(/[^a-zA-Z0-9_-]/g, '_').slice(0, 64) || 'local';

export class StoreKit {
  constructor(private dossier: string) { mkdirSync(dossier, { recursive: true }); }
  private chemin = (org?: string | null) => join(this.dossier, `${idOrganisation(org)}.json`);
  lire(org?: string | null): KitMarque | null {
    const p = this.chemin(org);
    if (!existsSync(p)) return null;
    const r = KitMarqueSchema.safeParse(JSON.parse(readFileSync(p, 'utf8')));
    return r.success ? r.data : null;
  }
  ecrire(org: string | null | undefined, kit: KitMarque): void {
    const p = this.chemin(org);
    writeFileSync(`${p}.tmp`, JSON.stringify(kit, null, 1));
    renameSync(`${p}.tmp`, p);
  }
}
