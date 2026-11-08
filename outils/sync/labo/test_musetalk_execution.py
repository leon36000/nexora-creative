"""Tests CPU portables du flux planifier/executer du banc MuseTalk."""
from __future__ import annotations

import fcntl
import hashlib
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest import mock

from outils.sync import valider_duree_av as av
from outils.sync.labo import capsule_sync, highsync_preflight, lanceur_musetalk
from outils.sync.labo import latentsync_execution as commun
from outils.sync.labo import musetalk_execution as mx
from outils.sync.labo import supervision_capsule
from outils.sync.labo.bootstrap import prepare_faceparser_bootstrap as bootstrap
from outils.sync.labo.musetalk_patch import adapter_audio_processor

LABO = Path(__file__).resolve().parent
UPSTREAM = LABO / 'fixtures' / 'upstream'
AUDIO_FIXTURE = LABO / 'musetalk_audio_fixture' / 'audio_processor.py.txt'
SYNC_TEST_ROOT = Path(os.environ['SYNC_TEST_ROOT'])
if not SYNC_TEST_ROOT.is_absolute() or SYNC_TEST_ROOT.is_symlink():
    raise RuntimeError('SYNC_TEST_ROOT doit être un chemin Storage absolu sans lien symbolique')
SYNC_TEST_ROOT.mkdir(mode=0o700, parents=True, exist_ok=True)

BOOTSTRAP_FIXTURES = {
    'scripts/inference.py': 'inference.py.txt',
    'musetalk/utils/preprocessing.py': 'preprocessing.py.txt',
    'musetalk/utils/face_parsing/resnet.py': 'faceparser-resnet.py.txt',
    'musetalk/utils/face_parsing/model.py': 'faceparser-model.py.txt',
    'musetalk/utils/face_parsing/__init__.py': 'faceparser-init.py.txt',
}
GPU = 'GPU-11111111-2222-3333-4444-555555555555'
PREVOL = {'gpu': {'uuid': GPU, 'total_mib': 32768, 'free_mib': 32000,
                  'utilisation': 0, 'power_limit_w': 475, 'processus': []},
          'ram_disponible_mib': 32000,
          'file_locale': {'statut': 'inconnue'}, 'portee': 'fixture CPU'}
PREFLIGHT = {'statut': 'preflight_cpu_valide', 'video': {'images_decodees': 226},
             'audio_pcm': {'echantillons': 144640}}
BILAN = {'statut': 'succès', 'phase': 'termine', 'arret_confirmé': True,
         'identite_namespace': {'pid': 2}, 'processus_observés': []}


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def put(path: Path, data: bytes, mode: int = 0o600) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    path.write_bytes(data)
    path.chmod(mode)
    return path


def put_json(path: Path, obj) -> Path:
    return put(path, (json.dumps(obj, ensure_ascii=False, indent=2) + '\n').encode())


def copy_fixture(source: Path, target: Path) -> bytes:
    data = source.read_bytes()
    target.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    with target.open('xb') as stream:
        stream.write(data)
    target.chmod(0o600)
    return data


class MuseTalkExecutionTests(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp(prefix='musetalk-cpu-', dir=SYNC_TEST_ROOT))
        self.root.chmod(0o700)
        self.prevol = mock.patch.object(commun, '_prevol', return_value=PREVOL)
        self.prevol_mock = self.prevol.start()
        self.addCleanup(self.prevol.stop)
        self.preflight = mock.patch.object(highsync_preflight, 'preflight', return_value=PREFLIGHT)
        self.preflight_mock = self.preflight.start()
        self.addCleanup(self.preflight.stop)
        self.supervise = mock.patch.object(supervision_capsule, 'superviser')
        self.supervise_mock = self.supervise.start()
        self.addCleanup(self.supervise.stop)
        self.validate_av = mock.patch.object(av, 'valider', return_value={'valide': True, 'statut': 'av_cpu_valide'})
        self.av_mock = self.validate_av.start()
        self.addCleanup(self.validate_av.stop)
        self.no_child = mock.patch('subprocess.Popen', side_effect=AssertionError('aucun enfant réel autorisé'))
        self.popen_mock = self.no_child.start()
        self.addCleanup(self.no_child.stop)

    def make_case(self, label='case'):
        case = self.root / f'{label}-{len(list(self.root.iterdir())):02d}'
        case.mkdir(mode=0o700, exist_ok=False)
        source_root = case / 'source'
        source_root.mkdir(mode=0o700)
        raw_source = {}
        for relative, fixture_name in BOOTSTRAP_FIXTURES.items():
            raw_source[relative] = copy_fixture(UPSTREAM / fixture_name, source_root / relative)
        overlay_outputs, overlay_manifest = bootstrap.build_outputs(source_root)

        runtime, models, run, bin_dir, locks = (case / n for n in ('runtime', 'models', 'run', 'bin', 'locks'))
        for directory in (runtime, models, run, bin_dir, locks):
            directory.mkdir(mode=0o700)
        # Inference reste la fixture upstream épinglée; les quatre autres
        # sources proviennent du vrai build_outputs() du dépôt.
        put(runtime / 'scripts/inference.py', raw_source['scripts/inference.py'])
        for relative, data in overlay_outputs.items():
            put(runtime / relative, data)
        audio_original = AUDIO_FIXTURE.read_bytes()
        audio_patched = adapter_audio_processor(audio_original)
        put(runtime / 'musetalk/utils/audio_processor.py', audio_patched)
        put(runtime / 'scripts/inference_preserve.py',
            lanceur_musetalk.make_preserving_runner(runtime / 'scripts/inference.py'))
        (runtime / 'models').symlink_to(models, target_is_directory=True)
        runtime_files = {
            path.relative_to(runtime).as_posix(): sha(path.read_bytes())
            for path in runtime.rglob('*') if path.is_file() and not path.is_symlink()
        }
        manifest = {
            'runtime': str(runtime), 'runtime_sha256': runtime_files,
            'links': {'models': str(models)}, 'source_root': str(source_root),
            'original_source_sha256': overlay_manifest['source_sha256'],
            'overlay_sha256': overlay_manifest['overlay_sha256'],
        }
        manifest_path = put_json(case / 'runtime-manifest.json', manifest)

        # Poids uniquement synthétiques; attendu épinglé aux SHA de la fixture
        # le temps de ce test, sans copier ou lire de poids réels.
        model_hashes = {}
        for name in lanceur_musetalk.EXPECTED_MODELS:
            relative = Path(name).relative_to('models')
            data = ('synthetic-weight:' + name).encode()
            put(models / relative, data)
            model_hashes[name] = sha(data)
        self.model_pin = mock.patch.object(lanceur_musetalk, 'EXPECTED_MODELS', model_hashes)
        self.model_pin.start()
        self.addCleanup(self.model_pin.stop)

        exe_hashes, executables = {}, {}
        for name in ('python', 'ffmpeg', 'ffprobe', 'bwrap', 'nvidia_smi'):
            path = bin_dir / name
            data = ('synthetic-executable:' + name).encode()
            put(path, data, 0o700)
            exe_hashes[name] = sha(data)
            executables[name] = str(path)
        config = {
            'runtime': str(runtime), 'runtime_manifest': str(manifest_path),
            'runtime_manifest_sha256': sha(manifest_path.read_bytes()),
            'models': str(models), **executables, 'executables_sha256': exe_hashes,
            'gpu_uuid': GPU, 'gpu_lock': str(locks / 'gpu.lock'),
        }
        input_bytes = {
            'audio-original.mp3': b'synthetic mp3 bytes',
            'audio-entree.wav': b'synthetic pcm bytes',
            'video-entree.mp4': b'synthetic mp4 bytes',
        }
        for name, data in input_bytes.items():
            put(run / name, data)
        provenance = {'modele_demande': 'elevenlabs/eleven-v4',
                      'fichiers': {name: sha(data) for name, data in input_bytes.items()}}
        provenance_path = put_json(run / 'provenance-entrees.json', provenance)
        config['provenance_sha256'] = sha(provenance_path.read_bytes())
        return {'root': case, 'runtime': runtime, 'models': models, 'run': run,
                'config': config}

    def plan(self, case):
        return mx.planifier(case['config'], case['run'])

    def assert_refuses_without_prevol(self, case, plan_sha):
        before = self.prevol_mock.call_count
        with self.assertRaises((ValueError, capsule_sync.ErreurCapsule, OSError)):
            mx.executer(case['run'], plan_sha)
        self.assertEqual(self.prevol_mock.call_count, before,
                         'refus arrivé après un prévol GPU')
        self.supervise_mock.assert_not_called()

    def test_pinned_mutations_refused_before_prevol_or_supervisor(self):
        for scenario in ('audio', 'runtime', 'weight', 'plan', 'task'):
            with self.subTest(scenario=scenario):
                case = self.make_case(scenario)
                self.prevol_mock.reset_mock(); self.supervise_mock.reset_mock()
                plan_sha = self.plan(case)
                if scenario == 'audio':
                    put(case['run'] / 'audio-entree.wav', b'changed pcm')
                elif scenario == 'runtime':
                    path = case['runtime'] / 'musetalk/utils/preprocessing.py'
                    put(path, path.read_bytes() + b'\n# mutation')
                elif scenario == 'weight':
                    put(case['models'] / 'musetalkV15/unet.pth', b'mutated fake weight')
                elif scenario == 'plan':
                    put(case['run'] / 'plan-execution.json', b'{"statut":"planifie_sans_inference"}\n')
                elif scenario == 'task':
                    put(case['run'] / 'task.yaml', b'{"task_0":{"video_path":"/wrong","audio_path":"/wrong"}}\n')
                self.assert_refuses_without_prevol(case, plan_sha)

    def test_occupied_gpu_lock_refuses_without_prevol_or_supervisor(self):
        case = self.make_case('locked')
        self.prevol_mock.reset_mock(); self.supervise_mock.reset_mock()
        plan_sha = self.plan(case)
        before = self.prevol_mock.call_count
        held = os.open(case['config']['gpu_lock'], os.O_CREAT | os.O_RDWR, 0o600)
        try:
            fcntl.flock(held, fcntl.LOCK_EX | fcntl.LOCK_NB)
            with self.assertRaises(BlockingIOError):
                mx.executer(case['run'], plan_sha)
            self.assertEqual(self.prevol_mock.call_count, before,
                             'un second prévol a été exécuté malgré le verrou')
            self.supervise_mock.assert_not_called()
        finally:
            fcntl.flock(held, fcntl.LOCK_UN)
            os.close(held)

    def test_preexisting_output_is_preserved_and_never_supervised(self):
        case = self.make_case('existing-output')
        self.prevol_mock.reset_mock(); self.supervise_mock.reset_mock()
        plan_sha = self.plan(case)
        before = self.prevol_mock.call_count
        output = case['run'] / 'sortie.mp4'
        original = b'preexisting synthetic result'
        put(output, original)
        with self.assertRaisesRegex(ValueError, 'essai déjà exécuté'):
            mx.executer(case['run'], plan_sha)
        self.assertEqual(output.read_bytes(), original)
        self.assertEqual(self.prevol_mock.call_count, before)
        self.supervise_mock.assert_not_called()

    def test_synthetic_plan_execute_supervisor_timeout_and_av_status(self):
        case = self.make_case('success-path')
        self.prevol_mock.reset_mock(); self.supervise_mock.reset_mock(); self.av_mock.reset_mock()
        plan_sha = self.plan(case)
        plan = json.loads((case['run'] / 'plan-execution.json').read_text())
        self.assertEqual(plan['statut'], 'planifie_sans_inference')
        self.assertFalse(plan['voix_validee_humain'])
        self.assertFalse(plan['produit_livre'])

        def fake_superviser(argv, run, lock_fd, status_fd_lire, status_fd_ecrire, delai, controle):
            self.assertEqual(delai, 1200)
            self.assertTrue({'--unshare-net', '--unshare-pid', '--clearenv'} <= set(argv))
            self.assertEqual(argv[argv.index('--sync-fd') + 1], str(lock_fd))
            self.assertEqual(argv[argv.index('--json-status-fd') + 1], str(status_fd_ecrire))
            boundary = argv.index('--')
            env = {}
            i = 0
            while i < boundary:
                if argv[i] == '--setenv':
                    env[argv[i + 1]] = argv[i + 2]; i += 3
                else:
                    i += 1
            self.assertEqual({k for k in env if k.startswith('NEXORA_')},
                             {'NEXORA_FFMPEG_BIN', 'NEXORA_FEATURE_AUDIO_PATH'})
            self.assertEqual(env['NEXORA_FFMPEG_BIN'], case['config']['ffmpeg'])
            self.assertEqual(env['NEXORA_FEATURE_AUDIO_PATH'], str(run / 'audio-entree.wav'))
            put(run / 'sortie.mp4', b'synthetic output; never decoded')
            os.close(status_fd_lire); os.close(status_fd_ecrire)
            return dict(BILAN)

        self.supervise_mock.side_effect = fake_superviser
        result = mx.executer(case['run'], plan_sha)
        self.supervise_mock.assert_called_once()
        self.av_mock.assert_called_once()
        self.assertEqual(result['statut'], 'av_valide_non_juge')
        self.assertEqual(result['qualite_humaine'], 'non évaluée')
        self.assertEqual(result['av']['statut'], 'av_cpu_valide')
        self.assertNotIn('produit_livre', result)
        self.assertEqual((case['run'] / 'sortie.mp4').read_bytes(), b'synthetic output; never decoded')


if __name__ == '__main__':
    unittest.main(verbosity=2)
