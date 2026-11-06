"""Tests FFmpeg réels : médias factices conservés dans SYNC_TEST_ROOT."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import unittest
import uuid
from unittest import mock

from outils.sync.labo.highsync_export import exporter

ROOT = Path(os.environ.get('SYNC_TEST_ROOT') or os.environ['TMPDIR'])
FFMPEG = Path(os.environ.get('SYNC_TEST_FFMPEG') or os.environ.get('SYNC_FFMPEG') or shutil.which('ffmpeg'))
FFPROBE = Path(os.environ.get('SYNC_TEST_FFPROBE') or os.environ.get('SYNC_FFPROBE') or shutil.which('ffprobe'))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


class ExportTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root = ROOT / ('highsync-export-fixture-'+uuid.uuid4().hex)
        cls.root.mkdir(parents=True)
        cls.audio=cls.root/'source.wav';cls.brut=cls.root/'brut27.mp4';cls.court=cls.root/'brut23.mp4'
        def ff(*args):
            subprocess.run([str(FFMPEG),'-v','error','-nostdin','-n',*args],check=True,timeout=30)
        ff('-f','lavfi','-i','sine=frequency=440:sample_rate=16000:duration=1',str(cls.audio))
        for path, frames in ((cls.brut,27),(cls.court,23)):
            ff('-f','lavfi','-i','testsrc2=s=64x64:r=25','-frames:v',str(frames),'-c:v','libx264','-pix_fmt','yuv420p',str(path))

    def test_export_lossless_25_et_pcm_integral_telephone(self):
        src_before, audio_before=sha(self.brut),sha(self.audio)
        run=exporter(self.root,self.brut,src_before,self.audio,audio_before,FFMPEG,FFPROBE,True)
        d=json.loads((run/'manifest.json').read_text())
        self.assertEqual(d['statut'],'canonique_et_telephone_valides',d.get('erreur'))
        self.assertEqual(d['images_source'],27)
        self.assertEqual(d['images_cibles'],25)
        self.assertEqual(d['echantillons_pcm'],16000)
        self.assertTrue(d['validation_av']['valide'])
        self.assertTrue(d['validation_telephone']['valide'])
        self.assertLess(d['telephone_octets'],28_000_000)
        self.assertEqual((sha(self.brut),sha(self.audio)),(src_before,audio_before))

    def test_video_trop_courte_refusee_avant_creation(self):
        avant=set(self.root.iterdir())
        with self.assertRaisesRegex(ValueError,'trop courte'):
            exporter(self.root,self.court,sha(self.court),self.audio,sha(self.audio),FFMPEG,FFPROBE)
        self.assertEqual(set(self.root.iterdir()),avant)

    def test_refus_reutilisation_namespace_sans_ecrasement(self):
        with mock.patch('outils.sync.labo.highsync_export.uuid.uuid4',return_value=uuid.UUID(int=42)):
            run=exporter(self.root,self.brut,sha(self.brut),self.audio,sha(self.audio),FFMPEG,FFPROBE)
            d=json.loads((run/'manifest.json').read_text())
            self.assertEqual(d['statut'],'canonique_valide',d.get('erreur'))
            before=sha(run/'canonique.mkv')
            with self.assertRaises(FileExistsError):
                exporter(self.root,self.brut,sha(self.brut),self.audio,sha(self.audio),FFMPEG,FFPROBE)
            self.assertEqual(sha(run/'canonique.mkv'),before)


if __name__ == '__main__': unittest.main()
