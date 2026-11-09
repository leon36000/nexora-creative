"""Contrats CPU du banc MuseTalk ; les médias produits restent dans SYNC_TEST_ROOT."""
import json
import os
from pathlib import Path
import subprocess
import shutil
from unittest.mock import patch
import tempfile
import unittest

from outils.sync.labo import lanceur_musetalk as lanceur


class BancMuseTalk(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root = Path(tempfile.mkdtemp(prefix='musetalk-cpu-', dir=os.environ['SYNC_TEST_ROOT']))
        cls.ffmpeg = Path(os.environ['SYNC_FFMPEG'])
        cls.ffprobe = Path(os.environ['SYNC_FFPROBE'])
        cls.audio = cls.root / 'reference.wav'
        cls.mp3 = cls.root / 'reference.mp3'
        cls.court = cls.root / 'court.mp4'
        cls.correct = cls.root / 'correct.mp4'
        def ff(*args):
            subprocess.run([str(cls.ffmpeg), '-nostdin', '-n', '-v', 'error', *args], check=True, timeout=30)
        ff('-f', 'lavfi', '-i', 'sine=frequency=440:sample_rate=48000:duration=2.7', str(cls.audio))
        ff('-i', str(cls.audio), '-c:a', 'libmp3lame', '-q:a', '4', str(cls.mp3))
        src = ['-f', 'lavfi', '-i', 'color=c=blue:s=64x64:r=24:d=2.708333333', '-i', str(cls.audio)]
        ff(*src, '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-c:a', 'aac', str(cls.correct))
        ff(*src, '-vf', 'trim=end_frame=27,setpts=PTS-STARTPTS', '-r', '24', '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-c:a', 'aac', str(cls.court))
        print('Fixtures MuseTalk CPU conservées :', cls.root, flush=True)

    def config(self):
        src = {'path': str(self.audio), 'bytes': self.audio.stat().st_size, 'sha256': lanceur.sha256_file(self.audio)}
        return {'root': str(self.root), 'source': str(self.root), 'weights': str(self.root), 'python': '/usr/bin/python3',
                'ffmpeg': str(self.ffmpeg), 'ffprobe': str(self.ffprobe), 'ffmpeg_sha256': lanceur.sha256_file(self.ffmpeg),
                'ffprobe_sha256': lanceur.sha256_file(self.ffprobe), 'gpu_name': 'Synthetic GPU', 'gpu_min_free_mib': 12288,
                'gpu_process': None, 'inputs': {'video': {'path': str(self.correct), 'bytes': self.correct.stat().st_size,
                'sha256': lanceur.sha256_file(self.correct)}, 'fr': {**src, 'language': 'fr'}}, 'padding_codec_seconds': .08}

    def charger(self, cfg):
        path = self.root / ('config-' + next(tempfile._get_candidate_names()) + '.json')
        path.write_text(json.dumps(cfg))
        lanceur.configurer(path)
        return path

    def test_cadence_25_est_transmise_et_validee_pour_mp4(self):
        video25 = self.root / 'cadence25.mp4'
        subprocess.run([str(self.ffmpeg), '-nostdin', '-n', '-v', 'error', '-f', 'lavfi', '-i',
                        'color=c=blue:s=64x64:r=25:d=2.72', '-i', str(self.audio), '-c:v', 'libx264',
                        '-pix_fmt', 'yuv420p', '-c:a', 'aac', str(video25)], check=True, timeout=30)
        cfg = self.config()
        cfg['fps'] = 25
        cfg['inputs']['video'] = {'path': str(video25), 'bytes': video25.stat().st_size,
                                  'sha256': lanceur.sha256_file(video25)}
        self.charger(cfg)
        self.assertEqual(lanceur.construire_commande(self.root)[lanceur.construire_commande(self.root).index('--fps') + 1], '25')
        self.assertTrue(lanceur.verifier_rendu_av(self.audio, video25)['valide'])
        lanceur.verifier_cadence_video(lanceur.probe(video25))
        with self.assertRaisesRegex(ValueError, 'Cadence vidéo incompatible'):
            lanceur.verifier_cadence_video(lanceur.probe(self.correct))
        self.charger(self.config())
        lanceur.verifier_cadence_video(lanceur.probe(self.correct))
        self.assertEqual(lanceur.construire_commande(self.root)[lanceur.construire_commande(self.root).index('--fps') + 1], '24')
        with self.assertRaisesRegex(ValueError, 'Cadence vidéo incompatible'):
            lanceur.verifier_cadence_video(lanceur.probe(video25))
        cfg['fps'] = True
        with self.assertRaises(ValueError):
            self.charger(cfg)


    def test_identites_et_refus_gpu(self):
        cfg = self.config()
        cfg['gpu_process'] = {'pid': 123, 'uid': '1000', 'start_ticks': '45', 'exe': '/usr/bin/python3', 'max_used_mib': 5}
        self.charger(cfg)
        lanceur.self_test_gpu_policy()
        cfg['gpu_min_free_mib'] = 100
        with self.assertRaises(ValueError):
            self.charger(cfg)

    def test_configuration_refuse_champ_non_prevu(self):
        cfg = self.config()
        cfg['inputs']['fr']['text'] = 'synthetic'
        with self.assertRaises(ValueError):
            self.charger(cfg)

    def test_conversion_reelle_et_refus_ecrasement(self):
        self.charger(self.config())
        dest = self.root / 'modele.wav'
        resultat = lanceur.make_model_audio(self.mp3, dest)
        self.assertEqual(resultat['sample_rate'], 16000)
        self.assertEqual(resultat['sample_count'], 43200)
        sha = lanceur.sha256_file(dest)
        with self.assertRaises(RuntimeError):
            lanceur.make_model_audio(self.audio, dest)
        self.assertEqual(sha, lanceur.sha256_file(dest))

    def test_validation_reelle_refuse_video_tronquee(self):
        self.charger(self.config())
        self.assertTrue(lanceur.verifier_rendu_av(self.audio, self.correct)['valide'])
        result = lanceur.verifier_rendu_av(self.audio, self.court)
        self.assertFalse(result['valide'])
        self.assertEqual(result['video']['images_decodees'], 27)

    def test_statut_terminal_exige_validation_av(self):
        self.charger(self.config())
        actual_run = subprocess.run
        for index, (media, expected) in enumerate(((self.correct, 'completed_av_validated'),
                                                    (self.court, 'failed_or_invalid_output'))):
            run = self.root / 'runs' / f'test-{index}'
            for name in ('inputs', 'runner', 'config'):
                (run / name).mkdir(parents=True, exist_ok=False)
            def stage(source, name):
                path = run / 'inputs' / name
                shutil.copyfile(source, path)
                return {'path': str(path), 'bytes': path.stat().st_size, 'sha256': lanceur.sha256_file(path)}
            video = stage(self.correct, 'video.mp4')
            audio = stage(self.audio, 'audio.wav')
            model = stage(self.audio, 'model.wav')
            runner = run / 'runner/inference_preserve.py'
            task = run / 'config/task.yaml'
            runner.write_text('synthetic fixture')
            task.write_text('task_0:\n' + f'  video_path: {json.dumps(video["path"])}\n' + f'  audio_path: {json.dumps(audio["path"])}\n')
            (run / 'config/launcher.json').write_bytes(lanceur.CONFIG_BYTES)
            output = lanceur.expected_final_output_path(run, Path(video['path']), Path(audio['path']))
            manifest = {'status': 'prepared_no_inference', 'classification': 'ESSAI TECHNIQUE NON APPROUVÉ',
                        'launcher_config_sha256': lanceur.CONFIG_SHA, 'language_key': 'fr',
                        'launcher': {'sha256': lanceur.sha256_file(Path(lanceur.__file__).resolve())},
                        'source_video': {'staged': video}, 'voice_sample': {'original_staged': audio, 'model_input': model},
                        'safe_runner_sha256': lanceur.sha256_file(runner), 'config_sha256': lanceur.sha256_file(task),
                        'planned_command': ['/bin/true'], 'output_layout': {'expected_final': str(output)}}
            (run / 'manifest.json').write_text(json.dumps(manifest))
            def fake_child(command, *args, **kwargs):
                if command == ['/bin/true']:
                    output.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copyfile(media, output)
                    return subprocess.CompletedProcess(command, 0)
                return actual_run(command, *args, **kwargs)
            with patch.object(lanceur, 'make_preserving_runner', return_value=b'synthetic fixture'), \
                 patch.object(lanceur, 'run_preflight', return_value={'gpu_policy': {'ready': True}}), \
                 patch.object(lanceur, 'construire_commande', return_value=['/bin/true']), \
                 patch.object(lanceur.subprocess, 'run', side_effect=fake_child):
                code = lanceur.safe_run(f'test-{index}', True, True)
            result = json.loads((run / 'result.json').read_text())
            self.assertEqual(result['status'], expected)
            self.assertEqual(code, 0 if index == 0 else 1)
            self.assertEqual(result['av_validation']['valide'], index == 0)

    def test_manifest_altere_refuse_avant_sous_processus(self):
        self.charger(self.config())
        run = self.root / 'runs' / 'altered'
        for name in ('inputs', 'runner', 'config'):
            (run / name).mkdir(parents=True, exist_ok=False)
        def stage(source, name):
            path = run / 'inputs' / name
            shutil.copyfile(source, path)
            return {'path': str(path), 'bytes': path.stat().st_size, 'sha256': lanceur.sha256_file(path)}
        video = stage(self.correct, 'video.mp4')
        audio = stage(self.audio, 'audio.wav')
        model = stage(self.audio, 'model.wav')
        runner, task = run / 'runner/inference_preserve.py', run / 'config/task.yaml'
        runner.write_text('fixture')
        task.write_text('task_0:\n' + f'  video_path: {json.dumps(video["path"])}\n' + f'  audio_path: {json.dumps(audio["path"])}\n')
        (run / 'config/launcher.json').write_bytes(lanceur.CONFIG_BYTES)
        manifest = {'status': 'prepared_no_inference', 'classification': 'ESSAI TECHNIQUE NON APPROUVÉ',
                    'launcher_config_sha256': lanceur.CONFIG_SHA, 'language_key': 'fr',
                    'launcher': {'sha256': lanceur.sha256_file(Path(lanceur.__file__).resolve())},
                    'source_video': {'staged': video}, 'voice_sample': {'original_staged': audio, 'model_input': model},
                    'safe_runner_sha256': lanceur.sha256_file(runner), 'config_sha256': lanceur.sha256_file(task),
                    'planned_command': ['/bin/true'], 'output_layout': {'expected_final': '/tmp/outside.mp4'}}
        path = run / 'manifest.json'
        with patch.object(lanceur, 'make_preserving_runner', return_value=b'fixture'), patch.object(lanceur.subprocess, 'run') as call:
            path.write_text(json.dumps(manifest))
            with self.assertRaisesRegex(RuntimeError, 'command'):
                lanceur.safe_run('altered', True, True)
            manifest['planned_command'] = lanceur.construire_commande(run)
            path.write_text(json.dumps(manifest))
            with self.assertRaisesRegex(RuntimeError, 'output'):
                lanceur.safe_run('altered', True, True)
            call.assert_not_called()

    def test_refus_soumission_non_autorisee(self):
        self.charger(self.config())
        with self.assertRaises(RuntimeError):
            lanceur.safe_run('unused', False, False)


if __name__ == '__main__':
    unittest.main()
