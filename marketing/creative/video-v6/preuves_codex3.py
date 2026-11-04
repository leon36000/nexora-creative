#!/usr/bin/env python3
"""Huit preuves CPU des segments 2, 3, 26, 32 ; seuls les MP4 sont conservés.

V6_CACHE=… python3 -B marketing/creative/video-v6/preuves_codex3.py
"""
import json
import argparse
import sys
import tempfile
from pathlib import Path

sys.dont_write_bytecode = True
import monter_v6 as v


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cache-local", action="store_true", help="repli explicite dans video-v6/.cache/codex3 si V6_CACHE est en lecture seule")
    parser.add_argument("--segments", nargs="+", type=int, choices=(2, 3, 26, 32), default=[2, 3, 26, 32])
    args = parser.parse_args()
    if args.cache_local:
        v.CACHE = v.ICI/".cache"/"codex3"
    origine = v.ICI/"montage-v6.json"
    montage = v.resoudre(json.loads(origine.read_text()), origine.parent)
    montage["marque"] = str(v.chemin(montage["marque"], origine.parent))
    montage["dossiers_voix"] = {k: str(v.chemin(p, origine.parent))
                                for k, p in montage.get("dossiers_voix", {}).items()}
    v.CACHE.mkdir(parents=True, exist_ok=True)
    avant = set((v.CACHE/"segments").glob("*.mp4"))
    mesures = []
    rapports = []
    try:
        with tempfile.TemporaryDirectory(prefix="codex3-", dir=v.CACHE) as travail:
            for numero in args.segments:
                s = montage["segments"][numero-1]
                attendu = {2: "saisie", 3: "boost", 26: "chapitre", 32: "boost"}[numero]
                def correspond(s):
                    return (s["type"] == attendu and
                            (numero != 26 or s.get("texte_id") == "ch_relief") and
                            (numero != 32 or len(s.get("texte", "")) > 2500))
                if not correspond(s):
                    candidats = [(i, x) for i, x in enumerate(montage["segments"], 1) if correspond(x)]
                    if len(candidats) != 1:
                        raise ValueError(f"La scène s{numero} a changé : correspondance unique requise")
                    index, s = candidats[0]
                    print(f"Scène de référence s{numero} retrouvée au segment {index}", flush=True)
                copie = dict(montage, segments=[s], duree=s["debut"]+s["duree"])
                fichier = Path(travail)/f"segment-{numero}.json"
                fichier.write_text(json.dumps(copie, ensure_ascii=False))
                for fmt in ("16x9", "9x16"):
                    sortie = v.CACHE/"essais"/f"codex3-{s['type']}-s{numero:02d}-{fmt}-fr.mp4"
                    rapports.append(sortie.with_suffix(".rendu.json"))
                    argv = [str(fichier), "--format", fmt, "--langue", "fr", "--sortie", str(sortie),
                            "--master", "web", "--jobs", "1", "--de", str(s["debut"]),
                            "--a", str(s["debut"]+s["duree"])]
                    if fmt == "9x16":
                        argv.append("--brouillon")
                    r = v.construire(v.parser().parse_args(argv))
                    mesures.append({k: r[k] for k in ("film", "duree", "images", "temps_rendu_s", "loudness_aac")})
    finally:
        for p in rapports:
            p.unlink(missing_ok=True)
        for p in set((v.CACHE/"segments").glob("*.mp4"))-avant:
            p.unlink(missing_ok=True)
    print("PREUVES_CODEX3="+json.dumps(mesures, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
