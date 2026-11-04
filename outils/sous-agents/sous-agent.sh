#!/usr/bin/env bash
# Lance UN sous-agent Claude Code sur un modèle bon marché (via la passerelle LiteLLM locale).
# Usage : sous-agent.sh [-w] <deepseek|muse|gemini|eco-…> <fichier-prompt> <dossier-de-travail> [max-tours=30] [budget-usd=0.50]
#   -w  : attendre la fin (sinon : lancement en arrière-plan, la commande rend la main et affiche le dossier de résultat).
# Sortie : $SA_OUT (défaut ~/.local/share/nexora-sous-agents/runs/<id>/) contenant pid, result.json, transcript.jsonl, summary.txt, stderr.log.
# Variables : SA_TIMEOUT (secondes, défaut 900), SA_OUT, SA_TAG (préfixe d'identifiant, utilisé par lot.sh), SA_EXTRA_RO (dossiers montés en lecture seule, séparés par « : »).
#             SA_EFFORT (low|medium|high|xhigh|max : niveau d'effort de Claude Code, traduit en effort de raisonnement par la passerelle).
set -u; export LC_ALL=C
WAIT=0; [ "${1:-}" = "-w" ] && { WAIT=1; shift; }
[ $# -ge 3 ] || { sed -n '2,7p' "$0" | sed 's/^# \{0,1\}//' >&2; exit 2; }
. "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/lib.sh"
ALIAS="$(sa_alias "$1")" || { echo "alias inconnu : $1 (deepseek|muse|gemini)" >&2; exit 2; }
PROMPT="$(readlink -f "$2")"; WORK="$(readlink -f "$3")"; TURNS="${4:-30}"; BUDGET="${5:-0.50}"
[ -f "$PROMPT" ] || { echo "prompt introuvable : $2" >&2; exit 2; }
[ -d "$WORK" ] || { echo "dossier de travail introuvable : $3" >&2; exit 2; }
case "$WORK" in /|/home|/home/*/|"$HOME"|/usr*|/etc*|/var*|/root*) echo "dossier de travail refusé : $WORK" >&2; exit 2;; esac
sa_up || "$SA_DIR/gateway.sh" start >/dev/null || { echo "passerelle indisponible" >&2; exit 1; }
RUN="${SA_TAG:+$SA_TAG-}$(date +%Y%m%d-%H%M%S)-${ALIAS#eco-}-$$-$RANDOM"
OUT="${SA_OUT:-$SA_STATE/runs/$RUN}"; mkdir -p "$OUT"; chmod 700 "$OUT"
SOCKDIR="$SA_STATE/sock-$RUN"; mkdir -p "$SOCKDIR"; chmod 700 "$SOCKDIR"
echo "$OUT"
cat > "$OUT/meta.json" <<JSON
{"run":"$RUN","alias":"$ALIAS","workdir":"$WORK","max_turns":$TURNS,"budget_usd":$BUDGET,"start":"$(date -Is)"}
JSON

runner() {
  local t0=$SECONDS MK; MK="$(sa_master_key)"
  # pont gateway : socket unix côté hôte (la sandbox n'a PAS de réseau, seulement ce pont vers 127.0.0.1:$SA_PORT)
  socat UNIX-LISTEN:"$SOCKDIR/gw.sock",fork,mode=600 TCP:127.0.0.1:"$SA_PORT" 2>/dev/null & local BRIDGE=$!
  for _ in 1 2 3 4 5 6 7 8 9 10; do [ -S "$SOCKDIR/gw.sock" ] && break; sleep 0.2; done
  local RO=(); IFS=: read -ra EX <<<"${SA_EXTRA_RO:-}"; for d in "${EX[@]}"; do [ -n "$d" ] && RO+=(--ro-bind "$d" "$d"); done
  local CLAUDE_REAL NODE_DIR; CLAUDE_REAL="$(readlink -f "$(command -v claude)")"; NODE_DIR="$(dirname "$(readlink -f "$(command -v node)")")"
  local SYS="Tu es un sous-agent d'exécution. Travaille UNIQUEMENT dans le dossier courant ($WORK). Pas de réseau, pas de web. N'écris rien hors de ce dossier. Sois concis et vérifie ton travail en exécutant les tests ou commandes demandés. Termine par un court compte rendu : fichiers modifiés, commandes lancées, résultat, doutes éventuels."
  timeout --kill-after=10 "${SA_TIMEOUT:-900}" bwrap --die-with-parent --unshare-pid --unshare-net --unshare-ipc --unshare-uts \
    --ro-bind /usr /usr --symlink usr/bin /bin --symlink usr/sbin /sbin --symlink usr/lib /lib --symlink usr/lib64 /lib64 \
    --ro-bind /etc /etc --proc /proc --dev /dev --tmpfs /tmp \
    --ro-bind "$CLAUDE_REAL" /opt/claude --ro-bind "$NODE_DIR" /opt/node \
    "${RO[@]}" --bind "$WORK" "$WORK" --bind "$SOCKDIR" /run/sa --chdir "$WORK" \
    --setenv HOME /tmp/home --setenv PATH /opt/node:/usr/local/bin:/usr/bin:/bin --setenv CLAUDE_CONFIG_DIR /tmp/home/.claude \
    --setenv ANTHROPIC_BASE_URL "http://127.0.0.1:$SA_PORT" --setenv ANTHROPIC_API_KEY "$MK" --unsetenv ANTHROPIC_AUTH_TOKEN \
    --setenv ANTHROPIC_MODEL "$ALIAS" --setenv ANTHROPIC_SMALL_FAST_MODEL "$ALIAS" \
    --setenv ANTHROPIC_DEFAULT_OPUS_MODEL "$ALIAS" --setenv ANTHROPIC_DEFAULT_SONNET_MODEL "$ALIAS" --setenv ANTHROPIC_DEFAULT_HAIKU_MODEL "$ALIAS" \
    --setenv CLAUDE_CODE_SUBAGENT_MODEL "$ALIAS" --setenv ANTHROPIC_CUSTOM_HEADERS "x-sa-run: $RUN" \
    --setenv DISABLE_TELEMETRY 1 --setenv DISABLE_ERROR_REPORTING 1 --setenv DISABLE_AUTOUPDATER 1 --setenv DISABLE_BUG_COMMAND 1 \
    --setenv CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC 1 --setenv CLAUDE_CODE_DISABLE_AUTO_MEMORY 1 --setenv NO_COLOR 1 \
    --setenv CLAUDE_CODE_MAX_OUTPUT_TOKENS 16000 \
    sh -c 'mkdir -p /tmp/home/.claude; socat TCP-LISTEN:'"$SA_PORT"',bind=127.0.0.1,fork,reuseaddr UNIX-CONNECT:/run/sa/gw.sock & sleep 0.3; exec "$@"' sh \
    /opt/claude -p "$(cat "$PROMPT")" --bare --model "$ALIAS" ${SA_EFFORT:+--effort "$SA_EFFORT"} --output-format stream-json --verbose \
      --max-turns "$TURNS" --no-session-persistence --permission-mode dontAsk \
      --tools "Read,Edit,Write,Glob,Grep,Bash" --allowedTools "Read Edit Write Glob Grep Bash" \
      --disallowedTools "WebFetch WebSearch Agent Task Bash(git push:*) Bash(ssh:*) Bash(scp:*) Bash(sudo:*) Bash(curl:*) Bash(wget:*)" \
      --append-system-prompt "$SYS" --strict-mcp-config --disable-slash-commands \
      > "$OUT/transcript.jsonl" 2> "$OUT/stderr.log" &
  local PID=$!; echo $PID > "$OUT/pid"
  # garde-fou de dépense : somme du coût de CE run dans le journal de la passerelle
  local SPENT=0 CAPPED=0
  while kill -0 $PID 2>/dev/null; do
    sleep 4
    SPENT="$(jq -s --arg r "$RUN" '[.[]|select(.run==$r)|.cost]|add // 0' "$SA_STATE/usage.jsonl" 2>/dev/null || echo 0)"
    if awk -v s="$SPENT" -v b="$BUDGET" 'BEGIN{exit !(s>=b)}'; then CAPPED=1; kill -TERM $PID 2>/dev/null; sleep 2; kill -KILL $PID 2>/dev/null; break; fi
  done
  wait $PID 2>/dev/null; local RC=$?
  kill $BRIDGE 2>/dev/null; rm -rf "$SOCKDIR"
  jq -c 'select(.type=="result")' "$OUT/transcript.jsonl" 2>/dev/null | tail -1 > "$OUT/result.json"
  [ -s "$OUT/result.json" ] || echo "{\"type\":\"result\",\"is_error\":true,\"subtype\":\"no_result\",\"rc\":$RC}" > "$OUT/result.json"
  SPENT="$(jq -s --arg r "$RUN" '[.[]|select(.run==$r)|.cost]|add // 0' "$SA_STATE/usage.jsonl" 2>/dev/null || echo 0)"
  local TOK; TOK="$(jq -s --arg r "$RUN" '[.[]|select(.run==$r)]|"\(map(.in)|add // 0)in/\(map(.out)|add // 0)out/\(length)req"' -r "$SA_STATE/usage.jsonl" 2>/dev/null)"
  local ST; ST="$(jq -r 'if .is_error then "FAIL:"+(.subtype//"error") else "OK:"+(.subtype//"success") end' "$OUT/result.json")"
  [ $CAPPED = 1 ] && ST="FAIL:plafond_budget"; [ $RC = 124 ] && ST="FAIL:timeout"
  local TURNS_USED; TURNS_USED="$(jq -r '.num_turns // "?"' "$OUT/result.json")"
  printf '%s %s %s tours=%s cout=$%.5f jetons=%s duree=%ss dossier=%s\n' "$ST" "$ALIAS" "$RUN" "$TURNS_USED" "$SPENT" "$TOK" "$((SECONDS-t0))" "$OUT" > "$OUT/summary.txt"
  touch "$OUT/done"
}
if [ $WAIT = 1 ]; then runner; cat "$OUT/summary.txt"
else ( runner >/dev/null 2>&1 & ) ; sleep 0.2; echo "(arrière-plan ; suivre : cat $OUT/summary.txt une fois $OUT/done présent)"; fi
