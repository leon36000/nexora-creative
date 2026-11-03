"""Travailleur de synthèse vocale exécuté sur pc1 (un venv par moteur).

Usage : <venv>/bin/python moteur.py <moteur> <travail.json>
travail.json = {"items": [{"id", "texte", "role", "sortie", "graine"}], "reglages": {...}}
Écrit chaque WAV (fréquence native du moteur) et une ligne JSON par phrase sur la sortie standard.
"""
import json
import os
import sys
import time

import numpy as np
import soundfile as sf
import torch

RACINE = os.path.dirname(os.path.abspath(__file__))
REF = {
    "narrateur": (os.path.join(RACINE, "ref", "alexandre.wav"),
                  "De l'accueil aux ventes, du terrain aux finances, du marketing à la direction. "
                  "Une entreprise pensée comme un ensemble. Votre entreprise avance. Chaque minute compte. Chaque décision aussi."),
    "assistant": (os.path.join(RACINE, "ref", "adam.wav"),
                  "Votre entreprise avance. Chaque minute compte. Voici Opsys AI par Nexora. "
                  "Une soumission, un chantier, des coûts plus clairs."),
}
torch.set_num_threads(int(os.environ.get("VOIX_FILS", "12")))


def charger(moteur, r):
    if moteur == "chatterbox":
        from chatterbox.mtl_tts import ChatterboxMultilingualTTS
        m = ChatterboxMultilingualTTS.from_pretrained(device="cpu")

        def dire(texte, role):
            w = m.generate(texte, language_id="fr", audio_prompt_path=REF[role][0],
                           exaggeration=r.get("expressivite", 0.55), cfg_weight=r.get("cfg", 0.4),
                           temperature=r.get("temperature", 0.75))
            return w.squeeze(0).cpu().numpy(), m.sr
        return dire
    if moteur == "xtts":
        from huggingface_hub import snapshot_download
        from TTS.tts.configs.xtts_config import XttsConfig
        from TTS.tts.models.xtts import Xtts
        d = snapshot_download("coqui/XTTS-v2")
        c = XttsConfig()
        c.load_json(os.path.join(d, "config.json"))
        m = Xtts.init_from_config(c)
        m.load_checkpoint(c, checkpoint_dir=d, use_deepspeed=False)
        lat = {k: m.get_conditioning_latents(audio_path=[v[0]]) for k, v in REF.items()}

        def dire(texte, role):
            g, s = lat[role]
            o = m.inference(texte, "fr", g, s, temperature=r.get("temperature", 0.7), speed=r.get("vitesse", 1.0),
                            enable_text_splitting=True)
            return np.asarray(o["wav"]), 24000
        return dire
    if moteur == "kokoro":
        from kokoro import KPipeline
        p = KPipeline(lang_code="f", repo_id="hexgrad/Kokoro-82M")

        def dire(texte, role):
            morceaux = [a.numpy() for _, _, a in p(texte, voice="ff_siwis", speed=r.get("vitesse", 1.0))]
            return np.concatenate(morceaux), 24000
        return dire
    if moteur == "f5":
        from f5_tts.api import F5TTS
        m = F5TTS(model=r.get("modele", "F5TTS_Base"), ckpt_file=r["ckpt"], vocab_file=r["vocab"], device="cpu")
        # F5 tronque les références > 12 s : prise courte de 7 s pour le narrateur.
        ref = dict(REF, narrateur=(os.path.join(RACINE, "ref", "alexandre-court.wav"),
                                   "De l'accueil aux ventes, du terrain aux finances, du marketing à la direction. "
                                   "Une entreprise pensée comme un ensemble."))

        def dire(texte, role):
            w, sr, _ = m.infer(ref[role][0], ref[role][1], texte, nfe_step=r.get("nfe", 32),
                               speed=r.get("vitesse", 1.0), remove_silence=False, show_info=lambda *a: None)
            return np.asarray(w), sr
        return dire
    if moteur == "qwen3":
        from qwen_tts import Qwen3TTSModel
        m = Qwen3TTSModel.from_pretrained(r.get("modele", "Qwen/Qwen3-TTS-12Hz-1.7B-Base"),
                                          device_map="cpu", dtype=torch.float32)
        invites = {k: m.create_voice_clone_prompt(ref_audio=v[0], ref_text=v[1]) for k, v in REF.items()}

        def dire(texte, role):
            ws, sr = m.generate_voice_clone(text=texte, language="French", voice_clone_prompt=invites[role],
                                            non_streaming_mode=True)
            return np.asarray(ws[0]), sr
        return dire
    raise SystemExit(f"moteur inconnu : {moteur}")


def main():
    moteur = sys.argv[1]
    travail = json.load(open(sys.argv[2], encoding="utf-8"))
    t0 = time.time()
    dire = charger(moteur, travail.get("reglages", {}))
    print(json.dumps({"chargement": round(time.time() - t0, 1)}), flush=True)
    for it in travail["items"]:
        torch.manual_seed(it.get("graine", 0))
        t = time.time()
        w, sr = dire(it["texte"], it.get("role", "narrateur"))
        os.makedirs(os.path.dirname(it["sortie"]), exist_ok=True)
        sf.write(it["sortie"], w.astype(np.float32), sr)
        print(json.dumps({"id": it["id"], "sortie": it["sortie"], "secondes_calcul": round(time.time() - t, 2),
                          "duree": round(len(w) / sr, 2)}), flush=True)


if __name__ == "__main__":
    main()
