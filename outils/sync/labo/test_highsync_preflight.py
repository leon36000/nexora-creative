"""Tests CPU réels ; toutes les fixtures restent dans SYNC_TEST_ROOT."""
import hashlib
import json
import os
import shutil
from pathlib import Path
import subprocess
import sys
import unittest
import uuid
from unittest import mock

from outils.sync.labo.highsync_preflight import preflight
from outils.sync.labo.highsync_prepare import preparer, preparer_audio_source

FFMPEG = Path(os.environ.get('SYNC_TEST_FFMPEG') or os.environ.get('SYNC_FFMPEG') or shutil.which('ffmpeg'))
FFPROBE = Path(os.environ.get('SYNC_TEST_FFPROBE') or os.environ.get('SYNC_FFPROBE') or shutil.which('ffprobe'))
ROOT = Path(os.environ.get('SYNC_TEST_ROOT') or os.environ['TMPDIR'])


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


class HighSyncPreflightTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.run_dir = ROOT / ('highsync-preflight-' + uuid.uuid4().hex)
        cls.run_dir.mkdir(parents=True, exist_ok=False)
        cls.audio = cls.run_dir / 'ton.wav'
        cls.video = cls.run_dir / 'cfr25.mkv'
        cls.courte = cls.run_dir / 'courte.mkv'
        cls.fps24 = cls.run_dir / 'cfr24.mkv'
        def creer(*args):
            subprocess.run([str(FFMPEG), '-v', 'error', '-nostdin', '-n', *args], check=True, timeout=30)
        creer('-f', 'lavfi', '-i', 'sine=frequency=440:sample_rate=16000:duration=1', str(cls.audio))
        for dest, rate, duration in ((cls.video, 25, 1.2), (cls.courte, 25, 0.6), (cls.fps24, 24, 1.2)):
            creer('-f', 'lavfi', '-i', f'color=black:s=32x32:r={rate}:d={duration}',
                  '-c:v', 'ffv1', str(dest))

    def verifier(self, video):
        return preflight(video, self.audio, sha(video), sha(self.audio), FFMPEG, FFPROBE)

    def test_entrees_valides(self):
        res = self.verifier(self.video)
        self.assertEqual(res['statut'], 'preflight_cpu_valide')
        self.assertEqual(res['audio_pcm']['echantillons'], 16000)
        self.assertEqual(res['video']['images_decodees'], 30)

    def test_prepare_reel_conserve_et_lie_les_octets(self):
        source = Path(__file__).parent / "highsync_fixture" / "inference.py.txt"
        run = preparer(self.run_dir, self.video, self.audio, sha(self.video), sha(self.audio), FFMPEG, FFPROBE, source)
        rapport = json.loads((run / "manifest.json").read_text())
        self.assertEqual(rapport["statut"], "prepare_sans_inference")
        self.assertEqual(rapport["detector_backend"], "s3fd")
        self.assertEqual(rapport["image_processor_sha256"], sha(run / "highsync_image_processor.py"))
        self.assertEqual(rapport["s3fd_adapter_sha256"], sha(run / "highsync_s3fd.py"))
        self.assertEqual(sha(run / "video-entree.mp4"), sha(self.video))
        self.assertEqual(sha(run / "audio-entree.wav"), sha(self.audio))
        self.assertEqual(rapport["runner_sha256"], sha(run / "inference_adaptee.py"))
        self.assertTrue(self.video.exists())
        self.assertTrue(self.audio.exists())

    def test_cli_prepare_sans_inference(self):
        source = Path(__file__).parent / "highsync_fixture" / "inference.py.txt"
        cp = subprocess.run([sys.executable, "-m", "outils.sync.labo.highsync_prepare",
            "--run-root", str(self.run_dir), "--video", str(self.video), "--video-sha256", sha(self.video),
            "--audio-pcm", str(self.audio), "--audio-sha256", sha(self.audio),
            "--ffmpeg", str(FFMPEG), "--ffprobe", str(FFPROBE), "--source-auteur", str(source)],
            check=True, text=True, capture_output=True, timeout=30)
        result = json.loads(cp.stdout)
        self.assertEqual(result["statut"], "prepare_sans_inference")
        self.assertTrue((Path(result["run"]) / "manifest.json").is_file())

    def test_lien_symbolique_refuse_sans_creation(self):
        lien = self.run_dir / "lien-video.mp4"
        lien.symlink_to(self.video)
        source = Path(__file__).parent / "highsync_fixture" / "inference.py.txt"
        avant = set(self.run_dir.iterdir())
        with self.assertRaisesRegex(ValueError, "régulier"):
            preparer(self.run_dir, lien, self.audio, sha(self.video), sha(self.audio), FFMPEG, FFPROBE, source)
        self.assertEqual(set(self.run_dir.iterdir()), avant)
        self.assertTrue(lien.is_symlink())
        self.assertTrue(self.video.is_file())

    def test_conversion_audio_origine_tracee(self):
        origine = self.run_dir / 'origine-synthetique.mp3'
        subprocess.run([str(FFMPEG), '-v', 'error', '-nostdin', '-n', '-i', str(self.audio), str(origine)], check=True, timeout=30)
        source = Path(__file__).parent / "highsync_fixture" / "inference.py.txt"
        run = preparer_audio_source(self.run_dir, self.video, origine, sha(self.video), sha(origine), FFMPEG, FFPROBE, source)
        preuve = json.loads((run / 'provenance-audio.json').read_text())
        self.assertEqual(preuve['audio_original_sha256'], sha(origine))
        self.assertEqual(preuve['audio_pcm_sha256'], sha(run / 'audio-16k-mono.wav'))
        self.assertEqual(sha(run / 'audio-original.mp3'), sha(origine))
        self.assertEqual(preuve['ffmpeg_sha256'], sha(FFMPEG))
        self.assertTrue((run / preuve['essai'] / 'manifest.json').is_file())
        self.assertTrue(origine.is_file())

    def test_video_trop_courte(self):
        with self.assertRaisesRegex(ValueError, 'plus courte'):
            self.verifier(self.courte)

    def test_cadence_differente(self):
        with self.assertRaisesRegex(ValueError, 'CFR 25'):
            self.verifier(self.fps24)

    def test_derniere_image_allongee_refusee_meme_si_la_cadence_moyenne_est_25(self):
        # Mesure contradictoire injectée, pas une fixture FFmpeg réelle.
        reel = self.verifier(self.video)['video']
        mesure = {**reel, 'duree_derniere_image_secondes': .5}
        with mock.patch('outils.sync.labo.highsync_preflight.av.mesure_video', return_value=mesure):
            with self.assertRaisesRegex(ValueError, 'CFR 25'):
                self.verifier(self.video)

    def test_duree_annoncee_suffisante_ne_remplace_pas_les_images_manquantes(self):
        # Contrat numérique : une durée annoncée ne justifie pas une boucle vidéo.
        reel = self.verifier(self.video)['video']
        mesure = {**reel, 'images_decodees': 24, 'duree_secondes': 1.01}
        with mock.patch('outils.sync.labo.highsync_preflight.av.mesure_video', return_value=mesure):
            with self.assertRaisesRegex(ValueError, 'nombre d’images insuffisant'):
                self.verifier(self.video)

    def test_empreinte_invalide_avant_decodage(self):
        with self.assertRaisesRegex(ValueError, 'empreinte'):
            preflight(self.video, self.audio, '0' * 64, sha(self.audio), FFMPEG, FFPROBE)


if __name__ == '__main__':
    unittest.main()
