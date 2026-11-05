#!/usr/bin/env bash
# Démarre la passerelle et vérifie les quatre alias par défaut.
set -u
SA_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
. "$SA_DIR/lib.sh"

mode=providers
case "$#:${1:-}" in
  0:) ;;
  1:--test-fournisseurs) mode=providers ;;
  1:--local) mode=local ;;
  *) echo "usage: $0 [--local|--test-fournisseurs]" >&2; exit 2 ;;
esac

"$SA_DIR/gateway.sh" start || { echo "passerelle indisponible; contrôles interrompus" >&2; exit 1; }

if [ "$mode" = providers ]; then
  echo "ATTENTION : le test des fournisseurs envoie une requête à chaque alias et peut entraîner des coûts."
  exec python3 "$SA_DIR/activation_check.py" \
    --base-url "$SA_URL" --key-file "$SA_HOME/master.key" \
    --config "$SA_DIR/litellm/config.yaml" --test-fournisseurs
fi

python3 "$SA_DIR/activation_check.py" \
  --base-url "$SA_URL" --key-file "$SA_HOME/master.key" \
  --config "$SA_DIR/litellm/config.yaml"
