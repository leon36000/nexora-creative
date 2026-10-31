#!/usr/bin/env bash
# Lance Nexora Creative en développement sur pc6 avec l'assistant d'écriture branché sur le LiteLLM de développement
# de NexoraSite (modèle cloud). La clé est lue au lancement depuis ~/Desktop/NexoraSite/.env, jamais recopiée.
set -euo pipefail
cd "$(dirname "$0")/.."
if [ -f "$HOME/Desktop/NexoraSite/.env" ]; then
  set -a; . "$HOME/Desktop/NexoraSite/.env" >/dev/null 2>&1; set +a
  export NEXORA_LLM_BASE_URL="${NEXORA_LLM_BASE_URL:-${LITELLM_BASE_URL%/}/v1}"
  export NEXORA_LLM_CLE="${NEXORA_LLM_CLE:-$LITELLM_MASTER_KEY}"
  export NEXORA_LLM_MODELE="${NEXORA_LLM_MODELE:-dev/cloud-glm-5-3}"
fi
exec npm run dev
