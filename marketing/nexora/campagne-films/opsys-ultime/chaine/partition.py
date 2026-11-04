"""Musique écrite pour le montage (consigne du fondateur du 04/11) : carte des temps forts → plusieurs pistes par plusieurs moteurs
→ conformation au montage (la musique frappe sur les temps forts : décalage global puis déformation temporelle par segments entre
ancres, vrais silences) → mesures (alignement coups-coupes, dynamique) → juge audio-vidéo sur le film mixé → choix.

  python3 partition.py carte <equipe> [version]            carte des temps forts (équipe, sinon dérivée de l'EditPlan et de l'annexe)
  python3 partition.py generer <equipe> [id …]             candidats de dossier.musique.candidats : lyria | music3 | acestep
  python3 partition.py conformer <equipe> <id> [version]   → musique/conforme-<id>-<version>.wav + rapport
  python3 partition.py evaluer <equipe> [version]          film brouillon par candidat, mesures + juge, choix du meilleur (choix.json)

Moteurs : Lyria 3 Pro (OpenRouter), MiniMax-Music3 (local, GB10, ComfyUI 37188), ACE-Step (local, GB10, script ace.sh).
"""
import json
import subprocess
import sys
import time
from pathlib import Path

import numpy as np

import tourner as T
sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "creative/video-v3"))

ACE = Path("/media/pc6/Storage/Nexora/travail/ace-step/ace.sh")
SR = 48000


# ---------------------------------------------------------------------------------------------------------------- carte
def coupes(plan):
    deb, tot, t = [], 0, 0
    for i, c in enumerate(plan["video"]):
        tr = c.get("transition_in") or {}
        rec = tr.get("duree_f", 0) if i and tr.get("type", "cut") != "cut" else 0
        t -= rec
        deb.append(t / 24)
        t += c["duree_f"]
    return deb[1:], t / 24


def carte(eq, version="long"):
    D = T.dossier(eq)
    P = D["montage"][version]
    ann = (D.get("annexe") or {}).get(version) or {}
    cs, duree = coupes(P)
    m = D.get("musique", {})
    c = (m.get("carte") or {}).get(version) if isinstance(m.get("carte"), dict) and version in (m.get("carte") or {}) else m.get("carte") if version == "long" else None
    if c and c.get("impacts"):
        out = {"impacts": sorted(float(x) for x in c["impacts"]), "trous": c.get("trous", []), "montees": c.get("montees", []),
               "climax": c.get("climax"), "fin": c.get("fin", duree), "source": "équipe"}
    else:
        imp = []
        if version == "long":
            imp += [float(x["t_s"]) for x in m.get("coups", []) if isinstance(x, dict) and "t_s" in x]
        imp += [x["debut_f"] / 24 for x in ann.get("sfx", []) if x.get("type") in ("impact", "boom", "chute", "explosion")]
        imp += [x["debut_f"] / 24 + 0.08 for x in ann.get("incrustations", []) if x.get("type") == "flash"]
        imp = sorted(set(round(t, 2) for t in imp if 0.2 < t < duree - 0.2))
        fus = []
        for t in imp:  # fusion des coups à moins de 0,4 s
            if not fus or t - fus[-1] > 0.4:
                fus.append(t)
        out = {"impacts": fus, "trous": [], "montees": [[x["debut_f"] / 24, x["debut_f"] / 24 + float(x.get("duree_s", 1.0))]
                                                      for x in ann.get("sfx", []) if x.get("type") == "montee"],
               "climax": None, "fin": duree, "source": "dérivée (coups du dossier, impacts et flashs de l'annexe)"}
    out["coupes"] = [round(x, 3) for x in cs]
    out["duree"] = round(duree, 3)
    return out


# ------------------------------------------------------------------------------------------------------------- analyse
def lire(f, sr=22050):
    raw = subprocess.run([T.FF, "-v", "error", "-i", str(f), "-ac", "1", "-ar", str(sr), "-f", "f32le", "-"], capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.float32)


def attaques(x, sr=22050, hop=220):
    """Enveloppe d'attaques (flux spectral, 100 valeurs/s), normalisée 0..1."""
    fen = np.hanning(1024)
    n = (len(x) - 1024) // hop
    S = np.abs(np.fft.rfft(np.stack([x[i * hop:i * hop + 1024] * fen for i in range(n)]), axis=1))
    flux = np.maximum(0, np.diff(np.log1p(S * 10), axis=0)).sum(1)
    flux = (flux - np.convolve(flux, np.ones(30) / 30, "same")).clip(0)
    return flux / (np.percentile(flux, 99.5) + 1e-9)


def pics(env, seuil=0.35, dist=12):
    p = [i for i in range(1, len(env) - 1) if env[i] >= seuil and env[i] >= env[i - 1] and env[i] >= env[i + 1]]
    out = []
    for i in p:
        if not out or i - out[-1] >= dist:
            out.append(i)
        elif env[i] > env[out[-1]]:
            out[-1] = i
    return np.array(out) / 100.0


def alignement(temps, env, decalage=0.0, tol=2 / 24):
    """Part des temps (coupes ou impacts) qui tombent à ± tol d'une attaque forte de la musique (décalée de `decalage`)."""
    pk = pics(env)
    if not len(temps) or not len(pk):
        return 0.0
    return round(float(np.mean([np.min(np.abs(pk - (t + decalage))) <= tol for t in temps])), 3)


def dynamique(f):
    r = subprocess.run([T.FF, "-hide_banner", "-i", str(f), "-af", "ebur128", "-f", "null", "-"], capture_output=True, text=True).stderr
    lra = [l for l in r.splitlines() if l.strip().startswith("LRA:")]
    x = lire(f)
    e = np.array([20 * np.log10(np.sqrt(np.mean(x[k:k + 11025] ** 2)) + 1e-6) for k in range(0, len(x) - 11025, 11025)])
    e = e[e > -60]
    return {"lra_lu": float(lra[-1].split()[1]) if lra else None, "ecart_energie_db": round(float(np.percentile(e, 95) - np.percentile(e, 10)), 1) if len(e) else None}


# ----------------------------------------------------------------------------------------------------------- moteurs
def music3(eq, cid, prompt, duree, graine=7):
    import h3
    g = {
        "u": {"class_type": "UNETLoader", "inputs": {"unet_name": "minimax_music3_dit_int8_convrot.safetensors", "weight_dtype": "default"}},
        "c": {"class_type": "CLIPLoader", "inputs": {"clip_name": "minimax_music3_text_encoder_pruned_int8_convrot.safetensors", "type": "minimax", "device": "default"}},
        "v": {"class_type": "VAELoader", "inputs": {"vae_name": "minimax_music3_dav.safetensors"}},
        "enc": {"class_type": "MiniMaxMusic3TextEncode", "inputs": {"clip": ["c", 0], "caption": prompt, "lyrics": "[Instrumental]", "seed": graine,
                                                                    "max_duration": float(min(300, duree)), "cfg_scale": 1.7, "top_k": 50}},
        "neg": {"class_type": "ConditioningZeroOut", "inputs": {"conditioning": ["enc", 0]}},
        "lat": {"class_type": "EmptyMiniMaxMusic3LatentAudio", "inputs": {"seconds": ["enc", 1], "batch_size": 1}},
        "ks": {"class_type": "KSampler", "inputs": {"model": ["u", 0], "seed": graine, "steps": 30, "cfg": 1.7, "sampler_name": "euler", "scheduler": "simple",
                                                    "positive": ["enc", 0], "negative": ["neg", 0], "latent_image": ["lat", 0], "denoise": 1}},
        "dec": {"class_type": "VAEDecodeAudio", "inputs": {"samples": ["ks", 0], "vae": ["v", 0]}},
        "save": {"class_type": "SaveAudio", "inputs": {"audio": ["dec", 0], "filename_prefix": f"opsys-ultime/{eq}/musique-{cid}"}},
    }
    comfy = h3.IMG_COMFY
    t0 = time.time()
    pid = json.loads(h3.http(f"{comfy}/prompt", json.dumps({"prompt": g}).encode(), {"Content-Type": "application/json"}))["prompt_id"]
    while True:
        time.sleep(5)
        h = json.loads(h3.http(f"{comfy}/history/{pid}")).get(pid)
        if not h:
            continue
        st = h.get("status", {})
        if st.get("status_str") == "error":
            raise RuntimeError(json.dumps(st.get("messages"))[-800:])
        if st.get("completed"):
            break
    f = [x for o in h["outputs"].values() for x in o.get("audio", [])][0]
    import urllib.parse
    q = urllib.parse.urlencode({"filename": f["filename"], "subfolder": f.get("subfolder", ""), "type": f.get("type", "output")})
    data = h3.http(f"{comfy}/view?{q}", timeout=600)
    brut = T.dossier_travail(eq, "musique") / f"{cid}-brut{Path(f['filename']).suffix}"
    brut.write_bytes(data)
    return brut, round(time.time() - t0, 1), 0.0


def generer(eq, ids=None):
    import musique as MU
    D = T.dossier(eq)
    cands = D.get("musique", {}).get("candidats") or []
    d = T.dossier_travail(eq, "musique")
    for c in cands:
        if ids and c["id"] not in ids:
            continue
        wav = d / f"{c['id']}.wav"
        if wav.exists():
            continue
        mot, pr, du = c.get("moteur", "lyria"), c["prompt"], float(c.get("duree_s", 150))
        t0 = time.time()
        try:
            if mot == "lyria":
                octets, cout = MU.lyria(pr)
                brut = d / f"{c['id']}-brut.mp3"
                brut.write_bytes(octets)
            elif mot == "music3":
                brut, _, cout = music3(eq, c["id"], pr, du, int(c.get("graine", 7)))
            elif mot == "acestep":
                brut = d / f"{c['id']}-brut.wav"
                subprocess.run(["bash", str(ACE), pr, str(int(du)), str(brut), str(int(c.get("graine", 7))), "instrumental"], check=True,
                               capture_output=True, timeout=3600)
                cout = 0.0
            else:
                print("moteur inconnu", mot, flush=True)
                continue
            subprocess.run([T.FF, "-v", "error", "-y", "-i", str(brut), "-ar", str(SR), "-ac", "2", str(wav)], check=True)
            g = MU.grille(wav)
            g.update({"id": c["id"], "moteur": mot, "prompt": pr, "cout_usd": cout, "secondes": round(time.time() - t0, 1)})
            (d / f"{c['id']}.json").write_text(json.dumps(g, ensure_ascii=False, indent=1))
            with (T.TRAVAIL / "journal-api.jsonl").open("a") as fh:
                fh.write(json.dumps({"equipe": eq, "quoi": f"musique {c['id']}", "moteur": mot, "cout_usd": cout, "secondes": g["secondes"], "duree_s": g["duree_s"]}) + "\n")
            print("candidat", c["id"], mot, g["bpm"], "BPM", g["duree_s"], "s", flush=True)
        except Exception as e:
            print("ECHEC musique", c["id"], mot, str(e)[:300], flush=True)


# --------------------------------------------------------------------------------------------------------- conformer
def etirer(x, sr, ratio):
    """Étire (ratio > 1 : plus long) en gardant la hauteur (rubberband de ffmpeg)."""
    import tempfile
    with tempfile.TemporaryDirectory(dir=str(T.TRAVAIL / "tmp")) as td:
        a, b = Path(td) / "a.f32", Path(td) / "b.f32"
        x.astype(np.float32).tofile(a)
        subprocess.run([T.FF, "-v", "error", "-y", "-f", "f32le", "-ar", str(sr), "-ac", "2", "-i", str(a), "-af", f"rubberband=tempo={1 / ratio:.5f}",
                        "-f", "f32le", "-ar", str(sr), "-ac", "2", str(b)], check=True)
        return np.fromfile(b, np.float32).reshape(-1, 2)


def conformer(eq, cid, version="long"):
    d = T.TRAVAIL / eq / "musique"
    src = d / f"{cid}.wav"
    if not src.exists():
        src = d / f"lyria-{cid}.wav"
    k = carte(eq, version)
    duree, imp, cs = k["duree"], k["impacts"], k["coupes"]
    x = lire(src)
    env = attaques(x)
    L = len(x) / 22050
    # 1) décalage global : maximise la force des attaques sous les impacts (+ un peu sous les coupes)
    meilleurs = []
    for o in np.arange(0, max(0.05, L - min(duree, L) + 0.01), 0.05):
        sc = sum(env[max(0, int((t + o) * 100) - 8):int((t + o) * 100) + 9].max(initial=0) for t in imp if (t + o) * 100 < len(env))
        sc += 0.3 * sum(env[max(0, int((t + o) * 100) - 4):int((t + o) * 100) + 5].max(initial=0) for t in cs if (t + o) * 100 < len(env))
        meilleurs.append((sc, o))
    o = max(meilleurs)[1] if meilleurs else 0.0
    avant = {"impacts": alignement(imp, env, o), "coupes": alignement(cs, env, o)}
    # 2) ancres : pour chaque impact, l'attaque forte la plus proche à ± 0,5 s ; segments étirés de 0,88 à 1,12
    pk = pics(env, 0.3)
    ancres = [(0.0, o)]
    for t in imp:
        if t <= ancres[-1][0] + 0.8:
            continue
        cand = pk[np.abs(pk - (t + o)) <= 0.5] if len(pk) else []
        if not len(cand):
            continue
        m = float(cand[np.argmin(np.abs(cand - (t + o)))])
        r = (t - ancres[-1][0]) / max(0.05, m - ancres[-1][1])
        if 0.88 <= r <= 1.12 and m > ancres[-1][1]:
            ancres.append((t, m))
    # 3) rendu stéréo 48 kHz : segments étirés bout à bout, puis la fin telle quelle
    y = lire_st(src)
    morceaux = []
    for (t0, m0), (t1, m1) in zip(ancres, ancres[1:]):
        seg = y[int(m0 * SR):int(m1 * SR)]
        morceaux.append(etirer(seg, SR, (t1 - t0) / max(1e-3, m1 - m0)) if abs((t1 - t0) - (m1 - m0)) > 0.004 else seg)
    tf, mf = ancres[-1]
    reste = y[int(mf * SR): int((mf + (duree - tf) + 0.5) * SR)]
    morceaux.append(reste)
    out = morceaux[0]
    for s in morceaux[1:]:  # fondus enchaînés de 10 ms aux jointures
        n = min(480, len(out), len(s))
        if n:
            r_ = np.linspace(0, 1, n)[:, None]
            out = np.concatenate([out[:-n], out[-n:] * (1 - r_) + s[:n] * r_, s[n:]])
        else:
            out = np.concatenate([out, s])
    N = int(duree * SR)
    if len(out) < N:  # musique trop courte : silence (le montage décide)
        out = np.concatenate([out, np.zeros((N - len(out), 2), np.float32)])
    out = out[:N].copy()
    # 4) vrais trous et fin
    for a, b in k.get("trous", []):
        i0, i1 = int(a * SR), int(b * SR)
        f20 = int(0.02 * SR)
        out[max(0, i0 - f20):i0] *= np.linspace(1, 0, min(f20, i0))[:, None]
        out[i0:i1] = 0
        out[i1:i1 + f20] *= np.linspace(0, 1, len(out[i1:i1 + f20]))[:, None]
    fo = int(1.2 * SR)
    out[-fo:] *= np.linspace(1, 0, fo)[:, None]
    f = d / f"conforme-{cid}-{version}.wav"
    import sfx_v3
    sfx_v3.ecrire(out / max(1.0, float(np.abs(out).max()) / 0.98), str(f))
    env2 = attaques(lire(f))
    rap = {"candidat": cid, "version": version, "decalage_s": round(o, 2), "ancres": len(ancres) - 1, "impacts": len(imp),
           "alignement_avant": avant, "alignement_apres": {"impacts": alignement(imp, env2), "coupes": alignement(cs, env2)},
           "dynamique": dynamique(f), "carte": k["source"], "fichier": str(f)}
    (d / f"conforme-{cid}-{version}.json").write_text(json.dumps(rap, ensure_ascii=False, indent=1))
    print(json.dumps({k2: rap[k2] for k2 in ("candidat", "decalage_s", "ancres", "impacts", "alignement_avant", "alignement_apres", "dynamique")}, ensure_ascii=False), flush=True)
    return rap


def lire_st(f):
    raw = subprocess.run([T.FF, "-v", "error", "-i", str(f), "-ac", "2", "-ar", str(SR), "-f", "f32le", "-"], capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.float32).reshape(-1, 2).copy()


# ----------------------------------------------------------------------------------------------------------- évaluer
def evaluer(eq, version="long"):
    import juge
    import monter
    d = T.TRAVAIL / eq / "musique"
    D = T.dossier(eq)
    cands = [c["id"] for c in (D.get("musique", {}).get("candidats") or []) if (d / f"{c['id']}.wav").exists()]
    c0 = T.choix(eq)
    res = {}
    for cid in cands:
        rap = conformer(eq, cid, version)
        c = T.choix(eq)
        m = c.get("musique") if isinstance(c.get("musique"), dict) else {}
        c["musique"] = {**m, version: f"conforme-{cid}-{version}.wav"}
        T.ecrire_choix(eq, c)
        film = monter.construire(eq, version, brouillon=True, sortie=str(T.TRAVAIL / eq / "montage" / f"essai-musique-{cid}-{version}.mp4"), jobs=12)
        j = juge.film(film["film"], f"Publicité OPSYS-AI de l'équipe {eq}, version {version}, musique candidate {cid}.")
        mo = j["moyennes"]
        note_juge = np.mean([mo.get(k, 0) for k in ("accord_image_musique", "frappe_coupes", "dynamique", "motif", "energie")])
        al = rap["alignement_apres"]
        note = round(0.7 * note_juge + 0.3 * 10 * (0.6 * al["impacts"] + 0.4 * al["coupes"]), 2)
        res[cid] = {"juge": mo, "alignement": al, "dynamique": rap["dynamique"], "note_combinee": note, "film": film["film"],
                    "faiblesses": [x for p in j["passes"] if "faiblesses" in p for x in p["faiblesses"]][:4]}
        print("évalué", cid, note, flush=True)
    T.ecrire_choix(eq, c0)  # le choix reste à l'équipe (ou à sa règle) : on remet l'état d'avant
    (d / f"evaluation-{version}.json").write_text(json.dumps(res, ensure_ascii=False, indent=1))
    return res


if __name__ == "__main__":
    cmd, eq, *r = sys.argv[1:]
    if cmd == "carte":
        print(json.dumps(carte(eq, r[0] if r else "long"), ensure_ascii=False))
    elif cmd == "generer":
        generer(eq, set(r) or None)
    elif cmd == "conformer":
        conformer(eq, r[0], r[1] if len(r) > 1 else "long")
    elif cmd == "evaluer":
        print(json.dumps(evaluer(eq, r[0] if r else "long"), ensure_ascii=False)[:3000])
