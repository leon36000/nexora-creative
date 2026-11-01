#!/usr/bin/env bash
# Agrandit (Real-ESRGAN x4, outils/agrandir.py) chaque image générée de generees/ vers generees/<nom>-x4.jpg (JPEG q90, pour l'impression).
# Usage : agrandir-lot.sh nom1 nom2 … (sans extension). Attend que l'image brute existe (génération en cours), 20 min au plus.
cd "$(dirname "$0")/generees" || exit 1
OUTILS="$(cd ../../.. && pwd)/outils"
for n in "$@"; do
  for i in $(seq 1 240); do [ -f "$n.png" ] && break; sleep 5; done
  [ -f "$n.png" ] || { echo "absent: $n"; continue; }
  [ -f "$n-x4.jpg" ] && continue
  case "$n" in *16x9*) arg="--largeur 7168";; *) arg="--largeur 4096";; esac
  python3 "$OUTILS/agrandir.py" "$n.png" "$n-x4.tmp.png" $arg && python3 -c "
from PIL import Image
im=Image.open('$n-x4.tmp.png').convert('RGB'); im.save('$n-x4.jpg',quality=90,subsampling=0,optimize=True); print('$n',im.size)" && rm -f "$n-x4.tmp.png"
done
echo FINI
