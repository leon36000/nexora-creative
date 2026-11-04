"""Film V6 : archive TOUTES les vidéos produites (finales, essais, rushes, dialogues, voix, musiques) sur pc1 dans
~/Bureau/Nexora-Livrables/TOUS-LES-FILMS/creative-v6/ et ajoute une ligne par fichier à INVENTAIRE.csv (sans doublon de sha256).
Rien n'est jamais supprimé, ni ici ni là-bas.
  python3 archiver.py
"""
import csv
import hashlib
import io
import json
import subprocess
from pathlib import Path

D = Path.home() / "nexora-creative-data/promo/v6-creative"
ICI = Path(__file__).resolve().parent
DEST = "Bureau/Nexora-Livrables/TOUS-LES-FILMS/creative-v6"
INV = "Bureau/Nexora-Livrables/TOUS-LES-FILMS/INVENTAIRE.csv"
FFPROBE = str(Path.home() / "nexora-creative-data/engine/ffmpeg/ffmpeg-7.0.2-arm64-static/ffprobe")
# (motif, sous-dossier, quoi, rôle, modèle)
GROUPES = [
    ("montage/*.mp4", "films", "Film V6 « Trois mots. » (Creative)", "master", "montage monter_v6.py"),
    ("rushes/*.mp4", "rushes-plans-H3", "Rush du film V6 (parcours réel Creative : boost → image clé → Qualité cinéma)", "rush", "MiniMax H3 h3-max (10Eros-Max × Singularity)"),
    ("rushes/dialogues/*.mp4", "rushes-dialogues-H3", "Plan à réplique du film V6 (voix native H3)", "rush", "MiniMax H3 h3-max"),
    ("voix/h3/*.mp4", "voix-essais-H3", "Essai de voix native H3 (distribution des voix V6)", "travail", "MiniMax H3 h3-max"),
    ("voix/narration/h3-*/brut/*.mp4", "voix-narration-H3", "Narration V6 en voix native H3 (groupes de phrases)", "travail", "MiniMax H3 h3-max"),
    ("captures/detourage/sorties/*.mp4", "detourage", "Sortie réelle du détourage vidéo (SAM 2.1 + ViTMatte)", "rush", "détourage Creative"),
    ("captures/detourage-src/*.mp4", "detourage", "Source du détourage (extrait de rush V6)", "rush", "MiniMax H3"),
    ("cache-montage/essais/*.mp4", "essais", "Essai de montage V6 (animatique, essais du moteur)", "travail", "monter_v6.py"),
    ("voix/casting/*.mp3", "voix-casting", "Échantillon de distribution des voix V6 (même texte pour tous)", "travail", "voir voix/casting/casting.jsonl"),
    ("voix/casting/*.wav", "voix-casting", "Échantillon de distribution des voix V6 (même texte pour tous)", "travail", "Qwen3-TTS VoiceDesign (pc1, CPU)"),
    ("musique/lyria-*.mp3", "musique", "Bande originale candidate V6", "travail", "Lyria 3 Pro (OpenRouter)"),
]


def sh(cmd, **kw):
    return subprocess.run(cmd, check=True, capture_output=True, text=True, **kw).stdout


def sonde(f):
    try:
        j = json.loads(sh([FFPROBE, "-v", "error", "-show_entries", "format=duration:stream=width,height", "-of", "json", str(f)]))
        st = next((s for s in j.get("streams", []) if s.get("width")), {})
        return round(float(j["format"]["duration"]), 2), f"{st.get('width', '')}x{st.get('height', '')}" if st else ""
    except Exception:
        return 0.0, ""


if __name__ == "__main__":
    essais = ICI / ".cache/essais"
    connus = set(sh(["ssh", "pc1", f"cut -d, -f6 {INV}"]).split())
    lignes = []
    for motif, sous, quoi, role, modele in GROUPES:
        base = essais.parent if motif.startswith("essais/") else D
        for f in sorted(base.glob(motif)):
            h = hashlib.sha256(f.read_bytes()).hexdigest()
            dest = f"{DEST}/{sous}/{f.name}"
            sh(["ssh", "pc1", f"mkdir -p {DEST}/{sous}"])
            sh(["rsync", "-a", str(f), f"pc1:{dest}"])
            if h in connus:
                continue
            duree, res = sonde(f)
            lignes.append([f"creative-v6/{sous}/{f.name}", f.stat().st_size, duree, res,
                           __import__("time").strftime("%Y-%m-%d %H:%M", __import__("time").localtime(f.stat().st_mtime)), h, quoi, "V6",
                           modele, role, "", "", f"pc6:{f}", 1, ""])
            connus.add(h)
    if lignes:
        buf = io.StringIO()
        csv.writer(buf).writerows(lignes)
        subprocess.run(["ssh", "pc1", f"cat >> {INV}"], input=buf.getvalue(), text=True, check=True)
    print(f"{len(lignes)} nouvelles lignes dans INVENTAIRE.csv")
