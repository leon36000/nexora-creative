#!/usr/bin/env bash
# Lance un ORCHESTRATEUR non-Claude (Terra, Gemini 4 Carbon, Sol, Qwen…) : le CLI de Nexora LifeCode tourne dans un worktree, avec ses outils
# (Bash, Edit, tests, git) et peut lancer à son tour des essaims avec outils/sous-agents (sous-agent.sh, lot.sh). Le modèle passe par la passerelle locale.
# Usage : orchestrateur.sh [-w] <terra|carbon|carbon-eleve|sol|deepseek|muse|qwen|eco-…> <fichier-prompt> <worktree> [max-tours=250] [budget-usd=12]
#   -w : attendre la fin (sinon arrière-plan). Sortie : $OR_OUT (défaut ~/.local/share/nexora-sous-agents/orchestrateurs/<id>/) : pid, rapport.json, journal.log, summary.txt.
# Variables : OR_ROUNDS (tours de pilotage max, défaut 6 : relance tant que $OUT/FINI n'existe pas), OR_LIFECODE (dépôt LifeCode qui fournit src/core/cli-runner.js ; défaut /home/pc6/nexora-recherche/integ2), OR_TIMEOUT (secondes, défaut 14400), OR_EFFORT (défaut high).
# Le worktree est le SEUL dossier où l'orchestrateur doit écrire ; il ne pousse jamais (le chef de projet fusionne). Pas de bac à sable : même confiance que les agents Sonnet.
set -u; export LC_ALL=C
WAIT=0; [ "${1:-}" = "-w" ] && { WAIT=1; shift; }
[ $# -ge 3 ] || { sed -n '2,7p' "$0" | sed 's/^# \{0,1\}//' >&2; exit 2; }
. "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/lib.sh"
REQUESTED_ALIAS="$(sa_alias "$1")" || { echo "alias inconnu : $1" >&2; exit 2; }
PROMPT="$(readlink -f "$2")"; WORK="$(readlink -f "$3")"; TURNS="${4:-250}"; BUDGET="${5:-12}"
[[ "$TURNS" =~ ^[1-9][0-9]*$ ]] || { echo "max-tours invalide" >&2; exit 2; }
[[ "$BUDGET" =~ ^[0-9]+([.][0-9]+)?$ ]] || { echo "budget invalide" >&2; exit 2; }
[ -f "$PROMPT" ] || { echo "prompt introuvable : $2" >&2; exit 2; }
[ -d "$WORK" ] || { echo "worktree introuvable : $3" >&2; exit 2; }
case "$WORK" in /|/home|/home/*/|"$HOME"|/usr*|/etc*|/var*|/root*|"$HOME/Desktop"|"$HOME/.config"*|"$HOME/.ssh"*) echo "dossier refusé : $WORK" >&2; exit 2;; esac
git -C "$WORK" rev-parse --show-toplevel >/dev/null 2>&1 || { echo "le dossier doit être un worktree git" >&2; exit 2; }
LC="${OR_LIFECODE:-/home/pc6/nexora-recherche/integ2}"
[ -f "$LC/src/core/cli-runner.js" ] || { echo "CLI LifeCode introuvable : $LC/src/core/cli-runner.js" >&2; exit 2; }
[ -r "$SA_HOME/master.key" ] || { echo "clé de la passerelle illisible (outils/sous-agents/activer.sh)" >&2; exit 2; }
curl --noproxy '*' -fs -m 5 "http://127.0.0.1:${SA_PORT:-4410}/health/liveliness" >/dev/null 2>&1 || curl --noproxy '*' -fs -m 5 "http://127.0.0.1:${SA_PORT:-4410}/v1/models" -H "Authorization: Bearer $(cat "$SA_HOME/master.key")" >/dev/null 2>&1 || { echo "passerelle injoignable : lancer outils/sous-agents/activer.sh" >&2; exit 2; }

ALIAS="$REQUESTED_ALIAS"
FALLBACK_NOTE=""
if [ "$REQUESTED_ALIAS" = "eco-qwen" ]; then
  DECISION="$(python3 -E -s -S "$SA_DIR/qwen_ctl.py" resolve eco-qwen --keyfile "$SA_STRATA_KEYFILE" 2>/dev/null)" || DECISION=""
  OK_DEC="$(jq -r '.ok // false' <<< "$DECISION" 2>/dev/null || echo false)"
  if [ "$OK_DEC" != "true" ]; then
    REASON="$(jq -r '.reason // "indisponible"' <<< "$DECISION" 2>/dev/null || echo indisponible)"
    echo "pc4 (eco-qwen) indisponible ($REASON) et SA_QWEN_FALLBACK=0" >&2
    exit 1
  fi
  ALIAS="$(jq -r '.model' <<< "$DECISION")"
  if [ "$(jq -r '.fallback_used // false' <<< "$DECISION")" = "true" ]; then
    REASON="$(jq -r '.reason // "repli"' <<< "$DECISION")"
    FALLBACK_NOTE=" ; repli_depuis : eco-qwen ($REASON)"
  fi
fi

ID="$(date +%Y%m%d-%H%M%S)-orch-$1-$$"
OUT="${OR_OUT:-$SA_STATE/orchestrateurs/$ID}"; mkdir -p "$OUT/cfg"; chmod 700 "$OUT"
# Réglages minimaux : ni mémoire AMD ni apprentissage (l'orchestrateur ne doit pas écrire dans la mémoire du fondateur), pas de bac à sable (il a besoin de git, des tests et des sous-agents).
cat > "$OUT/cfg/settings.json" <<'JSON'
{ "amd": { "enabled": false }, "memory": { "enabled": false, "sessionRecall": { "enabled": false }, "changeHistory": { "enabled": false } }, "externalRag": { "enabled": false }, "learning": { "review": { "enabled": false } }, "sandbox": { "mode": "off" } }
JSON
ROUNDS="${OR_ROUNDS:-6}"; [[ "$ROUNDS" =~ ^[1-9][0-9]*$ ]] || ROUNDS=6
PER_BUDGET="$(python3 -c "print(round($BUDGET/$ROUNDS*1.2,2))")"
protocole() {  # texte ajouté à chaque tour de pilotage
  cat <<TXT

PROTOCOLE DE FIN (pilotage automatique) : tu es relancé automatiquement, au plus $ROUNDS fois, tant que le fichier $OUT/FINI n'existe pas. Une réponse finale sans ce fichier = on te relance : ne t'arrête donc JAMAIS pour « faire le point », « proposer la suite » ou « attendre » : avance. À chaque relance : (1) lis ton plan et ton rapport dans ton worktree et \`git log --oneline\` de ta branche pour reprendre où tu en étais, (2) avance sur le prochain élément non fait des critères de fin du brief. Crée le fichier avec \`touch $OUT/FINI\` UNIQUEMENT quand tous les critères de fin du brief sont atteints et prouvés ET que ton rapport final est commité, ou après un blocage dur que tu as documenté dans le rapport (dis lequel).
TXT
}
run() {
  cd "$WORK" || exit 2
  local code=0 k=1
  while [ "$k" -le "$ROUNDS" ]; do
    local ROUND_ALIAS="$ALIAS"
    if [ "$REQUESTED_ALIAS" = "eco-qwen" ]; then
      local DEC OK_D
      DEC="$(python3 -E -s -S "$SA_DIR/qwen_ctl.py" resolve eco-qwen --keyfile "$SA_STRATA_KEYFILE" 2>/dev/null)" || DEC=""
      OK_D="$(jq -r '.ok // false' <<< "$DEC" 2>/dev/null || echo false)"
      [ "$OK_D" = "true" ] && ROUND_ALIAS="$(jq -r '.model' <<< "$DEC")"
    fi
    local SLOT_PREFIX=()
    if [ "$ROUND_ALIAS" = "eco-qwen" ]; then
      SLOT_PREFIX=(python3 -E -s -S "$SA_DIR/qwen_ctl.py" with-slot --lock-dir "$SA_STATE/locks/qwen" --slots "${SA_QWEN_MAX_CONCURRENCY:-2}" --wait "${SA_QWEN_QUEUE_TIMEOUT:-180}" --timeout-exit 75 --)
    fi
    local P; if [ "$k" -eq 1 ]; then P="$(cat "$PROMPT")$(protocole)"; else P="RELANCE n°$k sur $ROUNDS : tu n'as pas encore créé $OUT/FINI. $(cat "$PROMPT")$(protocole)"; fi
    NEXORA_API_KEY="$(cat "$SA_HOME/master.key")" NEXORA_LIFECODE_CONFIG_DIR="$OUT/cfg" NEXORA_SANDBOX_MODE=off NEXORA_LIFECODE_AUTO_APPROVE=1 \
    "${SLOT_PREFIX[@]}" timeout --kill-after=30 "${OR_TIMEOUT:-14400}" node "$LC/src/core/cli-runner.js" \
      --provider orch-gateway --base-url "http://127.0.0.1:${SA_PORT:-4410}/v1" --model "$ROUND_ALIAS" --effort "${OR_EFFORT:-high}" \
      --max-turns "$TURNS" --max-tool-calls "$((TURNS * 4))" --max-budget-usd "$PER_BUDGET" --cwd "$WORK" --no-register --auto-approve --quiet \
      --output-json "$OUT/rapport-$k.json" --prompt "$P" > "$OUT/journal-$k.log" 2>&1
    code=$?; cp -f "$OUT/rapport-$k.json" "$OUT/rapport.json" 2>/dev/null
    echo "$(date +%H:%M:%S) tour de pilotage $k/$ROUNDS terminé (modèle=$ROUND_ALIAS code=$code)" >> "$OUT/pilotage.log"
    [ -e "$OUT/FINI" ] && break
    k=$((k + 1))
  done
  { echo "orchestrateur : $1 ($ALIAS)$FALLBACK_NOTE ; tours de pilotage : $((k > ROUNDS ? ROUNDS : k)) ; FINI : $([ -e "$OUT/FINI" ] && echo oui || echo non) ; dernier code : $code ; worktree : $WORK"; python3 - "$OUT/rapport.json" <<'PY' 2>/dev/null
import json,sys
r=json.load(open(sys.argv[1]))
for k in ("status","turns","durationSec","finalOutput"):
    if k in r: print(k+" :", str(r[k])[:1200])
PY
  } > "$OUT/summary.txt"
  touch "$OUT/done"
}
echo "$ID" > "$OUT/id"
if [ "$WAIT" = 1 ]; then run "$@"; cat "$OUT/summary.txt"; else ( run "$@" ) >/dev/null 2>&1 & echo $! > "$OUT/pid"; echo "$OUT"; echo "(arrière-plan ; suivre : $OUT/journal.log, $OUT/summary.txt, $OUT/done)"; fi
