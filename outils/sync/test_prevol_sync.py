"""Tests CPU : vrais médias courts et vraies sondes FFmpeg, sans modèle."""
import contextlib
import io
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest import mock

import prevol_sync


class PrevolTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.racine = Path(tempfile.mkdtemp(prefix='sync-test-', dir=os.environ.get('TMPDIR')))
        cls.ffmpeg = os.environ.get('SYNC_FFMPEG', 'ffmpeg')
        cls.ffprobe = os.environ.get('SYNC_FFPROBE', '/usr/bin/ffprobe')
        cls.video = cls.racine / 'source.mp4'
        cls.court = cls.racine / 'court.wav'
        cls.long = cls.racine / 'long.wav'
        for sortie, source, arguments in [
            (cls.video, 'color=blue:s=64x64:r=10:d=1', ['-c:v', 'mpeg4']),
            (cls.court, 'sine=frequency=400:duration=0.5', ['-c:a', 'pcm_s16le']),
            (cls.long, 'sine=frequency=500:duration=2', ['-c:a', 'pcm_s16le']),
        ]:
            subprocess.run([cls.ffmpeg, '-nostdin', '-v', 'error', '-f', 'lavfi', '-i', source,
                            *arguments, '-n', str(sortie)], check=True, timeout=30)

    def appel(self, namespace, video=None, audio=None, genre='continu', langue='fr', extra=()):
        args = ['--namespace', str(namespace), '--pair', langue, genre,
                str(video or self.video), str(audio or self.court), '--fps', '25',
                '--padding-seconds', '0.16', '--ffprobe', self.ffprobe, *extra]
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            return prevol_sync.main(args)

    def test_manifest_et_refus_rejeu(self):
        cible = self.racine / 'accepte'
        self.assertEqual(self.appel(cible), 0)
        manifeste = json.loads((cible / 'manifest.json').read_text())
        self.assertEqual(manifeste['couples'][0]['expected_language'], 'fr')
        self.assertFalse(manifeste['generation_effectuee'])
        self.assertFalse(manifeste['couples'][0]['boucle_necessaire_selon_durees'])
        self.assertEqual(self.appel(cible), 2)

    def test_court_refuse_et_avatar_explicite(self):
        cible = self.racine / 'continu-refuse'
        self.assertEqual(self.appel(cible, audio=self.long), 2)
        self.assertFalse(cible.exists())
        cible = self.racine / 'avatar'
        self.assertEqual(self.appel(cible, audio=self.long, genre='avatar-bouclable', langue='en'), 0)
        self.assertTrue(json.loads((cible / 'manifest.json').read_text())['couples'][0]['boucle_necessaire_selon_durees'])

    def test_entree_absente_et_lien_refuses(self):
        cible = self.racine / 'manquant'
        self.assertEqual(self.appel(cible, video=self.racine / 'absent'), 2)
        lien = self.racine / 'lien.mp4'
        lien.symlink_to(self.video)
        self.assertEqual(self.appel(cible, video=lien), 2)
        self.assertFalse(cible.exists())

    def test_type_et_langue_invalides(self):
        self.assertEqual(self.appel(self.racine / 'type', genre='autre'), 2)
        self.assertEqual(self.appel(self.racine / 'langue', langue='xx'), 2)

    def test_flux_invalide_et_namespace_reserve(self):
        cible = self.racine / 'namespace-reserve'
        cible.mkdir()
        (cible / 'cache').mkdir()
        self.assertEqual(self.appel(cible), 2)
        self.assertTrue((cible / 'cache').is_dir())
        self.assertEqual(self.appel(self.racine / 'mauvais-flux', audio=self.video), 2)
        self.assertEqual(self.appel(self.racine / 'malforme' / '..' / 'plan'), 2)

    def test_timeout_confirme_et_refuse(self):
        for permission in (False, True):
            enfant = mock.Mock()
            enfant.communicate.side_effect = [subprocess.TimeoutExpired('ffprobe', 30), (b'', b'')]
            if permission:
                enfant.kill.side_effect = PermissionError('signal refusé')
            with self.subTest(permission=permission), mock.patch.object(prevol_sync.subprocess, 'Popen', return_value=enfant):
                with self.assertRaisesRegex(ValueError, 'non confirmé' if permission else 'confirmé'):
                    prevol_sync.examiner(Path(self.ffprobe), self.video, 'video')
                enfant.kill.assert_called_once()

    def test_deux_couples_et_valeurs_invalides(self):
        cible = self.racine / 'deux'
        self.assertEqual(self.appel(cible, extra=['--pair', 'en', 'continu', str(self.video), str(self.court)]), 0)
        self.assertEqual(len(json.loads((cible / 'manifest.json').read_text())['couples']), 2)
        with self.assertRaises(SystemExit):
            self.appel(self.racine / 'fps-invalide', extra=['--fps', '0'])


if __name__ == '__main__':
    unittest.main()
