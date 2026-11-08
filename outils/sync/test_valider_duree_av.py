"""Tests CPU réels ; les médias synthétiques sont conservés dans SYNC_TEST_ROOT."""
import json
import os
from pathlib import Path
import selectors
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


def sonder_sigterm_sur_enfant_propre():
    """Sonde SIGTERM sur un Popen créé ici; si refusé, l’enfant sort par EOF."""
    code = 'import os,sys; os.write(1,b\"R\"); sys.stdin.buffer.read(1)'
    enfant = subprocess.Popen(
        [sys.executable, '-I', '-S', '-c', code], env={},
        stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
        close_fds=True,
    )
    try:
        with selectors.DefaultSelector() as selecteur:
            selecteur.register(enfant.stdout, selectors.EVENT_READ)
            if not selecteur.select(1.0):
                raise AssertionError('enfant de sonde sans signal READY en une seconde')
            if enfant.stdout.read(1) != b'R':
                raise AssertionError('réponse READY invalide de l’enfant de sonde')
        try:
            enfant.terminate()
        except PermissionError as exc:
            return False, f'SIGTERM refusé ({type(exc).__name__}, errno={exc.errno})'
        return True, 'SIGTERM accepté sur l’enfant de sonde'
    finally:
        # En cas de refus, EOF délie l’enfant sans autre signal ni PID étranger.
        if enfant.stdin and not enfant.stdin.closed:
            enfant.stdin.close()
        try:
            enfant.wait(timeout=1.0)
        finally:
            if enfant.stdout:
                enfant.stdout.close()


def commande(*args):
    subprocess.run([FFMPEG, '-v', 'error', '-nostdin', '-n', *args], check=True, timeout=30)


class DureeAV(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sigterm_ok, cls.sigterm_raison = sonder_sigterm_sur_enfant_propre()
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
        if not self.sigterm_ok:
            self.skipTest(self.sigterm_raison)
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
        if not self.sigterm_ok:
            self.skipTest(self.sigterm_raison)
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




class NettoyageSignauxMockes(unittest.TestCase):
    class Sortie:
        def __init__(self): self.closed = False
        def fileno(self): return 123
        def close(self): self.closed = True

    class Selecteur:
        def __init__(self, pret, erreur=None): self.pret = pret; self.erreur = erreur; self.closed = False
        def register(self, *_):
            if self.erreur: raise self.erreur
        def select(self, _): return self.pret
        def close(self): self.closed = True

    class Enfant:
        def __init__(self, refuse=False):
            self.stdout = NettoyageSignauxMockes.Sortie()
            self.rc = None
            self.refuse = refuse
            self.terminations = self.tues = self.attentes = 0
        def poll(self): return self.rc
        def terminate(self):
            self.terminations += 1
            if self.refuse: raise PermissionError(13, 'signal refusé simulé')
            self.rc = -15
        def kill(self):
            self.tues += 1
            if self.refuse: raise PermissionError(13, 'signal refusé simulé')
            self.rc = -9
        def wait(self, timeout=None):
            self.attentes += 1
            return self.rc

    def _patches(self, enfant, pret):
        return (
            patch.object(validateur.subprocess, 'Popen', return_value=enfant),
            patch.object(validateur.selectors, 'DefaultSelector', return_value=self.Selecteur(pret)),
            patch.object(validateur.os, 'read', return_value=b'x' * 1025),
        )

    def test_sortie_excessive_propage_erreur_apres_arret_confirme(self):
        enfant = self.Enfant()
        p = self._patches(enfant, [object()])
        with p[0], p[1], p[2]:
            with self.assertRaisesRegex(validateur.ValidationErreur, 'Métadonnées excessives'):
                validateur.executer(['faux-ffprobe'], 1, True, 1024)
        self.assertEqual((enfant.terminations, enfant.tues, enfant.attentes), (1, 0, 1))
        self.assertEqual(enfant.poll(), -15)
        self.assertTrue(enfant.stdout.closed)

    def test_timeout_propage_erreur_apres_arret_confirme(self):
        enfant = self.Enfant()
        p = self._patches(enfant, [])
        with p[0], p[1]:
            with self.assertRaisesRegex(validateur.ValidationErreur, 'Délai de décodage dépassé'):
                validateur.executer(['faux-ffmpeg'], 1, True, 1024)
        self.assertEqual((enfant.terminations, enfant.tues, enfant.attentes), (1, 0, 1))
        self.assertEqual(enfant.poll(), -15)
        self.assertTrue(enfant.stdout.closed)

    def test_refuse_le_faux_succes_si_terminate_et_kill_sont_refuses(self):
        enfant = self.Enfant(refuse=True)
        p = self._patches(enfant, [])
        with p[0], p[1]:
            with self.assertRaisesRegex(validateur.ValidationErreur, 'Arrêt du décodeur non confirmé'):
                validateur.executer(['faux-ffmpeg'], 1, True, 1024)
        self.assertEqual((enfant.terminations, enfant.tues, enfant.attentes), (1, 1, 0))
        self.assertIsNone(enfant.poll(), 'un processus non confirmé ne doit pas sembler arrêté')
        self.assertTrue(enfant.stdout.closed, 'le pipe doit être fermé même si l’arrêt n’est pas confirmé')

    def test_echec_initialisation_ou_enregistrement_selecteur_nettoie_enfant(self):
        for phase in ('initialisation', 'enregistrement'):
            with self.subTest(phase=phase):
                enfant = self.Enfant()
                if phase == 'initialisation':
                    selecteur = None
                    patch_selecteur = patch.object(
                        validateur.selectors, 'DefaultSelector',
                        side_effect=OSError('mock selector initialization'),
                    )
                else:
                    selecteur = self.Selecteur([], OSError('mock selector register'))
                    patch_selecteur = patch.object(
                        validateur.selectors, 'DefaultSelector', return_value=selecteur,
                    )
                with patch.object(validateur.subprocess, 'Popen', return_value=enfant), patch_selecteur:
                    with self.assertRaisesRegex(OSError, 'mock selector'):
                        validateur.executer(['faux-ffprobe'], 1, True, 1024)
                self.assertEqual((enfant.terminations, enfant.attentes), (1, 1))
                self.assertEqual(enfant.poll(), -15)
                self.assertTrue(enfant.stdout.closed)
                if selecteur is not None:
                    self.assertTrue(selecteur.closed)


if __name__ == '__main__':
    unittest.main()
