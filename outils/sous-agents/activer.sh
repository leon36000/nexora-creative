#!/usr/bin/env bash
# Active et vérifie les sous-agents (passerelle LiteLLM locale) : à lancer au début de chaque session.
set -u
cd "$(dirname "$0")/../.." || exit 1
outils/sous-agents/gateway.sh start >/dev/null 2>&1
K=$(cat "$HOME/.config/nexora-sous-agents/master.key" 2>/dev/null) || { echo "clé de passerelle absente"; exit 1; }
for m in eco-deepseek eco-muse eco-gemini eco-gemini-eleve; do
  r=$(curl -s -m 120 http://127.0.0.1:4410/v1/chat/completions -H "Authorization: Bearer $K" -H 'Content-Type: application/json' \
      -d "{\"model\":\"$m\",\"messages\":[{\"role\":\"user\",\"content\":\"Réponds seulement: OK\"}],\"max_tokens\":2000}")
  printf "%-18s %s\n" "$m" "$(echo "$r" | python3 -c 'import sys,json; d=json.load(sys.stdin); print("OK" if "choices" in d else "ÉCHEC "+str(d.get("error",d))[:120])' 2>&1)"
done
echo "--- coût d'aujourd'hui"; outils/sous-agents/cout.sh --since "$(date +%F)" 2>&1 | tail -8
