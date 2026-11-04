# 25 — Le réalisateur (« le LLM qui booste le tout ») et les effets en images de synthèse (Relief + Blender), 04/11/2026

Branche `feat/llm-booste`. Code : `app/server/nexora/realisateur.ts`, `reecritureH3.ts`, `bench/` (banc, juges, planches), `vfx/scene_blender.py`. Données brutes : `app/server/nexora/bench/resultats/reecriture-2026-11-04/`.

## 1. Ce qui existait

- `/api/nexora/creer` → `reecrireH3` : le LLM du poste (en production `z-ai/glm-5.3` par OpenRouter, raisonnement obligatoire) reçoit **le guide officiel H3 entier** (≈ 3 700 jetons) et rend un prompt ; un validateur vérifie la forme, deux réparations, puis un repli. Même chemin pour les plans des films (`filmMoteur.ts`), le projet long et les références.
- « Booster ma phrase » : réécriture française de l'idée (rôle `boost`), sans lien avec le prompt H3.
- Les paliers Éco / Équilibré / Expert (`niveaux.ts`) ne servaient pas à la rédaction ; ses jetons n'étaient ni mesurés ni facturés.

## 2. Ce qui est construit

**Le réalisateur** (`realisateur.ts`), un appel, deux réparations au plus :

1. **Comprendre** : orthographe, québécois (char, pis, tuque, tire…), famille de la demande (pub, produit, film, vfx, cours, social, clip), tout ce que le client a nommé est gardé ; marques et personnages protégés remplacés par un équivalent générique (sabre laser → lame d'énergie ; « comme Starbucks » → café haut de gamme). **Aucune question** : les choix faits par défaut sont listés (`hypotheses`).
2. **Réaliser** : chaque plan est **un paragraphe de prose de réalisateur** (cadrage et objectif, action découpée dans le temps, un mouvement de caméra du vocabulaire H3, lumière motivée, matières, sons synchronisés), découpage multi-plans réglé par la durée (5 s : 1 plan ; 10 s : 2-3 ; 15 s : 3-4 ; ≥ 2,5 s par plan), règles propres à chaque famille (à la TIDE / SCMAPR : routage puis règles du scénario), moteur visé (FastH3 832×480 : compositions lisibles ; cinéma : détail).
3. **Compiler (le code, pas le LLM)** : dialecte H3 T2VA / I2VA (ligne d'instruction, champs, horodatages), personnages `[P1]` décrits **une seule fois en entier** puis toujours par le même groupe nominal (cohérence), répliques `[R1]` posées **mot pour mot** avec l'identifiant de locuteur du guide, dialecte image (plan clé Qwen) depuis la même fiche. Vérifications : durées, marques, texte à l'écran non demandé, français resté dans les champs, longueur.
4. **Montrer** : `compris` (ce que l'IA a compris, en français), `hypotheses`, `variantes` (trois autres directions), storyboard (cadrage et début de chaque plan) ; affichés dans Créer (panneau « Ce que l'IA a compris », variantes en un clic, prompt H3 visible sur demande, crédits de l'écriture).

**Facturation** : rôle `redaction` au palier **Expert** par défaut (`paliers.ts`), secours Équilibré ; dans `/creer` l'écriture passe par `executerSousReservation` (devis `realisation`, réservation, règlement, grand livre) ; ailleurs (films, projet long, références) chaque jeton va au grand livre. `NEXORA_REALISATEUR=off` rétablit l'ancien réécrivain, qui reste aussi le repli automatique.

## 3. Banc texte : 32 demandes à l'arrache, deux juges à l'aveugle

Demandes : `bench/demandesReecriture.ts` (6 pubs, 5 films, 10 effets spéciaux dont dragons, explosions, bataille spatiale, duels de sabres d'énergie, 4 produits, 3 cours, 3 réseaux sociaux, 1 clip ; fautes et québécois ; 3 répliques à dire mot pour mot ; une demande de texte à l'écran). Chaque demande garde une liste de ce qu'elle exige (jamais montrée aux LLM).

### 3.1 Coût, fiabilité, délai (moyennes par demande)

| Système | Valide au 1er coup | Jetons entrée / sortie | USD | Crédits exacts | Délai médian |
|---|---|---|---|---|---|
| Actuel, GLM-5.3 (production) | 30/32 | 4 336 / 2 583 | 0,01033 | 1,59 | 17,5 s |
| Actuel, Éco (DeepSeek V4.1 Flash) | 32/32 | 3 926 / 386 | 0,00016 | 0,02 | 7,3 s |
| Réalisateur v1 (champs), Éco | 23/32 | 2 733 / 1 027 | 0,00033 | 0,05 | 25,3 s |
| Réalisateur v1, Équilibré (Muse Spark 1.3) | 32/32 | 1 880 / 825 | 0,00029 | 0,05 | 10,5 s |
| Réalisateur v1, Expert (Gemini 4 Argon Flex) | 32/32 | 1 993 / 740 | 0,00569 | 0,88 | 15,0 s |
| **Réalisateur v2 (prose), Expert** | **32/32** | **2 140 / 672** | **0,00550** | **0,85** | **14,3 s** |
| Réalisateur v2, Équilibré | 32/32 | 2 026 / 885 | 0,00032 | 0,05 | 10,8 s |
| Réalisateur v2, Éco | 13/32 | 3 755 / 1 111 | 0,00036 | 0,06 | 16,7 s |

Aucun repli sur 256 réécritures. Le crédit facturé est arrondi au supérieur avec un minimum de 1 : **Éco, Équilibré et Expert coûtent tous 1 crédit au client** ; l'ancien chemin GLM en coûtait 2. Le réalisateur Expert est donc **moins cher que la production actuelle** (−47 % en dollars) et plus rapide.

### 3.2 Juge 1 : Gemini 4 Argon, raisonnement élevé, liste de 5 prompts mélangés, deux ordres

Échelle sévère (« les évaluations passées étaient de 1 à 3 points trop généreuses »). Note globale moyenne (IC 95 % par rééchantillonnage des demandes) :

| Ronde | Actuel GLM | Réal. v1 Expert | Réal. v2 Expert | v2 Équilibré | v2 Éco |
|---|---|---|---|---|---|
| ronde 1 (v1) | 6,11 [5,67 ; 6,58] | 7,34 [6,91 ; 7,73] | — | (v1 : 5,67) | (v1 : 5,47) |
| ronde 2 (v2) | 5,36 [5,00 ; 5,75] | 6,66 [6,33 ; 7,00] | **8,03 [7,72 ; 8,31]** | 5,67 | 5,84 |

Écart apparié v2 Expert − actuel : **+2,67 [+2,14 ; +3,19]**, 28 demandes gagnées, 2 perdues. Les modèles bon marché ne battent pas significativement l'actuel (+0,3 et +0,5, IC qui touchent 0).

La ronde 1 a servi de diagnostic : le juge reprochait au v1 un **style télégraphique** (listes de mots-clés recollées), des contradictions (« static shot » qui bouge, macro qui cadre deux personnes), des plans de 3 s surchargés, un accent québécois ajouté sans demande (mon propre exemple dans les consignes), le look anamorphique en 9:16, l'absence de musique dans une pub, des incohérences de saison (lucioles dans la neige) ou d'ordre (le cuisinier mange avant de servir), « canister » pour canette. Le v2 corrige chacun de ces points (prose, vérification silencieuse des contradictions, règles de durée, musique, traduction exacte).

### 3.3 Juge 2 : GPT-6.1 Sol (Codex, effort élevé), par paires, ordre tiré au hasard

Pour écarter la **préférence de Gemini pour un texte écrit par Gemini** : réalisateur v2 Expert contre l'actuel, 32 paires.

**Réalisateur 23 victoires, actuel 9** ; notes moyennes **7,09 contre 5,88 (+1,2)**. C'est l'écart que je retiens : celui d'Argon (+2,7) est probablement gonflé par l'auto-préférence. Défauts que Sol trouve encore au réalisateur : quelques plans trop chargés (cockpit, chat en skate), une découverte physiquement maladroite (film noir), un ajout de destruction non demandé (robot), une explication biologique moins juste (cellule).

## 4. Banc vidéo : le meilleur prompt donne-t-il la meilleure vidéo ?

La littérature (Prompt-A-Video, recherche/24 §3) prévient qu'un prompt « plus beau » peut tuer le mouvement : la décision se prend sur la vidéo. **10 paires** (5 effets spéciaux dont sabres, explosion, dragon, bataille spatiale ; une pub ; deux produits ; un film avec réplique ; un réseau social ; un cours), h3-fast sur la RTX 5090, même graine (777), même format et durée que la demande ; A = prompt de la production actuelle (GLM-5.3), B = réalisateur v2 Expert. Rendus : 47 s de moteur en moyenne (≈ 13 min d'attente dans la file partagée avec deux autres agents).

Juge visuel à l'aveugle (Argon élevé, six images de chaque vidéo, rangées X/Y tirées au hasard puis inversées, 20 jugements, 0,21 $ ; `juge-videos-paires.jsonl`) :

| Critère | A actuel | B réalisateur |
|---|---|---|
| fidélité | 6,00 | 6,55 |
| image | 4,90 | 5,75 |
| **mouvement** | 4,70 | **5,90** |
| impact | 4,70 | 5,95 |
| **global** | **4,75** | **5,90** |

**B gagne 17 jugements sur 20** ; dans 7 paires il gagne dans les deux ordres (sabres, explosion, dragon, poutine, parfum, chat en skate, volcan), 3 paires sont partagées (bataille spatiale, montre, retrouvailles). Le mouvement monte (+1,2) au lieu de baisser : la règle « une action par plan, un mouvement de caméra » tient.

Ce que je vois moi-même sur les planches (`marketing/creative/captures-v3/llm-booste-paire-*.jpg`) : le dragon demandé **noir** est rouge chez A, noir chez B ; la poutine de B donne faim (sauce, fromage qui file, client qui mange) quand A montre surtout la préparation ; les retrouvailles se valent (les deux disent la réplique, vérifiée par transcription faster-whisper : « T'as pas changé, mon vieux »). Défauts restants chez B : des lames d'énergie qui se confondent dans le duel, des visages en gros plan parfois cireux (FastH3 832×480), des plans de 3 s encore chargés.

**Note honnête de la vidéo** : 5,9/10 avec le réalisateur contre 4,75 avant, au juge sévère, sur FastH3 en 832×480. C'est un gain net, pas encore du triple A : la résolution et le moteur rapide plafonnent l'image ; le moteur cinéma (h3-max) et une seconde prise jugée sont les leviers suivants.

**Le son n'a été écouté par aucun humain** ; seule la réplique a été vérifiée par transcription.

## 4 bis. Coût par demande (ce que paie le client)

| | Avant (GLM-5.3) | Après (réalisateur Expert) |
|---|---|---|
| USD fournisseur | 0,0103 | **0,0055** |
| Crédits facturés (×1,10 × 1,4025 × 100, arrondi, minimum 1) | 2 | **1** |
| Délai médian de l'écriture | 17,5 s | **14,3 s** |
| Note du prompt (Sol / Argon) | 5,9 / 5,4 | **7,1 / 8,0** |
| Note de la vidéo (Argon, images) | 4,75 | **5,90** |

Rapport qualité/prix : le palier Éco (0,0004 $) n'apporte que +0,3 à +0,5 au texte, non significatif, et coûterait le même crédit au client ; Expert est le bon défaut. Si un jour le prix du crédit descend sous le centième, Équilibré (Muse Spark, 10,8 s, 0,0003 $, 32/32 valides) est le repli naturel.

## 5. Effets en images de synthèse : Relief + Blender

### 5.1 Machine

**Blender n'a pas de version Linux ARM64 officielle** (5.2.3 LTS : `linux-x64` seulement ; `bpy` sur PyPI : pas de roue `linux_aarch64` ; Ubuntu arm64 propose 4.0.2, ancien et sans CUDA) et le disque de pc6 est à 99 %. Choix : **pc1**, Blender 5.2.3 LTS officiel (somme SHA-256 vérifiée, 1,2 Go) dans `/run/media/pc1/Infrastructure/NexoraStudioWork/blender/`, rendu EEVEE sans interface sur la 5090 (≈ 0,4 à 0,8 s par image en 832×480, 32 à 48 échantillons ; ≈ 0,35 s par image de passe de données ; VRAM négligeable à côté de H3).

### 5.2 Le prototype

`app/server/nexora/vfx/scene_blender.py` (bpy, `blender -b -P … -- spec.json`) : importe un GLB de Relief, le normalise (centre, taille), anime l'objet et une caméra (images clés, cible suivie, secousse, flou de mouvement), éclaire (soleil + contre-jour + ambiance réglés sur la plaque) et rend **couleur RGBA, profondeur 16 bits, normales (espace caméra), masque** par substitution de matériau (aucune dépendance au compositeur, dont l'API change entre versions ; courbes lues dans les « channelbags » de Blender 5). Planche des passes : `marketing/creative/captures-v3/vfx-blender-04-passes.jpg`.

Actifs : deux modèles Relief faits pour l'essai (image Qwen-Image-2.1 puis TRELLIS.2 qualité sur la GB10, 174 s et ≈ 170 s) : un chasseur spatial et une chaussure de course blanche. Plaque d'espace : Qwen-Image-2.1.

### 5.3 Trois façons de faire le même plan, même budget (h3-fast, 5 s, 832×480, graine 4242)

- **A, H3 seul** : prompt du réalisateur (T2VA), l'objet décrit en mots.
- **B, plan clé 3D** : Blender pose le modèle Relief sur la plaque, une image ; H3 l'anime en I2VA.
- **C, calque 3D** : Blender rend les 121 images de l'objet ; elles sont posées sur une plaque vidéo H3 (I2VA de la plaque vide, son gardé) ; pour la chaussure, rendu Blender seul (tournette).

Planches : `vfx-blender-01-vaisseau-approche.jpg`, `-02-vaisseau-passage.jpg`, `-03-soulier.jpg`. Juge visuel à l'aveugle (Argon élevé, deux ordres, `juge-vfx.jsonl`, 0,13 $) et mon propre visionnage :

| Plan | A H3 seul | B plan clé 3D | C calque 3D | Ce que je vois |
|---|---|---|---|---|
| Vaisseau qui fonce vers la caméra | **6,5** | 4,5 | (raté) | A est spectaculaire (nébuleuse, reflets, passage au-dessus) ; B ajoute un reflet d'objectif puis le vaisseau devient une coque géante qui ne ressemble plus au modèle ; C est raté : la plaque « vide » contient elle-même des vaisseaux inventés par H3 (le son décrit un passage, H3 le montre) |
| Vaisseau qui passe en profil | 5 | **6** | 3,5 | B garde la forme exacte du modèle et H3 ajoute les tuyères bleues et le mouvement ; A est beau mais c'est un autre vaisseau que celui du plan 1 ; C a l'air incrusté (image de synthèse sans lumière ni flou de la plaque) |
| Chaussure qui tourne (produit) | 5,5 | 4,5 | **6** contre B ; 5,5 contre A | A est la plus « pub » mais **invente le produit** (grand panneau orange et un logo triangulaire de marque) ; B garde exactement la chaussure mais ne la fait presque pas tourner ; C la fait tourner exactement, en image de synthèse un peu plastique (texture de TRELLIS bosselée au talon) |

### 5.4 Décision

**Le gain est réel mais étroit, et Blender n'est pas indispensable pour l'obtenir.**

- Ce que la chaîne 3D apporte vraiment : **la fidélité d'un objet précis** (le produit du client, le même vaisseau d'un plan à l'autre) et une trajectoire exacte. H3 seul garde mieux le spectacle et la lumière, mais change l'objet (et ajoute des logos).
- Ce qu'elle n'apporte pas : du spectacle triple A. Le calque 3D posé sur une plaque générée perd (3,5/10) : lumière, grain et flou ne raccordent pas, et la plaque n'est pas contrôlable.
- Le gain vient du **plan clé** (B), qui n'a besoin que d'une image de l'objet sous le bon angle : le visualiseur 3D de Relief la donne déjà. **Intégré** : bouton « Animer avec H3 » dans Relief (la vue telle que la personne l'a tournée, posée sur un fond de studio, devient le plan clé I2VA du mode Vidéo), sans service Blender à exploiter.
- Le rendu exact d'une tournette (C3) reste utile pour les produits ; il demande un travailleur Blender (pc1) qui n'est **pas déployé** : à faire quand un client produit le demande, avec une meilleure texture (retexture prévue dans Relief).
- **Ce qui rendrait Blender décisif** : un modèle vidéo guidé par profondeur, pose ou trajectoire. H3 n'en a pas ; recherche/24 §4 désigne Wan2.2-Fun-Control / VACE-Fun (Apache-2.0) et Wan-Move. Les passes de profondeur, normales et masque du prototype sont exactement ce qu'ils consomment ; c'est à ce moment-là que la chaîne vaudra la peine d'être un outil de l'agent. Décision de moteur (Wan retiré le 31/10 par le fondateur) à reprendre avec lui.

## 6. Ce qui reste

- **Boucle de retour sur la vidéo** (RAPO++, recherche/24 §3) : juger la prise (planche + juge visuel, déjà en place pour les films « 2 prises par plan ») et réécrire le plan raté. Non fait pour le mode Vidéo simple.
- Réalisateur au service du **Producteur** et du **storyboard Film** (`planifierFilm`) : aujourd'hui il écrit chaque plan déjà découpé ; la découpe du film elle-même reste l'ancien rôle `realisation`.
- **Dialectes** : H3 T2VA/I2VA et image Qwen sont compilés par le code ; FL2VA, L2VA et Ref2VA (personnages @) passent encore par la conversion existante (`convertirEnPromptRef`). LTX n'a pas de dialecte : il est retiré de l'interface (licence), il n'y a rien à compiler.
- Banc plus large sur la vidéo (10 paires ici ; le son à écouter par un humain ; h3-max non mesuré).
- Les deux juges sont des LLM ; aucun humain n'a départagé.
- Blender : travailleur sur pc1 non déployé ; à reprendre avec un modèle vidéo guidé par profondeur (décision de moteur au fondateur). Pika H3 Flex (TA1) non mesuré : la file de la 5090 était saturée.

## 7. Observations pour la vague « interface triple A et Mode Studio »

- Le panneau « Ce que l'IA a compris » est la bonne place pour un **storyboard visuel** : la fiche a déjà les plans (cadrage, début) ; une vignette Qwen par plan (`versImage`) coûterait ≈ 20 s de GB10 par plan et donnerait l'aperçu avant tout rendu vidéo.
- Les **variantes** devraient lancer un brouillon chacune (FastH3, 30 s de moteur) côte à côte plutôt que réécrire la description : c'est le « 4 prises » de Higgsfield, à un coût que nos GPU permettent.
- La file partagée de la 5090 (13 min d'attente moyenne pour 47 s de calcul pendant ce banc) se verra dans l'interface : il faut afficher la position dans la file et l'heure prévue, et réserver une part de la file aux clients.
- Mode Studio (FreeCut) : la fiche du réalisateur se traduit directement en pistes (un plan = un clip avec sa durée, sa réplique, sa musique) ; l'importer comme timeline éditable donnerait le pont « Créer → Studio » que filmcraft fait par contrats (recherche/24 §9).
