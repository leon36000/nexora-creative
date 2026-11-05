#!/usr/bin/env bash
# Fake launcher for offline tests; intentionally no gateway or model access.
set -eu
budget="${6:-}"
[[ "$budget" =~ ^[0-9]+([.][0-9]+)?$ && ${#budget} -le 128 ]] || {
  echo "budget invalide" >&2
  exit 2
}
exec python3 "$(dirname "$0")/fake_runner.py" "$@"
