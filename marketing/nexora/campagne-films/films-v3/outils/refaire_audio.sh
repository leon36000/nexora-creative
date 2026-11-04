#!/usr/bin/env bash
# Refait l'audio d'un film V5 sans toucher aux images : narration (moteur de ../audio-choix.json ou $2), mixage, puis
# remultiplexage des deux formats (finir.py réutilise les images déjà rendues).  Usage : refaire_audio.sh <film> [moteur]
set -euo pipefail
cd "$(dirname "$0")"
python3 voix.py "$1" ${2:-}
python3 mixer.py "$1" ${2:-}
for f in 16x9 9x16; do python3 finir.py "$1" "$f"; done
