#!/usr/bin/env bash
# Régénère toute la famille « identité » (logos, profils, verrouillages, icônes, guide fr + en, planche-contact).
# Prérequis : bun, Chromium de Playwright (voir identite/LISEZMOI.md), ghostscript et poppler (verrouillages SVG).
set -e
cd "$(dirname "$(readlink -f "$0")")/sources"
bun construire-identite.mjs
bun guide.mjs
bun apercu.mjs
