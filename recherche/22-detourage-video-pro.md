# 22 · Détourage vidéo pro (SAM 3.1 + ViTMatte, palier « pro » LTX-2.5 Alpha-Gen)

Date : 03/11/2026. Branche `feat/detourage-video`. Cadre : les questions juridiques sont gérées par le fondateur ; ce document consigne des **faits** (licence, accès), sans commentaire juridique.

Légende : **[LU]** lu aujourd'hui (README, fiche, API publique) ; **[MESURÉ]** mesuré sur la GB10 aujourd'hui ; **[NON FAIT]** non exécuté, avec la raison.

## 1. Résumé

- Le palier **rapide** (SAM 2.1 pour le clic et le suivi, ViTMatte pour les bords, stabilisation par flux optique, sorties PNG 16 bits / EXR / ProRes 4444 / WebM alpha) est **construit de bout en bout et mesuré** sur la GB10 : de l'importation d'une vidéo dans la page `/detourage` aux fichiers vérifiés par des lecteurs indépendants.
- Le palier **pro** (LTX-2.5 22B + IC-LoRA Alpha-Gen) est **bloqué à la source** : le modèle de base, le LoRA et SAM 3 sont **protégés par un formulaire d'accès** (HTTP 401 sans compte accepté) ; je n'ai accepté aucune licence. Aucune mesure pro n'existe donc : le plan de comparaison (§6) est prêt et chiffré comme protocole, pas comme résultat.
- **Mise à jour du 04/11 : le rapide tourne en production sur la RTX 5080 de pc3** (pod k3s, SAM 3.1 + ViTMatte base, 0,54 s par image sur 224 images à 1280 px, contre 0,67 s sur la GB10) ; la V100 est validée techniquement (0,84 s par image) mais pas en production ; le pro est installé et mesuré : meilleur que le rapide sur le verre (SAD de bande 19,4 contre 102,8), moins bon sur fourrure et fumée (§11).
- **Mise à jour du 04/11 : SAM 3.1 remplace SAM 2.1** (sélection par mot, détecteur ouvert, Object Multiplex) et SAM 2.1 est retiré ; une vérité terrain Blender chiffre la qualité (§9) et fixe le nouveau défaut de trimap (base, bande 5 %).
- Le dépôt de référence a changé de licence pendant la mission : **PolyForm Noncommercial jusqu'au 27/10/2026, puis GPL-3.0-or-later** (commit « Relicense to GPL-3.0-or-later with a commercial option », avec une licence commerciale à part pour du code fermé) **[LU API GitHub]**. Nous n'avons ni copié, ni embarqué, ni exécuté son code : l'intégration est écrite pour Nexora.

## 2. Ce que le dépôt de référence ajoute au-delà d'un workflow ComfyUI [LU README, code non lu]

Un seul nœud ComfyUI en trois étapes (Plate, Subject, Render) avec interface web, fait de `node.py`, `_engine.py`, `_video.py`, `sequence.py`. Fonctions (comportement seulement) :

| Fonction | Principe décrit |
|---|---|
| Sélection du sujet au clic, texte (« person », « dog »), option « tout le monde » | SAM 3 (détection + suivi) |
| Trimap depuis le masque | érosion 10 px / dilatation 15 px, bande « near » 15 px |
| Alpha | LTX-2.5 distilled + IC-LoRA Alpha-Gen, mode « Best » 2 passes ou « Fast » 1 passe |
| Vidéos longues | blocs de 49 images, recouvrement 9 (17 si raccords visibles), lissage temporel de 2 images |
| Personnes qui se croisent (v13) | 3 passes LTX + profondeur Depth Anything V2 Small |
| Bords en résolution native (v14) | tuiles 1920×1088 au-delà du 1080p |
| Affinage des bords | ViTMatte base |
| Couleur de bord (v15) | `quick`, `perfect` (LoRA Clean-Plate), `off` ; fichiers `rgba_` |
| Sortie | séquences PNG 16 bits ou EXR |

Réglages recommandés : 1920×1088, seed 42, seuil SAM 3 à 0,3 ; le README ne donne ni CFG, ni pas, ni force de LoRA (Lightricks : LoRA à 1,0, une seule passe en résolution native). Exigences annoncées : 12 Go de VRAM minimum, 16 Go de RAM ; ARM / sm_121 non mentionnés.

## 3. Tableau des composants

| Composant | Licence (fait) | Accès | Taille | Matériel | Rôle chez nous |
|---|---|---|---|---|---|
| **SAM 2.1** hiera-large / small | Apache-2.0 | **libre**, sans compte | 898 Mo / 184 Mo | 1,0 à 2,6 Go de VRAM mesurés (GB10) | clic, suivi, occlusions : **utilisé** |
| **ViTMatte** small / base (Composition-1k) | Apache-2.0 (fiche HF) ; entraîné sur Composition-1k, jeu Adobe dont la licence est restreinte (relevé secondaire, non vérifié à la source) | libre | 103 Mo / 387 Mo | < 1 Go | bords : **utilisé** (small) |
| BiRefNet (HR-matting) | MIT | libre | 444 Mo | idem | alternative image par image, **non intégré** (manque de temps) |
| Depth Anything V2 **Small** | Apache-2.0 (Base et Large : CC-BY-NC) | libre | 99 Mo | négligeable | futur : personnes qui se croisent |
| **SAM 3 / 3.1** | « SAM License » de Meta (19/11/2025) | **protégé** (accès manuel Meta) ; copies `Comfy-Org/sam3.1` et `unsloth/sam3.1` non protégées, même licence | 3,4 Go (1,0 à 1,7 Go en 3.1) | cœur ComfyUI 0.43.2 : nœuds `SAM3_Detect`, `SAM3_VideoTrack` | non utilisé : texte→sujet reporté ; **SAM 2.1 sert** |
| **LTX-2.5 22B distilled** int8-convrot / nvfp4 | LTX-2.x Community License (seuil de revenu 10 M$ par an, politique d'usage acceptable, dérivés sous cette licence) | **protégé** (« Agree and Access », compte HF, consentement marketing dans le formulaire) | 21,5 Go / 18,7 Go | tient entièrement dans les 128 Go de la GB10 | palier pro : **bloqué** |
| Encodeur texte Gemma 4 12B int8 | idem | protégé | 15,4 Go | idem | non requis (prompt vide), à confirmer |
| VAE vidéo « conv » | idem | protégé | 1,45 Go | – | requis par Alpha-Gen |
| **IC-LoRA Alpha-Gen 0.9** | idem | **protégé** | 1,31 Go | – | cœur du palier pro : **bloqué** |
| LoRA Clean-Plate | idem | protégé | 0,33 Go | – | couleur de bord « perfect » |
| GGUF LTX-2.5 (`unsloth`, `Abiray`…) | idem (dérivés quantifiés) | non protégé techniquement, **même licence** | Q4_K_M 13,6 à 15,7 Go ; Q8_0 22,8 à 23,6 Go | – | non utilisé : le LoRA reste protégé |
| ComfyUI-GGUF (city96) | Apache-2.0 | libre | petit | – | seulement si GGUF |
| ComfyUI-LTXVideo (Lightricks) | LTX-2 Community | libre | petit | annonce 32 Go de VRAM, pas d'ARM | fournit `LTXAddVideoICLoRAGuide` (absent du cœur 0.43.2) |
| Comfy Pro Alpha Generator | **GPL-3.0-or-later** (PolyForm NC avant le 27/10/2026) + licence commerciale à part | libre | petit | – | **étudié, non copié, non exécuté** |
| RobustVideoMatting | GPL-3.0 | libre | petit | – | écarté (qualité) |
| MatAnyone, VideoMaMa (code), GVM | non commercial / académique | variable | – | – | écartés |

Déjà sur la GB10 : ComfyUI 0.43.2 porte les nœuds LTX audio-vidéo (`LTXVAddGuide`, `LTXVCropGuides`, `LTXAVTextEncoderLoader`…) et `SAM3_*` ; ni IC-LoRA guide, ni ViTMatte, ni SAM 2 : rien à ne pas réinstaller en double.

## 4. Architecture sûre : ce que nous réutilisons, ce que nous réécrivons

- **Réécrit chez Nexora** (rien du dépôt de référence) : sélection et suivi (`outils/detourage/modeles.py`), segments avec recouvrement (`noyau.py`), trimap, fusion, estimation de l'avant-plan, stabilisation par flux optique, écrivains PNG 16 bits et EXR (`ecriture.py`), chaîne reprenable (`traitement.py`), serveur HTTP (`serveur.py`), cycle de vie des travaux, devis, isolation (`app/server/nexora/detourage/`), page `/detourage`.
- **Briques tierces appelées comme bibliothèques**, sous leur licence : `transformers` (Sam2Video, VitMatte), PyTorch, OpenCV (flux optique DIS ; Apache-2.0), ffmpeg (déjà là).
- **Palier pro** : graphe ComfyUI à écrire **d'après la fiche du modèle** (vidéo RGB, prompt vide, LoRA à 1,0, une passe en résolution native, 8n+1 images, ≤ 145 images, dimensions multiples de 32), avec nos propres nœuds de découpe en blocs et de raccord ; seuls les nœuds de base de ComfyUI et, au besoin, `LTXAddVideoICLoRAGuide` (licence LTX) servent.
- **Machine** : un serveur de détourage par machine GPU (`serveur.py`), déclaré dans la configuration des moteurs : variable `NEXORA_DETOURAGE_URL` (moteur principal) ou champ `detourageUrl` d'une entrée de `NEXORA_MOTEURS_GPU`, recettes `detourage-rapide` / `detourage-pro`. Le serveur de Creative ne touche pas aux pixels : il envoie la vidéo en flux, lance, suit, annule, relaie les fichiers.

## 5. Ce qui est construit et mesuré (palier rapide)

Chaîne : extraction (ffmpeg) → détection des changements de plan → segments (96 images, recouvrement 12, rampes qui somment à 1) → SAM 2.1 par segment, graîné par le masque du segment voisin → trimap (bande 1,5 % du petit côté) → ViTMatte sur une vignette autour du sujet → stabilisation (flux DIS, voisines t±1 pondérées par l'accord de couleur, uniquement sur la bande de bord) → avant-plan estimé (Blur-Fusion d'après l'article) → sorties → relecture de contrôle.

**Fonctions** : clics positifs et négatifs sur plusieurs images (chaque image cliquée est une graine) ; propagation avant et arrière ; **score d'objet** de SAM par image : sujet absent → masque vide + intervalle d'occlusion rapporté ; **coupures de plan détectées** (ffmpeg `scene`), le suivi ne les traverse jamais, un plan sans clic donne un masque vide signalé (« plans sans clic ») ; vidéo longue découpée, tâche **reprenable** (clés de contenu : changer le fond ne recalcule rien, changer le matting ne refait pas le suivi), **annulable**, nettoyée (suppression par l'utilisateur, par TTL 48 h après la fin, 7 j pour un dépôt jamais lancé).

**Mesures GB10** (bf16, 1280×720, clips de test §5.3) :

| Séquence | Images | Segments | Total | Suivi | Matting | Stabilisation + images | Encodage | VRAM pic | RAM pic | Scintillement avant → après |
|---|---|---|---|---|---|---|---|---|---|---|
| Lapin en prairie (fourrure, fond clair) | 22 | 1 | 18 s (chargement des modèles inclus) | 8,1 s | 1,1 s | – | – | 1,3 Go | 3,2 Go | 0,0219 → 0,0142 (−35 %) |
| Gros plan flou, mouvement rapide | 25 | 2 | 14 s | 3,9 s | – | – | – | 1,2 Go | 3,2 Go | 0,0333 → 0,0219 (−34 %) |
| Raccords (segments de 12, recouvrement 4) | 32 | 5 | 21 s | 8,9 s | 1,4 s | 7,8 s | 2,4 s | 1,1 Go | 3,1 Go | 0,0060 → 0,0045 (−26 %) |
| **Long continu (aller-retour ×4, segments 64 / 12)** | **224** | **5** | **151 s** | 67,6 s | 10,2 s | 59,0 s | 13,4 s | **2,6 Go** | **4,1 Go** | 0,0061 → 0,0041 (−33 %) |

Soit **0,67 s par image à 720p** (SAM 0,30, ViTMatte 0,05, stabilisation et écriture 0,26, encodage 0,06) ; Disque pour les 224 images : 0,36 Go de travail (images, masques) + 0,35 Go de sorties, soit ≈ 0,08 Go par seconde de vidéo à 720p (garde-fou dans le serveur : pc6 n'a que 12 Go libres ; limite par défaut 120 s par travail). L'aperçu interactif d'un clic : **0,15 s** une fois SAM chargé, 2,5 s au premier clic.

**Annulation et reprise** (serveur réel) : annulation à 38 s, puis reprise du même travail : suivi **37,8 s au lieu de 61,7 s** (2 segments sur 5 déjà calculés, images déjà extraites, réutilisés) ; suppression : dossier de la machine GPU et registre vidés.

**Raccords** (long continu, 48 images de recouvrement) : écart temporel moyen de l'alpha **0,0058 aux images de recouvrement contre 0,0037 ailleurs** ; écart maximal **0,0102 contre 0,0104** : pas de saut visible au raccord, une légère hausse moyenne attribuée à la rampe (fusion de deux suivis) et non à une marche.

**Vérification indépendante des fichiers** (`verifier.py`, OpenEXR officielle, OpenCV, ffprobe) sur la séquence longue :

| Fichier | Résultat |
|---|---|
| Alpha PNG | `uint16`, **11 508 valeurs distinctes** (pas du 8 bits promu), 0 à 65 535, gris 16 bits, alpha droit |
| RGBA PNG | `uint16`, 4 canaux, avant-plan estimé, alpha droit (non prémultiplié) |
| EXR | `float16` (demi), compression ZIP16, canal `RGBA`, attribut `nexora/alpha = premultiplied`, **R ≤ A partout**, écart max alpha PNG / EXR 0,00025, écart moyen couleur prémultipliée vs recalcul 1·10⁻⁵ ; couleur en **lumière linéaire** |
| ProRes 4444 | `yuva444p12le`, alpha 16 bits demandé |
| WebM | VP9, tag `alpha_mode=1` |

Tests : 22 tests Python (`outils/detourage/tests`, dont ré-lecture OpenEXR officielle) + 17 tests TypeScript (cycle de vie, isolation entre organisations, crédits, annulation, reprise, nettoyage, persistance ; validation des réglages).

### 5.3 Clips de test (honnêtes sur leurs limites)

Aucune vidéo réelle de personne avec vérité terrain n'était disponible. Les clips viennent de la bande-annonce de *Big Buck Bunny* (Blender, CC-BY 3.0, téléchargée de download.blender.org) : **fourrure** (lapin, écureuil), fond clair (prairie), flou de mouvement, plusieurs personnages, changements de plan. **Non couverts** : cheveux de personne filmée, verre, fumée, personnes qui se croisent filmées. Les images H3 de nos plateaux ne contiennent pas de personnes. Il n'y a pas de note chiffrée de qualité du matte (pas de vérité terrain) : le jugement est visuel (planches `marketing/creative/captures-v3/detourage-*`) et le scintillement est mesuré.

## 6. Plan de comparaison pro / rapide (à exécuter dès que les poids sont accessibles) [NON FAIT]

Matériel : GB10 (128 Go unifiés, le modèle int8 de 21,5 Go + Gemma int8 de 15,4 Go tiennent sans NVMe), RTX 5090 (32 Go, plafonnée à 475 W) si libre.

1. **Quantifications** : INT8 convrot (21,5 Go) contre GGUF Q4_K_M (≈ 15 Go, avec ComfyUI-GGUF), mêmes clips, même seed, même LoRA à 1,0.
2. **Clips** (courts d'abord, 49 puis 97 images, 1920×1088) : cheveux fins, fourrure, mouvement rapide, personnes qui se croisent, fonds complexes, verre/fumée, un long plan avec raccords (blocs de 49, recouvrement 9 et 17).
3. **Mesures par essai** : VRAM réelle (pic), RAM système (pic), débit NVMe (iostat) si délestage, secondes par bloc et par image, reproductibilité (3 graines : écart d'alpha entre exécutions), stabilité (OOM, NaN).
4. **Fidélité** : planches de bords (ZOOM ×4) pro / rapide / source, scintillement par la même mesure (flux DIS), écart d'alpha moyen entre paliers sur la bande de bord, détail conservé (pixels de bande partiellement transparents), note visuelle à l'aveugle.
5. **Règle de décision** : le pro n'est conservé que s'il bat le rapide **d'au moins 1,5 point** sur les catégories cheveux, fumée et verre, sans scintillement supérieur, dans un temps par image acceptable ; GGUF Q4 n'est retenu que si son alpha reste à moins de 0,01 d'écart moyen du INT8 sur la bande de bord (sinon INT8 : on ne suppose pas que GGUF est meilleur).

Sources de risque connues : l'Alpha-Gen est limité à 145 images par passe et 1920×1088, ne choisit pas l'objet (il décide seul de l'avant-plan : il faut notre masque en trimap ou en post-filtre), annonce un GPU de classe H100/B200 pour 145 images HD ; ComfyUI-LTXVideo n'annonce pas l'ARM.

## 7. Recommandation

1. **Livrer le rapide maintenant** (fait) : qualité honnête **7/10 sur la fourrure et les bords nets, non évaluée sur cheveux, verre et fumée**.
2. **Demander au fondateur** d'accepter lui-même, s'il le décide, les formulaires Hugging Face de `Lightricks/LTX-2.5` et `LTX-2.5-22b-IC-LoRA-Alpha-Gen` (et, séparément, `facebook/sam3`), puis de me fournir un jeton de lecture sur la machine de mesure. Je lance alors le plan §6 sur la GB10. Avant cela, **ne pas promettre le pro**.
3. En attendant, améliorer le rapide là où il est faible : texte → sujet (SAM 3 si accès), personnes qui se croisent (profondeur Depth Anything V2 Small, libre), BiRefNet-matting pour une seconde opinion.

## 8. Pc3 (04/11/2026)

Installation réelle sur la RTX 5080 16 Go de pc3 (sm_120, pilote 595.99, 30 Go de RAM dont ≈ 14 Go pris par la VM qemu), nœud agent k3s (contrôle sur pc1), sans sudo.

- **En pod** (`deploy/k8s/detourage/`, 00 à 50) : serveur `detourage` en production (1 GPU, hostPort 8231 lié à 192.168.1.126 seulement, Service ClusterIP, NetworkPolicy limitée à 192.168.1.122/32), jeton partagé + liste d'adresses dans le serveur ; image construite par Job kaniko (`construire.sh cu130|cu126`) et poussée au registre provisoire de pc3 (8,4 Go de stockage après ménage) ; pods `poids-webdav` (lecture seule des poids pour la VM V100) et `comfyui-pro` (`replicas: 0`).
- **Installation native de secours** : venv uv Python 3.12, superviseur `demarrer.sh` / `arreter.sh`, unité systemd utilisateur, scripts gardés dans `deploy/pc3/` ; arrêtée après validation du pod. Linger désactivé (`loginctl enable-linger pc3` à faire par le fondateur).
- **Creative branché** : `NEXORA_DETOURAGE_URL=http://192.168.1.126:8231` + jeton dans `/etc/nexora/creative.env` de la VM 202, `/api/nexora/etat` répond `detourage: true`. Parcours de bout en bout vérifié sur la VM 202 : santé, aperçu d'un clic (0,11 à 0,16 s), dépôt, travail complet (16,4 s pour 49 images), téléchargement des six sorties, nettoyage ; long clip de 224 images en 126,5 s.
- **V100 dans la VM** : torch 2.14.1 cu126 (les roues cu128 et cu130 n'ont plus sm_70), fp16, poids montés par `rclone mount` depuis pc3, venv local 7,1 Go. Validée, pas en production : la VM 202 ne peut pas joindre la VM V100 (réseau qemu « user »).

Mesures pc3 contre GB10 (mêmes 5 clips Big Buck Bunny, mêmes clics, 1280 px de large, `outils/detourage/banc.py`, long continu de 224 images) :

| Machine, réglage | Total | s/image | Suivi | Matting | Stabilisation + images | Encodage | VRAM pic (torch) | RAM pic | Scintillement après |
|---|---|---|---|---|---|---|---|---|---|
| GB10, SAM 2.1 + ViTMatte small, bande 1,5 % (03/11) | 151 s | 0,67 | 67,6 | 10,2 | 59,0 | 13,4 | 2,6 Go | 4,1 Go | 0,0041 |
| 5080 native, même réglage | 110,8 s | 0,49 | 35,7 | 12,6 | 53,9 | 6,9 | 2,56 Go | 4,9 Go | 0,00415 |
| 5080 native, ViTMatte base, bande 5 % | 135,6 s | 0,61 | 37,1 | 32,6 | 56,9 | 7,2 | 2,75 Go | 5,6 Go | 0,00371 |
| 5080 en pod, ViTMatte base, bande 5 % | 127,9 s | 0,57 | 34,9 | 29,4 | 55,3 | 7,3 | 2,7 Go | 4,7 Go | 0,00371 |
| **5080 en pod, SAM 3.1 + ViTMatte base, bande 5 %** | **120,0 s** | **0,54** | 27,6 | 29,2 | 54,6 | 7,5 | 2,69 Go (3,27 Go par `nvidia-smi`) | 5,9 Go | **0,00362** |
| V100 (VM), SAM 3.1 fp16 + ViTMatte base, bande 5 % | 188,7 s | 0,84 | 64,8 | 54,6 | 58,3 | 8,1 | 2,89 Go | 4,8 Go | 0,00363 |

Lecture : la 5080 fait le travail en 0,54 s par image, soit 20 % de moins que la GB10 ; le pod coûte un peu moins que le natif à réglage égal (le premier chargement passe par le disque local) ; la V100 tient la chaîne complète à 0,84 s par image malgré l'absence de bf16 (fp16). Fichiers : `marketing/creative/captures-v3/detourage-mesures-pc3-*.json`.

## 9. Qualité à vérité terrain

Méthode (`outils/detourage/verite/`) : quatre scènes Blender 5.2.3 rendues sur pc3 avec un alpha exact au pixel près (fourrure, fumée, verre, bords nets), 49 images 1280×720, composées par `composer.py` sur des fonds de la bande-annonce de Sintel (Blender, CC-BY) ; la vérité est l'alpha du rendu, sans estimation. `noter.py` calcule SAD, MSE, Grad et dtSSD dans la bande incertaine (pixels où 0,002 < vérité < 0,998, dilatés de 10 px). Une même sélection (boîte + point au centre) est donnée à toutes les variantes ; `banc_verite.py` réutilise le suivi déjà calculé (clés de contenu) et ne refait que le matting.

SAD de bande (plus bas = mieux) :

| Réglage | fourrure | fumée | bords nets | verre |
|---|---|---|---|---|
| SAM seul (pas de matting) | 13,56 | 11,89 | 1,65 | 100,8 |
| ViTMatte small, bande 1,5 % (ancien défaut) | 13,28 | 14,01 | 0,683 | 102,9 |
| ViTMatte base, bande 1,5 % | 13,67 | 12,21 | – | 102,8 |
| ViTMatte small, bande 5 % | 5,98 | 8,49 | 0,689 | 102,7 |
| **ViTMatte base, bande 5 % (nouveau défaut)** | **6,05** | **6,59** | **0,668** | 102,8 |
| ViTMatte base, bande 8 % | 8,90 | 4,40 | 0,869 | 101,6 |

Conclusions :
- La largeur de la bande du trimap pèse plus que la taille du modèle ; base + 5 % divise l'erreur par 2 sur fourrure et fumée sans dégrader les bords nets.
- Sur les vrais clips, ce réglage baisse le scintillement de 11 % et coûte +22 % de temps par image : il est devenu le défaut.
- Le **verre transparent** échoue avec toutes les variantes rapides (SAD ≈ 100 : le sujet est rendu opaque) ; c'est le cas d'usage du palier pro.
- Ces mesures ont été faites avec SAM 2.1 ; SAM 3.1 a été adopté ensuite sans nouveau banc comparatif (consigne du fondateur).
- Non testés : BiRefNet (arrêté faute de temps, le trimap domine), MatAnyone (licence non commerciale S-Lab), ViTMatte plus grand (n'existe pas en Composition-1k au-delà de base).

## 10. SAM 3.1

Ce qu'il apporte :
- **Sélection par mot** (en anglais) en plus du clic et de la boîte : la route `POST /api/nexora/detourage/texte` renvoie les objets trouvés avec leur score, un clic choisit l'objet et sert de graine ; champ « Désigner par un mot (en anglais) » dans l'étape « 2 · Sujet » de `/detourage`.
- **Détecteur ouvert** : les objets sont proposés par le modèle, sans liste fermée de classes.
- **Object Multiplex** : plusieurs objets suivis ensemble par un seul passage, au lieu d'un suivi par objet.
- Intégration : le code SAM 3 de ComfyUI v0.44.0 est appelé comme bibliothèque (`outils/detourage/sam31.py`) ; pas de second serveur, un seul processus tient le GPU.
- Poids : `Comfy-Org/sam3.1`, révision 7bb8374, `checkpoints/sam3.1_multiplex_fp16.safetensors`, 1,75 Go, sha256 vérifié ; licence SAM de Meta jointe au dépôt. Le dépôt officiel `facebook/sam3.1` répond encore 403 (accès en attente) et n'est pas utilisé.

Mesures :

| Machine | Chargement | Clic | Mot | Suivi de 49 images | IoU contre la vérité terrain | VRAM pic |
|---|---|---|---|---|---|---|
| 5080 (pod) | 4 s | 0,81 s | 0,55 s (« furry ball », score 0,94) | 4,3 s | 0,971 | 2,9 Go |
| V100 (VM) | ≈ 70 s (lecture par le montage WebDAV) | 0,56 s | 0,67 s | 9,0 s | 0,970 | 2,85 Go |

Limite de suivi : un masque initial unique par segment (les autres clics du segment ne servent qu'à l'image où ils sont posés) et masques suivis binaires, contre des probabilités par image avec SAM 2.1.

SAM 2.1 **retiré le 04/11/2026** (consigne du fondateur) : code de repli supprimé, poids effacés sur pc3 (`~/nexora-detourage/modeles/hf`) et sur pc6 (`~/nexora-creative-data/models/detourage/hf`, blobs 1,08 Go et cache `xet`) ; les anciens noms `large` et `small` envoyés par d'anciens clients désignent désormais SAM 3.1.

## 11. Palier pro mesuré sur la RTX 5080 (04/11/2026)

Essai du 04/11 sur la 5080 (nvfp4, LoRA 1,0, 8 pas distillés, `executer_pro.py`) : fonctionne ; 25 images en 1280×736 en 18 à 20 s une fois les poids en mémoire (0,73 à 0,8 s par image ; premier passage 768×448 avec chargement : 34,4 s), 97 images en 88,3 s (0,91 s par image) ; VRAM pleine (15,3 à 16,1 Go, déchargement dynamique en RAM) ; RAM de pc3 au pic 29,2 Go sur 30 (pod 14,8 Go) : 1920×1088 ou 145 images saturerait pc3 tant que la VM V100 garde ses 14 Go. Qualité à vérité terrain (SAD de bande, 25 images, 1280 px) : le pro choisit seul l'avant-plan et prend le personnage du fond de Sintel (fourrure brute 123, ignorée) ; guidé par notre masque SAM (hors sujet remplacé par du gris), il donne **verre 19,4 contre 102,8 pour le rapide (5 fois mieux)**, mais **fourrure 22,5 contre 6,05** et **fumée 35,4 contre 6,59** (moins bien). Scènes de synthèse : le modèle est entraîné sur des prises réelles, à revérifier sur de vrais plans.

Graphe : `outils/detourage/pro/executer_pro.py` (d'après le flux officiel « LTX-2.5 V2V IC-LoRA Single Stage Distilled ») ; poids officiels et sha256 : `outils/detourage/pro/modeles-pro.json`. Règle de décision du §6 : le pro n'est gardé que là où il bat le rapide ; aujourd'hui, le verre seulement.
