/** Validation ciblée du contrat RemeshMesh, sans accès réseau. */
import type { buildPairedTrellisGraph } from './paired-graph';

type ObjectRecord = Record<string, unknown>;
const COMMUN: Record<string, string> = {
  mesh: 'MESH', resolution: 'INT', band: 'FLOAT', project_back: 'FLOAT', fix_poles: 'BOOLEAN',
  smooth_iters: 'INT', drop_small_components: 'FLOAT', precluster_max_verts: 'INT',
};
const MODES: Record<string, Record<string, string>> = {
  udf: { qef: 'BOOLEAN', drop_inverted_components: 'BOOLEAN', drop_enclosed_components: 'BOOLEAN' },
  sdf: { qef: 'BOOLEAN', manifold: 'BOOLEAN' },
  solid: { fill: 'FLOAT', qef: 'BOOLEAN' },
};

function objet(value: unknown): ObjectRecord {
  if (!value || typeof value !== 'object' || Array.isArray(value)) throw new Error('schéma RemeshMesh invalide');
  return value as ObjectRecord;
}
function specification(value: unknown, type: string): ObjectRecord {
  if (!Array.isArray(value) || value.length < 2 || value[0] !== type) throw new Error(`type RemeshMesh invalide : ${type}`);
  return objet(value[1]);
}
function clesExactes(value: ObjectRecord, keys: string[]): void {
  if (Object.keys(value).length !== keys.length || keys.some((key) => !(key in value))) throw new Error('champs RemeshMesh différents');
}
function verifierValeur(value: unknown, type: string, meta: ObjectRecord): void {
  if (type === 'MESH') {
    if (!Array.isArray(value) || value.length !== 2 || value[0] !== 'mesh' || value[1] !== 0) throw new Error('lien mesh invalide');
  } else if (type === 'BOOLEAN') {
    if (typeof value !== 'boolean') throw new Error('booléen RemeshMesh invalide');
  } else {
    if (typeof value !== 'number' || !Number.isFinite(value) || (type === 'INT' && !Number.isInteger(value))) throw new Error('nombre RemeshMesh invalide');
    if (typeof meta.min !== 'number' || !Number.isFinite(meta.min) || typeof meta.max !== 'number' || !Number.isFinite(meta.max) || meta.min > meta.max || value < meta.min || value > meta.max) throw new Error('borne RemeshMesh invalide');
  }
}

function lireModes(objectInfo: unknown): { required: ObjectRecord; modes: Record<string, ObjectRecord> } {
  const required = objet(objet(objet(objet(objectInfo).RemeshMesh).input).required);
  clesExactes(required, [...Object.keys(COMMUN), 'sign_mode']);
  for (const [key, type] of Object.entries(COMMUN)) specification(required[key], type);
  const dynamic = specification(required.sign_mode, 'COMFY_DYNAMICCOMBO_V3');
  if (!Array.isArray(dynamic.options)) throw new Error('options RemeshMesh absentes');
  const modes: Record<string, ObjectRecord> = {};
  for (const option of dynamic.options) {
    const data = objet(option);
    if (typeof data.key !== 'string' || modes[data.key]) throw new Error('mode RemeshMesh invalide');
    modes[data.key] = objet(objet(objet(data.inputs).required));
  }
  clesExactes(modes, Object.keys(MODES));
  for (const [mode, fields] of Object.entries(MODES)) {
    clesExactes(modes[mode], Object.keys(fields));
    for (const [key, type] of Object.entries(fields)) specification(modes[mode][key], type);
  }
  return { required, modes };
}

function verifierSorties(paired: ReturnType<typeof buildPairedTrellisGraph>, required: ObjectRecord, modes: Record<string, ObjectRecord>): void {
  const outputs = paired.outputs;
  if (!Array.isArray(outputs) || outputs.length < 1 || outputs.length > 4 || new Set(outputs).size !== outputs.length || !outputs.includes('A_save')) throw new Error('sorties appariées invalides');
  for (const output of outputs) verifierSortie(output, paired, required, modes);
}

function verifierSortie(output: string, paired: ReturnType<typeof buildPairedTrellisGraph>, required: ObjectRecord, modes: Record<string, ObjectRecord>): void {
  if (!/^[ABCD]_save$/.test(output)) throw new Error('sortie appariée invalide');
  const inputs = objet(paired.graph[`${output[0]}_remesh`]?.inputs);
  const mode = inputs.sign_mode;
  if (typeof mode !== 'string' || !MODES[mode]) throw new Error('mode RemeshMesh inconnu');
  const expectedMode: Record<string, string> = { A: 'udf', B: 'udf', C: 'sdf', D: 'solid' };
  if (mode !== expectedMode[output[0]] || inputs.fix_poles !== output.startsWith('B') || inputs['sign_mode.qef'] !== false ||
      (mode === 'sdf' && inputs['sign_mode.manifold'] !== true) || (mode === 'solid' && inputs['sign_mode.fill'] !== 20) ||
      (mode === 'udf' && (inputs['sign_mode.drop_inverted_components'] !== false || inputs['sign_mode.drop_enclosed_components'] !== false))) throw new Error('variante RemeshMesh modifiée');
  clesExactes(inputs, [...Object.keys(COMMUN), 'sign_mode', ...Object.keys(MODES[mode]).map((key) => `sign_mode.${key}`)]);
  for (const [key, type] of Object.entries(COMMUN)) verifierValeur(inputs[key], type, specification(required[key], type));
  for (const [key, type] of Object.entries(MODES[mode])) verifierValeur(inputs[`sign_mode.${key}`], type, specification(modes[mode][key], type));
}

/** Vérifie toutes les options A/B/C/D et les valeurs des branches demandées. */
export function verifyPairedRemeshSchema(objectInfo: unknown, paired: ReturnType<typeof buildPairedTrellisGraph>): void {
  const { required, modes } = lireModes(objectInfo);
  verifierSorties(paired, required, modes);
}
