#!/usr/bin/env bash
# Rend toutes les versions du film de marque et des spots courts, l'une après l'autre (ffmpeg occupe tous les cœurs).
cd "$(dirname "$0")/.."
for lang in fr en; do
  for fmt in 16x9 9x16 1x1; do
    f="final/film-marque-$fmt-$lang.mp4"
    [ -s "$f" ] && [ "$fmt$lang" != "16x9fr" ] || python3 sources/montage-hero.py $lang $fmt || echo "ECHEC film $lang $fmt"
  done
done
for spot in 30 15 6; do
  [ -s sources/musique/$( [ $spot = 30 ] && echo D-30s || ([ $spot = 15 ] && echo E-15s || echo F-6s) ).flac ] || { echo "musique du spot $spot absente"; continue; }
  for lang in fr en; do for fmt in 16x9 9x16 1x1; do
    python3 sources/montage-court.py $spot $lang $fmt || echo "ECHEC spot $spot $lang $fmt"
  done; done
done
echo "terminé"
