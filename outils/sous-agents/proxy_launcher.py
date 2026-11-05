#!/usr/bin/env python3
"""Open the gateway key once, validate that same descriptor, then exec the isolated relay."""
from __future__ import annotations

import os
import stat
import sys


KEY_MAX_BYTES = 4096
LEDGER_MAX_BYTES = 64 * 1024 * 1024
PROXY_ENV = (
    "SA_PROXY_RUN",
    "SA_PROXY_MODEL",
    "SA_PROXY_PORT",
    "SA_PROXY_TIMEOUT",
    "SA_PROXY_AUDIT",
    "SA_PROXY_LEDGER",
    "SA_PROXY_BUDGET",
    "SA_PROXY_LEDGER_WAIT",
)


class KeyUnavailable(Exception):
    pass


class LedgerUnavailable(Exception):
    pass


def open_master_key(path: str) -> int:
    """Return the one validated, nonblocking descriptor; never read the key in this helper."""
    if not hasattr(os, "O_NOFOLLOW") or not hasattr(os, "O_NONBLOCK"):
        raise KeyUnavailable
    flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0) | os.O_NOFOLLOW | os.O_NONBLOCK
    try:
        fd = os.open(path, flags)
    except OSError as exc:
        raise KeyUnavailable from exc
    try:
        info = os.fstat(fd)
        if (not stat.S_ISREG(info.st_mode) or info.st_uid != os.getuid()
                or info.st_mode & 0o077 or not 1 <= info.st_size <= KEY_MAX_BYTES):
            raise KeyUnavailable
        return fd
    except BaseException:
        os.close(fd)
        raise


def ensure_ledger(path: str) -> None:
    """Create the initial empty ledger atomically, or validate an existing regular file."""
    if not hasattr(os, "O_NOFOLLOW") or not hasattr(os, "O_NONBLOCK"):
        raise LedgerUnavailable
    nofollow = os.O_NOFOLLOW
    common = getattr(os, "O_CLOEXEC", 0) | nofollow | os.O_NONBLOCK
    try:
        try:
            fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | common, 0o600)
        except FileExistsError:
            fd = os.open(path, os.O_RDONLY | common)
        try:
            info = os.fstat(fd)
            if (not stat.S_ISREG(info.st_mode) or info.st_mode & 0o022
                    or info.st_size > LEDGER_MAX_BYTES):
                raise LedgerUnavailable
        finally:
            os.close(fd)
    except OSError as exc:
        raise LedgerUnavailable from exc


def main() -> int:
    if len(sys.argv) != 4:
        return 2
    os.umask(0o077)
    try:
        fd = open_master_key(sys.argv[1])
    except Exception:
        print("master key unavailable", file=sys.stderr)
        return 3

    if fd != 3:
        os.dup2(fd, 3, inheritable=True)
        os.close(fd)
    else:
        os.set_inheritable(3, True)

    env = {name: os.environ[name] for name in PROXY_ENV if name in os.environ}
    if len(env) != len(PROXY_ENV):
        print("relay startup failed", file=sys.stderr)
        return 2
    try:
        ensure_ledger(env["SA_PROXY_LEDGER"])
    except Exception:
        print("usage ledger unavailable", file=sys.stderr)
        return 4
    command = [sys.executable, "-E", "-s", "-S", sys.argv[2], sys.argv[3]]
    try:
        os.execve(sys.executable, command, env)
    except OSError:
        print("relay startup failed", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
