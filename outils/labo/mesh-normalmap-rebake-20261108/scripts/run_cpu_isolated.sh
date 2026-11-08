#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 5 ]]; then
  echo "Usage: $0 COMFY_ROOT PYTHON OVERLAY_FILE RUN_DIR TEST_SCRIPT" >&2
  exit 2
fi

COMFY_ROOT=$(realpath "$1")
# Keep the venv's lexical entrypoint; resolving its symlink to /usr/bin/python bypasses pyvenv.cfg.
PYTHON=$2
if [[ "$PYTHON" != /* ]]; then
  PYTHON="$(pwd -P)/$PYTHON"
fi
OVERLAY_FILE=$(realpath "$3")
RUN_DIR=$(realpath "$4")
TEST_SCRIPT=$(realpath "$5")
TARGET_MODULE="$COMFY_ROOT/comfy_extras/nodes_mesh_postprocess.py"

for path in "$COMFY_ROOT" "$PYTHON" "$OVERLAY_FILE" "$RUN_DIR" "$TEST_SCRIPT"; do
  [[ -e "$path" ]] || { echo "Required path missing: $path" >&2; exit 2; }
done
[[ -d "$COMFY_ROOT" && -f "$PYTHON" && -f "$OVERLAY_FILE" && -d "$RUN_DIR" && -f "$TEST_SCRIPT" ]] || {
  echo "Path type mismatch" >&2; exit 2;
}
[[ -f "$TARGET_MODULE" ]] || { echo "Comfy Mesh module missing: $TARGET_MODULE" >&2; exit 2; }
mkdir -p "$RUN_DIR/tmp"

# Root is read-only; only RUN_DIR is writable. No HOME is set or changed. The copied module is
# mounted read-only over the canonical import path. The network namespace is isolated.
exec bwrap \
  --unshare-net \
  --ro-bind / / \
  --dev /dev \
  --proc /proc \
  --bind "$RUN_DIR" /run \
  --ro-bind "$OVERLAY_FILE" "$TARGET_MODULE" \
  --chdir /run \
  env -i \
    PATH=/usr/bin:/bin \
    PYTHONPATH="$COMFY_ROOT" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONNOUSERSITE=1 \
    CUDA_VISIBLE_DEVICES= \
    TMPDIR=/run/tmp \
    XDG_CACHE_HOME=/run/tmp/cache \
    "$PYTHON" -u "$TEST_SCRIPT"
