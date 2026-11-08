"""Banc de voix FR pour le film V7 : nouveaux essais ElevenLabs v4 uniquement.
Usage : python3 banc_voix_v7.py <candidat-eleven4-explicite>
Les anciens essais restent identifiés par leur modèle ; aucun timbre final n'est choisi ici.
Le banc utilise une sortie séparée et exige une configuration API explicite.
"""
import base64
import json
import subprocess
import sys
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'chaine'))
from commun import api_configuration

D = Path.home() / "nexora-creative-data/promo/v7-creative/voix-banc-eleven4"
FF = str(Path.home() / "nexora-creative-data/engine/ffmpeg/ffmpeg-7.0.2-arm64-static/ffmpeg")
REF_H3 = Path.home() / "nexora-creative-data/promo/v6-creative/voix/casting/K-h3-natif-a-fr.mp3"
REF_TXT = "Trois mots. Même mal écrits. L'IA écrit le reste. Une bataille dans l'espace ? Réglé. T'écris trois mots. On fait le film."
TEXTES = {
    "narration": "Trois mots. Et tout explose.",
    "cri": "Bouclier ! Maintenant ! Ils arrivent !",
}
JEU = {"narration": "Bande-annonce de film d'action : voix grave, rauque, attaques franches, une pause sèche après « Trois mots ». Jamais douce.",
       "cri": "Pilote de chasse en plein combat, elle hurle des ordres, essoufflée, urgente, la voix qui casse sur « Maintenant »."}


def post(chemin_api, corps, timeout=300):
    url, cle = api_configuration(chemin_api, corps.get('model'))
    r = urllib.request.Request(url, data=json.dumps(corps).encode(), headers={"Authorization": "Bearer " + cle, "Content-Type": "application/json"})
    for i in range(3):
        try:
            with urllib.request.urlopen(r, timeout=timeout) as x:
                return x.read()
        except urllib.error.HTTPError as e:
            if e.code in (429, 500, 502, 503) and i < 2:
                time.sleep(6 * (i + 1))
                continue
            raise RuntimeError(f"HTTP {e.code}") from None


def ref_clone():
    return [{"type": "input_audio", "input_audio": {"data": "data:audio/mpeg;base64," + base64.b64encode(REF_H3.read_bytes()).decode()}},
            {"type": "text", "text": REF_TXT}]


# Les anciens essais demeurent identifiés par leur vrai modèle dans l'historique.
MODELE_FILM = "elevenlabs/eleven-v4"

# id : (modèle, voix, options, format de réponse)
CANDIDATS = {
    "eleven4-liam": (MODELE_FILM, "liam", {}, "mp3"),
    "eleven4-charlie": (MODELE_FILM, "charlie", {}, "mp3"),
    "vox3-marie-excitee": ("mistralai/voxtral-mini-tts-3-0", "fr_marie_excited", {}, "mp3"),
    "vox3-marie-colere": ("mistralai/voxtral-mini-tts-3-0", "fr_marie_angry", {}, "mp3"),
    "vox3-clone-h3": ("mistralai/voxtral-mini-tts-3-0", None, {"input_references": "clone"}, "mp3"),
    "vox2603-marie-excitee": ("mistralai/voxtral-mini-tts-2603", "fr_marie_excited", {}, "mp3"),
    "vox2603-clone-h3": ("mistralai/voxtral-mini-tts-2603", None, {"input_references": "clone"}, "mp3"),
    "minimax28-narrateur": ("minimax/speech-2.8-hd", "French_MaleNarrator", {}, "mp3"),
    "minimax28-homme": ("minimax/speech-2.8-hd", "French_Male_Speech_New", {}, "mp3"),
    "mai21-grant": ("microsoft/mai-voice-2.1", "fr-FR-Grant:MAI-Voice-2.1", {}, "mp3"),
    "mai21-marc": ("microsoft/mai-voice-2.1", "fr-FR-Marc:MAI-Voice-2.1", {}, "mp3"),
    "mai21-harper": ("microsoft/mai-voice-2.1", "fr-FR-Harper:MAI-Voice-2.1", {}, "mp3"),
    "fish21-direction": ("fish-audio/s2.1-pro", None, {"instructions": "jeu"}, "mp3"),
    "fish21-clone-h3": ("fish-audio/s2.1-pro", None, {"instructions": "jeu", "input_references": "clone"}, "mp3"),
    "gemini38-fenrir": ("google/gemini-3.8-flash-tts", "Fenrir", {"instructions": "jeu"}, "pcm"),
    "gemini38-puck": ("google/gemini-3.8-flash-tts", "Puck", {"instructions": "jeu"}, "pcm"),
}
# les voix numérotées de Voxtral 3 (bibliothèque sans étiquette de langue) : passées au crible sur la narration
for v in ["voice_3150", "voice_478", "voice_447", "voice_485", "voice_3149", "voice_3147", "voice_591", "voice_590", "voice_1788",
          "voice_1787", "voice_1786", "voice_479", "voice_3143", "voice_481", "voice_483", "voice_592", "voice_3137", "voice_589",
          "voice_3141", "voice_3153", "voice_3139", "voice_3146", "voice_482", "voice_3133", "voice_3136", "voice_3135", "voice_3145",
          "voice_3134", "voice_3154", "voice_480", "voice_3155", "voice_3132", "voice_3138", "voice_3140", "voice_3144", "voice_3142"]:
    CANDIDATS[f"vox3-{v.replace('_', '')}"] = ("mistralai/voxtral-mini-tts-3-0", v, {}, "mp3")

GRILLE = ("Tu es directeur de casting pour une bande-annonce québécoise. Écoute ce clip ({role}). Texte attendu : « {texte} ». "
          "Réponds en JSON : {{\"langue_francaise\": 0-10 (français naturel, pas d'accent anglais), \"accent_quebecois\": 0-10, "
          "\"energie\": 0-10, \"caractere\": 0-10 (grain, personnalité ; une voix lisse de publicité = 2), \"naturel\": 0-10 "
          "(humain, pas synthétique), \"cheap\": 0-10 (10 = sonne bon marché / TTS), \"genre\": \"homme|femme\", \"commentaire\": \"une phrase\"}}")


def generer(nom, texte_id):
    modele, voix, opt, fmt = CANDIDATS[nom]
    if modele != MODELE_FILM or not isinstance(voix, str) or not voix.strip():
        raise ValueError("La politique de voix des films exige ElevenLabs v4 et une voix explicite.")
    fichier = D / f"{nom}-{texte_id}.mp3"
    if fichier.exists() or fichier.is_symlink():
        raise FileExistsError(f"Prise existante conservée : {fichier}")
    direction = JEU.get(texte_id, '').strip().replace('[', '').replace(']', '')
    entree = f"[{direction}] {TEXTES[texte_id]}" if direction else TEXTES[texte_id]
    corps = {"model": modele, "input": entree, "response_format": fmt}
    if voix:
        corps["voice"] = voix
    if opt.get("input_references"):
        corps["input_references"] = ref_clone()
    b = post("audio/speech", corps)
    f = D / f"{nom}-{texte_id}.mp3"
    if fmt == "pcm":
        brut = D / f"{nom}-{texte_id}.pcm"
        brut.write_bytes(b)
        subprocess.run([FF, "-v", "error", "-y", "-f", "s16le", "-ar", "24000", "-ac", "1", "-i", str(brut), "-q:a", "2", str(f)], check=True)
        brut.unlink()
    else:
        with f.open("xb") as out:
            out.write(b)
    return f


GRILLE_EN = ("You are a casting director for an English-language action trailer. Listen to this clip ({role}). Expected text: \"{texte}\". "
             "Reply in JSON: {{\"langue_anglaise\": 0-10 (natural English), \"accent_naturel\": 0-10 (natural accent), "
             "\"energie\": 0-10, \"caractere\": 0-10, \"naturel\": 0-10, \"cheap\": 0-10, "
             "\"genre\": \"homme|femme\", \"commentaire\": \"one sentence\"}}")


def juger(f, texte_id, passes=2, langue='fr'):
    if langue not in ('fr', 'en'):
        raise ValueError('Langue de jugement explicite : fr ou en.')
    grille = GRILLE if langue == 'fr' else GRILLE_EN
    cles_langue = ('langue_francaise', 'accent_quebecois') if langue == 'fr' else ('langue_anglaise', 'accent_naturel')
    b = base64.b64encode(f.read_bytes()).decode()
    notes = []
    for i in range(passes):
        corps = {"model": "google/gemini-4-argon", "temperature": 0.3 if i else 0.0, "response_format": {"type": "json_object"},
             "provider": {"order": ["google-ai-studio/flex"], "allow_fallbacks": False},
                 "messages": [{"role": "user", "content": [{"type": "input_audio", "input_audio": {"data": b, "format": "mp3"}},
                                                          {"type": "text", "text": grille.format(role=texte_id, texte=TEXTES[texte_id])}]}]}
        try:
            r = json.loads(post("chat/completions", corps, timeout=180))
            t = r["choices"][0]["message"]["content"]
            notes.append(json.loads(t[t.find("{"): t.rfind("}") + 1]))
        except Exception as e:
            notes.append({"erreur": str(e)[:150]})
    ok = [n for n in notes if "erreur" not in n]
    moy = {k: round(sum(n[k] for n in ok if isinstance(n.get(k), (int, float))) / max(1, len(ok)), 1)
           for k in (*cles_langue, "energie", "caractere", "naturel", "cheap")} if ok else {}
    return moy, [n.get("commentaire") for n in ok], (ok[0].get("genre") if ok else None)


def tache(args):
    nom, texte_id = args
    try:
        f = generer(nom, texte_id)
        moy, com, genre = juger(f, texte_id)
        score = round(moy.get("langue_francaise", 0) * .25 + moy.get("energie", 0) * .2 + moy.get("caractere", 0) * .2
                      + moy.get("naturel", 0) * .25 - moy.get("cheap", 0) * .2 + moy.get("accent_quebecois", 0) * .1, 2) if moy else None
        return {"id": nom, "texte": texte_id, "fichier": f.name, "modele_demande": CANDIDATS[nom][0], "origine": "modele_demande_non_atteste", "voix": CANDIDATS[nom][1],
                "oreille": moy, "genre": genre, "commentaires": com, "score": score}
    except Exception as e:
        return {"id": nom, "texte": texte_id, "erreur": str(e)[:200]}


if __name__ == "__main__":
    if len(sys.argv) != 2 or sys.argv[1] not in CANDIDATS:
        raise SystemExit("Choisir explicitement un candidat ElevenLabs v4 ; aucun timbre final n'est présélectionné.")
    filtre = sys.argv[1]
    if CANDIDATS[filtre][0] != MODELE_FILM:
        raise SystemExit("Ce candidat historique ne répond pas à la politique ElevenLabs v4.")
    jobs = [(filtre, "narration"), (filtre, "cri")]
    if any((D / f"{nom}-{texte}.mp3").exists() or (D / f"{nom}-{texte}.mp3").is_symlink() for nom, texte in jobs):
        raise SystemExit("Une prise existe déjà ; aucun fichier historique ne sera remplacé.")
    if (D / "banc.json").exists():
        ancien = json.loads((D / "banc.json").read_text())
        if any((r.get("id"), r.get("texte")) in jobs for r in ancien):
            raise SystemExit("Une entrée de banc existe déjà ; aucun historique ne sera remplacé.")
    D.mkdir(parents=True, exist_ok=True)
    with ThreadPoolExecutor(6) as ex:
        res = list(ex.map(tache, jobs))
    old = json.loads((D / "banc.json").read_text()) if (D / "banc.json").exists() else []
    res = [r for r in old if (r["id"], r["texte"]) not in {(x["id"], x["texte"]) for x in res}] + res
    (D / "banc.json").write_text(json.dumps(res, ensure_ascii=False, indent=1))
    ok = sorted([r for r in res if r.get("score") is not None], key=lambda r: -r["score"])
    lignes = ["# Banc des voix V7 (même texte pour tous ; oreille de machine Gemini 4 Argon, 2 passes ; à confirmer à l'oreille)", "",
              "| rang | fichier | modèle demandé | voix | genre | français | québécois | énergie | caractère | naturel | cheap | score |", "|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for i, r in enumerate(ok, 1):
        o = r["oreille"]
        lignes.append(f"| {i} | {r['fichier']} | {r.get('modele_demande', r.get('modele', 'inconnu'))} | {r['voix']} | {r['genre']} | {o.get('langue_francaise')} | {o.get('accent_quebecois')} | "
                      f"{o.get('energie')} | {o.get('caractere')} | {o.get('naturel')} | {o.get('cheap')} | {r['score']} |")
    lignes += ["", "Échecs : " + ", ".join(f"{r['id']}/{r['texte']} ({r['erreur'][:60]})" for r in res if r.get("erreur"))]
    (D / "INDEX.md").write_text("\n".join(lignes) + "\n")
    print("\n".join(lignes[:30]))
