#!/usr/bin/env bash
# Versions légères (720p, grain atténué) des vidéos phares pour le partage et la galerie.
F=~/nexora-creative-data/engine/ffmpeg/ffmpeg-7.0.2-arm64-static/ffmpeg
cd "$(dirname "$0")/.."
enc() { # entrée sortie largeur_max crf
  $F -v error -y -i "$1" -vf "hqdn3d=3:2:4:4,scale='min($3,iw)':-2:flags=lanczos" -c:v libx264 -preset slow -crf $4 -pix_fmt yuv420p -movflags +faststart -c:a aac -b:a 128k "$2"
}
V=video/final; P=partage/video
enc $V/film-marque-16x9-fr.mp4 $P/film-marque-16x9-fr.mp4 1280 28
enc $V/film-marque-16x9-en.mp4 $P/film-marque-16x9-en.mp4 1280 28
enc $V/film-marque-9x16-fr.mp4 $P/film-marque-9x16-fr.mp4 720 28
enc $V/spot-30s-16x9-fr.mp4 $P/spot-30s-16x9-fr.mp4 1280 28
enc $V/spot-15s-9x16-fr.mp4 $P/spot-15s-9x16-fr.mp4 720 28
enc $V/spot-6s-1x1-fr.mp4 $P/spot-6s-1x1-fr.mp4 720 26
for t in workstudio code rag bot creative webpilot privacy-router vps; do
  f=$(ls video/teasers/$t/final/teaser-$t-fr-CA-9x16.mp4 2>/dev/null | head -1)
  [ -n "$f" ] && enc "$f" $P/teaser-$t-fr-9x16.mp4 540 28
done
s=$(ls video/teasers/stings/final/sting-nexora-16x9-fr-CA.mp4 2>/dev/null); [ -n "$s" ] && enc "$s" $P/sting-nexora-16x9.mp4 1280 26
echo fini
