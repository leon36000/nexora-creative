/**
 * Client du serveur de détourage (outils/detourage/serveur.py) d'une machine GPU : HTTP simple, sans état. Le serveur de
 * Creative le pilote comme un moteur ; la machine peut être la GB10, la RTX 5090 ou la RTX 5080 de pc3.
 */
import type { Readable } from 'node:stream';

export interface EtatMoteur {
  etat: 'en_attente' | 'en_cours' | 'termine' | 'erreur' | 'annule' | 'interrompu';
  etape?: string; progression?: number; message?: string;
  mesures?: Record<string, unknown>; sorties?: { fichiers?: Record<string, number>; sequences?: Record<string, number> };
}

export interface InfoSource { largeur: number; hauteur: number; fps: number; duree: number; audio: boolean }

export interface ClientDetourage {
  sante(): Promise<Record<string, unknown>>;
  segmenter(corps: { imageB64: string; points: number[][]; boite?: number[] | null; sam?: string }): Promise<{ masqueB64: string; score: number; aire: number; secondes: number; largeur: number; hauteur: number }>;
  /** Sélection par texte (SAM 3.1) : un mot ou une phrase en anglais -> les objets trouvés, du plus sûr au moins sûr. */
  texte(corps: { imageB64: string; texte: string; seuil?: number }): Promise<{ objets: { masqueB64: string; score: number; boite: number[]; aire: number }[]; secondes: number; largeur: number; hauteur: number }>;
  /** Dépose un fichier ; pour la source, le serveur renvoie ses caractéristiques (sonde ffprobe). */
  deposer(id: string, nom: string, flux: Readable | Buffer, octets?: number): Promise<InfoSource | undefined>;
  lancer(id: string, params: Record<string, unknown>): Promise<void>;
  etat(id: string): Promise<EtatMoteur | null>;
  annuler(id: string): Promise<void>;
  supprimer(id: string): Promise<void>;
  /** Réponse brute (corps en flux) d'un fichier de sortie, avec l'en-tête Range éventuel. */
  sortie(id: string, chemin: string, range?: string): Promise<Response>;
}

async function verifier(r: Response): Promise<Response> {
  if (r.ok) return r;
  const t = await r.text().catch(() => '');
  let m = `HTTP ${r.status}`;
  try { m = (JSON.parse(t) as { erreur?: string }).erreur ?? m; } catch { /* corps non JSON */ }
  throw new Error(`détourage : ${m}`);
}

/**
 * `jeton` : secret partagé avec le serveur de la machine GPU (NEXORA_DETOURAGE_JETON), envoyé en « Authorization: Bearer »
 * à chaque requête ; jamais journalisé (les erreurs ne reprennent que le code HTTP et le message du serveur).
 */
export function clientDetourage(base: string, f0: typeof fetch = fetch, jeton?: string): ClientDetourage {
  const u = (c: string) => `${base.replace(/\/+$/, '')}${c}`;
  const auth: Record<string, string> = jeton ? { authorization: `Bearer ${jeton}` } : {};
  const f = ((url: string, init: RequestInit = {}) => f0(url, { ...init, headers: { ...(init.headers as Record<string, string> | undefined), ...auth } })) as typeof fetch;
  const json = (corps: unknown) => ({ method: 'POST', headers: { 'content-type': 'application/json' }, body: JSON.stringify(corps) });
  return {
    async sante() { return (await verifier(await f(u('/sante'), { signal: AbortSignal.timeout(8_000) }))).json() as Promise<Record<string, unknown>>; },
    async segmenter(c) {
      const r = await verifier(await f(u('/segmenter'), { ...json({ image_b64: c.imageB64, points: c.points, boite: c.boite ?? null, sam: c.sam }), signal: AbortSignal.timeout(120_000) }));
      const j = (await r.json()) as any;
      return { masqueB64: j.masque_b64, score: j.score, aire: j.aire, secondes: j.secondes, largeur: j.largeur, hauteur: j.hauteur };
    },
    async texte(c) {
      const r = await verifier(await f(u('/texte'), { ...json({ image_b64: c.imageB64, texte: c.texte, seuil: c.seuil }), signal: AbortSignal.timeout(120_000) }));
      const j = (await r.json()) as any;
      const objets = (Array.isArray(j.objets) ? j.objets : []).map((o: any) => ({ masqueB64: o.masque_b64, score: o.score, boite: o.boite, aire: o.aire }));
      return { objets, secondes: j.secondes, largeur: j.largeur, hauteur: j.hauteur };
    },
    async deposer(id, nom, flux, octets) {
      const init: RequestInit & { duplex?: 'half' } = { method: 'PUT', body: flux as never, duplex: 'half', headers: { 'content-type': 'application/octet-stream', ...(octets ? { 'content-length': String(octets) } : {}) } };
      const r = await verifier(await f(u(`/travaux/${id}/fichiers/${encodeURIComponent(nom)}`), init));
      return ((await r.json().catch(() => ({}))) as { info?: InfoSource }).info;
    },
    async lancer(id, params) { await verifier(await f(u(`/travaux/${id}/lancer`), { ...json({ params }), signal: AbortSignal.timeout(15_000) })); },
    async etat(id) {
      const r = await f(u(`/travaux/${id}`), { signal: AbortSignal.timeout(8_000) });
      if (r.status === 404) return null;
      return (await verifier(r)).json() as Promise<EtatMoteur>;
    },
    async annuler(id) { await verifier(await f(u(`/travaux/${id}/annuler`), { ...json({}), signal: AbortSignal.timeout(8_000) })); },
    async supprimer(id) { await verifier(await f(u(`/travaux/${id}`), { method: 'DELETE', signal: AbortSignal.timeout(60_000) })); },
    async sortie(id, chemin, range) {
      const r = await f(u(`/travaux/${id}/sorties/${chemin.split('/').map(encodeURIComponent).join('/')}`), { headers: range ? { range } : {} });
      if (r.status === 404) throw Object.assign(new Error('fichier introuvable'), { code: 404 });
      return verifier(r);
    },
  };
}
