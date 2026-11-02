#!/usr/bin/env bash
# Encodage web de la vidéo vitrine v3 (maîtres produits par boucle_v3.py 16x9|9x16).
# Écrase les fichiers que lit cms/scripts/medias-site.sh du site : ~/nexora-creative-data/site-medias/
#   hero-boucle-{16x9,9x16}.mp4 (H.264, ≤ 7 Mo), .webm (VP9), -poster.jpg et -poster.avif (image 168 : stationnement verrouillé).
set -euo pipefail
FF="${FFMPEG:-$HOME/nexora-creative-data/engine/ffmpeg/ffmpeg-7.0.2-arm64-static/ffmpeg}"
W="$HOME/nexora-creative-data/site-medias/hero-v3"
D="$HOME/nexora-creative-data/site-medias"
POSTER="${POSTER:-168}"
for f in 16x9 9x16; do
  m="$W/maitre-$f.mp4"; o="$D/hero-boucle-$f"
  "$FF" -v error -y -i "$m" -an -c:v libx264 -preset slow -crf 22 -maxrate 3.0M -bufsize 6M -profile:v high \
    -pix_fmt yuv420p -g 60 -movflags +faststart -map_metadata -1 "$o.mp4"
  "$FF" -v error -y -i "$m" -an -c:v libvpx-vp9 -b:v 2.4M -maxrate 3.0M -crf 31 -row-mt 1 -deadline good \
    -cpu-used 2 -g 60 -pix_fmt yuv420p -map_metadata -1 "$o.webm"
  "$FF" -v error -y -i "$m" -vf "select=eq(n\,$POSTER)" -frames:v 1 -q:v 3 "$o-poster.jpg"
  "$FF" -v error -y -i "$o-poster.jpg" -c:v libaom-av1 -still-picture 1 -crf 28 -pix_fmt yuv420p "$o-poster.avif"
  ls -la "$o".* "$o"-poster.*
done
