/**
 * Détourage vidéo : routes /api/nexora/detourage/*. Fines : validation, isolation par organisation, devis en crédits,
 * puis délégation au cycle de vie (gestion.ts) et au serveur de la machine GPU (client.ts).
 */
import { join } from 'node:path';
import { Readable } from 'node:stream';
import type { FastifyInstance, FastifyReply, FastifyRequest } from 'fastify';
import { ParamsSchema, secondesEstimees, versParamsMoteur } from './schema.js';
import { clientDetourage, type ClientDetourage } from './client.js';
import { Detourage, ErreurDetourage } from './gestion.js';
import { compteCourant } from '../compte.js';
import { tarifDepuisEnv, type Facturation } from '../credits.js';

export interface MoteurDetourageDeclare { id: string; nom: string; detourageUrl?: string; detourageJeton?: string; recettes: string[] }

export interface DepsDetourage {
  dossierDonnees: string;
  moteurs: () => MoteurDetourageDeclare[];
  /** Facturation de l'organisation (null en poste local). */
  facturation: (organisation: string) => Facturation | null;
  /** Nexora actif (compte obligatoire) ou poste local. */
  nexora: boolean;
  journal?: (m: string) => void;
}

const MAX_SOURCE = 4 * 1024 ** 3;
const SECONDES_MAX = () => Math.max(5, Number(process.env.NEXORA_DETOURAGE_SECONDES_MAX) || 120);

/** Un moteur propose un palier s'il déclare un serveur de détourage et la recette (ou « * » pour le palier rapide). */
export function moteurPour(moteurs: MoteurDetourageDeclare[], palier: string): MoteurDetourageDeclare | undefined {
  return moteurs.find((m) => m.detourageUrl && (m.recettes.includes(`detourage-${palier}`) || (palier === 'rapide' && m.recettes.includes('*'))));
}

export function enregistrerDetourage(app: FastifyInstance, deps: DepsDetourage): { detourage: Detourage; arreter: () => void } {
  const clients = new Map<string, ClientDetourage>();
  const clientDe = (id: string): ClientDetourage | null => {
    const m = deps.moteurs().find((x) => x.id === id && x.detourageUrl);
    if (!m?.detourageUrl) return null;
    const cle = `${id}@${m.detourageUrl}#${m.detourageJeton ?? ""}`; // en mémoire seulement
    let c = clients.get(cle);
    if (!c) { c = clientDetourage(m.detourageUrl, fetch, m.detourageJeton); clients.set(cle, c); }
    return c;
  };
  const detourage = new Detourage({
    registre: join(deps.dossierDonnees, 'detourage', 'registre.json'),
    moteur: (palier) => {
      const m = moteurPour(deps.moteurs(), palier);
      const c = m && clientDe(m.id);
      return m && c ? { id: m.id, client: c } : null;
    },
    clientDe,
    facturation: (org) => deps.facturation(org),
  });
  const ID = /^[0-9a-f]{24}$/;
  const qui = () => {
    const c = compteCourant();
    return { org: c?.organisationId ?? 'local', user: c?.utilisateurId ?? 'local' };
  };
  const garde = async (reply: FastifyReply, fn: () => Promise<unknown>) => {
    try { return await fn(); } catch (e) {
      if (e instanceof ErreurDetourage) return reply.code(e.code).send({ error: e.message });
      deps.journal?.(`détourage : ${e instanceof Error ? e.message : e}`);
      return reply.code(502).send({ error: e instanceof Error ? e.message : 'Le moteur de détourage ne répond pas.' });
    }
  };
  const idDe = (req: FastifyRequest, reply: FastifyReply): string | null => {
    const id = (req.params as { id?: string }).id ?? '';
    if (!ID.test(id)) { reply.code(404).send({ error: 'Travail introuvable.' }); return null; }
    return id;
  };
  const vue = (t: ReturnType<Detourage['obtenir']>) => ({
    id: t.id, nom: t.nom, etat: t.etat, etape: t.etape, progression: t.progression, message: t.message, creeLe: t.creeLe, majLe: t.majLe,
    source: t.source ?? null, fichiers: t.fichiers, devis: t.devis ?? null, credits: t.credits ? { credits: t.credits.credits, etat: t.credits.etat } : null,
    mesures: t.mesures ?? null, sorties: t.sorties ?? null, params: t.params ?? null, moteur: t.moteurId,
  });
  const verifierMoteurRapide = (t: ReturnType<Detourage['obtenir']>) => {
    const moteur = deps.moteurs().find((m) => m.id === t.moteurId);
    if (!moteur || !moteurPour([moteur], 'rapide')) {
      throw new ErreurDetourage('Le moteur rapide de ce travail n’est pas disponible.', 503);
    }
  };

  const P = '/api/nexora/detourage';

  app.get(`${P}/capacites`, async () => {
    const m = deps.moteurs();
    const rapide = moteurPour(m, 'rapide');
    const pro = moteurPour(m, 'pro');
    let sante: Record<string, unknown> | null = null;
    if (rapide) sante = await clientDe(rapide.id)?.sante().catch(() => null) ?? null;
    return {
      rapide: { disponible: sante?.ok === true, moteur: rapide ? { id: rapide.id, nom: rapide.nom } : null, modeles: sante?.modeles ?? null,
        description: 'SAM 3.1 (sélection par clics, boîte ou mot, suivi) + ViTMatte (bords) + stabilisation par flux optique' },
      pro: { disponible: false, moteur: pro ? { id: pro.id, nom: pro.nom } : null,
        description: 'Détourage avancé indisponible actuellement.' },
      limites: { secondesMax: SECONDES_MAX(), largeurMax: 3840, sourceOctetsMax: MAX_SOURCE },
      sorties: ['alpha PNG 16 bits', 'RGBA PNG 16 bits (avant-plan estimé)', 'EXR demi-flottant ZIP (premultiplié, linéaire)', 'EXR alpha', 'ProRes 4444', 'WebM VP9 alpha', 'matte', 'composite sur nouveau fond'],
      tarif: deps.nexora ? tarifDepuisEnv() : null,
    };
  });

  /** Aperçu interactif : une image + des clics (ou une boîte) -> masque. Rapide (une image), sans travail ni crédit. */
  app.post(`${P}/apercu`, { bodyLimit: 16 * 1024 * 1024 }, async (req, reply) => garde(reply, async () => {
    const b = (req.body ?? {}) as { imageB64?: string; points?: unknown; boite?: unknown };
    if (typeof b.imageB64 !== 'string' || b.imageB64.length < 100 || b.imageB64.length > 14_000_000) throw new ErreurDetourage('Image absente ou trop lourde.');
    const points = (Array.isArray(b.points) ? b.points : []).slice(0, 64).map((p) => (Array.isArray(p) ? p.map(Number) : [NaN]));
    if (points.some((p) => p.length !== 3 || p.slice(0, 2).some((v) => !(v >= 0 && v <= 1)) || ![0, 1].includes(p[2]))) throw new ErreurDetourage('Clics invalides.');
    const boite = Array.isArray(b.boite) && b.boite.length === 4 && b.boite.every((v) => Number(v) >= 0 && Number(v) <= 1) ? b.boite.map(Number) : null;
    if (!points.length && !boite) throw new ErreurDetourage('Clique sur le sujet.');
    const m = moteurPour(deps.moteurs(), 'rapide');
    const c = m && clientDe(m.id);
    if (!c) throw new ErreurDetourage('Aucun moteur de détourage en ligne.', 503);
    // Le moteur choisit SAM 3.1 : plus de variante à envoyer.
    return c.segmenter({ imageB64: b.imageB64, points, boite });
  }));

  /** Sélection par un mot (en anglais, l’encodeur de SAM 3.1) : une image -> les objets trouvés, sans travail ni crédit. */
  app.post(`${P}/texte`, { bodyLimit: 16 * 1024 * 1024 }, async (req, reply) => garde(reply, async () => {
    const b = (req.body ?? {}) as { imageB64?: string; texte?: unknown; seuil?: unknown };
    if (typeof b.imageB64 !== 'string' || b.imageB64.length < 100 || b.imageB64.length > 14_000_000) throw new ErreurDetourage('Image absente ou trop lourde.');
    const texte = typeof b.texte === 'string' ? b.texte.trim() : '';
    if (!texte || texte.length > 120) throw new ErreurDetourage('Écris ce qu’il faut détourer, en anglais (ex. person).');
    const seuil = b.seuil === undefined || b.seuil === null ? 0.4 : Number(b.seuil);
    if (!(seuil >= 0.05 && seuil <= 0.95)) throw new ErreurDetourage('Seuil invalide (0,05 à 0,95).');
    const m = moteurPour(deps.moteurs(), 'rapide');
    const c = m && clientDe(m.id);
    if (!c) throw new ErreurDetourage('Aucun moteur de détourage en ligne.', 503);
    return c.texte({ imageB64: b.imageB64, texte, seuil });
  }));

  app.get(`${P}/travaux`, async () => detourage.lister(qui().org).map(vue));

  app.post(`${P}/travaux`, async (req, reply) => garde(reply, async () => {
    const b = (req.body ?? {}) as { nom?: string; palier?: string };
    if (b.palier === 'pro') throw new ErreurDetourage('Le détourage pro n’est pas encore disponible.', 503);
    const { org, user } = qui();
    return vue(detourage.creer(org, user, String(b.nom ?? ''), b.palier === 'pro' ? 'pro' : 'rapide'));
  }));

  // Dépôt de la vidéo (ou d'un fond) en flux : jamais en mémoire, jamais sur le disque du serveur de Creative.
  app.register(async (sub) => {
    sub.addContentTypeParser('*', (_req, payload, done) => done(null, payload));
    for (const [segment, nom] of [['source', () => 'source.mp4'], ['fond', (ext: string) => `fond-${Date.now()}.${ext}`]] as const) {
      sub.put(`${P}/travaux/:id/${segment}`, { bodyLimit: MAX_SOURCE }, async (req, reply) => garde(reply, async () => {
        const id = idDe(req, reply); if (!id) return;
        const { org } = qui();
        const octets = Number(req.headers['content-length']) || undefined;
        if (octets && octets > MAX_SOURCE) throw new ErreurDetourage('Fichier trop lourd (4 Go au plus).', 413);
        const ext = segment === 'fond' ? ((req.query as { ext?: string }).ext ?? 'png').replace(/[^a-z0-9]/gi, '').slice(0, 5).toLowerCase() || 'png' : 'mp4';
        if (segment === 'fond' && !['png', 'jpg', 'jpeg', 'webp', 'mp4', 'mov', 'webm'].includes(ext)) throw new ErreurDetourage('Format de fond non pris en charge.');
        const cible = nom(ext) as 'source.mp4' | `fond-${string}`;
        const t = await detourage.deposer(org, id, cible, req.body as Readable, octets);
        if (segment === 'source' && t.source && t.source.duree > SECONDES_MAX()) {
          return { ...vue(t), avertissement: `Vidéo de ${Math.round(t.source.duree)} s : ${SECONDES_MAX()} s au plus par travail ; choisis une plage au lancement.` };
        }
        return { ...vue(t), fond: segment === 'fond' ? cible : undefined };
      }));
    }
  });

  app.post(`${P}/travaux/:id/lancer`, async (req, reply) => garde(reply, async () => {
    const id = idDe(req, reply); if (!id) return;
    const { org } = qui();
    const t = detourage.obtenir(org, id);
    const lu = ParamsSchema.safeParse(req.body);
    if (!lu.success) throw new ErreurDetourage(lu.error.issues.map((i) => `${i.path.join('.') || 'réglages'} : ${i.message}`).join(' ; '));
    const p = lu.data;
    if (p.palier === 'pro') throw new ErreurDetourage('Le détourage pro n’est pas encore disponible.', 503);
    verifierMoteurRapide(t);
    const src = t.source;
    const duree = Math.min(p.dureeS ?? Infinity, Math.max(0, (src?.duree ?? 5) - p.debutS));
    if (duree > SECONDES_MAX()) throw new ErreurDetourage(`Plage trop longue (${Math.round(duree)} s, ${SECONDES_MAX()} s au plus) : choisis une durée plus courte.`);
    const images = Math.round(duree * (src?.fps ?? 24));
    if (p.invites.some((i) => i.image >= images)) throw new ErreurDetourage(`Un clic est placé après la dernière image (${images}).`);
    for (const f of [p.composite?.type === 'image' || p.composite?.type === 'video' ? p.composite.fichier : null]) {
      if (f && !t.fichiers[f]) throw new ErreurDetourage('Le fond choisi n’a pas été déposé.');
    }
    const secondes = secondesEstimees({ ...p, dureeS: duree }, src?.fps ?? 24, duree, { parImageMpx: Number(process.env.NEXORA_DETOURAGE_S_PAR_IMAGE_MPX) || undefined });
    const credits = deps.nexora ? Math.max(1, Math.ceil(secondes * tarifDepuisEnv().creditsParSecondeGpu)) : null;
    return vue(await detourage.lancer(org, id, { ...versParamsMoteur({ ...p, dureeS: p.dureeS ?? null }) }, { secondes, credits }));
  }));

  app.get(`${P}/travaux/:id`, async (req, reply) => garde(reply, async () => {
    const id = idDe(req, reply); if (!id) return;
    return vue(await detourage.actualiser(qui().org, id));
  }));
  app.post(`${P}/travaux/:id/annuler`, async (req, reply) => garde(reply, async () => {
    const id = idDe(req, reply); if (!id) return;
    return vue(await detourage.annuler(qui().org, id));
  }));
  app.post(`${P}/travaux/:id/reprendre`, async (req, reply) => garde(reply, async () => {
    const id = idDe(req, reply); if (!id) return;
    const { org } = qui();
    const travail = detourage.obtenir(org, id);
    if (travail.params?.palier === 'pro') throw new ErreurDetourage('Le détourage pro n’est pas encore disponible.', 503);
    verifierMoteurRapide(travail);
    return vue(await detourage.reprendre(org, id));
  }));
  app.delete(`${P}/travaux/:id`, async (req, reply) => garde(reply, async () => {
    const id = idDe(req, reply); if (!id) return;
    await detourage.supprimer(qui().org, id);
    return { ok: true };
  }));

  /** Fichiers de sortie (aperçus, vidéos, archives de séquences), relayés depuis la machine GPU avec Range. */
  app.get(`${P}/travaux/:id/sorties/*`, async (req, reply) => garde(reply, async () => {
    const id = idDe(req, reply); if (!id) return;
    const t = detourage.obtenir(qui().org, id);
    const chemin = String((req.params as { '*'?: string })['*'] ?? '');
    if (!/^[a-zA-Z0-9][a-zA-Z0-9._-]{0,80}$/.test(chemin)) throw new ErreurDetourage('Fichier inconnu.', 404);
    const c = clientDe(t.moteurId);
    if (!c) throw new ErreurDetourage('Le moteur de ce travail est hors ligne.', 503);
    let r: Response;
    try { r = await c.sortie(id, chemin, req.headers.range); } catch (e) {
      if ((e as { code?: number }).code === 404) throw new ErreurDetourage('Fichier inconnu.', 404);
      throw e;
    }
    reply.code(r.status);
    for (const h of ['content-type', 'content-length', 'content-range', 'accept-ranges']) { const v = r.headers.get(h); if (v) reply.header(h, v); }
    if ((req.query as { telecharger?: string }).telecharger) reply.header('content-disposition', `attachment; filename="detourage-${id.slice(0, 6)}-${chemin}"`);
    return reply.send(Readable.fromWeb(r.body as never));
  }));

  // Nettoyage périodique des travaux terminés ou abandonnés (fichiers temporaires de la machine GPU compris).
  const minuteur = setInterval(() => { void detourage.nettoyer().then((s) => s.length && deps.journal?.(`détourage : ${s.length} travail(aux) nettoyé(s)`)); }, 30 * 60_000);
  minuteur.unref();
  return { detourage, arreter: () => clearInterval(minuteur) };
}
