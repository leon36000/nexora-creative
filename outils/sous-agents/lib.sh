# Fonctions communes (source). Ne jamais afficher les clés.
SA_HOME="${SA_HOME:-$HOME/.config/nexora-sous-agents}"
SA_STATE="${SA_STATE:-$HOME/.local/share/nexora-sous-agents}"
SA_PORT="${SA_PORT:-4410}"
SA_URL="http://127.0.0.1:${SA_PORT}"
SA_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SA_KEYFILE="${SA_KEYFILE:-/home/pc6/Desktop/Deepinfra.env}"
SA_STRATA_KEYFILE="${SA_STRATA_KEYFILE:-$SA_HOME/strata.key}"
SA_QWEN_URL="${SA_QWEN_URL:-http://192.168.1.161:8080/v1}"
SA_QWEN_FALLBACK="${SA_QWEN_FALLBACK:-1}"
SA_QWEN_FALLBACK_MODEL="${SA_QWEN_FALLBACK_MODEL:-eco-deepseek}"
SA_QWEN_MAX_CONCURRENCY="${SA_QWEN_MAX_CONCURRENCY:-2}"
SA_QWEN_QUEUE_TIMEOUT="${SA_QWEN_QUEUE_TIMEOUT:-180}"
SA_QWEN_PROBE_TIMEOUT="${SA_QWEN_PROBE_TIMEOUT:-3}"
SA_QWEN_MAX_PROBE_MS="${SA_QWEN_MAX_PROBE_MS:-1500}"
SA_IMAGE="ghcr.io/berriai/litellm@sha256:7294b90f868c5c38c99b83021c7ba46f9b439e95f8e32964c925c7d2563a03f7"  # = v1.106.2
SA_CONTAINER="${SA_CONTAINER:-${SA_CONTAINER_NAME:-nexora-sa-litellm}}"
SA_CONTAINER_NAME="$SA_CONTAINER"
mkdir -p "$SA_HOME" "$SA_STATE/runs"; chmod 700 "$SA_HOME"

sa_master_key() {  # clé validée/créée par Python; sortie capturée en interne par gateway.sh
  python3 "$SA_DIR/master_key.py" --path "$SA_HOME/master.key"
}
sa_extract() {  # sa_extract <Nom> : valeur de « Nom: valeur » dans le fichier des clés
  awk -F': *' -v n="$1" '$1==n {print $2; exit}' "$SA_KEYFILE" 2>/dev/null | tr -d '\r\n '
}
sa_strata_key() {  # clé optionnelle du serveur Strata/llama-server (pc4), jamais affichée en clair
  local val=""
  [ -r "$SA_KEYFILE" ] && val="$(sa_extract Strata)"
  if [ -z "$val" ]; then
    val="$(python3 -E -s -S -c '
import os, re, stat, sys
def read_safe(p):
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
    try: fd = os.open(p, flags)
    except OSError: return ""
    try:
        st = os.fstat(fd)
        if not stat.S_ISREG(st.st_mode) or st.st_uid != os.getuid() or (stat.S_IMODE(st.st_mode) & 0o077):
            return ""
        return os.read(fd, 4096).decode("utf-8", "ignore")
    finally:
        os.close(fd)
raw = read_safe(sys.argv[1]).strip()
if raw and not any(c.isspace() for c in raw):
    print(raw); raise SystemExit(0)
env_raw = read_safe(sys.argv[2])
for line in env_raw.splitlines():
    m = re.match(r"^(?:export\s+)?STRATA_PC4_API_KEY=[\"\x27]?([^\"\x27\s]+)[\"\x27]?\s*$", line.strip())
    if m:
        print(m.group(1)); raise SystemExit(0)
' "$SA_STRATA_KEYFILE" "$HOME/.config/gitspace/pc4-dsh.env" 2>/dev/null)"
  fi
  printf '%s\n' "${val:-sk-strata-local}"
}
sa_up() { curl --noproxy '*' -s -m 3 -o /dev/null -w '%{http_code}' "$SA_URL/health/liveliness" 2>/dev/null | grep -q '^200$'; }
sa_alias() {  # nom court -> alias de la passerelle
  case "$1" in
    deepseek|eco-deepseek) echo eco-deepseek;;
    muse|eco-muse) echo eco-muse;;
    gemini|eco-gemini) echo eco-gemini;;
    gemini-eleve|eco-gemini-eleve) echo eco-gemini-eleve;;
    qwen|eco-qwen) echo eco-qwen;;
    carbon|eco-carbon) echo eco-carbon;;
    carbon-eleve|eco-carbon-eleve) echo eco-carbon-eleve;;
    terra|eco-terra) echo eco-terra;;
    sol|eco-sol) echo eco-sol;;
    argon|eco-argon) echo eco-argon;;
    kimi|eco-kimi) echo eco-kimi;;
    *) return 1;;
  esac
}
sa_model() { sa_alias "$@"; }
