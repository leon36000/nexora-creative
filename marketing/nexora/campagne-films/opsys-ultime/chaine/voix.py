"""Voix du film ultime : génération par moteur (une fonction par moteur), mesures, oreille de machine.

Moteurs (voir casting/PALETTE.md pour les identifiants de voix) :
  eleven:<id_voix>            ElevenLabs v4 par OpenRouter (balises de jeu [energetic] etc. dans le texte acceptées)
  drama3:<ref>                Fish Audio Drama 3 par OpenRouter, clonage sans état depuis une prise de référence de la palette,
                              consigne de jeu en langage naturel (`instructions`) et vitesse (`speed`, honorée par Drama 3)
  qwen3tts:<ref>              Qwen3-TTS 1.7B Base en local (GB10), clonage depuis la même référence (apache-2.0)
Mesures : durée, débit (caractères/s), hauteur (F0 médiane, écart en demi-tons = « relief » de la voix : une voix « smooth »
a peu de relief), dynamique (écart-type de l'énergie en dB), EMR Whisper. Oreille : Gemini 4 Argon (audio) note l'accent
québécois, l'énergie, le naturel, la clarté (2 passes, moyenne) ; ce n'est pas une écoute humaine.

  python3 voix.py ligne <equipe> <id> <moteur> "<texte>" [--direction "..."] [--vitesse 1.1] [--prise 1]
  python3 voix.py juger fichier.mp3 "<texte attendu>" "<rôle>"
"""
import argparse
import base64
import json
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

import numpy as np

ICI = Path(__file__).resolve().parent
sys.path.insert(0, str(ICI.parents[1] / "films-v3/outils"))
import commun as C  # noqa: E402

TRAVAIL = Path.home() / "nexora-creative-data/work/opsys-ultime"
FF = str(Path.home() / "nexora-creative-data/engine/ffmpeg/ffmpeg-7.0.2-arm64-static/ffmpeg")
WHISPER_PY = str(Path.home() / "nexora-creative-data/engine/transcription-venv/bin/python")
QWEN_PY = str(Path.home() / "nexora-creative-data/work/voix2-modeles/qwen3tts/venv/bin/python")
REFS = TRAVAIL / "casting/refs"  # prises de référence (wav + .txt) pour le clonage


def post(url, corps, timeout=300):
    d = json.dumps(corps).encode()
    err = None
    for i in range(4):
        r = urllib.request.Request(url, data=d, headers={"Authorization": "Bearer " + C.cle("openrouter"), "Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(r, timeout=timeout) as resp:
                return resp.read()
        except urllib.error.HTTPError as e:
            err = f"HTTP {e.code} {e.read().decode()[:300]}"
            if e.code == 429 or e.code >= 500:
                time.sleep(6 * (i + 1))
                continue
            break
        except Exception as e:  # coupure réseau
            err = str(e)
            time.sleep(5)
    raise RuntimeError(err)


def ref_clone(nom):
    wav = REFS / f"{nom}.mp3"
    txt = (REFS / f"{nom}.txt").read_text().strip()
    b = base64.b64encode(wav.read_bytes()).decode()
    return {"input_references": [{"type": "input_audio", "input_audio": {"data": "data:audio/mpeg;base64," + b}}, {"type": "text", "text": txt}]}


def generer(moteur, texte, direction="", vitesse=1.0):
    """Renvoie (octets mp3 ou wav, extension, coût estimé USD)."""
    famille, _, arg = moteur.partition(":")
    if famille == "eleven":
        t = (direction.strip() + " " + texte).strip() if direction else texte
        return post("https://openrouter.ai/api/v1/audio/speech", {"model": "elevenlabs/eleven-v4", "input": t, "voice": arg,
                                                                 "response_format": "mp3"}), "mp3", round(len(t) * 0.08 / 1000, 5)
    if famille == "drama3":
        corps = {"model": "fish-audio/drama-3", "input": texte, "response_format": "mp3", **ref_clone(arg)}
        if direction:
            corps["instructions"] = direction
        if vitesse and abs(vitesse - 1) > 1e-3:
            corps["speed"] = vitesse
        return post("https://openrouter.ai/api/v1/audio/speech", corps), "mp3", round(len(texte) * 2 / 1e6, 6)
    if famille == "or":  # moteur OpenRouter générique : or:<modèle>|voice=<voix>|ref=<prise de référence>|instr
        champs = arg.split("|")
        corps = {"model": champs[0], "input": texte, "response_format": "mp3"}
        for c in champs[1:]:
            k, _, v = c.partition("=")
            if k == "voice":
                corps["voice"] = v
            elif k == "ref":
                corps.update(ref_clone(v))
            elif k == "instr" and direction:
                corps["instructions"] = direction
        if vitesse and abs(vitesse - 1) > 1e-3:
            corps["speed"] = vitesse
        return post("https://openrouter.ai/api/v1/audio/speech", corps), "mp3", round(len(texte) * 20 / 1e6, 6)
    if famille == "qwen3tts":
        out = TRAVAIL / "tmp" / f"qwen-{abs(hash((texte, arg)))}.wav"
        out.parent.mkdir(parents=True, exist_ok=True)
        code = (
            "import sys,torch,soundfile as sf\nfrom qwen_tts import Qwen3TTSModel\n"
            "m=Qwen3TTSModel.from_pretrained('Qwen/Qwen3-TTS-12Hz-1.7B-Base',device_map='cuda:0',dtype=torch.bfloat16,attn_implementation='sdpa')\n"
            "w,sr=m.generate_voice_clone(text=sys.argv[1],language='French',ref_audio=sys.argv[2],ref_text=open(sys.argv[3]).read().strip())\n"
            "sf.write(sys.argv[4],w[0],sr)\n")
        ref = REFS / f"{arg}.mp3"
        wav = REFS / f"{arg}.wav"
        if not wav.exists():
            subprocess.run([FF, "-v", "error", "-y", "-i", str(ref), "-ac", "1", "-ar", "24000", str(wav)], check=True)
        subprocess.run([QWEN_PY, "-c", code, texte, str(wav), str(REFS / f"{arg}.txt"), str(out)], check=True, capture_output=True)
        b = out.read_bytes()
        out.unlink()
        return b, "wav", 0.0
    raise SystemExit(f"moteur inconnu : {moteur}")


# ------------------------------------------------------------------------------------------------------------ mesures
def lire(f, sr=16000):
    raw = subprocess.run([FF, "-v", "error", "-i", str(f), "-ac", "1", "-ar", str(sr), "-f", "f32le", "-"], capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.float32)


def f0(x, sr=16000):
    """F0 par autocorrélation normalisée sur trames voisées (70 à 400 Hz)."""
    n, hop = 640, 160
    out = []
    for i in range(0, len(x) - n, hop):
        fr = x[i:i + n] * np.hanning(n)
        if np.sqrt(np.mean(fr ** 2)) < 0.01:
            continue
        ac = np.correlate(fr, fr, "full")[n - 1:]
        ac /= ac[0] + 1e-9
        lo, hi = sr // 400, sr // 70
        k = lo + int(np.argmax(ac[lo:hi]))
        if ac[k] > 0.45:
            out.append(sr / k)
    return np.array(out)


def mesurer(f, texte=None):
    x = lire(f)
    d = len(x) / 16000
    # durée utile : sans silences de tête et de queue (−40 dB)
    e = np.array([np.sqrt(np.mean(x[i:i + 320] ** 2)) for i in range(0, len(x) - 320, 320)])
    db = 20 * np.log10(e + 1e-6)
    act = np.where(db > db.max() - 40)[0]
    utile = (act[-1] - act[0] + 1) * 0.02 if len(act) else d
    p = f0(x)
    demi = 12 * np.log2(p / np.median(p)) if len(p) > 10 else np.array([0.0])
    voise = db[db > db.max() - 30]
    m = {"duree_s": round(d, 2), "utile_s": round(utile, 2), "f0_hz": round(float(np.median(p)), 1) if len(p) else None,
         "relief_demitons": round(float(np.std(demi)), 2), "dynamique_db": round(float(np.std(voise)), 2)}
    if texte:
        m["cps"] = round(len(texte) / max(utile, 0.1), 1)
    return m


def transcrire(fichiers):
    p = subprocess.run([WHISPER_PY, "-I", str(ICI / "transcrire.py"), *map(str, fichiers)], capture_output=True, text=True, check=True)
    return json.loads(p.stdout.strip().splitlines()[-1])


def emr(attendu, obtenu):
    import re
    import unicodedata

    def norm(s):
        s = unicodedata.normalize("NFD", s.lower())
        s = "".join(c for c in s if unicodedata.category(c) != "Mn")
        s = re.sub(r"(\d+)\s*h\b", r"\1 heures", s).replace("%", " pour cent ")
        nombres = {"un": "1", "deux": "2", "trois": "3", "quatre": "4", "cinq": "5", "six": "6", "sept": "7", "huit": "8", "neuf": "9",
                   "dix": "10", "onze": "11", "douze": "12", "treize": "13", "quatorze": "14", "quinze": "15", "seize": "16",
                   "vingt": "20", "trente": "30"}
        return [nombres.get(w, w) for w in re.findall(r"[a-z0-9]+", s)]
    a, b = norm(attendu), norm(obtenu)
    D = np.zeros((len(a) + 1, len(b) + 1), int)
    D[:, 0], D[0, :] = range(len(a) + 1), range(len(b) + 1)
    for i in range(1, len(a) + 1):
        for j in range(1, len(b) + 1):
            D[i, j] = min(D[i - 1, j] + 1, D[i, j - 1] + 1, D[i - 1, j - 1] + (a[i - 1] != b[j - 1]))
    return round(D[-1, -1] / max(1, len(a)), 3)


GRILLE = (
    "Tu es directeur de distribution vocale pour une publicité télévisée québécoise. Écoute cette prise (rôle : {role}). "
    "Texte attendu : « {texte} ». Note de 0 à 10, sévèrement (5 = moyen, 8 = diffusable à la télé au Québec) : "
    "accent_quebecois (10 = Québécois naturel, 0 = français de France ou accent étranger), energie (10 = énergique, caractère, "
    "punch ; 0 = plat, trop lisse, endormi), naturel (10 = humain, 0 = synthétique), clarte (articulation, prononciation des noms), "
    "adequation_role. Liste les fautes de prononciation ou de lecture. Réponds en JSON strict : "
    '{{"accent_quebecois":n,"energie":n,"naturel":n,"clarte":n,"adequation_role":n,"fautes":["..."],"commentaire":"une phrase"}}')


def juger(f, texte, role, passes=2, modele="google/gemini-4-argon"):
    b = base64.b64encode(Path(f).read_bytes()).decode()
    fmt = Path(f).suffix.lstrip(".").lower()
    notes = []
    for i in range(passes):
        corps = {"model": modele, "temperature": 0.3 if i else 0.0, "response_format": {"type": "json_object"},
                 "messages": [{"role": "user", "content": [{"type": "input_audio", "input_audio": {"data": b, "format": fmt}},
                                                          {"type": "text", "text": GRILLE.format(role=role, texte=texte)}]}]}
        try:
            r = json.loads(post("https://openrouter.ai/api/v1/chat/completions", corps, timeout=180))
            txt = r["choices"][0]["message"]["content"]
            j = json.loads(txt[txt.find("{"): txt.rfind("}") + 1])
            j["_cout"] = r.get("usage", {}).get("cost")
            notes.append(j)
        except Exception as e:
            notes.append({"erreur": str(e)[:200]})
    ok = [n for n in notes if "erreur" not in n]
    moy = {k: round(float(np.mean([n[k] for n in ok if isinstance(n.get(k), (int, float))])), 1)
           for k in ("accent_quebecois", "energie", "naturel", "clarte", "adequation_role")} if ok else {}
    return {"moyennes": moy, "passes": notes}


def lot(taches, paralleles=6):
    """Plusieurs prises d'un coup : génération en parallèle, une seule passe Whisper, oreille en parallèle.
    tache = (equipe, ident, moteur, texte, direction, vitesse, prise)."""
    import concurrent.futures as cf

    def gen(t):
        try:
            return ligne(*t, juge=False, avec_whisper=False)
        except Exception as e:
            print("ECHEC voix", t[1], t[6], str(e)[:300], flush=True)
            return None
    with cf.ThreadPoolExecutor(paralleles) as ex:
        ms = [m for m in ex.map(gen, taches) if m]
    if not ms:
        return []
    tr = transcrire([m["fichier"] for m in ms])
    for m in ms:
        x = tr.get(m["fichier"], {"texte": "", "mots": []})
        m["transcription"], m["mots"], m["emr"] = x["texte"], x["mots"], emr(m["texte"], x["texte"])

    def ore(m):
        m["oreille"] = juger(m["brut"], m["texte"], m["id"])
        return m
    with cf.ThreadPoolExecutor(paralleles) as ex:
        ms = list(ex.map(ore, ms))
    for m in ms:
        Path(m["fichier"]).with_suffix(".json").write_text(json.dumps(m, ensure_ascii=False, indent=1))
    return ms


def ligne(equipe, ident, moteur, texte, direction="", vitesse=1.0, prise=1, juge=True, avec_whisper=True):
    d = TRAVAIL / equipe / "voix"
    d.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    for essai in range(3):  # réponse vide ou tronquée du fournisseur : on recommence
        octets, ext, cout = generer(moteur, texte, direction, vitesse)
        if len(octets) > 2000:
            break
        time.sleep(3)
    brut = d / f"{ident}-p{prise}-brut.{ext}"
    brut.write_bytes(octets)
    # version de montage : 48 kHz mono, silences de tête/queue coupés, −16 LUFS
    wav = d / f"{ident}-p{prise}.wav"
    subprocess.run([FF, "-v", "error", "-y", "-i", str(brut), "-af",
                    "silenceremove=start_periods=1:start_threshold=-45dB:start_silence=0.05,areverse,"
                    "silenceremove=start_periods=1:start_threshold=-45dB:start_silence=0.10,areverse,loudnorm=I=-16:TP=-2,aresample=48000",
                    "-ac", "1", str(wav)], check=True)
    m = mesurer(wav, texte)
    m.update({"equipe": equipe, "id": ident, "prise": prise, "moteur": moteur, "texte": texte, "direction": direction, "vitesse": vitesse,
              "fichier": str(wav), "brut": str(brut), "cout_usd": cout, "secondes": round(time.time() - t0, 1)})
    if not avec_whisper:
        return m
    tr = transcrire([wav])[str(wav)]
    m["transcription"] = tr["texte"]
    m["mots"] = tr["mots"]
    m["emr"] = emr(texte, tr["texte"])
    if juge:
        m["oreille"] = juger(brut, texte, ident)
    (d / f"{ident}-p{prise}.json").write_text(json.dumps(m, ensure_ascii=False, indent=1))
    with (TRAVAIL / "journal-api.jsonl").open("a") as fh:
        fh.write(json.dumps({"equipe": equipe, "quoi": f"voix {ident} p{prise}", "moteur": moteur, "cout_usd": cout,
                             "secondes": m["secondes"]}) + "\n")
    return m


if __name__ == "__main__":
    a = argparse.ArgumentParser()
    a.add_argument("cmd")
    a.add_argument("args", nargs="*")
    a.add_argument("--direction", default="")
    a.add_argument("--vitesse", type=float, default=1.0)
    a.add_argument("--prise", type=int, default=1)
    a.add_argument("--sans-juge", action="store_true")
    o = a.parse_args()
    if o.cmd == "ligne":
        eq, ident, mot, txt = o.args
        r = ligne(eq, ident, mot, txt, o.direction, o.vitesse, o.prise, not o.sans_juge)
        print(json.dumps({k: r.get(k) for k in ("id", "moteur", "utile_s", "cps", "relief_demitons", "emr", "oreille")}, ensure_ascii=False))
    elif o.cmd == "juger":
        print(json.dumps(juger(o.args[0], o.args[1], o.args[2]), ensure_ascii=False))
