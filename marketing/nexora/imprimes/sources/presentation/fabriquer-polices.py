"""Convertit les polices libres (woff2 variables) en TTF statiques installables pour PowerPoint/LibreOffice.
Utilise fontTools + brotli (pip install fonttools brotli). Sortie : final/presentation/polices-a-installer/
Geist 500 -> famille « Geist Medium » ; Inter 400 -> « Inter » ; JetBrains Mono 500 -> « JetBrains Mono Medium »."""
import sys, pathlib
from fontTools.ttLib import TTFont
from fontTools.varLib import instancer
P = pathlib.Path(__file__).resolve().parents[3] / "identite/sources/polices"
OUT = pathlib.Path(__file__).resolve().parents[2] / "final/presentation/polices-a-installer"
OUT.mkdir(parents=True, exist_ok=True)
def faire(src, wght, famille, nomfichier):
    f = TTFont(P / src); f.flavor = None
    g = instancer.instantiateVariableFont(f, {"wght": wght}, inplace=False)
    n = g["name"]
    for rec in list(n.names):
        if rec.nameID in (16, 17, 21, 22, 25): n.removeNames(nameID=rec.nameID)
    for nid, val in ((1, famille), (2, "Regular"), (3, famille + " Regular"), (4, famille), (6, famille.replace(" ", "") + "-Regular")):
        n.setName(val, nid, 3, 1, 0x409); n.setName(val, nid, 1, 0, 0)
    g["OS/2"].usWeightClass = 400; g["OS/2"].fsSelection = (g["OS/2"].fsSelection & ~0x21) | 0x40
    g["head"].macStyle = 0
    g.save(OUT / nomfichier); print(nomfichier)
faire("geist-latin-wght-normal.woff2", 500, "Geist Medium", "GeistMedium.ttf")
faire("inter-latin-wght-normal.woff2", 400, "Inter", "Inter-Regular.ttf")
faire("jetbrains-mono-latin-wght-normal.woff2", 500, "JetBrains Mono Medium", "JetBrainsMono-Medium.ttf")
