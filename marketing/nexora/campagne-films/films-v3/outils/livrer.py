"""Livraison des films V5 sur pc1 (rien d'écrasé des livraisons précédentes) et allègement de pc6.

  python3 livrer.py
pc1 : /home/pc1/Bureau/Nexora-Livrables/films-v5/   masters (CRF 15, AAC 320k) et versions web
      /home/pc1/Bureau/Nexora-Livrables/infographies/v5/   1080×1350 et 1080×1080
      /home/pc1/Bureau/Nexora-Livrables/rapports/v5/   scénarios, revues chiffrées, planches, RAPPORT.md
      /home/pc1/Bureau/Nexora-Livrables/audio/v5/<film>/   stems (voix par phrase, musique, bruitages), mix, audio.json
      /run/media/pc1/Infrastructure/NexoraStudioWork/films-v3/<film>/   travail complet (captures, plaques, rendus)
pc6 : seules les versions web restent (~/nexora-creative-data/promo/montage/V5-*.mp4).
"""
import subprocess
from pathlib import Path

import commun as C

L = "/home/pc1/Bureau/Nexora-Livrables"
W = "/run/media/pc1/Infrastructure/NexoraStudioWork/films-v3"
FILMS = ("creative", "opsys", "workstudio")


def ssh(cmd):
    subprocess.run(["ssh", "pc1", cmd], check=True)


def rsync(src, dst):
    subprocess.run(["rsync", "-a", "--partial", *map(str, src), f"pc1:{dst}"], check=True)


def livrer():
    ssh(f"mkdir -p {L}/films-v5 {L}/infographies/v5 {L}/rapports/v5 {L}/audio/v5 {W}")
    for f in FILMS:
        dos = C.TRAVAIL / f
        r = dos / "rendu"
        rsync(sorted(r.glob("V5-*-master.mp4")) + sorted(Path.home().glob(f"nexora-creative-data/promo/montage/V5-{f}-*-fr.mp4")), f"{L}/films-v5/")
        rsync(sorted(r.glob("infographie-*.png")), f"{L}/infographies/v5/")
        rsync(sorted(r.glob("revue-*.json")) + sorted(r.glob("planche-*.jpg")) + [C.RACINE / f / "SCENARIO.md", C.RACINE / f / "film.json"],
              f"{L}/rapports/v5/{f}/")
        ssh(f"mkdir -p {L}/audio/v5/{f}")
        rsync([dos / "audio", dos / "voix", dos / "musique"], f"{L}/audio/v5/{f}/")
        rsync([dos], f"{W}/")
    rsync([C.RACINE / "RAPPORT.md", C.RACINE / "MANIFESTE.md", C.RACINE / "audio-choix.json"], f"{L}/rapports/v5/")
    rsync([C.RACINE / "MANIFESTE.md"], f"{L}/films-v5/")


if __name__ == "__main__":
    livrer()
