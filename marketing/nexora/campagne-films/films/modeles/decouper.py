"""Film « Modèles et API » : du flux d'images brut (capturer.mjs) aux séquences à 30 images/s par segment (liens symboliques, aucun
doublon sur le disque), et aux courbes de curseur recalées sur le temps du segment.
  python3 decouper.py <dossier-travail>        → <travail>/ui/<langue>-NNNN-<étiquette>.jpg, <travail>/ui/sections.json
Une « section » = une plage du parcours réel (repères du journal) ; plusieurs plages bout à bout forment une étiquette (coupes
invisibles : même état de page de part et d'autre). Les temps du curseur sont donnés en secondes depuis le début de l'étiquette."""
import json
import os
import sys
from pathlib import Path

FPS = 30
# étiquette → [(repère de début, décalage s, repère de fin, décalage s), ...]   (le repère « _ » = début de la plage suivante)
SECTIONS = {
    "hero": [("hero", -0.15, "cat", -0.45)],                       # chargement, réponse en continu, clic « Parcourir », défilement
    "cat": [("cat", -0.45, "c_fin", 0.0), ("c_res2", 0.12, "tape", -0.5)],  # 36 modèles → pastille Code → 25
    "rech": [("tape", -0.5, "tape_fin", 0.3), ("q_res", 0.12, "t_go", 0.0), ("t_res", 0.12, "f_go", -0.5)],  # recherche, 5 modèles, tri, résultat
    "fiche": [("f_res", 0.1, "defile_bench", 0.0)],                # fiche ouverte : prix d'entrée et de sortie
    "bench": [("defile_bench", 0.0, "defile_api", -0.3)],          # défilement vers les mesures publiées, avec leur source
    "api": [("defile_api", 0.0, "fin", 0.0)],                      # exemple d'appel, étiquette d'aperçu, clic « Copier »
}


def lire(rep):
    ims = [json.loads(l) for l in (rep / "frames.jsonl").read_text().splitlines() if l]
    jo = [json.loads(l) for l in (rep / "journal.jsonl").read_text().splitlines() if l]
    marques = {}
    for j in jo:
        for k in ("marque",):
            if k in j:
                marques.setdefault(j[k], j["t"])
    return ims, jo, marques


def principal(brut, ui):
    sortie = {}
    ui.mkdir(parents=True, exist_ok=True)
    for f in ui.glob("*.jpg"):
        f.unlink()
    for lg in ("fr", "en"):
        rep = brut / lg
        if not (rep / "frames.jsonl").exists():
            continue
        ims, jo, marques = lire(rep)
        ts = [x["t"] for x in ims]
        sortie[lg] = {}
        for et, plages in SECTIONS.items():
            t_rel, fichiers, trames, ns = 0.0, [], [], []
            for ip, (a, da, b, db) in enumerate(plages):
                t0, t1 = marques[a] + da, marques[b] + db
                n = int(round((t1 - t0) * FPS))
                if lg != "fr":  # même nombre d'images par plage qu'en français : les temps du curseur et des clics du brief valent pour les deux langues
                    n = sortie["fr"][et]["plages_n"][ip]
                for k in range(n):
                    t = t0 + k * (t1 - t0) / n
                    i = max(0, max(j for j in range(len(ts)) if ts[j] <= t) if ts[0] <= t else 0)
                    fichiers.append(rep / "frames" / f"{ims[i]['f']:06d}.jpg")
                trames.append((t0, t1, t_rel)); ns.append(n)
                t_rel += n / FPS
            for k, f in enumerate(fichiers):
                lien = ui / f"{lg}-{k:04d}-{et}.jpg"
                os.symlink(f, lien)
            # curseur et clics, en secondes depuis le début de l'étiquette
            def rel(t):
                for t0, t1, r in trames:
                    if t0 <= t <= t1:
                        return round(r + t - t0, 3)
                return None
            cur = [[rel(j["t"]), j["x"], j["y"]] for j in jo if "pos" in j and rel(j["t"]) is not None]
            clics = [rel(j["t"]) for j in jo if "clic" in j and rel(j["t"]) is not None]
            reperes = {m: rel(t) for m, t in marques.items() if rel(t) is not None}
            sortie[lg][et] = {"d": round(t_rel, 3), "n": len(fichiers), "curseur": cur, "clics": clics, "reperes": reperes, "plages_n": ns}
    (ui / "sections.json").write_text(json.dumps(sortie, ensure_ascii=False, indent=1))
    for lg, d in sortie.items():
        print(lg, {k: v["d"] for k, v in d.items()})


if __name__ == "__main__":
    tr = Path(sys.argv[1]).expanduser()
    principal(tr / "brut", tr / "ui")
