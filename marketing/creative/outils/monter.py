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
# Version verticale 9:16 (Reels, TikTok, Shorts) : les plans d'action sont recadrés au centre (décalage « x » de 0 à 1
# réglable par plan), les cartons sont centrés dans l'image sur le noir encre.
NORME_V = "scale=-2:1920:flags=lanczos,crop=1080:1920:(iw-1080)*{x}:0,unsharp=5:5:0.6,fps=24,format=yuv420p,setsar=1"
CARTON_V = "scale=1260:-2:flags=lanczos,crop=1080:ih:(iw-1080)/2:0,pad=1080:1920:0:(1920-ih)/2:color=0x0a0a0e,fps=24,format=yuv420p,setsar=1"
VERTICAL = False


def lancer(args: list[str]):
    r = subprocess.run([FFMPEG, "-v", "error", "-y", *args], capture_output=True, text=True)
    if r.returncode:
        raise SystemExit(f"ffmpeg : {r.stderr[-1500:]}")


def segment(s: dict, images: int, sortie: Path):
    duree = images / 24.0  # coupe sur la grille d'images : un -t flottant arrondirait chaque segment à l'image supérieure
    if "carton" in s:
        lancer(["-i", s["carton"], "-t", f"{duree:.4f}", "-frames:v", str(images), "-vf", CARTON_V if VERTICAL else "fps=24,format=yuv420p,setsar=1", "-af", "aresample=48000",
                "-ac", "2", "-c:v", "libx264", "-preset", "slow", "-crf", "15", "-c:a", "pcm_s16le", str(sortie.with_suffix(".mov"))])
        return
    v = float(s.get("vitesse", 1.0))
    debut = float(s.get("debut", 0.0))
    pre = f"setpts={1 / v:.4f}*PTS," if v != 1.0 else ""
    af = "aresample=48000" + (f",atempo={max(0.5, v):.4f}" if v != 1.0 else "")
    post = ""
    if s.get("flash"):
        post += ",fade=in:st=0:d=0.12:color=white"
    # Un plan qui dépasse la fin de son rush (ralenti, coupe tardive) se prolonge par son image figée et du silence :
    # la durée du segment reste exacte, sinon toute la suite se décale par rapport à la musique.
    post += ",tpad=stop_mode=clone:stop_duration=4"
    af += ",apad=pad_dur=4"
    entree = ["-ss", f"{debut:.4f}", "-i", s["plan"], "-t", f"{duree:.4f}", "-frames:v", str(images)]
    if VERTICAL and s.get("ajuste"):
        # Plan large : image entière à la largeur de l'écran vertical, sur son propre flou agrandi.
        fc = (f"[0:v]{pre}split[a][b];[a]scale=-2:1920,crop=1080:1920,boxblur=40:6[bg];[b]scale=1080:-2:flags=lanczos[fg];"
              f"[bg][fg]overlay=(W-w)/2:(H-h)/2,unsharp=5:5:0.6,fps=24,format=yuv420p,setsar=1{post}[v]")
        lancer([*entree, "-filter_complex", fc, "-map", "[v]", "-map", "0:a:0", "-af", af, "-ac", "2",
                "-c:v", "libx264", "-preset", "slow", "-crf", "15", "-c:a", "pcm_s16le", str(sortie.with_suffix(".mov"))])
        return
    base = NORME_V.format(x=float(s.get("x", 0.5))) if VERTICAL else NORME
    lancer([*entree, "-vf", pre + base + post, "-af", af, "-ac", "2",
            "-c:v", "libx264", "-preset", "slow", "-crf", "15", "-c:a", "pcm_s16le", str(sortie.with_suffix(".mov"))])


def monter(liste: dict):
    temps_beat = 60.0 / float(liste.get("bpm", 120))
    with tempfile.TemporaryDirectory() as d:
        dossier = Path(d)
        morceaux = []
        precedent = 0.0
        images_faites = 0
        for i, s in enumerate(liste["segments"]):
            # Une coupe se donne par son instant absolu sur la musique (« fin », en secondes), ou en temps (« temps »).
            if "fin" in s:
                precedent = float(s["fin"])
            else:
                precedent += float(s["temps"]) * temps_beat
            # Nombre d'images = écart entre les instants de coupe arrondis à la grille : aucune dérive cumulée.
            cible = round(precedent * 24)
            images = max(1, cible - images_faites)
            images_faites += images
            f = dossier / f"s{i:03d}"
            segment(s, images, f)
            morceaux.append(f.with_suffix(".mov"))
        concat = dossier / "liste.txt"
        concat.write_text("".join(f"file '{m}'\n" for m in morceaux))
        image = dossier / "image.mov"
        lancer(["-f", "concat", "-safe", "0", "-i", str(concat), "-c", "copy", str(image)])
        sfx, mus = liste.get("sfx_db", -9), liste.get("musique_db", 0)
        # Silences voulus (dernier souffle avant un impact) : forcés à zéro après la normalisation.
        coupes = "".join(f",volume=enable='between(t,{a},{b})':volume=0" for a, b in liste.get("silences", []))
        filtre = (
            f"[0:a]volume={sfx}dB[s];[1:a]aresample=48000,volume={mus}dB[m];"
            f"[m][s]amix=inputs=2:duration=first:normalize=0,loudnorm=I=-14:TP=-1:LRA=11{coupes}[a]"
        )
        lancer(["-i", str(image), "-ss", str(liste.get("musique_debut", 0)), "-i", liste["musique"],
                "-filter_complex", filtre.replace("[m][s]amix=inputs=2:duration=first", "[m][s]amix=inputs=2:duration=longest"),
                "-map", "0:v", "-map", "[a]", "-shortest", "-c:v", "libx264", "-preset", "slow", "-crf", "17",
                "-profile:v", "high", "-pix_fmt", "yuv420p", "-movflags", "+faststart", "-c:a", "aac", "-b:a", "256k",
                liste["sortie"]])


if __name__ == "__main__":
    VERTICAL = "--vertical" in sys.argv
    monter(json.loads(Path(sys.argv[1]).read_text()))
