#!/usr/bin/env bash
# Lance le Creative de la branche (ports 37170/37171) avec le LLM de production (OpenRouter, z-ai/glm-5.3) pour les
# captures du film V6. La clé est lue dans le fichier de clés et gardée en variable : jamais affichée ni écrite.
set -euo pipefail
. "/home/pc6/Desktop/Nexora Creative/outils/sous-agents/lib.sh"
cd "$(dirname "$0")/../../../app"
export NEXORA_LLM_BASE_URL=https://openrouter.ai/api/v1
export NEXORA_LLM_MODELE="${NEXORA_LLM_MODELE:-z-ai/glm-5.3}"
NEXORA_LLM_CLE="$(sa_extract Openrouter)"; export NEXORA_LLM_CLE
export PATH=/home/pc6/nexora-creative-data/engine/ffmpeg/ffmpeg-7.0.2-arm64-static:$PATH
exec npm run dev
