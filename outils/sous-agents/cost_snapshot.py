"""Réconciliation locale, en lecture seule, entre l'audit des appels et le journal de coûts JSONL."""

from __future__ import annotations

import argparse
import json
import math
import os
import re
import stat
import sys
import time
from decimal import Decimal
from typing import Any


ERROR_MESSAGE = "snapshot failed"
MAX_FILE_BYTES = 64 * 1024 * 1024
MAX_LINE_BYTES = 1024 * 1024
MAX_RECORDS = 250_000
MAX_DECIMAL_DIGITS = 1000
MAX_DECIMAL_EXPONENT = 1000
_RUN_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")


class SnapshotError(ValueError):
    """Erreur générique; ne contient jamais chemin, ligne, clé ni prompt."""

    def __init__(self) -> None:
        super().__init__(ERROR_MESSAGE)


def _fail() -> None:
    raise SnapshotError()


def _no_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            _fail()
        result[key] = value
    return result


def _reject_constant(_value: str) -> None:
    # Python's JSON decoder otherwise accepts NaN and Infinity, which JSON itself forbids.
    _fail()


def _parse_line(raw: bytes) -> dict[str, Any]:
    if not raw or len(raw) > MAX_LINE_BYTES:
        _fail()
    try:
        text = raw.decode("utf-8")
        value = json.loads(
            text,
            parse_float=Decimal,
            parse_int=int,
            parse_constant=_reject_constant,
            object_pairs_hook=_no_duplicate_keys,
        )
    except Exception:
        _fail()
    if not isinstance(value, dict):
        _fail()
    return value


def _read_jsonl(path: str | os.PathLike[str]) -> list[dict[str, Any]]:
    """Lit un fichier régulier borné. Le détail des erreurs d'E/S reste privé."""
    fd = -1
    try:
        flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0)
        flags |= getattr(os, "O_NONBLOCK", 0)
        fd = os.open(os.fspath(path), flags)
        if not stat.S_ISREG(os.fstat(fd).st_mode):
            _fail()
        with os.fdopen(fd, "rb", closefd=True) as stream:
            fd = -1
            if os.fstat(stream.fileno()).st_size > MAX_FILE_BYTES:
                _fail()
            data = stream.read(MAX_FILE_BYTES + 1)
    except Exception:
        if fd >= 0:
            try:
                os.close(fd)
            except OSError:
                pass
        _fail()

    if len(data) > MAX_FILE_BYTES:
        _fail()
    if not data:
        return []

    lines = data.split(b"\n")
    if lines[-1] == b"":  # trailing LF is the normal JSONL terminator
        lines.pop()
    if len(lines) > MAX_RECORDS:
        _fail()

    records: list[dict[str, Any]] = []
    for raw in lines:
        if raw.endswith(b"\r"):
            raw = raw[:-1]
        records.append(_parse_line(raw))
    return records


def _checked_decimal(value: Any) -> Decimal:
    if isinstance(value, bool):
        _fail()
    if isinstance(value, int):
        number = Decimal(value)
    elif isinstance(value, Decimal):
        number = value
    else:
        _fail()

    if not number.is_finite() or number < 0:
        _fail()
    parts = number.as_tuple()
    if len(parts.digits) > MAX_DECIMAL_DIGITS or abs(parts.exponent) > MAX_DECIMAL_EXPONENT:
        _fail()
    if not number.is_zero() and abs(number.adjusted()) > MAX_DECIMAL_EXPONENT:
        _fail()
    return number


def _format_exact_sum(values: list[Decimal]) -> str:
    """Somme sans contexte Decimal ni arrondi, rendue en notation décimale fixe."""
    if not values:
        return "0"
    scale = max(0, *(-value.as_tuple().exponent for value in values))
    total_units = 0
    for value in values:
        sign, digits, exponent = value.as_tuple()
        coefficient = 0
        for digit in digits:
            coefficient = coefficient * 10 + digit
        if coefficient == 0:
            continue
        shift = exponent + scale
        if shift < 0:
            _fail()
        total_units += (-coefficient if sign else coefficient) * (10**shift)

    sign = "-" if total_units < 0 else ""
    digits = str(abs(total_units))
    if scale == 0:
        return sign + digits
    if len(digits) <= scale:
        digits = "0" * (scale + 1 - len(digits)) + digits
    split = len(digits) - scale
    return sign + digits[:split] + "." + digits[split:]


def _audit_tags(audit_records: list[dict[str, Any]], run: str) -> list[str]:
    tags: list[str] = []
    pattern = _call_tag_pattern(run)

    for expected, record in enumerate(audit_records, start=1):
        if set(record) != {"sequence", "call"}:
            _fail()
        sequence = record["sequence"]
        tag = record["call"]
        if isinstance(sequence, bool) or not isinstance(sequence, int) or sequence != expected:
            _fail()
        if not isinstance(tag, str):
            _fail()
        match = pattern.fullmatch(tag)
        if match is None or match.group(1) != str(expected):
            _fail()
        tags.append(tag)
    return tags


def _call_tag_pattern(run: str) -> re.Pattern[str]:
    return re.compile(re.escape(run) + r"--p[0-9a-f]{16}--c([1-9][0-9]*)")


def _ledger_row_matches_run(ledger_run: Any, run: str, pattern: re.Pattern[str]) -> bool:
    if ledger_run == run:
        return True
    if not isinstance(ledger_run, str):
        return False

    # A malformed value claiming this run's call-tag prefix is ambiguous; fail closed rather
    # than silently omit a potentially real cost. Other run IDs are ignored.
    prefix = run + "--p"
    if not ledger_run.startswith(prefix):
        return False
    if pattern.fullmatch(ledger_run) is None:
        _fail()
    return True


def snapshot(
    ledger_path: str | os.PathLike[str],
    audit_path: str | os.PathLike[str],
    run: str,
) -> dict[str, str | int]:
    """Retourne le total exact (`spent` texte), les tentatives, les pending et les lignes comptées.

    Le `run` exact et tout tag de ce run au format valide contribuent au total, y compris un tag
    historique absent de l'audit. Seuls les tags audités confirment les tentatives correspondantes.
    """
    try:
        if not isinstance(run, str) or _RUN_RE.fullmatch(run) is None:
            _fail()
        audit_records = _read_jsonl(audit_path)
        tags = _audit_tags(audit_records, run)
        tag_set = set(tags)
        tag_pattern = _call_tag_pattern(run)
        ledger_records = _read_jsonl(ledger_path)

        costs: list[Decimal] = []
        confirmed: set[str] = set()
        record_count = 0
        for record in ledger_records:
            ledger_run = record.get("run")
            if not _ledger_row_matches_run(ledger_run, run, tag_pattern):
                continue
            if "cost" not in record:
                _fail()
            costs.append(_checked_decimal(record["cost"]))
            record_count += 1
            if ledger_run in tag_set:
                confirmed.add(ledger_run)

        return {
            "spent": _format_exact_sum(costs),
            "attempts": len(tags),
            "pending": len(tags) - len(confirmed),
            "records": record_count,
        }
    except SnapshotError:
        raise
    except Exception:
        _fail()


def snapshot_wait(
    ledger_path: str | os.PathLike[str],
    audit_path: str | os.PathLike[str],
    run: str,
    timeout_seconds: float,
) -> dict[str, str | int]:
    """Attend au plus 60 s que toutes les tentatives auditées aient une ligne ledger exacte."""
    if (isinstance(timeout_seconds, bool) or not isinstance(timeout_seconds, (int, float))
            or not math.isfinite(timeout_seconds) or not 0 <= timeout_seconds <= 60):
        _fail()
    deadline = time.monotonic() + timeout_seconds
    while True:
        try:
            result = snapshot(ledger_path, audit_path, run)
            if result["pending"] == 0:
                return result
        except SnapshotError:
            pass
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            _fail()
        time.sleep(min(0.1, remaining))


class _GenericArgumentParser(argparse.ArgumentParser):
    def error(self, _message: str) -> None:
        # argparse's default error includes user-supplied arguments, which may contain secrets.
        print(ERROR_MESSAGE, file=sys.stderr)
        raise SystemExit(2)


def main(argv: list[str] | None = None) -> int:
    parser = _GenericArgumentParser(description="Read-only JSONL cost snapshot")
    parser.add_argument("--ledger", required=True)
    parser.add_argument("--audit", required=True)
    parser.add_argument("--run", required=True)
    parser.add_argument("--wait-seconds", type=float)
    args = parser.parse_args(argv)
    try:
        if args.wait_seconds is None:
            result = snapshot(args.ledger, args.audit, args.run)
        else:
            result = snapshot_wait(args.ledger, args.audit, args.run, args.wait_seconds)
    except Exception:
        print(ERROR_MESSAGE, file=sys.stderr)
        return 1
    print(json.dumps(result, separators=(",", ":"), ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
