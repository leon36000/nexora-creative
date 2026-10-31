import { describe, expect, it } from 'vitest';
import { analyserSortieFfmpeg, argsControle, verdictControle } from './controle.js';

const BON = `  Duration: 00:00:05.17, start: 0.000000, bitrate: 4890 kb/s
[Parsed_volumedetect_0 @ 0x1] mean_volume: -18.9 dB
[Parsed_volumedetect_0 @ 0x1] max_volume: -3.9 dB`;

const NOIR = `  Duration: 00:00:02.00, start: 0.000000, bitrate: 19 kb/s
[Parsed_volumedetect_0 @ 0x1] mean_volume: -91.0 dB
[Parsed_volumedetect_0 @ 0x1] max_volume: -91.0 dB
[freezedetect @ 0x2] lavfi.freezedetect.freeze_start: 0
[blackdetect @ 0x3] black_start:0 black_end:1.96 black_duration:1.96`;

describe('contrôle qualité déterministe d’une prise', () => {
  it('lit durée, noir, image figée et volume dans la sortie de ffmpeg', () => {
    expect(analyserSortieFfmpeg(BON)).toEqual({ duree: 5.17, noirS: 0, figeS: 0, volumeMoyenDb: -18.9, volumeMaxDb: -3.9 });
    expect(analyserSortieFfmpeg(NOIR)).toEqual({ duree: 2, noirS: 1.96, figeS: 2, volumeMoyenDb: -91, volumeMaxDb: -91 });
  });

  it('accepte une bonne prise et explique les défauts d’une mauvaise, en français', () => {
    expect(verdictControle(analyserSortieFfmpeg(BON), { dureeAttendue: 5.17, sonAttendu: true })).toEqual({ ok: true, defauts: [] });
    const v = verdictControle(analyserSortieFfmpeg(NOIR), { dureeAttendue: 5.17, sonAttendu: true });
    expect(v.ok).toBe(false);
    expect(v.defauts.join(' ')).toMatch(/noire/);
    expect(v.defauts.join(' ')).toMatch(/figée/);
    expect(v.defauts.join(' ')).toMatch(/silencieu/);
    expect(v.defauts.join(' ')).toMatch(/durée/);
  });

  it('ne réclame pas de son quand le moteur n’en produit pas', () => {
    const muet = { duree: 5.04, noirS: 0, figeS: 0, volumeMoyenDb: null, volumeMaxDb: null };
    expect(verdictControle(muet, { dureeAttendue: 5.04, sonAttendu: false }).ok).toBe(true);
    expect(verdictControle(muet, { dureeAttendue: 5.04, sonAttendu: true }).defauts.join(' ')).toMatch(/son/);
  });

  it('lance ffmpeg avec les trois détecteurs', () => {
    const a = argsControle('/v.mp4', true).join(' ');
    expect(a).toMatch(/blackdetect/);
    expect(a).toMatch(/freezedetect/);
    expect(a).toMatch(/volumedetect/);
    expect(argsControle('/v.mp4', false).join(' ')).not.toMatch(/volumedetect/);
  });
});
