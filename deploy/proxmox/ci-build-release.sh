#!/bin/sh
# Job amd64 uniquement : chroot minimal, sans /proc ni fichiers d'environnement du runner.
set -eu
: "${CI_PROJECT_DIR:?}" "${CI_COMMIT_SHA:?}"
test "$(id -u)" = 0
test "$(uname -m)" = x86_64
command -v python3 >/dev/null
command -v g++ >/dev/null
command -v git >/dev/null
ROOT="$CI_PROJECT_DIR/.ci-release/chroot"
OUT="$CI_PROJECT_DIR/.ci-release/artefact"
mkdir -p "$ROOT" "$OUT"
mkdir -p "$CI_PROJECT_DIR/.ci-release/canari"
printf '%s\n' 'CANARI_SYNTHETIQUE=interdit' > "$CI_PROJECT_DIR/.ci-release/canari/.env"
env -i PATH=/usr/local/bin:/usr/bin:/bin HOME=/nonexistent PYTHONDONTWRITEBYTECODE=1 \
  python3 -B "$CI_PROJECT_DIR/deploy/proxmox/preparer_release.py" archive "$CI_PROJECT_DIR" "$CI_COMMIT_SHA" "$OUT/source.tar" > "$OUT/source.sha256"
# Seuls les exécutables/libs de l'image publique sont copiés ; aucun montage du workspace ni du HOME.
tar -C / --exclude='*/.env*' --exclude='*/.npmrc' -cf - usr bin lib lib64 | tar -C "$ROOT" -xf -
mkdir -p "$ROOT/etc/ssl" "$ROOT/dev" "$ROOT/tmp" "$ROOT/tools" "$ROOT/input" "$ROOT/work"
cp -a /etc/ssl/certs "$ROOT/etc/ssl/"
cp -L /etc/resolv.conf "$ROOT/etc/resolv.conf"
cp -L /etc/hosts "$ROOT/etc/hosts"
printf '%s\n' 'hosts: files dns' > "$ROOT/etc/nsswitch.conf"
printf '%s\n' 'nobody:x:65534:65534:CI:/work:/bin/sh' > "$ROOT/etc/passwd"
printf '%s\n' 'nogroup:x:65534:' > "$ROOT/etc/group"
mknod -m 666 "$ROOT/dev/null" c 1 3
mknod -m 666 "$ROOT/dev/urandom" c 1 9
chmod 1777 "$ROOT/tmp"
cp "$CI_PROJECT_DIR/deploy/proxmox/preparer_release.py" "$CI_PROJECT_DIR/deploy/proxmox/transaction_release.py" "$ROOT/tools/"
cp "$OUT/source.tar" "$ROOT/input/source.tar"
chmod 755 "$ROOT" "$ROOT/tools" "$ROOT/input"
chmod 644 "$ROOT/tools/"*.py "$ROOT/input/source.tar"
chown 65534:65534 "$ROOT/work"
SHA="$(cat "$OUT/source.sha256")"
env -i PATH=/usr/local/bin:/usr/bin:/bin HOME=/nonexistent \
  python3 -B - "$ROOT" "$SHA" "$CI_PROJECT_DIR/.ci-release/canari/.env" <<'PY'
import os, subprocess, sys
root, sha, canari = sys.argv[1:]
cmd = ['chroot', '--userspec=65534:65534', '--groups=65534', root, '/usr/bin/env', '-i',
       'PATH=/usr/local/bin:/usr/bin:/bin', 'HOME=/work', 'PYTHONDONTWRITEBYTECODE=1',
       'NEXORA_RELEASE_SANDBOX=ci-chroot', '/usr/bin/python3', '-B']
check = "import os,sys; assert os.geteuid()==65534 and os.getegid()==65534 and set(os.getgroups())<={65534}; assert not os.path.exists('/proc/self/environ'); assert not os.path.exists('/etc/nexora'); assert not os.path.exists('/root/.npmrc'); assert not os.path.exists(sys.argv[1])"
subprocess.run(cmd + ['-c', check, canari], check=True, close_fds=True, stdin=subprocess.DEVNULL)
subprocess.run(cmd + ['/tools/preparer_release.py', 'construire', '/input/source.tar', sha, '/work/release'],
               check=True, close_fds=True, stdin=subprocess.DEVNULL)
PY
printf '%s\n' "$CI_COMMIT_SHA" > "$ROOT/work/release/CI_COMMIT_SHA"
tar -C "$ROOT/work" -cf "$OUT/release.tar" release/app release/mode-studio/dist release/BUILD_OK release/SOURCE_FILES.json release/SOURCE_HASHES.json release/DEPENDANCES_SHA256 release/CI_COMMIT_SHA
(cd "$OUT" && sha256sum release.tar > release.sha256)
printf 'Release amd64 construite pour %s\n' "$CI_COMMIT_SHA"
