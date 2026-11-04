"""Repli d'écriture pour une équipe dont l'agent outillé ne passe pas par la passerelle (04/11 : Muse renvoie « reasoning_effort
et reasoning.effort en conflit » derrière Claude Code). Même brief, mêmes fichiers, même budget : on envoie tout le dossier de
travail au modèle (OpenRouter, effort de raisonnement demandé) et il rend DOSSIER.md et dossier.json ; si le JSON est invalide, il
reçoit l'erreur et corrige (3 tours au plus, comme un agent qui relit son travail).
  python3 ecriture_directe.py <dossier-de-travail> <equipe> <modèle OpenRouter> <effort>
"""
import json
import re
import sys
import urllib.request
from pathlib import Path

W, EQ, MODELE, EFFORT = Path(sys.argv[1]), sys.argv[2], sys.argv[3], sys.argv[4]
FICHIERS = ["PROMPT.md", "equipes/deepseek/fabrique.py", "BRIEF-V7.md", "README-montage.md", "exemple-montage.json", "marque-v7.json", "captures-disponibles.md",
            "voix/PALETTE.md", "recette/recette_live.py", "recette/mesures-cles.json"]


import os
BASE = os.environ.get("V7_BASE", "https://openrouter.ai/api/v1")


def cle():
    if os.environ.get("V7_CLE_FICHIER"):
        return Path(os.environ["V7_CLE_FICHIER"]).expanduser().read_text().strip()
    for l in open(Path.home() / "Desktop/Deepinfra.env"):
        if ":" in l and l.split(":", 1)[0].strip().lower() == os.environ.get("V7_CLE_NOM", "openrouter"):
            return l.split(":", 1)[1].strip()


def appel(messages):
    corps = {"model": MODELE, "messages": messages, "max_tokens": 60000}
    if EFFORT.startswith("re:"):  # fournisseur au format OpenAI (DeepInfra) : reasoning_effort
        corps["reasoning_effort"] = EFFORT[3:]
    elif EFFORT != "passerelle":  # la passerelle des sous-agents règle elle-même l'effort
        corps["reasoning"] = {"effort": EFFORT}
    r = urllib.request.Request(BASE + "/chat/completions", data=json.dumps(corps).encode(),
                               headers={"Authorization": "Bearer " + cle(), "Content-Type": "application/json"})
    with urllib.request.urlopen(r, timeout=1800) as x:
        j = json.loads(x.read())
    return j["choices"][0]["message"]["content"], j.get("usage", {}).get("cost")


contexte = "\n\n".join(f"===== FICHIER {f} =====\n{(W / f).read_text()}" for f in FICHIERS if (W / f).exists())
consigne = (f"{contexte}\n\n===== CONSIGNE DE RENDU =====\nTu n'as pas d'outils : rends tout dans ta réponse, dans cet ordre et avec ces "
            f"balises exactes : <DOSSIER_MD> … </DOSSIER_MD> puis <DOSSIER_JSON> … </DOSSIER_JSON> (JSON strict, sans commentaire), puis "
            f"<TEXTES_JSON> … </TEXTES_JSON> (tes textes à l'écran, format {{\"fr\": {{}}, \"en\": {{}}}}). Calcule toi-même les temps.")
msgs = [{"role": "user", "content": consigne}]
cout_total = 0.0
for tour in range(3):
    rep, cout = appel(msgs)
    cout_total += cout or 0
    blocs = {k: (re.search(rf"<{k}>(.*?)</{k}>", rep, re.S) or [None, None])[1] for k in ("DOSSIER_MD", "DOSSIER_JSON", "TEXTES_JSON")}
    erreur = None
    try:
        d = json.loads(blocs["DOSSIER_JSON"].strip().strip("`").removeprefix("json"))
        t = json.loads(blocs["TEXTES_JSON"].strip().strip("`").removeprefix("json")) if blocs["TEXTES_JSON"] else {"fr": {}, "en": {}}
    except Exception as e:
        erreur = f"JSON invalide ou balise absente : {e}"
    if not erreur:
        out = W / "equipes" / EQ
        out.mkdir(parents=True, exist_ok=True)
        (out / "DOSSIER.md").write_text(blocs["DOSSIER_MD"].strip() + "\n")
        (out / "dossier.json").write_text(json.dumps(d, ensure_ascii=False, indent=1))
        (out / "textes.json").write_text(json.dumps(t, ensure_ascii=False, indent=1))
        print(json.dumps({"equipe": EQ, "tours": tour + 1, "cout_usd": round(cout_total, 4)}))
        break
    msgs += [{"role": "assistant", "content": rep}, {"role": "user", "content": erreur + " Corrige et rends à nouveau les trois blocs complets."}]
else:
    print(json.dumps({"equipe": EQ, "echec": erreur, "cout_usd": round(cout_total, 4)}))
