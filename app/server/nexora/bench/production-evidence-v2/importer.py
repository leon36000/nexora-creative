#!/usr/bin/env python3
"""Importer strict d'un registre d'observations V2, sans intégration à la mémoire AMD.

Le registre ne contient que des preuves de workcuts explicitement non promues. Il est
séparé du corpus AMD et des chargeurs de mémoire professeur. Les références de V1
pointent vers une archive immuable; aucun lecteur V1 n'est inclus dans ce module.

Usage : python3 importer.py RECORD.json --registry REGISTRY.jsonl
        --storage-root /path/to/Storage/Nexora --repo-root /path/to/repository
"""
from __future__ import annotations

import argparse
import fcntl
import hashlib
import json
import os
import re
import stat
import sys
from pathlib import Path, PurePosixPath
from typing import Any


SCHEMA = "nexora-creative-v7-production-evidence-v2"
DEFAULT_REGISTRY = Path(__file__).with_name("v7-workcuts-v2.jsonl")
TEAM_NAMES = {"deepseek", "gemini", "muse", "opus"}
V1_RECORD_ID = re.compile(r"^v7\.workcut\.(deepseek|gemini|muse|opus)\.(?:r1|r8c|r8d)$")
RECORD_ID = re.compile(r"^v7\.workcut\.(deepseek|gemini|muse|opus)\.(?:r1|r8c|r8d)\.v2$")
SHA256 = re.compile(r"^[0-9a-f]{64}$")
AMD2_BRIEF_ID = re.compile(r"AMD2-\d{3}", re.ASCII)
RECORD_FIELDS = {
    "schema", "record_id", "team", "edition", "team_role", "status",
    "amd2_brief_id", "amd2_corpus_sha256", "artifacts", "seed_reconciliation",
    "observations", "founder_review", "memory_promotion", "lineage",
    "replaces_v1_record", "record_sha256",
}
ARTIFACT_FIELDS = {"root", "path", "sha256", "size_bytes", "kind"}
SEED_FIELDS = {"plan_id", "seed_kind", "declared", "used", "texte_brut", "used_source", "state"}


class EvidenceError(ValueError):
    """Entrée, preuve ou registre incohérent."""


def _nonempty(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _int_or_none(value: Any) -> bool:
    return value is None or (isinstance(value, int) and not isinstance(value, bool))


def _reject_duplicate_json_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise EvidenceError(f"duplicate JSON object key: {key}")
        result[key] = value
    return result


def _reject_nonstandard_json_constant(value: str) -> None:
    raise EvidenceError(f"non-standard JSON constant: {value}")


def _strict_json_loads(text: str) -> Any:
    try:
        return json.loads(
            text,
            object_pairs_hook=_reject_duplicate_json_keys,
            parse_constant=_reject_nonstandard_json_constant,
        )
    except json.JSONDecodeError as exc:
        raise EvidenceError("invalid JSON") from exc


def _canonical_bytes(record: dict[str, Any]) -> bytes:
    payload = {key: value for key, value in record.items() if key != "record_sha256"}
    return json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def record_digest(record: dict[str, Any]) -> str:
    return hashlib.sha256(_canonical_bytes(record)).hexdigest()


def _expected_seed_state(declared: int | None, used: int | None) -> str:
    if used is None:
        return "unknown"
    if declared is not None and used != declared:
        return "discordant"
    return "known"


def _validate_record_shape(record: Any) -> dict[str, Any]:
    if not isinstance(record, dict):
        raise EvidenceError("record must be an object")
    unknown = set(record) - RECORD_FIELDS
    if unknown:
        raise EvidenceError("unknown record fields: " + ", ".join(sorted(unknown)))
    missing = (RECORD_FIELDS - {"record_sha256"}) - set(record)
    if missing:
        raise EvidenceError("missing record fields: " + ", ".join(sorted(missing)))
    if record["schema"] != SCHEMA:
        raise EvidenceError("unsupported evidence schema; V2 registry accepts schema 2 only")
    return record


def _validate_identity(record: dict[str, Any]) -> tuple[str, str]:
    record_id = record["record_id"]
    match = RECORD_ID.fullmatch(record_id) if isinstance(record_id, str) else None
    if not match:
        raise EvidenceError("invalid V2 record_id")
    team = record["team"]
    if not isinstance(team, str) or team not in TEAM_NAMES or match.group(1) != team:
        raise EvidenceError("team and record_id do not agree")
    if not _nonempty(record["edition"]):
        raise EvidenceError("edition must be nonempty")
    if record["team_role"] != "independent_team_not_confirmed_professor":
        raise EvidenceError("team_role must not assert professor approval")
    if record["status"] != "codex_machine_observation_unjudged":
        raise EvidenceError("status must preserve unjudged machine-observation state")
    return team, record_id


def _validate_review_and_corpus_fields(record: dict[str, Any]) -> None:
    if record["founder_review"] != {"status": "pending"}:
        raise EvidenceError("founder_review must remain pending")
    if record["memory_promotion"] != "none":
        raise EvidenceError("evidence records cannot promote memory")
    brief_id = record["amd2_brief_id"]
    if brief_id is not None and not (isinstance(brief_id, str) and AMD2_BRIEF_ID.fullmatch(brief_id)):
        raise EvidenceError("amd2_brief_id must be null or an AMD2-### id")
    corpus_sha = record["amd2_corpus_sha256"]
    if not isinstance(corpus_sha, str) or not SHA256.fullmatch(corpus_sha):
        raise EvidenceError("amd2_corpus_sha256 is invalid")


def _validate_v1_replacement(record: dict[str, Any], team: str, record_id: str) -> dict[str, Any]:
    replaced = record["replaces_v1_record"]
    if not isinstance(replaced, dict) or set(replaced) != {"record_id", "record_sha256", "registry_sha256"}:
        raise EvidenceError("replaces_v1_record has an invalid shape")
    replaced_id = replaced["record_id"]
    replaced_match = V1_RECORD_ID.fullmatch(replaced_id) if isinstance(replaced_id, str) else None
    if (not replaced_match or replaced_match.group(1) != team
            or replaced_id + ".v2" != record_id):
        raise EvidenceError("V2 record must link its matching archived V1 record")
    if not isinstance(replaced["record_sha256"], str) or not SHA256.fullmatch(replaced["record_sha256"]):
        raise EvidenceError("replaces_v1_record.record_sha256 is invalid")
    if not isinstance(replaced["registry_sha256"], str) or not SHA256.fullmatch(replaced["registry_sha256"]):
        raise EvidenceError("replaces_v1_record.registry_sha256 is invalid")
    return replaced


def _validate_artifact_path(artifact: dict[str, Any], index: int) -> None:
    path = artifact["path"]
    if not isinstance(path, str) or not path or "\\" in path:
        raise EvidenceError(f"artifacts[{index}].path must be a canonical relative path")
    posix = PurePosixPath(path)
    if posix.is_absolute() or str(posix) != path or any(part in {".", ".."} for part in posix.parts):
        raise EvidenceError(f"artifacts[{index}].path escapes its declared root")


def _validate_artifact_shape(artifact: Any, index: int) -> None:
    if not isinstance(artifact, dict) or set(artifact) != ARTIFACT_FIELDS:
        raise EvidenceError(f"artifacts[{index}] has an invalid shape")
    if not isinstance(artifact["root"], str) or artifact["root"] not in {"storage", "repo", "creative_data"}:
        raise EvidenceError(f"artifacts[{index}].root is invalid")
    _validate_artifact_path(artifact, index)
    if not isinstance(artifact["sha256"], str) or not SHA256.fullmatch(artifact["sha256"]):
        raise EvidenceError(f"artifacts[{index}].sha256 is invalid")
    size = artifact["size_bytes"]
    if not isinstance(size, int) or isinstance(size, bool) or size < 0:
        raise EvidenceError(f"artifacts[{index}].size_bytes is invalid")
    if not _nonempty(artifact["kind"]):
        raise EvidenceError(f"artifacts[{index}].kind is invalid")


def _validate_artifact_links(artifacts: list[dict[str, Any]], corpus_sha: str,
                             replaced: dict[str, Any]) -> None:
    corpus_artifacts = [artifact for artifact in artifacts if artifact["kind"] == "amd2_corpus"]
    if (len(corpus_artifacts) != 1 or corpus_artifacts[0]["sha256"] != corpus_sha
            or corpus_artifacts[0]["root"] != "repo"
            or corpus_artifacts[0]["path"] != "app/server/nexora/bench/corpus-amd-v2/corpus.json"):
        raise EvidenceError("one canonical AMD2 corpus artifact is required as context")
    archive_artifacts = [artifact for artifact in artifacts if artifact["kind"] == "archived_v1_registry"]
    if (len(archive_artifacts) != 1 or archive_artifacts[0]["root"] != "storage"
            or not archive_artifacts[0]["path"].endswith("archive-v1/v7-workcuts-v1.jsonl")
            or archive_artifacts[0]["sha256"] != replaced["registry_sha256"]):
        raise EvidenceError("the immutable V1 archive must be referenced with its recorded SHA-256")
    receipt_artifacts = [artifact for artifact in artifacts if artifact["kind"] == "archived_v1_pc1_receipt"]
    if (len(receipt_artifacts) != 1 or receipt_artifacts[0]["root"] != "storage"
            or not receipt_artifacts[0]["path"].endswith("archive-v1/pc1-v1-registry-receipt.json")):
        raise EvidenceError("one V1 archive verification receipt must be referenced")


def _validate_artifacts(artifacts: Any, corpus_sha: str,
                        replaced: dict[str, Any]) -> None:
    if not isinstance(artifacts, list) or not artifacts:
        raise EvidenceError("artifacts must be a nonempty array")
    artifact_paths: set[tuple[str, str]] = set()
    for index, artifact in enumerate(artifacts):
        _validate_artifact_shape(artifact, index)
        key = (artifact["root"], artifact["path"])
        if key in artifact_paths:
            raise EvidenceError(f"duplicate artifact path: {artifact['root']}:{artifact['path']}")
        artifact_paths.add(key)
    _validate_artifact_links(artifacts, corpus_sha, replaced)


def _validate_seed(seed: Any, index: int) -> tuple[str, str]:
    if not isinstance(seed, dict) or set(seed) != SEED_FIELDS:
        raise EvidenceError(f"seed_reconciliation[{index}] has an invalid shape")
    if (not _nonempty(seed["plan_id"]) or seed["seed_kind"] != "keyframe"
            or not _nonempty(seed["used_source"])):
        raise EvidenceError(f"seed_reconciliation[{index}] is missing its source")
    if not _int_or_none(seed["declared"]) or not _int_or_none(seed["used"]):
        raise EvidenceError(f"seed_reconciliation[{index}] numeric seed values must be integer or null")
    raw_text = seed["texte_brut"]
    if raw_text is not None and not _nonempty(raw_text):
        raise EvidenceError(f"seed_reconciliation[{index}].texte_brut must be nonempty or null")
    if seed["used"] is not None and raw_text is not None:
        raise EvidenceError(f"seed_reconciliation[{index}] cannot claim a typed value and raw text together")
    if seed["state"] != _expected_seed_state(seed["declared"], seed["used"]):
        raise EvidenceError(f"seed_reconciliation[{index}].state does not match typed values")
    return seed["plan_id"], seed["seed_kind"]


def _validate_seeds(seeds: Any) -> None:
    if not isinstance(seeds, list):
        raise EvidenceError("seed_reconciliation must be an array")
    seed_keys = [_validate_seed(seed, index) for index, seed in enumerate(seeds)]
    if len(seed_keys) != len(set(seed_keys)):
        raise EvidenceError("seed_reconciliation has duplicate (plan_id, seed_kind) entries")


def _validate_observations(observations: Any) -> None:
    if not isinstance(observations, list) or not observations:
        raise EvidenceError("observations must be a nonempty array")
    for index, observation in enumerate(observations):
        if (not isinstance(observation, dict) or set(observation) != {"authority", "text"}
                or observation["authority"] != "codex_machine" or not _nonempty(observation["text"])):
            raise EvidenceError(f"observations[{index}] must be an explicit Codex machine observation")


def _validate_lineage(lineage: Any, record_id: str) -> None:
    if not isinstance(lineage, list):
        raise EvidenceError("lineage must be an array")
    invalid = [item for item in lineage if not isinstance(item, str) or not RECORD_ID.fullmatch(item)]
    if invalid:
        raise EvidenceError("lineage may reference V2 records only")
    if len(lineage) != len(set(lineage)):
        raise EvidenceError("lineage contains duplicate parent ids")
    if record_id in lineage:
        raise EvidenceError("record cannot be its own lineage parent")


def validate_record(record: Any) -> dict[str, Any]:
    record = _validate_record_shape(record)
    team, record_id = _validate_identity(record)
    _validate_review_and_corpus_fields(record)
    replaced = _validate_v1_replacement(record, team, record_id)
    _validate_artifacts(record["artifacts"], record["amd2_corpus_sha256"], replaced)
    _validate_seeds(record["seed_reconciliation"])
    _validate_observations(record["observations"])
    _validate_lineage(record["lineage"], record_id)
    declared_digest = record.get("record_sha256")
    actual_digest = record_digest(record)
    if declared_digest is not None and declared_digest != actual_digest:
        raise EvidenceError("record_sha256 does not match canonical record content")
    return {**record, "record_sha256": actual_digest}


def _digest_file(path: Path) -> tuple[str, int]:
    digest = hashlib.sha256()
    size = 0
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            size += len(chunk)
            digest.update(chunk)
    return digest.hexdigest(), size


def _artifact_ref(record: dict[str, Any], kind: str) -> dict[str, Any]:
    return next(item for item in record["artifacts"] if item["kind"] == kind)


def _archived_v1_matches(path: Path, replaced_id: str) -> list[dict[str, Any]]:
    try:
        data = path.read_text(encoding="utf-8")
        if data and not data.endswith("\n"):
            raise EvidenceError("archived V1 JSONL ends with an incomplete row")
        matches: list[dict[str, Any]] = []
        for line_no, line in enumerate(data.splitlines(), start=1):
            if not line:
                raise EvidenceError(f"archived V1 JSONL has a blank row at {line_no}")
            try:
                archived = json.loads(line)
            except json.JSONDecodeError as exc:
                raise EvidenceError(f"archived V1 JSONL has invalid JSON at row {line_no}") from exc
            if not isinstance(archived, dict):
                raise EvidenceError(f"archived V1 JSONL row {line_no} is not an object")
            if archived.get("record_id") == replaced_id:
                matches.append(archived)
    except (UnicodeDecodeError, OSError) as exc:
        raise EvidenceError("archived V1 registry cannot be read") from exc
    return matches


def _check_archived_v1_record(record: dict[str, Any], archive_path: Path) -> None:
    replaced = record["replaces_v1_record"]
    matches = _archived_v1_matches(archive_path, replaced["record_id"])
    if len(matches) != 1:
        raise EvidenceError("replaced V1 record id must occur exactly once in the immutable archive")
    archived = matches[0]
    actual_record_sha = record_digest(archived)
    if (not isinstance(archived.get("record_sha256"), str)
            or not SHA256.fullmatch(archived["record_sha256"])
            or archived["record_sha256"] != actual_record_sha
            or archived["record_sha256"] != replaced["record_sha256"]):
        raise EvidenceError("replaced V1 record digest does not match the archived row")


def _receipt_bytes_attested(receipt: dict[str, Any], archive_ref: dict[str, Any],
                            receipt_ref: dict[str, Any]) -> bool:
    archive_path = PurePosixPath(archive_ref["path"])
    expected_relative = (PurePosixPath("archive-v1") / archive_path.name).as_posix()
    sizes = (receipt.get("storage_size_bytes"), receipt.get("pc1_size_bytes"))
    if any(not isinstance(size, int) or isinstance(size, bool) for size in sizes):
        return False
    return (
        receipt.get("schema") == "nexora-v7-registry-archive-receipt-v1"
        and receipt.get("storage_sha256") == archive_ref["sha256"]
        and receipt.get("pc1_sha256") == archive_ref["sha256"]
        and sizes[0] == archive_ref["size_bytes"]
        and sizes[1] == archive_ref["size_bytes"]
        and receipt.get("storage_relative_path") == expected_relative
        and PurePosixPath(receipt_ref["path"]).parent == archive_path.parent
        and isinstance(receipt.get("pc1_path"), str)
        and receipt["pc1_path"].startswith("/run/media/pc1/Infrastructure/")
        and _nonempty(receipt.get("verified_at_utc"))
        and _nonempty(receipt.get("verification"))
    )


def _check_v1_receipt(archive_ref: dict[str, Any], receipt_ref: dict[str, Any],
                      receipt_path: Path) -> None:
    try:
        receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError, OSError) as exc:
        raise EvidenceError("V1 archive receipt is not readable JSON") from exc
    if not isinstance(receipt, dict) or not _receipt_bytes_attested(receipt, archive_ref, receipt_ref):
        raise EvidenceError("V1 archive receipt does not attest the referenced Storage and pc1 bytes")


def _verify_archived_v1_link(record: dict[str, Any], storage_root: Path) -> None:
    archive_ref = _artifact_ref(record, "archived_v1_registry")
    receipt_ref = _artifact_ref(record, "archived_v1_pc1_receipt")
    _check_archived_v1_record(record, storage_root / PurePosixPath(archive_ref["path"]))
    _check_v1_receipt(archive_ref, receipt_ref, storage_root / PurePosixPath(receipt_ref["path"]))


def _verify_amd2_brief_membership(record: dict[str, Any], repo_root: Path) -> None:
    brief_id = record["amd2_brief_id"]
    if brief_id is None:
        return
    corpus_path = repo_root / "app/server/nexora/bench/corpus-amd-v2/corpus.json"
    try:
        corpus = _strict_json_loads(corpus_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, EvidenceError) as exc:
        raise EvidenceError("referenced AMD2 corpus cannot be read as strict JSON") from exc
    if not isinstance(corpus, dict) or not isinstance(corpus.get("briefs"), list):
        raise EvidenceError("referenced AMD2 corpus has an invalid structure")
    briefs = corpus["briefs"]
    if any(not isinstance(brief, dict) or not _nonempty(brief.get("id")) for brief in briefs):
        raise EvidenceError("referenced AMD2 corpus has an invalid brief entry")
    if brief_id not in {brief["id"] for brief in briefs}:
        raise EvidenceError("amd2_brief_id is absent from the referenced AMD2 corpus")


def _resolve_artifact(artifact: dict[str, Any], roots: dict[str, Path]) -> Path:
    root_name, path = artifact["root"], artifact["path"]
    if root_name not in roots:
        raise EvidenceError(f"artifact root was not supplied: {root_name}")
    root = roots[root_name]
    relative = PurePosixPath(path)
    component = root
    for part in relative.parts:
        component = component / part
        if component.is_symlink():
            raise EvidenceError(f"artifact path must not traverse a symlink: {root_name}:{path}")
    try:
        resolved = (root / relative).resolve(strict=True)
    except OSError as exc:
        raise EvidenceError(f"artifact is unavailable: {root_name}:{path}") from exc
    if not resolved.is_relative_to(root) or not resolved.is_file():
        raise EvidenceError(f"artifact is outside its root or not a regular file: {root_name}:{path}")
    return resolved


def _check_artifact(artifact: dict[str, Any], roots: dict[str, Path]) -> None:
    resolved = _resolve_artifact(artifact, roots)
    actual_sha, actual_size = _digest_file(resolved)
    if actual_sha != artifact["sha256"] or actual_size != artifact["size_bytes"]:
        raise EvidenceError(f"artifact hash/size mismatch: {artifact['root']}:{artifact['path']}")


def verify_artifacts(record: dict[str, Any], storage_root: Path, repo_root: Path,
                     creative_data_root: Path | None = None) -> None:
    roots = {"storage": storage_root.resolve(strict=True), "repo": repo_root.resolve(strict=True)}
    if creative_data_root is not None:
        roots["creative_data"] = creative_data_root.resolve(strict=True)
    for artifact in record["artifacts"]:
        _check_artifact(artifact, roots)
    _verify_amd2_brief_membership(record, roots["repo"])
    _verify_archived_v1_link(record, roots["storage"])


def _load_registry(fd: int) -> tuple[dict[str, dict[str, Any]], int]:
    os.lseek(fd, 0, os.SEEK_SET)
    chunks: list[bytes] = []
    while True:
        part = os.read(fd, 1024 * 1024)
        if not part:
            break
        chunks.append(part)
    data = b"".join(chunks)
    if data and not data.endswith(b"\n"):
        raise EvidenceError("registry ends with an incomplete JSONL record")
    records: dict[str, dict[str, Any]] = {}
    for line_no, line in enumerate(data.splitlines(), start=1):
        if not line:
            raise EvidenceError(f"blank registry line at {line_no}")
        try:
            item = validate_record(_strict_json_loads(line.decode("utf-8")))
        except (UnicodeDecodeError, EvidenceError) as exc:
            raise EvidenceError(f"invalid V2 registry line {line_no}: {exc}") from exc
        record_id = item["record_id"]
        if record_id in records:
            raise EvidenceError(f"duplicate record_id in V2 registry: {record_id}")
        missing_parents = [parent for parent in item["lineage"] if parent not in records]
        if missing_parents:
            raise EvidenceError(f"invalid V2 registry lineage at line {line_no}: absent prior parent")
        records[record_id] = item
    return records, len(data)


def _resolve_registry_target(registry_path: Path, repo_root: Path) -> Path:
    resolved = registry_path.resolve(strict=False)
    if resolved.suffix != ".jsonl":
        raise EvidenceError("active V2 registry path must end in .jsonl")
    memory_dir = (repo_root.resolve(strict=True) / "app/server/nexora/memoire").resolve(strict=False)
    if resolved.is_relative_to(memory_dir):
        raise EvidenceError("production evidence cannot be written inside any runtime memory directory")
    return resolved


def _append_locked(fd: int, encoded: bytes, original_size: int) -> None:
    view = memoryview(encoded)
    try:
        while view:
            written = os.write(fd, view)
            if written <= 0:
                raise EvidenceError("append made no progress")
            view = view[written:]
        os.fsync(fd)
    except BaseException:
        os.ftruncate(fd, original_size)
        os.fsync(fd)
        raise


def _append_record(fd: int, item: dict[str, Any], storage_root: Path, repo_root: Path,
                   creative_data_root: Path | None) -> str:
    existing, original_size = _load_registry(fd)
    current = existing.get(item["record_id"])
    if current is not None:
        if current["record_sha256"] == item["record_sha256"]:
            return "already_present"
        raise EvidenceError(f"record_id conflict with different SHA-256: {item['record_id']}")
    missing_parents = [record_id for record_id in item["lineage"] if record_id not in existing]
    if missing_parents:
        raise EvidenceError("lineage parent is absent from the V2 registry: " + ", ".join(missing_parents))
    verify_artifacts(item, storage_root, repo_root, creative_data_root)
    encoded = (json.dumps(item, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")
    _append_locked(fd, encoded, original_size)
    return "imported"


def _check_registry_preconditions(lineage: list[str], registry_path: Path,
                                  repo_root: Path) -> Path:
    # Ordre historique des erreurs : suffixe et dossier mémoire d'abord, puis
    # parent lineage absent si le registre n'existe pas, puis dossier parent absent.
    resolved = _resolve_registry_target(registry_path, repo_root)
    if lineage and not resolved.exists():
        raise EvidenceError("lineage parent is absent because the V2 registry does not exist")
    if not resolved.parent.is_dir():
        raise EvidenceError("V2 registry parent directory must already exist")
    return resolved


def import_record(record: Any, registry_path: Path, storage_root: Path, repo_root: Path,
                  creative_data_root: Path | None = None) -> tuple[str, dict[str, Any]]:
    item = validate_record(record)
    verify_artifacts(item, storage_root, repo_root, creative_data_root)
    registry_path = _check_registry_preconditions(item["lineage"], registry_path, repo_root)
    flags = os.O_CREAT | os.O_RDWR | os.O_APPEND
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    if hasattr(os, "O_CLOEXEC"):
        flags |= os.O_CLOEXEC
    fd = os.open(registry_path, flags, 0o600)
    try:
        if not stat.S_ISREG(os.fstat(fd).st_mode):
            raise EvidenceError("registry path is not a regular file")
        fcntl.flock(fd, fcntl.LOCK_EX)
        return _append_record(fd, item, storage_root, repo_root, creative_data_root), item
    finally:
        try:
            fcntl.flock(fd, fcntl.LOCK_UN)
        finally:
            os.close(fd)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("record", type=Path, help="JSON V2 record to validate and import")
    parser.add_argument("--registry", type=Path, default=DEFAULT_REGISTRY, help="append-only V2 JSONL registry")
    parser.add_argument("--storage-root", required=True, type=Path, help="root for Storage-relative artifacts")
    parser.add_argument("--repo-root", required=True, type=Path, help="root for repository-relative artifacts")
    parser.add_argument("--creative-data-root", type=Path, help="optional root for persistent creative-data inputs")
    args = parser.parse_args(argv)
    try:
        with args.record.open("r", encoding="utf-8") as stream:
            record = _strict_json_loads(stream.read())
        result, item = import_record(record, args.registry, args.storage_root, args.repo_root, args.creative_data_root)
    except (OSError, UnicodeDecodeError, EvidenceError) as exc:
        print(f"ERREUR: {exc}", file=sys.stderr)
        return 2
    print(json.dumps({"result": result, "record_id": item["record_id"], "record_sha256": item["record_sha256"], "verified_artifacts": len(item["artifacts"])}, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
