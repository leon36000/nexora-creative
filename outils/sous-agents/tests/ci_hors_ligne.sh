#!/usr/bin/env bash
# Fixtures hors ligne ; les quatre tests du client réel restent une preuve locale distincte.
set -eu
ROOT="${SA_CI_ROOT:?SA_CI_ROOT requis}"
WORK="$ROOT/.ci-sousagents/${SA_CI_RUN_ID:-run}"
TEST_TMP="${SA_CI_TMPDIR:-$WORK/tmp}"
PYTHON="${SA_CI_PYTHON:-$(command -v python3)}"
mkdir -p "$WORK/home" "$TEST_TMP" "$WORK/cache" "$WORK/bin" "$WORK/coverage"
ln -s /bin/true "$WORK/bin/node"
cd "$ROOT"
export HOME="$WORK/home" TMPDIR="$TEST_TMP" XDG_CACHE_HOME="$WORK/cache" PYTHONDONTWRITEBYTECODE=1
export PATH="$WORK/bin:$(dirname "$PYTHON"):/usr/local/bin:/usr/bin:/bin"
export PYTHONPATH="$ROOT/outils/sous-agents/tests"
export COVERAGE_FILE="$WORK/coverage/.coverage" COVERAGE_RCFILE="$ROOT/outils/sous-agents/tests/coverage-ci.ini"
if "$PYTHON" -m coverage run -m unittest -v \
  test_activation test_cost_snapshot test_cout test_lot test_lot_direct test_proxy test_proxy_launcher test_proxy_launcher_direct test_runner test_sa_callbacks > "$WORK/tests.log" 2>&1; then
  cat "$WORK/tests.log"
else
  cat "$WORK/tests.log"
  exit 1
fi
"$PYTHON" -m coverage combine "$WORK/coverage"
"$PYTHON" -m coverage report > "$WORK/coverage-report.txt"
cat "$WORK/coverage-report.txt"
"$PYTHON" -m coverage xml -o "$ROOT/.ci-sousagents/coverage.xml"
