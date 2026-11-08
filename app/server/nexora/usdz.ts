/** Export USDZ des primitives glTF statiques. Les caractéristiques non traduites sont refusées. */
import { NodeIO, type Node as GltfNode } from '@gltf-transform/core';
import { Matrix3, Matrix4, Vector3 } from 'three';
import { strToU8 } from 'fflate';
import { zipAligne } from './relief.js';

export class UsdzIncompatible extends Error {
  readonly code = 'USDZ_UNSUPPORTED';
}
const incompatible = (motif: string): never => { throw new UsdzIncompatible(motif); };
const fmt = (n: number): string => {
  if (!Number.isFinite(n)) return incompatible('Données USDZ non finies.');
  return Math.abs(n) < 1e-9 ? '0' : String(+n.toFixed(6));
};
const tuple = (v: readonly number[]) => `(${v.map(fmt).join(', ')})`;

/** Détecte les extensions avant décimation, qui pourrait les supprimer silencieusement. */
export function verifierGlbUsdz(glb: Uint8Array): void {
  if (glb.byteLength < 20) throw new Error('GLB invalide.');
  const dv = new DataView(glb.buffer, glb.byteOffset, glb.byteLength);
  const taille = dv.getUint32(12, true);
  if (dv.getUint32(0, true) !== 0x46546c67 || dv.getUint32(16, true) !== 0x4e4f534a || taille > glb.byteLength - 20) throw new Error('GLB invalide.');
  const j = JSON.parse(new TextDecoder().decode(glb.subarray(20, 20 + taille))) as Record<string, unknown>;
  const extensions = (v: unknown): boolean => {
    if (!v || typeof v !== 'object') return false;
    if (Array.isArray(v)) return v.some(extensions);
    return Object.entries(v).some(([k, x]) => (k === 'extensions' && !!x && typeof x === 'object' && Object.keys(x).length > 0) || extensions(x));
  };
  if (extensions(j) || (Array.isArray(j.extensionsRequired) && j.extensionsRequired.length > 0)) incompatible('Extensions glTF non prises en charge en USDZ.');
  if ((Array.isArray(j.animations) && j.animations.length) || (Array.isArray(j.skins) && j.skins.length)) incompatible('Animations et peau non prises en charge en USDZ.');
}

export async function exporterUsdz(glb: Uint8Array, nomOption?: string): Promise<Uint8Array> {
  verifierGlbUsdz(glb);
  const doc = await new NodeIO().readBinary(glb);
  if (doc.getRoot().listCameras().length) incompatible('Caméras non prises en charge en USDZ.');
  const nom = (nomOption ?? 'relief').replace(/[^A-Za-z0-9_-]+/g, '_').slice(0, 40) || 'relief';
  // Les identifiants USD ne peuvent pas débuter par un chiffre ou contenir un tiret.
  const prim = `Mesh_${nom.replaceAll('-', '_')}`;
  const fichiers: { nom: string; octets: Uint8Array }[] = [];
  const meshes: string[] = [], mats: string[] = [];
  let nombre = 0;
  const wraps: Record<number, string> = { 33071: 'clamp', 33648: 'mirror', 10497: 'repeat' };
  const scenes = doc.getRoot().listScenes();
  if (scenes.length !== 1) incompatible('Une seule scène glTF est prise en charge en USDZ.');
  const nodes: GltfNode[] = [];
  const visiter = (node: GltfNode) => { nodes.push(node); node.listChildren().forEach(visiter); };
  scenes[0].listChildren().forEach(visiter);
  for (const node of nodes.filter((n) => n.getMesh())) {
    if (node.getSkin()) incompatible('Peau non prise en charge en USDZ.');
    const world = node.getWorldMatrix();
    const matrice = new Matrix4().fromArray(world), det = matrice.determinant();
    if (!Number.isFinite(det) || det === 0) incompatible('Transformation USDZ singulière.');
    const normaleMatrice = new Matrix3().getNormalMatrix(matrice);
    for (const p of node.getMesh()!.listPrimitives()) {
      if (p.getMode() !== 4 || p.listTargets().length) incompatible('Primitive non triangulaire ou cible de morphose non prise en charge.');
      if (p.listSemantics().some((s) => s.startsWith('COLOR_') || s.startsWith('JOINTS_') || s.startsWith('WEIGHTS_'))) incompatible('Couleurs de sommets et peau non prises en charge.');
      const P = p.getAttribute('POSITION') ?? incompatible('Positions USDZ absentes ou invalides.');
      if (P.getType() !== 'VEC3') incompatible('Positions USDZ absentes ou invalides.');
      const count = P.getCount(), points: string[] = [], positions: Vector3[] = [], normales: (Vector3 | null)[] = [];
      const a = [0, 0, 0], v = new Vector3();
      const N = p.getAttribute('NORMAL');
      if (N && (N.getType() !== 'VEC3' || N.getCount() !== count)) incompatible('Normales USDZ invalides.');
      for (let i = 0; i < count; i++) {
        P.getElement(i, a);
        v.set(a[0], a[1], a[2]).applyMatrix4(matrice);
        points.push(tuple([v.x, v.y, v.z]));
        positions.push(v.clone());
        if (N) {
          N.getElement(i, a);
          v.set(a[0], a[1], a[2]).applyMatrix3(normaleMatrice);
          if (!Number.isFinite(v.lengthSq())) incompatible('Normale USDZ non finie.');
          normales.push(v.lengthSq() === 0 ? null : v.clone().normalize());
        }
      }
      const indices: number[] = [];
      const I = p.getIndices();
      const n = I?.getCount() ?? count;
      if (n === 0 || n % 3 !== 0) incompatible('Indices USDZ vides ou invalides.');
      for (let i = 0; i < n; i++) { const x = I ? I.getScalar(i) : i; if (!Number.isInteger(x) || x < 0 || x >= count) incompatible('Indice USDZ hors plage.'); indices.push(x); }
      if (det < 0) for (let i = 0; i < n; i += 3) [indices[i + 1], indices[i + 2]] = [indices[i + 2], indices[i + 1]];
      let nrm: string[] = [];
      let interpolation = 'vertex';
      if (N && normales.some((x) => x === null)) {
        interpolation = 'faceVarying';
        for (let i = 0; i < n; i += 3) {
          let face: Vector3 | null = null;
          if (indices.slice(i, i + 3).some((j) => normales[j] === null)) {
            const [a, b, c] = indices.slice(i, i + 3).map((j) => positions[j]);
            face = b.clone().sub(a).cross(c.clone().sub(a));
            if (!Number.isFinite(face.lengthSq()) || face.lengthSq() === 0) incompatible('Normale USDZ nulle sur une face dégénérée.');
            face.normalize();
          }
          for (let j = i; j < i + 3; j++) { const normal = normales[indices[j]] ?? face!; nrm.push(tuple([normal.x, normal.y, normal.z])); }
        }
      } else if (N) nrm = normales.map((normal) => tuple([normal!.x, normal!.y, normal!.z]));
      const mat = p.getMaterial();
      if (mat && (mat.getNormalTexture() || mat.getOcclusionTexture() || mat.getEmissiveTexture() || mat.getEmissiveFactor().some((x) => x !== 0))) incompatible('Cartes normales, occlusion et émission non prises en charge en USDZ.');
      const facteur = mat?.getBaseColorFactor() ?? [1, 1, 1, 1], metallic = mat?.getMetallicFactor() ?? 1, roughness = mat?.getRoughnessFactor() ?? 1;
      const alpha = mat?.getAlphaMode() ?? 'OPAQUE';
      const uvDecl: string[] = [], shaderDecl: string[] = [];
      const textureNode = (type: 'base' | 'mr') => {
        const tex = type === 'base' ? mat?.getBaseColorTexture() : mat?.getMetallicRoughnessTexture();
        if (!tex) return false;
        const info = type === 'base' ? mat?.getBaseColorTextureInfo() : mat?.getMetallicRoughnessTextureInfo();
        const image = tex.getImage(), mime = tex.getMimeType();
        if (!image || !info || (mime !== 'image/png' && mime !== 'image/jpeg') || info.listExtensions().length) incompatible('Texture USDZ non prise en charge.');
        // UsdPreviewSurface laisse le lecteur choisir le filtrage : le mode linéaire courant est accepté,
        // mais nearest et les variantes mipmap explicites ne peuvent pas être garantis.
        if (![null, 9729].includes(info!.getMinFilter()) || ![null, 9729].includes(info!.getMagFilter())) incompatible('Filtrage de texture non pris en charge en USDZ.');
        const U = p.getAttribute(`TEXCOORD_${info!.getTexCoord()}`);
        if (!U || U.getType() !== 'VEC2' || U.getCount() !== count) incompatible('Coordonnées de texture USDZ absentes ou invalides.');
        const uv: string[] = [], coord = [0, 0];
        for (let i = 0; i < count; i++) { U!.getElement(i, coord); uv.push(tuple([coord[0], 1 - coord[1]])); }
        uvDecl.push(`texCoord2f[] primvars:st_${type} = [${uv.join(', ')}] (interpolation = "vertex")`);
        const wS = wraps[info!.getWrapS()], wT = wraps[info!.getWrapT()];
        if (!wS || !wT) incompatible('Répétition de texture USDZ non prise en charge.');
        const filename = `texture_${nombre}_${type}.${mime === 'image/jpeg' ? 'jpg' : 'png'}`;
        fichiers.push({ nom: filename, octets: image! });
        const scale = type === 'base' ? facteur : [1, roughness, metallic, 1];
        shaderDecl.push(`def Shader "coord_${type}" {\n uniform token info:id = "UsdPrimvarReader_float2"\n string inputs:varname = "st_${type}"\n float2 outputs:result\n}\ndef Shader "texture_${type}" {\n uniform token info:id = "UsdUVTexture"\n asset inputs:file = @${filename}@\n float2 inputs:st.connect = </${prim}/Materiaux/m${nombre}/coord_${type}.outputs:result>\n token inputs:sourceColorSpace = "${type === 'base' ? 'sRGB' : 'raw'}"\n token inputs:wrapS = "${wS}"\n token inputs:wrapT = "${wT}"\n float4 inputs:scale = ${tuple(scale)}\n float outputs:r\n float outputs:g\n float outputs:b\n float outputs:a\n float3 outputs:rgb\n}`);
        return true;
      };
      const base = textureNode('base');
      const mr = textureNode('mr');
      const path = `/${prim}/Materiaux/m${nombre}`;
      const opacity = alpha === 'OPAQUE' ? 'float inputs:opacity = 1' : base ? `float inputs:opacity.connect = <${path}/texture_base.outputs:a>` : `float inputs:opacity = ${fmt(facteur[3])}`;
      mats.push(`def Material "m${nombre}" {\n token outputs:surface.connect = <${path}/surface.outputs:surface>\n def Shader "surface" {\n uniform token info:id = "UsdPreviewSurface"\n ${base ? `color3f inputs:diffuseColor.connect = <${path}/texture_base.outputs:rgb>` : `color3f inputs:diffuseColor = ${tuple(facteur.slice(0, 3))}`}\n ${opacity}\n ${alpha === 'MASK' ? `float inputs:opacityThreshold = ${fmt(mat!.getAlphaCutoff())}` : ''}\n ${mr ? `float inputs:metallic.connect = <${path}/texture_mr.outputs:b>\n float inputs:roughness.connect = <${path}/texture_mr.outputs:g>` : `float inputs:metallic = ${fmt(metallic)}\n float inputs:roughness = ${fmt(roughness)}`}\n token outputs:surface\n }\n ${shaderDecl.join('\n')}\n}`);
      meshes.push(`def Mesh "mesh_${nombre}" (prepend apiSchemas = ["MaterialBindingAPI"]) {\n int[] faceVertexCounts = [${Array.from({ length: n / 3 }, () => 3).join(', ')}]\n int[] faceVertexIndices = [${indices.join(', ')}]\n point3f[] points = [${points.join(', ')}]\n ${N ? `normal3f[] normals = [${nrm.join(', ')}] (interpolation = "${interpolation}")` : ''}\n uniform token subdivisionScheme = "none"\n uniform bool doubleSided = ${mat?.getDoubleSided() ? 'true' : 'false'}\n ${uvDecl.join('\n')}\n rel material:binding = <${path}>\n}`);
      nombre++;
    }
  }
  if (!nombre) incompatible('Aucun triangle à exporter en USDZ.');
  const usda = `#usda 1.0\n(\n defaultPrim = "${prim}"\n metersPerUnit = 1\n upAxis = "Y"\n)\ndef Xform "${prim}" (kind = "component") {\n ${meshes.join('\n')}\n def Scope "Materiaux" {\n ${mats.join('\n')}\n }\n}\n`;
  return zipAligne([{ nom: `${nom}.usda`, octets: strToU8(usda) }, ...fichiers]);
}
