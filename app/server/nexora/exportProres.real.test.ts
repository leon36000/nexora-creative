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

it.skipIf(!process.env.TEST_FFMPEG || !process.env.TEST_FFPROBE)('refuse une vidéo tronquée et accepte VFR et WebM sans durée de flux', async () => {
  const { execFileSync } = await import('node:child_process');
  const { verifierProres } = await import('./exportProres.js');
  const { argsExport } = await import('./film.js');
  const { sansEcrasement } = await import('./filmSorties.js');
  const ffmpeg = process.env.TEST_FFMPEG; const ffprobe = process.env.TEST_FFPROBE;
  if (!ffmpeg || !ffprobe) throw new Error('TEST_FFMPEG et TEST_FFPROBE explicites requis');
  const b = base();
  const f = (name: string) => join(b.root, name);
  const run = (...args: string[]) => execFileSync(ffmpeg, ['-v','error','-nostdin','-n', ...args], { timeout:30000 });
  const prores = ['-c:v','prores_ks','-profile:v','3','-pix_fmt','yuv422p10le','-threads','2','-c:a','pcm_s16le'];
  const exporter = (source: string, sortie: string) => { const args = sansEcrasement(argsExport(source, sortie, 'prores')); args.splice(args.length - 1, 0, '-threads', '2'); run(...args); };
  run('-f','lavfi','-i','testsrc2=size=160x90:rate=24:duration=2','-f','lavfi','-i','sine=frequency=440:sample_rate=48000:duration=2','-c:v','libx264','-threads','2','-c:a','aac',f('source.mp4'));
  run('-i',f('source.mp4'),'-vf','trim=duration=0.5,setpts=PTS-STARTPTS',...prores,f('tronque.mov'));
  exporter(f('source.mp4'), f('complet.mov'));
  await expect(verifierProres(f('tronque.mov'), f('source.mp4'), ffprobe)).rejects.toThrow('temporel');
  await expect(verifierProres(f('complet.mov'), f('source.mp4'), ffprobe)).resolves.toBeUndefined();
  run('-f','lavfi','-i','testsrc2=size=160x90:rate=24:duration=2','-vf',"select='not(mod(n,2))+not(mod(n,5))'",'-fps_mode','vfr','-c:v','libx264','-threads','2',f('vfr.mp4'));
  exporter(f('vfr.mp4'), f('vfr.mov'));
  const sonde = (nom: string) => JSON.parse(execFileSync(ffprobe, ['-v','error','-select_streams','v:0','-count_frames','-show_entries','stream=nb_read_frames,duration,start_time','-of','json',f(nom)], {encoding:'utf8',timeout:30000})).streams[0];
  expect(sonde('vfr.mp4').nb_read_frames).not.toBe(sonde('vfr.mov').nb_read_frames);
  await expect(verifierProres(f('vfr.mov'), f('vfr.mp4'), ffprobe)).resolves.toBeUndefined();
  run('-f','lavfi','-i','testsrc2=size=160x90:rate=24:duration=2','-c:v','libvpx-vp9','-deadline','realtime','-cpu-used','8','-threads','2',f('source.webm'));
  exporter(f('source.webm'), f('webm.mov'));
  expect(sonde('source.webm').duration).toBeUndefined();
  await expect(verifierProres(f('webm.mov'), f('source.webm'), ffprobe)).resolves.toBeUndefined();
  run('-i',f('source.mp4'),'-map','0','-c','copy','-output_ts_offset','1',f('offset.mp4'));
  exporter(f('offset.mp4'), f('offset.mov'));
  expect(Number(sonde('offset.mp4').start_time)).toBeGreaterThan(0.5);
  expect(Number(sonde('offset.mov').start_time)).toBeLessThan(0.1);
  await expect(verifierProres(f('offset.mov'), f('offset.mp4'), ffprobe)).resolves.toBeUndefined();
}, 120_000);
