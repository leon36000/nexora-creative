"""Terminal « filmé en code » du film Modèles et API : images (JPEG 1400×1400) d'un appel d'API tapé puis de sa réponse en continu,
puis du même appel où seule la ligne « model » change. Le texte de l'appel est celui de l'exemple de la page /modeles du site
(clé et modèles fictifs, réponse figurée) ; l'adresse est remplacée par un exemple neutre et la clé est masquée.
Usage : python3 terminal.py <dossier>     écrit NNNN-t1.jpg (appel + réponse) et NNNN-t2.jpg (changement de modèle), 15 images/s.
"""
import json
import re
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

MARQUE = json.loads((Path(__file__).resolve().parents[2] / "marque.json").read_text())
POL = Path(MARQUE["polices"]["dossier"]).expanduser() / MARQUE["polices"]["mono"]
C = {k: tuple(v) for k, v in MARQUE["couleurs"].items()}
FOND, S, SH = (13, 13, 17), 1400, 1400
TAILLE, PAS = 34, 50
IPS = 15
POLICE = ImageFont.truetype(str(POL), TAILLE)
try:
    POLICE.set_variation_by_name("Medium")
except Exception:
    pass
CW = POLICE.getlength("M")
X0, Y0 = 150, 330

CMD = ['$ curl https://api.exemple.ca/v1/chat/completions \\',
       '  -H "Authorization: Bearer nxk_••••••••" \\',
       "  -d '{",
       '    "model": "{MODELE}",',
       '    "messages": [{"role": "user",',
       '      "content": "Bonjour !"}],',
       '    "stream": true',
       "  }'"]
REP = ['data: {"choices":[{"delta":{"content":', '"Bonjour ! Comment puis-je vous aider ?"', "}}]}"]
ANCIEN, NOUVEAU = "nexora/nom-du-modele", "nexora/autre-modele"


def couleur(tok, ligne_rep=False):
    if ligne_rep:
        return C["signal"] if tok.startswith('"Bonjour') else C["os"]
    if tok.startswith(('"nexora/')):
        return C["signal"]
    if tok.startswith('"') and tok.endswith('"') and ":" not in tok:
        return C["os"]
    return C["brume"] if re.match(r"^\s*(-[a-zA-Z]|\$)", tok) else C["os"]


def ligne(d, y, txt, n, rep=False, cursor=False):
    """Trace les n premiers caractères de txt (jetons colorés) ; renvoie x de fin."""
    x = X0
    reste = n
    for tok in re.findall(r'"[^"]*"|nxk_•+|\s+|[^"\s]+', txt):
        if reste <= 0:
            break
        part = tok[:reste]
        reste -= len(part)
        d.text((x, y), part, font=POLICE, fill=couleur(tok, rep) if not tok.startswith("nxk_") else C["brume"])
        x += CW * len(part)
    if cursor:
        d.rectangle([x + 2, y + 4, x + CW * 0.75, y + TAILLE + 4], fill=C["os"])
    return x


def image(lignes, selection=None, marqueur=None, curseur=None):
    """lignes : [(texte, n_caractères, est_réponse)] ; selection : (indice_ligne, c0, c1) surbrillance ; marqueur : indice de ligne
    avec barre d'accent à gauche ; curseur : indice de ligne où poser le curseur de saisie."""
    im = Image.new("RGB", (S, SH), FOND)
    d = ImageDraw.Draw(im, "RGBA")
    for i, (txt, n, rep) in enumerate(lignes):
        y = Y0 + i * PAS
        if marqueur == i:
            d.rectangle([X0 - 40, y - 4, S - X0 + 20, y + PAS - 8], fill=(*C["signal"], 34))
            d.rectangle([X0 - 40, y - 4, X0 - 34, y + PAS - 8], fill=C["signal"])
        if selection and selection[0] == i:
            d.rectangle([X0 + CW * selection[1], y - 2, X0 + CW * selection[2], y + PAS - 10], fill=(*C["signal"], 110))
        ligne(d, y, txt, n, rep, cursor=(curseur == i))
    return im


MODEL_IDX = 3


def etat_cmd(modele):
    return [t.replace("{MODELE}", modele) for t in CMD]


def t1(k, n):
    """Image k sur n : saisie de l'appel (0,25 → 1,9 s), Entrée (2,0 s), réponse en continu (2,5 → 4,0 s)."""
    t = k / IPS
    cmd = etat_cmd(ANCIEN)
    total = sum(len(l) for l in cmd)
    typed = int(total * min(1, max(0, (t - 0.25) / 1.65)))
    lignes, reste = [], typed
    for l in cmd:
        m = min(len(l), max(0, reste))
        lignes.append((l, m, False))
        reste -= len(l)
    cur = next((i for i, (l, m, _) in enumerate(lignes) if m < len(l)), len(lignes) - 1)
    if t > 1.95:
        cur = None
        nrep = sum(len(x) for x in REP)
        shown = int(nrep * min(1, max(0, (t - 2.45) / 1.5)))
        for x in REP:
            m = min(len(x), max(0, shown))
            lignes.append((x, m, True))
            shown -= len(x)
        lignes.insert(len(cmd), ("", 0, False))
        lignes = lignes[: len(cmd)] + [("", 0, False)] + [l for l in lignes[len(cmd) + 1:]]
        cur = None if t > 2.2 else None
    else:
        cur = cur if int(t * 2.2) % 2 == 0 or t < 1.9 else None
    return image(lignes, curseur=cur)


def t2(k, n):
    """Même appel : la valeur de « model » est sélectionnée (0,5 s), retapée (1,0 → 1,8 s), l'appel repart (2,3 s), la réponse revient."""
    t = k / IPS
    modele = ANCIEN
    selection = None
    marqueur = None
    if 0.5 <= t < 1.0:
        selection = (MODEL_IDX, len('    "model": "'), len('    "model": "') + len(ANCIEN))
        marqueur = MODEL_IDX
    elif t >= 1.0:
        c = int(len(NOUVEAU) * min(1, (t - 1.0) / 0.8))
        modele = NOUVEAU[:c]
        marqueur = MODEL_IDX
    cmd = etat_cmd(modele)
    lignes = [(l, len(l), False) for l in cmd]
    if t >= 2.3:
        nrep = sum(len(x) for x in REP)
        shown = int(nrep * min(1, (t - 2.3) / 1.3))
        lignes.append(("", 0, False))
        for x in REP:
            lignes.append((x, min(len(x), max(0, shown)), True))
            shown -= len(x)
    return image(lignes, selection=selection, marqueur=marqueur, curseur=MODEL_IDX if 1.0 <= t < 1.85 else None)


VERTICAL = ['$ curl \\', '  https://api.exemple.ca/v1/chat/completions \\', '  -H "Authorization: Bearer nxk_••••••••" \\',
            "  -d '{", '    "model": "{MODELE}",', '    "messages": [{"role": "user",', '      "content": "Bonjour !"}],',
            '    "stream": true', "  }'"]


def variante_verticale():
    """Version 9:16 : colonne étroite (45 caractères), corps 36 px, image 1100×1126 (carte presque carrée)."""
    global S, SH, TAILLE, PAS, X0, Y0, CMD, MODEL_IDX, POLICE, CW
    S, SH, TAILLE, PAS, X0, Y0, MODEL_IDX = 1100, 1126, 36, 50, 50, 250, 4
    CMD = VERTICAL
    POLICE = ImageFont.truetype(str(POL), TAILLE)
    try:
        POLICE.set_variation_by_name("Medium")
    except Exception:
        pass
    CW = POLICE.getlength("M")


if __name__ == "__main__":
    out = Path(sys.argv[1])
    out.mkdir(parents=True, exist_ok=True)
    for suffixe in ("", "v"):
        if suffixe:
            variante_verticale()
        for nom, fn, d, base in (("t1", t1, 4.6875, 100), ("t2", t2, 3.75, 200)):
            n = round(d * IPS) + 1
            for k in range(n):
                fn(k, n).save(out / f"{base + k:04d}-{nom}{suffixe}.jpg", quality=90)
            print(nom + suffixe, n, "images")
