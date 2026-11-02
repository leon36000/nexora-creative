"""Edits of the redesign films (one film per solution / tool), fr and en, 16:9 and 9:16.

  python3 montage.py <film> <fr|en> <16x9|9x16> [--rapide] [--sans-export]

Writes montages/<film>-<lang>-<fmt>.json (the edit: shots, texts, music, sound design — editable by hand), renders the
"Signal" end card if needed, edits with outils/film_signal.py into site-medias/masters/, then exports the web encodings
and the manifest entry. Texts are set in code: to change a sentence, edit films.py (or the JSON) and re-run, no new
GPU render. Brand name/signature: marque.json.
"""
import json, subprocess, sys
from pathlib import Path
import numpy as np

ICI = Path(__file__).resolve().parent
sys.path.insert(0, str(ICI / "outils"))
from moteurs import TRAVAIL
from films import FILMS, CHOIX
import exporter

FFMPEG = exporter.FFMPEG
LIVRE = exporter.LIVRE
FORMATS = {"16x9": "16:9", "9x16": "9:16"}


def tempo(f):
    """Beat grid (s) of a piece of music: onset envelope + autocorrelation (marketing/creative/outils/tempo.py)."""
    SR, HOP = 16000, 160
    x = np.frombuffer(subprocess.run([FFMPEG, "-v", "error", "-i", str(f), "-ac", "1", "-ar", str(SR), "-f", "f32le", "-"],
                                     capture_output=True).stdout, dtype=np.float32)
    n = len(x) // HOP
    e = np.log1p(100 * np.sqrt((x[: n * HOP].reshape(n, HOP) ** 2).mean(axis=1)))
    att = np.maximum(0, np.diff(e, prepend=e[0]))
    a0 = att - att.mean()
    ac = np.correlate(a0, a0, "full")[n - 1:]
    lo, hi = int(60 / 180 * 100), int(60 / 70 * 100)
    lag = lo + int(np.argmax(ac[lo:hi]))
    phase = int(np.argmax([a0[p::lag].sum() for p in range(lag)]))
    grille = [(phase + k * lag) / 100 for k in range(0, n // lag + 1)]
    # strongest impact (energy jump over 0.5 s windows)
    w = 50
    m = len(e) // w
    db = e[: m * w].reshape(m, w).mean(axis=1)
    return grille, att, db


def impact_musique(f, entre=(8.0, 20.0)):
    _, _, db = tempo(f)
    saut = np.diff(db)
    i0, i1 = int(entre[0] * 2), int(entre[1] * 2)
    k = i0 + int(np.argmax(saut[i0:i1]))
    return (k + 1) * 0.5


def chemin_plan(cle, fmt, lang, hud=None):
    groupe, nom = cle.split("/")
    src_fmt = "16x9" if (hud is not None and hud.get("vertical_par_recadrage")) else fmt
    v = CHOIX.get(f"{cle}-{src_fmt}", CHOIX.get(cle, "v1"))
    f = TRAVAIL / "plans" / groupe / f"{nom}-{src_fmt}-{v}.mp4"
    if not f.exists():
        raise SystemExit(f"plan absent : {f}")
    if hud is not None:
        out = f.with_name(f"{f.stem}-hud-{lang}-{fmt}.mp4")
        if not out.exists() or out.stat().st_mtime < max(f.stat().st_mtime, (ICI / "films.py").stat().st_mtime, (ICI / "outils" / "hud.py").stat().st_mtime):
            args = [sys.executable, str(ICI / "outils" / "hud.py"), str(f), str(out), "--lang", lang,
                    "--debut", str(hud.get("debut", 0.5)), "--alerte", str(hud.get("alerte", 99)), "--camera", hud.get("camera", "CAM 04")]
            if hud.get("cles"):
                args += ["--cles", hud["cles"]]
            elif hud.get("cible"):
                args += ["--cible", ",".join(map(str, hud["cible"]))]
            if fmt == "9x16" and src_fmt == "16x9":
                args += ["--recadre", str(hud["recadre"])]
            subprocess.run(args, check=True, capture_output=True)
        f = out
    return f


def construire(film, lang, fmt, sortie):
    F = FILMS[film]
    vertical = fmt == "9x16"
    mus = TRAVAIL / "musique" / CHOIX.get(f"musique-{film}", f"{F['musique']}-v1.flac")
    beats = F["beats"]
    # Music: its main impact lands on the cut of beat F["impact"] (pre-impact beats stretched or squeezed to fit).
    ti = impact_musique(mus, F.get("impact_entre", (8.0, 20.0))) if F.get("impact") is not None else None
    durs = [b["d"] for b in beats]
    mus_debut = 0.0
    if ti is not None:
        k = F["impact"]
        avant = sum(durs[:k])
        cible = min(max(ti, avant * 0.8), avant * 1.25)
        durs[:k] = [d * cible / avant for d in durs[:k]]
        mus_debut = max(0.0, ti - cible)
    segs, textes, sfx = [], [], []
    t = 0.0
    for b, d in zip(beats, durs):
        f = chemin_plan(b["plan"], fmt, lang, b.get("hud"))
        fondu = b.get("fondu", 0.0) if segs else 0.0
        s = {"plan": str(f), "debut": b.get("src", 0.3), "duree": round(d + fondu, 3), "fondu": fondu, "zoom": b.get("z", 0.03),
             "vitesse": b.get("v", 1.0)}
        if vertical and "cadre_x" in b:
            s["cadre_x"] = b["cadre_x"]
        segs.append(s)
        tx = b.get(lang)
        if tx:
            st = b.get("style", "titre")
            txt = {"texte": tx if (vertical or b.get("lignes16")) else tx.replace("\n", " "),
                   "debut": round(t + b.get("t_txt", 0.35), 3), "duree": round(d - b.get("t_txt", 0.35) - 0.25 + b.get("txt_plus", 0), 3),
                   "style": st}
            if st == "invite":
                txt.update({"frappe": b.get("frappe", 26), "taille": 0.026 if not vertical else 0.019,
                            "position": 0.86 if not vertical else 0.80, "alignement": "gauche"})
            else:
                txt.update({"taille": b.get("taille", 0.064) * (0.6 if vertical else 1.0),
                            "position": b.get("pos", 0.80 if not vertical else 0.72)})
                if vertical:
                    txt["largeur_max"] = 0.86
                if not vertical and b.get("droite"):
                    txt["alignement"] = "droite"
                elif not vertical and b.get("gauche", True):
                    txt["alignement"] = "gauche"
            if b.get("accent", {}).get(lang):
                txt["accent"] = b["accent"][lang]
            textes.append(txt)
        for x in b.get("sfx", []):
            sfx.append({**x, "t": round(t + x.get("dt", 0.0), 3)})
        t += d
    # end card
    carton = TRAVAIL / "montage" / f"carton-{film}-{lang}-{fmt}.mp4"
    if not carton.exists() or carton.stat().st_mtime < (ICI / "marque.json").stat().st_mtime:
        carton.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run([sys.executable, str(ICI / "outils" / "carton_signal.py"), str(carton), "--format", FORMATS[fmt],
                        "--lang", lang, "--etiquette", F["etiquette"][lang], "--duree", "5.5"], check=True)
    segs.append({"carton": str(carton), "duree": 5.5, "fondu": 0.5})
    t_carton = t - 0.5
    sfx += [{"type": "whoosh", "t": round(t_carton - 0.3, 3), "duree": 1.0, "db": -16},
            {"type": "tick", "t": round(t_carton + 1.05, 3), "duree": 0.3, "db": -20}]
    if ti is not None:
        ki = sum(durs[:F["impact"]])
        sfx += [{"type": "riser", "t": round(max(0.0, ki - 2.4), 3), "duree": 2.4, "db": -15},
                {"type": "boom", "t": round(ki, 3), "duree": 2.0, "db": -6}]
    total = t + 5.0
    return {
        "sortie": str(sortie), "format": FORMATS[fmt], "ips": 24, "ambiance_db": F.get("ambiance_db", -16),
        "musique": {"fichier": str(mus), "debut": round(mus_debut, 3), "db": F.get("musique_db", -1), "fondu_fin": 1.4},
        "segments": segs, "textes": textes, "sfx": sfx, "noir_debut": 0.6, "noir_fin": 0.8,
        "degrade": {"bas": 0.62, "haut": 0.25, "hauteur": 0.45},
        "_duree_prevue_s": round(total, 2), "_impact_musique_s": ti,
    }


if __name__ == "__main__":
    film, lang, fmt = sys.argv[1], sys.argv[2], sys.argv[3]
    rapide = "--rapide" in sys.argv
    nom = f"film-{film}-{lang}-{fmt}"
    (LIVRE / "masters").mkdir(parents=True, exist_ok=True)
    sortie = (TRAVAIL / "montage" / f"{nom}-apercu.mp4") if rapide else (LIVRE / "masters" / f"{nom}-master.mp4")
    spec = construire(film, lang, fmt, sortie)
    js = ICI / "montages" / f"{nom}.json"
    js.parent.mkdir(exist_ok=True)
    js.write_text(json.dumps(spec, indent=1, ensure_ascii=False))
    subprocess.run([sys.executable, str(ICI / "outils" / "film_signal.py"), str(js), *(["--rapide"] if rapide else [])], check=True)
    if not rapide and "--sans-export" not in sys.argv:
        F = FILMS[film]
        exporter.exporter_video(str(sortie), nom, F["role"], lang, poster_t=F.get("poster_t"), cible_mo=24 if fmt == "16x9" else 16,
                                extra={"montage": f"marketing/nexora/refonte-medias/montages/{nom}.json",
                                       "master": f"masters/{nom}-master.mp4",
                                       "plans_h3": "prompts dans marketing/nexora/refonte-medias/plans.py (groupes " + ", ".join(sorted({b['plan'].split('/')[0] for b in F['beats']})) + ")",
                                       "musique": "MiniMax-Music3, description dans marketing/nexora/refonte-medias/musiques.py"})
