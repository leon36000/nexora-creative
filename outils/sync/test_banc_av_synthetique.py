"""Exercice CPU de la CLI : médias synthétiques conservés sous SYNC_TEST_ROOT."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


CLI = Path(__file__).with_name('banc_av_synthetique.py')


class BancAVSynthetiqueTest(unittest.TestCase):
    def test_offsets_et_refus_ecrasement(self):
        root = Path(os.environ['SYNC_TEST_ROOT'])
        root.mkdir(parents=True, exist_ok=True)
        work = Path(tempfile.mkdtemp(prefix='banc-av-fixture-', dir=root))
        destination = work / 'resultats'
        args = [sys.executable, str(CLI), str(destination), '--ffmpeg', os.environ['SYNC_FFMPEG'],
                '--ffprobe', os.environ['SYNC_FFPROBE']]
        result = subprocess.run(args, capture_output=True, text=True, timeout=60)
        self.assertEqual(result.returncode, 0, result.stderr)
        report = json.loads((destination / 'resultats.json').read_text())
        public = json.loads(result.stdout)
        self.assertEqual(len(public['resultats']), 3)
        cases = {item['media']: item for item in report['resultats']}
        self.assertEqual(set(cases), {'zero.mkv', 'retard_audio.mkv', 'avance_audio.mkv'})
        for name, expected in [('zero', 0.0), ('retard_audio', .2), ('avance_audio', -.2)]:
            row = cases[name + '.mkv']
            self.assertEqual(row['offset_secondes'], expected)
            self.assertEqual(row['attendu_secondes'], expected)
            self.assertEqual(row['video_frame'], 20)
            self.assertEqual(row['sha256'], hashlib.sha256((destination / row['media']).read_bytes()).hexdigest())
            self.assertTrue((destination / (name + '.gray')).is_file())
            self.assertTrue((destination / (name + '.pcm')).is_file())
        self.assertEqual(public['resultats'], [{k: row[k] for k in
            ('media', 'sha256', 'video_frame', 'audio_sample', 'offset_secondes', 'attendu_secondes')}
            for row in report['resultats']])
        before = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in destination.iterdir() if p.is_file()}
        self.assertEqual(len(before), 10)
        retry = subprocess.run(args, capture_output=True, text=True, timeout=60)
        self.assertNotEqual(retry.returncode, 0)
        after = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in destination.iterdir() if p.is_file()}
        self.assertEqual(after, before)
        print('Fixtures banc AV synthétiques conservées :', work, flush=True)

    def test_binaire_absent_refuse_avant_creation(self):
        root = Path(os.environ['SYNC_TEST_ROOT'])
        root.mkdir(parents=True, exist_ok=True)
        work = Path(tempfile.mkdtemp(prefix='banc-av-refus-', dir=root))
        destination = work / 'non-cree'
        result = subprocess.run([sys.executable, str(CLI), str(destination), '--ffmpeg', str(work / 'absent'),
                                 '--ffprobe', os.environ['SYNC_FFPROBE']], capture_output=True, text=True, timeout=30)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('Exécutable absolu invalide', result.stderr)
        self.assertFalse(destination.exists())


if __name__ == '__main__':
    unittest.main()
