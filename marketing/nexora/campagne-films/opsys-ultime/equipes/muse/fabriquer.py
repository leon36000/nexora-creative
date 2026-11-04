# -*- coding: utf-8 -*-
"""Fabrique equipes/muse/dossier.json — concept « L'USINE INVISIBLE »."""
import json

EQUIPE = "muse"

def H(summary, desc, action, sound, dialogue=None):
    t = "summary:\n" + summary + "\n\ndetailed_description:\n" + desc
    t += "\n[Shot 1] " + action + " No text, no logos.\n"
    if dialogue:
        t += "\ndialogue:\n" + dialogue + "\n"
    t += "\noverall_soundscape:\n" + sound + "\n\nnon_diegetic_music:\nN/A"
    return t

BASE = ("Cinematic frame from a 2026 feature film, shot on a large-format digital "
        "cinema camera, real exposure, rich contrast, natural film colour, fine grain. ")

personnages = [
 {"id":"etienne","nom":"Étienne","role":"représentant",
  "fiche":("Character reference sheet, plain light-grey studio background: on the left Etienne, "
  "a Quebec man in his early thirties, short brown hair, light stubble, athletic build, wearing a navy "
  "work jacket over a grey hoodie and work boots, holding a smartphone; on the right a large close-up "
  "of his face with a friendly grin. Photorealistic, neutral lighting. Plain clothing with no logo, no text, no letters anywhere."),
  "voix":"drama3-adamqc"},
 {"id":"marie","nom":"Marie","role":"adjointe",
  "fiche":("Character reference sheet, plain light-grey studio background: on the left Marie, "
  "a Quebec woman in her late twenties, long dark-brown hair tied back, bright eyes, wearing a teal "
  "blouse with a call-center headset; on the right a large close-up of her smiling face. Photorealistic, "
  "neutral lighting. Plain clothing with no logo, no text, no letters anywhere."),
  "voix":"eleven-jeannemance"},
 {"id":"morin","nom":"Morin","role":"employé de chantier",
  "fiche":("Character reference sheet, plain light-grey studio background: on the left Morin, "
  "a Quebec man in his forties, shaved head, short beard, solid build, wearing an orange high-visibility "
  "vest over a dark hoodie and work gloves; on the right a large close-up of his weathered smiling face. "
  "Photorealistic, neutral lighting. Plain clothing with no logo, no text, no letters anywhere."),
  "voix":"eleven-adamqc"},
 {"id":"patron","nom":"Le patron","role":"administrateur",
  "fiche":("Character reference sheet, plain light-grey studio background: on the left the owner, "
  "a Quebec man in his fifties, short grey beard, glasses, calm confident eyes, wearing a navy quilted "
  "vest over a plaid shirt; on the right a large close-up of his face. Photorealistic, neutral lighting. "
  "Plain clothing with no logo, no text, no letters anywhere."),
  "voix":"eleven-frederic"},
 {"id":"vox","nom":"Vox","role":"avatar des départements",
  "fiche":("Holographic avatar reference on a dark background: on the left a feminine face sculpted from "
  "fine ion-blue points of light, glowing wireframe bust, elegant and futuristic; on the right a close-up "
  "of her luminous eye with a single warm orange glint. No text, no logos."),
  "voix":"eleven-amelie"},
]
lieux = [
 {"id":"maison","fiche":("Location plate: a suburban Quebec house with new warm-grey horizontal siding, "
  "white soffit and fascia, small front lawn, morning sun. Photorealistic, no text, no logos.")},
 {"id":"serveur","fiche":("Location plate: a dark vast server hall, rows of tall racks with ion-blue lights "
  "receding into haze, one warm orange lamp glowing far away. Cinematic, no text, no logos.")},
 {"id":"chantier","fiche":("Location plate: a renovation work site at golden hour, scaffold along a house wall, "
  "a pickup truck, tool crates. Photorealistic, no text, no logos.")},
]
cles = [
 {"id":"k01","format":"16:9","prompt":("Close-up of a smartphone held up before a Quebec house wall with fresh siding, "
  "morning light, shallow depth of field. Photorealistic, no text, no logos.")},
 {"id":"k02","format":"16:9","prompt":("A glowing blue signal beam rising from a rooftop phone into dramatic clouds, "
  "birds, sun flare. Cinematic, no text, no logos.")},
 {"id":"k03","format":"16:9","prompt":("Inside a dark server corridor, ion-blue rack lights, a luminous beam racing "
  "along the floor toward camera, haze. Cinematic, no text, no logos.")},
 {"id":"k04","format":"16:9","prompt":("A worker tapping a badge on a time-clock post at dawn on a work site, "
  "golden light, shallow depth of field. Photorealistic, no text, no logos.")},
]
voix = [
 {"id":"v01","role":"narrateur","voix":"drama3-frederic","vitesse":1.1,"prises":2,
  "direction":"Narrateur quebecois, energie brute, rythme vif, voix qui pousse, jamais lisse.",
  "texte":"Une photo. Pis toute une usine se met au travail."},
 {"id":"v02","role":"representant","voix":"drama3-adamqc","vitesse":1.1,"prises":2,
  "direction":"Jeune representant enthousiaste, parle vite, accent quebecois naturel.",
  "texte":"Mur arrière, revêtement... c'est envoyé!"},
 {"id":"v03","role":"avatar","voix":"eleven-amelie","vitesse":1.0,"prises":2,
  "direction":"[warm, professional, efficient]",
  "texte":"Photo reçue. Mesures en cours."},
 {"id":"v04","role":"avatar","voix":"eleven-amelie","vitesse":1.0,"prises":2,
  "direction":"[warm, professional, efficient]",
  "texte":"Soumission prête : dix-huit mille neuf cent quarante dollars. J'attends ton approbation."},
 {"id":"v05","role":"administrateur","voix":"eleven-frederic","vitesse":1.0,"prises":2,
  "direction":"[energetic, confident, natural Quebecois]",
  "texte":"Montre-moi les profits avec les nouveaux ratios."},
 {"id":"v06","role":"avatar","voix":"eleven-amelie","vitesse":1.0,"prises":2,
  "direction":"[warm, professional, efficient]",
  "texte":"Profits anticipés, mis à jour : la productivité a monté de sept pour cent."},
 {"id":"v07","role":"avatar","voix":"eleven-amelie","vitesse":1.0,"prises":2,
  "direction":"[warm, professional, efficient]",
  "texte":"Voici la cédule des trois prochaines semaines."},
 {"id":"v08","role":"adjointe","voix":"eleven-jeannemance","vitesse":1.0,"prises":2,
  "direction":"[warm, professional, efficient]",
  "texte":"Vous avez rendez-vous avec monsieur Thibault à quatorze heures, pis j'ai déplacé votre seize heures comme vous me l'avez demandé."},
 {"id":"v09","role":"employe","voix":"eleven-adamqc","vitesse":1.0,"prises":2,
  "direction":"[energetic, confident, natural Quebecois]",
  "texte":"Dossier reçu! On part sur le chantier."},
 {"id":"v10","role":"narrateur","voix":"drama3-frederic","vitesse":1.1,"prises":2,
  "direction":"Narrateur quebecois, energie brute, rythme vif, voix qui pousse, jamais lisse.",
  "texte":"Dix départements. Une seule équipe."},
 {"id":"v11","role":"administrateur","voix":"eleven-frederic","vitesse":1.0,"prises":2,
  "direction":"[energetic, confident, natural Quebecois]",
  "texte":"Approuvé. Envoyez ça."},
 {"id":"v12","role":"narrateur","voix":"drama3-frederic","vitesse":1.1,"prises":1,
  "direction":"Narrateur quebecois, energie brute, isole, net.",
  "texte":"OPSYS. L'usine invisible."},
]

plans = [
 {"id":"p01","sequence":"S1 crochet","recette":"h3-max","images":124,"graine":101,"format":"16:9",
  "refs":["etienne","maison"],"premiere":"k01","parole":None,
  "camera":"macro, focus rack du téléphone vers la maison","effets":"flash blanc à la photo","son":"déclic photo, souffle","statut":"VISION",
  "prompt":H("A single continuous cinematic shot: a man photographs a house wall, flash freeze.",
   BASE+"A young Quebec contractor @etienne in a navy work jacket holds up a smartphone before a suburban house @maison with fresh siding, morning sun flare, shallow depth of field.",
   "Extreme close-up on the phone, @etienne taps, a white flash freezes the frame, the camera whips up to the sky. No text, no logos.",
   "Phone camera click, bright flash pop, rising wind.")},
 {"id":"p02","sequence":"S1 signal","recette":"h3-max","images":124,"graine":102,"format":"16:9",
  "refs":["maison"],"premiere":None,"parole":None,
  "camera":"grue ascendante, grand large","effets":"faisceau lumineux, impulsion","son":"montée, souffle","statut":"RÉEL",
  "prompt":H("A single continuous cinematic shot: a beam of light rises from a rooftop into the sky.",
   BASE+"A glowing ion-blue signal beam erupts from a suburban rooftop @maison and climbs into dramatic clouds, birds scattering, sun flare.",
   "The camera cranes up fast, following the beam as a pulse of light shoots upward. No text, no logos.",
   "Deep rising whoosh, crackling energy beam, wind rush.")},
 {"id":"p03","sequence":"S1 tour","recette":"h3-max","images":124,"graine":103,"format":"16:9",
  "refs":[],"premiere":"k02","parole":None,
  "camera":"filé latéral rapide, travelling","effets":"faisceau longeant câbles et pylônes","son":"bourdonnement électrique, fouet","statut":"RÉEL",
  "prompt":H("A single continuous cinematic shot: a light beam races along power lines.",
   BASE+"A luminous blue signal races along sagging power lines between wooden poles over Quebec fields at dusk, sparks and haze.",
   "Fast lateral tracking shot chasing the pulse of light from pole to pole. No text, no logos.",
   "Electric hum, rushing wind, crackling sparks.")},
 {"id":"p04","sequence":"S1 serveur","recette":"h3-max","images":124,"graine":104,"format":"16:9",
  "refs":["serveur"],"premiere":"k03","parole":None,
  "camera":"travelling avant rapide dans l'allée","effets":"racks qui s'allument en cascade","son":"vrombissement, impacts","statut":"RÉEL",
  "prompt":H("A single continuous cinematic shot: a beam dives into a giant server hall.",
   BASE+"A vast dark server hall @serveur, rows of racks igniting in ion-blue cascades as a beam of light dives down the corridor.",
   "The camera rushes forward down the aisle as lights wake in waves toward camera. No text, no logos.",
   "Deep server rumble, cascading power-up chimes, heavy impacts.")},
 {"id":"p05","sequence":"S2 usine","recette":"h3-max","images":124,"graine":105,"format":"16:9",
  "refs":["serveur"],"premiere":None,"parole":None,
  "camera":"plan large, lente montée","effets":"dix îlots lumineux + portraits holographiques","son":"pulsation, chœur de machines","statut":"RÉEL",
  "prompt":H("A single continuous cinematic shot: a server hall becomes a luminous factory.",
   BASE+"Inside the dark server hall @serveur, ten glowing work islands light up in a row, translucent holographic worker portraits rising above each, dust and haze in ion-blue light.",
   "Slow rising wide shot revealing all ten islands igniting one after another. No text, no logos.",
   "Industrial pulse, machine hums, airy metallic echoes.")},
 {"id":"p06","sequence":"S2 mesure","recette":"h3-max","images":124,"graine":106,"format":"16:9",
  "refs":["serveur"],"premiere":None,"parole":"v03",
  "camera":"orbite lente autour de l'hologramme","effets":"maison holographique qui se mesure, filet laser","son":"bips laser, voix","statut":"VISION",
  "prompt":H("A single continuous cinematic shot: a hologram measures a house, an avatar speaks.",
   BASE+"A feminine hologram made of ion-blue light points gestures over the server floor @serveur as a wireframe house assembles and laser grids sweep its walls.",
   "Slow orbit around the hologram while the wireframe house builds itself. No text, no logos.",
   "Laser scanning zaps, holographic shimmer, room tone.",
   "The hologram @vox speaks in Quebecois French, matching <Audio 1> word for word.")},
 {"id":"p07","sequence":"S2 estimation","recette":"h3-max","images":141,"graine":107,"format":"16:9",
  "refs":["serveur"],"premiere":None,"parole":"v04",
  "camera":"travelling circulaire, resserrement","effets":"document holographique qui s'assemble","son":"assemblage, voix","statut":"RÉEL",
  "prompt":H("A single continuous cinematic shot: a holographic quote assembles line by line.",
   BASE+"Above the server floor @serveur, a large holographic quote card assembles line by line in glowing blue glass, totals counting, a stamp slamming at the end.",
   "Circular tracking shot tightening on the glowing card as each glowing line locks in. No text, no logos.",
   "Glass chimes per line, deep stamp thud, shimmer.",
   "The hologram @vox speaks in Quebecois French, matching <Audio 1> word for word.")},
 {"id":"p08","sequence":"S3 approbation","recette":"h3-max","images":124,"graine":108,"format":"16:9",
  "refs":["patron"],"premiere":None,"parole":"v11",
  "camera":"gros plan, lent push-in","effets":"reflet bleu sur le visage","son":"voix, pièce feutrée","statut":"RÉEL",
  "prompt":H("A single continuous cinematic shot: a business owner approves with one word.",
   BASE+"A Quebec business owner in his fifties @patron sits at a wooden desk in a warm renovation office at dusk, practical lamps, large window, ion-blue glow on his face.",
   "Medium close-up, slow push-in as he looks into the lens and decides. No text, no logos.",
   "Quiet room tone, soft chair creak.",
   "@patron speaks in Quebecois French, matching <Audio 1> word for word.")},
 {"id":"p09","sequence":"S3 morin","recette":"h3-max","images":124,"graine":109,"format":"16:9",
  "refs":["morin","chantier"],"premiere":None,"parole":"v09",
  "camera":"steadicam, entrée dans le chantier","effets":"carte holographique reçue sur le téléphone","son":"chantier, voix","statut":"RÉEL",
  "prompt":H("A single continuous cinematic shot: a worker receives the job file on site.",
   BASE+"A sturdy Quebec worker @morin in a high-visibility vest stands on a renovation work site @chantier at golden hour, scaffold and pickup truck, glancing at his glowing phone.",
   "Steadicam walks in with him as he looks up, energised, toward the house. No text, no logos.",
   "Work-site ambience, tools clanking, distant radio.",
   "@morin speaks in Quebecois French, matching <Audio 1> word for word.")},
 {"id":"p10","sequence":"S4 pointage","recette":"h3-max","images":124,"graine":110,"format":"16:9",
  "refs":["morin"],"premiere":"k04","parole":None,
  "camera":"gros plan main-badge, tilt vers le visage","effets":"heure frappée en incrustation","son":"bip, chantier aube","statut":"EN PRÉPARATION",
  "prompt":H("A single continuous cinematic shot: a worker clocks in at dawn.",
   BASE+"At dawn on a Quebec work site, a worker @morin in a high-visibility vest taps a badge reader on a post, breath fogging, golden light flaring.",
   "Close-up on the tap, slight tilt up to his satisfied face. No text, no logos.",
   "Badge beep, cold morning wind, distant truck.")},
 {"id":"p11","sequence":"S4 adjointe","recette":"h3-max","images":141,"graine":111,"format":"16:9",
  "refs":["marie"],"premiere":None,"parole":"v08",
  "camera":"plan moyen, léger travelling","effets":"casque lumineux, onde vocale","son":"bureau, voix","statut":"VISION",
  "prompt":H("A single continuous cinematic shot: a smiling assistant calls a client.",
   BASE+"A young Quebec woman @marie with a call-center headset smiles in a bright modern office, soft daylight, blurred plants behind.",
   "Medium shot with a gentle lateral drift as she speaks warmly into her headset. No text, no logos.",
   "Bright office tone, soft keyboard clicks.",
   "@marie speaks in Quebecois French, matching <Audio 1> word for word.")},
 {"id":"p12","sequence":"S4 projection","recette":"h3-max","images":124,"graine":112,"format":"16:9",
  "refs":["patron"],"premiere":None,"parole":"v05",
  "camera":"contre-plongée légère, push-in","effets":"courbe holographique en incrustation","son":"voix, pièce feutrée","statut":"EN PRÉPARATION",
  "prompt":H("A single continuous cinematic shot: an owner questions his numbers.",
   BASE+"A Quebec business owner in his fifties @patron stands before a tall dark window at night, city lights behind, a faint blue glow rising in front of him.",
   "Low-angle medium shot, slow push-in as he asks his question. No text, no logos.",
   "Quiet room tone, low synth pulse.",
   "@patron speaks in Quebecois French, matching <Audio 1> word for word.")},
 {"id":"p13","sequence":"S4 profits","recette":"h3-max","images":124,"graine":113,"format":"16:9",
  "refs":["serveur"],"premiere":None,"parole":"v06",
  "camera":"grue descendante sur la courbe","effets":"courbe holographique ascendante","son":"montée, voix","statut":"EN PRÉPARATION",
  "prompt":H("A single continuous cinematic shot: a profit curve climbs above the servers.",
   BASE+"Above the dark server floor @serveur, a great arc of ion-blue light climbs like a profit curve, sparks and haze, one warm orange glint.",
   "Crane shot descending along the rising arc of light. No text, no logos.",
   "Rising shimmer, deep confirming boom.",
   "The hologram @vox speaks in Quebecois French, matching <Audio 1> word for word.")},
 {"id":"p14","sequence":"S4 cedule","recette":"h3-max","images":124,"graine":114,"format":"16:9",
  "refs":["serveur"],"premiere":None,"parole":"v07",
  "camera":"travelling latéral sur la grille","effets":"grille de cédule holographique","son":"clics rythmés, voix","statut":"EN PRÉPARATION",
  "prompt":H("A single continuous cinematic shot: a schedule grid fills the air.",
   BASE+"In the dark server hall @serveur, a vast holographic schedule grid hangs in the air, glowing blocks filling week after week in ion blue and warm orange.",
   "Lateral tracking shot gliding along the filling grid. No text, no logos.",
   "Rhythmic locking clicks, airy shimmer.",
   "The hologram @vox speaks in Quebecois French, matching <Audio 1> word for word.")},
 {"id":"p15","sequence":"S5 retour","recette":"h3-max","images":124,"graine":115,"format":"16:9",
  "refs":[],"premiere":"fin:p04","parole":None,
  "camera":"travelling arrière rapide","effets":"impulsion lumineuse qui repart","son":"montée inversée, fouet","statut":"RÉEL",
  "prompt":H("A single continuous cinematic shot: light races back up the server aisle.",
   BASE+"A pulse of ion-blue light races back up the dark server corridor, racks strobing past, haze tearing toward a distant bright exit.",
   "Fast backward tracking shot fleeing with the pulse toward the light. No text, no logos.",
   "Reversed rising whoosh, electric crackle.")},
 {"id":"p16","sequence":"S5 livraison","recette":"h3-max","images":124,"graine":116,"format":"16:9",
  "refs":["etienne","maison"],"premiere":None,"parole":"v02",
  "camera":"plan moyen, lever de soleil","effets":"lueur qui touche le téléphone","son":"sonnerie douce, voix","statut":"RÉEL",
  "prompt":H("A single continuous cinematic shot: a contractor gets the quote back.",
   BASE+"At sunrise before a suburban house @maison, the young contractor @etienne in a navy work jacket looks at his smartphone as a soft blue glow washes his smiling face.",
   "Medium shot, gentle push-in as he reacts with joy. No text, no logos.",
   "Soft notification chime, morning birds.",
   "@etienne speaks in Quebecois French, matching <Audio 1> word for word.")},
 {"id":"p17","sequence":"S6 quai","recette":"h3-max","images":124,"graine":117,"format":"16:9",
  "refs":["patron"],"premiere":None,"parole":None,
  "camera":"drone large, lent","effets":"reflet orange sur l'eau","son":"eau, vent, loin","statut":"RÉEL",
  "prompt":H("A single continuous cinematic shot: an owner breathes on a quiet dock.",
   BASE+"A Quebec man in his fifties @patron stands alone at the end of a wooden dock on a calm lake at dusk, warm orange sun on the water, deep peace.",
   "Wide slow drone drift pulling back from the lone figure. No text, no logos.",
   "Lapping water, soft wind, distant loon.")},
 {"id":"p18","sequence":"S6 manifeste","recette":"h3-max","images":124,"graine":118,"format":"16:9",
  "refs":["serveur"],"premiere":None,"parole":"v10",
  "camera":"montée majestueuse, grand large","effets":"dix îlots en pleine gloire","son":"apothéose, voix","statut":"RÉEL",
  "prompt":H("A single continuous cinematic shot: ten glowing departments in full glory.",
   BASE+"The vast server hall @serveur blazes with ten glowing work islands in a row, beams of light rising to the ceiling, majestic haze, one warm orange heart of light.",
   "Majestic rising wide shot over the blazing hall. No text, no logos.",
   "Epic swelling pulse, deep choir-like boom.",
   "The narrator voice speaks in Quebecois French, matching <Audio 1> word for word.")},
 {"id":"p19","sequence":"S7 paye","recette":"h3-max","images":124,"graine":119,"format":"16:9",
  "refs":["morin","chantier"],"premiere":None,"parole":None,
  "camera":"travelling bas, contre-jour","effets":"enveloppe remise, poignée de main","son":"chantier joyeux","statut":"VISION",
  "prompt":H("A single continuous cinematic shot: a worker gets his pay with a handshake.",
   BASE+"On a Quebec work site @chantier at golden hour, a foreman hands a pay envelope to the smiling worker @morin, firm handshake, dust glowing in backlight.",
   "Low tracking shot gliding past the handshake into the sun flare. No text, no logos.",
   "Happy work-site ambience, laughter, claps.")},
 {"id":"p20","sequence":"S7 carton","recette":"h3-max","images":124,"graine":120,"format":"16:9",
  "refs":["marie","patron"],"premiere":None,"parole":None,
  "camera":"fixe, lent zoom avant","effets":"visages qui se tournent vers la lumière","son":"queue musicale","statut":"RÉEL",
  "prompt":H("A single continuous cinematic shot: two faces turn toward the light.",
   BASE+"A young Quebec woman @marie and a business owner in his fifties @patron stand side by side in soft darkness, turning together toward a rising warm light.",
   "Locked-off shot with a slow push-in as they face the light. No text, no logos.",
   "Soft musical tail, gentle room tone.")},
]

# --- correctifs de cadrage voix/image ---
for p in plans:
    if p["id"]=="p07": p["images"]=158
    if p["id"]=="p11": p["images"]=243
    if p["id"]=="p13": p["images"]=141

musique = {
 "prompt":("High-energy modern corporate anthem, instrumental only, no vocals. Driving electronic drums at 124 BPM, "
  "pulsing synth bass, bright electric guitars, soaring strings and brass stabs. Structure in seconds: 0-8 rising intro with "
  "impacts, 8-30 verse groove, 30-55 build with risers, 55-75 epic chorus, 75-95 breakdown then bigger final chorus, "
  "95-110 peak with hits on every cut, 110-120 outro tail. Positive, powerful, never sad, Quebec TV commercial energy. "
  "Clean mix, wide stereo, no voices, no sound effects."),
 "bpm_vise":124, "duree_s":150,
 "coups":[{"t_s":5.2,"evenement":"le flash photo"},
          {"t_s":15.5,"evenement":"le signal frappe le serveur"},
          {"t_s":31.0,"evenement":"la soumission s'assemble"},
          {"t_s":75.0,"evenement":"la courbe des profits monte"},
          {"t_s":94.0,"evenement":"apotheose : dix departements"}]}

VDUR = {"p01":124,"p02":124,"p03":124,"p04":124,"p05":124,"p06":124,"p07":158,
        "p08":124,"p09":124,"p10":124,"p11":226,"p12":124,"p13":141,"p14":124,
        "p15":124,"p16":124,"p17":124,"p18":124,"p19":124,"p20":124}

def build_long():
    order=["p01","p02","p03","p04","p05","p06","p07","p08","p09","p10",
           "p11","p12","p13","p14","p15","p16","p17","p18","p19","p20"]
    sources={}; video=[]; cur=0; starts={}
    for i,pid in enumerate(order):
        d=VDUR[pid]
        sources[pid]={"kind":"video","duree_f":243 if pid=="p11" else (158 if pid=="p07" else 141 if pid=="p13" else 124)}
        video.append({"id":"c%02d"%(i+1),"src":pid,"entree_f":0,"duree_f":d,"vitesse":1,
                      "transition_in":{"type":"cut","duree_f":0}})
        starts[pid]=cur; cur+=d
    total=cur
    vest={"v01":84,"v02":66,"v03":51,"v04":151,"v05":82,"v06":127,"v07":79,
          "v08":221,"v09":65,"v10":60,"v11":36,"v12":43}
    for vid,l in vest.items(): sources[vid]={"kind":"audio","duree_f":l}
    sources["musique"]={"kind":"audio","duree_f":total+240}
    voix=[{"src":"v01","debut_f":10,"entree_f":0,"duree_f":84,"gain_db":0},
          {"src":"v03","debut_f":630,"entree_f":0,"duree_f":51,"gain_db":0},
          {"src":"v04","debut_f":750,"entree_f":0,"duree_f":151,"gain_db":0},
          {"src":"v11","debut_f":908,"entree_f":0,"duree_f":36,"gain_db":0},
          {"src":"v09","debut_f":1032,"entree_f":0,"duree_f":65,"gain_db":0},
          {"src":"v08","debut_f":1278,"entree_f":0,"duree_f":221,"gain_db":0},
          {"src":"v05","debut_f":1506,"entree_f":0,"duree_f":82,"gain_db":0},
          {"src":"v06","debut_f":1630,"entree_f":0,"duree_f":127,"gain_db":0},
          {"src":"v07","debut_f":1771,"entree_f":0,"duree_f":79,"gain_db":0},
          {"src":"v02","debut_f":2019,"entree_f":0,"duree_f":66,"gain_db":0},
          {"src":"v10","debut_f":2267,"entree_f":0,"duree_f":60,"gain_db":0},
          {"src":"v12","debut_f":2515,"entree_f":0,"duree_f":43,"gain_db":0}]
    plan={"version":1,"fps":24,"format":"16:9","genre":"pub","titre":"L'usine invisible",
          "sources":sources,"video":video,
          "audio":{"musique":{"src":"musique","entree_f":0,"duree_f":total,"gain_db":-8,"fondu_in_f":24,"fondu_out_f":48},
                  "voix":voix,"ducking":{"actif":True,"profondeur_db":10},
                  "cible_lufs":-14,"crete_db":-1,"fondu_coupe_ms":30},
          "textes":[],"generations":[],"metadonnees":{"modele":"muse","savoir":["opsys"]}}
    inc=[{"type":"trajet","debut_f":130,"duree_f":110,"position":"centre","points":[[0.3,0.7],[0.5,0.3],[0.7,0.2]],"couleur":"ion"},
         {"type":"flash","debut_f":60,"duree_f":3,"position":"centre","intensite":0.8},
         {"type":"etiquette","debut_f":620,"duree_f":100,"position":"haut-droite","texte":"VISION"},
         {"type":"statut","debut_f":620,"duree_f":72,"position":"bas","texte":"Photo reçue. Mesures en cours…"},
         {"type":"surtitre","debut_f":744,"duree_f":96,"position":"haut-gauche","texte":"M3 · ESTIMATION"},
         {"type":"compteur","debut_f":760,"duree_f":120,"position":"droite","de":0,"a":18940,"decimales":0,"prefixe":"","suffixe":" $","etiquette":"Soumission"},
         {"type":"document","debut_f":760,"duree_f":130,"position":"droite","titre":"Soumission","destinataire":"Monsieur Morin",
          "lignes":[["Revêtement","12 400 $"],["Soffite-fascia","3 890 $"],["Gouttières","2 650 $"]],"total":"18 940 $","tampon":"APPROUVÉ"},
         {"type":"impact","debut_f":908,"duree_f":48,"position":"centre","texte":"Approuvé."},
         {"type":"pointage","debut_f":1156,"duree_f":72,"position":"gauche","heure":"07:02","nom":"Morin","etat":"ARRIVÉE"},
         {"type":"etiquette","debut_f":1150,"duree_f":110,"position":"haut-droite","texte":"EN PRÉPARATION"},
         {"type":"appel","debut_f":1280,"duree_f":210,"position":"gauche","nom":"Marie · Adjointe","sous_titre":"Appel client","voix":"v08"},
         {"type":"etiquette","debut_f":1280,"duree_f":210,"position":"haut-droite","texte":"VISION"},
         {"type":"courbe","debut_f":1630,"duree_f":130,"position":"droite","points":[4,5,6,7,9,12,16,21],"etiquette":"Profits · 26 semaines","valeur":"+7 %","pointille_depuis":5},
         {"type":"etiquette","debut_f":1630,"duree_f":130,"position":"haut-droite","texte":"EN PRÉPARATION"},
         {"type":"cedule","debut_f":1771,"duree_f":110,"position":"droite","titre":"Cédule · 3 semaines","semaines":3,"jours":["Lun","Mar","Mer","Jeu","Ven"],
          "blocs":[[0,0,2,0,"Équipe A"],[1,0,4,1,"Équipe B"],[2,0,3,0,"Morin"]]},
         {"type":"etiquette","debut_f":1771,"duree_f":110,"position":"haut-droite","texte":"EN PRÉPARATION"},
         {"type":"titre","debut_f":2267,"duree_f":96,"position":"centre","texte":"Dix départements. *Une* équipe.","zone":"centre"},
         {"type":"etiquette","debut_f":2385,"duree_f":110,"position":"haut-droite","texte":"VISION"},
         {"type":"carton","debut_f":2513,"duree_f":120,"position":"centre"}]
    sfx=[{"type":"fouet","debut_f":124,"db":-8},{"type":"impact","debut_f":372,"db":-6},
         {"type":"montee","debut_f":620,"db":-10},{"type":"frappe","debut_f":890,"db":-8},
         {"type":"clic","debut_f":1771,"db":-10},{"type":"montee","debut_f":2261,"db":-8},
         {"type":"boom","debut_f":2513,"db":-6}]
    ann={"incrustations":inc,"sfx":sfx,"son_plans":[{"plan":"p09","db":-10},{"plan":"p10","db":-12}],
         "etalonnage":{"contraste":1.05,"saturation":1.05,"chaleur":0.05,"grain":1.0}}
    return plan,ann,total

def build_court():
    order=["p01","p02","p04","p05","p07","p16"]
    use={"p01":96,"p02":48,"p04":48,"p05":36,"p07":60,"p16":48}
    sources={}; video=[]; cur=0
    for i,pid in enumerate(order):
        d=use[pid]
        sources[pid]={"kind":"video","duree_f":243 if pid=="p11" else (158 if pid=="p07" else 141 if pid=="p13" else 124)}
        video.append({"id":"s%02d"%(i+1),"src":pid,"entree_f":0,"duree_f":d,"vitesse":1,
                      "transition_in":{"type":"cut","duree_f":0}})
        cur+=d
    total=cur
    sources["v10"]={"kind":"audio","duree_f":60}
    sources["musique"]={"kind":"audio","duree_f":total+240}
    plan={"version":1,"fps":24,"format":"16:9","genre":"pub","titre":"L'usine invisible (court)",
          "sources":sources,"video":video,
          "audio":{"musique":{"src":"musique","entree_f":0,"duree_f":total,"gain_db":-8,"fondu_in_f":12,"fondu_out_f":24},
                  "voix":[{"src":"v10","debut_f":total-84,"entree_f":0,"duree_f":60,"gain_db":0}],
                  "ducking":{"actif":True,"profondeur_db":10},
                  "cible_lufs":-14,"crete_db":-1,"fondu_coupe_ms":30},
          "textes":[],"generations":[]}
    inc=[{"type":"trajet","debut_f":100,"duree_f":60,"position":"centre","points":[[0.3,0.7],[0.5,0.3],[0.7,0.2]],"couleur":"ion"},
         {"type":"surtitre","debut_f":228,"duree_f":60,"position":"haut-gauche","texte":"M3 · ESTIMATION"},
         {"type":"etiquette","debut_f":228,"duree_f":60,"position":"haut-droite","texte":"VISION"},
         {"type":"document","debut_f":228,"duree_f":60,"position":"droite","titre":"Soumission","destinataire":"Monsieur Morin",
          "lignes":[["Revêtement","12 400 $"],["Main-d'œuvre","6 540 $"]],"total":"18 940 $","tampon":None},
         {"type":"carton","debut_f":total-48,"duree_f":48,"position":"centre"}]
    sfx=[{"type":"fouet","debut_f":96,"db":-8},{"type":"impact","debut_f":156,"db":-6},{"type":"boom","debut_f":total-48,"db":-6}]
    ann={"incrustations":inc,"sfx":sfx,"son_plans":[],"etalonnage":{"contraste":1.05,"saturation":1.05,"chaleur":0.05,"grain":1.0}}
    return plan,ann,total

def main():
    long,annL,totL=build_long()
    court,annC,totC=build_court()
    dossier={"equipe":EQUIPE,"titre":"L'USINE INVISIBLE",
      "personnages":personnages,"lieux":lieux,"cles":cles,"voix":voix,"plans":plans,
      "musique":musique,
      "montage":{"long":long,"court":court,"vertical":None},
      "annexe":{"long":annL,"court":annC}}
    with open("equipes/muse/dossier.json","w") as f:
        json.dump(dossier,f,ensure_ascii=False,indent=1)
    print("long: %.1fs (%d images) | court: %.1fs (%d images)"%(totL/24,totL,totC/24,totC))

main()
