"""Mesure une piste Music3 : tempo réel (autocorrélation du flux spectral), phase de la grille, sections (énergie par 0,25 s),
coups forts. Usage : python mesurer_musique.py <piste.flac>"""
import subprocess
import sys
from pathlib import Path

import numpy as np

FF = str(Path.home() / "nexora-creative-data/engine/ffmpeg/ffmpeg-7.0.2-arm64-static/ffmpeg")
SR, HOP = 22050, 220  # 100 trames/s


def lire(f):
    b = subprocess.run([FF, "-v", "error", "-i", f, "-f", "f32le", "-ac", "1", "-ar", str(SR), "-"], capture_output=True).stdout
    return np.frombuffer(b, np.float32)


def mesurer(f):
    x = lire(f)
    n = len(x) // HOP - 4
    fen = np.hanning(1024)
    S = np.abs(np.fft.rfft(np.stack([x[i * HOP:i * HOP + 1024] * fen for i in range(n) if i * HOP + 1024 <= len(x)]), axis=1))
    flux = np.maximum(0, np.diff(np.log1p(S * 10), axis=0)).sum(1)
    flux = (flux - np.convolve(flux, np.ones(50) / 50, "same")).clip(0)
    ac = np.correlate(flux, flux, "full")[len(flux) - 1:]
    lags = np.arange(len(ac)) / 100
    ok = (lags > 60 / 180) & (lags < 60 / 70)
    lag = lags[ok][np.argmax(ac[ok])]
    # affinage parabolique
    i = int(round(lag * 100)); y0, y1, y2 = ac[i - 1], ac[i], ac[i + 1]
    lag = (i + 0.5 * (y0 - y2) / (y0 - 2 * y1 + y2)) / 100
    bpm = 60 / lag
    # phase : décalage qui maximise le flux sur la grille
    T = np.arange(len(flux)) / 100
    phases = np.linspace(0, lag, 50, endpoint=False)
    sc = [flux[np.clip(np.round((np.arange(p, T[-1], lag)) * 100).astype(int), 0, len(flux) - 1)].sum() for p in phases]
    phase = phases[int(np.argmax(sc))]
    e = np.array([np.sqrt(np.mean(x[int(k * 0.25 * SR):int((k + 1) * 0.25 * SR)] ** 2)) for k in range(int(len(x) / SR / 0.25))])
    edb = 20 * np.log10(e + 1e-6)
    sauts = [(round(k * 0.25, 2), round(edb[k] - edb[max(0, k - 4):k].mean(), 1)) for k in range(4, len(edb)) if edb[k] - edb[max(0, k - 4):k].mean() > 6]
    print(f"{Path(f).name} : {len(x) / SR:.1f} s, tempo {bpm:.2f} BPM (temps {lag:.4f} s), phase {phase:.3f} s")
    print("énergie (dB) par seconde :", " ".join(f"{edb[k * 4:(k + 1) * 4].mean():.0f}" for k in range(len(edb) // 4)))
    print("sauts d'énergie > 6 dB :", sauts[:30])


if __name__ == "__main__":
    for f in sys.argv[1:]:
        mesurer(f)
