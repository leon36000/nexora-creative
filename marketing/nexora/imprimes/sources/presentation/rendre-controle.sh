#!/usr/bin/env bash
# Contrôle visuel des .pptx : LibreOffice (polices installées depuis final/presentation/polices-a-installer via un fontconfig temporaire,
# sans rien installer sur le système) -> PDF -> PNG (une image par diapositive) dans sources/html/deck-controle/.
set -e
RACINE="$(cd "$(dirname "$0")/../.." && pwd)"
TMP="$(mktemp -d)"
cat > "$TMP/fonts.conf" <<XML
<?xml version="1.0"?><!DOCTYPE fontconfig SYSTEM "fonts.dtd"><fontconfig><dir>/usr/share/fonts</dir><dir>$RACINE/final/presentation/polices-a-installer</dir><cachedir>$TMP/cache</cachedir></fontconfig>
XML
OUT="$RACINE/sources/html/deck-controle"; mkdir -p "$OUT"
for l in fr en; do
  FONTCONFIG_FILE="$TMP/fonts.conf" soffice -env:UserInstallation=file://$TMP/profil --headless --convert-to pdf --outdir "$TMP" "$RACINE/final/presentation/presentation-nexora-ai-$l.pptx" >/dev/null 2>&1
  pdftoppm -r 80 -png "$TMP/presentation-nexora-ai-$l.pdf" "$OUT/deck-$l"
done
rm -rf "$TMP"; echo "images dans $OUT"
