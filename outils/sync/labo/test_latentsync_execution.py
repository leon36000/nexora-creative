"""Intégrité des octets avant lancement ; prévol AV et GPU simulés explicitement."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest import mock

from outils.sync.labo import latentsync_execution as execution
from outils.sync.labo import supervision_capsule

GPU = 'GPU-00000000-0000-0000-0000-000000000000'


class LatentSyncExecutionIntegrityTest(unittest.TestCase):
    def setUp(self):
        # Même les fichiers factices restent disponibles pour inspection.
        self.root = Path(tempfile.mkdtemp(prefix='latentsync-integrity-',
                                         dir=os.getenv('SYNC_TEST_ROOT')))

    @staticmethod
    def _sha(path: Path) -> str:
        return hashlib.sha256(path.read_bytes()).hexdigest()

    @staticmethod
    def _write(path: Path, data: bytes, mode: int = 0o600) -> None:
        path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        path.write_bytes(data)
        os.chmod(path, mode)

    def _fixture(self):
        runtime = self.root / 'runtime'
        run = self.root / 'run'
        tools = self.root / 'tools'
        runtime.mkdir(mode=0o700)
        run.mkdir(mode=0o700)
        tools.mkdir(mode=0o700)

        script = runtime / 'scripts' / 'capsule_inference.py'
        config_unet = runtime / 'configs' / 'unet' / 'stage2_512.yaml'
        self._write(script, b'# fake inference source\n')
        self._write(config_unet, b'synthetic-config: true\n')
        runtime_files = {
            str(path.relative_to(runtime)): self._sha(path)
            for path in sorted(runtime.rglob('*')) if path.is_file()
        }
        manifest = self.root / 'runtime-manifest.json'
        self._write(manifest, json.dumps({
            'runtime': str(runtime), 'runtime_sha256': runtime_files,
        }, sort_keys=True).encode())

        executables = {}
        for key, filename in (
            ('python', 'python'), ('ffmpeg', 'ffmpeg'), ('ffprobe', 'ffprobe'),
            ('bwrap', 'bwrap'), ('nvidia_smi', 'nvidia-smi'),
        ):
            path = tools / filename
            self._write(path, b'#!/bin/sh\nexit 0\n', 0o700)
            executables[key] = str(path)

        unet = self.root / 'weights' / 'unet.safetensors'
        vae = self.root / 'weights' / 'vae'
        vae_config = vae / 'config.json'
        vae_weights = vae / 'diffusion_pytorch_model.bin'
        self._write(unet, b'synthetic-unet-weight-fixture')
        self._write(vae_config, b'{"synthetic":true}\n')
        self._write(vae_weights, b'synthetic-vae-weight-fixture')

        inputs = {
            'audio-original.mp3': b'synthetic-mp3-fixture',
            'audio-entree.wav': b'synthetic-pcm-fixture',
            'video-entree.mp4': b'synthetic-cfr-video-fixture',
        }
        for filename, data in inputs.items():
            self._write(run / filename, data)
        provenance = run / 'provenance-entrees.json'
        self._write(provenance, json.dumps({
            'modele_demande': 'elevenlabs/eleven-v4',
            'fichiers': {filename: hashlib.sha256(data).hexdigest()
                         for filename, data in inputs.items()},
        }, sort_keys=True).encode())

        config = {
            'runtime': str(runtime), 'python': executables['python'],
            'ffmpeg': executables['ffmpeg'], 'ffprobe': executables['ffprobe'],
            'bwrap': executables['bwrap'], 'nvidia_smi': executables['nvidia_smi'],
            'gpu_uuid': GPU, 'runtime_manifest': str(manifest),
            'runtime_manifest_sha256': self._sha(manifest),
            'executables_sha256': {name: self._sha(Path(path))
                                   for name, path in executables.items()},
            'unet': str(unet), 'vae': str(vae),
            'poids_sha256': {
                str(unet): self._sha(unet), str(vae_config): self._sha(vae_config),
                str(vae_weights): self._sha(vae_weights),
            },
            'provenance_sha256': self._sha(provenance),
            'gpu_lock': str(self.root / 'gpu.lock'),
        }
        mutation_targets = {
            'poids': unet,
            'source runtime': script,
            'entrée audio': run / 'audio-entree.wav',
        }
        return run, config, mutation_targets

    def _assert_mutation_refused_before_gpu(self, target: str) -> None:
        run, config, targets = self._fixture()
        calls = {'gpu_preflight': 0}

        def gpu_preflight(_config):
            calls['gpu_preflight'] += 1
            return {
                'uuid': GPU, 'total_mib': 40960, 'free_mib': 32000,
                'utilisation': 0, 'power_limit_w': 300.0, 'processus': [],
            }

        def gpu_forbidden(_config):
            raise AssertionError('gpu() ne doit pas être appelé par ce test')

        def supervisor_forbidden(*_args, **_kwargs):
            raise AssertionError('superviser() ne doit pas être appelé par ce test')

        with mock.patch.object(execution, '_prevol', side_effect=gpu_preflight), \
             mock.patch.object(execution, 'gpu', side_effect=gpu_forbidden), \
             mock.patch.object(execution.highsync_preflight, 'preflight',
                               return_value={'statut': 'preflight_synthetique_valide'}) as av_preflight, \
             mock.patch.object(supervision_capsule, 'superviser',
                               side_effect=supervisor_forbidden) as superviseur:
            plan_sha = execution.planifier(config, run)
            gpu_calls_after_plan = calls['gpu_preflight']
            path = targets[target]
            path.write_bytes(path.read_bytes() + b'!')

            with self.assertRaisesRegex(ValueError, 'empreinte différente'):
                execution.executer(run, plan_sha)

            self.assertEqual(gpu_calls_after_plan, 1)
            self.assertEqual(calls['gpu_preflight'], gpu_calls_after_plan)
            av_preflight.assert_called_once()
            superviseur.assert_not_called()

    def test_mutation_du_poids_refusee_avant_gpu(self):
        self._assert_mutation_refused_before_gpu('poids')

    def test_mutation_de_la_source_runtime_refusee_avant_gpu(self):
        self._assert_mutation_refused_before_gpu('source runtime')

    def test_mutation_de_l_entree_audio_refusee_avant_gpu(self):
        self._assert_mutation_refused_before_gpu('entrée audio')

    def test_plan_modifie_refuse_avant_tout_lancement(self):
        run, config, _ = self._fixture()
        with mock.patch.object(execution, '_prevol', return_value={'simulation':True}) as prevol, \
             mock.patch.object(execution.highsync_preflight, 'preflight', return_value={}), \
             mock.patch.object(supervision_capsule, 'superviser') as superviseur:
            sha = execution.planifier(config,run)
            plan = run/'plan-execution.json'
            plan.write_bytes(plan.read_bytes()+b' ')
            with self.assertRaisesRegex(ValueError,'empreinte différente'):
                execution.executer(run,sha)
            self.assertEqual(prevol.call_count,1)
            superviseur.assert_not_called()
        self.assertFalse((run/'execution.log').exists())

    def test_reexecution_refuse_et_preserve_les_traces(self):
        run, config, _ = self._fixture()
        with mock.patch.object(execution, '_prevol', return_value={'simulation':True}) as prevol, \
             mock.patch.object(execution.highsync_preflight, 'preflight', return_value={}), \
             mock.patch.object(supervision_capsule, 'superviser') as superviseur:
            sha = execution.planifier(config,run)
            log = run/'execution.log'
            log.write_bytes(b'temoin precedent a conserver')
            with self.assertRaisesRegex(ValueError,'déjà exécuté'):
                execution.executer(run,sha)
            self.assertEqual(prevol.call_count,1)
            superviseur.assert_not_called()
        self.assertEqual(log.read_bytes(),b'temoin precedent a conserver')


if __name__ == '__main__':
    unittest.main()
