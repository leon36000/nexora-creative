"""H3 shots for the site redesign (MiniMax H3, RTX 5090). Usage: python3 plans.py <group> [--format 16:9|9:16]
[--moteur max|rapide] [--variantes N] [names...]
Each shot = (seconds, sound, description, soundscape). Prompts follow the official H3 guide (T2VA, three fields).
Files: site-medias-travail/plans/<group>/<name>-<format>-vN.mp4 (skipped if already there)."""
import sys, argparse, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent / "outils"))
from moteurs import video, h3, TRAVAIL

# Recurring style anchors (the "Signal" identity: precise light in the dark).
NUIT = ("deep black shadows, very low-key lighting, cold blue-black palette with fine cyan light accents, "
        "a single small warm orange light as the only warm point, light haze, anamorphic lens, subtle film grain")
SANS = "No people, no text, no letters, no logos, no robots anywhere in the frame."

PLANS = {
  # ---------------- hero loop of the home page (silent) ----------------
  "hero": {
    "allee": (7, False,
      f"[Shot 1] Live-action, cinematic, photorealistic. A perfectly smooth, slow push-in along the central aisle of a vast "
      f"silent data center at night, symmetrical one-point perspective, tall black server racks on both sides receding into "
      f"darkness, thousands of tiny cyan status lights glowing in precise horizontal rows and blinking softly, thin haze "
      f"hanging in the air, a fine horizontal beam of cyan light slowly sweeps across the aisle from left to right, the "
      f"polished dark concrete floor reflects every light, far away at the vanishing point a single warm orange light. "
      f"The camera pushes in with small amplitude at slow speed, steady as a dolly. {NUIT}. {SANS}",
      "Low hum of server fans and air conditioning."),
    "champ": (7, False,
      f"[Shot 1] 3D CG, photorealistic, cinematic. A vast night landscape of rolling hills, a winding river and a distant "
      f"forest made entirely of millions of fine cyan points of light on pure black, like a lidar point cloud, the points "
      f"denser near the ground and fading into the distance under a black sky with faint stars. A thin horizontal line of "
      f"brighter light slowly travels across the landscape, making the points it touches glow a little brighter. The "
      f"camera trucks forward slowly and smoothly at low altitude above the point cloud, with small amplitude at slow "
      f"speed. Elegant, precise, scientific instrument aesthetic, a single tiny warm orange point on the horizon. {SANS}",
      "Soft low wind and a faint electronic shimmer."),
  },

  # ---------------- AI surveillance ----------------
  "surv": {
    "murs": (5, True,
      f"[Shot 1] Live-action, cinematic, photorealistic. A dark modern security monitoring room at night: a huge curved wall "
      f"of dozens of video screens showing grey, grainy security camera views of empty corridors, loading docks, parking lots "
      f"and warehouse aisles, the screens flicker softly and cast a cold blue glow on a long empty desk and an empty office "
      f"chair. The camera pushes in with small amplitude at slow speed toward the wall of screens. {NUIT}. No people, no "
      f"readable text, no letters, no logos.",
      "Low electrical hum of many monitors, a soft air-conditioning drone, faint fan noise."),
    "stockage": (5, True,
      f"[Shot 1] Live-action, cinematic, photorealistic macro. A long row of video recorder storage servers in a dark rack, "
      f"hundreds of hard drive bays with tiny cyan activity lights blinking in fast random rhythms, brushed metal drive "
      f"trays with fine ventilation holes, shallow depth of field. The camera trucks right with small amplitude at slow "
      f"speed along the drive bays. {NUIT}. {SANS}",
      "Dense whir of spinning hard drives and the clicking of drive heads, a steady fan hum."),
    "chaise": (5, True,
      f"[Shot 1] Live-action, cinematic, photorealistic. Close shot of an empty black office chair in front of a desk in a "
      f"dark monitoring room at night, a dark jacket hangs on the backrest, a paper cup of coffee sits forgotten on the desk, "
      f"the blue light of many security screens flickers across the empty chair. The camera holds a static shot while the "
      f"screen light keeps changing. Quiet, lonely atmosphere. {NUIT}. {SANS}",
      "Soft monitor hum and distant ventilation, a lonely silence."),
    "entrepot": (5, True,
      f"[Shot 1] Live-action, security camera footage aesthetic but high quality: a static high-angle wide view from a "
      f"ceiling camera over a large warehouse at night, long aisles of tall shelving with pallets and boxes, cold dim light. "
      f"A person in a dark hooded jacket walks slowly from the left side toward the center along the main aisle, looking "
      f"around nervously, then stops near a shelf. The camera holds a perfectly static shot, no camera movement at all. "
      f"Slightly desaturated night footage, sharp, wide-angle lens. No text, no timestamp, no logos, no letters.",
      "Quiet warehouse room tone, faint footsteps on concrete, a distant hum of lights."),
    "stationnement": (5, True,
      f"[Shot 1] Live-action, security camera footage aesthetic but high quality: a static high wide view from a pole camera "
      f"over an outdoor parking lot at night, wet asphalt reflecting cold LED lights, a few parked cars. A person in a dark "
      f"hoodie walks between the parked cars from the right, glances around, and pulls on the door handle of a dark sedan. "
      f"The camera holds a perfectly static shot, no camera movement at all. Night footage, sharp, wide-angle lens. No text, "
      f"no timestamp, no logos, no letters, no license plates readable.",
      "Light rain on asphalt, distant traffic, quick footsteps, the click of a car door handle."),
    "alerte": (5, True,
      f"[Shot 1] Live-action, cinematic, photorealistic macro. At night on a dark wooden desk in a security booth, a "
      f"smartphone lies face down next to a flashlight and a ring of keys; it vibrates and a strong red glow spills out from "
      f"under its edges onto the wood grain, pulsing like an alarm, the reflections of a distant street light on the window "
      f"behind are blurred into bokeh. The camera pushes in with small amplitude at slow speed toward the phone. {NUIT}. "
      f"No people, no hands, no screen visible, no text, no letters, no logos.",
      "A phone vibrates sharply against a wooden desk, keys rattle slightly, quiet night room tone."),
    "intervention": (5, True,
      f"[Shot 1] Live-action, cinematic, real actors. Tracking shot from behind a security guard in a plain dark uniform "
      f"jacket walking quickly down a dark warehouse aisle at night, holding a flashlight whose white beam cuts through light "
      f"haze and sweeps across tall shelves. The camera follows him at walking speed. {NUIT}. No text, no logos, no letters.",
      "Quick footsteps echoing on concrete, the jingle of keys, a faint radio crackle, warehouse room tone."),
    "rapport": (5, True,
      f"[Shot 1] Live-action, cinematic, real actors, photorealistic skin and fabric. Morning in a bright modern office with "
      f"large windows, a woman manager in her forties in a dark blazer sits at a desk and reads attentively on a laptop seen "
      f"from behind (only the back of the laptop is visible), soft daylight and a faint cool glow of the screen on her face, "
      f"she nods slowly and takes a sip of coffee. The camera pushes in with small amplitude at slow speed. Natural light, "
      f"calm. No readable text, no logos.",
      "Quiet office ambience, a soft keyboard tap, a cup set down on the desk."),
  },
  # ---------------- virtual reception ----------------
  "recep": {
    "telephone": (5, True,
      f"[Shot 1] Live-action, cinematic, photorealistic. An empty modern reception desk in an office lobby late at night, "
      f"dark walnut and black stone, a slim desk phone on the counter rings and its small indicator light blinks, large "
      f"windows behind show the blurred lights of a city at night. The camera pushes in with small amplitude at slow speed "
      f"toward the phone. {NUIT}. {SANS}",
      "A desk phone rings repeatedly in a quiet empty lobby, soft room tone, distant city."),
    "onde": (5, True,
      f"[Shot 1] 3D CG, photorealistic, cinematic. In a deep black space, a delicate sound waveform made of hundreds of fine "
      f"luminous cyan light threads appears and starts to oscillate smoothly as if a calm voice were speaking, the threads "
      f"ripple and glow brighter on the peaks, tiny particles drift around them. The camera arcs slowly around the waveform "
      f"with small amplitude. Elegant, precise. {SANS}",
      "A soft airy shimmer and a low resonant hum that pulses with the waveform."),
    "cliente": (5, True,
      f"[Shot 1] Live-action, cinematic, real actors, photorealistic skin and fabric. Evening in a warm modern kitchen, a "
      f"woman in her thirties in a grey sweater holds a smartphone to her ear, listens, then smiles with relief and nods, "
      f"warm practical lights in the background, shallow depth of field, medium close-up. The camera holds a static shot "
      f"with a slight handheld feel. No readable text, no logos.",
      "Quiet kitchen ambience, a soft hum of a fridge, the faint indistinct sound of a calm voice on the phone line."),
    "artisan": (5, True,
      f"[Shot 1] Live-action, cinematic, real actors. Daytime inside a work van parked on a residential street, a plumber in "
      f"his forties wearing a work jacket and gloves is busy sorting tools in the back of the van; on the dashboard his phone "
      f"in a holder lights up and rings; he glances at it, shrugs because his hands are full, and keeps working, relaxed. "
      f"Medium shot, natural light. No readable text, no logos, no letters on the van.",
      "Tools clinking in a metal box, a phone ringing, street ambience outside the van."),
    "texto": (5, True,
      f"[Shot 1] Live-action, cinematic, photorealistic macro. A smartphone lies face up on a dark wooden table at night, its "
      f"screen lights up with a soft cyan glow and it vibrates once, the light spilling on the wood grain, shallow depth of "
      f"field, bokeh of warm lights behind. The camera pushes in with small amplitude at slow speed. The screen shows only "
      f"soft abstract light, no readable text, no letters, no icons, no logos.",
      "A single phone vibration on wood, quiet room tone."),
    "transfert": (5, True,
      f"[Shot 1] Live-action, cinematic, real actors, photorealistic skin and fabric. Daytime in a bright modern office, a "
      f"man in his thirties in a light blue shirt at his desk picks up the desk phone as it rings, listens, smiles and starts "
      f"taking notes on a paper notepad, colleagues blurred in the background. Medium shot, the camera pushes in with small "
      f"amplitude. Natural daylight. No readable text, no logos.",
      "Office ambience, a desk phone rings once and is picked up, a pen writing on paper."),
    "matin": (5, True,
      f"[Shot 1] Live-action, cinematic, real actors, photorealistic. Early morning, a business owner in her fifties with "
      f"short grey hair enters her small sunlit office holding a coffee, sits down, opens a laptop seen from behind (only "
      f"the back of the laptop is visible) and smiles as she reads. Golden morning light through the window. The camera "
      f"holds a static shot. No readable text, no logos.",
      "Morning birds outside, a door closes softly, a laptop opens, a cup set on the desk."),
    "aube": (5, True,
      f"[Shot 1] Live-action, cinematic, photorealistic aerial. Dawn over a northern city beside a wide river, the city lights "
      f"still on under a deep blue sky, a thin line of warm sunlight appearing on the horizon, light mist on the water. The "
      f"camera trucks forward slowly at high altitude, with small amplitude at slow speed. {SANS}",
      "High-altitude wind, a distant city waking up."),
  },
  # ---------------- AI infrastructure ----------------
  "infra": {
    "mousse": (5, True,
      f"[Shot 1] Live-action, cinematic, extreme macro product shot. The porous open-cell surface of a champagne gold metal "
      f"foam panel fills the frame, like a metallic sponge with thousands of tiny cells; a narrow blade of white light with a "
      f"cyan edge slowly sweeps across the surface at a grazing angle, revealing the depth of the cells. The camera trucks "
      f"left with small amplitude at slow speed. Pure black background around. {SANS}",
      "A low airy hum, a soft electronic shimmer as the light passes."),
    "spark": (5, True,
      f"[Shot 1] Live-action, cinematic, premium product film. The compact champagne gold desktop AI computer shown in "
      f"<Picture 1> stays on the dark stone desk, preserving its exact shape, proportions, materials and the metal foam "
      f"front. The camera arcs slowly around it to the right with small amplitude at slow speed, while a thin cyan rim light "
      f"travels along its edges and the reflections on the gold aluminium move. Dark studio, grazing light. No text, no "
      f"logos, no letters.",
      "A very soft fan whisper and a low studio ambience."),
    "station": (5, True,
      f"[Shot 1] Live-action, cinematic, premium product film. The tall workstation tower shown in <Picture 1> stays in "
      f"place, preserving its exact shape, black chassis and gold metal foam front panel. The camera pushes in with small "
      f"amplitude at slow speed while a grazing light slowly rises along the metal foam front and the thin cyan light line "
      f"glows. Dark studio. No text, no logos, no letters.",
      "A soft deep fan hum, a quiet studio room tone."),
    "racks": (5, True,
      f"[Shot 1] Live-action, cinematic, photorealistic. Inside a modern data center at night, a long row of tall black "
      f"server racks with glass doors, full of dense servers with honeycomb front grilles and rows of tiny cyan status lights "
      f"blinking, neat cabling, light haze. The camera tracks smoothly along the row at slow speed, grazing light skimming "
      f"the metal fronts, polished dark floor reflections, one single warm orange status light. {NUIT}. {SANS}",
      "Powerful steady server fan roar and air conditioning, faint electrical hum."),
    "installation": (5, True,
      f"[Shot 1] Live-action, cinematic, real actors. In a dim data center, a technician in a dark long-sleeve shirt slides "
      f"a server into an open rack on its rails with both hands, then plugs in two network cables that light up with tiny "
      f"cyan lights. Medium close-up, shallow depth of field, grazing light, natural hands with five fingers. The camera "
      f"pushes in with small amplitude. {NUIT}. No text, no logos, no letters.",
      "Metal rails sliding, a firm click as the server locks in, cables snapping into ports, fan noise."),
    "fibres": (5, True,
      f"[Shot 1] Live-action, cinematic macro. Dozens of fiber optic cables plugged into a network switch in a dark rack, "
      f"pulses of cyan light travel through the translucent cables and tiny port lights blink in rhythm, shallow depth of "
      f"field. The camera trucks right with small amplitude at slow speed. {NUIT}. {SANS}",
      "A steady electronic hum and the faint high whine of network equipment."),
    "batiment": (5, True,
      f"[Shot 1] Live-action, cinematic, photorealistic. Exterior of a modern low data center building at night in a snowy "
      f"northern landscape, dark metal and glass facade with a long horizontal strip of cool light, snow falling gently, "
      f"boreal forest silhouettes around, blue night, warm light from a few windows. The camera pushes in slowly with small "
      f"amplitude at slow speed. No text, no signs, no logos, no letters, no people.",
      "Soft winter wind, falling snow hush, a distant low hum of cooling units."),
    "salle": (5, True,
      f"[Shot 1] Live-action, cinematic, photorealistic. A vast data center hall at night seen from a high catwalk, dozens of "
      f"rows of black server racks with thousands of tiny cyan lights stretching into the distance, light haze. The camera "
      f"pulls out and pedestals up with large amplitude at slow speed, revealing the immense scale. {NUIT}. {SANS}",
      "A vast powerful hum of thousands of fans, a deep low resonance."),
  },
  # ---------------- Creative ----------------
  "crea": {
    "phare": (5, True,
      "[Shot 1] Live-action, cinematic, photorealistic, epic. A lone lighthouse on a rocky cape at night during a violent "
      "storm, gigantic waves crash against the rocks and explode into white spray, the lighthouse beam sweeps through rain "
      "and low clouds, lightning flashes in the distance. The camera pushes in slowly with small amplitude. No people, no "
      "text, no logos.",
      "Roaring wind, huge waves crashing on rocks, heavy rain, distant thunder."),
    "baleine": (5, True,
      "[Shot 1] Photorealistic cinematic CG, epic and surreal. At night, a gigantic humpback whale swims slowly through the "
      "air above a sleeping city of glowing windows, its huge body lit from below by the city lights, a few clouds drift "
      "around it, its long pectoral fins move gracefully. The camera tilts up with small amplitude at slow speed. No text, "
      "no logos, no people.",
      "A deep resonant whale song echoing over the city, soft wind, distant city hum."),
    "cafe": (5, True,
      "[Shot 1] Live-action, cinematic commercial, extreme slow motion macro. Hot black coffee pours into a matte black cup, "
      "a crown of droplets splashes upward and hangs in the air, warm golden backlight makes the droplets glow, steam "
      "curls, dark background. The camera pushes in with small amplitude at slow speed. No text, no logos.",
      "A slowed-down liquid splash, a deep low whoosh, soft steam hiss."),
    "renard": (5, True,
      "[Shot 1] Live-action, cinematic wildlife film, photorealistic. An arctic fox with thick white fur walks through fresh "
      "snow in a boreal forest at dawn, pink and gold light through the snowy spruce trees, breath vapor, it stops and looks "
      "toward the camera. Long telephoto lens, shallow depth of field, the camera tracks it slowly. No text, no logos, no people.",
      "Soft crunch of paws in snow, a light wind in the trees, a distant bird."),
    "danse": (5, True,
      "[Shot 1] Live-action, cinematic, real actors, extreme slow motion. A contemporary dancer in a flowing dark dress spins "
      "in a black studio and throws a cloud of fine cyan and orange powder that explodes around her in slow motion, rim light "
      "outlines the powder and fabric, her face in soft shadow. The camera arcs around her with small amplitude. No text, no logos.",
      "A deep slowed-down whoosh of fabric and powder, a soft resonant boom."),
    "studio": (5, True,
      f"[Shot 1] Live-action, cinematic, real actors, photorealistic. A video creator in her twenties sits in a dark studio "
      f"at night in front of a large monitor, the screen's light changes colors on her face as different cinematic images "
      f"play (we only see the light, the screen faces away from the camera), she leans back and smiles, amazed. Medium "
      f"close-up, the camera pushes in with small amplitude at slow speed. {NUIT}. No readable text, no logos.",
      "Quiet studio room tone, a soft click of a mouse, a faint music leak from headphones."),
  },
  # ---------------- WorkStudio (agents and workflows) ----------------
  "work": {
    "graphe": (5, True,
      f"[Shot 1] 3D CG, photorealistic, cinematic. In an infinite dark space above a fine glowing 1-pixel grid floor, dozens "
      f"of small precise glass nodes are connected by thin glowing cyan light lines forming an elegant branching graph in "
      f"perspective; small bright pulses of light travel along the lines from node to node, nodes light up one after another "
      f"as tasks complete, one node glows warm orange. The camera pushes in and arcs slowly with small amplitude. {SANS}",
      "Soft precise electronic ticks as each node lights up, a low airy pad."),
    "documents": (5, True,
      f"[Shot 1] 3D CG, photorealistic, cinematic. In a dark space, hundreds of thin translucent sheets of paper made of "
      f"light float in a chaotic cloud, then smoothly fly and align themselves into neat precise stacks and rows, each sheet "
      f"catching a cyan edge light, the pages are blank with no writing. The camera pulls out slowly. {SANS}",
      "Soft fluttering paper sounds and gentle whooshes as the sheets settle."),
    "equipe": (5, True,
      "[Shot 1] Live-action, cinematic, real actors, photorealistic skin and fabric. Daytime in a bright modern open-space "
      "office with plants and large windows, a small team of four colleagues of different ages stands around a high table, "
      "relaxed, one of them makes a decision gesture and the others nod and smile. Medium-wide shot, the camera trucks right "
      "with small amplitude at slow speed. Natural light, shallow depth of field. No readable text, no logos.",
      "Lively office ambience, soft indistinct voices and light laughter."),
    "flux": (5, True,
      f"[Shot 1] 3D CG, photorealistic, cinematic. A network of clear glass tubes branching and merging in a dark space, "
      f"streams of tiny cyan light particles flow through them, split at the junctions, and converge into one bright stream, "
      f"reflections on the glass. The camera tracks along the main tube at slow speed. {SANS}",
      "A smooth flowing hiss and soft liquid-like electronic sounds."),
    "nuit": (5, True,
      f"[Shot 1] Live-action, cinematic, photorealistic. An empty modern office at night, chairs pushed in, the city lights "
      f"through the windows, the monitors on several desks are on and their soft cool light changes subtly as work continues "
      f"without anyone there (the screens face away from the camera). The camera pushes in with small amplitude at slow "
      f"speed. {NUIT}. {SANS}",
      "Quiet night office ambience, a soft hum of computers, distant city."),
  },
  # ---------------- Code (hosted coding agent) ----------------
  "code": {
    "nuit": (5, True,
      f"[Shot 1] Live-action, cinematic, real actors, photorealistic. At night a software developer in his thirties sits in "
      f"a dark room, his face lit by the cool cyan glow of a monitor seen from behind (the screen faces away), rain streaks on "
      f"the window behind him, he leans back with a slight smile and crosses his arms while the screen light keeps "
      f"flickering. Medium close-up, the camera pushes in with small amplitude at slow speed. {NUIT}. No readable text, no logos.",
      "Rain on the window, a soft hum of a computer, a faint keyboard rhythm."),
    "lignes": (5, True,
      f"[Shot 1] 3D CG, photorealistic, cinematic. In a deep black space, thousands of thin horizontal lines of cyan and "
      f"white light of different lengths stream forward in perspective like abstract lines of code without any characters, "
      f"assembling into a precise three-dimensional wireframe structure. The camera flies forward slowly through the lines. {SANS}",
      "A fast soft data shimmer and a low rising hum."),
    "clavier": (5, True,
      f"[Shot 1] Live-action, cinematic, macro. A dark mechanical keyboard with a subtle cool backlight on a desk at night, "
      f"two hands type quickly and precisely, natural hands with five fingers, shallow depth of field, the glow of a monitor "
      f"reflects on the keys. The camera trucks right with small amplitude at slow speed. {NUIT}. No readable text, no "
      f"letters, no logos.",
      "Crisp mechanical keyboard clicks, quiet room tone."),
    "architecture": (5, True,
      f"[Shot 1] 3D CG, photorealistic, cinematic. In a dark space above a 1-pixel glowing grid, a city-like architecture of "
      f"precise wireframe blocks made of thin cyan light lines builds itself block after block, rising from the grid, each "
      f"new block snapping into place with a flash. The camera arcs slowly around it with small amplitude. {SANS}",
      "Precise soft clicks and snaps as blocks lock into place, a low electronic hum."),
    "serveur": (5, True,
      f"[Shot 1] Live-action, cinematic, photorealistic. A small private server room in an office, one black server rack "
      f"with cyan status lights behind a glass door, a desk with a closed laptop nearby, quiet and secure. The camera pushes "
      f"in with small amplitude at slow speed toward the rack. {NUIT}. {SANS}",
      "Steady server fan hum, a quiet room tone."),
    "equipe": (5, True,
      "[Shot 1] Live-action, cinematic, real actors, photorealistic skin and fabric. Daytime in a bright modern office, two "
      "developers, a woman and a man in their thirties, stand in front of a large monitor seen from behind (the screen faces "
      "away), discussing, the woman points at the screen and they both smile, satisfied. Medium shot, the camera trucks left "
      "with small amplitude. Natural light. No readable text, no logos.",
      "Office ambience, soft indistinct conversation, a short laugh."),
  },
}

# I2VA shots: first frame = the Qwen still kept (product consistent with the site photos). (image, horizontal framing 0-1)
DEPART = {
  ("infra", "spark"): {"16:9": ("infra-dgx-spark-v5.png", 0.5), "9:16": ("infra-dgx-spark-9x16-v1.png", 0.5)},
  ("infra", "station"): {"16:9": ("infra-dgx-station-v1.png", 0.46), "9:16": ("infra-dgx-station-9x16-v1.png", 0.5)},
}


def image_depart(groupe, nom, fmt):
    from PIL import Image
    src, cx = DEPART[(groupe, nom)][fmt]
    w, h = {"16:9": (1344, 768), "9:16": (768, 1344)}[fmt]
    im = Image.open(TRAVAIL / "images" / src).convert("RGB")
    k = max(w / im.width, h / im.height)
    im = im.resize((round(im.width * k), round(im.height * k)), Image.LANCZOS)
    x = round((im.width - w) * cx); y = (im.height - h) // 2
    out = TRAVAIL / "images" / f"depart-{nom}-{fmt.replace(':', 'x')}.png"
    im.crop((x, y, x + w, y + h)).save(out)
    return out


if __name__ == "__main__":
    a = argparse.ArgumentParser()
    a.add_argument("groupe"); a.add_argument("noms", nargs="*")
    a.add_argument("--format", default="16:9"); a.add_argument("--moteur", default="max")
    a.add_argument("--variantes", type=int, default=1); a.add_argument("--depart", type=int, default=1)
    o = a.parse_args()
    g = PLANS[o.groupe]
    for nom in (o.noms or list(g)):
        sec, son, desc, amb = g[nom]
        fmt = o.format.replace(":", "x")
        for v in range(o.depart, o.depart + o.variantes):
            f = TRAVAIL / "plans" / o.groupe / f"{nom}-{fmt}-v{v}.mp4"
            if f.exists():
                continue
            if o.format == "9:16":
                desc = desc.replace("[Shot 1]", "[Shot 1] Vertical 9:16 framing, the main subject centered.", 1)
            try:
                dep = image_depart(o.groupe, nom, o.format) if (o.groupe, nom) in DEPART else None
                _, tid, s = video(h3(desc, amb), f, o.format, o.moteur, sec, son, seed=4242 + 97 * v, depart=dep)
                print(f"ok {f.name} prise {tid} {s:.0f}s", flush=True)
            except Exception as e:
                print(f"ECHEC {f.name} {e}", flush=True)
            time.sleep(20)  # leaves an empty window in the engine queue (another agent maintains pc1 between jobs)
