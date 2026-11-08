"""Tests de l'adaptation de sources; aucun import Torch ni modèle exécuté."""
import ast
import copy
import hashlib
import json
import os
from pathlib import Path
import subprocess
from types import SimpleNamespace
import unittest
from unittest import mock

from outils.sync.labo.latentsync_patch import adapter, SOURCE_COMMIT, SOURCES

FIXTURES = Path(__file__).parent / 'latentsync_fixture'


def adaptee(nom):
    return adapter(nom, (FIXTURES / (nom + '.txt')).read_bytes()).decode()


def extraire(nom, fonction):
    arbre = ast.parse(adaptee(nom))
    return copy.deepcopy(next(n for n in ast.walk(arbre) if isinstance(n, ast.FunctionDef) and n.name == fonction))


def charger_fonction(noeud, contexte):
    noeud.decorator_list = []
    for n in ast.walk(noeud):
        if isinstance(n, ast.arg):
            n.annotation = None
        if isinstance(n, ast.FunctionDef):
            n.returns = None
    module = ast.fix_missing_locations(ast.Module(body=[noeud], type_ignores=[]))
    exec(compile(module, '<fonction-adaptee-sans-modele>', 'exec'), contexte)
    return contexte[noeud.name]


class AdaptationLatentSyncTest(unittest.TestCase):
    def test_six_sources_epinglees_et_syntaxe_adaptee(self):
        provenance = json.loads((FIXTURES / 'provenance.json').read_text())
        self.assertEqual(provenance['commit'], SOURCE_COMMIT)
        self.assertEqual({f['path']: f['sha256'] for f in provenance['files']}, SOURCES)
        for nom, sha in SOURCES.items():
            with self.subTest(nom=nom):
                source = (FIXTURES / (nom + '.txt')).read_bytes()
                self.assertEqual(hashlib.sha256(source).hexdigest(), sha)
                sortie = adapter(nom, source)
                compile(sortie, nom, 'exec')  # Compilation seulement : aucun import exécuté.
                self.assertNotEqual(sortie, source)
                self.assertEqual(source, (FIXTURES / (nom + '.txt')).read_bytes())

    def test_toute_source_modifiee_ou_inconnue_est_refusee(self):
        for nom in SOURCES:
            with self.subTest(nom=nom):
                with self.assertRaises(ValueError):
                    adapter(nom, (FIXTURES / (nom + '.txt')).read_bytes() + b'\n')
        with self.assertRaises(ValueError):
            adapter('../inference.py', b'')

    def test_ni_suppression_ni_shell_ni_ecrasement_ffmpeg(self):
        for nom in SOURCES:
            for n in ast.walk(ast.parse(adaptee(nom))):
                if isinstance(n, ast.Call):
                    self.assertNotIn(getattr(n.func, 'attr', ''), ('rmtree', 'unlink', 'remove'))
                    self.assertFalse(any(k.arg == 'shell' and isinstance(k.value, ast.Constant) and k.value.value is True for k in n.keywords))
                if isinstance(n, ast.Constant):
                    self.assertNotEqual(n.value, '-y')

    def test_vae_local_obligatoire_et_deepcache_optionnel(self):
        arbre = ast.parse(adaptee('scripts/inference.py'))
        self.assertFalse(any(isinstance(n, ast.ImportFrom) and n.module == 'DeepCache' for n in arbre.body))
        vae = next(n for n in ast.walk(arbre) if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
                   and n.func.attr == 'from_pretrained' and isinstance(n.func.value, ast.Name) and n.func.value.id == 'AutoencoderKL')
        self.assertEqual(ast.unparse(vae.args[0]), 'args.vae_local_path')
        self.assertTrue(next(k.value.value for k in vae.keywords if k.arg == 'local_files_only'))
        self.assertIn('"--vae_local_path", type=str, required=True', adaptee('scripts/inference.py'))

    def test_unet_charge_strictement(self):
        n = extraire('latentsync/models/unet.py', 'from_pretrained')
        appel = next(n for n in ast.walk(n) if isinstance(n, ast.Call) and getattr(n.func, 'attr', None) == 'load_state_dict')
        self.assertTrue(next(k.value.value for k in appel.keywords if k.arg == 'strict'))

    def test_identifiant_vae_distant_refuse_avant_tout_modele(self):
        n = extraire('scripts/inference.py', 'main')
        n.body = [n.body[0], ast.Return(value=ast.Constant(value=True))]
        verifier = charger_fonction(n, {'os': os})
        for chemin in ('stabilityai/sd-vae-ft-mse', '/chemin-absent-latentsync-test'):
            with self.subTest(chemin=chemin), self.assertRaises(ValueError):
                verifier(None, SimpleNamespace(vae_local_path=chemin))
        self.assertTrue(verifier(None, SimpleNamespace(vae_local_path=str(FIXTURES.resolve()))))

    def test_reencodage_implicite_refuse_avant_lecture(self):
        lecteurs = dict(read_video_cv2=mock.Mock(return_value='cv2'), read_video_decord=mock.Mock(return_value='decord'))
        lire = charger_fonction(extraire('latentsync/utils/util.py', 'read_video'), lecteurs)
        with self.assertRaises(ValueError):
            lire('source.mp4', change_fps=True)
        lecteurs['read_video_cv2'].assert_not_called()
        lecteurs['read_video_decord'].assert_not_called()
        self.assertEqual(lire('source.mp4', use_decord=False), 'cv2')

    def test_whisper_ne_telecharge_jamais(self):
        telecharger = charger_fonction(extraire('latentsync/whisper/whisper/__init__.py', '_download'), {})
        with self.assertRaisesRegex(RuntimeError, 'interdit'):
            telecharger('adresse-non-contactee', 'dossier-non-cree', False)

    def test_aucune_boucle_et_aucune_affine_si_source_insuffisante(self):
        boucle = charger_fonction(extraire('latentsync/pipelines/lipsync_pipeline.py', 'loop_video'), {})
        objet = SimpleNamespace(affine_transform_video=mock.Mock(return_value=('faces', 'boxes', 'matrices')))
        for chunks in ([], [1, 2, 3, 4]):
            with self.subTest(chunks=chunks):
                with self.assertRaises(ValueError):
                    boucle(objet, chunks, ['a', 'b', 'c'])
        objet.affine_transform_video.assert_not_called()
        self.assertEqual(boucle(objet, [1, 2], ['a', 'b', 'c']), (['a', 'b'], 'faces', 'boxes', 'matrices'))

    def test_conditionnement_trop_court_refuse_avant_le_denoising(self):
        n = extraire('latentsync/pipelines/lipsync_pipeline.py', '__call__')
        garde = next(x for x in n.body if isinstance(x, ast.If) and 'len(whisper_chunks)' in ast.unparse(x.test))
        fonction = ast.parse('def verifier(audio_samples, whisper_chunks, video_fps, audio_sample_rate):\n    pass').body[0]
        fonction.body = [garde]
        verifier = charger_fonction(fonction, {})
        verifier(SimpleNamespace(numel=lambda: 640), [1], 25, 16000)
        with self.assertRaisesRegex(ValueError, 'Conditionnement trop court'):
            verifier(SimpleNamespace(numel=lambda: 641), [1], 25, 16000)


class FinPipelineSimuleeTest(unittest.TestCase):
    """Exécute seulement la fin adaptée, avec données et encodeur simulés."""
    def setUp(self):
        n = extraire('latentsync/pipelines/lipsync_pipeline.py', '__call__')
        debut = next(i for i, x in enumerate(n.body) if isinstance(x, ast.If) and 'synced_video_frames.shape' in ast.unparse(x.test))
        signature = ast.parse('def finir(audio_samples, synced_video_frames, video_fps, audio_sample_rate, is_train, temp_dir, video_out_path, audio_path):\n    pass').body[0]
        signature.body = n.body[debut:]
        self.fs = SimpleNamespace(path=SimpleNamespace(lexists=mock.Mock(return_value=False), join=os.path.join), makedirs=mock.Mock())
        self.encodeur = SimpleNamespace(run=mock.Mock(), DEVNULL=subprocess.DEVNULL)
        self.son = SimpleNamespace(write=mock.Mock())
        self.video = mock.Mock()
        self.finir = charger_fonction(signature, dict(os=self.fs, subprocess=self.encodeur, sf=self.son, write_video=self.video))

    def lancer(self, samples=16000, images=26):
        pcm = SimpleNamespace(numel=lambda: samples, cpu=lambda: SimpleNamespace(numpy=lambda: list(range(samples))))
        return self.finir(pcm, SimpleNamespace(shape=(images,)), 25, 16000, False, '/neuf/temp', '/neuf/sortie.mp4', '/source/audio.wav')

    def test_pcm_trop_long_refuse_avant_toute_sortie(self):
        with self.assertRaisesRegex(ValueError, 'troncature'):
            self.lancer(samples=16001, images=25)
        self.fs.makedirs.assert_not_called()
        self.encodeur.run.assert_not_called()

    def test_chemin_existant_ou_lien_meme_casse_refuse(self):
        self.fs.path.lexists.return_value = True
        with self.assertRaises(FileExistsError):
            self.lancer()
        self.fs.makedirs.assert_not_called()
        self.video.assert_not_called()

    def test_mux_audio_original_et_erreur_encodeur_propagee(self):
        self.lancer()
        self.assertEqual(len(self.son.write.call_args.args[1]), 16000)
        commande = self.encodeur.run.call_args.args[0]
        self.assertIsInstance(commande, list)
        self.assertIn('/source/audio.wav', commande)
        self.assertNotIn('/neuf/temp/audio.wav', commande)
        self.assertIn('-n', commande)
        self.assertNotIn('-shortest', commande)
        self.assertTrue(self.encodeur.run.call_args.kwargs['check'])
        self.encodeur.run.side_effect = subprocess.CalledProcessError(1, commande)
        with self.assertRaises(subprocess.CalledProcessError):
            self.lancer()


if __name__ == '__main__':
    unittest.main()
