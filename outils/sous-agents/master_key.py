#!/usr/bin/env python3
"""Crée ou lit la clé maître après validation stricte du fichier."""
from __future__ import annotations

import argparse
import os
import secrets
import stat
import sys
from pathlib import Path

MAX_KEY_BYTES = 4096


def required_flag(name: str) -> int:
    value = getattr(os, name, None)
    if value is None:
        raise OSError(f"primitive de sécurité absente: {name}")
    return value


def open_directory(path: Path) -> int:
    flags = os.O_RDONLY | required_flag("O_DIRECTORY") | required_flag("O_NOFOLLOW")
    flags |= getattr(os, "O_CLOEXEC", 0)
    fd = os.open(path, flags)
    info = os.fstat(fd)
    if not stat.S_ISDIR(info.st_mode) or info.st_uid != os.getuid() or stat.S_IMODE(info.st_mode) & 0o077:
        os.close(fd)
        raise ValueError("répertoire de clé maître non privé")
    return fd


def validate_and_read(dir_fd: int, name: str) -> str:
    flags = os.O_RDONLY | required_flag("O_NOFOLLOW") | required_flag("O_NONBLOCK")
    flags |= getattr(os, "O_CLOEXEC", 0)
    fd = os.open(name, flags, dir_fd=dir_fd)
    try:
        info = os.fstat(fd)
        mode = stat.S_IMODE(info.st_mode)
        if (not stat.S_ISREG(info.st_mode) or info.st_uid != os.getuid()
                or mode & ~0o600 or not mode & 0o400):
            raise ValueError("fichier de clé maître invalide")
        chunks = bytearray()
        while len(chunks) <= MAX_KEY_BYTES:
            part = os.read(fd, min(1024, MAX_KEY_BYTES + 1 - len(chunks)))
            if not part:
                break
            chunks.extend(part)
        if len(chunks) > MAX_KEY_BYTES:
            raise ValueError("fichier de clé maître trop long")
        key = chunks.decode("utf-8").strip()
        if not key or any(ch.isspace() or ord(ch) < 32 for ch in key):
            raise ValueError("fichier de clé maître invalide")
        return key
    finally:
        os.close(fd)


def create_if_absent(dir_fd: int, name: str) -> None:
    key = f"sk-sa-{secrets.token_hex(24)}"
    data = (key + "\n").encode("ascii")
    temp = f".{name}.{os.getpid()}.{secrets.token_hex(8)}.tmp"
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | required_flag("O_NOFOLLOW")
    flags |= getattr(os, "O_CLOEXEC", 0)
    fd = os.open(temp, flags, 0o600, dir_fd=dir_fd)
    try:
        offset = 0
        while offset < len(data):
            offset += os.write(fd, data[offset:])
        os.fchmod(fd, 0o600)
        os.fsync(fd)
        try:
            # link() is atomic and fails instead of replacing an existing name.
            os.link(temp, name, src_dir_fd=dir_fd, dst_dir_fd=dir_fd, follow_symlinks=False)
            os.fsync(dir_fd)
        except FileExistsError:
            pass
    finally:
        os.close(fd)
        try:
            os.unlink(temp, dir_fd=dir_fd)
        except FileNotFoundError:
            pass


def ensure(path: Path) -> str:
    directory_fd = open_directory(path.parent)
    try:
        try:
            return validate_and_read(directory_fd, path.name)
        except FileNotFoundError:
            create_if_absent(directory_fd, path.name)
            # Reopen the published inode with O_NOFOLLOW/O_NONBLOCK and validate it
            # before reading, including when another process won the creation race.
            return validate_and_read(directory_fd, path.name)
    finally:
        os.close(directory_fd)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--path", required=True)
    args = parser.parse_args()
    try:
        key = ensure(Path(args.path))
    except (OSError, ValueError):
        print("clé maître absente, invalide ou non privée", file=sys.stderr)
        return 1
    # gateway.sh captures this on a pipe; it is never an argument or log line.
    sys.stdout.write(key)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
