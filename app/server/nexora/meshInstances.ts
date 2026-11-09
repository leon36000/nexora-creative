/** Expansion bornée des transformations d'instances glTF pour les exports statiques. */
import type { Node } from '@gltf-transform/core';
import type { InstancedMesh } from '@gltf-transform/extensions';
import { Matrix4, Quaternion, Vector3 } from 'three';

export class InstanceExpansionLimit extends Error {
  readonly statusCode = 422;
  readonly code = 'MESH_INSTANCE_LIMIT';
}

export class InstanceInvalid extends Error {
  readonly statusCode = 422;
  readonly code = 'MESH_INSTANCE_INVALID';
  constructor(message: string) { super(`${message} / Invalid or unsupported instance data.`); }
}

export class InstanceExtensionUnsupported extends Error {
  readonly statusCode = 422;
  readonly code = 'MESH_EXTENSION_UNSUPPORTED';
  constructor() { super('Extension glTF requise non prise en charge. / Required glTF extension is not supported.'); }
}

export const INSTANCE_LIMITS = { triangles: 2_000_000, vertices: 750_000, parts: 250_000 } as const;
const standard = new Set(['TRANSLATION', 'ROTATION', 'SCALE', '_COLOR_0']);

function batchOf(node: Node): InstancedMesh | null {
  return node.getExtension<InstancedMesh>('EXT_mesh_gpu_instancing');
}

export function instanceCount(node: Node): number {
  const batch = batchOf(node);
  if (!batch) return 1;
  const attrs = batch.listAttributes();
  if (!attrs.length || !attrs[0].getCount() || attrs.some((a) => a.getCount() !== attrs[0].getCount())) throw new InstanceInvalid('Attributs d’instance invalides ou de tailles différentes.');
  for (const [name, shape] of [['TRANSLATION', 'VEC3'], ['ROTATION', 'VEC4'], ['SCALE', 'VEC3']] as const) {
    const a = batch.getAttribute(name);
    if (!a) continue;
    const component = a.getComponentType();
    const validComponent = component === 5126 || (name === 'ROTATION' && (component === 5120 || component === 5122) && a.getNormalized());
    if (a.getType() !== shape || !validComponent) throw new InstanceInvalid(`Attribut d’instance ${name} invalide.`);
  }
  const color = batch.getAttribute('_COLOR_0');
  if (color && color.getType() !== 'VEC3' && color.getType() !== 'VEC4') throw new InstanceInvalid('Couleur d’instance invalide.');
  return attrs[0].getCount();
}

/** Borne chaque somme avant multiplication et avant toute expansion. */
export function addInstances(current: number, count: number, units: number, limit: number): number {
  if (![current, count, units, limit].every(Number.isSafeInteger) || current < 0 || count < 0 || units < 0 || limit < 0 || current > limit || (units && count > Math.floor((limit - current) / units))) {
    throw new InstanceExpansionLimit('Expansion des instances trop grande pour cet export ; téléchargez le GLB original. / Instance expansion exceeds the export limit; download the original GLB.');
  }
  return current + count * units;
}

export function checkExpansion(nodes: Node[]): void {
  if (!nodes.some((node) => batchOf(node))) return;
  let triangles = 0, vertices = 0, parts = 0;
  for (const node of nodes) {
    const count = instanceCount(node);
    for (const primitive of node.getMesh()!.listPrimitives()) {
      if (primitive.getMode() !== 4) continue;
      const pos = primitive.getAttribute('POSITION');
      if (!pos) continue;
      const indices = primitive.getIndices()?.getCount() ?? pos.getCount();
      if (indices % 3 !== 0) throw new InstanceInvalid('Indices d’instance invalides.');
      triangles = addInstances(triangles, count, indices / 3, INSTANCE_LIMITS.triangles);
      vertices = addInstances(vertices, count, pos.getCount(), INSTANCE_LIMITS.vertices);
      parts = addInstances(parts, count, 1, INSTANCE_LIMITS.parts);
    }
  }
}

export type Instance = { matrix: Matrix4; color: [number, number, number] | null; unknown: boolean };
export function* instanceMatrices(node: Node): Generator<Instance> {
  const batch = batchOf(node), world = new Matrix4().fromArray(node.getWorldMatrix());
  if (!batch) { yield { matrix: world, color: null, unknown: false }; return; }
  const count = instanceCount(node), pos = new Vector3(), rot = new Quaternion(), scale = new Vector3(), values: number[] = [];
  const t = batch.getAttribute('TRANSLATION'), r = batch.getAttribute('ROTATION'), s = batch.getAttribute('SCALE'), c = batch.getAttribute('_COLOR_0');
  const unknown = batch.listSemantics().some((name) => !standard.has(name));
  for (let i = 0; i < count; i++) {
    pos.fromArray(t ? t.getElement(i, values) : [0, 0, 0]);
    rot.fromArray(r ? r.getElement(i, values) : [0, 0, 0, 1]);
    // Tolérance de longueur du validateur glTF, élargie à l'erreur maximale
    // d'arrondi SNORM8 ; la marge couvre les arrondis de calcul, sans normalisation.
    const longueurRotation = rot.length();
    const tolerance = r?.getComponentType() === 5120 ? Math.max(0.00769, 1 / 127) + 8 * Number.EPSILON : 0.00769;
    if (!Number.isFinite(longueurRotation) || Math.abs(1 - longueurRotation) > tolerance) throw new InstanceInvalid('Rotation d’instance invalide.');
    scale.fromArray(s ? s.getElement(i, values) : [1, 1, 1]);
    const matrix = world.clone().multiply(new Matrix4().compose(pos, rot, scale));
    if (!matrix.elements.every(Number.isFinite)) throw new InstanceInvalid('Transformation d’instance non finie.');
    let color: [number, number, number] | null = null;
    if (c) {
      const value = c.getElement(i, []);
      if (!value.slice(0, 3).every(Number.isFinite)) throw new InstanceInvalid('Couleur d’instance non finie.');
      color = [value[0], value[1], value[2]];
    }
    yield { matrix, color, unknown };
  }
}
