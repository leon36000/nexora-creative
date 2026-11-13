#!/usr/bin/env python3
"""Validated, budget-aware coordinator for lot.sh (standard library only)."""
from __future__ import annotations

import json
import os
import re
import secrets
import stat
import subprocess
import sys
import time
from dataclasses import dataclass
from decimal import Decimal, DecimalException, InvalidOperation
from pathlib import Path
from typing import Any


ALIASES = {
    "deepseek": "eco-deepseek", "eco-deepseek": "eco-deepseek",
    "muse": "eco-muse", "eco-muse": "eco-muse",
    "gemini": "eco-gemini", "eco-gemini": "eco-gemini",
    "gemini-eleve": "eco-gemini-eleve", "eco-gemini-eleve": "eco-gemini-eleve",
    "qwen": "eco-qwen", "eco-qwen": "eco-qwen",
    "carbon": "eco-carbon", "eco-carbon": "eco-carbon",
    "carbon-eleve": "eco-carbon-eleve", "eco-carbon-eleve": "eco-carbon-eleve",
    "terra": "eco-terra", "eco-terra": "eco-terra",
    "sol": "eco-sol", "eco-sol": "eco-sol",
    "argon": "eco-argon", "eco-argon": "eco-argon",
    "kimi": "eco-kimi", "eco-kimi": "eco-kimi",
}
# With <=64 coefficient digits and adjusted exponent >= -30, the lowest
# nonzero Decimal exponent accepted below is -30 - (64 - 1) = -93.
MONEY_UNIT_EXPONENT = -93
MAX_LEDGER_BYTES = 64 * 1024 * 1024
MAX_LEDGER_LINE_BYTES = 1024 * 1024
MAX_LEDGER_RECORDS = 250_000
RUN_ID_PATTERN = re.compile(r"[A-Za-z0-9_.-]{1,128}")


class LotError(Exception):
    pass


class DuplicateJSONKey(ValueError):
    pass


def unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    obj: dict[str, Any] = {}
    for key, value in pairs:
        if key in obj:
            raise DuplicateJSONKey("duplicate key")
        obj[key] = value
    return obj


def reject_constant(_value: str) -> None:
    raise ValueError("non-finite JSON number")


def positive_decimal(raw: str, label: str) -> Decimal:
    try:
        value = Decimal(raw)
    except (InvalidOperation, ValueError):
        raise LotError(f"{label} invalide") from None
    if not value.is_finite() or value <= 0 or len(value.as_tuple().digits) > 64:
        raise LotError(f"{label} invalide")
    if not value.is_zero() and not -30 <= value.adjusted() <= 30:
        raise LotError(f"{label} hors plage")
    return value


def money_units(value: Decimal) -> int:
    """Exact integer representation at 10^-93 for every accepted amount."""
    if value.is_zero():
        return 0
    sign, digits, exponent = value.as_tuple()
    if exponent < MONEY_UNIT_EXPONENT:
        raise ValueError("montant hors précision acceptée")
    coefficient = int("".join(str(digit) for digit in digits))
    units = coefficient * (10 ** (exponent - MONEY_UNIT_EXPONENT))
    return -units if sign else units


def parse_args(argv: list[str]) -> tuple[str, Path, Path, int, bool]:
    if len(argv) < 3:
        raise LotError("usage: lot.sh <alias> <dossier-prompts> <dossier-workdirs> [parallélisme=8] [--create-workdirs]")
    alias = ALIASES.get(argv[0])
    if alias is None:
        raise LotError("alias inconnu")
    rest = argv[3:]
    if rest.count("--create-workdirs") > 1:
        raise LotError("option --create-workdirs répétée")
    create_workdirs = "--create-workdirs" in rest
    rest = [item for item in rest if item != "--create-workdirs"]
    if len(rest) > 1:
        raise LotError("trop d'arguments")
    try:
        parallelism = int(rest[0]) if rest else 8
    except ValueError:
        raise LotError("parallélisme invalide") from None
    if parallelism < 1:
        raise LotError("parallélisme doit être supérieur à zéro")
    prompt_dir = Path(argv[1]).expanduser().resolve(strict=True)
    work_root = Path(argv[2]).expanduser().resolve(strict=True)
    if not prompt_dir.is_dir() or not work_root.is_dir():
        raise LotError("les dossiers de prompts et de workdirs doivent déjà exister")
    return alias, prompt_dir, work_root, parallelism, create_workdirs


@dataclass
class Task:
    name: str
    prompt: Path
    workdir: Path
    status: str = "SKIP"
    detail: str = "non_demarre"
    rc: str = "-"
    out: Path | None = None
    log: Path | None = None
    process: subprocess.Popen[bytes] | None = None
    run_id: str | None = None


def task_name_is_safe(name: str) -> bool:
    return bool(name) and name not in {".", ".."} and not any(
        ord(char) < 32 or ord(char) == 127 for char in name
    )


def workdir_identity(path: Path) -> tuple[Any, ...]:
    resolved = path.resolve(strict=True)
    info = resolved.stat()
    return (str(resolved), info.st_dev, info.st_ino)


def is_strict_descendant(path: Path, root: Path) -> bool:
    """Require a resolved prompt/workdir to be inside, but not equal to, its declared root."""
    return path != root and path.is_relative_to(root)


def discover_tasks(prompt_dir: Path, work_root: Path, create_workdirs: bool) -> list[Task]:
    entries = sorted(
        (p for p in prompt_dir.iterdir() if p.name.endswith((".txt", ".md"))),
        key=lambda p: p.name,
    )
    if not entries:
        raise LotError("aucun prompt .txt ou .md dans le dossier")
    tasks: list[Task] = []
    by_name: dict[str, Path] = {}
    effective_workdirs: list[tuple[str, Path]] = []
    for entry in entries:
        suffix = ".txt" if entry.name.endswith(".txt") else ".md"
        name = entry.name[:-len(suffix)]
        if not task_name_is_safe(name):
            raise LotError("nom de tâche vide ou contenant un caractère de contrôle")
        if name in by_name:
            raise LotError(f"collision .txt/.md pour le nom de tâche {name!r}")
        by_name[name] = entry
        try:
            prompt = entry.resolve(strict=True)
        except OSError:
            raise LotError(f"prompt introuvable : {entry.name}") from None
        if not is_strict_descendant(prompt, prompt_dir):
            raise LotError(f"prompt résolu hors du dossier déclaré : {entry.name}")
        if not prompt.is_file():
            raise LotError(f"le prompt n'est pas un fichier régulier : {entry.name}")
        tasks.append(Task(name=name, prompt=prompt, workdir=work_root / name))

    identities: dict[tuple[Any, ...], str] = {}
    for task in tasks:
        target = task.workdir
        if os.path.lexists(target):
            if not target.is_dir():
                raise LotError(f"workdir existant non répertoire : {task.name}")
            try:
                identity = workdir_identity(target)
            except OSError:
                raise LotError(f"workdir illisible : {task.name}") from None
            resolved = Path(identity[0])
            if not is_strict_descendant(resolved, work_root):
                raise LotError(f"workdir résolu hors du dossier déclaré : {task.name}")
            prior = identities.get(identity)
            if prior is not None:
                raise LotError(f"workdirs identiques ou liés par symlink : {prior!r} et {task.name!r}")
            identities[identity] = task.name
            task.workdir = resolved
            effective_workdirs.append((task.name, resolved))
        elif create_workdirs:
            # Tous les workdirs manquants sont enfants directs du chemin canonique.
            # Les noms ont déjà été limités à des noms de base sûrs et uniques.
            identity = (str(work_root), task.name)
            prior = identities.get(identity)
            if prior is not None:
                raise LotError(f"collision de workdir : {prior!r} et {task.name!r}")
            identities[identity] = task.name
            resolved = target.resolve(strict=False)
            if not is_strict_descendant(resolved, work_root):
                raise LotError(f"workdir à créer hors du dossier déclaré : {task.name}")
            task.detail = "a_creer"
            effective_workdirs.append((task.name, resolved))
        else:
            task.status, task.detail = "SKIP", "pas_de_workdir"

    # Deux chemins distincts mais imbriqués partagent le contenu visible à l'agent
    # parent; ils ne constituent donc pas deux workdirs indépendants.
    for index, (name, path) in enumerate(effective_workdirs):
        for other_name, other_path in effective_workdirs[index + 1:]:
            if path == other_path or path in other_path.parents or other_path in path.parents:
                raise LotError(f"workdirs se recouvrent ou sont identiques : {name!r} et {other_name!r}")
    return tasks


def validate_output_names(tasks: list[Task]) -> None:
    """Reserve top-level lot artifacts before any workdir or agent is started."""
    reserved = {"index.tsv", "index.tsv.tmp", "lot_status.txt"}
    claims: dict[str, tuple[str, str]] = {}
    for task in tasks:
        for path_name, kind in ((task.name, "sortie"), (task.name + ".launcher.log", "journal")):
            if path_name in reserved:
                raise LotError(f"nom de tâche réservé par un artefact du lot : {path_name!r}")
            prior = claims.get(path_name)
            if prior is not None:
                prior_name, prior_kind = prior
                raise LotError(
                    f"collision de sorties entre {prior_name!r} ({prior_kind}) et {task.name!r} ({kind})"
                )
            claims[path_name] = (task.name, kind)


def parse_cost(raw: Any) -> Decimal | None:
    if isinstance(raw, bool) or not isinstance(raw, (int, float, Decimal)):
        return None
    try:
        cost = Decimal(str(raw))
    except (InvalidOperation, ValueError):
        return None
    if not cost.is_finite() or cost < 0 or len(cost.as_tuple().digits) > 64:
        return None
    if not cost.is_zero() and not -30 <= cost.adjusted() <= 30:
        return None
    return cost


def base_run_id(run: str) -> str:
    # The current host relay appends one nonce/call tag to every provider request:
    # RUN--p<16 lowercase hex digits>--c<N>. Older runners record RUN directly.
    match = re.fullmatch(r"(.+)--p[0-9a-f]{16}--c[1-9][0-9]*", run)
    return match.group(1) if match else run


@dataclass
class LedgerBaseline:
    raw: bytes
    unattributed_rows: int


@dataclass
class Ledger:
    known: bool
    spent: int
    costs_by_run: dict[str, int]
    reason: str = ""


def parse_journal(raw: bytes) -> list[dict[str, Any]]:
    if raw and not raw.endswith(b"\n"):
        raise ValueError("journal sans LF terminal")
    try:
        lines = raw.split(b"\n")
        if lines and lines[-1] == b"":
            lines.pop()
        if len(lines) > MAX_LEDGER_RECORDS:
            raise ValueError("journal trop volumineux")
        rows: list[dict[str, Any]] = []
        for line_number, raw_line in enumerate(lines, 1):
            if len(raw_line) > MAX_LEDGER_LINE_BYTES:
                raise ValueError("ligne trop volumineuse")
            if raw_line.endswith(b"\r"):
                raw_line = raw_line[:-1]
            if not raw_line.strip():
                continue
            line = raw_line.decode("utf-8")
            row = json.loads(
                line,
                parse_float=Decimal,
                parse_int=Decimal,
                parse_constant=reject_constant,
                object_pairs_hook=unique_object,
            )
            if not isinstance(row, dict):
                raise ValueError(f"ligne {line_number} non objet")
            rows.append(row)
        return rows
    except (UnicodeError, ValueError, DecimalException, json.JSONDecodeError, RecursionError):
        raise ValueError("journal_illisible") from None


def read_ledger_bytes(path: Path) -> bytes:
    if not os.path.lexists(path):
        return b""
    fd = -1
    try:
        flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0)
        flags |= getattr(os, "O_NONBLOCK", 0)
        fd = os.open(path, flags)
        before = os.fstat(fd)
        if not stat.S_ISREG(before.st_mode) or before.st_size > MAX_LEDGER_BYTES:
            raise OSError("journal non régulier ou trop volumineux")
        with os.fdopen(fd, "rb", closefd=True) as stream:
            fd = -1
            raw = stream.read(MAX_LEDGER_BYTES + 1)
            after = os.fstat(stream.fileno())
        current_path = os.stat(path, follow_symlinks=False)
        same_file = (before.st_dev, before.st_ino) == (after.st_dev, after.st_ino) == (
            current_path.st_dev, current_path.st_ino
        )
        stable = (before.st_size, before.st_mtime_ns, before.st_ctime_ns) == (
            after.st_size, after.st_mtime_ns, after.st_ctime_ns
        ) == (current_path.st_size, current_path.st_mtime_ns, current_path.st_ctime_ns)
        if (not same_file or not stat.S_ISREG(current_path.st_mode) or not stable
                or len(raw) != after.st_size or len(raw) > MAX_LEDGER_BYTES):
            raise OSError("journal changé pendant sa lecture")
        return raw
    except OSError:
        raise OSError("journal indisponible") from None
    finally:
        if fd >= 0:
            os.close(fd)


def snapshot_ledger(path: Path) -> LedgerBaseline:
    try:
        raw = read_ledger_bytes(path)
        rows = parse_journal(raw)
    except (OSError, ValueError):
        raise LotError("journal_illisible") from None
    unattributed = sum(not isinstance(row.get("run"), str) or not row.get("run") for row in rows)
    return LedgerBaseline(raw=raw, unattributed_rows=unattributed)


def read_ledger(path: Path, lot_id: str, baseline: LedgerBaseline) -> Ledger:
    try:
        current = read_ledger_bytes(path)
        if current and not current.endswith(b"\n"):
            return Ledger(False, 0, {}, "journal_illisible")
        if len(current) < len(baseline.raw) or not current.startswith(baseline.raw):
            return Ledger(False, 0, {}, "journal_historique_modifie")
        historical = parse_journal(baseline.raw)
        new_rows = parse_journal(current[len(baseline.raw):])
    except (OSError, ValueError):
        return Ledger(False, 0, {}, "journal_illisible")
    # Only exact pre-lot bytes may contain records without a run identifier.
    if any(not isinstance(row.get("run"), str) or not row.get("run") for row in new_rows):
        return Ledger(False, 0, {}, "cout_nouveau_non_attribuable")
    costs: dict[str, int] = {}
    for row in [*historical, *new_rows]:
        if not isinstance(row.get("run"), str) or not row.get("run"):
            continue
        run = row["run"]
        base_run = base_run_id(run)
        if base_run != lot_id and not base_run.startswith(lot_id + "-"):
            continue
        cost = parse_cost(row.get("cost"))
        if cost is None:
            return Ledger(False, 0, {}, "cout_inconnu")
        costs[base_run] = costs.get(base_run, 0) + money_units(cost)
    return Ledger(True, sum(costs.values()), costs)


def read_run_id(task: Task) -> str | None:
    if task.out is None:
        return None
    meta_path = task.out / "meta.json"
    try:
        # This file is produced by sous-agent.sh in the unique lot output dir.
        data = json.loads(meta_path.read_text(encoding="utf-8"), object_pairs_hook=unique_object)
        run = data.get("run") if isinstance(data, dict) else None
        return run if isinstance(run, str) and run else None
    except (OSError, UnicodeError, ValueError, json.JSONDecodeError, RecursionError):
        return None


def register_run_id(task: Task, lot_id: str, tasks: list[Task], owners: dict[str, str],
                    duplicates: set[str]) -> str:
    run_id = task.run_id
    if not run_id:
        return ""
    if RUN_ID_PATTERN.fullmatch(run_id) is None:
        return "run_id_invalide"
    if not run_id.startswith(lot_id + "-"):
        return "run_id_hors_lot"
    if run_id in duplicates:
        return "run_id_duplique"
    prior = owners.get(run_id)
    if prior is not None and prior != task.name:
        duplicates.add(run_id)
        for item in tasks:
            if item.run_id == run_id:
                item.status, item.detail = "FAIL", "run_id_duplique"
        return "run_id_duplique"
    owners[run_id] = task.name
    return ""


def safe_line(path: Path) -> str:
    try:
        with path.open("rb") as stream:
            stream.seek(0, os.SEEK_END)
            size = stream.tell()
            stream.seek(max(0, size - 8192))
            data = stream.read(8192)
        lines = data.decode("utf-8", "replace").splitlines()
        for line in reversed(lines):
            stripped = line.strip()
            if stripped:
                return stripped
    except OSError:
        pass
    return ""


def finish_task(task: Task, returncode: int, run_budget: int, costs_by_run: dict[str, int]) -> None:
    task.process = None
    task.rc = str(returncode)
    line = safe_line(task.log) if task.log is not None else ""
    summary_status = line.split(maxsplit=1)[0] if line else ""
    actual = costs_by_run.get(task.run_id, 0) if task.run_id else 0
    if not task.run_id or task.run_id not in costs_by_run:
        task.status, task.detail = "FAIL", "cout_run_non_verifiable"
    elif actual > run_budget:
        task.status, task.detail = "FAIL", "budget_run_depasse"
    elif returncode != 0:
        task.status, task.detail = "FAIL", "processus_en_echec"
    elif summary_status.startswith("FAIL:"):
        task.status, task.detail = "FAIL", "resume_agent_echec"
    elif summary_status.startswith("OK:"):
        task.status, task.detail = "OK", "termine"
    else:
        task.status, task.detail = "FAIL", "resume_agent_absent_ou_invalide"


def write_index(path: Path, tasks: list[Task]) -> None:
    temp = path.with_name(path.name + ".tmp")
    with temp.open("w", encoding="utf-8", newline="") as stream:
        stream.write("statut\ttache	code_retour	detail\n")
        for task in tasks:
            stream.write(f"{task.status}\t{task.name}\t{task.rc}\t{task.detail}\n")
    temp.replace(path)


def make_lot_dir(state: Path) -> tuple[str, Path]:
    lots = state / "lots"
    lots.mkdir(parents=True, exist_ok=True, mode=0o700)
    for _ in range(10):
        lot_id = f"lot{time.strftime('%H%M%S')}-{secrets.token_hex(4)}"
        output = lots / lot_id
        try:
            output.mkdir(mode=0o700)
            return lot_id, output
        except FileExistsError:
            continue
    raise LotError("impossible de réserver un dossier de sortie unique")


def create_workdirs(tasks: list[Task], work_root: Path) -> list[Task]:
    failures = False
    for task in tasks:
        if task.status == "SKIP" and task.detail == "a_creer":
            # Explicit creation overrides only this preflight state.
            try:
                task.workdir.mkdir(mode=0o755)
                task.status, task.detail = "SKIP", "non_demarre"
            except FileExistsError:
                if task.workdir.is_dir():
                    task.status, task.detail = "SKIP", "non_demarre"
                else:
                    task.status, task.detail = "FAIL", "creation_workdir_echec"
                    failures = True
            except OSError:
                task.status, task.detail = "FAIL", "creation_workdir_echec"
                failures = True
    if failures:
        for task in tasks:
            if task.status == "SKIP" and task.detail == "non_demarre":
                task.detail = "creation_lot_incomplete"
    else:
        # Recheck identities after explicit creation to catch a concurrent alias.
        identities: dict[tuple[Any, ...], str] = {}
        paths: list[tuple[str, Path]] = []
        for task in tasks:
            if task.status == "FAIL":
                continue
            identity = workdir_identity(task.workdir)
            resolved = Path(identity[0])
            if not is_strict_descendant(resolved, work_root):
                raise LotError(f"workdir créé ou résolu hors du dossier déclaré : {task.name}")
            prior = identities.get(identity)
            if prior is not None:
                raise LotError(f"workdirs devenus identiques : {prior!r} et {task.name!r}")
            identities[identity] = task.name
            task.workdir = resolved
            paths.append((task.name, resolved))
        for index, (name, path) in enumerate(paths):
            for other_name, other_path in paths[index + 1:]:
                if path in other_path.parents or other_path in path.parents:
                    raise LotError(f"workdirs devenus imbriqués : {name!r} et {other_name!r}")
    return tasks


def launch(task: Task, alias: str, lot_id: str, lot_dir: Path, turns: int, run_budget: Decimal,
           sa_dir: Path, work_root: Path, env: dict[str, str]) -> None:
    try:
        resolved_workdir = task.workdir.resolve(strict=True)
    except OSError:
        task.status, task.detail = "FAIL", "workdir_illisible_au_lancement"
        return
    if not is_strict_descendant(resolved_workdir, work_root):
        task.status, task.detail = "FAIL", "workdir_hors_racine_au_lancement"
        return
    task.workdir = resolved_workdir
    task.out = lot_dir / task.name
    task.log = lot_dir / f"{task.name}.launcher.log"
    if os.path.lexists(task.out) or os.path.lexists(task.log):
        task.status, task.detail = "FAIL", "sortie_tache_deja_existante"
        return
    child_env = dict(env)
    child_env.update({"SA_TAG": lot_id, "SA_OUT": str(task.out), "LOT_RUN_BUDGET": format(run_budget, "f")})
    try:
        log = task.log.open("xb")
        try:
            task.process = subprocess.Popen(
                [str(sa_dir / "sous-agent.sh"), "-w", alias, str(task.prompt), str(task.workdir),
                 str(turns), format(run_budget, "f")],
                stdin=subprocess.DEVNULL,
                stdout=log,
                stderr=subprocess.STDOUT,
                env=child_env,
                close_fds=True,
            )
        finally:
            log.close()
    except OSError:
        task.status, task.detail = "FAIL", "lancement_impossible"
        task.rc = "-"
        task.process = None


def main(argv: list[str]) -> int:
    try:
        alias, prompt_dir, work_root, parallelism, allow_create = parse_args(argv)
        if alias == "eco-qwen":
            try:
                qwen_conc = max(1, int(os.environ.get("SA_QWEN_MAX_CONCURRENCY", "2")))
                qwen_lot_cap = max(qwen_conc, int(os.environ.get("SA_QWEN_LOT_PARALLEL", "3")))
            except ValueError:
                raise LotError("SA_QWEN_MAX_CONCURRENCY ou SA_QWEN_LOT_PARALLEL invalide") from None
            cap = qwen_lot_cap if os.environ.get("SA_QWEN_FALLBACK", "1") == "1" else qwen_conc
            parallelism = min(parallelism, cap)
        budget = positive_decimal(os.environ.get("LOT_BUDGET", "5"), "LOT_BUDGET")
        per_run_budget = positive_decimal(os.environ.get("LOT_RUN_BUDGET", "0.30"), "LOT_RUN_BUDGET")
        if per_run_budget > budget:
            raise LotError("LOT_RUN_BUDGET ne peut pas dépasser LOT_BUDGET")
        budget_units = money_units(budget)
        run_budget_units = money_units(per_run_budget)
        try:
            turns = int(os.environ.get("LOT_TURNS", "30"))
        except ValueError:
            raise LotError("LOT_TURNS invalide") from None
        if turns < 1:
            raise LotError("LOT_TURNS doit être supérieur à zéro")
        sa_dir = Path(os.environ["SA_DIR"]).resolve(strict=True)
        state = Path(os.environ["SA_STATE"]).expanduser().resolve(strict=False)
        tasks = discover_tasks(prompt_dir, work_root, allow_create)
        validate_output_names(tasks)
        if allow_create:
            create_workdirs(tasks, work_root)
        lot_id, lot_dir = make_lot_dir(state)
        env = dict(os.environ)
        env.update({
            "LOT_ID": lot_id, "LOT": str(lot_dir), "LOT_BUDGET": str(budget),
            "LOT_RUN_BUDGET": str(per_run_budget), "LOT_TURNS": str(turns),
            "LOT_ALIAS": alias, "WDIR": str(work_root), "SA_DIR": str(sa_dir),
            "SA_STATE": str(state),
        })
        ledger_path = state / "usage.jsonl"
        try:
            ledger_baseline = snapshot_ledger(ledger_path)
        except LotError as exc:
            ledger_baseline = LedgerBaseline(raw=b"", unattributed_rows=0)
            initial_ledger = Ledger(False, 0, {}, str(exc))
        else:
            initial_ledger = read_ledger(ledger_path, lot_id, ledger_baseline)
        if not initial_ledger.known:
            for task in tasks:
                if task.status == "SKIP" and task.detail == "non_demarre":
                    task.detail = initial_ledger.reason
            write_index(lot_dir / "index.tsv", tasks)
            (lot_dir / "lot_status.txt").write_text("FAIL\n", encoding="utf-8")
            print(f"statut du lot : FAIL ({initial_ledger.reason}); aucun lancement ; index : {lot_dir / 'index.tsv'}")
            return 1

        eligible = [task for task in tasks if task.detail == "non_demarre"]
        if eligible:
            try:
                gateway = subprocess.run(
                    [str(sa_dir / "gateway.sh"), "start"], env=env,
                    stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                    check=False,
                )
            except OSError:
                gateway = subprocess.CompletedProcess([], 127)
            if gateway.returncode != 0:
                for task in eligible:
                    task.status, task.detail = "SKIP", "passerelle_indisponible"
                eligible = []

        active: list[Task] = []
        launched_any = False
        pending = [task for task in tasks if task.detail == "non_demarre"]
        ledger_problem = ""
        run_owners: dict[str, str] = {}
        duplicate_run_ids: set[str] = set()
        while pending or active:
            changed = False
            # Collect completions first; their full reservation becomes reusable
            # only after the cost journal has been read again and validated.
            for task in list(active):
                process = task.process
                if process is not None and process.poll() is not None:
                    task.run_id = task.run_id or read_run_id(task)
                    run_problem = register_run_id(task, lot_id, tasks, run_owners, duplicate_run_ids)
                    if run_problem:
                        task.status, task.detail = "FAIL", run_problem
                        task.rc = str(process.returncode)
                        ledger_problem = run_problem
                    else:
                        current = read_ledger(ledger_path, lot_id, ledger_baseline)
                        if current.known:
                            if not task.run_id or task.run_id not in current.costs_by_run:
                                task.status, task.detail = "FAIL", "cout_run_non_verifiable"
                                task.rc = str(process.returncode)
                                ledger_problem = "cout_run_non_verifiable"
                            else:
                                finish_task(task, process.returncode, run_budget_units, current.costs_by_run)
                        else:
                            task.status, task.detail = "FAIL", current.reason
                            task.rc = str(process.returncode)
                            ledger_problem = current.reason
                    active.remove(task)
                    changed = True
            # Observe per-run metadata while requests are active. Missing metadata
            # leaves the full reservation in place.
            for task in active:
                task.run_id = task.run_id or read_run_id(task)
                run_problem = register_run_id(task, lot_id, tasks, run_owners, duplicate_run_ids)
                if run_problem:
                    ledger_problem = run_problem

            ledger = read_ledger(ledger_path, lot_id, ledger_baseline)
            if not ledger.known:
                ledger_problem = ledger.reason

            while pending and len(active) < parallelism and not ledger_problem:
                ledger = read_ledger(ledger_path, lot_id, ledger_baseline)
                if not ledger.known:
                    ledger_problem = ledger.reason
                    break
                active_reservation = 0
                for running in active:
                    if running.run_id:
                        observed = ledger.costs_by_run.get(running.run_id, 0)
                        active_reservation += max(0, run_budget_units - observed)
                    else:
                        active_reservation += run_budget_units
                if ledger.spent + active_reservation + run_budget_units > budget_units:
                    # An in-flight task may finish below its reservation; wait and
                    # re-evaluate before classifying the remaining tasks as skips.
                    if active:
                        break
                    while pending:
                        task = pending.pop(0)
                        task.status, task.detail = "SKIP", "budget_reserve_insuffisante"
                    changed = True
                    break
                task = pending.pop(0)
                launch(task, alias, lot_id, lot_dir, turns, per_run_budget, sa_dir, work_root, env)
                if task.process is not None:
                    active.append(task)
                    launched_any = True
                else:
                    changed = True
            if ledger_problem:
                while pending:
                    task = pending.pop(0)
                    task.status, task.detail = "SKIP", ledger_problem
                changed = True
            if active and not changed:
                # Reparse the append-only ledger at a bounded cadence; new starts
                # still require a fresh read immediately before each launch.
                time.sleep(0.5)
            elif active and changed:
                # Revisit active PIDs promptly without introducing a long wait.
                continue

        final_ledger = read_ledger(ledger_path, lot_id, ledger_baseline)
        all_tasks_ok = all(task.status == "OK" for task in tasks)
        final_cost_ok = final_ledger.known and final_ledger.spent <= budget_units
        cost_report_rc = 0
        if launched_any:
            try:
                report = subprocess.run(
                    [str(sa_dir / "cout.sh"), "--run", lot_id], env=env,
                    stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                    text=True, encoding="utf-8", errors="replace", check=False,
                )
                cost_report_rc = report.returncode
                if report.stdout:
                    print(report.stdout.rstrip())
            except OSError:
                cost_report_rc = 127
        lot_ok = all_tasks_ok and final_cost_ok and cost_report_rc == 0
        write_index(lot_dir / "index.tsv", tasks)
        (lot_dir / "lot_status.txt").write_text(("OK" if lot_ok else "FAIL") + "\n", encoding="utf-8")
        if not final_ledger.known:
            cost_note = final_ledger.reason
        elif final_ledger.spent > budget_units:
            cost_note = "depassement_budget_constate"
        else:
            cost_note = "cout_attribue"
        print(f"statut du lot : {'OK' if lot_ok else 'FAIL'} ({cost_note}); index : {lot_dir / 'index.tsv'}")
        print("réservations budgétaires locales à ce lot ; aucun partage entre lots simultanés ni plafond dur d'appel en vol")
        if ledger_baseline.unattributed_rows:
            print(f"{ledger_baseline.unattributed_rows} ligne(s) sans run existaient avant ce lot ; seules ces lignes historiques sont ignorées pour sa réserve")
        return 0 if lot_ok else 1
    except (LotError, OSError, KeyError) as exc:
        print(f"lot refusé : {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
