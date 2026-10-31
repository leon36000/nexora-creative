#!/usr/bin/env bash
# Télécharge des fichiers de poids Hugging Face un par un, avec reprise et garde de disque.
# Usage : telecharger-poids.sh <dossier_modeles> <depot> <chemin_dans_depot> <sous-dossier> [...]
set -euo pipefail
MIN_LIBRE_GO=${MIN_LIBRE_GO:-50}
dest_root=$1; shift
while [ $# -ge 3 ]; do
  repo=$1 file=$2 sub=$3; shift 3
  out="$dest_root/$sub/$(basename "$file")"
  taille=$(curl -sIL --max-time 60 "https://huggingface.co/$repo/resolve/main/$file" | awk 'tolower($1)=="content-length:"{v=$2} END{print v+0}')
  libre=$(df --output=avail -B1 "$dest_root" | tail -1)
  deja=$( [ -f "$out" ] && stat -c %s "$out" || echo 0 )
  besoin=$(( taille - deja ))
  if [ $(( libre - besoin )) -lt $(( MIN_LIBRE_GO * 1000000000 )) ]; then
    echo "REFUS $file : il resterait moins de ${MIN_LIBRE_GO} Go libres"; exit 3
  fi
  if [ "$deja" -eq "$taille" ] && [ "$taille" -gt 0 ]; then echo "DÉJÀ $out"; continue; fi
  echo "$(date -Is) DÉBUT $repo/$file ($((taille/1000000)) Mo)"
  curl -sSL --retry 5 -C - -o "$out" "https://huggingface.co/$repo/resolve/main/$file"
  echo "$(date -Is) FIN $out $(stat -c %s "$out")"
done
