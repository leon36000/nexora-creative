#!/usr/bin/env bash
# Arrête le superviseur et son serveur (par fichier PID uniquement ; aucun pkill).
R="$HOME/nexora-detourage"; PID="$R/journaux/superviseur.pid"
if [[ -f "$PID" ]] && kill -0 "$(cat "$PID")" 2>/dev/null; then kill -TERM "$(cat "$PID")"; echo "arrêté"; else echo "pas en marche"; fi
rm -f "$PID"
