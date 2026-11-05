#!/usr/bin/env bash
# Démarre le serveur de détourage de pc3 sous superviseur (relance en cas d'arrêt), détaché de la session SSH.
# Sert tant que `loginctl enable-linger pc3` n'est pas actif (sans linger, systemd --user s'arrête à la déconnexion).
# Usage : ~/nexora-detourage/demarrer.sh   (idempotent)   ;   arrêt : ~/nexora-detourage/arreter.sh
set -euo pipefail
R="$HOME/nexora-detourage"
PID="$R/journaux/superviseur.pid"
if [[ -f "$PID" ]] && kill -0 "$(cat "$PID")" 2>/dev/null; then echo "déjà en marche (superviseur $(cat "$PID"))"; exit 0; fi
setsid nohup "$R/superviser.sh" >>"$R/journaux/superviseur.log" 2>&1 < /dev/null &
echo $! > "$PID"
echo "superviseur lancé ($(cat "$PID")) ; journal : $R/journaux/detourage.log"
