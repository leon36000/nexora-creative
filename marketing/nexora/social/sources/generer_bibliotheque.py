"""Bibliothèque de plans générés (Qwen-Image-2.1) pour le social et la publicité. Reprend là où il s'est arrêté.
  python3 generer_bibliotheque.py [nom ...]     (sans argument : tous les plans manquants, 2 en parallèle)
Les plans ne contiennent ni texte ni logo ni visage : tout cela se pose en code par-dessus."""
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "outils"))
from generer import image

SORTIE = Path(__file__).resolve().parent / "generees"
FIN = (" No text, no letters, no numbers, no logo, no watermark, no people, no robot. Cinematic still, fine film grain, "
       "shallow depth of field, large areas of deep black, palette of near-black #0A0A0E, cold midnight blue and a single "
       "signal orange (#FF5A1F) with warm ember glow. Restrained, premium, quiet, one focal point.")

PLANS = {
 # --- 16:9 ---
 "aurore-foret": ("16:9", "Wide low-angle view of a snow-covered boreal forest at night, a huge ribbon aurora in glowing orange and ember red rolling across a deep midnight-blue sky, cold blue snow in the foreground catching orange light, a few stars, mist between the spruce trees."),
 "aurore-lac": ("16:9", "A perfectly still frozen lake at night under an orange aurora, the aurora mirrored in the dark ice, a thin line of black spruce on the far shore, vast empty dark sky, minimalist composition with a low horizon."),
 "fleuve-aube": ("16:9", "The Saint Lawrence river at dawn seen from a high bank, slow mist over the water, the first orange light of the sun on the far shore, deep blue shadows, a lone cargo ship as a tiny dark silhouette, cinematic and calm."),
 "ville-crepuscule": ("16:9", "Old Québec City at dusk seen from across the frozen Saint Lawrence river: stone ramparts, steep snow-covered roofs with copper dormers, a grand green-copper-roofed château-style hotel high on the cliff, church steeples, every window a small glowing orange square, blue hour sky with a thin band of orange at the horizon, reflections on the dark water, quiet and monumental. No modern skyscrapers."),
 "atelier": ("16:9", "Interior of a craftsman's workshop lit only by a warm hanging lantern, wooden workbench with tools, sparks of orange light drifting up like embers and forming small glowing square objects mid-air, deep shadows, rim light, dust particles."),
 "phare": ("16:9", "A lighthouse on a black rocky cape in a storm at night, a single orange beam cutting through rain and fog across a dark turbulent sea, tiny waves of foam catching the light, dramatic but calm, the lighthouse is small in the frame."),
 "salle-calcul": ("16:9", "A vast underground machine hall, long symmetrical rows of black server cabinets receding into the distance, thin warm amber light strips on the floor and cabinets, silent, slight haze, a perspective vanishing point, concrete and dark metal."),
 "pont-lumiere": ("16:9", "A bridge made of pure orange light spanning a dark gorge between two snowy cliffs at night, particles of light drifting off it like embers, a deep blue misty valley below, cinematic wide shot, symmetrical."),
 "carres-flottants": ("16:9", "Hundreds of small glowing square tiles in shades from pale gold to deep orange and crimson floating in a black void, slowly aligning into a loose grid toward the right of the frame, sharp squares, tiny ones in the distance blurred by shallow depth of field."),
 "sablier-braises": ("16:9", "A glass hourglass on a dark surface where glowing orange embers fall as tiny glowing square pixels instead of sand, dark moody studio lighting, rim light, macro, shallow depth of field, black background."),
 "neige-pixels": ("16:9", "A dark spruce forest at night in falling snow, the snowflakes are tiny glowing square pixels, some of them orange, drifting slowly, blue-black atmosphere, a faint orange glow behind the trees."),
 "mosaique-braise": ("16:9", "Macro abstract: a field of square glossy tiles, colour ramp from pale gold through orange to crimson, dissolving into scattered single pixels toward the left side, the right side fading into pure black, crisp graphic squares, subtle depth of field."),
 "mosaique-nuit": ("16:9", "Macro abstract: a field of square tiles in cold midnight blue and slate, almost black, with a handful of tiles glowing signal orange like embers, dissolving into scattered pixels toward the right, elegant and quiet."),
 "cabane-neige": ("16:9", "A small wooden cabin alone in deep snow at night in a Québec winter landscape, a single warm orange glowing window, spruce trees, blue shadows, starry sky with a faint aurora, wisps of chimney smoke, wide and peaceful."),
 "rue-pluie": ("16:9", "An empty city street at night after rain, wet asphalt reflecting orange window lights as vertical streaks, deep blue shadows, a distant glowing orange crossing signal, anamorphic bokeh, cinematic and quiet."),
 "erabliere-crepuscule": ("16:9", "A maple forest in autumn at dusk, leaves in ember orange and deep red, a few leaves in the air glowing like embers, thin mist, cold blue light in the background, shallow depth of field."),
 "bureau-nuit": ("16:9", "A quiet desk by a tall window at night, a warm orange desk lamp lighting a wooden desk with a closed notebook and a cup, the window shows a blue city with orange lit windows, nobody present, cinematic."),
 "montagne-aube": ("16:9", "Snowy mountain ridge at the blue hour before dawn, a thin line of orange light on the horizon, cold blue snow, fine clouds in the valleys, vast and silent, minimalist."),
 # --- 9:16 ---
 "aurore-vertical": ("9:16", "Tall vertical view: black spruce forest silhouette at the bottom, a huge orange aurora curtain rising up through the deep midnight-blue sky, stars at the top, snow in the foreground, the upper third dark and empty."),
 "phare-vertical": ("9:16", "Tall vertical: a lighthouse on a black cliff at the lower third, one orange beam sweeping across a stormy dark blue sky, waves below, huge empty dark sky at the top."),
 "ville-vertical": ("9:16", "Tall vertical view of a narrow snowy cobblestone street in Old Québec at dusk, stone buildings with steep roofs and dormer windows, every window a small glowing orange square forming a grid, a church steeple at the end of the street, blue hour, the top dissolves into darkness. No modern skyscrapers."),
 "foret-vertical": ("9:16", "Tall vertical: a snowy boreal forest path at night, tall spruce trees, falling snow lit by a faint orange glow at the end of the path, deep blue shadows, quiet."),
 "braises-montantes": ("9:16", "Tall vertical: hundreds of small glowing square embers in orange and gold rising from the bottom of a black frame, becoming sparser and smaller toward the top, shallow depth of field, a warm glow at the bottom."),
 "fleuve-vertical": ("9:16", "Tall vertical: the Saint Lawrence river at dawn, mist, an orange sun low at the bottom near the far shore, blue water reflecting, huge soft gradient sky going to dark blue at the top, minimal."),
 "mosaique-vertical": ("9:16", "Tall vertical abstract: square glossy tiles from crimson at the bottom through orange to pale gold, dissolving into scattered pixels toward the top, the top half becoming pure black, graphic and clean."),
 "pont-vertical": ("9:16", "Tall vertical: a luminous orange bridge of light crossing a misty blue gorge at night between two dark cliffs, particles floating, huge dark sky above."),
 # --- 1:1 ---
 "carres-assemblage": ("1:1", "Centered macro: glowing orange and gold square tiles floating and slowly gathering toward the center in a loose cluster, black void, tiny blurred squares in the foreground and background, calm, sharp focal cluster."),
 "atelier-carre": ("1:1", "Close view of an artisan's workbench lit by a single orange lantern, glowing small square objects of light resting on the wood like crafted gems, deep shadows, shallow depth of field."),
 "aurore-carre": ("1:1", "Square composition: orange aurora over a dark snowy forest, lower third black treeline, aurora in the middle, deep blue sky, minimal and balanced."),
 "main-pixel": ("1:1", "Close-up of a human hand from the side, only fingers visible, gently placing a single glowing orange square pixel of light onto a dark surface, small orange glow lighting the skin, black background, no face."),
}

def un(nom):
    f, p = PLANS[nom]
    sortie = SORTIE / f"{nom}.png"
    if sortie.exists():
        return nom, "déjà là"
    for essai in (1, 2):
        try:
            image(p + FIN, str(sortie), f)
            return nom, "ok"
        except Exception as e:
            err = str(e)[:120]
    return nom, "ÉCHEC " + err

# ordre de priorité (le GPU est partagé : environ 2 plans par minute au mieux, souvent moins)
PRIORITE = ["atelier", "phare", "cabane-neige", "salle-calcul", "carres-flottants", "bureau-nuit", "aurore-vertical", "ville-vertical",
            "phare-vertical", "fleuve-vertical", "foret-vertical", "braises-montantes", "montagne-aube", "mosaique-vertical", "pont-lumiere",
            "mosaique-braise", "mosaique-nuit", "rue-pluie", "pont-vertical", "neige-pixels", "sablier-braises", "erabliere-crepuscule",
            "carres-assemblage", "aurore-carre", "atelier-carre", "main-pixel"]

if __name__ == "__main__":
    noms = sys.argv[1:] or [n for n in PRIORITE if n in PLANS] + [n for n in PLANS if n not in PRIORITE]
    with ThreadPoolExecutor(2) as ex:
        for nom, s in ex.map(un, noms):
            print(nom, s, flush=True)
