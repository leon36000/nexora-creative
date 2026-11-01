#!/bin/bash
# Reconstruit toute la campagne SOCIAL et PUBLICITÉ (≈ 3 min) : images, PDF, calendrier, documents, planches-contact.
set -e
R="$(cd "$(dirname "$0")/../.." && pwd)"
(cd "$R/social/sources" && bun construire.mjs && python3 calendrier.py)
(cd "$R/publicite/sources" && python3 images_bannieres.py && bun construire.mjs && bun atterrissage.mjs && bun documents.mjs)
python3 "$R/social/sources/apercu_familles.py"
