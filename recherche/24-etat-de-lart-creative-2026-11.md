# 24 — État de l'art de Creative, novembre 2026 : concurrents, libre, littérature (03/11/2026)

**Pour qui** : le fondateur et les agents qui construisent Creative. Ce document résume, tranche et date ; le détail sourcé (près de 300 liens) est dans les trois annexes `recherche/24-annexes/`. Il prolonge `03`, `07`, `12`, `13`, `15`, `16`, `17`, `18`, `22` sans les refaire. Le plan d'action qui en découle : `docs/backlog/creative-triple-a.md`.

## 0. Les dix constats

1. **MiniMax H3 reste le meilleur générateur vidéo à poids ouverts du monde.** Arène Artificial Analysis (T2V v2.1 avec audio, lue le 03/11/2026) : H3 768p **3e, 1160 Elo**, devant Seedance 2.5 (5e, 1155), Gemini Omni Flash 1.1 (10e), Veo 3.1 (22e) et loin devant le premier autre modèle ouvert, MAGI-2 Preview (15e, 1041), puis LTX-2.5 (25e-26e, ≈ 940). Seuls Wan 3.0 (1172, poids non publiés) et Utopai X (1169, fermé) sont devant. Notre choix « H3 seul » est confirmé. [arène](https://artificialanalysis.ai/video/leaderboard/text-to-video)
2. **La seule chose qui « bat H3 en local » est un dérivé de H3 : Pika H3 Flex**, publié le 29/10/2026 en poids ouverts **non protégés**, sous **la même licence communautaire que H3** ([Hugging Face](https://huggingface.co/Pika-Labs/Pika-H3-Flex), métadonnées lues le 03/11 : `gated: false`, `license_name: minimax-h3-community-license-agreement`). Pika annonce 6 étapes au lieu de 50, des plans jusqu'à 15 s, et une préférence humaine supérieure à H3 sur l'anatomie, la composition et la synchro audio ([billet technique](https://pika.art/blog/pika-h3-flex-research), affirmation de l'éditeur, non reproduite). Surtout : il existe des **adaptateurs LoRA ComfyUI** (`comfy/loras/pika_h3_flex_{fl2va,ref2va}_comfy_bf16.safetensors`, rangs 128/384) qui se posent **sur les points de contrôle FL2VA et Ref2VA que pc1 possède déjà**. C'est le gain le plus rentable de tout ce rapport : vitesse ×3 à ×4 attendue sur `h3-max` sans changer de moteur ni de licence. **À mesurer en premier** (aucun rendu de bout en bout n'est garanti par Pika pour le chemin ComfyUI).
3. **Le marché est devenu « agrégateur + agent dans Claude/ChatGPT ».** Higgsfield, OpenArt, Krea, Magnific, Hedra, Leonardo, Autodesk Flow agrègent les mêmes moteurs (Seedance 2.5, Kling 4.0, H3, Wan 3.0, Veo) ; la différence se fait sur les **recettes**, les **références persistantes**, le **brouillon → master**, et le **MCP** (Higgsfield, OpenArt, Runway, Pika, Krea, Magnific, Hedra, Vidu, Meshy ont un MCP officiel). Sora a quitté le marché (API retirée le 24/09/2026, [OpenAI](https://developers.openai.com/api/docs/deprecations)) ; Freepik s'appelle Magnific depuis le 28/04/2026 ([Magnific](https://www.magnific.com/freepik)) ; Moonvalley a fermé son libre-service.
4. **Prix par seconde de vidéo (API, 1080p sauf mention)** : Pika H3 Flex 0,035 $ (lancement) / 0,07 $ (régulier) ; Runway Gen-4.5 0,12 $ (720p natif) ; MiniMax H3 0,13 $ (2K) ; LTX-2.5 Pro 0,17 $ ; Luma Ray 3.2 0,24 $ ; Higgsfield Cinema 4.0 0,46 $ (720p API) et ≈ 0,78 $ en application ; Seedance 2.5 0,57 $. **Notre coût complet sur nos GPU est d'environ 0,002 à 0,008 CAD par seconde produite**, 0,006 à 0,025 CAD prises ratées comprises (§2.4, hypothèses d'amortissement écrites) : nous pouvons être **moins chers que Pika et plus généreux que tout le monde** sur les brouillons.
5. **L'écart produit avec Higgsfield et OpenArt n'est plus la génération, c'est l'édition et la voix** : édition de vidéo existante (retrait, remplacement, restyle, relight), voix expressive et lip-sync sur audio fourni, transfert de mouvement, recettes illustrées par centaines, et acquisition par MCP distant. Tous les concurrents de la colonne « studio » les ont ; nous non (§1.3).
6. **Le « LLM qui booste tout » est mesuré dans la littérature, et le gain vient du retour sur la vidéo, pas d'un prompt plus long.** RAPO++ : +1,8 à +3,7 points VBench ; VPO : « multiple objects » 45,7 → 75,7 sur CogVideoX-5B ; Prompt-A-Video : esthétique en hausse mais **mouvement en baisse** (0,70 → 0,54). Pour H3, la bonne architecture est un **compilateur par mode** (T2VA, I2VA, FL2VA, Ref2VA ont des dialectes différents dans le guide officiel) + quelques règles distillées à la TIDE, jugées sur le rendu (§3).
7. **Les VFX « infinis » s'assemblent en libre, mais par spécialistes, pas par un modèle magique** : Wan2.2-Fun-Control / VACE-Fun (profondeur, pose, fond, retouche), Wan-Move (trajectoires de dragons et de vaisseaux), Wan-Alpha v2 (éléments RGBA), LiveLight / Relit-LiVE (lumière d'explosion et de sabre), FlashVSR+ (export 1080p/4K), plus notre détourage SAM 2.1 déjà livré. Aucun n'est mesuré chez nous ; plusieurs ne tiennent que sur la GB10 (§4).
8. **Voix : le problème « trop smooth » est d'abord un problème de direction, ensuite de modèle.** Candidats locaux à licence permissive avec contrôle d'émotion et français : **Qwen3-TTS 1.7B** (Apache-2.0, VoiceDesign/CustomVoice), **CosyVoice 3** (Apache-2.0, instructions d'émotion, français), **Chatterbox Multilingual** réglé « dramatique » (MIT, déjà sur pc5). Drama 3 (déjà mesuré en local par l'équipe voix) reste le meilleur clone, licence « Community » (§6).
9. **Musique : Music3 tient la comparaison publiée la plus récente** (YuE2, 192 demandes : meilleur PER, SongBench 6,28 contre 6,73 pour YuE2 et 6,01 pour ACE-Step 1.5). ACE-Step 1.5 (MIT) est le seul complément utile, pour imposer BPM, sections et réparer un passage (§7).
10. **Blender piloté par agent est utile mais pas indispensable au triple A.** Les bancs 2025-2026 (BlenderGym, 3DHarnessBench, BlenderWorld) montrent que les agents échouent encore sur des opérations simples ; le bon usage est un **travailleur Blender à gabarits** (prévisualisation, trajectoire caméra, passes de profondeur pour guider la vidéo), pas un « Blender conversationnel » (§8). FilmCraft : prendre des contrats, pas du code (§9).

## 1. Concurrents (pages officielles, consultées le 03/11/2026)

Détail, calculs et 106 sources datées : `24-annexes/A-concurrents.md` (rapport délégué à GPT-6.1 Sol avec recherche web, contrôlé : quatre affirmations recoupées par moi le 03/11 : retrait de Sora, renommage Magnific, prix Pika H3 Flex, rang H3 dans l'arène ; 83 des 85 dépôts GitHub cités existent).

### 1.1 Qui fait quoi

| Concurrent | Moteur(s) | Ce qui le rend simple | Ce qui le rend lourd |
|---|---|---|---|
| **Higgsfield** | DoP (maison), Cinema Studio 4.0 = Seedance 2.5, + Kling 4.0, H3, Wan 3.0, LTX 2.5 | vignettes de mouvements, références `@`, réglages sur « Auto », skills Claude (Katana, Ad Multiplier, Content Factory) | profusion d'espaces et de moteurs, facturation app/API distincte |
| **OpenArt** | agrégateur (Seedance, Kling, Wan, LTX, Omni) ; VFX via Beeble SwitchX | entrée par résultat (film, UGC, pub), Character Builder, VFX avant/après | choisir le moteur, préparer les références |
| **Kling** | Kling 4.0 (15/10/2026), 3 à 30 s, 15 références, 10 images clés | un parcours texte/image/références, images clés sur une chronologie | limites croisées des médias |
| **Runway** | Gen-4.5 (720p natif), Aleph 2.0 (édition), Act-Two, Characters, GWM Worlds 2 | prévisualiser l'édition sur une image avant la vidéo | formats et suppléments multiples |
| **Luma** | Ray 3.2, Luma Agents | images clés, modification de vidéo | prix non linéaire selon la durée |
| **Pika** | **Pika H3 Flex** (dérivé de H3, poids ouverts), Pika 2.5 | applications par tâche, brouillon puis finition, timeline dans ChatGPT | distinguer Flex, tiers et facturation |
| **MiniMax** | H3 (poids ouverts 03/08/2026), Hailuo 2.3, MiniMax Design (agent, canevas) | brief → exécution par l'agent | application de bureau |
| **Google** | Flow (Veo 3.1 + Gemini Omni Flash 1.1) | chat dans le projet, essai en 360p puis agrandissement | conditions régionales |
| **Seedance / Dreamina** | Seedance 2.5 (30 s, 30 images + 10 vidéos + 10 sons de référence, édition par horodatage) | studio par usage | régions, portefeuilles distincts |
| **LTX Studio** | LTX-2.5 Fast/Pro (jusqu'à 4K) + tiers | scénario/storyboard comme entrée | dépend du plan |
| **Krea** | agrégateur, Krea 3 = image | agent depuis un brief, « apps » qui cachent les nœuds, devis MCP avant exécution | graphes complexes |
| **Magnific (ex-Freepik)** | agrégateur | un Flow devient quelques champs et un bouton | coût = somme des nœuds |
| **Leonardo** | Motion 2.0 + tiers | Blueprints | coûts variables |
| **Hedra** | Character 3 (audio → avatar) | portrait + audio | audio propre à préparer |
| **Vidu** | Q4 Preview, S2 (temps réel) | gabarits, voix attachées aux personnages | familles et variantes |
| **Moonvalley** | Marey 1.5 | dessiner la trajectoire | partenariats seulement |
| **Meshy / Tripo** | 3D (Meshy 7.1, N1 ; Tripo H3.1, P2) | photo → modèle rigué, export Blender/Unity | décisions de production 3D |
| **Autodesk Flow Studio** | Wonder 3D + tiers | vidéo réelle → personnage CG sans marqueurs | finition dans un logiciel 3D |
| **Sora** | retiré | — | — |

### 1.2 Matrice contre Creative aujourd'hui

✔ documenté ; ◐ partiel ; ✘ absent ; ? non vérifié. Colonne Creative : lue dans `docs/ETAT.md` du 04/11 et le code de `app/` (pages `Creer`, `Director`, `Cast`, `Marketing`, `Object`/Relief, `Detourage`, Mode Studio). La matrice complète des 20 concurrents est dans l'annexe A.

| Fonction | **Creative** | Higgsfield | OpenArt | Kling | Runway | Pika | Google Flow | Seedance |
|---|---|---|---|---|---|---|---|---|
| Moteur vidéo de classe mondiale | ✔ H3 (3e de l'arène), hébergé chez nous | ✔ | ✔ (tiers) | ✔ | ✔ | ✔ | ✔ | ✔ |
| Presets / recettes illustrées | ◐ 8 modèles prêts, 16 caméras, 26 recettes d'effets | ✔ centaines | ✔ | ? | ✔ | ✔ | ? | ✔ |
| Contrôle caméra | ✔ 16 mouvements à vignettes | ✔ | ◐ | ✔ | ◐ | ✔ | ◐ | ✔ |
| Personnages / éléments cohérents | ✔ `@` Ref2VA (2 plans prouvés) | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ |
| Avatar parlant / lip-sync sur audio fourni | ✘ (H3 parle seul) | ✔ | ◐ | ✔ | ✔ | ✔ | ◐ | ✔ |
| Voix TTS / clonage / doublage | ✘ dans l'interface (Kokoro, Chatterbox sur pc5) | ✔ | ◐ | ? | ✔ | ✔ | ◐ | ? |
| Musique générée | ✔ Music3 | ✔ | ◐ | ? | ✔ | ✔ | ◐ | ◐ |
| Édition de vidéo existante (retrait, restyle, relight) | ✘ (sauf détourage et fond) | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ |
| Détourage vidéo pro (alpha 16 bits, EXR) | ✔ | ? | ◐ | ? | ✔ | ? | ? | ? |
| 3D exportable | ✔ Relief (5 formats) | ◐ | ◐ | ? | ? | ? | ? | ? |
| Montage multipiste | ✔ Mode Studio | ◐ | ◐ | ◐ | ◐ | ✔ | ◐ | ◐ |
| Agent qui planifie, chiffre et tourne | ✔ Producteur (devis par le code) | ✔ | ✔ | ? | ✔ | ◐ | ✔ | ? |
| Juge visuel automatique des prises | ✔ | ✘ | ◐ Smart Shot | ✘ | ✘ | ✘ | ✘ | ✘ |
| Brouillon → finale | ◐ brouillon ≠ même plan | ✔ | ✔ | ? | ✔ | ✔ | ✔ | ✔ Draft |
| MCP officiel | ◐ stdio local, 22 outils | ✔ | ✔ | ? | ✔ | ✔ | ? | ? |
| API publique | ✘ | ✔ | ? | ✔ | ✔ | ✔ | ✔ | ✔ |
| Impression (PDF fond perdu) et kit de marque | ✔ | ✘ | ✘ | ✘ | ✘ | ✘ | ✘ | ✘ |
| Hébergement souverain (Québec) | ✔ | ✘ | ✘ | ✘ | ✘ | ✘ | ✘ | ✘ |

### 1.3 Lecture

- **Nous menons** sur : juge visuel des prises, devis par le code avant toute dépense, 3D exportable, détourage pro, impression, souveraineté, et un moteur au niveau des meilleurs.
- **Nous sommes en retard** sur : édition de vidéo existante, voix et lip-sync, recettes illustrées, brouillon fidèle, API/MCP distant. Ce sont exactement les cinq lignes que les concurrents ont tous.
- **Personne** n'a de juge visuel systématique ni de devis exact avant dépense : c'est notre argument de confiance (« vous ne payez jamais une prise ratée »).

### 1.4 Les dix tendances (deux sources officielles chacune dans l'annexe A)
Studio dans Claude/ChatGPT par MCP ; brouillon → master comme étape commerciale ; références multimodales à rôles (identité, mouvement, caméra, son) ; plans de 30 s dirigés ; 4K par chemins de finition distincts ; édition de vidéo existante comme produit central (Aleph 2.0, SwitchX) ; temps réel pour avatars et flux ; mondes jouables (Genie, Higgsfield Playable) ; graphes cachés derrière des « apps » simples (Magnific Flows, Krea Apps) ; audio co-généré puis rendu éditable (pistes séparées de Pika Flex).

## 2. Génération vidéo à poids ouverts : qui bat H3, sur quelle machine

Détail des 15 familles (dates, paramètres, licence, mémoire, vitesses publiées) : `24-annexes/B-libre-video-vfx.md` (GPT-6.1 Sol, effort très élevé, recherche web ; contrôlé).

| Modèle | Licence | Audio | Arène AA (03/11) | Machine chez nous | Verdict |
|---|---|---|---|---|---|
| **MiniMax H3** (FastH3 V2 NVFP4, FL2VA, Ref2VA) | H3 Community | oui | **3e, 1160** | GB10 (rapide), 5090 (max) — en service | **garder** |
| **Pika H3 Flex** (LoRA sur H3, 6 étapes, 15 s) | H3 Community | oui | non classé | 5090 et GB10 attendus (mêmes bases que H3) | **mesurer en priorité 1** |
| Wan 3.0 | poids non publiés | oui | 1er, 1172 | — | surveiller une publication |
| MAGI-2 Preview (114B stockés) | Apache-2.0 | oui | 15e, 1041 | aucune (8 Hopper) | écarter |
| LTX-2.5 Fast/Pro (22B) | Community, accès protégé | oui | 25e-26e, ≈ 940 | GB10 probable | écarter comme générateur ; garder pour IC-LoRA (alpha) si l'accès est accordé (recherche/22) |
| Kandinsky 6 Lite/Pro (3B/29B, 06/10/2026) | MIT | oui | non classé | 5090 mesuré par l'éditeur : 44 s pour 5 s 480p (Lite) | tester comme brouillon audio-vidéo de secours |
| SANA-Video 2.0 4 étapes (4,5B) | Apache-2.0 | non | non classé | 5090 probable | tester pour brouillons muets ultra-rapides |
| Wan 2.2 (5B, A14B) | Apache-2.0 | non | — | 5090 (5B), GB10 (A14B) | **garder comme socle de contrôle VFX** (§4), pas comme générateur |
| HunyuanVideo 1.5, Helios, Cosmos 3, LongCat, Ovi, SkyReels V3, Motif 2B, Step-Video, Mochi, Waver | divers | surtout non | non classés ou loin | voir annexe B | surveiller ou écarter |

**Conclusion** : on ne change pas de moteur ; on **ajoute Pika H3 Flex** sur nos bases H3 (vitesse, durée 15 s, qualité annoncée) et des **spécialistes de contrôle et de retouche** autour.

### 2.4 Coût par seconde sur nos GPU (mesures internes + hypothèses écrites)

Hypothèses (à remplacer par les vraies valeurs comptables) : système RTX 5090 ≈ 5 500 CAD, DGX Spark ≈ 5 600 CAD, amortis sur 3 ans à 50 % d'occupation ; puissance 0,625 kW (5090 bridée à 475 W + reste du poste) et 0,2 kW (GB10) ; électricité **11,142 ¢/kWh** (tarif D, 2e tranche, au 1er avril 2026, [grille Hydro-Québec](https://www.hydroquebec.com/data/documents-donnees/pdf/grille-tarifaire.pdf)). Coût d'une seconde de GPU : ≈ **0,000136 CAD** (5090) et ≈ **0,000124 CAD** (GB10), dont 85 à 95 % d'amortissement.

| Recette (mesure) | Secondes GPU par seconde de vidéo | Coût CAD par seconde produite | Source |
|---|---|---|---|
| Brouillon ref2va 768×448 (28,7 s pour 5 s) | 5,7 | 0,0008 | JOURNAL 02/11 |
| FastH3 GB10 832×480 (82 s pour 5,17 s) | 15,9 | 0,0020 | recherche/08 |
| Ref2VA h3-max 1344×768 (129 s pour 5 s) | 25,8 | 0,0035 | JOURNAL 02/11 |
| FL2VA h3-max 5090 1344×768, 24 étapes (290 s) | 56 | 0,0076 | recherche/10 |
| FastH3 GB10 1344×768 (344 s) | 66,5 | 0,0083 | recherche/10 |
| **Pika H3 Flex 6 étapes sur 5090 (estimé : 24 → 6 étapes)** | ≈ 15-20 | ≈ 0,002-0,003 | **à mesurer** |
| Musique Music3 (27 s pour 60 s) | 0,45 | 0,00006 | recherche/10 |
| LLM du Producteur (palier Éco, un film) | — | 0,001 CAD le film | recherche/19 |

Avec un facteur ×3 pour les brouillons, la seconde prise du juge et les ratés, une seconde **finie** en qualité cinéma coûte **≈ 0,01 à 0,025 CAD** ; en qualité rapide, **≈ 0,006 CAD**. Le prix actuel du devis (0,5 crédit par seconde GPU, 1 crédit = 1 ¢ CA, `app/server/nexora/credits.ts`, `usage.ts`) donne ≈ **0,28 CAD par seconde h3-max** : marge confortable mais **au-dessus** de l'API Pika Flex (≈ 0,05 CAD/s au lancement) et de l'API MiniMax H3 (≈ 0,18 CAD/s). Stratégie de prix : `docs/backlog/creative-triple-a.md` §4.

## 3. Le « LLM qui booste le tout » (réécriture, réalisation, cohérence)

Détail : `24-annexes/C-agents-voix-musique-blender.md` (GPT-6 Astra, effort élevé, recherche web ; contrôlé).

| Piste | Ce qu'elle apporte | Mesure publiée | Licence | Verdict |
|---|---|---|---|---|
| **Compilateur par mode H3** (guides officiels `base-en.txt`, `ref-en.txt` du dépôt MiniMax-H3) | le LLM produit une intention typée (sujet, action observable, état initial/final, caméra, lumière, son, contraintes immuables, références) ; le code la compile dans le dialecte du mode (T2VA, I2VA, FL2VA, Ref2VA) | aucune (prescriptions) | ? | **adopter** (audit de `promptH3.ts`/`reecritureH3.ts`) |
| RAPO / **RAPO++** ([2504.11739](https://arxiv.org/abs/2504.11739), [2510.20206](https://arxiv.org/abs/2510.20206)) | modificateurs récupérés + correction après observation de la vidéo | VBench +1,76 (LaVie), +3,72 (Latte) ; « multiple objects » 37,7 → 71,9 | ? | tester la boucle de retour |
| **VPO** ([2503.20491](https://arxiv.org/abs/2503.20491)) | sépare fidélité au brief et qualité vidéo ; pénalise la belle vidéo qui change l'action | CogVideoX-5B multiple objects 45,7 → 75,7 | Apache-2.0 | **adopter** la double évaluation |
| Prompt-A-Video ([2412.15156](https://arxiv.org/abs/2412.15156)) | réécriveur entraîné par préférences | esthétique +, **dynamique 0,70 → 0,54** | ? | avertissement : un prompt « plus beau » peut tuer le mouvement |
| **TIDE** ([2610.15098](https://arxiv.org/abs/2610.15098)) | distille hors ligne des règles réutilisables : une seule réécriture au déploiement | coût de boucle supprimé | MIT | **adopter** une petite bibliothèque de règles gagnantes, versionnée |
| AniMaker ([2506.10540](https://arxiv.org/abs/2506.10540)) | plus de prises pour les plans difficiles (MCTS) | AniEval | ? | tester un **budget de prises adaptatif** borné |
| GroundShot ([2606.20799](https://arxiv.org/abs/2606.20799)) | tourner d'abord les plans « ancres » des entités, puis les plans dépendants | GroundBench | ? | tester « ancre d'abord » dans le projet long |
| Complementary RAP ([2609.37407](https://arxiv.org/abs/2609.37407)) | choisir un petit jeu de références **complémentaires** (lieu + personnage + accessoire) plutôt que quatre portraits | — | ? | **adopter** le principe dans `personnagesCast.ts` |
| VideoClaw (ex-FilmAgent) | étapes éditables, reprise depuis un artefact intermédiaire, routage I2V/FL2V/référence | — | MIT | tester la reprise ; garder notre orchestrateur |
| LIT ([2610.41865](https://arxiv.org/abs/2610.41865)) | réalisateur, utilisateur simulé, réviseur de méthodes ; démonstrations sur H3 | +19,1 % production (auteurs) | ? | surveiller |
| MovieAgent, Mora, HoloCine, MVAgent | décomposition narrative ; HoloCine = modèle multi-plans entraîné (CC-BY-NC-SA) | — | divers | écarter comme socle |

**Banc proposé** (24 briefs, moitié pub/produit, moitié action/personnages) : réécrivain actuel contre compilateur par mode, contre compilateur + règles TIDE ; mêmes prises ; notes séparées pour fidélité, mouvement, lisibilité du produit, cohérence, son, préférence. Le résultat de ce banc décide du défaut.

## 4. Effets spéciaux : les briques ouvertes (annexe B, partie 2 : 25 pistes)

| Rang | Brique | Pour quoi | Machine | Verdict |
|---|---|---|---|---|
| 1 | **Wan2.2-Fun-5B-Control → VACE-Fun-A14B** | une même prévisualisation pilote profondeur, pose, occultations, remplacement de fond, retouche | 5090 (5B), GB10 (A14B) | **adopter** comme socle de contrôle |
| 2 | **Wan-Move** | dessiner la trajectoire du dragon, du vaisseau, du projectile | GB10 (≥ 40 Go publiés) | tester |
| 3 | **Wan-Alpha v2** (RGBA) ; Alpha++ « effets » encore annoncé | bibliothèque d'éléments détourés (fumée, étincelles, créatures) à poser en calque | GB10 | tester |
| 4 | **LiveLight**, **Relit-LiVE** ; Light-A-Video en témoin | lumière mobile d'une explosion ou d'un sabre sur le décor et les visages | 5090 (≥ 24 Go) | comparer, garder un seul |
| 5 | **FlashVSR+** (+ SeedVR2 en témoin) | export 1080p/4K (0,5 à 0,98 image/s publiés sur 4090) | 5090 | **adopter** en file d'export |
| 6 | Wan-Animate-2 | transfert de geste ou de duel sur un personnage | GB10 si monocarte | tester, arrêter si multi-GPU |
| 7 | SoL-Refiner | raffinage une étape des sorties H3/LTX | ? (gain mesuré sur GB200) | surveiller |
| 8 | DiffuEraser (dépend de ProPainter), VideoPainter (académique), Qwen-Video-Edit, UniVideo | retrait d'objet, retouche par instruction | 5090/GB10 | comparer à VACE-Fun |
| 9 | InsertAnywhere, OmniInsert | insertion d'objet avec géométrie, occultation, lumière | — | surveiller |
| 10 | VFX Creator, VFXMaster, IC-Effect, EasyVFX, EffectMaker | LoRA d'effets « à la Higgsfield », transfert d'effet depuis une vidéo de référence | — | VFXMaster tester ; les autres incomplets ou vides |
| 11 | PhysChoreo, RealWonder (NC), FluidGen | physique (chorégraphie, fumée, feu) | — | surveiller : rien de livrable |
| 12 | Cosmos-Transfer2.5 | prévisualisation 3D → rendu photoréaliste | GB10 | tester avec le travailleur Blender |

Règle d'architecture retenue : **un effet = une couche** (élément RGBA, masque, passe de lumière) posée sur la prise, jamais une régénération globale qui change les gestes ; les lames de sabre restent **procédurales** (suivi + segment lumineux), la lumière qu'elles projettent est générative. Les quatre scènes test (dragon dans une prise réelle, explosion, bataille spatiale, duel au sabre) et leurs critères de réussite sont dans l'annexe B.

## 5. Avatars et synchronisation labiale

| Piste | Usage | Mémoire publiée | Licence | Verdict |
|---|---|---|---|---|
| **MuseTalk 1.5** | redoublage rapide (aperçu) | 30 i/s+ sur V100 | MIT | **tester** sur Turing ou 5090 |
| **LatentSync 1.6** | finition des gros plans | 18 Go | Apache-2.0 (code), OpenRAIL++ (poids) | **tester** sur 5090 |
| InfiniteTalk | tête et corps suivent l'audio (présentateur) | offload | Apache-2.0 | tester |
| OmniAvatar 14B | jeu corporel par texte | 21 Go avec 7B résidents | Apache-2.0 | tester si le jeu corporel compte |
| LongCat-Video-Avatar 1.5 | 8 étapes, multi-intervenants | ? | MIT | tester après recette monocarte |
| Wan2.2-S2V, HunyuanVideo-Avatar | 80 Go / 24 Go très lent | — | Apache / Tencent | surveiller |

Deux niveaux : MuseTalk en aperçu, LatentSync en finale ; un générateur corporel seulement si le plan l'exige. H3 continue de faire parler ses propres personnages (c'est ce que les promos utilisent, recherche/23 R7).

## 6. Voix expressives (priorité au local)

Ce que l'équipe voix a déjà mesuré (`marketing/nexora/campagne-films/comparatif-v2/rapports/VOIX-MUSIQUE-MANCHE-2.md`) : Drama 3 tourne en local (5090 int4 RTF 0,12 ; GB10 FP8 RTF 0,83), ElevenLabs v4 « Alexandre » est la référence du fondateur. Ajouts de ce rapport :

| Modèle | Expressivité | Français | Licence | Machine | Verdict |
|---|---|---|---|---|---|
| **Qwen3-TTS 1.7B** (VoiceDesign, CustomVoice, Base) | voix décrite par texte, instructions de style | oui | Apache-2.0 | 5090 ; 0.6B sur Turing | **tester en priorité** (déjà en tête des licences permissives à la manche 2) |
| **CosyVoice 3** (0.5B) | instructions de vitesse, volume, émotion ; clonage croisé | oui | Apache-2.0 | Turing FP16 | **tester en priorité** |
| **Chatterbox Multilingual** | `exaggeration` ≈ 0,7, `cfg_weight` ≈ 0,3 pour une parole dramatique (README) | oui | MIT | Turing (en service) | **adopter les réglages tout de suite** |
| Higgs TTS 3 (4B) | instructions de prosodie | oui (non validé québécois) | Research-NC (poids) | 5090 | écarter (licence) |
| IndexTTS 2.5 | huit émotions, durée | **pas de français** | Bilibili | 5090 | anglais seulement |
| Orpheus 3B fr (recherche) | balises de rire, soupir | oui | Apache (code) | 5090 | quatrième voix de casting |
| Dia2, VibeVoice, F5/E2, Kokoro | dialogues anglais, conversations longues, brouillons | partiel | divers | — | Kokoro reste voix de travail |
| Fish S2 / Drama 3 | direction expressive, clonage | oui | Research / Community | 5090 (S2), GB10 (Drama 3) | Drama 3 : en cours de décision par le fondateur |

Méthode de casting (annexe C §5) : six textes de 15-25 s (sport, révélation de bande-annonce, urgence, sourire pub, intime, phrase québécoise), une **référence enregistrée dans le style visé** (pas une lecture calme), écoute à l'aveugle par le fondateur à niveau égal.

## 7. Musique

| Modèle | Contrôle | Mesure publiée (YuE2, 192 demandes) | Licence | Verdict |
|---|---|---|---|---|
| **MiniMax-Music3** (en service) | description structurée | SongBench 6,28 ; **PER 0,063 (meilleur)** | Music3 Community | **garder** |
| **ACE-Step 1.5 / XL** | BPM, tonalité, mesure, durée, sections, reprise d'un passage, stems | 6,01 ; PER 0,075 | MIT | **tester** pour imposer la structure et réparer un passage |
| YuE2 | partition symbolique éditable | 6,73 (meilleur agrégat) | CC-BY-NC-4.0 (poids) | surveiller (licence) |
| HeartMuLa, DiffRhythm 2, SongBloom | chansons longues | 6,25 ; 5,24 ; — | Apache / Apache / dépôt 404 | surveiller |

Essai décisif : trois briefs (15/30/60 s) avec tempo et accents imposés ; compter les corrections de montage nécessaires avec Music3 et avec ACE-Step ; mesurer le BPM obtenu, pas celui demandé.

## 8. Blender et agents 3D

| Piste | Ce qui est documenté | Licence | Verdict |
|---|---|---|---|
| **BlenderMCP → `mcp-for-blender`** (ahujasid) | exécution de Python Blender, inspection de scène, outil `look` (vues multiples, bandes d'animation) | MIT | tester dans un travailleur isolé à gabarits |
| BlenderGym ([2504.01786](https://arxiv.org/abs/2504.01786)), 3DHarnessBench ([2609.06535](https://arxiv.org/abs/2609.06535)), **BlenderWorld** ([2610.23986](https://arxiv.org/abs/2610.23986), 223 tâches, 2 651 critères) | bancs : les agents ratent encore des opérations simples | MIT (BlenderWorld) | adopter le principe de 10 tâches internes vérifiables |
| FilmFlow ([2610.30753](https://arxiv.org/abs/2610.30753)) | caméra virtuelle par agents ; code « bientôt » | ? | surveiller, reprendre sa grammaire de caméra |
| Vibe3DScene | contrats de travailleur et persistance de scène | Apache-2.0 | tester les contrats |
| SceneCraft ([2403.01248](https://arxiv.org/abs/2403.01248)) | graphe de scène → code Blender | ? | surveiller |

Ce qu'un agent Blender apporte vraiment : prévisualisation et cadrage, trajectoires de caméra exactes, passes (profondeur, normales, masques) pour guider Wan-Fun/VACE ou servir de première/dernière image à H3, rendus déterministes de ce qui doit être exact (logo, produit, dimensions). Ce qu'il n'apporte pas : du photoréalisme autonome à partir d'un brief vague, ni une simulation crédible sans gabarit validé. Réponse au fondateur dans le backlog §1.

## 9. Montage par agent et FilmCraft

- **WeVisCut** ([2610.38352](https://arxiv.org/abs/2610.38352), Tencent, Apache-2.0) : agent 9B à douze outils et état reconstruit à chaque étape ; 90,5 contre 89,9 pour Opus 5 sur leur banc, ≈ 33 fois moins de jetons par minute réussie. À prendre : **les vues d'état compactes et la réparation locale** (on corrige un plan sans tout remonter). Nos `EditPlan`, `critique` et `revise` (recherche/13-14) vont déjà dans ce sens.
- **Uncut** (MIT) : critique indépendant qui juge le rendu sans voir le raisonnement du monteur. À prendre pour notre juge.
- **FilmCraft** ([storytold/filmcraft](https://github.com/storytold/filmcraft), MIT/Apache-2.0) : 64 commits du 02/11 au 03/11 (dernier : `9bd7250`, 03/11 22:31 heure de Montréal), release 0.17.0, ≈ 650 commandes. À prendre, en TypeScript : (1) **validation indexée des opérations groupées** (toute l'entrée validée avant d'agir, erreur `moves[i]`) ; (2) **aperçu en lecture seule** sérialisé ; (3) **rapport d'export** qui liste ce qui est perdu (pistes, effets) ; (4) **fermeture des dépendances** d'une sélection exportée ; (5) unités séparées (fréquence audio ≠ cadence vidéo) ; (6) verrou d'écriture par projet. **Correction de la note 13** : `command_batch` de FilmCraft **n'est pas atomique** (pas de retour arrière global ; un pas d'annulation par modification) ; notre `enUnePas` doit garder sa propre atomicité.

## 10. Remue-méninges : ce qui survit (Gemini 4 Argon, effort élevé, et GPT-6.1 Sol)

Même dossier de départ pour les deux (résumé de l'état de Creative, du marché, des coûts et de la grammaire des promos) ; réponses complètes dans `24-annexes/D-remue-meninges.md`. J'ai gardé ce qui résiste à l'examen, écarté le reste.

**Survit**
- **Positionnement** (Sol, adopté) : « *Votre idée devient un film prêt à publier, et vous gardez la main sur chaque détail.* » Les trois preuves en moins de 3 minutes (fusion des deux) : (1) une phrase → les plans, les ingrédients et **le prix total en dollars** avant tout calcul, un seul bouton ; (2) le premier plan en brouillon avec le personnage reconnaissable et son son, références affichées à côté (règle R5 de recherche/23) ; (3) une retouche à la phrase au clic droit, avant/après, Ctrl+Z, puis export **vidéo 16:9 + 9:16 + imprimé assorti** (aucun concurrent ne relie vidéo et imprimé, Gemini).
- **Vingt recettes complètes et fiables plutôt que des centaines de presets** (Sol rang 1) ; l'une d'elles est le **gabarit « Promo qui claque »** qui code les 16 règles de recherche/23 dans l'`EditPlan` (Gemini rang 2).
- **Un projet, trois formats** (recadrage 9:16 / 1:1 / 16:9 suivi, lissé, textes dans la zone sûre) ; **« change seulement le plan 2 »** avec invalidation minimale ; **MCP distant + API** idempotents avec plafond de dépense ; **voix et audio fourni** choisis à l'écoute ; **lip-sync MuseTalk d'abord** ; **agrandissement à l'export** ; **lien de revue client** horodaté (pas de co-montage simultané) ; **retrait d'objet** sur plan court en dernier (SAM + VACE-Fun).
- **Pika H3 Flex à mesurer d'abord** (les deux) ; Sol a raison : ne pas transformer « 6 étapes contre 50 » en promesse ×8 avant la mesure.
- **À refuser** (les deux) : devenir un agrégateur d'API payantes (marge et cohérence détruites), communauté et concours maintenant, mondes jouables, entraînement de LoRA par les clients sur nos GPU, « illimité » GPU, plans longs comme objectif en soi.
- **Prix** : vendre la **seconde retenue**, pas la seconde de GPU ; brouillon presque gratuit ; Studio gratuit (il tourne dans le navigateur) ; forfait qui achète la récurrence et l'organisation (chiffres retenus dans le backlog §4).
- **Blender** : non indispensable (les deux) ; utile en opérations bornées et scriptées. Idée de Gemini retenue : une **scène 3D légère dans le navigateur** (la visionneuse de Relief existe déjà) pour poser objet et caméra, et en tirer première/dernière image ou carte de profondeur.
- **Interface triple A** : deux vitesses (Producteur sans jargon, « Ouvrir dans le Studio » pour le reste) ; 60 i/s sacrés (proxys) ; **pas de champ vide** : chaque réglage est une vignette vidéo qui s'anime au survol ; **rideau avant/après** universel ; **attente lisible** (état réel, délai, coût verrouillé, aperçu qui se précise) ; grille de 8 px, trois niveaux typographiques, contraste AA, clavier.
- **Deux paris audacieux, gardés comme expériences** : le **« Producteur de nuit »** (Gemini : entre 1 h et 6 h, sur des GPU libres et amortis, le studio prépare sans qu'on le demande une pub de 15 s par client abonné, sous plafond et avec son accord explicite, livrée au réveil) et le **film « document vivant »** (Sol : prix, horaires et stock reliés au catalogue ; une promotion change le carton, une rupture retire le produit ; rendu incrémental, nouvelle version soumise à validation).

**Écarté** (affirmations de Gemini non vérifiées ou contraires à nos règles de licence) : YOLOv11 pour le suivi (AGPL), ProPainter et F5-TTS (poids non commerciaux), Hallo3, brouillon « en 3,5 s » et capacité « 2 500 s par heure » (extrapolations sans mesure), « devis en vrais dollars » à la place des crédits (on affiche l'équivalent en dollars, 1 crédit = 1 ¢ CA, sans casser le grand livre du portail).

## 11. Ce que je n'ai pas pu vérifier

- Aucun modèle n'a été installé ni mesuré pour ce rapport : toutes les vitesses tierces sont publiées par leurs auteurs sur d'autres machines ; les placements GB10/5090/Turing sont des estimations de capacité.
- Pika H3 Flex : qualité et vitesse sur nos bases H3 et dans ComfyUI 0.43 non mesurées ; Pika lui-même dit qu'aucun rendu ComfyUI de bout en bout n'a été vérifié pour ces adaptateurs.
- Prix : plusieurs grilles d'application (OpenArt, Kling, Krea, Magnific, Leonardo en 1080p) ne permettent pas de calculer un prix par seconde ; les prix de lancement (Pika) peuvent changer.
- Les identifiants arXiv des rapports délégués ont été contrôlés par lecture automatique de leur page (titre et date, §12) ; leur contenu chiffré n'a été relu que pour les articles cités ci-dessus.
- Licences : un mot par ligne, lues sur la page du dépôt ou la fiche du modèle ; aucune analyse.
- Coût par seconde : hypothèses d'amortissement à remplacer par les vraies valeurs ; consommation électrique non mesurée à la prise.

## 12. Vérification des références

| Contrôle | Résultat |
|---|---|
| 79 identifiants arXiv cités dans les trois annexes | **79 sur 79** existent et leur titre recopié est identique au titre de la page `arxiv.org/abs` (lecture automatique le 03/11/2026) |
| 85 dépôts GitHub cités | **83 existent** (réponse 200) ; `Cypress-Yang/SongBloom` répond 404 (déjà signalé par l'annexe C) ; le 85e était une URL d'API mal extraite |
| Affirmations recoupées à la main | retrait de Sora (page OpenAI des dépréciations : API et modèles retirés le 24/09/2026) ; Freepik → Magnific (page Magnific, 28/04/2026) ; prix Pika H3 Flex (page Pika : 0,07 $/s régulier, 0,035 $/s lancement en 1080p) ; rang de H3 dans l'arène (3e, 1160) ; poids Pika H3 Flex non protégés, licence H3, adaptateurs ComfyUI (API Hugging Face et README `comfy/`) ; tarif Hydro-Québec 2026 |
| Ajout absent des annexes | **Pika H3 Flex comme modèle local** : l'annexe B ne le mentionne pas, l'annexe A le cite seulement comme offre commerciale ; trouvé et vérifié par moi |
