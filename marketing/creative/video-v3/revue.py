"""Auto-revue d'un montage V3 : planche contact (une image au milieu de chaque plan, plus l'image de chaque coupe),
statistiques de coupe par section (nombre, durée moyenne), et contrôle du son autour des coupes (crête dans ±60 ms :
un coup doit tomber sur la coupe), sonie intégrée et crête vraie.

Usage : python3 revue.py montage-v3.json film.mp4 planche.jpg [version]
"""
import json
import subprocess
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, str(Path(__file__).resolve().parent))
from couches import FFMPEG, FFPROBE  # noqa: E402

m = json.loads(Path(sys.argv[1]).read_text())
film, planche = sys.argv[2], sys.argv[3]
version = sys.argv[4] if len(sys.argv) > 4 else "long"
seq = m["sequence"] if version == "long" else m["versions"][version]["sequence"]
coupes, t0 = [], 0.0
for s in seq:
    coupes.append((t0, s["fin"], s.get("plan") or s.get("type"), s.get("section", "")))
    t0 = s["fin"]

# --- statistiques par section
print(f"{len(coupes)} plans, {coupes[-1][1]:.2f} s")
sections = {}
for a, b, nom, sec in coupes:
    sections.setdefault(sec, []).append(b - a)
for sec, ds in sections.items():
    print(f"  {sec or '-':<12} {len(ds):>3} plans, moyenne {np.mean(ds):.2f} s, min {min(ds):.2f}, max {max(ds):.2f}")

# --- planche contact
r = subprocess.run([FFMPEG, "-v", "error", "-i", film, "-vf", "scale=320:-2", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True)
w0 = 320
fr = np.frombuffer(r.stdout, np.uint8)
h0 = fr.size // w0 // 3
n_img = None
probe = subprocess.run([FFPROBE, "-v", "error", "-select_streams", "v:0", "-show_entries",
                        "stream=width,height", "-of", "csv=p=0", film], capture_output=True, text=True).stdout.strip().split(",")
W, H = int(probe[0]), int(probe[1])
h0 = round(320 * H / W / 2) * 2
fr = fr.reshape(-1, h0, w0, 3)
cols = 8
rows = (len(coupes) + cols - 1) // cols
pl = Image.new("RGB", (cols * w0, rows * (h0 + 18)), (12, 12, 16))
d = ImageDraw.Draw(pl)
for k, (a, b, nom, sec) in enumerate(coupes):
    i = min(len(fr) - 1, int((a + b) / 2 * 24))
    x, y = (k % cols) * w0, (k // cols) * (h0 + 18)
    pl.paste(Image.fromarray(fr[i]), (x, y + 18))
    d.text((x + 4, y + 3), f"{k:02d} {a:5.2f} {nom}"[:44], fill=(235, 235, 235))
pl.save(planche, quality=88)

# --- son autour des coupes
pcm = subprocess.run([FFMPEG, "-v", "error", "-i", film, "-ac", "1", "-ar", "8000", "-f", "f32le", "-"], capture_output=True).stdout
x = np.frombuffer(pcm, np.float32)
env = np.sqrt(np.convolve(x ** 2, np.ones(160) / 160, "same"))  # 20 ms
fond = np.median(env)
sur, coups = 0, []
for a, b, nom, sec in coupes[1:]:
    i = int(a * 8000)
    av = env[max(0, i - 2400):i - 400].mean() + 1e-6
    ap = env[i - 480:i + 480].max()
    gain = 20 * np.log10(ap / av)
    coups.append(gain)
    sur += gain > 3
print(f"coupes avec attaque ≥ 3 dB dans ±60 ms : {sur}/{len(coupes) - 1} (moyenne {np.mean(coups):.1f} dB)")
lo = subprocess.run([FFMPEG, "-hide_banner", "-i", film, "-af", "loudnorm=print_format=json", "-f", "null", "-"], capture_output=True, text=True).stderr
j = json.loads(lo[lo.rindex("{"):lo.rindex("}") + 1])
print(f"sonie {j['input_i']} LUFS, crête vraie {j['input_tp']} dBTP, LRA {j['input_lra']}")
