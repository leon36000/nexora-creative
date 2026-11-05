# Palette de voix V7 (banc du 04/11 : même texte, oreille de machine Gemini 4 Argon en 2 passes ; échantillons dans
`~/nexora-creative-data/promo/v7-creative/voix-banc/`). Identifiant à mettre dans `voix[].moteur`.

Rappels : le fondateur a trouvé la voix de la V6 « cheap » et préfère le film sans narration ; une voix = un personnage ou une
narration très courte. `h3-natif` = la réplique est dite par le personnage dans le plan H3 (balise `<d>[French] …</d>`), rien
à générer. Licence : Voxtral local (poids CC BY-NC) exclu ; Voxtral par API autorisé.

| identifiant | modèle | genre | français | québécois | énergie | caractère | naturel | cheap (bas = mieux) | score |
|---|---|---|---|---|---|---|---|---|---|
| gemini38-puck | google/gemini-3.8-flash-tts Puck | homme | 10.0 | 6.5 | 7.5 | 9.0 | 9.0 | 1.0 | 8.5 |
| gemini38-fenrir | google/gemini-3.8-flash-tts Fenrir | femme | 10.0 | 1.5 | 8.5 | 7.0 | 9.0 | 2.0 | 7.6 |
| vox3-voice3146 | mistralai/voxtral-mini-tts-3-0 voice_3146 | femme | 9.5 | 9.0 | 3.5 | 5.5 | 8.0 | 2.5 | 6.58 |
| vox2603-marie-excitee | mistralai/voxtral-mini-tts-2603 fr_marie_excited | femme | 10.0 | 1.5 | 5.5 | 5.0 | 8.5 | 2.0 | 6.47 |
| vox3-voice3154 | mistralai/voxtral-mini-tts-3-0 voice_3154 | femme | 8.5 | 6.0 | 5.5 | 5.0 | 7.5 | 2.5 | 6.2 |
| mai21-marc | microsoft/mai-voice-2.1 fr-FR-Marc:MAI-Voice-2.1 | homme | 10.0 | 1.0 | 7.5 | 5.0 | 7.0 | 4.0 | 6.05 |
| fish21-clone-h3 | fish-audio/s2.1-pro  | homme | 9.0 | 0.5 | 6.5 | 6.5 | 6.5 | 4.0 | 5.72 |
| mai21-grant | microsoft/mai-voice-2.1 fr-FR-Grant:MAI-Voice-2.1 | homme | 9.5 | 1.5 | 5.0 | 6.0 | 6.0 | 4.5 | 5.33 |
| minimax28-narrateur | minimax/speech-2.8-hd French_MaleNarrator | homme | 9.0 | 7.0 | 5.0 | 4.5 | 5.0 | 5.5 | 5.0 |
| vox3-voice3141 | mistralai/voxtral-mini-tts-3-0 voice_3141 | femme | 10.0 | 1.0 | 4.0 | 3.0 | 7.0 | 4.0 | 4.95 |
| minimax28-homme | minimax/speech-2.8-hd French_Male_Speech_New | homme | 9.5 | 1.5 | 4.0 | 3.0 | 6.5 | 4.0 | 4.75 |
| vox3-voice3135 | mistralai/voxtral-mini-tts-3-0 voice_3135 | homme | 9.5 | 1.5 | 4.5 | 4.5 | 5.5 | 5.0 | 4.7 |
| fish21-direction | fish-audio/s2.1-pro  | homme | 8.0 | 3.5 | 8.0 | 5.5 | 4.0 | 7.0 | 4.65 |
| vox3-voice482 | mistralai/voxtral-mini-tts-3-0 voice_482 | homme | 8.5 | 4.0 | 5.0 | 4.5 | 5.0 | 5.5 | 4.58 |
| vox3-voice3132 | mistralai/voxtral-mini-tts-3-0 voice_3132 | femme | 9.0 | 3.0 | 3.5 | 4.0 | 6.0 | 5.0 | 4.55 |
| vox3-voice592 | mistralai/voxtral-mini-tts-3-0 voice_592 | femme | 10.0 | 1.5 | 3.5 | 3.0 | 6.0 | 5.0 | 4.45 |
| h3-natif | voix native MiniMax H3 du personnage dans le plan | selon le prompt | — | bon accent | jeu d'acteur | — | — | jugée « cheap » en narration V6 | — |
