"""Vérifie le choix de fournisseur sans API ni génération audio."""
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import urllib.error
import unittest
from unittest.mock import patch

SOURCE = Path(__file__).resolve().parents[2] / 'voix/banc_voix_v7.py'
SPEC = importlib.util.spec_from_file_location('banc_v7_politique_test', SOURCE)
banc = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(banc)


class PolitiqueVoixV7(unittest.TestCase):
    def test_candidat_voxtral_refuse_avant_reseau(self):
        with patch.object(banc, 'post') as post:
            with self.assertRaisesRegex(ValueError, 'ElevenLabs v4'):
                banc.generer('vox3-marie-excitee', 'narration')
            post.assert_not_called()

    def test_eleven4_explicite_et_prise_existante_preservee(self):
        dossier = Path(tempfile.mkdtemp(prefix='voix-v7-', dir=__import__('os').environ['TMPDIR']))
        cible = dossier / 'eleven4-liam-narration.mp3'
        with patch.object(banc, 'D', dossier), patch.object(banc, 'post', return_value=b'synthetic') as post:
            self.assertEqual(banc.generer('eleven4-liam', 'narration'), cible)
            self.assertEqual(post.call_args.args[1]['model'], 'elevenlabs/eleven-v4')
            self.assertEqual(post.call_args.args[1]['voice'], 'liam')
            self.assertEqual(post.call_args.args[1]['input'], f"[{banc.JEU['narration']}] {banc.TEXTES['narration']}")
            self.assertNotIn('speed', post.call_args.args[1])
            with self.assertRaises(FileExistsError):
                banc.generer('eleven4-liam', 'narration')
            self.assertEqual(post.call_count, 1)
            self.assertEqual(cible.read_bytes(), b'synthetic')

    def test_jugement_anglais_utilise_grille_et_cles_anglaises(self):
        dossier = Path(tempfile.mkdtemp(prefix='jugement-en-', dir=__import__('os').environ['TMPDIR']))
        clip = dossier / 'synthetic.mp3'
        clip.write_bytes(b'fake')
        scores = {'langue_anglaise': 9, 'accent_naturel': 8, 'energie': 7, 'caractere': 6, 'naturel': 8, 'cheap': 1, 'genre': 'homme', 'commentaire': 'ok'}
        body = json.dumps({'choices': [{'message': {'content': json.dumps(scores)}}]}).encode()
        with patch.object(banc, 'post', return_value=body) as post:
            moyennes, _, _ = banc.juger(clip, 'narration', passes=1, langue='en')
        self.assertEqual(moyennes['langue_anglaise'], 9)
        self.assertNotIn('langue_francaise', moyennes)
        prompt = post.call_args.args[1]['messages'][0]['content'][1]['text']
        self.assertIn('natural English', prompt)
        self.assertNotIn('accent québécois', prompt)

    def test_erreur_http_ne_lit_ni_n_affiche_le_corps(self):
        class CorpsInterdit:
            def read(self, *args):
                raise AssertionError('corps HTTP non demandé')
            def close(self):
                pass
        erreur = urllib.error.HTTPError('https://example.invalid/audio', 400, 'bad', {}, CorpsInterdit())
        with patch.object(banc, 'api_configuration', return_value=('https://example.invalid/audio', 'synthetic')), \
             patch.object(banc.urllib.request, 'urlopen', side_effect=erreur):
            with self.assertRaisesRegex(RuntimeError, '^HTTP 400$'):
                banc.post('audio/speech', {'model': 'elevenlabs/eleven-v4'})

    def test_cli_sans_candidat_refuse_avant_generation(self):
        result = subprocess.run([sys.executable, str(SOURCE)], capture_output=True, text=True, timeout=10)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('Choisir explicitement', result.stderr)


if __name__ == '__main__':
    unittest.main()
