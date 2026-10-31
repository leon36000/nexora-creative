"""Sound design de la bande-annonce : sons de coupe synthétisés avec ffmpeg (aucun échantillon externe, aucune licence).

  boom    : impact grave (sinus qui tombe de 110 à 38 Hz, queue de bruit rose filtrée), pour les chutes et les coups
  whoosh  : passage de bruit rose enveloppé, pour les changements de plan et les balayages de caméra
  riser   : montée (sinus + bruit) qui précède une chute
  tick    : petit clic sec (typographie, cartons)
Usage : python3 sfx.py type duree_s sortie.wav
"""
import subprocess
import sys
from pathlib import Path

FFMPEG = str(Path.home() / "nexora-creative-data/engine/ffmpeg/ffmpeg-7.0.2-arm64-static/ffmpeg")
SR = 48000


def lancer(args: list[str]):
    r = subprocess.run([FFMPEG, "-v", "error", "-y", *args], capture_output=True, text=True)
    if r.returncode:
        raise SystemExit(f"ffmpeg : {r.stderr[-800:]}")


def generer(kind: str, d: float, sortie: str):
    if kind == "boom":
        # corps : sinus à glissando descendant ; queue : bruit rose passe-bas ; le tout en stéréo, compressé et saturé doucement
        corps = f"aevalsrc='0.9*sin(2*PI*t*(38+72*exp(-9*t)))*exp(-2.4*t)':d={d}:s={SR}"
        queue = f"anoisesrc=c=pink:d={d}:r={SR}:a=0.8,lowpass=f=420,afade=t=in:d=0.004,afade=t=out:st=0.05:d={max(0.1, d - 0.05)}"
        lancer(["-f", "lavfi", "-i", corps, "-f", "lavfi", "-i", queue, "-filter_complex",
                f"[0][1]amix=inputs=2:normalize=0,acompressor=threshold=-18dB:ratio=4:attack=2:release=120,alimiter=limit=0.95,aformat=channel_layouts=stereo,afade=t=out:st={d * 0.7}:d={d * 0.3}", "-t", str(d), sortie])
    elif kind == "whoosh":
        lancer(["-f", "lavfi", "-i", f"anoisesrc=c=pink:d={d}:r={SR}:a=0.9", "-af",
                f"highpass=f=250,lowpass=f=7000,afade=t=in:d={d * 0.62}:curve=exp,afade=t=out:st={d * 0.62}:d={d * 0.38}:curve=log,"
                f"aecho=0.6:0.4:35:0.25,aformat=channel_layouts=stereo,alimiter=limit=0.9", "-t", str(d), sortie])
    elif kind == "riser":
        ton = f"aevalsrc='0.35*sin(2*PI*t*(180+900*(t/{d})^2))*(t/{d})':d={d}:s={SR}"
        bruit = f"anoisesrc=c=white:d={d}:r={SR}:a=0.5,highpass=f=1200,afade=t=in:d={d}:curve=exp"
        lancer(["-f", "lavfi", "-i", ton, "-f", "lavfi", "-i", bruit, "-filter_complex",
                f"[0][1]amix=inputs=2:normalize=0,aformat=channel_layouts=stereo,alimiter=limit=0.9", "-t", str(d), sortie])
    elif kind == "tick":
        lancer(["-f", "lavfi", "-i", f"anoisesrc=c=white:d={d}:r={SR}:a=0.7", "-af",
                f"highpass=f=2500,afade=t=out:st=0:d={d},aformat=channel_layouts=stereo", "-t", str(d), sortie])
    else:
        raise SystemExit(f"type inconnu : {kind}")


if __name__ == "__main__":
    generer(sys.argv[1], float(sys.argv[2]), sys.argv[3])
