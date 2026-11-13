#!/usr/bin/env bash
# Lance un lot de sous-agents après validation complète des prompts et workdirs.
# Usage : lot.sh <deepseek|muse|gemini|gemini-eleve|qwen> <dossier-de-prompts> <dossier-des-workdirs> [parallélisme=8] [--create-workdirs]
# Les workdirs absents sont ignorés sauf si --create-workdirs est demandé.
# LOT_BUDGET est indicatif par invocation (non partagé entre lots simultanés) ;
# LOT_RUN_BUDGET réserve une part par agent. Un appel en vol peut dépasser sa réserve.
set -u
export LC_ALL=C
SA_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
. "$SA_DIR/lib.sh"
export SA_DIR SA_STATE
exec python3 "$SA_DIR/lot.py" "$@"
