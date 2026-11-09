"""unittest suite for bench3d. Uses temporary directories only."""
from __future__ import annotations

import hashlib
import io
import json
import os
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from bench3d import cli  # noqa: E402
from bench3d.layout import LayoutError, build_layout, mapping_from_key  # noqa: E402
from bench3d.manifest import ManifestError, load_manifest, sha256_file  # noqa: E402
from bench3d.outputs import OutputExistsError, dumps, write_exclusive  # noqa: E402

ARMS = [
    {"id": "nexora", "label": "Moteur Nexora", "kind": "nexora"},
    {"id": "alt-a", "label": "Alternative A", "kind": "alternative"},
    {"id": "alt-b", "label": "Alternative B", "kind": "alternative"},
]


def _mk_bench(tmp: Path, n_subjects=24, arms=None, seed=1234):
    img_dir = tmp / "images"
    img_dir.mkdir(parents=True, exist_ok=True)
    subjects = []
    for i in range(n_subjects):
        name = "s%03d.png" % i
        content = b"\x89PNG\r\n\x1a\nfake-image-%d" % i
        (img_dir / name).write_bytes(content)
        subjects.append({
            "id": "s%03d" % i,
            "image": "images/" + name,
            "sha256": hashlib.sha256(content).hexdigest(),
            "category": ["object", "scene", "face"][i % 3],
        })
    manifest = {
        "version": 1,
        "seed": seed,
        "arms": list(ARMS if arms is None else arms),
        "subjects": subjects,
    }
    mpath = tmp / "manifest.json"
    mpath.write_text(json.dumps(manifest), encoding="utf-8")
    return mpath, manifest


class BaseCase(unittest.TestCase):
    def setUp(self):
        self._td = tempfile.TemporaryDirectory()
        self.tmp = Path(self._td.name)
        self.addCleanup(self._td.cleanup)

    def expect_manifest_error(self, manifest: dict) -> ManifestError:
        p = self.tmp / "bad.json"
        p.write_text(json.dumps(manifest), encoding="utf-8")
        with self.assertRaises(ManifestError) as ctx:
            load_manifest(p)
        return ctx.exception


class ManifestTests(BaseCase):
    def test_valid_manifest_loads(self):
        mpath, raw = _mk_bench(self.tmp)
        m = load_manifest(mpath)
        self.assertEqual(len(m.subjects), 24)
        self.assertEqual([a.id for a in m.arms], ["nexora", "alt-a", "alt-b"])
        self.assertEqual(m.seed, 1234)

    def test_too_few_subjects(self):
        mpath, raw = _mk_bench(self.tmp, n_subjects=19)
        with self.assertRaises(ManifestError) as ctx:
            load_manifest(mpath)
        self.assertTrue(any("at least 20" in p for p in ctx.exception.problems))

    def test_too_few_arms(self):
        mpath, raw = _mk_bench(self.tmp, arms=ARMS[:2])
        with self.assertRaises(ManifestError) as ctx:
            load_manifest(mpath)
        self.assertTrue(any("at least 3 arms" in p for p in ctx.exception.problems))

    def test_text_with_image_extension_is_rejected(self):
        _, raw = _mk_bench(self.tmp)
        p = self.tmp / 'images' / 'ordinary.png'
        content = b'plain synthetic text, not an image'
        p.write_bytes(content)
        raw['subjects'][0].update(image='images/ordinary.png', sha256=hashlib.sha256(content).hexdigest())
        self.assertTrue(any('image signature' in x for x in self.expect_manifest_error(raw).problems))

    def test_common_secret_names_are_rejected_before_open(self):
        _, raw = _mk_bench(self.tmp)
        for name in ['.env', '.env.local', 'prod.env', '.npmrc', 'demo.pem', 'demo.key', 'id_rsa', 'credentials.json']:
            p = self.tmp / 'images' / name
            p.write_bytes(b'only synthetic data')
            raw['subjects'][0].update(image='images/' + name, sha256=hashlib.sha256(b'only synthetic data').hexdigest())
            with patch('builtins.open', wraps=open) as opened:
                err = self.expect_manifest_error(raw)
            self.assertTrue(any('sensitive path' in x for x in err.problems))
            self.assertFalse(any(Path(call.args[0]) == p for call in opened.call_args_list))

    def test_symlink_to_sensitive_name_is_rejected_before_open(self):
        _, raw = _mk_bench(self.tmp)
        secret = self.tmp / 'images' / '.env.synthetic'
        secret.write_bytes(b'only synthetic data')
        link = self.tmp / 'images' / 'photo.png'
        try:
            os.symlink(secret, link)
        except (OSError, NotImplementedError):
            self.skipTest('symlinks unsupported')
        raw['subjects'][0].update(image='images/photo.png', sha256=hashlib.sha256(b'only synthetic data').hexdigest())
        with patch('builtins.open', wraps=open) as opened:
            err = self.expect_manifest_error(raw)
        self.assertTrue(any('sensitive path' in x for x in err.problems))
        self.assertFalse(any(Path(call.args[0]) in (secret, link) for call in opened.call_args_list))

    def test_verify_key_rejects_malformed_json_structure(self):
        p = self.tmp / 'invalid-key.json'
        for content in [[], {'kind': 'local_answer_key', 'mapping': {}}, {'kind': 'local_answer_key', 'mapping': [{}]}]:
            p.write_text(json.dumps(content))
            with redirect_stderr(io.StringIO()):
                self.assertNotEqual(cli.cmd_verify_key(type('Args', (), {'key': str(p)})()), 0)

    def test_verify_key_refuses_sensitive_path_before_read(self):
        p = self.tmp / '.env.synthetic'
        p.write_text('only synthetic data')
        with patch.object(Path, 'read_text', side_effect=AssertionError('must not read')):
            result = cli.cmd_verify_key(type('Args', (), {'key': str(p)})())
        self.assertNotEqual(result, 0)

    def test_manifest_with_sensitive_name_is_not_read(self):
        p = self.tmp / '.env.synthetic'
        p.write_text('only synthetic data')
        with patch.object(Path, 'read_bytes', side_effect=AssertionError('must not read')):
            with self.assertRaises(ManifestError):
                load_manifest(p)

    def test_matching_jpeg_and_webp_signatures_are_accepted(self):
        _, raw = _mk_bench(self.tmp)
        for i, (name, content) in enumerate([('synthetic.jpg', b'\xff\xd8\xffsynthetic-jpeg'), ('synthetic.webp', b'RIFF\x08\x00\x00\x00WEBPsynthetic')]):
            (self.tmp / 'images' / name).write_bytes(content)
            raw['subjects'][i].update(image='images/' + name, sha256=hashlib.sha256(content).hexdigest())
        p = self.tmp / 'formats.json'
        p.write_text(json.dumps(raw))
        self.assertEqual(len(load_manifest(p).subjects), 24)

    def test_duplicate_subject_id(self):
        mpath, raw = _mk_bench(self.tmp)
        raw["subjects"][1]["id"] = raw["subjects"][0]["id"]
        err = self.expect_manifest_error(raw)
        self.assertTrue(any("duplicate subject id" in p for p in err.problems))

    def test_duplicate_bytes_are_rejected_even_with_distinct_paths(self):
        mpath, raw = _mk_bench(self.tmp)
        source = self.tmp / raw["subjects"][0]["image"]
        dest = self.tmp / raw["subjects"][1]["image"]
        dest.write_bytes(source.read_bytes())
        raw["subjects"][1]["sha256"] = raw["subjects"][0]["sha256"]
        mpath.write_text(json.dumps(raw))
        with self.assertRaises(ManifestError) as ctx:
            load_manifest(mpath)
        self.assertTrue(any("duplicate image bytes" in p for p in ctx.exception.problems))

    def test_arms_require_engine_and_two_alternatives(self):
        arms = [dict(a, kind="alternative") for a in ARMS]
        mpath, _ = _mk_bench(self.tmp, arms=arms)
        with self.assertRaises(ManifestError):
            load_manifest(mpath)

    def test_duplicate_arm_id(self):
        arms = list(ARMS)
        arms[2] = dict(arms[2], id="nexora")
        mpath, raw = _mk_bench(self.tmp, arms=arms)
        with self.assertRaises(ManifestError) as ctx:
            load_manifest(mpath)
        self.assertTrue(any("duplicate arm id" in p for p in ctx.exception.problems))

    def test_duplicate_image(self):
        mpath, raw = _mk_bench(self.tmp)
        raw["subjects"][1]["image"] = raw["subjects"][0]["image"]
        err = self.expect_manifest_error(raw)
        self.assertTrue(any("duplicate image" in p for p in err.problems))

    def test_sha_mismatch(self):
        mpath, raw = _mk_bench(self.tmp)
        raw["subjects"][0]["sha256"] = "0" * 64
        err = self.expect_manifest_error(raw)
        self.assertTrue(any("mismatch" in p for p in err.problems))

    def test_sha_malformed(self):
        mpath, raw = _mk_bench(self.tmp)
        raw["subjects"][0]["sha256"] = "xyz"
        err = self.expect_manifest_error(raw)
        self.assertTrue(any("sha256: not a 64-char" in p for p in err.problems))

    def test_missing_file(self):
        mpath, raw = _mk_bench(self.tmp)
        (self.tmp / "images" / "s003.png").unlink()
        p = self.tmp / "m.json"
        p.write_text(json.dumps(raw), encoding="utf-8")
        with self.assertRaises(ManifestError) as ctx:
            load_manifest(p)
        self.assertTrue(any("does not exist" in x for x in ctx.exception.problems))

    def test_unsafe_paths_rejected(self):
        mpath, raw = _mk_bench(self.tmp)
        (self.tmp.parent / "outside.png").write_bytes(b"x")
        bad = [
            "../outside.png",
            "/etc/passwd",
            "C:\\windows\\x.png",
            "images/../../outside.png",
            "images//s000.png",
            "images/./s000.png",
            "",
        ]
        for path in bad:
            raw["subjects"][0]["image"] = path
            err = self.expect_manifest_error(raw)
            self.assertTrue(any("image" in p for p in err.problems), (path, err.problems))

    def test_symlink_escape_rejected(self):
        mpath, raw = _mk_bench(self.tmp)
        outside = self.tmp.parent / ("outside_%s.png" % self.tmp.name)
        outside.write_bytes(b"secret")
        link = self.tmp / "images" / "link.png"
        try:
            os.symlink(outside, link)
        except (OSError, NotImplementedError):
            self.skipTest("symlinks unsupported")
        self.addCleanup(lambda: outside.unlink(missing_ok=True))
        raw["subjects"][0]["image"] = "images/link.png"
        raw["subjects"][0]["sha256"] = hashlib.sha256(b"secret").hexdigest()
        err = self.expect_manifest_error(raw)
        self.assertTrue(any("escapes image_root" in p for p in err.problems))

    def test_empty_file_rejected(self):
        mpath, raw = _mk_bench(self.tmp)
        (self.tmp / "images" / "s000.png").write_bytes(b"")
        raw["subjects"][0]["sha256"] = hashlib.sha256(b"").hexdigest()
        err = self.expect_manifest_error(raw)
        self.assertTrue(any("empty" in p for p in err.problems))

    def test_nexora_kind_constraint(self):
        arms = [dict(a) for a in ARMS]
        arms[1]["kind"] = "nexora"
        mpath, raw = _mk_bench(self.tmp, arms=arms)
        with self.assertRaises(ManifestError) as ctx:
            load_manifest(mpath)
        self.assertTrue(any("at most one arm" in p for p in ctx.exception.problems))

    def test_no_seed_and_no_override(self):
        mpath, raw = _mk_bench(self.tmp)
        del raw["seed"]
        mpath.write_text(json.dumps(raw), encoding="utf-8")
        m = load_manifest(mpath)
        with self.assertRaises(LayoutError):
            build_layout(m)


class LayoutTests(BaseCase):
    def setUp(self):
        super().setUp()
        self.mpath, _ = _mk_bench(self.tmp)
        self.man = load_manifest(self.mpath)

    def test_deterministic_same_seed(self):
        a = build_layout(self.man, 7)
        b = build_layout(load_manifest(self.mpath), 7)
        self.assertEqual(dumps(a.plan), dumps(b.plan))
        self.assertEqual(dumps(a.blind_plan), dumps(b.blind_plan))
        self.assertEqual(dumps(a.mapping_key), dumps(b.mapping_key))

    def test_different_seed_changes_mapping_but_not_counts(self):
        a = build_layout(self.man, 7)
        b = build_layout(self.man, 8)
        self.assertNotEqual(dumps(a.mapping_key), dumps(b.mapping_key))
        self.assertEqual(a.plan["n_units"], b.plan["n_units"])
        self.assertEqual(a.plan["n_units"], 24 * 3)

    def test_every_subject_x_arm_once(self):
        lay = build_layout(self.man, 7)
        pairs = [(u["subject_id"], u["arm_id"]) for u in lay.plan["units"]]
        self.assertEqual(len(pairs), len(set(pairs)))
        self.assertEqual(len(pairs), 24 * 3)
        subjects = {u["subject_id"] for u in lay.plan["units"]}
        self.assertEqual(len(subjects), 24)
        for s in subjects:
            arms = [u["arm_id"] for u in lay.plan["units"] if u["subject_id"] == s]
            self.assertEqual(sorted(arms), ["alt-a", "alt-b", "nexora"])

    def test_blind_plan_has_no_arm_names(self):
        lay = build_layout(self.man, 7)
        text = dumps(lay.blind_plan).lower()
        self.assertNotIn("nexora", text)
        self.assertNotIn("alt-a", text)
        self.assertNotIn("alt-b", text)
        self.assertNotIn("moteur", text)
        self.assertNotIn("alternative", text)

    def test_blind_plan_does_not_copy_free_form_category(self):
        mpath, raw = _mk_bench(self.tmp)
        raw['subjects'][0]['category'] = 'SYNTHETIC_PRIVATE_CATEGORY_MARKER'
        mpath.write_text(json.dumps(raw))
        layout = build_layout(load_manifest(mpath))
        self.assertNotIn('SYNTHETIC_PRIVATE_CATEGORY_MARKER', dumps(layout.blind_plan))
        self.assertNotIn('SYNTHETIC_PRIVATE_CATEGORY_MARKER', layout.layout_csv)
        self.assertIn('SYNTHETIC_PRIVATE_CATEGORY_MARKER', dumps(layout.plan))

    def test_blind_plan_hides_shuffle_seed_and_manifest_digest(self):
        mpath, _ = _mk_bench(self.tmp)
        blind = build_layout(load_manifest(mpath)).blind_plan
        self.assertNotIn("seed", blind)
        self.assertNotIn("manifest_digest", blind)
        self.assertNotIn("manifest_file_sha256", blind)

    def test_blind_units_have_no_score_fields(self):
        lay = build_layout(self.man, 7)
        forbidden = {"score", "rank", "ranking", "quality", "metric", "winner"}
        for u in lay.blind_plan["units"]:
            self.assertFalse(forbidden & set(k.lower() for k in u), u)

    def test_key_matches_public_plan(self):
        lay = build_layout(self.man, 7)
        mapping = mapping_from_key(lay.mapping_key)
        self.assertEqual(len(mapping), len(lay.plan["units"]))
        for u in lay.plan["units"]:
            self.assertEqual(mapping[u["unit_id"]], u["arm_id"])
        # blind labels in key match blind plan
        blind = {u["unit_id"]: u["blind_label"] for u in lay.blind_plan["units"]}
        for e in lay.mapping_key["mapping"]:
            self.assertEqual(blind[e["unit_id"]], e["blind_label"])

    def test_labels_distinct_per_subject_and_shuffled(self):
        lay = build_layout(self.man, 7)
        by_subject = {}
        for e in lay.mapping_key["mapping"]:
            by_subject.setdefault(e["subject_id"], set()).add(e["blind_label"])
        for s, labels in by_subject.items():
            self.assertEqual(labels, {"A", "B", "C"}, s)
        # mapping should actually vary across subjects (not always nexora=A)
        orders = set()
        for s in by_subject:
            unit_order = [(u["review_order"], u["arm_id"]) for u in lay.plan["units"]
                          if u["subject_id"] == s]
            orders.add(tuple(a for _, a in sorted(unit_order)))
        self.assertGreater(len(orders), 1)

    def test_layout_csv_rows(self):
        lay = build_layout(self.man, 7)
        lines = lay.layout_csv.strip().splitlines()
        self.assertEqual(len(lines), 1 + 24 * 3)
        for line in lines[1:]:
            self.assertNotIn("nexora", line)
            self.assertNotIn("alt-", line)

    def test_seed_must_be_int(self):
        with self.assertRaises(LayoutError):
            build_layout(self.man, "7")


class OutputTests(BaseCase):
    def test_write_exclusive_refuses_overwrite(self):
        p = self.tmp / "x.json"
        write_exclusive(p, "first\n")
        with self.assertRaises(OutputExistsError):
            write_exclusive(p, "second\n")
        self.assertEqual(p.read_text(encoding="utf-8"), "first\n")

    def test_write_exclusive_uses_lf(self):
        p = self.tmp / "x.json"
        write_exclusive(p, "a\nb\n")
        self.assertEqual(p.read_bytes(), b"a\nb\n")


class CliTests(BaseCase):
    def run_cli(self, argv):
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            try:
                code = cli.main(argv)
            except SystemExit as exc:  # argparse errors
                code = int(exc.code)
        return code, out.getvalue(), err.getvalue()

    def test_prepare_writes_separate_files(self):
        mpath, _ = _mk_bench(self.tmp)
        out_dir = self.tmp / "out"
        code, out, err = self.run_cli(["prepare", str(mpath), "--out", str(out_dir)])
        self.assertEqual(code, 0, err)
        names = sorted(p.name for p in out_dir.iterdir())
        self.assertEqual(names, ["blind_plan.json", "layout.csv",
                                 "mapping_key.json", "plan.json"])
        blind = json.loads((out_dir / "blind_plan.json").read_text())
        key = json.loads((out_dir / "mapping_key.json").read_text())
        self.assertEqual(blind["kind"], "blind_review_plan")
        self.assertEqual(key["kind"], "local_answer_key")
        self.assertIn("PRIVATE", key["warning"])
        self.assertNotIn("nexora", (out_dir / "blind_plan.json").read_text().lower())
        self.assertEqual(len(key["mapping"]), 72)

    def test_prepare_refuses_overwrite(self):
        mpath, _ = _mk_bench(self.tmp)
        out_dir = self.tmp / "out"
        code, _, _ = self.run_cli(["prepare", str(mpath), "--out", str(out_dir),
                                   "--seed", "1"])
        self.assertEqual(code, 0)
        before = (out_dir / "plan.json").read_bytes()
        code, _, err = self.run_cli(["prepare", str(mpath), "--out", str(out_dir),
                                     "--seed", "1"])
        self.assertEqual(code, cli.EXIT_EXISTS)
        self.assertIn("refusing to overwrite", err)
        self.assertEqual((out_dir / "plan.json").read_bytes(), before)

    def test_partial_failure_leaves_no_new_files(self):
        mpath, _ = _mk_bench(self.tmp)
        out_dir = self.tmp / "out"
        out_dir.mkdir()
        (out_dir / "mapping_key.json").write_text("existing\n")
        code, _, _ = self.run_cli(["prepare", str(mpath), "--out", str(out_dir)])
        self.assertEqual(code, cli.EXIT_EXISTS)
        self.assertEqual(sorted(p.name for p in out_dir.iterdir()), ["mapping_key.json"])
        self.assertEqual((out_dir / "mapping_key.json").read_text(), "existing\n")

    def test_invalid_manifest_exit_code(self):
        mpath, raw = _mk_bench(self.tmp, n_subjects=5)
        code, _, err = self.run_cli(["prepare", str(mpath), "--out", str(self.tmp / "o")])
        self.assertEqual(code, cli.EXIT_MANIFEST)
        self.assertIn("at least 20", err)
        self.assertFalse((self.tmp / "o").exists())

    def test_stdout_does_not_leak_key(self):
        mpath, _ = _mk_bench(self.tmp)
        code, out, err = self.run_cli(["prepare", str(mpath), "--stdout"])
        self.assertEqual(code, 0)
        data = json.loads(out)
        self.assertEqual(data["kind"], "blind_review_plan")
        self.assertNotIn("mapping", out.lower())
        self.assertNotIn("nexora", out.lower())

    def test_seed_override(self):
        mpath, _ = _mk_bench(self.tmp)
        code, _, err = self.run_cli(["prepare", str(mpath), "--out",
                                     str(self.tmp / "a"), "--seed", "99"])
        self.assertEqual(code, 0, err)
        plan = json.loads((self.tmp / "a" / "plan.json").read_text())
        self.assertEqual(plan["seed"], 99)

    def test_verify_key(self):
        mpath, _ = _mk_bench(self.tmp)
        out_dir = self.tmp / "out"
        self.run_cli(["prepare", str(mpath), "--out", str(out_dir)])
        code, out, _ = self.run_cli(["verify-key", str(out_dir / "mapping_key.json")])
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(out)["n_units"], 72)

    def test_module_entrypoint_runs(self):
        mpath, _ = _mk_bench(self.tmp)
        r = subprocess.run(
            [sys.executable, "-m", "bench3d", "prepare", str(mpath),
             "--out", str(self.tmp / "o")],
            cwd=str(ROOT), capture_output=True, text=True,
            env={**os.environ, "PYTHONPATH": str(ROOT)},
        )
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertNotIn(str(ROOT), (self.tmp / "o" / "plan.json").read_text())


if __name__ == "__main__":
    unittest.main()
