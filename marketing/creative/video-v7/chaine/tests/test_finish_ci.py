"""Essais réels CPU Finish sur petits flux synthétiques, jamais sur GPU ni réseau."""
import csv
import io
import json
import runpy
import os
from pathlib import Path
import subprocess
import sys
import unittest
from unittest.mock import patch

ROOT = Path(os.environ['V7_TEST_TMPDIR']).resolve()
REPO = Path(__file__).resolve().parents[5]
BANC = REPO / 'recherche/30-annexes/finish-banc/banc_finish.py'
DIX = BANC.with_name('profondeur_10bits.py')
FF = os.environ['V6_FFMPEG']
FP = os.environ['V6_FFPROBE']

class FinishCI(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.base = ROOT / 'finish-ci'
        cls.base.mkdir(exist_ok=False)
        cls.medias = cls.base / 'medias'
        cls.medias.mkdir()
        # Les profils désignent des candidatures de test, pas des sorties NVENC.
        source = cls.base / 'source.mkv'
        subprocess.run([FF, '-v', 'error', '-nostdin', '-n', '-f', 'lavfi', '-i',
                        'testsrc2=size=64x64:rate=24:duration=12', '-c:v', 'ffv1',
                        '-threads', '2', str(source)], check=True)
        for codec, profil, pix in [('libx264', 'h264', 'yuv420p'), ('libx265', 'hevc10', 'yuv420p10le')]:
            cmd = [FF, '-v', 'error', '-nostdin', '-n', '-threads', '2', '-i', str(source),
                   '-an', '-c:v', codec, '-threads', '2', '-pix_fmt', pix]
            if codec == 'libx265': cmd += ['-x265-params', 'pools=1:frame-threads=1:wpp=0:log-level=error']
            subprocess.run([*cmd, str(cls.base / (profil + '.mp4'))], check=True)
        for clip in ('action', 'bureau', 'espace'):
            os.link(source, cls.medias / (clip + '-source.mkv'))
            for profil in ('h264-p4', 'h264-p7', 'hevc10-p4', 'hevc10-p7'):
                template = 'h264.mp4' if profil.startswith('h264') else 'hevc10.mp4'
                os.link(cls.base / template, cls.medias / (clip + '-' + profil + '.mp4'))

    def lance(self, name, args, success=True):
        cmd = [sys.executable, '-m', 'coverage', 'run', '--parallel-mode', '--branch', *map(str, args)]
        p = subprocess.run(cmd, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        (self.base / (name + '.log')).write_text(p.stdout + '\n' + p.stderr)
        self.assertEqual(p.returncode == 0, success, p.stdout[-1000:] + p.stderr[-1000:])
        return p

    def test_parcours_et_refus(self):
        out = self.base / 'resultats'
        self.lance('banc', [BANC, self.medias, out, '--ffmpeg', FF, '--ffprobe', FP])
        self.lance('10bits', [DIX, self.medias, out, '--ffmpeg', FF])
        rows = json.loads((out / 'mesures.json').read_text())
        rows10 = json.loads((out / 'mesures-10bits.json').read_text())
        self.assertEqual(len(rows), 12)
        self.assertEqual(len(rows10), 12)
        self.assertTrue(all(r['images'] == 288 and r['fps'] == 24 for r in rows))
        self.assertTrue(all(len(r['x264_sha256']) == 64 for r in rows))
        self.lance('refus-ecrasement', [BANC, self.medias, out, '--ffmpeg', FF, '--ffprobe', FP], False)
        self.lance('refus-reprise-10bits', [DIX, self.medias, out, '--ffmpeg', FF], False)
        self.lance('profil-invalide', [BANC, self.medias, self.base / 'profil-invalide', '--profil-x264', 'bad'], False)
        self.lance('probe-inexistant', [BANC, self.medias, self.base / 'probe-inexistant', '--ffmpeg', FF, '--ffprobe', '/inexistant'], False)
        self.lance('probe-echec', [BANC, self.medias, self.base / 'probe-echec', '--ffmpeg', FF, '--ffprobe', '/bin/false'], False)
        for label, frames, size in [('court', 1, '64x64'), ('dimension', 288, '32x32')]:
            bad = self.base / (label + '.mkv')
            subprocess.run([FF, '-v', 'error', '-nostdin', '-n', '-f', 'lavfi', '-i',
                            'testsrc2=size='+size+':rate=24', '-frames:v', str(frames),
                            '-c:v', 'ffv1', '-threads', '2', str(bad)], check=True)
            inputs = self.base / ('medias-' + label); inputs.mkdir()
            os.link(bad if label == 'court' else self.base / 'source.mkv', inputs / 'action-source.mkv')
            os.link(bad if label == 'dimension' else self.base / 'h264.mp4', inputs / 'action-h264-p4.mp4')
            self.lance('banc-' + label, [BANC, inputs, self.base / ('sortie-' + label), '--profils', 'h264-p4', '--ffmpeg', FF, '--ffprobe', FP], False)

        # FFmpeg éteint en milieu de mesure : échec réel, sans inventer de score.
        interrupted = self.base / 'ffmpeg-echec'; interrupted.mkdir()
        for row in rows:
            name = row['clip'] + '-x264-' + row['profil_nvenc'] + '.mp4'
            os.link(out / name, interrupted / name)
        (interrupted / 'mesures.json').write_text(json.dumps(rows))
        self.lance('ffmpeg-echec', [DIX, self.medias, interrupted, '--ffmpeg', '/bin/false'], False)

        # Un manifeste altéré est rejeté avant toute mesure 10 bits.
        altered = self.base / 'sha-altere'
        altered.mkdir()
        for row in rows:
            name = row['clip'] + '-x264-' + row['profil_nvenc'] + '.mp4'
            os.link(out / name, altered / name)
        rows[0]['source_sha256'] = '0' * 64
        (altered / 'mesures.json').write_text(json.dumps(rows))
        self.lance('sha-altere', [DIX, self.medias, altered, '--ffmpeg', FF], False)

    def test_main_et_garde_home(self):
        out = self.base / 'main'
        self.lance('main', [BANC, self.medias, out, '--profils', 'h264-p4', '--profil-x264', 'main', '--ffmpeg', FF, '--ffprobe', FP])
        self.assertEqual(len(json.loads((out / 'mesures.json').read_text())), 3)
        self.lance('main-10bits', [DIX, self.medias, out, '--ffmpeg', FF])
        env = dict(os.environ, HOME='/home/interdit')
        cmd = [sys.executable, '-m', 'coverage', 'run', '--parallel-mode', '--branch', str(REPO / 'marketing/creative/video-v7/chaine/ci_tests.py')]
        p = subprocess.run(cmd, env=env, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        (self.base / 'home-interdit.log').write_text(p.stdout + '\n' + p.stderr)
        self.assertNotEqual(p.returncode, 0)
        self.assertIn('doivent être sous V7_CI_ROOT', p.stderr)
        env = dict(os.environ, HOME=os.environ['V7_TEST_TMPDIR'])
        p = subprocess.run(cmd, env=env, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self.assertNotEqual(p.returncode, 0)
        self.assertIn('doivent être distincts', p.stderr)
        escape = self.base / 'home-escape'; escape.symlink_to('/home/interdit')
        env = dict(os.environ, HOME=str(escape))
        p = subprocess.run(cmd, env=env, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self.assertNotEqual(p.returncode, 0)
        self.assertIn('Chemin résolu hors', p.stderr)

    def test_verificateur_refuse_corruptions(self):
        verifier = BANC.with_name('verifier_paquet.py')
        package = verifier.parent
        original_text, original_bytes, original_open = Path.read_text, Path.read_bytes, Path.open
        def execute(mode):
            summary = json.loads(original_text(package / 'synthese.json'))
            if mode == 'doublon': summary['resultats_high'][1] = dict(summary['resultats_high'][0])
            if mode == 'correction': summary['resultats_main_corrections'][0]['ecart_corrige_pct'] = 1.0
            def text(path, *args, **kwargs):
                if path == package / 'synthese.json' and mode in ('doublon', 'correction'):
                    return json.dumps(summary)
                return original_text(path, *args, **kwargs)
            def bytes_(path):
                data = original_bytes(path)
                return data + b'x' if mode == 'sha' and path == package / 'synthese.json' else data
            def open_(path, *args, **kwargs):
                file_mode = kwargs.get('mode', args[0] if args else 'r')
                if 'b' in file_mode: return original_open(path, *args, **kwargs)
                if path == package / 'resultats-high.csv' and mode in ('tronque', 'cellule'):
                    with original_open(path, encoding='utf-8') as stream: content = stream.read()
                    if mode == 'tronque': content = content.splitlines()[0] + '\n'
                    else: content = content.replace('action,', 'alteree,', 1)
                    return io.StringIO(content, newline='')
                if path == package / 'resultats-main-corrections.csv' and mode == 'correction':
                    rows = summary['resultats_main_corrections']; output = io.StringIO(newline='')
                    writer = csv.DictWriter(output, fieldnames=rows[0]); writer.writeheader(); writer.writerows(rows); output.seek(0)
                    return output
                return original_open(path, *args, **kwargs)
            with patch.object(Path, 'read_text', text), patch.object(Path, 'read_bytes', bytes_), patch.object(Path, 'open', open_):
                with self.assertRaises(ValueError): runpy.run_path(str(verifier), run_name='__main__')
        for mode in ('sha', 'doublon', 'tronque', 'cellule', 'correction'):
            with self.subTest(mode=mode): execute(mode)

if __name__ == '__main__': unittest.main(verbosity=2)
