"""Banc de voix, manche 2 (04/11, demande du fondateur) : Mistral Voxtral TTS (3-0 et 2603, clonage), MiniMax Speech 2.8 HD,
MAI-Voice-2.1, Fish S2.1 Pro (clonage), surtout pour la voix féminine de l'adjointe ; mêmes répliques et même oreille que la manche 1."""
import json, sys, traceback
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import voix as V
from banc_voix import LIGNES

DIR_F = "Adjointe québécoise chaleureuse, professionnelle et efficace, accent québécois naturel, rythme vif."
DIR_N = "Narrateur de publicité québécoise, énergique et punché, voix qui sourit, accent québécois naturel."
M = [
    ("adjointe", "or:microsoft/mai-voice-2.1|voice=fr-CA-SylvieNeural", DIR_F), ("comptable", "or:microsoft/mai-voice-2.1|voice=fr-CA-SylvieNeural", DIR_F),
    ("narrateur", "or:microsoft/mai-voice-2.1|voice=fr-CA-AntoineNeural", DIR_N), ("narrateur", "or:microsoft/mai-voice-2.1|voice=fr-CA-ThierryNeural", DIR_N),
    ("narrateur", "or:microsoft/mai-voice-2.1|voice=fr-CA-JeanNeural", DIR_N), ("administrateur", "or:microsoft/mai-voice-2.1|voice=fr-CA-JeanNeural", DIR_N),
    ("adjointe", "or:mistralai/voxtral-mini-tts-3-0|voice=voice_592", DIR_F), ("adjointe", "or:mistralai/voxtral-mini-tts-3-0|voice=voice_3137", DIR_F),
    ("adjointe", "or:mistralai/voxtral-mini-tts-3-0|voice=voice_589", DIR_F), ("adjointe", "or:mistralai/voxtral-mini-tts-3-0|voice=voice_3141", DIR_F),
    ("adjointe", "or:mistralai/voxtral-mini-tts-2603|voice=fr_marie_happy", DIR_F), ("adjointe", "or:microsoft/mai-voice-2.1|voice=fr-FR-DeniseNeural", DIR_F),
    ("adjointe", "or:mistralai/voxtral-mini-tts-3-0|ref=jeannemance", DIR_F), ("adjointe", "or:mistralai/voxtral-mini-tts-3-0|ref=marieline", DIR_F),
    ("adjointe", "or:mistralai/voxtral-mini-tts-2603|ref=jeannemance", DIR_F), ("adjointe", "or:mistralai/voxtral-mini-tts-3-0|voice=marie", DIR_F),
    ("adjointe", "or:fish-audio/s2.1-pro|ref=jeannemance|instr", DIR_F), ("adjointe", "or:fish-audio/s2.1-pro|ref=marieline|instr", DIR_F),
    ("adjointe", "or:minimax/speech-2.8-hd|voice=French_FemaleAnchor", DIR_F), ("adjointe", "or:minimax/speech-2.8-hd|ref=jeannemance", DIR_F),
    ("adjointe", "or:microsoft/mai-voice-2.1|voice=fr-FR-Vivienne", DIR_F),
    ("comptable", "or:mistralai/voxtral-mini-tts-3-0|ref=amelie", DIR_F), ("comptable", "or:fish-audio/s2.1-pro|ref=amelie|instr", DIR_F),
    ("narrateur", "or:mistralai/voxtral-mini-tts-3-0|ref=frederic", DIR_N), ("narrateur", "or:mistralai/voxtral-mini-tts-2603|ref=frederic", DIR_N),
    ("narrateur", "or:fish-audio/s2.1-pro|ref=frederic|instr", DIR_N), ("narrateur", "or:minimax/speech-2.8-hd|voice=French_MaleNarrator", DIR_N),
    ("narrateur", "or:microsoft/mai-voice-2.1|voice=fr-FR-Marc", DIR_N),
]

def main():
    out = V.TRAVAIL / "casting" / "banc2.json"
    res = json.loads(out.read_text()) if out.exists() else {"prises": []}
    faits = {(p["role"], p["moteur_court"]) for p in res["prises"]}
    taches = []
    for role, mot, d in M:
        if (role, mot) in faits:
            continue
        nom = mot.split(":", 1)[1].replace("/", "_").replace("|", "_").replace("=", "-")
        taches.append(("casting2", f"{role}-{nom}"[:90], mot, LIGNES[role], d, 1.0, 1))
    for m in V.lot(taches, paralleles=5):
        role = m["id"].split("-")[0]
        mc = next(x[1] for x in M if f"{x[0]}-{x[1].split(':',1)[1].replace('/', '_').replace('|', '_').replace('=', '-')}"[:90] == m["id"])
        m.update({"role": role, "moteur_court": mc}); m.pop("mots", None)
        res["prises"].append(m)
        print(m["id"], m.get("emr"), (m.get("oreille") or {}).get("moyennes"), flush=True)
    out.write_text(json.dumps(res, ensure_ascii=False, indent=1))

if __name__ == "__main__":
    main()
