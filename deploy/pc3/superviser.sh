#!/usr/bin/env bash
# Boucle de supervision : lance serveur.py, le relance 5 s après un arrêt anormal. Ne tue rien d'autre que son enfant.
set -uo pipefail
R="$HOME/nexora-detourage"
set -a; . "$R/detourage.env"; set +a
export NEXORA_DETOURAGE_DOSSIER="$R/travaux" NEXORA_DETOURAGE_POIDS="$R/modeles" HF_HOME="$R/modeles/hf"
export NEXORA_DETOURAGE_JETON_FICHIER="$R/secrets/jeton" FFMPEG_BIN="$R/ffmpeg/bin/ffmpeg"
# Prise Unix d'administration (contrôles et bancs sur pc3) : mode 600, hors d'atteinte de la VM qemu.
export NEXORA_DETOURAGE_SOCKET="$R/secrets/detourage.sock"
enfant=0
trap '[[ $enfant -gt 0 ]] && kill -TERM $enfant 2>/dev/null; wait; exit 0' TERM INT
while true; do
  echo "$(date -Is) démarrage"
  "$R/venvs/rapide/bin/python" -I "$R/code/detourage/serveur.py" >>"$R/journaux/detourage.log" 2>&1 &
  enfant=$!; echo $enfant > "$R/journaux/serveur.pid"
  wait $enfant; code=$?
  echo "$(date -Is) arrêt (code $code)"
  sleep 5
done
