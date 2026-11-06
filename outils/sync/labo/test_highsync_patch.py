"""Tests CPU des préimages et de la création exclusive du runner HighSync."""
import hashlib
from pathlib import Path
import tempfile
import unittest

from outils.sync.labo import highsync_patch as patch

FIXTURE = Path(__file__).parent / 'highsync_fixture' / 'inference.py.txt'


class PatchHighSyncTest(unittest.TestCase):
    def test_source_epinglee_et_runner_compilable(self):
        source = FIXTURE.read_bytes()
        self.assertEqual(hashlib.sha256(source).hexdigest(), patch.SOURCE_SHA256)
        resultat = patch.adapter(source)
        compile(resultat, 'highsync_adapte', 'exec')
        texte = resultat.decode()
        self.assertNotIn('os.system(', texte)
        self.assertNotIn('shell=True', texte)
        self.assertNotIn('pretrained.dns64()', texte)
        self.assertIn('source_frames < audio_frame_num', texte)
        self.assertIn('count_img != video_length', texte)

    def test_source_alteree_refusee(self):
        with self.assertRaises(ValueError):
            patch.adapter(FIXTURE.read_bytes() + b' ')

    def test_sortie_exclusive_conserve_temoin(self):
        with tempfile.TemporaryDirectory() as repertoire:
            cible = Path(repertoire) / 'runner.py'
            cible.write_bytes(b'temoin')
            with self.assertRaises(FileExistsError):
                patch.ecrire_source(FIXTURE, cible)
            self.assertEqual(cible.read_bytes(), b'temoin')


if __name__ == '__main__':
    unittest.main()
