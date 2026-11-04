# Moteurs de musique offerts aux quatre équipes (révision du 04/11)

La musique s'écrit pour le montage : carte des temps forts, 3 à 4 candidates sur au moins 2 moteurs, conformation au montage par la
chaîne (`chaine/partition.py`), juge audio-vidéo sur le film mixé et mesures. Mesures faites ici, sur nos machines.

| `moteur` | Modèle | Où | Durées | Temps mesuré | Prompt | Licence (faits) |
|---|---|---|---|---|---|---|
| `lyria` | Google Lyria 3 Pro | OpenRouter | ≈ 60 à 155 s (une demande de 150 s a rendu 153,7 s) | 90 s | texte libre en anglais ; structure en secondes suivie à peu près ; BPM approximatif (124 demandés → 124 à 128 mesurés, parfois moitié) | conditions Google via OpenRouter |
| `music3` | MiniMax-Music3 (int8) | local, GB10 (ComfyUI) | jusqu'à 300 s, le modèle peut finir plus tôt | 215 s pour 60 s | gabarit officiel en trois blocs : « Global Metadata: … / Vocal Details: Instrumental, no vocals. / Arrangement: [Intro] … [Drop] … » | MiniMax-Music3 Community (afficher « MiniMax-Music3 ») |
| `acestep` | ACE-Step 1.5 turbo 2B | local, GB10 | 15 à 180 s, durée exacte | ≈ 45 s chargement compris (150 s en 6,8 s) | tags de style en anglais (genre, BPM, instruments, énergie) ; mode instrumental | MIT (code et poids, vérifié dans les sources) |

Constats du premier tour : les pistes Lyria tiennent un groove mais restent « en boucle » au milieu (juge audio-vidéo : « sans vrai thème
mélodique mémorable ») ; un saut d'énergie arrive rarement à la seconde demandée. D'où la conformation : la chaîne cale les attaques de
la piste sur tes impacts (décalage global, puis étirement de 0,88 à 1,12 par segment), pose de vrais silences et mixe tes bruitages.
Mesures rendues pour chaque candidate : part des impacts et des coupes à ± 2 images d'une attaque forte, plage de sonie (LRA),
écart d'énergie (p95 − p10), et le juge audio-vidéo (accord image-musique, frappe sur les coupes, dynamique, motif, énergie).
