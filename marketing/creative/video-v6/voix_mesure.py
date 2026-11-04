"""Mesures objectives des échantillons de voix (aucune ne remplace l'oreille du fondateur).
  <venv transcription>/bin/python -I voix_mesure.py <dossier>   → <dossier>/mesures.json et un tableau texte
Par fichier : durée, mots/s, F0 médiane et étendue p10–p90 en demi-tons (une voix « smooth » a une étendue étroite),
écart-type du niveau court terme en dB (dynamique des attaques), part de silence, transcription Whisper et taux d'erreur.
"""
import json
import re
import subprocess
import sys
from pathlib import Path

import numpy as np

FF = str(Path.home() / "nexora-creative-data/engine/ffmpeg/ffmpeg-7.0.2-arm64-static/ffmpeg")
sys.path.insert(0, str(Path(__file__).resolve().parent))
from voix_casting import TEXTE  # noqa: E402

# texte des essais de voix native H3 (voix_h3 : specs-voix-h3.json)
TEXTE_H3 = {"fr": "Trois mots. Même mal écrits. L'IA écrit le reste. Une bataille dans l'espace ? Réglé. T'écris trois mots. On fait le film.",
            "en": "Three words. Typos and all. The AI writes the rest. A space battle? Done. You type three words. We make the movie."}


def charger(p):
    raw = subprocess.run([FF, "-loglevel", "error", "-i", str(p), "-f", "f32le", "-ac", "1", "-ar", "16000", "-"], capture_output=True).stdout
    return np.frombuffer(raw, dtype=np.float32)


def f0(x):
    n, hop, out = 640, 160, []
    for i in range(0, len(x) - n, hop):
        w = x[i:i + n]
        if np.sqrt((w ** 2).mean()) < 0.02:
            continue
        w = w - w.mean()
        ac = np.correlate(w, w, "full")[n - 1:]
        lo, hi = int(16000 / 400), int(16000 / 65)
        k = lo + int(np.argmax(ac[lo:hi]))
        if ac[k] / ac[0] > 0.5:
            out.append(16000 / k)
    if len(out) < 10:
        return None, None
    o = np.array(out)
    return float(np.median(o)), float(12 * np.log2(np.percentile(o, 90) / np.percentile(o, 10)))


def dynamique(x):
    fen = 1600  # 100 ms
    db = np.array([20 * np.log10(np.sqrt((x[i:i + fen] ** 2).mean()) + 1e-6) for i in range(0, len(x) - fen, fen)])
    voix = db[db > db.max() - 40]
    return float(voix.std()), float((db < db.max() - 35).mean())


def norm(s):
    return re.sub(r"[^\w\s'-]", " ", s.lower().replace("’", "'")).split()


def wer(ref, hyp):
    r, h = norm(ref), norm(hyp)
    d = list(range(len(h) + 1))
    for i in range(1, len(r) + 1):
        p = d[:]
        d[0] = i
        for j in range(1, len(h) + 1):
            d[j] = min(p[j] + 1, d[j - 1] + 1, p[j - 1] + (r[i - 1] != h[j - 1]))
    return round(d[len(h)] / max(1, len(r)), 3)


if __name__ == "__main__":
    from faster_whisper import WhisperModel
    dossier = Path(sys.argv[1])
    m = WhisperModel("medium", device="cpu", compute_type="int8", cpu_threads=12)
    res = []
    for f in sorted(list(dossier.glob("*.mp3")) + list(dossier.glob("*.wav"))):
        langue = "en" if re.search(r"-en(\.|-)", f.name) else "fr"
        x = charger(f)
        dur = len(x) / 16000
        med, etendue = f0(x)
        dyn, silence = dynamique(x)
        txt = " ".join(s.text.strip() for s in m.transcribe(x, language=langue, beam_size=5)[0])
        ref = TEXTE_H3[langue] if f.name.startswith("K-") else TEXTE[langue]
        r = {"fichier": f.name, "langue": langue, "duree": round(dur, 2), "mots_s": round(len(norm(ref)) / dur, 2),
             "f0_med": round(med or 0), "f0_etendue_dt": round(etendue or 0, 1), "dyn_db": round(dyn, 1), "silence": round(silence, 2),
             "wer": wer(ref, txt), "whisper": txt}
        res.append(r)
        print(f"{f.name:52s} {dur:5.1f}s {r['mots_s']:4.2f} m/s  F0 {r['f0_med']:3d} Hz étendue {r['f0_etendue_dt']:4.1f} dt  dyn {r['dyn_db']:4.1f} dB  "
              f"sil {r['silence']:.2f}  WER {r['wer']:.2f}", flush=True)
    (dossier / "mesures.json").write_text(json.dumps(res, ensure_ascii=False, indent=1))
