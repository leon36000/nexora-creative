import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "outils"))
from generer import musique
M = {
 "A-epique": "Instrumental cinématographique de 60 secondes, sans voix. Ouverture presque silencieuse : un pouls grave et quelques notes de piano seules dans le noir, puis montée progressive de cordes et de synthétiseurs chauds, tension qui s'accumule, un grand impact (chute) à environ 38 secondes, puis résolution lumineuse et large, final qui s'éteint sur un dernier accord soutenu et un court silence. Tempo environ 90 BPM. Émotion : rêve, grandeur, nuit québécoise, aurore.",
 "B-pixels": "Électronique orchestrale moderne de 60 secondes, sans voix : pouls de basse sourd, arpèges cristallins qui rappellent de petits points de lumière qui s'allument un à un, percussions douces qui montent, nappe de synthétiseur chaude, grande montée puis chute puissante à environ 36 secondes, section héroïque avec cordes, outro calme. Tempo environ 100 BPM. Précision et émotion.",
 "C-piano": "Minimalisme émotionnel de 60 secondes, sans voix, style film de marque haut de gamme : piano doux et nappes chaudes, cordes qui s'ouvrent lentement, crescendo noble sans percussions lourdes, point culminant lumineux à environ 40 secondes, fin tendre qui se pose. Tempo environ 80 BPM. Espoir, calme, force tranquille.",
}
for nom, envie in M.items():
    f = Path("musique") / f"{nom}.flac"
    if f.exists(): continue
    try:
        musique(envie, f, 60); print("ok", f.name, flush=True)
    except Exception as e:
        print("ECHEC", nom, e, flush=True)
