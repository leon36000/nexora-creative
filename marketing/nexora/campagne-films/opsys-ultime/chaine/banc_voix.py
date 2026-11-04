"""Banc de distribution vocale commun aux quatre équipes (une seule ronde). Écrit casting/banc.json.
1) prises de référence (ElevenLabs v4, voix québécoises de la bibliothèque publique) pour le clonage Drama 3 / Qwen3-TTS ;
2) chaque rôle lu par plusieurs moteurs ; mesures + oreille Gemini 4 Argon (2 passes)."""
import json, sys, traceback
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import voix as V

VOIX = {"thomas": "4FLkNETtL5THnClfpjpb", "frederic": "oziFLKtaxVDHQAh7o45V", "adamqc": "93nuHbke4dTER9x2pDwE",
        "alexandre": "IPgYtHTNLjC7Bq7IPHrm", "marieline": "u5l0VNCfzO5oqrKTuA1e", "jeannemance": "K7gx0ylJdff0yjM2uVQS",
        "amelie": "UJCi4DDncuo0VJDSIegj"}
REFTXT = "Bonjour! Ici, on travaille fort, mais on a du plaisir. Chaque matin, l'équipe part sur les chantiers, pis le soir, tout est prêt pour demain."
LIGNES = {
    "narrateur": "Une photo. Dix secondes. Et toute une entreprise se met au travail.",
    "adjointe": "Vous avez un rendez-vous avec monsieur Thibault à quatorze heures, et j'ai déplacé votre rendez-vous de seize heures, comme vous me l'avez demandé.",
    "comptable": "Voici les profits anticipés, mis à jour avec les nouveaux ratios de productivité des employés : leur productivité a augmenté de sept pour cent.",
    "gestion": "Voici la cédule des trois prochaines semaines. Deux équipes sur le chantier Morin dès lundi.",
    "administrateur": "Parfait. Envoie la soumission à monsieur Morin, pis bloque-moi jeudi matin.",
    "representant": "C'est beau, j'ai la photo. Ça part tout de suite.",
}
ENER = "[energetic, confident, natural Québécois]"
DIR_D3 = "Énergique, assuré, naturel, accent québécois, rythme vif, jamais lisse ni endormi."
MATRICE = [
    ("narrateur", "eleven:thomas", ENER, 1.0), ("narrateur", "eleven:frederic", ENER, 1.0), ("narrateur", "eleven:adamqc", ENER, 1.0),
    ("narrateur", "eleven:alexandre", ENER, 1.0), ("narrateur", "drama3:thomas", DIR_D3, 1.1), ("narrateur", "drama3:frederic", DIR_D3, 1.1),
    ("narrateur", "qwen3tts:frederic", "", 1.0),
    ("adjointe", "eleven:marieline", "[warm, professional, efficient]", 1.0), ("adjointe", "eleven:jeannemance", "[warm, professional, efficient]", 1.0),
    ("adjointe", "eleven:amelie", "[warm, professional, efficient]", 1.0), ("adjointe", "drama3:marieline", "Chaleureuse, professionnelle, efficace, accent québécois naturel.", 1.05),
    ("adjointe", "drama3:jeannemance", "Chaleureuse, professionnelle, efficace, accent québécois naturel.", 1.05), ("adjointe", "qwen3tts:jeannemance", "", 1.0),
    ("comptable", "eleven:amelie", "[confident, precise, upbeat]", 1.0), ("comptable", "eleven:frederic", "[confident, precise, upbeat]", 1.0),
    ("comptable", "drama3:amelie", "Assurée, précise, enjouée, accent québécois.", 1.05),
    ("gestion", "eleven:jeannemance", "[clear, upbeat, organized]", 1.0), ("gestion", "eleven:thomas", "[clear, upbeat, organized]", 1.0),
    ("gestion", "drama3:jeannemance", "Claire, dynamique, organisée, accent québécois.", 1.05),
    ("administrateur", "eleven:adamqc", "[casual, decisive, Québécois]", 1.0), ("administrateur", "eleven:frederic", "[casual, decisive, Québécois]", 1.0),
    ("administrateur", "drama3:adamqc", "Patron québécois décontracté et décidé, parle vite, naturel.", 1.1),
    ("representant", "eleven:thomas", "[upbeat, casual, Québécois]", 1.0), ("representant", "drama3:thomas", "Jeune représentant québécois, enjoué, décontracté.", 1.1),
    ("representant", "eleven:adamqc", "[upbeat, casual, young Québécois]", 1.0), ("representant", "drama3:adamqc", "Jeune représentant québécois, enjoué, décontracté, parle vite.", 1.1),
    ("comptable", "drama3:jeannemance", "Assurée, précise, enjouée, accent québécois.", 1.05), ("narrateur", "drama3:frederic", "Narrateur de publicité québécoise : énergique, punché, sourire dans la voix, rythme vif.", 1.15),
]

def main():
    out = V.TRAVAIL / "casting" / "banc.json"
    res = json.loads(out.read_text()) if out.exists() else {"refs": {}, "prises": []}
    for nom, vid in VOIX.items():
        f = V.REFS / f"{nom}.mp3"
        if not f.exists():
            b, _, c = V.generer(f"eleven:{vid}", REFTXT, "[energetic, warm, natural]")
            f.write_bytes(b); (V.REFS / f"{nom}.txt").write_text(REFTXT)
            res["refs"][nom] = {"voix": vid, "fichier": str(f), "cout": c}
    faits = {(p["role"], p["moteur_court"]) for p in res["prises"]}
    for role, mot, direc, vit in MATRICE:
        if (role, mot) in faits:
            continue
        fam, _, arg = mot.partition(":")
        moteur = f"eleven:{VOIX[arg]}" if fam == "eleven" else mot
        ident = f"{role}-{fam}-{arg}"
        try:
            m = V.ligne("casting", ident, moteur, LIGNES[role], direc if fam != "qwen3tts" else "", vit)
            m.update({"role": role, "moteur_court": mot}); m.pop("mots", None)
            res["prises"].append(m)
            print(ident, m.get("emr"), m.get("oreille", {}).get("moyennes"), flush=True)
        except Exception as e:
            print("ECHEC", ident, str(e)[:300], flush=True); traceback.print_exc()
        out.write_text(json.dumps(res, ensure_ascii=False, indent=1))
    out.write_text(json.dumps(res, ensure_ascii=False, indent=1))

if __name__ == "__main__":
    main()
