#!/usr/bin/env bash
# Planche d'un rush : 8 images réparties sur la durée (contrôle qualité plan par plan).  planche_rush.sh <video> <sortie.jpg> [colonnes]
FF=/home/pc6/nexora-creative-data/engine/ffmpeg/ffmpeg-7.0.2-arm64-static
d=$($FF/ffprobe -v error -show_entries format=duration -of csv=p=0 "$1")
n=$(python3 -c "print(8/max(0.5,$d))")
$FF/ffmpeg -v error -y -i "$1" -vf "fps=$n,scale=480:-2,tile=${3:-4}x2:padding=4" -frames:v 1 "$2"
