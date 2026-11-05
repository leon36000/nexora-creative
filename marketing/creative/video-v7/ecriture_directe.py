"""Repli d'écriture pour une équipe dont l'agent outillé ne passe pas par la passerelle (04/11 : Muse renvoie « reasoning_effort
et reasoning.effort en conflit » derrière Claude Code). Même brief, mêmes fichiers, même budget : on envoie tout le dossier de
travail au modèle (OpenRouter, effort de raisonnement demandé) et il rend DOSSIER.md et dossier.json ; si le JSON est invalide, il
reçoit l'erreur et corrige (3 tours au plus, comme un agent qui relit son travail).
  V7_API_BASE_URL=https://openrouter.ai/api/v1 V7_API_KEY=… python3 ecriture_directe.py <dossier-de-travail> <equipe> <modèle> <effort>
L'URL, le modèle passé en argument et la clé V7_API_KEY forment une configuration explicite ; aucun fichier secret n'est lu.
"""
import json
import re
import sys
import urllib.request
from pathlib import Path
from chaine.commun import api_configuration

FICHIERS = ["PROMPT.md", "equipes/deepseek/fabrique.py", "BRIEF-V7.md", "README-montage.md", "exemple-montage.json", "marque-v7.json", "captures-disponibles.md",
            "voix/PALETTE.md", "recette/recette_live.py", "recette/mesures-cles.json"]


def appel(messages, modele, effort, url, cle):
    corps = {"model": modele, "messages": messages, "max_tokens": 60000}
    if effort.startswith("re:"):  # fournisseur au format OpenAI : reasoning_effort
        corps["reasoning_effort"] = effort[3:]
    elif effort != "passerelle":  # la passerelle des sous-agents règle elle-même l'effort
        corps["reasoning"] = {"effort": effort}
    r = urllib.request.Request(url, data=json.dumps(corps).encode(),
                               headers={"Authorization": "Bearer " + cle, "Content-Type": "application/json"})
    with urllib.request.urlopen(r, timeout=1800) as x:
        j = json.loads(x.read())
    return j["choices"][0]["message"]["content"], j.get("usage", {}).get("cost")


def main(argv=None):
    argv = sys.argv[1:] if argv is None else list(argv)
    if len(argv) != 4:
        raise SystemExit('usage: ecriture_directe.py <dossier-de-travail> <equipe> <modèle> <effort>')
    w, equipe, modele, effort = Path(argv[0]), argv[1], argv[2], argv[3]
    out = w / 'equipes' / equipe
    livrables = [out / name for name in ('DOSSIER.md', 'dossier.json', 'textes.json')]
    if any(path.exists() for path in livrables):
        raise FileExistsError(f'Livrable déjà présent dans {out}; choisir une nouvelle équipe de sortie')
    url, cle = api_configuration('chat/completions', modele)
    contexte = "\n\n".join(f"===== FICHIER {f} =====\n{(w / f).read_text()}" for f in FICHIERS if (w / f).exists())
    consigne = (f"{contexte}\n\n===== CONSIGNE DE RENDU =====\nTu n'as pas d'outils : rends tout dans ta réponse, dans cet ordre et avec ces "
                f"balises exactes : <DOSSIER_MD> … </DOSSIER_MD> puis <DOSSIER_JSON> … </DOSSIER_JSON> (JSON strict, sans commentaire), puis "
                f"<TEXTES_JSON> … </TEXTES_JSON> (tes textes à l'écran, format {{\"fr\": {{}}, \"en\": {{}}}}). Calcule toi-même les temps.")
    msgs = [{"role": "user", "content": consigne}]
    cout_total = 0.0
    for tour in range(3):
        rep, cout = appel(msgs, modele, effort, url, cle)
        cout_total += cout or 0
        blocs = {k: (re.search(rf"<{k}>(.*?)</{k}>", rep, re.S) or [None, None])[1] for k in ("DOSSIER_MD", "DOSSIER_JSON", "TEXTES_JSON")}
        erreur = None
        try:
            d = json.loads(blocs["DOSSIER_JSON"].strip().strip("`").removeprefix("json"))
            t = json.loads(blocs["TEXTES_JSON"].strip().strip("`").removeprefix("json")) if blocs["TEXTES_JSON"] else {"fr": {}, "en": {}}
        except Exception as e:
            erreur = f"JSON invalide ou balise absente : {e}"
        if not erreur:
            out.mkdir(parents=True, exist_ok=True)
            contenus = [blocs['DOSSIER_MD'].strip() + '\n', json.dumps(d, ensure_ascii=False, indent=1),
                        json.dumps(t, ensure_ascii=False, indent=1)]
            for path, contenu in zip(livrables, contenus):
                with path.open('x', encoding='utf-8') as fichier:
                    fichier.write(contenu)
            print(json.dumps({"equipe": equipe, "tours": tour + 1, "cout_usd": round(cout_total, 4)}))
            return 0
        msgs += [{"role": "assistant", "content": rep}, {"role": "user", "content": erreur + " Corrige et rends à nouveau les trois blocs complets."}]
    else:
        print(json.dumps({"equipe": equipe, "echec": erreur, "cout_usd": round(cout_total, 4)}))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
