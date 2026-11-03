# 17 — Modes de Creative et Mode Studio « Premiere simplifié et boosté » : la bulle d'effet au clic droit (3 novembre 2026)

Prolonge `02` (base d'éditeur), `07` (feuille de route vs Higgsfield), `12`, `13` (harnais de montage, `EditPlan`), `15` et `16` (littérature). Ne les répète pas : on ne redit ici ni le choix de FreeCut, ni l'`EditPlan`, ni les techniques de cohérence de personnages.

## 0. Méthode et légende

- **[LU]** : code, licence, README, page de modèle ou passages de l'article ouverts et lus aujourd'hui (3/11/2026) ; les métadonnées GitHub/Hugging Face (licence déclarée, étoiles, date du dernier push) viennent des API publiques le même jour.
- **[RÉSUMÉ]** : seul le résumé (abstract) ou une connaissance générale, non revérifiée aujourd'hui. À traiter comme une piste.
- Les licences sont notées **comme des faits** (colonne « Licence »), sans analyse juridique (cadre de travail : le fondateur gère le juridique). Un nom de licence entre guillemets est celui que l'API ou la fiche du modèle déclare ; « NOASSERTION » = l'API ne sait pas, le fichier `LICENSE` est à lire.
- Limites : je n'ai exécuté aucun modèle ; les besoins GPU sont ceux des dépôts ou des articles, pas des mesures sur le GB10 ou la RTX 5090. Les modes (§B) sont des propositions de conception, pas des constats.

## 1. Les six constats qui comptent

1. **Le Mode Studio possède déjà 80 % du moteur d'une « bulle d'effet »** [LU, code local] : 52 effets WebGPU (`gpu-glow`, `gpu-vhs`, `gpu-grain`, `gpu-rgb-split`, `gpu-block-glitch`, `gpu-crt`, `gpu-halftone`, `gpu-chroma-key`, `gpu-secondary-qualifier`, `gpu-power-window`…), 17 transitions GPU (glitch, light-leak-burn, liquid-distort, lens-warp-zoom…), des éléments `adjustment` (effets sur toutes les pistes au-dessus), `lottie`, `controller`, `composition`, la vitesse par clip, les images clés, RIFE (interpolation) et Anime4K (agrandissement) dans le navigateur, et une couche d'opérations validées (`addEffect`, `addKeyframe`, `addItem`, `addTransition`, `split`, `updateItem`…). Il manque : le menu clic droit « Effet IA ici », le contrat typé de recette, et les voies qui exigent des serveurs (masques, retrait d'objet, bruitage).
2. **Un « effet IA » n'est pas un préréglage de plus, c'est un compilateur d'intention** : le LLM ne produit pas de pixels, il produit une **recette typée** (liste d'étapes tirées d'un catalogue fermé, avec portée, bornes, coût), que le code valide, chiffre, prévisualise et applique en un seul pas d'annulation. Le même principe que le harnais `EditPlan` (rapport 13 §5.3) et que le Producteur : le modèle propose, le code dispose.
3. **Les licences coupent net le choix des briques de pixels** [LU] : MatAnyone et ProPainter sont sous *S-Lab License 1.0* (usage non commercial) ; les poids de MMAudio (bruitage vidéo→audio) sont CC-BY-NC-4.0 (le code est MIT) ; MiniMax-Remover (poids CC-BY-NC-4.0), Lucy Edit Dev (licence non commerciale Decart) et les poids de F5-TTS (CC-BY-NC-4.0) sont dans le même cas. Les voies à licence permissive existent : **SAM 2 (Apache-2.0), SAM 3 (licence « SAM » de Meta), VACE (Apache-2.0), DiffuEraser (Apache-2.0), BiRefNet (MIT), Qwen-Image-Edit-2511 et Qwen-Image-Layered (Apache-2.0), Kokoro (Apache-2.0), Chatterbox (MIT), SeedVR2 (Apache-2.0)**.
4. **Pour les plaques à transparence, la génération sur noir + mélange « écran » évite 90 % du matting** (flammes, étincelles, fumée, éclat d'objectif, pluie, poussière : la lumière s'additionne, pas besoin d'alpha). Pour les vrais alpha, la recherche 2025-2026 donne **Wan-Alpha** (code MIT, WeChatCV, 425 étoiles ; article 2509.24979) et TransPixeler (2501.03006) [RÉSUMÉ pour les deux] ; et l'article **Vera** (Netflix/Caltech, 2606.23610) [LU] montre la bonne architecture d'édition : générer une **couche d'édition + un alpha** et recomposer sur la vidéo source, ce qui préserve les pixels non touchés. Principe à copier même avec VACE : recomposer par masque avec bord adouci.
5. **Les modes de Creative sont des configurations, pas des produits séparés** : un même projet (kit de marque, médias, grand livre de crédits, Producteur, Mode Studio) avec un *mode* qui fixe le brief, les gabarits, les outils autorisés, les recettes (mémoire AMD, rapport 14) et les sorties. Le pipeline `marketing/nexora/imprimes/` est déjà un moteur de rendu déterministe (HTML → Playwright → PDF fond perdu, traits de coupe, contours Ghostscript, calque de vernis) : il lui manque une **spécification de conception en JSON** (comme le « protocole » de CreatiPoster [LU]) et un **kit de marque** persistant.
6. **Sources de gain rapide, sans GPU** : importer **gl-transitions** (MIT, ~100 transitions, traductions WGSL fournies avec un fichier `compatibility.json` [LU]), exposer le **catalogue du registre GPU** au LLM en JSON Schema avec bornes, et ajouter la **rampe de vitesse** par découpage en segments (la vitesse FreeCut est constante par clip, plage 0,1 à 10 [LU]).

---

# Partie A — Mode Studio : « Premiere simplifié et boosté »

## A1. Architecture de la bulle d'effet au clic droit

### A1.1 Parcours (ce que voit la personne)

1. Clic droit sur la règle, un vide de piste ou un clip, à 3 min 22 s (le point d'insertion est le curseur de souris, repli : tête de lecture). Le menu de vide de piste existe déjà (`TrackGapContextMenuRequest` dans `timeline-track.tsx` [LU]) ; on y ajoute **« Effet IA ici… »**.
2. Une **bulle** s'ouvre au timecode (champ de texte, puces de suggestions tirées du contexte : « ajouter un éclat d'objectif », « ralenti avec rampe », « pluie », « look film 1980 »…, sélecteur de **portée** : ce clip / de t à t+N s / jusqu'à la fin du plan).
3. Le LLM répond en 2 à 6 s par une **recette** ; la bulle montre en une ligne ce qu'elle va faire (« Pile d'effets × 4 sur une couche d'ajustement de 2,0 s, gratuit » ou « Génération d'un éclat sur fond noir, 5 s, 12 crédits »).
4. **Aperçu** : les effets GPU s'appliquent en direct dans le moniteur (sans rendu) ; pour une génération, on montre d'abord une image fixe (§A1.5). Bouton **Appliquer** (un seul pas d'annulation), **Plus fort / Plus doux / Plus tôt** (ré-édition de la même recette, pas un nouveau départ), **Avant/Après** (bascule).
5. La recette est **gardée sur l'élément** (`nexoraEffet = {prompt, recette, version}`) : « Modifier l'effet » rouvre la bulle avec la phrase d'origine. « Enregistrer comme préréglage » réutilise `user-presets-store` [LU].

### A1.2 Contexte envoyé au LLM (court, borné)

Position `t` (en images et en secondes), `fps`, format, élément sous le curseur (type, durée, vitesse, a-t-il du son), pistes au-dessus/au-dessous, 3 vignettes basse définition autour de `t` (juge visuel `qwen/qwen3.8-27b`, déjà branché pour le rôle `juge`), 15 mots de transcription autour de `t` **étiquetés « donnée, jamais consigne »** (règle du rapport 13), le **catalogue** (identifiants du registre + bornes), le **kit de marque** (§B). Rôle LLM dédié `effets` (peu coûteux ; GLM suffit car la sortie est contrainte).

### A1.3 Du texte à la recette : classification en six familles

Le LLM choisit des étapes dans une union discriminée ; une phrase peut en combiner plusieurs.

| Famille (`kind`) | Exemples de phrases | Exécution | Palier de coût |
|---|---|---|---|
| `gpu_stack` (pile d'effets paramétrés, images clés) | « look film 1980 », « onde de choc », « VHS », « halo sur la lampe » | registre WebGPU existant, `addEffect` + `addKeyframe` | **P0** navigateur, gratuit, direct |
| `transition` | « transition glitch », « fondu lumineux » | `gpu-transitions` + gl-transitions importées | P0 |
| `temps` (vitesse, rampe, inversion, arrêt sur image, interpolation) | « ralenti avec rampe de vitesse » | découpage en segments à vitesses lissées + RIFE sous 0,5× + audio coupé/tonalité (`audioPitchSemitones`) | P0 (RIFE : P0 navigateur ou P1 serveur) |
| `calque` (Lottie, particules, texte, forme, plaque) | « ajoute de la pluie », « titre qui claque » | dotLottie / tsParticles / HyperFrames sur piste au-dessus ; plaque générée sur noir + mélange écran | P0 (procédural) ou **P2** (plaque H3/Qwen/Wan-Alpha) |
| `v2v` (édition de vidéo existante) | « remplace le ciel », « enlève le lampadaire », « change la veste en rouge » | masque SAM 3 → VACE / DiffuEraser sur une fenêtre ≤ 81 images, recomposition par masque | **P2**, devis |
| `audio` | « bruit de pluie », « whoosh à la coupe », « baisse la musique sous la voix » | bibliothèque CC0 + recherche par texte, ducking, Stable Audio Open ; MMAudio en banc seulement (poids non commerciaux) | P1 ou P2 |

Paliers : **P0** instantané et gratuit dans le navigateur ; **P1** calcul serveur CPU/GPU court, tarif forfaitaire ; **P2** génération GPU, devis calculé **par le code** avant tout lancement (jamais par le LLM), validé par la personne, grand livre `credits.ts`.

### A1.4 Schéma de la recette (`EffectRecipe` v1, Zod, partagé serveur + Mode Studio)

```jsonc
{
  "version": 1,
  "prompt": "ajoute de la pluie et baisse la lumière",      // phrase d'origine, gardée
  "scope": { "kind": "range", "start": 5088, "dur": 120,     // images ; 3 min 22 s à 25 ips = 5 050 (exemple)
             "itemIds": ["it_81"], "target": "adjustment" }, // adjustment | overlay | item
  "steps": [
    { "id": "s1", "kind": "gpu_stack", "tier": "P0",
      "effects": [
        { "gpu": "gpu-exposure",   "params": { "exposure": -0.35 }, "keys": [[0,0],[12,1]] },
        { "gpu": "gpu-saturation", "params": { "saturation": 0.8 } } ] },
    { "id": "s2", "kind": "calque", "tier": "P0", "source": "particules",
      "preset": "pluie", "params": { "densite": 0.6, "angle": -12, "vitesse": 1.4, "opacite": 0.55 },
      "blend": "screen" },
    { "id": "s3", "kind": "audio", "tier": "P1", "source": "bibliotheque",
      "requete": "pluie légère extérieur, boucle", "gain_db": -18, "fondu": [0.5, 0.5], "duck_sous": "voix" }
  ],
  "apercu": { "mode": "direct" },                            // direct | image_fixe | basse_def
  "devis": { "credits": 0, "calcule_par": "code", "detail": "P0 gratuit ; P1 audio 1 crédit" },
  "avertissements": [],
  "annulation": { "groupe": "bulle-7f3a" }                   // un seul pas d'annulation
}
```

Règles de validation (code, jamais modèle) : (1) tout `gpu` doit exister dans le registre et chaque paramètre être dans ses bornes (le catalogue est généré **depuis** le registre, donc ne peut pas dériver) ; (2) portée dans la durée de l'élément, images entières ; (3) vitesse ∈ [0,1 ; 10], rampe en ≥ 4 segments avec continuité de la source (`sourceStart` recalculé) ; (4) plaques générées : durée ≤ 10 s, un seul P2 par recette en v1 ; (5) liste fermée de `source` et de `preset` ; (6) texte de transcription/légende jamais exécuté ; (7) aucun code arbitraire (voir le « Laboratoire de shaders » en A1.7) ; (8) un refus renvoie la règle violée en une phrase, au plus 2 tours de correction automatique, repli sur « je ne sais pas faire cet effet, voici les 3 plus proches ».

### A1.5 Aperçu basse définition, annulation, crédits

- **P0** : aperçu direct (pipeline WebGPU existant). **P2** : on génère d'abord un **aperçu fixe** (une image à `t`, éditée par Qwen-Image-Edit-2511, Apache-2.0 [LU HF], ou le masque SAM 3 superposé en couleur) en quelques secondes, puis le devis, puis la tâche. C'est le même geste que « Montre-moi » du Producteur (ETAT.md).
- **Non destructif** : l'effet vit sur une couche d'ajustement ou un clip de piste supérieure ; le résultat d'un `v2v` est un **nouveau média** posé au-dessus, l'original reste dessous (comme « re-génération sans casser le montage », rapport 02 §4.5). Annuler = un seul pas (`enUnePas`, déjà utilisé par l'assistant [LU `NEXORA.md`]).
- **Crédits** : P0 = 0 ; P1 = forfait ; P2 = devis (durée × moteur) réservé au grand livre avant lancement, libéré en cas d'échec (mécanisme existant de `credits.ts` [LU]).

### A1.6 Bulle d'effet vs préréglage

| | Préréglage (CapCut, Higgsfield, `EFFECT_PRESETS`) | Bulle d'effet |
|---|---|---|
| Entrée | choix dans une grille | phrase libre + contexte (temps, clip, mots, vignettes) |
| Sortie | un paquet de paramètres fixe | recette = composition de préréglages + images clés + opérations de temps + éventuelle génération |
| Portée | choisie à la main | déduite (clip/plage/plan) et modifiable |
| Itération | on re-choisit | « plus fort », « plus tôt », « sans le grain » modifient la **même** recette |
| Coût | nul | routage P0/P1/P2 avec devis |
| Mémoire | aucune | la recette réussie rejoint la mémoire AMD (rapport 14) et peut devenir un préréglage perso |
| Risque | aucun | hallucination de paramètres → neutralisée par le catalogue fermé et le validateur |

### A1.7 Laboratoire de shaders (R&D, après la v1)

Pour les effets absents du catalogue, le LLM peut écrire un shader. Littérature : ShadAR (génération de shaders par LLM, compilation en temps réel) 2602.17481 et AI Co-Artist (évolution interactive de shaders GLSL) 2512.08951 [RÉSUMÉ pour les deux]. Garde-fous proposés : WGSL uniquement, une entrée/une sortie texture, uniformes déclarés et bornés, compilation dans un `GPUDevice` isolé, minuteur de 50 ms/image, repli sur l'effet précédent à la première erreur, jamais de lecture hors texture. Reste de la R&D : pas avant les paliers 1 à 8 de la feuille de route.

## A2. Les briques par famille : meilleure implémentation ouverte

Les besoins GPU des modèles sont ceux annoncés (dépôt/article), **à mesurer sur GB10 (aarch64, 128 Go) et RTX 5090 (32 Go)** avant toute promesse. Règle empirique à vérifier : un modèle de 14 Md en bf16 pèse ~28 Go de poids, trop juste sur 32 Go avec les activations (quantifier ou prendre la variante 1,3 Md) et à l'aise sur 128 Go (mais plus lent).

### A2.1 Effets procéduraux et transitions (navigateur)

- **gl-transitions** [LU] : MIT (chaque transition porte son en-tête de licence ; toutes MIT sauf deux BSD), npm `gl-transitions` 2.2.0, traductions GLSL/SkSL/WGSL/Metal/AGSL vérifiées par CI et `compatibility.json`. Branchement : `infrastructure/gpu-transitions/registry.ts` ; écrire un adaptateur « nom → WGSL + uniformes → entrée du registre » et générer le catalogue LLM (nom, paramètres, défauts). Mode navigateur.
- **Registre FreeCut** [LU] : à exposer tel quel (52 effets). Manque probable pour la bulle : *halation* (contour lumineux rouge des pellicules) = `gpu-glow` + `gpu-gradient-map` ; *éclat d'objectif* = plaque (A2.3) ; *pluie* = particules ; *tremblement de caméra* = images clés sur `transform`.
- **Lottie** : `@lottiefiles/dotlottie-web` 0.82.1 (MIT, utilisé par FreeCut en 0.76) [LU] ; Rive (`rive-wasm`, MIT) [RÉSUMÉ]. Les animations Lottie ont chacune leur licence : n'embarquer que celles dont on connaît l'origine.
- **Particules** : tsParticles 4.5.1, MIT, 9 069 étoiles [LU API/npm] : pluie, neige, étincelles, confettis, poussière ; rendu dans un canvas puis capturé comme calque (ou rendu serveur par HyperFrames).
- **HyperFrames** (Apache-2.0, 77 847 étoiles, push du 3/11/2026 [LU README]) : HTML/CSS/médias/animations *seekables* → MP4 déterministe, pensé pour les agents ; ~450 blocs (CRT, glitch, grain, cartons, graphiques) via le registre. Rôle : rendu serveur de calques riches (titres cinétiques, bandeaux, graphiques animés) quand le WebGPU ne suffit pas. Remotion (licence « Remotion License » : gratuite jusqu'à 3 salariés et pour les organismes sans but lucratif, licence entreprise au-delà [LU]) reste écarté du cœur, comme dans `02`.

### A2.2 Étalonnage et « look »

LUT (`gpu-lut`), roues de couleur, courbes, qualificateur secondaire, fenêtres de puissance existent [LU]. « Make this shot look like 1980s film » = recette canonique `gpu_stack` : température +, saturation −0,15, courbe en S douce, `gpu-glow` (halation), `gpu-grain`, `gpu-vignette`, très léger `gpu-gaussian-blur` ; livrée avec 30 recettes de test (§C) pour mesurer la qualité du LLM avant d'aller plus loin. Les LUT de tiers : vérifier une à une la licence.

### A2.3 Éléments générés (plaques de VFX)

| Besoin | Voie recommandée | Alternative | Note |
|---|---|---|---|
| Éclat, flammes, étincelles, fumée, pluie, poussière | H3 ou Qwen-Image sur **fond noir uni**, mélange `screen`/`add` dans le compositeur | Wan-Alpha pour un vrai alpha (code MIT [LU API] ; poids : licence à vérifier ; backbone Wan, Apache-2.0) | Gain rapide : aucune découpe nécessaire |
| Objet opaque sur fond uni (logo 3D, produit) | génération sur **vert** + `gpu-chroma-key` (existant) ; ou BiRefNet par image (MIT [LU HF], 828 k téléchargements) | RMBG-2.0 : licence Bria « autre » [LU HF] | trames individuelles : scintillement possible, lisser par flux optique |
| Personne/objet détourés dans un plan existant | SAM 3 (masque suivi par texte) → bord adouci | SAM 2 (Apache-2.0) avec points/boîtes ; MatAnyone / VideoMaMa pour les cheveux | MatAnyone : S-Lab non commercial [LU] ; VideoMaMa (cvlab-kaist) : licence NOASSERTION, à lire [RÉSUMÉ] ; RobustVideoMatting : GPL-3.0, inactif depuis 2024-04 [LU API] |
| Vrai RGBA vidéo | Wan-Alpha / Wan-Alpha++ (2610.26189) [RÉSUMÉ], TransPixeler (2501.03006) [RÉSUMÉ] | Vera (2606.23610) : bon modèle d'architecture, **code/poids non vérifiés** [LU article] | à bancher sur la 5090 |

**Mélange sans alpha** : le compositeur FreeCut a des modes de fusion et des éléments `adjustment` ; la plaque sur noir est un clip normal avec `blendMode: screen` [à confirmer dans `types/timeline.ts`, non lu en détail].

### A2.4 Édition de vidéo existante (v2v)

Ce que H3 ne fait pas (ETAT.md : pas d'échange, de restyle, de transfert de mouvement) est ce que les modèles ouverts permettent, avec des limites réelles.

| Besoin | Meilleur choix ouvert | Licence (fait) | Maturité / limites | GPU |
|---|---|---|---|---|
| Échange, ajout, extension, « bouger » un objet, remplacer l'arrière-plan | **VACE** (`ali-vilab/VACE`, Wan2.1-VACE 1,3 Md et 14 Md) : R2V, V2V, MV2V ; Move/Swap/Reference/Expand/Animate-Anything ; inpainting par boîte ou masque [LU README] | Apache-2.0 (poids HF aussi) [LU] | 4 045 étoiles, dernier push 2025-10 ; **81 images** à 480×832 (1,3 Md) ou 720×1280 (14 Md) | article Vera (tableau de comparaison) : VACE-1.3B 25,3 Go, 2,4 min ; VACE-14B 37,2 Go par carte sur 4 A100, 5,6 min [LU] |
| Retrait d'objet (lampadaire, micro, passant) | **DiffuEraser** (SAM masque + diffusion, modèle d'inpainting vidéo) | Apache-2.0 [LU API], 706 étoiles, push 2025-04 | stable mais ancien ; sinon VACE (inpainting) | non mesuré |
| Retrait d'objet, meilleure qualité | ProPainter | S-Lab non commercial [LU] | **exclu** sauf accord | – |
| Retrait en une passe sans masque | MiniMax-Remover / LoVoRA (2512.02933) | poids CC-BY-NC [LU HF] / [RÉSUMÉ] | **exclu** / surveiller | – |
| Édition par instruction (« mets-lui une veste rouge ») | Lucy Edit Dev ; OpenVE-Edit (5 Md, jeu OpenVE-3M, 2512.07826) ; Aurora (agent VLM + DiT, 2605.18748) | Lucy : non commercial [LU HF] ; OpenVE / Aurora : [RÉSUMÉ], licences non lues | **surveiller** : aucun n'a une licence vérifiée pour nous | – |
| Image clé éditée (aperçu et point de départ) | **Qwen-Image-Edit-2511** | Apache-2.0 [LU HF] | mature ; l'image clé édite le premier plan, puis I2V (H3) ou VACE propage | déjà dans notre parc image |
| Éclairage, restyle global | VACE V2V ou recette `gpu_stack` | – | le restyle par diffusion change tous les pixels : proposer d'abord le `gpu_stack` | – |
| Effet « de référence » (explosion, transformation) | VFXMaster (CogVideoX-5B-I2V, attention en contexte avec vidéo de référence, adaptation en une prise) [LU article] ; IC-Effect (2512.15635), EffectMaker (2603.06014, 130 k vidéos EffectData), P-Flow (2603.22091, optimisation de prompt par VLM) [RÉSUMÉ] | code/poids à vérifier (« will release » pour VFXMaster) | **surveiller**, ne pas intégrer | – |

**Principe commun à imposer** (tiré de Vera [LU]) : ne jamais remplacer le plan entier. Pipeline `v2v` : (1) SAM 3 → masque suivi sur la plage ; (2) dilater et adoucir ; (3) VACE/DiffuEraser sur la **fenêtre minimale** (≤ 81 images, recadrée sur la boîte englobante + marge) ; (4) recomposer `source × (1 − masque) + résultat × masque` ; (5) raccord de teinte/grain ; (6) poser comme nouveau clip. Plage > 81 images : découper en fenêtres avec 8 images de recouvrement et fondu.

### A2.5 Audio

| Besoin | Voie | Licence (fait) | Note |
|---|---|---|---|
| Bruitage depuis la vidéo | **MMAudio** (8 s par défaut, ~6 Go VRAM en 16 bits [LU README]) ; HunyuanVideo-Foley (2508.16930) ; Kling-Foley (2506.19774), Foley Control (2510.21581, T2A gelé + passerelle vidéo) [RÉSUMÉ] | MMAudio : code MIT, **poids CC-BY-NC-4.0** [LU] ; Foley : licence « tencent-hunyuan-community » [LU HF] (texte non lu) | pour un produit : **bibliothèque de sons libres de droits connus + recherche par texte** d'abord ; le modèle génératif en banc/démo jusqu'à clarification des poids |
| Texte → effet sonore/musique courte | Stable Audio Open 1.0 (+ `stable-audio-tools`, MIT) | poids « stable-audio-community » [LU HF] | durée limitée (~47 s annoncés par la fiche, non revérifié) |
| Musique | MiniMax-Music3 (déjà) | – | ne pas dupliquer |
| Séparation de pistes | Demucs (MIT) | dépôt **archivé** depuis 2024-04 [LU API] | OK en l'état ; forks à surveiller |
| Voix et dialogues | Whisper (MIT), faster-whisper (MIT), WhisperX (BSD-2, mots alignés), Silero VAD (MIT) [LU API] | – | déjà sur le serveur (sous-titres) |
| TTS | **Kokoro-82M** (Apache-2.0, 11 M téléchargements [LU HF], tourne même dans le navigateur via transformers.js [RÉSUMÉ]) ; Chatterbox (MIT, clonage de voix) ; VibeVoice-1.5B (MIT, longue durée multi-locuteurs) ; Dia (Apache-2.0, dialogues) | F5-TTS : code MIT, **poids CC-BY-NC** [LU] | Kokoro pour la narration de cours ; clonage : exiger un indicateur de consentement dans le projet |
| Ducking, mixage | `ducking.js`, `loudness.js` du harnais (rapport 13) | – | `mix_audio` deux passes encore à faire (ETAT.md) |

### A2.6 Opérations de temps et de plan

- **Rampe de vitesse** : pas de remappage temporel natif ; découper en N segments de vitesse constante (courbe d'accélération lissée) avec `sourceStart` continu, RIFE (MIT, déjà en ONNX dans `infrastructure/interpolation` [LU]) pour les ralentis < 0,5×. P0.
- **Recadrage 9:16** : `reframe.js` du harnais ; régénérer en vertical natif pour les plans H3 (rapport 13 §5.2 outil 8).
- **Stabilisation** : peu utile pour les plans générés ; pour des prises importées, `vidstab` (via ffmpeg, GPL-2+ NOASSERTION [LU API]) ou Gyroflow (GPL-3.0, avec gyroscope [LU API]) côté serveur. Priorité basse.
- **Agrandissement** : Anime4K déjà dans le navigateur [LU] ; SeedVR2-3B/7B (Apache-2.0 [LU HF]) pour la restauration/agrandissement vidéo serveur, à bancher face à Real-ESRGAN (déjà utilisé pour les affiches).

## A3. Modèles d'interface à copier (et à simplifier)

[RÉSUMÉ pour toute cette section : connaissance générale des produits, non relue aujourd'hui ; la comparaison Higgsfield est dans `07`, `12`.]

| Motif | Origine | À copier | À simplifier |
|---|---|---|---|
| Montage par le texte | Descript, Premiere (montage basé sur la transcription) | supprimer un mot = couper ; les mots horodatés existent (faster-whisper) | une seule vue « Texte » à côté du moniteur |
| Couche d'ajustement | Premiere, DaVinci | contenant des effets de la bulle (non destructif) | la bulle la crée seule |
| Images clés / courbes | Premiere, After Effects | `addKeyframe` existe | la bulle les pose, l'éditeur les affine |
| Préréglages en un clic + recherche | CapCut | grille de préréglages → même schéma de recette | les 12 plus utiles seulement |
| Suggestions contextuelles | CapCut, Premiere | puces dans la bulle selon l'analyse (silences, scène sombre, voix) | 3 puces maximum |
| Édition « en contexte » par prompt | Runway (Aleph), Adobe (Generative Extend) | v2v par masque et prompt | devis et aperçu fixe d'abord |
| Page Cut / Edit à deux niveaux | DaVinci | mode Simple/Expert (existe déjà côté Creative) | – |
| Timeline magnétique | Final Cut | inutile ici | ne pas copier |

## A4. Bibliothèques et éditeurs à réutiliser (état des lieux)

| Brique | Licence (fait) | État | Rôle |
|---|---|---|---|
| FreeCut | MIT | 2 305 étoiles, push 2026-10-29 [LU] | base du Mode Studio |
| OpenCut | MIT | 97 184 étoiles, push 2026-09-24 [LU API] | référence UX ; réécriture complète en cours (rapport 02) |
| Olive | GPL-3.0 | 9 146 étoiles, **push 2024-12** [LU API] | écarté (inactif, GPL) |
| Kdenlive / MLT | GPL-3.0 / LGPL-2.1 | actifs (push 2026-11-03 / 2026-10-29) [LU API] | MLT XML comme échange et `melt` comme rendu serveur de secours ; Kdenlive en référence UX seulement |
| OpenTimelineIO | Apache-2.0 | 2 053 étoiles, push 2026-10-31 [LU API] | échange vers Premiere/DaVinci (adaptateurs) ; l'export projet existe déjà |
| editly | MIT | 5 577 étoiles, **push 2025-05** [LU API] | stagnant ; idées seulement |
| Motion Canvas | MIT | 19 659 étoiles, push 2026-07 [LU API] | animations de schémas pour les cours (dérivé Revideo, rapport 02) |
| Natron, Blender VSE | GPL | – [RÉSUMÉ] | référence de compositing ; non intégrables |
| ffmpeg.wasm / WebCodecs / Mediabunny | LGPL-GPL selon build / – / MPL (voir `02`) | Mediabunny 1.54.0 dans le dépôt [LU] | E/S et export du navigateur |

---

# Partie B — Les modes de Creative

## B0. Le « mode » comme configuration

```ts
interface Mode {
  id: 'marketing' | 'cours' | 'long-metrage' | 'clip';       // + 'simple' existant
  schemaBrief: ZodType;                // champs demandés (ex. carte : nom, titre, coordonnées)
  gabarits: GabaritRef[];              // modèles de conception / de plan
  outils: NomOutil[];                  // liste fermée pour l'agent (Producteur) et la bulle
  competences: string[];               // fichiers server/nexora/competences/*.md
  recettes: RecetteRef[];              // mémoire AMD (rapport 14)
  sorties: Sortie[];                   // pdf-impression, png, mp4 16:9/9:16, otio, fountain…
  regleDevis: RegleDevis;              // ce qui est gratuit, forfaitaire, sur devis
}
interface Projet { id; mode; kitMarque: KitMarque; medias: Media[]; execution: Run[]; /* + corps propre au mode */ }
```

Le **kit de marque** (`KitMarque`) est partagé par tous les modes : couleurs (hex, cible CMJN ou profil ICC, nom de couleur d'accompagnement s'il y en a une), polices (OFL), logos SVG (variantes sur fond clair/sombre, zone de protection), ton (3 adjectifs, mots interdits), coordonnées (`personnes[]`, comme `coordonnees.json`), format de QR par défaut, style visuel (références + préfixe de prompt Qwen/H3). Extraction automatique depuis un site ou un logo (couleurs dominantes + polices détectées) en proposition à valider.

## B1. Mode Marketing (« Imprimés & identité »)

### B1.1 Architecture proposée

1. **Brief** (formulaire court + phrase libre) → le LLM choisit un **gabarit** et remplit une **`SpecConception`** (JSON de calques sur le modèle du « protocole » de CreatiPoster : calques texte avec contenu, police, taille, position, couleur, contour, alignement, interlignage ; calques d'actif avec position, recadrage, rotation, masque ; ordre = z-order ; invite de fond séparée [LU, 2506.10890]).
2. **Rendu déterministe** par le moteur existant `identite/sources/moteur.mjs` + Playwright → PDF fond perdu, traits de coupe, texte en contours (Ghostscript), calque de vernis, PNG [LU `LISEZMOI.md`]. Le LLM ne dessine pas des mises en page libres : il choisit un gabarit et des valeurs ; le code garantit marges, zones de sécurité, contraste, lisibilité du texte et débords.
3. **Fond ou illustration** : Qwen-Image (déjà), conditionné sur le rendu des calques de premier plan (idée de CreatiPoster : le modèle de fond voit le texte posé) [LU] ; agrandissement Real-ESRGAN (déjà ; le rapport imprimés note ~224 dpi sur 18×24 po) ou SeedVR2.
4. **Éditeur léger dans le navigateur** pour retoucher la `SpecConception` : Fabric.js (MIT, 31 534 étoiles [LU API]) ou Konva (licence NOASSERTION à l'API ; à lire) au-dessus du même JSON, avec rendu de référence côté serveur ; **Penpot** (MPL-2.0, 62 003 étoiles, plugins avec runtime et événements de sélection/fichier [LU API/README]) reste l'option « vrai outil de design » à auto-héberger, mais lourd (pile Clojure, base de données) ; ne pas la prendre en v1.
5. **Calques depuis une image** : Qwen-Image-Layered (Apache-2.0, décompose une image en plusieurs calques RGBA, poids HF Apache-2.0 [LU]) permet d'importer un flyer ou une affiche existante et de le retoucher couche par couche ; limite lue dans le README : le texte d'invite décrit l'ensemble, il ne pilote pas chaque calque. Compléments : Accordion (2507.05601, descente de la pile par VLM + SAM + retrait d'éléments), LaDe (2603.17965, calques RGBA de longueur variable, comparé à Qwen-Image-Layered) [RÉSUMÉ].
6. **Sorties imprimeur** : fond perdu et traits (fait) ; imposition « n-up » (planches de cartes/accroche-portes) avec `pdf-lib` (MIT, mais dernier push 2024-07 [LU API]) ou génération directe à la taille de planche par le moteur ; contrôle préliminaire (résolution effective des images, polices intégrées, noir riche, débordement hors fond perdu) ; **CMJN / PDF-X** : Ghostscript (déjà utilisé pour les contours ; conversion de profil et PDF/X possibles [RÉSUMÉ]) ou Scribus en ligne de commande (GPL [RÉSUMÉ]) ; honnêtetés déjà écrites dans `LISEZMOI.md` : l'orange `#FF5A1F` est hors gamme CMJN, demander une épreuve ; ne pas promettre le CMJN « automatique ».
7. **Codes** : QR (génération en code, bibliothèques MIT) et lecture de contrôle avec `zxing-js` (Apache-2.0 [LU API]) : tester que le QR imprimé en taille finale se décode (contraste, zone de silence), à intégrer au contrôle préliminaire.

### B1.2 Pièces et gabarits (v1)

| Pièce | Existant | À ajouter |
|---|---|---|
| Carte d'affaires | oui (4 variantes, vernis) | gabarit paramétré par kit de marque |
| Dépliant, fiche, affiche, bannière | oui | idem |
| **Accroche-porte** (accroche-porte 3,5 × 8,5 po avec gabarit de découpe en page 3) | oui (salon) | gabarit « offre locale », slogan 6 à 9 mots, QR, trou de poignée en calque `decoupe` |
| Logo (SVG) | logos officiels Nexora | **module Logo** (B1.3) |
| Slogans / accroches | – | compétence `accroches.md` (B1.4) |
| Posts réseaux (carré, 4:5, 9:16), bannières | partiel (publication par réseau) | gabarits + déclinaisons automatiques de format |
| Vidéo promo | Producteur, V3, campagne films | recette « promo 15 s » + HyperFrames pour cartons |

### B1.3 Module Logo

Voie recommandée en trois temps : (1) **explorer** : Qwen-Image génère 8 pistes de marques simples (fond uni, aplats), sans promettre qu'elles soient exploitables ; (2) **vectoriser** : `vtracer` (MIT, 7 446 étoiles, push 2026-10-22 [LU API]) ou potrace (GPL [RÉSUMÉ]) puis nettoyage (fusion de chemins, SVGO, nombre de nœuds borné, texte converti en contours) ; (3) **vérifier** : lisibilité à 16 px et en noir/blanc, zone de protection, deux variantes (clair/sombre). Génération vectorielle directe : **OmniSVG** (Apache-2.0, poids 1.1 8 Md, MMSVG-2M, article 2504.06263 [LU API/HF]) et **StarVector-8b** (Apache-2.0 [LU HF]) à bancher, car ils produisent du SVG structuré mais sur des icônes plus que des marques ; SVGThinker (2509.24299), LayerTracer (2502.01105), NeuralSVG (2501.03992) [RÉSUMÉ]. Pour un logo texte : composer avec une police OFL, c'est plus fiable qu'un modèle.

### B1.4 Compétence « accroches »

Écrite dans nos mots : fichier `server/nexora/competences/accroches.md` qui force un raisonnement en deux temps. Cadre **AIDA** (attirer l'attention, susciter l'intérêt, faire naître le désir, appeler à l'action) pour les supports qui se lisent d'un coup d'œil (affiche, accroche-porte) ; cadre **PAS** (nommer le problème, l'amplifier, offrir la solution) pour les messages courts à bénéfice clair (publicité, courriel). Sortie : 5 variantes sur 3 angles (gain, preuve, urgence honnête), chaque variante avec son nombre de mots (6 à 9 sur accroche-porte, ≤ 40 caractères sur bannière) vérifié **par le code**, sa langue (fr-CA / en), et une ligne « pourquoi ça marche ». Le juge (`qwen/qwen3.8-27b`) note clarté, bénéfice, absence de superlatifs invérifiables ; aucune affirmation chiffrée sans source dans le kit de marque. Les skills de rédaction déjà installés (copywriting, marketing-psychology) servent de matériel, pas d'API.

## B2. Mode Cours / format court

### B2.1 Pipeline

`source` (texte, diapositives, document, enregistrement d'écran, idée) → **plan de leçon** (objectifs, public, chapitres) → **script** par diapositive → **narration TTS avec horodatage des mots** → **scènes** → montage → sous-titres → chapitres → sorties 16:9 et 9:16.

- **Narration synchronisée** : Kokoro (Apache-2.0, léger) ; l'article 2505.02966 (« Generating Narrated Lecture Videos from Slides with Synchronized Highlights ») aligne phrases et zones de diapositive par distance de Levenshtein ou analyse LLM avec TTS horodaté et rapporte F1 > 92 % pour l'alignement LLM [RÉSUMÉ] : modèle pour les surlignages animés.
- **Cadre agentique** : PresentAgent (2507.04036, évaluation par VLM) et PresentAgent-2 (2605.11363, recherche + médias + mode discussion à deux voix) ; **Paper2Video / PaperTalker** (2510.05096, dépôt `showlab/Paper2Video`, métriques *PresentQuiz* et *IP Memory*, diapositives avec recherche d'arbre de mise en page, curseur, sous-titres, parole, tête parlante) [RÉSUMÉ]. À reprendre : la métrique **PresentQuiz** comme contrôle qualité automatique (poser des questions de compréhension sur la transcription seule et mesurer le score) ; elle coûte quelques jetons.
- **Scènes** : diapositives → images (mise en page déterministe HTML) ou compositions HyperFrames ; schémas animés Motion Canvas (MIT) ; capture d'écran avec zoom automatique (suiveur de curseur) [RÉSUMÉ, pas de dépôt retenu].
- **Avatar / tête parlante** (option) : Wan2.2-S2V-14B et InfiniteTalk (Apache-2.0 tous deux [LU HF]) pour parole→vidéo ; LatentSync 1.6 (OpenRAIL++, doublage labial sur vidéo existante [LU HF]) ; MuseTalk (licence NOASSERTION) [RÉSUMÉ]. Avatars réalistes = risque de mauvais usage : indicateur de consentement du sujet obligatoire dans le projet. Le fondateur tranche le reste.
- **Chapitres** : LLM sur transcription → liste `{t, titre}` (format de chapitres de plateforme) ; **qualité** : titres ≤ 6 mots, premier chapitre à 0:00.

### B2.2 Modèle de données

```ts
interface Cours { objectifs: string[]; public: string; langue: 'fr'|'en';
  chapitres: { id; titre; t0?: number }[];
  diapos: { id; chapitreId; source: 'image'|'html'|'ecran'; contenu: string; notes: string }[];
  narration: { diapoId; texte; voix: VoixId; mots: { w: string; t0: number; t1: number }[] }[];
  surlignages: { diapoId; cible: BoiteNormalisee; t0; t1 }[];
  quiz?: { q: string; r: string }[]; avatar?: { actif: boolean; consentement: boolean } }
```
UX : trois colonnes (plan, diapositive, script avec mots surlignés pendant la lecture), un bouton « Essayer 30 s », devis par minute de vidéo, sortie MP4 + sous-titres + chapitres + version 9:16 recadrée. Réutilise : sous-titres au mot, `montage_auto`, Producteur (script), Mode Studio (retouche).

## B3. Mode Long métrage

S'appuie sur le **squelette de projet long déjà réel** (scénario → plans, bible, estimation, lots, Mode Studio ; 4 plans dont 2 tournés ; test d'échelle de 1 080 plans — ETAT.md) et sur les 12 techniques de `15` (banque d'entités avec états, mémoire d'images clés, FilmDSL) et `16`.

### B3.1 Modèle de données

```ts
interface Film { titre; logline; format: '2.39:1'|'16:9'|'9:16'; fps: 24;
  actes: Acte[]; bible: Bible; planification: Planif; assemblage: EditPlanRef }
interface Acte { id; sequences: Sequence[] }
interface Sequence { id; scenes: Scene[] }
interface Scene { id; slug: string /* INT. CUISINE - NUIT */; lieuId; entites: EntiteId[]; enjeu: string;
  plans: Plan[]; etat: 'ecrit'|'storyboard'|'brouillon'|'final'|'approuve' }
interface Plan { id; valeur: 'TGP'|'PG'|'PM'|'GP'|'ECU'; angle; mouvement: CameraMove /* 16 existants */;
  duree: number; action: string; dialogue?: { entite; texte; voix };
  etats: Record<EntiteId, EtatEntite>;    // tenue, blessure, heure, météo… (rapport 15 T1)
  prises: Prise[]; /* brouillon 768p turbo puis final */ cout: Devis }
interface Bible { personnages: Fiche[]; lieux: Fiche[]; accessoires: Fiche[]; style: StyleVisuel; refs: ImageRef[] /* pré-générées */ }
```
Entrées/sorties : import et export **Fountain** (`fountain-js`, MIT, 1.2.4 [LU npm]) → scènes, personnages, dialogues ; export vers Premiere/DaVinci (déjà : `projetExport` et OTIO Apache-2.0).

### B3.2 Planification des heures de GPU

Le coût d'un plan est connu à l'avance par les mesures (`08`, `10` : plan de 5 s 1344×768 avec son ≈ 290 s sur la RTX 5090, 344 s sur le GB10 ; brouillon ≈ 28,7 s contre 129 s la finale). Le planificateur est du **code**, pas un LLM : file de lots avec priorité (1. images de référence des entités, 2. brouillons de tous les plans, 3. finals des plans approuvés, 4. reprises), affectation GB10/RTX 5090 selon la recette portée, estimation « fin dans X h » et coût en crédits, reprise après redémarrage, plafond par jour, et **jamais plus de N plans non validés en vol** (on valide un brouillon avant de dépenser le final).

### B3.3 Interface

Tableau des scènes (colonnes : écrit, storyboard, brouillon, final, approuvé), carte de plan avec vignette, états des personnages en frise (continuité), jauge de coût et d'heures, vue « bobine » (assemblage Mode Studio), panneau « continuité » alimenté par le juge (tenue différente d'un plan à l'autre, lieu, heure). Cinq actions : *Écrire* (scénario), *Découper* (plans), *Tourner brouillons*, *Approuver*, *Monter*.

---

# Partie C — Tableau des composants

Colonnes : nom, URL, licence (fait), maturité, ce qu'on prend, où ça se branche. Étiquette en dernière colonne.

| # | Nom | URL | Licence | Maturité | On prend | Branchement | |
|---|---|---|---|---|---|---|---|
| 1 | FreeCut | github.com/walterlow/freecut | MIT | 2 305 ★, push 2026-10-29 | éditeur, 52 effets GPU, 17 transitions, RIFE, Anime4K, Lottie | `mode-studio/` (déjà) | LU |
| 2 | gl-transitions | github.com/gl-transitions/gl-transitions | MIT (2 BSD) | 2 221 ★, push 2026-11-02, npm 2.2.0 | ~100 transitions WGSL + compatibilité | `infrastructure/gpu-transitions/registry.ts` | LU |
| 3 | HyperFrames | github.com/heygen-com/hyperframes | Apache-2.0 | 77 847 ★, push 2026-11-03 | HTML → MP4 déterministe, ~450 blocs | rendu serveur de calques/cartons ; mode Cours | LU |
| 4 | dotLottie web | github.com/LottieFiles/dotlottie-web | MIT | v0.82.1 | animations vectorielles | `lottie` du compositeur | LU |
| 5 | tsParticles | github.com/tsparticles/tsparticles | MIT | 9 069 ★, v4.5.1 | pluie, neige, étincelles | famille `calque` | LU |
| 6 | Rive wasm | github.com/rive-app/rive-wasm | MIT | 1 018 ★ | animations interactives | option | RÉSUMÉ |
| 7 | RIFE | github.com/hzwer/ECCV2022-RIFE | MIT | 5 648 ★ | interpolation (ralentis) | déjà en ONNX | LU |
| 8 | Anime4K / SeedVR2 | HF `ByteDance-Seed/SeedVR2-3B`,`-7B` | Apache-2.0 | 23-46 k téléch. | agrandissement/restauration serveur | P1 | LU |
| 9 | SAM 2 | github.com/facebookresearch/sam2 | Apache-2.0 | 20 095 ★ | masque suivi par points/boîtes | `v2v`, calque | LU |
| 10 | SAM 3 / 3.1 | github.com/facebookresearch/sam3 | « SAM License » (Meta, 19/11/2025) | 12 186 ★, 3.1 du 27/03/2026 | masque suivi **par texte** (« le ciel ») | job serveur P1 (Python ≥ 3.12, CUDA ≥ 12.6) | LU |
| 11 | BiRefNet | HF `ZhengPeng7/BiRefNet` | MIT | 829 k téléch. | détourage par image | plaques sur vert, logos | LU |
| 12 | MatAnyone | github.com/pq-yang/MatAnyone | S-Lab 1.0 non commercial | 1 639 ★ | – | **exclu** (banc interne seulement) | LU |
| 13 | RobustVideoMatting | github.com/PeterL1n/RobustVideoMatting | GPL-3.0 | 9 586 ★, push 2024-04 | – | écarté | LU |
| 14 | VideoMaMa | github.com/cvlab-kaist/VideoMaMa | NOASSERTION | 547 ★ | matting guidé par masque SAM | à surveiller (licence à lire) | RÉSUMÉ |
| 15 | VACE (Wan2.1) | github.com/ali-vilab/VACE ; HF `Wan-AI/Wan2.1-VACE-14B` | Apache-2.0 | 4 045 ★, push 2025-10 | échange, extension, retrait, déplacement | `v2v` P2 | LU |
| 16 | DiffuEraser | github.com/lixiaowen-xw/DiffuEraser | Apache-2.0 | 706 ★, push 2025-04 | retrait d'objet | `v2v` P2 | LU |
| 17 | ProPainter | github.com/sczhou/ProPainter | S-Lab 1.0 non commercial | 7 033 ★ | – | **exclu** | LU |
| 18 | MiniMax-Remover | HF `zibojia/minimax-remover` | poids CC-BY-NC-4.0 | – | – | **exclu** | LU |
| 19 | Lucy Edit Dev | HF `decart-ai/Lucy-Edit-Dev` | licence non commerciale Decart | – | – | **exclu** | LU |
| 20 | Qwen-Image-Edit-2511 | HF `Qwen/Qwen-Image-Edit-2511` | Apache-2.0 | 210 k téléch. | aperçu fixe et image clé éditée | bulle P2, « Montre-moi » | LU |
| 21 | Qwen-Image-Layered | github.com/QwenLM/Qwen-Image-Layered | Apache-2.0 | 2 166 ★ | image → calques RGBA | mode Marketing | LU |
| 22 | Wan2.2 / S2V-14B | github.com/Wan-Video/Wan2.2 | Apache-2.0 | 18 334 ★ | parole → vidéo | mode Cours (avatar) | LU |
| 23 | InfiniteTalk | HF `MeiGen-AI/InfiniteTalk` | Apache-2.0 | 72 k téléch. | tête parlante longue durée | mode Cours | LU |
| 24 | LatentSync 1.6 | HF `ByteDance/LatentSync-1.6` | OpenRAIL++ | 361 k téléch., push 2025-06 | doublage labial | doublage/localisation | LU |
| 25 | Wan-Alpha | github.com/WeChatCV/Wan-Alpha | code MIT (poids : à vérifier) | 425 ★ ; art. 2509.24979 | plaques RGBA | banc RTX 5090 | LU (dépôt) / RÉSUMÉ |
| 26 | MMAudio | github.com/hkchengrex/MMAudio | code MIT, poids CC-BY-NC-4.0 | 2 303 ★ ; ~6 Go VRAM | bruitage vidéo→audio | banc interne | LU |
| 27 | HunyuanVideo-Foley | github.com/Tencent-Hunyuan/HunyuanVideo-Foley | « tencent-hunyuan-community » | 1 086 ★ | bruitage | à lire avant usage | LU (fiche) |
| 28 | Stable Audio Open + tools | HF `stabilityai/stable-audio-open-1.0` | « stable-audio-community » ; outils MIT | – | SFX courts | P1 | LU |
| 29 | Demucs | github.com/facebookresearch/demucs | MIT | **archivé** 2024-04 | séparation voix/musique | P1 | LU |
| 30 | faster-whisper / WhisperX | github.com/SYSTRAN/faster-whisper ; m-bain/whisperX | MIT / BSD-2 | 26 427 / 25 036 ★ | mots horodatés | déjà | LU |
| 31 | Kokoro-82M | HF `hexgrad/Kokoro-82M` | Apache-2.0 | 11 M téléch. | narration légère | mode Cours | LU |
| 32 | Chatterbox | github.com/resemble-ai/chatterbox | MIT | 27 518 ★, push 2026-07 | voix clonée (avec consentement) | option | LU |
| 33 | VibeVoice-1.5B / Dia | HF `microsoft/VibeVoice-1.5B` ; `nari-labs/Dia-1.6B` | MIT / Apache-2.0 | – | dialogues longs | mode Cours/film | LU |
| 34 | F5-TTS | github.com/SWivid/F5-TTS | code MIT, poids CC-BY-NC | 15 504 ★ | – | exclu | LU |
| 35 | Penpot (+ plugins) | github.com/penpot/penpot | MPL-2.0 | 62 003 ★ | éditeur de design auto-hébergé | option mode Marketing | LU |
| 36 | Fabric.js | github.com/fabricjs/fabric.js | MIT | 31 534 ★ | éditeur de `SpecConception` | mode Marketing | LU |
| 37 | Konva | github.com/konvajs/konva | NOASSERTION (à lire) | 14 911 ★ | alternative | idem | LU (API) |
| 38 | pdf-lib | github.com/Hopding/pdf-lib | MIT | v1.17.1, push 2024-07 | imposition, métadonnées | sorties imprimeur | LU |
| 39 | Typst | github.com/typst/typst | Apache-2.0 | 56 957 ★ | mise en page de documents longs | brochures | LU |
| 40 | WeasyPrint / Paged.js | github.com/Kozea/WeasyPrint ; pagedjs/pagedjs | BSD-3 / MIT | 9 756 / 1 558 ★ | CSS Paged Media (repères, fond perdu) | alternative à Chromium | LU (API) |
| 41 | vtracer | github.com/visioncortex/vtracer | MIT | 7 446 ★ | raster → SVG | module Logo | LU |
| 42 | OmniSVG 1.1 | github.com/OmniSVG/OmniSVG ; HF `OmniSVG/OmniSVG1.1_8B` | Apache-2.0 | 2 655 ★, push 2026-03 | SVG structuré | banc module Logo | LU |
| 43 | StarVector-8b | HF `starvector/starvector-8b-im2svg` | Apache-2.0 | 1,6 k téléch. | image → SVG | banc | LU |
| 44 | zxing-js | github.com/zxing-js/library | Apache-2.0 | 2 944 ★ | contrôle de QR | contrôle préliminaire | LU |
| 45 | fountain-js | npm `fountain-js` | MIT | v1.2.4 | scénario Fountain | mode Long métrage | LU |
| 46 | OpenTimelineIO | github.com/AcademySoftwareFoundation/OpenTimelineIO | Apache-2.0 | 2 053 ★ | échange NLE | export | LU |
| 47 | MLT | github.com/mltframework/mlt | LGPL-2.1 | actif | XML d'échange, rendu `melt` | secours serveur | LU |
| 48 | Motion Canvas | github.com/motion-canvas/motion-canvas | MIT | 19 659 ★ | schémas animés | mode Cours | LU |
| 49 | Remotion | github.com/remotion-dev/remotion | « Remotion License » | 70 180 ★ | – | écarté du cœur (rapport 02) | LU |
| 50 | Vera (Netflix/Caltech) | arxiv.org/abs/2606.23610 | article CC BY-NC-SA ; code non vérifié | juin 2026 | principe édition = couche + alpha | modèle de recomposition | LU |
| 51 | VFXMaster | arxiv.org/abs/2510.25772 | n/c (« will release ») | oct. 2025 | effets par référence | surveiller | LU |
| 52 | CreatiPoster | arxiv.org/abs/2506.10890 ; github.com/graphic-design-ai/creatiposter | à lire | 2025 | protocole JSON de calques | `SpecConception` | LU |
| 53 | Aurora | arxiv.org/abs/2605.18748 | n/c | mai 2026 | agent VLM → plan d'édition | modèle de la bulle | RÉSUMÉ |
| 54 | OpenVE-3M | arxiv.org/abs/2512.07826 | n/c | déc. 2025 | données et banc d'édition par instruction | évaluation | RÉSUMÉ |
| 55 | Paper2Video / PresentAgent | arxiv.org/abs/2510.05096 ; 2507.04036 | n/c | 2025 | cours à partir de documents ; PresentQuiz | mode Cours | RÉSUMÉ |

---

# Partie D — Feuille de route classée (20 jalons, impact × effort)

Impact 1-5, effort en jours-personne approximatifs (un développeur, avec la base actuelle). Ordre = rapport impact/effort décroissant, avec dépendances respectées.

| Rang | Jalon | Impact | Effort | Dépend de | Pourquoi maintenant |
|---|---|---|---|---|---|
| 1 | **Bulle d'effet v0** : « Effet IA ici… » + recette v0 (`gpu_stack`, `transition`, vitesse constante, texte, volume) via le registre existant | 5 | 3-5 | – | tranche minimale (§E) |
| 2 | Catalogue du registre → JSON Schema avec bornes + 30 recettes canon et banc d'évaluation | 5 | 2 | 1 | rend le LLM fiable |
| 3 | Aperçu direct, Avant/Après, « plus fort/plus doux », recette gardée sur l'élément | 4 | 2-3 | 1 | itération |
| 4 | Import de gl-transitions (WGSL) | 4 | 2-3 | – | 100 transitions gratuites |
| 5 | Rampe de vitesse (segments + RIFE) | 4 | 3 | 1 | demande explicite du fondateur |
| 6 | Compétence « accroches » (AIDA/PAS) + juge | 3 | 2 | – | gain marketing immédiat |
| 7 | Calques procéduraux : pluie, neige, étincelles (tsParticles) + Lottie | 4 | 3-4 | 1 | effets populaires sans GPU |
| 8 | Plaques sur noir (H3/Qwen) + mélange écran, devis P2 | 4 | 4 | 1 | éclats, fumée, flammes |
| 9 | **Kit de marque** partagé (JSON, UI, injection dans Producteur et Imprimés) | 5 | 5 | – | socle des modes |
| 10 | Mode Marketing v1 : brief → `SpecConception` → moteur existant → PDF fond perdu (carte, flyer, accroche-porte) | 5 | 8-10 | 9 | valeur commerciale directe |
| 11 | Masques SAM 3 par texte (job serveur, piste de masque) | 5 | 5-7 | – | débloque ciel, retrait, détourage |
| 12 | Remplacement de ciel (masque + plaque Qwen + raccord de teinte) | 4 | 4 | 11 | effet à fort effet « wow » |
| 13 | Retrait d'objet (SAM 3 + DiffuEraser/VACE, fenêtre ≤ 81 images, recomposition par masque) | 5 | 6-8 | 11 | demande explicite |
| 14 | Bruitage : bibliothèque CC0 + recherche par texte + ducking (MMAudio en banc) | 4 | 4 | 1 | son = moitié de l'effet |
| 15 | Mode Cours v1 (Kokoro mots horodatés, scènes, sous-titres, chapitres, PresentQuiz) | 4 | 8 | 9 | marché formation |
| 16 | Module Logo (Qwen → vtracer → nettoyage ; banc OmniSVG) | 3 | 5 | 9 | demande explicite |
| 17 | Mode Long métrage : modèle `Film`, import Fountain, tableau d'états, planificateur GPU | 5 | 8-10 | squelette actuel | vision « film » |
| 18 | Imposition, contrôle préliminaire, CMJN/PDF-X (épreuve) | 3 | 4 | 10 | confiance imprimeur |
| 19 | Plaques RGBA natives (Wan-Alpha) sur RTX 5090 | 3 | 5 | 8 | si licence des poids OK |
| 20 | Laboratoire de shaders (LLM → WGSL sandboxé) | 3 | 8+ | 1-3 | R&D, risque élevé |

---

# Partie E — La plus petite tranche de la bulle d'effet (livrable en quelques jours)

**Objectif** : clic droit → phrase → effet GPU appliqué à la tête de lecture, annulable d'un pas, gratuit. Aucun nouveau modèle, aucun GPU.

1. **UI** (≈ 1 j) : dans `timeline-track.tsx`, ajouter « Effet IA ici… » au menu de vide de piste (le menu à chargement paresseux existe) et un menu équivalent dans `item-context-menu.tsx` ; popover avec champ, durée (par défaut 2 s, ou la durée du clip), état « réflexion », bouton Appliquer/Annuler.
2. **Route serveur** (≈ 1 j) : `POST /api/nexora/effet` dans `app/server/nexora/`, rôle LLM `effets` (GLM), entrée : phrase, `t`, `fps`, élément, catalogue ; sortie contrainte par un schéma (`EffectRecipe` v0 : `gpu_stack`, `transition`, `volume`, `texte`). Validation Zod + bornes + au plus 2 tours de correction.
3. **Catalogue** (≈ 0,5 j) : script qui lit `infrastructure/gpu-effects/registry.ts` et émet `catalogue-effets.json` (id, libellé, paramètres, min/max/défaut) ; test qui échoue si un effet du registre n'est pas dans le catalogue.
4. **Traduction** (≈ 1 j) : étendre `features/nexora/commandes.ts` : recette → opérations FreeCut existantes (`addItem` de type `adjustment` couvrant `[t, t+d]` sur une piste au-dessus, puis `addEffect`/`addKeyframe`), le tout dans un seul pas d'annulation. Les opérations existent déjà [LU `edit-op-support.ts`].
5. **Évaluation** (≈ 1 j) : 30 phrases françaises (« look film 1980 », « VHS », « onde de choc », « halo doux », « glitch », « noir et blanc contrasté », « flou de mouvement rapide »…) → recette valide dans ≥ 90 % des cas, identifiants toujours dans le catalogue, 0 appel hors liste ; rapport dans `docs/JOURNAL.md`.

**Critère de sortie** : sur un vrai projet, « look film des années 80 » à 3 min 22 s crée une couche d'ajustement de 2 s avec 4 effets, s'annule d'un Ctrl+Z, et le test d'évaluation passe. Étape suivante immédiate : rampe de vitesse (jalon 5) et Avant/Après (jalon 3).

---

# Partie F — Risques

| Risque | Gravité | Parade |
|---|---|---|
| Licences non commerciales sur les modèles les plus performants (MatAnyone, ProPainter, MMAudio-poids, MiniMax-Remover, Lucy Edit, F5-TTS) | haute | colonne « Licence » par brique ; interdiction de les lancer en production ; voies Apache/MIT d'abord ; relire la licence de chaque poids avant l'intégration (HunyuanVideo-Foley, Wan-Alpha, SAM License, VideoMaMa non lues en entier) |
| Hallucination de paramètres ou d'identifiants par le LLM | moyenne | catalogue généré depuis le registre, validation Zod, bornes, deux tours maximum, repli sur les 3 effets les plus proches |
| Injection par texte de transcription ou de légende | moyenne | étiquette « donnée », aucune action déclenchée par ce texte (règle du rapport 13) |
| `v2v` : fenêtre de 81 images, dérive de couleur, bords visibles | haute | recomposition par masque adouci, raccord de teinte et de grain, aperçu fixe, plan de secours « générer un autre plan » |
| Aperçu ≠ rendu final (WebGPU navigateur vs export) | moyenne | un seul moteur de rendu (risque R1 du rapport 13) ; test de parité sur 10 recettes |
| Charge sur deux GPU partagés (H3, Qwen, Music3 déjà) | moyenne | file unique et priorités du planificateur ; jobs de bulle P1 courts ; pas de job P2 sans devis validé |
| Portabilité aarch64 (GB10) des dépendances (SAM 3 : Python ≥ 3.12, CUDA ≥ 12.6) | moyenne | fiches de mesure et d'installation par brique avant promesse ; images de conteneur par brique |
| Dépassement de coût (devis faux) | haute | devis calculé par le code à partir de mesures réelles, plafond par bulle et par jour |
| CMJN/PDF-X promis mais mal tenu (orange hors gamme) | moyenne | message explicite « épreuve conseillée », contrôle préliminaire, ne pas promettre la fidélité couleur |
| Avatars et voix clonées | haute | indicateur de consentement obligatoire, filigrane si le moteur en propose, pas de clonage sans consentement du sujet |
| Dérive de périmètre (trop de modes à la fois) | haute | une tranche par mode, mêmes briques (kit de marque, devis, Producteur) ; le mode Long métrage reste en lecture du squelette actuel |
| Bulle peu découvrable | moyenne | raccourci clavier, puces contextuelles, entrée aussi dans le panneau Assistant |
| Qualité de la littérature récente (articles de 2026 non évalués par les pairs, codes non publiés) | moyenne | rien dans la feuille de route ne dépend d'un code « à venir » ; VFXMaster, Vera, Aurora, Wan-Alpha++ en veille |

## Ce que cette étude ne permet pas de dire

- Aucun modèle n'a été exécuté ; les durées et mémoires viennent des dépôts et de l'article Vera, pas du GB10 ni de la RTX 5090. Les 4 chiffres de VACE/Vera cités sont ceux d'un tableau de comparaison sur A100.
- Les licences de poids marquées « à lire » n'ont pas été ouvertes.
- Les motifs d'interface (§A3) sont issus de la connaissance générale des produits, pas d'une relecture de leurs pages aujourd'hui.
- Aucune évaluation humaine de qualité des effets ; le banc de 30 recettes (§E) est la première mesure.
