"""Échecs du lanceur sans GPU, avec fichiers synthétiques conservés."""
import fcntl
import json
import io
import os
import sys
import contextlib
from pathlib import Path
import shutil
import subprocess
import unittest
from unittest.mock import patch

from outils.sync.labo import lanceur_musetalk as m
from outils.sync.labo import test_lanceur_musetalk as base


class EchecsLanceur(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        base.BancMuseTalk.setUpClass()
        cls.fixture = base.BancMuseTalk()
        cls.counter = 0

    def preparer(self):
        self.fixture.charger(self.fixture.config())
        EchecsLanceur.counter += 1
        name = 'echec-' + str(EchecsLanceur.counter)
        run = self.fixture.root / 'runs' / name
        for d in ('inputs', 'runner', 'config'):
            (run / d).mkdir(parents=True, exist_ok=False)
        def stage(src, name):
            dest = run / 'inputs' / name
            shutil.copyfile(src, dest)
            return {'path': str(dest), 'bytes': dest.stat().st_size, 'sha256': m.sha256_file(dest)}
        video, audio = stage(self.fixture.correct, 'video.mp4'), stage(self.fixture.audio, 'audio.wav')
        model = stage(self.fixture.audio, 'model.wav')
        runner, task = run / 'runner/inference_preserve.py', run / 'config/task.yaml'
        runner.write_bytes(b'fixture runner')
        task.write_text('task_0:\n' + f'  video_path: {json.dumps(video["path"])}\n' + f'  audio_path: {json.dumps(audio["path"])}\n')
        (run / 'config/launcher.json').write_bytes(m.CONFIG_BYTES)
        output = m.expected_final_output_path(run, Path(video['path']), Path(audio['path']))
        manifest = {'status': 'prepared_no_inference', 'classification': 'ESSAI TECHNIQUE NON APPROUVÉ',
                    'launcher_config_sha256': m.CONFIG_SHA, 'language_key': 'fr',
                    'launcher': {'sha256': m.sha256_file(Path(m.__file__).resolve())},
                    'source_video': {'staged': video}, 'voice_sample': {'original_staged': audio, 'model_input': model},
                    'safe_runner_sha256': m.sha256_file(runner), 'config_sha256': m.sha256_file(task),
                    'planned_command': m.construire_commande(run), 'output_layout': {'expected_final': str(output)}}
        (run / 'manifest.json').write_text(json.dumps(manifest))
        return name, run, output

    def exercise(self, kind):
        name, run, output = self.preparer()
        original = subprocess.run
        def child(command, *args, **kwargs):
            if command == m.construire_commande(run):
                if kind == 'timeout':
                    raise subprocess.TimeoutExpired(command, 1200)
                if kind == 'nonzero':
                    return subprocess.CompletedProcess(command, 12)
                if kind == 'absent':
                    return subprocess.CompletedProcess(command, 0)
                output.parent.mkdir(parents=True, exist_ok=True)
                if kind == 'decode':
                    output.write_bytes(b'not video')
                else:
                    shutil.copyfile(self.fixture.correct, output)
                return subprocess.CompletedProcess(command, 0)
            return original(command, *args, **kwargs)
        def validator(*args):
            raise RuntimeError('synthetic validator failure')
        with patch.object(m, 'make_preserving_runner', return_value=b'fixture runner'), \
             patch.object(m, 'run_preflight', return_value={'gpu_policy': {'ready': True}}), \
             patch.object(m.subprocess, 'run', side_effect=child):
            if kind == 'validator':
                with patch.object(m, 'verifier_rendu_av', side_effect=validator):
                    code = m.safe_run(name, True, True)
            else:
                code = m.safe_run(name, True, True)
        result = json.loads((run / 'result.json').read_text())
        self.assertEqual(code, 1)
        self.assertEqual(result['status'], 'failed_or_invalid_output')
        self.assertIsNone(result['av_validation'])
        if kind == 'nonzero': self.assertEqual(result['child_exit_code'], 12)
        if kind == 'timeout': self.assertIn('TimeoutExpired', result['child_exception'])
        if kind == 'validator': self.assertIn('RuntimeError', result['postflight_exception'])

    def test_erreurs_enfant_et_rendu(self):
        for kind in ('nonzero', 'timeout', 'absent', 'decode', 'validator'):
            with self.subTest(kind=kind): self.exercise(kind)

    def test_verrou_deja_tenu(self):
        name, run, _ = self.preparer()
        lock = self.fixture.root / 'runs/active-gpu.lock'
        with lock.open('a+b') as held:
            fcntl.flock(held.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            with patch.object(m, 'make_preserving_runner', return_value=b'fixture runner'), patch.object(m.subprocess, 'run') as child:
                self.assertEqual(m.safe_run(name, True, True), 2)
                child.assert_not_called()
        result = json.loads((run / 'result.json').read_text())
        self.assertEqual(result['execution_stage'], 'before_model_start')
        self.assertIn('lock', result['reason'])

    def test_config_source_et_assets_alteres(self):
        for kind in ('config', 'source', 'assets'):
            with self.subTest(kind=kind):
                name, run, _ = self.preparer()
                if kind == 'config': (run / 'config/launcher.json').write_bytes(b'changed')
                with patch.object(m, 'make_preserving_runner', side_effect=RuntimeError('source changed') if kind == 'source' else None,
                                  return_value=b'fixture runner'), patch.object(m, 'run_preflight', side_effect=RuntimeError('assets changed')), \
                     patch.object(m.subprocess, 'run') as child:
                    if kind == 'assets':
                        self.assertEqual(m.safe_run(name, True, True), 2)
                        self.assertEqual(json.loads((run / 'result.json').read_text())['execution_stage'], 'before_model_start')
                    else:
                        with self.assertRaises(RuntimeError): m.safe_run(name, True, True)
                    child.assert_not_called()

    def test_statut_apres_tentative_demarrage(self):
        name, run, _ = self.preparer()
        original = m.append_event
        def events(path, row):
            if row['event'] == 'model_process_launch_requested':
                raise RuntimeError('synthetic journal failure')
            return original(path, row)
        with patch.object(m, 'make_preserving_runner', return_value=b'fixture runner'), \
             patch.object(m, 'run_preflight', return_value={'gpu_policy': {'ready': True}}), \
             patch.object(m, 'append_event', side_effect=events), patch.object(m.subprocess, 'run') as child:
            self.assertEqual(m.safe_run(name, True, True), 2)
            child.assert_not_called()
        result = json.loads((run / 'result.json').read_text())
        self.assertEqual(result['status'], 'launcher_error')
        self.assertEqual(result['execution_stage'], 'before_model_start')
        self.assertIn('not started', result['human_status'])
        open_targets = []
        for fd in Path('/proc/self/fd').iterdir():
            try: open_targets.append(os.readlink(fd))
            except FileNotFoundError: pass
        self.assertNotIn(str(run / 'run.log'), open_targets)

    def test_assets_reels_miniatures_puis_mutations_refusees(self):
        cfg = self.fixture.config()
        root = self.fixture.root / 'assets-controlled'
        source, weights = root / 'source', root / 'weights'
        (source / 'scripts').mkdir(parents=True)
        (weights / 'syncnet/auxiliary').mkdir(parents=True)
        shutil.copyfile(Path(__file__).parent / 'fixtures/upstream/inference.py.txt', source / 'scripts/inference.py')
        model = weights / 'syncnet/auxiliary/s3fd-619a316812.pth'
        model.write_bytes(b'synthetic model, not weights')
        (source / 'models').symlink_to(weights, target_is_directory=True)
        cache = root / 'cache/torch/hub/checkpoints'
        cache.mkdir(parents=True)
        (cache / 's3fd-619a316812.pth').symlink_to(model)
        cfg.update(root=str(root), source=str(source), weights=str(weights))
        self.fixture.charger(cfg)
        sources = {'scripts/inference.py': m.sha256_file(source / 'scripts/inference.py')}
        models = {'models/syncnet/auxiliary/s3fd-619a316812.pth': m.sha256_file(model)}
        with patch.object(m, 'EXPECTED_SOURCE', sources), patch.object(m, 'EXPECTED_MODELS', models):
            assets = m.verify_static_assets()
            self.assertEqual(assets['models'][next(iter(models))]['sha256'], models[next(iter(models))])
            fake_tool = root / 'fake-tool'
            fake_tool.write_text('#!/bin/sh\nexit 0\n')
            fake_tool.chmod(0o700)
            with patch.object(m, 'FFMPEG', fake_tool), patch.object(m, 'EXPECTED_MEDIA_HASHES',
                    {'ffmpeg': m.sha256_file(fake_tool), 'ffprobe': m.sha256_file(m.FFPROBE)}):
                m.verify_static_assets()
                fake_tool.chmod(0o600)
                with self.assertRaisesRegex(RuntimeError, 'media-tool hash/execute check failed'):
                    m.verify_static_assets()
            other = root / 'other-checkpoints/hub/checkpoints'
            other.mkdir(parents=True)
            (other / 's3fd-619a316812.pth').symlink_to(source / 'scripts/inference.py')
            with patch.object(m, 'TORCH_HOME', root / 'other-checkpoints'):
                with self.assertRaisesRegex(RuntimeError, 'SFD cache path'):
                    m.verify_static_assets()
            model.write_bytes(b'changed model')
            with self.assertRaisesRegex(RuntimeError, 'model/config hash mismatch'):
                m.verify_static_assets()
            model.write_bytes(b'synthetic model, not weights')
            (source / 'scripts/inference.py').write_bytes(b'changed source')
            with self.assertRaisesRegex(RuntimeError, 'source hash mismatch'):
                m.verify_static_assets()

    def test_identite_proc_reelle_et_pid_disparu(self):
        cfg = self.fixture.config()
        self.fixture.charger(cfg)
        pid = os.getpid()
        gpu = subprocess.CompletedProcess(['nvidia-smi'], 0, 'Synthetic GPU, fake-id, 16384, 15000, 0, 1\n', '')
        def probe(pid_number):
            proc = subprocess.CompletedProcess(['nvidia-smi'], 0, f'{pid_number}, python, 1\n', '')
            with patch.object(m.subprocess, 'run', side_effect=[gpu, proc]):
                return m.gpu_snapshot()
        snapshot = probe(pid)
        identity = snapshot['compute_process_identities'][str(pid)]
        self.assertEqual(identity['pid'], pid)
        self.assertEqual(identity['uid'], str(os.getuid()))
        m.AUTHORIZED_EXISTING_GPU_PROCESS = {**identity, 'max_used_mib': 5}
        self.assertTrue(m.evaluate_gpu_snapshot(snapshot)['ready'])
        disappeared = probe(999999999)
        self.assertIn('metadata_error', disappeared['compute_process_identities']['999999999'])
        self.assertFalse(m.evaluate_gpu_snapshot(disappeared)['ready'])

    def test_inputs_symlink_refuse_avant_sous_processus(self):
        name, run, _ = self.preparer()
        outside = self.fixture.root / ('inputs-exterieurs-' + name)
        (run / 'inputs').rename(outside)
        (run / 'inputs').symlink_to(outside, target_is_directory=True)
        with patch.object(m.subprocess, 'run') as child:
            with self.assertRaisesRegex(RuntimeError, 'inputs directory is a symlink'):
                m.safe_run(name, True, True)
            child.assert_not_called()
        self.assertTrue((outside / 'audio.wav').is_file())

    def test_main_prepare_source_epinglee_et_ffmpeg_reel(self):
        fixture_file = Path(__file__).parent / 'fixtures' / 'upstream' / 'inference.py.txt'
        self.assertTrue(fixture_file.is_file(), 'fixture amont épinglée absente')
        fixture_source = self.fixture.root / 'upstream-prepare'
        (fixture_source / 'scripts').mkdir(parents=True, exist_ok=False)
        shutil.copyfile(fixture_file, fixture_source / 'scripts/inference.py')
        cfg = self.fixture.config()
        cfg['source'] = str(fixture_source.resolve())
        cfg['inputs']['fr'] = {'path': str(self.fixture.mp3), 'bytes': self.fixture.mp3.stat().st_size,
                               'sha256': m.sha256_file(self.fixture.mp3), 'language': 'fr'}
        config_path = self.fixture.root / 'cli-prepare-config.json'
        config_path.write_text(json.dumps(cfg))
        output = io.StringIO()
        assets = {'source': {}, 'models': {}, 'ffmpeg': {}, 'ffprobe': {}}
        with patch.object(sys, 'argv', ['lanceur_musetalk.py', '--config', str(config_path), 'prepare', '--language', 'fr']), \
             patch.object(m, 'verify_static_assets', return_value=assets), contextlib.redirect_stdout(output):
            self.assertEqual(m.main(), 0)
        run = Path(output.getvalue().strip())
        manifest = json.loads((run / 'manifest.json').read_text())
        self.assertEqual(manifest['launcher_config_sha256'], m.sha256_file(config_path))
        self.assertEqual((run / 'config/launcher.json').read_bytes(), config_path.read_bytes())
        self.assertEqual((run / 'runner/inference_preserve.py').read_bytes(),
                         m.make_preserving_runner(fixture_source / 'scripts/inference.py'))
        self.assertEqual(manifest['voice_sample']['model_input']['sample_rate'], 16000)
        self.assertFalse((run / 'results').exists())

    def test_statut_apres_enfant_reellement_simule(self):
        name, run, _ = self.preparer()
        child_result = subprocess.CompletedProcess(m.construire_commande(run), 0)
        with patch.object(m, 'make_preserving_runner', return_value=b'fixture runner'), \
             patch.object(m, 'run_preflight', return_value={'gpu_policy': {'ready': True}}), \
             patch.object(m.subprocess, 'run', return_value=child_result) as child, \
             patch.object(Path, 'rglob', side_effect=OSError('synthetic listing error')):
            self.assertEqual(m.safe_run(name, True, True), 2)
            child.assert_called_once()
        result = json.loads((run / 'result.json').read_text())
        self.assertEqual(result['status'], 'launcher_error')
        self.assertEqual(result['execution_stage'], 'model_start_attempted')
        self.assertIn('may have started', result['human_status'])

    def test_prepare_refuse_entrees_avant_toute_sonde(self):
        for kind in ('video', 'fr'):
            for problem in ('symlink', 'altered'):
                with self.subTest(kind=kind, problem=problem):
                    cfg = self.fixture.config()
                    path = self.fixture.root / f'input-{kind}-{problem}'
                    original = Path(cfg['inputs'][kind]['path'])
                    if problem == 'symlink':
                        path.symlink_to(original)
                    else:
                        shutil.copyfile(original, path)
                        with path.open('ab') as out:
                            out.write(b'modification')
                    cfg['inputs'][kind]['path'] = str(path)
                    self.fixture.charger(cfg)
                    before = set(self.fixture.root.rglob('*'))
                    with patch.object(m, 'verify_static_assets', return_value={}), \
                         patch.object(m, 'probe') as probe, patch.object(m.subprocess, 'run') as child:
                        with self.assertRaises(RuntimeError):
                            m.prepare('fr')
                        probe.assert_not_called()
                        child.assert_not_called()
                    self.assertEqual(set(self.fixture.root.rglob('*')), before)
                    self.assertTrue(path.is_symlink() if problem == 'symlink' else path.is_file())

    def test_configuration_refuse_doublons_racine_et_inputs(self):
        text = json.dumps(self.fixture.config())
        for label, mutated in (
            ('root', text.replace('"gpu_name":', '"gpu_name": "autre", "gpu_name":', 1)),
            ('inputs', text.replace('"video":', '"video": {}, "video":', 1)),
        ):
            with self.subTest(label=label):
                path = self.fixture.root / f'doublon-{label}.json'
                path.write_text(mutated)
                with self.assertRaisesRegex(ValueError, 'JSON dupliquée'):
                    m.configurer(path)

    def test_configuration_rejouee_differe(self):
        name, run, _ = self.preparer()
        cfg = self.fixture.config(); cfg['padding_codec_seconds'] = .09
        self.fixture.charger(cfg)
        with patch.object(m.subprocess, 'run') as child:
            with self.assertRaisesRegex(RuntimeError, 'configuration changed'):
                m.safe_run(name, True, True)
            child.assert_not_called()


if __name__ == '__main__': unittest.main()
