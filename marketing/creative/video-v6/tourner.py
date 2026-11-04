"""Film V6 : tournage des plans par le VRAI parcours du client dans Creative (serveur de la branche, port 37171).
Chaque plan part de la version boostée capturée (captures/boost/<plan>/boost.json) : image clé par le mode Image de
Creative (réécrivain d'image + Qwen-Image-2.1), puis vidéo par « Créer » en Qualité cinéma (réécrivain H3 + h3-max sur la
RTX 5090) avec l'image choisie comme photo de départ. Toutes les réponses (prompts réécrits, prises) sont journalisées.

  python3 tourner.py cles <plan> [16:9|9:16] [nombre=2]      images clés (GB10)
  python3 tourner.py video <plan> <take_image> [16:9|9:16] [prises=1] [camera…]   vidéo(s) h3-max à partir d'une image clé
  python3 tourner.py t2v <plan> [16:9|9:16] [prises=1]       vidéo h3-max sans image (texte seul)
  python3 tourner.py file                                     travaux en file sur la 5090 (règle : 6 au plus d'avance)
Journal : ~/nexora-creative-data/promo/v6-creative/tournage.jsonl ; rushes copiés par prises.py.
"""
import base64
import json
import sys
import time
import urllib.request
from pathlib import Path

API = "http://127.0.0.1:37171"
D = Path.home() / "nexora-creative-data/promo/v6-creative"
JOURNAL = D / "tournage.jsonl"
MAX_FILE = 6


def post(u, corps, timeout=300):
    r = urllib.request.Request(API + u, data=json.dumps(corps, ensure_ascii=False).encode(), headers={"content-type": "application/json"})
    with urllib.request.urlopen(r, timeout=timeout) as x:
        return json.loads(x.read())


MIENS = ("video/OpenField", "OpenField/", "nexora-promo-v3/v6voix", "nexora-promo-v3/d1-", "nexora-promo-v3/d2-", "nexora-promo-v3/v6-")


def file_5090(tous=False):
    """Travaux en file sur la 5090 ; par défaut seulement les miens (préfixe de sortie), la file étant partagée."""
    with urllib.request.urlopen("http://127.0.0.1:37288/queue", timeout=30) as x:
        q = json.loads(x.read())
    items = q["queue_running"] + q["queue_pending"]
    if tous:
        return len(items)
    pref = lambda it: [str(n.get("inputs", {}).get("filename_prefix", "")) for n in it[2].values()]
    return sum(1 for it in items if any(p.startswith(MIENS) for p in pref(it)))


def attendre_place(n=1):
    while file_5090() + n > MAX_FILE:
        time.sleep(20)


def boost(plan):
    return json.loads((D / "captures/boost" / plan / "boost.json").read_text())["boost"]


def noter(o):
    o = {"t": time.strftime("%Y-%m-%d %H:%M:%S"), **o}
    with JOURNAL.open("a") as fh:
        fh.write(json.dumps(o, ensure_ascii=False) + "\n")
    print(json.dumps(o, ensure_ascii=False)[:600], flush=True)


def cles(plan, fmt="16:9", nombre=2):
    r = post("/api/nexora/image", {"intention": boost(plan), "format": fmt, "nombre": int(nombre), "qualite": "max"})
    noter({"etape": "cles", "plan": plan, "format": fmt, "takes": r.get("takeIds"), "prompt": r.get("prompt"), "source": r.get("source")})


def jeton_image(take):
    f = D / "rushes" / f"{take}.png"
    d = "data:image/png;base64," + base64.b64encode(f.read_bytes()).decode()
    return post("/api/upload", {"name": f"v6-{take}", "dataUrl": d})["name"]


def video(plan, take_image=None, fmt="16:9", prises=1, camera=None):
    corps = {"intention": boost(plan), "format": fmt, "duree": 5, "son": True, "qualite": "max"}
    if take_image:
        corps["image"] = jeton_image(take_image)
    if camera:
        corps["camera"] = camera
    for _ in range(int(prises)):
        attendre_place()
        r = post("/api/nexora/creer", corps)
        noter({"etape": "video", "plan": plan, "format": fmt, "image": take_image, "camera": camera, "takes": r.get("takeIds"),
               "prompt": r.get("prompt"), "source": r.get("source"), "moteur": r.get("moteur"), "erreur": r.get("error")})
        time.sleep(3)


if __name__ == "__main__":
    a = sys.argv[1:]
    if a[0] == "cles":
        cles(a[1], *(a[2:4]))
    elif a[0] == "video":
        video(a[1], int(a[2]), a[3] if len(a) > 3 else "16:9", a[4] if len(a) > 4 else 1, " ".join(a[5:]) or None)
    elif a[0] == "t2v":
        video(a[1], None, a[2] if len(a) > 2 else "16:9", a[3] if len(a) > 3 else 1)
    elif a[0] == "file":
        print(file_5090())
