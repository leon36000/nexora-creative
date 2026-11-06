"""Adaptateur OPSYS CPU : transport factice, FFmpeg réel, aucune API."""
import io
import importlib.machinery
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
import wave

FFMPEG = os.environ.get('OPSYS_TEST_FFMPEG') or os.environ.get('V7_FFMPEG') or '/usr/bin/ffmpeg'
CHAINE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(CHAINE))
import tourner
import voix


class VoixElevenOpsys(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp(prefix='opsys-eleven-factice-', dir=os.environ['TMPDIR']))
        self.palette = self.root / 'palette.json'
        self.palette.write_text(json.dumps({'voix': {'narrateur': {'moteur': 'eleven:liam', 'vitesse': 1.0, 'direction': 'excited'}}}))
        self.dossier = {'voix': [{'id': 'l01', 'voix': 'narrateur', 'texte': 'Bonjour', 'langue': 'fr', 'prises': 1}]}
        self.inputs = []
        buf = io.BytesIO()
        with wave.open(buf, 'wb') as wav:
            wav.setnchannels(1); wav.setsampwidth(2); wav.setframerate(16000); wav.writeframes(b'\0\0' * 1600)
        self.wav_bytes = buf.getvalue()

    def fake(self, payload):
        self.inputs.append(payload)
        return self.wav_bytes

    def test_palette_producteur_et_lecteur_en_bout_a_bout(self):
        ancien = self.root / 'equipe/voix/l01-p1.wav'
        ancien.parent.mkdir(parents=True)
        ancien.write_bytes(b'ancienne prise synthetique')
        reel_ligne = voix.ligne
        def ligne_factice(*args, **kwargs):
            return reel_ligne(*args, **kwargs, transport=self.fake, factice=True)
        with patch.object(tourner, 'TRAVAIL', self.root), patch.object(tourner, 'FF', FFMPEG), \
             patch.object(tourner, 'dossier', return_value=self.dossier), \
             patch.object(tourner, 'choix', return_value={'voix': {'l01': 1}}), \
             patch.object(voix, 'ligne', side_effect=ligne_factice), patch.object(voix, 'demander', side_effect=AssertionError('aucun réseau')):
            tourner.voix('equipe', palette=self.palette)
            tourner.voix('equipe', palette=self.palette)  # reprise du reçu, aucun nouveau POST
            self.assertEqual(len(self.inputs), 1)
            self.assertEqual(self.inputs[0], {'model': 'elevenlabs/eleven-v4', 'voice': 'liam', 'input': '[excited] Bonjour', 'response_format': 'mp3'})
            with self.assertRaisesRegex(ValueError, 'absente ou ambiguë'):
                tourner.prise_voix('equipe', 'l01', palette=self.palette)  # factice jamais accepté en production
            selected = tourner.prise_voix('equipe', 'l01', palette=self.palette, autoriser_factice=True)
        self.assertEqual(ancien.read_bytes(), b'ancienne prise synthetique')
        with wave.open(str(selected), 'rb') as wav:
            self.assertEqual(wav.getframerate(), 48000)
            self.assertEqual(wav.getnchannels(), 2)
        recu = json.loads(selected.with_suffix('.json').read_text())
        self.assertEqual(recu['origine'], 'factice')
        self.assertEqual(recu['modele_demande'], 'elevenlabs/eleven-v4')
        self.assertEqual(recu['statut_humain'], 'non_juge')
        self.assertIsNone(recu['emr']); self.assertIsNone(recu['utile_s']); self.assertIsNone(recu['oreille'])

    def test_client_v7_resout_et_transmet_payload_sans_reseau(self):
        class Loader:
            def create_module(self, spec): return None
            def exec_module(self, module):
                module.api_configuration = lambda path, model: ('https://example.invalid/' + path, 'factice')
        class Reponse:
            def __enter__(self): return self
            def __exit__(self, *args): return False
            def read(self): return b'fake audio'
        payload = {'model': 'elevenlabs/eleven-v4', 'voice': 'liam', 'input': '[excited] Hello', 'response_format': 'mp3'}
        module_spec = importlib.machinery.ModuleSpec('client_fixture', Loader())
        with patch.object(voix.importlib.util, 'spec_from_file_location', return_value=module_spec), \
             patch.object(voix.urllib.request, 'urlopen', return_value=Reponse()) as urlopen:
            self.assertEqual(voix.demander(payload), b'fake audio')
        request = urlopen.call_args.args[0]
        self.assertEqual(json.loads(request.data), payload)
        self.assertEqual(request.full_url, 'https://example.invalid/audio/speech')

    def test_anglais_valide_et_signature_distincte(self):
        opts = {'racine': self.root, 'ffmpeg': FFMPEG, 'transport': self.fake, 'factice': True}
        fr = voix.ligne('equipe', 'l01', 'eleven:liam', 'Bonjour', 'excited', 1, 1, langue='fr', **opts)
        en = voix.ligne('equipe', 'l01', 'eleven:liam', 'Hello', '', 1, 1, langue='en', **opts)
        self.assertNotEqual(fr['signature'], en['signature'])
        self.assertEqual(en['langue'], 'en')
        self.assertEqual(self.inputs[-1]['input'], 'Hello')
        self.assertEqual(en['origine'], 'factice')
        spec = voix.contrat('equipe', 'l01', 'eleven:liam', 'Hello', '', 1, 1, 'en')
        self.assertNotEqual(voix.signature(spec, True), voix.signature(spec, False))
        with patch.object(tourner, 'TRAVAIL', self.root), patch.object(tourner, 'dossier', return_value=self.dossier), \
             patch.object(tourner, 'choix', return_value={'voix': {'l01': 1}}):
            self.assertEqual(str(tourner.prise_voix('equipe', 'l01', palette=self.palette, autoriser_factice=True)), fr['fichier'])

    def test_vitesse_langue_et_ancien_modele_refuses_avant_transport(self):
        kwargs = {'langue': 'fr', 'racine': self.root, 'ffmpeg': FFMPEG, 'transport': self.fake, 'factice': True}
        with self.assertRaisesRegex(ValueError, 'vitesse'):
            voix.ligne('equipe', 'l01', 'eleven:liam', 'Salut', '', 1.2, 1, **kwargs)
        with self.assertRaisesRegex(ValueError, 'Langue'):
            voix.ligne('equipe', 'l01', 'eleven:liam', 'Salut', '', 1, 1, **{**kwargs, 'langue': None})
        with self.assertRaisesRegex(ValueError, 'eleven:'):
            voix.ligne('equipe', 'l01', 'voxtral', 'Salut', '', 1, 1, **kwargs)
        self.assertEqual(self.inputs, [])
        self.assertFalse((self.root / 'equipe').exists())

    def test_intention_sans_recu_refuse_sans_second_envoi(self):
        def panne(payload):
            self.inputs.append(payload)
            raise RuntimeError('perte synthétique')
        kwargs = {'langue': 'en', 'racine': self.root, 'ffmpeg': FFMPEG, 'transport': panne, 'factice': True}
        with self.assertRaisesRegex(RuntimeError, 'perte'):
            voix.ligne('equipe', 'l01', 'eleven:liam', 'Hello', '', 1, 1, **kwargs)
        with self.assertRaises(FileExistsError):
            voix.ligne('equipe', 'l01', 'eleven:liam', 'Hello', '', 1, 1, **kwargs)
        self.assertEqual(len(self.inputs), 1)
        self.assertEqual(len(list(self.root.rglob('intention.json'))), 1)

    def test_recu_factice_modifie_refuse_et_ancien_non_reutilise(self):
        kwargs = {'langue': 'en', 'racine': self.root, 'ffmpeg': FFMPEG, 'transport': self.fake, 'factice': True}
        recu = voix.ligne('equipe', 'l01', 'eleven:charlie', 'Hello', '', 1, 1, **kwargs)
        wav = Path(recu['fichier'])
        wav.write_bytes(b'altere')
        with patch.object(tourner, 'TRAVAIL', self.root), patch.object(tourner, 'dossier', return_value={'voix': [{'id': 'l01', 'langue': 'en', 'voix': 'narrateur', 'texte': 'Hello'}]}), \
             patch.object(tourner, 'choix', return_value={'voix': {'l01': 1}}):
            with self.assertRaisesRegex(ValueError, 'absente ou ambiguë'):
                tourner.prise_voix('equipe', 'l01', palette=self.palette, autoriser_factice=True)
        self.assertEqual(wav.read_bytes(), b'altere')

    def test_source_modifiee_et_choix_ambigu_refuses(self):
        opts = {'langue': 'fr', 'racine': self.root, 'ffmpeg': FFMPEG, 'transport': self.fake, 'factice': True}
        premier = voix.ligne('equipe', 'l01', 'eleven:liam', 'Bonjour', 'excited', 1, 1, **opts)
        second = voix.ligne('equipe', 'l01', 'eleven:charlie', 'Bonjour', '', 1, 1, **opts)
        with patch.object(tourner, 'TRAVAIL', self.root), patch.object(tourner, 'dossier', return_value=self.dossier), \
             patch.object(tourner, 'choix', return_value={'voix': {'l01': 1}}):
            self.assertEqual(str(tourner.prise_voix('equipe', 'l01', palette=self.palette, autoriser_factice=True)), premier['fichier'])
            Path(premier['fichier']).with_suffix('.mp3').write_bytes(b'altere')
            with self.assertRaisesRegex(ValueError, 'absente ou ambiguë'):
                tourner.prise_voix('equipe', 'l01', palette=self.palette, autoriser_factice=True)
            self.assertTrue(Path(second['fichier']).exists())

    def test_texte_ou_voix_modifies_refusent_ancienne_prise(self):
        opts = {'langue': 'fr', 'racine': self.root, 'ffmpeg': FFMPEG, 'transport': self.fake, 'factice': True}
        ancien = voix.ligne('equipe', 'l01', 'eleven:liam', 'Bonjour', 'excited', 1, 1, **opts)
        with patch.object(tourner, 'TRAVAIL', self.root), patch.object(tourner, 'choix', return_value={'voix': {'l01': 1}}):
            modifie = {'voix': [{**self.dossier['voix'][0], 'texte': 'Salut'}]}
            with patch.object(tourner, 'dossier', return_value=modifie):
                with self.assertRaisesRegex(ValueError, 'absente ou ambiguë'):
                    tourner.prise_voix('equipe', 'l01', palette=self.palette, autoriser_factice=True)
            self.palette.write_text(json.dumps({'voix': {'narrateur': {'moteur': 'eleven:charlie', 'vitesse': 1, 'direction': 'excited'}}}))
            with patch.object(tourner, 'dossier', return_value=self.dossier):
                with self.assertRaisesRegex(ValueError, 'absente ou ambiguë'):
                    tourner.prise_voix('equipe', 'l01', palette=self.palette, autoriser_factice=True)
        self.assertTrue(Path(ancien['fichier']).is_file())
        self.assertEqual(len(self.inputs), 1)

    def test_partiels_et_liens_casses_refuses_avant_transport(self):
        spec = voix.contrat('equipe', 'l01', 'eleven:liam', 'Bonjour', '', 1, 1, 'fr')
        dossier = self.root / 'equipe' / 'voix' / 'eleven4' / 'liam' / voix.signature(spec, True)
        dossier.mkdir(parents=True)
        for nom in ('l01-p1.mp3', 'l01-p1.wav', 'l01-p1.json'):
            for lien in (False, True):
                with self.subTest(nom=nom, lien=lien):
                    sentinelle = dossier / nom
                    if lien:
                        sentinelle.symlink_to(self.root / 'cible-absente')
                    else:
                        sentinelle.write_bytes(b'fixture')
                    with self.assertRaises((FileExistsError, ValueError, json.JSONDecodeError)):
                        voix.ligne('equipe', 'l01', 'eleven:liam', 'Bonjour', '', 1, 1, langue='fr',
                                   racine=self.root, ffmpeg=FFMPEG, transport=self.fake, factice=True)
                    self.assertEqual(self.inputs, [])
                    self.assertTrue(sentinelle.exists() or sentinelle.is_symlink())
                    sentinelle.unlink()  # seulement la sentinelle synthétique de ce cas
        self.assertFalse((dossier / 'intention.json').exists())


if __name__ == '__main__':
    unittest.main()
