"""[Copie « Signal » de video/outils/film.py pour la refonte du site : couleurs et polices lues dans ../marque.json,
étalonnage froid « signal » (ombres bleu nuit, hautes lumières neutres), accent ion, texte aligné à gauche possible
(« alignement »: "gauche"), style « corps » (Inter), plans sans piste son acceptés (silence ajouté).]

Moteur de montage des films Nexora AI : plans H3 + cartons dessinés en code + texte Geist en surimpression + musique
MiniMax-Music3 + bruitages synthétisés, étalonnés d'un seul regard (contraste doux, ombres froides, hautes lumières chaudes,
vignette, grain), mixés et normalisés à −14 LUFS (cible des réseaux sociaux).

Usage : python3 film.py montage.json [--rapide]
montage.json :
{ "sortie": "x.mp4", "format": "16:9"|"9:16"|"1:1", "ips": 24,
  "musique": {"fichier": "m.flac", "debut": 0, "db": -2, "fondu_fin": 1.5},
  "ambiance_db": -15,                      # sons propres des plans H3, sous la musique
  "segments": [ {"plan": "p.mp4", "debut": 0.4, "duree": 2.6, "vitesse": 1.0, "zoom": 0.06, "fondu": 0.0 },
                {"carton": "c.mp4", "duree": 8.4, "fondu": 0.0} ],
  # « fondu » : durée du fondu enchaîné avec le segment précédent (0 = coupe franche)
  "textes": [ {"texte": "Imaginez.", "debut": 3.0, "duree": 2.4, "position": "centre|bas|haut", "taille": 0.075,
               "style": "titre|mono", "accent": "mot ou groupe de mots en orange"} ],
  "sfx": [ {"type": "boom|whoosh|riser|tick", "t": 12.0, "duree": 1.2, "db": -4} ],
  "noir_debut": 0.0, "noir_fin": 0.8, "etalonnage": true }
--rapide : aperçu 960×540, qualité réduite (pour juger le rythme avant le rendu final).
"""
import argparse, json, subprocess, sys, tempfile
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter, ImageFont

FFMPEG = str(Path.home() / "nexora-creative-data/engine/ffmpeg/ffmpeg-7.0.2-arm64-static/ffmpeg")
POLICES = Path.home() / "Desktop/NexoraSite/web/src/fonts"
SFX = Path(__file__).resolve().parents[3] / "creative" / "outils" / "sfx.py"
TAILLES = {"16:9": (1920, 1080), "9:16": (1080, 1920), "1:1": (1080, 1080)}
MARQUE = json.loads((Path(__file__).resolve().parents[1] / "marque.json").read_text())
POLICES = Path(MARQUE["polices"]["dossier"]).expanduser()
FFPROBE = str(Path(FFMPEG).with_name("ffprobe"))


def _hexa(h):
    h = h.lstrip("#"); return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


_C = {k: _hexa(v) for k, v in MARQUE["couleurs"].items()}
OS, SIGNAL, ACCENT, BRUME = _C["texte"], _C["ion"], _C["ion"], _C["texte_2"]


def a_du_son(f):
    r = subprocess.run([FFPROBE, "-v", "error", "-select_streams", "a", "-show_entries", "stream=index", "-of", "csv=p=0", str(f)],
                       capture_output=True, text=True)
    return bool(r.stdout.strip())


def police(nom, taille, graisse=b"SemiBold"):
    f = ImageFont.truetype(str(POLICES / nom), taille)
    f.set_variation_by_name(graisse)
    return f


def png_texte(t, W, H, chemin):
    """Une image transparente W×H avec le texte (ombre douce pour la lisibilité sur l'image), en Geist ou JetBrains Mono."""
    style = t.get("style", "titre")
    taille = round(H * t.get("taille", 0.075 if style == "titre" else 0.022))
    if style in ("mono", "invite"):
        f = police(MARQUE["polices"]["mono"], taille, b"Medium" if style == "mono" else b"Regular")
    elif style == "corps":
        f = police(MARQUE["polices"]["texte"], taille, b"Regular")
    else:
        f = police(MARQUE["polices"]["titre"], taille, b"SemiBold")
    texte = t["texte"].upper() if style == "mono" else t["texte"]
    lignes = texte.split("\n")
    if t.get("largeur_max"):
        # automatic wrapping (vertical formats): a line wider than largeur_max × W is split at the words
        lim, res = t["largeur_max"] * W, []
        for l in lignes:
            cour = ""
            for mot in l.split(" "):
                essai = (cour + " " + mot).strip()
                if cour and f.getlength(essai) > lim:
                    res.append(cour); cour = mot
                else:
                    cour = essai
            res.append(cour)
        lignes = res
    interligne = round(taille * (1.28 if style == "mono" else 1.08))
    h_bloc = interligne * len(lignes)
    pos = t.get("position", "centre")
    y0 = {"centre": (H - h_bloc) / 2, "bas": H * (0.78 if W > H else 0.74) - h_bloc / 2, "haut": H * 0.16}.get(pos) if isinstance(pos, str) else H * pos - h_bloc / 2
    gauche = t.get("alignement") == "gauche"
    marge = W * (0.075 if W > H else 0.09)
    couche = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ombre = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d, ds = ImageDraw.Draw(couche), ImageDraw.Draw(ombre)
    accent = t.get("accent")
    couleur = SIGNAL if style == "mono" else (BRUME if style == "corps" else OS)
    if style == "invite":
        couleur = OS
    if t.get("couleur"):
        couleur = _C[t["couleur"]]
    acc = _C[t.get("accent_couleur", "ion")]
    for i, ligne in enumerate(lignes):
        y = y0 + i * interligne
        espace = taille * (0.16 if style == "mono" else 0.0)
        # largeur de la ligne (interlettrage manuel pour le mono)
        def larg(s):
            return sum(f.getlength(c) + espace for c in s) if espace else f.getlength(s)
        x = marge if gauche else ((W - marge - larg(ligne)) if t.get("alignement") == "droite" else (W - larg(ligne)) / 2)
        morceaux = [(ligne, False)]
        if accent and accent in ligne:
            a, b = ligne.split(accent, 1)
            morceaux = [(a, False), (accent, True), (b, False)]
        for m, est_accent in morceaux:
            if not m:
                continue
            col = acc if est_accent else couleur
            if espace:
                for c in m:
                    ds.text((x, y), c, font=f, fill=(0, 0, 0, 200)); d.text((x, y), c, font=f, fill=col + (255,)); x += f.getlength(c) + espace
            else:
                ds.text((x, y), m, font=f, fill=(0, 0, 0, 190)); d.text((x, y), m, font=f, fill=col + (255,)); x += f.getlength(m)
    ombre = ombre.filter(ImageFilter.GaussianBlur(taille * 0.18))
    ombre.alpha_composite(couche)
    ombre.save(chemin)


def synth(sfx, dossier, ips_dummy=None):
    """Bruitages synthétisés par ffmpeg (sfx.py de la bande-annonce Creative) : retourne [(wav, t, db)]."""
    sortie = []
    for i, s in enumerate(sfx or []):
        wav = Path(dossier) / f"sfx{i}.wav"
        subprocess.run([sys.executable, str(SFX), s["type"], str(s.get("duree", 1.0)), str(wav)], check=True, capture_output=True)
        sortie.append((wav, s["t"], s.get("db", -6)))
    return sortie


def monter(spec, rapide=False):
    W, H = TAILLES[spec.get("format", "16:9")]
    ips = spec.get("ips", 24)
    if rapide:
        W, H = W // 2, H // 2
    segs = spec["segments"]
    tmp = tempfile.mkdtemp(prefix="film-")
    entrees, filtres = [], []
    # --- Segments vidéo + audio
    cur_v = cur_a = None
    silences = []
    long = 0.0
    for i, s in enumerate(segs):
        dur = s["duree"]
        vit = s.get("vitesse", 1.0)
        src = s.get("plan") or s["carton"]
        debut = s.get("debut", 0.0)
        src_dur = dur * vit
        entrees += ["-ss", f"{debut:.3f}", "-t", f"{src_dur + 0.05:.3f}", "-i", str(src)] if "plan" in s else ["-i", str(src)]
        if not a_du_son(src):
            silences.append(i)
        z = s.get("zoom", 0.0)
        v = f"[{i}:v]fps={ips},setpts=PTS-STARTPTS"
        if vit != 1.0:
            v += f",setpts=PTS/{vit}"
        # Image gelée si le plan est plus court que prévu ; instants régénérés par numéro d'image (tpad seul laisse des
        # horodatages en double) puis coupe exacte à N images : les fondus et la musique restent calés à l'image près.
        v += f",tpad=stop_mode=clone:stop={ips * 4},setpts=N/{ips}/TB,trim=end_frame={max(1, round(dur * ips))},setpts=N/{ips}/TB,scale={W}:{H}:force_original_aspect_ratio=increase:flags=lanczos,crop={W}:{H}:x='(iw-ow)*{s.get("cadre_x", 0.5)}':y='(ih-oh)*{s.get("cadre_y", 0.5)}'"
        if z:
            v += f",scale=w='trunc({W}*(1+{z}*t/{dur:.3f})/2)*2':h=-2:eval=frame:flags=bilinear,crop={W}:{H}"
        v += f",fps={ips},setsar=1,format=yuv420p[v{i}]"  # fps : le zoom (scale eval=frame) fait perdre la cadence
        a = (f"anullsrc=r=48000:cl=stereo,atrim=duration={dur + 0.1:.3f}," if i in silences else f"[{i}:a]") + "aformat=sample_rates=48000:channel_layouts=stereo,asetpts=PTS-STARTPTS"
        if vit != 1.0:
            a += f",atempo={vit}"
        a += f",atrim=duration={dur:.3f},apad=whole_dur={dur:.3f},asetpts=PTS-STARTPTS[a{i}]"
        filtres += [v, a]
        if cur_v is None:
            cur_v, cur_a, long = f"v{i}", f"a{i}", dur
            continue
        # Toute jonction est un xfade (une coupe franche = fondu d'une image : invisible) : une seule mécanique, cadence constante.
        d = s.get("fondu", 0.0) or round(1.0 / ips, 4)
        filtres.append(f"[{cur_v}][v{i}]xfade=transition=fade:duration={d}:offset={long - d:.4f}[x{i}]")
        filtres.append(f"[{cur_a}][a{i}]acrossfade=d={d}[y{i}]")
        long += dur - d
        cur_v, cur_a = f"x{i}", f"y{i}"
    total = long
    n_seg = len(segs)
    # --- Étalonnage d'ensemble
    base = cur_v
    if spec.get("etalonnage", True):
        filtres.append(
            f"[{base}]eq=contrast=1.05:saturation=1.0:gamma=0.98,"
            "colorbalance=rs=-0.02:gs=0.0:bs=0.045:rm=-0.01:bm=0.02:rh=0.0:gh=0.005:bh=0.01,"
            "curves=preset=medium_contrast,unsharp=5:5:0.5:5:5:0.0,vignette=angle=PI/4.4,"
            f"noise=alls={4 if not rapide else 2}:allf=t,format=yuv420p[g]")
        base = "g"
    # --- Dégradé de lisibilité (bas et/ou haut de l'image, sous les textes), constant sur tout le film
    idx = n_seg
    deg = spec.get("degrade")
    if deg:
        import numpy as _np
        yy = _np.linspace(0, 1, H)[:, None]
        a = _np.zeros((H, 1))
        if deg.get("bas"):
            a = _np.maximum(a, deg["bas"] * _np.clip((yy - (1 - deg.get("hauteur", 0.42))) / deg.get("hauteur", 0.42), 0, 1) ** 1.6)
        if deg.get("haut"):
            a = _np.maximum(a, deg["haut"] * _np.clip((deg.get("hauteur", 0.42) - yy) / deg.get("hauteur", 0.42), 0, 1) ** 1.6)
        rgba = _np.zeros((H, W, 4), _np.uint8)
        rgba[..., :3] = (5, 7, 11)
        rgba[..., 3] = (_np.repeat(a, W, axis=1) * 255).astype(_np.uint8)
        Image.fromarray(rgba, "RGBA").save(Path(tmp) / "degrade.png")
        entrees += ["-loop", "1", "-t", f"{total:.3f}", "-framerate", str(ips), "-i", str(Path(tmp) / "degrade.png")]
        filtres.append(f"[{base}][{idx}:v]overlay=0:0:format=auto[dg]")
        base = "dg"
        idx += 1
    for j, t in enumerate(spec.get("textes", [])):
        png = Path(tmp) / f"t{j}.png"
        d, st = t["duree"], t["debut"]
        if t.get("frappe"):
            # typewriter: one image per frame, characters appear at t["frappe"] chars/s, blinking cursor
            nimg = round((d + 0.1) * ips)
            for k in range(nimg):
                c = min(len(t["texte"]), int(k / ips * t["frappe"]))
                curseur = "_" if (c < len(t["texte"]) or (k // 12) % 2 == 0) else " "
                png_texte(dict(t, texte=t["texte"][:c] + curseur + " " * (len(t["texte"]) - c)), W, H, Path(tmp) / f"t{j}_{k:04d}.png")
            entrees += ["-framerate", str(ips), "-i", str(Path(tmp) / f"t{j}_%04d.png")]
        else:
            png_texte(t, W, H, png)
            entrees += ["-loop", "1", "-t", f"{d + 0.1:.3f}", "-framerate", str(ips), "-i", str(png)]
        f_in, f_out = 0.45, 0.45
        filtres.append(
            f"[{idx}:v]format=rgba,fade=t=in:st=0:d={f_in}:alpha=1,fade=t=out:st={max(0.0, d - f_out):.3f}:d={f_out}:alpha=1,"
            f"setpts=PTS-STARTPTS+{st:.3f}/TB[tx{j}]")
        # montée douce de 14 px
        filtres.append(f"[{base}][tx{j}]overlay=x=0:y='{round(H * 0.012)}*(1-min(1,max(0,(t-{st:.3f})/0.6)))':eof_action=pass:format=auto[o{j}]")
        base = f"o{j}"
        idx += 1
    # --- Fondus noirs
    fins = []
    if spec.get("noir_debut"):
        fins.append(f"fade=t=in:st=0:d={spec['noir_debut']}")
    if spec.get("noir_fin"):
        fins.append(f"fade=t=out:st={total - spec['noir_fin']:.3f}:d={spec['noir_fin']}")
    filtres.append(f"[{base}]{','.join(fins) if fins else 'null'}[video]")
    # --- Audio : ambiance des plans + musique + bruitages
    amb = spec.get("ambiance_db", -15)
    pistes = [f"[{cur_a}]volume={amb}dB[amb]"]
    mix_in = ["[amb]"]
    mus = spec.get("musique")
    if mus:
        entrees += ["-ss", str(mus.get("debut", 0)), "-t", f"{total:.3f}", "-i", mus["fichier"]]
        fm = mus.get("fondu_fin", 1.2)
        pistes.append(f"[{idx}:a]aformat=sample_rates=48000:channel_layouts=stereo,volume={mus.get('db', -2)}dB,afade=t=in:st=0:d=0.8,afade=t=out:st={max(0.0, total - fm):.3f}:d={fm}[mus]")
        mix_in.append("[mus]")
        idx += 1
    for k, (wav, t, db) in enumerate(synth(spec.get("sfx"), tmp)):
        entrees += ["-i", str(wav)]
        pistes.append(f"[{idx}:a]aformat=sample_rates=48000:channel_layouts=stereo,volume={db}dB,adelay={int(t * 1000)}|{int(t * 1000)}[s{k}]")
        mix_in.append(f"[s{k}]")
        idx += 1
    pistes.append(f"{''.join(mix_in)}amix=inputs={len(mix_in)}:normalize=0:duration=first,alimiter=limit=0.95,loudnorm=I=-14:TP=-1.5:LRA=11,aresample=48000,alimiter=limit=0.84:level=false,aformat=sample_fmts=fltp:channel_layouts=stereo[audio]")
    graphe = ";".join(filtres + pistes)
    sortie = spec["sortie"]
    Path(sortie).parent.mkdir(parents=True, exist_ok=True)
    cmd = [FFMPEG, "-v", "error", "-y", *entrees, "-filter_complex", graphe, "-map", "[video]", "-map", "[audio]",
           "-c:v", "libx264", "-preset", "veryfast" if rapide else "slow", "-crf", "28" if rapide else "18", "-pix_fmt", "yuv420p",
           "-movflags", "+faststart", "-c:a", "aac", "-b:a", "256k", "-r", str(ips), "-t", f"{total:.3f}", sortie]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode:
        Path(tmp, "graphe.txt").write_text(graphe)
        Path(tmp, "commande.json").write_text(json.dumps(cmd))
        raise SystemExit(f"ffmpeg a échoué ({tmp}/graphe.txt) :\n{r.stderr[-1500:]}")
    print(f"{sortie}  {total:.2f} s  {W}×{H}")


if __name__ == "__main__":
    a = argparse.ArgumentParser()
    a.add_argument("montage")
    a.add_argument("--rapide", action="store_true")
    o = a.parse_args()
    monter(json.loads(Path(o.montage).read_text()), o.rapide)
