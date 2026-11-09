/** Routes de rapport et d’export Mesh, avec accès aux prises fourni par le serveur. */
import { createReadStream, existsSync, mkdirSync, readFileSync, statSync, writeFileSync } from 'node:fs';
import { join } from 'node:path';
import type { FastifyInstance, FastifyRequest, FastifyReply } from 'fastify';
import { analyser, cibleTriangles, compatibiliteObj, decimerGlb, EXTENSION_RELIEF, exporter, nomCacheExport, nomCacheRapport, ObjIncompatible, repondreObjIncompatible, FORMATS_RELIEF, lireGlb, TAILLE_MM_DEFAUT, TYPE_MIME_RELIEF, type FormatRelief, type Maillage } from './relief.js';
import { UsdzIncompatible } from './usdz.js';
import { PRODUIT_3D } from '../../src/produit3d.js';

type Prise = { id: number; glb: string; t: { settings: string } };
type TakeMesh = { output_path: string | null; status: string; settings: string };

/** Conserve les contrôles de prise et d’existence avant toute lecture de fichier. */
export function creerPriseRelief<T extends TakeMesh>(getTake: (id: number) => T | undefined) {
  return (req: FastifyRequest, reply: FastifyReply): { id: number; glb: string; t: T } | null => {
    const id = Number((req.params as any).take);
    const t = getTake(id);
    if (!t?.output_path || !/\.glb$/i.test(t.output_path) || t.status !== 'done') { void reply.code(404).send({ error: `${PRODUIT_3D} : modèle introuvable ou pas encore prêt.` }); return null; }
    if (!existsSync(t.output_path)) { void reply.code(410).send({ error: 'Le fichier du modèle n’est plus sur le disque.' }); return null; }
    return { id, glb: t.output_path, t };
  };
}
type Dependances = {
  priseRelief: (req: FastifyRequest, reply: FastifyReply) => Prise | null;
  unSeulCalcul: <T>(cle: string, travail: () => Promise<T>) => Promise<T>;
};

/** Absence ou zéro = plein ; refuse une cible négative ou non numérique. */
function facesInvalides(faces: unknown): boolean {
  if (faces === undefined) return false;
  if (typeof faces !== 'string' || !faces.trim()) return true;
  const n = Number(faces);
  return !Number.isFinite(n) || n < 0;
}

export function enregistrerRoutesRelief(app: FastifyInstance, { priseRelief, unSeulCalcul }: Dependances): void {
app.get('/api/nexora/relief/:take/rapport', async (req, reply) => {
  const p = priseRelief(req, reply); if (!p) return;
  const q = req.query as any;
  if (facesInvalides(q.faces)) return reply.code(400).send({ code: 'MESH_INVALID_FACES', error: 'Nombre de faces invalide. / Invalid face count.' });
  const dir = `${p.glb}.relief`;
  mkdirSync(dir, { recursive: true });
  const octets = readFileSync(p.glb);
  let maillagePlein: Maillage | null = null;
  const chargerPlein = async () => maillagePlein ??= await lireGlb(octets);
  const lire = async (cible: number | null) => {
    const fichier = join(dir, nomCacheRapport(cible));
    if (existsSync(fichier)) return JSON.parse(readFileSync(fichier, 'utf8'));
    const r = await unSeulCalcul(fichier, async () => analyser(cible ? await lireGlb(await decimerGlb(octets, cible)) : await chargerPlein()));
    writeFileSync(fichier, JSON.stringify(r));
    return r;
  };
  const plein = await lire(null);
  const cible = cibleTriangles(q.faces, plein.triangles);
  const s = JSON.parse(p.t.settings ?? '{}');
  return {
    rapport: plein, decime: cible ? await lire(cible) : null, cible,
    formats: FORMATS_RELIEF, extensions: EXTENSION_RELIEF, tailleMm: TAILLE_MM_DEFAUT,
    compatibiliteObj: compatibiliteObj(octets, await chargerPlein()),
    // Les exports sont calculés par le serveur (CPU, quelques secondes) : aucun crédit GPU.
    credits: 0, juge: s.relief?.juge ?? null,
  };
});

app.get('/api/nexora/relief/:take/export', async (req, reply) => {
  const p = priseRelief(req, reply); if (!p) return;
  const q = req.query as any;
  const format = String(q.format ?? 'glb').toLowerCase() as FormatRelief;
  if (!FORMATS_RELIEF.includes(format)) return reply.code(400).send({ error: `Format inconnu : ${FORMATS_RELIEF.join(', ')}.` });
  if (facesInvalides(q.faces)) return reply.code(400).send({ code: 'MESH_INVALID_FACES', error: 'Nombre de faces invalide. / Invalid face count.' });
  if (format === 'glb' && (q.faces === undefined || Number(q.faces) === 0)) {
    reply.headers({ 'Content-Type': TYPE_MIME_RELIEF.glb, 'Content-Length': statSync(p.glb).size, 'Content-Disposition': `attachment; filename="relief-${p.id}.glb"` });
    return reply.send(createReadStream(p.glb));
  }
  const taille = Math.max(1, Math.min(2000, Number(q.taille) || TAILLE_MM_DEFAUT));
  const dir = `${p.glb}.relief`;
  mkdirSync(dir, { recursive: true });
  const octets = readFileSync(p.glb);
  const maillage = await lireGlb(octets);
  const compatibilite = format === 'obj' ? compatibiliteObj(octets, maillage) : null;
  if (compatibilite && !compatibilite.compatible) return repondreObjIncompatible(reply);
  const cible = cibleTriangles(q.faces, analyser(maillage).triangles);
  const fichier = join(dir, nomCacheExport(format, cible, taille));
  if (!existsSync(fichier)) {
    try {
      const sortie = await unSeulCalcul(fichier, () => exporter(octets, format, { nom: `relief-${p.id}`, tailleMm: taille, cible }));
      writeFileSync(fichier, sortie);
    } catch (error) {
      if (error instanceof ObjIncompatible) return repondreObjIncompatible(reply);
      if (error instanceof UsdzIncompatible) return reply.code(400).send({ code: error.code, error: 'Export USDZ incompatible avec ce modèle. Utilisez le GLB. / USDZ export does not support this model. Use GLB.' });
      throw error;
    }
  }
  reply.headers({ 'Content-Type': TYPE_MIME_RELIEF[format === 'obj' ? 'zip' : format], 'Content-Length': statSync(fichier).size, 'Content-Disposition': `attachment; filename="relief-${p.id}${cible ? `-${cible}` : ''}.${EXTENSION_RELIEF[format]}"` });
  return reply.send(createReadStream(fichier));
});

}
