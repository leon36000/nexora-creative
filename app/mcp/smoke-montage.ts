/**
 * Preuve de bout en bout du harnais de montage par MCP, sans moteur ni GPU : génère de petits médias synthétiques avec
 * ffmpeg, puis analyse → montage_auto → validation/mesure → rustine → rendu MP4 → relecture du rendu.
 *   npx tsx mcp/smoke-montage.ts      (ou : npm run mcp:smoke:montage)
 */
import assert from 'node:assert/strict';
import { execFileSync } from 'node:child_process';
import { existsSync, mkdtempSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { Client } from '@modelcontextprotocol/sdk/client/index.js';
import { StdioClientTransport } from '@modelcontextprotocol/sdk/client/stdio.js';
import { ffmpegParDefaut } from '../server/nexora/montage/analyse.ts';

const here = dirname(fileURLToPath(import.meta.url));
const ff = ffmpegParDefaut();
const d = mkdtempSync(join(tmpdir(), 'nx-mcp-montage-'));
try {
  const media = (nom: string, src: string, extra: string[] = []) => execFileSync(ff, ['-v', 'error', '-y', '-f', 'lavfi', '-i', src, ...extra, join(d, nom)]);
  media('a.mp4', 'testsrc2=s=320x180:r=24:d=12', ['-pix_fmt', 'yuv420p']);
  media('b.mp4', 'smptebars=s=320x180:r=24:d=12', ['-pix_fmt', 'yuv420p']);
  media('c.mp4', 'life=s=320x180:r=24:mold=10:ratio=0.1:death_color=#00c800:life_color=#ffc800,scale=320:180,format=yuv420p', ['-t', '12']);
  execFileSync(ff, ['-v', 'error', '-y', '-f', 'lavfi', '-i', 'aevalsrc=0.8*sin(2*PI*110*t)*exp(-8*mod(t\\,0.5)):d=24:s=22050', join(d, 'musique.wav')]);

  const client = new Client({ name: 'smoke-montage', version: '0.1.0' });
  await client.connect(new StdioClientTransport({ command: process.execPath, args: ['--import', 'tsx', join(here, 'server.ts')], env: process.env as Record<string, string>, stderr: 'ignore' }));
  const outils = (await client.listTools()).tools.map((t) => t.name);
  for (const n of ['montage_analyze_media', 'montage_auto', 'montage_valider', 'montage_revise', 'montage_rendre', 'montage_savoir', 'montage_proposer_exemplaire']) assert.ok(outils.includes(n), `outil manquant : ${n}`);
  const json = (r: any) => JSON.parse(r.content[0].text);

  const medias = { m1: join(d, 'a.mp4'), m2: join(d, 'b.mp4'), m3: join(d, 'c.mp4') };
  const ctx = { brief: 'Publicité de 15 s pour un café', genre: 'pub', format: '16:9', duree_cible_s: 15, medias, musique: { musique: join(d, 'musique.wav') }, textes: ['Le vrai café du quartier.', 'Essayez-le cette semaine'] };
  const vues = json(await client.callTool({ name: 'montage_analyze_media', arguments: { fichiers: { ...medias, musique: join(d, 'musique.wav') } } }));
  assert.ok(vues.some((v: string) => v.includes('BPM')), 'la musique doit avoir un tempo');
  console.log(vues.at(-1));

  const plan = json(await client.callTool({ name: 'montage_auto', arguments: ctx }));
  assert.equal(plan.version, 1);
  const v = json(await client.callTool({ name: 'montage_valider', arguments: { ...ctx, plan } }));
  assert.equal(v.valide, true);
  console.log(`montage_auto : ${plan.video.length} plans, score ${v.score}`, v.metriques);

  const r = json(await client.callTool({ name: 'montage_revise', arguments: { ...ctx, plan, rustines: [{ op: 'regler_audio', cible_lufs: -16 }] } }));
  assert.equal(r.ok, true);

  const sortie = join(d, 'film.mp4');
  const rendu = json(await client.callTool({ name: 'montage_rendre', arguments: { plan, medias: { ...medias, musique: join(d, 'musique.wav') }, sortie, apercu: true } }));
  assert.equal(rendu.ok, true, JSON.stringify(rendu));
  assert.ok(existsSync(sortie));
  const analyse = json(await client.callTool({ name: 'montage_analyze_media', arguments: { fichiers: { film: sortie } } }));
  console.log(analyse[0]);
  assert.match(analyse[0], /15\.\d s|14\.\d s/);
  await client.close();
  console.log('OK : montage de bout en bout par MCP');
} finally {
  rmSync(d, { recursive: true, force: true });
}
