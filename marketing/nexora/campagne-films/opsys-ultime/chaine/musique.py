"""Musique du film ultime : Lyria 3 Pro (OpenRouter), puis grille MESURÉE (tempo, phase, temps, énergie par 0,5 s, premier
saut d'énergie). Le BPM demandé n'est jamais cru : le montage se cale sur la grille mesurée.

  python3 musique.py <equipe> <n°> "<prompt>"   → <travail>/<equipe>/musique/lyria-<n°>.{mp3,wav,json}
  python3 musique.py --mesurer fichier.wav       → grille seule
La clé est lue dans ~/Desktop/Deepinfra.env par commun.cle (jamais imprimée).
"""
import json
import subprocess
import sys
import time
from pathlib import Path

import numpy as np

ICI = Path(__file__).resolve().parent
sys.path.insert(0, str(ICI.parents[1] / "films-v3/outils"))
import commun as C  # noqa: E402


def lyria(prompt, modele="google/lyria-3-pro-preview"):
    """Appel en flux d'OpenRouter (repris de films-v3/outils/musique.py) ; renvoie (octets mp3, coût USD)."""
    import base64
    import urllib.request
    corps = {"model": modele, "messages": [{"role": "user", "content": prompt}], "modalities": ["text", "audio"], "stream": True}
    r = urllib.request.Request("https://openrouter.ai/api/v1/chat/completions", data=json.dumps(corps).encode(),
                               headers={"Authorization": "Bearer " + C.cle("openrouter"), "Content-Type": "application/json"})
    morceaux, cout = [], None
    with urllib.request.urlopen(r, timeout=900) as resp:
        for ligne in resp:
            ligne = ligne.decode().strip()
            if not ligne.startswith("data:") or ligne[5:].strip() == "[DONE]":
                continue
            try:
                j = json.loads(ligne[5:])
            except ValueError:
                continue
            if j.get("usage"):
                cout = j["usage"].get("cost")
            for c in j.get("choices", []):
                a = c.get("delta", {}).get("audio")
                if a and a.get("data"):
                    morceaux.append(a["data"])
    return base64.b64decode("".join(morceaux)), cout

TRAVAIL = Path.home() / "nexora-creative-data/work/opsys-ultime"
FF = str(Path.home() / "nexora-creative-data/engine/ffmpeg/ffmpeg-7.0.2-arm64-static/ffmpeg")


def lire(f, sr=22050):
    raw = subprocess.run([FF, "-v", "error", "-i", str(f), "-ac", "1", "-ar", str(sr), "-f", "f32le", "-"], capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.float32)


def grille(f):
    SR, HOP = 22050, 220
    x = lire(f, SR)
    n = len(x) // HOP - 5
    fen = np.hanning(1024)
    S = np.abs(np.fft.rfft(np.stack([x[i * HOP:i * HOP + 1024] * fen for i in range(n) if i * HOP + 1024 <= len(x)]), axis=1))
    flux = np.maximum(0, np.diff(np.log1p(S * 10), axis=0)).sum(1)
    flux = (flux - np.convolve(flux, np.ones(50) / 50, "same")).clip(0)
    ac = np.correlate(flux, flux, "full")[len(flux) - 1:]
    lags = np.arange(len(ac)) / 100
    ok = (lags > 60 / 170) & (lags < 60 / 70)
    i = int(round(lags[ok][np.argmax(ac[ok])] * 100))
    y0, y1, y2 = ac[i - 1], ac[i], ac[i + 1]
    lag = (i + 0.5 * (y0 - y2) / (y0 - 2 * y1 + y2)) / 100
    phases = np.linspace(0, lag, 50, endpoint=False)
    sc = [flux[np.clip(np.round(np.arange(p, len(flux) / 100, lag) * 100).astype(int), 0, len(flux) - 1)].sum() for p in phases]
    ph = float(phases[int(np.argmax(sc))])
    rms = np.array([20 * np.log10(np.sqrt(np.mean(x[k:k + SR // 2] ** 2)) + 1e-6) for k in range(0, len(x) - SR // 2, SR // 2)])
    # sauts d'énergie : hausse ≥ 6 dB entre deux demi-secondes consécutives (moyenne glissante de 1 s)
    lis = np.convolve(rms, np.ones(2) / 2, "same")
    sauts = [round(0.5 * k, 1) for k in range(2, len(lis)) if lis[k] - lis[k - 2] >= 6]
    return {"fichier": str(f), "bpm": round(60 / lag, 2), "temps_s": round(lag, 4), "phase_s": round(ph, 3),
            "duree_s": round(len(x) / SR, 2), "sauts_energie_s": sauts[:20],
            "energie_db_05s": [round(float(v), 1) for v in rms]}


def composer(equipe, n, prompt, modele="google/lyria-3-pro-preview"):
    d = TRAVAIL / equipe / "musique"
    d.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    octets, cout = lyria(prompt, modele)
    mp3 = d / f"lyria-{n}.mp3"
    mp3.write_bytes(octets)
    wav = d / f"lyria-{n}.wav"
    subprocess.run([FF, "-v", "error", "-y", "-i", str(mp3), "-ar", "48000", "-ac", "2", str(wav)], check=True)
    g = grille(wav)
    g.update({"equipe": equipe, "n": n, "modele": modele, "cout_usd": cout, "secondes": round(time.time() - t0, 1), "prompt": prompt})
    (d / f"lyria-{n}.json").write_text(json.dumps(g, ensure_ascii=False, indent=1))
    with (TRAVAIL / "journal-api.jsonl").open("a") as fh:
        fh.write(json.dumps({"equipe": equipe, "quoi": f"musique {n}", "modele": modele, "cout_usd": cout,
                             "secondes": g["secondes"], "duree_s": g["duree_s"]}) + "\n")
    return g


if __name__ == "__main__":
    if sys.argv[1] == "--mesurer":
        print(json.dumps(grille(sys.argv[2]), ensure_ascii=False))
    else:
        g = composer(sys.argv[1], sys.argv[2], sys.argv[3], *(sys.argv[4:5]))
        print(json.dumps({k: g[k] for k in ("bpm", "duree_s", "sauts_energie_s", "cout_usd", "secondes")}, ensure_ascii=False))
