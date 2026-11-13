#!/usr/bin/env python3
"""Contrôle local de la ferme Qwen3.8 Flash Next sur pc4 : sonde, repli et sémaphore."""
from __future__ import annotations

import argparse
import fcntl
import json
import os
import re
import stat
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

DEFAULT_QWEN_URL = "http://192.168.1.161:8080/v1"
DEFAULT_FALLBACK_MODEL = "eco-deepseek"
ALLOWED_FALLBACKS = {"eco-deepseek", "eco-muse"}
MAX_KEY_BYTES = 4096
MAX_PROBE_BODY = 262_144


def normalize_v1_url(raw: str) -> str:
    value = (raw or DEFAULT_QWEN_URL).strip().rstrip("/")
    parsed = urllib.parse.urlsplit(value)
    if parsed.scheme not in ("http", "https") or not parsed.hostname:
        raise ValueError("URL Qwen invalide")
    if parsed.username or parsed.password or parsed.query or parsed.fragment:
        raise ValueError("URL Qwen ne doit contenir ni secret ni requête")
    path = parsed.path.rstrip("/")
    if not path:
        path = "/v1"
    netloc = f"{parsed.hostname}:{parsed.port}" if parsed.port else parsed.hostname
    return urllib.parse.urlunsplit((parsed.scheme, netloc, path, "", ""))


def root_from_v1(v1_url: str) -> str:
    if v1_url.endswith("/v1"):
        return v1_url[:-3]
    return v1_url


def read_private_secret(path: Path) -> str | None:
    flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_NONBLOCK", 0)
    try:
        fd = os.open(path, flags)
    except OSError:
        return None
    try:
        info = os.fstat(fd)
        mode = stat.S_IMODE(info.st_mode)
        if not stat.S_ISREG(info.st_mode) or info.st_uid != os.getuid() or (mode & 0o077):
            return None
        raw = os.read(fd, MAX_KEY_BYTES + 1)
    except OSError:
        return None
    finally:
        os.close(fd)
    if len(raw) > MAX_KEY_BYTES:
        return None
    text = raw.decode("utf-8", errors="ignore").strip()
    return text or None


def load_strata_key(keyfile: Path | None = None, env_keyfile: Path | None = None) -> str | None:
    env_val = os.environ.get("STRATA_API_KEY", "").strip()
    if env_val and env_val not in ("sk-strata-unconfigured", "sk-strata-local") and not any(ch.isspace() for ch in env_val):
        return env_val

    sa_home = Path(os.environ.get("SA_HOME", str(Path.home() / ".config" / "nexora-sous-agents")))
    candidates = [keyfile] if keyfile else [
        Path(os.environ["SA_STRATA_KEYFILE"]) if os.environ.get("SA_STRATA_KEYFILE") else sa_home / "strata.key",
    ]
    for candidate in candidates:
        if candidate is None:
            continue
        content = read_private_secret(candidate)
        if content and not any(ch.isspace() for ch in content):
            return content

    pc4_env = env_keyfile or (Path.home() / ".config" / "gitspace" / "pc4-dsh.env")
    raw_env = read_private_secret(pc4_env)
    if raw_env:
        for line in raw_env.splitlines():
            match = re.match(r'^(?:export\s+)?STRATA_PC4_API_KEY=["\']?([^"\'\s]+)["\']?\s*$', line.strip())
            if match:
                return match.group(1)
    return None


def _http_get_json(url: str, timeout: float, token: str | None = None) -> tuple[int | None, Any, str]:
    headers = {"Accept": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(url, headers=headers, method="GET")
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    try:
        with opener.open(req, timeout=timeout) as resp:
            body = resp.read(MAX_PROBE_BODY + 1)
            status = resp.status
    except urllib.error.HTTPError as exc:
        return exc.code, None, f"http_{exc.code}"
    except (urllib.error.URLError, TimeoutError, OSError, ValueError) as exc:
        reason = getattr(exc, "reason", exc)
        return None, None, str(reason)[:120]
    if len(body) > MAX_PROBE_BODY:
        return status, None, "reponse_trop_volumineuse"
    try:
        return status, json.loads(body.decode("utf-8")), ""
    except (UnicodeDecodeError, json.JSONDecodeError):
        return status, None, "json_invalide"


def probe_pc4(
    url: str | None = None,
    timeout: float = 3.0,
    token: str | None = None,
    expected_substr: str = "Qwen",
    max_latency_ms: float | None = None,
) -> dict[str, Any]:
    started = time.monotonic()
    try:
        v1_url = normalize_v1_url(url or os.environ.get("SA_QWEN_URL", DEFAULT_QWEN_URL))
    except ValueError as exc:
        return {"ok": False, "url": "", "models": [], "latency_ms": 0.0, "reason": str(exc)}

    if max_latency_ms is None:
        try:
            max_latency_ms = float(os.environ.get("SA_QWEN_MAX_PROBE_MS", "1500"))
        except ValueError:
            max_latency_ms = 1500.0

    root_url = root_from_v1(v1_url)
    h_status, h_doc, h_err = _http_get_json(f"{root_url}/health", timeout=timeout, token=token)
    if h_status not in (200, 404):
        elapsed = round((time.monotonic() - started) * 1000.0, 1)
        return {
            "ok": False,
            "url": v1_url,
            "models": [],
            "latency_ms": elapsed,
            "reason": h_err or f"health_http_{h_status}",
        }
    if h_status == 200 and isinstance(h_doc, dict):
        st = str(h_doc.get("status", "ok")).lower()
        if st not in ("ok", "healthy", "ready"):
            elapsed = round((time.monotonic() - started) * 1000.0, 1)
            return {
                "ok": False,
                "url": v1_url,
                "models": [],
                "latency_ms": elapsed,
                "reason": f"health_{st}",
            }

    status, doc, err = _http_get_json(f"{v1_url}/models", timeout=timeout, token=token)
    elapsed = round((time.monotonic() - started) * 1000.0, 1)
    if status != 200 or not isinstance(doc, dict) or not isinstance(doc.get("data"), list):
        return {
            "ok": False,
            "url": v1_url,
            "models": [],
            "latency_ms": elapsed,
            "reason": err or f"models_http_{status}",
        }

    models = [
        str(item.get("id"))
        for item in doc["data"]
        if isinstance(item, dict) and isinstance(item.get("id"), str) and item.get("id")
    ]
    if not models:
        return {"ok": False, "url": v1_url, "models": [], "latency_ms": elapsed, "reason": "aucun_modele"}
    if expected_substr and not any(expected_substr.lower() in m.lower() for m in models):
        return {
            "ok": False,
            "url": v1_url,
            "models": models,
            "latency_ms": elapsed,
            "reason": "modele_qwen_absent",
        }
    if max_latency_ms > 0 and elapsed > max_latency_ms:
        return {
            "ok": False,
            "url": v1_url,
            "models": models,
            "latency_ms": elapsed,
            "reason": f"pc4_lent_{elapsed}ms",
        }
    return {"ok": True, "url": v1_url, "models": models, "latency_ms": elapsed, "reason": "ok"}


def fallback_alias(raw: str | None = None) -> str:
    candidate = (raw if raw is not None else os.environ.get("SA_QWEN_FALLBACK_MODEL", DEFAULT_FALLBACK_MODEL)).strip()
    mapping = {
        "deepseek": "eco-deepseek",
        "eco-deepseek": "eco-deepseek",
        "muse": "eco-muse",
        "eco-muse": "eco-muse",
    }
    resolved = mapping.get(candidate, DEFAULT_FALLBACK_MODEL)
    return resolved if resolved in ALLOWED_FALLBACKS else DEFAULT_FALLBACK_MODEL


def resolve_model(
    requested_alias: str,
    *,
    url: str | None = None,
    timeout: float = 3.0,
    token: str | None = None,
    fallback_enabled: bool | None = None,
    fallback_model: str | None = None,
    max_latency_ms: float | None = None,
) -> dict[str, Any]:
    normalized = "eco-qwen" if requested_alias in ("qwen", "eco-qwen") else requested_alias
    if normalized != "eco-qwen":
        return {
            "ok": True,
            "requested": normalized,
            "model": normalized,
            "fallback_used": False,
            "reason": "non_qwen",
        }

    fb_on = (
        (os.environ.get("SA_QWEN_FALLBACK", "1").strip() not in ("0", "false", "non", "off"))
        if fallback_enabled is None
        else bool(fallback_enabled)
    )
    fb_target = fallback_alias(fallback_model)
    probe = probe_pc4(url=url, timeout=timeout, token=token, max_latency_ms=max_latency_ms)
    if probe["ok"]:
        return {
            "ok": True,
            "requested": "eco-qwen",
            "model": "eco-qwen",
            "fallback_used": False,
            "reason": "pc4_sain",
            "probe": probe,
        }
    if fb_on:
        return {
            "ok": True,
            "requested": "eco-qwen",
            "model": fb_target,
            "fallback_used": True,
            "reason": probe["reason"],
            "probe": probe,
        }
    return {
        "ok": False,
        "requested": "eco-qwen",
        "model": "eco-qwen",
        "fallback_used": False,
        "reason": probe["reason"],
        "probe": probe,
    }


def acquire_slot(lock_dir: Path, slots: int, wait_seconds: float) -> tuple[int, int] | None:
    if slots < 1:
        raise ValueError("SA_QWEN_MAX_CONCURRENCY doit être >= 1")
    if wait_seconds < 0:
        raise ValueError("SA_QWEN_QUEUE_TIMEOUT doit être >= 0")
    lock_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
    try:
        os.chmod(lock_dir, 0o700)
    except OSError:
        pass
    deadline = time.monotonic() + wait_seconds
    while True:
        for slot in range(slots):
            slot_path = lock_dir / f"slot-{slot}.lock"
            fd = os.open(slot_path, os.O_CREAT | os.O_RDWR | getattr(os, "O_CLOEXEC", 0), 0o600)
            try:
                fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
                os.ftruncate(fd, 0)
                os.write(fd, f"{os.getpid()} {int(time.time())}\n".encode("ascii"))
                return fd, slot
            except BlockingIOError:
                os.close(fd)
        if time.monotonic() >= deadline:
            return None
        time.sleep(min(0.2, max(0.02, deadline - time.monotonic())))


def run_with_slot(lock_dir: Path, slots: int, wait_seconds: float, command: list[str], timeout_rc: int = 75) -> int:
    if not command:
        raise ValueError("commande manquante après --")
    acquired = acquire_slot(lock_dir, slots=slots, wait_seconds=wait_seconds)
    if acquired is None:
        return timeout_rc
    fd, slot = acquired
    env = dict(os.environ, SA_QWEN_ACTIVE_SLOT=str(slot))
    try:
        proc = subprocess.run(command, env=env, check=False)
        return proc.returncode
    finally:
        try:
            fcntl.flock(fd, fcntl.LOCK_UN)
        finally:
            os.close(fd)


def format_status_line(probe: dict[str, Any], fb_target: str) -> str:
    if probe.get("ok"):
        models = ", ".join(probe.get("models") or ["Qwen"])
        return (
            f"Ferme Qwen pc4 ({probe.get('url', DEFAULT_QWEN_URL)}) : disponible "
            f"({models}, sonde {probe.get('latency_ms', 0.0)} ms, repli={fb_target})."
        )
    reason = probe.get("reason") or "injoignable"
    return (
        f"Ferme Qwen pc4 ({probe.get('url') or DEFAULT_QWEN_URL}) : indisponible ({reason}) ; "
        f"repli automatique vers {fb_target} actif."
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_probe = sub.add_parser("probe", help="Sonde HTTP locale vers pc4 (/health et /v1/models)")
    p_probe.add_argument("--url", default=None)
    p_probe.add_argument("--timeout", type=float, default=float(os.environ.get("SA_QWEN_PROBE_TIMEOUT", "3")))
    p_probe.add_argument("--max-latency-ms", type=float, default=None)
    p_probe.add_argument("--keyfile", default=None)

    p_status = sub.add_parser("status-line", help="Ligne informative concise pour activer.sh (code retour 0)")
    p_status.add_argument("--url", default=None)
    p_status.add_argument("--timeout", type=float, default=float(os.environ.get("SA_QWEN_PROBE_TIMEOUT", "1.5")))
    p_status.add_argument("--max-latency-ms", type=float, default=None)
    p_status.add_argument("--keyfile", default=None)

    p_res = sub.add_parser("resolve", help="Résout eco-qwen ou son modèle de repli")
    p_res.add_argument("alias")
    p_res.add_argument("--url", default=None)
    p_res.add_argument("--timeout", type=float, default=float(os.environ.get("SA_QWEN_PROBE_TIMEOUT", "3")))
    p_res.add_argument("--max-latency-ms", type=float, default=None)
    p_res.add_argument("--keyfile", default=None)

    p_slot = sub.add_parser("with-slot", help="Exécute une commande sous sémaphore local pc4")
    p_slot.add_argument("--lock-dir", default=None)
    p_slot.add_argument("--slots", type=int, default=int(os.environ.get("SA_QWEN_MAX_CONCURRENCY", "2")))
    p_slot.add_argument("--wait", type=float, default=float(os.environ.get("SA_QWEN_QUEUE_TIMEOUT", "180")))
    p_slot.add_argument("--timeout-exit", type=int, default=75)
    p_slot.add_argument("command", nargs=argparse.REMAINDER)

    p_hold = sub.add_parser("hold-slot", help="Acquiert un slot, écrit LOCKED <slot> et attend EOF sur stdin")
    p_hold.add_argument("--lock-dir", default=None)
    p_hold.add_argument("--slots", type=int, default=int(os.environ.get("SA_QWEN_MAX_CONCURRENCY", "2")))
    p_hold.add_argument("--wait", type=float, default=float(os.environ.get("SA_QWEN_QUEUE_TIMEOUT", "180")))
    p_hold.add_argument("--timeout-exit", type=int, default=75)

    args = parser.parse_args(argv)
    if args.cmd == "probe":
        token = load_strata_key(Path(args.keyfile) if args.keyfile else None)
        res = probe_pc4(url=args.url, timeout=args.timeout, token=token, max_latency_ms=args.max_latency_ms)
        print(json.dumps(res, ensure_ascii=False))
        return 0 if res["ok"] else 1

    if args.cmd == "status-line":
        token = load_strata_key(Path(args.keyfile) if args.keyfile else None)
        res = probe_pc4(url=args.url, timeout=args.timeout, token=token, max_latency_ms=args.max_latency_ms)
        print(format_status_line(res, fallback_alias()))
        return 0

    if args.cmd == "resolve":
        token = load_strata_key(Path(args.keyfile) if args.keyfile else None)
        res = resolve_model(
            args.alias,
            url=args.url,
            timeout=args.timeout,
            token=token,
            max_latency_ms=args.max_latency_ms,
        )
        print(json.dumps(res, ensure_ascii=False))
        return 0 if res["ok"] else 1

    sa_state = Path(os.environ.get("SA_STATE", str(Path.home() / ".local" / "share" / "nexora-sous-agents")))
    lock_dir = Path(args.lock_dir) if args.lock_dir else (sa_state / "locks" / "qwen")

    if args.cmd == "hold-slot":
        try:
            acquired = acquire_slot(lock_dir, slots=args.slots, wait_seconds=args.wait)
        except ValueError as exc:
            print(str(exc), file=sys.stderr)
            return 2
        if acquired is None:
            print("TIMEOUT", flush=True)
            return args.timeout_exit
        fd, slot = acquired
        try:
            print(f"LOCKED {slot}", flush=True)
            try:
                sys.stdin.read()
            except KeyboardInterrupt:
                pass
            return 0
        finally:
            try:
                fcntl.flock(fd, fcntl.LOCK_UN)
            finally:
                os.close(fd)

    cmd = list(args.command)
    if cmd and cmd[0] == "--":
        cmd = cmd[1:]
    try:
        return run_with_slot(lock_dir, slots=args.slots, wait_seconds=args.wait, command=cmd, timeout_rc=args.timeout_exit)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
