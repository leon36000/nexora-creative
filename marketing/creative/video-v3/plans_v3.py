"""Prompts MiniMax H3 des plans de la promo V3 (format du guide officiel : description intégrée, ambiance sonore, musique).

Deux familles :
  - i2v : le plan part d'une image clé Qwen-Image-2.1 (cles/), qui porte déjà l'échelle (flotte, planète, vaisseaux-villes) ;
  - t2v : plans d'action pure (passages, poursuite, explosion proche) écrits directement.
Les moteurs sont choisis par la ronde de comparaison (voir JOURNAL-V3.md) : QUALITE pour les plans héros, VOLUME pour le reste.
Usage : python3 plans_v3.py > specs-plans.json   (puis python3 moteur.py specs-plans.json [noms…])
"""
import json
import sys

# Moteurs retenus après la comparaison (même graine, même prompt) : voir JOURNAL-V3.md
QUALITE = {"checkpoint": "10Eros_Max_h3_8stepTURBO_beta7_SingularityV2_ref2va_int8HQ.safetensors", "etapes": 8, "decalage": [12, 3],
           "echantillonneur": "euler", "ref": True}
VOLUME = {"checkpoint": "fastvideo_fasth3_8step_v2_pruned_nvfp4.safetensors", "etapes": 8, "decalage": [10, 3], "echantillonneur": "res_multistep"}
CLES = "~/nexora-creative-data/promo/v3/cles"
SORTIE = "~/nexora-creative-data/promo/v3/plans"
I2V = "For the target video, at 0.00 seconds into the target video, <Picture 1> (from [Shot 1]) is fully referenced.\n\n"
LOOK = ("Live-action IMAX footage from a 2026 science-fiction blockbuster, large-format film camera with anamorphic lenses, real exposure, "
        "deep blacks, cold steel-blue space light against hot orange-white fire, fine film grain, motion blur. Original ship designs. ")
FIN = "\n\nnon_diegetic_music: N/A"


def p(desc, son):
    return f"integrated_multimodal_description: [Shot 1] {LOOK}{desc} No text, no logos.\n\noverall_soundscape: {son}{FIN}"


PLANS = [
    # nom, image clé (ou None), moteur, description, son
    ("p01-orbite-nuit", "k01-orbite-nuit-101", VOLUME,
     "Silent wide shot from high orbit over the night side of the Earth. The camera drifts forward very slowly. Hundreds of tiny dark warships hold a long wall formation above the planet, their small blue engine lights flickering. Golden city lights twinkle under thin moving cloud layers, the thin blue line of the atmosphere glows, and the sunrise flare on the right edge slowly grows brighter.",
     "Near silence: a very low hum of deep space and a faint distant radio crackle."),
    ("p02-mur-flotte", "k02-mur-flotte-102", QUALITE,
     "The camera glides slowly along the flank of the kilometre-long battleship in the foreground, revealing rows upon rows of warships stretching to the horizon above the cloud-covered Earth. A wave of engine ignitions ripples through the formation, blue-white engine flares lighting up one after another as the whole fleet starts to move forward together.",
     "A deep rumbling of colossal engines swelling one after another, metallic hull groans, a low resonant thrum."),
    ("p03-vague-ennemie", "k03-vague-ennemie-103", QUALITE,
     "The black swarm of thousands of small angular enemy craft pours toward the camera at great speed, filling more and more of the frame, while the colossal crescent mothership looms behind, its red veins pulsing. Handheld camera with nervous shake, motion blur on the closest craft streaking past.",
     "A rising roar of thousands of engines like an insect swarm, a deep ominous drone, sharp whooshes as craft pass close."),
    ("p04-bordee", "k04-bordee-104", QUALITE,
     "The battleship's broadside fires again and again: muzzle flashes ripple down the whole flank in sequence, thick clouds of grey smoke burst out and drift, heavy tracer shells streak away into black space. The camera shakes violently with every salvo, handheld.",
     "Thunderous cannon salvos in rapid sequence, deep concussive booms, metallic clanks of reloading, rumbling smoke."),
    ("p05-hangar", "k05-hangar-105", VOLUME,
     "Handheld camera on the launch deck: the fighter craft launch one after another at tremendous speed through the open bay doors toward the blue Earth, blasting jets of white vapour, amber lights strobing, the camera shaking as each one roars past.",
     "Roaring jet engines, a hard launch catapult clang, alarm klaxon, rushing air."),
    ("p06-cockpit", "k06-cockpit-106", VOLUME,
     "Cockpit point of view, handheld vibration: the fighter banks hard to the left, the horizon of the Earth tilting, streams of orange tracer fire flash past the canopy, an enemy craft explodes ahead in an orange fireball and the fighter flies straight through the debris; the pilot's gloved hand pushes the stick.",
     "Engine whine, rapid cannon fire, alarm beeps, debris rattling on the canopy, a muffled explosion."),
    ("p07-pilote", "k07-pilote-107", QUALITE,
     "Close-up, handheld: the pilot's face is lit by flickering orange explosion light, she clenches her jaw, her eyes track something passing fast outside, then she exhales sharply; the cockpit vibrates and reflections of tracer fire slide over the glass.",
     "Heavy breathing inside the helmet, muffled explosions outside, cockpit rattle, a short alarm beep."),
    ("p08-vaisseau-mere", "k08-vaisseau-mere-108", QUALITE,
     "A chain of gigantic explosions races along the hull of the colossal crescent mothership above the Earth: fireballs burst one after another, armour plates and burning debris blast outward, rings of shockwave light expand, the hull starts to crack open. Slow camera push-in with heavy shake.",
     "Colossal detonations one after another, deep sub-bass booms, metal tearing, a roaring shockwave."),
    ("p09-rupture", "k09-rupture-109", QUALITE,
     "The two halves of the broken cruiser drift apart in slow motion, secondary explosions burst from the inside, fire and burning debris spray toward the camera, sparks and hull plates tumble past the lens, the glowing atmosphere of the Earth below.",
     "Deep metal groaning, crackling fire, rumbling secondary explosions, debris pinging off the camera."),
    ("p10-aube", "k10-aube-110", VOLUME,
     "Quiet aftermath: the sun rises over the Earth's horizon, warm golden light slowly floods the frame, a huge anamorphic lens flare spreads, burning wreckage tumbles slowly in the foreground, the surviving fleet stays silhouetted in formation.",
     "Near silence, a soft low hum, distant crackle of cooling metal."),
    ("t01-passage", None, QUALITE,
     "Handheld camera floating inside a dense space battle above the cloud tops of the Earth: three dark grey angular defender fighters scream past the lens from left to right at tremendous speed, firing streams of orange tracer fire, heavy motion blur, explosions flashing in the background, the camera whipping to follow them.",
     "Three fighters roar past with a doppler whoosh, rapid cannon bursts, distant explosions."),
    ("t02-poursuite", None, QUALITE,
     "Chase camera right behind a dark grey defender fighter weaving through a field of burning wreckage above the Earth, firing orange tracers at a black angular enemy craft ahead; the enemy craft explodes into a fireball and shrapnel sprays toward the lens. Violent handheld shake, motion blur.",
     "Engine roar, rapid cannon fire, a sharp explosion, debris clattering."),
    ("t03-torpilles", None, QUALITE,
     "Dozens of torpedoes launch in sequence from vertical tubes along the armoured spine of a huge gunmetal defender capital ship, each leaving a bright engine flare and a trail of white smoke, curving away in a swarm toward a distant dark crescent mothership above the Earth. Low angle, the camera rising slowly.",
     "A rapid series of heavy launch thumps, hissing rocket motors, rumble of the ship."),
    ("t04-explosion", None, QUALITE,
     "An angular enemy craft explodes right in front of the camera above the Earth: an enormous orange-white fireball fills the frame, burning debris, sparks and smoke fly straight into the lens, the camera is knocked back by the blast with violent shake.",
     "A huge close explosion, crackling fire, debris hitting the camera, a deep sub boom."),
    ("t05-onde-choc", None, QUALITE,
     "From high orbit: a colossal explosion detonates above the Earth, a flat ring-shaped shockwave of white-blue light expands across space over the cloud tops, hundreds of tiny defender ships silhouetted against the flash, debris racing outward.",
     "A colossal deep boom rolling in, a roaring shockwave, then rumbling."),
    ("t06-tourelle", None, QUALITE,
     "Close-up on the hull of a gunmetal battleship: a massive twin-barrel gun turret swings toward camera and fires rapidly, huge orange-white muzzle flashes, blast smoke, recoil, sparks, the Earth's cloud-covered surface far below. Handheld shake on each shot.",
     "Deafening cannon blasts with heavy recoil clanks, mechanical turret whine."),
    ("t07-essaim", None, QUALITE,
     "Wide shot: hundreds of black angular enemy craft dive like a swarm onto a long wall of defender warships above the Earth, the defenders answer with a dense curtain of orange tracer fire and blue plasma bolts, explosions sparkling across the formation. The camera pans fast to follow the dive.",
     "A dense roar of battle, thousands of cannon shots crackling, explosions rumbling in waves."),
    # Re-générations ciblées après l'auto-revue (tourelle trop molle, onde de choc aux chasseurs « jeu vidéo ») :
    ("t08-tourelle", "k11-tourelle-311", QUALITE,
     "Low angle on the battleship deck: the massive triple-barrel turret fires again and again, each shot a blinding orange-white muzzle blast with an expanding ring of smoke and a violent recoil, glowing shells streaking away into space, sparks raining on the deck; the camera shakes hard with every shot, handheld.",
     "Deafening heavy cannon blasts, metallic recoil clanks, pressure thumps, debris rattling on the deck."),
    ("t09-onde-choc", "k12-onde-choc-312", QUALITE,
     "The ring-shaped shockwave of white-blue light keeps expanding across space above the Earth, burning debris races outward past the line of defender warships, the light slowly fades to reveal the planet; the camera drifts slowly forward, then shakes as the wave passes.",
     "A colossal deep boom rolling in, a roaring shockwave washing over, then a low rumble fading."),
]


def p_ref(desc, son):
    """Format « référence complète » (guide ref) : l'image clé est la première image du plan, sur un point de contrôle ref2va."""
    return ("subject_definitions:\n<Picture 1> is the first frame of [Shot 1], establishing the composition, the ships, the planet and the lighting.\n\n"
            "summary:\n[reference generation] A single continuous shot of a space battle above the Earth that begins from <Picture 1>.\n\n"
            "retention_analysis:\n<Picture 1> ([Shot 1] first frame): fully_preserved - the composition, ship designs, planet and lighting of the first frame are kept.\n\n"
            f"detailed_description:\n{LOOK}\n[Shot 1] The shot begins from <Picture 1>. {desc} No text, no logos.\n\n"
            f"overall_soundscape:\n{son}\n\nnon_diegetic_music:\nN/A")


def specs(seulement=None):
    out = []
    for nom, cle, moteur, desc, son in PLANS:
        if seulement and nom not in seulement:
            continue
        prompt = p(desc, son)
        s = {"type": "h3", "nom": nom, "largeur": 1344, "hauteur": 768, "images": 124, "graine": 5000 + len(out), "sortie": SORTIE, **moteur}
        if cle:
            s["image"] = f"{CLES}/{cle}.png"
            prompt = p_ref(desc, son) if moteur.get("ref") else I2V + prompt
        s["prompt"] = prompt
        out.append(s)
    return out


if __name__ == "__main__":
    print(json.dumps(specs(set(sys.argv[1:]) or None), ensure_ascii=False, indent=1))
