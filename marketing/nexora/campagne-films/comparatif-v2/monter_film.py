"""Étapes « voix » et « montage » du comparatif v2 : film.json (écrit par le modèle) + ses plaques + sa musique → film fini,
par l'usine de la campagne (`usine/usine.py`, `usine/monter.py`, typographie `usine/typo.py`).

  python3 monter_film.py <film> [--sans-rendu]      ex. opsys-expert
Ce que fait le code (identique pour tous les modèles ; la copie est celle du modèle, le style est celui du code) :
  - tempo MESURÉ de la musique rendue (flux spectral + autocorrélation) ; chaque coupe aimantée sur le temps réel le plus proche ;
  - textes : temps du modèle reportés plan par plan sur le montage recalé ; style typographique de l'usine (titre en bas sur voile,
    impact au centre, surtitre en haut, étiquette prepa) ;
  - narration : voix.py (Chatterbox, clonage québécois, contrôle Whisper), phrase par phrase, posée au temps du modèle sans
    chevauchement ; la musique baisse de 11 dB sous la voix (rampes 0,25 s) ;
  - tableau M1–M10 (OPSYS-AI) dessiné par le code ; inserts réels d'interface (WorkStudio) en carte ;
  - bruitages : impact sur les éclairs, souffle sur les raccords, boom sous le carton ; −14 LUFS, crête vraie ≤ −1 dBTP.
Dossier de travail : ~/nexora-creative-data/work/films-v2/<film> (archivé ensuite sur pc1 : NexoraStudioWork/films-v2/travail/).
Sortie : ~/nexora-creative-data/promo/montage/Test2-<brief>-<palier>-16x9-fr.mp4 ; planche et revue.json dans <film>/usine/.
"""
import json
import subprocess
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

ICI = Path(__file__).resolve().parent
sys.path.insert(0, str(ICI.parent / "usine"))
import typo  # noqa: E402
import usine  # noqa: E402

TRAVAIL = Path.home() / "nexora-creative-data/work/films-v2"
FF = usine.FFMPEG
MARQUE_F = ICI.parent / "marque.json"
PRODUITS = {"creative": "CREATIVE", "opsys": "OPSYS-AI", "workstudio": "WORKSTUDIO"}
DEPTS = {"M1": "Réception", "M2": "CRM", "M3": "Estimation", "M4": "Terrain", "M5": "Finance", "M6": "Matériel", "M7": "Marketing",
         "M8": "Analytique", "M9": "Stratégie", "M10": "Mémoire"}
DUCK_DB, VOIX_DB, SON_H3_DB = -11, 3.0, -17


# ---------------------------------------------------------------------------------------------------------------- tempo
def mesurer(f):
    SR, HOP = 22050, 220
    b = subprocess.run([FF, "-v", "error", "-i", str(f), "-f", "f32le", "-ac", "1", "-ar", str(SR), "-"], capture_output=True).stdout
    x = np.frombuffer(b, np.float32)
    n = len(x) // HOP - 5
    fen = np.hanning(1024)
    S = np.abs(np.fft.rfft(np.stack([x[i * HOP:i * HOP + 1024] * fen for i in range(n) if i * HOP + 1024 <= len(x)]), axis=1))
    flux = np.maximum(0, np.diff(np.log1p(S * 10), axis=0)).sum(1)
    flux = (flux - np.convolve(flux, np.ones(50) / 50, "same")).clip(0)
    ac = np.correlate(flux, flux, "full")[len(flux) - 1:]
    lags = np.arange(len(ac)) / 100
    ok = (lags > 60 / 170) & (lags < 60 / 72)
    i = int(round(lags[ok][np.argmax(ac[ok])] * 100))
    y0, y1, y2 = ac[i - 1], ac[i], ac[i + 1]
    lag = (i + 0.5 * (y0 - y2) / (y0 - 2 * y1 + y2)) / 100
    phases = np.linspace(0, lag, 50, endpoint=False)
    sc = [flux[np.clip(np.round(np.arange(p, len(flux) / 100, lag) * 100).astype(int), 0, len(flux) - 1)].sum() for p in phases]
    return {"bpm": round(60 / lag, 2), "temps_s": round(lag, 4), "phase_s": round(float(phases[int(np.argmax(sc))]), 3), "duree_s": round(len(x) / SR, 2)}


def recaler(durees, temps, bornes):
    """Coupes aimantées au temps musical le plus proche ; chaque durée reste dans ses bornes (en nombre entier de temps)."""
    out, t_mod, t = [], 0.0, 0.0
    for d, (lo, hi) in zip(durees, bornes):
        t_mod += d
        k = max(1, round((t_mod - t) / temps))
        while k * temps < lo - 1e-6:
            k += 1
        while k * temps > hi + 1e-6 and k > 1:
            k -= 1
        out.append(round(k * temps, 4))
        t += k * temps
    return out


def reporter(t, anciens, nouveaux):
    """Temps du modèle → temps du montage recalé (même fraction dans le même plan)."""
    a = n = 0.0
    for i, (da, dn) in enumerate(zip(anciens, nouveaux)):
        if t < a + da or i == len(anciens) - 1:
            return n + min(1.0, max(0.0, (t - a) / da)) * dn
        a, n = a + da, n + dn
    return n


# -------------------------------------------------------------------------------------------------------------- tableau
def rendre_tableau(tuiles, d, sortie, marque):
    """Tableau vivant M1–M10 : dix tuiles sur fond d'encre, celles du plan s'allument une à une (contour signal, halo) et leur
    action se frappe dessous ; une ligne de lumière relie la tuile allumée à la suivante ; lente poussée de caméra."""
    W, H, IPS = 1920, 1080, 24
    ty = typo.Typo(marque)
    C = {k: tuple(v) for k, v in marque["couleurs"].items()}
    f_m = ty.police("mono", 26, "Medium")
    f_n = ty.police("titre", 42, "SemiBold")
    f_a = ty.police("titre", 32, "Regular")
    actives = [x["m"] for x in tuiles]
    actions = {x["m"]: x["action"] for x in tuiles}
    tw, th, gx, gy = 330, 250, 30, 36
    x0, y0 = (W - (5 * tw + 4 * gx)) / 2, (H - (2 * th + gy)) / 2 - 20
    pos = {f"M{i + 1}": (x0 + (i % 5) * (tw + gx), y0 + (i // 5) * (th + gy)) for i in range(10)}
    pas = max(0.35, (d - 0.6) / max(1, len(actives)))
    fond = Image.new("RGB", (W, H), C["encre"])
    dr = ImageDraw.Draw(fond)
    for gxx in range(0, W, 48):
        dr.line([(gxx, 0), (gxx, H)], fill=(14, 15, 20))
    for gyy in range(0, H, 48):
        dr.line([(0, gyy), (W, gyy)], fill=(14, 15, 20))
    enc = subprocess.Popen([FF, "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(IPS), "-i", "-",
                            "-c:v", "libx264", "-crf", "14", "-pix_fmt", "yuv420p", str(sortie)], stdin=subprocess.PIPE)
    for i in range(int((d + 0.3) * IPS)):
        t = i / IPS
        im = fond.copy()
        halo = Image.new("RGB", (W, H), (0, 0, 0))
        dh = ImageDraw.Draw(halo)
        dd = ImageDraw.Draw(im)
        for m, (x, y) in pos.items():
            k = actives.index(m) if m in actives else None
            a = 0.0 if k is None else min(1.0, max(0.0, (t - 0.3 - k * pas) / 0.3))
            bord = tuple(int(40 + (c - 40) * a) for c in C["signal"]) if a else (38, 40, 48)
            dd.rounded_rectangle([x, y, x + tw, y + th], radius=18, fill=(16, 17, 22), outline=bord, width=3 if a else 2)
            if a:
                dh.rounded_rectangle([x - 6, y - 6, x + tw + 6, y + th + 6], radius=22, outline=tuple(int(c * a) for c in C["signal"]), width=10)
            dd.text((x + 22, y + 20), m, font=f_m, fill=C["signal"] if a else C["brume"])
            dd.text((x + 22, y + 56), DEPTS[m], font=f_n, fill=C["os"] if a else (104, 106, 118))
            if a:
                txt = actions[m]
                n = int(len(txt) * min(1.0, max(0.0, (t - 0.45 - k * pas) / 0.5)))
                lignes, cour = [], ""
                for mot in txt[:n].split(" "):
                    if dd.textlength((cour + " " + mot).strip(), font=f_a) > tw - 44:
                        lignes.append(cour)
                        cour = mot
                    else:
                        cour = (cour + " " + mot).strip()
                lignes.append(cour)
                for li, l in enumerate(lignes[:3]):
                    dd.text((x + 22, y + 128 + li * 40), l, font=f_a, fill=C["os"])
                dd.ellipse([x + tw - 34, y + 22, x + tw - 18, y + 38], fill=C["signal"])
            if k is not None and k + 1 < len(actives):
                u = min(1.0, max(0.0, (t - 0.6 - k * pas) / (pas * 0.6)))
                if u > 0:
                    (ax, ay), (bx, by) = pos[m], pos[actives[k + 1]]
                    p0, p1 = (ax + tw / 2, ay + th / 2), (bx + tw / 2, by + th / 2)
                    pe = (p0[0] + (p1[0] - p0[0]) * u, p0[1] + (p1[1] - p0[1]) * u)
                    dh.line([p0, pe], fill=C["signal"], width=6)
        halo = halo.filter(ImageFilter.GaussianBlur(14))
        im = Image.fromarray(np.clip(np.asarray(im, np.int16) + np.asarray(halo, np.int16), 0, 255).astype(np.uint8))
        s = 1.0 + 0.035 * t / d
        cw, ch = W / s, H / s
        im = im.crop(((W - cw) / 2, (H - ch) / 2, (W + cw) / 2, (H + ch) / 2)).resize((W, H), Image.BICUBIC)
        enc.stdin.write(im.tobytes())
    enc.stdin.close()
    enc.wait()


# ---------------------------------------------------------------------------------------------------------------- monter
def monter(nom, rendu=True):
    brief, palier = nom.split("-", 1)
    dos = TRAVAIL / nom
    film = json.loads((dos / "film.json").read_text())
    pj = json.loads((dos / "plaques.json").read_text())
    marque = json.loads(MARQUE_F.read_text())
    mus = mesurer(dos / "musique.flac")
    temps = mus["temps_s"]
    plans = film["plans"]
    bornes = [(1.0, 2.2) if p["type"] == "ui" else (1.0, 5.05) for p in plans]
    anciens = [p["duree"] for p in plans]
    nouveaux = recaler(anciens, temps, bornes)
    tp = sum(nouveaux)
    k_fin = max(1, round(film["fin"]["duree"] / temps))
    while tp + k_fin * temps < 40.0:
        k_fin += 1
    d_fin = round(k_fin * temps, 4)
    total = tp + d_fin
    tp_mod = sum(anciens)
    segs, ordre, textes = {}, [], {}
    us = dos / "usine"
    (us / "tableaux").mkdir(parents=True, exist_ok=True)
    debuts = np.cumsum([0] + nouveaux)
    for i, (p, d) in enumerate(zip(plans, nouveaux)):
        sid = p["id"]
        if p["type"] == "plan":
            r = pj["plaques"][sid]
            s = {"type": "plan", "d": d, "plaque": str(dos / "plaques" / r["video"]), "cle": str(dos / "plaques" / r["cle"]), "debut": 0.0,
                 "son_h3": SON_H3_DB}
        elif p["type"] == "tableau":
            f = us / "tableaux" / f"{sid}.mp4"
            if not f.exists():
                rendre_tableau(p["tableau"], d, f, marque)
            s = {"type": "plan", "d": d, "plaque": str(f), "debut": 0.0, "etalonnage": {"grain": 0.018, "halo": 0.1}}
        else:
            et = "tri" if p.get("ui") == "ui-tri" else "approuver"
            s = {"type": "ecran", "d": d, "entree": True, "images": [[0, d, et]], "cadre": [[0, 0.5, 0.5, 1.0], [d, 0.5, 0.47, 0.86]]}
        tr = p.get("transition")
        sfx = []
        if tr == "flash" and i:
            s["flash"] = 0.0
            sfx.append({"t": 0.0, "type": "impact", "duree": 1.5, "db": -9})
        elif tr == "fondu":
            s["fondu_entree"] = 0.35
        elif tr == "raccord" and i:
            sfx.append({"t": 0.0, "type": "souffle", "duree": 0.6, "db": -20})
        s["sfx"] = sfx
        s["textes"] = []
        segs[sid] = s
        ordre.append(sid)
    segs["fin"] = {"type": "fin", "d": d_fin, "t_marque": 1.1, "textes": [], "sfx": [{"t": 0.0, "type": "boom", "duree": 2.5, "db": -12}]}
    ordre.append("fin")
    # textes : temps reportés sur le montage recalé ; style par le code
    textes_glob = []
    for k, x in enumerate(sorted(film.get("textes", []), key=lambda x: x["debut"])):
        t0 = reporter(min(x["debut"], tp_mod - 0.01), anciens, nouveaux)
        dur = max(x["duree"], 0.3 * typo.mots(x["texte"]) + 0.5) if x["style"] != "prepa" else x["duree"]
        dur = min(dur, tp - t0)
        for jj, sid2 in enumerate(ordre[:-1]):  # un texte ne déborde pas sur un insert d'interface (la carte le couvrirait)
            if segs[sid2]["type"] == "ecran" and debuts[jj] > t0 + 0.01 and debuts[jj] < t0 + dur:
                dur = max(debuts[jj] - t0, 1.0)
        j = int(np.searchsorted(debuts, t0, side="right") - 1)
        sid = ordre[min(j, len(plans) - 1)]
        style = x["style"]
        spec = {"t": round(t0 - debuts[j], 3), "d": round(dur, 3), "cle": f"t{k:02d}", "style": "titre" if style == "sur" and False else style}
        if film.get("mode") == "texte" and style in ("titre", "impact"):  # film sans voix : la typographie porte tout, corps plus grand
            spec["taille"] = 1.3 if style == "titre" else 1.2
        if style == "titre":
            spec["zone"] = "colonne" if segs[sid]["type"] == "ecran" else "bas"
        elif style == "impact":
            spec["zone"] = "centre"
        elif style == "sur":
            spec["zone"] = "haut"
        textes_glob.append({**spec, "t": round(t0, 3)})  # temps absolu : un texte peut chevaucher une coupe (l'usine le couperait)
        textes[f"t{k:02d}"] = x["texte"].replace("→", "›").replace("->", "›")  # la flèche n'est pas dans le sous-ensemble latin de Geist
        if style in ("titre", "impact"):  # voile sur le plan qui porte le texte (et le suivant s'il déborde)
            for jj in range(j, len(plans)):
                if debuts[jj] >= t0 + dur:
                    break
                if segs[ordre[jj]]["type"] == "plan":
                    segs[ordre[jj]]["voile"] = {"v": 0.62, "h": 0.55, "haut": False} if spec.get("zone") == "bas" else {"v": 0.6, "centre": True}
    textes.update({"slogan": film["fin"]["slogan"], "sous_titre": film["fin"].get("sous_titre", ""), "mentions": film["fin"].get("mentions", "")})
    b = {"film": nom, "titre": f"Test2 {nom}", "produit": PRODUITS[brief], "marque": str(MARQUE_F), "langues": ["fr"], "formats": ["16x9"],
         "travail": str(us), "captures": str(TRAVAIL / "ui"), "segments": segs, "textes": {"fr": textes},
         "musique": {"fichier": str(dos / "musique.flac"), "bpm": mus["bpm"], "subdivision": 1, "repere_source": mus["phase_s"]},
         "versions": {"long": {"ordre": ordre, "musique": {"repere_segment": ordre[0], "fondu_entree": 0.05}}}}
    (us / "brief.json").write_text(json.dumps(b, ensure_ascii=False, indent=1))
    bb = usine.charger(us / "brief.json")
    ok = usine.valider(bb)
    m = usine.montage(bb)
    m["versions"]["long"]["textes"] = textes_glob
    # narration
    nar = sorted(film.get("narration") or [], key=lambda x: x["debut"])
    pose_voix = []
    if nar:
        phr = us / "phrases.json"
        phr.write_text(json.dumps([{"id": x["id"], "texte": x["texte"], "role": x.get("role", "narrateur")} for x in nar], ensure_ascii=False))
        subprocess.run([sys.executable, str(ICI / "voix.py"), "narrer", str(phr), str(us / "voix")], check=True)
        vj = {v["id"]: v for v in json.loads((us / "voix" / "voix.json").read_text())}
        fin_prec = 0.0
        for x in nar:
            v = vj[x["id"]]
            t = max(reporter(min(x["debut"], tp_mod - 0.01), anciens, nouveaux), fin_prec + 0.15)
            pose_voix.append([t, v["duree"], str(us / "voix" / f"{x['id']}.wav"), x["id"]])
            fin_prec = t + v["duree"]
        deb = total - 0.4 - fin_prec  # débordement : on resserre les respirations depuis la fin
        if deb < 0:
            for k in range(len(pose_voix) - 1, -1, -1):
                marge = pose_voix[k][0] - ((pose_voix[k - 1][0] + pose_voix[k - 1][1] + 0.12) if k else 0.2)
                dec = min(marge, -deb)
                for kk in range(k, len(pose_voix)):
                    pose_voix[kk][0] -= dec
                deb += dec
                if deb >= 0:
                    break
        for t, dv, f, _ in pose_voix:
            m["versions"]["long"]["musique"].append({"fichier": f, "source": 0.0, "pose": round(t, 3), "d": round(dv + 0.05, 3), "db": VOIX_DB,
                                                     "fondu_entree": 0.005, "fondu_fin": 0.03, "voix": True})
    (us / "montage.json").write_text(json.dumps(m, ensure_ascii=False, indent=1))
    rythme = {"musique": mus, "durees_modele": anciens, "durees_montees": nouveaux, "carton_s": d_fin, "duree_s": round(total, 2),
              "plans": len(plans), "plan_moyen_s": round(tp / len(plans), 2), "ecart_coupes_moyen_s": round(float(np.mean(np.abs(
                  np.cumsum(nouveaux) - np.cumsum(anciens)))), 3), "voix": [[round(t, 2), round(dv, 2), i] for t, dv, _, i in pose_voix],
              "valide_usine": ok}
    (us / "rythme.json").write_text(json.dumps(rythme, ensure_ascii=False, indent=1))
    print(json.dumps({k: rythme[k] for k in ("musique", "duree_s", "plans", "plan_moyen_s", "ecart_coupes_moyen_s", "valide_usine")}, ensure_ascii=False))
    if not rendu:
        return
    usine.rendre(bb, ["long"])
    usine.masteriser(bb)
    usine.revue(bb)
    src = us / "brouillons" / f"{nom}-16x9-fr-long.mp4"
    fin = Path.home() / f"nexora-creative-data/promo/montage/Test2-{brief}-{palier}-16x9-fr.mp4"
    subprocess.run(["cp", str(src), str(fin)], check=True)
    print("livré :", fin)




def pret(nom):
    dos = TRAVAIL / nom
    try:
        film = json.loads((dos / "film.json").read_text())
        pj = json.loads((dos / "plaques.json").read_text())
    except FileNotFoundError:
        return False
    besoin = [p["id"] for p in film["plans"] if p["type"] == "plan"]
    return (dos / "musique.flac").exists() and all(pj["plaques"].get(i, {}).get("video") for i in besoin)


def tous():
    """Monte chaque film dès que ses plaques et sa musique sont prêtes (une fois), jusqu'aux 12."""
    import time
    faits = set()
    films = [f"{b}-{p}" for p in ("eco", "equilibre", "expert", "opus") for b in ("creative", "opsys", "workstudio")]
    while len(faits) < len(films):
        for n in films:
            if n not in faits and pret(n):
                b, p = n.split("-", 1)
                if not (Path.home() / f"nexora-creative-data/promo/montage/Test2-{b}-{p}-16x9-fr.mp4").exists():
                    try:
                        monter(n)
                    except (Exception, SystemExit) as e:  # noqa: BLE001  (ffmpeg du moteur V4 lève SystemExit)
                        print("échec", n, e, flush=True)
                faits.add(n)
                print("fait", n, flush=True)
        time.sleep(30)


if __name__ == "__main__":
    if sys.argv[1] == "tous":
        tous()
    else:
        monter(sys.argv[1], "--sans-rendu" not in sys.argv)
