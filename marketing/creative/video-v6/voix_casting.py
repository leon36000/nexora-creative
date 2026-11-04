"""Film V6 : distribution des voix. Même texte d'essai pour tous les candidats, FR et EN, une prise par fichier.
  python3 voix_casting.py [candidat ...]       (sans argument : tous les candidats API)
Sortie : ~/nexora-creative-data/promo/v6-creative/voix/casting/<candidat>-<langue>.mp3 + casting.jsonl
La clé OpenRouter est lue dans ~/Desktop/Deepinfra.env et reste en mémoire : jamais affichée ni écrite.
Les candidats locaux (Qwen3-TTS VoiceDesign sur pc1, voix native H3) ont leurs propres scripts (voix_qwen_pc1.py, voix_h3.py).
"""
import base64
import json
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

SORTIE = Path.home() / "nexora-creative-data/promo/v6-creative/voix/casting"

TEXTE = {
    "fr": "Trois mots. Même mal écrits. Creative fait le reste. Un dragon ? Réglé. Une bataille dans l'espace ? Réglé. "
          "T'écris trois mots. Creative fait le film.",
    "en": "Three words. Typos and all. Creative does the rest. A dragon? Done. A space battle? Done. "
          "You type three words. Creative makes the movie.",
}
# Direction de jeu commune : à l'opposé du « trop smooth » de la V5 (calme, intime, lent).
JEU = {
    "fr": ("Énergique, percutant, avec du caractère : un animateur de bande-annonce qui s'amuse, sourire dans la voix, "
           "attaques franches, débit rapide, petites pauses sèches avant « Réglé ». Accent québécois naturel. Jamais doux ni posé."),
    "en": ("Energetic, punchy, full of character: a hype trailer announcer having fun, grin in the voice, hard attacks, "
           "fast pace, short dry beat before each 'Done'. Never soft, never smooth."),
}
TAGS = {"fr": "[excited] [punchy] [fast] ", "en": "[excited] [punchy] [fast] "}
ALEXANDRE = "IPgYtHTNLjC7Bq7IPHrm"  # ElevenLabs, catalogue Québec (voix des films Codex et de la V5)
REF_ALEXANDRE = (Path.home() / "nexora-creative-data/work/opsys-pc1/voix/alexandre-narration/sample-alexandre-00.mp3",
                 "Votre entreprise avance, chaque minute compte. Voici OPSYS-AI par Nexora. Une soumission, un chantier, des coûts plus clairs.")


def ref_alexandre():
    f, t = REF_ALEXANDRE
    b = base64.b64encode(f.read_bytes()).decode()
    return {"input_references": [{"type": "input_audio", "input_audio": {"data": "data:audio/mpeg;base64," + b}}, {"type": "text", "text": t}]}


# candidat -> {langue: (modèle, voix, préfixe, options)}
CANDIDATS = {
    "A-eleven4-alexandre-energique": {l: ("elevenlabs/eleven-v4", ALEXANDRE, TAGS[l], {}) for l in ("fr", "en")},
    "B-eleven4-liam": {l: ("elevenlabs/eleven-v4", "liam", TAGS[l], {}) for l in ("fr", "en")},
    "C-eleven4-callum": {l: ("elevenlabs/eleven-v4", "callum", TAGS[l], {}) for l in ("fr", "en")},
    "D-eleven4-charlie": {l: ("elevenlabs/eleven-v4", "charlie", TAGS[l], {}) for l in ("fr", "en")},
    "E-drama3-direction": {l: ("fish-audio/drama-3", None, "", {"instructions": JEU[l]}) for l in ("fr", "en")},
    "F-drama3-clone-alexandre-energique": {l: ("fish-audio/drama-3", None, "", {"instructions": JEU[l], "_ref": 1}) for l in ("fr", "en")},
    "G-drama3-balises": {l: ("fish-audio/drama-3", None, "[excited, hype trailer announcer, grinning, fast] ", {}) for l in ("fr", "en")},
    "H-voxtral-marie-excited": {"fr": ("mistralai/voxtral-mini-tts-3-0", "fr_marie_excited", "", {})},
    "I-gemini38-puck": {l: ("google/gemini-3.8-flash-tts", "Puck", "", {"instructions": JEU[l]}) for l in ("fr", "en")},
}


def cle():
    for ligne in open(Path.home() / "Desktop/Deepinfra.env"):
        if ":" in ligne:
            k, v = ligne.split(":", 1)
            if k.strip().lower() == "openrouter":
                return v.strip()
    raise KeyError("openrouter")


def parler(modele, texte, voix, extra):
    corps = {"model": modele, "input": texte, "response_format": "mp3", **{k: v for k, v in extra.items() if not k.startswith("_")}}
    if extra.get("_ref"):
        corps.update(ref_alexandre())
    if voix:
        corps["voice"] = voix
    d = json.dumps(corps).encode()
    err = None
    for i in range(4):
        r = urllib.request.Request("https://openrouter.ai/api/v1/audio/speech", data=d,
                                   headers={"Authorization": "Bearer " + cle(), "Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(r, timeout=300) as resp:
                return resp.read()
        except urllib.error.HTTPError as e:
            err = f"HTTP {e.code} {e.read().decode()[:300]}"
            if e.code == 429 or e.code >= 500:
                time.sleep(8 * (i + 1))
                continue
            break
    raise RuntimeError(err)


if __name__ == "__main__":
    SORTIE.mkdir(parents=True, exist_ok=True)
    noms = sys.argv[1:] or list(CANDIDATS)
    for n in noms:
        for langue, (modele, voix, pre, extra) in CANDIDATS[n].items():
            f = SORTIE / f"{n}-{langue}.mp3"
            t = time.time()
            try:
                f.write_bytes(parler(modele, pre + TEXTE[langue], voix, extra))
                res = {"candidat": n, "langue": langue, "modele": modele, "voix": voix, "fichier": str(f), "secondes": round(time.time() - t, 1),
                       "caracteres": len(pre + TEXTE[langue])}
            except Exception as e:
                res = {"candidat": n, "langue": langue, "modele": modele, "erreur": str(e)[:300]}
            print(json.dumps(res, ensure_ascii=False), flush=True)
            with (SORTIE / "casting.jsonl").open("a") as fh:
                fh.write(json.dumps(res, ensure_ascii=False) + "\n")
