#!/usr/bin/env bash
# Régénère tous les imprimés depuis coordonnees.json (à lancer après l'avoir rempli). Les images IA ne sont pas régénérées :
# voir LISEZMOI.md (generer.py puis sources/agrandir-lot.sh). Options : --coordonnees chemin.json --url-images https://…/images
set -e
D="$(dirname "$(readlink -f "$0")")"
while [ $# -gt 0 ]; do case "$1" in --coordonnees) export NEXORA_COORDONNEES="$2"; shift 2;; --url-images) URLIMG=(--url-images "$2"); shift 2;; *) shift;; esac; done
cd "$D/sources"
"$D/generer-cartes"
bun papeterie.mjs "${URLIMG[@]}"
bun affiches.mjs
bun depliants.mjs
bun salon.mjs
( cd presentation && bun actifs.mjs && bun deck.mjs && ./rendre-controle.sh )
bun apercu.mjs
