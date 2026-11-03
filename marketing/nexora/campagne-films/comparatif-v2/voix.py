#!/usr/bin/env python3
"""Narration fr-CA pour les films Nexora : synthèse sur pc1, contrôle Whisper et post-traitement sur pc6.

Usage : python3 voix.py narrer <phrases.json> <dossier_sortie_pc6>
  phrases.json = [{"id": "n01", "texte": "...", "role": "narrateur"|"assistant"}]

Pour chaque phrase : lexique de prononciation -> synthèse sur pc1 (ssh) -> transcription Whisper (pc6)
-> 2e puis 3e prise si WER > 0,15 (on garde la meilleure) -> coupe des silences, 48 kHz mono, -16 LUFS
-> <sortie>/<id>.wav ; bilan dans <sortie>/voix.json. Idempotent : un id déjà fait avec le même texte
(et le même moteur) n'est pas refait. Le travailleur moteur.py (à côté) est copié sur pc1 à chaque lot.

Variables d'environnement (facultatives) :
  VOIX_MOTEUR  chatterbox (défaut) | qwen3 | xtts | f5 | kokoro   (les autres moteurs servent au banc d'essai)
  VOIX_HOTE    alias ssh de pc1 (défaut « pc1 », repli « pc1-lan » ; pc1-ts exige une validation Tailscale)
  VOIX_REGLAGES  JSON fusionné aux réglages du moteur, ex. '{"expressivite": 0.7}'
  VOIX_FILS    fils processeur sur pc1 (défaut 12 ; ComfyUI garde le GPU, la synthèse tourne sur le CPU)
Référence de clonage : prises ElevenLabs « Alexandre Boutin » (narrateur) et « Adam » (assistant) ;
licence gérée par le fondateur.
"""
import json
import os
import re
import shlex
import subprocess
import sys
import tempfile
import time
import unicodedata

DISTANT = "/run/media/pc1/Infrastructure/NexoraStudioWork/films-v2/voix"
FFMPEG = os.path.expanduser("~/nexora-creative-data/engine/ffmpeg/ffmpeg-7.0.2-arm64-static/ffmpeg")
WHISPER_PY = os.path.expanduser("~/nexora-creative-data/engine/transcription-venv/bin/python")
MOTEUR = os.environ.get("VOIX_MOTEUR", "chatterbox")
SEUIL_WER = 0.15
LUFS = -16
DEBIT_MIN = 2.6  # mots/s

# Réglages par moteur : défaut « pub chaleureuse », visée 2,6 à 3 mots/s.
REGLAGES = {
    "chatterbox": {"expressivite": 0.65, "cfg": 0.5, "temperature": 0.75},
    "xtts": {"temperature": 0.7, "vitesse": 1.0},
    "kokoro": {"vitesse": 1.0},
    "f5": {"ckpt": DISTANT + "/hf/hub/models--tontate--f5-tts-quebec-french-finetune/snapshots/"
                   "c59b5de7008a03336c19caa75a126fb902c327f5/model_quebec_v1.safetensors",
           "vocab": DISTANT + "/hf/hub/models--tontate--f5-tts-quebec-french-finetune/snapshots/"
                    "c59b5de7008a03336c19caa75a126fb902c327f5/vocab.txt", "nfe": 32, "vitesse": 1.0},
    "qwen3": {},
}

# ---------------------------------------------------------------- lexique de prononciation
LEXIQUE = [  # (motif, réécriture phonétique) appliqués dans l'ordre, insensibles à la casse
    (r"\bOPSYS[-\s]?AI\b", "Opsis é-aïe"),
    (r"\bOPSYS\b", "Opsis"),
    (r"\bWork\s?Studio\b", "Weurk Stoudio"),
    (r"\bNexora\b", "Nexora"),
    (r"\bM(\d{1,2})\s*[–-]\s*M(\d{1,2})\b", lambda m: f"èm {nombre(int(m[1]))} à èm {nombre(int(m[2]))}"),
    (r"\bM(\d{1,2})\b", lambda m: f"èm {nombre(int(m[1]))}"),
    (r"\bIA\b", "i-a"), (r"\bAI\b", "é-aïe"), (r"\bPME\b", "pé-èm-eu"), (r"\bPDF\b", "pé-dé-èf"),
    (r"\bCRM\b", "cé-èr-èm"), (r"\bAPI\b", "a-pé-i"), (r"\bERP\b", "eu-èr-pé"), (r"\bSaaS\b", "sasse"),
    (r"\bQR\b", "cu-èr"), (r"\bTI\b", "té-i"), (r"\b3D\b", "trois-dé"), (r"\bH3\b", "ache-trois"),
    (r"\b(\d+)\s?%", lambda m: f"{nombre(int(m[1]))} pour cent"),
    (r"\b(\d+)\s?\$", lambda m: f"{nombre(int(m[1]))} dollars"),
    (r"\b(\d{1,4})\b", lambda m: nombre(int(m[1]))),
]
UNITES = "zéro un deux trois quatre cinq six sept huit neuf dix onze douze treize quatorze quinze seize".split()
DIZAINES = {2: "vingt", 3: "trente", 4: "quarante", 5: "cinquante", 6: "soixante"}


def nombre(n: int) -> str:
    """Nombre en toutes lettres (0 à 9999), graphie rectifiée à traits d'union."""
    if n < 17:
        return UNITES[n]
    if n < 20:
        return "dix-" + UNITES[n - 10]
    if n < 70:
        d, u = divmod(n, 10)
        return DIZAINES[d] + ("" if u == 0 else "-et-un" if u == 1 else "-" + UNITES[u])
    if n < 80:
        return "soixante-et-onze" if n == 71 else "soixante-" + nombre(n - 60)
    if n < 100:
        return "quatre-vingts" if n == 80 else "quatre-vingt-" + nombre(n - 80)
    if n < 1000:
        c, r = divmod(n, 100)
        tete = "cent" if c == 1 else UNITES[c] + "-cent" + ("s" if r == 0 else "")
        return tete if r == 0 else tete + "-" + nombre(r)
    m, r = divmod(n, 1000)
    tete = "mille" if m == 1 else nombre(m) + "-mille"
    return tete if r == 0 else tete + "-" + nombre(r)


def prononcer(texte: str) -> str:
    for motif, remplacement in LEXIQUE:
        texte = re.sub(motif, remplacement, texte, flags=re.IGNORECASE)
    return re.sub(r"\s+", " ", texte).strip()


# ---------------------------------------------------------------- WER
MARQUES = [  # variantes entendues par Whisper ramenées à une forme canonique
    (r"\bop\s?s[iy]s\s?(?:a\s?i|é\s?a[iï]e?|ai|ia|i\s?a)\b", "opsys ai"),
    (r"\bop\s?s[iy]s\b", "opsys"),
    (r"\b(?:work|weurk|wörk)\s?-?\s?st[iu]o?u?dio\b", "workstudio"),
    (r"\bnex\s?or+a\b", "nexora"),
    (r"\b(?:m|aime|èm|em|ème)\s?(un|deux|trois|quatre|cinq|six|sept|huit|neuf|dix)\b", r"m\1"),
]


def normaliser(texte: str) -> list:
    t = texte.lower().replace("’", "'")
    t = re.sub(r"\bm(\d{1,2})\b", lambda m: "m" + nombre(int(m[1])), t)
    t = re.sub(r"\d+", lambda m: nombre(int(m[0])) if len(m[0]) <= 4 else m[0], t)
    t = re.sub(r"[^\w'à-ÿ]+", " ", t).replace("-", " ")
    for motif, forme in MARQUES:
        t = re.sub(motif, forme, t)
    t = unicodedata.normalize("NFC", t)
    return [m for m in re.split(r"[\s']+", t) if m]


def wer(reference: str, hypothese: str) -> float:
    r, h = normaliser(reference), normaliser(hypothese)
    d = list(range(len(h) + 1))
    for i in range(1, len(r) + 1):
        prec, d[0] = d[0], i
        for j in range(1, len(h) + 1):
            prec, d[j] = d[j], min(d[j] + 1, d[j - 1] + 1, prec + (r[i - 1] != h[j - 1]))
    return round(d[len(h)] / max(1, len(r)), 3)


# ---------------------------------------------------------------- pc1
def hote() -> str:
    if os.environ.get("VOIX_HOTE"):
        return os.environ["VOIX_HOTE"]
    for h in ("pc1", "pc1-lan"):
        if subprocess.run(["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=6", h, "true"],
                          capture_output=True).returncode == 0:
            return h
    sys.exit("pc1 injoignable (ni « pc1 » ni « pc1-lan »)")


def synthetiser(h: str, items: list, local: str) -> dict:
    """Lance un lot sur pc1 (modèle chargé une fois) et rapatrie les WAV bruts. Retourne {cle: infos}."""
    lot = f"{DISTANT}/travaux/{os.getpid()}-{int(time.time())}"
    travail = {"items": [{**it, "sortie": f"{lot}/{it['cle']}.wav"} for it in items], "reglages": {**REGLAGES[MOTEUR], **json.loads(os.environ.get("VOIX_REGLAGES", "{}"))}}
    chemin = os.path.join(local, "travail.json")
    with open(chemin, "w", encoding="utf-8") as f:
        json.dump(travail, f, ensure_ascii=False)
    subprocess.run(["ssh", h, f"mkdir -p {lot}"], check=True)
    subprocess.run(["scp", "-q", os.path.join(os.path.dirname(os.path.abspath(__file__)), "moteur.py"),
                    f"{h}:{DISTANT}/moteur.py"], check=True)
    subprocess.run(["scp", "-q", chemin, f"{h}:{lot}/travail.json"], check=True)
    commande = (f"cd {DISTANT} && PATH={DISTANT}/venvs/{MOTEUR}/bin:$PATH HF_HOME={DISTANT}/hf VOIX_FILS={os.environ.get('VOIX_FILS', '12')} "
                f"venvs/{MOTEUR}/bin/python moteur.py {MOTEUR} {lot}/travail.json")
    p = subprocess.run(["ssh", h, commande], capture_output=True, text=True)
    infos = {}
    for ligne in p.stdout.splitlines():
        if ligne.startswith("{"):
            d = json.loads(ligne)
            if "id" in d:
                infos[d["id"]] = d
            else:
                print(f"  modèle {MOTEUR} chargé en {d['chargement']} s", flush=True)
    if p.returncode != 0 and not infos:
        sys.exit(f"échec de la synthèse sur pc1 :\n{p.stderr[-2000:]}")
    subprocess.run(["scp", "-q", f"{h}:{lot}/*.wav", local + "/"], check=True)
    subprocess.run(["ssh", h, f"rm -rf {shlex.quote(lot)}"])
    return infos


# ---------------------------------------------------------------- pc6 : Whisper et post-traitement
TRANSCRIRE = r"""
import json, sys, subprocess, numpy as np
from faster_whisper import WhisperModel
ff, fichiers = sys.argv[1], sys.argv[2:]
m = WhisperModel("medium", device="cpu", compute_type="int8", cpu_threads=16)
out = {}
for f in fichiers:
    pcm = subprocess.run([ff, "-v", "error", "-i", f, "-ac", "1", "-ar", "16000", "-f", "f32le", "-"], capture_output=True, check=True).stdout
    seg, _ = m.transcribe(np.frombuffer(pcm, np.float32), language="fr", beam_size=5, initial_prompt="Nexora, OPSYS-AI, WorkStudio.")
    out[f] = " ".join(s.text.strip() for s in seg)
print(json.dumps(out, ensure_ascii=False))
"""


def transcrire(fichiers: list) -> dict:
    if not fichiers:
        return {}
    p = subprocess.run([WHISPER_PY, "-I", "-c", TRANSCRIRE, FFMPEG, *fichiers], capture_output=True, text=True, check=True)
    return json.loads(p.stdout.strip().splitlines()[-1])


def duree_wav(f: str) -> float:
    p = subprocess.run([os.path.join(os.path.dirname(FFMPEG), "ffprobe"), "-v", "error", "-show_entries",
                        "format=duration", "-of", "csv=p=0", f], capture_output=True, text=True, check=True)
    return float(p.stdout.strip())


def finaliser(brut: str, sortie: str, mots: int) -> float:
    coupe = ("silenceremove=start_periods=1:start_threshold=-45dB:start_silence=0.06,areverse,"
             "silenceremove=start_periods=1:start_threshold=-45dB:start_silence=0.12,areverse,"
             "aresample=48000,pan=mono|c0=c0")
    # Débit visé 2,6 à 3 mots/s : si la prise est plus lente, léger atempo (plafonné à x1,10, hauteur conservée).
    tmp = brut + ".coupe.wav"
    subprocess.run([FFMPEG, "-v", "error", "-y", "-i", brut, "-af", coupe, tmp], check=True)
    debit = mots / max(0.1, duree_wav(tmp))
    os.remove(tmp)
    if debit < DEBIT_MIN:
        coupe += f",atempo={min(1.10, DEBIT_MIN / debit):.3f}"
    mesure = subprocess.run([FFMPEG, "-hide_banner", "-i", brut, "-af", coupe + f",loudnorm=I={LUFS}:TP=-1.5:LRA=11:print_format=json",
                             "-f", "null", "-"], capture_output=True, text=True).stderr
    m = json.loads(mesure[mesure.rindex("{"):mesure.rindex("}") + 1])
    norme = (f"loudnorm=I={LUFS}:TP=-1.5:LRA=11:measured_I={m['input_i']}:measured_TP={m['input_tp']}:"
             f"measured_LRA={m['input_lra']}:measured_thresh={m['input_thresh']}:offset={m['target_offset']}:linear=true")
    subprocess.run([FFMPEG, "-v", "error", "-y", "-i", brut, "-af", coupe + "," + norme, "-ar", "48000", "-ac", "1",
                    "-c:a", "pcm_s24le", sortie], check=True)
    return round(duree_wav(sortie), 2)


# ---------------------------------------------------------------- commande « narrer »
def narrer(phrases_json: str, dossier: str) -> None:
    phrases = json.load(open(phrases_json, encoding="utf-8"))
    os.makedirs(dossier, exist_ok=True)
    bilan_chemin = os.path.join(dossier, "voix.json")
    bilan = {e["id"]: e for e in json.load(open(bilan_chemin, encoding="utf-8"))} if os.path.exists(bilan_chemin) else {}
    a_faire = [p for p in phrases if not (p["id"] in bilan and bilan[p["id"]]["texte"] == p["texte"]
                                          and bilan[p["id"]].get("moteur", MOTEUR) == MOTEUR
                                          and os.path.exists(os.path.join(dossier, f"{p['id']}.wav")))]
    print(f"{len(phrases) - len(a_faire)} phrase(s) déjà faite(s), {len(a_faire)} à synthétiser ({MOTEUR})", flush=True)
    if a_faire:
        h = hote()
        prises = {p["id"]: [] for p in a_faire}
        with tempfile.TemporaryDirectory(prefix="voix-") as tmp:
            restantes = a_faire
            for numero in (1, 2, 3):  # 3e prise : rattrape les hallucinations de fin de phrase (WER > seuil après deux prises)
                items = [{"id": f"{p['id']}_p{numero}", "cle": f"{p['id']}_p{numero}", "texte": prononcer(p["texte"]),
                          "role": p.get("role", "narrateur"), "graine": 1000 * numero + i}
                         for i, p in enumerate(restantes)]
                infos = synthetiser(h, items, tmp)
                textes = transcrire([os.path.join(tmp, f"{c}.wav") for c in infos])
                for p in restantes:
                    c = f"{p['id']}_p{numero}"
                    if c not in infos:
                        continue
                    brut = os.path.join(tmp, f"{c}.wav")
                    tr = textes.get(brut, "")
                    prises[p["id"]].append({"brut": brut, "transcription": tr, "wer": wer(p["texte"], tr),
                                            "secondes_calcul": infos[c]["secondes_calcul"]})
                    print(f"  {p['id']} prise {numero} : WER {prises[p['id']][-1]['wer']:.2f} | {tr}", flush=True)
                restantes = [p for p in restantes if prises[p["id"]] and min(x["wer"] for x in prises[p["id"]]) > SEUIL_WER]
                if not restantes:
                    break
            for p in a_faire:
                if not prises[p["id"]]:
                    print(f"  {p['id']} : aucune prise produite", file=sys.stderr)
                    continue
                meilleure = min(prises[p["id"]], key=lambda x: x["wer"])
                fichier = os.path.join(dossier, f"{p['id']}.wav")
                bilan[p["id"]] = {"id": p["id"], "fichier": fichier, "duree": finaliser(meilleure["brut"], fichier, len(p["texte"].split())),
                                  "texte": p["texte"], "transcription": meilleure["transcription"], "wer": meilleure["wer"],
                                  "prises": len(prises[p["id"]]),
                                  "secondes_calcul": round(sum(x["secondes_calcul"] for x in prises[p["id"]]), 2),
                                  "machine": f"pc1 (CPU, {MOTEUR})", "role": p.get("role", "narrateur"), "moteur": MOTEUR}
    ordre = [p["id"] for p in phrases] + [i for i in bilan if i not in {p["id"] for p in phrases}]
    with open(bilan_chemin, "w", encoding="utf-8") as f:
        json.dump([bilan[i] for i in ordre if i in bilan], f, ensure_ascii=False, indent=2)
    faits = [bilan[p["id"]] for p in phrases if p["id"] in bilan]
    if faits:
        print(f"WER moyen {sum(e['wer'] for e in faits) / len(faits):.3f} -> {bilan_chemin}")


if __name__ == "__main__":
    if len(sys.argv) != 4 or sys.argv[1] != "narrer":
        sys.exit(__doc__)
    narrer(sys.argv[2], sys.argv[3])
