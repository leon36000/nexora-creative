#!/usr/bin/env bash
# Essai de capacité : 3 tâches × 3 modèles. Usage : capacite.sh [racine=/tmp/sa-capacite]   (coût attendu < 1 $)
set -u; D="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"; ROOT="${1:-/tmp/sa-capacite}"
for m in deepseek muse gemini; do
  R="$ROOT/$m"; rm -rf "$R"; python3 "$D/fabrique.py" "$R"
  LOT_RUN_BUDGET="${LOT_RUN_BUDGET:-0.30}" LOT_BUDGET=2 "$D/../lot.sh" "$m" "$R/prompts" "$R/work" 3 > "$R/lot.log" 2>&1
  echo "== $m"; "$D/verifie.sh" "$R"; sort "$(grep -o '/home[^ ]*/lots/lot[^ ]*' "$R/lot.log" | head -1)/index.tsv" | cut -f1-2 | sed -E 's/dossier=.*//' 
done
