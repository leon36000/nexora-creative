"""Garde TOUTES les vidéos du concours sur pc1 : ~/Bureau/Nexora-Livrables/TOUS-LES-FILMS/opsys-ultime/<equipe>/{plans,montage}/
(+ voix et musiques à côté), et ajoute chaque vidéo à INVENTAIRE.csv (une ligne par fichier, sans doublon de sha256).
Ne supprime jamais rien, ni ici ni sur pc1.   python3 archiver.py [equipe …]
"""
import csv
import hashlib
import io
import json
import subprocess
import sys
import time
from pathlib import Path

import tourner as T

DEST = "/home/pc1/Bureau/Nexora-Livrables/TOUS-LES-FILMS/opsys-ultime"
INV = "/home/pc1/Bureau/Nexora-Livrables/TOUS-LES-FILMS/INVENTAIRE.csv"


def sonde(f):
    r = subprocess.run([T.FP, "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height:format=duration", "-of", "json", str(f)],
                       capture_output=True, text=True)
    j = json.loads(r.stdout or "{}")
    s = (j.get("streams") or [{}])[0]
    return float(j.get("format", {}).get("duration", 0)), f"{s.get('width', '')}x{s.get('height', '')}"


def main(equipes):
    existants = subprocess.run(["ssh", "pc1", f"cut -d, -f6 {INV}"], capture_output=True, text=True).stdout.split()
    connus = set(existants)
    lignes = []
    for eq in equipes:
        base = T.TRAVAIL / eq
        for sous in ("plans", "montage", "voix", "musique", "revue", "fiches", "cles"):
            d = base / sous
            if d.exists():
                subprocess.run(["ssh", "pc1", f"mkdir -p {DEST}/{eq}/{sous}"], check=True)
                subprocess.run(["rsync", "-a", "--exclude", "tranches-*", f"{d}/", f"pc1:{DEST}/{eq}/{sous}/"], check=True)
        for sous, role in (("plans", "rush"), ("montage", "master")):
            for f in sorted((base / sous).glob("*.mp4")) if (base / sous).exists() else []:
                h = hashlib.sha256(f.read_bytes()).hexdigest()
                if h in connus:
                    continue
                connus.add(h)
                du, res = sonde(f)
                quoi = f"film ultime OPSYS-AI, équipe {eq} : " + ("plan H3 " + f.stem if role == "rush" else "montage " + f.stem)
                lignes.append([f"{DEST}/{eq}/{sous}/{f.name}", f.stat().st_size, round(du, 2), res,
                               time.strftime("%Y-%m-%d %H:%M", time.localtime(f.stat().st_mtime)), h, quoi, f.stem,
                               "MiniMax H3 (h3-max/h3-fast)" if role == "rush" else "chaine/monter.py (EditPlan v1)",
                               role if "brouillon" not in f.stem else "travail", "", "non",
                               f"pc6:{f}", 1, ""])
    if lignes:
        buf = io.StringIO()
        csv.writer(buf).writerows(lignes)
        subprocess.run(["ssh", "pc1", f"cat >> {INV}"], input=buf.getvalue(), text=True, check=True)
    print(f"{len(lignes)} vidéo(s) ajoutée(s) à l'inventaire ; copies dans pc1:{DEST}")


if __name__ == "__main__":
    main(sys.argv[1:] or ["opus", "deepseek", "muse", "gemini", "commun", "casting"])
