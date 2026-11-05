import { expect, it } from 'vitest';
import { mkdtempSync, statSync } from 'node:fs';
import { join } from 'node:path';
import { tmpdir } from 'node:os';
import { creerExportProres } from './exportProres.js';
function base() { const root=mkdtempSync(join(tmpdir(),'export-prores-real-')); return { root, exports: join(root,'exports') }; }

it.skipIf(!process.env.TEST_FFMPEG || !process.env.TEST_FFPROBE)('valide un export FFmpeg CPU réel sur média synthétique', async () => {
  const { execFileSync } = await import('node:child_process');
  const { argsExport } = await import('./film.js');
  const { sansEcrasement } = await import('./filmSorties.js');
  const { verifierProres } = await import('./exportProres.js');
  const { executerBorne } = await import('./executionBornee.js');
  const ffmpeg = process.env.TEST_FFMPEG; const ffprobe = process.env.TEST_FFPROBE;
  if (!ffmpeg || !ffprobe) throw new Error('TEST_FFMPEG et TEST_FFPROBE explicites requis');
  const b = base(); const entree = join(b.root, 'lavfi.mp4');
  execFileSync(ffmpeg, ['-v','error','-n','-f','lavfi','-i','testsrc2=size=160x90:rate=24','-f','lavfi','-i','sine=frequency=440:sample_rate=48000','-t','0.25','-threads','2','-c:v','libx264','-c:a','aac',entree], { timeout:30000 });
  const exporteur = creerExportProres(async (source, p) => { await executerBorne(ffmpeg, ['-nostdin','-v','error', ...sansEcrasement(argsExport(source,p,'prores'))], 30000); }, async (p, source) => verifierProres(p, source, ffprobe));
  const sortie = await exporteur(2, entree, b.exports);
  expect(statSync(sortie).size).toBeGreaterThan(0);
}, 60_000);
