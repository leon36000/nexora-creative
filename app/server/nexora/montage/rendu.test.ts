import { execFileSync } from 'node:child_process';
import { existsSync, mkdtempSync, readFileSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { describe, expect, it } from 'vitest';
import { analyserMedia, ffmpegParDefaut } from './analyse.js';
import type { EditPlan } from './editplan.js';
import { commandeRendu, fichierAssTextes, rendreEditPlan } from './rendu.js';

const plan = (): EditPlan => ({
  version: 1, fps: 24, format: '16:9', genre: 'explicatif',
  sources: { a: { kind: 'video', duree_f: 96 }, b: { kind: 'video', duree_f: 96 }, mus: { kind: 'audio', duree_f: 480 }, voix: { kind: 'audio', duree_f: 480 } },
  video: [
    { id: 'p1', src: 'a', entree_f: 0, duree_f: 48, vitesse: 1, transition_in: { type: 'cut', duree_f: 0 }, zoom: { de: 1, a: 1.1 } },
    { id: 'p2', src: 'b', entree_f: 0, duree_f: 48, vitesse: 1, transition_in: { type: 'fondu', duree_f: 12 } },
    { id: 'p3', src: 'a', entree_f: 48, duree_f: 36, vitesse: 1, rampe: { de: 0.5, a: 2 }, transition_in: { type: 'cut', duree_f: 0 } },
  ],
  audio: { musique: { src: 'mus', entree_f: 0, duree_f: 120, gain_db: -14, fondu_in_f: 6, fondu_out_f: 24 }, voix: [{ src: 'voix', debut_f: 12, entree_f: 0, duree_f: 84, gain_db: 0 }], ducking: { actif: true, profondeur_db: 10 }, cible_lufs: -14, crete_db: -1, fondu_coupe_ms: 30 },
  textes: [{ texte: 'Bonjour le monde.', debut_f: 6, duree_f: 48, style: 'titre', position: 'bas', taille_pct: 6 }],
  generations: [],
});

describe('rendu ffmpeg d’un EditPlan', () => {
  it('construit un graphe : concat, xfade décalé, ass en dernier, ducking, loudnorm', () => {
    const c = commandeRendu(plan(), (s) => `/m/${s}.mp4`, '/o.mp4', { taille: [320, 180] }, '/o.ass');
    const g = c.args[c.args.indexOf('-filter_complex') + 1];
    expect(g).toContain('xfade=transition=fade:duration=0.5:offset=1.5');
    expect(g).toContain('concat=n=6'); // rampe en 6 morceaux
    expect(g.indexOf("ass='/o.ass'")).toBeGreaterThan(g.indexOf('xfade'));
    expect(g).toContain('sidechaincompress'); expect(g).toContain('loudnorm=I=-14:TP=-1');
    expect(c.dureeS).toBeCloseTo((48 + 48 - 12 + 36) / 24);
    expect(c.ass).toContain('Bonjour le monde.');
    expect(fichierAssTextes(plan(), 320, 180)).toContain('PlayResX: 320');
  });
  it('refuse de rendre un plan invalide', async () => {
    const p = plan(); p.video[0].entree_f = 500;
    const r = await rendreEditPlan(p, () => '/x.mp4', '/tmp/inutile.mp4');
    expect(r.ok).toBe(false);
  });
  const ff = ffmpegParDefaut();
  const dispo = (() => { try { execFileSync(ff, ['-version'], { stdio: 'ignore' }); return true; } catch { return false; } })();
  it.skipIf(!dispo)('rend un vrai petit film : durée, son normalisé à −14 LUFS', async () => {
    const d = mkdtempSync(join(tmpdir(), 'nx-rendu-'));
    try {
      const mk = (nom: string, src: string, audio = false) => { execFileSync(ff, ['-v', 'error', '-y', '-f', 'lavfi', '-i', src, ...(audio ? [] : ['-pix_fmt', 'yuv420p']), join(d, nom)]); };
      mk('a.mp4', 'testsrc2=s=160x90:r=24:d=4'); mk('b.mp4', 'smptebars=s=160x90:r=24:d=4');
      mk('mus.wav', 'sine=f=220:d=20', true); mk('voix.wav', 'sine=f=880:d=20', true);
      const sortie = join(d, 'film.mp4');
      const r = await rendreEditPlan(plan(), (s) => join(d, { a: 'a.mp4', b: 'b.mp4', mus: 'mus.wav', voix: 'voix.wav' }[s]!), sortie, { ffmpeg: ff, taille: [320, 180] });
      expect(r.ok).toBe(true);
      expect(existsSync(sortie)).toBe(true);
      const a = await analyserMedia(sortie, { ffmpeg: ff, cache: false });
      expect(a.duree_s).toBeGreaterThan(4.9); expect(a.duree_s).toBeLessThan(5.2);
      expect(a.a_video && a.a_audio).toBe(true);
      expect(Math.abs((a.loudness?.integre_lufs ?? 0) + 14)).toBeLessThan(3.5);
      expect(readFileSync(join(d, 'film.mp4.ass'), 'utf8')).toContain('Dialogue');
    } finally { rmSync(d, { recursive: true, force: true }); }
  }, 120_000);
});
