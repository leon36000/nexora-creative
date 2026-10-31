"""Montage de la bande-annonce Nexora Creative à partir d'une liste de montage (JSON).

Chaque segment est un carton (MP4 déjà rendu par cartons.py) ou un extrait de plan (fichier, début, durée). Tout est
ramené en 1920×1080, 24 i/s ; les bruitages H3 des plans passent sous la musique MiniMax-Music3, puis le mixage est
normalisé à −14 LUFS (cible des réseaux sociaux). Les coupes tombent sur la grille de la musique : la liste donne des
durées en temps (beats × 60 / BPM).

Usage : python3 monter.py liste.json
Liste : { "sortie", "musique", "bpm", "sfx_db", "musique_db", "segments": [
          {"carton": "x.mp4", "fin": 3.6} | {"plan": "x.mp4", "debut": 1.0, "fin": 8.76, "vitesse": 1.0, "flash": true} ] }
        (« temps » en battements à la place de « fin » si la musique suit son BPM)
"""
import json
import subprocess
import sys
import tempfile
from pathlib import Path

FFMPEG = str(Path.home() / "nexora-creative-data/engine/ffmpeg/ffmpeg-7.0.2-arm64-static/ffmpeg")
NORME = "scale=1920:-2:flags=lanczos,crop=1920:1080,unsharp=5:5:0.6,fps=24,format=yuv420p,setsar=1"


def lancer(args: list[str]):
    r = subprocess.run([FFMPEG, "-v", "error", "-y", *args], capture_output=True, text=True)
    if r.returncode:
        raise SystemExit(f"ffmpeg : {r.stderr[-1500:]}")


def segment(s: dict, duree: float, sortie: Path):
    if "carton" in s:
        lancer(["-i", s["carton"], "-t", f"{duree:.4f}", "-vf", "fps=24,format=yuv420p,setsar=1", "-af", "aresample=48000",
                "-ac", "2", "-c:v", "libx264", "-preset", "slow", "-crf", "15", "-c:a", "pcm_s16le", str(sortie.with_suffix(".mov"))])
        return
    v = float(s.get("vitesse", 1.0))
    debut = float(s.get("debut", 0.0))
    vf = NORME
    af = "aresample=48000"
    if v != 1.0:
        # Ralenti : on étire l'image (setpts) et le son (atempo, borné à 0,5 par passage).
        vf = f"setpts={1 / v:.4f}*PTS," + vf
        af += f",atempo={max(0.5, v):.4f}"
    if s.get("flash"):
        vf += ",fade=in:st=0:d=0.12:color=white"
    lancer(["-ss", f"{debut:.4f}", "-i", s["plan"], "-t", f"{duree:.4f}", "-vf", vf, "-af", af, "-ac", "2",
            "-c:v", "libx264", "-preset", "slow", "-crf", "15", "-c:a", "pcm_s16le", str(sortie.with_suffix(".mov"))])


def monter(liste: dict):
    temps_beat = 60.0 / float(liste.get("bpm", 120))
    with tempfile.TemporaryDirectory() as d:
        dossier = Path(d)
        morceaux = []
        precedent = 0.0
        for i, s in enumerate(liste["segments"]):
            # Une coupe se donne par son instant absolu sur la musique (« fin », en secondes), ou en temps (« temps »).
            if "fin" in s:
                duree = float(s["fin"]) - precedent
                precedent = float(s["fin"])
            else:
                duree = float(s["temps"]) * temps_beat
                precedent += duree
            f = dossier / f"s{i:03d}"
            segment(s, duree, f)
            morceaux.append(f.with_suffix(".mov"))
        concat = dossier / "liste.txt"
        concat.write_text("".join(f"file '{m}'\n" for m in morceaux))
        image = dossier / "image.mov"
        lancer(["-f", "concat", "-safe", "0", "-i", str(concat), "-c", "copy", str(image)])
        sfx, mus = liste.get("sfx_db", -9), liste.get("musique_db", 0)
        filtre = (
            f"[0:a]volume={sfx}dB[s];[1:a]aresample=48000,volume={mus}dB[m];"
            "[m][s]amix=inputs=2:duration=first:normalize=0,loudnorm=I=-14:TP=-1:LRA=11[a]"
        )
        lancer(["-i", str(image), "-ss", str(liste.get("musique_debut", 0)), "-i", liste["musique"],
                "-filter_complex", filtre.replace("[m][s]amix=inputs=2:duration=first", "[m][s]amix=inputs=2:duration=longest"),
                "-map", "0:v", "-map", "[a]", "-shortest", "-c:v", "libx264", "-preset", "slow", "-crf", "17",
                "-profile:v", "high", "-pix_fmt", "yuv420p", "-movflags", "+faststart", "-c:a", "aac", "-b:a", "256k",
                liste["sortie"]])


if __name__ == "__main__":
    monter(json.loads(Path(sys.argv[1]).read_text()))
