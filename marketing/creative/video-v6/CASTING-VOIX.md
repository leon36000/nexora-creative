# Distribution des voix du film V6 (04/11/2026)

Consigne : énergique, percutante, avec du caractère, **surtout pas « smooth »** (la V5 était dirigée « calme, intime, lent »).
Recherche 23 : pas de narrateur lisse ; voix des personnages, narration ≤ 25 % de la durée, une phrase par coupe.

## Le même texte d'essai pour tous (FR et EN)
« Trois mots. Même mal écrits. Creative fait le reste. Un dragon ? Réglé. Une bataille dans l'espace ? Réglé. T'écris trois mots.
Creative fait le film. » (les essais H3 disent « L'IA écrit le reste » / « On fait le film », comme le film final).

## Candidats (fichiers : `~/nexora-creative-data/promo/v6-creative/voix/casting/` et sur pc1
`~/Bureau/Nexora-Livrables/TOUS-LES-FILMS/creative-v6/voix-casting/`)
| fichier | moteur | direction | débit (mots/s) | étendue F0 (demi-tons) | silence | WER |
|---|---|---|---|---|---|---|
| A-eleven4-alexandre-energique-{fr,en} | ElevenLabs v4, voix « Alexandre » (Québec, celle de la V5) | balises [excited][punchy][fast] | 2,65 / 2,50 | 14,1 / 15,1 | 0,11 / 0,09 | 0,04 / 0 |
| B-eleven4-liam-{fr,en} | ElevenLabs v4, « Liam » (jeune, nerveux) | idem | 2,65 / 2,59 | 16,1 / 14,9 | 0,17 / 0,11 | 0,12 / 0 |
| C-eleven4-callum-{fr,en} | ElevenLabs v4, « Callum » (rauque) | idem | 2,46 / 2,26 | 14,0 / 14,3 | 0,14 / 0,15 | 0,04 / 0 |
| D-eleven4-charlie-{fr,en} | ElevenLabs v4, « Charlie » | idem | 2,50 / 2,36 | 11,2 / 14,4 | 0,16 / 0,14 | 0,04 / 0 |
| E-drama3-direction-{fr,en} | Fish Audio Drama 3, consigne de jeu en langage naturel | « animateur de bande-annonce, accent québécois » | 1,81 / 1,82 | 11,4 / 10,9 | 0,34 / 0,21 | 0 / 0 |
| F-drama3-clone-alexandre-energique-{fr,en} | Drama 3, clone d'Alexandre + consigne énergique | idem | 2,09 / 1,84 | 12,5 / 17,9 | 0,15 / 0,15 | 0,08 / 0 |
| G-drama3-balises-{fr,en} | Drama 3, balises dans le texte | [excited, hype trailer announcer…] | 2,29 / 1,73 | 16,2 / 10,0 | 0,18 / 0,20 | 0,12 / 0 |
| H-voxtral-marie-excited-fr | Voxtral TTS 3, fr_marie_excited (voix féminine) | préréglage | 2,12 | 9,7 | 0,36 | 0,17 |
| J-qwen3tts-voicedesign-{a,b}-{fr,en} | **Qwen3-TTS 1.7B VoiceDesign, local** (pc1, CPU, Apache-2.0) | voix « dessinée » : (a) annonceur rauque, (b) animateur survolté | 2,08–2,27 / 1,97–2,21 | 9,2–18,2 | 0,21–0,32 | 0–0,12 |
| K-h3-natif-{a,b}-{fr,en} | **voix native MiniMax H3** (h3-max, 5090) : un annonceur filmé en cabine, on garde le son | (a) annonceur rauque, (b) animateur survolté ; accent québécois | 2,22 / 2,33 | 12,6–15,5 | 0,09–0,19 | 0–0,10 |
(Gemini 3.8 TTS refusé par OpenRouter en mp3 : non essayé. Mesures de machine : étendue F0 par autocorrélation, sujette aux
erreurs d'octave ; elles ne remplacent pas l'oreille.)

## Choix pour le film, motivé
- **Voix native H3 « a » (K-h3-natif-a)** pour la narration, découpée en phrases. Raisons : c'est celle que le fondateur trouvait
  « bien meilleure » ; c'est un **personnage joué** (annonceur filmé, jeu d'acteur demandé : attaques dures, sourire), pas un TTS
  de lecture ; mesures les plus « nerveuses » du banc avec ElevenLabs (débit 2,2 à 2,3 mots/s sur des phrases courtes, très peu
  de silence, WER ≈ 0) ; accent québécois demandé dans le prompt ; et c'est **notre propre moteur** (même chaîne que les plans).
  Le timbre est tenu d'un groupe de phrases à l'autre par une référence audio (`<Audio 1>` = l'essai K-a) ; narration rendue en
  6 groupes par langue (`voix_h3.py`), découpée par Whisper. Limite : chaque groupe est un rendu H3 de 5 à 7 s (≈ 2 min de GPU,
  12 à 15 min avec la file partagée) et le timbre peut encore varier légèrement d'un groupe à l'autre.
- **Les deux répliques dans l'image** (pilote « Bouclier ! Maintenant ! », duelliste « C'est tout ?! ») sont aussi en voix native
  H3, synchronisées aux lèvres, FR et EN.
- **Repli prêt** : ElevenLabs v4 Alexandre énergique (FR) et Liam (EN), phrase par phrase (`voix_narration.py eleven`), dans
  `voix/narration/eleven4-*` : un seul paramètre à changer (`V6_VOIX_FR/EN`) et le film se remonte en 3 minutes de CPU.
- À écouter en priorité par le fondateur : K-a, A, F, J-a (local), dans cet ordre.
