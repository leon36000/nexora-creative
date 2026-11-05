#!/usr/bin/env bash
# Teste uniquement les fixtures hors ligne ; les quatre tests client réel sont une preuve locale distincte.
set -eu
ROOT="${SA_CI_ROOT:?SA_CI_ROOT requis}"
WORK="$ROOT/.ci-sousagents/${SA_CI_RUN_ID:-run}"
TEST_TMP="${SA_CI_TMPDIR:-$WORK/tmp}"
mkdir -p "$WORK/home" "$TEST_TMP" "$WORK/cache" "$WORK/bin" "$WORK/repo/outils/sous-agents"
ln -s /bin/true "$WORK/bin/node"
python3 - "$ROOT/outils/sous-agents" "$WORK/repo/outils/sous-agents" <<'PY'
from pathlib import Path
import shutil, sys
src, dst = map(Path, sys.argv[1:])
for p in src.rglob('*'):
    if p.is_symlink() or not p.is_file() or p.suffix not in ('.py', '.sh'):
        continue
    if p.name == 'test_real_client_local.py':
        continue
    target = dst / p.relative_to(src)
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(p, target)
config = dst / 'litellm/config.yaml'
config.parent.mkdir(parents=True, exist_ok=True)
config.write_text('model_list:\n  - model_name: eco-deepseek\n  - model_name: eco-muse\n  - model_name: eco-gemini\n  - model_name: eco-gemini-eleve\n')
PY
cd "$WORK/repo"
if env -i HOME="$WORK/home" PATH="$WORK/bin:/usr/local/bin:/usr/bin:/bin" TMPDIR="$TEST_TMP" XDG_CACHE_HOME="$WORK/cache" PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest discover -s outils/sous-agents/tests -p 'test_*.py' -v > "$WORK/tests.log" 2>&1; then
  cat "$WORK/tests.log"
else
  cat "$WORK/tests.log"
  exit 1
fi
