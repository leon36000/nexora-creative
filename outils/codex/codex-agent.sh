#!/usr/bin/env bash
# Lance un agent Codex (abonnement ChatGPT du fondateur) en arrière-plan.
# Usage : outils/codex/codex-agent.sh [-w] <sol|astra|terra> <high|xhigh|max> <fichier-prompt> <dossier-de-travail> [sandbox=workspace-write]
#   -w : attendre la fin au lieu de rendre la main.
# Résultat : <dossier>/.codex-agent/<horodatage>/{dernier-message.md,journal.log,pid,etat}
set -euo pipefail
ATTENDRE=0
[ "${1:-}" = "-w" ] && { ATTENDRE=1; shift; }
[ $# -ge 4 ] || { sed -n 2,5p "$0"; exit 2; }
case "$1" in
  sol) MODELE=gpt-6.1-sol ;; astra) MODELE=gpt-6-astra ;; terra) MODELE=gpt-6.1-terra ;;
  *) echo "modèle inconnu : $1" >&2; exit 2 ;;
esac
EFFORT=$2; PROMPT=$(realpath "$3"); DOSSIER=$(realpath "$4"); BAC=${5:-workspace-write}
CODEX=${CODEX_BIN:-/usr/lib/chatgpt/resources/codex}
[ -x "$CODEX" ] || CODEX=$(command -v codex)
SORTIE="$DOSSIER/.codex-agent/$(date +%Y%m%d-%H%M%S)-$1"
mkdir -p "$SORTIE"
lancer() {
  echo encours > "$SORTIE/etat"
  if "$CODEX" exec --skip-git-repo-check -C "$DOSSIER" -m "$MODELE" -c model_reasoning_effort="$EFFORT" \
       -s "$BAC" -o "$SORTIE/dernier-message.md" - < "$PROMPT" > "$SORTIE/journal.log" 2>&1
  then echo ok > "$SORTIE/etat"; else echo "echec:$?" > "$SORTIE/etat"; fi
}
if [ $ATTENDRE = 1 ]; then lancer; cat "$SORTIE/etat"; else
  ( lancer ) & echo $! > "$SORTIE/pid"; fi
echo "$SORTIE"
