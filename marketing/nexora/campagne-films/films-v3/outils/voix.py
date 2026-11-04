"""Narration des films V5 : une phrase = un fichier (stems interchangeables), moteur choisi sans toucher aux images.

  python3 voix.py <film> [moteur]          moteurs : voir MOTEURS (défaut : celui de ../audio-choix.json)
Sortie : ~/nexora-creative-data/work/films-v3/<film>/voix/<moteur>/<id>.wav (48 kHz, stéréo, −16 LUFS par phrase)
         + voix.json (durée, mots/s, tempo appliqué, transcription Whisper et WER).
Débit visé ≈ 2,2 mots/s : la phrase est ralentie au besoin (atempo, hauteur conservée), entre 0,86 et 1,0.
Chatterbox et Kokoro sont refusés pour les finales (consigne du fondateur).
"""
import json
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

import commun as C

INSTR = ("Calm, intimate, confident narration in Québec French (Québécois accent, not France French), slow pace, "
         "warm close-mic male voice, restrained, like a premium Apple product film.")
# moteur → (modèle OpenRouter, voix, préfixe de texte, options)
REF_ALEXANDRE = (Path.home() / "nexora-creative-data/work/opsys-pc1/voix/alexandre-narration/sample-alexandre-00.mp3",
                 "Votre entreprise avance, chaque minute compte. Voici OPSYS-AI par Nexora. Une soumission, un chantier, des coûts plus clairs.")
DIRECTION = "[calm, intimate, confident, Québec French accent, slow, long pauses] "


def ref_alexandre():
    import base64
    f, t = REF_ALEXANDRE
    b = base64.b64encode(f.read_bytes()).decode()
    return {"input_references": [{"type": "input_audio", "input_audio": {"data": "data:audio/mpeg;base64," + b}}, {"type": "text", "text": t}]}


MOTEURS = {
    # n° 1 du classement de machine du banc d'écoute (INDEX.md du 03/11) : Drama 3, clone Alexandre + direction
    "drama3-clone-alexandre-direction": ("fish-audio/drama-3", None, DIRECTION, "ref_alexandre"),
    # choix du fondateur à l'écoute (03/11) : ElevenLabs v4, voix québécoise « Alexandre »
    "eleven-v4-alexandre": ("elevenlabs/eleven-v4", "IPgYtHTNLjC7Bq7IPHrm", "[calm, intimate, confident, slow] ", {}),
    "eleven-v3-alexandre": ("elevenlabs/eleven-v3", "IPgYtHTNLjC7Bq7IPHrm", "[calm, intimate, confident, slow] ", {}),
    "drama3": ("fish-audio/drama-3", None, "", {"instructions": INSTR}),
    "minimax-speech28hd": ("minimax/speech-2.8-hd", None, "", {}),
    "gemini38-charon": ("google/gemini-3.8-flash-tts", "Charon", "", {"instructions": INSTR}),
}
INTERDITS = ("chatterbox", "kokoro")
CIBLE_MPS = 2.2


def parler(modele, texte, voix, extra, fmt="mp3"):
    corps = {"model": modele, "input": texte, "response_format": fmt, **extra}
    if voix:
        corps["voice"] = voix
    d = json.dumps(corps).encode()
    err = None
    for i in range(4):
        r = urllib.request.Request("https://openrouter.ai/api/v1/audio/speech", data=d,
                                   headers={"Authorization": "Bearer " + C.cle("openrouter"), "Content-Type": "application/json"})
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


def mots(t):
    return len(t.replace("…", " ").split())


def nettoyer(src, dst, tempo):
    """Coupe les silences de bord, applique le tempo, normalise à −16 LUFS, 48 kHz stéréo."""
    f = (f"silenceremove=start_periods=1:start_threshold=-50dB:start_silence=0.02,areverse,"
         f"silenceremove=start_periods=1:start_threshold=-50dB:start_silence=0.06,areverse,"
         f"atempo={tempo:.3f},highpass=f=70,loudnorm=I=-16:TP=-2:LRA=7")
    C.ff("-i", src, "-af", f, "-ar", C.SR, "-ac", 2, dst)


def transcrire(fichiers):
    py = Path.home() / "nexora-creative-data/engine/transcription-venv/bin/python3"
    # PyAV du venv ne lit pas nos WAV : décodage par ffmpeg en tableau 16 kHz, passé directement à Whisper
    code = ("import sys,json,subprocess,numpy as np\nfrom faster_whisper import WhisperModel\nm=WhisperModel('medium',device='cpu',compute_type='int8',cpu_threads=12)\n"
            f"FF={C.FF!r}\n"
            "a=lambda f:np.frombuffer(subprocess.run([FF,'-v','error','-i',f,'-f','f32le','-ac','1','-ar','16000','-'],capture_output=True).stdout,np.float32)\n"
            "print(json.dumps({f:' '.join(s.text.strip() for s in m.transcribe(a(f),language='fr',beam_size=5)[0]) for f in sys.argv[1:]}))")
    r = subprocess.run([str(py), "-c", code, *map(str, fichiers)], capture_output=True, text=True)
    return json.loads(r.stdout.strip().splitlines()[-1]) if r.returncode == 0 else {}


def wer(ref, hyp):
    import re
    n = lambda s: re.sub(r"[^\w\sàâäçéèêëîïôöùûüÿœæ'-]", " ", s.lower().replace("’", "'")).split()
    r, h = n(ref), n(hyp)
    d = list(range(len(h) + 1))
    for i in range(1, len(r) + 1):
        p = d[:]
        d[0] = i
        for j in range(1, len(h) + 1):
            d[j] = min(p[j] + 1, d[j - 1] + 1, p[j - 1] + (r[i - 1] != h[j - 1]))
    return round(d[len(h)] / max(1, len(r)), 3)


def narrer(film, moteur):
    if any(x in moteur for x in INTERDITS):
        raise SystemExit("moteur refusé pour les finales : " + moteur)
    f = C.charger_film(film)
    modele, voix, pre, extra = MOTEURS[moteur]
    if extra == "ref_alexandre":
        extra = ref_alexandre()
    out = C.dossier(film) / "voix" / moteur
    out.mkdir(parents=True, exist_ok=True)
    res = []
    for x in f["narration"]:
        # « dit » : graphie pour le moteur (ex. « Opsis A I »), « texte » : sous-titre ; les virgules deviennent des
        # points de suspension (vraies respirations chez ElevenLabs v3 : débit ≈ 2,2 mots/s sans trop ralentir la bande)
        dit = x.get("dit", x["texte"]).replace(", ", "… ")
        if moteur.startswith("drama3"):  # balise de pause entre les phrases (banc d'écoute : « direction + pauses »)
            dit = x.get("dit", x["texte"]).replace(". ", ". [pause] ")
        brut = out / f"{x['id']}.brut.mp3"
        if not brut.exists() or C.os.environ.get("VOIX_REFAIRE") in ("1", x["id"]) or x["id"] in C.os.environ.get("VOIX_REFAIRE", "").split(","):
            brut.write_bytes(parler(modele, pre + dit, voix, extra))
        tmp = out / f"{x['id']}.t.wav"
        nettoyer(brut, tmp, 1.0)
        d0 = C.duree(tmp)
        mps = mots(x["texte"]) / d0
        tempo = max(0.84, min(1.0, CIBLE_MPS / mps)) if mps > CIBLE_MPS else 1.0
        nettoyer(brut, out / f"{x['id']}.wav", tempo)
        tmp.unlink()
        d = C.duree(out / f"{x['id']}.wav")
        res.append({"id": x["id"], "texte": x["texte"], "duree": round(d, 3), "mots_s": round(mots(x["texte"]) / d, 2), "tempo": round(tempo, 3)})
        print(res[-1], flush=True)
    tr = transcrire([out / f"{r['id']}.wav" for r in res])
    for r in res:
        h = tr.get(str(out / f"{r['id']}.wav"), "")
        r["whisper"], r["wer"] = h, wer(r["texte"], h)
    (out / "voix.json").write_text(json.dumps({"moteur": moteur, "modele": modele, "phrases": res}, ensure_ascii=False, indent=1))
    return res


if __name__ == "__main__":
    choix = json.loads((C.RACINE / "audio-choix.json").read_text())
    narrer(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else choix["voix"])
