"""Film V6 : narration par la voix native de MiniMax H3 (h3-max, RTX 5090 de pc1, tunnel 37288).
Chaque groupe de phrases est un rendu H3 (annonceur filmé en cabine) dont on garde le son ; le timbre est tenu d'un rendu
à l'autre par une référence audio (<Audio 1> = l'essai de casting retenu). Les phrases sont ensuite découpées par Whisper.
  python3 voix_h3.py rendre <fr|en> [groupe…]     rendus → voix/narration/h3-<langue>/brut/<groupe>.mp4
  python3 voix_h3.py decouper <fr|en>              → voix/narration/h3-<langue>/<id>.wav + decoupe.json
"""
import json
import subprocess
import sys
import time
import urllib.request
import uuid
from pathlib import Path

ICI = Path(__file__).resolve().parent
sys.path.insert(0, str(ICI.parent / "video-v3"))
import moteur as M  # noqa: E402

D = Path.home() / "nexora-creative-data/promo/v6-creative/voix"
FF = str(Path.home() / "nexora-creative-data/engine/ffmpeg/ffmpeg-7.0.2-arm64-static/ffmpeg")
NARR = json.loads((ICI / "narration-v6.json").read_text())
PRISM = "10Eros_Max_h3_8stepTURBO_beta7_SingularityV2_ref2va_int8HQ.safetensors"
REF = {"fr": D / "casting/K-h3-natif-a-fr.mp3", "en": D / "casting/K-h3-natif-a-en.mp3"}
GROUPES = {  # groupe : (phrases, images, jeu)
    "g1": (["v01", "v02", "v03"], 141, "teasing and cheeky at first, then a confident punch on the last sentence"),
    "g2": (["v04", "v05"], 141, "a sly rising question, then a fast, gleeful answer that lands hard on the last word"),
    "g3": (["v06", "v07", "v08"], 175, "escalating excitement, each question bigger, each last word slammed with a grin"),
    "g4": (["v09", "v10", "v11", "v12"], 175, "rapid-fire, rhythmic and punchy, like a hype host listing superpowers"),
    "g5": (["v13"], 124, "a sudden hushed, teasing, conspiratorial question, almost a whisper, with a smile"),
    "g6": (["v14", "v15"], 124, "big, triumphant and proud, the final line delivered like a blockbuster tagline"),
}
ACCENT = {"fr": ("French", "Québécois French accent"), "en": ("English", "North American English")}


def prompt(langue, groupe):
    ids, _, jeu = GROUPES[groupe]
    tag, acc = ACCENT[langue]
    texte = " ".join(NARR[langue][i] for i in ids)
    return ("integrated_multimodal_description: [Shot 1] Live-action, cinematic, a medium close-up frames a charismatic male "
            "movie-trailer announcer in his thirties with a gritty, powerful, punchy voice (S1) standing in a dark professional "
            "recording booth in front of a large studio microphone, warm key light, black acoustic foam behind him. His voice is "
            f"exactly the voice of <Audio 1>. He leans into the microphone and speaks in a {acc}, {jeu}, hard attacks, never soft, "
            f"never calm. The announcer (S1) says: <d>[{tag}] {texte}</d> Then he stops talking and smiles silently. The camera "
            "pushes in with small amplitude at slow speed.\n\n"
            "overall_soundscape: A dry, close-miked studio voice with no room echo and no background noise.\n\nnon_diegetic_music: N/A")


def envoyer(chemin):
    lim = uuid.uuid4().hex
    corps = (f"--{lim}\r\nContent-Disposition: form-data; name=\"image\"; filename=\"{chemin.name}\"\r\nContent-Type: audio/mpeg\r\n\r\n").encode() \
        + chemin.read_bytes() + f"\r\n--{lim}\r\nContent-Disposition: form-data; name=\"overwrite\"\r\n\r\ntrue\r\n--{lim}--\r\n".encode()
    return json.loads(M.http(f"{M.H3_COMFY}/upload/image", corps, {"Content-Type": f"multipart/form-data; boundary={lim}"}))["name"]


def rendre(langue, groupe, graine=9101):
    s = {"nom": f"v6voix-{langue}-{groupe}", "prompt": prompt(langue, groupe), "checkpoint": PRISM, "etapes": 8, "decalage": [12, 3],
         "echantillonneur": "euler", "ref": True, "largeur": 960, "hauteur": 544, "images": GROUPES[groupe][1], "graine": graine}
    g = M.graphe_h3(s, None)
    g["la"] = {"class_type": "LoadAudio", "inputs": {"audio": envoyer(REF[langue])}}
    g["gen"]["inputs"]["ref_audios.ref_audio_0"] = ["la", 0]
    from tourner import attendre_place
    attendre_place()
    pid = json.loads(M.http(f"{M.H3_COMFY}/prompt", json.dumps({"prompt": g}).encode(), {"Content-Type": "application/json"}))["prompt_id"]
    t0 = time.time()
    while True:
        time.sleep(4)
        h = json.loads(M.http(f"{M.H3_COMFY}/history/{pid}")).get(pid)
        if not h:
            continue
        st = h.get("status", {})
        if st.get("status_str") == "error":
            raise RuntimeError(json.dumps(st.get("messages"))[-800:])
        if st.get("completed"):
            f = [x for o in h["outputs"].values() for x in o.get("video", []) + o.get("images", [])][0]
            q = urllib.parse.urlencode({"filename": f["filename"], "subfolder": f.get("subfolder", ""), "type": "output"})
            out = D / f"narration/h3-{langue}/brut"
            out.mkdir(parents=True, exist_ok=True)
            (out / f"{groupe}.mp4").write_bytes(M.http(f"{M.H3_COMFY}/view?{q}", timeout=600))
            print(json.dumps({"langue": langue, "groupe": groupe, "secondes": round(time.time() - t0, 1)}), flush=True)
            return


def decouper(langue):
    """Whisper (mots horodatés) aligne chaque phrase sur le son du groupe ; coupe 40 ms avant le premier mot et 120 ms après le dernier."""
    import re
    out = D / f"narration/h3-{langue}"
    py = Path.home() / "nexora-creative-data/engine/transcription-venv/bin/python3"
    code = ("import sys,json,subprocess,numpy as np\nfrom faster_whisper import WhisperModel\n"
            "m=WhisperModel('medium',device='cpu',compute_type='int8',cpu_threads=12)\n"
            f"FF={FF!r}\n"
            "a=lambda f:np.frombuffer(subprocess.run([FF,'-v','error','-i',f,'-f','f32le','-ac','1','-ar','16000','-'],capture_output=True).stdout,np.float32)\n"
            "r={}\n"
            "for f in sys.argv[2:]:\n"
            " seg,_=m.transcribe(a(f),language=sys.argv[1],word_timestamps=True,beam_size=5)\n"
            " r[f]=[(w.word,w.start,w.end) for s in seg for w in s.words]\n"
            "print(json.dumps(r))")
    fichiers = [str(out / "brut" / f"{g}.mp4") for g in GROUPES if (out / "brut" / f"{g}.mp4").exists()]
    mots = json.loads(subprocess.run([str(py), "-c", code, langue, *fichiers], capture_output=True, text=True).stdout.strip().splitlines()[-1])
    norm = lambda s: re.sub(r"[^\w']", "", s.lower().replace("’", "'"))
    res = {}
    for g, (ids, _, _) in GROUPES.items():
        f = str(out / "brut" / f"{g}.mp4")
        if f not in mots:
            continue
        w = []
        for x in mots[f]:  # Whisper coupe « l'IA » en « l » + « 'IA » : on recolle
            if w and (x[0].startswith("'") or x[0].startswith("’")):
                w[-1] = (w[-1][0] + x[0], w[-1][1], x[2])
            else:
                w.append(tuple(x))
        k = 0
        for i in ids:
            n = len([x for x in NARR[langue][i].replace("…", " ").split() if norm(x)])
            bloc = w[k:k + n]
            k += n
            if not bloc:
                continue
            t0, t1 = max(0, bloc[0][1] - 0.04), bloc[-1][2] + 0.12
            subprocess.run([FF, "-v", "error", "-y", "-ss", f"{t0:.3f}", "-to", f"{t1:.3f}", "-i", f, "-vn", "-ac", "1", "-ar", "48000",
                            "-af", "highpass=f=70", str(out / f"{i}.wav")], check=True)
            res[i] = {"groupe": g, "debut": round(t0, 3), "fin": round(t1, 3), "entendu": "".join(x[0] for x in bloc).strip(), "texte": NARR[langue][i]}
    (out / "decoupe.json").write_text(json.dumps(res, ensure_ascii=False, indent=1))
    for i, r in res.items():
        print(i, r["fin"] - r["debut"], "|", r["entendu"], "|", r["texte"])


if __name__ == "__main__":
    import urllib.parse  # noqa: F401
    a = sys.argv[1:]
    if a[0] == "rendre":
        for g in a[2:] or list(GROUPES):
            rendre(a[1], g)
    elif a[0] == "decouper":
        decouper(a[1])
