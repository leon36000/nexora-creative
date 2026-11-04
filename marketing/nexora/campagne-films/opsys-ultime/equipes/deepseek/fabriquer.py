# -*- coding: utf-8 -*-
"""Fabrique dossier.json (equipe deepseek).
Grille : 124 BPM, 24 i/s -> 1 temps = 11,6129 images. Toutes les frontieres de plan
sont des multiples de temps arrondis une seule fois (cumul) : pas de derive.
Budget : 40 unites 16:9 (1 unite = un rendu <=124 images), 6 unites 9:16,
12 plans parlants, 8 fiches, 24 images cles, 30 repliques, 3 musiques.
"""
import json, math
from pathlib import Path

BPM, FPS = 124.0, 24
BEAT = 60.0 / BPM
GRILLE = [124 + 17 * k for k in range(8)]   # 124,141,158,175,192,209,226,243

def B(n):
    """n temps -> image (arrondi)."""
    return int(round(n * BEAT * FPS))

def fr(t_s):
    return int(round(t_s * FPS))

def rendu(images):
    """Plus petite longueur de rendu permise >= images."""
    for g in GRILLE:
        if g >= images:
            return g
    return GRILLE[-1]

STYLE = ("Cinematic frame from a 2026 feature film, shot on a large-format digital cinema camera "
         "with anamorphic lenses, real exposure, rich contrast, natural film colour, fine grain, "
         "shallow depth of field.")

PERSOS = [
 {"id": "etienne", "nom": "Étienne", "role": "représentant (mesure, soumission)",
  "voix": "drama3-adamqc",
  "fiche": ("Character reference sheet on a plain neutral grey studio background, 1792x1024, two views side by side: "
            "full body standing on the left, tight head-and-shoulders portrait on the right. A Québécois exterior-renovation "
            "sales representative, man of 34, short dark brown hair, three-day stubble, sharp friendly eyes, athletic build. "
            "He wears a plain charcoal work jacket over a plain heather-grey t-shirt, dark work trousers, worn leather work "
            "boots, a plain navy baseball cap with no logo and no lettering, a measuring tape clipped to his belt. Natural skin "
            "texture, soft even studio light, plain clothing with no logo, no text, no letters anywhere.")},
 {"id": "morin", "nom": "Monsieur Morin", "role": "propriétaire de la PME (administrateur)",
  "voix": "drama3-frederic",
  "fiche": ("Character reference sheet on a plain neutral grey studio background, 1792x1024, two views side by side: full body "
            "on the left, tight head-and-shoulders portrait on the right. A Québécois small-business owner, man of 54, short "
            "greying hair, close grey beard, reading glasses pushed up on his forehead, broad shoulders, weathered hands. He "
            "wears a plain navy knit sweater over a plain checked shirt, dark trousers, no tie, no watch. Warm, stubborn, kind "
            "face, deep smile lines. Natural skin texture, soft even studio light, plain clothing with no logo, no text, no letters.")},
 {"id": "adjointe", "nom": "L'adjointe", "role": "adjointe administrative virtuelle (M1 Réception)",
  "voix": "eleven-jeannemance",
  "fiche": ("Character reference sheet on a plain neutral grey studio background, 1792x1024, two views side by side: full body "
            "seated on the left, tight head-and-shoulders portrait on the right. A woman of 30, dark hair tied back in a low "
            "bun, clear intelligent eyes, light makeup, small headset with a thin boom microphone. She wears a plain light-grey "
            "blazer over a plain white shirt, no jewellery. She is rendered as a figure made of fine blue-white points of light, "
            "translucent, edges glowing, with a warm orange rim light on one side, while her face stays clearly readable and "
            "human. No text, no letters, no logo anywhere.")},
 {"id": "avatar", "nom": "L'avatar des départements", "role": "avatar holographique (comptabilité, gestion)",
  "voix": "drama3-jeannemance",
  "fiche": ("Character reference sheet on a plain neutral grey studio background, 1792x1024, two views side by side: bust on the "
            "left, tight head-and-shoulders portrait on the right. A humanoid bust built from thousands of fine blue-white points "
            "of light, no clothing details, smooth shoulders fading into darkness, a calm androgynous face with clearly readable "
            "eyes and mouth, a deep orange glow inside one eye, faint horizontal scan lines crossing the skin of light. No text, "
            "no letters, no logo anywhere.")},
]

LIEUX = [
 {"id": "toit", "fiche": ("Location reference sheet, plain neutral grey background, 1792x1024, two views: wide exterior on the left, "
   "detail on the right. The roof of a suburban Québec bungalow at first light: worn asphalt shingles in the foreground, a strip of "
   "new dark grey soffit-fascia and a section of freshly installed pale grey siding on the right, an aluminium ladder hooked on the "
   "eave, morning mist, wet shingles, no people, no text, no logo.")},
 {"id": "tour", "fiche": ("Location reference sheet, plain neutral grey background, 1792x1024, two views: full tower on the left, "
   "close detail of one floor on the right. A colossal virtual office tower standing above a layer of clouds at dawn: ten distinct "
   "floors of dark glass and ion-blue light, each floor a wide open office seen in cross-section with rows of desks and silhouetted "
   "workers, thin vertical fins between floors, one warm orange light burning at the very top, no text, no logo.")},
 {"id": "bureau", "fiche": ("Location reference sheet, plain neutral grey background, 1792x1024, two views: wide room on the left, "
   "detail of the desk on the right. The office of a small Québec renovation company at dusk: a worn wooden desk, rolled paper plans, "
   "a coffee mug, a window onto a quiet suburban street, warm practical lamps, a plain pegboard wall with hand tools, a filing "
   "cabinet, no text, no logo, no computer screen readable.")},
 {"id": "serveur", "fiche": ("Location reference sheet, plain neutral grey background, 1792x1024, two views: wide room on the left, "
   "detail of the rack on the right. A small client server room in a clean basement: one dark steel rack with neat bundles of cable, "
   "small blue status lights, a concrete floor, a single warm work lamp, cold blue ambient light, no text, no logo, no readable "
   "screen anywhere.")},
]

CLES = [
 {"id": "k01", "format": "16:9", "prompt": ("First frame of a film shot. Low angle on the roof of a suburban Québec bungalow at first light, wet "
   "asphalt shingles in the foreground, a strip of freshly installed pale grey siding on the right, morning mist. A man in a plain "
   "charcoal work jacket and a plain navy cap stands at the edge of the roof, back to camera, raising a plain dark phone toward the "
   "siding. Overcast dawn sky, cold blue light with one warm orange glow on the horizon. Photographic, anamorphic, fine grain, no "
   "text, no logo, no readable screen.")},
 {"id": "k02", "format": "16:9", "prompt": ("First frame of a film shot. A dawn sky above a layer of low cloud, seen from high altitude. A lattice "
   "communications tower stands on the left, a white satellite dish on the right; a thin thread of ion-blue light crosses between them "
   "and continues toward the horizon. Cold blue and pale pink sky, anamorphic flare, fine grain, no text, no logo.")},
 {"id": "k03", "format": "16:9", "prompt": ("First frame of a film shot. A corridor of wooden hydro poles and sagging cables along a country road at "
   "dawn, frost on the grass, a pulse of ion-blue light running along the cables toward a small industrial building in the distance. "
   "Low camera at cable height, cold blue light, warm orange in a window, fine grain, no text, no logo, no readable sign.")},
 {"id": "k04", "format": "16:9", "prompt": ("First frame of a film shot. A plain white cargo van pulling out of a suburban driveway at dawn, seen from "
   "the side at low angle, headlights on, wet asphalt, a light trail of ion-blue drawn in the air ahead of it. Cold blue dawn, fine "
   "grain, no text, no logo, no readable plate.")},
 {"id": "k05", "format": "16:9", "prompt": ("First frame of a film shot. A finished house exterior at golden hour: new pale grey siding, dark soffit and "
   "fascia, clean eaves, a ladder leaning against the wall, long warm shadows on the lawn. A camera rig made of thin light orbits the "
   "roof, small petals of light floating away from it. Warm gold and deep shadow, anamorphic, fine grain, no text, no logo.")},
 {"id": "k07", "format": "16:9", "prompt": ("First frame of a film shot. A wall of fine blue-white light fills the frame, slightly curved, one brighter "
   "rectangle beginning to thicken on its surface. Cold blue, warm orange at the edges, fine grain, no text, no logo, no readable letters.")},
 {"id": "k08", "format": "16:9", "prompt": ("First frame of a film shot. An empty dawn sky, deep blue at the top fading to pale amber at the horizon, one thin band "
   "of cloud, nothing else. Clean, quiet, anamorphic, fine grain, no text, no logo.")},
 {"id": "k09", "format": "16:9", "prompt": ("First frame of a film shot. A wide virtual office floor in cross-section: dark desks in rows, tall glass onto a cloud sea, "
   "silhouetted workers standing, one empty desk in the foreground lit by a cold shaft of light. Ion-blue accents, fine grain, no text, no logo, "
   "no readable screen.")},
 {"id": "k10", "format": "16:9", "prompt": ("First frame of a film shot. A small industrial building at dawn seen from the road, overhead hydro "
   "cables entering its wall, one lit window, frost on the gravel, a thin blue line of light running down the wall toward a steel door. "
   "Cold blue, fine grain, no text, no logo, no readable sign.")},
 {"id": "k11", "format": "16:9", "prompt": ("First frame of a film shot. A wide virtual office floor seen in cross-section from the outside through tall "
   "glass: rows of dark desks, silhouetted workers standing between them, a cloud sea beyond, ion-blue light from the ceiling. Fine grain, "
   "no text, no logo, no readable screen.")},
 {"id": "k06", "format": "16:9", "prompt": ("First frame of a film shot. A construction site trailer at 7 a.m. in winter, breath of cold air, a worker in "
   "a plain dark parka walking toward a gate of thin light that flares as he passes. Snow on the ground, blue hour, one warm orange "
   "lamp above the door, fine grain, no text, no logo, no readable sign.")},
]

def P(summary, desc, sound, dialogue=None):
    s = "summary:\n" + summary + "\n\ndetailed_description:\n" + STYLE + "\n" + desc + "\n\n"
    if dialogue:
        s += "dialogue:\n" + dialogue + "\n\n"
    s += "overall_soundscape:\n" + sound + "\n\nnon_diegetic_music:\nN/A"
    return s

VQ = "speaks in Québécois French, matching <Audio 1> word for word"

REPLIQUES = [
 {"id": "l01", "role": "Étienne, sur le toit", "voix": "drama3-adamqc", "vitesse": 1.12, "prises": 2,
  "texte": "Photo prise. Toit de monsieur Thibault, le 3.",
  "direction": "Représentant pressé mais de bonne humeur : ton de gars qui travaille, un peu essoufflé par le froid, "
               "articulation nette, énergie qui monte sur « photo prise ». Pas de ton de speaker."},
 {"id": "l02", "role": "L'adjointe (M1 Réception)", "voix": "eleven-jeannemance", "vitesse": 1.08, "prises": 3,
  "texte": "Bonjour Étienne. Monsieur Thibault à 14 h. J'ai déplacé votre 16 h.",
  "direction": "[warm, professional, efficient] Sourire audible, débit vif et sûr, petite pointe de fierté sur « j'ai déplacé ». "
               "Une vraie adjointe qui connaît son dossier, pas une voix de répondeur."},
 {"id": "l03", "role": "Avatar comptable (M5 Finance)", "voix": "drama3-jeannemance", "vitesse": 1.05, "prises": 2,
  "texte": "Voici les profits anticipés, mis à jour avec les nouveaux ratios. Productivité : plus sept pour cent.",
  "direction": "Autoritaire, précise, sans emphase commerciale : elle énonce un fait vérifié et s'arrête net. "
               "Appuyer « plus sept pour cent » comme une conclusion, pas comme une promesse."},
 {"id": "l04", "role": "Avatar gestion (M4 Terrain)", "voix": "drama3-jeannemance", "vitesse": 1.1, "prises": 2,
  "texte": "Voici la cédule des trois prochaines semaines.",
  "direction": "Sèche, efficace, un peu bousculée : elle a déjà tourné la page avant la fin de la phrase."},
 {"id": "l05", "role": "Monsieur Morin", "voix": "drama3-frederic", "vitesse": 1.12, "prises": 2,
  "texte": "Le deuxième camion, on peut-tu ?",
  "direction": "Patron québécois qui pense tout haut, un peu bourru, regard direct dans la caméra. "
               "Monter sur « peut-tu », ton de défi amical, jamais suppliant."},
 {"id": "l06", "role": "Avatar finance", "voix": "drama3-jeannemance", "vitesse": 1.1, "prises": 2,
  "texte": "Oui. En mars. Le dossier est prêt pour ton comptable.",
  "direction": "Réponse coupée, trois blocs nets. Aucune flatterie. Le « oui » tombe comme un couperet."},
 {"id": "l07", "role": "Monsieur Morin", "voix": "drama3-frederic", "vitesse": 1.15, "prises": 3,
  "texte": "Approuvé.",
  "direction": "Un seul mot, lourd, satisfait, presque à voix basse. La décision d'un homme qui signe. "
               "Ne pas étirer : la coupe tombe sur le « é »."},
 {"id": "l08", "role": "L'adjointe, finale", "voix": "eleven-jeannemance", "vitesse": 1.05, "prises": 2,
  "texte": "OPSYS. Dix départements. Le onzième, c'est vous.",
  "direction": "[confident, warm, punchy] Trois blocs, un temps entre chacun. Le nom tombe net, sans emphase publicitaire. "
               "Le dernier mot se pose, presque complice."},
 {"id": "l09", "role": "Étienne, sur le chantier", "voix": "drama3-adamqc", "vitesse": 1.1, "prises": 2,
  "texte": "La soumission est prête pour ton approbation. Beau toit, hein ?",
  "direction": "Soulagement réel, ton de gars qui rentre chez lui : plus bas, plus lent, sourire dans la voix."},
]

# (id, seq, recette, images, refs, premiere, parole, beats, statut, camera, effets, son, prompt)
PLANS = []

PLANS.append(dict(id="p01", sequence="S1", recette="h3-max", images=124, refs=["etienne", "toit"], premiere="k01",
  beats=8, statut="RÉEL", camera="grues lente de la rue vers le toit, montée de 3 m",
  effets="brume au sol, flare anamorphique sur le soleil levant",
  son="vent léger, gouttière qui craque, oiseaux lointains",
  prompt=P("A single continuous cinematic shot that begins from the key frame: a man on a roof at dawn raises a phone toward new siding.",
    "[Shot 1] The shot begins from the first frame. @etienne, a Québécois renovation representative in a plain charcoal work jacket and a plain navy cap, stands on the wet shingled roof of @toit, beside a strip of freshly installed pale grey siding. He plants his boots, turns his shoulders toward the siding, and lifts a plain dark phone to eye level. Morning mist drifts across the roof and the low sun flares behind him. The camera cranes slowly upward from the street below and settles behind him. Plain clothing with no logo, no text, no letters anywhere.",
    "Light wind over shingles, a distant dog, the creak of an aluminium ladder, the soft click of a phone being lifted.")))
PLANS.append(dict(id="p02", sequence="S1", recette="h3-max", images=124, refs=["etienne"], premiere=None,
  parole="l01", beats=8, statut="RÉEL", camera="gros plan poitrine, léger travelling avant",
  effets="souffle visible, flare froid",
  son="vent, respiration",
  prompt=P("A single continuous cinematic shot: a Québécois representative on a roof speaks to camera, lips perfectly synchronised with <Audio 1>.",
    "[Shot 1] Medium close-up on @etienne on the roof, his plain navy cap low over his eyes, breath visible in the cold air, wet shingles blurred behind him. He looks just past the lens, says his line with the flat efficiency of a man who has done this a thousand times, then his eyes drop to the phone in his hand. The camera pushes in slowly. Plain clothing with no logo, no text, no letters anywhere.",
    "Wind, his breath, the faint electrical hum of the phone.",
    dialogue="@etienne " + VQ + ".")))
PLANS.append(dict(id="p03", sequence="S1", recette="h3-max", images=124, refs=["etienne", "toit"], premiere=None,
  beats=4, statut="RÉEL", camera="plan taille, axe latéral",
  effets="éclair de flash, onde de choc lumineuse",
  son="déclic de l'obturateur, souffle",
  prompt=P("A single continuous cinematic shot: a phone camera fires, and a ring of light expands across the wet siding.",
    "[Shot 1] @etienne holds the phone steady at arm's length toward the new siding of @toit; a hard white shutter flash fires and a thin ring of ion-blue light bursts outward from the lens, races across the wet shingles of @toit and dies at the eave. His jacket sleeve lifts in the wind. The camera slides sideways, keeping him centred. Plain clothing with no logo, no text, no letters anywhere.",
    "A sharp camera shutter, a low electric thump, wind.")))
PLANS.append(dict(id="p04", sequence="S1", recette="h3-max", images=124, refs=["etienne", "toit"], premiere=None,
  beats=6, statut="RÉEL", camera="contre-plongée, la caméra monte avec l'objet",
  effets="la photo se détache de l'écran en volume, particules",
  son="bourdonnement qui monte, crépitement",
  prompt=P("A single continuous cinematic shot: a photograph lifts out of a phone screen and becomes a solid plate of light in the air.",
    "[Shot 1] @etienne lowers the phone; a small rectangle of pale light rises out of it, turns in the air above his open palm, thickens into a floating plate showing the siding of @toit in relief, then shoots upward past his shoulder into the dawn sky. Loose particles of light trail behind it. The camera tilts up and follows it. Plain clothing with no logo, no text, no letters anywhere.",
    "A rising electrical hum, fine crackle of particles, wind falling away.")))

PLANS.append(dict(id="p05", sequence="S2", recette="h3-fast", images=124, refs=[], premiere="k02",
  beats=4, statut="RÉEL", camera="travelling latéral rapide, très haute altitude",
  effets="fil de lumière, nuages qui défilent, flare",
  son="vent d'altitude, bourdonnement de signal",
  prompt=P("A single continuous cinematic shot that begins from the key frame: a thread of light crosses a dawn sky between a tower and a dish.",
    "[Shot 1] The shot begins from the first frame. High above a layer of low cloud, a thin thread of ion-blue light snaps taut between the lattice tower on the left and the white dish on the right, then runs on toward the horizon, pulsing once as it goes. Cloud shadows slide underneath. The camera tracks fast and level, chasing the thread. No text, no logos.",
    "High-altitude wind, a clean electrical tone, the deep silence above clouds.")))
PLANS.append(dict(id="p06", sequence="S2", recette="h3-fast", images=124, refs=[], premiere="k03",
  beats=4, statut="RÉEL", camera="rasante à hauteur de câble, avant",
  effets="impulsion bleue courant sur les câbles, givre",
  son="vent dans les fils, claquement de câble",
  prompt=P("A single continuous cinematic shot that begins from the key frame: a pulse of light races along hydro cables over a frozen country road.",
    "[Shot 1] The shot begins from the first frame. At cable height, a pulse of ion-blue light runs along the sagging cables from pole to pole, throwing a brief cold flash on the frost and the grass below, and disappears toward a small industrial building at the end of the road. The camera flies forward just under the wires, the poles whipping past. No text, no logos.",
    "Wind humming in the wires, a cable clacking, the pulse buzzing past the lens.")))
PLANS.append(dict(id="p07", sequence="S2", recette="h3-max", images=124, refs=["serveur"], premiere="k04",
  beats=6, statut="RÉEL", camera="plan large, puis poussée vers la porte du local",
  effets="le signal entre dans le bâtiment, halo bleu",
  son="moteur de camionnette, gravier, bourdonnement",
  prompt=P("A single continuous cinematic shot: a pulse of light leaves the cables and dives into a small server room.",
    "[Shot 1] A pulse of ion-blue light drops from the overhead cables, threads down the wall of a small industrial building and slips under the door of @serveur. The camera follows it down the wall, then pushes through the doorway into the cold blue room: one dark steel rack, neat cables, small blue status lights, a single warm work lamp. No text, no logos, no readable screen anywhere.",
    "The pulse buzzing down the wall, a door seal hissing, then a low steady hum of fans.")))
PLANS.append(dict(id="p08", sequence="S3", recette="h3-max", images=124, refs=["serveur", "tour"], premiere=None,
  beats=6, statut="RÉEL", camera="contre-plongée verticale dans le rack",
  effets="la tour se déplie hors du rack, échelle impossible, poussière lumineuse",
  son="souffle grave, craquement métallique, chœur bas",
  prompt=P("A single continuous cinematic shot: a colossal office tower unfolds out of a single server rack.",
    "[Shot 1] Inside @serveur, the blue status lights of the rack brighten in sequence from bottom to top, and out of the rack's dark glass a vast structure pushes forward and upward: @tour, ten floors of dark glass and ion-blue light, each floor an open office in cross-section, desks and silhouetted workers visible, thin vertical fins between floors, one warm orange light burning at the very top. The room around it stays real and small, dust turning in the lamp. The camera tilts up hard, dwarfed. No text, no logos, no readable screen.",
    "A deep rising rumble, metal ticking as it cools, a low choral tone underneath.")))
PLANS.append(dict(id="p09", sequence="S3", recette="h3-max", images=124, refs=["tour"], premiere=None,
  beats=4, statut="RÉEL", camera="travelling vertical ascendant le long de la façade",
  effets="chaque étage s'allume au passage, reflets",
  son="relais qui claquent, électricité",
  prompt=P("A single continuous cinematic shot: a camera climbs the facade of a ten-floor virtual tower as the floors light up.",
    "[Shot 1] The camera rises fast along the facade of @tour. As it passes each floor, the floor lights up from the inside: rows of desks, silhouetted workers leaning over plans, a hand raising, a screen glow, all seen through the glass and never readable. The vertical fins throw long blue reflections. At the top floor the warm orange light pulses once. No text, no logos, no readable screen anywhere.",
    "Electrical relays snapping one after another, a rising hum, glass ticking in the wind.")))
PLANS.append(dict(id="p10", sequence="S3", recette="h3-max", images=124, refs=["tour"], premiere=None,
  beats=4, statut="RÉEL", camera="plan large fixe, la tour occupe tout le cadre",
  effets="le toit s'ouvre, la lumière orange monte",
  son="grondement, souffle",
  prompt=P("A single continuous cinematic shot: the roof of the tower opens and a column of warm light rises out of it.",
    "[Shot 1] Seen from a distance, @tour fills the frame above a sea of cloud. The top floor's warm orange light swells, the roof panels iris open, and a slow column of amber light rises straight up into the dawn sky, carrying fine dust and a few sheets of paper that turn and climb. The camera holds steady, small against the scale. No text, no logos, no readable screen.",
    "A deep ground-shaking swell, paper fluttering, a long breath of air.")))

PLANS.append(dict(id="p11", sequence="S4", recette="h3-max", images=124, refs=["tour"], premiere="k09",
  beats=4, statut="RÉEL", camera="plan taille dans un étage, caméra portée",
  effets="dossiers qui s'assemblent en l'air, lumière de fenêtre",
  son="clavier, papier, rumeur de bureau",
  prompt=P("A single continuous cinematic shot: inside a virtual office floor, documents assemble themselves in mid-air above a desk.",
    "[Shot 1] Inside one floor of @tour: a wide open office of dark desks and glass, silhouetted workers moving between them. Above one empty desk, sheets of light lift and lock together into a neat stack, edges glowing ion-blue, then a second stack forms beside it. A worker in silhouette walks through the frame and the sheets part around him without breaking. The camera tracks sideways at chest height. No text, no logos, no readable screen, no readable writing on the sheets.",
    "Office murmur, keys, paper sliding, a soft electrical shimmer.")))
PLANS.append(dict(id="p12", sequence="S4", recette="h3-max", images=124, refs=["morin", "bureau"], premiere=None,
  beats=8, statut="RÉEL", camera="plan moyen, lente poussée avant",
  effets="poussière dans la lumière, reflet orange",
  son="horloge, pluie fine sur la fenêtre",
  prompt=P("A single continuous cinematic shot: a business owner in his office looks up as light gathers on the wall behind him.",
    "[Shot 1] @morin sits at the worn wooden desk of @bureau, glasses pushed up on his forehead, a pencil in his hand over a rolled plan. Behind him, on the plain wall, a rectangle of blue-white light gathers and sharpens. He turns his head toward it, not startled, just tired and curious. The camera pushes in slowly past his shoulder. Plain clothing with no logo, no text, no letters anywhere.",
    "A wall clock, fine rain on the window, the pencil tapping once.")))
PLANS.append(dict(id="p13", sequence="S4", recette="h3-max", images=158, refs=["adjointe", "morin"], premiere=None,
  parole="l02", beats=13, statut="VISION", camera="plan poitrine sur Morin, l'adjointe en amorce lumineuse à droite",
  effets="l'adjointe se matérialise par balayage, onde vocale",
  son="bureau, pluie",
  prompt=P("A single continuous cinematic shot: a business owner listens as a figure of light speaks to him, lips synchronised with <Audio 1>.",
    "[Shot 1] Medium close-up on @morin at his desk, turned three-quarters toward the right of frame. At the right edge, @adjointe stands as a translucent figure of fine blue-white points of light, a plain light-grey blazer and a thin headset readable, her face clearly human, an orange rim light along one cheek. She speaks; he listens, eyebrows lifting, then a short nod. The camera holds a slow push-in on his face. Plain clothing with no logo, no text, no letters anywhere.",
    "Room tone, rain on glass, a chair creaking.",
    dialogue="@adjointe " + VQ + ".")))
PLANS.append(dict(id="p14", sequence="S4", recette="h3-fast", images=124, refs=[], premiere="k04",
  beats=4, statut="RÉEL", camera="plan large, caméra fixe au sol",
  effets="traînée de lumière sur l'asphalte mouillé",
  son="moteur, gravier",
  prompt=P("A single continuous cinematic shot that begins from the key frame: a plain white cargo van pulls out of a driveway at dawn.",
    "[Shot 1] The shot begins from the first frame. A plain white cargo van rolls out of a suburban driveway onto a wet street, headlights on, a thin trail of ion-blue light drawn in the air ahead of it like a wire pulled tight. Water sprays from the tires. The camera holds low at the curb and lets the van cross the frame. No text, no logos, no readable plate.",
    "A cold engine, gravel, water under the tires.")))
PLANS.append(dict(id="p15", sequence="S5", recette="h3-max", images=158, refs=["tour", "avatar"], premiere=None,
  parole="l03", beats=13, statut="EN PRÉPARATION", camera="plan poitrine, l'avatar au centre, la ville virtuelle derrière",
  effets="l'avatar s'assemble à partir de points, courbe de lumière derrière",
  son="bourdonnement doux, battement",
  prompt=P("A single continuous cinematic shot: a holographic bust of light forms in a virtual office and speaks, lips synchronised with <Audio 1>.",
    "[Shot 1] In the open space of one floor of @tour, with the city of glass behind, thousands of fine blue-white points stream together and lock into @avatar, a humanoid bust of light with a calm readable face and a deep orange glow in one eye. Behind it, a wide dark window shows the cloud sea. It speaks to camera, unhurried, one small tilt of the head; a curve of pale light traces itself in the air beside it, rising to the right. The camera pushes in slowly. No text, no logos, no readable numbers anywhere.",
    "A soft electrical shimmer, a slow pulse, glass ticking.",
    dialogue="@avatar " + VQ + ".")))
PLANS.append(dict(id="p16", sequence="S5", recette="h3-max", images=124, refs=["avatar", "tour"], premiere=None,
  beats=4, statut="EN PRÉPARATION", camera="plan large, la caméra recule",
  effets="grille de cédule qui se dessine en volume",
  son="clics réguliers, souffle",
  prompt=P("A single continuous cinematic shot: a grid of light draws itself in the air in front of a holographic figure.",
    "[Shot 1] @avatar turns slightly and lifts one hand; in the air in front of it a wide grid of thin blue lines draws itself row by row, then blocks of pale light drop into the cells one after another, each block settling with a small pulse. The grid turns slowly in space, throwing faint light on the glass floor of @tour. The camera pulls back to take in the whole grid. No text, no logos, no readable letters or numbers anywhere.",
    "Even mechanical clicks, a soft airy swell, a low hum.")))

PLANS.append(dict(id="p17", sequence="S6", recette="h3-fast", images=124, refs=[], premiere="k06",
  beats=4, statut="EN PRÉPARATION", camera="plan large, caméra fixe, léger vent latéral",
  effets="porte de lumière qui s'ouvre, neige soulevée",
  son="vent d'hiver, pas dans la neige",
  prompt=P("A single continuous cinematic shot that begins from the key frame: a worker walks through a gate of light at a winter job site.",
    "[Shot 1] The shot begins from the first frame. At a construction site trailer in blue winter dawn, a worker in a plain dark parka walks toward a tall rectangle of thin blue light standing open in the air; as he passes through it, the light flares, snow lifts off the ground in a ring, and the rectangle closes behind him. The camera holds steady at ground level. Plain clothing with no logo, no text, no letters anywhere.",
    "Wind, snow crunching, a short electrical flare.")))
PLANS.append(dict(id="p18", sequence="S6", recette="h3-max", images=124, refs=["avatar"], premiere=None,
  beats=8, statut="VISION", camera="plan poitrine serré, l'avatar de trois quarts",
  effets="heure de pointage en lumière, particules",
  son="bip, bourdonnement",
  prompt=P("A single continuous cinematic shot: a holographic bust of light speaks to camera inside a virtual office, lips synchronised with <Audio 1>.",
    "[Shot 1] Close on @avatar, three-quarters, the orange glow in one eye flaring slightly as it speaks. Behind it, a wall of blue light scrolls slowly upward. It lifts its chin at the end of the line and holds the look. The camera pushes in a few centimetres. No text, no logos, no readable numbers anywhere.",
    "A single clean beep, a low hum, glass ticking.",
    dialogue="@avatar " + VQ + ".")))
PLANS.append(dict(id="p19", sequence="S6", recette="h3-fast", images=124, refs=[], premiere="k07",
  beats=4, statut="VISION", camera="plan serré sur un mur de lumière, caméra fixe",
  effets="un rectangle de papier lumineux se détache du mur",
  son="papier, souffle",
  prompt=P("A single continuous cinematic shot: a sheet of luminous paper peels off a wall of blue light and floats forward.",
    "[Shot 1] A wall of fine blue light, slightly curved, fills the frame. One rectangle of it thickens, peels away from the surface with a soft tearing sound, and floats toward the lens, edges glowing warm orange, surface blank and bright. The camera holds and lets it fill the frame, then it passes the lens. No text, no logos, no readable letters or numbers anywhere.",
    "Paper tearing softly, a warm hum, air moving.")))
PLANS.append(dict(id="p20", sequence="S6", recette="h3-max", images=124, refs=["morin", "bureau"], premiere=None,
  beats=6, statut="RÉEL", camera="plan large du bureau, la caméra recule vers la fenêtre",
  effets="la pile de documents lumineux se pose sur le bureau",
  son="horloge, papier",
  prompt=P("A single continuous cinematic shot: a stack of luminous documents settles onto a wooden desk in front of a business owner.",
    "[Shot 1] @morin looks up as a stack of glowing sheets floats down through the air of @bureau and settles onto his desk with a soft weight, edges pulsing once. He reaches out, hesitates, then puts two fingers on the top sheet. The lamp flickers warm. The camera pulls back slowly toward the window. Plain clothing with no logo, no text, no letters anywhere.",
    "The clock, paper settling, a lamp buzzing.")))
PLANS.append(dict(id="p21", sequence="S7", recette="h3-max", images=124, refs=["morin", "bureau"], premiere=None,
  parole="l05", beats=8, statut="RÉEL", camera="gros plan, axe direct, très légère plongée",
  effets="aucun : visage, peau, lumière",
  son="silence de bureau, pluie",
  prompt=P("A single continuous cinematic shot: a business owner speaks straight to camera, lips synchronised with <Audio 1>.",
    "[Shot 1] Tight on the face of @morin at the desk of @bureau, glasses still up on his forehead, the warm lamp on one cheek and cold window light on the other. He looks straight into the lens and asks his question, jaw set, a small shrug at the end. Behind him the office is dark and quiet. The camera holds, breathing slightly. Plain clothing with no logo, no text, no letters anywhere.",
    "Room tone, a chair creak, rain.",
    dialogue="@morin " + VQ + ".")))

PLANS.append(dict(id="p22", sequence="S7", recette="h3-max", images=124, refs=["avatar", "tour"], premiere=None,
  parole="l06", beats=8, statut="VISION", camera="plan poitrine, contre-champ, la ville derrière",
  effets="le buste se reforme, éclats de lumière",
  son="bourdonnement, battement grave",
  prompt=P("A single continuous cinematic shot: a holographic bust of light answers to camera, lips synchronised with <Audio 1>.",
    "[Shot 1] @avatar reforms in the dark of a floor of @tour, points of light rushing inward and locking into the face, the orange glow in one eye steady. It speaks to camera in three short blocks, no gesture, no smile. Behind it the cloud sea turns slowly from blue to amber. The camera is locked off, a slow drift only. No text, no logos, no readable numbers anywhere.",
    "A low hum, a single deep pulse on each block of speech.",
    dialogue="@avatar " + VQ + ".")))
PLANS.append(dict(id="p23", sequence="S7", recette="h3-max", images=124, refs=["morin", "bureau"], premiere=None,
  parole="l07", beats=6, statut="RÉEL", camera="gros plan main + visage, caméra fixe",
  effets="un tampon de lumière orange se pose sur la feuille",
  son="papier, tampon",
  prompt=P("A single continuous cinematic shot: a business owner presses two fingers on a glowing document and a seal of light appears.",
    "[Shot 1] In @bureau, @morin looks at the glowing stack, says one word under his breath, then brings his weathered hand down flat on the top sheet; under his fingers a ring of warm orange light spreads across the paper and settles into a solid disc, then fades to a thin outline. He exhales and sits back. The camera holds tight on his hand and the lower half of his face. Plain clothing with no logo, no text, no letters anywhere.",
    "Paper under a hand, a soft thump, a long exhale.",
    dialogue="@morin " + VQ + ".")))
PLANS.append(dict(id="p24", sequence="S8", recette="h3-max", images=124, refs=["tour"], premiere=None,
  beats=4, statut="RÉEL", camera="travelling latéral le long de la façade, puis arrêt",
  effets="les dix étages s'éteignent un à un vers le haut",
  son="relais, électricité qui s'éteint",
  prompt=P("A single continuous cinematic shot: the floors of a colossal tower go dark one after another, bottom to top.",
    "[Shot 1] Along the facade of @tour, the office floors switch off one by one from the bottom up, each going from ion-blue to deep black with a small relay snap, leaving only the top floor's warm orange light. The camera tracks sideways and then stops, the dark tower filling the frame against a pale dawn. No text, no logos, no readable screen.",
    "Relays snapping in sequence, a hum powering down, wind.")))
PLANS.append(dict(id="p25", sequence="S8", recette="h3-max", images=124, refs=["morin", "bureau"], premiere=None,
  beats=6, statut="RÉEL", camera="plan large depuis l'extérieur, à travers la fenêtre",
  effets="la lumière orange de la tour se reflète dans la vitre",
  son="rue calme, pluie fine",
  prompt=P("A single continuous cinematic shot: seen through an office window, a business owner stands up and turns off his lamp.",
    "[Shot 1] From the street, through the wet window of @bureau, @morin stands, stretches his back, and clicks off the desk lamp; the office falls into blue dusk. In the glass, the reflection of a distant tower with one warm orange light at the top lines up exactly over his shoulder. He picks up his coat. The camera holds, rain running down the pane. Plain clothing with no logo, no text, no letters anywhere.",
    "Quiet street, fine rain on glass, a lamp switch.")))
PLANS.append(dict(id="p26", sequence="S8", recette="h3-max", images=124, refs=["etienne", "toit"], premiere="k05",
  beats=4, statut="RÉEL", camera="orbite lente autour de la maison",
  effets="rig de lumière, pétales de lumière, golden hour",
  son="vent doux, oiseaux",
  prompt=P("A single continuous cinematic shot that begins from the key frame: a rig of light orbits a finished house at golden hour.",
    "[Shot 1] The shot begins from the first frame. Around the finished exterior of @toit, a house with new pale grey siding and dark soffit-fascia, a thin rig of blue-white light circles the roof once, and @etienne stands small at the foot of the ladder, shedding small petals of light that drift down and dissolve before they touch the lawn. The camera orbits with it, low, the long shadows sliding. No text, no logos, no readable sign.",
    "Soft wind, birds, a low warm hum.")))
PLANS.append(dict(id="p27", sequence="S9", recette="h3-max", images=124, refs=["etienne"], premiere=None,
  parole="l09", beats=8, statut="RÉEL", camera="plan poitrine, l'homme assis sur le hayon",
  effets="halo doux, poussière dans la lumière",
  son="camionnette qui refroidit, oiseaux",
  prompt=P("A single continuous cinematic shot: a representative sitting on a van tailgate speaks to camera, lips synchronised with <Audio 1>.",
    "[Shot 1] @etienne sits on the tailgate of a plain white van at golden hour, cap pushed back, phone in one hand, the finished house soft behind him. He speaks to camera with a tired smile, then looks down at the phone and taps once. The camera holds a slow push-in. Plain clothing with no logo, no text, no letters anywhere.",
    "A cooling engine ticking, birds, a light breeze.",
    dialogue="@etienne " + VQ + ".")))
PLANS.append(dict(id="p28", sequence="S9", recette="h3-max", images=124, refs=["adjointe", "morin"], premiere=None,
  parole="l08", beats=10, statut="VISION", camera="plan poitrine de l'adjointe, Morin flou en amorce",
  effets="l'adjointe se reforme, la pièce s'assombrit autour d'elle",
  son="bourdonnement doux",
  prompt=P("A single continuous cinematic shot: a figure of light speaks to camera in a dark office, lips synchronised with <Audio 1>.",
    "[Shot 1] In the dark of @bureau, @adjointe stands as a translucent figure of blue-white points of light, her plain light-grey blazer and thin headset readable, orange rim light on one cheek; @morin is a soft blurred shape in the left foreground, his shoulder in frame. She speaks to camera in three blocks, calm, and on the last word she looks directly into the lens. The camera pushes in slowly. Plain clothing with no logo, no text, no letters anywhere.",
    "A soft electrical shimmer, a low warm tone, silence behind.",
    dialogue="@adjointe " + VQ + ".")))

PLANS.append(dict(id="p29", sequence="S9", recette="h3-max", images=158, refs=["etienne"], premiere=None,
  beats=6, statut="RÉEL", camera="gros plan sur le téléphone puis sur le visage",
  effets="la lumière remonte l'écran, halo",
  son="camionnette, oiseaux",
  prompt=P("A single continuous cinematic shot: a phone lights up in a man's hand and he smiles at it.",
    "[Shot 1] Close on @etienne's hand holding a plain dark phone at golden hour; the screen, kept blank and out of focus, blooms with warm light that spills onto his fingers and up his jaw. He reads, exhales through his nose, and a real smile arrives. He tilts the phone slightly toward the finished house behind him. The camera holds tight, then racks focus to his eyes. Plain clothing with no logo, no text, no letters anywhere, no readable screen.",
    "A cooling engine, birds, a soft notification chime, a breath.")))
PLANS.append(dict(id="p30", sequence="S9", recette="h3-max", images=175, refs=["tour", "bureau"], premiere=None,
  beats=8, statut="RÉEL", camera="la caméra perce le plafond du dixième et découvre l'étage au-dessus",
  effets="le toit s'ouvre, un vrai bureau apparaît posé sur la tour",
  son="souffle, craquement, puis silence chaud",
  prompt=P("A single continuous cinematic shot: the camera rises through the roof of a virtual tower and finds a small real office sitting on top of it.",
    "[Shot 1] The camera climbs the inside of @tour past the tenth floor, breaks through the roof into open sky, and keeps rising until a small, warm, ordinary office appears, sitting alone on the flat roof: @bureau, seen from outside through its window, wooden desk, rolled plans, a coffee mug, a child's drawing pinned to the wall, one warm lamp. The vast dark tower stretches below it. The camera arcs around the little room, the cloud sea turning gold. No text, no logos, no readable screen, no readable writing on the drawing.",
    "A rush of air, then the small sounds of a real room: a clock, a chair, a lamp.")))
PLANS.append(dict(id="p31", sequence="S9", recette="h3-max", images=175, refs=["tour", "bureau"], premiere=None,
  beats=8, statut="RÉEL", camera="très grand large, recul vertical continu",
  effets="la tour entière, dix étages bleus, un étage orange, la ville réelle en bas",
  son="nappe grave, vent",
  prompt=P("A single continuous cinematic shot: a colossal tower of ten blue floors with one small warm office on top, seen from very far away.",
    "[Shot 1] The camera pulls back and up, revealing @tour in full: ten floors of dark glass and ion-blue light stacked above a layer of cloud, and on the very top, small and bright and stubborn, the warm orange window of @bureau. Below the clouds, faint and real, the grid of a small Québec suburb at dusk. The camera keeps retreating until the tower is one bright vertical line in the sky. No text, no logos, no readable sign.",
    "A wide low chord of air, wind at altitude, one distant car.")))
PLANS.append(dict(id="p32", sequence="S9", recette="h3-fast", images=124, refs=[], premiere="k08",
  beats=6, statut="RÉEL", camera="plan fixe, léger flottement",
  effets="ciel d'aube pur, une seule ligne de lumière",
  son="vent très doux, silence",
  prompt=P("A single continuous cinematic shot: an empty dawn sky with one thin vertical line of light fading upward.",
    "[Shot 1] A clean dawn sky, deep blue at the top fading to pale amber at the horizon, a thin band of cloud. One fine vertical line of ion-blue light stands in the middle of the frame, fades slowly to a warm orange at its tip, then dissolves upward into the sky. Nothing else moves. No text, no logos.",
    "Very soft wind, a long fading tone, silence.")))

# ---------- ordre de montage ----------
ORDRE = ["p01","p02","p03","p04","p05","p06","p07","p08","p09","p10","p11","p12","p13","p14",
         "p15","p16","p17","p18","p19","p20","p21","p22","p23","p24","p25","p26","p27","p29",
         "p30","p31","p28","p32"]
PLANS.sort(key=lambda p: ORDRE.index(p["id"]))
byid = {p["id"]: p for p in PLANS}
for p in PLANS:
    p["premiere"] = p.get("premiere") or None
byid["p07"]["premiere"] = "k10"

CPS = {"drama3-adamqc": 19.5, "drama3-frederic": 16.5, "eleven-jeannemance": 21.5,
       "drama3-jeannemance": 19.1}
def duree_replique(r):
    return len(r["texte"]) / CPS[r["voix"]] / float(r["vitesse"]) + 0.35

REP = {r["id"]: r for r in REPLIQUES}

# un plan parlant doit contenir sa réplique : on allonge sur la grille des temps
for p in PLANS:
    if p.get("parole"):
        d = duree_replique(REP[p["parole"]])
        need = math.ceil((d + 0.55) / BEAT)
        p["beats"] = max(p["beats"], need)
    p["duree_f"] = B(p["beats"])
    # la duree a l'ecran ne peut pas depasser la longueur rendue
    while p["duree_f"] > p["images"]:
        p["images"] = rendu(p["duree_f"])
    assert p["duree_f"] <= p["images"], p["id"]

debuts, cur = {}, 0
for p in PLANS:
    debuts[p["id"]] = cur
    cur += p["duree_f"]
TOTAL = cur
print("total", TOTAL, TOTAL / FPS, "s ; beats", sum(p["beats"] for p in PLANS))
print("unites 16:9", sum(1 if p["images"] <= 124 else 2 for p in PLANS))

# ---------- corrections de distribution (cédule sur p16, paye sur p18) ----------
REPLIQUES.append({"id": "l10", "role": "Avatar paye (M5)", "voix": "drama3-jeannemance", "vitesse": 1.12, "prises": 2,
  "texte": "Pointage reçu. Le chèque de paye est prêt.",
  "direction": "Même autorité sèche, deux blocs. Le deuxième bloc plus bas, comme une confirmation administrative."})
REP = {r["id"]: r for r in REPLIQUES}
byid["p16"]["parole"] = "l04"
byid["p16"]["prompt"] = P("A single continuous cinematic shot: a holographic bust of light speaks and a wide grid of light draws itself in the air, lips synchronised with <Audio 1>.",
  "[Shot 1] @avatar turns slightly and lifts one hand; in the air in front of it a wide grid of thin blue lines draws itself row by row, then blocks of pale light drop into the cells one after another, each settling with a small pulse. It speaks to camera, then drops its hand. The grid turns slowly in space, throwing faint light on the glass floor of @tour. The camera pulls back to take in the whole grid. No text, no logos, no readable letters or numbers anywhere.",
  "Even mechanical clicks, a soft airy swell, a low hum.",
  dialogue="@avatar " + VQ + ".")
byid["p18"]["parole"] = "l10"
byid["p18"]["prompt"] = P("A single continuous cinematic shot: a holographic bust of light speaks to camera inside a virtual office, lips synchronised with <Audio 1>.",
  "[Shot 1] Close on @avatar, three-quarters, the orange glow in one eye flaring slightly as it speaks. Behind it, a wall of blue light scrolls slowly upward and a blank luminous slip of paper slides out of it and hangs in the air. It lifts its chin at the end of the line and holds the look. The camera pushes in a few centimetres. No text, no logos, no readable numbers anywhere.",
  "A single clean beep, a low hum, glass ticking.",
  dialogue="@avatar " + VQ + ".")

# ---------- table de montage : temps (1 temps = 11,61 images) et longueur de rendu ----------
BEATS = {"p01":12,"p02":8,"p03":5,"p04":7,"p05":8,"p06":7,"p07":11,"p08":18,"p09":11,"p10":9,
         "p11":10,"p12":10,"p13":9,"p14":6,"p15":13,"p16":8,"p17":7,"p18":8,"p19":5,"p20":8,
         "p21":6,"p22":8,"p23":4,"p24":10,"p25":11,"p26":10,"p27":9,"p29":7,"p30":20,"p31":18,
         "p28":8,"p32":9}
IMAGES = {"p01":141,"p07":141,"p08":209,"p09":141,"p15":158,"p25":141,"p30":243,"p31":209}
for p in PLANS:
    p["beats"] = BEATS[p["id"]]
    p["images"] = IMAGES.get(p["id"], 124)
    p["duree_f"] = B(p["beats"])
    if p.get("parole"):
        besoin = math.ceil((duree_replique(REP[p["parole"]]) + 0.5) / BEAT)
        assert p["beats"] >= besoin, (p["id"], besoin, p["beats"])
    assert p["duree_f"] <= p["images"], (p["id"], p["duree_f"], p["images"])

debuts, cur = {}, 0
for p in PLANS:
    debuts[p["id"]] = cur
    cur += p["duree_f"]
TOTAL = cur
u169 = sum(1 if p["images"] <= 124 else 2 for p in PLANS if p.get("format","16:9") != "9:16")
print("plans", len(PLANS), "total", TOTAL, "images =", round(TOTAL / FPS, 1), "s | unites 16:9", u169)

# ---------- EditPlan ----------
TRANS = {"p08": ("dip", 12), "p15": ("fondu", 8), "p24": ("dip", 10), "p30": ("fondu", 10),
         "p05": ("glisse", 6), "p20": ("fondu", 6), "p26": ("fondu", 8), "p31": ("fondu", 10),
         "p28": ("fondu", 8), "p13": ("fondu", 6), "p22": ("fondu", 6), "p02": ("fondu", 4),
         "p17": ("glisse", 6), "p11": ("fondu", 6), "p18": ("fondu", 4), "p21": ("fondu", 4)}

def timeline(ids, durees, trans):
    deb, cur = [], 0
    for i, pid in enumerate(ids):
        rec = 0
        if i:
            t = trans.get(pid)
            if t:
                rec = t[1]
        cur -= rec
        deb.append(cur)
        cur += durees[pid]
    return deb, cur

def plan_video(pid, ids_ordre, trans):
    t = trans.get(pid)
    d = dict(id=pid, src=pid, entree_f=0, duree_f=byid[pid]["duree_f"], vitesse=1)
    if t:
        d["transition_in"] = {"type": t[0], "duree_f": t[1]}
    else:
        d["transition_in"] = {"type": "cut", "duree_f": 0}
    return d

ORDRE_LONG = [p["id"] for p in PLANS]
DUR = {p["id"]: p["duree_f"] for p in PLANS}
DEB_LONG, T_LONG = timeline(ORDRE_LONG, DUR, TRANS)
print("long:", T_LONG, round(T_LONG / FPS, 1), "s")

MUSIQUE = {"bpm_vise": 124, "duree_s": 150,
 "prompt": ("Instrumental only, no vocals, no voice, no choir words. Driving cinematic electronic score for a technology commercial, "
   "124 BPM, key of D minor with a bright lift to F major in the last third. Structure in seconds: 0-15 a low pulsing sub bass and a "
   "tight closed hi-hat, one note of hope on a felt piano; 15-38 add a syncopated analogue bassline and hand claps, energy climbing, "
   "no melody yet; 38-62 the main four-note motif enters on a warm analogue synth, wide stereo, with a rising filtered arpeggio "
   "underneath; 62-80 a short breath, drums drop out for two bars, one sustained string pad; 80-112 full drop: big live-sounding "
   "drums, the motif doubled by pizzicato strings, sidechain pump, a tambourine on the backbeat, energy maximum, triumphant but "
   "clean and modern, never aggressive; 112-134 the drums pull back to a half-time groove, the motif played on celesta and piano, "
   "warm and human; 134-150 a final build and one last full chord, then a clean stop with a short warm tail. Production: punchy "
   "modern mix, wide but not washy, analogue warmth, no riser clichés longer than one bar, no dark or sad colours, no lo-fi, "
   "no distortion, no vocals. Uplifting, confident, propulsive, cinematic."),
 "coups": []}

def coup(t, ev):
    MUSIQUE["coups"].append({"t_s": round(t, 2), "evenement": ev})

COUPS = [
 (0.0, "noir, la première pulsation : le point orange du logo de signal s'allume"),
 (4.84, "la photo est prise (éclair de flash)"),
 (9.68, "la photo se détache du téléphone et monte"),
 (13.55, "le signal quitte le toit, coupe vers le ciel"),
 (17.42, "le fil de lumière se tend entre la tour et l'antenne"),
 (23.23, "la tour s'ouvre hors du rack : impact grave"),
 (32.03, "premier étage allumé, travelling vertical"),
 (39.68, "la tour entière, colonne de lumière orange"),
 (48.39, "l'adjointe apparaît, la voix entre"),
 (58.06, "la cédule se dessine, clics"),
 (70.65, "l'avatar comptable apparaît, la voix entre"),
 (78.87, "le pointage, bip"),
 (88.55, "la question de Morin : cassure, batterie qui tombe"),
 (96.77, "l'avatar répond, trois blocs"),
 (105.48, "le tampon orange : impact"),
 (113.23, "les étages s'éteignent un à un, relais"),
 (123.39, "le bureau réel posé sur la tour : lever, plein"),
 (133.55, "la tour entière vue de loin, apothéose"),
 (140.32, "carton final, coup final"),
]
for t, e in COUPS:
    coup(t, e)

def fmt_pts(n):
    return round(n, 1)

def build_plan(version, ids, durees, trans, fmt="16:9"):
    deb, total = timeline(ids, durees, trans)
    video = [plan_video(pid, ids, trans) for pid in ids]
    voix = []
    for i, pid in enumerate(ids):
        pid_parole = byid[pid].get("parole")
        if pid_parole:
            d = fr(duree_replique(REP[pid_parole]))
            voix.append({"src": pid_parole, "debut_f": deb[i] + 8, "entree_f": 0, "duree_f": d, "gain_db": 0})
    sources = {}
    for pid in ids:
        sources[pid] = {"kind": "video", "duree_f": byid[pid]["images"]}
    for v in voix:
        sources[v["src"]] = {"kind": "audio", "duree_f": v["duree_f"]}
    sources["m01"] = {"kind": "audio", "duree_f": total}
    P = {"version": 1, "fps": 24, "format": fmt, "genre": "pub",
         "titre": "OPSYS-AI · Le Onzième Étage",
         "sources": sources, "video": video,
         "audio": {"musique": {"src": "m01", "entree_f": 0, "duree_f": total, "gain_db": -9,
                              "fondu_in_f": 12, "fondu_out_f": 30},
                   "voix": voix,
                   "ducking": {"actif": True, "profondeur_db": 11},
                   "cible_lufs": -14, "crete_db": -1.5, "fondu_coupe_ms": 40},
         "textes": [], "generations": []}
    return P, deb, total

LONG, DEB_LONG, T_LONG = build_plan("long", ORDRE_LONG, DUR, TRANS)
print("LONG", T_LONG, T_LONG / FPS)

SD = {pid: DEB_LONG[i] for i, pid in enumerate(ORDRE_LONG)}
def s(pid, extra=0):
    return SD[pid] + extra

INC = []
def inc(**k):
    INC.append(k)

# S1
inc(type="statut", debut_f=s("p01")+6, duree_f=90, position="bas-gauche", texte="Photo reçue. Mesures en cours…")
inc(type="surtitre", debut_f=s("p01")+10, duree_f=78, position="haut-gauche", texte="M3 · ESTIMATION")
inc(type="document", debut_f=s("p04")+10, duree_f=100, position="droite",
    titre="SOUMISSION", destinataire="Monsieur Thibault · Toit, revêtement",
    lignes=[["Revêtement", "4 210 pi²"], ["Soffite-fascia", "62 pi"], ["Main-d'œuvre", "3 jours"],
            ["Préparation", "incluse"], ["Total", "18 940 $"]],
    total="18 940 $", tampon=None)
# S2
inc(type="trajet", debut_f=s("p05")+4, duree_f=70, position="centre",
    points=[[0.08, 0.62], [0.34, 0.31], [0.61, 0.44], [0.88, 0.22]], couleur="ion")
inc(type="surtitre", debut_f=s("p05")+8, duree_f=60, position="haut-droite", texte="SIGNAL · EN TRANSIT")
inc(type="trajet", debut_f=s("p06")+2, duree_f=80, position="centre",
    points=[[0.02, 0.55], [0.28, 0.5], [0.55, 0.58], [0.8, 0.47], [0.99, 0.52]], couleur="signal")
# S3
inc(type="surtitre", debut_f=s("p08")+8, duree_f=96, position="haut-gauche", texte="OPSYS-AI · DIX DÉPARTEMENTS")
inc(type="pile", debut_f=s("p09")+6, duree_f=104, position="gauche",
    lignes=["M1 Réception", "M2 CRM", "M3 Estimation", "M4 Terrain", "M5 Finance"])
inc(type="pile", debut_f=s("p10")+6, duree_f=96, position="droite",
    lignes=["M6 Matériel", "M7 Marketing", "M8 Analytique", "M9 Stratégie", "M10 Mémoire"])
# S4
inc(type="surtitre", debut_f=s("p11")+4, duree_f=84, position="haut-gauche", texte="M3 · SOUMISSION REVUE")
inc(type="statut", debut_f=s("p12")+8, duree_f=110, position="bas-gauche", texte="11 critères vérifiés. Prête à approuver.")
inc(type="etiquette", debut_f=s("p13")+4, duree_f=100, position="haut-droite", texte="VISION")
inc(type="appel", debut_f=s("p13")+12, duree_f=110, position="bas-droite",
    nom="L'adjointe · M1", sous_titre="Appel interne", voix="l02")
inc(type="surtitre", debut_f=s("p14")+2, duree_f=60, position="haut-gauche", texte="M4 · INTERVENTION")
# S5
inc(type="etiquette", debut_f=s("p15")+4, duree_f=110, position="haut-droite", texte="EN PRÉPARATION")
inc(type="courbe", debut_f=s("p15")+12, duree_f=126, position="droite",
    points=[62, 64, 63, 67, 70, 73, 76, 78, 81, 84], etiquette="PROFITS ANTICIPÉS · 26 SEMAINES",
    valeur="+7 %", pointille_depuis=5)
inc(type="surtitre", debut_f=s("p16")+4, duree_f=88, position="haut-gauche", texte="M4 · CÉDULE · 3 SEMAINES")
inc(type="cedule", debut_f=s("p16")+8, duree_f=88, position="droite", titre="CÉDULE",
    semaines=3, jours=["Lun", "Mar", "Mer", "Jeu", "Ven"],
    blocs=[[0,0,1,0,"Thibault · toit"],[0,2,3,1,"Gagnon · soffite"],[1,0,2,0,"Thibault · fin"],
           [1,3,4,1,"Leblanc · revêtement"],[2,0,1,0,"Morin · rénovation"],[2,2,4,1,"Gagnon · fascia"]])
# S6
inc(type="etiquette", debut_f=s("p17")+2, duree_f=90, position="haut-droite", texte="EN PRÉPARATION")
inc(type="pointage", debut_f=s("p18")+8, duree_f=92, position="bas-gauche", heure="07:02", nom="Étienne", etat="ARRIVÉE")
inc(type="etiquette", debut_f=s("p18")+2, duree_f=100, position="haut-droite", texte="VISION")
inc(type="statut", debut_f=s("p19")+2, duree_f=70, position="bas", texte="Chèque de paye · brouillon")
inc(type="etiquette", debut_f=s("p19")+2, duree_f=70, position="haut-droite", texte="VISION")
# S7
inc(type="impact", debut_f=s("p22")+4, duree_f=58, position="centre", texte="Mars.")
inc(type="surtitre", debut_f=s("p23")+2, duree_f=70, position="haut-gauche", texte="M5 · APPROBATION")
inc(type="statut", debut_f=s("p23")+30, duree_f=60, position="bas", texte="Approuvé. Dossier prêt pour le comptable.")
# S8
inc(type="statut", debut_f=s("p24")+8, duree_f=80, position="bas", texte="Journée terminée.")
inc(type="statut", debut_f=s("p25")+4, duree_f=96, position="bas-gauche", texte="18 h 30. La shop est fermée.")
inc(type="surtitre", debut_f=s("p26")+4, duree_f=90, position="haut-gauche", texte="M7 · CONTENUS PROPOSÉS")
inc(type="statut", debut_f=s("p27")+10, duree_f=90, position="bas", texte="Brouillon prêt. Approbation requise.")
# S9
inc(type="titre", debut_f=s("p30")+16, duree_f=100, position="bas", zone="bas",
    texte="Dix étages travaillent. Le onzième, c'est *vous*")
inc(type="titre", debut_f=s("p31")+30, duree_f=80, position="centre", zone="centre",
    texte="Une grande entreprise. À *votre* taille.")
inc(type="etiquette", debut_f=s("p28")+2, duree_f=100, position="haut-droite", texte="VISION")
inc(type="carton", debut_f=s("p32")+8, duree_f=90, position="centre")
print("incrustations", len(INC), "fin", s("p32")+30+140, "total", T_LONG)

INC[-1] = dict(type="carton", debut_f=s("p32")+2, duree_f=103, position="centre")

SFX = []
def sfx(t, f, db, d=None):
    e = {"type": t, "debut_f": f, "db": db}
    if d: e["duree_s"] = d
    SFX.append(e)

sfx("souffle", 0, -20, 2.0)
sfx("frappe", 4, -12)
sfx("clic", s("p03")+20, -6)
sfx("montee", s("p04")+6, -10, 1.4)
sfx("fouet", s("p05"), -8)
sfx("drone", s("p05")+2, -16, 4.0)
sfx("fouet", s("p07"), -8)
sfx("impact", s("p08")+14, -4)
sfx("boom", s("p08")+16, -8, 1.5)
sfx("montee", s("p09"), -12, 3.0)
sfx("impact", s("p10")+8, -6)
sfx("fouet", s("p11"), -9)
sfx("souffle", s("p13")+6, -14, 1.2)
sfx("fouet", s("p15"), -8)
sfx("impact", s("p16")+4, -9)
sfx("fouet", s("p17"), -9)
sfx("clic", s("p18")+10, -10)
sfx("fouet", s("p19"), -8)
sfx("frappe", s("p21")+30, -9)
sfx("chute", s("p22")+2, -7, 1.2)
sfx("impact", s("p23")+14, -3)
sfx("clic", s("p24"), -10)
sfx("chute", s("p25")+8, -12, 1.0)
sfx("souffle", s("p26"), -12, 1.6)
sfx("clic", s("p29")+16, -8)
sfx("montee", s("p30"), -9, 3.4)
sfx("impact", s("p31")+18, -5)
sfx("boom", s("p31")+20, -9, 2.0)
sfx("impact", s("p32")+2, -4)

SON_PLANS = [{"plan": pid, "db": db} for pid, db in [
 ("p01", -16), ("p03", -12), ("p05", -14), ("p06", -13), ("p07", -15), ("p08", -9),
 ("p11", -17), ("p12", -15), ("p14", -14), ("p17", -13), ("p20", -16), ("p23", -13),
 ("p24", -15), ("p25", -17), ("p26", -14), ("p29", -15), ("p30", -11), ("p31", -13)]]

ETAL = {"contraste": 1.08, "saturation": 0.94, "chaleur": 0.06, "grain": 1.15}
print("sfx", len(SFX), "son_plans", len(SON_PLANS))

# ---------- version courte 16:9 (13,6 s) : la soumission qui voyage par signal ----------
COURT = ["p01", "p03", "p05", "p07", "p08", "p10", "p26"]
CB = {"p01": 6, "p03": 3, "p05": 4, "p07": 4, "p08": 5, "p10": 3, "p26": 5}
CI = {"p01": 124, "p03": 124, "p05": 124, "p07": 124, "p08": 124, "p10": 124, "p26": 124}
CTR = {"p05": ("glisse", 4), "p08": ("dip", 8), "p10": ("fondu", 6), "p26": ("fondu", 6)}
CDUR = {k: B(v) for k, v in CB.items()}
CDEB, CT = timeline(COURT, CDUR, CTR)
print("court", CT, round(CT / FPS, 2), "s")

def build_court():
    video = []
    for i, pid in enumerate(COURT):
        d = dict(id=pid, src=pid, entree_f=0, duree_f=CDUR[pid], vitesse=1)
        t = CTR.get(pid)
        d["transition_in"] = {"type": t[0], "duree_f": t[1]} if t else {"type": "cut", "duree_f": 0}
        video.append(d)
    sources = {pid: {"kind": "video", "duree_f": CI[pid]} for pid in COURT}
    sources["m02"] = {"kind": "audio", "duree_f": CT}
    return {"version": 1, "fps": 24, "format": "16:9", "genre": "pub",
            "titre": "OPSYS-AI · Signal (13 s)",
            "sources": sources, "video": video,
            "audio": {"musique": {"src": "m02", "entree_f": 0, "duree_f": CT, "gain_db": -7,
                                 "fondu_in_f": 6, "fondu_out_f": 18},
                      "voix": [], "ducking": {"actif": True, "profondeur_db": 9},
                      "cible_lufs": -14, "crete_db": -1.5, "fondu_coupe_ms": 40},
            "textes": [], "generations": []}

COURT_PLAN = build_court()
CSD = {pid: CDEB[i] for i, pid in enumerate(COURT)}
CINC = [
 dict(type="surtitre", debut_f=CSD["p01"]+6, duree_f=60, position="haut-gauche", texte="M3 · ESTIMATION"),
 dict(type="statut", debut_f=CSD["p01"]+10, duree_f=62, position="bas-gauche", texte="Photo reçue."),
 dict(type="trajet", debut_f=CSD["p05"]+2, duree_f=54, position="centre",
      points=[[0.05, 0.6], [0.35, 0.3], [0.66, 0.45], [0.94, 0.2]], couleur="ion"),
 dict(type="surtitre", debut_f=CSD["p08"]+6, duree_f=62, position="haut-gauche", texte="OPSYS-AI · DIX DÉPARTEMENTS"),
 dict(type="titre", debut_f=CSD["p10"]+2, duree_f=54, position="bas", zone="bas",
      texte="Dix départements. Une *seule* équipe."),
 dict(type="statut", debut_f=CSD["p26"]+4, duree_f=40, position="bas", texte="Soumission prête. Approuver ?"),
 dict(type="carton", debut_f=CDEB[-1]+46, duree_f=CDUR["p26"] - 46, position="centre"),
]
CSFX = [
 dict(type="frappe", debut_f=0, db=-12),
 dict(type="clic", debut_f=CSD["p03"]+20, db=-6),
 dict(type="montee", debut_f=CSD["p01"]+8, db=-10, duree_s=1.0),
 dict(type="fouet", debut_f=CSD["p05"], db=-8),
 dict(type="impact", debut_f=CSD["p08"]+14, db=-4),
 dict(type="boom", debut_f=CSD["p08"]+16, db=-8, duree_s=1.2),
 dict(type="impact", debut_f=CSD["p10"]+4, db=-6),
 dict(type="impact", debut_f=CSD["p26"]+2, db=-5),
]
CSON = [dict(plan=p, db=d) for p, d in [("p01", -16), ("p03", -12), ("p05", -14), ("p06", -13),
                                        ("p07", -15), ("p08", -9), ("p26", -14)]]
print("court inc", len(CINC), "sfx", len(CSFX))

# ---------- version verticale 9:16 : 6 plans natifs (6 unités) ----------
VERT = [
 dict(id="v01", beats=5, prompt=P("A single vertical cinematic shot: a man on a roof at dawn raises a phone toward new siding.",
   "[Shot 1] Vertical framing, tall. @etienne, in a plain charcoal work jacket and plain navy cap, stands on the wet shingled roof of a suburban bungalow, the pale grey siding rising above him into a pale dawn sky, mist drifting between the shingles. He lifts a plain dark phone to eye level and holds. The camera cranes up slowly along his body and past his shoulder to the siding. Plain clothing with no logo, no text, no letters anywhere.",
   "Wind, a distant dog, a ladder creaking.")),
 dict(id="v02", beats=5, prompt=P("A single vertical cinematic shot: a ring of light bursts from a phone and races up a wall.",
   "[Shot 1] Vertical framing. @etienne fires the shutter; a ring of ion-blue light explodes from the lens and climbs the siding in a bright vertical streak, over the eave and into the sky, where it narrows to a single thread. The camera tilts straight up with it, the roof falling away below. Plain clothing with no logo, no text, no letters anywhere.",
   "A camera shutter, an electric thump, wind rising.")),
 dict(id="v03", beats=5, prompt=P("A single vertical cinematic shot: a pulse of light runs up a corridor of hydro poles.",
   "[Shot 1] Vertical framing. At cable height on a frozen country road, a pulse of ion-blue light climbs from pole to pole toward a small industrial building, throwing a cold flash on the frost. The camera rises with the pulse, the cables converging to a point at the top of frame. No text, no logos.",
   "Wind in the wires, a cable clacking, the pulse buzzing past.")),
 dict(id="v04", beats=6, prompt=P("A single vertical cinematic shot: a colossal tower unfolds upward out of a server rack.",
   "[Shot 1] Vertical framing. Inside @serveur, the status lights of one dark rack brighten bottom to top, and @tour unfolds upward out of the glass: ten floors of dark glass and ion-blue light stacked into the top of frame, each floor an open office in cross-section, one warm orange light at the very top. Dust turns in the work lamp beside the rack. The camera tilts up hard. No text, no logos, no readable screen.",
   "A deep rising rumble, metal ticking, a low choral tone.")),
 dict(id="v05", beats=5, prompt=P("A single vertical cinematic shot: the camera climbs the facade of a virtual tower as floors light up.",
   "[Shot 1] Vertical framing, straight up the facade. As the camera rises, each floor of @tour lights from inside: desks, silhouetted workers, a hand raised, glass glow never readable. The vertical fins throw long blue lines up the frame. At the top the warm orange light pulses once. No text, no logos, no readable screen.",
   "Relays snapping one after another, a rising hum.")),
 dict(id="v06", beats=5, prompt=P("A single vertical cinematic shot: a finished house at golden hour with a rig of light orbiting the roof.",
   "[Shot 1] Vertical framing, @toit filling the lower two thirds, sky above. Around the finished exterior, new pale grey siding and dark soffit-fascia, a thin rig of blue-white light circles the roof once, and @etienne stands small at the foot of the ladder and sheds small petals of light that dissolve before touching the lawn. The camera orbits low, long shadows sliding. No text, no logos, no readable sign.",
   "Soft wind, birds, a low warm hum.")),
]
REFS_V = {"v01": ["etienne"], "v02": ["etienne"], "v04": ["serveur", "tour"], "v06": ["toit"]}
for v in VERT:
    v.update(sequence="V", recette="h3-max", images=124, format="9:16", refs=REFS_V.get(v["id"], []), premiere=None,
             parole=None, statut="RÉEL", camera="voir prompt", effets="voir prompt", son="voir prompt")

VTR = {"v03": ("glisse", 4), "v04": ("dip", 4), "v05": ("cut", 0), "v06": ("fondu", 4)}
VDUR = {v["id"]: B(v["beats"]) for v in VERT}
VDEB, VT = timeline([v["id"] for v in VERT], VDUR, VTR)
print("vertical", VT, round(VT / FPS, 2), "s")

def build_vertical():
    video = []
    for v in VERT:
        t = VTR.get(v["id"])
        video.append({"id": v["id"], "src": v["id"], "entree_f": 0, "duree_f": VDUR[v["id"]], "vitesse": 1,
                      "transition_in": {"type": t[0], "duree_f": t[1]} if t else {"type": "cut", "duree_f": 0}})
    sources = {v["id"]: {"kind": "video", "duree_f": 124} for v in VERT}
    sources["m03"] = {"kind": "audio", "duree_f": VT}
    return {"version": 1, "fps": 24, "format": "9:16", "genre": "social",
            "titre": "OPSYS-AI · Signal (vertical)",
            "sources": sources, "video": video,
            "audio": {"musique": {"src": "m03", "entree_f": 0, "duree_f": VT, "gain_db": -6,
                                 "fondu_in_f": 4, "fondu_out_f": 14},
                      "voix": [], "ducking": {"actif": True, "profondeur_db": 9},
                      "cible_lufs": -14, "crete_db": -1.5, "fondu_coupe_ms": 40},
            "textes": [], "generations": []}

VERT_PLAN = build_vertical()
VSD = {v["id"]: VDEB[i] for i, v in enumerate(VERT)}
VINC = [
 dict(type="surtitre", debut_f=VSD["v01"]+4, duree_f=50, position="haut-gauche", texte="M3 · ESTIMATION"),
 dict(type="statut", debut_f=VSD["v01"]+8, duree_f=48, position="bas-gauche", texte="Photo reçue."),
 dict(type="trajet", debut_f=VSD["v03"]+2, duree_f=50, position="centre",
      points=[[0.5, 0.95], [0.42, 0.6], [0.56, 0.35], [0.5, 0.06]], couleur="ion"),
 dict(type="surtitre", debut_f=VSD["v04"]+6, duree_f=50, position="haut-gauche", texte="OPSYS-AI · DIX DÉPARTEMENTS"),
 dict(type="statut", debut_f=VSD["v06"]+4, duree_f=44, position="bas", texte="Soumission prête. Approuver ?"),
 dict(type="carton", debut_f=VSD["v06"]+50, duree_f=VT - VSD["v06"] - 50, position="centre"),
]
VSFX = [
 dict(type="frappe", debut_f=0, db=-12),
 dict(type="clic", debut_f=VSD["v02"]+18, db=-6),
 dict(type="fouet", debut_f=VSD["v03"], db=-8),
 dict(type="impact", debut_f=VSD["v04"]+10, db=-4),
 dict(type="boom", debut_f=VSD["v04"]+12, db=-8, duree_s=1.0),
 dict(type="impact", debut_f=VSD["v06"]+2, db=-5),
]
VSON = [dict(plan=p, db=d) for p, d in [("v01", -16), ("v02", -12), ("v03", -14), ("v04", -9), ("v05", -13), ("v06", -14)]]
print("vert inc", len(VINC), "fin", VSD["v06"]+50+(VT - VSD["v06"]-50), VT)

# ---------- assemblage ----------
D = {
 "equipe": "deepseek",
 "titre": "Le Onzième Étage",
 "logline": ("Une PME québécoise envoie une photo de toit ; le signal traverse le ciel, réveille une tour virtuelle de dix "
             "départements qui travaille toute la journée pour elle, et laisse à son patron le seul étage qui compte : le sien."),
 "personnages": PERSOS, "lieux": LIEUX, "cles": CLES,
 "voix": REPLIQUES,
 "plans": [{k: v for k, v in x.items() if k != "beats"} for x in PLANS + VERT],
 "musique": MUSIQUE,
 "montage": {"long": LONG, "court": COURT_PLAN, "vertical": VERT_PLAN},
 "annexe": {
   "long": {"incrustations": INC, "sfx": SFX, "son_plans": SON_PLANS, "etalonnage": ETAL},
   "court": {"incrustations": CINC, "sfx": CSFX, "son_plans": CSON, "etalonnage": ETAL},
   "vertical": {"incrustations": VINC, "sfx": VSFX, "son_plans": VSON, "etalonnage": ETAL},
 },
 "vertical": VERT,
}
MUSIQUE["prompts"] = [
 {"id": "m01", "duree_s": 150, "prompt": MUSIQUE["prompt"]},
 {"id": "m02", "duree_s": 30, "prompt": ("Instrumental only, no vocals. Compact 13-second cut of the same 124 BPM electronic cue in D minor: "
   "two bars of pulsing sub bass and closed hi-hat, a rising filtered arpeggio, then a full drop at 5 s with big live drums, the "
   "four-note analogue motif and pizzicato strings, one last hit and a clean stop with a warm tail. Punchy, modern, uplifting, "
   "propulsive, no dark colours, no lo-fi.")},
 {"id": "m03", "duree_s": 30, "prompt": ("Instrumental only, no vocals. Vertical social cut, 124 BPM, same palette: a single low pulse and hand claps "
   "for two bars, then a wide drop with drums, a bright analogue motif and a short string swell, ending on one clean hit. "
   "Confident, energetic, clean modern mix, no vocals.")},
]

Path("equipes/deepseek/dossier.json").write_text(json.dumps(D, ensure_ascii=False, indent=1))
print("ecrit")
