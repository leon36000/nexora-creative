/** Extraction CPU de la géométrie aplatie, en conservant le GLB original. */
import { createHash } from 'node:crypto';
import { readFileSync, writeFileSync, mkdirSync, lstatSync } from 'node:fs';
import { resolve, join } from 'node:path';
import { lireGlb } from '../../../app/server/nexora/relief.ts';

const sha = (value: Uint8Array) => createHash('sha256').update(value).digest('hex');
async function main() {
  const [sourceArg, outArg] = process.argv.slice(2);
  if (!sourceArg || !outArg || process.argv.length !== 4) throw new Error('usage : tsx extract-glb.ts SOURCE.glb NOUVEAU_DOSSIER');
  const source = resolve(sourceArg), out = resolve(outArg);
  if (!lstatSync(source).isFile() || !source.toLowerCase().endsWith('.glb')) throw new Error('GLB ordinaire attendu');
  const glb = readFileSync(source), mesh = await lireGlb(glb);
  const positions = Buffer.alloc(mesh.positions.length * 8), faces = Buffer.alloc(mesh.indices.length * 4);
  mesh.positions.forEach((value, index) => positions.writeDoubleLE(value, index * 8));
  mesh.indices.forEach((value, index) => faces.writeUInt32LE(value, index * 4));
  mkdirSync(out, { mode: 0o700 });
  writeFileSync(join(out, 'positions.f64le'), positions, { flag: 'wx' });
  writeFileSync(join(out, 'faces.u32le'), faces, { flag: 'wx' });
  writeFileSync(join(out, 'source.json'), JSON.stringify({ scope: 'géométrie aplatie seulement, GLB source inchangé', source_sha256: sha(glb), positions_sha256: sha(positions), faces_sha256: sha(faces), vertices: mesh.positions.length / 3, triangles: mesh.indices.length / 3 }, null, 2) + '\n', { flag: 'wx' });
}
main().catch(error => { console.error(error instanceof Error ? error.message : String(error)); process.exitCode = 1; });
