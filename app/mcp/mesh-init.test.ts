import { afterAll, beforeAll, describe, expect, it, vi } from 'vitest';
import { Client } from '@modelcontextprotocol/sdk/client/index.js';
import { InMemoryTransport } from '@modelcontextprotocol/sdk/inMemory.js';
import { NEXORA_PRODUCT_NAMES } from '../shared/productNames.ts';
import { server } from './server.ts';

let client: Client;
describe('initialisation MCP et erreur de service', () => {
  beforeAll(async () => {
    const [transportServeur, transportClient] = InMemoryTransport.createLinkedPair();
    client = new Client({ name: 'mesh-test', version: '1' });
    await server.connect(transportServeur);
    await client.connect(transportClient);
  });
  afterAll(async () => { vi.unstubAllGlobals(); await client.close(); await server.close(); });
  it('annonce les noms centraux et ne promet pas les outils bloqués', async () => {
    expect(client.getServerVersion()).toMatchObject({ name: 'openfield', title: NEXORA_PRODUCT_NAMES.creative });
    const instructions = client.getInstructions() ?? '';
    expect(instructions).toContain(NEXORA_PRODUCT_NAMES.creative);
    expect(instructions).toContain(NEXORA_PRODUCT_NAMES.mesh);
    for (const mot of ['local stdio', 'tools/list', 'En préparation', 'wait_for_take', 'get_take', 'take:<id>', 'status']) expect(instructions).toContain(mot);
    expect(instructions).not.toMatch(/LTX|mirror_motion|\bspeak\b|stage_render/i);
    const noms = (await client.listTools()).tools.map(tool => tool.name);
    for (const nom of ['status', 'nexora_mesh_rapport', 'wait_for_take', 'get_take']) expect(noms).toContain(nom);
    for (const bloque of ['mirror_motion', 'speak', 'stage_render', 'direct_scene']) expect(noms).not.toContain(bloque);
  });
  it('nomme correctement le service HTTP indisponible', async () => {
    vi.stubGlobal('fetch', vi.fn().mockRejectedValue(new Error('fixture')));
    const resultat = await client.callTool({ name: 'status', arguments: {} });
    expect(resultat.isError).toBe(true);
    expect(JSON.stringify(resultat)).toContain(NEXORA_PRODUCT_NAMES.creative);
    expect(JSON.stringify(resultat)).not.toContain('OpenField is not answering');
  });
});
