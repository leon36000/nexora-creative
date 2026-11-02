#!/usr/bin/env bash
# Livraison de la promo V3 : copie des masters dans promo/montage/, encodages web (1080p H.264 < 25 Mo, 9:16), affiche,
# et manifeste propre à Creative (site-medias/manifest-creative.json ; manifest.json appartient à un autre agent).
# Usage : bash livrer.sh   (après monter_v3.py pour toutes les versions, voir ~/nexora-creative-data/promo/v3/tout-rendre.sh)
set -euo pipefail
F=~/nexora-creative-data/engine/ffmpeg/ffmpeg-7.0.2-arm64-static/ffmpeg
B=~/nexora-creative-data/promo/v3/brouillons
M=~/nexora-creative-data/promo/montage
W=~/nexora-creative-data/site-medias
mkdir -p "$M" "$W"
for f in 16x9 9x16; do for l in fr en; do
  cp "$B/v3-$f-$l-long.mp4" "$M/Nexora-Creative-promo-V3-$f-$l.mp4"
  cp "$B/v3-$f-$l-30.mp4" "$M/Nexora-Creative-promo-V3-$f-$l-30s.mp4"
  cp "$B/v3-$f-$l-15.mp4" "$M/Nexora-Creative-promo-V3-$f-$l-15s.mp4"
done; done
# Encodages web : 2 passes à débit visé (≈ 2,9 Mb/s vidéo pour 60 s → ≈ 23 Mo), son AAC 160 kb/s, démarrage rapide
web() { # entrée sortie largeur hauteur débit
  $F -v error -y -i "$1" -c:v libx264 -preset slow -b:v "$5" -pass 1 -passlogfile /tmp/v3web -vf "scale=$3:$4:flags=lanczos" -an -f null /dev/null
  $F -v error -y -i "$1" -c:v libx264 -preset slow -b:v "$5" -maxrate "$(( ${5%k} * 2 ))k" -bufsize "$(( ${5%k} * 4 ))k" -pass 2 -passlogfile /tmp/v3web \
     -vf "scale=$3:$4:flags=lanczos" -profile:v high -pix_fmt yuv420p -c:a aac -b:a 160k -movflags +faststart "$2"
  rm -f /tmp/v3web*
}
for l in fr en; do
  web "$M/Nexora-Creative-promo-V3-16x9-$l.mp4" "$W/film-creative-16x9-$l.mp4" 1920 1080 2900k
  web "$M/Nexora-Creative-promo-V3-9x16-$l.mp4" "$W/film-creative-9x16-$l.mp4" 1080 1920 2900k
  web "$M/Nexora-Creative-promo-V3-16x9-$l-30s.mp4" "$W/film-creative-16x9-$l-30s.mp4" 1920 1080 3500k
  web "$M/Nexora-Creative-promo-V3-9x16-$l-15s.mp4" "$W/film-creative-9x16-$l-15s.mp4" 1080 1920 3500k
done
# Affiche : le mur de la flotte qui s'allume au-dessus de la Terre (image du film, sans texte)
$F -v error -y -ss "${AFFICHE_T:-10.9}" -i "$M/Nexora-Creative-promo-V3-16x9-fr.mp4" -frames:v 1 -q:v 2 "$W/film-creative-poster.jpg"
$F -v error -y -ss "${AFFICHE_V:-10.9}" -i "$M/Nexora-Creative-promo-V3-9x16-fr.mp4" -frames:v 1 -q:v 2 "$W/film-creative-poster-9x16.jpg"
ls -la "$W"/film-creative-*
