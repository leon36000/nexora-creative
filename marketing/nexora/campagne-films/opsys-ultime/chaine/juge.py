"""Juges de machine du concours (Gemini 4 Argon par OpenRouter ; deux passes, moyenne ; ce n'est pas un œil ni une oreille humains).

  python3 juge.py reel <equipe> [plan …]        « réel contre synthèse » : 3 images par plan → réalisme photographique /10, défauts
  python3 juge.py film <fichier.mp4> "<contexte>" juge audio-vidéo d'un montage mixé : accord image-musique, dynamique, motif,
                                                 frappe sur les coupes, voix, note /10
Sorties : <travail>/<equipe>/juge-reel.json ; <fichier>.juge.json
"""
import base64
import json
import subprocess
import sys
from io import BytesIO
from pathlib import Path

import numpy as np

import tourner as T
import voix as V

MODELE = "google/gemini-4-argon"

GRILLE_REEL = (
    "Tu es directeur de la photographie et superviseur des effets visuels pour une publicité télévisée haut de gamme. Voici trois images "
    "d'un même plan vidéo généré (début, milieu, fin). Juge sévèrement s'il a l'air d'une **vraie prise de vues tournée avec une caméra de "
    "cinéma** (acteurs réels, décor réel, lumière physique) ou d'une image de synthèse (rendu 3D, jeu vidéo, plastique, trop lisse, "
    "lumières néon gratuites). Pour un plan d'effets spéciaux (hologramme, faisceau de lumière), juge s'il est intégré comme un vrai VFX de "
    "film dans une prise réelle. Réponds en JSON strict : {{\"reel\": n (0 = image de synthèse évidente, 10 = indiscernable d'une vraie prise), "
    "\"look_jeu_video\": n (0 à 10, 10 = très jeu vidéo), \"defauts\": [\"texte ou logo visible\", \"mains déformées\", …], \"resume\": \"une phrase\"}}. "
    "Contexte du plan : {ctx}")

GRILLE_FILM = (
    "Tu es monteur et superviseur musical pour des publicités de technologie. Regarde et écoute ce montage en entier (image ET son). "
    "Juge sévèrement (5 = moyen, 8 = diffusable, 9 = excellent) : accord_image_musique (la musique va avec les images, elle les porte), "
    "frappe_coupes (les coups de la musique tombent sur les coupes et les événements), dynamique (contrastes, montées, vrais silences ; "
    "0 = nappe plate), motif (un thème mémorable), energie (entraînant ; pas forcément rapide), voix (naturelles, québécoises, avec du "
    "caractère, bien mixées), image_reelle (prises de vues réelles crédibles, pas « jeu vidéo »), clarte (un étranger comprend ce que fait "
    "le produit), note_globale. Réponds en JSON strict : {{\"accord_image_musique\": n, \"frappe_coupes\": n, \"dynamique\": n, \"motif\": n, "
    "\"energie\": n, \"voix\": n, \"image_reelle\": n, \"clarte\": n, \"note_globale\": n, \"forces\": [\"…\"], \"faiblesses\": [\"…\"], "
    "\"moments_plats\": [\"temps en s : pourquoi\"]}}. Contexte : {ctx}")


def appeler(contenu, passes=2):
    notes = []
    for i in range(passes):
        corps = {"model": MODELE, "temperature": 0.3 if i else 0.0, "response_format": {"type": "json_object"},
                 "messages": [{"role": "user", "content": contenu}]}
        try:
            r = json.loads(V.post("https://openrouter.ai/api/v1/chat/completions", corps, timeout=600))
            t = r["choices"][0]["message"]["content"]
            j = json.loads(t[t.find("{"): t.rfind("}") + 1])
            j["_cout"] = r.get("usage", {}).get("cost")
            notes.append(j)
        except Exception as e:
            notes.append({"erreur": str(e)[:300]})
    ok = [n for n in notes if "erreur" not in n]
    moy = {}
    for k in (ok[0].keys() if ok else []):
        vals = [n[k] for n in ok if isinstance(n.get(k), (int, float))]
        if vals and not k.startswith("_"):
            moy[k] = round(float(np.mean(vals)), 1)
    return {"moyennes": moy, "passes": notes, "cout_usd": round(sum((n.get("_cout") or 0) for n in ok), 4)}


def images_plan(f, n=3, largeur=768):
    d = T.duree(f)
    out = []
    for k in range(n):
        t = d * (0.15 + 0.7 * k / max(1, n - 1))
        raw = subprocess.run([T.FF, "-v", "error", "-ss", f"{t:.2f}", "-i", str(f), "-frames:v", "1", "-vf", f"scale={largeur}:-2",
                              "-f", "image2pipe", "-vcodec", "mjpeg", "-q:v", "4", "-"], capture_output=True).stdout
        out.append(base64.b64encode(raw).decode())
    return out


def reel(eq, plans=None):
    import concurrent.futures as cf
    D = T.dossier(eq)
    ctx = {p["id"]: (p.get("sequence", "") + " · " + p.get("effets", "") + " · " + p["prompt"].split("[Shot 1]")[-1][:400]) for p in D["plans"]}
    sortie = T.TRAVAIL / eq / "juge-reel.json"
    res = json.loads(sortie.read_text()) if sortie.exists() else {}
    fichiers = [f for f in sorted((T.TRAVAIL / eq / "plans").glob("*-r*.mp4")) if f.stem not in res and (not plans or f.stem.split("-r")[0] in plans)]

    def un(f):
        pid = f.stem.rsplit("-r", 1)[0].removesuffix("-v")
        imgs = images_plan(f)
        contenu = [{"type": "image_url", "image_url": {"url": "data:image/jpeg;base64," + b}} for b in imgs]
        contenu.append({"type": "text", "text": GRILLE_REEL.format(ctx=ctx.get(pid, ""))})
        return f.stem, appeler(contenu)
    with cf.ThreadPoolExecutor(6) as ex:
        for nom, r in ex.map(un, fichiers):
            res[nom] = r
            print(nom, r["moyennes"], flush=True)
            sortie.write_text(json.dumps(res, ensure_ascii=False, indent=1))
    sortie.write_text(json.dumps(res, ensure_ascii=False, indent=1))
    return res


def film(f, ctx):
    """Le montage est réduit en 480p (vidéo + son) pour le juge."""
    petit = Path(f).with_suffix(".juge.mp4")
    subprocess.run([T.FF, "-v", "error", "-y", "-i", str(f), "-vf", "scale=-2:480", "-r", "12", "-c:v", "libx264", "-crf", "30", "-preset", "fast",
                    "-c:a", "aac", "-b:a", "96k", str(petit)], check=True)
    b = base64.b64encode(petit.read_bytes()).decode()
    petit.unlink()
    contenu = [{"type": "video_url", "video_url": {"url": "data:video/mp4;base64," + b}}, {"type": "text", "text": GRILLE_FILM.format(ctx=ctx)}]
    r = appeler(contenu)
    Path(str(f) + ".juge.json").write_text(json.dumps(r, ensure_ascii=False, indent=1))
    return r


if __name__ == "__main__":
    if sys.argv[1] == "reel":
        reel(sys.argv[2], set(sys.argv[3:]) or None)
    elif sys.argv[1] == "film":
        print(json.dumps(film(sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else ""), ensure_ascii=False)[:2000])
