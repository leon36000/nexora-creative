"""Équipe Opus 5.5 : fabrique `dossier.json` (prompts, voix, musique, EditPlan long et court, annexe) depuis ce script.
La création est ici, en clair ; le script ne fait que l'écrire au bon format et calculer les images à partir de la grille
musicale. Relancer après la mesure de la musique :  python3 fabriquer.py --bpm 128.3 --phase 0.12 --decalage 0.0
(décalage = secondes de musique sautées pour caler le premier gros coup sur la révélation du siège social).
"""
import argparse
import json
from pathlib import Path

ICI = Path(__file__).resolve().parent
FPS = 24

REEL = ("Cinematic frame from a 2026 Québec television commercial, shot on a large-format digital cinema camera with anamorphic lenses: "
        "natural skin texture, real exposure, rich contrast, shallow depth of field, fine film grain.")
VIRTUEL = ("Cinematic frame from a 2026 science-fiction feature film, large-format digital cinema camera, anamorphic lenses: deep blacks, "
           "ion-blue and warm-white light, volumetric haze, crisp detail, epic scale. Original architecture, no neon grid, no franchise look.")
SANS = "Plain clothing, phones and vehicles with no logo; no text, no letters, no numbers anywhere in the image."
SIGNAL = "a single bright orange pulse of light (the photo travelling as data)"


def P(resume, decor, plan, son, dialogue=None, virtuel=False):
    s = (f"summary:\nA single continuous cinematic shot: {resume}\n\ndetailed_description:\n{VIRTUEL if virtuel else REEL} {decor} {SANS}\n"
         f"[Shot 1] {plan} No text, no logos.\n\n")
    if dialogue:
        s += f"dialogue:\n{dialogue}\n\n"
    return s + f"overall_soundscape:\n{son}\n\nnon_diegetic_music:\nN/A"


PERSONNAGES = [
    {"id": "etienne", "nom": "Étienne", "role": "sales representative", "voix": "eleven-thomas",
     "fiche": "Étienne, a 29-year-old Québécois sales representative for a renovation company: short dark-brown hair, short light beard, "
              "friendly open face, plain navy-blue softshell jacket over a plain grey t-shirt, dark work pants, brown leather boots."},
    {"id": "luc", "nom": "Luc", "role": "company owner", "voix": "drama3-adamqc",
     "fiche": "Luc, a 52-year-old Québécois owner of a renovation company: salt-and-pepper short hair, clean-shaven, strong jaw, warm eyes, "
              "plain charcoal quarter-zip sweater over a white collared shirt, dark jeans."},
    {"id": "kevin", "nom": "Kevin", "role": "siding installer",
     "fiche": "Kevin, a 34-year-old Québécois siding installer: athletic build, short blond hair under a plain grey knit beanie, stubble, "
              "plain dark-green work jacket with silver reflective strips, beige canvas work pants, tool belt."},
    {"id": "morin", "nom": "Monsieur Morin", "role": "homeowner", "voix": "eleven-alexandre",
     "fiche": "Monsieur Morin, a 67-year-old Québécois retired homeowner: short white hair, thin metal glasses, kind wrinkled face, "
              "plain beige cardigan over a red and navy plaid flannel shirt, grey trousers."},
    {"id": "comptable", "nom": "the AI accountant", "role": "holographic avatar", "voix": "eleven-amelie",
     "fiche": "A holographic AI accountant avatar: a confident woman in her early forties with short elegant dark hair, realistic human "
              "face, entirely made of translucent ion-blue light with fine horizontal scan lines and floating particles, a tailored "
              "blazer made of light, faint orange rim light, on a plain dark grey background."},
]
LIEUX = [
    {"id": "maison", "nom": "the Morin house",
     "fiche": "A two-storey suburban house in Laval, Québec, at golden hour in October: the front wall is covered with old, faded, "
              "cracked beige vinyl siding with several damaged and missing panels, white trim, a maple tree with red leaves, a paved "
              "driveway, a small front porch with two steps, quiet residential street."},
    {"id": "atelier", "nom": "the renovation company's work shop",
     "fiche": "The exterior of a renovation company's work shop in a Québec industrial park at dawn: a large metal building with an "
              "open garage door, warm light inside, stacks of siding boxes and ladders, a white pickup truck with no logo parked in "
              "front, frost on the asphalt, blue dawn sky."},
    {"id": "hq", "nom": "the virtual headquarters inside the server",
     "fiche": "The interior of a colossal virtual corporate headquarters inside a computer server: a vertical atrium hundreds of metres "
              "tall, ten stacked open floors of glass and warm white light, each floor a busy department with rows of luminous "
              "desks, translucent holographic workers made of ion-blue light, floating holographic sheets of light, a central column "
              "of white light rising through every floor, polished black glass floor reflecting everything, epic clean architecture."},
]

# ------------------------------------------------------------------------------------------------------------------ voix
V = [
    # narration (Frédéric : québécois, énergique ; jamais « smooth » : phrases courtes, frappées sur le temps)
    ("n01", "narrateur", "drama3-frederic", "Une photo.", "Narrateur de publicité québécoise, énergique et punché, voix qui sourit, rythme vif."),
    ("n02", "narrateur", "drama3-frederic", "Et toute une entreprise se met au travail.", "Énergique, l'excitation qui monte, rythme vif, accent québécois."),
    ("n03", "narrateur", "drama3-frederic", "Dedans : dix départements. Une seule équipe.", "Énergique, émerveillé, punché, accent québécois."),
    ("n04", "narrateur", "drama3-frederic", "Elle mesure. Elle chiffre. Elle vérifie… et elle attend votre accord.", "Énergique et précis, frappé sur chaque verbe, un sourire à la fin, accent québécois."),
    ("n05", "narrateur", "drama3-frederic", "Dix départements qui ne dorment jamais. Et c'est vous qui décidez.", "Fier, énergique, accent québécois."),
    ("n06", "narrateur", "drama3-frederic", "Les ressources d'une grande entreprise.", "Puissant, assuré, accent québécois."),
    ("n07", "narrateur", "drama3-frederic", "OPSYS-AI.", "Assuré, chaleureux, prononcé « op-sisse A-I »."),
    # dialogues (synchronisés sur les plans)
    ("e01", "etienne", "eleven-thomas", "Monsieur Morin… votre soumission est prête.", "[proud, friendly, casual]"),
    ("m01", "morin", "eleven-alexandre", "Déjà?!", "[surprised, delighted, older man]"),
    ("l01", "luc", "drama3-adamqc", "Pis, les profits, ça donne quoi?", "Patron québécois décontracté et curieux, naturel, parle vite."),
    ("c01", "comptable", "eleven-amelie",
     "Voici les profits anticipés, mis à jour avec les nouveaux ratios de productivité des employés : leur productivité a augmenté de 7 %.",
     "[confident, precise, upbeat]"),
    ("g01", "gestion", "eleven-marieline", "Voici la cédule des trois prochaines semaines.", "[clear, upbeat, organized]"),
    ("a01", "adjointe", "eleven-jeannemance",
     "Vous avez un rendez-vous avec monsieur Thibault à 14 h, et j'ai déplacé votre rendez-vous de 16 h comme vous me l'avez demandé.",
     "[warm, professional, efficient]"),
    ("e02", "etienne", "eleven-thomas", "Parfait, merci!", "[happy, casual]"),
    ("l02", "luc", "drama3-adamqc", "Bon travail, Kevin.", "Chaleureux, fier, patron québécois."),
]
VITESSE = {"c01": 1.0, "a01": 1.0, "n01": 1.1, "n02": 1.1, "n03": 1.1, "n04": 1.1, "n05": 1.1, "n06": 1.05, "n07": 1.0, "l01": 1.1, "l02": 1.05}

# ----------------------------------------------------------------------------------------------------------------- plans
# (id, séquence, recette, images, refs, parole, prompt, caméra, effets, son, statut)
PL = [
    ("p01", "S1 la photo", 124, ["etienne", "maison"], None,
     P("a sales representative photographs a damaged house wall with his phone.",
       "Late afternoon golden hour on a quiet Québec street.",
       "Extreme close-up over the shoulder of @etienne: his hand raises a black smartphone towards the damaged beige siding of @maison; "
       "the phone screen shows only the live camera image of the cracked siding; his thumb taps, a soft white flash, and a tiny orange "
       "spark of light lifts off the phone. Rack focus from the phone to the house.",
       "Camera shutter click, wind in the maple leaves, distant street ambience."),
     "macro, mise au point qui bascule", "étincelle orange", "déclencheur", "VISION"),
    ("p02", "S1 la photo", 124, ["etienne", "maison"], None,
     P(f"{SIGNAL} shoots from a phone up into the sky.",
       "Golden hour, long shadows, warm sky with scattered clouds.",
       f"Wide low-angle shot: @etienne stands on the driveway in front of @maison holding up his phone; from the phone {SIGNAL} shoots "
       "straight up into the sky like a tracer, the camera tilts up fast following it, the pulse pierces the clouds.",
       "Rising whoosh, deep sub-bass boom, wind."),
     "contre-plongée, panoramique vertical rapide", "traceur orange", "fouet + boum", "métaphore"),
    ("p03", "S2 le signal", 124, [], None,
     P(f"{SIGNAL} reaches a satellite above Québec at dusk.",
       "Above the clouds over Québec at dusk: the curve of the Earth, the St. Lawrence river glinting, city lights starting to glow.",
       f"A sleek communications satellite with golden foil and dark-blue solar panels hangs in orbit; {SIGNAL} streaks up from the clouds "
       "and strikes its dish; the satellite glints and fires the pulse back down towards the earth in a bright arc. Slow orbit camera.",
       "Deep space hum, electric zap, resonant chime."),
     "orbite lente", "arc lumineux", "zap", "métaphore", True),
    ("p04", "S2 le signal", 124, [], None,
     P(f"{SIGNAL} strikes a 5G tower and leaps onto the power lines.",
       "A tall telecommunications tower on a hill above a small Québec town at blue hour, red beacon lights, autumn forest.",
       f"{SIGNAL} descends from the sky and hits the tower's antennas, which flare with light; the pulse races down the steel lattice "
       "and leaps onto the power lines below. Dynamic crane-down camera.",
       "Electric crackle, metallic hum, whoosh."),
     "grue descendante", "arc électrique", "crépitement", "métaphore", True),
    ("p05", "S2 le signal", 124, [], None,
     P(f"{SIGNAL} races along power lines across rural Québec.",
       "A straight country road in rural Québec at dusk, wooden utility poles and power lines stretching to the horizon, autumn fields.",
       f"Low fast tracking shot alongside the poles: {SIGNAL} streaks along the wires at incredible speed leaving a glowing trail, each "
       "pole flashing as it passes, the camera racing with it, motion blur.",
       "Crackling electricity, rhythmic whoosh-by of the poles, wind."),
     "travelling latéral très rapide", "traînée lumineuse", "passages en rafale", "métaphore", True),
    ("p06", "S2 le signal", 124, [], None,
     P(f"{SIGNAL} dives into a server inside a data centre.",
       "A modern data centre: a long corridor of black server racks with blinking blue status lights, cold air haze.",
       f"{SIGNAL} races down the corridor along the cable trays and dives into the front of one server; the camera pushes in fast after "
       "it, through the server's panel into its glowing circuit board, macro, the circuits turn into a landscape of light.",
       "Server fans, rising electronic tone, whoosh into silence."),
     "poussée avant rapide, plongée macro", "plongée dans le circuit", "montée", "métaphore", True),
    ("p07", "S3 le siège social", 243, ["hq"], None,
     P("the camera emerges inside a colossal virtual headquarters made of light.",
       "Inside @hq.",
       f"The camera bursts out of a tunnel of light into @hq; {SIGNAL} flies into the atrium like a comet; floor after floor the building "
       "lights up in a cascade, thousands of translucent ion-blue holographic workers look up and get to work; the camera flies forward "
       "and rises through the immense space.", "Huge reverberant whoosh, choir-like synth swell, a cascade of soft chimes.", virtuel=True),
     "envol avant et montée", "cascade de lumière étage par étage", "grand souffle", "métaphore"),
    ("p08", "S3 M1 réception", 124, ["hq"], None,
     P("a holographic receptionist catches the photo and sends it upstairs.", "The reception floor of @hq, a curved luminous desk.",
       f"A holographic receptionist made of ion-blue light catches {SIGNAL}, now a small glowing photograph, in her open hand; she glances "
       "at it, smiles, and flicks it upward; it flies up the atrium towards the upper floors. Medium shot, slight push-in.",
       "Soft chime, airy whoosh upward.", virtuel=True),
     "plan moyen, léger avancé", "photo lumineuse lancée", "carillon", "VISION"),
    ("p09", "S3 M3 estimation", 124, ["hq", "maison"], None,
     P("holographic estimators measure a 3D hologram of the house wall.", "The estimation floor of @hq.",
       "Five holographic estimators made of ion-blue light stand around a floating life-size hologram of the front wall of @maison; the wall "
       "turns into a precise wireframe, measuring lines and points of light snap onto every panel, window and corner; one estimator opens "
       "his hands and the hologram expands. Slow circular dolly.",
       "Precise digital ticks, soft scanning hum.", virtuel=True),
     "travelling circulaire", "fil de fer, points de mesure", "tics de mesure", "VISION"),
    ("p10", "S3 M3 estimation", 124, ["hq"], None,
     P("a cloud of light particles explores thousands of cost scenarios.", "Deep black background with the bokeh of @hq.",
       "Close-up: thousands of tiny orange and blue particles of light fan out from a single point in the air like a probability cloud, "
       "swirl, then converge into one bright precise line; translucent holographic hands guide them.",
       "Shimmering granular sound converging into one clean tone.", virtuel=True),
     "gros plan", "nuage de probabilités", "granulaire", "RÉEL"),
    ("p11", "S3 M3 soumission", 124, ["hq"], None,
     P("a holographic document assembles in mid-air and seals.", "The atrium of @hq.",
       "Sheets of light fold together in mid-air into a glowing document; lines of light fill it from top to bottom (abstract lines only, "
       "no writing); a ring of eleven small lights around it turns on one by one; then it seals with a bright orange flash. The camera "
       "slowly orbits the document.", "Paper-like swishes of light, eleven ascending ticks, a bright seal impact.", virtuel=True),
     "orbite lente", "document qui s'assemble, 11 voyants", "11 tics + sceau", "RÉEL"),
    ("p12", "S3 approbation", 124, ["luc"], None,
     P("the company owner approves the quote with his thumb.",
       "Luc's office at golden hour, warm light through blinds, wooden desk.",
       "Close-up: @luc looks at his black smartphone, a soft orange glow on his face; he presses his thumb on the screen and a ring of light "
       "pulses around his thumb; he gives a small satisfied nod.", "Quiet office, a soft confirmation tone."),
     "gros plan", "anneau lumineux", "tonalité", "RÉEL"),
    ("p13", "S4 le retour", 124, [], None,
     P(f"{SIGNAL} rushes back from the server to the sky at hyperspeed.",
       "Night and dusk landscapes of Québec blurred by speed.",
       f"Hyperspeed: {SIGNAL} shoots out of the server racks, along the power lines and wooden poles, up a telecommunications tower and "
       "into the sky in a single continuous rush, extreme speed, streaks of light, strong motion blur.",
       "Massive reverse whoosh, Doppler sweep."),
     "hypervitesse", "stries", "fouet inversé", "métaphore", True),
    ("p14", "S4 le retour", 124, ["etienne", "maison"], None,
     P("the orange pulse falls from the sky into the representative's phone.", "The driveway of @maison at golden hour.",
       f"{SIGNAL} falls from the sky like a shooting star into the phone in @etienne's hand; the phone lights up softly; he looks at it and "
       "smiles broadly. Medium shot, slight push-in.", "Falling whoosh, soft impact, phone vibration."),
     "plan moyen", "étoile filante", "chute + vibration", "VISION"),
    ("p15", "S4 monsieur Morin", 124, ["etienne", "morin", "maison"], "e01",
     P("the representative tells the homeowner his quote is ready.", "In front of @maison, golden hour.",
       "Medium two-shot: @etienne turns his phone towards @morin, who stands on his porch; Étienne speaks to him with a proud smile.",
       "Street ambience, leaves.", "@etienne speaks in Québécois French, matching <Audio 1> word for word. Monsieur Morin listens."),
     "deux personnages, plan moyen", "—", "voix", "VISION"),
    ("p16", "S4 monsieur Morin", 124, ["morin", "maison"], "m01",
     P("the delighted homeowner reacts.", "The porch of @maison, golden hour.",
       "Close-up: @morin raises his eyebrows, delighted, says one word, then laughs warmly.", "Street ambience.",
       "@morin speaks in Québécois French, matching <Audio 1> word for word, then laughs."),
     "gros plan", "—", "voix + rire", "illustratif"),
    ("p17", "S5 le chantier", 124, ["atelier", "kevin"], None,
     P("the job file reaches an installer at the work shop at dawn.", "Dawn in front of @atelier.",
       f"{SIGNAL} streaks down from the dawn sky into the phone of @kevin; a holographic job file made of light unfolds in the air in front "
       "of him: a small floating 3D model of the Morin house and stacks of siding boxes; he studies it, breath vapour in the cold.",
       "Cold morning birds, distant highway, soft digital chime."),
     "plan moyen", "dossier holographique", "carillon", "EN PRÉPARATION"),
    ("p18", "S5 M6 matériel", 124, ["atelier", "kevin"], None,
     P("the installer loads siding boxes into the pickup truck.", "Dawn at @atelier.",
       "@kevin and a colleague load boxes of vinyl siding into the bed of a white pickup truck, brisk and efficient, dawn light, breath "
       "vapour; the small holographic job file floats beside the truck. Handheld tracking camera.", "Boxes thudding, truck tailgate, birds."),
     "caméra à l'épaule", "—", "cartons", "RÉEL"),
    ("p19", "S6 M5 finance", 124, ["luc", "comptable"], None,
     P("the holographic accountant materializes in the owner's office.",
       "Evening in Luc's office, large window on the city lights, warm desk lamp.",
       "A column of ion-blue light rises from the desk and @comptable materializes from swirling particles, standing beside the desk; "
       "@luc leans back in his chair, impressed. Slow push-in.", "Shimmering materialization, low hum."),
     "avancé lent", "matérialisation", "scintillement", "VISION"),
    ("p20", "S6 M5 finance", 124, ["luc"], "l01",
     P("the owner asks about profits.", "Evening in Luc's office, warm lamp, city lights.",
       "Medium close-up: @luc leans back, relaxed and curious, and asks a question to the hologram off-screen right.", "Office room tone.",
       "@luc speaks in Québécois French, matching <Audio 1> word for word."),
     "plan rapproché", "—", "voix", "illustratif"),
    ("p21", "S6 M5 finance", 243, ["comptable"], "c01",
     P("the holographic accountant presents the projected profits.", "Evening office, dark background with warm bokeh.",
       "Medium close-up: @comptable speaks to the camera with assurance and a slight smile, gesturing with one hand towards a rising "
       "holographic curve of light beside her; light flickers subtly across her face.", "Soft hum of the hologram.",
       "@comptable speaks in Québécois French, matching <Audio 1> word for word."),
     "plan rapproché", "courbe holographique", "voix", "VISION"),
    ("p22", "S6 M5 finance", 124, ["luc", "comptable"], None,
     P("the office fills with a giant holographic profit projection.", "Evening in Luc's office.",
       "Wide shot: a giant holographic projection fills the room, a rising curve of light and floating bars hovering over the desk; @luc "
       "stands up and walks into the light, reflections on his face; @comptable stands beside him. Slow arc camera.",
       "Rising shimmer, soft whoosh."),
     "arc lent", "projection géante", "scintillement", "VISION"),
    ("p23", "S7 M4 cédule", 124, ["luc"], "g01",
     P("a holographic operations planner presents the schedule.", "Evening in Luc's office, @luc in the background.",
       "A holographic operations planner — a woman in her late twenties with short curly hair and glasses, made of translucent ion-blue "
       "light with fine scan lines and a realistic face — appears on the other side of the desk and speaks, presenting with an open hand.",
       "Soft hum.", "The holographic planner speaks in Québécois French, matching <Audio 1> word for word."),
     "plan moyen", "avatar holographique", "voix", "VISION"),
    ("p24", "S7 M4 cédule", 124, ["luc"], None,
     P("a holographic three-week calendar covers the office floor.", "Evening office seen from above.",
       "High top-down shot slowly descending: the floor of the office becomes a huge holographic calendar of light, three weeks of glowing "
       "blocks sliding into place, tiny holographic trucks and crews moving between the blocks; @luc stands in the middle looking down.",
       "Blocks clicking into place, soft whooshes."),
     "plongée zénithale descendante", "calendrier holographique", "clics", "EN PRÉPARATION"),
    ("p25", "S8 l'adjointe", 124, ["etienne"], None,
     P("the representative gets a call while driving.",
       "Noon, a highway along the St. Lawrence river on a sunny autumn day.",
       "Inside a white pickup truck: @etienne drives; his phone in a dash mount lights up with an incoming-call glow (no text on the "
       "screen); he taps it with one finger and listens. Side angle from the passenger seat.", "Road noise, soft ringtone chime."),
     "côté passager", "—", "sonnerie", "illustratif"),
    ("p26", "S8 M1 réception", 243, ["hq"], "a01",
     P("the holographic administrative assistant calls the representative.", "The reception floor of @hq.",
       "Medium close-up: a holographic administrative assistant — a woman in her early thirties with dark hair in a low bun and a wireless "
       "headset, made of translucent ion-blue light with a warm realistic face — speaks warmly and efficiently into her headset; "
       "holographic agenda blocks rearrange themselves beside her.", "Soft office hum of light.",
       "The holographic assistant speaks in Québécois French, matching <Audio 1> word for word.", virtuel=True),
     "plan rapproché", "blocs d'agenda", "voix", "VISION"),
    ("p27", "S8 l'adjointe", 124, ["etienne"], "e02",
     P("the representative answers with a smile while driving.", "Inside the white pickup truck, noon sun.",
       "Medium close-up: @etienne, driving, smiles and answers, relaxed.", "Road noise.",
       "@etienne speaks in Québécois French, matching <Audio 1> word for word."),
     "plan rapproché", "—", "voix", "illustratif"),
    ("p28", "S9 pointage", 124, ["kevin", "atelier"], None,
     P("the installer clocks in at dawn.", "Dawn at the door of @atelier.",
       "@kevin walks to the shop door and holds his phone to a small glowing pad on the wall; a ring of orange light closes around it, he "
       "nods and walks in. Medium shot.", "Footsteps on frost, a short confirmation beep, door."),
     "plan moyen", "anneau orange", "bip", "EN PRÉPARATION"),
    ("p29", "S9 le chantier", 124, ["maison"], None,
     P("time-lapse of the crew renewing the siding of the house.", "@maison.",
       "Time-lapse: the sun arcs over @maison while a crew installs new dark-grey vinyl siding; the old beige siding disappears panel by "
       "panel, clouds race, shadows sweep across the lawn; the finished house glows at sunset.", "Time-lapse whoosh, faint hammering."),
     "accéléré, caméra fixe", "accéléré", "souffle", "illustratif"),
    ("p30", "S9 la paye", 124, ["luc", "kevin", "atelier"], "l02",
     P("the owner hands the installer his paycheque.", "Friday afternoon inside @atelier, warm light.",
       "Medium two-shot: @luc hands @kevin a white paycheque envelope and shakes his hand with a warm smile, speaking a few words; Kevin "
       "grins.", "Shop ambience.", "@luc speaks in Québécois French, matching <Audio 1> word for word."),
     "deux personnages", "—", "voix", "VISION"),
    ("p31", "S10 le réseau", 124, [], None,
     P("a living network of light connects a whole region.", "Night aerial view of a Québec suburb and countryside.",
       "Rising aerial shot: thin glowing orange and ion-blue lines of light connect houses, a work shop, pickup trucks on the roads and "
       "telecommunication towers, all converging towards a data centre glowing on the horizon; the network pulses like a heartbeat.",
       "Wide airy swell, distant pulses."),
     "montée aérienne", "réseau lumineux", "souffle", "métaphore", True),
    ("p32", "S10 les dix départements", 243, ["hq"], None,
     P("the camera rises through all ten floors of the virtual headquarters.", "Inside @hq.",
       "The camera rises vertically at speed through all ten floors of @hq: each floor a full department lit and busy with holographic "
       "workers — documents, graphs, calendars, small vehicles of light — up to the top, where a sphere of warm white light glows; the "
       "camera bursts into the light.", "Rising roar of light, layered chimes, final burst.", virtuel=True),
     "montée verticale", "dix étages", "montée + éclat", "métaphore"),
]
# 9:16 natif de la version courte (6 unités)
VERTICAUX = ["p02", "p05", "p07", "p11", "p14", "p16"]


# ------------------------------------------------------------------------------------------------------------- montage
def montage(bpm, phase, decalage, durees_voix):
    b = 60.0 / bpm
    f = lambda s: int(round(s * FPS))  # noqa: E731
    # (plan, temps de musique en battements, entrée dans la source en s)
    L = [("p01", 8, 0.6), ("p02", 6, 0.3), ("p03", 5, 0.5), ("p04", 5, 0.4), ("p05", 5, 0.5), ("p06", 8, 0.2),
         ("p07", 12, 0.0), ("p08", 5, 0.6), ("p09", 6, 0.5), ("p10", 5, 0.5), ("p11", 10, 0.3), ("p12", 5, 0.8),
         ("p13", 5, 0.3), ("p14", 5, 0.6), ("p15", 8, 0.0), ("p16", 6, 0.0),
         ("p17", 8, 0.4), ("p18", 6, 0.5), ("p19", 8, 0.4), ("p20", 5, 0.0), ("p21", 19, 0.0), ("p22", 8, 0.4),
         ("p23", 7, 0.0), ("p24", 11, 0.2), ("p25", 6, 0.6), ("p26", 18, 0.0), ("p27", 5, 0.0), ("p28", 6, 0.5),
         ("p29", 5, 0.3), ("p30", 8, 0.0), ("p31", 10, 0.3), ("p32", 20, 0.0)]
    parole = {p[0]: p[4] for p in PL}
    video, t, debuts = [], 0.0, {}
    for i, (pid, nb, ent) in enumerate(L):
        d = nb * b
        if parole.get(pid):  # un plan parlant dure au moins sa réplique + 0,35 s
            d = max(d, durees_voix.get(parole[pid], 2.0) + 0.35)
            ent = 0.0
        tr = {"type": "cut", "duree_f": 0}
        if pid in ("p07", "p17"):
            tr = {"type": "dip", "duree_f": 4}
            t -= 4 / FPS  # le dip chevauche le plan précédent
        debuts[pid] = t
        video.append({"id": f"c{i + 1:02d}", "src": pid, "entree_f": f(ent), "duree_f": f(d), "transition_in": tr,
                      **({"zoom": {"de": 1.0, "a": 1.08}} if pid in ("p12", "p20", "p27") else {}),
                      **({"rampe": {"de": 1.0, "a": 1.6}} if pid in ("p06", "p13") else {})})
        t += f(d) / FPS
    t_noir = t
    video.append({"id": "c-noir", "src": "noir", "entree_f": 0, "duree_f": f(6 * b)})
    t += f(6 * b) / FPS
    video.append({"id": "c-carton", "src": "carton", "entree_f": 0, "duree_f": f(20 * b)})
    t_carton = t
    t += f(20 * b) / FPS
    total_f = sum(c["duree_f"] - (c["transition_in"]["duree_f"] if c.get("transition_in", {}).get("type", "cut") != "cut" else 0) for c in video)

    def voix_a(lid, s):
        return {"src": lid, "debut_f": f(s), "duree_f": max(1, f(durees_voix.get(lid, 2.0))), "gain_db": 0}

    vx = [voix_a("n01", 0.45), voix_a("n02", debuts["p05"] - 1.2), voix_a("n03", debuts["p07"] + 0.8),
          voix_a("n04", debuts["p11"] + 0.2), voix_a("n05", debuts["p31"] + 0.2), voix_a("n06", t_noir + 0.25),
          voix_a("n07", t_carton + 0.5)]
    for pid, lid in parole.items():
        if lid:
            vx.append(voix_a(lid, debuts[pid]))
    sources = {p[0]: {"kind": "video"} for p in PL}
    sources.update({"noir": {"kind": "image"}, "carton": {"kind": "image"}, "musique": {"kind": "audio"}})
    sources.update({v[0]: {"kind": "audio"} for v in V})
    plan = {"version": 1, "fps": FPS, "format": "16:9", "genre": "pub", "titre": "Le siège social",
            "sources": sources, "video": video,
            "audio": {"musique": {"src": "musique", "entree_f": f(decalage), "gain_db": -6, "fondu_in_f": 0, "fondu_out_f": f(2.5)},
                      "voix": vx, "ducking": {"actif": True, "profondeur_db": 9}, "cible_lufs": -14, "crete_db": -1.5, "fondu_coupe_ms": 30},
            "textes": []}
    D = debuts
    inc = [
        {"type": "statut", "texte": "Photo reçue.", "debut_f": f(D["p02"] + 0.3), "duree_f": f(2.2), "position": "bas-gauche"},
        {"type": "flash", "intensite": 0.8, "debut_f": f(D["p02"] - 0.05), "duree_f": 4},
        {"type": "trajet", "points": [[0.5, 0.95], [0.55, 0.55], [0.62, 0.08]], "couleur": "signal", "debut_f": f(D["p02"] + 0.2), "duree_f": f(2.0)},
        {"type": "statut", "texte": "Signal : satellite · tour 5G · réseau électrique", "debut_f": f(D["p03"] + 0.3), "duree_f": f(D["p06"] - D["p03"] - 0.3), "position": "bas-gauche"},
        {"type": "flash", "intensite": 1.0, "debut_f": f(D["p07"] - 0.08), "duree_f": 4},
        {"type": "titre", "texte": "Dix départements.|*Une seule équipe.*", "zone": "colonne", "debut_f": f(D["p07"] + 1.2), "duree_f": f(3.6)},
        {"type": "surtitre", "texte": "M1 · RÉCEPTION", "debut_f": f(D["p08"] + 0.1), "duree_f": f(2.2), "position": "haut-gauche"},
        {"type": "surtitre", "texte": "M3 · ESTIMATION", "debut_f": f(D["p09"] + 0.1), "duree_f": f(D["p12"] - D["p09"] - 0.2), "position": "haut-gauche"},
        {"type": "etiquette", "texte": "VISION · MESURE PAR PHOTO", "debut_f": f(D["p09"] + 0.3), "duree_f": f(2.4), "position": "bas-droite"},
        {"type": "statut", "texte": "Façade : 62,8 m². Moulures : 46 m.", "debut_f": f(D["p09"] + 0.6), "duree_f": f(2.2), "position": "bas-gauche"},
        {"type": "statut", "texte": "Simulation des coûts…", "debut_f": f(D["p10"] + 0.2), "duree_f": f(2.0), "position": "bas-gauche"},
        {"type": "document", "titre": "SOUMISSION 2417", "destinataire": "M. Morin · revêtement de vinyle",
         "lignes": [["Mur avant", "38,2 m²"], ["Murs latéraux", "24,6 m²"], ["Moulures et coins", "46 m"], ["Main-d'œuvre", "3 jours"]],
         "total": "18 940 $", "tampon": None, "debut_f": f(D["p11"] + 0.2), "duree_f": f(D["p12"] - D["p11"] - 0.2), "position": "droite"},
        {"type": "statut", "texte": "Revue en 11 critères : conforme.", "debut_f": f(D["p11"] + 2.4), "duree_f": f(2.4), "position": "bas-gauche"},
        {"type": "surtitre", "texte": "APPROBATION HUMAINE", "debut_f": f(D["p12"] + 0.1), "duree_f": f(2.3), "position": "haut-gauche"},
        {"type": "statut", "texte": "Approuvée par Luc. Envoi.", "debut_f": f(D["p12"] + 0.9), "duree_f": f(1.5), "position": "bas-gauche"},
        {"type": "glitch", "intensite": 0.5, "debut_f": f(D["p13"]), "duree_f": 5},
        {"type": "document", "titre": "SOUMISSION 2417", "destinataire": "M. Morin · revêtement de vinyle",
         "lignes": [["Mur avant", "38,2 m²"], ["Murs latéraux", "24,6 m²"], ["Moulures et coins", "46 m"], ["Main-d'œuvre", "3 jours"]],
         "total": "18 940 $", "tampon": "PRÊTE", "debut_f": f(D["p14"] + 0.4), "duree_f": f(D["p15"] - D["p14"] + 1.5), "position": "droite", "echelle": 0.85},
        {"type": "flash", "intensite": 0.7, "debut_f": f(D["p17"] - 0.05), "duree_f": 4},
        {"type": "surtitre", "texte": "M4 · TERRAIN", "debut_f": f(D["p17"] + 0.1), "duree_f": f(3.6), "position": "haut-gauche"},
        {"type": "statut", "texte": "Dossier de chantier : Morin, lundi 7 h.", "debut_f": f(D["p17"] + 0.6), "duree_f": f(3.0), "position": "bas-gauche"},
        {"type": "surtitre", "texte": "M6 · MATÉRIEL", "debut_f": f(D["p18"] + 0.1), "duree_f": f(2.6), "position": "haut-gauche"},
        {"type": "statut", "texte": "Réservé : 14 boîtes de vinyle gris.", "debut_f": f(D["p18"] + 0.4), "duree_f": f(2.4), "position": "bas-gauche"},
        {"type": "surtitre", "texte": "M5 · FINANCE", "debut_f": f(D["p19"] + 0.1), "duree_f": f(3.6), "position": "haut-gauche"},
        {"type": "etiquette", "texte": "VISION · AVATAR", "debut_f": f(D["p19"] + 0.5), "duree_f": f(3.0), "position": "bas-droite"},
        {"type": "courbe", "points": [100, 104, 103, 109, 112, 115, 121, 126, 131], "pointille_depuis": 5, "etiquette": "PROFITS ANTICIPÉS",
         "valeur": "+7 %", "debut_f": f(D["p21"] + 2.0), "duree_f": f(D["p23"] - D["p21"] - 2.0), "position": "droite", "echelle": 0.9},
        {"type": "compteur", "de": 0, "a": 7, "suffixe": " %", "etiquette": "PRODUCTIVITÉ", "debut_f": f(D["p22"] + 0.1), "duree_f": f(D["p23"] - D["p22"] - 0.1), "position": "gauche"},
        {"type": "surtitre", "texte": "M4 · CÉDULE", "debut_f": f(D["p23"] + 0.1), "duree_f": f(D["p25"] - D["p23"] - 0.2), "position": "haut-gauche"},
        {"type": "cedule", "titre": "CÉDULE · 3 SEMAINES", "semaines": 3,
         "blocs": [[0, 0, 2, 0, "Chantier Morin"], [0, 3, 4, 1, "Gouttières Lavoie"], [1, 0, 1, 0, "Soffite Gagnon"], [1, 2, 4, 2, "Revêtement Roy"],
                   [2, 0, 4, 0, "Chantier Côté"], [2, 1, 3, 1, "Fascia Bélanger"]],
         "debut_f": f(D["p24"] + 0.2), "duree_f": f(D["p25"] - D["p24"] - 0.2), "position": "centre", "echelle": 0.95},
        {"type": "etiquette", "texte": "EN PRÉPARATION", "debut_f": f(D["p24"] + 0.5), "duree_f": f(2.5), "position": "bas-droite"},
        {"type": "appel", "nom": "Adjointe", "sous_titre": "Appel entrant", "voix": "a01", "debut_f": f(D["p25"] + 0.5), "duree_f": f(D["p27"] - D["p25"] - 0.5), "position": "haut-droite"},
        {"type": "surtitre", "texte": "M1 · RÉCEPTION", "debut_f": f(D["p26"] + 0.1), "duree_f": f(3.0), "position": "haut-gauche"},
        {"type": "etiquette", "texte": "VISION · RÉCEPTIONNISTE VOCALE", "debut_f": f(D["p26"] + 0.6), "duree_f": f(3.0), "position": "bas-droite"},
        {"type": "pointage", "heure": "06:58", "nom": "Kevin Tremblay", "etat": "ARRIVÉE", "debut_f": f(D["p28"] + 0.3), "duree_f": f(D["p29"] - D["p28"] - 0.3), "position": "droite", "echelle": 0.8},
        {"type": "etiquette", "texte": "EN PRÉPARATION", "debut_f": f(D["p28"] + 0.5), "duree_f": f(2.0), "position": "bas-droite"},
        {"type": "surtitre", "texte": "M5 · PAYE", "debut_f": f(D["p30"] + 0.1), "duree_f": f(3.0), "position": "haut-gauche"},
        {"type": "etiquette", "texte": "VISION", "debut_f": f(D["p30"] + 0.5), "duree_f": f(2.5), "position": "bas-droite"},
        {"type": "pile", "lignes": ["M1 Réception", "M2 CRM", "M3 Estimation", "M4 Terrain", "M5 Finance", "M6 Matériel", "M7 Marketing",
                                    "M8 Analytique", "M9 Stratégie", "M10 Mémoire"], "debut_f": f(D["p32"] + 0.6), "duree_f": f(8.6), "zone": "colonne"},
        {"type": "flash", "intensite": 1.0, "debut_f": f(t_noir - 0.08), "duree_f": 4},
        {"type": "impact", "texte": "Les ressources d'une *grande entreprise.*", "debut_f": f(t_noir + 0.1), "duree_f": f(6 * b - 0.2)},
        {"type": "carton", "debut_f": f(t_carton), "duree_f": f(20 * b)},
    ]
    sfx = [{"type": "clic", "debut_f": f(D["p01"] + 2.9), "db": -4}, {"type": "fouet", "debut_f": f(D["p02"] - 0.15), "db": -3},
           {"type": "impact", "debut_f": f(D["p02"]), "db": -2}, {"type": "montee", "debut_f": f(D["p06"]), "duree_s": round(D["p07"] - D["p06"], 2), "db": -6},
           {"type": "boom", "debut_f": f(D["p07"]), "db": -1}, {"type": "inverse", "debut_f": f(D["p13"] - 0.6), "db": -6},
           {"type": "impact", "debut_f": f(D["p17"]), "db": -4}, {"type": "impact", "debut_f": f(t_noir), "db": -1},
           {"type": "chute", "debut_f": f(t_carton), "db": -3}]
    son = [{"plan": p, "db": -14} for p in ("p01", "p02", "p03", "p04", "p05", "p06", "p07", "p13", "p18", "p25", "p29", "p31", "p32")]
    annexe = {"incrustations": inc, "sfx": sfx, "son_plans": son, "etalonnage": {"contraste": 1.05, "saturation": 1.04, "grain": 1.0},
              "caler_sur_temps": False}
    return plan, annexe, total_f


def court(bpm, phase, decalage, durees_voix, vertical=False):
    """10 à 15 s : la soumission qui voyage par signal. Plans du film long (16:9) ou verticaux natifs (9:16)."""
    b = 60.0 / bpm
    f = lambda s: int(round(s * FPS))  # noqa: E731
    v = "v" if vertical else ""
    L = [("p01", 3, 1.4), (f"p02{v}", 3, 0.4), ("p03", 2, 0.8), (f"p05{v}", 2, 0.8), ("p06", 2, 1.2), (f"p07{v}", 3, 0.0),
         ("p09", 2, 0.8), (f"p11{v}", 3, 1.0), ("p13", 2, 0.6), (f"p14{v}", 2, 1.0), (f"p16{v}", 3, 0.0)]
    if vertical:  # les plans non tournés en 9:16 sont recadrés au centre
        L = [(p if p.endswith("v") else p, n, e) for p, n, e in L]
    video, t, D = [], 0.0, {}
    for i, (pid, nb, ent) in enumerate(L):
        d = nb * b
        if pid.startswith("p16"):
            d = max(d, durees_voix.get("m01", 1.0) + 0.6)
        D[pid[:3]] = t
        video.append({"id": f"k{i + 1:02d}", "src": pid, "entree_f": f(ent), "duree_f": f(d), "transition_in": {"type": "cut", "duree_f": 0}})
        t += f(d) / FPS
    video.append({"id": "k-carton", "src": "carton", "entree_f": 0, "duree_f": f(4 * b)})
    t_carton = t
    t += f(4 * b) / FPS
    sources = {x[0]: {"kind": "video"} for x in L}
    sources.update({"carton": {"kind": "image"}, "musique": {"kind": "audio"}, "n01": {"kind": "audio"}, "m01": {"kind": "audio"}})
    plan = {"version": 1, "fps": FPS, "format": "9:16" if vertical else "16:9", "genre": "social", "titre": "Le siège social · 15 s",
            "sources": sources, "video": video,
            "audio": {"musique": {"src": "musique", "entree_f": f(decalage + 2.0), "gain_db": -6, "fondu_in_f": 0, "fondu_out_f": f(1.2)},
                      "voix": [{"src": "n01", "debut_f": f(0.25), "duree_f": f(durees_voix.get("n01", 1.0)), "gain_db": 0},
                               {"src": "m01", "debut_f": f(D["p16"]), "duree_f": f(durees_voix.get("m01", 1.0)), "gain_db": 0}],
                      "ducking": {"actif": True, "profondeur_db": 9}, "cible_lufs": -14, "crete_db": -1.5, "fondu_coupe_ms": 30},
            "textes": []}
    inc = [{"type": "compteur", "de": 0, "a": 10, "suffixe": " s", "etiquette": "SOUMISSION", "debut_f": f(D["p02"]), "duree_f": f(D["p16"] - D["p02"]),
            "position": "haut-droite", "echelle": 0.45},
           {"type": "statut", "texte": "Photo reçue.", "debut_f": f(D["p02"] + 0.1), "duree_f": f(1.4), "position": "bas-gauche"},
           {"type": "flash", "intensite": 1.0, "debut_f": f(D["p07"] - 0.05), "duree_f": 4},
           {"type": "document", "titre": "SOUMISSION 2417", "destinataire": "M. Morin · revêtement",
            "lignes": [["Mur avant", "38,2 m²"], ["Murs latéraux", "24,6 m²"], ["Moulures", "46 m"]], "total": "18 940 $", "tampon": "PRÊTE",
            "debut_f": f(D["p11"]), "duree_f": f(D["p14"] + 1.4 - D["p11"]), "position": "droite", "echelle": 0.8},
           {"type": "etiquette", "texte": "VISION", "debut_f": f(D["p07"]), "duree_f": f(3.0), "position": "bas-droite"},
           {"type": "carton", "debut_f": f(t_carton), "duree_f": f(4 * b)}]
    sfx = [{"type": "clic", "debut_f": f(1.0), "db": -4}, {"type": "fouet", "debut_f": f(D["p02"] - 0.12), "db": -3},
           {"type": "boom", "debut_f": f(D["p07"]), "db": -2}, {"type": "inverse", "debut_f": f(D["p13"] - 0.5), "db": -6},
           {"type": "impact", "debut_f": f(t_carton), "db": -2}]
    annexe = {"incrustations": inc, "sfx": sfx, "son_plans": [{"plan": "p05", "db": -14}, {"plan": "p07", "db": -14}],
              "recadrage_v": {"p01": 0.55, "p03": 0.5, "p06": 0.5, "p09": 0.5, "p13": 0.5}}
    return plan, annexe


def main():
    a = argparse.ArgumentParser()
    a.add_argument("--bpm", type=float, default=124.0)
    a.add_argument("--phase", type=float, default=0.0)
    a.add_argument("--decalage", type=float, default=0.0)
    o = a.parse_args()
    # durées mesurées des voix si elles existent (révision), sinon estimées à 14 caractères/s
    travail = Path.home() / "nexora-creative-data/work/opsys-ultime/opus/voix"
    dv = {}
    for lid, _r, _v, txt, _d in V:
        j = sorted(travail.glob(f"{lid}-p*.json"))
        dv[lid] = json.loads(j[0].read_text())["utile_s"] if j else round(len(txt) / 14 + 0.2, 2)
    long_, ann_long, total = montage(o.bpm, o.phase, o.decalage, dv)
    court_, ann_court = court(o.bpm, o.phase, o.decalage, dv)
    vert_, ann_vert = court(o.bpm, o.phase, o.decalage, dv, vertical=True)
    plans = []
    for x in PL:
        pid, seq, images, refs, parole, prompt, cam, eff, son, statut = x[:10]
        plans.append({"id": pid, "sequence": seq, "recette": "h3-max", "images": images, "graine": 5000 + int(pid[1:]) * 11,
                      "format": "16:9", "refs": refs, "premiere": None, "parole": parole, "prompt": prompt,
                      "camera": cam, "effets": eff, "son": son, "statut": statut})
    for pid in VERTICAUX:
        p = next(q for q in plans if q["id"] == pid)
        plans.append({**p, "id": pid + "v", "format": "9:16", "images": 124, "sequence": p["sequence"] + " (9:16)"})
    musique = {
        "prompt": ("Instrumental cinematic hybrid score for a high-energy Québec technology commercial, 136 seconds long, 124 BPM, "
                   "D minor rising to F major, uplifting, driving, heroic, confident, modern, never sad, never melancholic. Big punchy "
                   "drums, pulsing synth bass, bright arpeggios, string ostinatos, brass stabs, huge clean hits, wide stereo, loud polished "
                   "master, no vocals, no choir words. Structure: 0-4 s tense ticking pulse and a low heartbeat; at 4 s one huge hit with a "
                   "camera-flash-like snap; 4-18 s fast driving build, rising arpeggios and risers, energy climbing; at 18 s a massive "
                   "drop, the biggest moment so far, epic and bright; 18-50 s full anthem energy with soaring synth lead and big drums; at "
                   "50 s a hit and a switch to a confident mid-tempo groove with tight drums, funky bass and light synths, leaving space for "
                   "dialogue (no lead melody between 50 and 104 s); 104-108 s riser; 108-124 s the final and biggest chorus, heroic and "
                   "triumphant; at 124 s one final huge hit then a 12-second warm resolved tail."),
        "bpm_vise": 124, "duree_s": 136,
        "coups": [{"t_s": 3.9, "evenement": "le signal quitte le téléphone"}, {"t_s": 17.9, "evenement": "révélation du siège social"},
                  {"t_s": 50.3, "evenement": "acte 2 : le chantier"}, {"t_s": 108.4, "evenement": "le réseau"},
                  {"t_s": 123.4, "evenement": "Les ressources d'une grande entreprise"}]}
    dossier = {
        "equipe": "opus", "titre": "Le siège social",
        "logline": "Une photo prise devant une maison de Laval met au travail, en dix secondes, une entreprise entière qui vit dans un serveur.",
        "personnages": PERSONNAGES, "lieux": LIEUX, "cles": [],
        "voix": [{"id": i, "role": r, "voix": v, "texte": t, "direction": d, "vitesse": VITESSE.get(i, 1.0), "prises": 2} for i, r, v, t, d in V],
        "plans": plans, "musique": musique,
        "montage": {"long": long_, "court": court_, "vertical": vert_},
        "annexe": {"long": ann_long, "court": ann_court, "vertical": ann_vert},
        "_grille": {"bpm": o.bpm, "phase": o.phase, "decalage": o.decalage, "duree_long_s": round(total / FPS, 2)},
    }
    (ICI / "dossier.json").write_text(json.dumps(dossier, ensure_ascii=False, indent=1))
    u = sum(1 if p["images"] <= 124 else 2 for p in plans if p["format"] == "16:9")
    print(f"dossier.json : {len(plans)} plans, {u} unités 16:9, {len(VERTICAUX)} unités 9:16, "
          f"{sum(1 for p in plans if p['parole'] and p['format'] == '16:9')} plans parlants, film long {total / FPS:.1f} s")


if __name__ == "__main__":
    main()
