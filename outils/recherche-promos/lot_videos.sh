#!/usr/bin/env bash
# Usage : lot_videos.sh <liste.txt> [parallélisme=4] [effort=medium]
# liste.txt : une ligne "id[ tab marque]" ; télécharge en ≤ 480p (150 premières secondes au plus), analyse, supprime la vidéo.
S=${PROMOS_TRAVAIL:?dossier de travail (videos/, notes/, outils/venv avec yt-dlp)}
YT=${YT_DLP:-$S/outils/venv/bin/yt-dlp}
ICI=$(cd "$(dirname "$0")" && pwd)
FFD=/home/pc6/nexora-creative-data/engine/ffmpeg/ffmpeg-7.0.2-arm64-static/
LISTE=$1; PAR=${2:-4}; EFFORT=${3:-medium}
traiter() {
  id=$1; d=$S/videos/$id; mkdir -p "$d"
  [ -s "$S/notes/$id.json" ] && { echo "$id deja"; return; }
  timeout 300 "$YT" -q --no-playlist --no-warnings -f "bv*[height<=480]+ba/b[height<=480]/worst" --merge-output-format mp4 \
    --ffmpeg-location "$FFD" -o "$d/v.%(ext)s" --write-info-json \
    "https://www.youtube.com/watch?v=$id" >/dev/null 2>"$d/err.log"
  if [ ! -s "$d/v.mp4" ]; then echo "$id echec_telechargement $(tail -c 200 "$d/err.log")"; rm -rf "$d"; return; fi
  dur=$("$FFD/ffprobe" -v error -show_entries format=duration -of csv=p=0 "$d/v.mp4" | cut -d. -f1)
  if [ "${dur:-0}" -gt 150 ]; then "$FFD/ffmpeg" -v error -i "$d/v.mp4" -t 150 -c copy "$d/c.mp4" && mv "$d/c.mp4" "$d/v.mp4"; fi
  python3 -I "$ICI/analyser.py" "$d/v.mp4" "$d/v.info.json" "$S/notes/$id.json" google/gemini-4-argon "$EFFORT" 2>&1 | tail -1
  rm -rf "$d"   # œuvre de tiers : on ne garde que les notes
}
export -f traiter; export S YT FFD EFFORT ICI
cut -f1 "$LISTE" | grep -v '^#' | grep -v '^$' | xargs -P "$PAR" -I{} bash -c 'traiter {}'
