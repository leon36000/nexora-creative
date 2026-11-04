"""Mesure grossière de synchronisation labiale (sans détecteur de visage) : mouvement de la région de la bouche
(différence d'images dans une boîte autour du bas du visage, cadrée en fractions) contre l'enveloppe de la voix ;
corrélation croisée de −8 à +8 images. Usage : python3 synchro.py video.mp4 [x0 y0 x1 y1] → {lag_images, r_max, r_0}.
Un bon plan parlant donne r_max ≥ 0,3 à |lag| ≤ 2 images ; un visage figé ou désynchronisé, r < 0,15."""
import json, subprocess, sys
from pathlib import Path
import numpy as np
FF = str(Path.home() / "nexora-creative-data/engine/ffmpeg/ffmpeg-7.0.2-arm64-static/ffmpeg")
FP = FF.replace("ffmpeg/ffmpeg-7", "ffmpeg/ffmpeg-7").rsplit("/", 1)[0] + "/ffprobe"

def mesurer(f, boite=(0.40, 0.38, 0.60, 0.72)):
    w, h = map(int, subprocess.run([FP, "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height", "-of", "csv=p=0", f],
                                   capture_output=True, text=True).stdout.strip().split(","))
    v = np.frombuffer(subprocess.run([FF, "-v", "error", "-i", f, "-f", "rawvideo", "-pix_fmt", "gray", "-"], capture_output=True).stdout, np.uint8)
    v = v.reshape(-1, h, w).astype(np.float32)
    x0, y0, x1, y1 = boite
    r = v[:, int(y0 * h):int(y1 * h), int(x0 * w):int(x1 * w)]
    mouv = np.r_[0, np.abs(np.diff(r, axis=0)).mean((1, 2))]
    sombre = (r < np.percentile(r, 12)).mean((1, 2))  # cavité buccale
    a = np.frombuffer(subprocess.run([FF, "-v", "error", "-i", f, "-ac", "1", "-ar", "24000", "-f", "f32le", "-"], capture_output=True).stdout, np.float32)
    n = len(v)
    env = np.array([np.sqrt(np.mean(a[int(i * 1000):int((i + 1) * 1000)] ** 2)) if int(i * 1000) < len(a) else 0 for i in range(n)])
    def z(x):
        x = x - np.convolve(x, np.ones(9) / 9, "same")  # retire la tendance (travelling, respiration)
        return (x - x.mean()) / (x.std() + 1e-9)
    res = {}
    for nom, sig in (("mouvement", mouv), ("ouverture", sombre)):
        zs, ze = z(sig), z(env)
        cc = {k: float(np.mean(zs[max(0, k):n + min(0, k)] * ze[max(0, -k):n - max(0, k)])) for k in range(-8, 9)}
        k = max(cc, key=lambda q: cc[q])
        res[nom] = {"lag_images": k, "r_max": round(cc[k], 3), "r_0": round(cc[0], 3)}
    return res

if __name__ == "__main__":
    b = tuple(map(float, sys.argv[2:6])) if len(sys.argv) >= 6 else (0.40, 0.38, 0.60, 0.72)
    print(json.dumps(mesurer(sys.argv[1], b)))
