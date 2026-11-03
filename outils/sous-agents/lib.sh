# Fonctions communes (source). Ne jamais afficher les clés.
SA_HOME="${SA_HOME:-$HOME/.config/nexora-sous-agents}"
SA_STATE="${SA_STATE:-$HOME/.local/share/nexora-sous-agents}"
SA_PORT="${SA_PORT:-4410}"
SA_URL="http://127.0.0.1:${SA_PORT}"
SA_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SA_KEYFILE="${SA_KEYFILE:-/home/pc6/Desktop/Deepinfra.env}"
SA_IMAGE="ghcr.io/berriai/litellm@sha256:7294b90f868c5c38c99b83021c7ba46f9b439e95f8e32964c925c7d2563a03f7"  # = v1.106.2
SA_CONTAINER="nexora-sa-litellm"
mkdir -p "$SA_HOME" "$SA_STATE/runs"; chmod 700 "$SA_HOME"

sa_master_key() {  # crée la clé maître (0600) si absente et l'affiche sur stdout (usage interne uniquement)
  if [ ! -s "$SA_HOME/master.key" ]; then
    ( umask 077; printf 'sk-sa-%s' "$(openssl rand -hex 24)" > "$SA_HOME/master.key" )
  fi
  cat "$SA_HOME/master.key"
}
sa_extract() {  # sa_extract <Nom> : valeur de « Nom: valeur » dans le fichier des clés
  awk -F': *' -v n="$1" '$1==n {print $2; exit}' "$SA_KEYFILE" | tr -d '\r\n '
}
sa_up() { curl -s -m 3 -o /dev/null -w '%{http_code}' "$SA_URL/health/liveliness" 2>/dev/null | grep -q '^200$'; }
sa_alias() {  # deepseek|muse|gemini -> alias
  case "$1" in deepseek|eco-deepseek) echo eco-deepseek;; muse|eco-muse) echo eco-muse;; gemini|eco-gemini) echo eco-gemini;; *) return 1;; esac
}
