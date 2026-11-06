#!/usr/bin/env bash
# Lance UN sous-agent Claude Code sur un modèle bon marché (via la passerelle LiteLLM locale).
# Usage : sous-agent.sh [-w] <deepseek|muse|gemini|eco-…> <fichier-prompt> <dossier-de-travail> [max-tours=30] [budget-usd=0.50]
#   -w  : attendre la fin (sinon : lancement en arrière-plan, la commande rend la main et affiche le dossier de résultat).
# Sortie : $SA_OUT (défaut ~/.local/share/nexora-sous-agents/runs/<id>/) contenant pid, result.json, transcript.jsonl, summary.txt, stderr.log.
# Variables : SA_TIMEOUT (secondes, défaut 900), SA_OUT, SA_TAG (préfixe d'identifiant, utilisé par lot.sh), SA_EXTRA_RO (dossiers montés en lecture seule, séparés par « : »).
set -u; export LC_ALL=C
INTERNAL_RUN_ID=""
if [ "${1:-}" = "--runner-internal-run-id" ]; then
  [ $# -ge 2 ] || { echo "identifiant de run interne manquant" >&2; exit 2; }
  INTERNAL_RUN_ID="$2"; shift 2
fi
unset SA_INTERNAL_RUN_ID
WAIT=0; [ "${1:-}" = "-w" ] && { WAIT=1; shift; }
[ $# -ge 3 ] || { sed -n '2,7p' "$0" | sed 's/^# \{0,1\}//' >&2; exit 2; }
. "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/lib.sh"
ALIAS="$(sa_alias "$1")" || { echo "alias inconnu : $1 (deepseek|muse|gemini)" >&2; exit 2; }
PYTHON_BIN="$(command -v python3)" || { echo "Python indisponible" >&2; exit 2; }
TIMEOUT_LIMIT="$("$PYTHON_BIN" -E -s -S -c 'import decimal,re,sys
x=sys.argv[1]; m=re.fullmatch(r"([+]?(?:[0-9]+(?:[.][0-9]*)?|[.][0-9]+)(?:[eE][+-]?[0-9]+)?)([smhd]?)",x)
if not m: sys.exit(2)
try:
 d=decimal.Decimal(m.group(1))*{"":1,"s":1,"m":60,"h":3600,"d":86400}[m.group(2)]
 if not d.is_finite() or d<=0 or d>1000000000: sys.exit(2)
 print(int(d.to_integral_value(rounding=decimal.ROUND_CEILING)))
except decimal.DecimalException: sys.exit(2)' "${SA_TIMEOUT:-900}")" || { echo "SA_TIMEOUT invalide" >&2; exit 2; }

[[ -x "$PYTHON_BIN" ]] || { echo "Python indisponible" >&2; exit 2; }
PROMPT="$(readlink -f "$2")"; WORK="$(readlink -f "$3")"; TURNS="${4:-30}"; BUDGET="${5:-0.50}"
[[ "$TURNS" =~ ^[1-9][0-9]*$ ]] || { echo "max-tours invalide" >&2; exit 2; }
[[ "$BUDGET" =~ ^[0-9]+([.][0-9]+)?$ && ${#BUDGET} -le 128 ]] && \
  "$PYTHON_BIN" -E -s -S -c 'from decimal import Decimal; import sys; d=Decimal(sys.argv[1]); sys.exit(0 if d.is_finite() and d>0 else 1)' "$BUDGET" >/dev/null 2>&1 || { echo "budget invalide" >&2; exit 2; }
[[ "${SA_TIMEOUT:-900}" =~ ^[1-9][0-9]*$ ]] || { echo "délai invalide" >&2; exit 2; }
LEDGER_WAIT="${SA_LEDGER_WAIT:-3}"
[[ "$LEDGER_WAIT" =~ ^[0-9]+([.][0-9]+)?$ ]] && \
  "$PYTHON_BIN" -E -s -S -c 'from decimal import Decimal; import sys; d=Decimal(sys.argv[1]); sys.exit(0 if d.is_finite() and 0<=d<=60 else 1)' "$LEDGER_WAIT" >/dev/null 2>&1 || { echo "délai de rapprochement invalide" >&2; exit 2; }
[ -f "$PROMPT" ] || { echo "prompt introuvable : $2" >&2; exit 2; }
[ -d "$WORK" ] || { echo "dossier de travail introuvable : $3" >&2; exit 2; }
case "$WORK" in /|/home|/home/*/|"$HOME"|/usr*|/etc*|/var*|/root*) echo "dossier de travail refusé : $WORK" >&2; exit 2;; esac
# Refuse les montages qui contiennent ou se trouvent dans des emplacements de secrets connus.
protected_mount() {
  local candidate="$1" protected canonical
  canonical="$(realpath -e -- "$candidate")" || return 2
  case "$canonical" in /|/tmp|/run|/home|"$HOME"|"$HOME/Desktop"|"$HOME/Documents"|/media|/mnt|/usr|/etc|/var|/root) return 1;; esac
  local sensitive=("$SA_HOME" "$SA_STATE" "$SA_KEYFILE" "$HOME/.ssh" "$HOME/.aws" "$HOME/.config" "$HOME/.codex")
  local extra=(); IFS=: read -ra extra <<< "${SA_FORBID_PATHS:-}"
  sensitive+=("${extra[@]}")
  for protected in "${sensitive[@]}"; do
    [ -n "$protected" ] || continue
    protected="$(realpath -m -- "$protected")" || return 2
    if [[ "$canonical" == "$protected" || "$canonical" == "$protected/"* || "$protected" == "$canonical/"* ]]; then return 1; fi
  done
  return 0
}
safe_output_path() {
  local requested="$1" canonical state_root runs_root lots_root base protected state_zone=0
  [[ "$requested" != *$'\n'* && "$requested" != *$'\r'* ]] || return 1
  [ ! -L "$requested" ] || return 1
  canonical="$(realpath -m -- "$requested")" || return 1
  state_root="$(realpath -m -- "$SA_STATE")" || return 1
  runs_root="${state_root%/}/runs"
  lots_root="${state_root%/}/lots"
  for base in "$runs_root" "$lots_root"; do
    [[ "$canonical" == "$base/"* ]] && state_zone=1
    [ "$canonical" != "$base" ] || return 1
  done
  if [[ "$canonical" == "$state_root" || "$canonical" == "$state_root/"* || "$state_root" == "$canonical/"* ]]; then
    [ "$state_zone" = 1 ] || return 1
  fi
  case "$state_root" in
    /|/etc|/etc/*|/usr|/usr/*|/var|/var/*|/root|/root/*|/proc|/proc/*|/sys|/sys/*|/dev|/dev/*|/run|/run/*) return 1;;
  esac
  case "$canonical" in
    /|/home|/tmp|/tmp/*|/etc|/etc/*|/usr|/usr/*|/var|/var/*|/root|/root/*|/proc|/proc/*|/sys|/sys/*|/dev|/dev/*|/run|/run/*)
      [ "$state_zone" = 1 ] || return 1;;
  esac
  local sensitive=("$SA_HOME" "$SA_KEYFILE" "$HOME/.ssh" "$HOME/.aws" "$HOME/.config" "$HOME/.codex")
  for protected in "${sensitive[@]}"; do
    [ -n "$protected" ] || continue
    base="$(realpath -m -- "$protected")" || return 1
    if [[ "$canonical" == "$base" || "$canonical" == "$base/"* || "$base" == "$canonical/"* ]]; then
      return 1
    fi
  done
  printf '%s\n' "$canonical"
}
protected_mount "$WORK" || { echo "dossier de travail recouvre un emplacement protégé ou est illisible" >&2; exit 2; }
IFS=: read -ra EXTRA_MOUNTS <<< "${SA_EXTRA_RO:-}"
for mount in "${EXTRA_MOUNTS[@]}"; do
  [ -n "$mount" ] || continue
  protected_mount "$mount" || { echo "lecture supplémentaire recouvre un emplacement protégé ou est illisible" >&2; exit 2; }
done
RUN="${INTERNAL_RUN_ID:-${SA_TAG:+$SA_TAG-}$(date +%Y%m%d-%H%M%S)-${ALIAS#eco-}-$$-$RANDOM}"
case "$RUN" in *[!A-Za-z0-9_.-]*|"") echo "identifiant de run invalide" >&2; exit 2;; esac
[ "${#RUN}" -le 128 ] || { echo "identifiant de run invalide" >&2; exit 2; }
# Ne jamais transmettre la clé à un service local non identifié ni remplacer un conteneur existant.
[[ "$SA_PORT" =~ ^[0-9]{1,5}$ ]] && (( 10#$SA_PORT >= 1 && 10#$SA_PORT <= 65535 )) || { echo "port invalide" >&2; exit 2; }
GATEWAY_INFO="$(docker inspect --format '{{.State.Running}}|{{.Config.Image}}|{{range (index .NetworkSettings.Ports "4000/tcp")}}{{.HostIp}}:{{.HostPort}},{{end}}' "$SA_CONTAINER" 2>/dev/null)" || {
  echo "passerelle non identifiée ; lancer activer.sh puis vérifier son état" >&2; exit 1;
}
[ "$GATEWAY_INFO" = "true|$SA_IMAGE|127.0.0.1:$SA_PORT," ] || {
  echo "identité, image ou port de la passerelle inattendu ; lancement refusé" >&2; exit 1;
}
sa_up || { echo "passerelle indisponible ; aucun redémarrage automatique" >&2; exit 1; }
OUT_REQUESTED="${SA_OUT:-$SA_STATE/runs/$RUN}"
OUT="$(safe_output_path "$OUT_REQUESTED")" || { echo "dossier de résultats protégé ou illisible" >&2; exit 2; }
# Audit et résultats du relais ne doivent pas être accessibles en écriture par le modèle.
for mount in "$WORK" "${EXTRA_MOUNTS[@]}"; do
  [ -n "$mount" ] || continue
  canonical="$(realpath -e -- "$mount")" || { echo "montage illisible" >&2; exit 2; }
  if [[ "$canonical" == "$OUT" || "$canonical" == "$OUT/"* || "$OUT" == "$canonical/"* ]]; then
    echo "résultats et dossier de l’agent se recouvrent ; lancement refusé" >&2; exit 2
  fi
done
if [ -z "$INTERNAL_RUN_ID" ]; then
  if [ -e "$OUT" ] || [ -L "$OUT" ]; then
    echo "dossier résultat déjà présent, aucun écrasement : $OUT" >&2; exit 2
  fi
  for reserved in meta.json pid superviseur.pid done summary.txt result.json transcript.jsonl stderr.log lancement.log proxy.log proxy-audit.jsonl; do
    if [ -e "$OUT/$reserved" ] || [ -L "$OUT/$reserved" ]; then
      echo "résultat déjà présent, aucun écrasement : $OUT" >&2; exit 2
    fi
  done
else
  HANDOFF="$OUT/.runner-handoff"
  if [ ! -d "$OUT" ] || [ ! -O "$OUT" ] || [ "$(stat -c '%a' -- "$OUT" 2>/dev/null)" != 700 ] \
      || [ ! -f "$OUT/meta.json" ] || [ -L "$OUT/meta.json" ] || [ ! -O "$OUT/meta.json" ] \
      || [ "$(stat -c '%a' -- "$OUT/meta.json" 2>/dev/null)" != 600 ] || [ ! -s "$OUT/meta.json" ] || [ -e "$OUT/done" ] \
      || ! jq -e --arg run "$RUN" --arg alias "$ALIAS" --arg workdir "$WORK" \
          --argjson turns "$TURNS" --argjson budget "$BUDGET" \
          '.run == $run and .alias == $alias and .workdir == $workdir and .max_turns == $turns and .budget_usd == $budget' \
          "$OUT/meta.json" >/dev/null 2>&1; then
    echo "reprise interne invalide" >&2; exit 2
  fi
  if [ ! -f "$HANDOFF" ] || [ -L "$HANDOFF" ] || [ ! -O "$HANDOFF" ] \
      || [ "$(stat -c '%a' -- "$HANDOFF" 2>/dev/null)" != 600 ] \
      || [ "$(< "$HANDOFF")" != "$RUN" ]; then
    echo "reprise interne invalide" >&2; exit 2
  fi
  for reserved in pid done summary.txt result.json transcript.jsonl stderr.log proxy.log proxy-audit.jsonl; do
    if [ -e "$OUT/$reserved" ] || [ -L "$OUT/$reserved" ]; then
      echo "résultat interne déjà présent" >&2; exit 2
    fi
  done
  "$PYTHON_BIN" -E -s -S -c 'import os,sys; os.unlink(sys.argv[1])' "$HANDOFF" >/dev/null 2>&1 \
    || { echo "reprise interne invalide" >&2; exit 2; }
fi
umask 077
if [ -z "$INTERNAL_RUN_ID" ]; then
  mkdir -p "$OUT" && chmod 700 "$OUT" || { echo "dossier résultat inaccessible" >&2; exit 1; }
  echo "$OUT"
  jq -n --arg run "$RUN" --arg alias "$ALIAS" --arg workdir "$WORK" \
    --argjson turns "$TURNS" --argjson budget "$BUDGET" --arg start "$(date -Is)" \
    '{run:$run,alias:$alias,workdir:$workdir,max_turns:$turns,budget_usd:$budget,start:$start}' \
    > "$OUT/meta.json" || { echo "création de métadonnées impossible" >&2; exit 1; }
fi


# Le signal 0 peut lui-même être refusé : seul ESRCH ou un zombie lisible
# permet de considérer un enfant comme terminé avant wait.
child_ended() {
  "$PYTHON_BIN" -E -s -S -c 'import os,sys
p=int(sys.argv[1])
try:
 os.kill(p,0)
except ProcessLookupError: sys.exit(0)
except (PermissionError,OSError): sys.exit(2)
try:
 s=open("/proc/%d/stat"%p).read().rsplit(")",1)[1].split()[0]
except (OSError,IndexError): sys.exit(2)
sys.exit(0 if s=="Z" else 1)' "$1"
}

if [ "$WAIT" != 1 ]; then
  # Une nouvelle session survit à la fin du shell appelant ; les résultats restent dans OUT.
  ( set -o noclobber; printf '%s\n' "$RUN" > "$OUT/.runner-handoff" ) \
    || { echo "transmission arrière-plan impossible" >&2; exit 1; }
  SA_OUT="$OUT" nohup setsid "$SA_DIR/sous-agent.sh" --runner-internal-run-id "$RUN" -w \
    "$ALIAS" "$PROMPT" "$WORK" "$TURNS" "$BUDGET" > "$OUT/lancement.log" 2>&1 < /dev/null &
  SUPERVISEUR=$!
  printf '%s\n' "$SUPERVISEUR" > "$OUT/superviseur.pid"
  for _ in 1 2 3 4 5 6 7 8 9 10; do
    [ -s "$OUT/pid" ] || [ -e "$OUT/done" ] || { if ! child_ended "$SUPERVISEUR"; then sleep 0.2; continue; fi; }
    break
  done
  if [ -e "$OUT/done" ]; then
    if [ -s "$OUT/summary.txt" ] && [[ "$(cat "$OUT/summary.txt")" == OK:* ]]; then
      echo "(terminé en arrière-plan : $OUT/summary.txt)"
      exit 0
    fi
    echo "échec du lancement ou de l’exécution ; voir $OUT/summary.txt" >&2
    exit 1
  elif [ -s "$OUT/pid" ]; then
    echo "(arrière-plan confirmé ; suivre : $OUT/summary.txt et $OUT/done)"
  elif ! child_ended "$SUPERVISEUR"; then
    echo "(démarrage non confirmé ; ne pas relancer, vérifier $OUT/summary.txt et $OUT/done)" >&2
    exit 2
  else
    echo "échec du lancement ; voir $OUT/lancement.log" >&2
    exit 1
  fi
  exit 0
fi

SOCKDIR="$(mktemp -d /tmp/nexora-sa.XXXXXXXX)" || { echo "création du socket impossible" >&2; exit 1; }
chmod 700 "$SOCKDIR"
BRIDGE_PID=""
BRIDGE_STOP_RC=0
# Le jeton est le starttime du noyau ; un PID réattribué ne peut pas le remplacer.
capture_child() {
  "$PYTHON_BIN" -E -s -S -c 'import os,sys
try:
 p, parent=map(int,sys.argv[1:]); s=open("/proc/%d/stat"%p).read().rsplit(")",1)[1].split()
 if int(s[1]) != parent: sys.exit(1)
 print(s[19])
except (OSError,ValueError,IndexError): sys.exit(1)' "$1" "$$"
}
signal_child() {
  "$PYTHON_BIN" -E -s -S -c 'import os,signal,sys
try:
 p,parent=map(int,sys.argv[1:3]); token=sys.argv[3]; sig=getattr(signal, "SIG"+sys.argv[4])
 fd=os.pidfd_open(p)
 try:
  s=open("/proc/%d/stat"%p).read().rsplit(")",1)[1].split()
  if int(s[1]) != parent or s[19] != token: sys.exit(2)
  signal.pidfd_send_signal(fd,sig)
 finally: os.close(fd)
except (OSError,ValueError,IndexError,AttributeError): sys.exit(2)' "$1" "$$" "$2" "$3"
}
wait_child_bounded() {
  local pid="$1"
  WAIT_CHILD_CONFIRMED=0
  for _ in {1..50}; do
    if child_ended "$pid"; then WAIT_CHILD_CONFIRMED=1; wait "$pid" 2>/dev/null; return $?; fi
    sleep 0.1
  done
  return 125
}
stop_bridge() {
  [ -n "$BRIDGE_PID" ] || return 0
  printf 'arrêt demandé\n' > "$OUT/proxy-stop" || return 1
  local rc=0
  wait_child_bounded "$BRIDGE_PID" || rc=$?
  BRIDGE_STOP_RC="$rc"
  if [ "$WAIT_CHILD_CONFIRMED" = 0 ]; then
    printf 'arrêt du relais non confirmé, pid=%s ; socket conservé\n' "$BRIDGE_PID" >&2
    return 1
  fi
  BRIDGE_PID=""
  return 0
}
cleanup_socket() {
  local avant=$?
  if ! stop_bridge; then
    printf 'arrêt du relais non confirmé\n' > "$OUT/proxy-stop-error"
    [ "$avant" -ne 0 ] && exit "$avant"
    exit 1
  fi
  rm -f -- "$SOCKDIR/gw.sock" 2>/dev/null
  rmdir -- "$SOCKDIR" 2>/dev/null
}
trap cleanup_socket EXIT

# Result: records, exact Decimal total, audit attempts, pending attempts.
# Never turn an invalid or unreconciled cost into zero.
spent_snapshot() {
  local WAIT_SECS="${1:-}" WAIT_OPT=() RESULT
  [ -n "$WAIT_SECS" ] && WAIT_OPT=(--wait-seconds "$WAIT_SECS")
  RESULT="$("$PYTHON_BIN" -E -s -S "$SA_DIR/cost_snapshot.py" --ledger "$SA_STATE/usage.jsonl" \
    --audit "$OUT/proxy-audit.jsonl" --run "$RUN" "${WAIT_OPT[@]}" 2>/dev/null)" || return 1
  jq -er '[.records, .spent, .attempts, .pending] | @tsv' <<< "$RESULT" 2>/dev/null
}
decimal_ge() {
  "$PYTHON_BIN" -E -s -S -c 'from decimal import Decimal, InvalidOperation; import sys
try: a,b=Decimal(sys.argv[1]),Decimal(sys.argv[2])
except (InvalidOperation, ValueError): sys.exit(2)
if not a.is_finite() or not b.is_finite(): sys.exit(2)
sys.exit(0 if a>=b else 1)' "$1" "$2" >/dev/null 2>&1
}
format_cost() {
  "$PYTHON_BIN" -E -s -S -c 'from decimal import Decimal, InvalidOperation; import sys
try: d=Decimal(sys.argv[1])
except (InvalidOperation, ValueError): sys.exit(2)
if not d.is_finite() or d<0: sys.exit(2)
print("<$0.00001" if 0<d<Decimal("0.00001") else "$"+format(d,".5f"))' "$1" 2>/dev/null
}

runner() {
  local t0=$SECONDS
  # Le relais hôte injecte la vraie clé ; la sandbox ne reçoit qu'un identifiant factice.
  (
    exec env -i SA_PROXY_RUN="$RUN" SA_PROXY_MODEL="$ALIAS" SA_PROXY_PORT="$SA_PORT" \
      SA_PROXY_TIMEOUT="${SA_TIMEOUT:-900}" SA_PROXY_AUDIT="$OUT/proxy-audit.jsonl" \
      SA_PROXY_LEDGER="$(realpath -m -- "$SA_STATE/usage.jsonl")" SA_PROXY_BUDGET="$BUDGET" \
      SA_PROXY_LEDGER_WAIT="$LEDGER_WAIT" \
      "$PYTHON_BIN" -E -s -S "$SA_DIR/proxy_launcher.py" "$SA_HOME/master.key" \
      "$SA_DIR/sa_proxy.py" "$SOCKDIR/gw.sock"
  ) > "$OUT/proxy.log" 2>&1 & BRIDGE_PID=$!
  local BRIDGE_RC=0
  for _ in 1 2 3 4 5 6 7 8 9 10; do
    [ -S "$SOCKDIR/gw.sock" ] && break
    if child_ended "$BRIDGE_PID"; then wait "$BRIDGE_PID" 2>/dev/null; BRIDGE_RC=$?; BRIDGE_PID=""; break; fi
    sleep 0.2
  done
  if [ ! -S "$SOCKDIR/gw.sock" ]; then
    local WAIT_RC=0
    stop_bridge || WAIT_RC=125
    [ "$WAIT_RC" -eq 0 ] && WAIT_RC="$BRIDGE_STOP_RC"
    [ "$BRIDGE_RC" -eq 0 ] && BRIDGE_RC=$WAIT_RC
    local START_SUBTYPE="pont_indisponible"
    [ "$BRIDGE_RC" -eq 3 ] && START_SUBTYPE="cle_indisponible"
    [ "$BRIDGE_RC" -eq 4 ] && START_SUBTYPE="journal_indisponible"
    printf '{"type":"result","is_error":true,"subtype":"%s"}\n' "$START_SUBTYPE" > "$OUT/result.json"
    printf 'FAIL:%s %s %s cout=aucun_appel dossier=%s\n' "$START_SUBTYPE" "$ALIAS" "$RUN" "$OUT" > "$OUT/summary.txt"
    touch "$OUT/done"
    return 1
  fi
  # Aucun secret du processus parent ne doit parvenir à la sandbox.
  unset ANTHROPIC_API_KEY ANTHROPIC_AUTH_TOKEN
  local RO=(); IFS=: read -ra EX <<<"${SA_EXTRA_RO:-}"; for d in "${EX[@]}"; do [ -n "$d" ] && RO+=(--ro-bind "$d" "$d"); done
  local CLAUDE_REAL NODE_DIR; CLAUDE_REAL="$(readlink -f "$(command -v claude)")"; NODE_DIR="$(dirname "$(readlink -f "$(command -v node)")")"
  local SYS="Tu es un sous-agent d'exécution. Travaille UNIQUEMENT dans le dossier courant ($WORK). Pas de réseau, pas de web. N'écris rien hors de ce dossier. Sois concis et vérifie ton travail en exécutant les tests ou commandes demandés. Termine par un court compte rendu : fichiers modifiés, commandes lancées, résultat, doutes éventuels."
  local CLIENT_START=$SECONDS TIMED_OUT=0
  timeout --kill-after=10 "${SA_TIMEOUT:-900}" bwrap --clearenv --die-with-parent --unshare-pid --unshare-net --unshare-ipc --unshare-uts \
    --ro-bind /usr /usr --symlink usr/bin /bin --symlink usr/sbin /sbin --symlink usr/lib /lib --symlink usr/lib64 /lib64 \
    --ro-bind /etc /etc --proc /proc --dev /dev --tmpfs /tmp \
    --ro-bind "$CLAUDE_REAL" /opt/claude --ro-bind "$NODE_DIR" /opt/node \
    "${RO[@]}" --bind "$WORK" "$WORK" --bind "$SOCKDIR" /run/sa --chdir "$WORK" \
    --setenv HOME /tmp/home --setenv PATH /opt/node:/usr/local/bin:/usr/bin:/bin --setenv CLAUDE_CONFIG_DIR /tmp/home/.claude \
    --setenv ANTHROPIC_BASE_URL "http://127.0.0.1:$SA_PORT" --setenv ANTHROPIC_API_KEY "nexora-sandbox" \
    --setenv ANTHROPIC_MODEL "$ALIAS" --setenv ANTHROPIC_SMALL_FAST_MODEL "$ALIAS" \
    --setenv ANTHROPIC_DEFAULT_OPUS_MODEL "$ALIAS" --setenv ANTHROPIC_DEFAULT_SONNET_MODEL "$ALIAS" --setenv ANTHROPIC_DEFAULT_HAIKU_MODEL "$ALIAS" \
    --setenv CLAUDE_CODE_SUBAGENT_MODEL "$ALIAS" --setenv ANTHROPIC_CUSTOM_HEADERS "x-sa-run: $RUN" \
    --setenv DISABLE_TELEMETRY 1 --setenv DISABLE_ERROR_REPORTING 1 --setenv DISABLE_AUTOUPDATER 1 --setenv DISABLE_BUG_COMMAND 1 \
    --setenv CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC 1 --setenv CLAUDE_CODE_DISABLE_AUTO_MEMORY 1 --setenv NO_COLOR 1 \
    --setenv CLAUDE_CODE_MAX_OUTPUT_TOKENS 16000 \
    sh -c 'mkdir -p /tmp/home/.claude; socat TCP-LISTEN:'"$SA_PORT"',bind=127.0.0.1,fork,reuseaddr UNIX-CONNECT:/run/sa/gw.sock & sleep 0.3; exec "$@"' sh \
    /opt/claude -p --bare --model "$ALIAS" --output-format stream-json --verbose \
      --max-turns "$TURNS" --no-session-persistence --permission-mode dontAsk \
      --tools "Read,Edit,Write,Glob,Grep,Bash" --allowedTools "Read Edit Write Glob Grep Bash" \
      --disallowedTools "WebFetch WebSearch Agent Task Bash(git push:*) Bash(ssh:*) Bash(scp:*) Bash(sudo:*) Bash(curl:*) Bash(wget:*)" \
      --append-system-prompt "$SYS" --strict-mcp-config --disable-slash-commands \
      < "$PROMPT" > "$OUT/transcript.jsonl" 2> "$OUT/stderr.log" &
  local PID=$! CLIENT_TOKEN=""; echo $PID > "$OUT/pid"
  CLIENT_TOKEN="$(capture_child "$PID")" || CLIENT_TOKEN=""
  # Surveillance locale indicative : une requête en vol peut dépasser le budget.
  local SPENT=0 COUNT=0 ATTEMPTS=0 PENDING=0 CAPPED=0 UNKNOWN=0 SNAP="" COMPARE_RC=0
  while ! child_ended "$PID"; do
    for _ in {1..40}; do
      child_ended "$PID" && break
      if (( SECONDS - CLIENT_START >= TIMEOUT_LIMIT )); then
        TIMED_OUT=1; signal_child "$PID" "$CLIENT_TOKEN" TERM 2>/dev/null || true; break
      fi
      sleep 0.1
    done
    [ "$TIMED_OUT" = 1 ] && break
    child_ended "$PID" && break
    if ! SNAP="$(spent_snapshot)"; then
      sleep 1
      if ! SNAP="$(spent_snapshot)"; then
        UNKNOWN=1; signal_child "$PID" "$CLIENT_TOKEN" TERM 2>/dev/null || true; break
      fi
    fi
    read -r COUNT SPENT ATTEMPTS PENDING <<< "$SNAP"
    if decimal_ge "$SPENT" "$BUDGET"; then
      CAPPED=1; signal_child "$PID" "$CLIENT_TOKEN" TERM 2>/dev/null || true; sleep 2; signal_child "$PID" "$CLIENT_TOKEN" KILL 2>/dev/null || true; break
    else
      COMPARE_RC=$?
      if [ "$COMPARE_RC" -gt 1 ]; then
        UNKNOWN=1; signal_child "$PID" "$CLIENT_TOKEN" TERM 2>/dev/null || true; break
      fi
    fi
  done
  local RC=0 CLIENT_NON_CONFIRME=0
  wait_child_bounded "$PID" || RC=$?
  if [ "$WAIT_CHILD_CONFIRMED" = 0 ]; then CLIENT_NON_CONFIRME=1; UNKNOWN=1; fi
  local RELAIS_NON_CONFIRME=0
  stop_bridge || { RELAIS_NON_CONFIRME=1; UNKNOWN=1; }
  jq -c 'select(.type=="result")' "$OUT/transcript.jsonl" 2>/dev/null | tail -1 > "$OUT/result.json"
  [ -s "$OUT/result.json" ] || echo "{\"type\":\"result\",\"is_error\":true,\"subtype\":\"no_result\",\"rc\":$RC}" > "$OUT/result.json"
  # Wait a bounded interval for every audited call's exact call tag to appear in the ledger.
  if ! SNAP="$(spent_snapshot "$LEDGER_WAIT")"; then UNKNOWN=1
  else
    read -r COUNT SPENT ATTEMPTS PENDING <<< "$SNAP"
    [ "$PENDING" = 0 ] || UNKNOWN=1
    [[ "$ATTEMPTS" =~ ^[1-9][0-9]*$ ]] || UNKNOWN=1
    if decimal_ge "$SPENT" "$BUDGET"; then CAPPED=1
    else
      COMPARE_RC=$?
      [ "$COMPARE_RC" -gt 1 ] && UNKNOWN=1
    fi
  fi
  local TOK; TOK="$(jq -s --arg r "$RUN" '
    [.[] | select(.run == $r or ((.run | type) == "string" and (.run | startswith($r + "--p"))))] |
    (if all(.[]; ((.in | type) == "number") and (.in >= 0)) then (map(.in) | add // 0 | tostring) else "?" end) as $i |
    (if all(.[]; ((.out | type) == "number") and (.out >= 0)) then (map(.out) | add // 0 | tostring) else "?" end) as $o |
    "\($i)in/\($o)out/\(length)req"
  ' -r "$SA_STATE/usage.jsonl" 2>/dev/null || printf '?')"
  local ST; ST="$(jq -r 'if .type != "result" or .is_error != false then "FAIL:"+(.subtype//"error") else "OK:"+(.subtype//"success") end' "$OUT/result.json")"
  [ "$RC" -ne 0 ] && case "$ST" in OK:*) ST="FAIL:processus";; esac
  [ "$UNKNOWN" = 1 ] && ST="FAIL:cout_inconnu"
  [ "$CAPPED" = 1 ] && ST="FAIL:plafond_budget"
  { [ "$RC" = 124 ] || [ "$TIMED_OUT" = 1 ]; } && ST="FAIL:timeout"

  local TURNS_USED; TURNS_USED="$(jq -r '.num_turns // "?"' "$OUT/result.json")"
  local COUT COUT_EXACT
  if [ "$UNKNOWN" = 1 ]; then COUT="inconnu"; COUT_EXACT="inconnu"
  else
    COUT_EXACT="$SPENT"
    COUT="$(format_cost "$SPENT")" || { COUT="inconnu"; COUT_EXACT="inconnu"; UNKNOWN=1; ST="FAIL:cout_inconnu"; }
  fi
  local ETAT_CLIENT="confirme" ETAT_RELAIS="confirme"
  [ "$CLIENT_NON_CONFIRME" = 1 ] && ETAT_CLIENT="non_confirme"
  [ "$RELAIS_NON_CONFIRME" = 1 ] && ETAT_RELAIS="non_confirme"
  printf '%s %s %s num_turns_client=%s cout=%s cout_exact=%s source_cout=estimation_passerelle jetons=%s duree=%ss arret_client=%s arret_relais=%s dossier=%s\n' \
    "$ST" "$ALIAS" "$RUN" "$TURNS_USED" "$COUT" "$COUT_EXACT" "$TOK" "$((SECONDS-t0))" "$ETAT_CLIENT" "$ETAT_RELAIS" "$OUT" > "$OUT/summary.txt"
  touch "$OUT/done"
}
runner
if [ ! -s "$OUT/summary.txt" ]; then
  echo "échec : aucun résumé produit ; voir $OUT" >&2
  exit 1
fi
cat "$OUT/summary.txt"
case "$(cat "$OUT/summary.txt")" in OK:*) exit 0;; *) exit 1;; esac
