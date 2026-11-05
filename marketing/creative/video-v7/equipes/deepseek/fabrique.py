# -*- coding: utf-8 -*-
"""Fabrique dossier.json de l'équipe deepseek — film « LA DOUBLURE ».
Grille : 120 BPM -> 1 temps = 0,5 s ; 1 mesure = 2,0 s. Tous les debuts tombent sur la grille.
Budget BRIEF §7 verifie en fin de script.
"""
import json, math
from pathlib import Path

BPM = 120.0
T = 60.0 / BPM          # 0,5 s
def t(beats): return round(beats * T, 6)

CAP = "/home/pc6/nexora-creative-data/promo/v6-creative/captures"
S09 = CAP + "/boost/s09"          # saisie « voiture explose ralenti » (reelle)
S10 = CAP + "/boost/s10"          # saisie « dragn chato feu » (reelle) -> bonus

# ---------------------------------------------------------------- images cles
# Recette obligatoire : pellicule nommee, objectif reel, decor reel, lumiere pratique,
# atmosphere, imperfections, matieres vecues, echelle humaine. Aucun mot interdit.
HEAD = ("Production still from a live-action feature film, photographed on location on 35mm film "
        "(Kodak Vision3 500T) with ")
HER = ("a stunt performer in her thirties, dark hair plastered flat by rain, a small scar above her left eyebrow, "
       "soaked dark canvas coat, mud on her knuckles")
IMPERF = " rain on the lens, visible film grain, halation around the flames, slight motion blur"

K = {}
def cle(i, fmt, graine, objectif, scene):
    K[i] = {"id": i, "format": fmt, "graine": graine, "prompt": HEAD + objectif + "; " + scene}

cle("k01", "16:9", 1101,
    "an old Cooke 400mm telephoto lens from 300 metres away, compressed perspective, heat shimmer",
    "dusk on a rainy Scottish hillside, a huge dragon with scarred, mud-caked leathery hide clings to the top of a real "
    "ruined stone keep and breathes a jet of real fire onto the wet battlements, the flames light the drizzle and the wet "
    "stone, thick black smoke drifts across heavy overcast cloud, " + HER + " stands small in the long grass in the "
    "foreground with her back to us for scale, wet grass whipping in the wind" + IMPERF)
cle("k02", "16:9", 1102,
    "a handheld Arri Alexa 35 with an 85mm lens, rain drops on the glass",
    "night on the same moor, close on the face of " + HER + ", she looks just past the lens, firelight from a burning "
    "building flickers across her wet skin and the rain running down her cheek, she does not blink, out-of-focus "
    "firefighters in yellow coats far behind her" + IMPERF)
cle("k03", "16:9", 1103,
    "a handheld camera running beside her with a 32mm lens",
    "a peat bog at dusk, " + HER + " sprints through shin-deep mud away from a real fuel explosion behind her, a wall of "
    "orange flame and black smoke rolls over the heather, clods of peat and water thrown up by her boots, a burning "
    "truck tilted on the slope, her mouth open, breath visible" + IMPERF)
cle("k04", "16:9", 1104,
    "a Panavision anamorphic 40mm lens on a low tripod, 60 metres back",
    "a deserted asphalt road across a high desert at last light, a dark saloon car torn open by a real explosion, doors "
    "and glass thrown across the tarmac, burning fuel running in the gutter, " + HER + " walks toward the camera through "
    "the smoke with her coat flapping, heat shimmer bending the horizon, a road sign bent by the blast" + IMPERF)
cle("k05", "16:9", 1105,
    "a handheld Arri Alexa Mini with a 25mm lens, water on the front element",
    "night, heavy rain on a real industrial rooftop, " + HER + " slams back-first into a galvanised vent housing, steam "
    "bursts from a broken pipe, sodium lamps from the street below light the wet metal and the puddles, sparks from a "
    "severed cable skitter past her boot, the city out of focus far below" + IMPERF)
cle("k06", "16:9", 1106,
    "a gyro-stabilised camera mounted on a helicopter skid, 24mm lens, rotor vibration",
    "open sea at grey dawn, a rescue helicopter three metres above the swell, " + HER + " hangs from the skid by both "
    "hands, her legs swinging over the water, spray torn up by the rotor wash soaking the frame, a coast guard in a "
    "harness leaning out of the door to reach her, the horizon tilted" + IMPERF)
cle("k07", "16:9", 1107,
    "a handheld camera on a castle rampart with a 24mm Panavision lens, dirt and rain on the lens",
    "night, the belly and wings of an enormous dragon pass a few metres overhead above a real castle rampart in the "
    "rain, its wet hide lit from below by burning torches and fires, sparks and embers fly, a torn banner whips in the "
    "wind, two soldiers duck against the parapet in the foreground" + IMPERF)
cle("k08", "16:9", 1108,
    "a helmet camera strapped to a skydiver, 20mm lens, the frame shaking",
    "freefall inside a grey cloud bank, " + HER + " falls face down at terminal velocity, her coat and hair ripped flat "
    "by the wind, water droplets streaming off her sleeve, the dark shape of a helicopter small and far above her, "
    "cloud tearing past the lens" + IMPERF)
cle("k09", "16:9", 1109,
    "an Arri Alexa 65 with a 50mm lens, shot like aerial footage from a chase helicopter, high-altitude haze",
    "above a real cloud layer at sunset, an enormous dragon grips the scarred steel hull of a grey military airship the "
    "size of a ship and breathes fire onto the plating, rivets, rust streaks, buckled panels, real sunlight and haze, "
    "a crewman in the airship's open hatch firing a flare for scale" + IMPERF)
cle("k10", "16:9", 1110,
    "a 600mm telephoto lens from a second aircraft, heavy atmospheric haze",
    "the same airship burning and breaking apart as it falls through a layer of cloud at sunset, a long trail of black "
    "smoke, a tiny figure under a parachute a hundred metres below the wreck, torn metal turning slowly, the sun low "
    "and hard behind the cloud" + IMPERF)

cle("k11", "16:9", 1111,
    "a handheld camera held low to the wet grass, 35mm lens",
    "a rain-soaked field at night, " + HER + " lands hard on one knee in the mud, the helicopter searchlight sweeping "
    "across the grass behind her, her wet coat heavy with water, breath steaming, rain hammering the lens")
cle("k12", "16:9", 1112,
    "a handheld 85mm lens at close range, slight drift",
    "night, close on the face of " + HER + ", soaked, mud streaked across her cheek, lit from above by a helicopter "
    "searchlight, rain falling through the beam, a tired smile starting, the dark moor out of focus behind her" + IMPERF)
cle("k13", "16:9", 1113,
    "a 600mm telephoto lens on a tripod, slow pan",
    "the same rainy moor at night, a huge dragon circles far above in the low cloud, wings beating slowly, lit only by "
    "a helicopter searchlight beam crossing under it, rain visible in the beam, a stone wall and a dead tree in the "
    "foreground for scale" + IMPERF)
cle("k14", "16:9", 1114,
    "a handheld camera at ground level with a 50mm lens, very close",
    "dusk on black volcanic rock, a small red cat with singed whiskers sits and spits a thin jet of real orange flame "
    "into the wind, the flame gutters sideways, wet ash and cinders on the rock, the sea far below out of focus" + IMPERF)
cle("k15", "16:9", 1115,
    "a handheld camera at shoulder height, 32mm lens, following her",
    "a rainy Scottish moor at night, a real film crew at work: a camera operator tracks backwards on a dolly, a boom "
    "operator holds a microphone above " + HER + " who is wrapped in a silver blanket and soaked to the skin, a "
    "generator cable in the mud, and far behind them in the rain a huge dragon waits without moving" + IMPERF)
cle("k16", "16:9", 1116,
    "a macro lens at very shallow depth of field",
    "extreme close-up of a dragon's eye, the slit pupil narrowing, firelight moving across the wet iris, a rain drop "
    "running down the scales beside it, dust and a small scar on the hide" + IMPERF)
cle("k19", "16:9", 1119,
    "a motion-control camera with a 35mm lens, the warships built as large physical miniatures with weathered paint, "
    "panel lines and scorch marks, lit by one hard key light the way 1980s model photography was lit",
    "low Earth orbit seen from a real spacecraft window, two battered grey warships pass close, hard unfiltered "
    "sunlight from one side and pitch-black shadows, a real cloud-covered Earth below, a small explosion throwing "
    "debris and white vented gas, the only light is hard white sunlight" + IMPERF)
cle("k20", "16:9", 1120,
    "a helicopter-mounted 300mm lens, heat shimmer",
    "the dragon crosses in front of the low sun above a real cloud layer, wings spread wide, its body black against "
    "the sun, the cloud below turned orange, the sun flaring at the edge of the frame, rotor blur at the frame edge" + IMPERF)

# --- 9:16 natifs (2 cles, 2 plans = 2 unites)
cle("k17", "9:16", 1117,
    "a helmet camera in freefall, 24mm lens, vertical framing, the frame shaking",
    "freefall inside a grey cloud bank, seen from above: " + HER + " falls away from the camera face down, arms out, "
    "her coat and hair ripped flat by the wind, the cloud tearing past, a dark helicopter small far above her" + IMPERF)
cle("k18", "9:16", 1118,
    "a handheld camera on a castle rampart, 24mm lens, vertical framing, rain on the lens",
    "night, the head and neck of an enormous dragon pass a few metres overhead above a real castle rampart in the rain, "
    "its wet hide lit from below by burning torches, sparks and embers flying, a soldier ducking against the parapet "
    "at the bottom of the frame" + IMPERF)

# --- 9:16 supplementaires (k21 deja 16:9) -> total 24 cles
cle("k22", "9:16", 1122,
    "a handheld 85mm lens at close range, vertical framing, slight drift",
    "night, close on the face of " + HER + ", soaked, mud streaked across her cheek, lit from above by a helicopter "
    "searchlight, rain falling through the beam, a tired smile starting, the dark moor out of focus behind her" + IMPERF)
cle("k23", "9:16", 1123,
    "a 600mm telephoto lens on a tripod, vertical framing, 400 metres away, heavy rain haze",
    "dusk on a rainy Scottish moor, a real ruined stone keep burning on the hill, the fire lighting the rain, the black "
    "silhouette of a huge dragon rising above the flames, a stone wall and a dead tree in the foreground for scale" + IMPERF)

# ---------------------------------------------------------------- plans
VID = ("Live-action footage shot on 35mm film, {op}, natural motion blur from a 180-degree shutter, slight focus breathing, "
       "real physics and weight, practical fire, smoke and debris, film grain. ")
def plan(i, k, op, action, son, images=124, graine=0):
    return {"id": i, "cle": k, "format": "16:9", "images": images, "graine": graine,
            "prompt": ("For the target video, at 0.00 seconds into the target video, <Picture 1> (from [Shot 1]) is fully referenced.\n\n"
                       "integrated_multimodal_description: [Shot 1] " + VID.format(op=op) + action + " No text, no logos.\n\n"
                       "overall_soundscape: " + son + "\n\nnon_diegetic_music: N/A")}

P = []
P.append(plan("p01", "k01", "long telephoto camera on a tripod 300 metres away, slight pan, compressed perspective",
  "The dragon arches its neck and breathes a long jet of fire onto the battlements; burning debris falls, smoke rolls sideways in the wind, "
  "the woman in the long grass does not move. The camera pans a few degrees to follow the flames.",
  "Roaring fire, crackling burning timber, heavy rain, a deep animal growl far away, wind in the grass.", 124, 2101))
P.append(plan("p02", "k02", "handheld camera operator at close range, the frame breathing",
  "She stands in the rain and looks just past the lens without blinking; firelight moves across her wet face, rain runs down her cheek, "
  "a strand of wet hair lifts in the wind. Behind her, out of focus, firefighters walk past.",
  "Rain on a coat, distant fire, a man shouting orders, the low crackle of a burning building.", 124, 2102))
P.append(plan("p03", "k03", "handheld camera operator running beside her, strong shake",
  "She sprints through shin-deep mud away from the explosion; a wall of flame and black smoke rolls over the heather behind her, clods of peat "
  "and water thrown up by her boots, she stumbles once and keeps running. The camera runs with her.",
  "A fuel explosion, boots sucking in mud, hard breathing, wind, burning heather crackling.", 124, 2103))
P.append(plan("p04", "k04", "camera on a low tripod 60 metres back, slow push in on a long lens",
  "She walks toward the camera through the smoke of the wrecked car, coat flapping, heat shimmer bending the horizon; burning fuel runs in the "
  "gutter and a bent road sign creaks in the wind. She does not look at the car.",
  "Burning fuel, ticking hot metal, wind across the desert, glass cracking as it cools.", 124, 2104))
P.append(plan("p05", "k05", "handheld camera operator at close range, hard shake on impact",
  "She slams back-first into the vent housing and the metal buckles; steam bursts from a broken pipe and hides her for a moment, sparks from a "
  "severed cable skitter across the wet roof past her boot. She pushes herself up.",
  "Metal buckling, a burst of steam, an electrical crackle, rain on metal, city traffic far below.", 124, 2105))
P.append(plan("p06", "k06", "camera mounted on the helicopter skid, rotor vibration, wide lens",
  "She hangs from the skid by both hands above the swell; the coast guard leans out and grabs her wrist, her legs swing, spray from the rotor "
  "wash soaks the frame. She shouts one word up at him.",
  "Rotor thump, wind, heavy sea, the helicopter radio crackling, her shout lost in the noise.", 124, 2106))
P.append(plan("p07", "k07", "handheld camera on the rampart, operator ducks as the creature passes",
  "The dragon sweeps low over the rampart from right to left; the downdraft whips rain and embers into the lens, the camera ducks, a torn banner "
  "snaps, the two soldiers press against the parapet. Fires burn along the wall.",
  "Deafening wingbeats, gusting wind, rain, crackling fires, men shouting.", 124, 2107))
P.append(plan("p08", "k08", "helmet camera in freefall, the frame shaking hard",
  "She falls face down through the cloud, arms out, coat and hair ripped flat by the wind; the cloud tears past the lens and breaks into open grey "
  "air, the helicopter small and far above her. She turns her head to the camera.",
  "Wind roaring past a helmet, fabric snapping, her breathing inside the helmet.", 124, 2108))
P.append(plan("p09", "k09", "aerial camera from a chase helicopter, slight vibration",
  "The dragon grips the airship hull and breathes fire onto the plating; rivets pop, a panel buckles and falls away into the clouds, smoke streams "
  "backwards. A crewman in the open hatch fires a flare.",
  "Wind, the dragon's roar, tearing metal, a deep engine drone, fire.", 124, 2109))
P.append(plan("p10", "k10", "long telephoto camera from a second aircraft, heavy haze, slow drift",
  "The airship breaks apart as it falls through the cloud, a long trail of black smoke behind it; torn metal turns slowly, a tiny figure under a "
  "parachute swings a hundred metres below the wreck. The sun sits low and hard behind the cloud.",
  "A long low rumble, wind at altitude, metal groaning, then near silence.", 124, 2110))
P.append(plan("p11", "k11", "handheld camera held low in the wet grass",
  "She lands hard on one knee in the mud and stays there, breathing; the searchlight sweeps across the grass behind her and passes over her back, "
  "rain hammering. She wipes mud from her mouth with the back of her hand.",
  "A helicopter passing overhead, rain in grass, her breath, boots squelching.", 124, 2111))
P.append(plan("p12", "k12", "handheld camera at close range, slight drift",
  "Close on her face in the searchlight beam; rain falls through the light, mud streaked on her cheek, and a tired smile starts and holds. She "
  "looks straight into the lens.",
  "Rain, her breathing, the helicopter fading, a distant generator.", 124, 2112))
P.append(plan("p13", "k13", "long telephoto camera on a tripod, slow pan following the shape",
  "The dragon circles far above in the low cloud, wings beating slowly; the searchlight beam crosses under it and catches the rain. A stone wall "
  "and a dead tree hold the foreground.",
  "Wind over open moor, a faint deep call from above, rain.", 124, 2113))
P.append(plan("p14", "k14", "handheld camera at ground level, very close",
  "The small red cat sits on the volcanic rock and spits a thin jet of flame into the wind; the flame gutters sideways, cinders lift off the wet "
  "ash, the cat sneezes and looks straight at the lens.",
  "Wind, a small dry whoosh of flame, a cat's short sneeze, the sea far below.", 124, 2114))
P.append(plan("p15", "k15", "handheld camera at shoulder height following her through the crew",
  "The camera operator tracks backwards on the dolly, the boom operator holds the microphone over her; she is wrapped in a silver blanket, soaked, "
  "and the crew works around her in the rain. Far behind them the dragon waits without moving.",
  "Rain on nylon, the dolly wheels, crew voices, a generator, the boom operator counting her in.", 124, 2115))
P.append(plan("p16", "k16", "macro lens, very shallow depth of field",
  "The dragon's slit pupil narrows as firelight moves across the wet iris; a raindrop runs down the scales beside the eye and falls out of frame.",
  "A low breath, rain on hide, a deep rumble felt more than heard.", 124, 2116))
P.append(plan("p19", "k19", "motion-control camera gliding forward between the hulls",
  "The camera glides between the two battered hulls as a small explosion throws metal debris and white vented gas across the frame; hard sunlight "
  "flickers across the plating and the Earth turns slowly below.",
  "Muffled metallic groans through a hull, a dull distant impact, the hiss of venting gas, near silence.", 124, 2119))
P.append(plan("p20", "k20", "helicopter-mounted long lens, heat shimmer",
  "The dragon crosses in front of the low sun above the cloud layer, wings spread wide; the sun flares at the edge of the frame and the cloud below "
  "turns orange. Rotor blur at the frame edge.",
  "Rotor thump, wind, one long roar that ends in silence.", 124, 2120))
P.append(plan("p21", "k21", "long telephoto camera on a tripod, 400 metres away, locked off",
  "She stands small in the long grass with her back to the camera and watches the keep burn; the dragon's black shape rises above the flames and "
  "the fire lights the rain. Nothing moves except the smoke and the grass.",
  "Fire at a distance, rain, wind in the grass, no music.", 124, 2121))

# --- 9:16 natifs (4 unites)
V = []
V.append(plan("p22", "k17", "helmet camera in freefall, vertical framing, the frame shaking",
  "She falls away from the camera face down, arms out, coat and hair ripped flat; the cloud tears past and breaks, the helicopter small far above.",
  "Wind roaring past a helmet, fabric snapping, her breathing.", 124, 2122))
V[-1]["format"] = "9:16"
V.append(plan("p23", "k18", "handheld camera on the rampart, vertical framing, operator ducks",
  "The head and neck of the dragon pass a few metres overhead; embers and rain whip down, the soldier at the bottom of the frame ducks.",
  "Deafening wingbeats, gusting wind, rain, crackling fires.", 124, 2123))
V[-1]["format"] = "9:16"
V.append(plan("p24", "k22", "handheld camera at close range, vertical framing, slight drift",
  "Close on her face in the searchlight beam; rain falls through the light, mud on her cheek, a tired smile starts and holds.",
  "Rain, her breathing, the helicopter fading.", 124, 2124))
V[-1]["format"] = "9:16"
V.append(plan("p25", "k23", "long telephoto camera on a tripod, vertical framing, locked off",
  "The keep burns on the hill, the dragon's black shape rises above the flames, the rain is lit by the fire.",
  "Fire at a distance, rain, wind in the grass.", 124, 2125))
V[-1]["format"] = "9:16"

# ---------------------------------------------------------------- voix (personnages, <= 6 mots, 3 repliques)
VOIX = [
 {"id": "v01", "moteur": "gemini38-puck", "plan": "p02",
  "texte": "Tu es en retard.", "direction": "Homme, 40 ans, chef d'equipe pompiers, a bout de souffle, parle dans la pluie sans crier, ton blase et un peu inquiet."},
 {"id": "v02", "moteur": "gemini38-puck", "plan": "p06",
  "texte": "Lache pas!", "direction": "Le meme homme, cette fois il hurle par-dessus le rotor du pilote, gorge serree, une seule syllabe d'urgence."},
 {"id": "v03", "moteur": "h3-natif", "plan": "p06",
  "texte": "<d>[French] Attrape ma main.</d>", "direction": "Replique native du cascadeur coast guard dans le plan p06, dite en tendant le bras, soufflee par le vent."},
]

# ---------------------------------------------------------------- temps forts (grille 120 BPM, mesure = 2 s)
TF = [
 (0.0, "noir + deux mots a l'ecran, aucune musique, pluie seule"),
 (2.0, "PREMIER PLAN FORT : le dragon crache le feu sur le donjon (impact p01)"),
 (4.0, "coupe seche sur le visage, la pluie, le feu qui bouge sur la peau"),
 (6.0, "SILENCE MUSICAL 1,5 s : explosion de tourbe, souffle et boue"),
 (8.0, "rafale de trois plans (voiture, toit, helico)"),
 (11.0, "arret brutal : elle pend dans le vide, le rotor seul"),
 (13.0, "reprise : survol du rempart, le dragon passe au-dessus"),
 (15.0, "chute libre, coupe sur le souffle"),
 (16.0, "MONTE : l'airship en feu, puis la carcasse qui tombe"),
 (19.0, "silence 1 s avant l'impact, puis l'atterrissage dans la boue"),
 (20.0, "respiration : le visage, le sourire, la pluie"),
 (23.0, "le dragon tourne dans les nuages, le faisceau le cherche"),
 (25.0, "chute : plus rien, puis le chat qui crache une flamme (rire)"),
 (27.0, "plateau : l'equipe de tournage, le dragon immobile derriere"),
 (29.0, "macro de l'oeil, un battement"),
 (30.0, "derniere image : elle regarde le donjon bruler (echelle humaine)"),
 (32.0, "CARTON 2,5 s, silence puis une note"),
 (34.5, "bonus : le chat, une derniere flamme"),
]

# ---------------------------------------------------------------- musiques (3 pistes, sections horodatees)
M1 = ("Lyria 3 Pro, instrumental, 34 s, tempo 120 BPM, hybrid orchestral and electronic score written to picture. "
      "Signature motif: a four-note figure for low strings and a solo cello (D, F, E, A), stated quietly at 0:02, inverted at 0:11, "
      "played full by brass and low strings at 0:16, and left alone on cello at 0:30. "
      "0:00-0:02 near silence: rain texture only, no music. "
      "0:02-0:06 low string drone and a single deep drum on the downbeat, the four-note motif on cello, restrained. "
      "0:06-0:07 HARD SILENCE, everything drops out. "
      "0:07-0:10 percussion enters hard on the beat, taiko and metal hits, strings in fast repeated figures, rising. "
      "0:10-0:11 abrupt stop, one sustained low note only. "
      "0:11-0:15 full orchestra and electronic bass pulse, motif inverted, brass stabs on every second beat. "
      "0:15-0:16 build with snare rolls and rising strings, cut dead at 0:16. "
      "0:16-0:19 peak: full brass, choir-free, taiko, distorted low synth, the motif played twice, maximum energy. "
      "0:19-0:20 total silence for one second. "
      "0:20-0:23 warm resolution, cello motif, soft strings, no percussion. "
      "0:23-0:25 mysterious, low woodwind and muted strings, slow. "
      "0:25-0:27 comic drop: pizzicato strings and a single bassoon, playful, then a small brass sting on the cat's flame. "
      "0:27-0:30 wide and quiet, sustained strings and a distant solo trumpet, motif fragment. "
      "0:30-0:32 near silence, one low note. "
      "0:32-0:34 final: the four-note motif on solo cello alone, unresolved, ending on the third. "
      "No drums in the last four seconds. Mix: wide stereo, dry close percussion, no reverb wash.")
M2 = ("Lyria 3 Pro, instrumental, 34 s, 120 BPM, cinematic electronic tension score for a chase, written to picture. "
      "A two-note pulse (low synth, then a struck metal hit) is the signature, present from 0:02 to 0:19. "
      "0:00-0:02 silence except rain. 0:02-0:06 one low pulsing synth note every beat, no melody, pressure building. "
      "0:06-0:07 silence. 0:07-0:10 the pulse doubles, distorted bass, metallic percussion on the beat. "
      "0:10-0:11 stop. 0:11-0:15 pulse with rising filtered noise sweep, strings tremolo high. "
      "0:15-0:16 riser into a cut. 0:16-0:19 maximum: distorted bass, hard kick on every beat, brass cluster, chaotic but on tempo. "
      "0:19-0:20 silence. 0:20-0:23 pulse slows to half time, warm pad, release. "
      "0:23-0:25 sparse, one synth note, wide reverb. 0:25-0:27 playful detuned synth and pizzicato for the cat, then a small sting. "
      "0:27-0:30 half-time pulse, low strings. 0:30-0:32 near silence. 0:32-0:34 final two-note pulse alone, one hit, tail. "
      "No melody in the voice, no vocals, no drums after 0:30.")
M3 = ("MiniMax Music3, instrumental, 30 s, 120 BPM, orchestral percussion and low brass only, no melody instruments, "
      "built as a rhythmic bed: taiko and floor toms in a steady pattern from 0:00, accents every four beats, "
      "a rising cymbal swell at 0:06, 0:15 and 0:19, hard stops at 0:06, 0:11 and 0:19 lasting half a second, "
      "and a final single low drum at 0:28. Dry, close, punchy, no reverb, no synth pads.")
MUS = [{"id": "m1", "moteur": "lyria-pro", "duree": 34, "role": "principal", "prompt": M1},
       {"id": "m2", "moteur": "lyria-pro", "duree": 34, "role": "variante tension", "prompt": M2},
       {"id": "m3", "moteur": "music3", "duree": 30, "role": "lit de percussions pour la coupe", "prompt": M3}]

# ---------------------------------------------------------------- musiques v2 (calage sur le montage 41 s)
M1 = ("Lyria 3 Pro, instrumental, 41 s, tempo 120 BPM, hybrid orchestral and electronic score written to picture, "
      "with a memorable four-note motif (D, F, E, A) for solo cello and low strings. "
      "0:00-0:00.5 near silence, rain texture, no music. "
      "0:00.5-0:03 low string drone, one deep drum on the downbeat at 0:00.5, the motif on cello, restrained. "
      "0:03-0:05 motif repeats a step higher, muted strings, tension. "
      "0:05-0:06.5 HARD SILENCE, everything drops out for the explosion. "
      "0:06.5-0:09.5 percussion enters hard on the beat, taiko and metal hits, fast repeated string figures, rising. "
      "0:09.5-0:11.5 full orchestra and electronic bass pulse, brass stabs on every second beat. "
      "0:11.5-0:14.5 driving, motif inverted, snare rolls underneath. "
      "0:14.5-0:16 build, rising strings and cymbal swell, cut dead at 0:16. "
      "0:16-0:18 peak: full brass, taiko, distorted low synth, motif played twice, maximum energy. "
      "0:18-0:19.5 sudden drop, one sustained low note, almost nothing. "
      "0:19.5-0:22 warm resolution, cello motif, soft strings, no percussion. "
      "0:22-0:24 mysterious, low woodwind and muted strings, slow. "
      "0:24-0:25.5 quiet ticking pulse under the typing, sparse. "
      "0:25.5-0:26.5 a small brass sting. "
      "0:26.5-0:28 comic drop: pizzicato strings and a single bassoon, playful. "
      "0:28-0:30.5 wide and quiet, sustained strings, distant solo trumpet, motif fragment. "
      "0:30.5-0:32 one low note only, space. "
      "0:32-0:35 electronic pulse and low strings, slow build, no drums. "
      "0:35-0:37 the motif played full one last time, brass and strings, then cut. "
      "0:37-0:39.5 near silence, one sustained note, then nothing. "
      "0:39.5-0:41 the four-note motif on solo cello alone, ending on the third, plus one small comic pizzicato. "
      "Mix: wide stereo, dry close percussion, no reverb wash, no vocals.")
M2 = ("Lyria 3 Pro, instrumental, 41 s, 120 BPM, cinematic electronic tension score for a chase, written to picture. "
      "Signature: a two-note pulse, a low synth note then a struck metal hit, present from 0:00.5 to 0:18. "
      "0:00-0:00.5 silence. 0:00.5-0:05 one low pulsing synth note every beat, no melody, pressure building, "
      "a single deep hit at 0:00.5 and at 0:03. 0:05-0:06.5 silence. "
      "0:06.5-0:09.5 the pulse doubles, distorted bass, metallic percussion on the beat. "
      "0:09.5-0:11.5 filtered noise sweep rising, high string tremolo. 0:11.5-0:14.5 pulse and hard kick every beat. "
      "0:14.5-0:16 riser into a cut. 0:16-0:18 maximum: distorted bass, brass cluster, chaotic but on tempo. "
      "0:18-0:19.5 stop, one low note. 0:19.5-0:22 pulse slows to half time, warm pad, release. "
      "0:22-0:24 sparse, one synth note, wide reverb. 0:24-0:26 soft ticking under the typing, then a small sting. "
      "0:26.5-0:28 playful detuned synth and pizzicato. 0:28-0:30.5 half-time pulse, low strings. "
      "0:30.5-0:32 near silence. 0:32-0:35 electronic pulse building. 0:35-0:37 last full hit, then cut. "
      "0:37-0:41 near silence, final two-note pulse alone, one hit, long tail. No vocals, no drums after 0:37.")
M3 = ("MiniMax Music3, instrumental, 41 s, 120 BPM, orchestral percussion and low brass only, no melody instruments, "
      "built as a rhythmic bed: taiko and floor toms in a steady pattern from 0:00, accents every four beats, "
      "rising cymbal swells at 0:05, 0:14.5, 0:18 and 0:35, hard stops at 0:05, 0:09.5 and 0:18 lasting half a second, "
      "a sparse ticking pattern 0:24-0:28, and a final single low drum at 0:39.5. Dry, close, punchy, no reverb, no pads.")
MUS = [{"id": "m1", "moteur": "lyria-pro", "duree": 41, "role": "principal", "prompt": M1},
       {"id": "m2", "moteur": "lyria-pro", "duree": 41, "role": "variante tension", "prompt": M2},
       {"id": "m3", "moteur": "music3", "duree": 41, "role": "lit de percussions", "prompt": M3}]
