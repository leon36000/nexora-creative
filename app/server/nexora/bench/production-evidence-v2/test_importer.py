"""Tests CPU du registre V2; aucune génération média, clé ou service externe."""
from __future__ import annotations

import hashlib
import importlib.util
import json
import tempfile
import unittest
from unittest.mock import patch
from pathlib import Path


HERE = Path(__file__).resolve().parent
REPO_ROOT = next(
    parent for parent in HERE.parents
    if (parent / "app/server/nexora/montage/memoires.ts").is_file()
)
spec = importlib.util.spec_from_file_location("production_evidence_v2_importer", HERE / "importer.py")
assert spec is not None and spec.loader is not None
importer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(importer)


def _artifact(root_name: str, path: str, content: bytes, kind: str) -> dict:
    return {
        "root": root_name,
        "path": path,
        "sha256": hashlib.sha256(content).hexdigest(),
        "size_bytes": len(content),
        "kind": kind,
    }


def fixture_record(storage_root: Path, repo_root: Path) -> dict:
    media = b"synthetic evidence bytes"
    (storage_root / "fixture.mp4").write_bytes(media)
    corpus = b"synthetic AMD corpus fixture"
    corpus_path = repo_root / "app/server/nexora/bench/corpus-amd-v2/corpus.json"
    corpus_path.parent.mkdir(parents=True, exist_ok=True)
    corpus_path.write_bytes(corpus)
    old_record = {"record_id": "v7.workcut.deepseek.r1", "edition": "V1 fixture"}
    old_record["record_sha256"] = importer.record_digest(old_record)
    archived_v1 = (json.dumps(old_record, sort_keys=True, separators=(",", ":")) + "\n").encode()
    archive_path = storage_root / "archive-v1" / "v7-workcuts-v1.jsonl"
    archive_path.parent.mkdir(exist_ok=True)
    archive_path.write_bytes(archived_v1)
    archive_sha = hashlib.sha256(archived_v1).hexdigest()
    receipt_obj = {
        "schema": "nexora-v7-registry-archive-receipt-v1",
        "storage_sha256": archive_sha,
        "pc1_sha256": archive_sha,
        "storage_size_bytes": len(archived_v1),
        "pc1_size_bytes": len(archived_v1),
        "storage_relative_path": "archive-v1/v7-workcuts-v1.jsonl",
        "pc1_path": "/run/media/pc1/Infrastructure/NexoraStudioWork/fixture/v7-workcuts-v1.jsonl",
        "verified_at_utc": "2026-11-05T13:03:15Z",
        "verification": "synthetic test fixture",
    }
    receipt = (json.dumps(receipt_obj, sort_keys=True) + "\n").encode()
    receipt_path = storage_root / "archive-v1" / "pc1-v1-registry-receipt.json"
    receipt_path.write_bytes(receipt)
    return {
        "schema": importer.SCHEMA,
        "record_id": "v7.workcut.deepseek.r1.v2",
        "team": "deepseek",
        "edition": "R1-V2",
        "team_role": "independent_team_not_confirmed_professor",
        "status": "codex_machine_observation_unjudged",
        "amd2_brief_id": None,
        "amd2_corpus_sha256": hashlib.sha256(corpus).hexdigest(),
        "artifacts": [
            _artifact("storage", "fixture.mp4", media, "synthetic-test-fixture"),
            _artifact("repo", "app/server/nexora/bench/corpus-amd-v2/corpus.json", corpus, "amd2_corpus"),
            _artifact("storage", "archive-v1/v7-workcuts-v1.jsonl", archived_v1, "archived_v1_registry"),
            _artifact("storage", "archive-v1/pc1-v1-registry-receipt.json", receipt, "archived_v1_pc1_receipt"),
        ],
        "seed_reconciliation": [{
            "plan_id": "p01", "seed_kind": "keyframe", "declared": 101,
            "used": None, "texte_brut": "101 (déclarée seulement; non attestée comme soumise)",
            "used_source": "legacy source field was declarative only", "state": "unknown",
        }],
        "observations": [{"authority": "codex_machine", "text": "No human judgment."}],
        "founder_review": {"status": "pending"},
        "memory_promotion": "none",
        "lineage": [],
        "replaces_v1_record": {
            "record_id": "v7.workcut.deepseek.r1",
            "record_sha256": old_record["record_sha256"],
            "registry_sha256": archive_sha,
        },
    }


class TestImportEvidenceV2(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.base = Path(self.temp.name)
        self.storage = self.base / "storage"
        self.repo = self.base / "repo"
        self.storage.mkdir()
        self.repo.mkdir()
        self.registry = self.base / "registry-v2.jsonl"

    def tearDown(self):
        self.temp.cleanup()

    def test_import_verifies_hashes_and_keeps_amd_link_null(self):
        record = fixture_record(self.storage, self.repo)
        action, saved = importer.import_record(record, self.registry, self.storage, self.repo)
        self.assertEqual(action, "imported")
        self.assertIsNone(saved["amd2_brief_id"])
        self.assertEqual(saved["memory_promotion"], "none")
        self.assertEqual(saved["founder_review"], {"status": "pending"})
        self.assertEqual(saved["record_sha256"], importer.record_digest(record))
        saved_line = json.loads(self.registry.read_text(encoding="utf-8").strip())
        self.assertEqual(saved_line, saved)

    def test_null_typed_seed_with_raw_text_remains_unknown(self):
        record = fixture_record(self.storage, self.repo)
        seed = record["seed_reconciliation"][0]
        seed["used"] = None
        seed["texte_brut"] = "not recorded in this legacy manifest"
        seed["state"] = "unknown"
        _, saved = importer.import_record(record, self.registry, self.storage, self.repo)
        self.assertIsNone(saved["seed_reconciliation"][0]["used"])
        self.assertEqual(saved["seed_reconciliation"][0]["texte_brut"], "not recorded in this legacy manifest")
        self.assertEqual(saved["seed_reconciliation"][0]["state"], "unknown")

    def test_numeric_mismatch_remains_discordant(self):
        record = fixture_record(self.storage, self.repo)
        seed = record["seed_reconciliation"][0]
        seed.update({"declared": 7102, "used": 8102, "texte_brut": None, "used_source": "recorded submitted seed", "state": "discordant"})
        _, saved = importer.import_record(record, self.registry, self.storage, self.repo)
        self.assertEqual(saved["seed_reconciliation"][0]["used"], 8102)
        self.assertEqual(saved["seed_reconciliation"][0]["state"], "discordant")

    def test_state_cannot_hide_numeric_disagreement(self):
        record = fixture_record(self.storage, self.repo)
        seed = record["seed_reconciliation"][0]
        seed.update({"declared": 7102, "used": 8102, "texte_brut": None, "used_source": "recorded submitted seed", "state": "known"})
        with self.assertRaisesRegex(importer.EvidenceError, "state does not match"):
            importer.validate_record(record)

    def test_duplicate_seed_rows_are_refused(self):
        record = fixture_record(self.storage, self.repo)
        record["seed_reconciliation"].append(dict(record["seed_reconciliation"][0]))
        with self.assertRaisesRegex(importer.EvidenceError, "duplicate \\(plan_id, seed_kind\\)"):
            importer.validate_record(record)

    def test_numeric_equal_seed_is_known(self):
        record = fixture_record(self.storage, self.repo)
        seed = record["seed_reconciliation"][0]
        seed.update({"declared": 101, "used": 101, "texte_brut": None, "used_source": "recorded submitted seed", "state": "known"})
        self.assertEqual(importer.validate_record(record)["seed_reconciliation"][0]["state"], "known")

    def test_same_id_same_sha_is_idempotent_and_does_not_rewrite(self):
        record = fixture_record(self.storage, self.repo)
        first, saved = importer.import_record(record, self.registry, self.storage, self.repo)
        before = self.registry.read_bytes()
        second, repeated = importer.import_record(record, self.registry, self.storage, self.repo)
        self.assertEqual((first, second), ("imported", "already_present"))
        self.assertEqual(saved["record_sha256"], repeated["record_sha256"])
        self.assertEqual(self.registry.read_bytes(), before)

    def test_same_id_different_sha_is_refused_without_changing_bytes(self):
        record = fixture_record(self.storage, self.repo)
        importer.import_record(record, self.registry, self.storage, self.repo)
        before = self.registry.read_bytes()
        changed = dict(record, edition="R1-V2-different")
        with self.assertRaisesRegex(importer.EvidenceError, "different SHA-256"):
            importer.import_record(changed, self.registry, self.storage, self.repo)
        self.assertEqual(self.registry.read_bytes(), before)

    def test_artifact_change_and_path_traversal_are_refused(self):
        record = fixture_record(self.storage, self.repo)
        (self.storage / "fixture.mp4").write_bytes(b"changed bytes")
        with self.assertRaisesRegex(importer.EvidenceError, "hash/size mismatch"):
            importer.import_record(record, self.registry, self.storage, self.repo)
        self.assertFalse(self.registry.exists())
        record["artifacts"][0]["path"] = "../outside.mp4"
        with self.assertRaisesRegex(importer.EvidenceError, "escapes"):
            importer.validate_record(record)

    def test_artifact_symlink_in_parent_directory_is_refused(self):
        record = fixture_record(self.storage, self.repo)
        target = self.storage / "real-dir"
        target.mkdir()
        (target / "data.bin").write_bytes(b"symlink fixture")
        link = self.storage / "alias-dir"
        link.symlink_to(target, target_is_directory=True)
        record["artifacts"].append(_artifact("storage", "alias-dir/data.bin", b"symlink fixture", "symlink-test"))
        with self.assertRaisesRegex(importer.EvidenceError, "must not traverse a symlink"):
            importer.verify_artifacts(record, self.storage, self.repo)

    def test_registry_path_cannot_target_professor_memory_or_json(self):
        record = fixture_record(self.storage, self.repo)
        professor = self.repo / "app/server/nexora/memoire/professeur"
        with self.assertRaisesRegex(importer.EvidenceError, "runtime memory directory"):
            importer.import_record(record, professor / "not-a-memory.jsonl", self.storage, self.repo)
        with self.assertRaisesRegex(importer.EvidenceError, "must end in .jsonl"):
            importer.import_record(record, self.base / "not-jsonl.json", self.storage, self.repo)
        with self.assertRaisesRegex(importer.EvidenceError, "parent directory must already exist"):
            importer.import_record(record, self.base / "missing" / "registry.jsonl", self.storage, self.repo)
        self.assertFalse(professor.exists())
        self.assertFalse((self.base / "missing").exists())

    def test_archived_v1_registry_hash_is_linked_to_replacement_claim(self):
        record = fixture_record(self.storage, self.repo)
        record["replaces_v1_record"]["registry_sha256"] = "b" * 64
        with self.assertRaisesRegex(importer.EvidenceError, "recorded SHA-256"):
            importer.validate_record(record)

    def test_replaced_v1_row_and_pc1_receipt_are_checked(self):
        record = fixture_record(self.storage, self.repo)
        record["replaces_v1_record"]["record_sha256"] = "b" * 64
        with self.assertRaisesRegex(importer.EvidenceError, "does not match the archived row"):
            importer.verify_artifacts(record, self.storage, self.repo)

        record = fixture_record(self.storage, self.repo)
        receipt_path = self.storage / "archive-v1/pc1-v1-registry-receipt.json"
        receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
        receipt["pc1_sha256"] = "b" * 64
        content = (json.dumps(receipt, sort_keys=True) + "\n").encode()
        receipt_path.write_bytes(content)
        item = next(item for item in record["artifacts"] if item["kind"] == "archived_v1_pc1_receipt")
        item.update({"sha256": hashlib.sha256(content).hexdigest(), "size_bytes": len(content)})
        with self.assertRaisesRegex(importer.EvidenceError, "does not attest"):
            importer.verify_artifacts(record, self.storage, self.repo)

        record = fixture_record(self.storage, self.repo)
        receipt_path = self.storage / "archive-v1/pc1-v1-registry-receipt.json"
        receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
        receipt["storage_relative_path"] = "other/archive-v1/v7-workcuts-v1.jsonl"
        content = (json.dumps(receipt, sort_keys=True) + "\n").encode()
        receipt_path.write_bytes(content)
        item = next(item for item in record["artifacts"] if item["kind"] == "archived_v1_pc1_receipt")
        item.update({"sha256": hashlib.sha256(content).hexdigest(), "size_bytes": len(content)})
        with self.assertRaisesRegex(importer.EvidenceError, "does not attest"):
            importer.verify_artifacts(record, self.storage, self.repo)

    def test_v1_schema_is_rejected_by_v2_consumer(self):
        record = fixture_record(self.storage, self.repo)
        record["schema"] = "nexora-creative-v7-production-evidence-v1"
        with self.assertRaisesRegex(importer.EvidenceError, "schema 2 only"):
            importer.validate_record(record)

    def test_lineage_can_only_reference_v2_records(self):
        record = fixture_record(self.storage, self.repo)
        record["lineage"] = ["v7.workcut.opus.r8c"]
        with self.assertRaisesRegex(importer.EvidenceError, "V2 records only"):
            importer.validate_record(record)
        record = fixture_record(self.storage, self.repo)
        record["lineage"] = ["v7.workcut.opus.r8c.v2", "v7.workcut.opus.r8c.v2"]
        with self.assertRaisesRegex(importer.EvidenceError, "duplicate parent ids"):
            importer.validate_record(record)

    def test_missing_lineage_parent_is_refused_before_append(self):
        record = fixture_record(self.storage, self.repo)
        record["lineage"] = ["v7.workcut.opus.r8c.v2"]
        with self.assertRaisesRegex(importer.EvidenceError, "lineage parent is absent"):
            importer.import_record(record, self.registry, self.storage, self.repo)
        self.assertFalse(self.registry.exists())

    def test_registry_rejects_dangling_lineage_on_readback(self):
        record = fixture_record(self.storage, self.repo)
        record["lineage"] = ["v7.workcut.opus.r8c.v2"]
        self.registry.write_text(json.dumps(record) + "\n", encoding="utf-8")
        with self.registry.open("rb") as stream:
            with self.assertRaisesRegex(importer.EvidenceError, "absent prior parent"):
                importer._load_registry(stream.fileno())

    def test_partial_append_failure_rolls_back_registry_bytes(self):
        record = fixture_record(self.storage, self.repo)
        real_write = importer.os.write
        calls = 0

        def partial_then_fail(fd, content):
            nonlocal calls
            calls += 1
            if calls == 1:
                return real_write(fd, content[:7])
            raise OSError("simulated append failure")

        with patch.object(importer.os, "write", side_effect=partial_then_fail):
            with self.assertRaisesRegex(OSError, "simulated append failure"):
                importer.import_record(record, self.registry, self.storage, self.repo)
        self.assertEqual(self.registry.read_bytes(), b"")
        action, _ = importer.import_record(record, self.registry, self.storage, self.repo)
        self.assertEqual(action, "imported")

    def test_no_approval_or_memory_promotion(self):
        record = fixture_record(self.storage, self.repo)
        record["memory_promotion"] = "candidate"
        with self.assertRaisesRegex(importer.EvidenceError, "cannot promote"):
            importer.validate_record(record)
        record = fixture_record(self.storage, self.repo)
        record["founder_review"] = {"status": "approved"}
        with self.assertRaisesRegex(importer.EvidenceError, "remain pending"):
            importer.validate_record(record)

    def test_registry_is_strict_v2_and_outside_professor_loader_path(self):
        record = fixture_record(self.storage, self.repo)
        legacy = dict(record, schema="nexora-creative-v7-production-evidence-v1")
        legacy_registry = self.base / "legacy.jsonl"
        legacy_registry.write_text(json.dumps(legacy) + "\n", encoding="utf-8")
        with legacy_registry.open("rb") as fd:
            with self.assertRaisesRegex(importer.EvidenceError, "schema 2 only"):
                importer._load_registry(fd.fileno())

        professor_dir = (REPO_ROOT / "app/server/nexora/memoire/professeur").resolve()
        self.assertFalse(importer.DEFAULT_REGISTRY.resolve().is_relative_to(professor_dir))
        loader = (REPO_ROOT / "app/server/nexora/montage/memoires.ts").read_text(encoding="utf-8")
        self.assertIn("join(DOSSIER, 'professeur')", loader)
        self.assertIn("filter((f) => f.endsWith('.json'))", loader)
        self.assertEqual(importer.DEFAULT_REGISTRY.suffix, ".jsonl")


if __name__ == "__main__":
    unittest.main()
