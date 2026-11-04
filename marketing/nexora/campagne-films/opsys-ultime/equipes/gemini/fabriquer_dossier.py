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
        "texte": "Façade nord, monsieur Morin : deux étages d'aluminium et les gouttières. Envoie-moi l'estimé !",
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
        "direction": "[energetic, proud, dynamic Québécois executive presentation, upbeat commercial delivery]",
        "vitesse": 1.12,
        "prises": 3,
    },
    {
        "id": "v12",
        "role": "sonia",
        "voix": "eleven-jeannemance",
        "texte": "Voici la cédule des trois prochaines semaines. Toutes les tournées sont optimisées, monsieur Benoît.",
        "direction": "[confident, brisk, energetic Québécois operations director, warm and decisive]",
        "vitesse": 1.10,
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
        "texte": "Dix départements complets : la puissance d'une grande entreprise, bâtie pour la vôtre.",
        "direction": "Apothéose vocale, grande ampleur, fierté québécoise, franc et vibrant, prononcer dix sans liaison sonore devant départements.",
        "vitesse": 1.08,
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
        "voix": "eleven-frederic",
        "texte": "Opsys I.A.",
        "direction": "[authoritative, warm, proud Québécois trailer signature, crisp French pronunciation]",
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
        "graine": 5104,
        "format": "16:9",
        "refs": ["citadelle_opsys"],
        "premiere": "k04",
        "parole": None,
        "prompt": (
            "summary:\n"
            "A single continuous live-action shot inside a monumental glass-and-steel ten-story corporate atrium at night in @citadelle_opsys as all ten circular mezzanine rings light up.\n\n"
            "detailed_description:\n"
            "Live-action feature film footage shot on ARRI Alexa 35 with a 35 mm anamorphic lens, natural practical light, real architectural location, fine film grain, rich optical contrast, shallow depth of field. "
            "Inside @citadelle_opsys, a real monumental ten-story cylindrical atrium built of brushed dark steel, smoked glass balustrades, and concrete columns.\n"
            "[Shot 1] Wide crane shot rising smoothly up the central atrium shaft of @citadelle_opsys. As a warm signal-orange optical fiber beam climbs the central glass column, ten circular mezzanine floors illuminate in rapid succession with cool cyan and warm tungsten practical office lights, casting real reflections on the glass railings and polished stone floor while real human specialists move across the walkways in silhouette. Sweeping upward camera crane movement. No text, no numbers, no logos, no letters anywhere.\n\n"
            "overall_soundscape:\n"
            "Ten rapid harmonic power-up chimes, deep architectural atrium resonance, subtle electrical hum.\n\n"
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
        "graine": 5105,
        "format": "16:9",
        "refs": ["citadelle_opsys", "maison_morin"],
        "premiere": "k05",
        "parole": None,
        "prompt": (
            "summary:\n"
            "A single continuous live-action shot in a dark glass boardroom of @citadelle_opsys where an optical light projection of @maison_morin is scanned by golden light points.\n\n"
            "detailed_description:\n"
            "Live-action feature film footage shot on ARRI Alexa 35 with a 50 mm anamorphic prime lens, real location, natural practical light, optical lens flare, fine film grain, shallow depth of field. "
            "Inside a real dark slate-and-glass architectural engineering room of @citadelle_opsys, a physical polished black granite table reflects a crisp optical laser projection of @maison_morin.\n"
            "[Shot 1] Medium orbital dolly shot around the granite table. Thousands of fine golden and cyan optical laser pinpoints cascade over the roof eaves and aluminum siding of the projected @maison_morin model, casting real interactive warm light reflections onto the polished stone table and glass walls behind it, then converging into eleven clean glowing circular rings of light with no writing. Smooth orbiting camera push-in. Plain surfaces with no text, no numbers, no logos, no letters anywhere.\n\n"
            "overall_soundscape:\n"
            "Rapid crystalline calculation ticks, eleven harmonic locks, golden chime.\n\n"
            "non_diegetic_music:\n"
            "N/A"
        ),
        "camera": "Travelling circulaire rapide autour de la maquette optique de la maison Morin sur table de granit",
        "effets": "Simulation Monte Carlo en nuage de points laser d'or avec reflets physiques sur le granit et 11 anneaux de contrôle",
        "son": "Crépitement de calcul haute précision et verrouillage cristallin",
        "statut": "RÉEL",
    },
    {
        "id": "p06",
        "sequence": "S2",
        "recette": "h3-max",
        "images": 158,
        "graine": 5106,
        "format": "16:9",
        "refs": ["benoit", "shop_bureau"],
        "premiere": "k06",
        "parole": "v05",
        "prompt": (
            "summary:\n"
            "A single continuous live-action shot in @shop_bureau: @benoit speaks to camera matching <Audio 1> and touches a clean glowing ring of golden light in mid-air.\n\n"
            "detailed_description:\n"
            "Live-action feature film footage shot on ARRI Alexa 35 with a 50 mm anamorphic lens, natural practical tungsten desk lamp and cool cyan rim light, real renovation office location, authentic weathered skin pores and beard texture, shallow depth of field. "
            "Inside the glass-walled mezzanine office of @shop_bureau, @benoit in his plain dark navy merino sweater stands behind a real solid oak desk.\n"
            "[Shot 1] Medium close-up on @benoit. He looks directly into the lens with calm authority and speaks matching <Audio 1> word for word; at the end of his sentence, he reaches his hand forward and taps a pure translucent golden ring of light floating in the air in front of the desk, which casts real warm orange interactive light across his fingers and face and sends a clean streak of light into the server cabinet behind him. Slow dolly push-in. Plain clothing and pure light ring with no text, no symbols, no letters, no logos anywhere.\n\n"
            "dialogue:\n"
            "@benoit speaks in Québécois French, matching <Audio 1> word for word.\n\n"
            "overall_soundscape:\n"
            "Quiet office room tone, resonant bass confirmation pulse on the hand tap.\n\n"
            "non_diegetic_music:\n"
            "N/A"
        ),
        "camera": "Plan rapproché poitrine sur Benoît, lent travelling avant affirmant son autorité de décideur",
        "effets": "Anneau optique pur d'approbation humaine N3/N4 éclairant physiquement la main et le visage de Benoît",
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
        "graine": 5110,
        "format": "16:9",
        "refs": [],
        "premiere": "k10",
        "parole": None,
        "prompt": (
            "summary:\n"
            "A single continuous live-action shot inside a real industrial aluminum warehouse where optical laser beams scan steel storage racks.\n\n"
            "detailed_description:\n"
            "Live-action feature film footage shot on ARRI Alexa 35 with a 35 mm anamorphic lens, natural practical high-bay sodium and daylight lighting, real industrial warehouse location, fine film grain, shallow depth of field. "
            "Inside a real Québécois exterior-renovation warehouse with heavy steel shelving holding rolls of matte charcoal aluminum coil stock and stacked gutter crates.\n"
            "[Shot 1] The shot begins from <Picture 1>. A crisp plane of cyan optical laser light sweeps physically across the metal racks, casting real interactive cyan and warm amber reflections on the brushed aluminum coils and concrete floor as three pallets are highlighted by a warm golden light rim. Smooth lateral dolly tracking shot. Plain industrial packaging with no text, no logos, no labels, no numbers anywhere.\n\n"
            "overall_soundscape:\n"
            "Laser scan sweep, three deep harmonic reservation locks, warehouse echo.\n\n"
            "non_diegetic_music:\n"
            "N/A"
        ),
        "camera": "Travelling latéral fluide le long des travées d'entrepôt de matériaux",
        "effets": "Scan optique bleu ion avec reflets physiques sur les bobines d'aluminium du chantier Morin (M6 Matériel)",
        "son": "Balayage optique grave et triple verrouillage magnétique",
        "statut": "RÉEL",
    },
    # --- SEQUENCE S4 : L'ADJOINTE ADMINISTRATIVE (M1 RÉCEPTION) ---
    {
        "id": "p11",
        "sequence": "S4",
        "recette": "h3-max",
        "images": 209,
        "graine": 5111,
        "format": "16:9",
        "refs": ["claire", "citadelle_opsys"],
        "premiere": "k11",
        "parole": "v07",
        "prompt": (
            "summary:\n"
            "A single continuous live-action shot in @citadelle_opsys: @claire speaks to camera matching <Audio 1> while sliding a pure glowing sphere of amber light.\n\n"
            "detailed_description:\n"
            "Live-action feature film footage shot on ARRI Alexa 35 with a 50 mm anamorphic lens, real glass-walled executive office location at dusk, natural skin pores and realistic hair texture, warm practical key light and soft cyan optical rim light, shallow depth of field. "
            "Inside @citadelle_opsys, @claire in a plain dark tailored blazer with no lapel pin and no logo stands before a dark glass wall.\n"
            "[Shot 1] Medium close-up on @claire. She looks warmly into the camera lens and speaks with natural professional poise matching <Audio 1> word for word; with a subtle gesture of her hand, a pure unlabelled sphere of warm amber light glides along a clean horizontal filament of cyan light, casting real warm interactive light on her cheek and fingers. Gentle dolly push-in. Plain clothing and pure light spheres with no text, no numbers, no clock digits, no letters, no logos anywhere.\n\n"
            "dialogue:\n"
            "@claire speaks in Québécois French, matching <Audio 1> word for word.\n\n"
            "overall_soundscape:\n"
            "Soft crystalline chime as the light sphere slides, quiet executive room tone.\n\n"
            "non_diegetic_music:\n"
            "N/A"
        ),
        "camera": "Plan rapproché sur Claire dans le bureau vitré M1, léger travelling avant",
        "effets": "Sphère lumineuse ambrée pure sans chiffre qui glisse le long d'un fil optique en éclairant le visage de Claire",
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
        "graine": 5114,
        "format": "16:9",
        "refs": ["claire", "citadelle_opsys"],
        "premiere": "k14",
        "parole": "v11",
        "prompt": (
            "summary:\n"
            "A single continuous live-action shot in @citadelle_opsys: @claire speaks to camera matching <Audio 1> beside a rising ribbon of warm golden optical light.\n\n"
            "detailed_description:\n"
            "Live-action feature film footage shot on ARRI Alexa 35 with a 50 mm anamorphic lens, real modern glass boardroom location at night, natural skin texture with realistic pores, warm practical tungsten key light and interactive golden optical glow, shallow depth of field. "
            "Inside the finance boardroom of @citadelle_opsys, @claire in a plain dark tailored blazer with a completely bare lapel and no pin stands beside a glass conference table.\n"
            "[Shot 1] Medium close-up on @claire. She speaks with warm executive clarity matching <Audio 1> word for word as a clean continuous ribbon of golden and amber optical light rises smoothly in the air beside her, casting real warm interactive light reflections across her cheek, eyes, and blazer fabric. Smooth dolly push-in. Plain clothing with no lapel pin, no brooch, no logo, no text, no numbers anywhere.\n\n"
            "dialogue:\n"
            "@claire speaks in Québécois French, matching <Audio 1> word for word.\n\n"
            "overall_soundscape:\n"
            "Rising crystalline harmonic shimmer as the light ribbon climbs, resonant confirmation chime.\n\n"
            "non_diegetic_music:\n"
            "N/A"
        ),
        "camera": "Plan rapproché sur Claire (M5 Finance), travelling avant accompagné d'un ruban optique doré",
        "effets": "Ruban optique doré éclairant physiquement le visage de Claire (+7 % affiché par l'incrustation `courbe`)",
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
        "graine": 5117,
        "format": "16:9",
        "refs": ["benoit", "marc", "shop_bureau"],
        "premiere": "k17",
        "parole": "v14",
        "prompt": (
            "summary:\n"
            "A single continuous live-action shot in @shop_bureau: @benoit speaks to camera matching <Audio 1> while handing a normal folded paper pay stub to @marc.\n\n"
            "detailed_description:\n"
            "Live-action feature film footage shot on ARRI Alexa 35 with a 50 mm anamorphic lens, natural practical afternoon sunlight through the workshop office window, real location, authentic skin pores and fabric texture, shallow depth of field. "
            "Inside @shop_bureau, @benoit in his plain dark navy sweater stands in the foreground while @marc stands in three-quarter back profile beside him with his mouth closed in a quiet nod.\n"
            "[Shot 1] Medium close-up focused on @benoit. @benoit speaks warmly directly to the camera matching <Audio 1> word for word while handing a standard small folded cream paper pay stub to @marc, who receives it silently with a grateful nod and a pat on the shoulder as a subtle warm golden optical reflection glints on the desk glass. Gentle dolly push-in on @benoit. Plain clothing and plain paper envelope with no text, no writing, no logos, no letters anywhere.\n\n"
            "dialogue:\n"
            "@benoit speaks in Québécois French, matching <Audio 1> word for word.\n\n"
            "overall_soundscape:\n"
            "Crisp paper rustle, warm pat on the shoulder, quiet workshop room tone.\n\n"
            "non_diegetic_music:\n"
            "N/A"
        ),
        "camera": "Plan rapproché chaleureux centré sur Benoît qui parle en remettant le talon de paye à Marc (vu de trois-quarts dos)",
        "effets": "Reflet optique doré subtil reliant le serveur au talon de paye remis en main propre",
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
        "graine": 5120,
        "format": "16:9",
        "refs": ["benoit", "etienne", "marc", "shop_bureau"],
        "premiere": "k20",
        "parole": None,
        "prompt": (
            "summary:\n"
            "A single continuous live-action shot at blue hour: @benoit, @etienne, and @marc stand shoulder-to-shoulder at the open bay door of @shop_bureau.\n\n"
            "detailed_description:\n"
            "Live-action feature film footage shot on ARRI Alexa 35 with a 50 mm anamorphic prime lens, real renovation workshop location at twilight, natural practical tungsten overhead lights and deep blue-hour evening sky, authentic weathered human skin texture and pores, shallow depth of field. "
            "At the open bay door of @shop_bureau, only three men—@benoit in the center flanked by @etienne and @marc—stand close together in their plain work clothes.\n"
            "[Shot 1] Medium hero shot framing @benoit, @etienne, and @marc from chest up. They look forward with calm pride and genuine human warmth as warm workshop tungsten light models their faces and a stationary dark glass server cabinet glows softly with a single steady cyan and amber reflection in the background behind them, then the exposure gently dims into dark shadow for the end card. Slow steady dolly pull-back. Plain clothing with no text, no logos, no letters anywhere.\n\n"
            "overall_soundscape:\n"
            "Deep resonant final bass boom, peaceful evening air, subtle server hum.\n\n"
            "non_diegetic_music:\n"
            "N/A"
        ),
        "camera": "Plan moyen héroïque sur Benoît, Étienne et Marc devant la grande porte de l'atelier à l'heure bleue, lent recul",
        "effets": "Reflet fixe bleu ion et ambre du serveur en arrière-plan veillant sur les trois humains, fondu vers l'encre du carton",
        "son": "Impact grave final et souffle apaisé du soir",
        "statut": "RÉEL",
    },
]

u169 = sum(1 if p["images"] <= 124 else 2 for p in PLANS if p["format"] == "16:9")
u916 = sum(1 if p["images"] <= 124 else 2 for p in PLANS if p["format"] == "9:16")
parl = sum(1 for p in PLANS if p.get("parole") and p["format"] == "16:9")
print(f"Plans: {len(PLANS)} total | u169={u169}/40 | u916={u916}/6 | parlants={parl}/12")

MUSIQUE = {
    "prompt": (
        "Energetic cinematic electro-orchestral hybrid trailer soundtrack at 125 BPM in D minor resolving to D major, built around a memorable 4-note brass and analog-synth motif (D-F-A-D octave leap), "
        "crisp punchy drums, staccato string ostinatos, driving French-touch bass arpeggios, sharp dynamic contrasts with hard stops and sub-bass drops, triumphant, propulsive, never a flat pad, instrumental only. "
        "Timed structure for 112.0s edit: 0.0-11.2s tight camera-shutter synth pulse and supersonic rising arpeggio; 11.2-12.0s dramatic hard stop silence as the signal hits the server glass; "
        "12.0-32.2s first monumental brass and percussion drop igniting the 10-story citadel, pausing briefly at 32.2-33.0s for the human approval tap; 33.0-66.0s high-energy driving groove with syncopated accents; "
        "66.0-66.8s clean acoustic break; 66.8-91.4s warm heroic strings and rising melodic build (+7% profit curve, 3-week schedule, and 07:02 time-clock); 91.4-92.2s breath before final ascent; "
        "92.2-108.5s massive full-orchestra and synth climax with thunderous drums on all 10 departments blazing; 108.5-112.0s clean resonant final D-major chord and warm sub-bass tail."
    ),
    "prompts": [
        (
            "Energetic cinematic electro-orchestral hybrid trailer soundtrack at 125 BPM in D minor to D major, memorable 4-note brass and analog-synth hook, "
            "crisp punchy drums, staccato strings, sharp dynamic contrasts and hard stops, instrumental only."
        ),
    ],
    "bpm_vise": 125,
    "duree_s": 112,
    "carte": {
        "long": {
            "impacts": [0.0, 6.42, 12.0, 17.5, 23.0, 26.42, 33.0, 37.25, 42.0, 48.42, 53.17, 61.58, 66.75, 72.33, 80.75, 87.17, 92.17, 97.67, 103.42, 108.5],
            "trous": [[11.2, 12.0], [32.2, 33.0], [66.0, 66.75], [91.4, 92.17]],
            "montees": [[6.42, 11.2], [17.5, 26.42], [72.33, 80.75], [92.17, 103.42]],
            "climax": 103.42,
            "fin": 112.0,
        },
        "court": {
            "impacts": [0.0, 2.67, 5.0, 7.17, 10.0, 10.92],
            "trous": [[4.5, 5.0], [9.5, 10.0]],
            "montees": [[0.5, 4.5], [7.17, 9.5]],
            "climax": 10.0,
            "fin": 13.0,
        },
    },
    "candidats": [
        {
            "id": "m-lyria-citadelle",
            "moteur": "lyria",
            "cible": "long",
            "duree_s": 112,
            "prompt": (
                "Cinematic electro-orchestral hybrid trailer score at 125 BPM in D minor resolving to triumphant D major, instrumental only. "
                "Signature hook: a bold 4-note staccato French horn and analog Moog brass motif (D-F-A-D octave leap) answered by crisp 16th-note cello spiccato and punchy electronic drums. "
                "0.0-11.2s: high-tension clockwork synth pulse and supersonic rising arpeggio following a fiber-optic signal race. "
                "11.2-12.0s: sudden total silence hard-stop before server impact. "
                "12.0-32.2s: massive sub-bass boom and first heroic brass drop as a ten-story architectural citadel ignites floor by floor. "
                "32.2-33.0s: brief suspended silence for the human approval touch, then a resonant golden chord at 33.0s. "
                "33.0-66.0s: propulsive French-touch bass groove at 125 BPM with tight snare rimshots and sparkling marimba-synth pulses for field operations. "
                "66.0-66.8s: clean breath break. "
                "66.8-91.4s: warm soaring strings and ascending harmonic synth arpeggios building momentum across financial projections, 3-week scheduling, and morning time-clock. "
                "91.4-92.2s: dramatic drum-fill stop. "
                "92.2-108.5s: monumental full-orchestra and analog synth climax with thunderous taiko percussion and blazing brass stating the 4-note theme in radiant D major at 103.4s. "
                "108.5-112.0s: clean final orchestral hit at 108.5s with a warm resonant tail for the title card."
            ),
        },
        {
            "id": "m-music3-citadelle",
            "moteur": "music3",
            "cible": "long",
            "duree_s": 112,
            "prompt": (
                "Global Metadata: Style: Cinematic Hybrid Electro-Orchestral Trailer Anthem | Tempo: 125 BPM | Key: D Minor to D Major | "
                "Instruments: Analog Bass Synth, Staccato Strings, Heroic Brass Section, Punchy Electronic Drums, Crystalline Pluck Arpeggiator, Taiko Percussion.\n\n"
                "Vocal Details: Instrumental only, no vocals, no choir, no spoken words.\n\n"
                "Arrangement:\n"
                "[Intro - Signal Launch 0:00-0:11] Crisp camera-shutter pluck and accelerating 16th-note analog synth arpeggio building intense forward velocity, ending on a sharp hard-stop silence at 0:11.\n"
                "[Drop 1 - The Server Citadel 0:12-0:33] Massive sub-bass impact at 0:12 launches a bold 4-note heroic brass motif over driving staccato strings and tight kick-snare groove; brief stop at 0:32 then golden brass hit at 0:33.\n"
                "[Groove - Field & Warehouse 0:33-1:06] Propulsive 125 BPM electro-acoustic groove with syncopated bassline, crisp percussion accents, and bright crystalline synth counter-melody, pausing cleanly at 1:06.\n"
                "[Build - Executive Vision 1:07-1:31] Warm emotional cellos and rising golden synth waves steadily increase in pitch and intensity with snare rolls, cutting to a 0.8-second silence at 1:31.\n"
                "[Climax & Finale 1:32-1:52] Full orchestra, soaring D-major brass fanfare, and thunderous hybrid drums unleash the main 4-note anthem at maximum power from 1:38 to 1:48.5, resolving on a single clean resonant final chord at 1:48.5 with warm decay to 1:52."
            ),
        },
        {
            "id": "m-acestep-citadelle",
            "moteur": "acestep",
            "cible": "long",
            "duree_s": 112,
            "prompt": (
                "cinematic hybrid orchestral electronic trailer, 125 bpm, D minor to D major, instrumental only, no vocals, "
                "memorable 4-note heroic brass and analog synth lead motif, staccato strings, punchy French-touch bassline, crisp cinematic percussion, "
                "high dynamic range with hard stops and sub-bass drops, never a flat pad. "
                "[0:00-0:11] tight clockwork synth pulse and rising arpeggio; [0:11-0:12] hard stop silence; "
                "[0:12-0:33] massive bass drop and heroic brass theme with brief stop at 0:32; "
                "[0:33-1:06] propulsive 125 bpm driving bass and staccato string groove; [1:06-1:07] clean break; "
                "[1:07-1:31] soaring melodic string and synth build; [1:31-1:32] breath stop; "
                "[1:32-1:48] triumphant full-orchestra and synth climax; [1:48-1:52] clean final hit and resonant tail."
            ),
        },
        {
            "id": "m-lyria-blitz-court",
            "moteur": "lyria",
            "cible": "court",
            "duree_s": 14,
            "prompt": (
                "High-impact 13-second cinematic electro-orchestral commercial blitz at 125 BPM in D major, instrumental only. "
                "0.0-4.5s: instant camera-shutter synth hook and supersonic rising analog arpeggio with tight ticking percussion. "
                "4.5-5.0s: dramatic half-second hard-stop silence as the signal hits the server glass. "
                "5.0-9.5s: massive sub-bass boom and driving 4-note heroic brass and staccato string groove. "
                "9.5-10.0s: quick breath stop, then at 10.0s a triumphant full-orchestra and synth climax hit resolving cleanly at 10.9s with a warm resonant tail to 13.0s."
            ),
        },
    ],
    "coups": [
        {"t_s": 0.0, "evenement": "Accroche : Étienne lève son téléphone devant la maison de M. Morin"},
        {"t_s": 6.42, "evenement": "Relais tour 5G et course supersonique sur la fibre des poteaux"},
        {"t_s": 12.0, "evenement": "Premier grand drop après silence (11.2-12.0s) : plongée dans le serveur local"},
        {"t_s": 17.5, "evenement": "Allumage des 10 étages de la Citadelle dans le serveur"},
        {"t_s": 23.0, "evenement": "M3 Estimation : simulation Monte Carlo et 11 critères sur la maison"},
        {"t_s": 33.0, "evenement": "Approbation humaine après micro-silence : Benoît valide (18 940 $)"},
        {"t_s": 37.25, "evenement": "Le signal file sur les poteaux électriques jusqu'à l'atelier"},
        {"t_s": 42.0, "evenement": "M4 Terrain : Marc reçoit le dossier de chantier Morin devant son camion"},
        {"t_s": 48.42, "evenement": "M6 Matériel : scan optique bleu ion des bobines d'aluminium en entrepôt"},
        {"t_s": 53.17, "evenement": "M1 Réception : l'adjointe Claire confirme le RDV de 14 h et déplace 16 h"},
        {"t_s": 61.58, "evenement": "Étienne remercie Claire dans son camion et repart vers M. Thibault"},
        {"t_s": 66.75, "evenement": "Reprise après respiration : M5 Finance, Benoît interroge sa comptabilité"},
        {"t_s": 72.33, "evenement": "Projection comptable : montée mélodique sur la productivité +7 %"},
        {"t_s": 80.75, "evenement": "M4 Opérations : Sonia déploie la cédule des 3 prochaines semaines"},
        {"t_s": 87.17, "evenement": "Pointage 07:02 de Marc à l'entrée de la shop"},
        {"t_s": 92.17, "evenement": "Remise du talon de paye après respiration et lancement du final"},
        {"t_s": 97.67, "evenement": "M7-M10 : façade terminée et mémoire chaînée"},
        {"t_s": 103.42, "evenement": "Climax : embrasement des 10 départements et retour au serveur PME"},
        {"t_s": 108.5, "evenement": "Accord final résolu et ouverture du carton remplaçable OPSYS-AI"},
    ],
}

# --- CONSTRUCTION DE L'EDITPLAN LONG (106.5 s = 2556 images à 24 i/s) ---
VIDEO_LONG_SPEC = [
    ("c01", "p01", 0, 154, "S1_Photo", "Étienne photographie la façade de M. Morin et lance le signal"),
    ("c02", "p02", 0, 66, "S1_Signal5G", "Le signal bondit du sommet de la tour 5G vers la fibre aérienne"),
    ("c03", "p02", 52, 68, "S1_SignalFibre", "Accélération supersonique de la comète orange le long des poteaux"),
    ("c04", "p03", 0, 64, "S1_Serveur", "Le signal plonge à travers la vitre fumée du serveur local de la PME"),
    ("c05", "p03", 56, 68, "S1_Ouverture", "L'intérieur du serveur s'ouvre sur l'atrium monumental des 10 étages"),
    ("c06", "p04", 0, 66, "S2_CitadelleBas", "Allumage séquentiel des premiers étages départementaux dans le serveur"),
    ("c07", "p04", 54, 66, "S2_CitadelleHaut", "Mouvement de grue ascendant : les 10 départements tournent à plein régime"),
    ("c08", "p05", 0, 82, "S2_Estimation", "M3 chiffre le devis par simulation Monte Carlo et verrouille les 11 critères"),
    ("c09", "p06", 0, 158, "S2_Approbation", "Benoît vérifie et approuve humainement la soumission d'un geste"),
    ("c10", "p07", 0, 102, "S2_Retour", "La soumission approuvée revient à Étienne et rebondit vers la shop"),
    ("c11", "p08", 0, 114, "S3_FibreShop", "Le signal file sur les poteaux électriques jusqu'à l'atelier"),
    ("c12", "p09", 0, 154, "S3_ChantierMorin", "Marc reçoit le dossier de chantier de M. Morin devant son camion"),
    ("c13", "p10", 0, 114, "S3_Materiel", "M6 scanne et réserve automatiquement les bobines d'aluminium en entrepôt"),
    ("c14", "p11", 0, 202, "S4_Adjointe", "L'adjointe Claire annonce le RDV de 14 h et le déplacement de 16 h"),
    ("c15", "p12", 0, 124, "S4_RepCamion", "Étienne remercie Claire dans son camion et file chez M. Thibault"),
    ("c16", "p13", 0, 134, "S5_QuestionCFO", "Benoît interroge sa directrice financière sur la rentabilité de l'automne"),
    ("c17", "p14", 0, 202, "S5_Projection7", "Claire présente les profits anticipés et la productivité à +7 %"),
    ("c18", "p15", 0, 154, "S6_Cedule3Sem", "Sonia déploie la cédule optimisée des 3 prochaines semaines"),
    ("c19", "p16", 0, 120, "S7_Pointage", "Marc pointe son arrivée à 07:02 sous l'arche optique de la shop"),
    ("c20", "p17", 0, 132, "S7_Paye", "Benoît remet le talon de paye à Marc dans le bureau de l'atelier"),
    ("c21", "p18", 0, 68, "S8_Marketing", "M7 Marketing : capture optique de la façade rénovée au coucher du soleil"),
    ("c22", "p18", 52, 70, "S8_Memoire", "M10 Mémoire : verrouillage des blocs cristallins dans le registre chaîné"),
    ("c23", "p19", 36, 96, "S8_Apotheose", "Traversée retour de la vitre du serveur vers la réalité du bureau PME"),
    ("c24", "p20", 0, 110, "S8_Carton", "Plan héroïque de Benoît, Étienne et Marc à l'heure bleue et carton OPSYS-AI"),
]

# Vérification des débuts d'images sur la timeline longue
cur = 0
DEBUTS_LONG = {}
for cid, src, ent, dur, sec, pq in VIDEO_LONG_SPEC:
    DEBUTS_LONG[cid] = (cur, cur + dur)
    cur += dur
TOTAL_LONG_F = cur
print(f"Total long: {TOTAL_LONG_F} frames = {TOTAL_LONG_F/24:.2f} s ({len(VIDEO_LONG_SPEC)} clips)")

SOURCES_LONG = {
    p["id"]: {"kind": "video", "duree_f": p["images"]}
    for p in PLANS if p["format"] == "16:9"
}
SOURCES_LONG["musique_long"] = {"kind": "audio", "duree_f": TOTAL_LONG_F}
VOIX_LONG_IDS = ["v01", "v02", "v03", "v04", "v05", "v06", "v07", "v08", "v09", "v10", "v11", "v12", "v13", "v14", "v15", "v16", "v18"]
for vid in VOIX_LONG_IDS:
    SOURCES_LONG[vid] = {"kind": "audio"}

VOIX_TIMELINE_LONG = [
    # c01 (0..154) : v02 ancré sur Étienne dès l'image 0 (fin à 124)
    {"src": "v02", "debut_f": 0, "entree_f": 0, "duree_f": 124, "gain_db": 0},
    # c02+c03 (154..288) : v01 narrateur accroche (prise 1 = 5.32s = 128f -> 156..284, zéro chevauchement)
    {"src": "v01", "debut_f": 156, "entree_f": 0, "duree_f": 128, "gain_db": 0},
    # c04+c05 (288..420) : v03 narrateur plongée serveur (prise 2 = 5.22s = 126f -> 290..416)
    {"src": "v03", "debut_f": 290, "entree_f": 0, "duree_f": 126, "gain_db": 0},
    # c06+c07+c08 (420..634) : v04 narrateur 10 départements (prise 1 = 7.48s = 180f -> 424..604)
    {"src": "v04", "debut_f": 424, "entree_f": 0, "duree_f": 180, "gain_db": 0},
    # c09 (634..792) : v05 ancré sur Benoît dès le début du plan (prise 2 = 6.38s = 154f -> 634..788)
    {"src": "v05", "debut_f": 634, "entree_f": 0, "duree_f": 154, "gain_db": 0},
    # c12 (1008..1162) : v06 ancré sur Marc dès le début du plan (prise 3 = 5.64s = 136f -> 1008..1144)
    {"src": "v06", "debut_f": 1008, "entree_f": 0, "duree_f": 136, "gain_db": 0},
    # c13 (1162..1276) : v09 narrateur transition entrepôt -> bureaux (prise 3 = 5.32s, coupé proprement à 108f -> 1166..1274)
    {"src": "v09", "debut_f": 1166, "entree_f": 0, "duree_f": 108, "gain_db": 0},
    # c14 (1276..1478) : v07 ancré sur Claire dès le début du plan (prise 2 = 6.12s = 148f -> 1276..1424)
    {"src": "v07", "debut_f": 1276, "entree_f": 0, "duree_f": 148, "gain_db": 0},
    # c15 (1478..1602) : v08 ancré sur Étienne dès le début du plan (prise 3 = 3.76s = 91f -> 1478..1569)
    {"src": "v08", "debut_f": 1478, "entree_f": 0, "duree_f": 91, "gain_db": 0},
    # c16 (1602..1736) : v10 ancré sur Benoît dès le début du plan (prise 2 = 3.78s = 91f -> 1602..1693)
    {"src": "v10", "debut_f": 1602, "entree_f": 0, "duree_f": 91, "gain_db": 0},
    # c17 (1736..1938) : v11 ancré sur Claire dès le début du plan (1736..1920)
    {"src": "v11", "debut_f": 1736, "entree_f": 0, "duree_f": 184, "gain_db": 0},
    # c18 (1938..2092) : v12 ancré sur Sonia dès le début du plan (1938..2070)
    {"src": "v12", "debut_f": 1938, "entree_f": 0, "duree_f": 132, "gain_db": 0},
    # c19 (2092..2212) : v13 ancré sur Marc dès le début du plan (prise 2 = 4.40s = 106f -> 2092..2198)
    {"src": "v13", "debut_f": 2092, "entree_f": 0, "duree_f": 106, "gain_db": 0},
    # c20 (2212..2344) : v14 ancré sur Benoît dès le début du plan (prise 3 = 4.74s = 114f -> 2212..2326)
    {"src": "v14", "debut_f": 2212, "entree_f": 0, "duree_f": 114, "gain_db": 0},
    # c21+c22 (2344..2482) : v15 narrateur M7-M10 (prise 1 = 5.52s = 133f -> 2346..2479)
    {"src": "v15", "debut_f": 2346, "entree_f": 0, "duree_f": 133, "gain_db": 0},
    # c23+début c24 (2482..2688) : v16 narrateur apothéose (2484..2596) puis v18 signature isolée (2604..2628)
    {"src": "v16", "debut_f": 2484, "entree_f": 0, "duree_f": 112, "gain_db": 0},
    {"src": "v18", "debut_f": 2604, "entree_f": 0, "duree_f": 24, "gain_db": 0},
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
        {"texte": "1 PHOTO. 10 DÉPARTEMENTS.", "debut_f": 156, "duree_f": 124, "style": "titre", "position": "bas", "taille_pct": 6},
        {"texte": "LE CODE CALCULE.\nVOUS APPROUVEZ.", "debut_f": 636, "duree_f": 148, "style": "sous-titre", "position": "bas", "taille_pct": 5},
        {"texte": "PRODUIT EN CONSOLIDATION", "debut_f": 2484, "duree_f": 42, "style": "bas", "position": "bas", "taille_pct": 4},
    ],
    "generations": [],
    "metadonnees": {
        "modele": "gemini-4-argon",
        "savoir": ["higgsfield-status-hook", "kling-kinetic-proof", "signal-ion-orange", "honest-labels", "zero-voice-overlap", "live-action-arri"],
    },
}

# --- ANNEXE LONG ---
ANNEXE_LONG = {
    "incrustations": [
        # S1 : Photo et course du signal (0..420)
        {"type": "surtitre", "debut_f": 6, "duree_f": 140, "position": "haut-gauche", "texte": "M2 · CRM → M3 · ESTIMATION"},
        {"type": "etiquette", "debut_f": 6, "duree_f": 140, "position": "haut-droite", "texte": "VISION"},
        {"type": "statut", "debut_f": 70, "duree_f": 80, "position": "bas-gauche", "texte": "Photo reçue. Mesures de façade en cours…"},
        {"type": "trajet", "debut_f": 90, "duree_f": 60, "position": "centre", "points": [[0.48, 0.62], [0.52, 0.35], [0.58, 0.08]], "couleur": "signal"},
        {"type": "flash", "debut_f": 154, "duree_f": 3, "position": "centre", "intensite": 0.75},
        {"type": "trajet", "debut_f": 158, "duree_f": 124, "position": "centre", "points": [[0.50, 0.12], [0.46, 0.42], [0.78, 0.68], [0.92, 0.74]], "couleur": "ion"},
        {"type": "statut", "debut_f": 292, "duree_f": 122, "position": "bas-gauche", "texte": "Serveur local PME atteint. Réveil des 10 départements…"},
        # S2 : La Citadelle et l'estimation M3 (420..894)
        {"type": "flash", "debut_f": 420, "duree_f": 3, "position": "centre", "intensite": 0.85},
        {"type": "impact", "debut_f": 424, "duree_f": 120, "position": "centre", "texte": "DIX DÉPARTEMENTS. *UNE ENTREPRISE.*"},
        {"type": "surtitre", "debut_f": 552, "duree_f": 236, "position": "haut-gauche", "texte": "M3 · ESTIMATION DÉTERMINISTE"},
        {"type": "statut", "debut_f": 554, "duree_f": 76, "position": "bas-gauche", "texte": "Simulation Monte Carlo · Revue en 11 critères…"},
        {
            "type": "document",
            "debut_f": 560,
            "duree_f": 228,
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
        {"type": "trajet", "debut_f": 794, "duree_f": 96, "position": "centre", "points": [[0.52, 0.10], [0.48, 0.58], [0.85, 0.22]], "couleur": "signal"},
        # S3 : M. Morin, la shop et le matériel M4 / M6 (894..1276)
        {"type": "trajet", "debut_f": 898, "duree_f": 106, "position": "centre", "points": [[0.15, 0.25], [0.55, 0.38], [0.82, 0.55]], "couleur": "signal"},
        {"type": "surtitre", "debut_f": 1010, "duree_f": 148, "position": "haut-gauche", "texte": "M4 · OPÉRATIONS TERRAIN"},
        {"type": "etiquette", "debut_f": 1010, "duree_f": 148, "position": "haut-droite", "texte": "EN PRÉPARATION"},
        {"type": "statut", "debut_f": 1014, "duree_f": 140, "position": "bas-gauche", "texte": "Dossier chantier M. Morin transmis à la shop."},
        {"type": "surtitre", "debut_f": 1164, "duree_f": 108, "position": "haut-gauche", "texte": "M6 · MATÉRIEL & RÉSERVATIONS"},
        {"type": "statut", "debut_f": 1168, "duree_f": 102, "position": "bas-gauche", "texte": "Bobines aluminium et gouttières réservées depuis le devis."},
        # S4 : L'adjointe administrative M1 (1276..1602)
        {"type": "surtitre", "debut_f": 1278, "duree_f": 320, "position": "haut-gauche", "texte": "M1 · RÉCEPTION & ADJOINTE VOCALE"},
        {"type": "etiquette", "debut_f": 1278, "duree_f": 320, "position": "haut-droite", "texte": "VISION"},
        {
            "type": "appel",
            "debut_f": 1280,
            "duree_f": 192,
            "position": "gauche",
            "nom": "Claire · Adjointe M1",
            "sous_titre": "RDV M. Thibault 14 h · 16 h déplacé",
            "voix": "v07",
        },
        {"type": "statut", "debut_f": 1482, "duree_f": 114, "position": "bas-gauche", "texte": "Agenda mis à jour : M. Thibault 14 h confirmé."},
        # S5 : La comptabilité qui parle & projection +7 % (1602..1938)
        {"type": "surtitre", "debut_f": 1604, "duree_f": 330, "position": "haut-gauche", "texte": "M5 · FINANCE & PRÉVISION 26 SEMAINES"},
        {"type": "etiquette", "debut_f": 1604, "duree_f": 130, "position": "haut-droite", "texte": "VISION"},
        {"type": "etiquette", "debut_f": 1738, "duree_f": 196, "position": "haut-droite", "texte": "EN PRÉPARATION"},
        {
            "type": "courbe",
            "debut_f": 1740,
            "duree_f": 192,
            "position": "droite",
            "points": [100, 108, 115, 124, 136, 149, 164],
            "etiquette": "PROFITS ANTICIPÉS · PRODUCTIVITÉ EMPLOYÉS",
            "valeur": "+7 %",
            "pointille_depuis": 3,
        },
        {
            "type": "compteur",
            "debut_f": 1770,
            "duree_f": 160,
            "position": "bas-gauche",
            "de": 0,
            "a": 7,
            "decimales": 0,
            "prefixe": "+",
            "suffixe": " %",
            "etiquette": "PRODUCTIVITÉ DES ÉQUIPES",
        },
        # S6 : La cédule des 3 prochaines semaines (1938..2092)
        {"type": "surtitre", "debut_f": 1940, "duree_f": 148, "position": "haut-gauche", "texte": "M4 · CÉDULE PAR TOURNÉES"},
        {"type": "etiquette", "debut_f": 1940, "duree_f": 148, "position": "haut-droite", "texte": "EN PRÉPARATION"},
        {
            "type": "cedule",
            "debut_f": 1942,
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
        # S7 : Le pointage et la paye (2092..2344)
        {"type": "surtitre", "debut_f": 2094, "duree_f": 114, "position": "haut-gauche", "texte": "M4 · POINTAGE TERRAIN"},
        {"type": "etiquette", "debut_f": 2094, "duree_f": 114, "position": "haut-droite", "texte": "EN PRÉPARATION"},
        {
            "type": "pointage",
            "debut_f": 2096,
            "duree_f": 110,
            "position": "gauche",
            "heure": "07:02",
            "nom": "Marc · Chef d'équipe",
            "etat": "ARRIVÉE",
        },
        {"type": "surtitre", "debut_f": 2214, "duree_f": 126, "position": "haut-gauche", "texte": "M5 · DE LA POINTEUSE À LA PAYE"},
        {"type": "etiquette", "debut_f": 2214, "duree_f": 126, "position": "haut-droite", "texte": "VISION"},
        # S8 : Convergence M7-M10, Apothéose et Carton (2344..2688)
        {"type": "surtitre", "debut_f": 2346, "duree_f": 132, "position": "haut-gauche", "texte": "M7 MARKETING · M8 ANALYTIQUE · M9 STRATÉGIE · M10 MÉMOIRE"},
        {
            "type": "pile",
            "debut_f": 2414,
            "duree_f": 160,
            "position": "gauche",
            "lignes": [
                "M1 Réception · M2 CRM · M3 Estimation",
                "M4 Terrain · M5 Finance · M6 Matériel",
                "M7 Marketing · M8 Analytique · M9 Stratégie · *M10 Mémoire*",
            ],
        },
        {"type": "titre", "debut_f": 2484, "duree_f": 112, "position": "haut", "zone": "haut", "texte": "Une grande entreprise *pour la vôtre.*"},
        {"type": "flash", "debut_f": 2482, "duree_f": 3, "position": "centre", "intensite": 0.9},
        {"type": "carton", "debut_f": 2604, "duree_f": 84, "position": "centre"},
    ],
    "sfx": [
        {"type": "clic", "debut_f": 68, "db": -5},
        {"type": "montee", "debut_f": 90, "db": -6, "duree_s": 2.5},
        {"type": "fouet", "debut_f": 154, "db": -5},
        {"type": "fouet", "debut_f": 220, "db": -6},
        {"type": "inverse", "debut_f": 268, "db": -6, "duree_s": 0.8},
        {"type": "boom", "debut_f": 288, "db": -3},
        {"type": "impact", "debut_f": 420, "db": -3},
        {"type": "frappe", "debut_f": 552, "db": -5},
        {"type": "impact", "debut_f": 703, "db": -4},
        {"type": "fouet", "debut_f": 792, "db": -5},
        {"type": "fouet", "debut_f": 894, "db": -5},
        {"type": "clic", "debut_f": 1008, "db": -6},
        {"type": "souffle", "debut_f": 1162, "db": -7},
        {"type": "clic", "debut_f": 1276, "db": -6},
        {"type": "chute", "debut_f": 1500, "db": -7},
        {"type": "montee", "debut_f": 1736, "db": -6, "duree_s": 3.0},
        {"type": "frappe", "debut_f": 1938, "db": -6},
        {"type": "clic", "debut_f": 2092, "db": -4},
        {"type": "inverse", "debut_f": 2192, "db": -6, "duree_s": 0.8},
        {"type": "impact", "debut_f": 2344, "db": -4},
        {"type": "boom", "debut_f": 2482, "db": -3},
    ],
    "son_plans": [
        {"plan": "p02", "db": -9},
        {"plan": "p03", "db": -8},
        {"plan": "p04", "db": -9},
        {"plan": "p05", "db": -10},
        {"plan": "p07", "db": -10},
        {"plan": "p08", "db": -9},
        {"plan": "p10", "db": -10},
        {"plan": "p18", "db": -10},
        {"plan": "p19", "db": -8},
    ],
    "etalonnage": {"contraste": 1.08, "saturation": 1.04, "chaleur": 0.02, "grain": 0.85},
}

# --- CONSTRUCTION DE L'EDITPLAN COURT 16:9 (13.0 s = 312 images à 24 i/s) ---
VIDEO_COURT_SPEC = [
    ("sc01", "p01", 20, 64, "C1_Photo", "Étienne prend la photo de la façade et lance le signal"),
    ("sc02", "p02", 0, 56, "C2_Signal", "Le signal bondit de la tour 5G sur la fibre des poteaux"),
    ("sc03", "p03", 0, 52, "C3_Serveur", "Plongée dans le serveur local vers la Citadelle"),
    ("sc04", "p05", 0, 68, "C4_Estimation", "M3 chiffre le devis par projection optique et 11 critères"),
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
            {"src": "v17", "debut_f": 4, "entree_f": 0, "duree_f": 188, "gain_db": 0},
            {"src": "v18", "debut_f": 264, "entree_f": 0, "duree_f": 24, "gain_db": 0},
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
        {"plan": "p02", "db": -9},
        {"plan": "p03", "db": -8},
        {"plan": "p05", "db": -10},
        {"plan": "p07", "db": -10},
    ],
    "etalonnage": {"contraste": 1.08, "saturation": 1.04, "chaleur": 0.02, "grain": 0.85},
}

# --- CONSTRUCTION DE L'EDITPLAN VERTICAL 9:16 (13.0 s = 312 images à 24 i/s, recadré depuis 16:9) ---
VIDEO_VERT_SPEC = [
    ("vc01", "p01", 20, 64, "V1_Photo", "Étienne prend la photo sur le chantier et lance le signal"),
    ("vc02", "p02", 0, 56, "V2_Signal", "Course du signal de la tour 5G sur la fibre aérienne"),
    ("vc03", "p03", 0, 52, "V3_Serveur", "Plongée à travers la vitre du serveur local vers la Citadelle"),
    ("vc04", "p05", 0, 68, "V4_Citadelle", "M3 chiffre le devis par simulation Monte Carlo et 11 critères"),
    ("vc05", "p07", 0, 72, "V5_RetourCarton", "Retour du devis approuvé dans la main d'Étienne et carton final"),
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
        "p01": {"kind": "video", "duree_f": 158},
        "p02": {"kind": "video", "duree_f": 124},
        "p03": {"kind": "video", "duree_f": 124},
        "p05": {"kind": "video", "duree_f": 124},
        "p07": {"kind": "video", "duree_f": 124},
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
            {"src": "v17", "debut_f": 4, "entree_f": 0, "duree_f": 188, "gain_db": 0},
            {"src": "v18", "debut_f": 264, "entree_f": 0, "duree_f": 24, "gain_db": 0},
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
    "metadonnees": {"modele": "gemini-4-argon", "savoir": ["vertical-signal-run-crop"]},
}

ANNEXE_VERTICAL = {
    "incrustations": [
        {"type": "etiquette", "debut_f": 4, "duree_f": 60, "position": "haut-droite", "texte": "VISION"},
        {"type": "statut", "debut_f": 6, "duree_f": 56, "position": "bas", "texte": "Photo reçue. Mesures en cours…"},
        {"type": "trajet", "debut_f": 64, "duree_f": 56, "position": "centre", "points": [[0.50, 0.08], [0.50, 0.50], [0.50, 0.88]], "couleur": "signal"},
        {
            "type": "document",
            "debut_f": 172,
            "duree_f": 88,
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
        {"plan": "p02", "db": -9},
        {"plan": "p03", "db": -8},
        {"plan": "p05", "db": -10},
        {"plan": "p07", "db": -10},
    ],
    "recadrage_v": {
        "p01": 0.45,
        "p02": 0.50,
        "p03": 0.50,
        "p05": 0.50,
        "p07": 0.46,
    },
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
