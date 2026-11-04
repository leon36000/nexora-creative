"""Banc ASR (essais-20261104) : python asr.py <modele> <sortie.json> fichier... ; modele = turbo | medium-cpu | parakeet | parakeet-cpu"""
import sys, json, time, subprocess, os, threading
import numpy as np
mod, sortie, fichiers = sys.argv[1], sys.argv[2], sys.argv[3:]
def pcm(f):
    b = subprocess.run(["ffmpeg","-v","error","-i",f,"-f","f32le","-ac","1","-ar","16000","pipe:1"],capture_output=True,check=True).stdout
    return np.frombuffer(b, np.float32)
pic = [0]; stop = threading.Event()
def smi():
    while not stop.is_set():
        try:
            o = subprocess.run(["nvidia-smi","-i",os.environ.get("SMI_GPU","1"),"--query-gpu=memory.used","--format=csv,noheader,nounits"],capture_output=True,text=True).stdout
            pic[0] = max(pic[0], int(o.split()[0]))
        except Exception: pass
        stop.wait(0.3)
threading.Thread(target=smi, daemon=True).start()
t0 = time.time()
if mod in ("turbo","medium-cpu","large"):
    from faster_whisper import WhisperModel
    if mod == "turbo": m = WhisperModel("deepdml/faster-whisper-large-v3-turbo-ct2", device="cuda", compute_type="float16")
    elif mod == "large": m = WhisperModel("Systran/faster-whisper-large-v3", device="cuda", compute_type="float16")
    else: m = WhisperModel("Systran/faster-whisper-medium", device="cpu", compute_type="int8", cpu_threads=4)
    def run(a):
        segs, info = m.transcribe(a, language="fr", vad_filter=True, word_timestamps=True)
        mots = []
        for s in segs:
            for w in (s.words or []): mots.append([w.word.strip(), round(w.start,2), round(w.end,2)])
        return mots
else:
    import onnx_asr, onnxruntime as ort
    prov = ["CUDAExecutionProvider","CPUExecutionProvider"] if mod == "parakeet" else ["CPUExecutionProvider"]
    m = onnx_asr.load_model("nemo-parakeet-tdt-0.6b-v3", quantization="int8", providers=prov).with_timestamps()
    def run(a):
        mots = []
        # coupes au creux d'energie le plus proche de 22-30 s (evite de couper un mot)
        coupes=[0]
        while len(a)-coupes[-1] > 30*16000:
            d=coupes[-1]+22*16000; f=coupes[-1]+30*16000
            seg=np.abs(a[d:f]); n=len(seg)//1600; e=seg[:n*1600].reshape(n,1600).mean(1)
            coupes.append(d+int(np.argmin(e))*1600+800)
        coupes.append(len(a))
        for i, j in zip(coupes[:-1], coupes[1:]):
            r = m.recognize(a[i:j])
            toks, ts = r.tokens, r.timestamps
            cur = None
            for tk, t in zip(toks, ts):
                off = i/16000 + float(t)
                if tk.startswith(" ") or cur is None:
                    if cur: mots.append(cur)
                    cur = [tk.strip(), round(off,2), round(off,2)]
                else: cur[0] += tk; 
                if cur: cur[2] = round(off+0.08,2)
            if cur: mots.append(cur)
        return mots
charge = round(time.time()-t0, 1)
res = {"modele": mod, "chargement_s": charge, "fichiers": {}}
run(np.zeros(16000*3, np.float32)) if False else None
for f in fichiers:
    a = pcm(f); d = len(a)/16000
    t = time.time(); mots = run(a); dt = time.time()-t
    res["fichiers"][os.path.basename(f)] = {"duree_s": round(d,1), "temps_s": round(dt,2), "x_temps_reel": round(d/dt,1) if dt else None, "nb_mots": len(mots), "texte": " ".join(w[0] for w in mots), "mots": mots}
    print(mod, os.path.basename(f), "duree", round(d,1), "temps", round(dt,2), "xRT", round(d/max(dt,1e-3),1), "mots", len(mots), flush=True)
stop.set(); res["vram_pic_mo"] = pic[0]
json.dump(res, open(sortie,"w"), ensure_ascii=False)
print("VRAM pic (nvidia-smi, mo):", pic[0], "chargement", charge)
