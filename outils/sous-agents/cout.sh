#!/usr/bin/env bash
# Totaux déclarés par la passerelle : un coût absent reste inconnu, jamais zéro.
set -u
SA_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec python3 "$SA_DIR/cout.py" "$@"
