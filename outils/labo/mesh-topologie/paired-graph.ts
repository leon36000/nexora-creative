/** Préparation de graphes appariés expérimentaux : aucune soumission ComfyUI. */
import { buildTrellisGraph, type ObjectQuality } from '../../../app/server/graphs/trellis';

export type Branch = 'A' | 'B' | 'C' | 'D';
type Node = { class_type: string; inputs: Record<string, unknown> };
type Graph = Record<string, Node>;
export type PairedParams = {
  image: string;
  seed: number;
  quality: ObjectQuality;
  removeBackground: boolean;
  filenamePrefix: string;
  branches: readonly Branch[];
};

const POST: Record<string, string> = {
  remesh: 'RemeshMesh', dec: 'DecimateMesh', smooth: 'MeshSmoothNormals', uv: 'UnwrapMesh',
  bake: 'BakeTextureFromVoxel', nrm: 'BakeNormalMapFromMesh', ao: 'BakeAmbientOcclusion',
  apply: 'ApplyTextureToMesh', final: 'MeshSmoothNormals', save: 'SaveGLB',
};
const COMMON_POST = ['remesh', 'dec', 'smooth', 'uv', 'bake', 'apply', 'final', 'save'];
const BRANCHES: readonly string[] = ['A', 'B', 'C', 'D'];

function renommer(value: unknown, post: Set<string>, branch: Branch): unknown {
  if (Array.isArray(value)) {
    if (value.length === 2 && typeof value[0] === 'string' && Number.isInteger(value[1]) && post.has(value[0])) {
      return [`${branch}_${value[0]}`, value[1]];
    }
    return value.map((item) => renommer(item, post, branch));
  }
  if (value && typeof value === 'object') {
    return Object.fromEntries(Object.entries(value).map(([key, item]) => [key, renommer(item, post, branch)]));
  }
  return value;
}

function variante(inputs: Record<string, unknown>, branch: Branch): void {
  if (branch === 'B') inputs.fix_poles = true;
  if (branch === 'C' || branch === 'D') {
    delete inputs['sign_mode.drop_inverted_components'];
    delete inputs['sign_mode.drop_enclosed_components'];
    inputs.sign_mode = branch === 'C' ? 'sdf' : 'solid';
    inputs['sign_mode.qef'] = false;
    if (branch === 'C') inputs['sign_mode.manifold'] = true;
    else inputs['sign_mode.fill'] = 20;
  }
}

/** Quatre variantes au plus, amont TRELLIS et voxels partagés, GLB seulement. */
export function buildPairedTrellisGraph(p: PairedParams): { graph: Graph; outputs: string[] } {
  if (!/^[A-Za-z0-9][A-Za-z0-9_.-]{0,199}$/.test(p.image) || p.image.includes('..')) throw new Error('image Comfy invalide');
  if (!Number.isInteger(p.seed) || p.seed < 0 || p.seed > 0xffffffff) throw new Error('seed invalide');
  if (p.quality !== 'draft' && p.quality !== 'quality') throw new Error('profil invalide');
  if (typeof p.removeBackground !== 'boolean') throw new Error('fond invalide');
  if (!/^ESSAI\/[A-Za-z0-9][A-Za-z0-9_-]{0,63}$/.test(p.filenamePrefix)) throw new Error('préfixe ESSAI invalide');
  if (!Array.isArray(p.branches) || !p.branches.length || !p.branches.includes('A') || p.branches.length > 4 || new Set(p.branches).size !== p.branches.length || p.branches.some((b) => !BRANCHES.includes(b))) throw new Error('branches invalides');

  const base = buildTrellisGraph({ ...p, turntableFrames: 0 }) as Graph;
  const postNames = [...COMMON_POST, ...(p.quality === 'quality' ? ['nrm', 'ao'] : [])];
  const post = new Set(postNames);
  for (const name of postNames) if (base[name]?.class_type !== POST[name]) throw new Error(`graphe officiel incompatible : ${name}`);
  if (base.subject?.class_type !== 'PreviewImage' || base.mesh?.class_type !== 'VaeDecodeShapeTrellis' || base.colors?.class_type !== 'VaeDecodeTextureTrellis') throw new Error('amont officiel incompatible');
  const remeshAttendu: Record<string, unknown> = {
    mesh: ['mesh', 0], resolution: p.quality === 'draft' ? 512 : 768, sign_mode: 'udf',
    'sign_mode.qef': false, 'sign_mode.drop_inverted_components': false, 'sign_mode.drop_enclosed_components': false,
    band: 1, project_back: 0, fix_poles: false, smooth_iters: 0, drop_small_components: 0.01, precluster_max_verts: 20_000_000,
  };
  const remesh = base.remesh.inputs;
  if (Object.keys(remesh).length !== Object.keys(remeshAttendu).length ||
      Object.entries(remeshAttendu).some(([key, value]) => JSON.stringify(remesh[key]) !== JSON.stringify(value))) throw new Error('référence remesh modifiée');
  if (JSON.stringify(base.bake.inputs.voxel_colors) !== JSON.stringify(['colors', 0]) ||
      JSON.stringify(base.bake.inputs.reference_mesh) !== JSON.stringify(['mesh', 0])) throw new Error('référence bake modifiée');
  for (const [name, node] of Object.entries(base)) {
    if (!post.has(name) && name !== 'subject' && /^(?:Save|Preview)/.test(node.class_type)) throw new Error('sortie officielle inattendue');
  }
  const graph: Graph = {};
  for (const [name, node] of Object.entries(base)) if (!post.has(name) && name !== 'subject') graph[name] = structuredClone(node);
  const outputs: string[] = [];
  for (const branch of p.branches) {
    for (const name of postNames) {
      const node = structuredClone(base[name]);
      node.inputs = renommer(node.inputs, post, branch) as Record<string, unknown>;
      if (name === 'remesh') variante(node.inputs, branch);
      if (name === 'save') node.inputs.filename_prefix = `${p.filenamePrefix}_${branch}`;
      graph[`${branch}_${name}`] = node;
    }
    outputs.push(`${branch}_save`);
  }
  return { graph, outputs };
}
