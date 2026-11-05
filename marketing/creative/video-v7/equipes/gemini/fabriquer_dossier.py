#!/usr/bin/env python3
"""
Générateur et validateur strict du dossier V7 pour l'équipe « gemini ».
Produit equipes/gemini/dossier.json sur une grille exacte à 120.0 BPM (1 temps = 0.5 s = 12 images à 24 i/s).
Vérifie : budget (§7), recette live-action (§4), mots interdits, continuité 24 fps, durées sources, identifiants.
"""
import json
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
CAP = "/home/pc6/nexora-creative-data/promo/v6-creative/captures"

BPM = 120.0
BEAT = 60.0 / BPM  # 0.5 s exactement (12 images à 24 i/s)

CAM_PREFIX = (
    "Production still from a live-action feature film, photographed on location on "
    "35mm film (Kodak Vision3 500T) with a {lens}; natural exposure, visible film grain, "
    "slight halation around bright sources, soft lens imperfections, "
)

VID_PREFIX = (
    "For the target video, at 0.00 seconds into the target video, <Picture 1> (from [Shot 1]) is fully referenced.\n\n"
    "integrated_multimodal_description: [Shot 1] Live-action footage shot on 35mm film, {operator}, "
    "natural motion blur from a 180-degree shutter, slight focus breathing, real physics and weight, "
    "practical fire, smoke and debris, film grain. {action} No text, no logos.\n\n"
    "overall_soundscape: {sound}\n\n"
    "non_diegetic_music: N/A"
)

CLES_SPEC = [
    # 20 clés 16:9 (k01 à k20)
    ("k01", "16:9", 4101,
     "Panavision Primo 24mm wide-angle lens held low at ground level, rainwater and soot droplets on the front element",
     "night on a muddy Scottish castle courtyard in pouring rain: an enormous wyvern with scarred wet leathery skin and torn wing membranes crashes down onto a stone watchtower twenty metres away, crushing timber scaffolding and unleashing a torrent of real liquid napalm fire straight toward the camera; two stuntmen in soaked mud-caked wool cloaks and dented steel helmets dive into the mud in the immediate foreground for human scale, harsh practical orange firelight reflecting in dirty puddles, thick black diesel smoke."),
    ("k02", "16:9", 4102,
     "Cooke Anamorphic 40mm lens mounted on a rain-slicked camera car, water streaks across the glass",
     "stormy night on a flooded industrial concrete roof in Rotterdam: a thirty-00-kilogram armored stunt truck flips sideways through a sheet of real gasoline fire and flying asphalt chunks, metal roof buckling on wet concrete, a stunt driver in a dark rain-soaked coat rolling behind a concrete barrier in the foreground for scale, practical sodium vapour industrial lamps and fire illuminating the heavy rain."),
    ("k03", "16:9", 4103,
     "Cooke Panchro 400mm telephoto lens from 250 metres away, compressed perspective, heat shimmer",
     "dusk on a rainy Scottish highland ridge: a huge dragon with scarred, mud-caked leathery hide clings to the top of a real ruined stone keep and breathes a violent jet of real fire onto the wet battlements; the fire lights the drizzle and wet stone, thick black smoke drifts across heavy overcast clouds, three soldiers in muddy cloaks stand in silhouette in the long grass in the foreground for scale."),
    ("k04", "16:9", 4104,
     "Arri Master Prime 35mm lens on a shoulder rig, mud splatters and raindrops on the lens",
     "night inside a burning medieval courtyard in heavy rain: a terrified bearded medieval foot soldier in a dented steel helmet and soaked leather brigandine stumbles backward through deep mud in close medium shot, his wet weathered face lit by harsh flickering orange flames from a collapsing timber gate right behind him, flying sparks and heavy smoke filling the air."),
    ("k05", "16:9", 4105,
     "handheld Arri Alexa Mini with a 32mm Cooke lens, rain droplets and condensation on the glass",
     "night, heavy downpour on a real industrial refinery rooftop: two stunt performers in soaked dark waxed-cotton coats cross two orange plasma-heated steel blades; the hot orange blades are the only key light, casting harsh practical orange reflections on wet skin, soaked hair and puddles, thick white steam rising where pouring rain hits the scorching metal blades, blurred sodium street lamps far below."),
    ("k06", "16:9", 4106,
     "Panavision C-Series 50mm anamorphic lens at eye level, wet spray on the lens",
     "night on a rain-lashed steel catwalk: close medium shot of a fierce female stunt fighter with wet dark hair plastered to her bruised face, wearing a rain-soaked leather jacket, parrying a scorching orange heated blade inches from the lens; a shower of real white-hot welding sparks and dense steam erupts between the blades, practical orange light on wet skin."),
    ("k07", "16:9", 4107,
     "Arri Alexa 65 with a 28mm wide lens inside a lashed-down waterproof housing, heavy sea spray",
     "hurricane night in the North Sea on the rusted steel deck of a real offshore trawler: a colossal dark sea creature covered in barnacles, wet kelp and scarred whale-like blubber breaches forty metres out of black churning waves right beside the bow; tons of white seawater crash over the rusted railings onto two deckhands in yellow oilskins clinging to a winch in the foreground, harsh white deck floodlights cutting through the rain."),
    ("k08", "16:9", 4108,
     "Hasselblad 50mm medium-format lens mounted inside a real spacecraft cupola, scratch on the thick quartz pane",
     "low Earth orbit seen through a real scratched cupola window: a massive industrial grey steel orbital freighter with scorched thermal tiles and riveted hull plates fractures in half five hundred metres away; silent white clouds of vented liquid oxygen, tumbling aluminium struts and a brief burst of orange hydrazine fuel in vacuum, harsh unfiltered white sunlight from the left and pitch-black unlit shadows, cloud-covered Earth below, an astronaut's gloved hand braced on the window frame in the foreground."),
    ("k09", "16:9", 4109,
     "motion-control camera with a 35mm Zeiss Super Speed lens, practical 1980s physical miniature photography",
     "low Earth orbit above a real cloud-covered Earth: two battered grey naval spacecraft with weathered paint, scorch marks and antenna arrays pass close to the camera; a silent hull breach throws spinning metal panels and frozen white gas droplets right past the lens, lit by a single hard unfiltered solar key light with deep black shadows and zero coloured light."),
    ("k10", "16:9", 4110,
     "Arri Alexa 65 with a 50mm Prime lens shot from a chase helicopter, high-altitude mist on the glass",
     "above a real stratocumulus cloud deck at dusk over the North Atlantic: a gigantic dark-scaled dragon latches onto the rusted riveted steel wing of a heavy grey military cargo aircraft, tearing off aluminium skin panels and breathing a long plume of real orange fire that trails backward in the 300-knot slipstream; visible rivets, oil streaks and black smoke, framed from the side door of a chase helicopter."),
    ("k11", "16:9", 4111,
     "Panavision 180mm telephoto lens on a fluid head tripod, dust particles and heat haze",
     "twilight on a cracked desert highway in Nevada: a dusty 1980s dark grey sedan explodes from a real practical mortar charge underneath the chassis; the hood, doors and shattered tempered glass blow upward in a boiling fireball of black diesel smoke and orange flame, asphalt debris raining down onto dry scrub brush in the foreground, natural desert dusk sky."),
    ("k12", "16:9", 4112,
     "Cooke S4 25mm lens mounted on a low-flying helicopter nose mount, dust and stone chips in the air",
     "overcast afternoon in a real limestone quarry in Wales: a line of six medieval horsemen in muddy mail and tattered wool surcoats gallops full speed along a narrow dirt ledge while a colossal winged wyvern swoops down right behind them, snapping pine trees and kicking up a massive cloud of grey quarry dust and gravel."),
    ("k13", "16:9", 4113,
     "Zeiss Master Prime 35mm lens on a handheld shoulder rig, water droplets and soot on the lens",
     "dawn in a flooded concrete subway tunnel in Paris: a massive rusted steel tunnel-boring machine breaks through a brick retaining wall in a shower of falling masonry, dirty water and real electrical arc sparks, while two rescue workers in muddy reflective jackets sprint toward the camera through ankle-deep brown water in the foreground."),
    ("k14", "16:9", 4114,
     "Arri Ultra Prime 28mm lens inside a battered cockpit, frost and scratches on the canopy glass",
     "stratosphere at sunrise seen from inside a real high-altitude jet cockpit: over the pilot's scarred grey helmet and oxygen hose in the foreground, a massive dark winged creature banks sharply across the nose of the jet against blinding natural morning sun and thin cirrus clouds, contrails shredding in the wake."),
    ("k15", "16:9", 4115,
     "Leica Summilux-C 35mm lens at ground level in snow, snowflakes melted on the glass",
     "blizzard at dusk in a real pine forest in British Columbia: a towering bipedal mechanical walker built of rusted yellow industrial excavator steel and hydraulic hoses lumbers through deep snow, crushing real fir trees; harsh halogen worklights mounted on its chassis cut through falling snow and diesel exhaust, a lumberjack in a red wool parka crouching behind a fallen log in the foreground."),
    ("k16", "16:9", 4116,
     "Panavision Primo 50mm lens from a concrete bunker slit, rain and mud on the concrete",
     "stormy afternoon at a real coastal concrete seawall in Normandy: a thirty-metre Atlantic storm wave slams into a battered concrete lighthouse, exploding into a mountain of white foam and dark spray that engulfs the tower, seagulls and torn kelp flying in the gale, two coastguards watching from a bunker window in the foreground."),
    ("k17", "16:9", 4117,
     "Cooke Panchro 75mm telephoto lens at ground level, ash flakes drifting past the lens",
     "night on the black basalt slopes of Mount Etna in Sicily: a river of real crusted orange lava pours down a rocky gully while a massive horned creature with charcoal-black hide walks slowly across the molten crust, kicking up showers of real red cinders and sulphur smoke, two volcanologists in silver heat-reflective suits standing behind a tripod in the foreground."),
    ("k18", "16:9", 4118,
     "Panavision 300mm telephoto lens on a gimbal from a cliffside, morning mist",
     "sunrise over real misty mountain fjords in Patagonia: three enormous dark-scaled dragons glide close in formation fifty metres above a real pine-covered ridge, their scarred wings catching the low golden morning sun through thick valley fog, pine trees bending in the downdraft in the foreground."),
    ("k19", "16:9", 4119,
     "Arri Master Prime 50mm lens on a tripod, warm late-afternoon backstage light",
     "late afternoon on a real muddy film location parking lot in Scotland: a weary film director in a mud-spattered olive waxed jacket and wool beanie sits in a canvas folding chair holding a steaming paper coffee cup, while in the background a real stunt crew hoses down a blackened medieval tower and a mechanical dragon wing on a flatbed truck."),
    ("k20", "16:9", 4120,
     "Arri Macro 100mm lens at eye level on lava rock, heat wave distortion",
     "dusk on a wet black volcanic rock beach in Iceland: a real scruffy ginger tabby kitten with damp fur sits on a mossy basalt boulder, puffs up its small chest and belches a sudden two-metre blowtorch plume of real orange propane fire into the cold evening air, lighting up the wet pebbles and sea spray around it."),
    # 4 clés 9:16 natives (k21 à k24)
    ("k21", "9:16", 4121,
     "Panavision Primo 24mm vertical-gate lens held at ground level, rainwater and soot on the glass",
     "vertical 9:16 frame, night in a muddy Scottish castle courtyard in pouring rain: towering vertically above the camera, an enormous wyvern with wet scarred hide clings to a burning stone tower and blasts a vertical column of real liquid fire straight down toward two muddy soldiers diving at the bottom of the frame, thick black smoke rising to the top."),
    ("k22", "9:16", 4122,
     "handheld Arri Alexa Mini vertical frame with a 32mm lens, rain droplets on the lens",
     "vertical 9:16 frame, night in heavy rain on a real industrial steel rooftop: two stunt fighters in soaked dark coats clash vertically with orange plasma-heated steel blades on a narrow wet staircase; practical orange light illuminates wet faces and falling rain, white steam and sparks filling the vertical frame."),
    ("k23", "9:16", 4123,
     "Arri Alexa 65 vertical frame with a 28mm lens on a pitching trawler deck, heavy sea spray",
     "vertical 9:16 frame, hurricane night in the North Sea: towering vertically from the bottom of the churning black ocean to the top of the frame, a colossal barnacle-covered sea monster breaches straight up beside the rusted bow of a trawler, white water cascading down onto a deckhand in yellow oilskins at the bottom edge."),
    ("k24", "9:16", 4124,
     "Arri Macro 100mm vertical frame at eye level on wet basalt rock",
     "vertical 9:16 frame, dusk on a black volcanic beach in Iceland: a real scruffy ginger tabby kitten sits on a wet basalt rock in the lower third and belches a tall vertical column of real orange fire straight up toward the top of the frame, lighting up the damp fur and volcanic stones."),
]

PLANS_SPEC = [
    # 20 plans 16:9 (p01 à p20), tous à 124 images = 5.1667 s (1 unité chacun)
    ("p01", "k01", "16:9", 124, 5101,
     "low-angle handheld camera at ground level, violent shockwave shake as the creature hits",
     "The enormous wyvern slams onto the stone watchtower, crushing the timber and unleashing a roaring jet of real liquid fire toward the lens; the two muddy soldiers in the foreground dive flat into the puddles as burning debris rains down.",
     "Deafening stone collapse, roaring napalm fire, heavy rain, men yelling in panic, deep animal snarl."),
    ("p02", "k02", "16:9", 124, 5102,
     "tracking camera car swerving on wet concrete, rain streaking across the lens",
     "The heavy armored truck flips violently through the wall of gasoline fire, smashing onto its side on the flooded roof and sliding toward the concrete barrier in a shower of sparks and black smoke while the stuntman ducks.",
     "Screaming tires, heavy metal crunch, roaring gasoline fireball, pouring rain, hissing steam."),
    ("p03", "k03", "16:9", 124, 5103,
     "long-lens camera on a tripod with a whip-pan and focus pull through the rain",
     "The dragon arches its scarred neck atop the ruined keep and breathes a long, pressurized stream of real fire across the wet stone battlements; burning timbers collapse, thick black smoke rolls in the wind, and the soldiers in the foreground flinch.",
     "Roaring fire, crackling timber, howling highland wind, heavy rain, deep guttural dragon roar."),
    ("p04", "k04", "16:9", 124, 5104,
     "handheld shoulder camera backing up rapidly with the actor through the mud",
     "The mud-splattered medieval soldier stumbles backward toward the camera as the burning timber gate collapses behind him in a shower of sparks; he stares up in terror at the sky and shouts: <d>[French] Baissez la tête !</d>",
     "Crackling fire, heavy mud footsteps, falling timber, a terrified man shouting in French: <d>[French] Baissez la tête !</d>"),
    ("p05", "k05", "16:9", 124, 5105,
     "handheld camera operator circling the stunt fighters closely on the wet roof",
     "The two soaked fighters clash their scorching orange blades twice with heavy physical force; at each impact, real white-hot sparks and dense clouds of steam erupt in the pouring rain, and one fighter slides back across a puddle.",
     "Pouring rain, heavy metallic electric clash, loud hiss of boiling steam, boots slipping on wet steel."),
    ("p06", "k06", "16:9", 124, 5106,
     "tight handheld camera pushing in on the fighter's wet face as sparks fly",
     "The female fighter locks her scorching orange blade against her opponent's weapon inches from her face; boiling steam and sparks whip past her cheek in the rain as she shoves the blade away and yells: <d>[French] Recule !</d>",
     "Sizzling rain on hot metal, electric crackle, heavy breathing, a fierce woman shouting in French: <d>[French] Recule !</d>"),
    ("p07", "k07", "16:9", 124, 5107,
     "handheld camera braced against the trawler cabin, violent roll with the ocean swell",
     "The colossal barnacle-covered sea creature crashes its massive body back against the bow wave, sending a wall of white seawater and foam smashing over the rusted steel deck; the two deckhands cling to the winch as water floods the frame.",
     "Roaring hurricane wind, cavernous whale-like bellow, tons of seawater crashing on steel, creaking hull."),
    ("p08", "k08", "16:9", 124, 5108,
     "handheld camera inside the zero-gravity cupola, bumping slightly against the window frame",
     "Outside the scratched cupola window, the fractured steel orbital freighter breaks apart silently as white clouds of vented oxygen and spinning metal struts drift toward the glass; the astronaut's gloved hand braces hard against the frame.",
     "Near-total vacuum silence, a low muffled metallic thud transmitted through the hull, quiet astronaut breathing."),
    ("p09", "k09", "16:9", 124, 5109,
     "motion-control camera gliding forward between the two massive spacecraft hulls",
     "The camera glides between the two battered grey warships as a silent hull breach blows spinning aluminium panels and frozen gas crystals across the hard sunlight, casting sharp moving shadows across the riveted steel plating.",
     "Deep sub-bass structural hull vibration, muffled hiss of venting gas, eerie orbital quiet."),
    ("p10", "k10", "16:9", 124, 5110,
     "aerial camera from a chase helicopter, vibrating in the high-altitude turbulence",
     "The gigantic dragon digs its claws into the steel cargo wing, rips away a buckled sheet of riveted metal that tumbles into the clouds below, and blasts a plume of real orange fire that whips backward in the slipstream.",
     "Deafening turboprop engine drone, tearing sheet metal, roaring 300-knot wind, ferocious dragon roar."),
    ("p11", "k11", "16:9", 124, 5111,
     "tripod telephoto lens tracking the car, violent camera shudder as the shockwave hits",
     "The dark grey sedan detonates from underneath in a massive practical fireball; the steel hood flips high into the desert sky trailing black diesel smoke while burning tires and shattered glass bounce across the asphalt.",
     "Ear-splitting low-end explosion, tearing steel, roaring fireball, rattling debris hitting asphalt."),
    ("p12", "k12", "16:9", 124, 5112,
     "low-flying helicopter tracking shot racing parallel to the galloping horses",
     "The six muddy medieval horsemen gallop at full tilt along the quarry ledge as the huge winged wyvern swoops down right behind the last rider, its wings kicking up a blinding storm of gravel and dust.",
     "Thundering hooves on rock, snapping pine branches, massive leathery wingbeats, shouting riders."),
    ("p13", "k13", "16:9", 124, 5113,
     "handheld camera sprinting backward ahead of the rescue workers through the water",
     "The rusted steel cutterhead grinds through the brick tunnel wall in a cascade of muddy water, falling bricks and real blue electrical sparks while the two rescue workers splash frantically toward the lens.",
     "Grinding steel on stone, crashing brickwork, roaring floodwater, sharp electrical arc snaps."),
    ("p14", "k14", "16:9", 124, 5114,
     "handheld camera inside the cramped jet cockpit, jolting in severe wake turbulence",
     "Seen over the pilot's helmet, the enormous winged creature banks hard across the frosted canopy glass in blinding morning sunlight; the jet shudders violently in the creature's wake and the pilot grabs the canopy rail.",
     "High-pitched jet turbine whine, violent airframe rattling, muffled breathing in an oxygen mask."),
    ("p15", "k15", "16:9", 124, 5115,
     "low handheld camera crouching behind the snow-covered log, shaking with each heavy footstep",
     "The towering rusted industrial mech slams a hydraulic steel foot into the deep snow, snapping a real pine tree in half; diesel exhaust and snow blow across the lens as the lumberjack ducks behind the log.",
     "Heavy hydraulic whine, diesel engine chug, booming metallic footstep, snapping timber, howling wind."),
    ("p16", "k16", "16:9", 124, 5116,
     "tripod camera inside the concrete bunker, water splashing against the viewing slit",
     "The thirty-metre Atlantic storm wave slams into the concrete lighthouse, exploding into a towering white wall of foam that completely swallows the structure and hurls spray against the bunker slit.",
     "Deafening ocean thunder, howling gale wind, water slamming against concrete."),
    ("p17", "k17", "16:9", 124, 5117,
     "telephoto lens on a tripod, shimmering heat waves distorting the air",
     "The massive charcoal-black horned creature steps heavily across the crusted orange lava stream, cracking the surface and sending a geyser of real molten rock and red cinders bursting into the night air.",
     "Crackling lava crust, deep volcanic rumble, hissing sulphur gas, heavy crushing footsteps."),
    ("p18", "k18", "16:9", 124, 5118,
     "helicopter gimbal telephoto shot gliding smoothly alongside the lead dragon",
     "The three enormous dragons glide through the golden Patagonian morning mist just above the pine treetops; the lead dragon beats its scarred leathery wings once with heavy physical weight, parting the fog.",
     "Rushing mountain wind, slow powerful leathery wingbeats, distant eagle-like cry echoing in the valley."),
    ("p19", "k19", "16:9", 124, 5119,
     "locked-off 50mm tripod camera on the muddy film lot, slight breath of wind",
     "The weary film director in the mud-spattered jacket lowers his paper coffee cup, looks straight into the camera lens with a deadpan expression while the stunt crew hoses down the smoking dragon wing behind him, and says: <d>[French] Bon. On la garde.</d>",
     "Hissing water hose, distant crew chatter, wind, a calm man speaking clearly in French: <d>[French] Bon. On la garde.</d>"),
    ("p20", "k20", "16:9", 124, 5120,
     "locked-off macro tripod camera on the wet basalt beach, jolting slightly at the flame burst",
     "The scruffy ginger kitten sits on the wet black boulder, opens its tiny mouth wide and belches a sudden two-metre blowtorch plume of real orange fire into the dusk air, then blinks calmly and licks its paw.",
     "Tiny kitten squeak followed immediately by a loud pressurized blowtorch whoosh of fire, gentle ocean waves."),
    # 4 plans 9:16 natifs (p21 à p24), 124 images = 1 unité chacun
    ("p21", "k21", "9:16", 124, 5121,
     "vertical 9:16 handheld camera at ground level, violent shake as fire pours down",
     "The enormous wyvern atop the burning tower blasts a vertical column of real liquid fire straight down the 9:16 frame; the two muddy soldiers at the bottom dive aside as burning timbers tumble vertically.",
     "Roaring napalm fire, collapsing stone, pouring rain, terrified shouts."),
    ("p22", "k22", "9:16", 124, 5122,
     "vertical 9:16 handheld camera Tilting up the wet steel staircase in the rain",
     "The two soaked fighters clash their scorching orange blades on the narrow staircase; white-hot sparks cascade down the vertical frame through the pouring rain while thick steam rises.",
     "Pouring rain, heavy metallic blade clash, loud hiss of steam."),
    ("p23", "k23", "9:16", 124, 5123,
     "vertical 9:16 handheld camera on the pitching trawler deck, drenched in spray",
     "The colossal barnacle-covered sea monster breaches straight up the vertical frame beside the rusted bow, then slams back down, sending a towering wall of white water crashing over the deckhand at the bottom.",
     "Roaring hurricane wind, deep monster bellow, tons of water crashing on steel deck."),
    ("p24", "k24", "9:16", 124, 5124,
     "vertical 9:16 locked-off camera on the volcanic beach",
     "The scruffy ginger kitten on the wet black rock belches a tall vertical column of real orange fire straight up to the top of the 9:16 frame, then sits back and blinks.",
     "Tiny kitten meow followed by a loud blowtorch roar of fire, lapping waves."),
]

VOIX_SPEC = [
    {
        "id": "v01",
        "moteur": "gemini38-puck",
        "texte": "Trois mots bruts.",
        "direction": "Voix d'homme grave, posée, grain de réalisateur de cinéma, très sèche et proche du micro, sans emphase publicitaire, débit franc (0.9 s)."
    },
    {
        "id": "v02",
        "moteur": "gemini38-puck",
        "texte": "Zéro jeu vidéo.",
        "direction": "Ton tranchant, complice, sec et assuré, attaque nette sur le Z, humour froid de directeur photo sur un plateau (0.9 s)."
    },
    {
        "id": "v03",
        "moteur": "gemini38-fenrir",
        "texte": "Changez d'échelle.",
        "direction": "Voix de femme intense, grave et cinématographique, souffle retenu avant l'espace, autorité calme (1.0 s)."
    },
    {
        "id": "v04",
        "moteur": "gemini38-puck",
        "texte": "Faites votre film.",
        "direction": "Conclusion sobre, grave, chaleureuse et définitive, posée sur la résonance finale du cuivre, zéro ton de vendeur (1.0 s)."
    }
]

TEMPS_FORTS_SPEC = [
    {"t": 0.0, "evenement": "Attaque à froid : impact wyverne (p01) + premier coup du motif d'enclume à 120 BPM"},
    {"t": 2.0, "evenement": "Coupure sèche (trou musical 1) : bruit mécanique pur de la saisie « dragn chateau feu »"},
    {"t": 3.5, "evenement": "Riser granulaire sur le Boost IA : explosion des mots en rayons"},
    {"t": 4.5, "evenement": "Claque « ÇA TOURNE. » + Ré-entrée orchestrale lourde sur le dragon d'Écosse (p03)"},
    {"t": 7.0, "evenement": "Trou musical 2 (silence 1.5 s) : son natif pur du château en flammes et cri « Baissez la tête ! » (p04)"},
    {"t": 9.0, "evenement": "Saisie éclair « duel sabre laser orange oraj » + Boost"},
    {"t": 10.5, "evenement": "Impact Marche 2 : entrée des cordes staccato et enclumes sur le duel sous la pluie (p05, p06)"},
    {"t": 14.0, "evenement": "Preuve produit 1 : balayage Avant / Après du détourage vidéo réel sur le duel"},
    {"t": 16.0, "evenement": "Impact tempête : le léviathan crève l'océan (p07), cuivres graves à pleine puissance"},
    {"t": 19.0, "evenement": "Trou musical 3 (vide spatial 3.0 s) : coupure nette de l'orchestre, silence de l'orbite et décompression sourde (p08)"},
    {"t": 22.0, "evenement": "Reprise pulsée : travelling entre les cuirassés (p09) + Saisie/Boost « dragon atak croiseur spatial »"},
    {"t": 25.5, "evenement": "Impact Marche 3 : le dragon déchire l'aile du cargo en plein ciel (p10), motif de 4 notes aux cors"},
    {"t": 28.0, "evenement": "Preuve produit 2 : chapitre 3D Relief (« casque de dragon ») puis Mode Studio"},
    {"t": 31.0, "evenement": "Rafale cinétique à 1.0 s par plan (2 temps) : voiture explosée (p11), cavaliers (p12), tunnelier (p13), cockpit (p14), mécha (p15)"},
    {"t": 36.0, "evenement": "Mosaïque « TOUTES TES PRISES. » : 6 plans simultanés qui claquent sur chaque temps à 120 BPM"},
    {"t": 39.0, "evenement": "Saisie ultime « tout » + Claque « TOUT. » : montée d'orchestre vertigineuse"},
    {"t": 40.5, "evenement": "Apothéose : l'aube dorée sur les dragons de Patagonie (p18), motif héroïque majeur plein cadre"},
    {"t": 43.0, "evenement": "Trou musical 4 (contre-pied comique) : le réalisateur sur le parking boueux (p19) « Bon. On la garde. »"},
    {"t": 44.5, "evenement": "Accord final signature (motif 4 notes) sur le Carton de marque remplaçable (3.0 s)"},
    {"t": 47.5, "evenement": "Scène bonus post-générique (silence musical) : saisie « dragn chato feu » -> le chaton crache du vrai feu (p20)"}
]

MUSIQUES_SPEC = [
    {
        "id": "m1",
        "moteur": "lyria-pro",
        "prompt": (
            "120 BPM strict tempo, cinematic live-recorded hybrid orchestral and industrial percussion score for a theatrical film trailer. "
            "Memorable 4-note low brass and anvil signature motif (D - F - A - G#). High dynamic contrast, tight punchy transients, zero flat pad. "
            "[0:00-0:02] Violent opening impact at 120 BPM with taiko drums, metallic anvil strike and roaring low brass playing the 4-note motif. "
            "[0:02-0:04] Sudden drop to a tense sub-bass heartbeat pulse and ticking clockwork percussion, building into a sharp granular orchestral riser at 0:03.5. "
            "[0:04.5-0:07] Massive orchestral downbeat hit with war horns and heavy industrial drums driving at 120 BPM. "
            "[0:07-0:08.5] Complete dramatic silence stop, letting only a faint metallic reverb tail decay. "
            "[0:08.5-0:19] Fast-paced urgent act: aggressive spiccato cellos, pounding anvil percussion every beat (0.5s), and brazen trombone stabs escalating at 0:10.5 and 0:16.0. "
            "[0:19-0:22] Sudden hard cut to eerie near-silence, just a deep sub-bass vacuum drone. "
            "[0:22-0:31] Building orbital tension with pulsing analog bass synth, military snare rolls and rising brass swells hitting hard at 0:25.5. "
            "[0:31-0:39] Relentless climax montage at 120 BPM: every 1.0 second (every 2 beats) a huge taiko and brass hit punctuates the cuts, accelerating into a full orchestral riser at 0:39. "
            "[0:40.5-0:43] Glorious, wide acoustic symphonic resolution with soaring French horns playing the 4-note signature motif in major. "
            "[0:43-0:44.5] Abrupt stop. "
            "[0:44.5-0:47.5] Final definitive 4-note brass and anvil signature chord with a clean resonant decay, followed by silence from 0:47.5 to 0:52."
        )
    },
    {
        "id": "m2",
        "moteur": "lyria-pro",
        "prompt": (
            "120 BPM exact tempo, raw acoustic percussion, prepared piano and brutal low brass film score inspired by modern live-action action cinema. "
            "Distinctive 4-note signature riff on solo bass trombone and metallic foundry percussion. "
            "[0:00-0:02] Explosive drum ensemble and bass trombone slam on beat 1. "
            "[0:02-0:04.5] Stripped-back dry woodblock click at 120 BPM and escalating string scrape riser. "
            "[0:04.5-0:07] Heavy stomping groove with Scottish war drums and dirty brass stabs. "
            "[0:07-0:08.5] Dead stop silence for native dialogue. "
            "[0:08.5-0:19] High-voltage industrial chase rhythm: metallic clangs, distorted upright bass pulse and sharp horn accents hitting on every bar (2.0s). "
            "[0:19-0:22] Sudden vacuum drop, sub-zero bass hum only. "
            "[0:22-0:31] Relentless polyrhythmic build with timpani rolls and ascending brass clusters slamming at 0:25.5. "
            "[0:31-0:40.5] Full-throttle 120 BPM action blitz: synchronized orchestral hits every 2 beats, culminating in a massive cymbal choke at 0:40. "
            "[0:40.5-0:43] Majestic, breathable acoustic strings and warm horn fanfare over Patagonian vistas. "
            "[0:44.5-0:47.5] Iconic 4-note low brass and anvil logo stinger, dry cut at 0:47.5."
        )
    },
    {
        "id": "m3",
        "moteur": "lyria-clip",
        "prompt": (
            "120 BPM punchy cinematic percussion and hybrid brass cue (30 seconds loopable master). "
            "Built around a 4-note anvil and French horn motif, crisp transients on every 0.5s beat, "
            "dramatic 1-second silence drops at 0:07 and 0:19, escalating from tight rhythmic tension "
            "to a massive full-orchestra climax with zero muddy pad."
        )
    }
]


def build_montage():
    segments = [
        # --- OUVERTURE CHOC (0.0 à 2.0 s) ---
        {
            "type": "plan",
            "debut": 0.0,
            "duree": 1.0,
            "fichier": "plan:p01",
            "fichier_vertical": "plan_v:p21",
            "entree": 0.4,
            "vitesse": [[0.0, 1.3], [0.4, 0.4], [1.0, 1.2]],
            "cadrage": [[0.0, 0.5, 0.5, 1.0], [1.0, 0.52, 0.48, 1.12]],
            "cadrage_v": [[0.0, 0.5, 0.5, 1.0], [1.0, 0.5, 0.48, 1.08]],
            "secousses": [[0.15, 24, 0.35]],
            "flash": [[0.15, "signal", 0.1]],
            "etalonnage": "nuit_feu",
            "son_db": -4
        },
        {
            "type": "plan",
            "debut": 1.0,
            "duree": 1.0,
            "fichier": "plan:p02",
            "entree": 0.5,
            "vitesse": 1.15,
            "cadrage": [[0.0, 0.5, 0.52, 1.0], [1.0, 0.48, 0.5, 1.1]],
            "cadrage_v": [[0.0, 0.52, 0.52, 1.08], [1.0, 0.48, 0.5, 1.15]],
            "secousses": [[0.2, 20, 0.3]],
            "etalonnage": "orage",
            "son_db": -5,
            "textes": [
                {"t": 0.1, "duree": 0.8, "texte_id": "t_pellicule", "style": "claque", "position": "bas"}
            ]
        },

        # --- MARCHE 1 : L'ÉTINCELLE BRUTE (2.0 à 9.0 s) ---
        {
            "type": "saisie",
            "debut": 2.0,
            "duree": 1.5,
            "dossier": f"{CAP}/boost/s01",
            "etapes": ["vide", "saisie", "saisie-fin", "survol"],
            "viewport": [1600, 900],
            "zone": [100, 296, 532, 474],
            "clavier_db": -16
        },
        {
            "type": "boost",
            "debut": 3.5,
            "duree": 1.0,
            "dossier": f"{CAP}/boost/s01",
            "viewport": [1600, 900],
            "zone": [100, 490, 532, 765],
            "termes_cles": ["dragon", "château", "feu", "flammes", "rugissement"]
        },
        {
            "type": "titre",
            "debut": 4.5,
            "duree": 0.5,
            "texte_id": "tourne",
            "style": "claque",
            "sur_video": "suivant"
        },
        {
            "type": "plan",
            "debut": 5.0,
            "duree": 2.0,
            "fichier": "plan:p03",
            "entree": 0.5,
            "vitesse": [[0.0, 1.25], [0.7, 0.35], [1.3, 0.35], [2.0, 1.25]],
            "cadrage": [[0.0, 0.52, 0.48, 1.0], [2.0, 0.5, 0.46, 1.08]],
            "cadrage_v": [[0.0, 0.54, 0.46, 1.05], [2.0, 0.5, 0.45, 1.12]],
            "secousses": [[0.65, 18, 0.35]],
            "flash": [[0.65, "os", 0.1]],
            "etalonnage": "nuit_feu",
            "son_db": -4
        },
        {
            "type": "plan",
            "debut": 7.0,
            "duree": 2.0,
            "fichier": "plan:p04",
            "entree": 0.3,
            "vitesse": 1.0,
            "cadrage": [[0.0, 0.5, 0.48, 1.0], [2.0, 0.5, 0.46, 1.08]],
            "cadrage_v": [[0.0, 0.5, 0.45, 1.08], [2.0, 0.5, 0.44, 1.14]],
            "etalonnage": "nuit_feu",
            "son_db": -2,
            "textes": [
                {"t": 0.15, "duree": 1.5, "texte_id": "t_son_natif", "style": "legende", "position": "haut"}
            ]
        },

        # --- MARCHE 2 : LA MAÎTRISE DU PLAN & DU DÉTOURAGE (9.0 à 19.0 s) ---
        {
            "type": "saisie",
            "debut": 9.0,
            "duree": 0.75,
            "dossier": f"{CAP}/boost/s03",
            "etapes": ["saisie", "saisie-fin", "survol"],
            "viewport": [1600, 900],
            "zone": [100, 296, 532, 474],
            "clavier_db": -18
        },
        {
            "type": "boost",
            "debut": 9.75,
            "duree": 0.75,
            "dossier": f"{CAP}/boost/s03",
            "viewport": [1600, 900],
            "zone": [100, 490, 532, 765],
            "termes_cles": ["orage", "pluie", "orange", "étincelles"]
        },
        {
            "type": "plan",
            "debut": 10.5,
            "duree": 2.0,
            "fichier": "plan:p05",
            "fichier_vertical": "plan_v:p22",
            "entree": 0.4,
            "vitesse": [[0.0, 1.3], [0.6, 0.3], [1.1, 1.2], [2.0, 1.1]],
            "cadrage": [[0.0, 0.5, 0.5, 1.0], [2.0, 0.48, 0.48, 1.1]],
            "cadrage_v": [[0.0, 0.5, 0.5, 1.0], [2.0, 0.5, 0.48, 1.08]],
            "secousses": [[0.55, 22, 0.35]],
            "flash": [[0.55, "signal", 0.1]],
            "etalonnage": "orage",
            "son_db": -4
        },
        {
            "type": "plan",
            "debut": 12.5,
            "duree": 1.5,
            "fichier": "plan:p06",
            "entree": 0.4,
            "vitesse": 1.0,
            "cadrage": [[0.0, 0.5, 0.46, 1.0], [1.5, 0.52, 0.45, 1.08]],
            "cadrage_v": [[0.0, 0.5, 0.44, 1.06], [1.5, 0.52, 0.44, 1.12]],
            "secousses": [[0.3, 16, 0.25]],
            "etalonnage": "orage",
            "son_db": -2
        },
        {
            "type": "avant_apres",
            "debut": 14.0,
            "duree": 2.0,
            "couches": [
                {
                    "fichier": f"{CAP}/detourage-src/duel-795.mp4",
                    "entree": 0.5,
                    "saturation": 0.0,
                    "texte_id": "brut"
                },
                {
                    "fichier": f"{CAP}/detourage/sorties/matte.mp4",
                    "entree": 0.5,
                    "texte_id": "masque"
                },
                {
                    "fichier": f"{CAP}/detourage/sorties/composite.mp4",
                    "entree": 0.5,
                    "texte_id": "final"
                }
            ],
            "textes": [
                {"t": 0.15, "duree": 1.7, "texte_id": "ch_detourage", "style": "legende", "position": "haut"}
            ]
        },
        {
            "type": "plan",
            "debut": 16.0,
            "duree": 2.5,
            "fichier": "plan:p07",
            "fichier_vertical": "plan_v:p23",
            "entree": 0.3,
            "vitesse": [[0.0, 1.2], [0.9, 0.4], [1.6, 1.1], [2.5, 1.2]],
            "cadrage": [[0.0, 0.5, 0.5, 1.0], [2.5, 0.48, 0.46, 1.12]],
            "cadrage_v": [[0.0, 0.5, 0.5, 1.0], [2.5, 0.5, 0.46, 1.08]],
            "secousses": [[0.85, 25, 0.45]],
            "etalonnage": "orage",
            "son_db": -3
        },
        {
            "type": "titre",
            "debut": 18.5,
            "duree": 0.5,
            "texte_id": "plus_grand",
            "style": "claque",
            "sur_video": "precedent"
        },

        # --- MARCHE 3 : L'ÉCHELLE INFINIE & LE STUDIO COMPLET (19.0 à 40.5 s) ---
        {
            "type": "plan",
            "debut": 19.0,
            "duree": 3.0,
            "fichier": "plan:p08",
            "entree": 0.3,
            "vitesse": 1.0,
            "cadrage": [[0.0, 0.5, 0.5, 1.0], [3.0, 0.52, 0.48, 1.06]],
            "cadrage_v": [[0.0, 0.48, 0.5, 1.08], [3.0, 0.52, 0.48, 1.14]],
            "etalonnage": "espace",
            "son_db": -2
        },
        {
            "type": "plan",
            "debut": 22.0,
            "duree": 2.0,
            "fichier": "plan:p09",
            "entree": 0.4,
            "vitesse": 1.15,
            "cadrage": [[0.0, 0.5, 0.5, 1.0], [2.0, 0.5, 0.5, 1.12]],
            "cadrage_v": [[0.0, 0.5, 0.5, 1.05], [2.0, 0.5, 0.5, 1.16]],
            "etalonnage": "espace",
            "son_db": -5
        },
        {
            "type": "saisie",
            "debut": 24.0,
            "duree": 0.75,
            "dossier": f"{CAP}/boost/s07",
            "etapes": ["saisie", "saisie-fin", "survol"],
            "viewport": [1600, 900],
            "zone": [100, 296, 532, 474],
            "clavier_db": -18
        },
        {
            "type": "boost",
            "debut": 24.75,
            "duree": 0.75,
            "dossier": f"{CAP}/boost/s07",
            "viewport": [1600, 900],
            "zone": [100, 490, 532, 765],
            "termes_cles": ["dragon", "croiseur", "orbite", "feu"]
        },
        {
            "type": "plan",
            "debut": 25.5,
            "duree": 2.5,
            "fichier": "plan:p10",
            "entree": 0.3,
            "vitesse": [[0.0, 1.25], [0.8, 0.35], [1.4, 1.15], [2.5, 1.2]],
            "cadrage": [[0.0, 0.52, 0.5, 1.0], [2.5, 0.48, 0.48, 1.1]],
            "cadrage_v": [[0.0, 0.54, 0.48, 1.06], [2.5, 0.48, 0.48, 1.14]],
            "secousses": [[0.75, 20, 0.35]],
            "flash": [[0.75, "signal", 0.1]],
            "etalonnage": "aube",
            "son_db": -3
        },
        {
            "type": "chapitre",
            "debut": 28.0,
            "duree": 1.5,
            "texte_id": "ch_relief",
            "media": {
                "dossier": f"{CAP}/relief",
                "etapes": ["tour-wire", "tour-clay", "tour-textured"],
                "viewport": [1600, 900],
                "zone": [260, 110, 1340, 820]
            }
        },
        {
            "type": "chapitre",
            "debut": 29.5,
            "duree": 1.5,
            "texte_id": "ch_studio",
            "media": {
                "dossier": f"{CAP}/studio2",
                "etapes": ["timeline", "assistant", "aperçu"],
                "viewport": [1600, 900],
                "zone": [80, 70, 1520, 850]
            }
        },

        # --- RAFALE DE PRODUCTION : 5 PLANS × 1.0 S (31.0 à 36.0 s) ---
        {
            "type": "plan",
            "debut": 31.0,
            "duree": 1.0,
            "fichier": "plan:p11",
            "entree": 0.4,
            "vitesse": [[0.0, 1.4], [0.35, 0.3], [1.0, 1.2]],
            "cadrage": [[0.0, 0.5, 0.52, 1.0], [1.0, 0.5, 0.48, 1.12]],
            "cadrage_v": [[0.0, 0.5, 0.52, 1.05], [1.0, 0.5, 0.48, 1.15]],
            "secousses": [[0.2, 26, 0.4]],
            "flash": [[0.2, "os", 0.1]],
            "etalonnage": "nuit_feu",
            "son_db": -3
        },
        {
            "type": "plan",
            "debut": 32.0,
            "duree": 1.0,
            "fichier": "plan:p12",
            "entree": 0.5,
            "vitesse": 1.25,
            "cadrage": [[0.0, 0.52, 0.5, 1.0], [1.0, 0.46, 0.5, 1.1]],
            "cadrage_v": [[0.0, 0.55, 0.5, 1.08], [1.0, 0.45, 0.5, 1.14]],
            "etalonnage": "neutre",
            "son_db": -5
        },
        {
            "type": "plan",
            "debut": 33.0,
            "duree": 1.0,
            "fichier": "plan:p13",
            "entree": 0.4,
            "vitesse": 1.2,
            "cadrage": [[0.0, 0.5, 0.5, 1.0], [1.0, 0.5, 0.48, 1.12]],
            "cadrage_v": [[0.0, 0.5, 0.5, 1.06], [1.0, 0.5, 0.48, 1.14]],
            "secousses": [[0.15, 18, 0.3]],
            "etalonnage": "orage",
            "son_db": -5
        },
        {
            "type": "plan",
            "debut": 34.0,
            "duree": 1.0,
            "fichier": "plan:p14",
            "entree": 0.4,
            "vitesse": 1.2,
            "cadrage": [[0.0, 0.5, 0.48, 1.0], [1.0, 0.48, 0.46, 1.1]],
            "cadrage_v": [[0.0, 0.52, 0.48, 1.06], [1.0, 0.48, 0.46, 1.12]],
            "secousses": [[0.2, 16, 0.25]],
            "etalonnage": "aube",
            "son_db": -5
        },
        {
            "type": "plan",
            "debut": 35.0,
            "duree": 1.0,
            "fichier": "plan:p15",
            "entree": 0.4,
            "vitesse": 1.15,
            "cadrage": [[0.0, 0.5, 0.5, 1.0], [1.0, 0.5, 0.46, 1.1]],
            "cadrage_v": [[0.0, 0.5, 0.48, 1.06], [1.0, 0.5, 0.45, 1.12]],
            "secousses": [[0.25, 22, 0.35]],
            "etalonnage": "orage",
            "son_db": -4
        },

        # --- MUR DE RÉSULTATS : MOSAÏQUE (36.0 à 39.0 s) ---
        {
            "type": "mosaique",
            "debut": 36.0,
            "duree": 3.0,
            "temps": [0.0, 0.5, 1.0, 1.5, 2.0, 2.5],
            "rushes": [
                {"fichier": "plan:p01", "entree": 0.5},
                {"fichier": "plan:p05", "entree": 0.5},
                {"fichier": "plan:p07", "entree": 0.5},
                {"fichier": "plan:p10", "entree": 0.5},
                {"fichier": "plan:p16", "entree": 0.4},
                {"fichier": "plan:p17", "entree": 0.4}
            ],
            "textes": [
                {"t": 0.2, "duree": 2.6, "texte_id": "ch_tout", "style": "grand", "position": "centre"}
            ]
        },

        # --- POINT D'ORGUE : « TOUT. » + AUBE PATAGONIE (39.0 à 43.0 s) ---
        {
            "type": "saisie",
            "debut": 39.0,
            "duree": 1.0,
            "dossier": f"{CAP}/boost/tout",
            "dossier_en": f"{CAP}/boost/tout-en",
            "etapes": ["vide", "saisie", "saisie-fin"],
            "viewport": [1600, 900],
            "zone": [100, 296, 532, 474],
            "clavier_db": -16
        },
        {
            "type": "titre",
            "debut": 40.0,
            "duree": 0.5,
            "texte_id": "tout",
            "style": "claque",
            "sur_video": "suivant"
        },
        {
            "type": "plan",
            "debut": 40.5,
            "duree": 2.5,
            "fichier": "plan:p18",
            "entree": 0.3,
            "vitesse": 1.0,
            "cadrage": [[0.0, 0.5, 0.5, 1.0], [2.5, 0.48, 0.48, 1.06]],
            "cadrage_v": [[0.0, 0.52, 0.48, 1.04], [2.5, 0.48, 0.48, 1.1]],
            "etalonnage": "aube",
            "son_db": -5,
            "textes": [
                {"t": 0.3, "duree": 1.9, "texte_id": "t_moteur", "style": "legende", "position": "bas"}
            ]
        },

        # --- CONTRE-PIED COMIQUE + CARTON REMPLAÇABLE + BONUS CHATON (43.0 à 52.0 s) ---
        {
            "type": "plan",
            "debut": 43.0,
            "duree": 1.5,
            "fichier": "plan:p19",
            "entree": 0.3,
            "vitesse": 1.0,
            "cadrage": [[0.0, 0.5, 0.5, 1.0], [1.5, 0.5, 0.5, 1.03]],
            "cadrage_v": [[0.0, 0.5, 0.48, 1.04], [1.5, 0.5, 0.48, 1.06]],
            "etalonnage": "neutre",
            "son_db": -1
        },
        {
            "type": "carton",
            "debut": 44.5,
            "duree": 3.0
        },
        {
            "type": "saisie",
            "debut": 47.5,
            "duree": 1.25,
            "dossier": f"{CAP}/boost/s10",
            "etapes": ["saisie", "saisie-fin", "survol"],
            "viewport": [1600, 900],
            "zone": [100, 296, 532, 474],
            "clavier_db": -17,
            "textes": [
                {"t": 0.1, "duree": 1.0, "texte_id": "t_chaton", "style": "legende", "position": "haut"}
            ]
        },
        {
            "type": "plan",
            "debut": 48.75,
            "duree": 2.25,
            "fichier": "plan:p20",
            "fichier_vertical": "plan_v:p24",
            "entree": 0.3,
            "vitesse": 1.0,
            "cadrage": [[0.0, 0.5, 0.52, 1.0], [2.25, 0.5, 0.5, 1.08]],
            "cadrage_v": [[0.0, 0.5, 0.52, 1.0], [2.25, 0.5, 0.5, 1.06]],
            "flash": [[0.6, "signal", 0.08]],
            "etalonnage": "nuit_feu",
            "son_db": -2
        },
        {
            "type": "noir",
            "debut": 51.0,
            "duree": 1.0,
            "texte_id": "bonus"
        }
    ]

    montage = {
        "marque": "../../marque-v7.json",
        "bpm": BPM,
        "phase": 0.0,
        "duree": 52.0,
        "musique": {
            "fichier": "musique:m1",
            "entree": 0.0,
            "gain_db": -6.5,
            "coupes": [],
            "trous": [
                [2.0, 3.3],
                [7.0, 8.6],
                [19.0, 21.8],
                [43.0, 44.4],
                [47.5, 52.0]
            ],
            "ducking_db": 8.0
        },
        "dossiers_voix": {"fr": "voix/fr", "en": "voix/en"},
        "voix": [
            {"id": "v01", "t": 2.1, "db": 0.0},
            {"id": "v02", "t": 5.1, "db": 0.0},
            {"id": "v03", "t": 18.0, "db": 0.0},
            {"id": "v04", "t": 44.7, "db": 0.0}
        ],
        "sfx": [
            {"t": 0.0, "type": "impact", "db": -8, "duree": 0.6},
            {"t": 1.0, "type": "whoosh", "db": -12, "duree": 0.25},
            {"t": 3.5, "type": "riser", "db": -10, "duree": 1.0},
            {"t": 4.5, "type": "boom", "db": -7, "duree": 0.8},
            {"t": 10.5, "type": "impact", "db": -8, "duree": 0.5},
            {"t": 14.0, "type": "whoosh", "db": -12, "duree": 0.3},
            {"t": 16.0, "type": "sub", "db": -7, "duree": 1.0},
            {"t": 19.0, "type": "chute", "db": -9, "duree": 0.8},
            {"t": 25.5, "type": "explosion", "db": -8, "duree": 0.8},
            {"t": 28.0, "type": "whoosh", "db": -13, "duree": 0.25},
            {"t": 29.5, "type": "whoosh", "db": -13, "duree": 0.25},
            {"t": 31.0, "type": "impact", "db": -9, "duree": 0.4},
            {"t": 32.0, "type": "frappe", "db": -10, "duree": 0.3},
            {"t": 33.0, "type": "frappe", "db": -10, "duree": 0.3},
            {"t": 34.0, "type": "frappe", "db": -10, "duree": 0.3},
            {"t": 35.0, "type": "frappe", "db": -10, "duree": 0.3},
            {"t": 36.0, "type": "boom", "db": -8, "duree": 0.6},
            {"t": 39.0, "type": "riser", "db": -9, "duree": 1.0},
            {"t": 40.5, "type": "impact", "db": -7, "duree": 0.9},
            {"t": 44.5, "type": "boom", "db": -8, "duree": 1.2}
        ],
        "segments": segments
    }
    return montage


def assemble_dossier():
    cles = []
    for cid, fmt, seed, lens, desc in CLES_SPEC:
        prompt = CAM_PREFIX.format(lens=lens) + desc
        cles.append({
            "id": cid,
            "format": fmt,
            "graine": seed,
            "prompt": prompt
        })

    plans = []
    for pid, cid, fmt, imgs, seed, operator, action, sound in PLANS_SPEC:
        prompt = VID_PREFIX.format(operator=operator, action=action, sound=sound)
        plans.append({
            "id": pid,
            "cle": cid,
            "format": fmt,
            "images": imgs,
            "graine": seed,
            "prompt": prompt
        })

    return {
        "equipe": "gemini",
        "titre": "LA FIN DU JEU.",
        "cles": cles,
        "plans": plans,
        "voix": VOIX_SPEC,
        "temps_forts": TEMPS_FORTS_SPEC,
        "musiques": MUSIQUES_SPEC,
        "montage": build_montage()
    }


def validate_dossier(d):
    # 1. Budget checks
    cles = d["cles"]
    plans = d["plans"]
    assert len(cles) <= 24, f"Too many cles: {len(cles)}"
    p_169 = [p for p in plans if p["format"] == "16:9"]
    p_916 = [p for p in plans if p["format"] == "9:16"]
    u_169 = sum(1 if p["images"] == 124 else 2 for p in p_169)
    u_916 = sum(1 if p["images"] == 124 else 2 for p in p_916)
    assert u_169 <= 20, f"16:9 units {u_169} > 20"
    assert u_916 <= 4, f"9:16 units {u_916} > 4"
    assert len(d["voix"]) <= 8, f"Too many voix: {len(d['voix'])}"
    assert len(d["musiques"]) == 3, f"Expected 3 musiques, got {len(d['musiques'])}"

    # 2. Forbidden words check in cles and plans prompts
    forbidden = [
        r"\bcinematic\b", r"\bepic\b", r"\bglowing\b", r"\bincandescent\b",
        r"\bmajestic\b", r"dramatic lighting", r"hyper-detailed", r"\b8k\b",
        r"\brender\b", r"\bcgi\b", r"\bunreal\b", r"concept art",
        r"teal and orange", r"teal-and-orange", r"\bvibrant\b", r"\bstunning\b",
        r"\bjedi\b", r"\bsith\b", r"lightsaber", r"star wars", r"x-wing", r"tie fighter"
    ]
    for item in cles + plans:
        pr = item["prompt"]
        for pat in forbidden:
            m = re.search(pat, pr, flags=re.IGNORECASE)
            assert not m, f"Forbidden word '{m.group(0)}' in {item['id']}: {pr}"

    # 3. Check mandatory recipe prefixes
    for c in cles:
        assert c["prompt"].startswith("Production still from a live-action feature film, photographed on location on 35mm film (Kodak Vision3 500T) with a"), f"Bad prefix on {c['id']}"
    for p in plans:
        assert p["prompt"].startswith("For the target video, at 0.00 seconds into the target video, <Picture 1> (from [Shot 1]) is fully referenced.\n\nintegrated_multimodal_description: [Shot 1] Live-action footage shot on 35mm film,"), f"Bad prefix on {p['id']}"
        assert "No text, no logos." in p["prompt"], f"Missing 'No text, no logos.' in {p['id']}"
        assert "overall_soundscape:" in p["prompt"], f"Missing soundscape in {p['id']}"
        assert "non_diegetic_music: N/A" in p["prompt"], f"Missing non_diegetic_music in {p['id']}"

    # 4. Check montage timeline continuity, 24fps quantization, source durations, and text IDs
    textes = json.load(open(HERE / "textes.json"))["fr"]
    marque_textes = json.load(open(HERE.parent.parent / "marque-v7.json"))["textes"]["fr"]
    all_text_ids = set(textes.keys()) | set(marque_textes.keys())

    segs = d["montage"]["segments"]
    cur = 0.0
    carton_count = 0
    plan_ids_169 = {p["id"]: p for p in p_169}
    plan_ids_916 = {p["id"]: p for p in p_916}
    used_plans = set()

    for i, s in enumerate(segs):
        assert abs(s["debut"] - cur) < 1e-6, f"Gap/overlap at segment {i}: debut={s['debut']} vs cur={cur}"
        frames_start = round(s["debut"] * 24)
        frames_end = round((s["debut"] + s["duree"]) * 24)
        assert abs(frames_start / 24 - s["debut"]) < 1e-6, f"Segment {i} debut {s['debut']} not exact on 24fps"
        assert abs(frames_end / 24 - (s["debut"] + s["duree"])) < 1e-6, f"Segment {i} end not exact on 24fps"
        cur += s["duree"]

        if s["type"] == "carton":
            carton_count += 1
        if "texte_id" in s:
            assert s["texte_id"] in all_text_ids, f"Unknown texte_id {s['texte_id']}"
        for tx in s.get("textes", []):
            assert tx["texte_id"] in all_text_ids, f"Unknown overlay texte_id {tx['texte_id']}"

        if s["type"] == "plan":
            f = s["fichier"]
            assert f.startswith("plan:"), f"Invalid plan ref {f}"
            pid = f.split(":")[1]
            assert pid in plan_ids_169, f"Unknown 16:9 plan {pid}"
            used_plans.add(pid)
            # Check source duration with speed integral
            entree = s.get("entree", 0.0)
            vit = s.get("vitesse", 1.0)
            if isinstance(vit, (int, float)):
                consumed = s["duree"] * float(vit)
            else:
                # piecewise linear integration
                consumed = 0.0
                for j in range(len(vit) - 1):
                    t0, v0 = vit[j]
                    t1, v1 = vit[j + 1]
                    consumed += (t1 - t0) * 0.5 * (v0 + v1)
            max_dur = plan_ids_169[pid]["images"] / 24.0
            assert entree + consumed <= max_dur - 0.15, f"Plan {pid} exceeds source: {entree + consumed:.3f}s > {max_dur:.3f}s"

            if "fichier_vertical" in s:
                fv = s["fichier_vertical"]
                assert fv.startswith("plan_v:"), f"Invalid plan_v ref {fv}"
                pvid = fv.split(":")[1]
                assert pvid in plan_ids_916, f"Unknown 9:16 plan {pvid}"
                used_plans.add(pvid)
            else:
                assert "cadrage_v" in s, f"Missing cadrage_v on segment {i} ({pid})"

        if s["type"] == "mosaique":
            for r in s["rushes"]:
                pid = r["fichier"].split(":")[1]
                assert pid in plan_ids_169
                used_plans.add(pid)

    assert 40.0 <= cur <= 70.0, f"Total duration {cur}s outside 40..70s"
    assert carton_count == 1, f"Expected 1 carton, got {carton_count}"
    assert len(used_plans) == len(plans), f"Unused plans: {set(p['id'] for p in plans) - used_plans}"
    print(f"VALIDATION OK: {len(cles)} cles, {u_169}u 16:9, {u_916}u 9:16, {len(d['voix'])} voix, {len(d['musiques'])} musiques, {len(segs)} segments, duree={cur:.2f}s.")


if __name__ == "__main__":
    dossier = assemble_dossier()
    validate_dossier(dossier)
    out_path = HERE / "dossier.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(dossier, f, ensure_ascii=False, indent=2)
    print(f"Wrote {out_path} ({out_path.stat().st_size} bytes)")
