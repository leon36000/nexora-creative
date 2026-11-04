"""Mixeur des films V5 : stems séparés (narration phrase par phrase, musique, bruitages) → audio.json + mix −14 LUFS.

  python3 mixer.py <film> [moteur_voix]
Règles : la voix ne se chevauche jamais (respiration ≥ 0,3 s), la musique baisse de 10 dB sous la voix (rampes 0,3 / 0,5 s),
bruitages courts et rares (souffle, clic, coup sourd, vibration) synthétisés ici ; normalisation finale −14 LUFS intégrés,
crête vraie ≤ −1,5 dBTP (loudnorm en deux passes, linéaire). Changer la voix ou la musique = relancer ce script seul.
Sorties : work/films-v3/<film>/audio/{voix,musique,sfx}-stem.wav, mix.wav, audio.json, mesure.json.
"""
import json
import re
import subprocess
import sys

import numpy as np

import commun as C

SR = C.SR
DUCK_DB = -10.0


def db(x):
    return 10 ** (x / 20)


def sfx(type_, rng):
    n = lambda s: int(s * SR)
    if type_ == "impact":  # coup sourd : sinus 52 → 38 Hz, décroissance longue, attaque feutrée
        t = np.arange(n(2.2)) / SR
        f = 38 + 14 * np.exp(-t * 6)
        x = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 2.2) * (1 - np.exp(-t * 400))
        x += 0.15 * rng.normal(0, 1, len(t)) * np.exp(-t * 40)
    elif type_ == "clic":  # clic d'interface : bruit filtré très court
        t = np.arange(n(0.05)) / SR
        x = rng.normal(0, 1, len(t)) * np.exp(-t * 180)
        x = np.convolve(x, np.ones(6) / 6, "same") * 0.9
    elif type_ == "souffle":  # air, respiration de la salle
        t = np.arange(n(1.6)) / SR
        b = np.convolve(rng.normal(0, 1, len(t)), np.ones(40) / 40, "same")  # court : 77 000 × 40
        x = b * np.sin(np.pi * t / t[-1]) ** 2 * 3
    elif type_ == "vibre":  # téléphone qui vibre deux fois sur une surface
        t = np.arange(n(0.9)) / SR
        env = ((t % 0.45) < 0.28).astype(float) * (t < 0.73)
        x = np.sin(2 * np.pi * 150 * t) * (0.6 + 0.4 * np.sin(2 * np.pi * 23 * t)) * env * 0.5
    else:
        return None
    x = x / (np.abs(x).max() + 1e-9)
    return np.stack([x, x], 1).astype(np.float32)


def lufs(f):
    r = subprocess.run([C.FF, "-hide_banner", "-i", str(f), "-af", "ebur128=peak=true", "-f", "null", "-"], capture_output=True, text=True).stderr
    i = re.findall(r"I:\s+(-?[\d.]+) LUFS", r)
    p = re.findall(r"Peak:\s+(-?[\d.]+) dBFS", r)
    lra = re.findall(r"LRA:\s+(-?[\d.]+) LU", r)
    return {"lufs": float(i[-1]), "crete_vraie_dbtp": float(p[-1]) if p else None, "lra": float(lra[-1]) if lra else None}


def mixer(nom, moteur=None):
    film = C.charger_film(nom)
    choix = json.loads((C.RACINE / "audio-choix.json").read_text())
    moteur = moteur or choix["voix"]
    dos = C.dossier(nom)
    out = dos / "audio"
    out.mkdir(exist_ok=True)
    N = int((film["duree"] + 0.5) * SR)
    rng = np.random.default_rng(3)
    # --- narration
    vj = {x["id"]: x for x in json.loads((dos / "voix" / moteur / "voix.json").read_text())["phrases"]}
    voix = np.zeros((N, 2), np.float32)
    poses, fin_prec, actif = [], 0.0, np.zeros(N, np.float32)
    for x in film["narration"]:
        a = C.lire(dos / "voix" / moteur / f"{x['id']}.wav")
        t = max(x["t"], fin_prec + 0.3)
        i = int(t * SR)
        j = min(N, i + len(a))
        voix[i:j] += a[: j - i]
        actif[max(0, i - int(0.3 * SR)): min(N, j + int(0.5 * SR))] = 1
        fin_prec = t + len(a) / SR
        poses.append({"id": x["id"], "fichier": str(dos / "voix" / moteur / f"{x['id']}.wav"), "t": round(t, 3), "duree": round(len(a) / SR, 3),
                      "decale_s": round(t - x["t"], 3), "texte": x["texte"]})
    # --- musique : automation (entrée, ducking, sortie)
    mj = json.loads((dos / "musique/musique.json").read_text())
    m = C.lire(mj["choix"])[:N]
    m = np.pad(m, ((0, N - len(m)), (0, 0)))
    k = int(0.3 * SR)  # moyenne glissante par somme cumulée (rampe 0,3 s)
    cs = np.concatenate([[0.0], np.cumsum(actif, dtype=np.float64)])
    lis = ((cs[np.clip(np.arange(N) + k // 2, 0, N)] - cs[np.clip(np.arange(N) - k // 2, 0, N)]) / k).astype(np.float32)
    g = db(film["musique"].get("gain_db", 0) - 8.0) * db(DUCK_DB * lis)
    t = np.arange(N) / SR
    g *= np.clip(t / 0.5, 0, 1) * np.clip((film["duree"] - t) / 2.5, 0, 1)
    musique = m * g[:, None]
    # --- bruitages
    sf = np.zeros((N, 2), np.float32)
    for s in film.get("sfx", []):
        x = sfx(s["type"], rng)
        if x is None:
            continue
        i = int(s["t"] * SR)
        j = min(N, i + len(x))
        sf[i:j] += x[: j - i] * db(s["db"])
    for nomf, x in (("voix", voix), ("musique", musique), ("sfx", sf)):
        C.ecrire(out / f"{nomf}-stem.wav", x)
    brut = voix + musique + sf
    C.ecrire(out / "mix-brut.wav", brut)
    # --- loudnorm deux passes
    r = subprocess.run([C.FF, "-hide_banner", "-i", str(out / "mix-brut.wav"), "-af", "loudnorm=I=-14:TP=-1.5:LRA=11:print_format=json",
                        "-f", "null", "-"], capture_output=True, text=True).stderr
    js = json.loads(r[r.rindex("{"):r.rindex("}") + 1])
    f2 = (f"loudnorm=I=-14:TP=-1.5:LRA=11:measured_I={js['input_i']}:measured_TP={js['input_tp']}:measured_LRA={js['input_lra']}:"
          f"measured_thresh={js['input_thresh']}:offset={js['target_offset']}:linear=true")
    C.ff("-i", out / "mix-brut.wav", "-af", f2 + ",alimiter=limit=0.84:level=false", "-ar", SR, "-c:a", "pcm_s24le", out / "mix.wav")
    mes = lufs(out / "mix.wav")
    # écart voix / musique sous la voix (dB RMS) : preuve du ducking ≥ 9 dB
    vv = actif > 0.5
    ecart = 20 * np.log10((np.sqrt(np.mean(voix[vv] ** 2)) + 1e-9) / (np.sqrt(np.mean(musique[vv] ** 2)) + 1e-9))
    mes["voix_sur_musique_db"] = round(float(ecart), 1)
    aj = {"film": nom, "statut": choix["statut"], "voix": {"moteur": moteur, "phrases": poses},
          "musique": {"fichier": mj["choix"], "gain_db": film["musique"].get("gain_db", 0) - 8.0, "ducking_db": DUCK_DB},
          "sfx": film.get("sfx", []), "stems": {k: str(out / f"{k}-stem.wav") for k in ("voix", "musique", "sfx")},
          "mix": str(out / "mix.wav"), "mesure": mes}
    (out / "audio.json").write_text(json.dumps(aj, ensure_ascii=False, indent=1))
    print(json.dumps(mes), flush=True)
    return aj


if __name__ == "__main__":
    mixer(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None)
