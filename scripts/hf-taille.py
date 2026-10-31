"""Affiche la taille d'un dépôt Hugging Face (lu sur stdin : JSON de /api/models/<id>?blobs=true)."""
import json
import sys

d = json.load(sys.stdin)
s = d.get("siblings", [])
tot = sum((x.get("size") or 0) for x in s)
print(f"{d.get('id')}  gated={d.get('gated')}  total={tot / 1e9:.1f} Go  fichiers={len(s)}")
for x in sorted(s, key=lambda x: -(x.get("size") or 0))[:6]:
    print("   ", round((x.get("size") or 0) / 1e9, 2), x["rfilename"])
