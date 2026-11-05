#!/usr/bin/env python3
"""Unit tests for assemblage_portable strict manifest validation (no network, no GPU)."""
import copy
import hashlib
import importlib
import json
import os
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
from pathlib import Path

import assemblage_portable as ap

HERE = Path(__file__).resolve().parent
OK_SHA = hashlib.sha256(b'clip').hexdigest()


def base_manifest():
    return {
        'schema': 1,
        'teams': {
            'muse': {
                'status': 'incomplete-review-draft',
                'duration_s': 2.0,
                'language': 'fr',
                'format': '16x9',
                'notes': ['draft'],
                'segments': [
                    {'source_root': 'ui', 'source': 'ui/a.bin', 'sha256': OK_SHA,
                     'start_s': 0.0, 'duration_s': 1.0, 'entry_s': 0.0},
                    {'source_root': 'h3', 'source': 'h3/muse-b.bin', 'sha256': OK_SHA.upper(),
                     'start_s': 1.0, 'duration_s': 1.0, 'sound_db': -6},
                ],
            },
        },
    }


class ManifestValidation(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def load(self, doc, team='muse'):
        path = self.dir / 'manifest.json'
        path.write_text(json.dumps(doc) if not isinstance(doc, str) else doc)
        return ap.load_team(path, team)

    def mutate(self, fn):
        doc = base_manifest()
        fn(doc)
        return doc

    def assert_rejected(self, doc, fragment):
        with self.assertRaises(ValueError) as ctx:
            self.load(doc)
        self.assertIn(fragment, str(ctx.exception))

    def test_valid_manifest_compatible(self):
        raw, doc, team, ordered = self.load(base_manifest())
        self.assertEqual(json.loads(raw)['schema'], 1)
        self.assertEqual(team['status'], 'incomplete-review-draft')
        self.assertEqual([s['start_s'] for s in ordered], [0.0, 1.0])

    def test_bool_refused_as_number(self):
        for field in ('start_s', 'duration_s'):
            doc = self.mutate(lambda d: d['teams']['muse']['segments'][0].__setitem__(field, True))
            self.assert_rejected(doc, field)
        doc = self.mutate(lambda d: d['teams']['muse']['segments'][1].__setitem__('sound_db', False))
        self.assert_rejected(doc, 'sound_db')
        doc = self.mutate(lambda d: d['teams']['muse'].__setitem__('duration_s', True))
        self.assert_rejected(doc, 'duration_s')

    def test_arrays_and_strings_refused_as_numbers(self):
        doc = self.mutate(lambda d: d['teams']['muse']['segments'][0].__setitem__('start_s', '0'))
        self.assert_rejected(doc, 'start_s')
        doc = self.mutate(lambda d: d['teams']['muse']['segments'][0].__setitem__('duration_s', [1.0]))
        self.assert_rejected(doc, 'duration_s')

    def test_non_finite_and_negative(self):
        doc = self.mutate(lambda d: d['teams']['muse']['segments'][0].__setitem__('duration_s', float('nan')))
        self.assert_rejected(doc, 'non finie')
        doc = self.mutate(lambda d: d['teams']['muse']['segments'][0].__setitem__('duration_s', float('inf')))
        self.assert_rejected(doc, 'non finie')
        for field in ('start_s', 'entry_s'):
            doc = self.mutate(lambda d: d['teams']['muse']['segments'][0].__setitem__(field, -0.5))
            self.assert_rejected(doc, field)
        doc = self.mutate(lambda d: d['teams']['muse']['segments'][0].__setitem__('duration_s', 0))
        self.assert_rejected(doc, 'duration_s')

    def test_source_entry_may_exceed_segment_duration(self):
        doc = self.mutate(lambda d: d['teams']['muse']['segments'][0].__setitem__('entry_s', 5.0))
        self.load(doc)

    def test_crop_is_a_list_of_timed_camera_keys(self):
        doc = self.mutate(lambda d: d['teams']['muse']['segments'][0].__setitem__('crop_9x16', [[0, 0.5, 0.5, 1], [1, 0.4, 0.6, 1.1]]))
        self.load(doc)
        doc['teams']['muse']['segments'][0]['crop_9x16'] = {'left': 0}
        self.assert_rejected(doc, 'crop_9x16')

    def test_hash_format(self):
        for bad in ('abc', 'z' * 64, 'a' * 63, 'a' * 65, 123, None):
            doc = self.mutate(lambda d: d['teams']['muse']['segments'][0].__setitem__('sha256', bad))
            self.assert_rejected(doc, 'sha256')

    def test_team_names(self):
        with self.assertRaises(ValueError):
            self.load(base_manifest(), team='other')
        doc = base_manifest()
        doc['teams']['muse']['status'] = 'reviewed'
        self.assert_rejected(doc, 'status')

    def test_language_format_status(self):
        self.assert_rejected(self.mutate(lambda d: d['teams']['muse'].__setitem__('language', 'de')), 'language')
        self.assert_rejected(self.mutate(lambda d: d['teams']['muse'].__setitem__('format', '4x3')), 'format')
        self.assert_rejected(self.mutate(lambda d: d['teams']['muse'].pop('status')), 'status')

    def test_segment_list_shape(self):
        self.assert_rejected(self.mutate(lambda d: d['teams']['muse'].__setitem__('segments', [])), 'segment list')
        self.assert_rejected(self.mutate(lambda d: d['teams']['muse'].__setitem__('segments', 'x')), 'segment list')
        self.assert_rejected(self.mutate(lambda d: d['teams']['muse']['segments'].append('x')), 'objet JSON')

    def test_malformed_json_and_schema(self):
        with self.assertRaises(ValueError):
            self.load('{not json')
        with self.assertRaises(ValueError):
            self.load('[]')
        self.assert_rejected(self.mutate(lambda d: d.__setitem__('schema', True)), 'schema')
        self.assert_rejected(self.mutate(lambda d: d.__setitem__('schema', 2)), 'schema')

    def test_contiguity_and_total(self):
        self.assert_rejected(self.mutate(lambda d: d['teams']['muse']['segments'][1].__setitem__('start_s', 1.5)),
                             'contiguous')
        self.assert_rejected(self.mutate(lambda d: d['teams']['muse'].__setitem__('duration_s', 3.0)),
                             'declared duration')

    def test_paths_relative_and_traversal(self):
        for bad in ('/abs/a.bin', '../a.bin', '', '   ', './a.bin', 'a/../../b.bin'):
            doc = self.mutate(lambda d: d['teams']['muse']['segments'][0].__setitem__('source', bad))
            self.assert_rejected(doc, 'source')
        doc = self.mutate(lambda d: d['teams']['muse']['segments'][0].__setitem__('source', 'ui/./a.bin'))
        self.assert_rejected(doc, 'source')

    def test_rejects_malformed_additional_fields(self):
        for field, value in [('grade', 42), ('crop_9x16', [[0, .5, .5]]),
                             ('crop_9x16', [[0, 2, .5, 1]]),
                             ('source', 'other-team.bin')]:
            doc = base_manifest()
            index = 1 if field == 'source' else 0
            doc['teams']['muse']['segments'][index][field] = value
            self.assert_rejected(doc, field)
        for field, value in [('notes', 'not a list'), ('overlays', {})]:
            doc = self.mutate(lambda d: d['teams']['muse'].__setitem__(field, value))
            self.assert_rejected(doc, field)
        self.assert_rejected(self.mutate(lambda d: d.__setitem__('teams', [])), 'teams')
        self.assert_rejected(self.mutate(lambda d: d['teams'].pop('muse')), 'absent')
        doc = base_manifest()
        doc['teams']['muse']['segments'][0]['duration_s'] = .3
        self.assert_rejected(doc, 'frame grid')

    def test_source_root(self):
        self.assert_rejected(self.mutate(lambda d: d['teams']['muse']['segments'][0].__setitem__('source_root', 'x')),
                             'source_root')


class PathSecurity(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name) / 'root'
        (self.root / 'ui').mkdir(parents=True)
        self.clip = self.root / 'ui' / 'a.bin'
        self.clip.write_bytes(b'clip')
        self.sha = hashlib.sha256(b'clip').hexdigest()

    def tearDown(self):
        self.tmp.cleanup()

    def test_ok(self):
        self.assertEqual(ap.portable_asset(self.root, 'ui/a.bin', self.sha), self.clip.resolve())

    def test_sha_mismatch(self):
        with self.assertRaises(ValueError):
            ap.portable_asset(self.root, 'ui/a.bin', '0' * 64)

    def test_traversal_and_absolute(self):
        outside = Path(self.tmp.name) / 'out.bin'
        outside.write_bytes(b'clip')
        for rel in ('../out.bin', str(outside), 'ui/../../out.bin'):
            with self.assertRaises(ValueError):
                ap.portable_asset(self.root, rel, self.sha)

    def test_symlink_refused(self):
        link = self.root / 'ui' / 'link.bin'
        os.symlink(self.clip, link)
        with self.assertRaises(ValueError):
            ap.portable_asset(self.root, 'ui/link.bin', self.sha)


class NoImportSideEffects(unittest.TestCase):
    def test_import_is_clean(self):
        with tempfile.TemporaryDirectory() as tmp:
            before = set(os.listdir(tmp))
            env = {'HOME': tmp, 'PATH': '/usr/bin:/bin', 'PYTHONPATH': str(HERE.parent), 'PYTHONDONTWRITEBYTECODE': '1'}
            code = 'import assemblage_portable; print("ok")'
            out = subprocess.run([sys.executable, '-B', '-c', code],
                                 cwd=tmp, env=env, capture_output=True, text=True)
            self.assertEqual(out.returncode, 0, out.stderr)
            self.assertEqual(out.stdout.strip(), 'ok')
            self.assertEqual(set(os.listdir(tmp)), before)

    def test_write_new_never_overwrites(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / 'run' / 'file.json'
            ap.write_new(target, b'one')
            with self.assertRaises(FileExistsError):
                ap.write_new(target, b'two')
            self.assertEqual(target.read_bytes(), b'one')


class LocalAssembly(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.ui = self.root / 'ui'
        self.h3 = self.root / 'h3'
        self.ui.mkdir()
        self.h3.mkdir()
        (self.ui / 'clip.bin').write_bytes(b'clip')
        (self.h3 / 'muse-b.bin').write_bytes(b'clip')
        engine_dir = self.root / 'marketing/creative/video-v7'
        engine_dir.mkdir(parents=True)
        (engine_dir / 'monter_v6.py').write_text('')
        self.brand = self.root / 'brand.json'
        self.brand.write_text('{}')
        self.manifest = self.root / 'manifest.json'
        doc = base_manifest()
        doc['teams']['muse']['segments'][0]['source'] = 'clip.bin'
        doc['teams']['muse']['segments'][1]['source'] = 'muse-b.bin'
        doc['teams']['muse']['segments'].reverse()
        self.manifest.write_text(json.dumps(doc))
        self.args = ['assemble', '--manifest', str(self.manifest), '--team', 'muse',
                     '--repo-root', str(self.root), '--ui-root', str(self.ui), '--h3-root', str(self.h3),
                     '--brand-file', str(self.brand), '--output-root', str(self.root / 'out'),
                     '--home', str(self.root)]

    def tearDown(self):
        self.tmp.cleanup()

    def test_validation_writes_sorted_montage_and_provenance(self):
        with patch.object(sys, 'argv', self.args), patch.object(ap, 'validate_with_engine', return_value=self.root / 'engine.py'):
            ap.main()
        run = next((self.root / 'out').iterdir())
        montage = json.loads((run / 'montage.json').read_text())
        provenance = json.loads((run / 'provenance.json').read_text())
        status = json.loads((run / 'status.json').read_text())
        self.assertEqual([item['debut'] for item in montage['segments']], [0, 1])
        self.assertEqual(provenance['human_judgment'], 'not performed')
        self.assertEqual(status['status'], 'validated-not-rendered')

    def test_vertical_crop_is_included(self):
        doc = json.loads(self.manifest.read_text())
        doc['teams']['muse']['segments'][1]['crop_9x16'] = [[0, .5, .5, 1]]
        self.manifest.write_text(json.dumps(doc))
        with patch.object(sys, 'argv', self.args + ['--format', '9x16']), \
             patch.object(ap, 'validate_with_engine', return_value=self.root / 'engine.py'):
            ap.main()
        run = next((self.root / 'out').iterdir())
        montage = json.loads((run / 'montage.json').read_text())
        self.assertEqual(montage['segments'][0]['cadrage_v'], [[0, .5, .5, 1]])

    def test_validate_with_engine_success(self):
        engine = self.root / 'marketing/creative/video-v7/monter_v6.py'
        engine.write_text('def charger(*a, **k):\n    return None\n')
        self.assertEqual(ap.validate_with_engine(self.root, self.manifest, self.root, 'fr', self.root), engine)

    def test_validation_failure_is_preserved(self):
        with patch.object(sys, 'argv', self.args), patch.object(ap, 'validate_with_engine', side_effect=ValueError('invalid')):
            with self.assertRaises(ValueError):
                ap.main()
        run = next((self.root / 'out').iterdir())
        self.assertEqual(json.loads((run / 'validation-error.json').read_text())['status'], 'validation-failed-preserved')
        self.assertEqual(json.loads((run / 'status.json').read_text())['status'], 'validation-failed-preserved')

    def test_engine_validation_restores_process_state_after_failure(self):
        engine = self.root / 'marketing/creative/video-v7/monter_v6.py'
        engine.write_text("def charger(*a, **k):\n    raise ValueError('bad')\n")
        previous_path, previous_home = list(sys.path), os.environ.get('HOME')
        previous_cache, previous_bytecode = os.environ.get('V6_CACHE'), sys.dont_write_bytecode
        with self.assertRaisesRegex(ValueError, 'bad'):
            ap.validate_with_engine(self.root, self.manifest, self.root, 'fr', self.root)
        self.assertEqual(sys.path, previous_path)
        self.assertEqual(os.environ.get('HOME'), previous_home)
        self.assertEqual(os.environ.get('V6_CACHE'), previous_cache)
        self.assertEqual(sys.dont_write_bytecode, previous_bytecode)

    def test_bad_asset_records_preparation_failure(self):
        doc = json.loads(self.manifest.read_text())
        doc['teams']['muse']['segments'][0]['sha256'] = '0' * 64
        self.manifest.write_text(json.dumps(doc))
        with patch.object(sys, 'argv', self.args):
            with self.assertRaisesRegex(ValueError, 'SHA mismatch'):
                ap.main()
        run = next((self.root / 'out').iterdir())
        status = json.loads((run / 'status.json').read_text())
        self.assertEqual((status['status'], status['phase']), ('failed-preserved', 'preparation'))

    def test_executable_failure_records_render_phase(self):
        with patch.object(sys, 'argv', self.args + ['--render']), \
             patch.object(ap, 'validate_with_engine', return_value=self.root / 'engine.py'), \
             patch.object(ap.subprocess, 'run', side_effect=FileNotFoundError('interpreter absent')):
            with self.assertRaises(FileNotFoundError):
                ap.main()
        run = next((self.root / 'out').iterdir())
        status = json.loads((run / 'status.json').read_text())
        self.assertEqual((status['status'], status['phase']), ('failed-preserved', 'render'))

    def test_failed_render_is_not_reported_as_success(self):
        response = subprocess.CompletedProcess([], 1, stdout='', stderr='failure')
        with patch.object(sys, 'argv', self.args + ['--render']), \
             patch.object(ap, 'validate_with_engine', return_value=self.root / 'engine.py'), \
             patch.object(ap.subprocess, 'run', return_value=response):
            with self.assertRaisesRegex(RuntimeError, 'render failed'):
                ap.main()
        run = next((self.root / 'out').iterdir())
        self.assertEqual(json.loads((run / 'status.json').read_text())['status'], 'render-failed-preserved')


if __name__ == '__main__':
    unittest.main()
