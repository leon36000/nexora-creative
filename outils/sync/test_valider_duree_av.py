"""Tests CPU réels ; les médias synthétiques sont conservés dans SYNC_TEST_ROOT."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

import valider_duree_av as validateur

FFMPEG = os.environ.get('SYNC_TEST_FFMPEG', os.environ.get('SYNC_FFMPEG', 'ffmpeg'))
FFPROBE = os.environ.get('SYNC_TEST_FFPROBE', os.environ.get('SYNC_FFPROBE', 'ffprobe'))
RACINE = Path(os.environ.get('SYNC_TEST_ROOT') or os.environ['TMPDIR'])
CLI = Path(__file__).with_name('valider_duree_av.py')


def commande(*args):
    subprocess.run([FFMPEG, '-v', 'error', '-nostdin', '-n', *args], check=True, timeout=30)


class DureeAV(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        RACINE.mkdir(parents=True, exist_ok=True)
        cls.dossier = Path(tempfile.mkdtemp(prefix='av-fixtures-', dir=RACINE))
        cls.wav = cls.dossier / 'source.wav'
        cls.mp3 = cls.dossier / 'source.mp3'
        cls.correct = cls.dossier / 'correct.mp4'
        cls.court = cls.dossier / 'video-tronquee.mp4'
        cls.court63 = cls.dossier / 'video-63-images.mp4'
        cls.decale = cls.dossier / 'audio-decale.mp4'
        cls.sans_audio = cls.dossier / 'sans-audio.mp4'
        cls.vfr = cls.dossier / 'cadence-variable.mp4'
        cls.invalide = cls.dossier / 'invalide.bin'
        commande('-f', 'lavfi', '-i', 'sine=frequency=440:sample_rate=48000:duration=2.7', str(cls.wav))
        commande('-i', str(cls.wav), '-c:a', 'libmp3lame', '-q:a', '4', str(cls.mp3))
        source = ['-f', 'lavfi', '-i', 'color=c=blue:s=64x64:r=24:d=2.708333333', '-i', str(cls.wav)]
        commande(*source, '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-c:a', 'aac', str(cls.correct))
        commande(*source, '-vf', 'trim=end_frame=27,setpts=PTS-STARTPTS', '-r', '24', '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-c:a', 'aac', str(cls.court))
        commande(*source, '-vf', 'trim=end_frame=63,setpts=PTS-STARTPTS', '-r', '24', '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-c:a', 'aac', str(cls.court63))
        commande('-f', 'lavfi', '-i', 'color=c=blue:s=64x64:r=24:d=2.708333333', '-itsoffset', '0.5', '-i', str(cls.wav), '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-c:a', 'aac', str(cls.decale))
        commande('-f', 'lavfi', '-i', 'color=c=blue:s=64x64:r=24:d=1', '-an', '-c:v', 'libx264', str(cls.sans_audio))
        commande(*source, '-vf', "select='lt(n,44)',setpts='if(lt(N,24),N/(24*TB),(1+(N-24)/11.4)/TB)'", '-fps_mode', 'vfr', '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-c:a', 'aac', str(cls.vfr))
        cls.invalide.write_bytes(b'pas un media')
        print('Médias synthétiques conservés :', cls.dossier, flush=True)

    def verifier(self, reference, rendu, cadence=None):
        p = subprocess.run([sys.executable, str(CLI), '--reference-audio', str(reference), '--rendu', str(rendu),
                            '--ffmpeg', FFMPEG, '--ffprobe', FFPROBE, '--padding-codec-secondes', '0.08'] + (['--cadence-cible', cadence] if cadence else []),
                           check=False, capture_output=True, text=True, timeout=30)
        return p.returncode, json.loads(p.stdout)

    def test_rendu_correct(self):
        code, resultat = self.verifier(self.wav, self.correct)
        self.assertEqual(code, 0, resultat)
        self.assertTrue(resultat['valide'])
        self.assertEqual(resultat['audio_reference']['echantillons'], 129600)
        self.assertEqual(resultat['video']['images_decodees'], 65)

    def test_video_tronquee_audio_complet(self):
        code, resultat = self.verifier(self.wav, self.court)
        self.assertEqual(code, 1, resultat)
        self.assertEqual(resultat['video']['images_decodees'], 27)
        self.assertAlmostEqual(resultat['audio_reference']['duree_secondes'], 2.7, places=3)
        self.assertAlmostEqual(resultat['video']['duree_secondes'], 1.125, places=3)
        self.assertGreater(resultat['audio_rendu']['duree_secondes'], 2.69)

    def test_63_images_refuse_sans_padding_audio_sur_video(self):
        code, resultat = self.verifier(self.wav, self.court63)
        self.assertEqual(code, 1, resultat)
        self.assertEqual(resultat['video']['images_decodees'], 63)
        self.assertAlmostEqual(resultat['video']['duree_secondes'], 2.625, places=3)
        self.assertGreater(abs(resultat['ecarts_secondes']['video_moins_reference']), resultat['tolerance']['video_secondes'])

    def test_debut_audio_decale_refuse(self):
        code, resultat = self.verifier(self.wav, self.decale)
        self.assertEqual(code, 1, resultat)
        self.assertAlmostEqual(resultat['audio_reference']['duree_secondes'], 2.7, places=3)
        self.assertGreater(resultat['ecarts_secondes']['debut_audio_moins_video'], .4)
        self.assertLessEqual(abs(resultat['ecarts_secondes']['audio_moins_reference']), resultat['tolerance']['audio_secondes'])
        self.assertLessEqual(abs(resultat['ecarts_secondes']['video_moins_reference']), resultat['tolerance']['video_secondes'])
        self.assertAlmostEqual(resultat['video']['duree_secondes'], 2.7, delta=.05)

    def test_cadence_cible_cfr(self):
        code, correct = self.verifier(self.wav, self.correct, '24')
        self.assertEqual(code, 0, correct)
        code, variable = self.verifier(self.wav, self.vfr, '24')
        self.assertEqual(code, 1, variable)
        self.assertFalse(variable['cadence_cible_valide'])

    def test_image_unique_verifie_sa_duree_pour_la_cadence(self):
        audio = self.dossier / 'une-image-audio.wav'
        rendu = self.dossier / 'une-image.mkv'
        commande('-f', 'lavfi', '-i', 'sine=frequency=440:sample_rate=48000:duration=0.04', str(audio))
        commande('-f', 'lavfi', '-i', 'color=c=blue:s=64x64:r=25:d=0.04', '-i', str(audio),
                 '-c:v', 'ffv1', '-c:a', 'pcm_s16le', str(rendu))
        correct = validateur.valider(audio, rendu, FFMPEG, FFPROBE, 0, cadence_cible='25')
        self.assertTrue(correct['valide'], correct)
        self.assertEqual(correct['video']['images_decodees'], 1)
        self.assertAlmostEqual(correct['video']['duree_derniere_image_secondes'], .04)
        mauvais = validateur.valider(audio, rendu, FFMPEG, FFPROBE, 0, cadence_cible='50')
        self.assertFalse(mauvais['cadence_cible_valide'])
        self.assertFalse(mauvais['valide'])

    def test_video_variable_jugee_sur_pts(self):
        code, resultat = self.verifier(self.wav, self.vfr)
        self.assertEqual(code, 0, resultat)
        self.assertEqual(resultat['video']['images_decodees'], 44)
        self.assertAlmostEqual(resultat['video']['duree_secondes'], 2.7, delta=.08)
        self.assertGreater(abs(resultat['video']['duree_secondes'] - 44 / 24), .5)

    def test_mp3_mesure_decodee(self):
        code, resultat = self.verifier(self.mp3, self.correct)
        self.assertEqual(code, 0, resultat)
        self.assertEqual(resultat['audio_reference']['echantillons'], 129600)
        meta = json.loads(subprocess.check_output([FFPROBE, '-v', 'error', '-show_entries', 'format=duration', '-of', 'json', str(self.mp3)]))
        self.assertGreater(abs(float(meta['format']['duration']) - resultat['audio_reference']['duree_secondes']), .001)

    def test_processus_en_erreur_est_signale(self):
        with self.assertRaisesRegex(validateur.ValidationErreur, 'décodage échoué'):
            validateur.executer([sys.executable, '-c', 'raise SystemExit(7)'], 5, True)

    def test_sortie_trop_grande_et_enfant_termine(self):
        creer = validateur.subprocess.Popen
        enfants = []
        def lancer(*args, **kwargs):
            enfant = creer(*args, **kwargs); enfants.append(enfant); return enfant
        with patch.object(validateur.subprocess, 'Popen', side_effect=lancer):
            with self.assertRaisesRegex(validateur.ValidationErreur, 'Métadonnées excessives'):
                validateur.executer([sys.executable, '-c', 'import sys; sys.stdout.write("x" * 1000000); sys.stdout.flush()'], 5, True, 1024)
        self.assertEqual(len(enfants), 1)
        self.assertIsNotNone(enfants[0].poll())

    def test_timeout_termine_uniquement_son_enfant(self):
        creer = validateur.subprocess.Popen
        enfants = []
        def lancer(*args, **kwargs):
            enfant = creer(*args, **kwargs); enfants.append(enfant); return enfant
        with patch.object(validateur.subprocess, 'Popen', side_effect=lancer):
            with self.assertRaisesRegex(validateur.ValidationErreur, 'Délai de décodage dépassé'):
                validateur.executer([sys.executable, '-c', 'import time; time.sleep(10)'], .2, True)
        self.assertEqual(len(enfants), 1)
        self.assertIsNotNone(enfants[0].poll())

    def test_duree_image_ffprobe_5_et_repli_estime(self):
        flux = [{'codec_type': 'video', 'nb_read_frames': '2', 'avg_frame_rate': '24/1'}]
        frames = [{'best_effort_timestamp_time': '0'}, {'best_effort_timestamp_time': '0.05', 'pkt_duration_time': '0.08'}]
        with patch.object(validateur, 'executer', return_value=json.dumps({'frames': frames}).encode()):
            video = validateur.mesure_video('ffprobe', 'fixture', flux, 1)
        self.assertAlmostEqual(video['duree_secondes'], .13)
        self.assertEqual(video['provenance_duree_derniere_image'], 'pkt_duration_time')
        frames[-1].pop('pkt_duration_time')
        with patch.object(validateur, 'executer', return_value=json.dumps({'frames': frames}).encode()):
            video = validateur.mesure_video('ffprobe', 'fixture', flux, 1)
        self.assertEqual(video['provenance_duree_derniere_image'], 'estimation_cadence_moyenne')
        self.assertIn('estimation', video['methode_duree'])

    def test_absence_audio_video_et_media_invalide(self):
        for ref, rendu in [(self.wav, self.sans_audio), (self.wav, self.wav), (self.wav, self.invalide)]:
            code, resultat = self.verifier(ref, rendu)
            self.assertEqual(code, 2, resultat)
            self.assertFalse(resultat['valide'])


if __name__ == '__main__':
    unittest.main()
