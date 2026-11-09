from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import socket
import stat
import sys
import threading
import time
import unittest
import uuid
from unittest import mock

from outils.sync.labo import (
    capsule_sync, highsync_preflight, latentsync_execution, media_sync,
    musetalk_execution, sync_worker_adapter as adapter,
    sync_worker_rpc as rpc,
)
from outils.sync.labo.sync_worker_rpc import (
    AllowlistResolver, SyncWorkerRpc, TakeRecord,
)

CHILD_ERROR_RECEIPT_NAME = 'worker-error.json'


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


class _ThreadPresent:
    def is_alive(self):
        return True


class SyncWorkerRpcTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        root_value = os.environ.get('SYNC_TEST_ROOT')
        if not root_value:
            raise RuntimeError('SYNC_TEST_ROOT doit pointer vers un dossier Storage explicite')
        cls.test_root = Path(root_value)
        if cls.test_root.is_symlink() or not cls.test_root.is_dir():
            raise RuntimeError('SYNC_TEST_ROOT doit exister et ne pas être un lien')

    def setUp(self):
        self.case = self.test_root / f'rpc-{self._testMethodName}-{uuid.uuid4().hex}'
        self.case.mkdir(mode=0o700)
        self.media_root = self.case / 'media'
        self.media_root.mkdir(mode=0o700)
        self.state_root = self.case / 'state'
        self.state_root.mkdir(mode=0o700)
        self.socket_root = self.test_root / f's{uuid.uuid4().hex[:6]}'
        self.socket_root.mkdir(mode=0o700)
        self.video_bytes = b'server-owned synthetic video bytes\x00'
        self.audio_bytes = b'server-owned synthetic PCM bytes\x01'
        self.video_path = self.media_root / 'take-video.mp4'
        self.audio_path = self.media_root / 'take-audio.wav'
        self.video_path.write_bytes(self.video_bytes)
        self.audio_path.write_bytes(self.audio_bytes)
        self.records = AllowlistResolver([
            TakeRecord('org-local', 17, 'video', self.video_path, sha(self.video_bytes),
                       len(self.video_bytes), 1.0, fps=25.0),
            TakeRecord('org-local', 29, 'audio', self.audio_path, sha(self.audio_bytes),
                       len(self.audio_bytes), 1.0, sample_rate=16000),
        ])
        self.calls = []
        binding = adapter.Moteur({'binding': 'private-test'}, self._plan, self._execute)
        self.server = SyncWorkerRpc(
            self.state_root, self.socket_root / 's', (self.media_root,),
            self.records, {'musetalk': binding},
            {'musetalk': {'maxDurationSeconds': 12.0, 'maxInputBytes': 1024 * 1024}},
            worker_id='test-worker', max_concurrent=1,
            principal_allowed=lambda uid, org, user: uid == os.getuid() and org == 'org-local' and bool(user),
        )
        self.server._active = True
        self.server._processor_thread = _ThreadPresent()
        self.addCleanup(self._close_server)

    def _close_server(self):
        stop = getattr(self, 'stop', None)
        thread = getattr(self, 'serve_thread', None)
        if stop is not None:
            stop.set()
        if thread is not None:
            thread.join(timeout=3)
        if getattr(self, 'server', None) is not None:
            try:
                self.server.close()
            except Exception:
                pass

    def _test_child_runner(self, argv):
        self.assertEqual(argv[0], sys.executable)
        self.assertEqual(argv[1:3], ['-m', rpc._CHILD_MODULE])
        task_id = argv[argv.index('--task-id') + 1]
        try:
            adapter.executer_une_fois(self.server.task_root, task_id, self.server.engines)
        except BaseException:
            return 1
        return 0

    def _process_one(self):
        # Les tests historiques utilisent un moteur synthétique. Seul ce transport
        # est remplacé ici; un test distinct lance le vrai superviser en enfant.
        with mock.patch.object(rpc, '_run_child_process', side_effect=self._test_child_runner):
            return self.server.process_one()

    def _plan(self, config, run: Path) -> str:
        self.calls.append('plan')
        self.assertEqual(config['provenance_sha256'], sha((run / 'provenance-entrees.json').read_bytes()))
        body = json.dumps({'plan': 'synthetic-no-model', 'provenance': config['provenance_sha256']},
                          sort_keys=True, separators=(',', ':')) + '\n'
        path = run / adapter.PLAN_NAME
        fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
        with os.fdopen(fd, 'w', encoding='utf-8') as out:
            out.write(body)
        return sha(body.encode())

    def _execute(self, run: Path, plan_sha: str) -> dict:
        self.calls.append('execute')
        self.assertEqual((run / 'video-entree.mp4').read_bytes(), self.video_bytes)
        self.assertEqual((run / 'audio-entree.wav').read_bytes(), self.audio_bytes)
        output = b'synthetic no-model output'
        output_sha = sha(output)
        out_path = run / 'sortie.mp4'
        fd = os.open(out_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
        with os.fdopen(fd, 'wb') as out:
            out.write(output)
        receipt = {'plan_sha256': plan_sha, 'statut': 'av_valide_non_juge',
                   'av': {'valide': True}, 'sortie_sha256': output_sha}
        receipt_path = run / 'validation-av.json'
        fd = os.open(receipt_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
        with os.fdopen(fd, 'w', encoding='utf-8') as out:
            json.dump(receipt, out)
        return {'statut': 'av_valide_non_juge', 'sortie_sha256': output_sha}

    def request_body(self, job_id=None):
        job_id = job_id or str(uuid.uuid4())
        video = {'takeId': 17, 'path': '/pc6/path-that-is-not-used/video.mp4',
                 'sha256': sha(self.video_bytes), 'bytes': len(self.video_bytes),
                 'durationSeconds': 1.0, 'fps': 25.0}
        audio = {'takeId': 29, 'path': '/pc6/path-that-is-not-used/audio.wav',
                 'sha256': sha(self.audio_bytes), 'bytes': len(self.audio_bytes),
                 'durationSeconds': 1.0, 'sampleRate': 16000}
        return {'schema': 'nexora.sync.worker-request.v1', 'jobId': job_id,
                'engine': 'musetalk', 'organisationId': 'org-local', 'createdBy': 'user-local',
                'video': video, 'audio': audio,
                'manifest': {'schema': 'nexora.sync.job.v1', 'id': job_id,
                             'engine': 'musetalk', 'videoTakeId': 17, 'audioTakeId': 29,
                             'inputs': {'videoSha256': video['sha256'], 'audioSha256': audio['sha256']},
                             'state': 'dispatching', 'researchOnly': True,
                             'productAvailable': False, 'humanReview': 'pending',
                             'quality': 'not_evaluated'}}

    def _http(self, method, path, body=None, raw_body=None):
        left, right = socket.socketpair()
        def handle():
            with right:
                self.server.handle_connection(right)
        thread = threading.Thread(target=handle)
        thread.start()
        left.settimeout(3)
        if raw_body is not None:
            payload = raw_body
        elif body is None:
            payload = b''
        else:
            payload = json.dumps(body, separators=(',', ':'), allow_nan=False).encode()
        headers = (f'{method} {path} HTTP/1.1\r\nHost: local\r\nAccept: application/json\r\n'
                   + (f'Content-Type: application/json\r\nContent-Length: {len(payload)}\r\n' if payload else '')
                   + '\r\n').encode() + payload
        left.sendall(headers)
        left.shutdown(socket.SHUT_WR)
        response = bytearray()
        while True:
            chunk = left.recv(4096)
            if not chunk:
                break
            response.extend(chunk)
        left.close()
        thread.join(timeout=3)
        self.assertFalse(thread.is_alive())
        header, data = bytes(response).split(b'\r\n\r\n', 1)
        status = int(header.split(b' ', 2)[1])
        return status, json.loads(data)

    def test_durable_queue_ack_happens_before_manual_planning_and_completion_is_rnd_only(self):
        self.server._active = True
        request = self.request_body()
        status, ack = self._http('POST', '/jobs', request)
        self.assertEqual(status, 202)
        self.assertEqual(ack, {'accepted': True, 'jobId': request['jobId']})
        self.assertEqual(self.calls, [])
        self.assertEqual(self.server.inspect(request['jobId']),
                         (200, {'state': 'queued'}))
        row = self.server._lookup(request['jobId'])
        self.assertEqual(row[10], 'queued')
        self.assertEqual(row[18], 1)
        self.assertNotIn(request['video']['path'], row[2])
        self.assertNotIn(request['audio']['path'], row[2])

        self.assertEqual(self._process_one(), request['jobId'])
        self.assertEqual(self.calls, ['plan', 'execute'])
        status, observed = self.server.inspect(request['jobId'])
        self.assertEqual(status, 200)
        self.assertEqual(observed['state'], 'completed')
        result = observed['result']
        self.assertEqual(result['schema'], 'nexora.sync.worker-result.v1')
        self.assertEqual(result['avStatus'], 'pass')
        self.assertTrue(result['researchOnly'])
        self.assertFalse(result['productAvailable'])
        self.assertEqual(self._process_one(), None)

    def test_unacknowledged_durable_row_is_not_visible_or_plannable(self):
        request = self.request_body()
        status, ack = self.server.enqueue(request, os.getuid())
        self.assertEqual((status, ack['accepted']), (202, True))
        self.assertEqual(self.server._lookup(request['jobId'])[18], 0)
        self.assertEqual(self.server.inspect(request['jobId']),
                         (503, {'state': 'unknown', 'errorCode': 'acceptance_unconfirmed'}))
        self.assertIsNone(self._process_one())
        self.assertEqual(self.calls, [])
        # A retry can receive the same durable ACK; path differences are ignored.
        request['video']['path'] = '/pc1/actual/private/location/video.mp4'
        status, ack = self.server.enqueue(request, os.getuid())
        self.assertEqual((status, ack), (202, {'accepted': True, 'jobId': request['jobId']}))
        self.server._acknowledge(request['jobId'])
        self.assertEqual(self._process_one(), request['jobId'])

    def test_ack_loss_row_survives_reopen_and_same_request_can_be_acknowledged(self):
        request = self.request_body()
        status, ack = self.server.enqueue(request, os.getuid())
        self.assertEqual((status, ack['accepted']), (202, True))
        job_id = request['jobId']
        self.assertEqual(self.server.inspect(job_id)[0], 503)
        resolver, engines, limits = self.records, self.server.engines, self.server.engine_limits
        self.server.close()
        self.server = SyncWorkerRpc(
            self.state_root, self.socket_root / 's', (self.media_root,), resolver,
            engines, limits, worker_id='test-worker', max_concurrent=1,
            principal_allowed=lambda uid, org, user: uid == os.getuid() and org == 'org-local' and bool(user),
        )
        self.server._active = True
        self.server._processor_thread = _ThreadPresent()
        self.assertEqual(self.server.inspect(job_id),
                         (503, {'state': 'unknown', 'errorCode': 'acceptance_unconfirmed'}))
        retry_status, retry_ack = self.server.enqueue(request, os.getuid())
        self.assertEqual((retry_status, retry_ack), (202, {'accepted': True, 'jobId': job_id}))
        self.assertEqual(self.calls, [])
        self.server._acknowledge(job_id)
        self.assertEqual(self._process_one(), job_id)
        self.assertEqual(self.calls, ['plan', 'execute'])

    def test_http_capabilities_and_private_socket_modes(self):
        stop = threading.Event()
        self.stop = stop
        self.serve_thread = threading.Thread(target=self.server.serve_forever, args=(stop,))
        self.serve_thread.start()
        deadline = time.monotonic() + 3
        while not self.server.socket_path.exists() and time.monotonic() < deadline:
            time.sleep(0.01)
        st = self.server.socket_path.lstat()
        self.assertTrue(stat.S_ISSOCK(st.st_mode))
        self.assertEqual(stat.S_IMODE(st.st_mode), 0o600)
        self.assertEqual(stat.S_IMODE(self.socket_root.stat().st_mode), 0o700)
        client = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        client.connect(str(self.server.socket_path))
        client.sendall(b'GET /capabilities HTTP/1.1\r\nHost: local\r\n\r\n')
        response = bytearray()
        while True:
            chunk = client.recv(4096)
            if not chunk:
                break
            response.extend(chunk)
        client.close()
        header, body = bytes(response).split(b'\r\n\r\n', 1)
        self.assertIn(b' 200 ', header)
        caps = json.loads(body)
        self.assertEqual(caps['protocol'], 'nexora.sync.worker.v1')
        self.assertEqual(caps['workerId'], 'test-worker')
        self.assertTrue(caps['ready'])
        self.assertEqual(set(caps['engines']), {'musetalk'})
        stop.set()
        self.serve_thread.join(timeout=3)
        self.assertFalse(self.serve_thread.is_alive())
        self.stop = None
        self.serve_thread = None

    def test_registry_metadata_not_client_path_is_authority(self):
        self.server._active = True
        request = self.request_body()
        request['video']['path'] = '/not/on/this/host/and/never/opened'
        status, payload = self._http('POST', '/jobs', request)
        self.assertEqual(status, 202)
        self.assertTrue(payload['accepted'])
        self._process_one()
        row = self.server._lookup(request['jobId'])
        self.assertNotIn('/not/on/this/host', row[2])
        self.assertEqual((self.server.task_root / f"sync-{request['jobId']}" / 'video-entree.mp4').read_bytes(),
                         self.video_bytes)

    def test_mismatched_hash_or_size_refuses_without_queueing(self):
        self.server._active = True
        request = self.request_body()
        request['video']['sha256'] = '0' * 64
        request['manifest']['inputs']['videoSha256'] = request['video']['sha256']
        status, payload = self._http('POST', '/jobs', request)
        self.assertEqual(status, 200)
        self.assertFalse(payload['accepted'])
        self.assertEqual(payload['errorCode'], 'input_rejected')
        self.assertIsNone(self.server._lookup(request['jobId']))
        self.assertEqual(self.calls, [])

    def test_engine_without_bound_capsule_is_refused_before_resolution(self):
        request = self.request_body()
        request['engine'] = 'latentsync'
        request['manifest']['engine'] = 'latentsync'
        original = self.server.resolver.verifier_assertions
        self.server.resolver.verifier_assertions = lambda _req: self.fail('resolver must not run')
        status, payload = self._http('POST', '/jobs', request)
        self.assertEqual(status, 200)
        self.assertFalse(payload['accepted'])
        self.assertEqual(payload['errorCode'], 'engine_unavailable')
        self.assertIsNone(self.server._lookup(request['jobId']))
        self.server.resolver.verifier_assertions = original

    def test_duplicate_idempotency_is_same_job_and_changed_request_conflicts(self):
        request = self.request_body()
        first = self._http('POST', '/jobs', request)
        second = self._http('POST', '/jobs', request)
        self.assertEqual(first, second)
        self.assertEqual(first[1]['jobId'], request['jobId'])
        self.assertEqual(self.server._db.execute('SELECT COUNT(*) FROM jobs').fetchone()[0], 1)
        changed = self.request_body(request['jobId'])
        changed['createdBy'] = 'another-local-user'
        status, payload = self._http('POST', '/jobs', changed)
        self.assertEqual(status, 409)
        self.assertFalse(payload['accepted'])
        self.assertEqual(self.server._db.execute('SELECT COUNT(*) FROM jobs').fetchone()[0], 1)

    def test_dispatch_unknown_is_never_selected_for_automatic_replay(self):
        request = self.request_body()
        status, _ = self._http('POST', '/jobs', request)
        self.assertEqual(status, 202)
        original_execute = self.binding_execute = self.server.engines['musetalk'].executer
        def uncertain(_run, _plan):
            self.calls.append('execute-uncertain')
            raise adapter.DispatchAmbigu('synthetic ambiguous dispatch')
        binding = self.server.engines['musetalk']
        self.server.engines = {'musetalk': adapter.Moteur(binding.configuration, binding.planifier, uncertain)}
        self.assertEqual(self._process_one(), request['jobId'])
        self.assertEqual(self.server.inspect(request['jobId']),
                         (200, {'state': 'dispatch_unknown', 'errorCode': 'engine_failed'}))
        self.assertIsNone(self._process_one())
        self.assertEqual(self.calls.count('execute-uncertain'), 1)

    def test_dispatch_unknown_without_error_is_running_only_while_execution_is_unconfirmed(self):
        request = self.request_body()
        status, _ack = self._http('POST', '/jobs', request)
        self.assertEqual(status, 202)
        self.server._transaction(lambda: self.server._db.execute(
            "UPDATE jobs SET state='dispatch_unknown',error_code=NULL WHERE job_id=?",
            (request['jobId'],)))
        self.assertEqual(self.server.inspect(request['jobId']),
                         (200, {'state': 'running', 'progress': 0}))

    def _run_child_before_preparation(self, run: Path, task_id: str) -> int:
        argv = [sys.executable, '-m', rpc._CHILD_MODULE, '--execute-task',
                '--task-root', str(self.server.task_root), '--task-id', task_id,
                '--engine', 'musetalk', '--plan-sha256', '0' * 64]
        return rpc._run_child_process(argv)

    def test_child_preexecution_failure_writes_private_bounded_diagnostic(self):
        task_id = str(uuid.uuid4())
        run = self.server.task_root / f'sync-{task_id}'
        run.mkdir(mode=0o700)

        status = self._run_child_before_preparation(run, task_id)

        self.assertEqual(status, 1)
        receipt_path = run / CHILD_ERROR_RECEIPT_NAME
        self.assertTrue(receipt_path.is_file())
        receipt = json.loads(receipt_path.read_text(encoding='ascii'))
        self.assertEqual(receipt['schema'], 'nexora.sync.worker-child-error.v1')
        self.assertEqual(receipt['exceptionClass'], 'ErreurTache')
        self.assertLessEqual(len(receipt['frames']), 12)
        self.assertTrue(any(frame['function'] == '_executer_tache_enfant'
                            for frame in receipt['frames']))
        self.assertTrue(all(set(frame) == {'file', 'function', 'line'} and
                            isinstance(frame['line'], int) and frame['line'] > 0
                            for frame in receipt['frames']))
        details = json.dumps(receipt)
        self.assertNotIn(str(self.state_root), details)
        self.assertNotIn('message', receipt)
        st = receipt_path.stat(follow_symlinks=False)
        self.assertEqual(stat.S_IMODE(st.st_mode), 0o600)
        self.assertEqual(st.st_uid, os.getuid())
        self.assertEqual(st.st_nlink, 1)

    def test_child_diagnostic_is_exclusive_and_preserves_existing_receipt(self):
        task_id = str(uuid.uuid4())
        run = self.server.task_root / f'sync-{task_id}'
        run.mkdir(mode=0o700)
        receipt_path = run / CHILD_ERROR_RECEIPT_NAME
        sentinel = b'previous private receipt\n'
        receipt_path.write_bytes(sentinel)
        receipt_path.chmod(0o600)

        status = self._run_child_before_preparation(run, task_id)

        self.assertEqual(status, 1)
        self.assertEqual(receipt_path.read_bytes(), sentinel)

    def test_real_supervisor_installs_signals_in_dedicated_python_main_thread(self):
        run = self.case / 'signal-child-run'
        run.mkdir(mode=0o700)
        code = '\n'.join((
            'import os, sys, threading',
            'from pathlib import Path',
            'from outils.sync.labo.supervision_capsule import superviser',
            'run = Path(sys.argv[1])',
            'assert threading.current_thread() is threading.main_thread()',
            "lock_fd = os.open(run / 'lock', os.O_RDWR | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)",
            'read_fd, write_fd = os.pipe()',
            "argv = [sys.executable, '-c', 'pass', '--sync-fd', str(lock_fd),",
            "        '--json-status-fd', str(write_fd), '--', 'cpu-probe']",
            'bilan = superviser(argv, run, lock_fd, read_fd, write_fd, 2)',
            "assert bilan['phase'] == 'termine', bilan",
            "assert 'erreur' not in bilan, bilan",
            "fd = os.open(run / 'signal-handler-ok', os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)",
            "os.write(fd, b'ok')",
            'os.close(fd)',
            'os.close(lock_fd)',
        ))
        status = rpc._run_child_process([sys.executable, '-c', code, str(run)])
        self.assertEqual(status, 0)
        self.assertEqual((run / 'signal-handler-ok').read_bytes(), b'ok')
        result = json.loads((run / 'resultat-execution.json').read_text(encoding='utf-8'))
        self.assertEqual(result['phase'], 'termine')
        self.assertNotIn('erreur', result)
        self.assertFalse(result['arret_confirmé'])

    def test_bad_json_duplicate_keys_and_unexpected_paths_do_not_accept_job(self):
        body = json.dumps(self.request_body(), separators=(',', ':'))
        duplicate = body[:-1] + ',"jobId":"' + str(uuid.uuid4()) + '"}'
        status, payload = self._http('POST', '/jobs', raw_body=duplicate.encode())
        self.assertEqual(status, 400)
        self.assertFalse(payload['accepted'])
        self.assertEqual(self.server._db.execute('SELECT COUNT(*) FROM jobs').fetchone()[0], 0)
        status, payload = self._http('GET', '/jobs/not-a-uuid')
        self.assertEqual((status, payload), (200, {'state': 'not_found'}))

    def test_engine_duration_and_byte_limits_reject_before_registry_or_insert(self):
        original = self.server.resolver.verifier_assertions
        self.server.resolver.verifier_assertions = lambda _req: self.fail('registry must not run after limit refusal')
        request = self.request_body()
        self.server.engine_limits['musetalk']['maxInputBytes'] = len(self.video_bytes) - 1
        status, payload = self._http('POST', '/jobs', request)
        self.assertEqual(status, 200)
        self.assertFalse(payload['accepted'])
        self.assertEqual(payload['errorCode'], 'input_rejected')
        self.assertIsNone(self.server._lookup(request['jobId']))

        self.server.engine_limits['musetalk']['maxInputBytes'] = 1024 * 1024
        self.server.engine_limits['musetalk']['maxDurationSeconds'] = 0.5
        request = self.request_body()
        status, payload = self._http('POST', '/jobs', request)
        self.assertEqual(status, 200)
        self.assertFalse(payload['accepted'])
        self.assertEqual(payload['errorCode'], 'input_rejected')
        self.assertIsNone(self.server._lookup(request['jobId']))
        self.assertEqual(self.calls, [])
        self.server.resolver.verifier_assertions = original

    def _generic_server_media_run(self, engine):
        run = self.case / f'actual-plan-{engine}-{uuid.uuid4().hex}'
        run.mkdir(mode=0o700)
        for name, data in ((media_sync.VIDEO_NAME, self.video_bytes),
                           (media_sync.AUDIO_NAME, self.audio_bytes)):
            path = run / name
            path.write_bytes(data)
            path.chmod(0o600)
        provenance_sha = media_sync.ecrire_provenance_serveur(run, 17, 29)
        cfg = {
            'python': '/synthetic/bin/python', 'ffmpeg': '/synthetic/bin/ffmpeg',
            'ffprobe': '/synthetic/bin/ffprobe', 'bwrap': '/synthetic/bin/bwrap',
            'gpu_uuid': 'GPU-SYNTHETIC', 'nvidia_smi': '/synthetic/bin/nvidia-smi',
            'executables_sha256': {name: '0' * 64 for name in
                                   ('python', 'ffmpeg', 'ffprobe', 'bwrap', 'nvidia_smi')},
            'provenance_sha256': provenance_sha,
        }
        if engine == 'musetalk':
            cfg.update({
                'runtime': str(run / 'runtime'),
                'runtime_manifest': str(run / 'runtime-manifest.json'),
                'runtime_manifest_sha256': '0' * 64,
                'models': str(run / 'models'),
                'gpu_lock': str(run / 'gpu.lock'),
            })
        else:
            runtime = run / 'runtime'
            runtime.mkdir(mode=0o700)
            marker = runtime / 'fixture.py'
            marker.write_text('# synthetic runtime marker\n', encoding='utf-8')
            manifest = {'runtime': str(runtime), 'runtime_sha256': {'fixture.py': sha(marker.read_bytes())}}
            manifest_path = run / 'runtime-manifest.json'
            manifest_path.write_text(json.dumps(manifest), encoding='utf-8')
            vae = str(run / 'weights' / 'vae')
            unet = str(run / 'weights' / 'unet.pth')
            cfg.update({
                'runtime': str(runtime), 'runtime_manifest': str(manifest_path),
                'runtime_manifest_sha256': sha(manifest_path.read_bytes()),
                'poids_sha256': {
                    unet: '0' * 64,
                    str(Path(vae) / 'config.json'): '0' * 64,
                    str(Path(vae) / 'diffusion_pytorch_model.bin'): '0' * 64,
                },
                'unet': unet, 'vae': vae,
            })
        return run, cfg

    def _run_real_planner_with_synthetic_preflight(self, module, engine):
        run, config = self._generic_server_media_run(engine)
        preflight_result = {'source': 'generic-server-media', 'synthetic_inputs_only': True}
        preflight_owner = latentsync_execution if engine == 'musetalk' else module
        with (
            mock.patch.object(module, '_commande', return_value=[]),
            mock.patch.object(preflight_owner, '_prevol', return_value={'gpu': 'not-read-in-test'}),
            mock.patch.object(highsync_preflight, '_verifier_fichier'),
            mock.patch.object(highsync_preflight, 'preflight', return_value=preflight_result),
            mock.patch.object(capsule_sync, '_exe'),
            mock.patch.object(media_sync, 'verifier_provenance', wraps=media_sync.verifier_provenance) as verify_provenance,
        ):
            if module is musetalk_execution:
                runtime_patch = mock.patch.object(module, '_verifier_runtime')
            else:
                runtime_patch = mock.patch.object(module, '_gpu_initial', return_value={'synthetic': True})
            with runtime_patch:
                plan_sha = module.planifier(config, run)
        self.assertEqual(verify_provenance.call_count, 1)
        plan_path = run / ('plan-execution.json')
        plan = json.loads(plan_path.read_text(encoding='utf-8'))
        self.assertEqual(sha(plan_path.read_bytes()), plan_sha)
        self.assertEqual(plan['entrees_av'], preflight_result)
        self.assertFalse(plan['voix_validee_humain'])
        return run, plan

    def test_musetalk_real_planifier_accepts_server_media_provenance(self):
        run, plan = self._run_real_planner_with_synthetic_preflight(musetalk_execution, 'musetalk')
        provenance = json.loads((run / 'provenance-entrees.json').read_text(encoding='utf-8'))
        self.assertEqual(provenance['schema'], media_sync.SCHEMA_SERVER_MEDIA)
        self.assertEqual(plan['configuration']['provenance_sha256'], sha((run / 'provenance-entrees.json').read_bytes()))
        self.assertTrue((run / musetalk_execution.TASK_YAML).is_file())

    def test_latentsync_real_planifier_accepts_server_media_provenance(self):
        run, plan = self._run_real_planner_with_synthetic_preflight(latentsync_execution, 'latentsync')
        provenance = json.loads((run / 'provenance-entrees.json').read_text(encoding='utf-8'))
        self.assertEqual(provenance['schema'], media_sync.SCHEMA_SERVER_MEDIA)
        self.assertEqual(plan['configuration']['provenance_sha256'], sha((run / 'provenance-entrees.json').read_bytes()))


if __name__ == '__main__':
    unittest.main()
