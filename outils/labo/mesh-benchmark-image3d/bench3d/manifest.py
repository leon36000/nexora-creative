"""Manifest loading and validation.

Manifest schema (JSON object):
{
  "version": 1,                      # optional, must be 1 if present
  "seed": 20261109,                  # optional int, bench-level default seed
  "image_root": ".",                 # optional, default: directory of the manifest
  "arms": [                          # exactly >= 3 named arms
    {"id": "nexora", "label": "Moteur Nexora", "kind": "nexora", "notes": "..."},
    {"id": "alt-a",  "label": "Alternative A", "kind": "alternative"},
    {"id": "alt-b",  "label": "Alternative B", "kind": "alternative"}
  ],
  "subjects": [                      # >= 20 items
    {"id": "s001", "image": "images/s001.png", "sha256": "<64 hex>",
     "category": "object", "notes": "..."}
  ]
}

All referenced images must be regular files located inside image_root
(symlinks are resolved). `sha256` is verified against the actual file.
No field is guessed: missing required fields are errors.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

MIN_SUBJECTS = 20
MIN_ARMS = 3

_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$")
_SHA_RE = re.compile(r"^[0-9a-f]{64}$")


class ManifestError(ValueError):
    """Raised when a manifest is invalid. `problems` lists all found issues."""

    def __init__(self, problems):
        self.problems = list(problems)
        super().__init__("invalid manifest:\n- " + "\n- ".join(self.problems))


@dataclass(frozen=True)
class Subject:
    id: str
    image_rel: str      # POSIX-relative path as declared in the manifest
    abs_path: Path
    size: int
    sha256: str
    category: Optional[str] = None
    notes: Optional[str] = None


@dataclass(frozen=True)
class Arm:
    id: str
    label: str
    kind: Optional[str] = None
    notes: Optional[str] = None


@dataclass
class Manifest:
    path: Path
    root: Path
    seed: Optional[int]
    source_sha256: str
    arms: List[Arm] = field(default_factory=list)
    subjects: List[Subject] = field(default_factory=list)


def sha256_file(path: Path, chunk: int = 1 << 20) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for block in iter(lambda: fh.read(chunk), b""):
            h.update(block)
    return h.hexdigest()


def _refuse_sensitive_path(path: Path) -> None:
    """Reject common secret locations and filenames without opening them."""
    for part in path.parts:
        name = part.casefold()
        if (name in {'.ssh', '.aws', '.gnupg', '.kube', '.docker', '.azure', '.config', '.git', '.codex', '.agents', '.npmrc', '.pypirc', '.netrc', '.git-credentials', 'authorized_keys', 'known_hosts', 'credentials', 'credentials.json', 'token.json'}
                or name == '.env' or name.startswith('.env.')
                or name.startswith(('id_rsa', 'id_dsa', 'id_ecdsa', 'id_ed25519'))
                or name.endswith(('.env', '.pem', '.key', '.p8', '.ppk', '.p12', '.pfx', '.kdbx', '.keystore'))):
            raise ValueError('sensitive path is not an accepted input')


def _image_sha256(path: Path) -> str:
    """Check a supported file signature before hashing; this is not a decoder."""
    extension = path.suffix.casefold()
    if extension not in {'.png', '.jpg', '.jpeg', '.webp'}:
        raise ValueError('unsupported image extension')
    digest = hashlib.sha256()
    with open(path, 'rb') as fh:
        header = fh.read(12)
        valid = ((extension == '.png' and header.startswith(b'\x89PNG\r\n\x1a\n'))
                 or (extension in {'.jpg', '.jpeg'} and header.startswith(b'\xff\xd8\xff'))
                 or (extension == '.webp' and len(header) == 12 and header[:4] == b'RIFF' and header[8:12] == b'WEBP'))
        if not valid:
            raise ValueError('image signature does not match extension')
        digest.update(header)
        for block in iter(lambda: fh.read(1 << 20), b''):
            digest.update(block)
    return digest.hexdigest()


def normalize_rel(raw: str) -> str:
    """Validate a relative path; return POSIX form. Raises ValueError."""
    if not isinstance(raw, str) or not raw.strip():
        raise ValueError("image path must be a non-empty string")
    if raw != raw.strip():
        raise ValueError("image path must not have leading/trailing whitespace")
    if "\x00" in raw:
        raise ValueError("image path contains NUL")
    norm = raw.replace("\\", "/")
    p = Path(norm)
    if p.is_absolute() or norm.startswith("/"):
        raise ValueError("image path must be relative, got %r" % raw)
    if re.match(r"^[A-Za-z]:", norm):
        raise ValueError("image path must not contain a drive letter: %r" % raw)
    parts = norm.split("/")
    if any(part in ("", ".", "..") for part in parts):
        raise ValueError("image path must not contain '', '.' or '..': %r" % raw)
    return "/".join(parts)


def _resolve_inside(root: Path, rel: str) -> Path:
    """Resolve root/rel and ensure the real path stays inside real root."""
    real_root = Path(os.path.realpath(root))
    candidate = root / Path(rel)
    real = Path(os.path.realpath(candidate))
    try:
        real.relative_to(real_root)
    except ValueError:
        raise ValueError("image path escapes image_root: %r" % rel)
    return real


def _get(d: Any, key: str, where: str, problems: List[str], required=True, typ=None):
    if not isinstance(d, dict):
        problems.append("%s: expected an object" % where)
        return None
    if key not in d:
        if required:
            problems.append("%s: missing required field %r" % (where, key))
        return None
    val = d[key]
    if typ is not None and not isinstance(val, typ):
        problems.append("%s.%s: expected %s" % (where, key, getattr(typ, "__name__", typ)))
        return None
    return val


def _check_seed(seed: Any, where: str, problems: List[str]) -> Optional[int]:
    if seed is None:
        return None
    if isinstance(seed, bool) or not isinstance(seed, int):
        problems.append("%s: seed must be an integer" % where)
        return None
    return seed


def load_manifest(manifest_path: Path) -> Manifest:
    """Load and fully validate a manifest. Raises ManifestError with all problems."""
    manifest_path = Path(manifest_path)
    problems: List[str] = []
    try:
        _refuse_sensitive_path(manifest_path)
        _refuse_sensitive_path(manifest_path.resolve())
    except ValueError as exc:
        raise ManifestError([str(exc)])
    try:
        source_bytes = manifest_path.read_bytes()
        text = source_bytes.decode("utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        raise ManifestError(["cannot read manifest %s: %s" % (manifest_path, exc)])
    try:
        raw = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ManifestError(["manifest is not valid JSON: %s" % exc])
    if not isinstance(raw, dict):
        raise ManifestError(["manifest root must be a JSON object"])

    version = raw.get("version", 1)
    if version != 1:
        problems.append("version: unsupported value %r (expected 1)" % (version,))

    base = manifest_path.resolve().parent
    root_raw = raw.get("image_root", ".")
    if not isinstance(root_raw, str):
        raise ManifestError(["image_root: must be a string"])
    root = Path(root_raw)
    if not Path(root_raw).is_absolute():
        root = base / root_raw
    if not root.is_dir():
        problems.append("image_root: not a directory: %s" % root)
    root = Path(os.path.realpath(root))

    seed = _check_seed(raw.get("seed"), "seed", problems)

    arms_raw = raw.get("arms")
    arms: List[Arm] = []
    if not isinstance(arms_raw, list):
        problems.append("arms: must be a list")
        arms_raw = []
    if len(arms_raw) < MIN_ARMS:
        problems.append("arms: need at least %d arms, got %d" % (MIN_ARMS, len(arms_raw)))
    seen_arms = set()
    for i, a in enumerate(arms_raw):
        where = "arms[%d]" % i
        aid = _get(a, "id", where, problems, typ=str)
        label = _get(a, "label", where, problems, typ=str)
        kind = _get(a, "kind", where, problems, required=False, typ=str)
        notes = _get(a, "notes", where, problems, required=False, typ=str)
        if kind is not None and kind not in ("nexora", "alternative"):
            problems.append("%s.kind: must be 'nexora' or 'alternative'" % where)
        if aid is not None:
            if not _ID_RE.fullmatch(aid):
                problems.append("%s.id: invalid id %r" % (where, aid))
            elif aid in seen_arms:
                problems.append("%s.id: duplicate arm id %r" % (where, aid))
            seen_arms.add(aid)
        if label is not None and not label.strip():
            problems.append("%s.label: must be non-empty" % where)
        if aid is not None and label is not None:
            arms.append(Arm(id=aid, label=label, kind=kind, notes=notes))
    n_nexora = sum(1 for a in arms if a.kind == "nexora")
    n_alt = sum(1 for a in arms if a.kind == "alternative")
    if n_nexora > 1:
        problems.append("arms: at most one arm may have kind nexora")
    if n_nexora != 1 or n_alt < 2:
        problems.append("arms: exactly one nexora and at least two alternative arms are required (found %d, %d)" % (n_nexora, n_alt))

    subjects_raw = raw.get("subjects")
    subjects: List[Subject] = []
    if not isinstance(subjects_raw, list):
        problems.append("subjects: must be a list")
        subjects_raw = []
    if len(subjects_raw) < MIN_SUBJECTS:
        problems.append("subjects: need at least %d, got %d" % (MIN_SUBJECTS, len(subjects_raw)))
    seen_subjects = set()
    seen_images = set()
    seen_hashes = set()
    for i, s in enumerate(subjects_raw):
        where = "subjects[%d]" % i
        sid = _get(s, "id", where, problems, typ=str)
        img = _get(s, "image", where, problems, typ=str)
        sha = _get(s, "sha256", where, problems, typ=str)
        category = _get(s, "category", where, problems, required=False, typ=str)
        notes = _get(s, "notes", where, problems, required=False, typ=str)
        if sid is not None:
            if not _ID_RE.fullmatch(sid):
                problems.append("%s.id: invalid id %r" % (where, sid))
            elif sid in seen_subjects:
                problems.append("%s.id: duplicate subject id %r" % (where, sid))
            seen_subjects.add(sid)
        if sha is not None and not _SHA_RE.fullmatch(sha.lower()):
            problems.append("%s.sha256: not a 64-char lowercase hex digest" % where)
        if img is None or not root.is_dir():
            continue
        try:
            rel = normalize_rel(img)
        except ValueError as exc:
            problems.append("%s.image: %s" % (where, exc))
            continue
        key = rel.lower()
        if key in seen_images:
            problems.append("%s.image: duplicate image path %r" % (where, rel))
        seen_images.add(key)
        try:
            _refuse_sensitive_path(Path(rel))
            real = _resolve_inside(root, rel)
            _refuse_sensitive_path(real)
        except ValueError as exc:
            problems.append("%s.image: %s" % (where, exc))
            continue
        if not real.exists():
            problems.append("%s.image: file does not exist: %s" % (where, rel))
            continue
        if not real.is_file():
            problems.append("%s.image: not a regular file: %s" % (where, rel))
            continue
        size = real.stat().st_size
        if size == 0:
            problems.append("%s.image: file is empty: %s" % (where, rel))
        if sha is not None and _SHA_RE.fullmatch(sha.lower()):
            try:
                actual = _image_sha256(real)
            except (OSError, ValueError) as exc:
                problems.append("%s.image: %s" % (where, exc))
                continue
            if actual in seen_hashes:
                problems.append("%s.image: duplicate image bytes" % where)
            seen_hashes.add(actual)
            if actual != sha.lower():
                problems.append(
                    "%s.sha256: mismatch for %s" % (where, rel)
                )
        if sid is not None and _ID_RE.fullmatch(sid):
            subjects.append(Subject(id=sid, image_rel=rel, abs_path=real, size=size,
                                    sha256=sha.lower() if isinstance(sha, str) else "",
                                    category=category, notes=notes))

    if problems:
        raise ManifestError(problems)
    return Manifest(path=manifest_path, root=root, seed=seed, source_sha256=hashlib.sha256(source_bytes).hexdigest(), arms=arms, subjects=subjects)
