"""Film music (MiniMax-Music3, GB10). Usage: python3 musiques.py [names...] [--variantes 2]
Description in the format expected by Music3 (Global Metadata / Vocal Details / Arrangement), instrumental."""
import sys, argparse
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent / "outils"))
from moteurs import musique, TRAVAIL

def desc(meta, arr):
    return f"Global Metadata: {meta}\n\nVocal Details: Instrumental, no lyrics, no vocals.\n\nArrangement: {arr}"

PAROLES = "[Intro]\n[Build]\n[Drop]\n[Climax]\n[Outro]"

MUSIQUES = {
  "surv": (44, desc("Cinematic dark electronic, 100 BPM, D minor, modern trailer production, wide stereo, deep sub-bass, "
                   "polished mix. Progression: tense and suspended for 14 seconds, a sudden decisive impact, then a confident "
                   "driving pulse that grows, and a clean resolved ending.",
                   "Intro: a quiet ticking clock-like hi-hat, a low sustained sub drone and sparse cold synth notes. At about 14 "
                   "seconds a huge low impact with a reverse swell before it. Then a tight pulsing synth bass in sixteenth notes, "
                   "crisp electronic percussion and wide string pads build steadily. Final 6 seconds: the rhythm stops, one "
                   "sustained resolved chord with a soft shimmer that fades out.")),
  "recep": (44, desc("Warm modern electronic pop instrumental, 96 BPM, A major, bright and optimistic, clean premium "
                    "production, soft dynamics. Progression: gentle start, friendly groove, uplifting peak, soft ending.",
                    "Intro: soft felt piano chords and a gentle plucked synth arpeggio. Then light finger snaps, a round bass "
                    "and airy pads join with a relaxed groove. Middle: a bright uplifting lift with shimmering bells and wide "
                    "strings. Last 6 seconds: piano alone with a soft pad, ending on a warm sustained chord.")),
  "infra": (44, desc("Epic monumental cinematic electronic, 90 BPM, C minor, huge low end, modern blockbuster trailer "
                    "production. Progression: dark and vast, slow powerful build, massive climax, resolved ending.",
                    "Intro: deep metallic drones and slow distant booms in a vast space. Build: pulsing low synth ostinato, "
                    "taiko-like drums and rising brass-like synth swells. Climax around 28 seconds: full powerful hits with wide "
                    "strings. Last 6 seconds: a single deep sustained chord and a metallic shimmer fading out.")),
  "crea": (44, desc("Hybrid orchestral cinematic, 110 BPM, E minor to G major, wonder and energy, modern film trailer "
                   "production, very dynamic. Progression: mysterious, then accelerating, a big heroic climax, a bright ending.",
                   "Intro: delicate celesta and soft strings. Build: driving staccato strings, big drums and synth pulses "
                   "accelerate with risers between sections. Climax: heroic full orchestra with choir-like synth pads and "
                   "powerful percussion hits. Last 6 seconds: a bright sustained major chord with shimmering bells.")),
  "work": (44, desc("Precise minimal electronic, 112 BPM, F major, optimistic and focused, clean modern production. "
                   "Progression: steady clockwork beginning, layers added one by one, confident peak, neat ending.",
                   "Intro: marimba-like plucked arpeggio in a clockwork pattern and soft clicks. Build: a warm bass, light "
                   "kick and crisp hi-hats, glassy synth chords added one layer at a time. Peak: bright lead synth motif over "
                   "the full groove. Last 6 seconds: the arpeggio alone resolving on a clean final note.")),
  "code": (44, desc("Deep focused electronic, 118 BPM, G minor, nocturnal and driving, analog synth production, tight mix. "
                   "Progression: hypnotic start, building momentum, energetic peak, crisp ending.",
                   "Intro: a filtered analog bass arpeggio and soft rain-like noise. Build: the filter opens, crisp hi-hats, "
                   "a punchy kick and glassy pads join. Peak: a bright pulsing lead and wide chords at full energy. Last 6 "
                   "seconds: everything drops to a single sustained pad and a last soft bass note.")),
}

if __name__ == "__main__":
    a = argparse.ArgumentParser()
    a.add_argument("noms", nargs="*"); a.add_argument("--variantes", type=int, default=2)
    o = a.parse_args()
    for nom in (o.noms or list(MUSIQUES)):
        sec, d = MUSIQUES[nom]
        for v in range(1, o.variantes + 1):
            f = TRAVAIL / "musique" / f"{nom}-v{v}.flac"
            if f.exists():
                continue
            try:
                _, tid, s = musique(d, f, sec, PAROLES, seed=77 + 31 * v)
                print(f"ok {f.name} prise {tid} {s:.0f}s", flush=True)
            except Exception as e:
                print(f"ECHEC {f.name} {e}", flush=True)
