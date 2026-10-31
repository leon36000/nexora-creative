/**
 * Espace disque des organisations (contrat docs/INTEGRATION-NEXORA.md : `recordStorageUsage(orgId, "creative", delta)`
 * côté site). Chaque prise terminée est comptée une fois ; supprimer une prise efface ses fichiers et rend l'espace.
 * Si le quota est dépassé, la prise reste lisible mais l'organisation ne peut plus lancer de rendu tant qu'elle n'a pas
 * libéré d'espace (même règle que le site : écrire est refusé, lire et supprimer restent permis).
 */

export interface EspacePrise { octets: number; etat: 'compte' | 'depasse' }

export function actionEspace(t: { status: string; output_path: string | null; espace?: EspacePrise }): 'compter' | null {
  return t.status === 'done' && t.output_path && !t.espace ? 'compter' : null;
}

export type ResultatEspace = { ok: true } | { ok: false; message: string };

export interface Espace {
  enregistrer(deltaOctets: number): Promise<ResultatEspace>;
}

export function espaceSite(siteUrl: string, cle: () => string | undefined, f: typeof fetch = fetch): Espace {
  return {
    async enregistrer(deltaOctets) {
      const k = cle();
      if (!k) throw new Error('organisation sans accès Nexora : reconnecte-toi');
      const r = await f(`${siteUrl}/api/creative/storage`, {
        method: 'POST',
        headers: { 'content-type': 'application/json', authorization: `Bearer ${k}` },
        body: JSON.stringify({ deltaBytes: Math.round(deltaOctets) }),
        signal: AbortSignal.timeout(15_000),
      });
      if (r.ok) return { ok: true };
      const corps = (await r.json().catch(() => ({}))) as any;
      return { ok: false, message: corps?.error?.message ?? corps?.message ?? `Espace disque refusé (HTTP ${r.status}).` };
    },
  };
}

/** Organisations dont l'espace est plein : plus de nouveau rendu jusqu'à ce qu'une suppression libère de la place. */
const pleines = new Set<string>();
export const espacePlein = (org: string) => pleines.has(org);
export const marquerPlein = (org: string, plein: boolean) => (plein ? pleines.add(org) : pleines.delete(org));
