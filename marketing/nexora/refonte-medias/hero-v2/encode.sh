#!/usr/bin/env bash
# Encodage web de la vidéo vitrine (maîtres produits par boucle_signal.py rendu {16x9|9x16}).
# Sorties dans ~/nexora-creative-data/site-medias/ (noms que lit cms/scripts/medias-site.sh du site) :
#   hero-boucle-{16x9,9x16}.mp4 (H.264, < 6 Mo en 16:9), .webm (VP9), -poster.jpg et -poster.avif.
set -euo pipefail
FF="${FFMPEG:-$HOME/nexora-creative-data/engine/ffmpeg/ffmpeg-7.0.2-arm64-static/ffmpeg}"
W="$HOME/nexora-creative-data/site-medias/hero-v2"
D="$HOME/nexora-creative-data/site-medias"
for f in 16x9 9x16; do
  m="$W/maitre-$f.mp4"; o="$D/hero-boucle-$f"
  "$FF" -v error -y -i "$m" -an -c:v libx264 -preset slow -crf 21 -maxrate 3.4M -bufsize 6.8M -profile:v high \
    -pix_fmt yuv420p -g 60 -movflags +faststart -map_metadata -1 "$o.mp4"
  "$FF" -v error -y -i "$m" -an -c:v libvpx-vp9 -b:v 2.6M -maxrate 3.4M -crf 30 -row-mt 1 -deadline good \
    -cpu-used 2 -g 60 -pix_fmt yuv420p -map_metadata -1 "$o.webm"
  cp "$W/hero-boucle-$f-poster.jpg" "$o-poster.jpg"
  "$FF" -v error -y -i "$o-poster.jpg" -c:v libaom-av1 -still-picture 1 -crf 28 -pix_fmt yuv420p "$o-poster.avif"
  ls -la "$o".* "$o"-poster.*
done
