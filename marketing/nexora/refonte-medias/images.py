"""Site images, "Signal" identity (Qwen-Image-2.1, GB10). Usage: python3 images.py [name ...] [--variantes N]
Skips the files that already exist in the work folder (images/<name>-vN.png). The prompts are the ones in the manifest."""
import json, sys, argparse
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent / "outils"))
from moteurs import image, TRAVAIL

# Shared style: the "Signal" world (precise light in the dark, ion cyan, a single warm point).
STYLE = ("Photorealistic cinematic photograph, shot on a large-format digital cinema camera, 35mm anamorphic lens, "
         "dark low-key mood but well exposed, details clearly readable in the shadows, grazing light, fine cyan light (#3EC8FF) as the main accent, "
         "cold blue-black palette, subtle film grain, high dynamic range, ultra detailed, sharp focus, no text anywhere, "
         "no logo, no lettering, no people.")
STUDIO = ("Premium product photography in a dark studio, seamless deep black-blue backdrop, single soft key light at a "
          "grazing angle from the left, thin cyan rim light along the edges, subtle reflection on a dark glossy floor, "
          "85mm lens, f/8, extremely sharp, physically accurate metal and glass, 8k detail, no text, no logo, no lettering, "
          "no brand marks, no labels.")

IMAGES = {
    # --- hero (home page)
    "hero-datacenter": (2560, 1440, "A vast silent data center at night seen from the middle of a long aisle, symmetrical "
        "one-point perspective, tall black server racks on both sides receding into darkness, thousands of tiny cyan status "
        "lights forming precise horizontal lines, a single thin horizontal beam of cyan light sweeping across the aisle at "
        "waist height, light haze in the air catching the beam, polished dark concrete floor reflecting the lights, far at "
        "the vanishing point one single small warm orange light. " + STYLE),
    "hero-champ": (2560, 1440, "Scientific visualization of a lidar scan: a wide mountain valley with a river, "
        "rendered as a sparse 3D point cloud of discrete, separated, crisp glowing cyan points on pure black, every point "
        "clearly distinct like stars, fine topographic contour lines made of points follow the slopes, the cloud is bright "
        "in the foreground and dissolves into darkness toward distant peaks, one thin perfectly straight horizontal scan "
        "line of brighter cyan light crosses the valley, wide cinematic view from a low drone height, black sky, one single "
        "tiny warm orange point in the valley. High contrast, elegant, precise, no text, no logo, no people, no trees "
        "texture, no grass."),
    "hero-ville": (2560, 1440, "Aerial night view from very high altitude over a large northern city beside a wide river, "
        "the city a dark carpet of tiny cold white and pale cyan lights, a single perfectly straight thin line of cyan light "
        "sweeping horizontally across the whole city like a scanner, light mist over the river, a few low clouds catching "
        "the city glow, gentle curvature of the horizon, one single warm orange light near the center. " + STYLE),
    # --- infrastructure (product shots)
    "infra-dgx-spark": (2560, 1440, "A compact mini PC style desktop AI computer lying flat on a dark stone desk: "
        "square footprint, low profile, the box is three times wider than it is tall (a squat square block, height one "
        "third of the width, like two stacked hardcover books), the large flat top is smooth champagne gold anodized "
        "aluminium, the sides are the same gold metal with softly rounded corners, the front face is a full-height panel "
        "of porous open-cell gold metal foam, small rubber feet, three-quarter front view from 35 degrees above so the "
        "top surface and the front face are both visible, the device occupies the center third of the frame. "+ STUDIO),
    "infra-dgx-station": (2560, 1440, "A tall professional AI workstation tower, black chassis with a full-height front "
        "panel made of porous open-cell gold metal foam (sponge-like champagne gold metal texture), clean straight edges, "
        "a thin vertical line of cyan light at the side, standing alone on a dark floor, three-quarter front view, the "
        "tower fills two thirds of the frame height. " + STUDIO),
    "infra-racks": (2560, 1440, "Inside a modern data center, a row of tall black server racks with open glass doors, "
        "each rack full of dense 1U and 2U servers with fine honeycomb front grilles and rows of tiny cyan status lights, "
        "neat cable management, three-quarter view along the row, the server fronts clearly visible and well exposed, lit "
        "by soft cool overhead light and a grazing key light that makes the metal grilles sparkle, polished dark floor with "
        "reflections, light haze in the background, one single warm orange status light on one server. Photorealistic "
        "architectural photography, 24mm lens, sharp, rich detail, dark blue-black palette with cyan accents, no text, no "
        "logo, no labels, no people."),
    # --- virtual reception
    "reception-accueil": (2560, 1440, "A sober modern reception desk in an empty office lobby at night, dark walnut and "
        "black stone, a single slim desk phone and a lightweight headset resting on the counter, large windows behind "
        "showing a blurred night city, a thin horizontal line of cyan light running along the front of the desk, a faint "
        "floating sound waveform made of fine cyan light lines hovering above the counter. " + STYLE),
    "reception-onde": (2560, 1440, "Macro photograph of a premium black wireless headset with a slim boom microphone lying "
        "on dark brushed metal, beside it a delicate sound waveform made of fine luminous cyan light threads floating in "
        "the air, shallow depth of field, bokeh of tiny cyan lights in the background, one tiny warm orange indicator "
        "light on the headset. " + STYLE),
    # --- AI surveillance
    "surveillance-entrepot": (2560, 1440, "High-angle view from a ceiling security camera over a large empty warehouse at "
        "night, tall shelving aisles with pallets, cold low light, faint blue tint, a single forklift parked, wide angle "
        "slightly distorted like a real CCTV camera, clean and sharp, deep shadows, nobody in the scene. " + STYLE),
    "surveillance-stationnement": (2560, 1440, "An empty outdoor parking lot at night seen from a high pole camera, wet "
        "asphalt reflecting sodium and cold LED lights, painted lines, a few parked cars, a fence and dark trees at the "
        "edge, light rain mist, wide angle security camera perspective, cinematic, nobody in the scene. " + STYLE),
    "surveillance-salle": (2560, 1440, "A dark modern monitoring room at night, a long curved desk facing a large wall of "
        "many video screens showing grey security camera views of corridors, parking lots and warehouses (abstract, no "
        "text on the screens), the screens give a cold blue glow, an empty ergonomic chair, one single small red alert "
        "light on the desk, clean architecture, wide shot. " + STYLE),
    # --- Creative
    "creative-atelier": (2560, 1440, "A dark creative studio at night, a large curved monitor on a black desk showing a "
        "breathtaking cinematic image of a misty boreal forest at dawn, around the monitor delicate sheets of light float "
        "in the air like projected film frames, color grading control surface with knobs, a single warm lamp, cyan "
        "reflections on the desk. " + STYLE),
    "creative-lumiere": (2560, 1440, "Abstract cinematic image: a beam of white light passes through a glass prism in the "
        "dark and opens into a fan of thin rays that turn into floating translucent film frames, each frame showing a "
        "different tiny landscape (ocean, forest, city at night), deep black background, cyan and one warm orange ray, "
        "fine dust in the light. " + STYLE),
    # --- WorkStudio (agents and workflows)
    "workstudio-flux": (2560, 1440, "Abstract visualization of an automated workflow: in a dark infinite space, precise "
        "glass nodes connected by thin glowing cyan light lines form an elegant branching graph in perspective, small "
        "pulses of light travel along the lines from node to node, one node glows warm orange, 1 pixel grid on the floor "
        "fading into darkness. " + STYLE),
    # --- Code
    "code-poste": (2560, 1440, "A minimalist developer desk at night, a large dark monitor showing abstract blurred lines "
        "of colored code (unreadable, out of focus), a mechanical keyboard with a soft backlight, a terminal glow in cyan, "
        "a cup of coffee, rain on the window behind, cinematic shallow depth of field, the screen content deliberately "
        "blurred so nothing can be read. " + STYLE),
    # --- method (consultation, installation, operation)
    "methode-installation": (2560, 1440, "Close-up of hands of a technician wearing a dark long-sleeve shirt sliding a "
        "server into a rack in a dimly lit data center, the server front with honeycomb grille and tiny cyan lights, "
        "grazing light, careful and precise gesture, shallow depth of field, natural hands with five fingers. " + STYLE),
    "methode-consultation": (2560, 1440, "A calm meeting table at dusk in a modern office with large windows, two laptops "
        "closed, a notebook and a pen, a thin architectural model, soft cyan reflections on the glass table, city lights "
        "beginning to appear outside, nobody in the scene, quiet and serious atmosphere. " + STYLE),
    # --- sovereignty and security
    "souverainete-serveur": (2560, 1440, "A secure server room inside a building in a snowy northern landscape at night, "
        "seen through a large window from outside: warm interior with black racks and cyan lights, snow falling softly in "
        "front of the glass, boreal forest silhouettes around, blue night, a sense of shelter and protection. " + STYLE),
    "souverainete-coffre": (2560, 1440, "Abstract image of protection: a thick block of dark glass in the dark, inside it "
        "a small cluster of fine cyan light points like a data constellation, the glass edges catching a grazing white "
        "light, precise engineering, reflections on a black floor. " + STYLE),
}

# Native vertical versions of the product shots that a crop would cut (the device fills the 16:9 frame).
for _cle, (_w, _h) in {"infra-dgx-spark-4x5": (1152, 1440), "infra-dgx-spark-9x16": (1088, 1920)}.items():
    _p = IMAGES["infra-dgx-spark"][2].replace("the device occupies the center third of the frame", "the device is centered and "
                                               "occupies the middle of the frame with generous dark space above and below")
    IMAGES[_cle] = (_w, _h, _p)
IMAGES["infra-dgx-station-9x16"] = (1088, 1920, IMAGES["infra-dgx-station"][2].replace(
    "the tower fills two thirds of the frame height", "the tower is centered and fills half of the frame height, generous dark space around it"))

if __name__ == "__main__":
    a = argparse.ArgumentParser()
    a.add_argument("noms", nargs="*")
    a.add_argument("--variantes", type=int, default=1)
    a.add_argument("--depart", type=int, default=1)
    o = a.parse_args()
    for nom in (o.noms or list(IMAGES)):
        w, h, p = IMAGES[nom]
        for v in range(o.depart, o.depart + o.variantes):
            f = TRAVAIL / "images" / f"{nom}-v{v}.png"
            if f.exists():
                continue
            try:
                _, tid, s = image(p, f, w, h, seed=1000 * v + 7)
                print(f"ok {f.name} prise {tid} {s:.0f}s", flush=True)
            except Exception as e:
                print(f"ECHEC {f.name} {e}", flush=True)
