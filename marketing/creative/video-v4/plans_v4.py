"""Promo V4 « Une phrase. Un film. » : images clés Qwen-Image et plans MiniMax H3 de la séquence « tout ce que tu peux imaginer ».

Le film du héros (le parfum) n'est PAS ici : il est tourné par le vrai Producteur du studio (capturer.mjs), c'est la preuve.
Ici : six genres différents, chacun né d'une seule phrase (affichée à l'écran, en code). Aucun texte dans les images.

Usage : python3 plans_v4.py cles > specs-cles.json ; python3 plans_v4.py plans > specs-plans.json
        python3 ../video-v3/moteur.py specs-cles.json   (client ComfyUI partagé de la V3 : file normale, rien n'est tué)
"""
import json
import sys

D = "~/nexora-creative-data/promo/v4/"
PRISM = "10Eros_Max_h3_8stepTURBO_beta7_SingularityV2_ref2va_int8HQ.safetensors"
NEG = ("text, letters, words, numbers, writing, signage with letters, logo, watermark, signature, brand name, label, caption, "
       "subtitles, cartoon franchise character, famous person, deformed, extra limbs, extra fingers, distorted face, lowres, blurry, "
       "oversaturated, plastic skin, 3d render look, video game look")
FILM = ("Cinematic still frame from a 2026 feature film, shot on a large-format digital cinema camera with anamorphic lenses, "
        "real exposure, rich contrast, natural film colour, fine grain, shallow depth of field. ")

# nom : (phrase fr, phrase en, image clé, mouvement H3, ambiance sonore)
GENRES = {
    "g1-ville": (
        "Une ville sous la pluie, la nuit.", "A city in the rain, at night.",
        FILM + "A rainy night in a dense modern metropolis seen from street level: an elevated train glides on a bridge between glass "
        "towers, the wet asphalt below mirrors pools of magenta, cyan and amber light, a lone figure with a transparent umbrella crosses "
        "the foreground in silhouette, thick rain streaks lit by the lights, light haze, bokeh. All light panels are plain glowing colour "
        "with no writing at all.",
        "The elevated train glides across the frame from left to right, its lit windows streaking past; rain falls hard and splashes in "
        "the puddles, reflections ripple; the silhouette with the transparent umbrella walks slowly across the foreground. The camera "
        "tracks slowly sideways at street level.",
        "Heavy rain on asphalt and on an umbrella, the rumble and electric whine of a passing elevated train, distant city hum."),
    "g2-chevaux": (
        "Des chevaux sauvages au coucher du soleil.", "Wild horses at sunset.",
        FILM + "Nature documentary: a herd of wild horses gallops through shallow water across a vast flat plain at sunset, huge sprays "
        "of water backlit in gold, manes flying, low-angle telephoto lens, the sun low on the horizon, glittering droplets, epic scale.",
        "In slow motion the herd gallops through the shallow water towards the right of the frame, hooves throwing up huge golden "
        "sprays, manes and tails flowing, droplets glittering against the low sun. The telephoto camera pans smoothly with the herd.",
        "Thundering hooves splashing through water in slow motion, deep rumble, wind."),
    "g3-chocolat": (
        "Du chocolat, au ralenti.", "Chocolate, in slow motion.",
        "High-end food commercial photography, macro lens, high-speed camera: a thick glossy ribbon of molten dark chocolate pours "
        "onto a perfect pile of fresh red strawberries on a dark slate, warm golden rim light, black background, droplets of chocolate "
        "suspended in the air, luxurious, appetising, extremely detailed textures.",
        "Extreme slow motion: the glossy ribbon of molten chocolate keeps pouring and folds over the strawberries, coating them in "
        "shining waves, a strawberry rolls and splashes into the chocolate, droplets fly. The macro camera slowly pushes in.",
        "Soft thick liquid pouring sound, a gentle splash, close and intimate."),
    "g4-robe": (
        "Une robe rouge dans le vent du désert.", "A red dress in the desert wind.",
        FILM + "Fashion film: a woman seen from behind in three-quarter view stands on the crest of a pale golden sand dune, her long "
        "flowing crimson silk dress and long train billow in a huge wave in the wind against a deep clear blue sky, wide shot, golden "
        "hour sunlight, sand blowing off the crest, editorial elegance. Her face is turned away from the camera.",
        "The wind blows strongly: the long crimson silk train ripples and billows in huge slow waves behind her, sand streams off the "
        "dune crest, she slowly raises one arm. The camera slowly orbits around her at a distance.",
        "Strong desert wind, fluttering silk fabric, fine sand hissing."),
    "g5-vague": (
        "Un surfeur dans le tube.", "A surfer inside the barrel.",
        FILM + "Action sports cinematography: a surfer crouches low on his board deep inside the barrel of a huge curling turquoise "
        "wave, sunlight shining through the translucent wall of water, spray and mist, seen from inside the tube behind him, the bright "
        "opening ahead, crystal clear water.",
        "The surfer rides fast through the curling barrel towards the bright opening, the translucent turquoise wall of water curls "
        "over his head, spray explodes around him. The camera follows him from behind inside the tube.",
        "Roaring crashing wave, rushing water inside the tube, spray hissing."),
    "g6-papier": (
        "Un village de papier qui s'allume.", "A paper village lighting up.",
        "Handcrafted stop-motion animation still, original art style: a miniature papercraft village at dusk on layered paper hills, "
        "little folded paper houses with warm glowing windows, a winding river of crinkled blue cellophane with tiny paper boats, paper "
        "trees, paper stars hanging on threads in a deep blue paper sky, tilt-shift macro photography, soft warm light, cosy and magical.",
        "One by one the little windows of the paper houses light up warm orange, the cellophane river shimmers and the tiny paper boats "
        "drift, the paper stars sway gently on their threads. The camera glides slowly forward over the miniature village.",
        "Soft paper rustling, a gentle music-box like chime, crickets, cosy evening."),
}


def cles():
    out = []
    for nom, (_, _, img, _, _) in GENRES.items():
        for g in (11, 12):
            out.append({"type": "image", "comfy": "http://127.0.0.1:37188", "nom": f"{nom}-{g}", "prompt": img, "negatif": NEG,
                        "largeur": 1664, "hauteur": 928, "graine": g, "sortie": D + "cles"})
    return out


def prompt_ref(img, mouv, son):
    return ("subject_definitions:\n<Picture 1> is the first frame of [Shot 1], establishing the composition, the subjects and the lighting.\n\n"
            "summary:\n[reference generation] A single continuous cinematic shot that begins from <Picture 1>.\n\n"
            "retention_analysis:\n<Picture 1> ([Shot 1] first frame): fully_preserved - the composition, subjects, art style and lighting "
            "of the first frame are kept.\n\n"
            f"detailed_description:\n{img}\n[Shot 1] The shot begins from <Picture 1>. {mouv} No text, no logos.\n\n"
            f"overall_soundscape:\n{son}\n\nnon_diegetic_music:\nN/A")


def plans(choix):
    """choix : {nom: graine de l'image clé retenue}. Deux prises par plan (graines 7001, 7002)."""
    out = []
    for nom, g in choix.items():
        _, _, img, mouv, son = GENRES[nom]
        for k in (1, 2):
            out.append({"type": "h3", "nom": f"{nom}-p{k}", "largeur": 1344, "hauteur": 768, "images": 124, "graine": 7000 + k,
                        "sortie": D + "plans", "checkpoint": PRISM, "etapes": 8, "decalage": [12, 3], "echantillonneur": "euler",
                        "ref": True, "image": f"{D}cles/{nom}-{g}.png", "prompt": prompt_ref(img, mouv, son)})
    return out


if __name__ == "__main__":
    if sys.argv[1] == "cles":
        print(json.dumps(cles(), ensure_ascii=False, indent=1))
    else:
        print(json.dumps(plans(json.loads(sys.argv[2])), ensure_ascii=False, indent=1))
