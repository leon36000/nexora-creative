#!/usr/bin/env bash
# Démarre la passerelle, vérifie les alias configurés et affiche la sonde informative de pc4.
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

rc=0
if [ "$mode" = providers ]; then
  echo "ATTENTION : le test des fournisseurs envoie une requête à chaque alias et peut entraîner des coûts."
  python3 "$SA_DIR/activation_check.py" \
    --base-url "$SA_URL" --key-file "$SA_HOME/master.key" \
    --config "$SA_DIR/litellm/config.yaml" --test-fournisseurs
  rc=$?
else
  python3 "$SA_DIR/activation_check.py" \
    --base-url "$SA_URL" --key-file "$SA_HOME/master.key" \
    --config "$SA_DIR/litellm/config.yaml"
  rc=$?
fi

# Sonde informative de disponibilité de la ferme Qwen sur pc4 (ne bloque jamais l'activation).
if [ "$rc" -eq 0 ] && [ "${SA_QWEN_PROBE:-1}" != "0" ] && [ -f "$SA_DIR/qwen_ctl.py" ]; then
  python3 -E -s -S "$SA_DIR/qwen_ctl.py" status-line --timeout "${SA_QWEN_PROBE_TIMEOUT:-1.0}" --keyfile "$SA_STRATA_KEYFILE" 2>/dev/null || true
fi

exit "$rc"
