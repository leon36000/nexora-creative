import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "outils"))
from generer import musique
M = {
 "D-30s": ("Instrumental cinématographique de 30 secondes exactement, sans voix, même univers que piano, nappes chaudes et cordes : trois secondes d'ouverture presque silencieuse avec quelques notes de piano seules, montée rapide de cordes et de synthétiseurs, un grand impact (chute) très net à 20 secondes précises, résolution lumineuse, final qui se pose sur un dernier accord soutenu à 28 secondes puis silence. Tempo environ 115 BPM.", 30),
 "E-15s": ("Instrumental cinématographique de 15 secondes exactement, sans voix : une note de piano seule dans le noir, montée immédiate de cordes et de synthétiseurs, grand impact net à 9 secondes précises, final lumineux qui se pose sur un accord soutenu à 14 secondes. Tempo environ 115 BPM.", 15),
 "F-6s": ("Instrumental très court de 6 secondes exactement, sans voix : une note aiguë cristalline qui monte pendant 3,5 secondes avec un souffle, puis un impact grave net à 4 secondes précises suivi d'un accord lumineux qui s'éteint. Style film de marque haut de gamme.", 8),
}
for nom, (envie, dur) in M.items():
    f = Path("musique") / f"{nom}.flac"
    if f.exists(): continue
    try:
        musique(envie, f, dur); print("ok", f.name, flush=True)
    except Exception as e:
        print("ECHEC", nom, e, flush=True)
