import { describe, expect, it } from 'vitest';
import fixture from './remesh-schema.fixture.json';
import { buildPairedTrellisGraph } from './paired-graph';
import { verifyPairedRemeshSchema } from './paired-schema';

type Fixture = { RemeshMesh: { input: { required: {
  sign_mode: [string, { options: { key: string; inputs: { required: Record<string, [string, Record<string, unknown>]> } }[] }];
  resolution: [string, { min: number; max: number }];
} } } };

const make = (quality: 'draft' | 'quality' = 'draft') => buildPairedTrellisGraph({
  image: 's01.png', seed: 0, quality, removeBackground: true,
  filenamePrefix: 'ESSAI/test', branches: ['A', 'B', 'C', 'D'],
});

describe('schéma RemeshMesh apparié', () => {
  it.each(['draft', 'quality'] as const)('accepte le vrai schéma élagué avec %s', (quality) => {
    expect(() => verifyPairedRemeshSchema(structuredClone(fixture), make(quality))).not.toThrow();
  });
  it('refuse une variante absente même si seule A est demandée', () => {
    const schema = structuredClone(fixture) as unknown as Fixture;
    schema.RemeshMesh.input.required.sign_mode[1].options = schema.RemeshMesh.input.required.sign_mode[1].options.filter((o) => o.key !== 'solid');
    const graph = buildPairedTrellisGraph({ image: 's01.png', seed: 0, quality: 'draft', removeBackground: true, filenamePrefix: 'ESSAI/test', branches: ['A'] });
    expect(() => verifyPairedRemeshSchema(schema, graph)).toThrow();
  });
  it('refuse un type de combo dynamique changé', () => {
    const schema = structuredClone(fixture) as unknown as Fixture;
    schema.RemeshMesh.input.required.sign_mode[0] = 'STRING';
    expect(() => verifyPairedRemeshSchema(schema, make())).toThrow();
  });
  it('refuse un champ de variante d’un mauvais type', () => {
    const schema = structuredClone(fixture) as unknown as Fixture;
    const sdf = schema.RemeshMesh.input.required.sign_mode[1].options.find((o) => o.key === 'sdf')!;
    sdf.inputs.required.manifold[0] = 'INT';
    expect(() => verifyPairedRemeshSchema(schema, make())).toThrow();
  });
  it('refuse une borne qui ne couvre pas la valeur utilisée', () => {
    const schema = structuredClone(fixture) as unknown as Fixture;
    schema.RemeshMesh.input.required.resolution[1].max = 700;
    expect(() => verifyPairedRemeshSchema(schema, make('quality'))).toThrow();
  });
  it('refuse une valeur booléenne invalide et une clé inconnue', () => {
    const graph = make();
    graph.graph.B_remesh.inputs.fix_poles = 'true';
    expect(() => verifyPairedRemeshSchema(fixture, graph)).toThrow();
    const other = make(); other.graph.A_remesh.inputs.inconnu = true;
    expect(() => verifyPairedRemeshSchema(fixture, other)).toThrow();
  });
  it('refuse un réglage de variante altéré même si son type est valide', () => {
    const graph = make(); graph.graph.B_remesh.inputs.fix_poles = false;
    expect(() => verifyPairedRemeshSchema(fixture, graph)).toThrow();
  });
  it('refuse un champ obligatoire supplémentaire inconnu', () => {
    const schema = structuredClone(fixture) as unknown as { RemeshMesh: { input: { required: Record<string, unknown> } } };
    schema.RemeshMesh.input.required.extra = ['FLOAT', { min: 0, max: 1 }];
    expect(() => verifyPairedRemeshSchema(schema, make())).toThrow();
  });
});
