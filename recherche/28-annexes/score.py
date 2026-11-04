import json,sys,re,jiwer,unicodedata
ref40=open("/srv/nexora-gpu/essais-20261104/ref.txt").read()
def norm(t):
    t=t.lower().replace("’","'").replace("-"," ").replace("'"," ")
    t=unicodedata.normalize("NFC",t); t=re.sub(r"[^\w\s]"," ",t); return " ".join(t.split())
def ref(name):
    if name.startswith("p40"): return norm(ref40)
    if name.startswith("parole"): return norm(" ".join([ref40]*int(re.findall(r"\d+",name)[0]))) 
    if name.startswith(("c_","n_")): return "trois mots et tout explose"
    return None
for f in sys.argv[1:]:
    d=json.load(open(f)); print("==",d["modele"],"VRAM",d.get("vram_pic_mo"),"charge",d["chargement_s"])
    tot={"c":[0,0],"n":[0,0]}
    for k,v in d["fichiers"].items():
        r=ref(k); 
        if r is None:
            print(f"{k:34s} dur {v['duree_s']:6.1f}s xRT {v['x_temps_reel']:7.1f} mots {v['nb_mots']}  (hallucination si >0)"); continue
        w=jiwer.wer(r,norm(v["texte"]))
        print(f"{k:34s} dur {v['duree_s']:6.1f}s xRT {v['x_temps_reel']:7.1f} WER {w*100:5.1f}%")
