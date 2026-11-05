# 26 — Recette « prise de vues réelles » (live action) et direction sonore, pour le réalisateur de Creative (04/11/2026, v0.9)

État : la partie image est mesurée sur les images clés ; les plans vidéo du banc et les films V7 sont en cours de rendu (file de
la 5090 partagée). Sources : `marketing/creative/video-v7/recette/` (prompts, juge, mesures), `video-v7/BRIEF-V7.md` §4 et §6.

## 1. D'où vient l'aspect « jeu vidéo » (diagnostic sur les prompts réels de la V6, notée 5,7/10 par le fondateur)
- Vocabulaire de rendu écrit par nos réécrivains : « cinematic » ×37, « glowing » ×26, « epic » ×23, « incandescent » ×21,
  « grade / teal-and-orange » ×15, « majestic », « volumetric ». Aucune caméra, aucun objectif, aucune pellicule nommés.
- Lumière « lueur » partout (sources qui brillent d'elles-mêmes), surfaces propres, couleurs saturées, compositions centrées de
  jaquette de jeu, sujet (dragon, vaisseau) posé au milieu comme un modèle 3D, sans échelle humaine.
- Les images clés Qwen-Image héritent de ce vocabulaire : ce sont elles qui fixent le « look » du plan H3.

## 2. La recette (images clés)
1. Ouvrir par : « Production still from a live-action feature film, photographed on location on 35mm film (Kodak Vision3 500T)
   with <objectif réel> ; natural exposure, visible film grain, slight halation around bright sources, soft lens imperfections ».
2. Nommer un **décor réel** (lande écossaise, toit industriel, Montréal sous la pluie, Patagonie) et une **lumière pratique**
   (le feu, un ciel couvert, un lampadaire au sodium, le soleil dur de l'orbite).
3. Atmosphère (pluie, fumée, brume, poussière), imperfections (gouttes ou saleté sur l'objectif, flou de bougé, mise au point
   qui respire), matières vécues (boue, rouille, cuir mouillé), **échelle humaine** (figurants au premier plan).
4. Cadrage d'opérateur : téléobjectif de loin (compression, chaleur qui vibre), caméra à l'épaule qui court, hélicoptère.
5. Interdits au positif : cinematic, epic, glowing, incandescent, majestic, dramatic lighting, hyper-detailed, 8k, render, CGI,
   Unreal, concept art, teal and orange, vibrant, stunning. Négatif systématique : 3d render, cgi, video game, game cinematic,
   unreal engine, octane, digital painting, concept art, illustration, matte painting, airbrushed, smooth plastic surfaces,
   oversaturated, neon glow, bloom, hdr, teal and orange grade, toy, miniature look, symmetrical composition, text, logo.
6. Garder le sujet **grand dans le cadre** : trop loin, le spectacle disparaît (essai « flotte de dragons » devenu des oiseaux).
7. Plans H3 : « Live-action footage shot on 35mm film, <opérateur>, natural motion blur from a 180-degree shutter, slight focus
   breathing, real physics and weight, practical fire, smoke and debris, film grain » + une action simple et physique.

## 3. Mesures (juge « réel contre synthèse », Gemini 4 Argon Flex, deux ordres de présentation)
| plan (V6 → recette) | victoires V6 / recette | réalisme V6 → recette (/10) |
|---|---|---|
| dragon sur le château | 0 / 2 | 2,5 → 7,5 |
| dragon qui survole | 0 / 2 | 3,5 → 7,5 |
| bataille spatiale | 0 / 2 | 2,5 → 7,0 |
| dragon contre croiseur | 1 / 1 (incohérent) | 5,0 → 5,0 |
| flotte de dragons à l'aube | 0 / 2 | 2,5 → 8,0 (mais spectacle perdu) |
| duel aux lames sous la pluie | 0 / 2 | 3,0 → 7,0 |
Moyenne 2,9 → 7,0 ; 5 duels sur 6 gagnés dans les deux ordres. Le juge note sévèrement en absolu (images clés V7 : 3 à 7) et
relève des défauts précis (échelle de miniature, anatomie, intégration à la vitre) : il sert de filtre automatique (seuil 6,5,
une relance avec une autre graine, on garde la meilleure).

**Plans vidéo (h3-max depuis ces images clés, contre les plans V6 ; juge sur 3 images du plan, deux ordres)** :
| plan | victoires V6 / recette | réalisme V6 → recette |
|---|---|---|
| dragon sur le château | 0 / 2 | 3,0 → 7,0 |
| dragon qui survole | 0 / 2 | 3,0 → 7,5 |
| bataille spatiale | 1 / 1 (incohérent) | 5,5 → 4,0 |
| dragon contre croiseur | 0 / 2 | 4,0 → 6,0 |
| flotte de dragons | 0 / 2 | 2,5 → 7,5 |
| duel sous la pluie | 0 / 2 | 3,5 → 7,0 |
5 sur 6 gagnés dans les deux ordres, moyenne 3,6 → 6,5. Échec : l'espace en « maquette » (des cuirassés réels en orbite) ;
pour l'espace, garder la photographie réelle (soleil dur, Terre réelle) mais des vaisseaux d'un dessin original, pas des navires.

## 4. Pour `realisateur.ts`
Ajouter au réécrivain d'image et au réécrivain H3 : le préambule de §2.1 et §2.7, le choix d'un objectif et d'un opérateur selon
le plan, la liste d'interdits (au positif) et le négatif ; puis le juge « réel » sur chaque prise avec une relance.

## 5. Direction sonore (exigence du fondateur, à mesurer sur les films V7)
- Écrire la musique pour le montage : carte des temps forts horodatée → prompt musical par sections (Lyria suit des sections en
  secondes) → mesure du tempo réel → recalage des coupes sur la grille ; vrais silences avant les impacts ; motif de marque.
- Juger chaque piste **mixée sur le film** (Gemini avec la vidéo : adéquation, énergie, synchronisation) et mesurer l'alignement
  impacts-coupes (`chaine/v7.py juger-musique`). Constats V6 : Music3 plus plat (−13 à −20 dB contre −6 à −10 pour Lyria), sans
  vrai drop ni silence ; ElevenLabs Music absent d'OpenRouter ; ACE-Step et YuE non installés (poids non téléchargés).
