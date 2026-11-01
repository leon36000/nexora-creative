"""Construit les livrables d'un ou plusieurs objets.  python build.py tshirt tasse ...   (sans argument : tous)
Ecrit final/NN-slug/NN-slug-fabrication.{svg,pdf} et NN-slug-maquette.jpg (2400 px)."""
import sys, importlib, traceback
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from fab import *
from mock import sauver
MODULES = ["o_textile", "o_boisson", "o_papeterie", "o_accessoires", "o_boutique", "o_emballage", "o_idees"]


def registre():
    out = []
    for m in MODULES:
        try:
            out += importlib.import_module(m).OBJETS
        except ModuleNotFoundError as e:
            if e.name != m: raise
    return sorted(out, key=lambda t: t[0]["num"])


def construire(o, gab, maq, fab=True, mock=True, gab_en=None):
    nom = f"{o['num']:02d}-{o['slug']}"
    d = FINAL / nom
    if fab:
        ecrire_fabrication(o, gab(), d); print(nom, "fabrication ok", flush=True)
        if gab_en:
            ecrire_fabrication(o, gab_en(), d, "-en"); print(nom, "fabrication -en ok", flush=True)
    if mock:
        res = maq()
        vues = res if isinstance(res, dict) else {"": res}
        for suf, im in vues.items():
            sauver(im, d / f"{nom}-maquette{("-" + suf) if suf else ""}.jpg")
            print(nom, "maquette", suf, "ok", flush=True)


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    fab, mock = "--sans-fab" not in sys.argv, "--sans-maquette" not in sys.argv
    for o, gab, maq, *en in registre():
        if args and o["slug"] not in args: continue
        try:
            construire(o, gab, maq, fab, mock, en[0] if en else None)
        except Exception:
            print(o["slug"], "ECHEC"); traceback.print_exc()
