#!/usr/bin/env bash
set -euo pipefail
HERE="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
: "${MESH_ORACLE_ASSET_ROOT:?Set the explicit, verified Storage asset root}"
: "${MESH_ORACLE_RUN_DIR:?Set a new explicit run directory under Storage/Nexora/travail}"
: "${MESH_NODE_PACKAGE_JSON:?Set the existing package.json with pinned dependencies; do not install}"
python3 "$HERE/verify_inputs.py" --assets-root "$MESH_ORACLE_ASSET_ROOT" --run-dir "$MESH_ORACLE_RUN_DIR"
export MESH_ORACLE_ASSET_ROOT="$(realpath -- "$MESH_ORACLE_ASSET_ROOT")"
export MESH_ORACLE_RUN_DIR="$(realpath -- "$MESH_ORACLE_RUN_DIR")"
export MESH_NODE_PACKAGE_JSON="$(realpath -- "$MESH_NODE_PACKAGE_JSON")"
node "$HERE/create-storm-oracle.mjs"
node "$HERE/generate-oracle-n32.mjs"
node "$HERE/generate-oracle-n64.mjs"
node "$HERE/create-normal-variants.mjs"
