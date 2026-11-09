import { describe, expect, it, vi } from 'vitest';
import * as trellis from '../../../app/server/graphs/trellis';
import { buildTrellisGraph } from '../../../app/server/graphs/trellis';
import { buildPairedTrellisGraph, type Branch, type PairedParams } from './paired-graph';

const options: PairedParams = { image: 's01.png', seed: 0, quality: 'draft', removeBackground: true, filenamePrefix: 'ESSAI/paired', branches: ['A','B','C','D'] };
const branches: Branch[] = ['A','B','C','D'];

describe('construction appariée TRELLIS', () => {
  it.each(['draft', 'quality'] as const)('partage exactement l’amont et isole les sorties %s', (quality) => {
    const { graph, outputs } = buildPairedTrellisGraph({ ...options, quality });
    const original = buildTrellisGraph({ ...options, quality, turntableFrames: 0 }) as typeof graph;
    expect(outputs).toEqual(branches.map((b) => `${b}_save`));
    expect(Object.entries(graph).filter(([, n]) => /^(Save|Preview)/.test(n.class_type)).map(([id]) => id)).toEqual(outputs);
    expect(graph.subject).toBeUndefined();
    expect(graph.mesh).toEqual(original.mesh); expect(graph.colors).toEqual(original.colors);
    expect(graph.A_remesh).toEqual(original.remesh);
    expect(graph.kS).toEqual(original.kS); expect(graph.kG).toEqual(original.kG); expect(graph.kU).toEqual(original.kU); expect(graph.kT).toEqual(original.kT);
    for (const b of branches) {
      expect(graph[`${b}_remesh`].inputs.mesh).toEqual(['mesh', 0]);
      expect(graph[`${b}_bake`].inputs.voxel_colors).toEqual(['colors', 0]);
      expect(graph[`${b}_bake`].inputs.reference_mesh).toEqual(['mesh', 0]);
      expect(graph[`${b}_dec`].inputs.mesh).toEqual([`${b}_remesh`, 0]);
      expect(graph[`${b}_uv`].inputs.mesh).toEqual([`${b}_smooth`, 0]);
      expect(graph[`${b}_bake`].inputs.mesh).toEqual([`${b}_uv`, 0]);
      expect(graph[`${b}_apply`].inputs.base_color).toEqual([`${b}_bake`, 0]);
      expect(graph[`${b}_save`].inputs.mesh).toEqual([`${b}_final`, 0]);
      expect(graph[`${b}_save`].inputs.filename_prefix).toBe(`ESSAI/paired_${b}`);
      if (quality === 'quality') {
        expect(graph[`${b}_nrm`].inputs.high_poly).toEqual([`${b}_remesh`, 0]);
        expect(graph[`${b}_apply`].inputs.normal_map).toEqual([`${b}_nrm`, 0]);
        expect(graph[`${b}_apply`].inputs.occlusion).toEqual([`${b}_ao`, 0]);
      } else expect(graph[`${b}_nrm`]).toBeUndefined();
    }
  });
  it.each(['draft', 'quality'] as const)('conserve tout l’amont et toutes les connexions post-bake en %s', (quality) => {
    const { graph } = buildPairedTrellisGraph({ ...options, quality });
    const original = buildTrellisGraph({ ...options, quality, turntableFrames: 0 }) as typeof graph;
    const post = ['remesh','dec','smooth','uv','bake','apply','final','save', ...(quality === 'quality' ? ['nrm','ao'] : [])];
    const normalize = (value: unknown, branch: Branch): unknown => {
      if (Array.isArray(value)) {
        if (value.length === 2 && typeof value[0] === 'string' && value[0].startsWith(`${branch}_`)) return [value[0].slice(2), value[1]];
        return value.map((item) => normalize(item, branch));
      }
      if (value && typeof value === 'object') return Object.fromEntries(Object.entries(value).map(([k, v]) => [k, normalize(v, branch)]));
      return value;
    };
    for (const [id, node] of Object.entries(original)) if (id !== 'subject' && !post.includes(id)) expect(graph[id]).toEqual(node);
    for (const branch of branches) for (const id of post) {
      if (id === 'remesh' || id === 'save') continue;
      expect(normalize(graph[`${branch}_${id}`], branch)).toEqual(original[id]);
    }
    const visit = (value: unknown): void => {
      if (Array.isArray(value)) {
        if (value.length === 2 && typeof value[0] === 'string' && typeof value[1] === 'number') expect(graph[value[0]]).toBeDefined();
        else value.forEach(visit);
      } else if (value && typeof value === 'object') Object.values(value).forEach(visit);
    };
    Object.values(graph).forEach((node) => visit(node.inputs));
  });
  it('ne change que les réglages annoncés pour chaque branche', () => {
    const { graph } = buildPairedTrellisGraph(options);
    const a = graph.A_remesh.inputs;
    expect(a.sign_mode).toBe('udf'); expect(a.fix_poles).toBe(false);
    expect(graph.B_remesh.inputs).toEqual({ ...a, fix_poles: true });
    const { ['sign_mode.drop_inverted_components']: _inverted, ['sign_mode.drop_enclosed_components']: _enclosed, ...commun } = a;
    expect(graph.C_remesh.inputs).toEqual({ ...commun, sign_mode: 'sdf', 'sign_mode.qef': false, 'sign_mode.manifold': true });
    expect(graph.D_remesh.inputs).toEqual({ ...commun, sign_mode: 'solid', 'sign_mode.qef': false, 'sign_mode.fill': 20 });
  });
  it('renvoie des copies isolées et une construction déterministe', () => {
    const first = buildPairedTrellisGraph(options), second = buildPairedTrellisGraph(options);
    expect(first).toEqual(second);
    first.graph.A_remesh.inputs.band = 2;
    expect(first.graph.B_remesh.inputs.band).toBe(1);
    expect(second.graph.A_remesh.inputs.band).toBe(1);
  });
  it.each(['remesh', 'bake', 'output'] as const)('refuse un graphe officiel modifié : %s', (change) => {
    const original = trellis.buildTrellisGraph;
    const spy = vi.spyOn(trellis, 'buildTrellisGraph').mockImplementationOnce((params) => {
      const graph = original(params) as Record<string, { class_type: string; inputs: Record<string, unknown> }>;
      if (change === 'remesh') graph.remesh.inputs.fix_poles = true;
      if (change === 'bake') graph.bake.inputs.voxel_colors = ['other', 0];
      if (change === 'output') graph.extra = { class_type: 'SaveImage', inputs: {} };
      return graph;
    });
    try { expect(() => buildPairedTrellisGraph(options)).toThrow(); } finally { spy.mockRestore(); }
  });
  it('permet un sous-ensemble avec contrôle A obligatoire', () => {
    const { graph, outputs } = buildPairedTrellisGraph({ ...options, branches: ['A', 'C'] });
    expect(outputs).toEqual(['A_save', 'C_save']); expect(graph.B_save).toBeUndefined(); expect(graph.D_save).toBeUndefined();
  });
  it.each([
    { ...options, branches: [] }, { ...options, branches: ['B'] }, { ...options, branches: ['A','A'] },
    { ...options, branches: ['A','B','C','D','E'] }, { ...options, branches: ['A','Z'] },
    { ...options, filenamePrefix: '../x' }, { ...options, filenamePrefix: 'ESSAI/x/../secret' },
    { ...options, image: '../foo.png' }, { ...options, seed: -1 }, { ...options, seed: NaN },
  ])('refuse une entrée non conforme %#', (candidate) => {
    expect(() => buildPairedTrellisGraph(candidate as PairedParams)).toThrow();
  });
});
