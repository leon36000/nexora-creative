# 18 — Un mode « 3D » dans Nexora Creative, à la façon de Meshy (03/11/2026)

Ordre du fondateur : ajouter une option qui fait comme https://www.meshy.ai, avec notre technologie ; sonder tout l'open source, assembler ou extraire des fonctions pour gagner un temps considérable.

Étiquettes : **[LU]** source primaire lue directement (code, API de dépôt, fichier de licence, documentation) ; **[RÉSUMÉ]** page résumée par un outil ou extrait de moteur de recherche, non relu en entier ; **[LOCAL]** constaté sur nos machines ce jour ; **[MESURÉ amont]** mesure publiée dans le CHANGELOG du fork OpenField (pas la nôtre) ; **[ESTIMÉ]** extrapolation à valider par un banc. Les licences sont des faits relevés, sans commentaire juridique.

## 0. Ce qu'il faut retenir (la découverte qui change le plan)

1. **Le fork OpenField contient déjà un mode « Object » (image → 3D) complet** [LU] : `app/server/graphs/trellis.ts` (206 lignes), page `app/src/pages/Object.tsx` avec visionneuse three.js, « Make 3D » sur n'importe quelle image, filtre 3D dans la bibliothèque, outil MCP `make_3d`, ensemble de modèles `trellis2` (≈ 14 Go) déjà déclaré dans `models.ts`, règle `trellis2: permis` déjà dans `licences.ts`. Il rend un GLB PBR (couleur, métal, rugosité ; en « High » : normale + AO cuites) et une **tournette mp4 produite dans le moteur**. Il n'a jamais été activé chez nous : les poids ne sont pas téléchargés.
2. **Le moteur ComfyUI de la GB10 contient déjà les nœuds** [LOCAL] : `/home/pc6/nexora-creative-data/engine/ComfyUI` (v0.43.2) a `nodes_trellis2.py`, `nodes_mesh_postprocess.py` (Decimate, Remesh, Unwrap, bake normale/AO/texture, FillHoles, Weld, RenderMesh…), `nodes_save_3d.py`, `nodes_hunyuan3d.py`, `nodes_sam3d_body.py`, et les modèles de workflow `3d_pixal3d_trellis2_image_to_model`, `3d_hunyuan3d_*`. Le chemin TRELLIS.2 de ComfyUI est en **PyTorch pur** (imports lus : torch, numpy, scipy, `comfy.ops` ; sparse-conv réimplémentée dans `comfy/ldm/trellis2/flexgemm.py`). **Aucun flash-attn, nvdiffrast, spconv, cumesh à compiler** : c'est ce qui rend le projet faisable sur aarch64/GB10 en jours et non en semaines. Torch du venv GB10 : 2.14.1+cu130, capacité (12,1) [LOCAL].
3. **Hunyuan3D (Tencent) est écarté** : sa licence 2.1 « ne s'applique pas dans l'Union européenne, le Royaume-Uni et la Corée du Sud », interdit l'usage hors territoire et l'emploi des sorties pour améliorer un autre modèle, plafond de 1 million d'utilisateurs actifs mensuels [LU, fichier LICENSE]. Les autres dépôts Tencent 3D (Part, Omni) n'affichent pas de licence claire sur HF (« other » ou vide) : même prudence. TRELLIS.2 (MIT) et Pixal3D (MIT) couvrent le besoin.
4. **Ce qui manque pour égaler Meshy** : texte → 3D (se fait par assemblage : Qwen-Image puis Object), multi-images, retexture d'un maillage importé, topologie quad « artiste », export FBX/USDZ/BLEND/3MF/STL, rigging et animation, préparation d'impression, greffons Blender/Unity/Unreal, API publique. Tout cela se construit à partir de briques mûres (§4) ; seules la **topologie quad générative** et la **qualité de texture au niveau de Meshy 7** n'ont pas d'équivalent ouvert disponible aujourd'hui.

## 1. Ce que Meshy propose aujourd'hui

Sources : docs.meshy.ai (API Text-to-3D, Image-to-3D, Multi-Image, Retexture, Remesh, Rigging, Animation, accueil) et meshy.ai/pricing, lues le 03/11/2026 [RÉSUMÉ : pages passées par un résumeur, paramètres cohérents entre pages].

| Fonction Meshy | Détail relevé | Réf. |
|---|---|---|
| Texte → 3D, en deux temps | `preview` (maillage gris, prompt ≤ 800 car.) puis `refine` (texture). Modèles : Meshy-6-lite, Meshy-6, **Meshy-7.1** (« latest »), Smart Topology t2/t2.5. Pose A/T, `auto_size` (hauteur réelle estimée), modération du prompt | API text-to-3d |
| Image → 3D | 1 image JPG/PNG/WebP ≤ 20 Mo ; `should_texture`, `image_enhancement`, `remove_lighting` ; géométrie standard/2k/4k | API image-to-3d |
| Multi-images → 3D | **1 à 4 images**, mêmes options, `texture_image_urls` 1 à 4 | API multi-image |
| Texturation IA / PBR | `enable_pbr` (métal, rugosité, normale, émission selon le modèle), textures 2k/4k/8k, guidage par texte ou par image | API |
| Retexture | sur un modèle importé (GLB, glTF, OBJ, FBX, STL ≤ 400 Mo) avec texte, image de style ou 1 à 4 vues ; `enable_original_uv` | API retexture |
| Remesh / polycount | `topology` triangle ou **quad**, `target_polycount` 100–300 000, `decimation_mode` 1–4 (ultra→bas) ; Smart Topology 100–30 000 faces, ≈ 10 s | API remesh |
| Rigging | humanoïdes bipèdes uniquement, ≤ 380 000 triangles, `height_meters`, face vers +Z ; sorties FBX et GLB + marche/course | API rigging |
| Animation | bibliothèque de plus de 500 actions (20 en gratuit) en 5 catégories ; `change_fps` 24–60, `fbx2usdz`, `extract_armature` ; texte → mouvement | API animation |
| Formats | GLB, FBX, OBJ(+MTL), USDZ, STL, **3MF**, BLEND ; import à la texturation | docs, pricing |
| Impression 3D | module dédié, 3MF couleur, intégrations Bambu Studio / OrcaSlicer | accueil |
| Greffons et API | Blender, Unity, Unreal, Maya ; API REST (flux SSE, 20 req/s), serveur MCP, Playground | accueil |
| Autres modules | Image (texte → image), Scene, Video, **Meshy 3D Agent** (chat) | accueil |
| Vitesse annoncée | Meshy 7 « moins d'une minute », Meshy 6 ≈ 1 min, Smart Topology ≈ 10 s | accueil |
| Modèle économique | Gratuit 100 crédits/mois (10 modèles, CC BY 4.0) ; Pro 28 CAD → 1 000 crédits ; Premium 56 → 3 000 ; Ultra 140 → 8 000 ; Studio 98 → 5 500 partagés ; conservation des fichiers 3 jours (Pro) à 14 jours (Studio). Coûts relevés dans les exemples d'API : aperçu texte 20 crédits, image → 3D 30, retexture 10, rigging 5, animation 3 ; échecs remboursés | pricing, API |

## 2. Table des fonctions : ce que l'on égale, avec quoi, et les écarts

| Fonction | Brique ouverte retenue | État | Écart avec Meshy |
|---|---|---|---|
| Image → 3D PBR | TRELLIS.2 via nœuds ComfyUI (déjà dans Object) | **présent, à activer** | qualité proche des meilleurs ouverts ; artefacts connus (§7) |
| Texte → 3D | Qwen-Image (Apache-2.0, notre brique) → 4 candidats → juge → TRELLIS.2 | à construire, 2–3 j | pas de modèle natif texte → 3D ouvert récent ; la qualité dépend de l'image intermédiaire |
| Aperçu rapide puis raffinage | résolution 512³ puis 1024³/1536³ à la même graine ; l'étage texture est séparé de l'étage forme | à construire, 2 j | l'objectif 30–60 s reste à mesurer |
| Multi-images | Pixal3D multivue (MIT) ; vues fournies par l'utilisateur ou rendues par Qwen-Edit « Multiple-angles » (déjà dans `edit-angle.json`) | 3–4 j | 4 vues max chez Meshy ; Pixal3D lent (6–7 min côté hébergeur tiers) |
| Texturation PBR | étage texture de TRELLIS.2 + nœuds Bake/Paint/Unwrap/ApplyTexture | présent | pas de texte → texture sur maillage importé validé |
| Retexture d'un maillage importé | étage `imgshape2tex` de TRELLIS.2 (texture conditionnée par forme + image) ; repli MV-Adapter (Apache-2.0) | spike 2–3 j | à prouver ; Hunyuan-Paint écarté (licence) |
| Remesh / polycount triangles | `DecimateMesh` (QEM), `RemeshMesh`, `FillHoles`, `WeldVertices` de ComfyUI ; gabarits jeu/web/impression | présent, 1 j d'UI | — |
| Quad / topologie artiste | Instant Meshes ou QuadriFlow (via Blender) en post-traitement ; Meshy T2 et TaoFlowForge annoncés « code à venir » | **écart** | résultat quad-dominant, pas « artiste » |
| Formats | trimesh (OBJ, STL, PLY, 3MF), three.js USDZExporter, Blender sur pc1 (FBX, BLEND) | 2–3 j | FBX/BLEND demandent x86_64 (§4) |
| Rigging | SkinTokens / UniRig (MIT) sur pc1 | 4–5 j, phase 4 | GB10 impossible sans portage ; humanoïdes et quadrupèdes |
| Bibliothèque d'animations | à constituer (CC0 à vérifier), retargeting Blender | **écart** | pas de 500 actions clés en main |
| Impression 3D | manifold3d + trimesh : étanchéité, mise à l'échelle en mm, 3MF | 2 j | pas d'intégration slicer |
| Greffons / API / MCP | `make_3d` MCP existe ; API de recettes signées ; greffon Blender = petit client REST | 2 j + 3 j | Unity/Unreal : plus tard |
| Agent de chat | agent Nexora existant (`agent.ts`) + outil `make_3d` | 1 j | — |

## 3. Candidats ouverts : table des composants

Matériel : **GB10** = aarch64, CUDA 13, sm_121, 128 Go unifiés ; **5090** = x86_64, sm_120, 32 Go. Verdict : OK (pas de noyau à compiler ou preuve), RISQUE (compilation ou version imposée), NON.

### 3.1 Image / texte → 3D

| # | Nom (URL) | Licence | Maturité | GB10 aarch64 | 5090 sm_120 | Ce que l'on prend | Où ça se branche |
|---|---|---|---|---|---|---|---|
| 1 | **TRELLIS.2-4B** (github.com/microsoft/TRELLIS.2 ; HF Comfy-Org/TRELLIS.2) | MIT (code + poids) ; DINOv3 sous licence Meta | 12,6 k★, push 07/2026 ; intégré au noyau ComfyUI | **OK via ComfyUI** (PyTorch pur) ; le dépôt d'origine exige flash-attn, nvdiffrast, nvdiffrec, cumesh, o-voxel, flexgemm, CUDA 12.4, testé A100/H100 seulement → ne pas l'utiliser tel quel [RÉSUMÉ] | **OK** [MESURÉ amont, 10/17, 5090] | tout : forme, texture PBR, résolutions 512/1024/1536 | recettes `objet-*` |
| 2 | **Pixal3D** (github.com/TencentARC/Pixal3D ; HF Comfy-Org/Pixal3D) | MIT (étiquette HF) | 2,6 k★, push 09/2026 ; dans ComfyUI ; mêmes VAE et DINOv3 que TRELLIS.2 | OK en principe (même chemin de code) | OK | fidélité pixel, **multivue** (5,58 Go int8) | recette `objet-multivue` |
| 3 | TRELLIS v1 texte (HF microsoft/TRELLIS-text-xlarge) | MIT | 2025 ; chemin v1 (spconv, xformers…) | RISQUE | RISQUE | non : le texte passe par Qwen-Image | — |
| 4 | Hunyuan3D 2.0/2.1/2mv (Tencent-Hunyuan/Hunyuan3D-2.1) | licence communautaire : **hors UE, Royaume-Uni, Corée** ; 1 M d'utilisateurs actifs | 4,3 k★ ; forme native dans ComfyUI (7,37 Go) ; texture = `custom_rasterizer` à compiler, 21 Go de VRAM | RISQUE (retours d'usage sous Docker sur DGX Spark [RÉSUMÉ]) | OK | **rien** (écarté) | — |
| 5 | Hunyuan3D 3.0 / 3.1 Pro | non publié en poids (accès hébergé : Scenario, 3DAIStudio) [RÉSUMÉ] | — | — | — | rien | — |
| 6 | Step1X-3D (stepfun-ai) | Apache-2.0 | 900 ★, push 09/2025 ; 27 Go de VRAM ; exige pytorch3d, kaolin 0.17, torch-cluster, custom_rasterizer ; CUDA 12.4 / torch 2.5.1 [RÉSUMÉ] | NON (kaolin, rasterizer) | RISQUE | rien (surveiller) | — |
| 7 | TripoSG / TripoSF (VAST-AI-Research) | MIT | 1,9 k★, dernier push 04/2025 ; forme seulement | RISQUE | OK | seconde forme possible, non nécessaire | — |
| 8 | SPAR3D / SF3D (Stability) | licence communautaire Stability : gratuit sous 1 M$ de revenu annuel, enregistrement requis [LU] | 2025 ; < 1 s | RISQUE (noyaux maison) | OK | aperçu instantané éventuel, pas retenu | — |
| 9 | TripoSR (VAST-AI-Research) | MIT | 7,3 k★, push 06/2026 ; < 1 s, ≈ 6 Go [RÉSUMÉ] | RISQUE (torchmcubes) | OK | plan B pour un « aperçu éclair » | — |
| 10 | Direct3D-S2 (DreamTechAI) | MIT | 1,3 k★, 09/2025 ; forme SDF 2048³ | RISQUE | RISQUE | non | — |
| 11 | Hi3DGen (bytedance) | code MIT ; poids « other » | 106 ★, 09/2025 ; ComfyUI-Hi3DGen existe | RISQUE | OK | non | — |
| 12 | UltraShape 1.0 (PKU-YuanGroup) | non déclarée (NOASSERTION) | 872 ★, 01/2026 ; raffinement de géométrie | inconnu | inconnu | à surveiller (raffinage) | futur |
| 13 | SAM 3D Objects / SAM 3D Body (Meta) | « SAM License » ; Objects sort du Gaussian splat, pas un maillage [RÉSUMÉ] | `nodes_sam3d_body.py` déjà dans notre ComfyUI [LOCAL] | OK (nœuds noyau) | OK | Body : maillage humain depuis une photo, utile au rigging plus tard | phase 4 |
| 14 | Papiers 2026 à suivre : **Meshy T2** (arXiv 2607.28675, 6 s médian, dépôt `meshy-dev/meshy-t2` vide au 03/11 [RÉSUMÉ]), **TaoFlowForge** (2609.37139, « code et poids à venir »), **Channel Match** (2610.15321 : distillation en 2 étapes de TRELLIS.2, géométrie ×4,5 plus rapide), Luce (2608.23943), SUPRA-Tex (2610.22352), AniGen (2604.08746), Rigel3D (2605.13129) | — | aucun code utilisable lu | — | — | idées ; Channel Match servirait la cible 30–60 s si le code sort | veille |
| 15 | Nova3D (arXiv 2607.22738) | — | génération « code Blender » avec parties nommées et articulations ; pas de code lu | — | — | piste pour objets durs paramétriques via le LLM | veille |
| 16 | LocalAI `trellis2cpp` (GGML, MIT) | MIT | port C++ ; 18 Go complet, 7 Go géométrie seule [RÉSUMÉ] | OK probable | OK | alternative d'exécution sans Python, non nécessaire | — |

### 3.2 Texture, matériaux, retexture

| # | Nom | Licence | Maturité / matériel | Verdict | Décision |
|---|---|---|---|---|---|
| 17 | Étage texture TRELLIS.2 + nœuds `BakeTextureFromVoxel`, `PaintMesh`, `ApplyTextureToMesh`, `BakeNormalMapFromMesh`, `BakeAmbientOcclusion`, `UnwrapMesh` (ComfyUI) [LU] | MIT + GPL-3.0 (ComfyUI, processus externe) | noyau, pur PyTorch/scipy | OK GB10 et 5090 | **retenu** |
| 18 | MV-Adapter (huanngzh) | Apache-2.0 | 1,3 k★, 06/2025 ; multivue SDXL + texture | RISQUE aarch64 | repli retexture |
| 19 | Material-Anything (3DTopia) | MIT | 369 ★, 12/2025 ; matériaux PBR sur maillage sans texture | non testé | à tester si la retexture TRELLIS.2 échoue |
| 20 | Hunyuan3D-Paint 2.1 | licence Tencent (voir #4) | 2 B ; `custom_rasterizer` | écarté | — |
| 21 | RomanTex, Paint3D | — | dépôts non retrouvés aux adresses essayées | NON VÉRIFIÉ | ignorés |

### 3.3 Maillage : remaillage, UV, conversion, validation

| # | Nom | Licence | Matériel | Rôle |
|---|---|---|---|---|
| 22 | Nœuds ComfyUI `DecimateMesh` (QEM, « midpoint »), `RemeshMesh`, `FillHoles`, `WeldVertices`, `MeshSmoothNormals`, `RenderMesh`, `RenderUVAtlas` [LU] | GPL-3.0 (service interne) | GB10 + 5090 | polycount, nettoyage, tournette |
| 23 | trimesh 5.2 (PyPI) | MIT, wheel pur Python | toutes | lecture/écriture OBJ, STL, PLY, 3MF, contrôles d'étanchéité |
| 24 | manifold3d 3.5 | Apache-2.0, wheel aarch64 | GB10 OK | réparation en variété, préparation impression |
| 25 | xatlas 0.0.11 | MIT, wheel aarch64 | GB10 OK | UV de secours / comparaison avec `UnwrapMesh` |
| 26 | fast-simplification 0.2 | wheel aarch64 | GB10 OK | décimation CPU rapide |
| 27 | usd-core 26.11 | licence TOST, wheel aarch64 | GB10 OK | lecture/écriture USD ; l'export USDZ glTF → USD reste à valider |
| 28 | Blender / `bpy` 5.2.3 | GPL | **PyPI : wheel Linux x86_64 cp313 seulement** ; aucun binaire Linux ARM officiel [LU, RÉSUMÉ] | pc1 uniquement : FBX, BLEND, quad (QuadriFlow), retargeting |
| 29 | Instant Meshes (wjakob) / QuadriFlow / QuadWild (GPL-3.0) | NOASSERTION / NOASSERTION / GPL-3.0 | CPU, compilables | remaillage quad-dominant (processus externe) |
| 30 | three.js `USDZExporter` | MIT | navigateur | USDZ côté client, sans Blender [RÉSUMÉ, non relu] |
| 31 | Khronos glTF-Validator | Apache-2.0 [non relu] | CPU | dernière barrière avant livraison |

### 3.4 Rigging et animation

| # | Nom | Licence | Exigences | Verdict |
|---|---|---|---|---|
| 32 | **SkinTokens** (VAST-AI-Research/SkinTokens) | MIT, 577 ★, 05/2026 | Python ≥ 3.11, torch 2.7 cu128, flash-attn, ≥ 14 Go VRAM, entrée/sortie GLB ; poids 1,62 Go [LU, RÉSUMÉ] | pc1 (5090 x86_64) ; GB10 RISQUE (flash-attn) |
| 33 | UniRig (VAST-AI-Research/UniRig) | MIT, 1,9 k★, 06/2026 | `bpy==4.2`, flash_attn, spconv, torch_scatter, torch_cluster, Python 3.11 [LU] ; poids 6,4 Go (squelette 1,44 + peau 4,38) | pc1 ; GB10 NON |
| 34 | Puppeteer (Seed3D) | Apache-2.0, 441 ★, 09/2025 | non lu | repli |
| 35 | Bibliothèque de mouvements | CC0 (Quaternius, Kenney) à **vérifier** ; HY-Motion-1.0 (Tencent, licence « other », voir #4) | — | NON VÉRIFIÉ |

### 3.5 Visualisation web, compression, intégrations

| # | Nom | Licence | Rôle |
|---|---|---|---|
| 36 | three.js (déjà dans `Object.tsx`) | MIT | visionneuse orbite, argile, fil de fer |
| 37 | `<model-viewer>` (google/model-viewer, 8,3 k★, push 11/2026) | Apache-2.0 | page de partage et réalité augmentée (Quick Look, Scene Viewer) |
| 38 | meshoptimizer / gltfpack (zeux, 8,8 k★) | MIT | compression meshopt des GLB pour le web |
| 39 | glTF-Transform (donmccurdy, 2 k★) | MIT | pipeline Node : Draco/meshopt, KTX2, nettoyage, texture 4K → 2K |
| 40 | ComfyUI-3D-Pack (MrForExample) | MIT, 3,9 k★, dernier push 12/2025 | **non** : remplacé par le noyau ComfyUI |
| 41 | ComfyUI-Hunyuan3DWrapper (kijai) | NOASSERTION | non (Hunyuan écarté) |
| 42 | 3DAIGC-API (FishWoWater) | Apache-2.0 | modèle d'API FastAPI multi-modèles 3D, à lire pour inspiration |
| 43 | OpenField « Object » (notre fork, MIT) | MIT | **base du mode 3D** |
| 44 | Qwen-Image-2512 (Apache-2.0, `recherche/11`) ; Qwen-Image-Edit-2509 + LoRA « Multiple-angles » (déjà chargés dans `edit-angle.json`) [LOCAL] | Apache-2.0 | image de référence et vues multiples |
| 45 | BiRefNet (HF Comfy-Org/BiRefNet), MoGe-2 (Comfy-Org/MoGe) | MIT (d'après `models.ts`) | détourage, estimation du champ de vision pour Pixal3D |

## 4. Le mode « 3D » : conception

### 4.1 Expérience

1. **Entrée** : un prompt, ou 1 à 4 images, ou un GLB à retexturer. Un sélecteur « Réaliste / Stylisé / Jeu (low poly) / Impression » préremplit les réglages.
2. **Texte** : le LLM réécrit en « fiche objet » (sujet unique, centré, entier, 3/4 face, fond uni, éclairage neutre, sans ombre portée), Qwen-Image produit 4 candidats en ≈ 1 min, le **juge visuel** choisit celui qui se « reconstruit » le mieux (§4.4), l'utilisateur peut en choisir un autre.
3. **Aperçu en 30–60 s** (cible, voir §4.3) : maillage gris (« argile ») dans la visionneuse, rotation libre. Boutons : *Recommencer* (autre graine), *Raffiner*, *Changer l'image*.
4. **Raffiner** : même graine, 1024³ + texture PBR 2K (« Brouillon » existant) ou 1536³ + 4K + normale/AO (« Qualité » existant).
5. **Retoucher** : gabarit de polycount (Web 15 k, Jeu 30 k, Cinéma 150 k, Impression), « décaler l'origine », « mettre à l'échelle (hauteur en m) », retexture par texte ou image.
6. **Exporter** : GLB, OBJ, STL, PLY, 3MF, USDZ ; FBX et BLEND dès que le travail Blender (pc1) existe. Chaque export passe la validation (§4.6) et affiche son rapport.
7. **Utiliser** : « Envoyer à la vidéo » (§4.7), « Ajouter au projet long », « Copier le lien de partage » (`<model-viewer>`).

### 4.2 Graphes par recette

| Recette | Graphe | Sortie | Machine préférée |
|---|---|---|---|
| `objet-apercu` | image → BiRefNet → DINOv3 → structure 32³ → forme 512 (8–12 pas) → `VoxelToMesh` → `DecimateMesh` 30 k → GLB gris | GLB ≈ 2–4 Mo, sans tournette vidéo (la visionneuse client suffit) | 5090 ou GB10 |
| `objet-brouillon` (existant « draft ») | structure → forme 512 → montée à 1024 → texture (8 pas) → remaillage 512 → 150 k faces → UV → cuisson 2K → GLB + tournette 32 images | GLB ≈ 10 Mo | GB10 (par défaut) |
| `objet-qualite` (existant « quality ») | idem à 1536, remaillage 768, 400 k faces, 4K, normale + AO | GLB 42–45 Mo | 5090 |
| `objet-multivue` | 1–4 images (ou vues rendues par Qwen-Edit « angles ») → Pixal3D multivue → mêmes étages | GLB | 5090 ou GB10 |
| `objet-retexture` | GLB importé → voxels → étage texture TRELLIS.2 conditionné par image/texte → cuisson | GLB | spike |
| `objet-optimiser` | GLB → Decimate/Remesh/Weld/FillHoles → UV → glTF-Transform (meshopt + KTX2) | GLB léger | GB10 (CPU) |
| `objet-rig` | GLB → SkinTokens → squelette + poids → Blender (retarget, FBX) | GLB/FBX rigué | **pc1 seulement** |

### 4.3 Ordonnancement entre GB10 et 5090, budgets

- **Règle** : la 5090 est la machine du cinéma (`h3-max`, 290 s par plan). Mesure amont : en travaillant à côté d'autres modèles résidents, TRELLIS.2 « High » a fait monter la VRAM de la 5090 à **30,5 Go sur 32,6** ; ComfyUI a évincé d'autres modèles pour tenir [MESURÉ amont]. Donc : **aperçu et brouillon sur la GB10 par défaut** (128 Go unifiés, aucune éviction, int8 `convrot` déjà utilisé chez nous pour Qwen-Image 2.1 et MiniMax-Music3 [LOCAL]) ; **qualité et débordement sur la 5090 quand elle est libre** ; rigging et exports Blender sur pc1. Le manifeste du registre gagne un champ `arch` (`x86_64` ou `aarch64`) pour que le planificateur n'envoie pas un job Blender à la GB10.
- **Vitesses** : TRELLIS.2 sur H100 : 3 s (512³), 17 s (1024³), 60 s (1536³) [RÉSUMÉ, README]. Sur 5090 partagée : Brouillon 91 s à chaud (85 s avec 32 images de tournette), Qualité 240 s [MESURÉ amont]. **Sur GB10 : aucune mesure** ; la bande passante mémoire de la GB10 (≈ 273 Go/s) est très inférieure à celle de la 5090, on peut attendre 2 à 4 fois plus long [ESTIMÉ]. L'objectif « aperçu 30–60 s » est plausible sur la 5090 en 512³ [ESTIMÉ 15–30 s] et à vérifier sur la GB10. Le premier banc tranche.
- **Disque** : GB10 44 Go libres [LOCAL] ; 28 Go de modèles déjà présents. Le lot minimal ci-dessous tient sans rien retirer. Règle : **au plus 2 modèles de forme** (TRELLIS.2 + Pixal3D, qui partagent VAE et encodeur DINOv3) et **1 modèle de texture** (l'étage texture de TRELLIS.2, même fichier que la forme) ; rien d'autre.
- **Quantification** : `trellis_2_int8_convrot` (5,25 Go) au lieu de `trellis_2_bf16` (10,34 Go) sur la GB10 pour économiser 5 Go ; qualité à comparer sur un jeu d'or de 10 images avant d'adopter [ESTIMÉ].

### 4.4 Rôle du LLM et du juge

- **Réécriture** (`reecritureImage.ts` existe) : prompt libre → fiche objet ; extraction de la hauteur réelle probable (équivalent de `auto_size` de Meshy) et de la pose (A/T pour un personnage).
- **Image de référence** : Qwen-Image produit 4 candidats ; contrôles en code d'abord (sujet unique, détourage BiRefNet non vide, marge autour du sujet, pas de recadrage), puis le **juge visuel** note : objet complet, vue 3/4, éclairage neutre, parties cachées plausibles, absence de texte parasite.
- **Juge de résultat** (`juge.ts`) : on rend 4 vues (0°, 90°, 180°, 270°) avec `RenderMesh` ; le juge compare à l'image de référence et note silhouette, parties flottantes, face arrière plausible, couture de texture, matière (le CHANGELOG amont relève des textures « martelées » sur un émail lisse et des doigts fusionnés). En dessous du seuil : nouvelle graine, jusqu'à N essais, et le crédit n'est facturé que pour la prise retenue (le grand livre de `credits.ts` sait déjà libérer une réservation). Idée reprise de l'indicateur de stabilité en boucle (rendre, régénérer, comparer) du banc Cyc3D (arXiv 2608.28080) [RÉSUMÉ].
- **Garde-fous** : modération du prompt (`moderation.ts` existe), refus des sujets exclus.

### 4.5 Crédits et devis

`credits.ts` calcule déjà devis = secondes GPU estimées × tarif (0,5 crédit/s par défaut, valeur à valider par le fondateur). On ajoute les mesures 3D dans la table de mesures (aperçu, brouillon, qualité, multivue) et on réserve avant, valide à la réussite, libère à l'échec. Ordres de grandeur avec ce tarif : aperçu ≈ 10, brouillon ≈ 45, qualité ≈ 120 crédits ; pour comparaison, Meshy affiche 20 crédits pour un aperçu texte, 30 pour une image → 3D. Un jeu de 4 candidats d'image ajoute le coût Qwen. Le prix reste une décision du fondateur.

### 4.6 Formats et validation

Contrôles en code avant toute livraison (trimesh + manifold3d, CPU, aarch64 OK) : maillage en variété et étanche (sinon réparation `manifold3d`, sinon avertissement), nombre de composantes, faces dégénérées, nombre de faces dans ±10 % de la cible, UV dans [0,1] sans recouvrement notable, textures aux dimensions annoncées, aucune valeur NaN, boîte englobante et orientation (Y haut, face vers +Z, pieds à l'origine), poids du fichier. Puis glTF-Validator pour les GLB. Sorties par bibliothèque : GLB (natif), OBJ/STL/PLY/3MF (trimesh), USDZ (three.js `USDZExporter` côté navigateur ou Blender), FBX/BLEND (Blender sur pc1). Copie « web » : glTF-Transform (meshopt, KTX2, textures 2K) pour la visionneuse et le partage.

### 4.7 Liens avec la vidéo (H3) et le « projet long »

- **Tournette comme référence** : la tournette mp4 et les 4 vues rendues deviennent des images de référence pour H3 (cohérence d'un objet ou d'un personnage d'un plan à l'autre). Les vues peuvent être restylées par Qwen-Edit pour passer du rendu clay au rendu photo avant H3.
- **Scène** : le GLB est servi en `model/gltf-binary` (déjà fait amont) et peut être chargé par l'app « Stage » (three.js) pour composer une scène, rendue par le moteur puis passée à H3 en image de départ.
- **Bible de scène du projet long** : chaque personnage ou accessoire récurrent reçoit une entrée `asset3d` (GLB, 4 vues canoniques, taille réelle, notes de matière, graine). Le Director et le planificateur de plans y puisent leurs références ; modifier l'asset invalide les plans qui l'utilisent.

## 5. Première tranche : bout en bout sur une seule machine, en quelques jours

**Machine : la GB10** (nœuds déjà présents, poids ≈ 14 Go, aucun noyau à compiler).

Jour 1 : télécharger le lot A (sur autorisation) ; lancer le modèle de workflow officiel `3d_pixal3d_trellis2_image_to_model` puis `buildTrellisGraph` en mode `draft` sur 10 images ; **mesurer** temps, mémoire, qualité (jeu d'or) en bf16 puis int8.
Jour 2 : activer la page Object dans l'app Nexora (crédits, licence `trellis2` déjà permise, nom de produit), ajouter la recette `objet-apercu` (512³, sans tournette).
Jour 3 : texte → 3D (réécriture + 4 candidats Qwen-Image + choix + Object), juge sur 4 vues.
Jours 4–5 : exports trimesh (OBJ/STL/PLY/3MF) + rapport de validation + copie web glTF-Transform ; bibliothèque et partage.
Critère de réussite : prompt → GLB texturé validé, 2 minutes ou moins sur la GB10 en brouillon, crédits réservés puis validés, rapport de validation affiché.

**Risques d'installation de cette tranche** : (1) version du moteur : le fork a été câblé sur ComfyUI 0.38.2, la GB10 est en 0.43.2 (nœuds susceptibles d'avoir changé de noms ou d'entrées : relancer l'export des workflows et comparer) ; (2) noyaux int8 `convrot` pour TRELLIS.2 non essayés sur sm_121 (ceux de Qwen-Image 2.1 marchent) ; (3) `RenderMesh` coûte du temps par image (reconstruit son BVH à chaque image) ; (4) le DINOv3 d'origine est protégé par une approbation manuelle chez Meta ; la copie Comfy-Org est librement téléchargeable, mais ses conditions d'usage (exclusions militaires, rétro-ingénierie) sont celles de la licence DINOv3 et déjà notées dans `THIRD_PARTY_NOTICES.md` ; (5) la 5090 a connu 30,5/32,6 Go de VRAM en usage partagé : ne pas lancer un brouillon 3D pendant un plan `h3-max`.

### Poids à faire autoriser (tailles lues par l'API HF le 03/11/2026 [LU])

| Lot | Fichier | Taille | Quand |
|---|---|---|---|
| **A1 (obligatoire)** | `trellis_2_bf16.safetensors` (Comfy-Org/TRELLIS.2) | 10,34 Go | tranche 1 |
| A1 | `trellis_2_shape_vae_bf16.safetensors` | 1,10 Go | tranche 1 |
| A1 | `trellis_2_texture_vae_bf16.safetensors` | 0,95 Go | tranche 1 |
| A1 | `dino_v3_vit_l.safetensors` | 1,21 Go | tranche 1 |
| A1 | `birefnet.safetensors` (Comfy-Org/BiRefNet) | 0,44 Go | tranche 1 |
| **Total A1** | | **≈ 14,04 Go** | |
| A2 (variante GB10, au lieu de la ligne bf16) | `trellis_2_int8_convrot.safetensors` | 5,25 Go (soit ≈ 8,95 Go au total) | si le banc int8 est équivalent |
| **B (multi-images)** | `pixal3d_multiview_int8_convrot.safetensors` (Comfy-Org/Pixal3D) | 5,58 Go | tranche 3 |
| B | `moge_2_vitl_normal_fp16.safetensors` (Comfy-Org/MoGe) | 0,66 Go | tranche 3 |
| **C (rigging, pc1 seulement)** | SkinTokens : `grpo_1400.ckpt` + `last.ckpt` | 1,13 + 0,49 = 1,62 Go | phase 4 |
| C (si SkinTokens insuffisant) | UniRig : squelette 1,44 Go + peau 4,38 Go | 5,82 Go | phase 4 |

Déjà présents ou déjà autorisés pour d'autres usages : Qwen-Image, Qwen-Image-Edit-2509 et la LoRA « Multiple-angles » (utilisées par `edit-angle.json`).

## 6. Feuille de route classée

| Rang | Lot | Contenu | Effort | Machine | Dépend de |
|---|---|---|---|---|---|
| 1 | Activer Object + banc de mesure | lot A1, bancs GB10 et 5090, jeu d'or de 10 images, bf16 vs int8 | 1 j | GB10 | autorisation des poids |
| 2 | Recette aperçu + crédits + registre | `objet-apercu`, extension du registre (`famille`, `tache`, `arch`), mesures de devis | 2 j | GB10 | 1 |
| 3 | Texte → 3D | réécriture, 4 candidats Qwen-Image, juge d'image, Object | 2–3 j | GB10 | 2 |
| 4 | Juge de résultat + relances | 4 vues rendues, note, N essais, facturation de la prise retenue | 2 j | GB10 | 3 |
| 5 | Exports + validation + partage | trimesh, glTF-Transform, USDZ client, rapport, `<model-viewer>` | 3 j | GB10 | 2 |
| 6 | Polycount et gabarits | Decimate/Remesh/Weld/FillHoles, présélections Jeu/Web/Impression, échelle | 2 j | GB10 | 5 |
| 7 | Multi-images | Pixal3D multivue (lot B), vues Qwen-Edit | 3–4 j | 5090/GB10 | 4 |
| 8 | Retexture d'un GLB | spike `imgshape2tex`, repli MV-Adapter / Material-Anything | 2–3 j | 5090 | 7 |
| 9 | Impression 3D | manifold3d, 3MF, mise à l'échelle en mm | 2 j | GB10 | 6 |
| 10 | Vidéo et projet long | tournette/vues → références H3, Stage, entrée `asset3d` | 3–4 j | — | 4 |
| 11 | API publique, MCP, greffon Blender | recettes signées, `make_3d`, client REST Blender | 4–5 j | — | 5 |
| 12 | Blender sur pc1 : FBX, BLEND, quad | service x86_64, QuadriFlow, retargeting | 4 j | pc1 | 5 |
| 13 | Rigging et animation | SkinTokens/UniRig, bibliothèque CC0 à vérifier | 5+ j | pc1 | 12 |
| 14 | Veille | Meshy T2, TaoFlowForge, Channel Match, UltraShape | continu | — | — |

## 7. Risques

1. **Vitesse non mesurée sur GB10.** Toutes les mesures connues sont celles de l'amont sur une 5090 partagée ou celles de H100 publiées par Microsoft. L'objectif « aperçu en 30–60 s » peut n'être atteint que sur la 5090, donc en concurrence avec H3. À trancher au jour 1 par un banc.
2. **Plafond de qualité inférieur à Meshy.** Pas de modèle ouvert égal à Meshy 7.1 ni à Smart Topology ; défauts relevés en pratique : texture martelée sur surface lisse, doigts fusionnés, visage mou, dos inventé, buste coupé net [MESURÉ amont]. Pas de quad « artiste » : un remaillage quad-dominant ne donne pas des boucles d'arêtes propres. Le mode doit se vendre sur l'intégration (texte → image → 3D → vidéo → projet long), pas sur l'égalité de topologie.
3. **Dérive de ComfyUI et de ses nœuds 3D.** Les nœuds TRELLIS.2 sont jeunes et évoluent vite (0.38.2 le 17/10, 0.43.2 sur la GB10 au 30/10) ; le fork a été écrit pour 0.38.2. Il faut figer la version du moteur, exporter les workflows, tester à chaque mise à jour. ComfyUI est en GPL-3.0 : le garder comme processus interne, ne jamais importer son code dans le portail (règle déjà posée dans `ARCHITECTURE-NEXORA-CREATIVE.md`).
4. **Limites aarch64.** Pas de `bpy` ni de Blender officiel pour Linux ARM : FBX, BLEND, quad par QuadriFlow, retargeting et rigging (UniRig exige `bpy==4.2`, flash-attn, spconv, torch_scatter ; SkinTokens exige flash-attn et torch 2.7 cu128) ne peuvent tourner que sur pc1. Tout ce qui est « rigué » dépend donc d'une seule machine x86_64 et de wheels Blackwell non essayés (spconv sur sm_120 en particulier).
5. **Licences et conditions d'accès des poids.** Faits relevés : Hunyuan3D (famille Tencent) hors UE, Royaume-Uni, Corée ; SPAR3D plafonné à 1 M$ de revenu annuel ; DINOv3 sous licence Meta avec exclusions et approbation manuelle chez l'éditeur ; SAM 3D sous « SAM License » non détaillée ici ; UltraShape, Instant Meshes, QuadriFlow sans licence déclarée par l'API de dépôt. Le registre de licences (`licences.ts`) doit recevoir chaque ensemble 3D avant toute mise en ligne (échec fermé).
6. **Mémoire et files partagées.** Un brouillon 3D lancé pendant un plan `h3-max` sur la 5090 frôle les 32 Go ; sans règle d'ordonnancement, les deux se gênent. Aussi : `RenderMesh` coûte du temps par image, la tournette augmente le délai de façon sensible (+ 110 s pour 48 images en 400 k faces).
7. **Bibliothèque d'animations.** Pas d'équivalent ouvert vérifié aux 500 actions de Meshy ; ne pas promettre « animer » avant d'avoir une source libre de droits claire.

## 8. Sources principales

- Meshy : docs.meshy.ai/en (text-to-3d, image-to-3d, multi-image-to-3d, retexture, remesh, rigging-and-animation, animation) ; meshy.ai/pricing [RÉSUMÉ].
- Microsoft TRELLIS.2 : github.com/microsoft/TRELLIS.2 ; huggingface.co/microsoft/TRELLIS.2-4B ; arXiv 2512.14692 [RÉSUMÉ, API HF et GitHub LUES pour licence et tailles].
- ComfyUI : `comfy_extras/nodes_trellis2.py`, `nodes_mesh_postprocess.py`, `nodes_save_3d.py`, `comfy/ldm/trellis2/*` sur GitHub master et dans `/home/pc6/nexora-creative-data/engine/ComfyUI` ; docs.comfy.org/tutorials/3d/trellis2 [LU].
- HF Comfy-Org/TRELLIS.2, Pixal3D, BiRefNet, MoGe ; VAST-AI/UniRig, SkinTokens ; tencent/Hunyuan3D-2.1 [LU : arbres de fichiers].
- Licence Hunyuan 3D 2.1 : raw.githubusercontent.com/Tencent-Hunyuan/Hunyuan3D-2.1/main/LICENSE [LU]. Licence Stability : stable-point-aware-3d/LICENSE.md [LU].
- UniRig : README et requirements.txt [LU] ; SkinTokens, Step1X-3D, SAM 3D Objects, Meshy T2 : READMEs [RÉSUMÉ].
- DGX Spark / GB10 : natolambert/dgx-spark-setup, discussions NVIDIA sur flash-attn aarch64 et TRELLIS.2 [RÉSUMÉ ; fil TRELLIS.2 non lisible en entier].
- Papiers (résumés) : arXiv 2607.28675 (Meshy T2), 2609.37139, 2610.15321, 2608.23943, 2610.22352, 2604.08746, 2605.13129, 2605.10922 (Pixal3D), 2602.04805 (SkinTokens), 2608.28080 (Cyc3D), 2607.22738 (Nova3D).
- Fork : `app/server/graphs/trellis.ts`, `app/server/models.ts` (ensemble `trellis2`), `app/server/nexora/licences.ts`, `credits.ts`, `registre.ts`, `juge.ts`, `app/CHANGELOG.md` (mesures amont), `app/docs/MODELS.md`.
