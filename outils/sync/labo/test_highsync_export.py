"""Tests FFmpeg réels : médias factices conservés dans SYNC_TEST_ROOT."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import struct
import unittest
import uuid
import wave
from unittest import mock

from outils.sync.labo.highsync_export import exporter, planifier_fin_audio

ROOT = Path(os.environ.get('SYNC_TEST_ROOT') or os.environ['TMPDIR'])
FFMPEG = Path(os.environ.get('SYNC_TEST_FFMPEG') or os.environ.get('SYNC_FFMPEG') or shutil.which('ffmpeg'))
FFPROBE = Path(os.environ.get('SYNC_TEST_FFPROBE') or os.environ.get('SYNC_FFPROBE') or shutil.which('ffprobe'))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


class PlanFinAudioTest(unittest.TestCase):
    def test_duree_exacte_conserve_le_nombre_d_images(self):
        for politique in ('exacte', 'couvrir'):
            with self.subTest(politique=politique):
                p = planifier_fin_audio(16000, 16000, politique)
                self.assertEqual(p['images_cibles'], 25)
                self.assertEqual(p['ecart_fin_exact_secondes'], '0')

    def test_couvrir_ne_descend_jamais_a_l_image_precedente(self):
        for samples, images, gap in [(16001, 26, '639/16000'), (16320, 26, '1/50'),
                                     (16640, 26, '0'), (17279, 27, '1/16000'),
                                     (17281, 28, '639/16000')]:
            with self.subTest(samples=samples):
                p = planifier_fin_audio(samples, 16000, 'couvrir')
                self.assertEqual(p['images_cibles'], images)
                self.assertEqual(p['ecart_fin_exact_secondes'], gap)
                self.assertGreaterEqual(p['ecart_fin_secondes'], 0)
                self.assertLess(p['ecart_fin_secondes'], .04)

    def test_mode_exact_refuse_une_fin_entre_deux_images(self):
        with self.assertRaisesRegex(ValueError, 'non entière'):
            planifier_fin_audio(16320, 16000)

    def test_entrees_ambigues_refusees(self):
        for samples, rate, policy in [(0, 16000, 'couvrir'), (-1, 16000, 'exacte'),
                                      (True, 16000, 'couvrir'), (16000.0, 16000, 'couvrir'),
                                      (16000, 16000.0, 'couvrir'), (16000, 44100, 'couvrir'),
                                      (16000, 16000, 'inconnue')]:
            with self.subTest(samples=samples, rate=rate, policy=policy):
                with self.assertRaises(ValueError):
                    planifier_fin_audio(samples, rate, policy)


class ExportTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root = ROOT / ('highsync-export-fixture-'+uuid.uuid4().hex)
        cls.root.mkdir(parents=True)
        cls.audio=cls.root/'source.wav';cls.brut=cls.root/'brut27.mp4';cls.court=cls.root/'brut23.mp4'
        cls.audio_fraction=cls.root/'source-16320-echantillons.wav'
        cls.audio_image=cls.root/'source-640-echantillons.wav'
        cls.brut25=cls.root/'brut25.mp4'
        with wave.open(str(cls.audio_fraction), 'wb') as wav:
            wav.setparams((1, 2, 16000, 0, 'NONE', 'not compressed'))
            wav.writeframes(b''.join(struct.pack('<h', i % 2000 - 1000) for i in range(16320)))
        with wave.open(str(cls.audio_image), 'wb') as wav:
            wav.setparams((1, 2, 16000, 0, 'NONE', 'not compressed'))
            wav.writeframes(b''.join(struct.pack('<h', i % 2000 - 1000) for i in range(640)))
        def ff(*args):
            subprocess.run([str(FFMPEG),'-v','error','-nostdin','-n',*args],check=True,timeout=30)
        ff('-f','lavfi','-i','sine=frequency=440:sample_rate=16000:duration=1',str(cls.audio))
        for path, frames in ((cls.brut,27),(cls.court,23),(cls.brut25,25)):
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

    def test_couvrir_fin_audio_conserve_26_images_et_tout_le_pcm(self):
        brut_sha, audio_sha = sha(self.brut), sha(self.audio_fraction)
        run = exporter(self.root, self.brut, brut_sha, self.audio_fraction, audio_sha,
                       FFMPEG, FFPROBE, True, fin_audio='couvrir')
        d = json.loads((run/'manifest.json').read_text())
        self.assertEqual(d['statut'], 'canonique_et_telephone_valides', d.get('erreur'))
        self.assertEqual(d['images_cibles'], 26)
        self.assertEqual(d['echantillons_pcm'], 16320)
        self.assertEqual(d['fin_audio']['images_exactes'], '51/2')
        self.assertEqual(d['fin_audio']['ecart_fin_exact_secondes'], '1/50')
        self.assertAlmostEqual(d['validation_av']['ecarts_secondes']['video_moins_reference'], .02)
        self.assertEqual(d['validation_av']['audio_rendu']['echantillons'], 16320)
        with wave.open(str(self.audio_fraction), 'rb') as wav:
            self.assertEqual(d['pcm_decode_sha256'], hashlib.sha256(wav.readframes(16320)).hexdigest())
        self.assertEqual((sha(self.brut), sha(self.audio_fraction)), (brut_sha, audio_sha))

    def test_fin_audio_non_integrale_refusee_par_defaut_avant_creation(self):
        avant = set(self.root.iterdir())
        with self.assertRaisesRegex(ValueError, 'non entière'):
            exporter(self.root, self.brut, sha(self.brut), self.audio_fraction, sha(self.audio_fraction), FFMPEG, FFPROBE)
        self.assertEqual(set(self.root.iterdir()), avant)

    def test_export_une_image_a_la_bonne_cadence(self):
        run = exporter(self.root, self.brut, sha(self.brut), self.audio_image, sha(self.audio_image), FFMPEG, FFPROBE)
        d = json.loads((run/'manifest.json').read_text())
        self.assertEqual(d['statut'], 'canonique_valide', d.get('erreur'))
        self.assertEqual(d['images_cibles'], 1)
        self.assertEqual(d['validation_av']['audio_rendu']['echantillons'], 640)
        self.assertTrue(d['validation_av']['cadence_cible_valide'])

    def test_couvrir_ne_boucle_pas_une_source_de_25_images(self):
        avant = set(self.root.iterdir())
        with self.assertRaisesRegex(ValueError, 'trop courte'):
            exporter(self.root, self.brut25, sha(self.brut25), self.audio_fraction, sha(self.audio_fraction),
                     FFMPEG, FFPROBE, fin_audio='couvrir')
        self.assertEqual(set(self.root.iterdir()), avant)

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
