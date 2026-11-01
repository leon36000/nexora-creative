"""Génération avec les outils Nexora Creative, pour la campagne de lancement de Nexora AI.

Parle au serveur Creative de pc6 (OPENFIELD_PORT du .env, 37161 par défaut) : images Qwen-Image-2.1 (GB10), plans H3
(RTX 5090, avec son), musique MiniMax-Music3 (GB10). Chaque appel attend la fin du rendu et copie le fichier dans le
dossier demandé (jamais dans la base du serveur).

  python3 generer.py image  "<prompt>" sortie.png [--format 16:9|9:16|1:1] [--rapide]
  python3 generer.py video  "<prompt>" sortie.mp4 [--duree 5|10] [--format 16:9|9:16|1:1] [--max]
  python3 generer.py musique "<envie>" sortie.flac [--duree 60]

Utilisable aussi comme module : from generer import image, video, musique.
Le prompt d'image est réécrit par le LLM de Nexora (réécrivain de plans) : décrire la scène, pas la mise en page.
Règle de marque : jamais de texte, de logo ni de chiffres dans une image générée (le texte et le logo se posent en code).
"""
import argparse, json, shutil, sys, time, urllib.request
from pathlib import Path

PORT = 37161
for l in (Path(__file__).resolve().parents[3] / "app" / ".env").read_text().splitlines():
    if l.startswith("OPENFIELD_PORT="):
        PORT = int(l.split("=", 1)[1])
BASE = f"http://127.0.0.1:{PORT}"


def _appel(chemin, corps=None, delai=120):
    req = urllib.request.Request(BASE + chemin, data=None if corps is None else json.dumps(corps).encode(),
                                 headers={"content-type": "application/json"}, method="GET" if corps is None else "POST")
    try:
        with urllib.request.urlopen(req, timeout=delai) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"{chemin} : HTTP {e.code} {e.read().decode()[:300]}")


def attendre(take_id, delai_max=1800):
    debut = time.time()
    while True:
        p = _appel(f"/api/studio/prise/{take_id}")
        if p["statut"] == "done" and p.get("creation"):
            return p["creation"]
        if p["statut"] in ("failed", "stopped"):
            raise RuntimeError(f"rendu {take_id} échoué : {p.get('erreur')}")
        if time.time() - debut > delai_max:
            raise TimeoutError(f"rendu {take_id} trop long")
        time.sleep(4)


def _copier(creation, sortie):
    sortie = Path(sortie)
    sortie.parent.mkdir(parents=True, exist_ok=True)
    src = Path(creation["fichier"]) if creation.get("fichier") else None
    if src is None or not src.exists():
        with urllib.request.urlopen(BASE + f"/api/media/{creation['id']}?download=1", timeout=300) as r, open(sortie, "wb") as f:
            shutil.copyfileobj(r, f)
    else:
        shutil.copyfile(src, sortie)
    return sortie


def image(prompt, sortie, format="16:9", rapide=False):
    r = _appel("/api/nexora/image", {"intention": prompt, "format": format, "qualite": "rapide" if rapide else "max"})
    tid = r.get("takeId") or r["takeIds"][0]
    return _copier(attendre(tid), sortie)


def video(prompt, sortie, duree=5, format="16:9", son=True, max_=False):
    r = _appel("/api/nexora/creer", {"intention": prompt, "format": format, "duree": duree, "son": son, "qualite": "max" if max_ else "rapide"})
    return _copier(attendre(r["takeId"], 3600), sortie)


def musique(envie, sortie, duree=60):
    r = _appel("/api/studio/musique", {"envie": envie, "dureeS": duree})
    return _copier(attendre(r["takeId"], 1800), sortie)


if __name__ == "__main__":
    a = argparse.ArgumentParser()
    a.add_argument("genre", choices=["image", "video", "musique"])
    a.add_argument("texte")
    a.add_argument("sortie")
    a.add_argument("--format", default="16:9")
    a.add_argument("--duree", type=int, default=None)
    a.add_argument("--rapide", action="store_true")
    a.add_argument("--max", action="store_true")
    o = a.parse_args()
    if o.genre == "image":
        print(image(o.texte, o.sortie, o.format, o.rapide))
    elif o.genre == "video":
        print(video(o.texte, o.sortie, o.duree or 5, o.format, True, o.max))
    else:
        print(musique(o.texte, o.sortie, o.duree or 60))
