"""Silent loop of the home hero (10-15 s): shot A (data-center aisle) → cross-dissolve → shot B (light field) →
cross-dissolve → back into A. The file starts and ends at the same instant of A (seamless loop: the last frame
leads into the first one). "Signal" grading, no text (titles are set by the site in HTML).

  python3 hero_boucle.py 16x9|9x16 [--a allee] [--b champ] [--coupe 2.0] [--fondu 1.2]
→ site-medias/masters/hero-boucle-<fmt>-master.mp4 then web encodings (H.264 + WebM AV1, < 6 MB) + poster + manifest."""
import argparse, subprocess, sys
from pathlib import Path
ICI = Path(__file__).resolve().parent
sys.path.insert(0, str(ICI / "outils"))
from moteurs import TRAVAIL
from films import CHOIX
import exporter
from planche import duree

a = argparse.ArgumentParser()
a.add_argument("fmt"); a.add_argument("--a", default="allee"); a.add_argument("--b", default="champ")
a.add_argument("--coupe", type=float, default=2.0); a.add_argument("--fondu", type=float, default=1.2)
a.add_argument("--vitesse", type=float, default=1.0)
o = a.parse_args()
W, H = (1920, 1080) if o.fmt == "16x9" else (1080, 1920)
pa = TRAVAIL / "plans" / "hero" / f"{o.a}-{o.fmt}-{CHOIX.get(f'hero/{o.a}-{o.fmt}', CHOIX.get(f'hero/{o.a}', 'v1'))}.mp4"
pb = TRAVAIL / "plans" / "hero" / f"{o.b}-{o.fmt}-{CHOIX.get(f'hero/{o.b}-{o.fmt}', CHOIX.get(f'hero/{o.b}', 'v1'))}.mp4"
v = o.vitesse
da, db = duree(pa) / v, duree(pb) / v  # durations after slow-down
c, f = o.coupe, o.fondu
prep = (f"setpts=PTS/{v},fps=24,scale={W}:{H}:force_original_aspect_ratio=increase:flags=lanczos,crop={W}:{H},"
        "setsar=1,format=yuv420p")
g = (f"[0:v]{prep},split[a1][a2];[1:v]{prep}[b];"
     f"[a1]trim=start={c}:end={da - 0.1:.3f},setpts=PTS-STARTPTS,fps=24[queue];"
     f"[a2]trim=start=0:end={c:.3f},setpts=PTS-STARTPTS,fps=24[tete];"
     f"[b]trim=end={db - 0.1:.3f},setpts=PTS-STARTPTS,fps=24[bb];"
     f"[queue][bb]xfade=transition=fade:duration={f}:offset={da - 0.1 - c - f:.3f}[x1];"
     f"[x1][tete]xfade=transition=fade:duration={min(f, c - 0.05):.3f}:offset={da - 0.1 - c - f + db - 0.1 - min(f, c - 0.05):.3f}[x2];"
     "[x2]eq=contrast=1.05:gamma=0.98,colorbalance=rs=-0.02:bs=0.045:bm=0.02:bh=0.01,vignette=angle=PI/4.4,"
     "noise=alls=3:allf=t,format=yuv420p[v]")
(exporter.LIVRE / "masters").mkdir(parents=True, exist_ok=True)
master = exporter.LIVRE / "masters" / f"hero-boucle-{o.fmt}-master.mp4"
exporter.lancer("-i", pa, "-i", pb, "-filter_complex", g, "-map", "[v]", "-an", "-c:v", "libx264", "-preset", "slow", "-crf", "14",
                "-pix_fmt", "yuv420p", "-movflags", "+faststart", master)
from moteurs import h3
from plans import PLANS
e = exporter.exporter_video(str(master), f"hero-boucle-{o.fmt}", "Boucle muette du héros de l’accueil (lecture auto, en boucle, muette ; "
                            "texte posé par le site en HTML).", "aucune (muette, sans texte)", boucle=True, cible_mo=5.5,
                            poster_t=0.0, extra={"master": f"masters/{master.name}",
                                                 "plans_h3": {o.a: h3(PLANS["hero"][o.a][2], PLANS["hero"][o.a][3]),
                                                              o.b: h3(PLANS["hero"][o.b][2], PLANS["hero"][o.b][3])},
                                                 "moteur": "MiniMax H3 complet (RTX 5090), 24 étapes, sans son ; ralenti ×%.2f, fondus enchaînés" % v})
print(e)
