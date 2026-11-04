#!/usr/bin/env python3
"""Analyse fine d'une vidéo promotionnelle : mesures ffmpeg (coupes, sonie) + Gemini (vidéo via OpenRouter).
Usage : analyser.py <video.mp4> <info.json> <sortie.json> [modele] [effort]
La clé OpenRouter est lue dans le fichier de clés sans jamais être affichée."""
import base64, json, os, re, subprocess, sys, time, urllib.request

FF = "/home/pc6/nexora-creative-data/engine/ffmpeg/ffmpeg-7.0.2-arm64-static/ffmpeg"
FP = FF[:-len("ffmpeg")] + "ffprobe"
KEYFILE = os.environ.get("SA_KEYFILE", "/home/pc6/Desktop/Deepinfra.env")


def cle():
    with open(KEYFILE, encoding="utf-8") as f:
        for ligne in f:
            if ":" in ligne and ligne.split(":", 1)[0].strip().lower() == "openrouter":
                return ligne.split(":", 1)[1].strip()
    raise SystemExit("cle OpenRouter introuvable")


def coupes(video, seuil=0.15):
    """Changements de plan par la détection de scène de ffmpeg (score > seuil)."""
    p = subprocess.run([FF, "-hide_banner", "-nostats", "-i", video, "-vf",
                        f"select='gt(scene,{seuil})',showinfo", "-an", "-f", "null", "-"],
                       capture_output=True, text=True)
    brut = [float(m) for m in re.findall(r"pts_time:([0-9.]+)", p.stderr)]
    out = []
    for t in brut:  # fusionne les détections à moins de 0,3 s (fondus, flashs)
        if not out or t - out[-1] > 0.3:
            out.append(t)
    return [round(t, 2) for t in out]


def sonie(video):
    p = subprocess.run([FF, "-hide_banner", "-nostats", "-i", video, "-vn", "-af", "ebur128=peak=true", "-f", "null", "-"],
                       capture_output=True, text=True)
    i = re.findall(r"I:\s+(-?[0-9.]+) LUFS", p.stderr)
    lra = re.findall(r"LRA:\s+([0-9.]+) LU", p.stderr)
    return {"lufs": float(i[-1]) if i else None, "lra": float(lra[-1]) if lra else None}


def duree(video):
    p = subprocess.run([FP, "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", video],
                       capture_output=True, text=True)
    return float(p.stdout.strip() or 0)


CONSIGNE = """Tu es un monteur et directeur artistique de bandes-annonces et de publicités, spécialiste des vidéos promotionnelles d'outils d'IA générative.
Analyse cette vidéo promotionnelle avec précision, seconde par seconde. Réponds en FRANÇAIS, uniquement par un objet JSON valide (pas de Markdown autour) avec ces clés :
{
 "accroche_0_2s": "ce qu'on voit et entend exactement pendant les 2 premières secondes, et pourquoi ça retient (ou pas)",
 "structure": [ {"t": "0-3s", "role": "accroche|promesse|démonstration|escalade|preuve|révélation|appel", "contenu": "..."} ],
 "escalade": "comment l'intensité monte (échelle, vitesse, enjeux, nombre d'effets), en 2-3 phrases",
 "capacites_montrees": [ {"capacite": "...", "comment_rendue_evidente": "avant/après, écran partagé, interface visible, prompt affiché, transformation en direct, etc."} ],
 "textes_ecran": [ {"t": "...", "texte": "texte exact", "style": "police, taille, animation, position"} ],
 "voix": {"presence": "aucune|voix off|présentateur|personnages", "style": "débit, énergie, timbre, ton (posé, hype, chuchoté, narrateur de bande-annonce...)", "langue": "...", "exemple_phrase": "une phrase courte entendue"},
 "musique": {"genre": "...", "tempo_bpm_estime": 0, "energie_1_10": 0, "evolution": "montée, drop, silence avant révélation, etc.", "synchro_coupes": "les coupes tombent-elles sur les temps ?"},
 "design_sonore": "whooshes, impacts, risers, silences, sons diégétiques",
 "camera_et_image": "mouvements de caméra dominants, échelle des plans, étalonnage, transitions",
 "rythme_percu": "lent|moyen|rapide|frénétique + commentaire (varie-t-il ?)",
 "fin": "comment la vidéo se termine (logo, carton, appel à l'action, boucle, coupe sèche) et durée du carton final",
 "ce_qui_est_spectaculaire": "les 1 à 3 moments les plus forts et pourquoi",
 "faiblesses": "ce qui est faible ou à éviter",
 "regles_a_retenir": ["3 à 6 règles concrètes et réutilisables qu'un monteur peut appliquer à un film promotionnel pour un studio vidéo IA"],
 "nb_plans_estime": 0,
 "note_spectaculaire_10": 0
}
Données mesurées par le code (fiables, utilise-les pour le rythme) : DUREE_S, nombre de coupes détectées et instants des coupes : COUPES.
Métadonnées : METADONNEES"""


def analyser(video, info, sortie, modele="google/gemini-4-argon", effort="medium"):
    d = duree(video)
    c = coupes(video)
    s = sonie(video)
    meta = {k: info.get(k) for k in ("id", "title", "channel", "upload_date", "duration", "view_count")}
    meta["description"] = (info.get("description") or "")[:600]
    consigne = (CONSIGNE.replace("DUREE_S", f"{d:.1f} s").replace("COUPES", f"{len(c)} coupes : {c[:120]}")
                .replace("METADONNEES", json.dumps(meta, ensure_ascii=False)))
    with open(video, "rb") as f:
        b64 = base64.b64encode(f.read()).decode()
    corps = {
        "model": modele,
        "messages": [{"role": "user", "content": [
            {"type": "text", "text": consigne},
            {"type": "video_url", "video_url": {"url": f"data:video/mp4;base64,{b64}"}},
        ]}],
        "reasoning": {"effort": effort},
        "usage": {"include": True},
        "max_tokens": 12000,
    }
    req = urllib.request.Request("https://openrouter.ai/api/v1/chat/completions", data=json.dumps(corps).encode(),
                                 headers={"Authorization": "Bearer " + cle(), "Content-Type": "application/json"})
    t0 = time.time()
    for essai in range(3):
        try:
            with urllib.request.urlopen(req, timeout=600) as r:
                rep = json.load(r)
            break
        except Exception as e:  # noqa
            err = str(e)
            if hasattr(e, "read"):
                err += " " + e.read().decode()[:500]
            if essai == 2:
                raise SystemExit("echec OpenRouter : " + err)
            time.sleep(10)
    texte = rep["choices"][0]["message"].get("content") or ""
    m = re.search(r"\{.*\}", texte, re.S)
    try:
        analyse = json.loads(m.group(0)) if m else {"brut": texte}
    except Exception:
        analyse = {"brut": texte}
    u = rep.get("usage", {})
    res = {"meta": meta, "mesures": {"duree_s": round(d, 2), "nb_coupes": len(c), "coupes": c,
                                      "plans": len(c) + 1, "duree_moyenne_plan_s": round(d / (len(c) + 1), 2),
                                      "plans_par_seconde": round((len(c) + 1) / d, 3) if d else None, **s},
           "analyse": analyse, "modele": rep.get("model"),
           "cout_usd": u.get("cost"), "jetons": {"in": u.get("prompt_tokens"), "out": u.get("completion_tokens")},
           "secondes": round(time.time() - t0, 1)}
    with open(sortie, "w", encoding="utf-8") as f:
        json.dump(res, f, ensure_ascii=False, indent=1)
    print(f"{meta['id']} ok plans={len(c)+1} cout={u.get('cost')} t={res['secondes']}s")


if __name__ == "__main__":
    a = sys.argv
    analyser(a[1], json.load(open(a[2])), a[3], *(a[4:6]))
