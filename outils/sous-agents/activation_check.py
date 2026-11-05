#!/usr/bin/env python3
"""Contrôles locaux de la passerelle; aucun appel fournisseur par défaut."""
from __future__ import annotations

import argparse
import json
import os
import stat
import re
import sys
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import HTTPRedirectHandler, ProxyHandler, Request, build_opener

MAX_RESPONSE = 1_000_000
CONFIGURED_ALIAS = re.compile(r"^\s*-\s*model_name:\s*([A-Za-z0-9._-]+)\s*(?:#.*)?$")


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def local_base(value: str) -> str:
    parsed = urlsplit(value)
    if (parsed.scheme != "http" or parsed.hostname != "127.0.0.1"
            or parsed.username or parsed.password or parsed.query or parsed.fragment
            or parsed.path not in ("", "/") or parsed.port is None):
        raise ValueError("base URL non locale")
    return f"http://127.0.0.1:{parsed.port}"


def aliases_from_config(path: Path) -> list[str]:
    aliases = []
    for line in path.read_text(encoding="utf-8").splitlines():
        match = CONFIGURED_ALIAS.match(line)
        if match and match.group(1) not in aliases:
            aliases.append(match.group(1))
    if not aliases:
        raise ValueError("aucun alias configuré")
    return aliases


def request_json(base: str, route: str, *, token: str | None = None,
                 payload: dict | None = None) -> tuple[int | None, object | None]:
    headers = {"Accept": "application/json"}
    data = None
    method = "GET"
    if token is not None:
        headers["Authorization"] = f"Bearer {token}"
    if payload is not None:
        data = json.dumps(payload, separators=(",", ":")).encode("utf-8")
        headers["Content-Type"] = "application/json"
        method = "POST"
    req = Request(base + route, data=data, headers=headers, method=method)
    try:
        with build_opener(ProxyHandler({}), NoRedirect()).open(req, timeout=5) as response:
            body = response.read(MAX_RESPONSE + 1)
            status = response.status
    except HTTPError as exc:
        return exc.code, None
    except (OSError, URLError, TimeoutError, ValueError):
        return None, None
    if len(body) > MAX_RESPONSE:
        return status, None
    try:
        return status, json.loads(body.decode("utf-8"))
    except (UnicodeError, json.JSONDecodeError):
        return status, None


def load_master_key(path: Path) -> str:
    nofollow = getattr(os, "O_NOFOLLOW", None)
    nonblock = getattr(os, "O_NONBLOCK", None)
    if nofollow is None or nonblock is None:
        raise OSError("primitive de sécurité absente")
    fd = os.open(path, os.O_RDONLY | nofollow | nonblock | getattr(os, "O_CLOEXEC", 0))
    try:
        info = os.fstat(fd)
        mode = stat.S_IMODE(info.st_mode)
        if (not stat.S_ISREG(info.st_mode) or info.st_uid != os.getuid()
                or mode & ~0o600 or not mode & 0o400):
            raise ValueError("clé maître inaccessible ou trop exposée")
        chunks = bytearray()
        while len(chunks) <= 4096:
            part = os.read(fd, min(1024, 4097 - len(chunks)))
            if not part:
                break
            chunks.extend(part)
    finally:
        os.close(fd)
    if len(chunks) > 4096:
        raise ValueError("clé maître invalide")
    key = chunks.decode("utf-8").strip()
    if not key or any(ch.isspace() or ord(ch) < 32 for ch in key):
        raise ValueError("clé maître invalide")
    return key


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", required=True)
    parser.add_argument("--key-file", required=True)
    parser.add_argument("--config", required=True)
    parser.add_argument("--test-fournisseurs", action="store_true")
    args = parser.parse_args()

    try:
        base = local_base(args.base_url)
        aliases = aliases_from_config(Path(args.config))
        # The secret is read inside Python and never included in argv or output.
        key = load_master_key(Path(args.key_file))
    except (OSError, UnicodeError, ValueError):
        print("configuration locale ou clé maître invalide", file=sys.stderr)
        return 1

    status, _ = request_json(base, "/health/liveliness")
    if status != 200:
        print("santé de la passerelle locale: échec", file=sys.stderr)
        return 1
    print("Santé de la passerelle locale : OK.")

    status, document = request_json(base, "/v1/models", token=key)
    if status != 200 or not isinstance(document, dict) or not isinstance(document.get("data"), list):
        print("lecture authentifiée de la liste des modèles locaux: échec", file=sys.stderr)
        return 1
    model_ids = {item.get("id") for item in document["data"]
                 if isinstance(item, dict) and isinstance(item.get("id"), str)}
    missing = [alias for alias in aliases if alias not in model_ids]
    if missing:
        print("alias configuré(s) absent(s) de la passerelle: " + ", ".join(missing), file=sys.stderr)
        return 1
    print("Alias configurés présents : " + ", ".join(aliases) + ".")

    if not args.test_fournisseurs:
        print("Fournisseurs non testés; aucun appel modèle effectué.")
        return 0

    failed = False
    for alias in aliases:
        status, response = request_json(
            base, "/v1/chat/completions", token=key,
            payload={"model": alias, "messages": [{"role": "user", "content": "Réponds uniquement OK."}],
                     "max_tokens": 1, "temperature": 0},
        )
        ok = status == 200 and isinstance(response, dict) and isinstance(response.get("choices"), list)
        print(f"{alias}: {'réponse reçue' if ok else 'échec (fournisseur non confirmé)'}")
        failed |= not ok
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
