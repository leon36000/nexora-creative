"""Construit la palette commune de voix (casting/palette.json + casting/PALETTE.md) à partir du banc (casting/banc.json).
Une entrée de palette = un moteur + une voix, avec ses notes moyennes (oreille de machine), ses mesures et ses échantillons."""
import json
from collections import defaultdict
from pathlib import Path

ICI = Path(__file__).resolve().parent
RACINE = ICI.parent
TRAVAIL = Path.home() / "nexora-creative-data/work/opsys-ultime"
DESCR = {
    "frederic": ("homme", "Frédéric, voix québécoise d'âge moyen, « professionnelle et assurée » (bibliothèque ElevenLabs)"),
    "adamqc": ("homme", "Adam, voix québécoise d'âge moyen, « chaleureuse et amicale »"),
    "alexandre": ("homme", "Alexandre Boutin, voix des films V5 (jugée « beaucoup trop smooth » par le fondateur)"),
    "thomas": ("homme", "Thomas, jeune voix « claire, chaleureuse, professionnelle » (accent peu québécois à l'oreille de machine)"),
    "marieline": ("femme", "Marie Line, voix québécoise d'âge moyen, « énergique et claire »"),
    "jeannemance": ("femme", "Jeanne Mance, voix québécoise, « charmante, claire et jeune »"),
    "amelie": ("femme", "Amélie, voix québécoise, « jeune, assurée, amicale »"),
}
VOIX_ID = {"thomas": "4FLkNETtL5THnClfpjpb", "frederic": "oziFLKtaxVDHQAh7o45V", "adamqc": "93nuHbke4dTER9x2pDwE",
           "alexandre": "IPgYtHTNLjC7Bq7IPHrm", "marieline": "u5l0VNCfzO5oqrKTuA1e", "jeannemance": "K7gx0ylJdff0yjM2uVQS",
           "amelie": "UJCi4DDncuo0VJDSIegj"}
MOTEUR = {"eleven": "ElevenLabs v4 (OpenRouter)", "drama3": "Fish Audio Drama 3 (clonage de la voix ElevenLabs, OpenRouter ; même modèle en local GB10/5090)",
          "qwen3tts": "Qwen3-TTS 1.7B, local GB10 (clonage, apache-2.0)"}


def main():
    banc = json.loads((TRAVAIL / "casting" / "banc.json").read_text())
    groupes = defaultdict(list)
    for p in banc["prises"]:
        groupes[p["moteur_court"]].append(p)
    b2 = TRAVAIL / "casting" / "banc2.json"
    if b2.exists():  # manche 2 (04/11) : moteurs OpenRouter génériques « or:<modèle>|voice=…|ref=… »
        for p in json.loads(b2.read_text())["prises"]:
            groupes[p["moteur_court"]].append(p)
    pal, lignes = {}, []
    for mc, ps in sorted(groupes.items()):
        fam, _, v = mc.partition(":")
        genre, descr = DESCR.get(v, ("?", v))
        if fam == "or":
            champs = dict(c.partition("=")[::2] for c in v.split("|")[1:])
            modele = v.split("|")[0]
            court = {"mistralai/voxtral-mini-tts-3-0": "voxtral3", "mistralai/voxtral-mini-tts-2603": "voxtral2603", "fish-audio/s2.1-pro": "fish21",
                     "minimax/speech-2.8-hd": "minimax28", "microsoft/mai-voice-2.1": "mai21"}.get(modele, modele.split("/")[-1])
            nomv = champs.get("voice") or champs.get("ref") or "defaut"
            ident = f"{court}-{nomv.replace('Neural', '').replace('voice_', 'v').lower()}"
            fem = any(x in nomv.lower() for x in ("sylvie", "denise", "female", "marie", "jeanne", "amelie", "v592", "v3137", "v589", "v3141", "voice_"))
            genre = "femme" if fem and "frederic" not in nomv and "JeanNeural" not in nomv else "homme"
            descr = {"voxtral3": "Mistral Voxtral TTS 3, voix préréglée française", "voxtral2603": "Mistral Voxtral Mini TTS (2603), voix préréglée",
                     "fish21": f"Fish S2.1 Pro, clonage de {nomv}", "minimax28": f"MiniMax Speech 2.8 HD, voix {nomv}",
                     "mai21": f"MAI-Voice-2.1 (Microsoft), voix {nomv}" + (" — canadienne-française" if "fr-CA" in nomv else "")}.get(court, mc)
            MOTEUR.setdefault("or", "OpenRouter (manche 2)")
            fam_aff = {"voxtral3": "Mistral Voxtral 3", "voxtral2603": "Mistral Voxtral 2603", "fish21": "Fish S2.1 Pro", "minimax28": "MiniMax Speech 2.8 HD",
                       "mai21": "MAI-Voice-2.1"}.get(court, court)
        notes = defaultdict(list)
        for p in ps:
            for k, x in ((p.get("oreille") or {}).get("moyennes") or {}).items():
                notes[k].append(x)
        moy = {k: round(sum(x) / len(x), 1) for k, x in notes.items()}
        if fam != "or":
            ident = f"{fam}-{v}"
            fam_aff = MOTEUR[fam]
        moteur = f"eleven:{VOIX_ID[v]}" if fam == "eleven" else mc
        pal[ident] = {"moteur": moteur, "famille": fam_aff, "genre": genre, "description": descr, "manche": 2 if fam == "or" else 1,
                      "local": fam == "qwen3tts", "notes": moy,
                      "emr_moyen": round(sum(p.get("emr", 0) for p in ps) / len(ps), 3),
                      "cps_moyen": round(sum(p.get("cps", 0) for p in ps) / len(ps), 1),
                      "relief_demitons": round(sum(p.get("relief_demitons", 0) for p in ps) / len(ps), 2),
                      "direction": ps[0].get("direction", ""), "vitesse": ps[0].get("vitesse", 1.0),
                      "echantillons": {p["role"]: p["fichier"] for p in ps},
                      "commentaires": [c.get("commentaire") for p in ps for c in (p.get("oreille") or {}).get("passes", []) if c.get("commentaire")][:3]}
        lignes.append(ident)
    (RACINE / "casting").mkdir(exist_ok=True)
    (RACINE / "casting" / "palette.json").write_text(json.dumps({"voix": pal}, ensure_ascii=False, indent=1))
    t = ["# Palette commune de voix (manche 1 du 03/11 et manche 2 du 04/11, mêmes répliques pour tous)", "",
         "Manche 2 (consigne du fondateur du 04/11) : Mistral Voxtral TTS 3 et 2603 (voix préréglées françaises : OpenRouter refuse le clonage",
         "pour ces modèles), MiniMax Speech 2.8 HD, MAI-Voice-2.1 (voix canadiennes-françaises fr-CA Sylvie, Antoine, Thierry, Jean) et Fish S2.1 Pro",
         "(clonage). Aucune ne dépasse les meilleures de la manche 1 à l'oreille de machine ; les voix fr-CA de MAI sont québécoises mais plates.",
         "Attention : les deux manches ont été jugées à quelques heures d'écart ; l'écart de 1 point entre manches n'est pas significatif.", "",
         "Chaque équipe choisit par rôle une **voix de la palette** (colonne `id`), écrit le texte, la direction de jeu et la vitesse.",
         "Notes sur 10 de l'**oreille de machine** (Gemini 4 Argon, audio, deux passes, sévère : 8 = diffusable à la télé au Québec) ;",
         "ce n'est pas une écoute humaine. EMR = erreur de mots Whisper ; c/s = caractères par seconde (débit) ; relief = écart-type de",
         "la hauteur en demi-tons (une voix « smooth » a peu de relief).", "",
         "| id | genre | moteur | accent QC | énergie | naturel | clarté | rôle | EMR | c/s | relief | voix |",
         "|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for i in sorted(pal, key=lambda k: -sum(pal[k]["notes"].values())):
        p = pal[i]
        n = p["notes"]
        t.append(f"| `{i}` | {p['genre']} | {p['famille'].split(' (')[0]} | {n.get('accent_quebecois', '–')} | {n.get('energie', '–')} | "
                 f"{n.get('naturel', '–')} | {n.get('clarte', '–')} | {n.get('adequation_role', '–')} | {p['emr_moyen']} | {p['cps_moyen']} | "
                 f"{p['relief_demitons']} | {p['description']} |")
    t += ["", "## Avis de l'oreille de machine (extraits)", ""]
    for i in sorted(pal):
        if pal[i]["commentaires"]:
            t.append(f"- `{i}` : " + " / ".join(pal[i]["commentaires"][:2]))
    t += ["", "## Ce qu'il faut savoir", "",
          "- **Voix native de H3** (essai : l'adjointe dit sa réplique dans le plan, sans voix ancrée) : accent québécois 8,5/10 à l'oreille, mais",
          "  **erreur de lecture** (« 16 h » dit « 6 h ») et naturel 6,5 : non fiable pour un texte exact. La chaîne ancre donc toujours une prise",
          "  de la palette dans les plans parlants (lèvres synchronisées sur cette voix).",
          "- Drama 3 garde l'accent de la voix clonée quand la référence est très québécoise (Frédéric, Jeanne Mance), le perd parfois (Thomas, Amélie).",
          "  Il accepte une consigne de jeu en langage naturel (`direction`) et `vitesse` (1,0 à 1,3 sans erreur de mots mesurée). Il tourne aussi en",
          "  local (GB10 FP8, RTF 0,83 ; 5090 int4, RTF 0,12, mais la 5090 est prise par H3).",
          "- ElevenLabs v4 : balises de jeu entre crochets dans `direction` (« [energetic, punchy] »), vitesse non garantie (réglée au montage).",
          "- Qwen3-TTS : local, licence permissive, pas de consigne de jeu (le jeu vient de la référence clonée).",
          "- Échantillons (fichiers .wav) : `~/nexora-creative-data/work/opsys-ultime/casting/voix/` sur pc6 ; copie sur pc1.", ""]
    (RACINE / "casting" / "PALETTE.md").write_text("\n".join(t))
    print("\n".join(t[:40]))


if __name__ == "__main__":
    main()
