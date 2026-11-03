#!/usr/bin/env bash
# Lance beaucoup de sous-agents en parallèle : un par fichier prompt.
# Usage : lot.sh <deepseek|muse|gemini> <dossier-de-prompts> <dossier-des-workdirs> [parallélisme=8]
#   Le prompt <dossier-de-prompts>/NOM.txt (ou .md) travaille dans <dossier-des-workdirs>/NOM/ (doit exister ; un dépôt par tâche).
# Variables : LOT_BUDGET (plafond global en $, défaut 5), LOT_RUN_BUDGET (par agent, défaut 0.30), LOT_TURNS (défaut 30).
# Sortie : ~/.local/share/nexora-sous-agents/lots/<id>/ (un sous-dossier par agent, index.tsv avec le résumé d'une ligne de chacun).
set -u; export LC_ALL=C
[ $# -ge 3 ] || { sed -n '2,6p' "$0" | sed 's/^# \{0,1\}//' >&2; exit 2; }
. "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/lib.sh"
ALIAS="$(sa_alias "$1")" || { echo "alias inconnu" >&2; exit 2; }
PDIR="$(readlink -f "$2")"; WDIR="$(readlink -f "$3")"; PAR="${4:-8}"
export LOT_ID="lot$(date +%H%M%S)-$RANDOM"; export LOT="$SA_STATE/lots/$LOT_ID"; mkdir -p "$LOT"
export LOT_BUDGET="${LOT_BUDGET:-5}" LOT_RUN_BUDGET="${LOT_RUN_BUDGET:-0.30}" LOT_TURNS="${LOT_TURNS:-30}" LOT_ALIAS="$ALIAS" WDIR SA_DIR SA_STATE
"$SA_DIR/gateway.sh" start >/dev/null || exit 1
one() {
  local p="$1" n; n="$(basename "$p")"; n="${n%.*}"
  local spent; spent="$(jq -s --arg t "$LOT_ID" '[.[]|select((.run//"")|startswith($t))|.cost]|add // 0' "$SA_STATE/usage.jsonl" 2>/dev/null || echo 0)"
  if awk -v s="$spent" -v b="$LOT_BUDGET" 'BEGIN{exit !(s>=b)}'; then printf 'SKIP:plafond_global\t%s\n' "$n" >> "$LOT/index.tsv"; return; fi
  [ -d "$WDIR/$n" ] || { printf 'SKIP:pas_de_workdir\t%s\n' "$n" >> "$LOT/index.tsv"; return; }
  local line; line="$(SA_TAG="$LOT_ID" SA_OUT="$LOT/$n" "$SA_DIR/sous-agent.sh" -w "$LOT_ALIAS" "$p" "$WDIR/$n" "$LOT_TURNS" "$LOT_RUN_BUDGET" 2>&1 | tail -1)"
  printf '%s\t%s\n' "$line" "$n" >> "$LOT/index.tsv"
}
export -f one
echo "lot $LOT_ID : $ALIAS, parallélisme $PAR, plafond global \$$LOT_BUDGET -> $LOT"
find "$PDIR" -maxdepth 1 -type f \( -name '*.txt' -o -name '*.md' \) | sort | xargs -r -P "$PAR" -I{} bash -c 'one "$1"' _ {}
echo "terminé ; index : $LOT/index.tsv"; "$SA_DIR/cout.sh" --run "$LOT_ID"
