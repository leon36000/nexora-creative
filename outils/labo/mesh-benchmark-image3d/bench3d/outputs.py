"""Exclusive, portable JSON/text outputs."""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any


class OutputExistsError(FileExistsError):
    pass


def dumps(obj: Any) -> str:
    """Portable, deterministic JSON text (LF newlines, sorted keys)."""
    return json.dumps(obj, indent=2, sort_keys=True, ensure_ascii=True) + "\n"


def write_exclusive(path: Path, text: str) -> None:
    """Create `path` exclusively. Never overwrite; never partially write."""
    path = Path(path)
    try:
        fd = os.open(str(path), os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
    except FileExistsError:
        raise OutputExistsError("refusing to overwrite existing file: %s" % path)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(text)
            fh.flush()
            os.fsync(fh.fileno())
    except BaseException:
        try:
            path.unlink()
        except OSError:
            pass
        raise


def relative_portable(path: Path, base: Path) -> str:
    """Return a POSIX relative path from base when possible, else the name."""
    try:
        rel = os.path.relpath(str(Path(path).resolve()), str(Path(base).resolve()))
    except ValueError:
        return Path(path).name
    return Path(rel).as_posix()


def prepare_outdir(out_dir: Path, inputs) -> Path:
    """Create out_dir if needed; refuse if it overlaps any input file's dir."""
    out_dir = Path(out_dir)
    if out_dir.exists():
        raise OutputExistsError("refusing to overwrite existing output directory: %s" % out_dir)
    real_out = Path(os.path.realpath(out_dir)) if out_dir.exists() else out_dir
    for inp in inputs:
        inp_real = Path(os.path.realpath(inp))
        if real_out.resolve() == inp_real.resolve():
            raise OutputExistsError("output dir would equal an input file: %s" % inp)
    out_dir.mkdir(parents=True, mode=0o700, exist_ok=False)
    return out_dir
