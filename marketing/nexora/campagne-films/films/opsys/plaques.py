"""Plaques du film OPSYS-AI : images clés Qwen-Image (vérifiées une à une), puis plans H3 en image vers vidéo depuis l'image clé.

  python3 plaques.py cles [id ...]           images clés 1344x768 (GB10, Qwen-Image)
  python3 plaques.py videos [id[:max]] ...  plans H3 5 s depuis l'image clé (RTX 5090 ; « :max » = recette h3-max, sinon h3-fast)
  Le 02/11 la recette h3-max de pc1 = 10Eros-Max × Singularity (ref2va, 8 étapes) : lancer avec
  NEXORA_H3_MAX_CHECKPOINT=10Eros_Max_h3_8stepTURBO_beta7_SingularityV2_ref2va_int8HQ.safetensors (le FL2VA complet a été retiré).

Règles : aucun visage reconnaissable (dos, mains, silhouettes, contre-jour), aucun texte, aucun logo, aucune marque ; lumière
« Signal » : nuit ou aube, bleu ion froid, un seul point chaud. Québec : maisons à revêtement, gouttières, neige légère, aréna.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "refonte-medias/outils"))
import moteurs  # noqa: E402
from moteurs import image, video, h3  # noqa: E402

# recette h3-max du studio (app/server/nexora/creer.ts) : point de contrôle ref2va distillé, 8 étapes, mode référence
moteurs.H3_MAX = {"videoModel": "h3-max", "steps": 8, "refMode": True}

D = Path.home() / "nexora-creative-data/promo/v6/opsys/plaques"
STYLE = ("cinematic film still, anamorphic 35mm, shallow depth of field, deep blue night-and-dawn palette with cold ion-blue light, "
         "one small warm orange light source, rich shadows, fine film grain, photorealistic, no text anywhere, no logos, no brands")
PLANS = {
    # id : (image clé, mouvement H3, son d'ambiance)
    "l1-course": ("A lone runner seen from behind jogging along an empty riverside path at blue dawn in Quebec, mist over the water, "
                  "bare trees, a single warm streetlamp far ahead",
                  "Slow tracking shot following the runner from behind, breath visible in the cold air, mist drifting",
                  "Footsteps on gravel, soft breathing, distant birds, calm river"),
    "m1-appel": ("A smartphone lying face up on a dark kitchen counter at night, its screen glowing soft blue and lighting the "
                 "marble, rain drops on the window behind, a warm range-hood light far in the background, screen content blurred",
                 "Very slow push-in toward the glowing phone, the screen pulses gently as a call arrives, rain on the window",
                 "Soft rain on glass, a gentle phone vibration buzz"),
    "m3-maison": ("A two-storey Quebec suburban house with horizontal siding and aluminum gutters at blue hour, light snow on the lawn, "
                  "thin glowing blue measurement lines tracing the roof edge and gutters like light, one warm window",
                  "Slow lateral dolly along the house facade while thin lines of blue light trace the gutters and roof edges",
                  "Quiet suburban night, light wind, a soft electronic shimmer"),
    "l2-dejeuner": ("Over-the-shoulder view of a father and a young child at a breakfast table at sunrise, seen from behind, warm "
                    "golden window light, bowls and orange juice, cozy kitchen, faces not visible",
                    "Gentle handheld drift around the table, the child reaches for a glass, morning light flickers through curtains",
                    "Spoons clinking, soft laughter, morning kitchen ambience"),
    "m4-camion": ("A white work pickup truck with a ladder rack leaving a driveway at dawn, headlights on, exhaust vapour in the cold air, "
                  "Quebec residential street, no lettering on the truck",
                  "Low tracking shot as the truck pulls out and drives away down the street, headlights flare",
                  "Truck engine starting and pulling away, tires on wet asphalt"),
    "m6-entrepot": ("Interior of a small contractor warehouse at night, tall shelves of aluminum gutter coils and siding boxes, "
                    "cold blue overhead light, one warm work lamp, a reserved pallet glowing softly, no labels",
                    "Slow forward dolly down the aisle between the shelves, dust floating in the light beams",
                    "Hum of fluorescent lights, a distant forklift beep"),
    "m5-bureau": ("A minimalist home-office desk at night, a closed laptop, a fountain pen and a blank sheet of paper lit by a single "
                  "warm desk lamp, blue city light from the window, nobody present",
                  "Slow overhead slide across the desk toward the paper, the lamp light breathes softly",
                  "Quiet room tone, a soft clock tick"),
    "l3-terrasse": ("A man seen from behind sitting on a lakeside dock at golden late afternoon, coffee cup in hand, calm lake, "
                    "Quebec forest, warm sun low on the horizon, face not visible",
                    "Slow push-in from behind the man toward the lake, light ripples on the water",
                    "Lapping water, distant loon call, gentle breeze"),
    "m7-photo": ("Close-up of a worker's gloved hands holding a smartphone to photograph freshly installed dark grey siding and gutters "
                 "on a house at sunset, the phone screen shows only a blurred image of the wall, no interface text",
                 "Slow orbit around the hands as the phone frames the finished siding, warm sunset flare",
                 "Camera shutter click, light wind, birds"),
    "m2-porte": ("A homeowner opening a front door to a contractor seen from behind at dusk, warm light spilling from the entrance, "
                 "porch light, snow on the steps, both faces hidden",
                 "Slow push-in from behind the contractor as the door opens and warm light spills out",
                 "Door opening, muffled friendly greeting, winter wind"),
    "m9-matin": ("A kitchen island at 7 am, a steaming cup of coffee next to a smartphone emitting a soft blue glow, blue dawn outside "
                 "the window, a single warm pendant light, nobody present",
                 "Very slow push-in toward the cup and phone, steam rises through the light",
                 "Coffee machine finishing, quiet morning ambience"),
    "l4-hockey": ("A father seen from behind in the stands of a small Quebec community hockey arena at night, children playing hockey "
                  "on the bright ice below, cold blue arena light, warm glow of the snack bar, faces not visible, no logos, plain jerseys",
                  "Slow push-in over the father's shoulder toward the ice as a child skates past, the father raises his arms",
                  "Arena echo, skates carving ice, puck on stick, small crowd cheer"),
}


if __name__ == "__main__":
    cmd, ids = sys.argv[1], sys.argv[2:]
    D.mkdir(parents=True, exist_ok=True)
    if cmd == "cles":
        for i in ids or list(PLANS):
            f = D / f"{i}-cle.png"
            if not f.exists():
                print(image(f"{PLANS[i][0]}. {STYLE}", f, 1344, 768, seed=7)[1:], i, flush=True)
    elif cmd == "videos":
        for a in ids or list(PLANS):
            i, _, m = a.partition(":")
            moteur = "max" if m.startswith("max") else "rapide"
            f = D / f"{i}-{moteur}{m[3:] if m.startswith('max') else ''}.mp4"
            if not f.exists():
                p = h3(f"{PLANS[i][0]}. {PLANS[i][1]}. Photorealistic cinematic, no text, no logos.", PLANS[i][2])
                print(video(p, f, "16:9", moteur, 5, True, seed=11 + len(m), depart=D / f"{i}-cle.png")[1:], f.name, flush=True)
