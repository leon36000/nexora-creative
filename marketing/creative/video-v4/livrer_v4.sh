#!/usr/bin/env bash
# Livraison de la promo V4 : finaux (promo/montage), encodages web H.264 1080p ≤ 25 Mo, affiche et manifest-creative.json
# (site-medias, mêmes noms que la V3 : les emplacements Creative du site les rechargent sans changement de code).
set -euo pipefail
F=~/nexora-creative-data/engine/ffmpeg/ffmpeg-7.0.2-arm64-static/ffmpeg
B=~/nexora-creative-data/promo/v4/brouillons
M=~/nexora-creative-data/promo/montage
S=~/nexora-creative-data/site-medias
mkdir -p "$M"
for fmt in 16x9 9x16; do for l in fr en; do
  cp "$B/v4-$fmt-$l-long.mp4" "$M/Nexora-Creative-promo-V4-$fmt-$l.mp4"
  for v in 30 15; do cp "$B/v4-$fmt-$l-$v.mp4" "$M/Nexora-Creative-promo-V4-$fmt-$l-$v.mp4"; done
  # web : débit plafonné (≈ 2,9 Mb/s vidéo) pour rester sous 25 Mo à 60 s
  $F -v error -y -i "$M/Nexora-Creative-promo-V4-$fmt-$l.mp4" -c:v libx264 -preset slow -crf 21 -maxrate 2900k -bufsize 5800k \
     -profile:v high -pix_fmt yuv420p -c:a aac -b:a 160k -movflags +faststart "$S/film-creative-$fmt-$l.mp4"
done; done
# affiche sans texte : le flacon révélé (plan 4 du film tourné par le Producteur)
$F -v error -y -ss 34.0 -i "$M/Nexora-Creative-promo-V4-16x9-fr.mp4" -frames:v 1 -q:v 2 "$S/film-creative-poster.jpg"
python3 - <<'EOF'
import json, os, subprocess
from pathlib import Path
S = Path.home() / "nexora-creative-data/site-medias"
M = Path.home() / "nexora-creative-data/promo/montage"
FP = str(Path.home() / "nexora-creative-data/engine/ffmpeg/ffmpeg-7.0.2-arm64-static/ffprobe")
def duree(f):
    return round(float(subprocess.run([FP, "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(f)],
                                      capture_output=True, text=True).stdout), 2)
fichiers = []
for fmt in ("16x9", "9x16"):
    for l in ("fr", "en"):
        f = S / f"film-creative-{fmt}-{l}.mp4"
        fichiers.append({"file": f.name, "role": "film-principal" if fmt == "16x9" else "film-vertical", "format": fmt.replace("x", ":"),
                         "language": l, "dimensions": "1920x1080" if fmt == "16x9" else "1080x1920", "duration": duree(f),
                         "size_bytes": f.stat().st_size, "source_file": str(M / f"Nexora-Creative-promo-V4-{fmt}-{l}.mp4")})
fichiers.append({"file": "film-creative-poster.jpg", "role": "affiche", "format": "16:9", "dimensions": "1920x1080",
                 "size_bytes": (S / "film-creative-poster.jpg").stat().st_size})
(S / "manifest-creative.json").write_text(json.dumps({
    "projet": "Nexora Creative", "livraison": "promo V4 « Une phrase. Un film. »", "date": "2026-11-02",
    "note": "Une vraie session du Producteur IA (captures d'écran réelles) tourne un spot parfum à partir d'une phrase, puis six genres. "
            "Médias web livrés depuis promo/montage ; coupes 30 s et 15 s dans promo/montage (suffixes -30, -15). Affiche sans texte.",
    "fichiers": fichiers}, ensure_ascii=False, indent=2) + "\n")
print("\n".join(f"{x['file']} {x.get('size_bytes', 0) / 1e6:.1f} Mo" for x in fichiers))
EOF
