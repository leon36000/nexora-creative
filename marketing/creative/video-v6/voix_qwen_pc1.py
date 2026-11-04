"""Film V6 : candidat local Qwen3-TTS 1.7B VoiceDesign (Apache-2.0), exécuté sur pc1 en CPU (la 5090 reste aux plans).
La voix est « dessinée » par une consigne en langage naturel (aucun clonage).
  scp ce fichier sur pc1 puis : <venv qwen3>/bin/python voix_qwen_pc1.py <dossier-sortie>
"""
import os, sys, time, json
import numpy as np, soundfile as sf, torch
os.environ.setdefault("HF_HOME", "/run/media/pc1/Infrastructure/NexoraStudioWork/films-v2/voix/hf")
torch.set_num_threads(24)
from qwen_tts import Qwen3TTSModel
TEXTE = {"fr": "Trois mots. Même mal écrits. Creative fait le reste. Un dragon ? Réglé. Une bataille dans l'espace ? Réglé. T'écris trois mots. Creative fait le film.",
         "en": "Three words. Typos and all. Creative does the rest. A dragon? Done. A space battle? Done. You type three words. Creative makes the movie."}
VOIX = {
 "a": "A male movie-trailer announcer in his thirties, gritty and powerful voice, very energetic and punchy, big grin in the voice, fast pace with hard attacks and short dry pauses before each punchline. Never soft, never calm.",
 "b": "A playful high-energy male hype host in his late twenties, bright slightly raspy voice, excited and cheeky, speaking fast like a stand-up comedian hyping a crowd.",
}
LANG = {"fr": "French", "en": "English"}
out = sys.argv[1]; os.makedirs(out, exist_ok=True)
t = time.time()
m = Qwen3TTSModel.from_pretrained(os.environ.get("QWEN_VD", "Qwen/Qwen3-TTS-12Hz-1.7B-VoiceDesign"), device_map="cpu", dtype=torch.float32)
print(json.dumps({"chargement": round(time.time() - t, 1)}), flush=True)
for v, instr in VOIX.items():
    for l, txt in TEXTE.items():
        acc = " Québécois French accent." if l == "fr" else ""
        torch.manual_seed(7)
        t = time.time()
        w, sr = m.generate_voice_design(text=txt, instruct=instr + acc, language=LANG[l])
        f = os.path.join(out, f"J-qwen3tts-voicedesign-{v}-{l}.wav")
        sf.write(f, np.asarray(w[0], dtype=np.float32), sr)
        print(json.dumps({"fichier": f, "secondes_calcul": round(time.time() - t, 1)}), flush=True)
