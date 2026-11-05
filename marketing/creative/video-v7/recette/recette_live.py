"""Recette « prise de vues réelles » (live action) contre aspect jeu vidéo : banc sur les 6 plans les plus « jeu » de la V6.
Écrit les specs pour moteur.py (V3) : images clés Qwen-Image-2.1 (GB10) au vocabulaire photographique + négatif anti-rendu,
puis plans h3-max (5090) à partir de ces images, au vocabulaire de tournage réel.
  python3 recette_live.py > specs-recette.json ; python3 ../../video-v3/moteur.py specs-recette.json
"""
import json
from pathlib import Path

D = "~/nexora-creative-data/promo/v7-creative/recette"
PRISM = "10Eros_Max_h3_8stepTURBO_beta7_SingularityV2_ref2va_int8HQ.safetensors"

# 1) ce qui fait « jeu » (diagnostic V6 : 37 « cinematic », 26 « glowing », 23 « epic », 21 « incandescent », 15 « grade »,
#    0 caméra réelle, 0 pellicule, 0 éclairage pratique) : on l'interdit au positif et on le repousse au négatif.
NEG = ("3d render, cgi, computer graphics, video game, game cinematic, unreal engine, octane render, digital painting, concept art, "
       "illustration, matte painting, fantasy art, airbrushed, smooth plastic surfaces, clean perfect surfaces, oversaturated, neon glow, "
       "bloom, hdr, teal and orange grade, glossy, toy, miniature look, symmetrical composition, text, letters, logo, watermark")
# 2) ce qui fait « tournage réel » : caméra et objectif nommés, support, lumière pratique, atmosphère, imperfections, échelle.
CAM = ("Production still from a live-action feature film, photographed on location on 35mm film (Kodak Vision3 500T) with an "
       "{objectif}; natural exposure, visible film grain, slight halation around bright sources, soft lens imperfections, ")
VID = ("Live-action footage shot on 35mm film, {operateur}, natural motion blur from a 180-degree shutter, slight focus breathing, "
       "real physics and weight, practical fire, smoke and debris, film grain. ")

PLANS = {
    "r01-dragon-chateau": dict(  # V6 791
        objectif="old Cooke 400mm telephoto lens from 300 metres away, compressed perspective, heat shimmer",
        cle="dusk on a rainy Scottish hillside: a huge dragon with scarred, mud-caked leathery hide clings to the top of a real ruined stone "
            "keep and breathes a jet of real fire onto the wet battlements; the fire lights the drizzle and the wet stone, thick black smoke "
            "drifts across heavy overcast clouds, three soldiers in muddy cloaks stand in silhouette in the long grass in the foreground for scale.",
        operateur="long-lens camera on a tripod with a slight pan, compressed telephoto perspective",
        action="The dragon arches its neck and breathes a long jet of fire onto the battlements, burning debris falls, smoke rolls in the wind, "
               "the soldiers in the foreground flinch. The camera pans slightly to follow the flames.",
        son="Roaring fire, crackling burning timber, heavy rain, a deep animal growl in the distance, wind."),
    "r02-dragon-survol": dict(  # V6 809
        objectif="handheld Arri Alexa 35 with a 24mm Panavision lens, dirt and rain drops on the lens",
        cle="night, a soldier's point of view on a real castle rampart in the rain: the belly and wings of an enormous dragon pass a few metres "
            "overhead, its wet hide lit from below by burning torches and fires, sparks and embers fly, a torn banner whips in the wind.",
        operateur="handheld camera operator running along the wall, strong shake, the frame shudders as the creature passes",
        action="The dragon sweeps low over the rampart from right to left, the downdraft whips rain and embers into the lens, the camera ducks "
               "and recovers, fires burn on the wall.",
        son="Deafening wingbeats, gusting wind, rain, crackling fires, men shouting in the distance."),
    "r03-espace-plongee": dict(  # V6 797
        objectif="motion-control camera with a 35mm lens; the warships are large detailed physical miniature models with weathered paint, "
                 "panel lines and scorch marks, lit by a single hard key light like 1980s practical model photography",
        cle="low Earth orbit seen from a real spacecraft window: two battered grey warships pass close, hard unfiltered sunlight from one side "
            "and pitch-black shadows, a real cloud-covered Earth below, a small explosion of debris and vented gas, no coloured glow.",
        operateur="motion-control camera gliding forward between the hulls",
        action="The camera glides forward between the two hulls as a small explosion throws metal debris and white vented gas across the frame, "
               "hard sunlight flickers across the plating.",
        son="Muffled metallic groans through the hull, a dull distant impact, the hiss of venting gas, near silence."),
    "r04-dragon-croiseur": dict(  # V6 810
        objectif="Arri Alexa 65 with a 50mm lens, shot like aerial footage from a chase helicopter, high-altitude haze",
        cle="above a real cloud layer at sunset: an enormous dragon grips the scarred steel hull of a grey military airship the size of a ship "
            "and breathes fire onto the plating; rivets, rust streaks, buckled panels, the fire lights the hull, real sunlight and haze.",
        operateur="aerial camera from a chase helicopter, slight vibration, the frame drifts with the wind",
        action="The dragon tears at the hull and breathes fire, metal plates buckle and fall away tumbling into the clouds, smoke streams "
               "backwards in the wind.",
        son="Roaring wind, the dragon's roar, tearing metal, a deep engine drone, fire."),
    "r05-flotte-aube": dict(  # V6 819
        objectif="Panavision 600mm wildlife telephoto lens, shot like a BBC nature documentary",
        cle="sunrise over real misty mountain valleys in Patagonia: a flock of a dozen dragons flies in a loose line far away through layers "
            "of morning mist, backlit by the low sun, heavy atmospheric haze, the closest dragon still small in frame, real pine forests below.",
        operateur="wildlife camera on a gimbal tracking the flock, long-lens compression",
        action="The flock flies slowly across the valley through the mist, wings beating unevenly like real birds, the sun rises behind them.",
        son="Wind over mountains, distant cries of the creatures, faint wingbeats."),
    "r06-duel-pluie": dict(  # V6 795
        objectif="handheld Arri Alexa Mini with a 32mm lens, rain on the lens",
        cle="night, heavy rain on a real industrial rooftop: two stunt performers in soaked dark hooded coats cross two orange energy blades; "
            "the blades are the only light, practical orange light on wet skin and rain drops, steam rising where rain hits the blades, "
            "sodium street lights blurred far below, puddles.",
        operateur="handheld camera operator circling the fighters, real shake",
        action="The fighters clash twice, sparks and steam burst at each impact, one fighter is pushed back and slips on the wet roof, rain "
               "pours, the camera circles closer.",
        son="Heavy rain, electric hum and crackle of the blades, heavy impacts, boots on wet metal, breathing."),
}


def specs():
    out = []
    for nom, p in PLANS.items():
        out.append({"type": "image", "nom": f"{nom}-cle", "prompt": CAM.format(objectif=p["objectif"]) + p["cle"], "negatif": NEG,
                    "largeur": 1664, "hauteur": 928, "graine": 2601, "sortie": D})
    for nom, p in PLANS.items():
        prompt = ("For the target video, at 0.00 seconds into the target video, <Picture 1> (from [Shot 1]) is fully referenced.\n\n"
                  "integrated_multimodal_description: [Shot 1] " + VID.format(operateur=p["operateur"]) + p["action"]
                  + " No text, no logos.\n\noverall_soundscape: " + p["son"] + "\n\nnon_diegetic_music: N/A")
        out.append({"type": "h3", "nom": f"{nom}", "prompt": prompt, "checkpoint": PRISM, "etapes": 8, "decalage": [12, 3],
                    "echantillonneur": "euler", "ref": True, "image": f"{D}/{nom}-cle.png", "largeur": 1344, "hauteur": 768,
                    "images": 124, "graine": 2602, "sortie": D})
    return out


if __name__ == "__main__":
    print(json.dumps(specs(), ensure_ascii=False, indent=1))
