"""Équipe Opus, film V7 « Chez toi. » : fabrique dossier.json (écrit à l'aveugle, avant lecture des autres dossiers).
Idée : une seule personne, son vrai appartement, une vraie rue un soir de pluie. Elle tape trois mots ; le monde réel, devant sa
fenêtre, devient le film. Réel d'abord, effet ensuite, dans le même lieu (recherche 23 §4.10) : c'est ce qui rend le dragon crédible.
Grille : 120 BPM visés (temps = 0,5 s) ; la chaîne recale sur le tempo mesuré.
  python3 fabriquer.py > dossier.json
"""
import json

B = 0.5
CAP = "/home/pc6/nexora-creative-data/promo/v6-creative/captures"
FILM = ("Production still from a live-action feature film, photographed on location on 35mm film (Kodak Vision3 500T) with {o}; "
        "natural exposure, visible film grain, slight halation around bright sources, soft lens imperfections, ")
VID = ("For the target video, at 0.00 seconds into the target video, <Picture 1> (from [Shot 1]) is fully referenced.\n\n"
       "integrated_multimodal_description: [Shot 1] Live-action footage shot on 35mm film, {op}, natural motion blur from a "
       "180-degree shutter, slight focus breathing, real physics and weight, practical light, rain and smoke, film grain. {a} "
       "No text, no logos, no letters anywhere.\n\noverall_soundscape: {s}\n\nnon_diegetic_music: N/A")
LEA = "a woman in her thirties with short dark hair, an oversized grey hoodie and plain clothing with no logo"
LIEU = "a small third-floor apartment in an old brick building in Montreal, a rainy autumn night, wet street and orange sodium street lights outside"

# id : (objectif, image clé, opérateur, action, son, format)
P = {
    "p01": ("a Zeiss 100mm macro lens through a rain-streaked window", f"extreme close-up through {LIEU.split(',')[0]}'s rain-streaked kitchen window at night: "
            "a huge reptilian golden eye with a vertical pupil fills the glass from outside, wet scaled skin, raindrops on the window, a "
            "warm kitchen lamp reflected in the glass", "static macro lens, then a tiny pull back", "The giant eye opens slowly and its pupil "
            "contracts; rain runs down the glass; the glass fogs with the creature's breath.", "Rain on glass, a deep slow breath, a low growl."),
    "p02": ("a 32mm lens, handheld", f"inside {LIEU}: {LEA} stands frozen in her small kitchen, seen from behind, a laptop open on the table, "
            "while a gigantic scaled snout and eye press against the window, steam of breath on the glass, the kitchen lamp the only light",
            "handheld camera slowly pulling back", "She steps back from the window, bumping a chair; the creature's breath fogs the window and "
            "a plate rattles on the table.", "Fridge hum, rain, a chair scraping, a huge slow breath outside."),
    "p03": ("an Arri Alexa Mini with a 24mm lens on the balcony, rain drops on the lens", f"from a third-floor balcony over a real narrow Montreal "
            "street at night in heavy rain: a huge dark dragon with wet, scarred leathery hide stands in the middle of the street between "
            "parked cars, its wings half open, lit by orange street lights and car headlights, steam rising from its body",
            "handheld camera on the balcony, strong shake", "The dragon lifts its head and roars up at the camera, car alarms go off, rain "
            "blows sideways, a car's windows shatter.", "Huge roar, car alarms, rain, glass shattering, wind."),
    "p04": ("a 18mm lens, handheld, dirt and rain on the lens", "point of view from a rainy brick balcony at night: the dragon's head and neck "
            "sweep past a few metres away, enormous, wet hide lit by orange street lights, a potted plant and a bicycle on the balcony",
            "handheld operator ducking as the creature passes", "The dragon's head passes right in front of the balcony from left to right, "
            "its breath blows rain and leaves into the lens, the railing shakes.", "Gusting wind, rain, deep breathing, a metal railing rattling."),
    "p05": ("an Arri Alexa 65 with a 35mm lens from a rooftop", "night over a real city of brick buildings and church steeples in the rain: "
            "the gigantic dark underside of a battered grey steel spaceship, kilometres long, slowly descends through the low clouds, its "
            "hull scarred, rusted, panel lines and small warm lights, the clouds part around it, the whole neighbourhood lies under its shadow, "
            "people on balconies in the foreground looking up for scale", "camera on a tripod slowly tilting up", "The colossal ship pushes "
            "through the clouds, rain streams off its hull, the street lights below flicker.", "A sub-bass rumble that shakes windows, rain, distant dogs barking."),
    "p06": ("a 50mm lens, handheld, street level", "wet street at night, ordinary people in raincoats and pyjamas stand in the street and look "
            "up, faces lit by a cold white light from above, rain, parked cars, a man holds an umbrella that blows inside out",
            "handheld camera among the crowd", "A man in a raincoat (S1) points up and shouts: <d>[French] Regarde en haut !</d> The crowd steps "
            "back as the light sweeps over them.", "Murmurs, rain, a deep rumble from above, the man shouting."),
    "p07": ("a long Canon 300mm lens from across the street", "night, heavy rain, on the flat roof of the brick building across the street: "
            "two stunt performers in soaked dark coats fight with two orange energy blades, the blades are the only light, practical orange "
            "light on the wet roof, steam where the rain hits the blades, water tanks and chimneys around them", "long-lens camera with a "
            "slight pan, telephoto compression", "The two fighters clash three times, sparks and steam burst at each impact, one slips on the wet "
            "roof and rolls.", "Rain, electric hum of the blades, heavy impacts, boots on wet tar."),
    "p08": ("a handheld Arri Alexa Mini with a 32mm lens", "close on the rooftop fight in the rain at night: two crossed orange energy blades "
            "lock between two soaked fighters, sparks and steam explode at the contact point, one fighter's wet face lit orange, gritted teeth",
            "handheld camera pushing in", "The blades grind together throwing sparks; the fighter (S1) growls: <d>[French] Encore !</d> and "
            "shoves; steam bursts.", "Crackling blades, rain, a growl, a heavy impact."),
    "p09": ("an Arri Alexa 65 with a 40mm lens from a high rooftop", "the whole city at night from a rooftop: the dragon flies across the frame "
            "in front of the colossal spaceship hovering over the steeples, three explosions of fire and black smoke bloom along the ship's "
            "hull, rain, the city lights below, real atmospheric haze", "camera on a tripod, slight pan following the dragon", "The dragon "
            "breathes a long jet of fire along the hull; explosions roll and debris falls slowly into the clouds.", "Distant explosions, the roar of fire, wind, a deep hum."),
    "p10": ("an 85mm lens, handheld", f"{LEA} on her rainy balcony at night, seen from behind and the side, her face hidden by her hood, lit "
            "orange by distant explosions in the sky, rain on her shoulders, a laptop glowing on the table behind her", "handheld camera "
            "slowly circling her", "She steps forward to the railing and her shoulders shake with laughter as orange flashes light the rain.",
            "Rain, distant explosions, her laugh."),
    "p11": ("a 24mm lens from the street, looking up", "night street in the rain: the dragon perched on the roof edge of the brick building, "
            "head raised, breathing a huge plume of real fire straight up into the rain, the fire lighting the wet bricks and the windows",
            "camera on the ground, slow push in", "The dragon breathes fire straight up into the night sky, steam bursts where the rain meets "
            "the fire, sparks rain down on the street.", "A roaring jet of fire, hissing steam, rain."),
    "p12": ("a 40mm lens inside the kitchen", f"inside the small kitchen at night: {LEA} sits at the table in front of her closed laptop, seen in "
            "three-quarter view from behind, while outside the window the dragon's huge eye calmly watches her, rain, the lamp light",
            "static camera, very slow push in", "She taps the closed laptop, sighs and says to herself (S1), lips barely moving: <d>[French] "
            "Bon. Demain, je fais pire.</d> The eye outside blinks.", "Rain, fridge hum, her quiet voice, a slow breath outside."),
    "p13": ("an Arri Alexa Mini with a 24mm lens from the balcony", "night street in heavy rain: the dragon crouches between parked cars and "
            "spreads its huge wet wings, about to take off, water spraying off its hide, street lights and a bus stop for scale",
            "handheld camera on the balcony tilting up", "The dragon beats its wings once and leaps into the air, a wave of rain water "
            "slams over the parked cars and the bus stop glass, the camera tilts up as it rises past the balcony.",
            "A thunderous wingbeat, water crashing on cars, car alarms, rain."),
    "p14": ("a 35mm lens from a rooftop", "night city in the rain: a small battered grey military aircraft with hard lights screams low between "
            "brick buildings and church steeples under the colossal hovering ship, its exhaust heat-shimmer and spray, real rain",
            "camera on a rooftop panning fast with the aircraft", "The aircraft streaks through the frame between the buildings, rain swirls "
            "in its wake, windows rattle.", "A jet roar passing close, rain, rattling windows."),
    "p15": ("a handheld Arri Alexa Mini with a 24mm lens", "night rooftop in the rain: a fighter swings an orange energy blade through a large "
            "wooden rooftop water tank, the tank splits and a wall of water bursts out over the roof, steam, sparks",
            "handheld camera, the water hits the lens", "The blade cuts the tank in one stroke, thousands of litres of water burst out and "
            "flood the roof, steam explodes where water hits the blade.", "A heavy slicing hum, wood splitting, a rush of water, hissing steam."),
    "p16": ("a 40mm lens inside the kitchen", f"inside the small kitchen at night: {LEA} opens the window and holds out a steaming mug of coffee "
            "to the enormous dragon's snout that fills the window, rain, the kitchen lamp", "static camera", "The dragon sniffs the coffee "
            "and huffs a small puff of smoke that makes her hair fly; she laughs.", "Rain, a snort, a small puff of fire, her laugh."),
}
V = {"p03": "p03", "p05": "p05", "p09": "p09", "p11": "p11"}  # 4 plans natifs 9:16


def cles():
    out = []
    for i, (pid, (o, cle, *_)) in enumerate(P.items()):
        out.append({"id": f"k{pid[1:]}", "format": "16:9", "graine": 7100 + i, "prompt": FILM.format(o=o) + cle})
        if pid in V:
            out.append({"id": f"kv{pid[1:]}", "format": "9:16", "graine": 7200 + i, "prompt": FILM.format(o=o) + cle})
    return out


def plans():
    out = []
    for i, (pid, (o, cle, op, a, s)) in enumerate(P.items()):
        out.append({"id": pid, "cle": f"k{pid[1:]}", "format": "16:9", "images": 124, "graine": 7300 + i, "prompt": VID.format(op=op, a=a, s=s)})
        if pid in V:
            out.append({"id": f"{pid}v", "cle": f"kv{pid[1:]}", "format": "9:16", "images": 124, "graine": 7400 + i,
                        "prompt": VID.format(op=op, a=a, s=s)})
    return out


def t(b):
    return round(b * B, 3)


SEG = []


def plan(b0, b1, pid, entree, **kw):
    s = {"type": "plan", "debut": t(b0), "duree": round(t(b1) - t(b0), 3), "fichier": f"plan:{pid}", "entree": entree, "etalonnage": "nuit_feu", **kw}
    if pid in V:
        s["fichier_vertical"] = f"plan_v:{pid}"
    SEG.append(s)


# ---- montage (sans narration ; trois répliques dans l'image) ----
plan(0, 3, "p01", 1.0, son_db=-2, secousses=[[0.0, 6, 0.3]])                       # accroche : l'œil s'ouvre
plan(3, 8, "p02", 0.6, son_db=-6, cadrage=[[0, .5, .5, 1], [2.5, .5, .5, 1.08]])   # elle recule
SEG.append({"type": "saisie", "debut": t(8), "duree": t(3), "dossier": f"{CAP}/boost/o1", "etapes": ["saisie", "saisie-fin"],
            "viewport": [1600, 900], "zone": [100, 296, 532, 474], "zone_texte": [104, 300, 470, 345], "zoom_texte": 1.3, "zoom_texte_v": 2.0})
SEG.append({"type": "boost", "debut": t(11), "duree": t(2), "dossier": f"{CAP}/boost/o1", "viewport": [1600, 900], "zone": [100, 490, 532, 765],
            "termes_cles": ["dragon", "rue", "pluie", "rugit"]})
plan(13, 18, "p03", 0.8, son_db=-2, secousses=[[0.5, 22, 0.8]])                    # DROP 6,5 s : le dragon dans la rue
plan(18, 21, "p04", 0.5, son_db=-4, secousses=[[0.3, 16, 1.0]])
plan(21, 25, "p13", 0.6, son_db=-3)                                                 # il décolle
SEG.append({"type": "titre", "debut": t(25), "duree": t(2), "texte_id": "plus_gros", "style": "claque", "sur_video": "precedent"})
plan(27, 35, "p05", 0.4, son_db=-2, cadrage=[[0, .5, .6, 1], [4, .5, .45, 1.05]])  # le vaisseau (respiration)
plan(35, 40, "p06", 0.6, son_db=0)                                                  # « Regarde en haut ! »
plan(40, 44, "p14", 0.8, son_db=-3)
SEG.append({"type": "titre", "debut": t(44), "duree": t(2), "texte_id": "plus_fou", "style": "claque", "sur_video": "precedent"})
plan(46, 50, "p07", 0.5, son_db=-4)
plan(50, 53, "p15", 1.0, son_db=-3)
plan(53, 57, "p08", 1.6, son_db=0, flash=[[0.2, "os", 0.06]])                       # « Encore ! » + trou musical
SEG.append({"type": "avant_apres", "debut": t(57), "duree": t(6), "couches": [
    {"fichier": f"{CAP}/detourage-src/duel-795.mp4", "entree": 0.2, "texte_id": "brut"},
    {"fichier": f"{CAP}/detourage/sorties/apercu-echecs.mp4", "entree": 0.2, "texte_id": "masque"},
    {"fichier": f"{CAP}/detourage/sorties/composite.mp4", "entree": 0.2, "texte_id": "final"}]})
SEG.append({"type": "saisie", "debut": t(63), "duree": t(5), "dossier": f"{CAP}/boost/tout", "dossier_en": f"{CAP}/boost/tout-en",
            "etapes": ["saisie", "saisie-fin"], "viewport": [1600, 900], "zone": [100, 296, 532, 474], "zone_texte": [104, 300, 470, 345],
            "zoom_texte": 1.4, "zoom_texte_v": 2.2})
SEG.append({"type": "noir", "debut": t(68), "duree": t(1)})                         # vrai silence avant la reprise
plan(69, 77, "p09", 0.3, son_db=-2, secousses=[[1.0, 14, 1.5]])                    # TOUT : climax 34,5 s
plan(77, 81, "p11", 0.8, son_db=-4)
plan(81, 85, "p10", 0.6, son_db=-6)
plan(85, 95, "p12", 0.2, son_db=0)                                                  # « Bon. Demain, je fais pire. »
SEG.append({"type": "carton", "debut": t(95), "duree": t(6)})
plan(101, 109, "p16", 0.4, son_db=0)                                                # scène bonus : le café

DOSSIER = {
    "equipe": "opus", "titre": "Chez toi.",
    "concept": "Une femme ordinaire tape trois mots dans Creative ; devant sa fenêtre, sa vraie rue de Montréal devient le film.",
    "captures_demandees": [{"id": "o1", "mots": "dragn dans ma rue"}],
    "cles": cles(), "plans": plans(),
    "voix": [{"id": "d1", "moteur": "h3-natif", "plan": "p06", "texte": "Regarde en haut !"},
             {"id": "d2", "moteur": "h3-natif", "plan": "p08", "texte": "Encore !"},
             {"id": "d3", "moteur": "h3-natif", "plan": "p12", "texte": "Bon. Demain, je fais pire."}],
    "temps_forts": [{"t": 0.0, "evenement": "l'œil s'ouvre : sub seul"}, {"t": 1.5, "evenement": "le motif de 4 notes au célesta, seul"},
                    {"t": 4.0, "evenement": "frappe des touches : pulsation sèche, montée"}, {"t": 6.5, "evenement": "DROP : le dragon rugit dans la rue"},
                    {"t": 12.5, "evenement": "« PLUS GROS. » impact"}, {"t": 13.5, "evenement": "le vaisseau : tout se retire, grave tenu"},
                    {"t": 17.5, "evenement": "« Regarde en haut ! » relance des tambours"}, {"t": 22.0, "evenement": "« PLUS FOU. » impact"},
                    {"t": 26.5, "evenement": "« Encore ! » : coupure de 0,7 s (son natif)"}, {"t": 28.5, "evenement": "avant/après : pulsation"},
                    {"t": 31.5, "evenement": "« tout » : montée, roulement"}, {"t": 34.0, "evenement": "silence total 0,5 s"},
                    {"t": 34.5, "evenement": "REPRISE : thème complet avec chœur, le plus fort"}, {"t": 40.5, "evenement": "elle rit : le motif en grand"},
                    {"t": 42.5, "evenement": "cuisine : tout retombe, motif au célesta"}, {"t": 47.5, "evenement": "carton : coup final"},
                    {"t": 50.5, "evenement": "bonus : le motif en clin d'œil, pizzicato"}],
    "musiques": [
        {"id": "m1", "moteur": "lyria-pro", "prompt": (
            "Instrumental hybrid orchestral trailer score with a memorable four-note signature motif, 120 BPM, D minor resolving to "
            "F major. 0-1.5 s: no instruments, a deep sub-bass swell. 1.5-4 s: the four-note motif alone on a celesta. 4-6.5 s: dry "
            "ticking pulse and fast riser. 6.5 s exact: HUGE drop: taikos, low brass stabs, distorted cello ostinato, driving. "
            "12.5 s: big hit. 13.5-17.5 s: pull back to one sustained low brass note and sub rumble. 17.5-26.5 s: drums return, "
            "brass plays the motif, rising. 26.5-27.2 s: complete silence. 27.2-31.5 s: pulsing groove. 31.5-34 s: snare roll and "
            "riser. 34-34.5 s: total silence. 34.5 s: the biggest moment: full orchestra and choir play the motif triumphantly in F "
            "major. 42.5-47.5 s: drops to the motif alone on celesta. 47.5 s: one final deep boom. 50.5-54.5 s: the motif as a playful "
            "pizzicato, ending cleanly at 55 s.")},
        {"id": "m2", "moteur": "lyria-pro", "prompt": (
            "Instrumental cinematic electronic and heavy percussion score, thrilling and fun, 120 BPM, a memorable four-note synth "
            "motif. 0-4 s: near silence, sub swell, the motif once on a muted synth. 4-6.5 s: riser. 6.5 s: big drop: hybrid drums, "
            "pulsing bass, brass hits. 13.5-17.5 s: pull back to a drone. 17.5-26.5 s: drums rebuild. 26.5-27.2 s: silence. "
            "27.2-34 s: rising build. 34-34.5 s: silence. 34.5-42.5 s: full climax, the motif on huge synth brass. 42.5-47.5 s: motif "
            "alone. 47.5 s: final boom. 50.5-55 s: light playful outro.")},
        {"id": "m3", "moteur": "music3", "prompt": (
            "Hybrid orchestral trailer, 120 BPM, four-note celesta motif, sub-bass intro, huge drop at 6.5 seconds, quiet from 13.5 to "
            "17.5 seconds, build, silence at 34 seconds, triumphant choir climax at 34.5 seconds, quiet celesta at 42.5 seconds, final "
            "boom at 47.5 seconds, playful pizzicato ending.")}],
    "montage": {"marque": "marque-v7.json", "textes": "textes.json", "bpm": 120, "phase": 0.0,
                "musique": {"fichier": "musique:m1", "entree": 0.0, "gain_db": -3, "ducking_db": 6, "calage": "auto",
                            "trous": [[t(53.4), t(54.8)], [t(68), t(69)]]},
                "voix": [], "sfx": [{"t": t(13), "type": "boom", "db": -4}, {"t": t(25), "type": "impact", "db": -6},
                                    {"t": t(44), "type": "impact", "db": -6}, {"t": t(69), "type": "boom", "db": -3},
                                    {"t": t(95), "type": "boom", "db": -5}],
                "duree": t(109), "segments": SEG},
}
if __name__ == "__main__":
    print(json.dumps(DOSSIER, ensure_ascii=False, indent=1))
