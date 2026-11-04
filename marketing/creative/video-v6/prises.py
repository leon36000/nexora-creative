"""Suit les prises du Creative de la branche (port 37171) et copie les vidéos finies dans les rushes du film V6.
  python3 prises.py attendre <id> [<id> ...]   attend la fin, copie <rushes>/<id>.mp4 et écrit <id>.json (prompt, réglages)
  python3 prises.py etat                       les 10 dernières prises
  python3 prises.py synchro <id>               copie les prises finies manquantes depuis <id>
"""
import json, shutil, sys, time, urllib.request
from pathlib import Path
API = "http://127.0.0.1:37171"
RUSHES = Path.home() / "nexora-creative-data/promo/v6-creative/rushes"

def get(u):
    with urllib.request.urlopen(API + u, timeout=60) as r:
        return json.loads(r.read())

def prise(i):
    return next((t for t in get("/api/takes") if t["id"] == i), None)

def copier(t):
    RUSHES.mkdir(parents=True, exist_ok=True)
    src = Path(t.get("output_path") or t.get("file") or "")
    if not src.exists():
        for k, v in t.items():
            if isinstance(v, str) and v.endswith(".mp4") and Path(v).exists():
                src = Path(v)
    dst = RUSHES / f"{t['id']}{src.suffix or '.mp4'}"
    if src.exists():
        shutil.copy2(src, dst)
    (RUSHES / f"{t['id']}.json").write_text(json.dumps(t, ensure_ascii=False, indent=1))
    return dst if src.exists() else None

if __name__ == "__main__":
    if sys.argv[1] == "synchro":  # copie toutes les prises finies (>= id donné) qui manquent dans les rushes
        for t in get("/api/takes"):
            if t["id"] >= int(sys.argv[2]) and t["status"] == "done" and not list(RUSHES.glob(f"{t['id']}.*[!n]")):
                print(t["id"], copier(t))
    elif sys.argv[1] == "etat":
        for t in get("/api/takes")[:10]:
            print(t["id"], t["status"], t.get("shot_name", "")[:60])
    else:
        ids = [int(x) for x in sys.argv[2:]]
        while ids:
            for i in list(ids):
                t = prise(i)
                if t and t["status"] in ("done", "error", "failed", "cancelled"):
                    print(i, t["status"], copier(t) if t["status"] == "done" else t.get("error", ""), flush=True)
                    ids.remove(i)
            time.sleep(10)
