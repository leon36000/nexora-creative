"""Film V6 : narration complète, une phrase par fichier (stems interchangeables au montage).
  python3 voix_narration.py eleven <fr|en> [voix]        ElevenLabs v4 via OpenRouter (voix : alexandre, liam, callum…)
  python3 voix_narration.py h3 <fr|en>                   voix native MiniMax H3 (h3-max sur la 5090), par groupes de phrases,
                                                         timbre tenu par une référence audio (<Audio 1>) ; découpe par Whisper
Sortie : ~/nexora-creative-data/promo/v6-creative/voix/narration/<moteur>-<langue>/<id>.wav (48 kHz mono, bords coupés)
Textes : narration-v6.json (seul endroit).
"""
import json
import subprocess
import sys
import time
from pathlib import Path

ICI = Path(__file__).resolve().parent
sys.path.insert(0, str(ICI))
import voix_casting as VC  # noqa: E402

D = Path.home() / "nexora-creative-data/promo/v6-creative/voix/narration"
FF = str(Path.home() / "nexora-creative-data/engine/ffmpeg/ffmpeg-7.0.2-arm64-static/ffmpeg")
NARR = json.loads((ICI / "narration-v6.json").read_text())
VOIX_ELEVEN = {"alexandre": VC.ALEXANDRE}
# Direction par phrase : les questions montent, les « Réglé » tombent sec, la fin est triomphale.
TAG = {"v13": "[suspenseful, teasing] ", "v14": "[confident, punchy] ", "v15": "[triumphant, big grin] "}


def nettoyer(src, dst):
    f = ("silenceremove=start_periods=1:start_threshold=-45dB:start_silence=0.02,areverse,"
         "silenceremove=start_periods=1:start_threshold=-45dB:start_silence=0.05,areverse,highpass=f=70")
    subprocess.run([FF, "-v", "error", "-y", "-i", str(src), "-af", f, "-ar", "48000", "-ac", "1", str(dst)], check=True)


def eleven(langue, voix):
    out = D / f"eleven4-{voix}-{langue}"
    out.mkdir(parents=True, exist_ok=True)
    for i, texte in NARR[langue].items():
        brut = out / f"{i}.brut.mp3"
        pre = TAG.get(i, "[excited] [punchy] ")
        brut.write_bytes(VC.parler("elevenlabs/eleven-v4", pre + texte, VOIX_ELEVEN.get(voix, voix), {}))
        nettoyer(brut, out / f"{i}.wav")
        print(i, texte, flush=True)


if __name__ == "__main__":
    moteur, langue = sys.argv[1], sys.argv[2]
    if moteur == "eleven":
        eleven(langue, sys.argv[3] if len(sys.argv) > 3 else ("alexandre" if langue == "fr" else "liam"))
