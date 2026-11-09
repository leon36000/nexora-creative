import { afterAll, beforeAll, describe, expect, it, vi } from 'vitest';
import { mkdtemp, rm, writeFile } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { Client } from '@modelcontextprotocol/sdk/client/index.js';
import { InMemoryTransport } from '@modelcontextprotocol/sdk/inMemory.js';

// Montage imports unrelated services; suppress only its registration for this contract.
vi.mock('./montage.ts', () => ({ enregistrerMontage: () => undefined }));

type RecordedCall = { url: string; method: string; body: unknown };
type Capacity =
  | { kind: 'ready'; enabled: boolean; max: number | null }
  | { kind: 'null' }
  | { kind: 'unavailable' };

const origin = 'http://mcp-contract.fake.invalid';
const allCalls: RecordedCall[] = [];
let calls: RecordedCall[] = [];
let capacity: Capacity = { kind: 'ready', enabled: true, max: 2 };
let generationStatus = 200;
let uploadUnavailable = false;
let imageDirectory = '';
let imagePaths = {} as Record<'front' | 'left' | 'back' | 'right', string>;
let client!: Client;
let server!: typeof import('./server.ts')['server'];

const pngs = {
  front: 'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAIAAACQd1PeAAAADElEQVR4nGP4ICICAAMQARkzdtKQAAAAAElFTkSuQmCC',
  left: 'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAIAAACQd1PeAAAADElEQVR4nGMQuSMCAAIMAQWdoTQzAAAAAElFTkSuQmCC',
  back: 'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAIAAACQd1PeAAAADElEQVR4nGNgYAAAAAMAAWgmWQ0AAAAASUVORK5CYII=',
  right: 'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAIAAACQd1PeAAAADElEQVR4nGNgoBAAAAMBAQDJ/pLvAAAAAElFTkSuQmCC',
};

function jsonResponse(value: unknown, status = 200): Response {
  return new Response(JSON.stringify(value), { status, headers: { 'content-type': 'application/json' } });
}

async function fakeFetch(input: unknown, init?: RequestInit): Promise<Response> {
  const url = String(input);
  const method = String(init?.method ?? 'GET').toUpperCase();
  const body = typeof init?.body === 'string' ? JSON.parse(init.body) : null;
  const record = { url, method, body };
  calls.push(record);
  allCalls.push(record);

  if (url === `${origin}/api/nexora/etat` && method === 'GET') {
    if (capacity.kind === 'unavailable') return jsonResponse({ error: 'fixture state unavailable' }, 503);
    if (capacity.kind === 'null') return jsonResponse(null);
    return jsonResponse({ objet3d: { multivue: capacity.enabled, vuesMax: capacity.max } });
  }
  if (url === `${origin}/api/takes` && method === 'GET') {
    return jsonResponse([
      { id: 42, status: 'done', kind: 'still', settings: JSON.stringify({ userPrompt: 'primary prompt', width: 1, height: 1 }) },
      { id: 43, status: 'done', kind: 'still', settings: JSON.stringify({ userPrompt: 'left prompt', width: 1, height: 1 }) },
      { id: 44, status: 'done', kind: 'object', settings: '{}' },
      { id: 45, status: 'rendering', kind: 'still', settings: '{}' },
    ]);
  }
  if (url === `${origin}/api/media/42` && method === 'GET') {
    return new Response(Buffer.from(pngs.front, 'base64'), { headers: { 'content-type': 'image/png' } });
  }
  if (url === `${origin}/api/media/43` && method === 'GET') {
    return new Response(Buffer.from(pngs.left, 'base64'), { headers: { 'content-type': 'image/png' } });
  }
  if (url === `${origin}/api/upload` && method === 'POST') {
    if (uploadUnavailable) return jsonResponse({ error: 'upload unavailable' }, 503);
    return jsonResponse({ name: `token:${String((body as { name?: unknown } | null)?.name ?? 'missing')}` });
  }
  if (url === `${origin}/api/generate` && method === 'POST') {
    if (generationStatus !== 200) return jsonResponse({ error: 'server final capacity refusal' }, generationStatus);
    const count = Number((body as { count?: unknown } | null)?.count ?? 1);
    return jsonResponse({ takeId: 900, takeIds: Array.from({ length: count }, (_, i) => 900 + i) });
  }
  return jsonResponse({ error: `unexpected fake route: ${method} ${url}` }, 404);
}

function beginCase(nextCapacity: Capacity, nextGenerationStatus = 200) {
  capacity = nextCapacity;
  generationStatus = nextGenerationStatus;
  uploadUnavailable = false;
  calls = [];
}

function at(path: string, method?: string): RecordedCall[] {
  return calls.filter((call) => new URL(call.url).pathname === path && (!method || call.method === method));
}

function toolText(result: unknown): string {
  return JSON.stringify(result);
}

function input(sides: Array<'left' | 'back' | 'right'> | null, overrides: Record<string, unknown> = {}) {
  return {
    image: imagePaths.front,
    quality: 'draft',
    remove_background: false,
    count: 1,
    ...(sides === null ? {} : { views: Object.fromEntries(sides.map((side) => [side, imagePaths[side]])) }),
    ...overrides,
  };
}

function expectedBody(sides: Array<'left' | 'back' | 'right'>) {
  return {
    kind: 'object',
    app: 'object',
    quality: 'draft',
    removeBackground: false,
    count: 1,
    image: 'token:front.png',
    ...(sides.length ? { vues: Object.fromEntries(sides.map((side) => [side, { image: `token:${side}.png` }])) } : {}),
    shotName: 'object_front',
    userPrompt: '3D from front',
  };
}

async function callTool(args: Record<string, unknown>) {
  return client.callTool({ name: 'make_3d', arguments: args });
}

describe.sequential('MCP make_3d multivue → HTTP factice', () => {
  beforeAll(async () => {
    vi.stubEnv('OPENFIELD_URL', origin);
    vi.stubGlobal('fetch', fakeFetch);
    imageDirectory = await mkdtemp(join(tmpdir(), 'mesh-multivue-'));
    imagePaths = Object.fromEntries(await Promise.all(
      Object.entries(pngs).map(async ([name, data]) => {
        const path = join(imageDirectory, `${name}.png`);
        await writeFile(path, Buffer.from(data, 'base64'));
        return [name, path];
      }),
    )) as Record<'front' | 'left' | 'back' | 'right', string>;
    ({ server } = await import('./server.ts'));
    const [serverTransport, clientTransport] = InMemoryTransport.createLinkedPair();
    client = new Client({ name: 'mesh-multivue-contract', version: '1' });
    await server.connect(serverTransport);
    await client.connect(clientTransport);
  });

  afterAll(async () => {
    try { await client?.close(); } finally {
      try { await server?.close(); } finally {
        if (imageDirectory) await rm(imageDirectory, { recursive: true, force: true });
        vi.unstubAllGlobals();
        vi.unstubAllEnvs();
      }
    }
    const allowed = new Set(['/api/nexora/etat', '/api/takes', '/api/media/42', '/api/media/43', '/api/upload', '/api/generate']);
    expect(allCalls.every((call) => call.url.startsWith(`${origin}/`))).toBe(true);
    expect(allCalls.every((call) => allowed.has(new URL(call.url).pathname))).toBe(true);
  });

  it('annonce le schéma strict left/back/right', async () => {
    beginCase({ kind: 'ready', enabled: true, max: 2 });
    const tool = (await client.listTools()).tools.find((candidate) => candidate.name === 'make_3d');
    const properties = (tool?.inputSchema?.properties ?? {}) as Record<string, any>;
    expect(Object.keys(properties).sort()).toEqual(['count', 'image', 'quality', 'remove_background', 'views']);
    expect(Object.keys(properties.views?.properties ?? {}).sort()).toEqual(['back', 'left', 'right']);
    expect(properties.views?.additionalProperties).toBe(false);
    expect(calls).toHaveLength(0);
  });

  it('génère deux vues totales au plafond 2 et transmet le corps exact', async () => {
    beginCase({ kind: 'ready', enabled: true, max: 2 });
    const result = await callTool(input(['left']));
    expect(result.isError).not.toBe(true);
    expect(at('/api/nexora/etat', 'GET')).toHaveLength(1);
    expect(at('/api/upload', 'POST')).toHaveLength(2);
    expect(at('/api/generate', 'POST').map((call) => call.body)).toEqual([expectedBody(['left'])]);
  });

  it('génère trois vues totales au plafond 3 et transmet le corps exact', async () => {
    beginCase({ kind: 'ready', enabled: true, max: 3 });
    const result = await callTool(input(['left', 'back']));
    expect(result.isError).not.toBe(true);
    expect(at('/api/upload', 'POST')).toHaveLength(3);
    expect(at('/api/generate', 'POST').map((call) => call.body)).toEqual([expectedBody(['left', 'back'])]);
  });

  it('refuse une multivue désactivée avant upload ni génération', async () => {
    beginCase({ kind: 'ready', enabled: false, max: 3 });
    const result = await callTool(input(['left']));
    expect(result.isError).toBe(true);
    expect(toolText(result)).toMatch(/multi-view is unavailable/i);
    expect(at('/api/nexora/etat')).toHaveLength(1);
    expect(at('/api/upload')).toHaveLength(0);
    expect(at('/api/generate')).toHaveLength(0);
  });

  it('refuse le dépassement du plafond explicite avant upload', async () => {
    beginCase({ kind: 'ready', enabled: true, max: 2 });
    const result = await callTool(input(['left', 'back']));
    expect(result.isError).toBe(true);
    expect(toolText(result)).toMatch(/at most 2 views/i);
    expect(at('/api/nexora/etat')).toHaveLength(1);
    expect(at('/api/upload')).toHaveLength(0);
    expect(at('/api/generate')).toHaveLength(0);
  });

  it('refuse un état HTTP réussi mais nul avant upload', async () => {
    beginCase({ kind: 'null' });
    const result = await callTool(input(['left']));
    expect(result.isError).toBe(true);
    expect(toolText(result)).toMatch(/multi-view is unavailable/i);
    expect(at('/api/nexora/etat')).toHaveLength(1);
    expect(at('/api/upload')).toHaveLength(0);
    expect(at('/api/generate')).toHaveLength(0);
  });

  it('refuse la qualité high avant lecture de capacité ou upload', async () => {
    beginCase({ kind: 'ready', enabled: true, max: 3 });
    const result = await callTool(input(['left'], { quality: 'high' }));
    expect(result.isError).toBe(true);
    expect(toolText(result)).toMatch(/draft quality/i);
    expect(at('/api/nexora/etat')).toHaveLength(0);
    expect(at('/api/upload')).toHaveLength(0);
  });

  it('refuse count différent de 1 avant lecture de capacité ou upload', async () => {
    beginCase({ kind: 'ready', enabled: true, max: 3 });
    const result = await callTool(input(['left'], { count: 2 }));
    expect(result.isError).toBe(true);
    expect(toolText(result)).toMatch(/one take/i);
    expect(at('/api/nexora/etat')).toHaveLength(0);
    expect(at('/api/upload')).toHaveLength(0);
  });

  it('rejette une clé de vue inconnue avant toute requête HTTP', async () => {
    beginCase({ kind: 'ready', enabled: true, max: 3 });
    const result = await callTool(input([], { views: { left: imagePaths.left, top: imagePaths.right } }));
    expect(result.isError).toBe(true);
    expect(toolText(result)).toMatch(/Unrecognized key/i);
    expect(calls).toHaveLength(0);
  });

  it('résout l’image principale avant toute image de vue', async () => {
    beginCase({ kind: 'ready', enabled: true, max: 2 });
    const result = await callTool(input(['left'], { image: join(imageDirectory, 'missing.png') }));
    expect(result.isError).toBe(true);
    expect(toolText(result)).toMatch(/No such file/i);
    expect(at('/api/nexora/etat')).toHaveLength(1);
    expect(at('/api/upload')).toHaveLength(0);
    expect(at('/api/generate')).toHaveLength(0);
  });

  it('retombe sur deux vues totales lorsque la lecture de capacité échoue', async () => {
    beginCase({ kind: 'unavailable' });
    const result = await callTool(input(['left']));
    expect(result.isError).not.toBe(true);
    expect(at('/api/nexora/etat')).toHaveLength(1);
    expect(at('/api/upload')).toHaveLength(2);
    expect(at('/api/generate').map((call) => call.body)).toEqual([expectedBody(['left'])]);
  });

  it('refuse trois vues totales sur le fallback indisponible avant upload', async () => {
    beginCase({ kind: 'unavailable' });
    const result = await callTool(input(['left', 'back']));
    expect(result.isError).toBe(true);
    expect(toolText(result)).toMatch(/at most 2 views/i);
    expect(at('/api/nexora/etat')).toHaveLength(1);
    expect(at('/api/upload')).toHaveLength(0);
    expect(at('/api/generate')).toHaveLength(0);
  });

  it('borne à quatre vues totales une capacité excessive et transmet le corps exact', async () => {
    beginCase({ kind: 'ready', enabled: true, max: 99 });
    const result = await callTool(input(['left', 'back', 'right']));
    expect(result.isError).not.toBe(true);
    expect(at('/api/upload')).toHaveLength(4);
    expect(at('/api/generate').map((call) => call.body)).toEqual([expectedBody(['left', 'back', 'right'])]);
  });

  it('garde la compatibilité image seule sans lecture de capacité', async () => {
    beginCase({ kind: 'ready', enabled: false, max: 2 });
    const result = await callTool(input(null));
    expect(result.isError).not.toBe(true);
    expect(at('/api/nexora/etat')).toHaveLength(0);
    expect(at('/api/upload')).toHaveLength(1);
    expect(at('/api/generate').map((call) => call.body)).toEqual([expectedBody([])]);
  });

  it('préserve les identifiants take de l’image principale et de la vue secondaire', async () => {
    beginCase({ kind: 'ready', enabled: true, max: 2 });
    const result = await callTool({
      image: 'take:42',
      quality: 'draft',
      remove_background: false,
      count: 1,
      views: { left: 'take:43' },
    });
    expect(result.isError).not.toBe(true);
    expect(at('/api/takes', 'GET')).toHaveLength(2);
    expect(at('/api/media/42', 'GET')).toHaveLength(0);
    expect(at('/api/media/43', 'GET')).toHaveLength(0);
    expect(at('/api/upload', 'POST')).toHaveLength(0);
    expect(at('/api/generate').map((call) => call.body)).toEqual([{
      kind: 'object',
      app: 'object',
      quality: 'draft',
      removeBackground: false,
      count: 1,
      sourceTake: 42,
      vues: { left: { sourceTake: 43 } },
      shotName: 'object_primary prompt',
      userPrompt: '3D: primary prompt',
    }]);
  });

  it('utilise les prises existantes même si l’import de fichier est indisponible', async () => {
    beginCase({ kind: 'ready', enabled: true, max: 2 });
    uploadUnavailable = true;
    const result = await callTool({ image: 'take:42', quality: 'draft', count: 1, views: { left: 'take:43' } });
    expect(result.isError).not.toBe(true);
    expect(at('/api/upload', 'POST')).toHaveLength(0);
    expect(at('/api/media/42', 'GET')).toHaveLength(0);
    expect(at('/api/media/43', 'GET')).toHaveLength(0);
    expect(at('/api/generate', 'POST').map((call) => call.body)).toEqual([{
      kind: 'object', app: 'object', quality: 'draft', removeBackground: true, count: 1,
      sourceTake: 42, vues: { left: { sourceTake: 43 } },
      shotName: 'object_primary prompt', userPrompt: '3D: primary prompt',
    }]);
  });

  it.each(['take:44', 'take:45', 'take:999'])('refuse la prise invalide %s sans import ni génération', async (image) => {
    beginCase({ kind: 'ready', enabled: true, max: 2 });
    const result = await callTool({ image });
    expect(result.isError).toBe(true);
    expect(at('/api/upload', 'POST')).toHaveLength(0);
    expect(at('/api/generate', 'POST')).toHaveLength(0);
  });

  it('refuse aussi une vue secondaire qui est une prise non terminée', async () => {
    beginCase({ kind: 'ready', enabled: true, max: 2 });
    const result = await callTool({ image: 'take:42', views: { left: 'take:45' } });
    expect(result.isError).toBe(true);
    expect(at('/api/upload', 'POST')).toHaveLength(0);
    expect(at('/api/generate', 'POST')).toHaveLength(0);
  });

  it('relaie le refus du serveur pour une prise existante', async () => {
    beginCase({ kind: 'ready', enabled: true, max: 2 }, 422);
    const result = await callTool({ image: 'take:42' });
    expect(result.isError).toBe(true);
    expect(toolText(result)).toContain('server final capacity refusal');
    expect(at('/api/upload', 'POST')).toHaveLength(0);
    expect(at('/api/generate', 'POST')).toHaveLength(1);
  });

  it('accepte une seule prise existante sans lire la capacité ni importer son fichier', async () => {
    beginCase({ kind: 'ready', enabled: false, max: 2 });
    const result = await callTool({ image: 'take:42' });
    expect(result.isError).not.toBe(true);
    expect(at('/api/nexora/etat')).toHaveLength(0);
    expect(at('/api/media/42')).toHaveLength(0);
    expect(at('/api/upload')).toHaveLength(0);
    expect(at('/api/generate').map((call) => call.body)).toEqual([{
      kind: 'object', app: 'object', quality: 'draft', removeBackground: true, count: 1,
      sourceTake: 42, shotName: 'object_primary prompt', userPrompt: '3D: primary prompt',
    }]);
  });

  it('importe uniquement la vue locale lorsqu’une prise est utilisée comme face avant', async () => {
    beginCase({ kind: 'ready', enabled: true, max: 2 });
    const result = await callTool({ image: 'take:42', views: { left: imagePaths.left } });
    expect(result.isError).not.toBe(true);
    expect(at('/api/media/42')).toHaveLength(0);
    expect(at('/api/upload').map((call) => (call.body as { name: string }).name)).toEqual(['left.png']);
    expect(at('/api/generate').map((call) => call.body)).toEqual([{
      kind: 'object', app: 'object', quality: 'draft', removeBackground: true, count: 1,
      sourceTake: 42, vues: { left: { image: 'token:left.png' } },
      shotName: 'object_primary prompt', userPrompt: '3D: primary prompt',
    }]);
  });

  it('conserve le refus HTTP final sans annoncer queued', async () => {
    beginCase({ kind: 'ready', enabled: true, max: 2 }, 422);
    const result = await callTool(input(['left']));
    expect(result.isError).toBe(true);
    expect(toolText(result)).toContain('server final capacity refusal');
    expect(JSON.stringify(result)).not.toContain('"queued": true');
    expect(at('/api/nexora/etat')).toHaveLength(1);
    expect(at('/api/upload')).toHaveLength(2);
    expect(at('/api/generate')).toHaveLength(1);
  });
});
