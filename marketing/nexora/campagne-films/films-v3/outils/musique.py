"""Musique des films V5 : Lyria 3 Pro (OpenRouter), deux propositions par film, tempo et grille MESURÉS, choix automatique
de la proposition dont l'énergie suit le mieux la courbe voulue par le scénario (film.json → musique.courbe).

  python3 musique.py <film> [n=2]       → work/films-v3/<film>/musique/{lyria-1,lyria-2}.wav, musique.json (grille, choix)
La musique reste un stem séparé : le mixeur (mixer.py) la pose, la baisse sous la voix (≥ 9 dB) et coupe les plans sur sa grille.
"""
import base64
import json
import sys
import time
import urllib.request

import numpy as np

import commun as C


def lyria(prompt, modele="google/lyria-3-pro-preview"):
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


def grille(f):
    """Tempo (flux spectral + autocorrélation), phase et liste des temps (s) ; profil d'énergie par demi-seconde (dB)."""
    SR, HOP = 22050, 220
    x = C.lire(f, SR, 1)[:, 0]
    n = len(x) // HOP - 5
    fen = np.hanning(1024)
    S = np.abs(np.fft.rfft(np.stack([x[i * HOP:i * HOP + 1024] * fen for i in range(n) if i * HOP + 1024 <= len(x)]), axis=1))
    flux = np.maximum(0, np.diff(np.log1p(S * 10), axis=0)).sum(1)
    flux = (flux - np.convolve(flux, np.ones(50) / 50, "same")).clip(0)
    ac = np.correlate(flux, flux, "full")[len(flux) - 1:]
    lags = np.arange(len(ac)) / 100
    ok = (lags > 60 / 150) & (lags < 60 / 70)
    i = int(round(lags[ok][np.argmax(ac[ok])] * 100))
    y0, y1, y2 = ac[i - 1], ac[i], ac[i + 1]
    lag = (i + 0.5 * (y0 - y2) / (y0 - 2 * y1 + y2)) / 100
    phases = np.linspace(0, lag, 50, endpoint=False)
    sc = [flux[np.clip(np.round(np.arange(p, len(flux) / 100, lag) * 100).astype(int), 0, len(flux) - 1)].sum() for p in phases]
    ph = float(phases[int(np.argmax(sc))])
    rms = [float(20 * np.log10(np.sqrt(np.mean(x[k:k + SR // 2] ** 2)) + 1e-6)) for k in range(0, len(x) - SR // 2, SR // 2)]
    return {"bpm": round(60 / lag, 2), "temps_s": round(lag, 4), "phase_s": round(ph, 3), "duree_s": round(len(x) / SR, 2),
            "energie_db_05s": [round(v, 1) for v in rms]}


def score(g, courbe, duree):
    """Corrélation entre l'énergie mesurée et la courbe voulue [[t, niveau 0..1], ...] sur la durée du film."""
    e = np.array(g["energie_db_05s"])
    t = np.arange(len(e)) * 0.5
    m = t < duree
    if m.sum() < 10 or g["duree_s"] < duree - 1:
        return -1.0
    voulu = np.interp(t[m], [p[0] for p in courbe], [p[1] for p in courbe])
    return float(np.corrcoef(e[m], voulu)[0, 1])


def composer(film, n=2):
    f = C.charger_film(film)
    mu = f["musique"]
    d = C.dossier(film) / "musique"
    d.mkdir(exist_ok=True)
    props = []
    for k in range(1, n + 1):
        w = d / f"lyria-{k}.wav"
        if not w.exists():
            t0 = time.time()
            b, cout = lyria(mu["prompt"])
            (d / f"lyria-{k}.mp3").write_bytes(b)
            C.ff("-i", d / f"lyria-{k}.mp3", "-ar", C.SR, "-ac", 2, w)
            print(film, k, "coût", cout, round(time.time() - t0, 1), "s", flush=True)
        g = grille(w)
        g["fichier"] = str(w)
        g["score"] = round(score(g, mu["courbe"], f["duree"]), 3)
        props.append(g)
        print(film, k, g["bpm"], g["duree_s"], g["score"], flush=True)
    choix = max(props, key=lambda g: g["score"])
    (d / "musique.json").write_text(json.dumps({"choix": choix["fichier"], "propositions": props}, ensure_ascii=False, indent=1))
    return choix


if __name__ == "__main__":
    composer(sys.argv[1], int(sys.argv[2]) if len(sys.argv) > 2 else 2)
