#!/usr/bin/env python3
"""Générateur du dossier machine (dossier.json) pour l'équipe gemini."""
import json
from pathlib import Path

BASE = Path(__file__).parent

PERSONNAGES = [
    {
        "id": "etienne",
        "nom": "Étienne",
        "role": "Représentant aux ventes terrain (M2/M3)",
        "voix": "drama3-adamqc",
        "fiche": (
            "Character reference sheet on a neutral solid studio grey background, split composition: full-body standing view on the left, "
            "close-up portrait of the face on the right. A 34-year-old Québécois field sales representative named Étienne, athletic build, "
            "warm confident eyes, short tousled dark brown hair, neat three-day stubble, natural skin texture. He wears a fitted slate-blue "
            "waterproof softshell work jacket, dark charcoal cargo work trousers, rugged leather work boots, plain clothing with no logo, "
            "no text, no letters anywhere. Bright natural daylight studio lighting, photorealistic cinema quality."
        ),
    },
    {
        "id": "benoit",
        "nom": "Benoît",
        "role": "Fondateur et administrateur de la PME (Approbations N0-N5)",
        "voix": "drama3-frederic",
        "fiche": (
            "Character reference sheet on a neutral solid studio grey background, split composition: full-body standing view on the left, "
            "close-up portrait of the face on the right. A 52-year-old Québécois renovation company owner and administrator named Benoît, "
            "broad shoulders, sharp experienced eyes, short salt-and-pepper beard, silver-streaked dark hair, weathered authentic skin texture. "
            "He wears a dark navy merino crew-neck sweater over a crisp slate collared shirt, dark denim jeans, brown leather boots, "
            "plain clothing with no logo, no text, no letters anywhere. Balanced cinematic studio lighting, photorealistic."
        ),
    },
    {
        "id": "marc",
        "nom": "Marc",
        "role": "Chef d'équipe chantier et installateur (M4 Terrain)",
        "voix": "drama3-adamqc",
        "fiche": (
            "Character reference sheet on a neutral solid studio grey background, split composition: full-body standing view on the left, "
            "close-up portrait of the face on the right. A 29-year-old Québécois exterior renovation lead installer named Marc, sturdy muscular build, "
            "energetic smile, ruddy cheeks, short sandy-brown hair under a plain matte black hard hat, clean-shaven. He wears a heavy-duty olive-grey "
            "canvas work jacket, reinforced carpenter pants with a leather tool belt, steel-toe boots, plain clothing with no logo, "
            "no text, no letters anywhere. Crisp studio key light, photorealistic."
        ),
    },
    {
        "id": "claire",
        "nom": "Claire (Avatar M1 Réception & M5 Finance)",
        "role": "Adjointe exécutive et directrice financière virtuelle (Avatar 3D)",
        "voix": "eleven-jeannemance",
        "fiche": (
            "Character reference sheet on a neutral solid studio grey background, split composition: full-body standing view on the left, "
            "close-up portrait of the face on the right. A 35-year-old virtual executive assistant and financial director avatar named Claire, "
            "poised posture, expressive intelligent dark eyes, sleek chin-length dark auburn bob haircut, subtle translucent cyan bioluminescent "
            "filaments tracing along her collarbones and temples. She wears a tailored architectural midnight-ink blazer with subtle glowing "
            "ion-blue seam lines and a single warm signal-orange lapel pin, plain clothing with no logo, no text, no letters anywhere. "
            "High-contrast sci-fi cinema lighting, photorealistic."
        ),
    },
    {
        "id": "sonia",
        "nom": "Sonia (Avatar M4 Opérations & M9 Stratégie)",
        "role": "Directrice virtuelle des opérations, cédules et stratégie (Avatar 3D)",
        "voix": "drama3-jeannemance",
        "fiche": (
            "Character reference sheet on a neutral solid studio grey background, split composition: full-body standing view on the left, "
            "close-up portrait of the face on the right. A 40-year-old virtual operations and scheduling director avatar named Sonia, "
            "commanding calm presence, sharphazel eyes, platinum-streaked dark hair pulled into a neat low bun, faint holographic geometric "
            "light grid shimmering softly across her cheekbones. She wears a structured obsidian-grey high-collar tunic jacket with luminous "
            "amber-orange cuff accents, dark tailored trousers, plain clothing with no logo, no text, no letters anywhere. "
            "Cinematic volumetric studio lighting, photorealistic."
        ),
    },
]

LIEUX = [
    {
        "id": "maison_morin",
        "fiche": (
            "Location reference sheet, wide architectural establishing view in bright crisp autumn morning sunlight. A two-story Québécois "
            "suburban residential house undergoing exterior renovation in a leafy neighbourhood: weathered cedar and aluminum siding on the upper "
            "gables, fresh dark charcoal soffit and fascia boards ready for installation, maple trees with golden-orange leaves in the yard, "
            "a gravel driveway, clear blue sky, no text, no street numbers, no signs, no logos anywhere. Photorealistic large-format cinema look."
        ),
    },
    {
        "id": "shop_bureau",
        "fiche": (
            "Location reference sheet, wide architectural interior-exterior view at golden hour. A modern Québécois exterior-renovation PME "
            "headquarters combining a lofty timber-and-steel workshop bay filled with coils of matte aluminum gutter stock, neat racks of siding "
            "panels and dark pickup trucks, with a warm glass-walled mezzanine office overlooking the floor, a solid oak desk, warm tungsten pendant "
            "lamps, and a sleek black glass-fronted local server rack humming with a single vertical strip of ion-blue and signal-orange light. "
            "No text, no brand names, no logos anywhere."
        ),
    },
    {
        "id": "citadelle_opsys",
        "fiche": (
            "Location reference sheet, monumental wide architectural view inside the virtual enterprise citadel inside the server. A breathtaking "
            "ten-story cylindrical glass-and-obsidian corporate atrium rising inside a vast dark cybernetic vault: ten illuminated circular rings "
            "representing ten specialized enterprise departments stacked vertically around a central column of flowing ion-blue and signal-orange "
            "light streams, floating translucent geometric architectural models and luminous golden data threads, dramatic volumetric god rays, "
            "cinematic sci-fi realism, no readable text, no letters, no numbers, no logos anywhere."
        ),
    },
]

CLES = [
    {
        "id": "k01",
        "format": "16:9",
        "prompt": (
            "Cinematic wide shot in crisp morning sunlight outside a two-story Québécois house under renovation, a 34-year-old man in a plain "
            "slate-blue work jacket holding up a matte black smartphone toward the upper roof gable, a brilliant pulse of signal-orange and "
            "ion-blue light erupting from the camera lens into the air, shallow depth of field, no text, no logos."
        ),
    },
    {
        "id": "k02",
        "format": "16:9",
        "prompt": (
            "Cinematic low-angle tracking frame looking up at a wooden utility pole and a tall steel 5G telecommunications tower against a "
            "deep morning sky with high clouds; a blazing comet of signal-orange and ion-blue light arcs from the sky into the tower antenna "
            "and races down the overhead fiber-optic cable, dramatic lens flare, no text, no logos."
        ),
    },
    {
        "id": "k03",
        "format": "16:9",
        "prompt": (
            "Cinematic close-up inside a renovation workshop office: a sleek matte-black local server cabinet with a smoked-glass door, a "
            "blazing filament of signal-orange light shooting through the overhead conduit and plunging straight through the glass door into "
            "a glowing deep-blue architectural core inside, warm tungsten workshop background bokeh, no text, no logos."
        ),
    },
    {
        "id": "k04",
        "format": "16:9",
        "prompt": (
            "Monumental cinematic wide shot inside a vast ten-story obsidian-and-glass virtual corporate atrium: ten glowing circular mezzanine "
            "floors stacked vertically around a central vortex of ion-blue and signal-orange light, dozens of luminous specialist silhouettes "
            "working across the levels in synchronized harmony, volumetric light beams, feature-film VFX look, no text, no logos."
        ),
    },
    {
        "id": "k05",
        "format": "16:9",
        "prompt": (
            "Cinematic medium shot inside the virtual estimation department floor: a glowing translucent 3D wireframe replica of a two-story "
            "house floating above an obsidian table while thousands of golden and cyan light particles cascade like a Monte Carlo simulation "
            "around the roof eaves and siding, dramatic dark ink background, no text, no numbers, no logos."
        ),
    },
    {
        "id": "k06",
        "format": "16:9",
        "prompt": (
            "Cinematic medium close-up inside a glass-walled PME office: a 52-year-old Québécois business owner with a short salt-and-pepper "
            "beard in a plain dark navy sweater stands behind an oak desk, reaching his hand toward a floating translucent golden seal of "
            "approval hovering in mid-air, warm office lamps and ion-blue rim light, no text, no logos."
        ),
    },
    {
        "id": "k07",
        "format": "16:9",
        "prompt": (
            "Cinematic medium shot outside a suburban Québécois house: a 34-year-old sales representative in a plain slate-blue jacket catches "
            "a glowing translucent architectural dossier that materializes in the air above his hand, smiling with satisfaction as a burst of "
            "signal-orange light races back up into the overhead utility lines, no text, no logos."
        ),
    },
    {
        "id": "k08",
        "format": "16:9",
        "prompt": (
            "Cinematic wide tracking shot along a suburban Québécois road lined with autumn maples: a brilliant streak of signal-orange and "
            "cyan light races along the overhead fiber-optic cables on wooden utility poles, leading straight toward a large timber-and-steel "
            "renovation workshop in the distance, dynamic motion blur, no text, no logos."
        ),
    },
    {
        "id": "k09",
        "format": "16:9",
        "prompt": (
            "Cinematic medium shot in the bright doorway of a renovation workshop bay: a 29-year-old crew leader in a plain black hard hat and "
            "olive-grey work jacket stands beside a dark pickup truck loaded with aluminum gutters, watching a glowing 3D holographic model of "
            "a house roof unfold in the air before him, morning sunbeams through workshop dust, no text, no logos."
        ),
    },
    {
        "id": "k10",
        "format": "16:9",
        "prompt": (
            "Cinematic wide shot inside a high-bay renovation warehouse: automated beams of cyan and signal-orange light scan across neat racks "
            "of matte charcoal aluminum siding coils and gutter boxes, highlighting specific bundles with a warm golden aura while a forklift "
            "waits in the background, dramatic industrial lighting, no text, no logos."
        ),
    },
    {
        "id": "k11",
        "format": "16:9",
        "prompt": (
            "Cinematic medium close-up inside the virtual reception floor of the ten-story atrium: a 35-year-old female executive avatar with "
            "a dark auburn bob in a midnight-ink blazer with ion-blue seams stands surrounded by floating spheres of golden voice waves, speaking "
            "with warm authority, shallow depth of field, no text, no logos."
        ),
    },
    {
        "id": "k12",
        "format": "16:9",
        "prompt": (
            "Cinematic medium shot inside a parked pickup truck cab at midday: a 34-year-old sales representative in a plain slate-blue jacket "
            "sits at the steering wheel as a glowing cyan and orange acoustic waveform hovers in the air beside the dashboard, autumn trees "
            "outside the windshield, natural daylight, no text, no logos."
        ),
    },
    {
        "id": "k13",
        "format": "16:9",
        "prompt": (
            "Cinematic over-the-shoulder shot inside a warm PME mezzanine office at dusk: a 52-year-old business owner in a plain navy sweater "
            "stands before a life-size luminous 3D projection of the female financial avatar Claire emerging from a circle of ion-blue light, "
            "an ascending ribbon of golden light floating between them, no text, no logos."
        ),
    },
    {
        "id": "k14",
        "format": "16:9",
        "prompt": (
            "Cinematic close-up of the female financial avatar Claire in the virtual finance floor, sculpted from photorealistic skin and subtle "
            "cyan light filaments, gesturing toward an ascending three-dimensional wave of golden and signal-orange light particles that rises "
            "like a mountain ridge in the air, rich anamorphic bokeh, no text, no logos."
        ),
    },
    {
        "id": "k15",
        "format": "16:9",
        "prompt": (
            "Cinematic medium shot inside the virtual operations command floor: a 40-year-old female operations director avatar Sonia with a "
            "neat low bun and obsidian-grey tunic stands before a vast floating three-dimensional matrix of glowing cyan and amber light blocks "
            "representing three weeks of crew routes, dramatic volumetric lighting, no text, no logos."
        ),
    },
    {
        "id": "k16",
        "format": "16:9",
        "prompt": (
            "Cinematic medium shot at the entrance of a renovation workshop at dawn: a 29-year-old installer in a plain black hard hat and work "
            "jacket walks briskly through the bay door as a vertical arch of warm cyan light scans his silhouette and emits a crisp golden "
            "ripple in the air, morning mist outside, no text, no logos."
        ),
    },
    {
        "id": "k17",
        "format": "16:9",
        "prompt": (
            "Cinematic close-up inside a warm wood-panelled PME office: the 52-year-old owner Benoît hands a crisp cream paper envelope sealed "
            "with a glowing golden light thread to the smiling 29-year-old installer Marc, warm afternoon sunbeams streaming through the window, "
            "authentic human warmth, plain clothing with no text, no logos."
        ),
    },
    {
        "id": "k18",
        "format": "16:9",
        "prompt": (
            "Cinematic split-atmosphere wide shot: on the left, a Newly renovated Québécois house gleaming in golden sunset light as a glowing "
            "cyan frame captures its facade; on the right, inside the virtual memory vault, crystalline hexagonal blocks of golden light lock "
            "together into an unbreakable glowing chain, no text, no logos."
        ),
    },
    {
        "id": "k19",
        "format": "16:9",
        "prompt": (
            "Monumental cinematic crane shot pulling back from the ten-story virtual corporate citadel as all ten circular floors blaze in unison "
            "with ion-blue and signal-orange light, transitioning seamlessly through the smoked glass of the server rack into the quiet PME "
            "workshop at twilight, breathtaking VFX scale, no text, no logos."
        ),
    },
    {
        "id": "k20",
        "format": "16:9",
        "prompt": (
            "Cinematic wide hero shot at blue hour: the 52-year-old owner Benoît, the 34-year-old rep Étienne, and the 29-year-old installer "
            "Marc stand together at the open bay door of their illuminated renovation workshop looking out with pride while the server rack "
            "glows softly behind them, deep ink sky, warm tungsten and ion-blue contrast, no text, no logos."
        ),
    },
    {
        "id": "k21",
        "format": "9:16",
        "prompt": (
            "Vertical 9:16 cinematic frame outside a two-story Québécois house: a 34-year-old sales rep in a plain slate-blue jacket raises a "
            "matte black phone toward the high roof gable, launching a vertical spear of signal-orange and cyan light straight up into the sky, "
            "crisp morning sunlight, no text, no logos."
        ),
    },
    {
        "id": "k22",
        "format": "9:16",
        "prompt": (
            "Vertical 9:16 cinematic frame following a blazing bolt of signal-orange light rocketing from an orbital satellite down into a tall "
            "5G tower and plunging along vertical fiber cables into a sleek black server rack, dramatic speed lines, no text, no logos."
        ),
    },
    {
        "id": "k23",
        "format": "9:16",
        "prompt": (
            "Vertical 9:16 monumental interior shot looking straight up the ten-story cylindrical atrium of the virtual enterprise inside the "
            "server: ten glowing rings of specialists and a floating 3D wireframe house roof surrounded by cascading golden particles, "
            "breathtaking vertical scale, no text, no logos."
        ),
    },
    {
        "id": "k24",
        "format": "9:16",
        "prompt": (
            "Vertical 9:16 cinematic shot: the 52-year-old owner taps a glowing golden approval seal in mid-air, and the completed luminous "
            "architectural quote materializes instantly in the hand of the smiling sales rep in front of the house, no text, no logos."
        ),
    },
]

VOIX = [
    {
        "id": "v01",
        "role": "narrateur",
        "voix": "drama3-frederic",
        "texte": "Une photo sur le chantier de monsieur Morin. Dix secondes. Regardez bien ce qui se réveille.",
        "direction": "Énergique, percutant, accent québécois franc, ton de bande-annonce grand spectacle, jamais lisse.",
        "vitesse": 1.12,
        "prises": 3,
    },
    {
        "id": "v02",
        "role": "etienne",
        "voix": "drama3-adamqc",
        "texte": "Façade nord, monsieur Morin. Deux étages d'aluminium pis les gouttières. Envoie-moi l'estimé !",
        "direction": "Vendeur de terrain québécois vif et décidé, parle avec entrain sur un chantier, naturel et chaleureux.",
        "vitesse": 1.12,
        "prises": 3,
    },
    {
        "id": "v03",
        "role": "narrateur",
        "voix": "drama3-frederic",
        "texte": "Le signal bondit au satellite, file sur la fibre et plonge droit dans le serveur de votre entreprise.",
        "direction": "Rythme rapide, haletant, puissant, accent québécois authentique, suit l'accélération de l'image.",
        "vitesse": 1.14,
        "prises": 3,
    },
    {
        "id": "v04",
        "role": "narrateur",
        "voix": "drama3-frederic",
        "texte": "À l'intérieur ? Pas un simple programme. Dix départements complets. Une grande entreprise qui travaille rien que pour vous.",
        "direction": "Ample, spectaculaire, fier, articulé avec du mordant québécois.",
        "vitesse": 1.10,
        "prises": 3,
    },
    {
        "id": "v05",
        "role": "benoit",
        "voix": "drama3-frederic",
        "texte": "Le code calcule au sou près, onze critères vérifiés. Rien ne part sans mon accord. J'approuve !",
        "direction": "Patron de PME québécois solide, rassurant, tranchant sur la fin, pleine maîtrise.",
        "vitesse": 1.08,
        "prises": 3,
    },
    {
        "id": "v06",
        "role": "marc",
        "voix": "drama3-adamqc",
        "texte": "Dossier Morin reçu à la shop ! Les mesures, le pliage, les matériaux réservés : on charge le camion !",
        "direction": "Chef d'équipe chantier énergique, voix forte et franche en français québécois, prêt à l'action.",
        "vitesse": 1.12,
        "prises": 3,
    },
    {
        "id": "v07",
        "role": "claire",
        "voix": "eleven-jeannemance",
        "texte": "Vous avez un rendez-vous avec monsieur Thibault à 14 h, et j'ai déplacé votre rendez-vous de 16 h comme vous me l'avez demandé.",
        "direction": "[warm, professional, brisk, natural Québécois executive assistant]",
        "vitesse": 1.05,
        "prises": 3,
    },
    {
        "id": "v08",
        "role": "etienne",
        "voix": "drama3-adamqc",
        "texte": "Parfait, merci Claire ! Tu me sauves la vie, j'arrive chez monsieur Thibault !",
        "direction": "Souriant, reconnaissant, spontané, vrai accent québécois de tous les jours.",
        "vitesse": 1.12,
        "prises": 3,
    },
    {
        "id": "v09",
        "role": "narrateur",
        "voix": "drama3-frederic",
        "texte": "Au bureau, vous parlez directement à vos départements. Finances, opérations, stratégie.",
        "direction": "Posé mais tendu d'énergie, admiratif, accent québécois naturel.",
        "vitesse": 1.10,
        "prises": 3,
    },
    {
        "id": "v10",
        "role": "benoit",
        "voix": "drama3-frederic",
        "texte": "Claire, montre-moi où on s'en va côté rentabilité avec les chantiers de cet automne.",
        "direction": "Patron québécois naturel qui s'adresse à sa directrice financière de confiance.",
        "vitesse": 1.08,
        "prises": 3,
    },
    {
        "id": "v11",
        "role": "claire",
        "voix": "eleven-jeannemance",
        "texte": "Voici les profits anticipés, mis à jour avec les nouveaux ratios de productivité des employés : leur productivité a augmenté de 7 %.",
        "direction": "[clear, confident, executive Québécois financial presentation]",
        "vitesse": 1.04,
        "prises": 3,
    },
    {
        "id": "v12",
        "role": "sonia",
        "voix": "drama3-jeannemance",
        "texte": "Voici la cédule des trois prochaines semaines. Toutes les tournées sont optimisées, monsieur Benoît.",
        "direction": "Directrice des opérations québécoise, ton assuré, vif, précis et énergique.",
        "vitesse": 1.08,
        "prises": 3,
    },
    {
        "id": "v13",
        "role": "marc",
        "voix": "drama3-adamqc",
        "texte": "Pointé à sept heures deux ! Chantier terminé dans les temps, zéro reprise !",
        "direction": "Fier, dynamique, accent québécois franc et sympathique.",
        "vitesse": 1.12,
        "prises": 3,
    },
    {
        "id": "v14",
        "role": "benoit",
        "voix": "drama3-frederic",
        "texte": "Du pointage du matin jusqu'au chèque de paye : chaque heure travaillée compte pour vrai.",
        "direction": "Chaleureux, humain, solide, patron québécois proche de son monde.",
        "vitesse": 1.08,
        "prises": 3,
    },
    {
        "id": "v15",
        "role": "narrateur",
        "voix": "drama3-frederic",
        "texte": "Marketing, analytique, briefing du matin, mémoire chaînée : aucune donnée inventée.",
        "direction": "Cadencé, martelé sur le rythme, clair et puissant.",
        "vitesse": 1.12,
        "prises": 3,
    },
    {
        "id": "v16",
        "role": "narrateur",
        "voix": "drama3-frederic",
        "texte": "Dix départements. La puissance d'une grande entreprise, bâtie pour la vôtre.",
        "direction": "Apothéose vocale, grande ampleur, fierté québécoise, franc et vibrant.",
        "vitesse": 1.06,
        "prises": 3,
    },
    {
        "id": "v17",
        "role": "narrateur",
        "voix": "drama3-frederic",
        "texte": "Une photo sur le chantier. Le signal traverse le ciel, dix départements chiffrent et vérifient dans votre serveur : soumission approuvée en dix secondes.",
        "direction": "Ultra-dynamique, condensé, percutant pour format 13 secondes, accent québécois vif.",
        "vitesse": 1.22,
        "prises": 3,
    },
    {
        "id": "v18",
        "role": "narrateur",
        "voix": "drama3-frederic",
        "texte": "OPSYS-AI.",
        "direction": "Signature finale franche, grave, énergique et nette (isolée pour remplacement rapide).",
        "vitesse": 1.00,
        "prises": 3,
    },
]

print(f"Fiches: {len(PERSONNAGES)} persos + {len(LIEUX)} lieux = {len(PERSONNAGES)+len(LIEUX)}")
print(f"Cles: {len(CLES)}, Voix: {len(VOIX)}")

PLANS = [
    # --- SEQUENCE S1 : LA SOUMISSION PAR PHOTO ET LA COURSE DU SIGNAL ---
    {
        "id": "p01",
        "sequence": "S1",
        "recette": "h3-max",
        "images": 158,
        "graine": 4101,
        "format": "16:9",
        "refs": ["etienne", "maison_morin"],
        "premiere": "k01",
        "parole": "v02",
        "prompt": (
            "summary:\n"
            "A single continuous cinematic shot: @etienne aims his smartphone at @maison_morin, speaks to <Audio 1>, and fires a glowing signal pulse into the sky.\n\n"
            "detailed_description:\n"
            "Cinematic frame from a 2026 feature film, shot on a large-format digital cinema camera with anamorphic lenses, crisp autumn morning sunlight, rich contrast, shallow depth of field. "
            "Outside @maison_morin, a two-story Québécois house under exterior renovation, @etienne in his plain slate-blue work jacket stands in the driveway holding up a matte black smartphone with no logo.\n"
            "[Shot 1] Medium close-up on @etienne with @maison_morin behind him. He frames the upper roof gable with his phone, speaks with lively confidence matching <Audio 1>, and taps the screen; a brilliant holographic wireframe grid sweeps across the house siding and a blazing pulse of signal-orange and ion-blue light erupts from the phone upward into the sky. Dynamic low-angle push-in then tilt up. Plain clothing with no logo, no text, no letters anywhere.\n\n"
            "dialogue:\n"
            "@etienne speaks in Québécois French, matching <Audio 1> word for word.\n\n"
            "overall_soundscape:\n"
            "Crisp camera shutter chime, electric energy surge, light autumn wind.\n\n"
            "non_diegetic_music:\n"
            "N/A"
        ),
        "camera": "Plan moyen serré en légère contre-plongée, travelling avant rapide puis panoramique vertical suivant l'impulsion lumineuse vers le ciel",
        "effets": "Balayage laser bleu ion sur le revêtement de la maison et départ d'une comète orange signal (#FF5A1F) vers le ciel",
        "son": "Déclencheur optique cristallin + décharge d'énergie ascendante",
        "statut": "VISION",
    },
    {
        "id": "p02",
        "sequence": "S1",
        "recette": "h3-fast",
        "images": 124,
        "graine": 4102,
        "format": "16:9",
        "refs": [],
        "premiere": "k02",
        "parole": None,
        "prompt": (
            "summary:\n"
            "A single continuous cinematic shot following a blazing signal-orange light pulse from a 5G tower down along overhead utility pole cables.\n\n"
            "detailed_description:\n"
            "Cinematic frame from a 2026 sci-fi action commercial, shot on a large-format digital cinema camera, dramatic morning sky with high clouds, anamorphic lens flare, high contrast. "
            "A tall steel telecommunications tower and a line of wooden utility poles stretching along a Québécois road.\n"
            "[Shot 1] The shot begins from <Picture 1>. A blazing comet of signal-orange and ion-blue light strikes the top antenna of the telecommunications tower from the upper atmosphere, arcs into the overhead fiber-optic line, and races at supersonic speed along the cables from pole to pole. Fast aerial tracking camera racing alongside the light pulse. No text, no logos, no letters anywhere.\n\n"
            "overall_soundscape:\n"
            "Supersonic electromagnetic whoosh, crackling fiber-optic hum, rushing wind.\n\n"
            "non_diegetic_music:\n"
            "N/A"
        ),
        "camera": "Travelling aérien ultra-rapide suivant la comète lumineuse du sommet de la tour 5G le long des câbles des poteaux électriques",
        "effets": "Comète de données orange signal et bleu ion bondissant d'un relais satellite/5G vers la fibre optique aérienne",
        "son": "Sifflement électromagnétique supersonique et crépitement d'arc",
        "statut": "RÉEL",
    },
    {
        "id": "p03",
        "sequence": "S1",
        "recette": "h3-max",
        "images": 124,
        "graine": 4103,
        "format": "16:9",
        "refs": ["shop_bureau", "citadelle_opsys"],
        "premiere": "k03",
        "parole": None,
        "prompt": (
            "summary:\n"
            "A single continuous cinematic shot: the signal-orange light pulse plunges into the local server rack in @shop_bureau, revealing the vast @citadelle_opsys inside.\n\n"
            "detailed_description:\n"
            "Cinematic frame from a 2026 feature film, shot on a large-format digital cinema camera, warm tungsten workshop lighting contrasting with deep ion-blue server glow. "
            "Inside @shop_bureau, a sleek matte-black glass-fronted server cabinet hums quietly.\n"
            "[Shot 1] The blazing filament of signal-orange light shoots down the overhead conduit and plunges straight through the smoked-glass door of the server rack in @shop_bureau; the camera flies straight through the glass right behind the beam as the interior expands into the monumental ten-story atrium of @citadelle_opsys. Continuous macro-to-wide dive camera motion. No text, no logos, no letters anywhere.\n\n"
            "overall_soundscape:\n"
            "Deep sub-bass server ignition boom, crystalline glass resonance, monumental cathedral hum.\n\n"
            "non_diegetic_music:\n"
            "N/A"
        ),
        "camera": "Plongée vertigineuse traversant la vitre fumée du serveur local de la PME pour déboucher dans l'immense atrium virtuel",
        "effets": "Transition morphologique d'échelle : les lames du serveur deviennent les dix étages architecturaux de la Citadelle OPSYS",
        "son": "Impact grave sub-basses et ouverture acoustique monumentale",
        "statut": "RÉEL",
    },
    # --- SEQUENCE S2 : LA GRANDE ENTREPRISE DANS LE SERVEUR & M3 ESTIMATION ---
    {
        "id": "p04",
        "sequence": "S2",
        "recette": "h3-max",
        "images": 124,
        "graine": 4104,
        "format": "16:9",
        "refs": ["citadelle_opsys"],
        "premiere": "k04",
        "parole": None,
        "prompt": (
            "summary:\n"
            "A single continuous cinematic shot: inside @citadelle_opsys, all ten circular department floors ignite with synchronized activity as the signal rises through the central column.\n\n"
            "detailed_description:\n"
            "Cinematic frame from a 2026 sci-fi blockbuster, shot on a large-format digital cinema camera with anamorphic lenses, dark ink atmosphere, volumetric ion-blue and signal-orange light beams. "
            "The monumental ten-story cylindrical atrium of @citadelle_opsys.\n"
            "[Shot 1] Wide crane shot rising along the central energy core of @citadelle_opsys. As the signal-orange pulse climbs the column, ten circular glass floors light up one after another in rapid succession; luminous specialist silhouettes and holographic architectural models spin into motion across every level. Sweeping upward crane movement. No text, no logos, no letters anywhere.\n\n"
            "overall_soundscape:\n"
            "Ten rapid harmonic power-up chimes, orchestral synth swell, futuristic atrium ambience.\n\n"
            "non_diegetic_music:\n"
            "N/A"
        ),
        "camera": "Mouvement de grue ascendant majestueux au cœur de la tour cylindrique des dix départements",
        "effets": "Allumage séquentiel des 10 anneaux départementaux (M1 à M10) autour de la colonne centrale de lumière",
        "son": "Dix harmoniques d'allumage en cascade et souffle de puissance",
        "statut": "RÉEL",
    },
    {
        "id": "p05",
        "sequence": "S2",
        "recette": "h3-max",
        "images": 124,
        "graine": 4105,
        "format": "16:9",
        "refs": ["citadelle_opsys", "maison_morin"],
        "premiere": "k05",
        "parole": None,
        "prompt": (
            "summary:\n"
            "A single continuous cinematic shot: on the estimation floor of @citadelle_opsys, a glowing 3D wireframe replica of @maison_morin is analysed by thousands of golden Monte Carlo particles.\n\n"
            "detailed_description:\n"
            "Cinematic frame from a 2026 feature film, shot on a large-format digital cinema camera, dark obsidian room lit by glowing cyan and signal-orange holograms, shallow depth of field. "
            "Inside the estimation department of @citadelle_opsys, a translucent three-dimensional wireframe model of @maison_morin hovers above an obsidian table.\n"
            "[Shot 1] Medium orbital shot around the floating 3D replica of @maison_morin. Thousands of golden and ion-blue light particles cascade over the roof eaves, gutters, and siding panels like a precision Monte Carlo simulation, then snap into eleven glowing verification rings that lock into a crisp golden blueprint sheet. Orbiting camera push-in. No text, no numbers, no logos anywhere.\n\n"
            "overall_soundscape:\n"
            "Rapid crystalline calculation ticks, eleven harmonic locks, golden chime.\n\n"
            "non_diegetic_music:\n"
            "N/A"
        ),
        "camera": "Travelling circulaire rapide autour de la maquette holographique 3D de la maison Morin",
        "effets": "Simulation Monte Carlo en nuage de particules d'or et verrouillage des 11 anneaux de contrôle du devis brouillon",
        "son": "Crépitement de calcul haute précision et verrouillage cristallin",
        "statut": "RÉEL",
    },
    {
        "id": "p06",
        "sequence": "S2",
        "recette": "h3-max",
        "images": 158,
        "graine": 4106,
        "format": "16:9",
        "refs": ["benoit", "shop_bureau"],
        "premiere": "k06",
        "parole": "v05",
        "prompt": (
            "summary:\n"
            "A single continuous cinematic shot: in @shop_bureau, @benoit speaks to <Audio 1> and presses a floating golden approval seal in mid-air.\n\n"
            "detailed_description:\n"
            "Cinematic frame from a 2026 feature film, shot on a large-format digital cinema camera, warm tungsten desk lamp and cool ion-blue holographic rim light, natural skin texture, shallow depth of field. "
            "Inside the mezzanine office of @shop_bureau, @benoit in his plain dark navy sweater stands behind his oak desk.\n"
            "[Shot 1] Medium close-up on @benoit. He looks into the camera with calm authority, speaks matching <Audio 1>, and taps a glowing translucent golden seal hovering in mid-air before him; the seal flashes bright signal-orange and shoots a beam of light back into the server rack behind him. Slow confident push-in. Plain clothing with no logo, no text, no letters anywhere.\n\n"
            "dialogue:\n"
            "@benoit speaks in Québécois French, matching <Audio 1> word for word.\n\n"
            "overall_soundscape:\n"
            "Quiet office room tone, resonant bass confirmation pulse on the hand tap.\n\n"
            "non_diegetic_music:\n"
            "N/A"
        ),
        "camera": "Plan rapproché poitrine sur Benoît, lent travelling avant affirmant son autorité de décideur",
        "effets": "Sceau holographique d'approbation humaine N3/N4 qui s'embrase en orange signal au toucher de Benoît",
        "son": "Impulsion grave de validation et résonance cristalline",
        "statut": "RÉEL",
    },
    {
        "id": "p07",
        "sequence": "S2",
        "recette": "h3-max",
        "images": 124,
        "graine": 4107,
        "format": "16:9",
        "refs": ["etienne", "maison_morin"],
        "premiere": "k07",
        "parole": None,
        "prompt": (
            "summary:\n"
            "A single continuous cinematic shot: outside @maison_morin, the signal beam returns from the sky into @etienne's phone, materializing a glowing architectural quote while a second beam races away.\n\n"
            "detailed_description:\n"
            "Cinematic frame from a 2026 feature film, shot on a large-format digital cinema camera, bright morning sunlight, rich contrast, shallow depth of field. "
            "Outside @maison_morin, @etienne in his plain slate-blue work jacket holds his matte black smartphone.\n"
            "[Shot 1] Medium shot on @etienne. A bolt of ion-blue and signal-orange light drops from the overhead utility line into his phone, unfolding a luminous translucent architectural sheet in the air above his hand; @etienne grins and nods, and a second streak of signal-orange light launches from his phone back up into the overhead cables toward the workshop. Dynamic handheld tracking movement. Plain clothing with no logo, no text, no letters anywhere.\n\n"
            "overall_soundscape:\n"
            "Incoming light-speed chime, holographic paper unfold, outgoing electric zip.\n\n"
            "non_diegetic_music:\n"
            "N/A"
        ),
        "camera": "Plan moyen dynamique sur Étienne devant la maison, panoramique suivant le départ du second signal",
        "effets": "Arrivée de l'éclair retour et matérialisation du feuillet holographique du devis, puis rebond du signal vers la shop",
        "son": "Carillon d'arrivée haute vitesse et déploiement holographique",
        "statut": "RÉEL",
    },
    # --- SEQUENCE S3 : MONSIEUR MORIN, LA SHOP ET LE MATÉRIEL (M4 & M6) ---
    {
        "id": "p08",
        "sequence": "S3",
        "recette": "h3-fast",
        "images": 124,
        "graine": 4108,
        "format": "16:9",
        "refs": [],
        "premiere": "k08",
        "parole": None,
        "prompt": (
            "summary:\n"
            "A single continuous cinematic shot: a blazing signal-orange light pulse races along overhead utility cables down an autumn road straight into a renovation workshop.\n\n"
            "detailed_description:\n"
            "Cinematic frame from a 2026 feature film, shot on a large-format digital cinema camera, golden autumn morning sunlight, maple trees, dynamic motion blur. "
            "A suburban Québécois road lined with wooden utility poles leading to a large timber-and-steel renovation workshop.\n"
            "[Shot 1] The shot begins from <Picture 1>. A brilliant pulse of signal-orange and cyan light races at high speed along the overhead cables, dives down the drop wire into the workshop roof, and illuminates the open bay door below. Fast forward drone tracking shot. No text, no logos, no signs anywhere.\n\n"
            "overall_soundscape:\n"
            "High-speed electric zip along cables, rushing air, workshop bay door rumble.\n\n"
            "non_diegetic_music:\n"
            "N/A"
        ),
        "camera": "Travelling aérien rase-mottes filant le long des fils électriques jusqu'à la grande porte de la shop",
        "effets": "Impulsion lumineuse orange signal courant sur les câbles jusqu'à l'atelier",
        "son": "Sifflement électrique rapide et grondement d'atelier",
        "statut": "EN PRÉPARATION",
    },
    {
        "id": "p09",
        "sequence": "S3",
        "recette": "h3-max",
        "images": 158,
        "graine": 4109,
        "format": "16:9",
        "refs": ["marc", "shop_bureau", "maison_morin"],
        "premiere": "k09",
        "parole": "v06",
        "prompt": (
            "summary:\n"
            "A single continuous cinematic shot: in front of @shop_bureau, @marc receives the glowing 3D chantier model of @maison_morin and speaks enthusiastically to <Audio 1>.\n\n"
            "detailed_description:\n"
            "Cinematic frame from a 2026 feature film, shot on a large-format digital cinema camera, crisp morning sunbeams cutting through the open doorway of @shop_bureau, natural skin texture. "
            "@marc in his plain matte black hard hat and olive-grey canvas work jacket stands beside a dark pickup truck loaded with aluminum gutters.\n"
            "[Shot 1] Medium shot on @marc at the doorway of @shop_bureau. The signal-orange beam arrives and unfolds a floating 3D holographic wireframe of @maison_morin with highlighted gutter lines right in front of him; @marc looks at the camera with energetic pride and speaks matching <Audio 1>, gesturing toward the truck. Smooth tracking push-in. Plain clothing with no logo, no text, no letters anywhere.\n\n"
            "dialogue:\n"
            "@marc speaks in Québécois French, matching <Audio 1> word for word.\n\n"
            "overall_soundscape:\n"
            "Holographic blueprint chime, metallic clink of aluminum gutters, lively workshop ambience.\n\n"
            "non_diegetic_music:\n"
            "N/A"
        ),
        "camera": "Plan moyen devant la grande porte de la shop, travelling latéral puis rapprochement sur Marc",
        "effets": "Déploiement en plein air du plan 3D holographique du chantier de M. Morin devant le camion",
        "son": "Ouverture holographique et bruit métallique franc des gouttières d'aluminium",
        "statut": "EN PRÉPARATION",
    },
    {
        "id": "p10",
        "sequence": "S3",
        "recette": "h3-fast",
        "images": 124,
        "graine": 4110,
        "format": "16:9",
        "refs": [],
        "premiere": "k10",
        "parole": None,
        "prompt": (
            "summary:\n"
            "A single continuous cinematic shot: inside the renovation warehouse, cyan and signal-orange light beams scan racks of aluminum coils and highlight reserved bundles.\n\n"
            "detailed_description:\n"
            "Cinematic frame from a 2026 feature film, shot on a large-format digital cinema camera, dramatic industrial lighting with volumetric beams. "
            "Inside a high-bay renovation warehouse filled with neat racks of matte charcoal aluminum siding coils and gutter boxes.\n"
            "[Shot 1] The shot begins from <Picture 1>. Sweeping planes of ion-blue laser light scan across the storage racks from left to right; three pallets of aluminum coils light up with a warm signal-orange containment aura as reservation beacons lock onto them. Smooth sideways dolly tracking shot. No text, no logos, no labels anywhere.\n\n"
            "overall_soundscape:\n"
            "Laser scan sweep, three deep harmonic reservation locks, warehouse echo.\n\n"
            "non_diegetic_music:\n"
            "N/A"
        ),
        "camera": "Travelling latéral fluide le long des travées d'entrepôt de matériaux",
        "effets": "Scan laser bleu ion et halo de réservation orange signal sur les bobines d'aluminium du chantier Morin (M6 Matériel)",
        "son": "Balayage optique grave et triple verrouillage magnétique",
        "statut": "RÉEL",
    },
    # --- SEQUENCE S4 : L'ADJOINTE ADMINISTRATIVE (M1 RÉCEPTION) ---
    {
        "id": "p11",
        "sequence": "S4",
        "recette": "h3-max",
        "images": 209,
        "graine": 4111,
        "format": "16:9",
        "refs": ["claire", "citadelle_opsys"],
        "premiere": "k11",
        "parole": "v07",
        "prompt": (
            "summary:\n"
            "A single continuous cinematic shot: inside @citadelle_opsys, the virtual executive assistant @claire speaks to <Audio 1> while rearranging floating calendar spheres.\n\n"
            "detailed_description:\n"
            "Cinematic frame from a 2026 sci-fi feature film, shot on a large-format digital cinema camera, shallow depth of field, dark ink background with glowing ion-blue and warm amber accents. "
            "On the reception command floor of @citadelle_opsys, @claire in her midnight-ink blazer with glowing cyan seam lines stands poised amidst floating translucent time spheres.\n"
            "[Shot 1] Medium close-up on @claire. She looks warmly into the lens and speaks with crisp professional grace matching <Audio 1>; with a light flick of her fingers, a glowing amber sphere glides smoothly along a luminous timeline arc to a new slot. Gentle orbital push-in. Plain clothing with no logo, no text, no numbers anywhere.\n\n"
            "dialogue:\n"
            "@claire speaks in Québécois French, matching <Audio 1> word for word.\n\n"
            "overall_soundscape:\n"
            "Soft crystalline chime as the time sphere slides, subtle futuristic room tone.\n\n"
            "non_diegetic_music:\n"
            "N/A"
        ),
        "camera": "Plan rapproché sur l'avatar Claire dans l'atrium M1, léger mouvement circulaire élégant",
        "effets": "Sphères temporelles holographiques qui glissent d'un créneau à l'autre d'un geste de la main de Claire",
        "son": "Glissement cristallin et ambiance feutrée du département M1",
        "statut": "VISION",
    },
    {
        "id": "p12",
        "sequence": "S4",
        "recette": "h3-max",
        "images": 124,
        "graine": 4112,
        "format": "16:9",
        "refs": ["etienne"],
        "premiere": "k12",
        "parole": "v08",
        "prompt": (
            "summary:\n"
            "A single continuous cinematic shot: inside his pickup truck cab, @etienne smiles at a glowing voice wave and replies to <Audio 1>.\n\n"
            "detailed_description:\n"
            "Cinematic frame from a 2026 commercial, shot on a large-format digital cinema camera, natural midday sunlight through the windshield, warm skin tones, shallow depth of field. "
            "Inside a parked pickup truck cab, @etienne in his plain slate-blue jacket sits at the steering wheel as a glowing cyan-and-orange acoustic waveform shimmers in the air.\n"
            "[Shot 1] Medium close-up on @etienne from the passenger side. He smiles with genuine relief at the floating voice wave, speaks matching <Audio 1>, and shifts the truck into drive as the waveform dissolves into a guiding golden line on the windshield. Smooth handheld camera. Plain clothing with no logo, no text, no letters anywhere.\n\n"
            "dialogue:\n"
            "@etienne speaks in Québécois French, matching <Audio 1> word for word.\n\n"
            "overall_soundscape:\n"
            "Quiet truck cab interior, soft confirmation chime, subtle engine purr.\n\n"
            "non_diegetic_music:\n"
            "N/A"
        ),
        "camera": "Plan rapproché latéral dans la cabine du camion d'Étienne, lumière du jour naturelle",
        "effets": "Onde vocale holographique bleu ion et orange signal flottant dans l'habitacle qui répond à la voix de Claire",
        "son": "Ronronnement sourd du camion et carillon doux de fin d'appel",
        "statut": "VISION",
    },
    # --- SEQUENCE S5 : LA COMPTABILITÉ QUI PARLE & LA PROJECTION +7 % (M5 FINANCE) ---
    {
        "id": "p13",
        "sequence": "S5",
        "recette": "h3-max",
        "images": 141,
        "graine": 4113,
        "format": "16:9",
        "refs": ["benoit", "claire", "shop_bureau"],
        "premiere": "k13",
        "parole": "v10",
        "prompt": (
            "summary:\n"
            "A single continuous cinematic shot: in @shop_bureau, @benoit speaks to the life-size holographic projection of @claire, matching <Audio 1>.\n\n"
            "detailed_description:\n"
            "Cinematic frame from a 2026 feature film, shot on a large-format digital cinema camera, warm dusk office lighting mixed with cool ion-blue hologram light, shallow depth of field. "
            "In the mezzanine office of @shop_bureau, @benoit stands face-to-face with a life-size luminous 3D projection of @claire rising from a circle of light.\n"
            "[Shot 1] Over-the-shoulder medium shot framing @benoit in three-quarter profile facing @claire. @benoit speaks naturally and confidently matching <Audio 1>, gesturing toward the floating golden financial stream between them while @claire listens attentively and nods. Slow dolly arc around the two figures. Plain clothing with no logo, no text, no letters anywhere.\n\n"
            "dialogue:\n"
            "@benoit speaks in Québécois French, matching <Audio 1> word for word.\n\n"
            "overall_soundscape:\n"
            "Soft holographic hum, warm office room tone.\n\n"
            "non_diegetic_music:\n"
            "N/A"
        ),
        "camera": "Plan moyen par-dessus l'épaule dans le bureau en mezzanine, lent travelling circulaire reliant Benoît et l'avatar Claire",
        "effets": "Projection holographique grandeur nature de l'avatar comptable Claire face à l'administrateur",
        "son": "Bourdonnement harmonique léger du projecteur holographique",
        "statut": "VISION",
    },
    {
        "id": "p14",
        "sequence": "S5",
        "recette": "h3-max",
        "images": 209,
        "graine": 4114,
        "format": "16:9",
        "refs": ["claire", "citadelle_opsys"],
        "premiere": "k14",
        "parole": "v11",
        "prompt": (
            "summary:\n"
            "A single continuous cinematic shot: @claire speaks to <Audio 1> as a luminous 3D profit projection wave rises dramatically beside her.\n\n"
            "detailed_description:\n"
            "Cinematic frame from a 2026 sci-fi feature film, shot on a large-format digital cinema camera with anamorphic lenses, rich dark ink contrast, glowing ion-blue and signal-orange light. "
            "Inside the finance floor of @citadelle_opsys, @claire in her midnight-ink blazer stands beside a glowing three-dimensional ribbon of golden light.\n"
            "[Shot 1] Medium close-up on @claire. She speaks with executive clarity matching <Audio 1> and raises her hand; beside her, a luminous three-dimensional wave of cyan and signal-orange particles surges upward into a soaring golden peak that illuminates her face. Smooth push-in camera movement. Plain clothing with no logo, no text, no numbers anywhere.\n\n"
            "dialogue:\n"
            "@claire speaks in Québécois French, matching <Audio 1> word for word.\n\n"
            "overall_soundscape:\n"
            "Rising crystalline synth shimmer as the profit wave climbs, resonant confirmation chime.\n\n"
            "non_diegetic_music:\n"
            "N/A"
        ),
        "camera": "Plan rapproché sur l'avatar comptable Claire, travelling avant accompagné de la montée d'une vague lumineuse 3D",
        "effets": "Nappe lumineuse tridimensionnelle bleu ion et or qui s'élève en crête ascendante (+7 % affiché par l'incrustation `courbe`)",
        "son": "Montée cristalline harmonique suivant la courbe de rentabilité",
        "statut": "EN PRÉPARATION",
    },
    # --- SEQUENCE S6 : LA CÉDULE DES 3 SEMAINES (M4 OPÉRATIONS) ---
    {
        "id": "p15",
        "sequence": "S6",
        "recette": "h3-max",
        "images": 158,
        "graine": 4115,
        "format": "16:9",
        "refs": ["sonia", "benoit", "citadelle_opsys"],
        "premiere": "k15",
        "parole": "v12",
        "prompt": (
            "summary:\n"
            "A single continuous cinematic shot: on the operations floor of @citadelle_opsys, the scheduling avatar @sonia speaks to @benoit matching <Audio 1> as floating light blocks snap into a three-week matrix.\n\n"
            "detailed_description:\n"
            "Cinematic frame from a 2026 sci-fi feature film, shot on a large-format digital cinema camera, dramatic volumetric lighting, obsidian-and-cyan palette with signal-orange highlights. "
            "Inside @citadelle_opsys, @sonia in her structured obsidian-grey tunic stands before a vast floating 3D matrix of glowing light blocks while @benoit watches in the foreground.\n"
            "[Shot 1] Medium shot framing @sonia behind the floating 3D grid with @benoit in partial foreground silhouette. @sonia speaks with crisp authority matching <Audio 1> and sweeps her arm; dozens of cyan and signal-orange light blocks slide and lock into three neatly organized horizontal rows in mid-air. Dynamic tracking movement. Plain clothing with no logo, no text, no letters anywhere.\n\n"
            "dialogue:\n"
            "@sonia speaks in Québécois French, matching <Audio 1> word for word.\n\n"
            "overall_soundscape:\n"
            "Rapid magnetic block snaps, precision clockwork clicks, deep harmonic lock.\n\n"
            "non_diegetic_music:\n"
            "N/A"
        ),
        "camera": "Plan moyen dynamique sur l'avatar de gestion Sonia face à Benoît, travelling latéral dévoilant la matrice 3D",
        "effets": "Blocs lumineux 3D qui s'assemblent magnétiquement en trois rangées hebdomadaires (complétés par l'incrustation `cedule`)",
        "son": "Cliquetis magnétiques rapides de blocs qui s'emboîtent en cadence",
        "statut": "EN PRÉPARATION",
    },
    # --- SEQUENCE S7 : LE POINTAGE ET LA PAYE (M4 & M5) ---
    {
        "id": "p16",
        "sequence": "S7",
        "recette": "h3-max",
        "images": 124,
        "graine": 4116,
        "format": "16:9",
        "refs": ["marc", "shop_bureau"],
        "premiere": "k16",
        "parole": "v13",
        "prompt": (
            "summary:\n"
            "A single continuous cinematic shot: @marc walks briskly into @shop_bureau at dawn through a glowing cyan time-clock arch and speaks to <Audio 1>.\n\n"
            "detailed_description:\n"
            "Cinematic frame from a 2026 feature film, shot on a large-format digital cinema camera, crisp early-morning golden light mixing with a glowing cyan laser arch at the bay door of @shop_bureau. "
            "@marc in his plain black hard hat and olive-grey work jacket strides into the workshop carrying his tool belt.\n"
            "[Shot 1] Medium tracking shot walking backward ahead of @marc. As he steps across the threshold of @shop_bureau, a vertical arch of ion-blue light scans his shoulder and emits a warm golden ripple in the air; @marc smiles straight at the camera and speaks energetically matching <Audio 1>. Smooth Steadicam backward walk. Plain clothing with no logo, no text, no numbers anywhere.\n\n"
            "dialogue:\n"
            "@marc speaks in Québécois French, matching <Audio 1> word for word.\n\n"
            "overall_soundscape:\n"
            "Crisp electronic time-clock beep, energetic work-boot footsteps on concrete.\n\n"
            "non_diegetic_music:\n"
            "N/A"
        ),
        "camera": "Travelling arrière Steadicam précédant Marc qui franchit le portique lumineux d'entrée de l'atelier à l'aube",
        "effets": "Arche lumineuse de pointage bleu ion qui émet une onde dorée au passage de Marc (avec incrustation `pointage` 07:02)",
        "son": "Bip cristallin de pointage et pas francs de bottes de travail sur le béton",
        "statut": "EN PRÉPARATION",
    },
    {
        "id": "p17",
        "sequence": "S7",
        "recette": "h3-max",
        "images": 141,
        "graine": 4117,
        "format": "16:9",
        "refs": ["benoit", "marc", "shop_bureau"],
        "premiere": "k17",
        "parole": "v14",
        "prompt": (
            "summary:\n"
            "A single continuous cinematic shot: inside @shop_bureau, @benoit hands a crisp pay cheque envelope with a golden light seal to @marc while speaking to <Audio 1>.\n\n"
            "detailed_description:\n"
            "Cinematic frame from a 2026 feature film, shot on a large-format digital cinema camera, warm afternoon sunlight streaming through the workshop office window, rich natural skin tones, shallow depth of field. "
            "Inside @shop_bureau, @benoit in his plain navy sweater stands with @marc in his olive-grey work jacket.\n"
            "[Shot 1] Medium close-up framing @benoit and @marc. A golden filament of light from the server rack traces across a crisp cream pay envelope in @benoit's hand; @benoit hands the envelope to the smiling @marc, claps him warmly on the shoulder, and looks toward the lens speaking matching <Audio 1>. Gentle push-in. Plain clothing with no logo, no text, no letters anywhere.\n\n"
            "dialogue:\n"
            "@benoit speaks in Québécois French, matching <Audio 1> word for word.\n\n"
            "overall_soundscape:\n"
            "Crisp paper envelope rustle, warm pat on the shoulder, harmonic golden chime.\n\n"
            "non_diegetic_music:\n"
            "N/A"
        ),
        "camera": "Plan rapproché chaleureux réunissant Benoît et Marc lors de la remise du chèque de paye",
        "effets": "Fil d'or holographique reliant le serveur à l'enveloppe de paye remise en main propre",
        "son": "Froissement net du papier, tape amicale sur l'épaule et accord lumineux",
        "statut": "VISION",
    },
    # --- SEQUENCE S8 : CONVERGENCE DES 10 DÉPARTEMENTS (M7, M8, M9, M10) & APOTHÉOSE ---
    {
        "id": "p18",
        "sequence": "S8",
        "recette": "h3-fast",
        "images": 124,
        "graine": 4118,
        "format": "16:9",
        "refs": [],
        "premiere": "k18",
        "parole": None,
        "prompt": (
            "summary:\n"
            "A single continuous cinematic shot: a newly renovated house gleams in sunset light as golden crystalline memory blocks lock into an unbreakable chain.\n\n"
            "detailed_description:\n"
            "Cinematic frame from a 2026 feature film, shot on a large-format digital cinema camera, golden sunset light transitioning into a dark cybernetic vault of glowing hexagonal crystals. "
            "Split-atmosphere visual metaphor combining a completed exterior renovation with the virtual memory vault.\n"
            "[Shot 1] The shot begins from <Picture 1>. A glowing cyan frame captures the gleaming new siding and gutters of the house on the left, while on the right, translucent golden hexagonal blocks lock together one by one into a continuous glowing cryptographic chain stretching into infinity. Smooth forward camera glide. No text, no logos, no letters anywhere.\n\n"
            "overall_soundscape:\n"
            "Camera shutter flash, heavy crystalline blocks locking in sequence, deep vault resonance.\n\n"
            "non_diegetic_music:\n"
            "N/A"
        ),
        "camera": "Travelling avant fluide reliant le chantier terminé illuminé au coucher du soleil et la chaîne cristalline du registre M10",
        "effets": "Cadre lumineux M7 (Marketing) sur la façade neuve et verrouillage des blocs hexagonaux dorés M10 (Mémoire chaînée)",
        "son": "Impulsion de capture et emboîtement cristallin lourd de la chaîne de registres",
        "statut": "RÉEL",
    },
    {
        "id": "p19",
        "sequence": "S8",
        "recette": "h3-max",
        "images": 124,
        "graine": 4119,
        "format": "16:9",
        "refs": ["citadelle_opsys", "shop_bureau"],
        "premiere": "k19",
        "parole": None,
        "prompt": (
            "summary:\n"
            "A single continuous cinematic shot: all ten floors of @citadelle_opsys blaze in unison as the camera pulls back through the server glass into @shop_bureau.\n\n"
            "detailed_description:\n"
            "Cinematic frame from a 2026 blockbuster feature film, shot on a large-format digital cinema camera with anamorphic lenses, breathtaking VFX scale. "
            "The ten-story cylindrical atrium of @citadelle_opsys transitioning into @shop_bureau.\n"
            "[Shot 1] Monumental reverse crane shot pulling back rapidly from the heart of @citadelle_opsys as all ten circular department rings ignite simultaneously in a symphony of ion-blue and signal-orange light; the camera passes backward through the smoked glass door of the server rack, revealing the quiet, solid reality of @shop_bureau at twilight. Continuous reverse zoom-out. No text, no logos, no letters anywhere.\n\n"
            "overall_soundscape:\n"
            "Massive ten-chord harmonic crescendo, whoosh through glass, calm confident server hum.\n\n"
            "non_diegetic_music:\n"
            "N/A"
        ),
        "camera": "Travelling arrière monumental ressortant des 10 étages de la Citadelle à travers la vitre du serveur dans l'atelier",
        "effets": "Embrasement simultané des 10 anneaux départementaux et retour à l'échelle humaine du serveur local de la PME",
        "son": "Crescendo harmonique à dix accords et souffle de traversée du verre",
        "statut": "RÉEL",
    },
    {
        "id": "p20",
        "sequence": "S8",
        "recette": "h3-max",
        "images": 124,
        "graine": 4120,
        "format": "16:9",
        "refs": ["benoit", "etienne", "marc", "shop_bureau"],
        "premiere": "k20",
        "parole": None,
        "prompt": (
            "summary:\n"
            "A single continuous cinematic shot: @benoit, @etienne, and @marc stand proudly together at the open bay door of @shop_bureau at blue hour while the server glows behind them.\n\n"
            "detailed_description:\n"
            "Cinematic hero frame from a 2026 feature film, shot on a large-format digital cinema camera with anamorphic lenses, deep blue-hour twilight sky outside, warm tungsten workshop lights and a single vertical strip of ion-blue and signal-orange light on the server rack behind them. "
            "At the open bay door of @shop_bureau, @benoit, @etienne, and @marc stand shoulder to shoulder in their plain work clothes.\n"
            "[Shot 1] Wide heroic low-angle shot of @benoit in the center flanked by @etienne and @marc. They look out with calm pride and confidence as the warm lights of @shop_bureau frame their silhouettes and the server rack pulses softly in the background, then the scene settles into deep ink shadow for the final title card. Slow majestic dolly pull-back. Plain clothing with no logo, no text, no letters anywhere.\n\n"
            "overall_soundscape:\n"
            "Deep resonant final bass boom, peaceful evening breeze, subtle server pulse.\n\n"
            "non_diegetic_music:\n"
            "N/A"
        ),
        "camera": "Plan large héroïque en contre-plongée sur Benoît, Étienne et Marc devant la grande porte ouverte à l'heure bleue, lent recul",
        "effets": "Halo bleu ion et orange signal du serveur en arrière-plan veillant sur l'équipe humaine, fondu progressif vers l'encre du carton",
        "son": "Impact grave final et souffle apaisé du soir",
        "statut": "RÉEL",
    },
    # --- PLANS NATIFS 9:16 POUR LA VERSION VERTICALE (6 unités max) ---
    {
        "id": "pv01",
        "sequence": "V1",
        "recette": "h3-max",
        "images": 124,
        "graine": 4201,
        "format": "9:16",
        "refs": ["etienne", "maison_morin"],
        "premiere": "k21",
        "parole": None,
        "prompt": (
            "summary:\n"
            "A single continuous vertical 9:16 cinematic shot: @etienne aims his smartphone at @maison_morin and launches a blazing signal-orange light spear straight up into the sky.\n\n"
            "detailed_description:\n"
            "Vertical 9:16 cinematic frame from a 2026 feature film, crisp morning sunlight, rich contrast, shallow depth of field. "
            "Outside @maison_morin, @etienne in his plain slate-blue jacket raises a matte black phone toward the high roof gable.\n"
            "[Shot 1] Vertical medium shot tilting rapidly upward. @etienne taps his phone; a cyan wireframe scans @maison_morin and a vertical spear of signal-orange light rockets straight up into the blue sky. Fast vertical tilt up. Plain clothing with no logo, no text, no letters anywhere.\n\n"
            "overall_soundscape:\n"
            "Camera shutter chime, supersonic vertical launch whoosh.\n\n"
            "non_diegetic_music:\n"
            "N/A"
        ),
        "camera": "Cadrage 9:16 vertical, contre-plongée sur Étienne et panoramique vertical fulgurant suivant le rayon vers le ciel",
        "effets": "Scan filaire vertical de la façade et lance de lumière orange signal vers la stratosphère",
        "son": "Déclencheur optique et propulsion verticale",
        "statut": "VISION",
    },
    {
        "id": "pv02",
        "sequence": "V1",
        "recette": "h3-fast",
        "images": 124,
        "graine": 4202,
        "format": "9:16",
        "refs": [],
        "premiere": "k22",
        "parole": None,
        "prompt": (
            "summary:\n"
            "A single continuous vertical 9:16 cinematic shot: the signal-orange light bolt plunges from a 5G tower down vertical utility cables into a black server rack.\n\n"
            "detailed_description:\n"
            "Vertical 9:16 cinematic frame from a 2026 sci-fi commercial, dramatic vertical composition, high speed motion blur. "
            "A tall 5G tower and overhead fiber cables plunging down into a sleek black local server rack.\n"
            "[Shot 1] The shot begins from <Picture 1>. A blazing bolt of signal-orange and ion-blue light drops from the top of the 5G antenna, races down the vertical fiber conduit, and plunges straight through the smoked glass of the server rack. Fast vertical dive camera motion. No text, no logos, no letters anywhere.\n\n"
            "overall_soundscape:\n"
            "Electromagnetic dive whoosh, deep server ignition boom.\n\n"
            "non_diegetic_music:\n"
            "N/A"
        ),
        "camera": "Plongée verticale 9:16 suivant l'éclair du sommet de la tour 5G jusqu'au cœur du serveur",
        "effets": "Éclair vertical orange signal et bleu ion traversant les infrastructures jusqu'au serveur",
        "son": "Plongée électromagnétique et impact sub-basse",
        "statut": "RÉEL",
    },
    {
        "id": "pv03",
        "sequence": "V1",
        "recette": "h3-max",
        "images": 124,
        "graine": 4203,
        "format": "9:16",
        "refs": ["citadelle_opsys", "maison_morin"],
        "premiere": "k23",
        "parole": None,
        "prompt": (
            "summary:\n"
            "A single continuous vertical 9:16 cinematic shot: inside the ten-story vertical atrium of @citadelle_opsys, a 3D hologram of @maison_morin is calculated in a shower of golden particles.\n\n"
            "detailed_description:\n"
            "Vertical 9:16 cinematic frame from a 2026 sci-fi blockbuster, monumental vertical scale inside @citadelle_opsys, glowing ion-blue and signal-orange rings. "
            "All ten circular department levels stacked vertically above a floating 3D wireframe of @maison_morin.\n"
            "[Shot 1] Low-angle vertical crane shot looking straight up the ten glowing rings of @citadelle_opsys as cascading golden Monte Carlo particles crystallize around the 3D model of @maison_morin and lock into a glowing blueprint. Rising vertical camera movement. No text, no logos, no numbers anywhere.\n\n"
            "overall_soundscape:\n"
            "Ten harmonic chimes, rapid crystalline calculation ticks, power swell.\n\n"
            "non_diegetic_music:\n"
            "N/A"
        ),
        "camera": "Contre-plongée vertigineuse 9:16 au centre du puits cylindrique des 10 étages de la Citadelle OPSYS",
        "effets": "Perspective verticale des 10 anneaux départementaux et cristallisation Monte Carlo du devis 3D",
        "son": "Cascade harmonique et verrouillage cristallin",
        "statut": "RÉEL",
    },
    {
        "id": "pv04",
        "sequence": "V1",
        "recette": "h3-max",
        "images": 124,
        "graine": 4204,
        "format": "9:16",
        "refs": ["benoit", "etienne", "maison_morin"],
        "premiere": "k24",
        "parole": None,
        "prompt": (
            "summary:\n"
            "A single continuous vertical 9:16 cinematic shot: @benoit taps a glowing golden approval seal, and the completed quote materializes in @etienne's hand outside @maison_morin.\n\n"
            "detailed_description:\n"
            "Vertical 9:16 cinematic frame from a 2026 feature film, dynamic vertical split-to-unified transition, rich contrast. "
            "@benoit in his plain navy sweater approves the glowing seal, sending the light beam back to @etienne outside @maison_morin.\n"
            "[Shot 1] Vertical shot: @benoit taps the floating golden seal in the upper frame, launching a signal-orange bolt downward that lands directly in @etienne's smartphone in front of @maison_morin as a luminous architectural sheet unfolds above his hand and the frame settles into dark ink for the end card. Fast vertical whip-pan down. Plain clothing with no logo, no text, no letters anywhere.\n\n"
            "overall_soundscape:\n"
            "Resonant approval pulse, lightning return zip, triumphant final boom.\n\n"
            "non_diegetic_music:\n"
            "N/A"
        ),
        "camera": "Panoramique vertical éclair 9:16 reliant le geste d'approbation de Benoît au retour du devis dans la main d'Étienne",
        "effets": "Sceau d'approbation doré, retour fulgurant du signal et ouverture du devis holographique",
        "son": "Impulsion de validation, retour éclair et impact final",
        "statut": "RÉEL",
    },
]

u169 = sum(1 if p["images"] <= 124 else 2 for p in PLANS if p["format"] == "16:9")
u916 = sum(1 if p["images"] <= 124 else 2 for p in PLANS if p["format"] == "9:16")
parl = sum(1 for p in PLANS if p.get("parole") and p["format"] == "16:9")
print(f"Plans: {len(PLANS)} total | u169={u169}/40 | u916={u916}/6 | parlants={parl}/12")

MUSIQUE = {
    "prompt": (
        "Energetic cinematic electro-orchestral hybrid trailer soundtrack at 125 BPM, bright uplifting minor-to-major progression, "
        "driving analog bass arpeggios, crisp punchy electronic drums, soaring heroic brass and staccato string ostinatos, "
        "high-tech crystalline synth pulses, powerful, triumphant, propulsive, inspiring, never depressing, instrumental only. "
        "Structure: 0-14s tight rhythmic pulse and rising synth arpeggio (the signal launch); 14-35s first big brass and percussion drop "
        "(entering the ten-story virtual enterprise citadel); 35-65s propulsive driving groove with crisp rhythmic accents (field operations, "
        "warehouse scan, executive voice assistant); 65-86s soaring melodic build with warm heroic strings and high-tech shimmer "
        "(financial projection, 3-week schedule, time-clock to pay cheque); 86-105.6s massive full-orchestra and synth climax with thunderous "
        "drums, resolving on a clean resonant final chord at 101s with warm tail to 105.6s."
    ),
    "prompts": [
        (
            "Energetic cinematic electro-orchestral hybrid trailer soundtrack at 125 BPM, bright uplifting progression, driving analog bass "
            "arpeggios, crisp punchy drums, soaring heroic brass and staccato strings, high-tech crystalline synth pulses, powerful, triumphant, "
            "never depressing, instrumental only. 0-14s rising pulse; 14-35s monumental drop; 35-65s propulsive groove; 65-86s heroic build; "
            "86-106s massive climax and clean resonant finale."
        ),
        (
            "Upbeat futuristic corporate-blockbuster anthem at 125 BPM, French-touch driving synth bassline mixed with grand cinema percussion "
            "and brass, crisp rhythmic stabs on every bar, bright energetic momentum, optimistic and powerful technology theme, instrumental only."
        ),
        (
            "High-energy 15-second commercial blitz at 125 BPM: instant camera-shutter synth hook at 0s, supersonic rising arpeggio 0-6s, "
            "massive orchestral-electronic drop at 6s, triumphant brass hit at 11s, clean resonant tail to 14s, instrumental only."
        ),
    ],
    "bpm_vise": 125,
    "duree_s": 110,
    "coups": [
        {"t_s": 0.0, "evenement": "Accroche : Étienne lève son téléphone devant la maison de M. Morin"},
        {"t_s": 3.2, "evenement": "Éclair orange signal : la photo quitte le téléphone vers le ciel"},
        {"t_s": 6.4, "evenement": "Relais tour 5G et course supersonique sur la fibre des poteaux"},
        {"t_s": 10.4, "evenement": "Plongée à travers la vitre du serveur local de la PME"},
        {"t_s": 15.2, "evenement": "Premier grand drop musical : allumage des 10 étages de la Citadelle"},
        {"t_s": 20.0, "evenement": "M3 Estimation : simulation Monte Carlo et 11 critères sur la maison 3D"},
        {"t_s": 24.8, "evenement": "Approbation humaine : Benoît touche le sceau doré (18 940 $)"},
        {"t_s": 31.2, "evenement": "Retour du devis à Étienne et rebond du signal vers la shop"},
        {"t_s": 36.0, "evenement": "Le signal file sur les poteaux électriques jusqu'à l'atelier"},
        {"t_s": 40.8, "evenement": "M4 Terrain : Marc reçoit le dossier de chantier Morin devant son camion"},
        {"t_s": 47.2, "evenement": "M6 Matériel : scan laser bleu ion et réservation des bobines d'aluminium"},
        {"t_s": 52.0, "evenement": "M1 Réception : l'adjointe virtuelle Claire appelle Étienne (14 h / 16 h)"},
        {"t_s": 60.4, "evenement": "Étienne remercie Claire dans son camion et repart vers M. Thibault"},
        {"t_s": 65.2, "evenement": "M5 Finance : Benoît interroge l'avatar comptable Claire au bureau"},
        {"t_s": 70.8, "evenement": "Projection comptable : courbe ascendante et productivité +7 %"},
        {"t_s": 79.2, "evenement": "M4 Opérations : l'avatar Sonia déploie la cédule des 3 semaines"},
        {"t_s": 85.6, "evenement": "Pointage 07:02 de Marc à l'entrée de la shop"},
        {"t_s": 90.4, "evenement": "Remise du chèque de paye par Benoît à Marc"},
        {"t_s": 96.0, "evenement": "M7-M10 : façade terminée, mémoire chaînée et embrasement des 10 départements"},
        {"t_s": 100.8, "evenement": "Plan héroïque final et ouverture du carton remplaçable OPSYS-AI"},
    ],
}

# --- CONSTRUCTION DE L'EDITPLAN LONG (105.6 s = 2534 images à 24 i/s) ---
VIDEO_LONG_SPEC = [
    ("c01", "p01", 0, 154, "S1_Photo", "Étienne photographie la façade de M. Morin et lance le signal"),
    ("c02", "p02", 0, 96, "S1_Signal", "Le signal bondit de la tour 5G le long des câbles des poteaux"),
    ("c03", "p03", 0, 115, "S1_Serveur", "Le signal plonge dans le serveur local et ouvre la Citadelle"),
    ("c04", "p04", 0, 115, "S2_Citadelle", "Allumage séquentiel des 10 étages départementaux dans le serveur"),
    ("c05", "p05", 0, 115, "S2_Estimation", "M3 chiffre le devis par simulation Monte Carlo et 11 critères"),
    ("c06", "p06", 0, 154, "S2_Approbation", "Benoît vérifie et approuve humainement la soumission"),
    ("c07", "p07", 0, 115, "S2_Retour", "La soumission revient à Étienne et repart vers la shop"),
    ("c08", "p08", 0, 115, "S3_FibreShop", "Le signal file sur les poteaux jusqu'à la shop de travail"),
    ("c09", "p09", 0, 154, "S3_ChantierMorin", "Marc reçoit le dossier de chantier de M. Morin devant son camion"),
    ("c10", "p10", 0, 115, "S3_Materiel", "M6 réserve automatiquement les bobines d'aluminium en entrepôt"),
    ("c11", "p11", 0, 202, "S4_Adjointe", "L'adjointe Claire annonce le RDV de 14 h et le déplacement de 16 h"),
    ("c12", "p12", 0, 115, "S4_RepCamion", "Étienne remercie Claire dans son camion et file chez M. Thibault"),
    ("c13", "p13", 0, 134, "S5_QuestionCFO", "Benoît interroge l'avatar de sa comptabilité sur la rentabilité"),
    ("c14", "p14", 0, 202, "S5_Projection7", "L'avatar comptable Claire présente les profits anticipés (+7 %)"),
    ("c15", "p15", 0, 154, "S6_Cedule3Sem", "L'avatar de gestion Sonia présente la cédule des 3 prochaines semaines"),
    ("c16", "p16", 0, 115, "S7_Pointage", "Marc pointe son arrivée à 07:02 sous l'arche lumineuse de la shop"),
    ("c17", "p17", 0, 134, "S7_Paye", "Benoît remet le chèque de paye à Marc dans le bureau"),
    ("c18", "p18", 0, 65, "S8_Memoire", "M7 Marketing sur la maison finie et M10 Mémoire chaînée"),
    ("c19", "p19", 0, 65, "S8_Apotheose", "Les 10 départements flambent à l'unisson et retour au serveur"),
    ("c20", "p20", 0, 100, "S8_Carton", "Plan héroïque des trois humains et carton final OPSYS-AI"),
]

# Vérification des débuts d'images sur la timeline longue
cur = 0
DEBUTS_LONG = {}
for cid, src, ent, dur, sec, pq in VIDEO_LONG_SPEC:
    DEBUTS_LONG[cid] = (cur, cur + dur)
    cur += dur
TOTAL_LONG_F = cur
print(f"Total long: {TOTAL_LONG_F} frames = {TOTAL_LONG_F/24:.2f} s")

SOURCES_LONG = {
    p["id"]: {"kind": "video", "duree_f": p["images"]}
    for p in PLANS if p["format"] == "16:9"
}
SOURCES_LONG["musique_long"] = {"kind": "audio", "duree_f": TOTAL_LONG_F}
VOIX_LONG_IDS = ["v01", "v02", "v03", "v04", "v05", "v06", "v07", "v08", "v09", "v10", "v11", "v12", "v13", "v14", "v15", "v16", "v18"]
for vid in VOIX_LONG_IDS:
    SOURCES_LONG[vid] = {"kind": "audio"}

VOIX_TIMELINE_LONG = [
    # c01 (0..154) : v02 ancré sur Étienne (0..140)
    {"src": "v02", "debut_f": 4, "entree_f": 0, "duree_f": 136, "gain_db": 0},
    # c02 (154..250) : v01 narrateur accroche (154..248)
    {"src": "v01", "debut_f": 156, "entree_f": 0, "duree_f": 92, "gain_db": 0},
    # c03 (250..365) : v03 narrateur plongée serveur (252..360)
    {"src": "v03", "debut_f": 252, "entree_f": 0, "duree_f": 108, "gain_db": 0},
    # c04+c05 (365..595) : v04 narrateur 10 départements (370..520)
    {"src": "v04", "debut_f": 370, "entree_f": 0, "duree_f": 150, "gain_db": 0},
    # c06 (595..749) : v05 ancré sur Benoît (600..740)
    {"src": "v05", "debut_f": 600, "entree_f": 0, "duree_f": 140, "gain_db": 0},
    # c09 (979..1133) : v06 ancré sur Marc (984..1124)
    {"src": "v06", "debut_f": 984, "entree_f": 0, "duree_f": 140, "gain_db": 0},
    # c11 (1248..1450) : v07 ancré sur Claire (1252..1442)
    {"src": "v07", "debut_f": 1252, "entree_f": 0, "duree_f": 190, "gain_db": 0},
    # c12 (1450..1565) : v08 ancré sur Étienne (1454..1554)
    {"src": "v08", "debut_f": 1454, "entree_f": 0, "duree_f": 100, "gain_db": 0},
    # transition entre c12 et c13 / début c10 (1133..1248) : v09 narrateur (1138..1238)
    {"src": "v09", "debut_f": 1138, "entree_f": 0, "duree_f": 100, "gain_db": 0},
    # c13 (1565..1699) : v10 ancré sur Benoît (1570..1690)
    {"src": "v10", "debut_f": 1570, "entree_f": 0, "duree_f": 120, "gain_db": 0},
    # c14 (1699..1901) : v11 ancré sur Claire (1704..1894)
    {"src": "v11", "debut_f": 1704, "entree_f": 0, "duree_f": 190, "gain_db": 0},
    # c15 (1901..2055) : v12 ancré sur Sonia (1906..2046)
    {"src": "v12", "debut_f": 1906, "entree_f": 0, "duree_f": 140, "gain_db": 0},
    # c16 (2055..2170) : v13 ancré sur Marc (2060..2160)
    {"src": "v13", "debut_f": 2060, "entree_f": 0, "duree_f": 100, "gain_db": 0},
    # c17 (2170..2304) : v14 ancré sur Benoît (2175..2295)
    {"src": "v14", "debut_f": 2175, "entree_f": 0, "duree_f": 120, "gain_db": 0},
    # c18 (2304..2369) : v15 narrateur (2306..2368)
    {"src": "v15", "debut_f": 2306, "entree_f": 0, "duree_f": 62, "gain_db": 0},
    # c19 (2369..2434) : v16 narrateur apothéose (2372..2434)
    {"src": "v16", "debut_f": 2372, "entree_f": 0, "duree_f": 62, "gain_db": 0},
    # c20 (2434..2534) : v18 nom de marque isolé (2444..2474)
    {"src": "v18", "debut_f": 2444, "entree_f": 0, "duree_f": 30, "gain_db": 0},
]

EDITPLAN_LONG = {
    "version": 1,
    "fps": 24,
    "format": "16:9",
    "genre": "pub",
    "titre": "OPSYS-AI — La Citadelle dans le serveur (Version longue)",
    "sources": SOURCES_LONG,
    "video": [
        {
            "id": cid,
            "src": src,
            "entree_f": ent,
            "duree_f": dur,
            "vitesse": 1,
            "transition_in": {"type": "cut", "duree_f": 0},
            "section": sec,
            "pourquoi": pq,
        }
        for cid, src, ent, dur, sec, pq in VIDEO_LONG_SPEC
    ],
    "audio": {
        "musique": {
            "src": "musique_long",
            "entree_f": 0,
            "duree_f": TOTAL_LONG_F,
            "gain_db": -8,
            "fondu_in_f": 12,
            "fondu_out_f": 36,
        },
        "voix": VOIX_TIMELINE_LONG,
        "ducking": {"actif": True, "profondeur_db": 9},
        "cible_lufs": -14,
        "crete_db": -1.5,
        "fondu_coupe_ms": 35,
    },
    "textes": [
        {"texte": "1 PHOTO. 10 DÉPARTEMENTS.", "debut_f": 156, "duree_f": 88, "style": "titre", "position": "bas", "taille_pct": 6},
        {"texte": "LE CODE CALCULE.\nVOUS APPROUVEZ.", "debut_f": 605, "duree_f": 120, "style": "sous-titre", "position": "bas", "taille_pct": 5},
        {"texte": "PRODUIT EN CONSOLIDATION", "debut_f": 2372, "duree_f": 60, "style": "bas", "position": "bas", "taille_pct": 4},
    ],
    "generations": [],
    "metadonnees": {
        "modele": "gemini-4-argon",
        "savoir": ["higgsfield-status-hook", "kling-kinetic-proof", "signal-ion-orange", "honest-labels"],
    },
}

# --- ANNEXE LONG ---
ANNEXE_LONG = {
    "incrustations": [
        # S1 : Photo et course du signal (0..365)
        {"type": "surtitre", "debut_f": 6, "duree_f": 140, "position": "haut-gauche", "texte": "M2 · CRM → M3 · ESTIMATION"},
        {"type": "etiquette", "debut_f": 6, "duree_f": 140, "position": "haut-droite", "texte": "VISION"},
        {"type": "statut", "debut_f": 70, "duree_f": 80, "position": "bas-gauche", "texte": "Photo reçue. Mesures de façade en cours…"},
        {"type": "trajet", "debut_f": 90, "duree_f": 60, "position": "centre", "points": [[0.48, 0.62], [0.52, 0.35], [0.58, 0.08]], "couleur": "signal"},
        {"type": "flash", "debut_f": 154, "duree_f": 3, "position": "centre", "intensite": 0.75},
        {"type": "trajet", "debut_f": 158, "duree_f": 88, "position": "centre", "points": [[0.50, 0.12], [0.46, 0.42], [0.78, 0.68], [0.92, 0.74]], "couleur": "ion"},
        {"type": "statut", "debut_f": 254, "duree_f": 105, "position": "bas-gauche", "texte": "Serveur local PME atteint. Réveil des 10 départements…"},
        # S2 : La Citadelle et l'estimation M3 (365..864)
        {"type": "flash", "debut_f": 365, "duree_f": 3, "position": "centre", "intensite": 0.85},
        {"type": "impact", "debut_f": 370, "duree_f": 100, "position": "centre", "texte": "DIX DÉPARTEMENTS. *UNE ENTREPRISE.*"},
        {"type": "surtitre", "debut_f": 484, "duree_f": 260, "position": "haut-gauche", "texte": "M3 · ESTIMATION DÉTERMINISTE"},
        {"type": "statut", "debut_f": 488, "duree_f": 102, "position": "bas-gauche", "texte": "Simulation Monte Carlo · Revue en 11 critères…"},
        {
            "type": "document",
            "debut_f": 520,
            "duree_f": 225,
            "position": "droite",
            "titre": "SOUMISSION BROUILLON #M3-408",
            "destinataire": "Client : Monsieur Morin",
            "lignes": [
                ["Revêtement aluminium 2 étages", "12 450 $"],
                ["Gouttières sans joint + soffites", "4 190 $"],
                ["Main-d'œuvre et équipement", "2 300 $"],
                ["Revue 11 critères (sans coûts internes)", "VALIDE"],
            ],
            "total": "18 940 $",
            "tampon": "APPROUVÉ",
        },
        {"type": "trajet", "debut_f": 754, "duree_f": 105, "position": "centre", "points": [[0.52, 0.10], [0.48, 0.58], [0.85, 0.22]], "couleur": "signal"},
        # S3 : M. Morin, la shop et le matériel M4 / M6 (864..1248)
        {"type": "trajet", "debut_f": 868, "duree_f": 105, "position": "centre", "points": [[0.15, 0.25], [0.55, 0.38], [0.82, 0.55]], "couleur": "signal"},
        {"type": "surtitre", "debut_f": 982, "duree_f": 148, "position": "haut-gauche", "texte": "M4 · OPÉRATIONS TERRAIN"},
        {"type": "etiquette", "debut_f": 982, "duree_f": 148, "position": "haut-droite", "texte": "EN PRÉPARATION"},
        {"type": "statut", "debut_f": 988, "duree_f": 136, "position": "bas-gauche", "texte": "Dossier chantier M. Morin transmis à la shop."},
        {"type": "surtitre", "debut_f": 1136, "duree_f": 108, "position": "haut-gauche", "texte": "M6 · MATÉRIEL & RÉSERVATIONS"},
        {"type": "statut", "debut_f": 1140, "duree_f": 102, "position": "bas-gauche", "texte": "Bobines aluminium et gouttières réservées depuis le devis."},
        # S4 : L'adjointe administrative M1 (1248..1565)
        {"type": "surtitre", "debut_f": 1252, "duree_f": 308, "position": "haut-gauche", "texte": "M1 · RÉCEPTION & ADJOINTE VOCALE"},
        {"type": "etiquette", "debut_f": 1252, "duree_f": 308, "position": "haut-droite", "texte": "VISION"},
        {
            "type": "appel",
            "debut_f": 1254,
            "duree_f": 192,
            "position": "gauche",
            "nom": "Claire · Adjointe M1",
            "sous_titre": "RDV M. Thibault 14 h · 16 h déplacé",
            "voix": "v07",
        },
        {"type": "statut", "debut_f": 1454, "duree_f": 105, "position": "bas-gauche", "texte": "Agenda mis à jour : M. Thibault 14 h confirmé."},
        # S5 : La comptabilité qui parle & projection +7 % (1565..1901)
        {"type": "surtitre", "debut_f": 1568, "duree_f": 328, "position": "haut-gauche", "texte": "M5 · FINANCE & PRÉVISION 26 SEMAINES"},
        {"type": "etiquette", "debut_f": 1568, "duree_f": 130, "position": "haut-droite", "texte": "VISION"},
        {"type": "etiquette", "debut_f": 1702, "duree_f": 195, "position": "haut-droite", "texte": "EN PRÉPARATION"},
        {
            "type": "courbe",
            "debut_f": 1706,
            "duree_f": 190,
            "position": "droite",
            "points": [100, 108, 115, 124, 136, 149, 164],
            "etiquette": "PROFITS ANTICIPÉS · PRODUCTIVITÉ EMPLOYÉS",
            "valeur": "+7 %",
            "pointille_depuis": 3,
        },
        {
            "type": "compteur",
            "debut_f": 1740,
            "duree_f": 152,
            "position": "bas-gauche",
            "de": 0,
            "a": 7,
            "decimales": 0,
            "prefixe": "+",
            "suffixe": " %",
            "etiquette": "PRODUCTIVITÉ DES ÉQUIPES",
        },
        # S6 : La cédule des 3 prochaines semaines (1901..2055)
        {"type": "surtitre", "debut_f": 1904, "duree_f": 148, "position": "haut-gauche", "texte": "M4 · CÉDULE PAR TOURNÉES"},
        {"type": "etiquette", "debut_f": 1904, "duree_f": 148, "position": "haut-droite", "texte": "EN PRÉPARATION"},
        {
            "type": "cedule",
            "debut_f": 1906,
            "duree_f": 145,
            "position": "droite",
            "titre": "CÉDULE DES 3 PROCHAINES SEMAINES",
            "semaines": 3,
            "jours": ["Lun", "Mar", "Mer", "Jeu", "Ven"],
            "blocs": [
                [0, 0, 2, 0, "Chantier Morin · Façade"],
                [0, 3, 4, 1, "Thibault · Gouttières"],
                [1, 0, 2, 0, "Bélanger · Revêtement"],
                [1, 2, 4, 1, "Gagnon · Soffite-Fascia"],
                [2, 0, 3, 0, "Côté · Aluminium complet"],
                [2, 3, 4, 1, "Inspection & Finition"],
            ],
        },
        # S7 : Le pointage et la paye (2055..2304)
        {"type": "surtitre", "debut_f": 2058, "duree_f": 108, "position": "haut-gauche", "texte": "M4 · POINTAGE TERRAIN"},
        {"type": "etiquette", "debut_f": 2058, "duree_f": 108, "position": "haut-droite", "texte": "EN PRÉPARATION"},
        {
            "type": "pointage",
            "debut_f": 2060,
            "duree_f": 105,
            "position": "gauche",
            "heure": "07:02",
            "nom": "Marc · Chef d'équipe",
            "etat": "ARRIVÉE",
        },
        {"type": "surtitre", "debut_f": 2173, "duree_f": 128, "position": "haut-gauche", "texte": "M5 · DE LA POINTEUSE À LA PAYE"},
        {"type": "etiquette", "debut_f": 2173, "duree_f": 128, "position": "haut-droite", "texte": "VISION"},
        # S8 : Convergence M7-M10, Apothéose et Carton (2304..2534)
        {"type": "surtitre", "debut_f": 2306, "duree_f": 60, "position": "haut-gauche", "texte": "M7 MARKETING · M8 ANALYTIQUE · M9 STRATÉGIE · M10 MÉMOIRE"},
        {
            "type": "pile",
            "debut_f": 2370,
            "duree_f": 62,
            "position": "gauche",
            "lignes": [
                "M1 Réception · M2 CRM · M3 Estimation",
                "M4 Terrain · M5 Finance · M6 Matériel",
                "M7 Marketing · M8 Analytique · M9 Stratégie · *M10 Mémoire*",
            ],
        },
        {"type": "titre", "debut_f": 2372, "duree_f": 60, "position": "haut", "zone": "haut", "texte": "Une grande entreprise *pour la vôtre.*"},
        {"type": "flash", "debut_f": 2434, "duree_f": 3, "position": "centre", "intensite": 0.9},
        {"type": "carton", "debut_f": 2450, "duree_f": 84, "position": "centre"},
    ],
    "sfx": [
        {"type": "clic", "debut_f": 68, "db": -5},
        {"type": "montee", "debut_f": 90, "db": -6, "duree_s": 2.5},
        {"type": "fouet", "debut_f": 154, "db": -5},
        {"type": "boom", "debut_f": 250, "db": -4},
        {"type": "impact", "debut_f": 365, "db": -3},
        {"type": "frappe", "debut_f": 520, "db": -6},
        {"type": "impact", "debut_f": 690, "db": -4},
        {"type": "fouet", "debut_f": 749, "db": -5},
        {"type": "fouet", "debut_f": 864, "db": -5},
        {"type": "clic", "debut_f": 982, "db": -6},
        {"type": "souffle", "debut_f": 1135, "db": -7},
        {"type": "clic", "debut_f": 1252, "db": -6},
        {"type": "montee", "debut_f": 1705, "db": -6, "duree_s": 3.0},
        {"type": "frappe", "debut_f": 1910, "db": -6},
        {"type": "clic", "debut_f": 2060, "db": -4},
        {"type": "impact", "debut_f": 2369, "db": -4},
        {"type": "boom", "debut_f": 2434, "db": -3},
    ],
    "son_plans": [
        {"plan": "p01", "db": -10},
        {"plan": "p02", "db": -9},
        {"plan": "p03", "db": -8},
        {"plan": "p04", "db": -9},
        {"plan": "p05", "db": -10},
        {"plan": "p08", "db": -9},
        {"plan": "p10", "db": -10},
        {"plan": "p16", "db": -9},
        {"plan": "p19", "db": -8},
    ],
    "etalonnage": {"contraste": 1.08, "saturation": 1.04, "chaleur": 0.02, "grain": 0.85},
}

# --- CONSTRUCTION DE L'EDITPLAN COURT 16:9 (13.0 s = 312 images à 24 i/s) ---
VIDEO_COURT_SPEC = [
    ("sc01", "p01", 20, 64, "C1_Photo", "Étienne prend la photo de la façade et lance le signal"),
    ("sc02", "p02", 0, 56, "C2_Signal", "Le signal bondit de la tour 5G sur la fibre des poteaux"),
    ("sc03", "p03", 0, 52, "C3_Serveur", "Plongée dans le serveur local vers la Citadelle"),
    ("sc04", "p05", 0, 68, "C4_Estimation", "M3 chiffre le devis 3D avec Monte Carlo et 11 critères"),
    ("sc05", "p07", 0, 72, "C5_RetourCarton", "Le devis approuvé revient dans la main d'Étienne + carton"),
]
TOTAL_COURT_F = sum(x[3] for x in VIDEO_COURT_SPEC)
print(f"Total court 16:9: {TOTAL_COURT_F} frames = {TOTAL_COURT_F/24:.2f} s")

EDITPLAN_COURT = {
    "version": 1,
    "fps": 24,
    "format": "16:9",
    "genre": "pub",
    "titre": "OPSYS-AI — La soumission en 10 secondes (Version courte 16:9)",
    "sources": {
        "p01": {"kind": "video", "duree_f": 158},
        "p02": {"kind": "video", "duree_f": 124},
        "p03": {"kind": "video", "duree_f": 124},
        "p05": {"kind": "video", "duree_f": 124},
        "p07": {"kind": "video", "duree_f": 124},
        "musique_court": {"kind": "audio", "duree_f": TOTAL_COURT_F},
        "v17": {"kind": "audio"},
        "v18": {"kind": "audio"},
    },
    "video": [
        {
            "id": cid,
            "src": src,
            "entree_f": ent,
            "duree_f": dur,
            "vitesse": 1,
            "transition_in": {"type": "cut", "duree_f": 0},
            "section": sec,
            "pourquoi": pq,
        }
        for cid, src, ent, dur, sec, pq in VIDEO_COURT_SPEC
    ],
    "audio": {
        "musique": {
            "src": "musique_court",
            "entree_f": 0,
            "duree_f": TOTAL_COURT_F,
            "gain_db": -8,
            "fondu_in_f": 6,
            "fondu_out_f": 18,
        },
        "voix": [
            {"src": "v17", "debut_f": 4, "entree_f": 0, "duree_f": 252, "gain_db": 0},
            {"src": "v18", "debut_f": 264, "entree_f": 0, "duree_f": 32, "gain_db": 0},
        ],
        "ducking": {"actif": True, "profondeur_db": 9},
        "cible_lufs": -14,
        "crete_db": -1.5,
        "fondu_coupe_ms": 35,
    },
    "textes": [
        {"texte": "1 PHOTO. 10 DÉPARTEMENTS.", "debut_f": 68, "duree_f": 96, "style": "titre", "position": "bas", "taille_pct": 6},
    ],
    "generations": [],
    "metadonnees": {"modele": "gemini-4-argon", "savoir": ["signal-run-13s"]},
}

ANNEXE_COURT = {
    "incrustations": [
        {"type": "etiquette", "debut_f": 4, "duree_f": 60, "position": "haut-droite", "texte": "VISION"},
        {"type": "statut", "debut_f": 6, "duree_f": 56, "position": "bas-gauche", "texte": "Photo reçue. Signal vers le serveur…"},
        {"type": "trajet", "debut_f": 64, "duree_f": 56, "position": "centre", "points": [[0.50, 0.12], [0.46, 0.45], [0.85, 0.72]], "couleur": "signal"},
        {"type": "surtitre", "debut_f": 172, "duree_f": 68, "position": "haut-gauche", "texte": "M3 · ESTIMATION · 11 CRITÈRES"},
        {
            "type": "document",
            "debut_f": 176,
            "duree_f": 84,
            "position": "droite",
            "titre": "SOUMISSION #M3-408",
            "destinataire": "Client : Monsieur Morin",
            "lignes": [
                ["Revêtement + gouttières", "16 640 $"],
                ["Main-d'œuvre qualifiée", "2 300 $"],
            ],
            "total": "18 940 $",
            "tampon": "APPROUVÉ",
        },
        {"type": "flash", "debut_f": 240, "duree_f": 3, "position": "centre", "intensite": 0.8},
        {"type": "carton", "debut_f": 262, "duree_f": 50, "position": "centre"},
    ],
    "sfx": [
        {"type": "clic", "debut_f": 10, "db": -5},
        {"type": "fouet", "debut_f": 64, "db": -5},
        {"type": "boom", "debut_f": 120, "db": -4},
        {"type": "frappe", "debut_f": 180, "db": -5},
        {"type": "impact", "debut_f": 262, "db": -3},
    ],
    "son_plans": [
        {"plan": "p01", "db": -10},
        {"plan": "p02", "db": -9},
        {"plan": "p03", "db": -8},
    ],
    "etalonnage": {"contraste": 1.08, "saturation": 1.04, "chaleur": 0.02, "grain": 0.85},
}

# --- CONSTRUCTION DE L'EDITPLAN VERTICAL 9:16 (13.0 s = 312 images à 24 i/s) ---
VIDEO_VERT_SPEC = [
    ("vc01", "pv01", 0, 72, "V1_Photo", "Étienne lance le rayon vertical depuis le chantier"),
    ("vc02", "pv02", 0, 72, "V2_Signal", "Plongée verticale de la tour 5G au serveur local"),
    ("vc03", "pv03", 0, 84, "V3_Citadelle", "Les 10 étages verticaux chiffrent la maison 3D"),
    ("vc04", "pv04", 0, 84, "V4_RetourCarton", "Approbation de Benoît, retour à Étienne et carton final"),
]
TOTAL_VERT_F = sum(x[3] for x in VIDEO_VERT_SPEC)
print(f"Total vertical 9:16: {TOTAL_VERT_F} frames = {TOTAL_VERT_F/24:.2f} s")

EDITPLAN_VERTICAL = {
    "version": 1,
    "fps": 24,
    "format": "9:16",
    "genre": "social",
    "titre": "OPSYS-AI — La soumission en 10 secondes (Vertical 9:16)",
    "sources": {
        "pv01": {"kind": "video", "duree_f": 124},
        "pv02": {"kind": "video", "duree_f": 124},
        "pv03": {"kind": "video", "duree_f": 124},
        "pv04": {"kind": "video", "duree_f": 124},
        "musique_court": {"kind": "audio", "duree_f": TOTAL_VERT_F},
        "v17": {"kind": "audio"},
        "v18": {"kind": "audio"},
    },
    "video": [
        {
            "id": cid,
            "src": src,
            "entree_f": ent,
            "duree_f": dur,
            "vitesse": 1,
            "transition_in": {"type": "cut", "duree_f": 0},
            "section": sec,
            "pourquoi": pq,
        }
        for cid, src, ent, dur, sec, pq in VIDEO_VERT_SPEC
    ],
    "audio": {
        "musique": {
            "src": "musique_court",
            "entree_f": 0,
            "duree_f": TOTAL_VERT_F,
            "gain_db": -8,
            "fondu_in_f": 6,
            "fondu_out_f": 18,
        },
        "voix": [
            {"src": "v17", "debut_f": 4, "entree_f": 0, "duree_f": 252, "gain_db": 0},
            {"src": "v18", "debut_f": 264, "entree_f": 0, "duree_f": 32, "gain_db": 0},
        ],
        "ducking": {"actif": True, "profondeur_db": 9},
        "cible_lufs": -14,
        "crete_db": -1.5,
        "fondu_coupe_ms": 35,
    },
    "textes": [
        {"texte": "1 PHOTO. 10 DÉPARTEMENTS.", "debut_f": 72, "duree_f": 96, "style": "titre", "position": "bas", "taille_pct": 6},
    ],
    "generations": [],
    "metadonnees": {"modele": "gemini-4-argon", "savoir": ["vertical-signal-run"]},
}

ANNEXE_VERTICAL = {
    "incrustations": [
        {"type": "etiquette", "debut_f": 4, "duree_f": 68, "position": "haut-droite", "texte": "VISION"},
        {"type": "statut", "debut_f": 6, "duree_f": 64, "position": "bas", "texte": "Photo reçue. Mesures en cours…"},
        {"type": "trajet", "debut_f": 72, "duree_f": 72, "position": "centre", "points": [[0.50, 0.08], [0.50, 0.50], [0.50, 0.88]], "couleur": "signal"},
        {
            "type": "document",
            "debut_f": 148,
            "duree_f": 108,
            "position": "centre",
            "titre": "SOUMISSION #M3-408",
            "destinataire": "Client : Monsieur Morin",
            "lignes": [
                ["Revêtement + gouttières", "16 640 $"],
                ["Main-d'œuvre qualifiée", "2 300 $"],
            ],
            "total": "18 940 $",
            "tampon": "APPROUVÉ",
        },
        {"type": "flash", "debut_f": 258, "duree_f": 3, "position": "centre", "intensite": 0.8},
        {"type": "carton", "debut_f": 262, "duree_f": 50, "position": "centre"},
    ],
    "sfx": [
        {"type": "clic", "debut_f": 10, "db": -5},
        {"type": "fouet", "debut_f": 72, "db": -5},
        {"type": "boom", "debut_f": 144, "db": -4},
        {"type": "impact", "debut_f": 262, "db": -3},
    ],
    "son_plans": [
        {"plan": "pv01", "db": -10},
        {"plan": "pv02", "db": -9},
        {"plan": "pv03", "db": -9},
    ],
    "etalonnage": {"contraste": 1.08, "saturation": 1.04, "chaleur": 0.02, "grain": 0.85},
}

DOSSIER = {
    "equipe": "gemini",
    "titre": "La Citadelle dans le serveur",
    "personnages": PERSONNAGES,
    "lieux": LIEUX,
    "cles": CLES,
    "voix": VOIX,
    "plans": PLANS,
    "musique": MUSIQUE,
    "montage": {
        "long": EDITPLAN_LONG,
        "court": EDITPLAN_COURT,
        "vertical": EDITPLAN_VERTICAL,
    },
    "annexe": {
        "long": ANNEXE_LONG,
        "court": ANNEXE_COURT,
        "vertical": ANNEXE_VERTICAL,
    },
}

out_path = BASE / "dossier.json"
out_path.write_text(json.dumps(DOSSIER, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(f"Écrit : {out_path}")
