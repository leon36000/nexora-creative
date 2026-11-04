# Film V7 de Creative : brief commun des quatre équipes (04/11/2026)

Seul brief, identique au mot près pour les quatre équipes : DeepSeek V4.1 Flash 1017 (effort max), Muse Spark 1.3 Contributor
(effort max), Gemini 4 Argon (effort élevé), Opus 5.5 (qui écrit sa version **à l'aveugle**, avant de lire les autres, puis
produit les quatre). Chaque équipe joue une agence complète et rend un dossier ; **la même chaîne** tourne et monte les quatre
films, avec le même budget. Le producteur ne réécrit pas la création des autres : il ne corrige que le technique et le consigne
dans `equipes/<equipe>/CORRECTIONS.md`. Les quatre films doivent être **réellement différents** (concept, plans, montage).

## 1. Le produit
Nexora Creative : studio IA dans le navigateur (image, vidéo avec son natif MiniMax H3, musique, voix, 3D « Relief »,
détourage vidéo, Mode Studio = montage jusqu'au long métrage, mode Marketing). Mission : rendre tout le potentiel de l'IA
accessible au commun des mortels : le client écrit quelques mots à l'arrache, le réalisateur de Creative (LLM) les réécrit en
plan de réalisateur, et le moteur génère une vidéo époustouflante.

## 2. Ce que veut le fondateur, et ce qu'il a jugé
- « Pour montrer les capacités de Nexora Creative, elles se doivent d'être spectaculaires. […] Fais sortir des dragons, des
  explosions, des batailles spatiales, des combats au sabre laser (exemples), montre que les capacités sont infinies, montre des
  effets spéciaux. » Porte : **8/10** ; il vise 9.
- **V6 « Trois mots. » : 5,7/10.** « Certaines séquences font trop jeux vidéo, on dirait vraiment un jeu plutôt que du live
  action. » **Sa préférée : la version SANS narration.** « La voix fait cheap. » Sur la musique : « les musiques générées ne
  fittent pas avec la vidéo, elles ne vont juste pas ensemble, et de plus c'est plat ».
- V4 (goutte d'or, 6,5/10, le meilleur souvenir) : une minute sans parole, images de luxe photoréalistes, une histoire produit
  lisible. V3 (bataille spatiale, 3/10) : jeu vidéo, statique, cheap. V5 : banal, lent.
- Donc pour V7 : **base sans narration** ; s'il y a une voix, ce sont des **personnages** dans l'image ou une narration **très
  courte** (≤ 3 phrases). **Prise de vues réelles** partout : plus aucun look de jeu vidéo.

## 3. Grammaire (recherche 23, 102 promos ; extraits à appliquer)
Plan le plus fort avant 1 s ; un plan toutes les 1 à 2,5 s (rafales 0,7-1,5 s, respirations 3-6 s pour une preuve) ; escalade en
3 marches ; chaque capacité prouvée par une image (avant/après, ingrédient visible, prompt tapé puis effet) ; couper la musique
0,5-1,5 s pour laisser entendre le son natif ; voix des personnages, pas de narrateur lisse ; textes ≤ 4 mots, gros, une couleur
d'accent ; un mur de résultats ; fin courte (carton 1,5-3,5 s) + scène bonus ; 9:16 natif ou recadré par plan.
Références du fondateur : Kling 4.0 (typographie géante, une capacité = un mot + une preuve) et Higgsfield × Opus 5.5 (un héros,
l'IA fabrique autour de lui, messages d'état courts, humour).

## 4. Recette « prise de vues réelles » (obligatoire ; mesurée : `recette/MESURES.md`)
D'où venait l'aspect jeu en V6 : vocabulaire de rendu (« cinematic » ×37, « glowing » ×26, « epic » ×23, « incandescent » ×21,
« teal-and-orange grade »), aucune caméra ni pellicule nommée, lumière « lueur » partout, surfaces propres, compositions de
jaquette de jeu, vaisseaux et dragons au centre comme des modèles 3D. Sur 6 plans V6, la recette ci-dessous gagne 5 duels sur 6
au juge « réel contre synthèse » dans les deux ordres (réalisme moyen 2,9 → 7,0 / 10).
**Images clés (Qwen-Image-2.1)** : commencer par « Production still from a live-action feature film, photographed on location on
35mm film (Kodak Vision3 500T) with a <objectif réel nommé> » ; décor réel nommé (lande écossaise, toit industriel, Patagonie) ;
lumière **pratique** (le feu, un ciel couvert, un lampadaire au sodium, le soleil dur de l'orbite) ; atmosphère (pluie, fumée,
brume, poussière) ; imperfections (grain, halation, gouttes ou saleté sur l'objectif, flou de bougé) ; matières vécues (boue,
rouille, cuir mouillé, peau réelle) ; **échelle humaine** (des figurants au premier plan) ; cadrage d'opérateur (téléobjectif de
loin, caméra à l'épaule, hélicoptère), jamais une composition centrée de jaquette. Mots **interdits** au positif : cinematic,
epic, glowing, incandescent, majestic, dramatic lighting, hyper-detailed, 8k, render, CGI, Unreal, concept art, teal and orange,
vibrant, stunning. La chaîne ajoute toujours le négatif anti-rendu (3d render, cgi, video game, unreal engine, concept art,
plastic, bloom, hdr, text, logo…). Gardez le sujet **grand dans le cadre** : trop loin, on perd le spectacle (essai r05 : des
dragons devenus oiseaux).
**Plans (H3)** : « Live-action footage shot on 35mm film, <opérateur : caméra à l'épaule qui court, téléobjectif sur pied,
hélicoptère…>, natural motion blur from a 180-degree shutter, slight focus breathing, real physics and weight, practical fire,
smoke and debris, film grain. » puis l'action, simple et physique. Une action par plan.
**Juge automatique** : chaque image clé et chaque plan passe au juge « réel contre synthèse » (Gemini 4 Argon) ; sous 6,5/10, la
chaîne relance **une fois** avec une autre graine (compté dans le budget), puis garde la meilleure.
**Finition** : grain pellicule et étalonnage du moteur de montage (`etalonnage` : neutre, nuit_feu, espace, orage, aube).

## 5. Outils et limites mesurées
- **Images** : Qwen-Image-2.1 sur la GB10, 1664×928 (16:9) ou 928×1664 (9:16), ≈ 40 s. Pas de texte dans les images.
- **Vidéo** : MiniMax H3 `h3-max` (10Eros-Max × Singularity, 8 étapes) sur la RTX 5090, **partagée avec les quatre films OPSYS**
  (attente réelle 10 à 25 min par rendu) ; 1344×768 ou 768×1344 ; 124 images = 5,2 s (141, 158, 175 : 5,9 / 6,6 / 7,3 s) ;
  l'image clé est la première image de référence (« <Picture 1> fully referenced at 0.00 s »). Son natif (bruitages,
  répliques : balise `<d>[French] …</d>`, une personne qui parle par plan, ≤ 6 mots criés marchent bien). Faiblesses : texte et
  logos spontanés (toujours « No text, no logos »), mains et visages lointains, franchises imitées (pas de sabres bleu et rouge,
  pas de capuches de moines-chevaliers, pas de vaisseaux de franchise).
- **Captures réelles de Creative** (déjà faites, utilisables par toutes) : `captures/` : saisie + « Booster ma phrase » (réécriture
  réelle) pour 8 phrases, détourage réel (brut, masque, composite), Relief (fil de fer, argile, texturé), Mode Studio, Marketing.
  Chaque équipe peut aussi demander 2 nouvelles captures de saisie/boost (phrase de son choix).
- **Voix** (`voix/PALETTE.md`, banc mesuré à l'oreille de machine) : Gemini 3.8 TTS Puck / Fenrir, Voxtral TTS 3 (voix 3146 au
  meilleur accent québécois, Marie), MAI-Voice-2.1 Marc, Fish S2.1 Pro, MiniMax Speech 2.8 HD, et la voix native H3 des personnages.
- **Musique** : Lyria 3 Pro (≈ 60 s, suit une structure écrite en secondes, tempo jamais exact : la chaîne le mesure), Lyria 3
  Clip (30 s), MiniMax-Music3 (local, plus plat). **Au moins 3 pistes par équipe.**
- **Montage** : `monter_v6.py` (contrat `README-montage.md`) : plans, saisies, boost explosif, titres cinétiques, chapitres,
  avant/après, mosaïque, carton, bruitages (impact, boom, whoosh, riser, sub, clavier…), trous musicaux, ducking. Marque et textes
  à l'écran : `marque-v7.json` (le nom et le logo vont changer : un seul carton remplaçable).

## 6. Direction sonore (exigence du fondateur)
La musique s'écrit **pour le montage** : d'abord une **carte des temps forts** (impacts, coupes, silences, montée, climax, fin,
en secondes), puis un prompt musical **par sections** qui frappe sur ces temps (Lyria suit des sections horodatées). Pas de nappe
plate : contrastes forts, montée, pic, **vrai silence avant l'impact**, un **motif mémorable** (signature de marque). Style libre
(orchestral hybride, percussions et cuivres, électronique cinématique, autre) mais il doit **servir les images**. La chaîne
mesure le tempo réel et recale les coupes sur la grille ; elle juge chaque piste **mixée sur le film** (Gemini avec la vidéo :
adéquation, énergie, synchronisation) et mesure l'alignement impacts-coupes.

## 7. Budget identique par équipe
| poste | budget |
|---|---|
| images clés Qwen | 24 (+ 1 relance automatique par image sous le seuil du juge) |
| plans H3 16:9 | 20 unités (124 images = 1 ; 141 à 243 = 2) |
| plans H3 9:16 natifs | 4 unités (le reste du 9:16 est recadré par plan) |
| reprises après révision | 6 unités |
| voix | ≤ 8 répliques, 2 prises chacune |
| musique | 3 pistes (Lyria Pro, Clip ou Music3) + 1 après révision |
| durée du film | 40 à 70 s, 16:9 et 9:16, français (cartons aussi en anglais) |

## 8. Ce que chaque équipe rend dans `equipes/<equipe>/`
`DOSSIER.md` : concept (une phrase, pourquoi il bat la V6), scénario seconde par seconde, liste de plans, carte des temps forts,
direction sonore, direction des voix, plan de montage, version 9:16, auto-évaluation sévère.
`dossier.json` (lu par la chaîne ; contrôle : `python3 chaine/valider.py equipes/<equipe>/dossier.json` doit dire OK) :
```json
{"equipe": "…", "titre": "…",
 "cles": [{"id": "k01", "format": "16:9", "graine": 101, "prompt": "Production still from a live-action feature film, …"}],
 "plans": [{"id": "p01", "cle": "k01", "format": "16:9", "images": 124, "graine": 201,
            "prompt": "For the target video, at 0.00 seconds into the target video, <Picture 1> (from [Shot 1]) is fully referenced.\n\nintegrated_multimodal_description: [Shot 1] Live-action footage shot on 35mm film, … No text, no logos.\n\noverall_soundscape: …\n\nnon_diegetic_music: N/A"}],
 "voix": [{"id": "v01", "moteur": "gemini38-puck", "texte": "…", "direction": "…"}],
 "temps_forts": [{"t": 0.0, "evenement": "…"}],
 "musiques": [{"id": "m1", "moteur": "lyria-pro", "prompt": "<prompt par sections horodatées>"}],
 "montage": {"<liste de montage du README-montage.md>": "…, avec \"fichier\": \"plan:p01\" (ou \"plan_v:p01\" pour le natif 9:16), les captures par leur chemin dans captures/, \"musique\": {\"fichier\": \"musique:m1\", …}, \"voix\": [{\"id\": \"v01\", \"t\": 3.2}]"}}
```

## 9. Ronde de révision (une seule)
Chaque équipe reçoit la planche de ses plans, les notes du juge réel/synthèse, ses voix (transcription, oreille de machine), ses
3 musiques (tempo, dynamique, avis du juge audio-vidéo) et un premier montage ; elle choisit ses reprises (≤ 6 unités), sa voix,
sa musique (et peut en demander une 4e), et rend un `dossier.json` révisé.

## 10. Jugement
Le producteur note sévèrement (crédibilité live action, spectacle, clarté du produit, musique et son, rythme, voix) ; le fondateur
choisit.

## Précision technique (chaîne, 04/11)
Un plan 9:16 natif a son propre identifiant (ex. `p03v`, `format: "9:16"`) ; le montage le cite par `"fichier_vertical": "plan_v:p03v"`.
Validation : `python3 -B chaine/v7.py valider <equipe>` (depuis `marketing/creative/video-v7/`).
