# Brief Codex : chaîne de production commune du film V7 (`marketing/creative/video-v7/chaine/`)

Dépôt `/home/pc6/Desktop/NexoraCreative-film-v6` (branche `feat/film-v6-creative`). Écris seulement dans
`marketing/creative/video-v7/chaine/` (et ses tests). Lis d'abord : `marketing/creative/video-v7/BRIEF-V7.md` (le brief des équipes,
§7 budget, §8 format du `dossier.json`), `README-montage.md` (contrat de la liste de montage de `monter_v6.py`, copié ici),
`recette/recette_live.py` et `recette/juge_reel.py` (recette live action et juge), `voix/banc_voix_v7.py` (moteurs de voix),
`../video-v3/moteur.py` (client ComfyUI : graphes Qwen-Image et H3 ; réutilise-le par import), `../video-v6/musique_v6.py` et
`../video-v6/musique_music3_v6.py` (Lyria et Music3), `../../nexora/campagne-films/films-v3/outils/musique.py` (`grille()` : tempo,
phase, énergie). Règles : aucun commit ; ne lance **aucun** rendu GPU ni appel payant pendant ton travail (tests avec des doublures
`--a-blanc`) ; la clé OpenRouter se lit dans `~/Desktop/Deepinfra.env` (format « Openrouter: … ») et ne s'affiche jamais ; données
lourdes dans `~/nexora-creative-data/promo/v7-creative/` (lien vers un disque externe, beaucoup d'espace) ; réponds en français.

## Commandes à fournir (`python3 chaine/v7.py <commande> <equipe> …`, une équipe = `equipes/<equipe>/dossier.json`)
1. `valider` : schéma du §8 ; budgets du §7 (24 clés, 20 unités 16:9, 4 unités 9:16 natives, 8 voix, 3 musiques ; unités : 124
   images = 1, 141-243 = 2 ; grille 17k+5) ; références (`cle` existe, `plan:pXX` du montage existe, voix et musiques citées
   existent, chemins de captures existent) ; **mots interdits** de la recette au positif des clés et des plans (cinematic, epic,
   glowing, incandescent, majestic, dramatic lighting, hyper-detailed, 8k, render, cgi, unreal, concept art, teal and orange,
   vibrant, stunning) → erreur ; présence de « No text » dans chaque plan ; la liste de montage est validée par la fonction de
   validation de `monter_v6.py` après substitution par des fichiers factices. Affiche `OK` ou la liste des erreurs, et des
   avertissements (durée hors 40-70 s, plan de plus de 6 s, texte de carton de plus de 4 mots).
2. `cles` : rend les images clés sur la GB10 (ComfyUI 127.0.0.1:37188) avec le négatif anti-rendu de la recette ; chaque image
   passe au juge (`juge_reel.note`) ; sous 6,5 : **une** relance avec graine +1000, garde la meilleure ; journal
   `~/nexora-creative-data/promo/v7-creative/<equipe>/cles/journal.jsonl` (prompt, graine, note, défauts).
3. `plans` : rend les plans H3 sur la 5090 (127.0.0.1:37288, `moteur.graphe_h3` avec `ref` et l'image clé en `<Picture 1>`,
   checkpoint `10Eros_Max_h3_8stepTURBO_beta7_SingularityV2_ref2va_int8HQ.safetensors`, 8 étapes, décalage [12, 3], euler,
   1344×768 ou 768×1344). **File partagée** : jamais plus de 6 travaux de cette équipe en attente (préfixe de sortie
   `v7-<equipe>/…`, compte dans `/queue`) ; soumission asynchrone (plusieurs en vol) et reprise après coupure (ne refait pas un
   plan déjà rendu). Juge réel/synthèse sur chaque plan (3 images) ; sous 6,5 : une relance (graine +1000) si le budget de
   l'équipe le permet, sinon on garde. Journal pareil. Les quatre équipes tourneront en même temps (4 processus).
4. `voix` : génère chaque réplique (2 prises) avec le moteur nommé (identifiants de `voix/banc_voix_v7.py` CANDIDATS, plus
   `h3-natif` = la réplique est dans le plan, rien à générer) ; Whisper (venv `~/nexora-creative-data/engine/transcription-venv`),
   oreille de machine (fonction `juger` du banc) ; `<equipe>/voix/<id>.wav` = meilleure prise.
5. `musique` : génère les pistes (`lyria-pro`, `lyria-clip` par OpenRouter ; `music3` par l'API du studio sur
   http://127.0.0.1:37171 si en ligne, sinon par ComfyUI GB10) ; mesure `grille()` ; écrit `<equipe>/musique/<id>.wav` + grille.
6. `monter` : substitue `plan:pXX` → rush, `plan_v:pXX` → rush vertical, `musique:mX` → piste (avec `entree` calée : si le
   dossier donne `"calage": "auto"`, choisir l'`entree` qui aligne le plus fort saut d'énergie de la piste sur le premier temps
   fort du film), et rend avec `monter_v6.py` : 16:9 et 9:16, `--langue fr` (et `en` si demandé), master web ; `--musique mX`
   pour rendre une variante par piste ; `--brouillon` pour les essais.
7. `juger-musique` : pour chaque piste, un brouillon mixé du film (720p suffit) est envoyé à Gemini 4 Argon **avec la vidéo**
   (entrée vidéo par OpenRouter ; si refusé, 16 images + l'audio) : adéquation au film, énergie, synchronisation des temps forts,
   mémorabilité, « plat » (0-10), en JSON ; plus des mesures : tempo, plage de sonie, part des coupes à ±2 images d'un temps,
   écart moyen entre impacts de la musique (onsets forts) et coupes. Écrit `<equipe>/musique/jugement.json`.
8. `planche` : une planche par film (1 image/s, temps) et une planche des plans (3 images par plan, numéro, note du juge).
9. `telephone` : copie ≤ 28 Mo de chaque film (H.264, débit vidéo ≈ 3,8 Mb/s, AAC 128 k, `+faststart`), ffmpeg de
   `~/nexora-creative-data/engine/ffmpeg/`.
10. `archiver` : copie tous les MP4 de l'équipe (films, rushes, variantes) sur pc1 (`ssh pc1`) dans
   `~/Bureau/Nexora-Livrables/TOUS-LES-FILMS/creative-v7/<equipe>/…` et ajoute une ligne par fichier à
   `~/Bureau/Nexora-Livrables/TOUS-LES-FILMS/INVENTAIRE.csv` (même format que `../video-v6/archiver.py`, sans doublon de sha256).
11. `bilan` : temps GPU (somme des temps moteur), nombre d'unités, notes du juge, coût OpenRouter relevé dans les réponses.

## Preuve
Tests unitaires (validation, budget, substitution, calage auto, file limitée) avec doublures ; un `equipes/essai/dossier.json`
minimal (2 clés, 2 plans, 1 musique, 1 voix, montage de 10 s) qui passe `valider` et `monter --a-blanc` (médias factices).
Dernier message : commandes exactes, ce qui reste approximatif.

## Ajout (consigne du fondateur, 04/11 02 h)
Tout appel direct à Gemini 4 Argon par OpenRouter (juges image, vidéo, audio) passe **seulement par Flex** :
`"provider": {"order": ["google-ai-studio/flex"], "allow_fallbacks": false}` dans le corps de la requête.
