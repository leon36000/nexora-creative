"""CPU-only tests against raw source files from the pinned MuseTalk tar."""
from __future__ import annotations

import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import unittest
import uuid

PACKAGE_ROOT = Path(__file__).resolve().parents[1]
FIXTURES = PACKAGE_ROOT / "fixtures" / "upstream"
TEST_ROOT = Path(os.environ.get("BOOTSTRAP_TEST_ROOT") or os.environ["SYNC_TEST_ROOT"]).absolute()
BOOTSTRAP_PATH = Path(__file__).resolve().with_name("prepare_faceparser_bootstrap.py")
MODULE_SPEC = importlib.util.spec_from_file_location("nexora_prepare_faceparser_bootstrap", BOOTSTRAP_PATH)
if MODULE_SPEC is None or MODULE_SPEC.loader is None:
    raise RuntimeError("cannot load bootstrap under test")
bootstrap = importlib.util.module_from_spec(MODULE_SPEC)
MODULE_SPEC.loader.exec_module(bootstrap)
FIXTURE_FILES = {
    "scripts/inference.py": "inference.py.txt",
    "musetalk/utils/preprocessing.py": "preprocessing.py.txt",
    "musetalk/utils/face_parsing/resnet.py": "faceparser-resnet.py.txt",
    "musetalk/utils/face_parsing/model.py": "faceparser-model.py.txt",
    "musetalk/utils/face_parsing/__init__.py": "faceparser-init.py.txt",
}
EXPECTED_LAUNCHER_SOURCE = {
    "scripts/inference.py": "aaf9c8289c8f07eaf00b87fb11442ac0e1005ac4e2f469966ae3dab2dc4a03aa",
    "musetalk/utils/preprocessing.py": "14a4202869bc8dfa761a3c4c3fb13afe2be4aeb9b853e2389c4e7860b439799c",
    "musetalk/utils/face_parsing/resnet.py": "7bd02989cd50904713ede4fb9ca468e0d45f0cb0c7ed55e12fc8e2b05e591184",
    "musetalk/utils/face_parsing/model.py": "4fd6c5f15979686367b261749dd13f28fc9e551b4e60f5844656ce2cdeac98db",
    "musetalk/utils/face_parsing/__init__.py": "5b4bc38796072153014181f00214ccceff8fd1a58193684795dad60715fb652b",
}
PINNED_FIXTURE_HASHES = {
    "fixtures/upstream/inference.py.txt": "aaf9c8289c8f07eaf00b87fb11442ac0e1005ac4e2f469966ae3dab2dc4a03aa",
    "fixtures/upstream/preprocessing.py.txt": "ca22548666af9bb0b059306e3955bffb97a4a97592b4a050fdce42c5361359f8",
    "fixtures/upstream/faceparser-init.py.txt": "c2824281e80458b81b7ecdde6cfd2b5f0224b022f41aaf1c61144a52163b2494",
    "fixtures/upstream/faceparser-model.py.txt": "05d69d1bd77fbca7b537602fe3f7851e8b2e1a3ea0279f383b4223598157e2d2",
    "fixtures/upstream/faceparser-resnet.py.txt": "a3419dabeff41c535e24f4d056b054c1bfc70d56f9ee430808b440005cc3189f",
    "fixtures/upstream/LICENSE": "992ec5fd1dd4964cfa003665196cd0c0c10a7a5aa10109991e964eebd2c7f116",
}


class FaceParserBootstrapTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        TEST_ROOT.mkdir(mode=0o700, parents=True, exist_ok=True)
        if TEST_ROOT.is_symlink():
            raise RuntimeError("test root cannot be a symlink")

    def new_case(self) -> Path:
        case = TEST_ROOT / uuid.uuid4().hex
        case.mkdir(mode=0o700, exist_ok=False)
        return case

    def make_source(self, case: Path, symlink_relative: str | None = None) -> Path:
        root = case / "source"
        root.mkdir(mode=0o700, exist_ok=False)
        for relative, fixture_name in FIXTURE_FILES.items():
            target = root / relative
            target.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
            fixture = FIXTURES / fixture_name
            if relative == symlink_relative:
                target.symlink_to(fixture)
            else:
                with fixture.open("rb") as src, target.open("xb") as dst:
                    shutil.copyfileobj(src, dst)
        return root

    def test_real_pinned_text_builds_four_syntax_valid_outputs_and_matches_launcher(self) -> None:
        case = self.new_case()
        source = self.make_source(case)
        before = {rel: hashlib.sha256((source / rel).read_bytes()).hexdigest() for rel in FIXTURE_FILES}

        outputs, manifest = bootstrap.build_outputs(source)

        self.assertEqual(set(outputs), set(bootstrap.EXPECTED))
        self.assertEqual(manifest["upstream_commit"], "0a89dec45a0192b824e3cf4daf96c239440c5ed8")
        self.assertEqual(manifest["source_sha256"], {rel: before[rel] for rel in bootstrap.EXPECTED})
        integrated = {"scripts/inference.py": before["scripts/inference.py"], **manifest["overlay_sha256"]}
        from outils.sync.labo import lanceur_musetalk
        self.assertEqual(EXPECTED_LAUNCHER_SOURCE, lanceur_musetalk.EXPECTED_SOURCE)
        self.assertEqual(integrated, lanceur_musetalk.EXPECTED_SOURCE)
        for relative, data in outputs.items():
            compile(data.decode("utf-8"), relative, "exec")
            self.assertEqual(hashlib.sha256((source / relative).read_bytes()).hexdigest(), before[relative])
        parser_init = outputs["musetalk/utils/face_parsing/__init__.py"].decode("utf-8")
        self.assertIn("weights_only=True", parser_init)
        self.assertIn("strict=True", parser_init)
        self.assertIn("pretrained=False", parser_init)
        self.assertNotIn("weights_only=False", parser_init)
        pose = outputs["musetalk/utils/preprocessing.py"].decode("utf-8")
        self.assertIn("torch.serialization.safe_globals(", pose)
        self.assertNotIn("weights_only=False", pose)

    def test_pinned_text_fixture_manifest_and_license(self) -> None:
        manifest_path = PACKAGE_ROOT / "upstream-fixture-manifest.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        self.assertEqual(manifest["commit"], "0a89dec45a0192b824e3cf4daf96c239440c5ed8")
        self.assertEqual(manifest["archive_sha256"], "6e20b30210846113094e2402e5358ac59ef08ae342010c8458f76bab46d4693b")
        self.assertTrue(manifest["fixtures_are_raw_text_data"])
        self.assertTrue(manifest["no_models_or_weights_included"])
        self.assertEqual({item["fixture"]: item["sha256"] for item in manifest["files"]}, PINNED_FIXTURE_HASHES)
        for item in manifest["files"]:
            data = (PACKAGE_ROOT / item["fixture"]).read_bytes()
            self.assertEqual(len(data), item["bytes"], item["fixture"])
            self.assertEqual(hashlib.sha256(data).hexdigest(), item["sha256"], item["fixture"])

    def test_bootstrap_import_does_not_import_torch(self) -> None:
        completed = subprocess.run(
            [sys.executable, "-B", "-c", "import sys; import prepare_faceparser_bootstrap; print('torch' in sys.modules)"],
            check=True,
            capture_output=True,
            text=True,
            timeout=15,
            env={"PATH": "/usr/bin:/bin", "PYTHONDONTWRITEBYTECODE": "1"},
            cwd=Path(bootstrap.__file__).resolve().parent,
        )
        self.assertEqual(completed.stdout.strip(), "False")

    def test_full_validation_precedes_exclusive_publication(self) -> None:
        case = self.new_case()
        source = self.make_source(case)
        target = case / "overlay"
        before = {rel: hashlib.sha256((source / rel).read_bytes()).hexdigest() for rel in FIXTURE_FILES}

        manifest = bootstrap.publish_overlay(source, target)

        self.assertEqual(manifest["status"], "validated_overlay_ready")
        self.assertTrue((target / "bootstrap-manifest.json").is_file())
        saved_manifest = json.loads((target / "bootstrap-manifest.json").read_text(encoding="utf-8"))
        self.assertEqual(saved_manifest, manifest)
        self.assertEqual(len(manifest["overlay_sha256"]), 4)
        for relative, expected_sha in manifest["overlay_sha256"].items():
            self.assertEqual(hashlib.sha256((target / relative).read_bytes()).hexdigest(), expected_sha)
        self.assertEqual(before, {rel: hashlib.sha256((source / rel).read_bytes()).hexdigest() for rel in FIXTURE_FILES})

    def test_cli_main_prepares_overlay_from_text_fixtures(self) -> None:
        case = self.new_case()
        source = self.make_source(case)
        target = case / "cli-overlay"
        env = {"PATH": "/usr/bin:/bin", "PYTHONDONTWRITEBYTECODE": "1"}

        completed = subprocess.run(
            [
                sys.executable,
                "-B",
                str(Path(bootstrap.__file__).resolve()),
                "--source-root",
                str(source),
                "--destination",
                str(target),
            ],
            check=False,
            capture_output=True,
            text=True,
            timeout=15,
            env=env,
        )

        self.assertEqual(completed.returncode, 0, completed.stderr)
        result = json.loads(completed.stdout)
        self.assertEqual(result["manifest"]["status"], "validated_overlay_ready")
        self.assertTrue((target / "bootstrap-manifest.json").is_file())

    def test_bad_third_source_is_rejected_before_any_output_or_source_write(self) -> None:
        case = self.new_case()
        source = self.make_source(case)
        relative = "musetalk/utils/face_parsing/__init__.py"
        with (source / relative).open("ab") as file:
            file.write(b"# changed fixture\n")
        resnet_before = hashlib.sha256((source / "musetalk/utils/face_parsing/resnet.py").read_bytes()).hexdigest()
        target = case / "must-not-publish"

        with self.assertRaises(bootstrap.BootstrapError):
            bootstrap.publish_overlay(source, target)

        self.assertFalse(target.exists())
        self.assertEqual(hashlib.sha256((source / "musetalk/utils/face_parsing/resnet.py").read_bytes()).hexdigest(), resnet_before)

    def test_destination_inside_source_tree_is_refused_without_mutation(self) -> None:
        case = self.new_case()
        source = self.make_source(case)
        before = {rel: hashlib.sha256((source / rel).read_bytes()).hexdigest() for rel in FIXTURE_FILES}
        target = source / "not-created" / ".." / "generated-overlay"

        with self.assertRaisesRegex(bootstrap.BootstrapError, "outside the pinned source tree"):
            bootstrap.publish_overlay(source, target)

        self.assertFalse(target.exists())
        self.assertEqual(before, {rel: hashlib.sha256((source / rel).read_bytes()).hexdigest() for rel in FIXTURE_FILES})

    def test_existing_target_is_refused_without_changing_any_bytes(self) -> None:
        case = self.new_case()
        source = self.make_source(case)
        target = case / "occupied"
        target.mkdir(mode=0o700)
        sentinel = target / "sentinel.txt"
        sentinel.write_bytes(b"preserve exactly")
        before = hashlib.sha256(sentinel.read_bytes()).hexdigest()

        with self.assertRaisesRegex(bootstrap.BootstrapError, "already exists"):
            bootstrap.publish_overlay(source, target)

        self.assertEqual(hashlib.sha256(sentinel.read_bytes()).hexdigest(), before)
        self.assertEqual(sentinel.read_bytes(), b"preserve exactly")

    def test_symlinked_upstream_file_is_refused(self) -> None:
        case = self.new_case()
        source = self.make_source(case, symlink_relative="musetalk/utils/face_parsing/resnet.py")
        with self.assertRaisesRegex(bootstrap.BootstrapError, "symlink"):
            bootstrap.build_outputs(source)

    def test_patch_anchor_requires_exactly_one_match(self) -> None:
        with self.assertRaises(bootstrap.BootstrapError):
            bootstrap._apply_one("nothing here", "anchor", "patched", "fixture.py")
        with self.assertRaises(bootstrap.BootstrapError):
            bootstrap._apply_one("anchor anchor", "anchor", "patched", "fixture.py")


if __name__ == "__main__":
    unittest.main()
