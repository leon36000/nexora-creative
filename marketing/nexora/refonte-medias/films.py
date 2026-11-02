"""Scripts of the redesign films: sequence of beats (H3 shot, on-screen duration, fr/en text set in code, sound design).
"\n" = line break in 9:16 (16:9 keeps one line unless "lignes16": True). Editable without re-rendering anything:
re-run montage.py. CHOIX = H3 variant kept for each shot after review (plans/<group>/<name>-<fmt>-<variant>.mp4)."""

W = {"type": "whoosh", "duree": 0.9, "db": -19, "dt": -0.35}  # whoosh on the cut

FILMS = {
  "surveillance": {
    "role": "Film de la page Surveillance IA (/solutions/surveillance-ia) : message clé, détection, alertes, rapports.",
    "musique": "surv", "impact": 3, "etiquette": {"fr": "Surveillance IA", "en": "AI Surveillance"},
    "beats": [
      {"plan": "surv/murs", "d": 4.4, "fr": "Les meilleures caméras.", "en": "The best cameras."},
      {"plan": "surv/stockage", "d": 4.0, "fr": "Un stockage immense.", "en": "Massive storage.", "sfx": [W]},
      {"plan": "surv/chaise", "d": 5.2, "fr": "Mais personne ne regarde\ndes milliers d’heures de vidéo.",
       "en": "But no one watches\nthousands of hours of video.", "lignes16": True, "sfx": [W]},
      {"plan": "surv/entrepot", "d": 4.8, "hud": {"debut": 0.4, "alerte": 99, "camera": "CAM 12", "cible": [550, 632, 608, 748],
                                        "vertical_par_recadrage": True, "recadre": 360}, "droite": True, "fr": "Nos IA, si.\nEn temps réel.",
       "en": "Our AI does.\nIn real time.", "accent": {"fr": "En temps réel.", "en": "In real time."}, "z": 0.0, "src": 0.0},
      {"plan": "surv/stationnement", "d": 4.8, "hud": {"debut": 0.2, "alerte": 2.2, "camera": "CAM 03",
       "cles": "0:793,262,838,362;1.5:803,282,842,382;2.6:809,300,860,407;3.8:800,300,854,407;5.2:806,300,860,407",
       "vertical_par_recadrage": True, "recadre": 610}, "z": 0.0, "src": 0.0,
       "fr": "Elles détectent les comportements\nsuspects, au moment où ils arrivent.",
       "en": "It spots suspicious behaviour\nas it happens.", "lignes16": True, "sfx": [W]},
      {"plan": "surv/alerte", "d": 4.4, "fr": "Alerte par texto, courriel\nou application.", "en": "Alerts by text, email\nor app.",
       "sfx": [{"type": "tick", "duree": 0.3, "db": -14, "dt": 0.9}]},
      {"plan": "surv/intervention", "d": 4.6, "fr": "Vos agents, votre centrale ou la police :\nselon vos consignes.",
       "en": "Your guards, your monitoring centre or the police:\nas you instruct.", "lignes16": True, "sfx": [W]},
      {"plan": "surv/rapport", "d": 4.6, "fondu": 0.4, "fr": "Et un rapport\npour chaque événement.", "en": "And a report\nfor every event."},
    ],
  },
  "reception": {
    "role": "Film de la page Réception virtuelle (/solutions/reception-virtuelle) : appels, courriels, textos, 24/7, fr et en.",
    "musique": "recep", "impact": None, "etiquette": {"fr": "Réception virtuelle", "en": "Virtual reception"},
    "beats": [
      {"plan": "recep/telephone", "d": 4.4, "fr": "Il est tard.\nLe téléphone sonne.", "en": "It’s late.\nThe phone rings."},
      {"plan": "recep/onde", "d": 4.2, "fondu": 0.5, "fr": "Quelqu’un répond. Toujours.", "en": "Someone answers. Every time."},
      {"plan": "recep/cliente", "d": 4.4, "fr": "Rendez-vous pris.\nConfirmation envoyée.", "en": "Appointment booked.\nConfirmation sent.", "sfx": [W]},
      {"plan": "recep/artisan", "d": 4.4, "fr": "Les mains pleines ?\nVotre réception s’en occupe.", "en": "Hands full?\nYour reception has it covered.", "sfx": [W]},
      {"plan": "recep/texto", "d": 3.8, "fr": "Appels, courriels, textos.", "en": "Calls, emails, texts.",
       "sfx": [{"type": "tick", "duree": 0.3, "db": -16, "dt": 0.7}]},
      {"plan": "recep/transfert", "d": 4.4, "fr": "Qualifié, puis transféré\nà la bonne personne.", "en": "Qualified, then transferred\nto the right person.", "sfx": [W]},
      {"plan": "recep/matin", "d": 4.4, "fr": "Chaque échange, résumé.", "en": "Every conversation, summarized.", "sfx": [W]},
      {"plan": "recep/aube", "d": 4.4, "fondu": 0.5, "fr": "24 h sur 24.\nEn français et en anglais.", "en": "24/7.\nIn French and English.",
       "accent": {"fr": "24 h sur 24.", "en": "24/7."}},
    ],
  },
  "infrastructure": {
    "role": "Film de la page Infrastructure IA (/infrastructure) : DGX Spark, DGX Station, baies de serveurs ; chez vous ou hébergée.",
    "musique": "infra", "impact": 6, "impact_entre": (22.0, 30.0), "etiquette": {"fr": "Infrastructure IA", "en": "AI Infrastructure"},
    "beats": [
      {"plan": "infra/mousse", "d": 4.6, "fr": "La puissance de l’IA.", "en": "The power of AI."},
      {"plan": "infra/spark", "d": 4.6, "fr": "Compacte, sur votre bureau.", "en": "Compact, on your desk."},
      {"plan": "infra/station", "d": 4.4, "fr": "Puissante, à votre poste.", "en": "Powerful, at your workstation.", "sfx": [W]},
      {"plan": "infra/racks", "d": 4.4, "fr": "À grande échelle,\nen baies de serveurs.", "en": "At scale,\nin server racks.", "sfx": [W]},
      {"plan": "infra/installation", "d": 4.4, "fr": "Installée chez vous, clé en main.", "en": "Installed on your premises, turnkey.", "sfx": [W]},
      {"plan": "infra/fibres", "d": 3.8, "fr": "Modèles, applications,\nsécurité, supervision.", "en": "Models, applications,\nsecurity, monitoring.", "sfx": [W]},
      {"plan": "infra/batiment", "d": 4.4, "fondu": 0.5, "fr": "Ou hébergée chez nous, au Québec.", "en": "Or hosted with us, in Québec."},
      {"plan": "infra/salle", "d": 4.6, "fondu": 0.4, "fr": "Votre IA.\nSous votre contrôle.", "en": "Your AI.\nUnder your control.",
       "accent": {"fr": "Sous votre contrôle.", "en": "Under your control."}, "sfx": [{"type": "boom", "duree": 1.8, "db": -10, "dt": 0.0}]},
    ],
  },
  # Creative film: handed over to another agent on 02/11 (founder's instruction) — kept here as a draft, not rendered.
  "creative": {
    "role": "Film de la page Creative (/creative) : une phrase devient une image, une vidéo, une musique.",
    "musique": "crea", "impact": 5, "impact_entre": (14.0, 26.0), "etiquette": {"fr": "Creative", "en": "Creative"},
    "beats": [
      {"plan": "crea/studio", "d": 3.6, "fr": "Une phrase.", "en": "One sentence.", "taille": 0.09},
      {"plan": "crea/phare", "d": 4.2, "style": "invite", "fr": "> Un phare dans la tempête, la nuit.", "en": "> A lighthouse in a storm, at night.", "sfx": [W]},
      {"plan": "crea/baleine", "d": 4.2, "style": "invite", "fr": "> Une baleine au-dessus de la ville endormie.", "en": "> A whale above the sleeping city.", "sfx": [W]},
      {"plan": "crea/renard", "d": 4.0, "style": "invite", "fr": "> Un renard arctique à l’aube.", "en": "> An arctic fox at dawn.", "sfx": [W]},
      {"plan": "crea/cafe", "d": 3.8, "style": "invite", "fr": "> Café, gouttes au ralenti.", "en": "> Coffee, droplets in slow motion.", "sfx": [W]},
      {"plan": "crea/danse", "d": 4.6, "fr": "Un film.", "en": "A film.", "taille": 0.09},
      {"plan": "crea/phare", "d": 3.0, "src": 2.0, "fr": "Image. Vidéo. Musique.", "en": "Image. Video. Music.", "sfx": [W]},
      {"plan": "crea/baleine", "d": 3.6, "src": 1.5, "fondu": 0.4, "fr": "L’IA fait le gros du travail.", "en": "AI does the heavy lifting."},
      {"plan": "crea/studio", "d": 3.6, "src": 1.3, "fondu": 0.4, "fr": "Mode facile. Mode pro.", "en": "Easy mode. Pro mode."},
    ],
  },
  "workstudio": {
    "role": "Film de la page WorkStudio (agents et flux de travail).",
    "musique": "work", "impact": None, "etiquette": {"fr": "WorkStudio", "en": "WorkStudio"},
    "beats": [
      {"plan": "work/graphe", "d": 5.0, "fr": "Des agents\nqui travaillent pour vous.", "en": "Agents\nthat work for you."},
      {"plan": "work/documents", "d": 4.8, "fr": "Ils lisent, trient, rédigent.", "en": "They read, sort and draft.", "sfx": [W]},
      {"plan": "work/flux", "d": 4.8, "fr": "Des flux de travail\nautomatisés, de bout en bout.", "en": "Automated workflows,\nend to end.", "sfx": [W]},
      {"plan": "work/nuit", "d": 4.8, "fondu": 0.5, "fr": "Même quand le bureau est fermé.", "en": "Even when the office is closed."},
      {"plan": "work/equipe", "d": 4.8, "fondu": 0.4, "fr": "Vous gardez la décision.", "en": "You keep the final say.",
       "accent": {"fr": "la décision.", "en": "the final say."}},
      {"plan": "work/graphe", "d": 3.6, "src": 1.4, "fondu": 0.5, "fr": "Un seul espace pour tout orchestrer.", "en": "One place to orchestrate it all."},
    ],
  },
  "code": {
    "role": "Film de la page Code (agent de code hébergé).",
    "musique": "code", "impact": None, "etiquette": {"fr": "Code", "en": "Code"},
    "beats": [
      {"plan": "code/nuit", "d": 4.8, "fr": "Un agent de code,\nà vos côtés.", "en": "A coding agent,\nright beside you."},
      {"plan": "code/lignes", "d": 4.4, "fr": "Il lit votre code. Il écrit. Il teste.", "en": "It reads your code. Writes. Tests.", "sfx": [W]},
      {"plan": "code/clavier", "d": 4.0, "fr": "Vous révisez. Vous décidez.", "en": "You review. You decide.", "sfx": [W]},
      {"plan": "code/architecture", "d": 4.6, "fr": "De l’idée au logiciel.", "en": "From idea to software.", "sfx": [W]},
      {"plan": "code/serveur", "d": 4.4, "fondu": 0.5, "fr": "Hébergé. Sous votre contrôle.", "en": "Hosted. Under your control.",
       "accent": {"fr": "Sous votre contrôle.", "en": "Under your control."}},
      {"plan": "code/equipe", "d": 4.6, "fondu": 0.4, "fr": "Votre équipe, épaulée.", "en": "Your team, backed up."},
    ],
  },
}

# Variant kept per shot after review (default v1); key "<group>/<name>" or "<group>/<name>-<fmt>"; music "musique-<film>".
CHOIX = {
  "recep/artisan-16x9": "v2",
  "surv/alerte-16x9": "v3",  # v1, v2: insignia with letters / police-like crest on the monitor → phone shot with no character
  "musique-surveillance": "surv-v2.flac",  # silent 12 s then a +19 dB impact at 12.5 s: the "Our AI does" cut
  "musique-reception": "recep-v1.flac",     # natural ending at 39 s
  "musique-infrastructure": "infra-v1.flac",  # drop at 26 s: the "hosted with us" cut
  "musique-workstudio": "work-v2.flac",  # gentle build, steps up at 21 s
  "musique-code": "code-v1.flac",  # hypnotic, peak between 24 and 36 s
}
