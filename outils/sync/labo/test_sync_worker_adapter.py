from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import tempfile
import unittest
import uuid
from unittest import mock

from outils.sync.labo import media_sync, sync_worker_adapter as worker


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


class WorkerAdapterTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        root_value = os.environ.get('SYNC_TEST_ROOT')
        if not root_value:
            raise RuntimeError('SYNC_TEST_ROOT doit pointer vers un dossier Storage explicite')
        cls.test_root = Path(root_value)
        if cls.test_root.is_symlink() or not cls.test_root.is_dir():
            raise RuntimeError('SYNC_TEST_ROOT doit exister et ne pas être un lien')

    def setUp(self):
        self.case = self.test_root / f'case-{self._testMethodName}-{uuid.uuid4().hex}'
        self.case.mkdir(mode=0o700)
        self.media_root = self.case / 'resolved-media'
        self.media_root.mkdir(mode=0o700)
        self.task_root = self.case / 'tasks'
        self.task_root.mkdir(mode=0o700)
        self.video_bytes = b'private synthetic video fixture\x00\x01'
        self.audio_bytes = b'private synthetic audio fixture\x02\x03'
        self.video_path = self.media_root / 'video-take-17.mp4'
        self.audio_path = self.media_root / 'audio-take-29.wav'
        self.video_path.write_bytes(self.video_bytes)
        self.audio_path.write_bytes(self.audio_bytes)
        self.media = worker.MediasResolus(
            worker.PriseResolue(17, self.video_path, sha(self.video_bytes), len(self.video_bytes)),
            worker.PriseResolue(29, self.audio_path, sha(self.audio_bytes), len(self.audio_bytes)),
        )
        self.calls = []
        self.binding = worker.Moteur(
            configuration={'profile': 'server-owned-test-binding'},
            planifier=self._fake_plan,
            executer=self._fake_execute,
        )
        self.engines = {'musetalk': self.binding, 'latentsync': self.binding}

    def _fake_plan(self, config, run: Path) -> str:
        self.calls.append(('plan', dict(config)))
        body = json.dumps({'statut': 'planifie_sans_inference',
                           'provenance_sha256': config['provenance_sha256']},
                          sort_keys=True, separators=(',', ':')) + '\n'
        plan_path = run / worker.PLAN_NAME
        plan_path.write_text(body, encoding='utf-8')
        plan_path.chmod(0o600)
        return sha(body.encode())

    def _fake_execute(self, run: Path, plan_sha: str) -> dict:
        self.calls.append(('execute', plan_sha))
        output = b'synthetic no-model output fixture'
        (run / 'sortie.mp4').write_bytes(output)
        output_sha = sha(output)
        receipt = {'plan_sha256': plan_sha, 'statut': 'av_valide_non_juge',
                   'av': {'valide': True}, 'sortie_sha256': output_sha}
        receipt_path = run / 'validation-av.json'
        receipt_path.write_text(json.dumps(receipt), encoding='utf-8')
        receipt_path.chmod(0o600)
        return {'statut': 'av_valide_non_juge', 'sortie_sha256': output_sha}

    def _prepare(self, task_id='job-01', engine='musetalk'):
        return worker.preparer_tache(self.task_root, (self.media_root,), self.media,
                                     task_id, engine, self.engines)

    def _state(self, run_dir: str) -> dict:
        return json.loads((Path(run_dir) / worker.TASK_STATE).read_text(encoding='utf-8'))

    def test_server_media_provenance_is_separate_from_eleven4(self):
        prepared = self._prepare()
        run = Path(prepared['run_dir'])
        provenance = json.loads((run / 'provenance-entrees.json').read_text(encoding='utf-8'))
        self.assertEqual(provenance['schema'], media_sync.SCHEMA_SERVER_MEDIA)
        self.assertEqual(provenance['source_ids'], {'video': 17, 'audio': 29})
        self.assertEqual(set(provenance), {'schema', 'source_ids', 'fichiers'})
        self.assertNotIn('modele_demande', provenance)
        self.assertNotIn('voix', provenance)
        self.assertFalse((run / 'audio-original.mp3').exists())
        task_record = json.loads((run / worker.TASK_STATE).read_text(encoding='utf-8'))
        self.assertNotIn('modele_demande', task_record)
        self.assertNotIn('voix', task_record)
        self.assertNotIn(str(self.video_path), json.dumps(task_record))
        self.assertEqual(media_sync.verifier_provenance(
            run, sha((run / 'provenance-entrees.json').read_bytes()))[0], 'server-media')
        self.assertEqual((run / media_sync.VIDEO_NAME).read_bytes(), self.video_bytes)
        self.assertEqual((run / media_sync.AUDIO_NAME).read_bytes(), self.audio_bytes)

    def test_eleven4_bench_provenance_branch_is_preserved(self):
        run = self.case / 'eleven4-bench-fixture'
        run.mkdir(mode=0o700)
        files = {'audio-original.mp3': b'original requested sample',
                 media_sync.AUDIO_NAME: b'pcm fixture', media_sync.VIDEO_NAME: b'video fixture'}
        for name, data in files.items():
            (run / name).write_bytes(data)
        provenance = {'modele_demande': media_sync.ELEVEN4,
                      'fichiers': {name: sha(data) for name, data in files.items()}}
        payload = json.dumps(provenance, sort_keys=True).encode()
        (run / 'provenance-entrees.json').write_bytes(payload)
        kind, hashes = media_sync.verifier_provenance(
            run, hashlib.sha256(payload).hexdigest())
        self.assertEqual(kind, 'eleven4-bench')
        self.assertIn('audio-original.mp3', hashes)

    def test_source_outside_resolved_roots_is_refused_before_plan(self):
        outsider = self.case / 'outside.mp4'
        outsider.write_bytes(self.video_bytes)
        outside = worker.MediasResolus(
            worker.PriseResolue(18, outsider, sha(self.video_bytes), len(self.video_bytes)),
            self.media.audio)
        with self.assertRaises(worker.ErreurTache):
            worker.preparer_tache(self.task_root, (self.media_root,), outside,
                                  'outside-01', 'musetalk', self.engines)
        self.assertEqual(self.calls, [])

    def test_source_hash_change_is_refused_before_plan(self):
        wrong = worker.MediasResolus(
            worker.PriseResolue(17, self.video_path, '0' * 64, len(self.video_bytes)),
            self.media.audio)
        with self.assertRaises(worker.ErreurTache):
            worker.preparer_tache(self.task_root, (self.media_root,), wrong,
                                  'hash-01', 'latentsync', self.engines)
        self.assertEqual(self.calls, [])
        state = json.loads((self.task_root / 'sync-hash-01' / worker.TASK_STATE).read_text())
        self.assertEqual(state['status'], 'preparation_failed')

    def test_symlink_source_is_refused(self):
        link = self.media_root / 'linked.mp4'
        link.symlink_to(self.video_path)
        media = worker.MediasResolus(
            worker.PriseResolue(20, link, sha(self.video_bytes), len(self.video_bytes)),
            self.media.audio)
        with self.assertRaises((worker.ErreurTache, OSError)):
            worker.preparer_tache(self.task_root, (self.media_root,), media,
                                  'link-01', 'musetalk', self.engines)
        self.assertEqual(self.calls, [])

    def test_client_cannot_supply_unknown_engine_or_task_path(self):
        with self.assertRaises(worker.ErreurTache):
            worker.preparer_tache(self.task_root, (self.media_root,), self.media,
                                  '../escape', 'musetalk', self.engines)
        with self.assertRaises(worker.ErreurTache):
            worker.preparer_tache(self.task_root, (self.media_root,), self.media,
                                  'bad-engine-01', 'unlisted-engine', self.engines)
        self.assertEqual(self.calls, [])

    def test_execute_rejects_traversal_id_before_touching_task_root(self):
        with mock.patch.object(worker, '_trusted_dir', side_effect=AssertionError('filesystem touched')):
            with self.assertRaises(worker.ErreurTache):
                worker.executer_une_fois(Path('/never-open-this-root'), '../escape', self.engines)

    def test_source_fd_is_closed_when_exclusive_destination_open_fails(self):
        destination = self.case / 'already-exists.mp4'
        destination.write_bytes(b'keep this destination')
        opened = []
        original_open = worker._ouvrir_prise

        def capture_open(*args, **kwargs):
            fd = original_open(*args, **kwargs)
            opened.append(fd)
            return fd

        with mock.patch.object(worker, '_ouvrir_prise', side_effect=capture_open):
            with self.assertRaises(FileExistsError):
                worker._copier_prise(self.media.video, (self.media_root,), destination)
        self.assertEqual(destination.read_bytes(), b'keep this destination')
        with self.assertRaises(OSError):
            os.fstat(opened[0])

    def test_zero_byte_write_raises_and_closes_source_fd(self):
        destination = self.case / 'write-zero.mp4'
        opened = []
        original_open = worker._ouvrir_prise

        def capture_open(*args, **kwargs):
            fd = original_open(*args, **kwargs)
            opened.append(fd)
            return fd

        with mock.patch.object(worker, '_ouvrir_prise', side_effect=capture_open):
            with mock.patch.object(worker.os, 'write', return_value=0):
                with self.assertRaisesRegex(OSError, 'écriture de prise interrompue'):
                    worker._copier_prise(self.media.video, (self.media_root,), destination)
        with self.assertRaises(OSError):
            os.fstat(opened[0])

    def test_worker_resolves_server_ids_before_creating_any_task(self):
        seen = []

        def resolver(video_id, audio_id):
            seen.append((video_id, audio_id))
            return self.media

        prepared = worker.preparer_depuis_ids(self.task_root, (self.media_root,),
            17, 29, 'resolved-01', 'latentsync', self.engines, resolver)
        self.assertEqual(seen, [(17, 29)])
        self.assertEqual(prepared['status'], 'prepared')

        denied_root = self.case / 'denied-tasks'
        denied_root.mkdir(mode=0o700)

        def deny(_video_id, _audio_id):
            raise PermissionError('synthetic ACL refusal')

        with self.assertRaises(PermissionError):
            worker.preparer_depuis_ids(denied_root, (self.media_root,),
                17, 29, 'denied-01', 'musetalk', self.engines, deny)
        self.assertFalse((denied_root / 'sync-denied-01').exists())
        with self.assertRaises(worker.ErreurTache):
            worker.preparer_depuis_ids(denied_root, (self.media_root,),
                17, 29, 'unavailable-01', 'highsync', self.engines, deny)
        self.assertFalse((denied_root / 'sync-unavailable-01').exists())

    def test_capsule_bindings_use_only_the_explicitly_enabled_engines(self):
        linked = worker.lier_capsules({'musetalk': {'trusted': True},
                                       'latentsync': {'trusted': True}})
        self.assertEqual(set(linked), {'musetalk', 'latentsync'})
        self.assertEqual(linked['musetalk'].planifier.__module__,
                         'outils.sync.labo.musetalk_execution')
        self.assertEqual(linked['latentsync'].executer.__module__,
                         'outils.sync.labo.latentsync_execution')
        self.assertEqual(set(worker.lier_capsules({'musetalk': {'trusted': True}})), {'musetalk'})
        with self.assertRaises(worker.ErreurTache):
            worker.lier_capsules({})

    def test_completed_result_requires_matching_receipt_and_output_hash(self):
        prepared = self._prepare()
        result = worker.executer_une_fois(self.task_root, prepared['task_id'], self.engines)
        self.assertEqual(result['status'], 'av_validated_unjudged')
        self.assertEqual(self._state(prepared['run_dir'])['status'], 'av_validated_unjudged')
        self.assertEqual(len([c for c in self.calls if c[0] == 'execute']), 1)
        with self.assertRaises(worker.DispatchAmbigu):
            worker.executer_une_fois(self.task_root, prepared['task_id'], self.engines)

    def test_executor_exception_persists_ambiguous_dispatch_without_retry(self):
        prepared = self._prepare()
        calls = []

        def ambiguous(_run, _plan_sha):
            calls.append('called')
            self.assertEqual(self._state(prepared['run_dir'])['status'], 'dispatch_unknown')
            raise TimeoutError('synthetic timeout; no transport details stored')

        engines = {'musetalk': worker.Moteur(self.binding.configuration,
                                             self.binding.planifier, ambiguous)}
        with self.assertRaises(worker.DispatchAmbigu):
            worker.executer_une_fois(self.task_root, prepared['task_id'], engines)
        state = self._state(prepared['run_dir'])
        self.assertEqual(state['status'], 'dispatch_unknown')
        self.assertEqual(state['last_error_class'], 'TimeoutError')
        with self.assertRaises(worker.DispatchAmbigu):
            worker.executer_une_fois(self.task_root, prepared['task_id'], engines)
        self.assertEqual(calls, ['called'])

    def test_plan_mutated_after_prepare_is_refused_before_dispatch(self):
        prepared = self._prepare()
        run = Path(prepared['run_dir'])
        (run / worker.PLAN_NAME).write_text('{"changed":true}\n', encoding='utf-8')
        with self.assertRaises(worker.ErreurTache):
            worker.executer_une_fois(self.task_root, prepared['task_id'], self.engines)
        self.assertEqual(self._state(prepared['run_dir'])['status'], 'prepared')
        self.assertFalse(any(c[0] == 'execute' for c in self.calls))

    def test_nonprivate_task_state_is_refused_before_dispatch(self):
        prepared = self._prepare()
        state_path = Path(prepared['run_dir']) / worker.TASK_STATE
        state_path.chmod(0o644)
        with self.assertRaises(worker.ErreurTache):
            worker.executer_une_fois(self.task_root, prepared['task_id'], self.engines)
        self.assertFalse(any(c[0] == 'execute' for c in self.calls))

    def test_state_is_atomically_reprivatized_if_dispatch_then_fails(self):
        prepared = self._prepare()

        def chmod_then_timeout(run, _plan_sha):
            (run / worker.TASK_STATE).chmod(0o644)
            raise TimeoutError('synthetic post-dispatch ambiguity')

        engines = {'musetalk': worker.Moteur(self.binding.configuration,
                                             self.binding.planifier, chmod_then_timeout)}
        with self.assertRaises(worker.DispatchAmbigu):
            worker.executer_une_fois(self.task_root, prepared['task_id'], engines)
        state_path = Path(prepared['run_dir']) / worker.TASK_STATE
        state = json.loads(state_path.read_text(encoding='utf-8'))
        self.assertEqual(state['status'], 'dispatch_unknown')
        self.assertEqual(state['last_error_class'], 'TimeoutError')
        self.assertEqual(state_path.stat().st_mode & 0o777, 0o600)

    def test_malformed_engine_receipt_stays_ambiguous(self):
        prepared = self._prepare()

        def invalid(_run, _plan_sha):
            return {'statut': 'human_approved', 'produit_livre': True}

        engines = {'musetalk': worker.Moteur(self.binding.configuration,
                                             self.binding.planifier, invalid)}
        with self.assertRaises(worker.DispatchAmbigu):
            worker.executer_une_fois(self.task_root, prepared['task_id'], engines)
        self.assertEqual(self._state(prepared['run_dir'])['status'], 'dispatch_unknown')

    def test_existing_task_directory_is_never_overwritten(self):
        prepared = self._prepare()
        with self.assertRaises(FileExistsError):
            self._prepare()
        self.assertEqual(self._state(prepared['run_dir'])['status'], 'prepared')


if __name__ == '__main__':
    unittest.main()
