"""Site deliverables: web encodings + manifest.json (~/nexora-creative-data/site-medias/).

  python3 exporter.py image <source.png> <name> <role> [--cadre-x 0.5] [--prompt-de <images.py key>] [--recadrages 4x5,9x16]
  → <name>.avif / .webp / .jpg (2560×1440) + <name>-4x5.* (1152×1440) + <name>-9x16.* (810×1440)

Videos: exporter_video(master, name, role, ...) produces the H.264 web file, the WebM AV1 (or VP9) file, the poster
(JPG + AVIF) and the manifest entry. The manifest is rewritten on each export (one entry per base name)."""
import argparse, json, subprocess, time
from pathlib import Path
from PIL import Image

FFMPEG = str(Path.home() / "nexora-creative-data/engine/ffmpeg/ffmpeg-7.0.2-arm64-static/ffmpeg")
FFPROBE = str(Path(FFMPEG).with_name("ffprobe"))
LIVRE = Path.home() / "nexora-creative-data/site-medias"
MANIFESTE = LIVRE / "manifest.json"
RECADRAGES = {"4x5": (1152, 1440), "9x16": (810, 1440)}


def lancer(*args):
    r = subprocess.run([FFMPEG, "-v", "error", "-y", *map(str, args)], capture_output=True, text=True)
    if r.returncode:
        raise SystemExit(r.stderr[-1200:])


def sonde(f):
    r = subprocess.run([FFPROBE, "-v", "error", "-show_entries", "format=duration,size:stream=codec_type,codec_name,width,height,r_frame_rate",
                        "-of", "json", str(f)], capture_output=True, text=True)
    return json.loads(r.stdout)


def manifeste_maj(nom, entree):
    LIVRE.mkdir(parents=True, exist_ok=True)
    m = json.loads(MANIFESTE.read_text()) if MANIFESTE.exists() else {
        "_description": "Médias de la refonte du site (identité « Signal »). Aucun texte ni logo dans les images et vidéos générées : "
                        "titres et logo posés en code au montage (nom de marque provisoire, modifiable dans "
                        "marketing/nexora/refonte-medias/marque.json). Images : Qwen-Image-2.1 (GB10). Vidéo : MiniMax H3 (RTX 5090). "
                        "Musique : MiniMax-Music3.",
        "genere_le": None, "medias": {}}
    m["medias"][nom] = entree
    m["genere_le"] = time.strftime("%Y-%m-%dT%H:%M:%S")
    m["medias"] = dict(sorted(m["medias"].items()))
    MANIFESTE.write_text(json.dumps(m, indent=1, ensure_ascii=False))


def _ecrire_image(im, base):
    """base without extension → .jpg, .webp, .avif; returns the list of names."""
    im = im.convert("RGB")
    im.save(f"{base}.jpg", quality=86, optimize=True, progressive=True)
    im.save(f"{base}.webp", quality=84, method=6)
    tmp = f"{base}.tmp.png"
    im.save(tmp)
    lancer("-i", tmp, "-c:v", "libaom-av1", "-still-picture", "1", "-crf", "10", "-cpu-used", "4", "-pix_fmt", "yuv420p10le", f"{base}.avif")
    Path(tmp).unlink()
    return [Path(f"{base}.{e}").name for e in ("avif", "webp", "jpg")]


def exporter_image(src, nom, role, prompt, cadre_x=0.5, recadrages=("4x5", "9x16"), extra=None):
    im = Image.open(src).convert("RGB")
    if im.size != (2560, 1440):
        im = im.resize((2560, 1440), Image.LANCZOS)
    LIVRE.mkdir(parents=True, exist_ok=True)
    fichiers = {"16x9": _ecrire_image(im, LIVRE / nom)}
    for r in recadrages:
        w, h = RECADRAGES[r]
        x = round((2560 - w) * cadre_x)
        fichiers[r] = _ecrire_image(im.crop((x, 0, x + w, h)), LIVRE / f"{nom}-{r}")
    poids = {f: (LIVRE / f).stat().st_size for fs in fichiers.values() for f in fs}
    manifeste_maj(nom, {
        "type": "image", "role": role, "fichiers": fichiers, "dimensions": {"16x9": "2560x1440", **{r: "x".join(map(str, RECADRAGES[r])) for r in recadrages}},
        "poster": fichiers["16x9"][2], "langue": "aucune (sans texte)", "octets": poids,
        "moteur": "Qwen-Image-2.1 (GB10), 25 étapes, 2560×1440 natif", "prompt": prompt, **(extra or {})})
    return fichiers


def ajouter_variante(nom, ratio, src, prompt=None):
    """Adds a <nom>-<ratio> version made from a native render of another format (product that a crop would cut)."""
    w, h = RECADRAGES[ratio]
    im = Image.open(src).convert("RGB")
    k = max(w / im.width, h / im.height)
    im = im.resize((round(im.width * k), round(im.height * k)), Image.LANCZOS)
    x, y = (im.width - w) // 2, (im.height - h) // 2
    fichiers = _ecrire_image(im.crop((x, y, x + w, y + h)), LIVRE / f"{nom}-{ratio}")
    m = json.loads(MANIFESTE.read_text())
    e = m["medias"][nom]
    e["fichiers"][ratio] = fichiers
    e["dimensions"][ratio] = f"{w}x{h}"
    e["octets"].update({f: (LIVRE / f).stat().st_size for f in fichiers})
    e.setdefault("rendus_natifs", {})[ratio] = "rendu Qwen natif dans ce format (le recadrage couperait le produit)" + (f" ; prompt : {prompt}" if prompt else "")
    manifeste_maj(nom, e)
    return fichiers


def exporter_video(master, nom, role, langue, prompt=None, poster_t=None, boucle=False, cible_mo=None, av1=True, extra=None):
    """master: high-quality mp4 already in LIVRE (or elsewhere). Web: H.264 (crf tuned to stay under cible_mo) + WebM."""
    LIVRE.mkdir(parents=True, exist_ok=True)
    info = sonde(master)
    v = next(s for s in info["streams"] if s["codec_type"] == "video")
    W, H = v["width"], v["height"]
    duree = float(info["format"]["duration"])
    son = any(s["codec_type"] == "audio" for s in info["streams"])
    web = LIVRE / f"{nom}.mp4"
    webm = LIVRE / f"{nom}.webm"
    # H.264: 2 passes at the bitrate that targets cible_mo (headroom 6 %), capped at good quality.
    cible = (cible_mo or (6 if boucle else 24)) * 8e6 * 0.94
    a_br = 0 if (boucle or not son) else 160e3
    v_br = int(min(cible / duree - a_br, 12e6 if not boucle else 6e6))
    commun = ["-i", master, "-map", "0:v:0", *(["-map", "0:a:0"] if son and not boucle else []), "-c:v", "libx264", "-preset", "slow",
              "-profile:v", "high", "-pix_fmt", "yuv420p", "-b:v", str(v_br), "-maxrate", str(int(v_br * 1.5)), "-bufsize", str(int(v_br * 2))]
    journal = str(LIVRE / f".x264-{nom}")
    lancer(*commun, "-pass", "1", "-passlogfile", journal, "-an", "-f", "mp4", "/dev/null")
    lancer(*commun, "-pass", "2", "-passlogfile", journal, *(["-c:a", "aac", "-b:a", "160k"] if son and not boucle else ["-an"]),
           "-movflags", "+faststart", web)
    for f in LIVRE.glob(f".x264-{nom}*"):
        f.unlink()
    # WebM: AV1 (libaom, constant quality capped by the same bitrate) — VP9 if AV1 is not wanted.
    if av1:
        lancer("-i", master, "-map", "0:v:0", *(["-map", "0:a:0"] if son and not boucle else []), "-c:v", "libaom-av1", "-cpu-used", "6",
               "-row-mt", "1", "-crf", "32", "-b:v", str(int(v_br * 0.7)), "-pix_fmt", "yuv420p",
               *(["-c:a", "libopus", "-b:a", "128k"] if son and not boucle else ["-an"]), webm)
    else:
        lancer("-i", master, "-c:v", "libvpx-vp9", "-crf", "34", "-b:v", "0", "-row-mt", "1", *(["-c:a", "libopus"] if son and not boucle else ["-an"]), webm)
    # poster
    t = poster_t if poster_t is not None else min(duree * 0.4, duree - 0.1)
    pjpg = LIVRE / f"{nom}-poster.jpg"
    lancer("-ss", f"{t:.3f}", "-i", master, "-frames:v", "1", "-q:v", "3", pjpg)
    lancer("-i", pjpg, "-c:v", "libaom-av1", "-still-picture", "1", "-crf", "24", "-cpu-used", "4", LIVRE / f"{nom}-poster.avif")
    poids = {p.name: p.stat().st_size for p in (web, webm, pjpg, LIVRE / f"{nom}-poster.avif")}
    entree = {"type": "video", "role": role, "langue": langue, "format": f"{W}x{H}", "dimensions": f"{W}x{H}",
              "duree_s": round(duree, 2), "boucle": boucle, "son": bool(son and not boucle),
              "fichiers": {"web_h264": web.name, "web_webm": webm.name, "master": Path(master).name if Path(master).parent == LIVRE else None},
              "poster": {"jpg": pjpg.name, "avif": f"{nom}-poster.avif", "instant_s": round(t, 2)}, "octets": poids, **(extra or {})}
    if prompt:
        entree["prompt"] = prompt
    manifeste_maj(nom, entree)
    return entree


if __name__ == "__main__":
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    a = argparse.ArgumentParser()
    a.add_argument("genre"); a.add_argument("source"); a.add_argument("nom"); a.add_argument("role")
    a.add_argument("--cadre-x", type=float, default=0.5); a.add_argument("--cle"); a.add_argument("--recadrages", default="4x5,9x16")
    o = a.parse_args()
    from images import IMAGES
    cle = o.cle or o.nom
    prompt = IMAGES[cle][2] if cle in IMAGES else None
    print(exporter_image(o.source, o.nom, o.role, prompt, o.cadre_x, [r for r in o.recadrages.split(",") if r]))
