#!/usr/bin/env bash
# Totalise la dépense des sous-agents depuis le journal de la passerelle (jetons et coûts, jamais les prompts).
# Usage : cout.sh [--since AAAA-MM-JJ] [--run <préfixe-d'identifiant>]
set -u; export LC_ALL=C
. "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/lib.sh"
SINCE=""; RUNP=""
while [ $# -gt 0 ]; do case "$1" in --since) SINCE="$2"; shift 2;; --run) RUNP="$2"; shift 2;; *) echo "usage: $0 [--since AAAA-MM-JJ] [--run préfixe]" >&2; exit 2;; esac; done
[ -s "$SA_STATE/usage.jsonl" ] || { echo "journal vide"; exit 0; }
jq -rs --arg since "$SINCE" --arg rp "$RUNP" '
  map(select(($since==""  or .ts>=$since) and ($rp=="" or ((.run//"")|startswith($rp)))))
  | group_by(.alias) | map({alias:.[0].alias, req:length, echecs:(map(select(.ok|not))|length), in:(map(.in)|add), out:(map(.out)|add), usd:(map(.cost // 0)|add)})
  | (.[] | "\(.alias)\t\(.req) req\t\(.echecs) echecs\t\(.in) in\t\(.out) out\t$\(.usd*100000|round/100000)"),
    "TOTAL\t\(map(.req)|add) req\t\(map(.echecs)|add) echecs\t\(map(.in)|add) in\t\(map(.out)|add) out\t$\(((map(.usd)|add) // 0)*100000|round/100000)"' \
  "$SA_STATE/usage.jsonl" | column -t -s $'\t'
