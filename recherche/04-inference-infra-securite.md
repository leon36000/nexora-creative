# 04 — Infrastructure d'inférence image/vidéo multi-moteurs, workers GPU isolés, sécurité multi-client

Date de l'étude : 30 octobre 2026 (poste d'étude : le GB10 lui-même, aarch64).
Périmètre : moteurs d'inférence, orchestration de workers, sécurité multi-client, gestion multi-modèles/GPU, spécificités GB10.
Contraintes respectées : aucune installation, aucun compte, aucune dépense, aucun téléchargement de poids, aucun code cloné exécuté (lecture seule).

## 0. Légende des preuves et limites de la méthode

| Tag | Sens |
|---|---|
| **[CODE]** | Lu dans le code source cloné (`git clone --depth 1`, commit daté de la semaine du 29-30/10/2026). Chemins sous `/tmp/claude-1000/-home-pc6--claude-spares-spare-nqfgQg/4a161a25-a3c4-4a78-94f6-c7dc7ebef37d/scratchpad/infra/<nom>/repo/`. |
| **[DOC]** | Documentation officielle ou page web lue (README, docs, blog, forum). |
| **[TEST]** | Observation faite par moi sur CE poste, en lecture seule (`nvidia-smi`, `nvcc --version`, `free`, `uname`). Aucun benchmark n'a été lancé. |
| **[MESURÉ publié]** | Chiffre mesuré et publié par un tiers (équipe du projet, NVIDIA, forum). Je ne l'ai pas reproduit. |
| **[INFÉRENCE]** | Mon raisonnement à partir des éléments ci-dessus. À valider par un spike. |
| **[NON VÉRIFIÉ]** | Connaissance générale ou résultat de recherche non confirmé à la source. Ne pas bâtir de décision dessus sans test. |

Limites à connaître :
1. Les outils `firecrawl_*` et `exa` ont répondu « crédits épuisés » (erreurs 402) dès le premier appel. Je n'ai donc pas pu les utiliser. J'ai utilisé `WebSearch` et `WebFetch` à la place. **Les pages récupérées par `WebFetch` sont résumées par un petit modèle** : les chiffres cités ci-dessous sont ceux de ces résumés, relus pour cohérence, mais ils méritent un second contrôle sur la page d'origine avant un engagement financier. AlphaXiv n'a pas été utilisé (la question porte sur du code et de l'infra, pas sur des articles).
2. Je n'ai pas lu le code existant de Nexora (Next.js 16, worker Node/TS, file PostgreSQL, grand livre de crédits, Privacy Router). Le contrat proposé en section 5 est donc écrit pour s'y brancher, mais il n'est pas confronté à vos tables réelles.
3. Aucune mesure sur RTX 5090 ni RTX 5080 : ces machines ne sont pas ce poste. Tout chiffre 5090/5080 est publié par un tiers.
4. Le GB10 de ce poste ne contient pas PyTorch (`ModuleNotFoundError: torch`), donc je n'ai pas pu lire `torch.cuda.get_arch_list()`.

### Dépôts audités (commits cloné le 30/10/2026)

| Dépôt | Dernier commit | Licence | Remarque |
|---|---|---|---|
| hao-ai-lab/FastVideo | 2026-10-30 | Apache-2.0 | Doc Spark complète |
| ModelTC/LightX2V | 2026-10-29 | Apache-2.0 | |
| sgl-project/sglang (multimodal_gen) | 2026-10-30 | Apache-2.0 | SGLang-Diffusion |
| xdit-project/xDiT | 2026-10-29 | Apache-2.0 | |
| vllm-project/vllm-omni | 2026-10-30 | Apache-2.0 | release 0.32.0 |
| huggingface/diffusers | 2026-10-29 | Apache-2.0 | 0.42.0.dev0 |
| comfyanonymous/ComfyUI | 2026-10-29 | **GPL-3.0** | v0.43.0 |
| Comfy-Org/comfy-cli, ComfyUI-Manager | 2026-10-28/30 | non relu | |
| nunchaku-tech/nunchaku | 2026-09-06 | `LICENCE.txt` non relue | v1.2.0 (janv. 2026), peu actif |
| thu-ml/SageAttention | 2026-01-17 | Apache-2.0 | peu actif |
| vipshop/cache-dit | 2026-10-30 | Apache-2.0 | |
| NVIDIA/TensorRT | 2026-10-09 | non relu | 11.4 GA |
| NVIDIA/TensorRT-Model-Optimizer | 2026-10-30 | non relu | |
| SaladTechnologies/comfyui-api | 2026-09-18 | MIT | v1.19.2 |
| runpod-workers/worker-comfyui | 2026-09-21 | **AGPL-3.0** | |
| ViewComfy/ViewComfy | 2026-03-19 | **AGPL-3.0** | |
| comfy-deploy/comfydeploy | 2025-09-19 | **GPL-3.0** | inactif depuis un an |
| BennyKok/comfyui-deploy | 2025-11-12 | non relu | ancien dépôt |
| bentoml/comfy-pack | 2025-11-10 | Apache-2.0 | |
| mcmonkeyprojects/SwarmUI | 2026-10-30 | MIT | |
| replicate/cog | 2026-10-27 | Apache-2.0 | |
| beam-cloud/beta9 | 2026-10-29 | **AGPL-3.0** | |
| ai-dynamo/dynamo | 2026-10-30 | en-tête vide à la lecture | orienté LLM |
| kubernetes-sigs/kueue, NVIDIA/KAI-scheduler | 2026-10-30/28 | Apache-2.0 | |
| skypilot-org/skypilot | 2026-10-30 | Apache-2.0 | |
| NVIDIA/dcgm-exporter | 2026-09-18 | Apache-2.0 | |
| temporalio/sdk-typescript | 2026-10-30 | MIT | SDK 1.25.0 |
| taskforcesh/bullmq | 2026-10-30 | MIT | 6.5.1 |

Note licences [INFÉRENCE, pas un avis juridique] : ComfyUI est GPL-3.0. L'utiliser comme processus séparé derrière une API interne, sans le distribuer à des tiers, ne déclenche pas d'obligation de publication pour un service SaaS (la GPL n'est pas l'AGPL). En revanche, embarquer du code AGPL (worker-comfyui, ViewComfy, beta9) dans le service ou le modifier et l'exposer aux utilisateurs poserait la question de la publication du code source modifié. Faites valider par un juriste avant de copier du code AGPL.

---

## 1. Synthèse et décisions recommandées

1. **Ne jamais exposer ComfyUI. Le traiter comme un moteur d'exécution de graphes interne, à confiance nulle.** Le code montre qu'il n'a aucune authentification propre (aucun middleware d'auth dans `server.py`, seulement un filtre Origin/Host et un en-tête CORS optionnel) **[CODE]**. Un botnet de minage a compromis plus de 1 000 instances ComfyUI exposées en 2026 via des nœuds personnalisés qui exécutent du Python brut **[DOC]** (The Hacker News, 7 avril 2026).
2. **Le contrat utilisateur est une « recette » (recipe) typée et versionnée, jamais un workflow.** Le serveur compile la recette en graphe ComfyUI (ou en appel natif à un autre moteur). L'utilisateur ne soumet jamais un graphe, un chemin, une URL de modèle ou un nom de nœud.
3. **Garder la file PostgreSQL `SKIP LOCKED` pour le MVP**, en y ajoutant bail (lease) + heartbeat + jeton de fencing + idempotence + annulation coopérative + comptabilité de crédits en trois temps (réserver/valider/libérer). Aucun orchestrateur évalué n'apporte assez pour justifier une brique de plus avec 3 machines hétérogènes (x86 + aarch64). Temporal devient pertinent si on dépasse environ 3 étapes durables par job (génération puis upscale puis interpolation puis mux) ou si des workflows humains longs apparaissent.
4. **Un moteur = un adaptateur derrière une interface unique** (`EngineAdapter`). Les moteurs ont tous des files de jobs en mémoire, perdues au redémarrage (FastVideo, SGLang, vLLM-Omni, LightX2V, ComfyUI) **[CODE]/[DOC]**. La durabilité, la reprise et les crédits doivent donc vivre côté Nexora, pas dans le moteur.
5. **GB10 : machine de capacité, pas de débit.** Mesure publiée la plus comparable : même modèle (FastH3 V2, NVFP4, 832×480, clip de 5 s, 8 pas) en **14,8 s sur RTX 5090 contre 141,4 s sur DGX Spark, soit 9,6 fois plus lent** **[MESURÉ publié]**. Rôle recommandé : gros modèles qui ne tiennent pas en 32 Go, jobs batch/qualité en arrière-plan, modèles résidents multiples, ComfyUI/outils de préparation. Pas de promesse de latence interactive vidéo.
6. **Pile PyTorch GB10** : des roues `torch 2.14.1+cu130` pour `linux_aarch64` existent sur `download.pytorch.org/whl/cu130` **[DOC]** (résumé WebFetch de l'index, à reconfirmer en listant l'index vous-même). ComfyUI recommande explicitement l'index `cu130` **[CODE]** (README). Le point dur est la couche des noyaux spécialisés (NVFP4, FlashAttention 4, SageAttention3, noyaux CUTLASS) qui ciblent `sm_120a` et non `sm_121a` : voir section 2.3.
7. **Sandbox** : conteneurs durcis sans accès réseau sortant, système de fichiers racine en lecture seule, poids montés en lecture seule, scratch `tmpfs` par job, un seul job actif par GPU. gVisor ne documente pas de support GPU grand public/Blackwell (liste nvproxy : T4, L4, A100, A10G, H100) **[DOC]** ; Kata/Firecracker exigent un passthrough VFIO impossible sur un GPU intégré comme le GB10 **[INFÉRENCE]**. Ne pas planifier sur gVisor/Kata pour le MVP.
8. **Spikes à faire avant de s'engager** (section 9) : une journée par moteur sur chaque machine, chronomètre en main, en commençant par les trois qui comptent : FastVideo sur GB10, ComfyUI sur 5090 avec nœuds figés, SGLang-Diffusion sur 5090.

---

## 2. Moteurs d'inférence

### 2.1 Tableau comparatif

| Moteur | Rôle | API serveur native | Blackwell grand public (sm_120) | GB10 (sm_121, aarch64, CUDA 13) | File/état des jobs | Annulation | Points d'attention |
|---|---|---|---|---|---|---|---|
| **FastVideo** | Vidéo (Wan, LTX2, HunyuanVideo 1.5, Kandinsky, FastH3…) + images FLUX/SD3.5 + audio | Oui : REST compatible OpenAI `/v1/videos`, `/v1/images`, `fastvideo serve`, `router-serve`, streaming WebSocket **[CODE]** | Oui : recette `openai_compacth3_rtx5090.yaml` (CompactH3 NVFP4 sur une 5090) **[CODE]** | **Supporté et documenté** : guide `installation/spark.md`, page `spark_performance.md`, benchmark `wan-t2v-1.3b-1gpu-gb10`, noyau `fastvideo-kernel` compilé depuis les sources (pas de roue aarch64) **[CODE]/[DOC]** | `AsyncDictStore` en mémoire, verrou global de génération `_generation_lock` : **un job à la fois**, perdu au redémarrage **[CODE]** | `DELETE /v1/videos/{id}` annule la tâche asyncio, mais le code reconnaît que Python ne peut pas arrêter un thread de calcul en cours **[CODE]** (`serving_engine.py`) | Politique média intégrée (`media_roots`, URL privées refusées par défaut, limite 2 Gio) **[CODE]**. Meilleure preuve GB10 du lot |
| **LightX2V** | Vidéo/image très optimisée (Wan, HunyuanVideo, Qwen-Image, modèles temps réel) | Oui : FastAPI `POST /v1/tasks/video|image`, `/v1/files`, métriques Prometheus **[CODE]** | Oui, très ciblé 5090 (images Docker `…cu130-5090…`, scripts `run_5090.sh`) **[CODE]** | **Non documenté.** Noyaux NVFP4/MXFP4/FP8 compilés par défaut pour `120a` uniquement (`LIGHTX2V_GPU_ARCH` ∈ {90a,120a}) **[CODE]** | `TaskManager` en mémoire, file max 100, statuts pending/processing/completed/failed/cancelled **[CODE]** | `cancel_task` + `stop_event` **[CODE]** | Téléchargeur d'URL avec `verify=False` et `follow_redirects=True`, sans filtre d'adresses privées dans les lignes lues (SSRF) **[CODE]** (`file_service.py`) |
| **SGLang-Diffusion** | Image/vidéo (Wan, FLUX, Qwen-Image, LTX-2.x, MiniMax-H3, Z-Image…) | Oui : `sglang serve`, API OpenAI `/v1/videos`, `/v1/images`, plugin ComfyUI **[CODE]/[DOC]** | Oui (README liste 4090/5090) **[CODE]** | **Pas dans la liste de plateformes du README.** Seule mention : JIT `convrot_int8` pour CC 12.0/12.1 « DGX Spark » **[DOC]** (`quantization.mdx`) | Métadonnées de jobs **« process-local, perdues au redémarrage »** ; reprise, propriété durable et admission exigent « une couche externe » **[DOC]** | `DELETE /v1/videos/{id}` : arrêt après le pas de débruitage courant, **mono-nœud monolithique seulement** ; ailleurs, supprime l'enregistrement sans arrêter le GPU **[DOC]** | Meilleure observabilité : métriques Prometheus (`diffusion_num_queue_reqs`, `queue_time_seconds`…) ; résidence par composant (`--component-residency`) ; désagrégation encodeur/débruiteur/décodeur |
| **xDiT** | Parallélisme multi-GPU pour DiT (USP, PipeFusion, CFG parallèle) | Bibliothèque/runner, pas un service de jobs | Mentionne Blackwell pour attention (FAv4, FP8) **[DOC]** | Rien sur GB10 | n/a | n/a | Utile seulement avec plusieurs GPU reliés. Aucun intérêt pour 1 GPU par nœud sans NVLink **[INFÉRENCE]** |
| **vLLM-Omni** (0.32.0) | Omni (texte/audio/image/vidéo) + DiT | Oui : `/v1/videos` (+`/sync`), `/v1/images`, `/v1/audio` **[CODE]/[DOC]** | Oui ; `TRTLLM_ATTN` **non** auto-sélectionné sur sm_120/121 ; `SAGE_ATTN_3` possible **[DOC]** | Cité dans la plage « sm_100/103/120/121 » ; VSA FastVideo via FlashInfer sur SM121 ; « SM121 BF16 suit les exigences du noyau amont » **[DOC]**. Sur une Spark, la recette MiniMax H3 de vLLM-Omni a pris **1 881 s** pour un clip de 5 s en 1024×576 à 50 pas **[MESURÉ publié]** (blog FastVideo) | Jobs en mémoire, « perdus au redémarrage, non partagés entre répliques » **[DOC]** | `DELETE` avec abandon borné `VLLM_OMNI_ABORT_TIMEOUT` (2 s par défaut) **[DOC]** | Document de **matrice d'injection de pannes** (SIGTERM/SIGKILL/OOM) utile pour concevoir nos tests **[DOC]** |
| **diffusers** | Bibliothèque de référence | Aucune (c'est une bibliothèque) | Oui (backends d'attention : `sage_blackwell_hub`, etc.) **[DOC]** | Fonctionne en principe via PyTorch cu130 ; débit non optimisé | n/a | n/a | `use_safetensors=None` ⇒ **pickle autorisé si pas de safetensors** ; forcer `use_safetensors=True` et ne jamais activer `trust_remote_code` **[CODE]** (`pipeline_utils.py` : `allow_pickle = True if use_safetensors is None or False`) |
| **ComfyUI** (v0.43.0) | Moteur de graphes universel, écosystème le plus large | `POST /prompt`, `GET /history`, WebSocket `/ws`, `GET /api/jobs`, `POST /api/jobs/{id}/cancel`, `POST /interrupt {prompt_id}` **[CODE]** | Oui, référence | Fonctionne ; GPU intégré détecté, mémoire épinglée désactivée automatiquement **[CODE]** (`is_integrated_gpu`) ; gestionnaire de VRAM « dynamique » via `comfy-aimdo==0.6.0` **[CODE]** (`requirements.txt`) | File et historique **en mémoire** (`PromptQueue`, `MAXIMUM_HISTORY_SIZE = 10000`) **[CODE]** | `interrupt` ciblé par `prompt_id` ou global **[CODE]** | **Pas d'auth, graphe arbitraire, nœuds personnalisés = code arbitraire.** `prompt_id` UUID fourni par le client accepté **[CODE]** (clé d'idempotence côté adaptateur) |
| **Nunchaku** | Quantification SVDQuant 4 bits pour **images** (FLUX, Qwen-Image, SANA, Z-Image) | Bibliothèque + nœuds ComfyUI | NVFP4 sur sm_120 **[CODE]** | `setup.py` accepte `121a` si `nvcc ≥ 13.0` **[CODE]** ; non validé en bout en bout | n/a | n/a | Pas de vidéo. Dernier commit 2026-09-06, v1.2.0 de janvier 2026 : cadence ralentie. Documenté dans diffusers (`nvfp4` sur Blackwell) **[DOC]** |
| **TensorRT** (11.4 GA, 2026-10-09) | Compilation/optimisation | `demoDiffusion` **retiré** (CHANGELOG 11.3) **[CODE]** | n/a | Voir ci-dessous | n/a | n/a | La voie diffusion NVIDIA passe désormais par TensorRT-LLM « VisualGen » (bêta) et Dynamo (vidéo diffusion « expérimental ») **[DOC]** (résultats de recherche). Aucune preuve trouvée d'un Wan/FLUX NVFP4 via VisualGen mesuré sur GB10 |
| **TensorRT Model Optimizer** | Quantification PTQ (FP8, INT8, NVFP4, SVDQuant) pour diffusers | Outil hors ligne | NVFP4 « nécessite Blackwell et TensorRT-LLM ≥ 1.2 » **[CODE]** (README) | Pas de mention GB10 dans le README lu | n/a | n/a | À considérer pour produire NOS checkpoints NVFP4 internes (phase 2) |
| **SageAttention** | Attention quantifiée 8/4 bits | Bibliothèque | SA2++ et SA3 Blackwell (sm_120) **[CODE]** | `setup.py` génère `121a` ; `core.py` a une branche `sm121` ; SA3 `setup.py` gère `(12,1)` **[CODE]** | n/a | n/a | **Sur GB10, FastVideo mesure qu'aucune attention alternative n'aide** : la SDPA de PyTorch atteint déjà un noyau flash efficace sur sm_121 et FA2 fait jeu égal **[DOC]**. Dernier commit janvier 2026 |
| **Cache-DiT** | Cache de blocs, parallélisme, quantification pour DiT | Bibliothèque ; intégrée à SGLang et vLLM-Omni | Archs par défaut 89, 90a, 100, 120a ; `121` normalisé si nvcc le permet **[CODE]** | NVFP4 torchao « SM100+ » ; `ffpa_fp4` « sm_120 uniquement » **[CODE]** | n/a | n/a | Gain pur sur le calcul (moins de pas effectifs). Sur GB10, utile surtout pour les modèles dont le débruitage domine |

### 2.2 Ce que le code révèle sur la durabilité des jobs

Aucun des moteurs évalués ne persiste ses jobs : FastVideo (`AsyncDictStore`), LightX2V (`TaskManager`), SGLang (« process-local »), vLLM-Omni (« lost on restart »), ComfyUI (`PromptQueue.history`). **Conséquence directe pour l'architecture : Nexora possède l'état du job (PostgreSQL) ; le moteur est un exécutant sans mémoire.** Un redémarrage du moteur en plein job se traduit par « bail expiré, nouvelle tentative », jamais par « le moteur reprend ».

Un seul job actif à la fois par processus moteur (FastVideo : verrou explicite `_generation_lock`) est la bonne granularité pour les GPU grand public. Pas de co-location de jobs sur un GPU de 16 ou 32 Go.

### 2.3 Blackwell sm_121 / aarch64 / CUDA 13 / NVFP4 : état réel

**Mesuré sur ce poste [TEST]** : `NVIDIA GB10`, capacité de calcul `12.1`, pilote `580.178.04`, `nvcc 13.0.88` (CUDA 13.0), `nvidia-smi` rapporte la mémoire en `[N/A]`, 121 Gio de RAM unifiée visibles, 20 cœurs, Docker 29.6.2.

**PyTorch**
- Roues `torch 2.14.1+cu130`, `manylinux_2_28_aarch64`, pour cp310 à cp314 sur l'index `https://download.pytorch.org/whl/cu130/` **[DOC]** (résumé WebFetch).
- Historique : en octobre 2025–janvier 2026, un employé PyTorch indiquait que les binaires CUDA ≥ 12.8 pour ARM supportent déjà le Spark car `sm_121` est binairement compatible avec `sm_120`, et que compiler pour `sm_121` ne donne pas de gain ; les instructions tensor-core « a » (`sm_121a`) sont à part **[DOC]** (forum PyTorch, fil « DGX Spark GB10 Cuda 13.0 Python 3.12 SM_121 »). Un échec connu de ce fil : noyau CUTLASS `fmha_cutlassF_f16_aligned_64x128_rf_sm80` refusant `sm121` dans une compilation source de PyTorch 2.9 nightly **[DOC]** — ancien, à ne pas supposer résolu sans test sur 2.14.
- NVIDIA : la version CUDA du Spark n'est « vérifiée » que pour la version logicielle livrée ; les dernières fonctionnalités passent par les conteneurs NGC **[DOC]** (page « Known Issues » DGX Spark).

**Noyaux spécialisés (le vrai risque)**
- FastVideo : le noyau `fastvideo-kernel` se compile à l'installation pour `sm_121`, avec `TORCH_CUDA_ARCH_LIST=12.1a` si aucun GPU n'est visible. « Le code spécifique `sm_120a` ne peut pas tourner sur `sm_121` » **[DOC]** (`spark.md`). Pas de FA4 ni de VSA `ptx_blackwell` sur GB10 : `FASTVIDEO_FA4=0`, `FASTVIDEO_VSA_PTX_BLACKWELL=0` **[DOC]**. Le VSA Triton se sélectionne seul sur `sm_121` **[DOC]**.
- LightX2V : noyaux NVFP4 compilés pour `120a` seulement **[CODE]**. **Hypothèse à tester** : ils ne s'exécutent pas sur `121`. Aucun texte du dépôt ne dit le contraire **[NON VÉRIFIÉ]**.
- NVFP4 sur GB10 : FastVideo indique que FP4 attention (`ATTN_QAT_INFER`) est numériquement correcte sur `sm_121`, ~6 % plus rapide en bout en bout, mais n'est valable que sur un checkpoint entraîné pour cela ; le FP4 linéaire donne jusqu'à −24 % de temps de débruitage sur LTX2 à 1080p mais environ 0 % sur les modèles à longue séquence (Cosmos) **[MESURÉ publié]** (`spark_performance.md`).
- ComfyUI : utilise `comfy-kitchen==0.2.40` pour les noyaux de quantification (NVFP4 inclus) **[CODE]** ; je n'ai pas pu établir si elle fournit des noyaux `sm_121` sans test.
- Le blog ComfyUI sur le Spark dit « tous les modèles que j'ai essayés fonctionnent » et ne publie aucun chiffre **[DOC]**.

**Problèmes connus GB10**
- `nvidia-smi` : mémoire « Not Supported » (GPU intégré) ; `cudaMemGetInfo` peut sous-estimer la mémoire allouable ; estimer via `/proc/meminfo` **[DOC]**. Le plugin de périphérique Kubernetes plante à la lecture de la mémoire GPU (issue k8s-device-plugin #1482) **[DOC]** (résultat de recherche). Conséquence : toute supervision GPU basée sur la VRAM libre échoue ; il faut une métrique côté worker (`peak_memory_mb` FastVideo, `/system_stats` ComfyUI).
- DCGM : je n'ai trouvé aucune page affirmant que DCGM/dcgm-exporter fonctionne ou non sur GB10. GPUDirect Storage : « Model Not Supported » sur GB10 **[DOC]** (forum NVIDIA). **[NON VÉRIFIÉ]** pour DCGM : à tester avec `dcgmi discovery -l`.
- FastVideo : les gros chargements de DiT sur la mémoire unifiée peuvent être pris pour un emballement et tués par un superviseur mémoire (le texte de `spark_pair.md` décrit un SIGTERM sur chargement de 14 shards) **[CODE]/[DOC]** ; les génération lourdes peuvent rendre la machine injoignable : utiliser `nice -n 19`, tuilage VAE, et une limite mémoire dans le conteneur **[DOC]**.
- Communauté (forum NVIDIA, 13 mai 2026) : Wan 2.2 en diffusers natif, 5 s de vidéo = « 30+ minutes » contre ~3 min dans ComfyUI sur un PC avec RTX 5070 (12 Go) ; l'échange attribue l'écart à la bande passante (273 contre 672 Go/s) plus au pipeline, pas à une panne **[MESURÉ publié, anecdotique]**.

### 2.4 Détails notables par moteur

**FastVideo** — `fastvideo serve` expose les routes `/v1/videos` (POST création asynchrone, POST `/sync`, GET liste, GET `{id}`, DELETE `{id}`, GET `{id}/content`) **[CODE]** (`entrypoints/openai/video_api.py`). Statuts : QUEUED, IN_PROGRESS, COMPLETED, FAILED. Le dépôt contient un tableau « ledger » de ce qui est réellement lançable, avec la mention « Source-backed » et non « validé sur GPU » pour la plupart des recettes (`docs/cookbook/serving-coverage.md`, audit du 19/10/2026) **[CODE]**. Il contient aussi `comfyui/` (intégration ComfyUI) et `apps/dreamverse` (streaming temps réel). C'est le moteur dont la documentation GB10 est la plus honnête et la plus détaillée.

**SGLang-Diffusion** — Désagrégation Encodeur / Débruiteur / Décodeur par `--disagg-role`, vérifiée de bout en bout sur 8×H200 seulement **[DOC]**. Les rôles désagrégés n'ont **pas** d'annulation GPU fonctionnelle. Intéressant pour plus tard (par exemple encodeur de texte sur le GB10, débruiteur sur la 5090), mais ce n'est pas un MVP. Le cache de conditionnement (`--disable-conditioning-cache` pour l'éteindre) met en cache en CPU des entrées texte/image répétées : à éteindre ou à isoler par locataire en mode strict **[INFÉRENCE]**.

**ComfyUI** — Points de code utiles :
- `POST /prompt` accepte `prompt_id` (UUID canonique) fourni par l'appelant, sinon le serveur en génère un **[CODE]** (`server.py` l.1170-1195).
- `POST /interrupt` avec `prompt_id` n'interrompt que si ce prompt est en cours ; sans `prompt_id`, interruption globale **[CODE]**.
- `/system_stats` renvoie `argv` complet, la liste des périphériques et la VRAM/RAM **[CODE]** : fuite d'information si exposé.
- `/free` décharge les modèles à la demande (utile pour la gestion de résidence) **[CODE]**.
- `--listen` vaut `127.0.0.1` par défaut ; `--enable-manager` est désactivé par défaut ; `--disable-all-custom-nodes` + `--whitelist-custom-nodes` existent ; `--disable-metadata` ; `--offline` coupe les nœuds partenaires (API payantes) ; `--base-directory`, `--input-directory`, `--output-directory`, `--user-directory` ; `--cache-none` / `--cache-ram` / `--cache-lru` ; `--cuda-device` ; `--reserve-vram` **[CODE]** (`comfy/cli_args.py`).
- **Module de gouvernance** (`app/governance.py`) : politique signée Ed25519 listant des paquets de nœuds autorisés **par empreinte blake3 du contenu** (`allowlist`) ou refusés (`blocklist`), refus des liens symboliques et du bytecode `.pyc`, refus de ComfyUI-Manager sous politique, nœuds désactivés par ID. **Mais** il n'est actif que si `GOVERNANCE_REQUIRED` est vrai, valeur codée en dur à `False` dans le dépôt cloné : c'est un mécanisme de « build gouverné » **[CODE]**. Il ne protège pas une installation standard, mais il montre le modèle à copier : liste d'autorisation par empreinte de contenu, pas par nom de dossier.
- Chargement des poids : `.safetensors` avec validation d'en-tête ; sinon `torch.load(..., weights_only=True)` **[CODE]** (`comfy/utils.py`). Cela protège les poids du cœur de ComfyUI, **pas** le code des nœuds personnalisés, qui peuvent appeler `torch.load` sans cette protection.
- Pas de bibliothèque embarquable officielle : on peut instancier `execution.PromptExecutor` dans son propre processus **[CODE]** (`execution.py` l.666), mais c'est une API interne non garantie. À ne pas retenir comme contrat stable.

**ComfyUI as a library / headless** — Mode headless = lancer `main.py` avec `--listen 127.0.0.1`, `--disable-all-custom-nodes`/liste blanche, sans frontend utile. `comfy-cli` sert à installer ComfyUI et ses nœuds par commande (`comfy --workspace … install --version …`, utilisé par `worker-comfyui` pour figer la version) **[CODE]**. Pour une image figée, installer ComfyUI + nœuds à la construction, jamais au démarrage.

### 2.5 Recommandation moteurs (par usage)

| Usage | Moteur primaire | Secours / alternative | Machines |
|---|---|---|---|
| Image (FLUX, Qwen-Image, SDXL, Z-Image) | ComfyUI compilé (écosystème, LoRA, ControlNet) ou SGLang-Diffusion/FastVideo pour les modèles supportés nativement | diffusers (scripts maîtrisés) ; Nunchaku NVFP4 sur 5090 pour la vitesse | 5090 (principal), 5080 (volume), GB10 (gros modèles) |
| Vidéo rapide (modèles distillés few-step) | FastVideo ou LightX2V sur 5090 | SGLang-Diffusion | 5090 |
| Vidéo qualité (14B+, plusieurs encodeurs) | FastVideo/SGLang sur GB10 en batch ; ComfyUI sur 5090 si le modèle quantifié tient | vLLM-Omni | GB10 |
| Étapes annexes (upscale, interpolation, mux) | ComfyUI ou ffmpeg dans un conteneur dédié | | 5080 |

Règle : ajouter un moteur seulement s'il a (a) un mode serveur avec annulation, (b) un contrôle des entrées média, (c) un journal exploitable. FastVideo, SGLang, vLLM-Omni et LightX2V le satisfont ; diffusers/xDiT/Nunchaku/SageAttention/Cache-DiT sont des briques, pas des serveurs.

---

## 3. GB10 : mémoire unifiée, latence et résultats publiés

### 3.1 Matériel [DOC]
- LPDDR5X 128 Go unifiée, interface 256 bits, **273 Go/s**, GPU Blackwell 6 144 cœurs CUDA, jusqu'à 1 PFLOP FP4 avec sparsité, SoC 140 W, alimentation externe 240 W, NVMe 1 ou 4 To, ConnectX-7 (2 QSFP), 10 GbE **[DOC]** (guide utilisateur DGX Spark).
- Mémoire utilisable par un travail : environ 118-121 Go **[DOC]** (FastVideo, blog FastH3).
- RTX 5090 : 32 Go GDDR7, bus 512 bits, 21 760 cœurs, 575 W, 3 352 « AI TOPS » ; RTX 5080 : 16 Go GDDR7, bus 256 bits, 10 752 cœurs, 360 W, 1 801 AI TOPS **[DOC]** (pages NVIDIA). Les débits mémoire ne figurent pas sur ces pages ; les valeurs usuelles (≈ 1 792 Go/s pour la 5090, ≈ 960 Go/s pour la 5080) sont **[NON VÉRIFIÉ]** ici, déduites de largeur de bus × cadence.

### 3.2 Implications pour la diffusion [INFÉRENCE]
- Un pas de DiT lit tous les poids actifs une fois : pour un DiT de 14 Go en FP8, la limite basse due à la bande passante est d'environ 51 ms/pas sur GB10 (14 / 273) contre ≈ 8 ms sur 5090 (14 / 1792). Mais les modèles vidéo ont de longues séquences et sont plutôt limités par le calcul d'attention (O(N²)) que par la lecture des poids ; le rapport 9-10× mesuré ci-dessous dépasse le rapport de bande passante (≈ 6,6) et le rapport de calcul affiché (≈ 3,4 en TOPS) : les noyaux moins optimisés sur `sm_121` y contribuent probablement.
- Le décodage VAE est limité par la bande passante : sur un modèle à peu de pas, c'est le goulot sur le GB10 (le bascule se situe vers 4 pas) **[MESURÉ publié]** (FastVideo `spark_performance.md`). Un VAE « léger » (TAEH3) fait passer le décodage de 114 s à 1,3 s sur 832×480 **[MESURÉ publié]** (blog FastH3).
- La quantification linéaire (FP8/NVFP4) apporte peu sur les modèles à longue séquence sur GB10, mais aide les modèles à séquence courte (LTX2 : −24 % de débruitage à 1080p) **[MESURÉ publié]**.
- Un avantage réel : la capacité. Un DiT de 65 Go tient, la RAM unifiée évite l'échange CPU↔GPU (pas de mémoire épinglée à gérer ; ComfyUI désactive l'épinglage sur GPU intégré **[CODE]**).

### 3.3 Résultats publiés (tous **[MESURÉ publié]**, non reproduits)

| Source | Machine | Modèle / réglage | Résultat |
|---|---|---|---|
| Blog FastVideo « FastH3 RTX » | RTX 5090 (32 Go) | FastH3 V2, NVFP4, 832×480, clip 5 s avec audio, 8 pas, médiane de 2 exécutions, serveur chaud | **14,8 s** (Trim : 13,4 s) |
| idem | RTX 5090 | FastH3 V2, 1344×768 | **38,6 s** (Trim : 35,4 s) |
| idem | DGX Spark | FastH3 V2, NVFP4, 832×480 | **141,4 s** (Trim : 125,8 s) |
| idem | DGX Spark | FastH3 Trim, 1344×768 | **340,1 s** (V2 : non rapporté) |
| idem | RTX 4090 (24 Go) | FastH3 V2, FP8, 832×480 / 1344×768 | 54,6 s / 154,6 s |
| idem | RTX PRO 6000 (96 Go) | FastH3 V2, NVFP4 | 13,5 s / 36,5 s |
| Blog FastVideo « FastH3 local » | 1 Spark | FastH3 V1, 832×480, 124 images, 4 pas, VAE complet | 264 s à froid, 243 s à chaud |
| idem | 1 Spark | 1024×576, clip 5 s : baseline vLLM-Omni 50 pas contre FastH3 4 pas | 1 881 s contre 268 s (≈ 7×) |
| FastVideo `spark_performance.md` | GB10 | FastWan2.1-T2V-1.3B, 3 pas | ≈ 40 s (≈ 39,3 s, pic 8,4 Go, ≈ 1,15 fps) |
| idem | GB10 | Wan2.1-T2V-1.3B 50 pas / Cosmos-Predict2.5-2B 51 pas / LTX2.3 distillé 8 pas + audio | ≈ 12 min / ≈ 47 min / ≈ 6 min |
| Forum NVIDIA (24/09/2026) | GB10 partagé avec 6 autres conteneurs | Wan 2.2 TI2V-5B fp16, 1280×704, 30 pas, ComfyUI 0.22.0 | 49 images : 417,6 s à froid / 330,2 s à chaud ; 121 images : 935,2 s / 848,4 s ; chargement du modèle ≈ 87 s |
| Fiche HF `lightx2v/LightWan2.2-A14B` | RTX 5090 | Wan 2.2 14B, NVFP4 + attention creuse, 4 pas ; référence 40 pas | T2V 480p : 9,1 s contre 734 s ; 720p : 22,5 s contre 2 668 s (nombre d'images non précisé ; revendication du projet) |
| Recherche web (résumé non vérifié à la source) | GB10 | Wan 2.2 14B fp16, 81 images, 640×640 | ≈ 557 s à froid / ≈ 370 s à chaud **[NON VÉRIFIÉ]** |
| Recherche web (résumé non vérifié) | RTX 5090 contre Spark | ComfyUI par défaut, mêmes modèles | 5090 ≈ 3,18× plus rapide **[NON VÉRIFIÉ]** |

Lecture [INFÉRENCE] : rapport 5090/GB10 observé sur un même modèle NVFP4 = **9,4× à 9,6×** (141,4/14,8 ; 125,8/13,4 ; 340,1/35,4). Budgétez le GB10 à environ **un dixième du débit d'une 5090** sur la vidéo quantifiée NVFP4, et plutôt un tiers à un quart sur des charges peu dépendantes de l'attention (le chiffre non vérifié de 3,18× vient d'un autre mélange de modèles). Comme les noyaux FP4 les plus rapides ciblent `sm_120a`, une partie de l'écart peut se réduire avec le temps (FastVideo traque l'allowlist `sm_121` dans les tickets #1598, #1647, #1632).

### 3.4 Recommandations GB10
1. **Rôle** : machine « qualité/capacité » en arrière-plan + hôte des modèles volumineux et des services annexes (VAE lourds, upscalers, LLM de prompt via LiteLLM). Pas de SLA d'interactivité vidéo.
2. **Modèles à privilégier** : distillés few-step, séquences courtes (LTX 2.x), VAE légers. Éviter les modèles 50 pas : 12 à 47 min **[MESURÉ publié]**.
3. **Limites de sécurité mémoire** : budget 128 Go partagés entre OS, caches de disque, conteneurs voisins, poids, activations, VAE. Limite cgroup explicite par conteneur (`--memory`, `--memory-swap` égal), tuilage VAE obligatoire, `vm.swappiness` bas, pas de co-location de deux moteurs lourds. Les conteneurs « voisins » du test forum (78,4 Gio utilisés) montrent que la contention est réelle.
4. **Supervision** : métrique `peak_memory_mb` du worker, `MemAvailable` de `/proc/meminfo`, température/puissance via NVML si disponible (à vérifier), jamais `nvidia-smi --query-gpu=memory.*`.
5. **Préchauffage** : le chargement coûte 39 à 445 s (FastH3 DiT : 445 s avant optimisation `lazy_module_load`, 39 s après ; ComfyUI Wan 5B : ≈ 87 s) **[MESURÉ publié]**. Garder les modèles résidents, ne pas décharger entre jobs si la RAM le permet.
6. **Deux Sparks** : possible (Ray + QSFP 200 Gb/s), gain modeste (clip 768×1344×124 : 374 s contre 292 s) **[MESURÉ publié]**. Pas rentable pour nous.

---

## 4. Orchestration des workers GPU

### 4.1 Comparatif

| Option | Licence | Ce que c'est | Reprise sur panne | Idempotence | Annulation | Priorités / équité | Fit pour 3 machines hétérogènes | Verdict |
|---|---|---|---|---|---|---|---|---|
| **File PostgreSQL `SKIP LOCKED` (existant)** | n/a | File maison sur la base déjà exploitée | À écrire (bail + heartbeat) | À écrire (clé unique + fencing) | À écrire (drapeau + sondage) | À écrire (ORDER BY, quotas) | Excellent : aucune dépendance de plus, transactions communes avec le grand livre de crédits | **Retenu pour le MVP** |
| **Temporal** (SDK TS 1.25.0, MIT ; serveur Go + base) | MIT | Exécution durable de workflows, activités, files de tâches | Natif : historique rejoué ; activités avec `heartbeatTimeout` et reprise | IDs de workflow uniques ; activités à rendre idempotentes | Une activité ne reçoit l'annulation **que si elle envoie des heartbeats** et a un `heartbeatTimeout` ; `TRY_CANCEL` par défaut **[DOC]** | Files de tâches séparées ; pas d'équité native par locataire | Bon (workers pull), mais ajoute un cluster Temporal à exploiter. Limite 51 200 événements par historique (avertissement à 10 240) **[DOC]** : prévoir Continue-As-New pour les longs flux | **Phase 2** si pipelines multi-étapes |
| **BullMQ 6.5.1** | MIT | File Node/TS sur Redis | Détection de jobs bloqués, tentatives, backoff | `jobId` unique | Annulation coopérative à écrire | Priorités, limiteur de débit, flows parent/enfant | Bon techniquement, mais **Redis en plus** et deuxième source de vérité à réconcilier avec les crédits | Non retenu : double comptabilité d'état |
| **Celery** | BSD (non relu) | Tâches Python | `task_acks_late` désactivé par défaut ; `task_reject_on_worker_lost` désactivé par défaut (risque de boucles de messages) **[DOC]** | À écrire | `revoke` (best effort) | Priorités : supportées Redis/RabbitMQ selon options (`task_queue_max_priority` documenté pour RabbitMQ seulement) **[DOC]** | Mauvais fit : pile Node/TS | Non |
| **Ray** | Apache-2.0 (non cloné) | Calcul distribué Python | `max_retries` = 3 par défaut pour pannes de worker ; exceptions applicatives non réessayées par défaut ; une tâche annulée n'est pas réessayée **[DOC]** | Sémantique « au moins une fois » à gérer soi-même | `ray.cancel` (KeyboardInterrupt ; `force=True` tue le worker) **[DOC]** | Ressources GPU fractionnaires ; pas d'équité par locataire | Cluster Ray hétérogène x86/aarch64 + PyTorch par nœud : lourd. FastVideo l'utilise pour 2 Sparks (`--execution-backend ray`) | Non pour l'ordonnancement ; acceptable seulement en interne d'un moteur multi-nœud |
| **Dagster / Prefect** | non audité | Orchestration de pipelines de données | Oui (planifié) | Partielle | Partielle | Non | Pensé pour des DAG de données, pas pour des jobs interactifs à file prioritaire | Non |
| **Kubernetes + Kueue / KAI Scheduler** | Apache-2.0 | Planificateurs de quotas/GPU pour K8s | Kubernetes redémarre les pods | n/a | Suppression de pod | Quotas, files, préemption, équité (Kueue, KAI) | Exige un cluster K8s sur 3 machines dont 1 aarch64 et un GPU intégré dont le plugin de périphérique plante à la lecture de la mémoire (issue #1482) **[DOC]** | Non avant d'avoir >2 nœuds identiques |
| **SkyPilot** | Apache-2.0 | Provisionnement multi-cloud de VM/jobs GPU | Reprise de jobs managés | n/a | oui | n/a | Orienté cloud ; hors sujet pour un parc propre | Non (utile si débordement cloud plus tard) |
| **Cog / Replicate** | Apache-2.0 | Empaquetage d'un modèle en conteneur avec serveur HTTP Rust/Axum et schéma OpenAPI | Non (un conteneur = un modèle) | **`PUT /predictions/<id>` idempotent**, `POST` non idempotent **[DOC]** (`docs/http.md`) ; webhooks `succeeded|failed|canceled` | Oui | Non | Bon comme format d'emballage d'un worker (entrées typées, schéma) | **À imiter pour le contrat** (PUT idempotent par id), pas comme orchestrateur |
| **Beam (beta9)** | **AGPL-3.0** | Plateforme serverless auto-hébergeable | Oui | n/a | n/a | n/a | Ajoute une plateforme complète | Non (licence + surface) |
| **NVIDIA Dynamo / Triton** | Apache-2.0 (à confirmer) | Orchestration d'inférence LLM désagrégée ; support vidéo FastVideo/SGLang annoncé, « diffusion TRT-LLM » expérimentale | | | | | Conçu pour clusters datacenter ; aucune mention GB10 dans le README | Non pour le MVP ; à surveiller |
| **comfyui-api (Salad)** | MIT | Enveloppe stateless autour de ComfyUI : webhooks, stockage S3/Azure/HF, téléchargement dynamique, sondes `/health` `/ready`, bascule de modèles | Sans état (le client réessaie) | `id` de requête | Interrompt via ComfyUI | Non | **Utile comme référence de code** (voir `safe-http.ts`, `safe-s3-handler.ts`, `storage-policy.ts`). **Il ne fournit pas d'authentification entrante** et son README précise qu'il ne met pas en bac à sable les workflows arbitraires **[DOC]** | Lire et copier les idées (MIT), ne pas l'exposer |
| **worker-comfyui (RunPod)** | **AGPL-3.0** | Image + `handler.py` pour RunPod serverless | | | | | Attention licence | Lire seulement |
| **ComfyDeploy / ViewComfy / comfy-pack** | GPL-3.0 / AGPL-3.0 / Apache-2.0 | Plateformes de déploiement de workflows ComfyUI | | | | | ComfyDeploy inactif depuis 09/2025 ; ViewComfy AGPL ; comfy-pack (Apache-2.0) fige l'environnement : versions de nœuds + empreintes de modèles dans un `.cpack.zip` | **Idée à reprendre : le « lock » d'environnement** (nœuds + commits + empreintes). Pas la plateforme |
| **SwarmUI** | MIT | Interface + multi-backends ComfyUI, scheduler « model-aware » | Pas de persistance des demandes | n/a | n/a | Heuristique de pression par modèle (voir 7) | Backend auto-scalable marqué WIP **[DOC]** | **Source d'inspiration** pour l'ordonnancement, pas pour la production |

### 4.2 Pourquoi garder PostgreSQL pour le MVP

1. **Une seule base de vérité** : le job, la réservation de crédits et le résultat commit dans la même transaction. Avec BullMQ/Temporal, il faut réconcilier deux systèmes après chaque panne.
2. **Les moteurs ne persistent rien** (2.2). Quel que soit l'orchestrateur, c'est le code Nexora qui gère « le moteur est mort, que fait-on ».
3. **3 machines** : le risque est dans l'isolation et les modèles, pas dans la distribution des tâches.
4. **Seuil de bascule vers Temporal** [INFÉRENCE] : plus de 3 étapes durables par job, besoin de timers longs (rendus planifiés), ou besoin d'attendre une validation humaine. À ce moment, garder PostgreSQL comme registre et laisser Temporal gérer la saga, avec un `idempotencyKey` identique.

### 4.3 Ce qu'il faut ajouter à la file PostgreSQL (sinon les pannes coûtent des crédits)

Voir le contrat détaillé en section 5. En résumé : bail avec expiration, heartbeat par thread séparé, jeton de fencing (`lease_epoch`) vérifié à chaque écriture, clé d'idempotence unique par (locataire, clé client), annulation coopérative, tentatives bornées avec classification des erreurs, mise en quarantaine des « jobs poison », réservation de crédits en trois temps.

---

## 5. Architecture de workers recommandée et contrat Job ↔ Worker

### 5.1 Vue d'ensemble

```
Next.js 16 (API publique, authentification, quotas, crédits)
   │  POST /api/generations  { recipe_id, version, params, profile, Idempotency-Key }
   ▼
Contrôleur (Node/TS)  ── valide les paramètres (zod) ── réserve les crédits ── INSERT jobs (queued)
   │
PostgreSQL  ←── jobs / job_attempts / job_events / ledger / models / workers
   ▲  fonctions SECURITY DEFINER : claim_job, heartbeat_job, complete_job, fail_job, request_cancel
   │
GPU Agent (Node/TS, un par GPU, hors conteneur moteur, sans GPU)
   │  boucle pull : claim → préparer (résidence modèles) → exécuter → téléverser → clore
   │  supervise un « sidecar moteur » (conteneur) via socket Unix/loopback
   ▼
Moteur (conteneur durci : ComfyUI figé OU FastVideo OU SGLang OU vLLM-Omni OU script diffusers)
   │  entrée : fichiers dans /scratch (tmpfs par job) ; sortie : fichiers dans /scratch/out
   ▼
Agent téléverse vers S3 compatible (SeaweedFS/…) avec ses propres identifiants (le moteur n'en a aucun)
```

Principes :
- **Le moteur n'a ni réseau, ni identifiants, ni accès à la base.** Seul l'agent parle à PostgreSQL et au stockage objet.
- **Les agents appellent des fonctions SQL à privilèges limités**, pas des tables brutes : un hôte GPU compromis ne peut pas lire les jobs d'autres machines ni le grand livre.
- **Un agent par GPU physique**, un seul job actif à la fois. Pour le GB10 : un agent, un job actif.
- L'agent est dans le même langage que le worker existant (Node/TS) ; il peut le prolonger plutôt que de le remplacer.

### 5.2 Machine à états du job

```
                      ┌───────────── cancel_requested ──────────────┐
                      ▼                                              │
queued ──claim──▶ leased ──▶ preparing ──▶ running ──▶ uploading ──▶ succeeded
  ▲                 │            │            │            │
  │                 └────────────┴────────────┴────────────┘
  │                              │ échec / bail expiré
  │                              ▼
  └──────(retry, run_after)── failed_retryable ──(max_attempts)──▶ failed_permanent
                                                                   ▲
 cancel_requested ──▶ cancelling ──▶ cancelled        quarantined ─┘ (poison : même job tue N workers)
```

États terminaux : `succeeded`, `failed_permanent`, `cancelled`, `expired` (non pris en charge avant `deadline`), `quarantined`. Règle : **toute transition se fait par un `UPDATE … WHERE id = $1 AND lease_epoch = $2 AND state = $3`** ; zéro ligne modifiée = le worker a perdu le bail et doit abandonner sans écrire.

### 5.3 Schéma minimal (esquisse SQL)

```sql
CREATE TABLE gen_jobs (
  id               uuid PRIMARY KEY,
  tenant_id        uuid NOT NULL,
  user_id          uuid NOT NULL,
  idempotency_key  text NOT NULL,
  recipe_id        text NOT NULL,          -- ex. 'video.i2v.wan22.v3'
  recipe_hash      text NOT NULL,          -- empreinte du graphe compilé et signé
  profile          text NOT NULL CHECK (profile IN ('fast','balanced','quality')),
  params           jsonb NOT NULL,         -- validé par le schéma de la recette
  params_hash      text NOT NULL,
  input_assets     jsonb NOT NULL DEFAULT '[]',   -- IDs opaques, jamais des chemins/URL
  priority_class   smallint NOT NULL,      -- 0 batch, 1 standard, 2 interactif
  required_caps    jsonb NOT NULL,         -- {gpu_class, vram_gb_min, engine, arch}
  model_set        text[] NOT NULL,        -- empreintes de modèles requis (résidence)
  vram_est_mb      int NOT NULL,
  state            text NOT NULL,
  attempt          int  NOT NULL DEFAULT 0,
  max_attempts     int  NOT NULL DEFAULT 3,
  lease_epoch      bigint NOT NULL DEFAULT 0,      -- jeton de fencing
  lease_owner      text,
  lease_expires_at timestamptz,
  heartbeat_at     timestamptz,
  progress         real,
  cancel_requested_at timestamptz,
  run_after        timestamptz NOT NULL DEFAULT now(),
  deadline_at      timestamptz,
  credits_hold_id  uuid,                   -- réservation dans le grand livre
  credits_quote    numeric(14,4) NOT NULL,
  output_manifest  jsonb,
  error_class      text,                   -- retryable | permanent | policy | oom | cancelled
  error_code       text,
  created_at       timestamptz NOT NULL DEFAULT now(),
  started_at       timestamptz,
  finished_at      timestamptz,
  UNIQUE (tenant_id, idempotency_key)
);
CREATE INDEX ON gen_jobs (state, run_after, priority_class DESC, created_at);

CREATE TABLE gen_attempts (
  job_id uuid, attempt int, worker_id text, gpu_uuid text,
  engine text, engine_version text, image_digest text,
  started_at timestamptz, ended_at timestamptz,
  outcome text, gpu_seconds real, load_seconds real, peak_mem_mb int,
  energy_wh real, metrics jsonb,
  PRIMARY KEY (job_id, attempt)
);
-- Journal d'événements append-only pour l'UI (SSE) : job_id, seq, kind, payload, at
```

### 5.4 Verbe par verbe (contrat)

| Verbe (fonction SQL) | Appelé par | Effet | Idempotence / fencing |
|---|---|---|---|
| `submit(tenant, key, recipe, params, …)` | Contrôleur | Valide, calcule `credits_quote`, **réserve** les crédits, insère `queued` | `UNIQUE(tenant_id, idempotency_key)` : même clé + même `params_hash` = renvoie le job existant ; même clé + autre `params_hash` = erreur 409 |
| `claim(worker_id, caps, resident_models, window=20)` | Agent | Choisit un job `queued` compatible, incrémente `lease_epoch` et `attempt`, pose `lease_expires_at = now()+lease_ttl`, renvoie le job | `FOR UPDATE SKIP LOCKED` ; `epoch` renvoyé = jeton |
| `heartbeat(job_id, epoch, progress, stats)` | Agent (thread dédié) | Prolonge le bail ; **renvoie `cancel_requested`** | Refus (0 ligne) si l'epoch a changé |
| `phase(job_id, epoch, phase)` | Agent | `leased → preparing → running → uploading` | idem |
| `complete(job_id, epoch, manifest, usage)` | Agent | Après téléversement vérifié : état `succeeded`, **valide** la réservation au coût réel (ou au prix de la recette), écrit `gen_attempts` | Conditionnel à `epoch` ; rejouable : si déjà `succeeded` avec le même manifeste, renvoie OK |
| `fail(job_id, epoch, error_class, code, usage)` | Agent | `retryable` : `queued` avec `run_after = now() + backoff·2^attempt + jitter`, ou `failed_permanent` si `attempt ≥ max_attempts` ; **libère** la réservation sur l'état final | Conditionnel à `epoch` |
| `request_cancel(job_id)` | Contrôleur | Si `queued` : `cancelled` immédiat + libération complète. Sinon pose `cancel_requested_at` | Idempotent |
| `reap_expired()` | Tâche périodique (toutes les 10-15 s) | Jobs `leased|preparing|running|uploading` avec `lease_expires_at < now()` → `queued` (tentative suivante) ou `quarantined` si N workers morts successifs | `lease_epoch` incrémenté au prochain `claim`, ce qui invalide le vieux worker |

**Paramètres recommandés [INFÉRENCE, à calibrer]** : heartbeat toutes les 10 s depuis un thread indépendant de la boucle de calcul (un pas de GB10 peut durer des dizaines de secondes) ; `lease_ttl` 60 s (90 s sur GB10) ; chargement de modèle = phase `preparing` avec heartbeat explicite (jusqu'à 445 s mesuré avant optimisation sur GB10) ; `max_attempts` 3 ; backoff 15 s, 60 s, 240 s ; quarantaine après 2 morts de worker successives sur le même job.

### 5.5 Reprise après panne

| Panne | Détection | Traitement |
|---|---|---|
| Agent ou hôte meurt en plein calcul | Bail expiré (≤ `lease_ttl`) | `reap_expired` remet en file avec `attempt+1` ; les sorties partielles de l'ancienne tentative sont sous `…/attempt-N/` et nettoyées par ramasse-miettes |
| Moteur plante / OOM | L'agent le voit (code de sortie, `/health`) | Classe `oom` : retenter **sur une classe de GPU plus grande ou avec un profil plus économe** (par exemple Rapide), pas à l'identique ; classe `retryable` sinon |
| Moteur bloqué (pas de progression) | Watchdog : aucune progression pendant `stall_timeout` | Annulation dure (tuer le conteneur), `fail(retryable)` |
| Perte du réseau vers PostgreSQL | Heartbeat en échec | L'agent **arrête d'abord le calcul au bout d'un délai < `lease_ttl`**, puis abandonne, pour ne pas produire de doublon payé |
| Double exécution (zombie qui se réveille) | `epoch` périmé | Ses `heartbeat/complete` renvoient 0 ligne ; il détruit son scratch ; ses objets S3 d'une ancienne tentative ne sont pas référencés |
| Résultat prêt mais `complete` échoue | Réessai de `complete` avec le même manifeste | Idempotent. Si le bail a expiré entre-temps, le résultat reste référencé par la tentative de plus haut `epoch` qui réussira ; sinon, nettoyage |
| Job « poison » qui tue les workers | Compteur de morts | `quarantined` + alerte, crédits libérés |

Les sorties vont sous `tenant/{tenant_id}/job/{job_id}/attempt-{n}/…`. Le manifeste final (liste de fichiers, tailles, SHA-256) est l'unique source de ce qui appartient au résultat.

### 5.6 Annulation

1. Utilisateur → `request_cancel`. Si le job est `queued` : fin immédiate, crédits libérés.
2. Sinon, `cancel_requested_at` est posé ; la **réponse du prochain heartbeat** le signale à l'agent (≤ 10 s).
3. L'agent appelle l'annulation propre du moteur :
   - ComfyUI : `POST /interrupt {"prompt_id": …}` **[CODE]** (le ciblage par `prompt_id` évite l'interruption globale).
   - SGLang : `DELETE /v1/videos/{id}` ; arrêt après le pas courant, monolithique mono-nœud seulement **[DOC]**.
   - vLLM-Omni : `DELETE` avec abandon borné **[DOC]**.
   - FastVideo : ne repose pas sur une annulation du thread de calcul **[CODE]** → prévoir l'arrêt dur.
4. **Délai de grâce de 15 s**, puis arrêt dur du conteneur moteur (coût : rechargement du modèle ; sur GB10 jusqu'à plusieurs dizaines de secondes à plus de 400 s) — d'où l'intérêt de garder un état « moteur chaud » et de ne tuer que si nécessaire.
5. Politique de facturation à l'annulation : libération totale avant `running` ; au-delà, débit proportionnel au `gpu_seconds` consommé (configurable). Un seul calcul, documenté pour l'utilisateur.

### 5.7 Priorités, équité, quotas

- Trois classes (batch 0, standard 1, interactif 2). Sélection : `ORDER BY priority_class DESC, score`, avec un score qui combine l'âge dans la file et la **dette d'équité** du locataire (GPU-secondes consommées sur les dernières 15 min / part contractuelle), pour qu'un gros client ne bloque pas les autres.
- Quotas dans le contrôleur avant `submit` : jobs actifs par locataire, GPU-secondes par jour, résolution/durée/pas maximaux par profil, taille des entrées. Un plafond de coûts bloque avant la réservation, pas après.
- Préemption : pas de préemption de jobs en cours au MVP (coût de rechargement). Les jobs interactifs vont sur une machine ou un GPU réservé.

### 5.8 Coûts par tâche et crédits

Le grand livre existant doit gagner trois écritures par job, toutes idempotentes par `(job_id, kind)` :
1. `HOLD` à la soumission (montant = `credits_quote`, issu du **prix de la recette × profil**, pas du temps réel : prévisibilité pour le client).
2. `CAPTURE` au succès (montant = prix de la recette ; le coût réel en GPU-secondes est consigné à part pour la marge).
3. `RELEASE` en cas d'échec définitif, d'annulation ou d'expiration.

Mesures par tentative (`gen_attempts`) : `gpu_seconds` (phase `running`), `load_seconds` (chargement modèle, imputé à la plateforme, pas au client), pic mémoire, énergie estimée, version/digest du moteur. Le **prix de recette** se calibre par le percentile 95 mesuré par classe de GPU (voir plan de spikes, section 9). Les temps du GB10 étant ≈ 10× ceux de la 5090 sur la vidéo quantifiée, le prix dépend du profil et non de la classe de GPU (détail d'ordonnancement), mais la **marge** se calcule par classe.

### 5.9 Métriques et supervision

- Côté agent/moteur : durée en file, durée de chargement, durée de calcul, pas/s, pic mémoire, taux d'échec par code, nombre de baux perdus, nombre d'annulations dures. SGLang et LightX2V exposent déjà du Prometheus **[CODE]/[DOC]** ; pour ComfyUI, dériver depuis les événements WebSocket (`executing`, `executed`, `execution_error`) **[CODE]**.
- GPU : DCGM-exporter (Apache-2.0) pour les GPU discrets (5090, 5080) ; **pour le GB10, ne pas compter sur les champs mémoire** (voir 2.3). Compléter par `nvidia-smi dmon`/NVML (puissance, température, horloges) et par la mémoire vue de l'agent. DCGM sur GB10 : **[NON VÉRIFIÉ]**, test à faire.
- Alertes : file `queued` plus ancienne que X, bail expiré, quarantaine, ratio retenté/total, écart prix/coût réel > seuil, espace disque des poids.

### 5.10 Interface `EngineAdapter` (extrait)

```ts
interface EngineAdapter {
  capabilities(): { engine: string; version: string; recipes: string[]; arch: string[] };
  residentModels(): Promise<string[]>;            // empreintes
  ensureResident(models: string[], budgetMb: number): Promise<{ loadSeconds: number }>;
  run(job: CompiledJob, scratch: string, ctx: { signal: AbortSignal;
      onProgress(p: number): void }): Promise<{ files: OutFile[]; usage: Usage }>;
  cancel(jobId: string): Promise<void>;           // coopératif
  kill(): Promise<void>;                          // dur
  health(): Promise<'ok' | 'degraded' | 'dead'>;
}
```

Adaptateurs : `comfy` (graphe compilé, `prompt_id` = `job_id` en UUID), `fastvideo` / `sglang` / `vllm-omni` (REST loopback `/v1/videos`), `diffusers` (script maison, processus fils). Le contrôleur ne connaît que `recipe_id` ; l'adaptateur sait comment l'exécuter. Un même `recipe_id` peut avoir plusieurs implémentations (ComfyUI sur 5090, FastVideo sur GB10) avec une **table de correspondance** `recipe × GPU class → engine`, ce qui permet de basculer de moteur sans toucher à l'API.

---

## 6. Sécurité multi-client

### 6.1 Modèle de menace

| # | Menace | Vecteur | Gravité | Mesures principales |
|---|---|---|---|---|
| T1 | **Exécution de code arbitraire via nœuds personnalisés** | Un workflow soumis nomme un nœud qui exécute du Python ; ou un paquet de nœuds installé est malveillant | Critique | Aucun workflow utilisateur ; liste blanche de nœuds figée dans l'image ; pas de Manager ; pas d'installation à l'exécution |
| T2 | **Chaîne d'approvisionnement des nœuds/modèles** | Paquet malveillant du registre ; dépendance `requirements.txt` ; mise à jour automatique | Critique | Images construites en CI, versions et empreintes épinglées, `pip --require-hashes`, pas de réseau à l'exécution |
| T3 | **Pickle / modèles piégés** | Fichiers `.ckpt`/`.pt`/`.bin` | Haute | safetensors uniquement, ingestion en sas, `weights_only=True`, `use_safetensors=True` |
| T4 | **Téléchargements pilotés par l'utilisateur (SSRF)** | URL d'image/modèle dans la requête ; téléchargeur sans filtre | Haute | Pas d'URL côté moteur : le contrôleur télécharge/valide les entrées dans un service d'ingestion et ne passe que des IDs d'actifs |
| T5 | **Lecture/écriture hors périmètre** | Traversée de chemin sur `LoadImage`, `/view`, `filename_prefix`, sous-dossiers | Haute | Scratch par job, chemins jamais fournis par l'utilisateur, système de fichiers en lecture seule hors scratch |
| T6 | **Fuite inter-clients** | Répertoires `output`/`temp` partagés, historique ComfyUI global, caches de conditionnement/VAE, LoRA d'un client chargée pour un autre, métadonnées PNG contenant le graphe | Haute | Un job à la fois par GPU, scratch éphémère, `--disable-metadata`, caches désactivés en mode strict, adaptateur qui nettoie, LoRA par locataire |
| T7 | **Exposition réseau du moteur** | `--listen 0.0.0.0`, port ouvert, route `/system_stats` (argv) | Critique | Liaison loopback/socket Unix, réseau conteneur sans route sortante |
| T8 | **Épuisement de ressources / coût** | Résolution, nombre de pas, longueur de vidéo, boucles dans le graphe, fichiers énormes | Moyenne/Haute | Plafonds par recette/profil validés avant la file, délai maximal par job, quotas de crédits, `ulimit`, limite cgroup mémoire |
| T9 | **Évasion de conteneur / pilote GPU** | Faille du runtime ou du toolkit NVIDIA | Haute | Conteneur non privilégié, `cap-drop ALL`, `no-new-privileges`, seccomp, pilotes et toolkit à jour (des CVE d'évasion visant NVIDIA Container Toolkit ont été publiées en 2024-2025 : **[NON VÉRIFIÉ]**, à relire sur le bulletin NVIDIA) |
| T10 | **Compromission d'un hôte GPU** | Agent ou moteur détourné | Haute | Rôle PostgreSQL à fonctions seules, identifiants S3 limités au préfixe du job (URL pré-signées courtes), aucun secret dans le conteneur moteur |
| T11 | **Nœuds « partenaires » / API payantes de ComfyUI** | Sortie de données vers des services tiers, coûts | Moyenne | `--offline`/`--disable-api-nodes` ; Privacy Router pour tout appel de modèle de langage |
| T12 | **Contenu illicite / politique** | Prompts, images | Variable | Hors périmètre de ce rapport ; point d'insertion : étape de modération avant `submit` et sur la sortie |

**Faits datés qui justifient la sévérité de T1/T2/T7** :
- Avril 2026 : plus de 1 000 instances ComfyUI exposées, abusées via des nœuds acceptant du Python brut (par exemple des « shell executor »), avec repli d'installation par ComfyUI-Manager si aucun nœud vulnérable n'est présent ; minage Monero/Conflux et proxy Hysteria V2 **[DOC]** (The Hacker News, 7 avril 2026, d'après Censys).
- Octobre 2025 : paquets malveillants (`upscaler-4k` et un autre) publiés dans le registre officiel Comfy, 790 téléchargements avant bannissement le 21 octobre 2025 **[DOC]** (post-mortem Comfy).
- Janvier 2026 : CVE-2026-22777, exécution de code à distance dans ComfyUI-Manager (versions < 3.39.2, et 4.0.0 à < 4.0.5), preuve de concept publique, corrigé par ComfyUI ≥ 0.3.76 et Manager 3.39.2 / 4.0.5 **[DOC]** (bulletin BytePlus ; **[NON VÉRIFIÉ]** sur l'avis GitHub GHSA-562r-8445-54r2).
- Juin 2024 : `ComfyUI_LLMVISION`, nœud volant des identifiants via des roues Python piégées **[DOC]** (résultats de recherche ; détails judiciaires non confirmés).

### 6.2 Mesures — la liste « à faire » dans l'ordre d'importance

**A. Aucune surface utilisateur sur ComfyUI.**
1. Pas de proxy transparent `/prompt` ; l'API publique n'accepte que `recipe_id + params`.
2. Le moteur écoute sur `127.0.0.1` ou une socket Unix partagée avec l'agent (défaut ComfyUI : `127.0.0.1` **[CODE]**). Jamais `--listen`.
3. Le contrôleur ne retourne jamais d'erreur brute du moteur à l'utilisateur (elles contiennent chemins et noms de nœuds) ; codes d'erreur Nexora seulement.

**B. Recettes compilées, signées, listées blanches.**
1. Une recette = module TypeScript + schéma `zod` (types, bornes, énumérations) qui émet un graphe API ComfyUI (ou un appel natif). Version et empreinte SHA-256 du graphe émis stockées dans `recipe_hash` ; signature Ed25519 de la recette lors du déploiement.
2. Le graphe émis est revalidé par l'agent contre une **liste blanche de `class_type`** et de schémas d'entrées par nœud ; tout nœud inconnu = job rejeté (`policy`).
3. Aucun champ chaîne libre de l'utilisateur ne atteint un nom de fichier, un chemin ou une URL. Les entrées médias sont des **IDs d'actifs** que l'adaptateur résout vers des fichiers du scratch après ingestion et vérification (type MIME réel, décodage ffprobe/PIL dans un sas, taille, dimensions).
4. `filename_prefix` imposé par l'adaptateur ; `SaveImage`/`SaveVideo` ne peuvent écrire que dans `/scratch/out`.
5. Plafonds par profil : résolution, nombre d'images, pas, taille de lot, nombre de nœuds ; délai maximal par job.

**C. Image moteur figée, minimale, reproductible.**
1. Construite en CI : ComfyUI à un commit précis (`comfy --workspace … install --version X`, comme le fait `worker-comfyui` **[CODE]**), un petit ensemble de nœuds personnalisés relus à la main, `pip install --require-hashes`, image référencée **par digest**.
2. Démarrage : `--disable-all-custom-nodes --whitelist-custom-nodes <liste>`, pas de `--enable-manager`, `--offline`, `--disable-metadata`, `--cache-none` ou `--cache-lru N` en mode strict, `--base-directory` vers un répertoire en lecture seule hors scratch, `--listen 127.0.0.1` **[CODE]**.
3. Reproduire le **modèle de gouvernance de ComfyUI** (empreinte blake3 du contenu de chaque paquet, refus des liens symboliques et du `.pyc`) avec un contrôle de démarrage maison, puisque le module `governance` n'est actif que dans un build gouverné **[CODE]**. Idée complémentaire : adopter le « lock » de `comfy-pack` (versions + commits + empreintes de modèles) comme artefact de build.
4. Revue obligatoire (lecture du code, recherche de `subprocess`, `eval`, `exec`, `requests`, `torch.load`, `pickle`, `os.system`) pour tout nœud personnalisé ajouté. Dans le cœur de ComfyUI, la recherche de `subprocess/eval/exec/urlopen` dans `nodes.py`, `comfy_extras`, `comfy_execution`, `comfy_api` n'a rien montré d'inquiétant hors `app/frontend_management.py` (téléchargement de l'interface) **[CODE]**.

**D. Isolation d'exécution.**

| Technique | Contribution | Statut sur notre parc |
|---|---|---|
| Conteneur non privilégié (Podman sans root ou Docker avec `userns-remap`) | Réduit l'impact d'une exécution de code | Applicable partout. Accès GPU par CDI (`nvidia-ctk cdi generate`) plutôt que `--privileged` |
| `--read-only` + `tmpfs` pour `/scratch` et `/tmp` | Rien de persistant hors poids | Applicable |
| `--cap-drop=ALL --security-opt=no-new-privileges` + seccomp par défaut | Réduit les appels système | Applicable |
| Réseau : `--network none` + socket Unix vers l'agent, ou réseau `internal` sans passerelle | Empêche l'exfiltration, les mineurs, le C2 | Applicable ; **à tester** : certains outils attendent un réseau local |
| Poids montés `:ro` depuis un volume partagé adressé par contenu | Un nœud malveillant ne peut pas altérer les poids ; une seule copie pour plusieurs conteneurs | Applicable |
| Limites cgroup (mémoire, PIDs, CPU) | Évite le gel de l'hôte (surtout GB10 : RAM unifiée) | Applicable ; critique sur GB10 |
| Un job à la fois par GPU + purge du scratch | Évite les fuites entre locataires | Applicable |
| **gVisor** | Noyau utilisateur | Liste GPU documentée : T4, L4, A100, A10G, H100 ; rien sur RTX 50 ni GB10 **[DOC]** → **non retenu** |
| **Kata / Firecracker + VFIO** | VM par job | Passthrough d'un GPU PCIe possible pour 5090/5080 en théorie (hôte sans GPU, groupe IOMMU propre) ; **impossible pour un GPU intégré au SoC** comme le GB10 **[INFÉRENCE]** → phase 2, seulement pour 5090/5080 si le risque l'exige |
| **Une VM dédiée par machine** (hôte → VM avec VFIO) | Défense en profondeur | À étudier pour 5090/5080, hors GB10 |

Mode « strict » (clients sensibles, cohérent avec le Privacy Router) : conteneur éphémère recréé à chaque job, caches désactivés, aucune résidence de modèle partagée avec d'autres locataires (au prix du temps de chargement).

**E. Modèles et poids.**
1. Registre interne des modèles : table `models(sha256, nom, format, taille, licence, source, état)`. Seuls les modèles `approved` sont montés.
2. Format : **safetensors uniquement** dans les images de production. L'ingestion (sas, sans réseau sortant sauf la source, hors ligne ensuite) : télécharger par l'opérateur uniquement, SHA-256, analyse de l'en-tête safetensors (longueur d'en-tête bornée, types autorisés, offsets contigus sans recouvrement, taille de fichier cohérente), refus des fichiers « .ckpt/.pt/.bin/.pkl ». Conversion éventuelle dans le sas avec `weights_only=True`, puis nouvelle empreinte.
3. HF : épingler la révision par SHA de commit ; `HF_HUB_OFFLINE=1` à l'exécution ; jamais `trust_remote_code`. diffusers : forcer `use_safetensors=True` **[CODE]**.
4. LoRA/modèles fournis par un locataire : safetensors seuls, plafonds de taille et de rang, analyse, espace de noms par locataire, chargés uniquement pour ses jobs.
5. GGUF, ONNX, TensorRT engines : traiter comme du code natif (un engine TensorRT est lié à une version de GPU/TensorRT et n'est pas portable) ; ne les accepter que produits en interne.

**F. Stockage objet, URL pré-signées, quotas.**
1. Sorties sous `tenant/job/attempt` ; l'agent téléverse avec des identifiants restreints au préfixe du job ; le moteur n'a aucun identifiant.
2. Livraison par **URL pré-signées courtes** (par exemple 5-15 min, `Content-Disposition` et `Content-Type` imposés), générées par le contrôleur après contrôle d'appartenance du locataire ; jamais de liste de bucket publique ; chiffrement au repos selon la politique du Privacy Router.
3. Choix du stockage : MinIO Community a été mis en mode maintenance en décembre 2025 et archivé en 2026 (dépôt serveur archivé le 25 avril 2026), distribution source seulement, licence AGPL **[DOC]** (sources de blog tierces, non confirmées sur le site de MinIO). Alternatives à évaluer : **SeaweedFS** (API S3, URL pré-signées à confirmer), Garage, Ceph RGW. **[NON VÉRIFIÉ]** : compatibilité S3 exacte de chacun, à tester avec `aws s3 presign`. Pour un parc de 3 machines, un seul SeaweedFS ou un dossier NFS + service de signature maison suffit au MVP.
4. Rétention : suppression automatique des sorties après N jours, par locataire ; purge des actifs d'entrée dès la fin du job ; ramasse-miettes des tentatives orphelines.
5. Quotas : stockage total par locataire, nombre de fichiers, taille maximale par sortie, bande passante de téléchargement.

**G. Réseau et secrets.**
- Segmenter : réseau « GPU » sans sortie Internet, accès uniquement au contrôleur/PostgreSQL (fonctions) et au stockage objet. Sortie Internet limitée à un dépôt miroir interne, utilisé seulement par la CI pour construire les images.
- Aucun secret dans l'environnement du moteur ; rotation des secrets de l'agent ; journaux sans prompts en clair pour les locataires stricts.
- Filtrer les sorties DNS ; surveiller les connexions sortantes tentées (un conteneur sans route ne doit en produire aucune : toute tentative est une alerte).

**H. Surveillance de sécurité.**
- Alertes : tentative de connexion sortante, processus inattendu (miner), pic GPU hors job, hash de paquet de nœuds différent de la liste, modèles non approuvés dans le montage.
- Inventaire quotidien des empreintes d'images et de nœuds ; l'agent refuse de démarrer sur une image non listée.

---

## 7. Gestion multi-modèles et multi-GPU

### 7.1 Ce que font les outils existants
- **SwarmUI** [CODE] : chaque requête signale le modèle voulu ; le gestionnaire calcule une « pression » par modèle : `Heuristic = Count*10 + (temps d'attente en secondes)`, charge le modèle de plus forte pression sur un backend libre, mémorise les backends en échec pour ce modèle (`BadBackends`), a des filtres de compatibilité et une préférence d'ordre de chargement (`ModelLoadOrderPreference`, défaut `last_used`). Les requêtes en attente de modèle sont conservées en mémoire (non durables). C'est une bonne heuristique de départ.
- **ComfyUI** [CODE] : gestion de VRAM intégrée (déchargement vers la RAM par défaut, `--highvram`, `--lowvram`, `--reserve-vram`, `--disable-smart-memory`, cache RAM avec seuil, VRAM dynamique via `comfy-aimdo`) ; `/free` pour décharger ; réglages pensés pour un utilisateur unique, pas pour du multi-locataire.
- **SGLang** [DOC] : `--component-residency` par composant (`resident`, `component-offload`, `snapshot-offload`, `layerwise-offload`) ; c'est le mécanisme le plus précis pour planifier la mémoire.
- **FastVideo** [DOC] : `lazy_module_load` (automatique sur GB10), offloading séquentiel, VAE tuilé.

### 7.2 Ordonnancement conscient des modèles (model-aware) pour Nexora

Le champ `model_set` du job (liste d'empreintes) et la liste `resident_models` envoyée par l'agent à `claim()` suffisent.

Score d'un job candidat pour un worker (plus petit = meilleur) [INFÉRENCE] :

```
score = -W_prio * priority_class
        - W_age  * wait_seconds
        - W_fair * fairness_credit(tenant)
        + W_swap * swap_cost_seconds(worker, job)     -- 0 si tous les modèles sont résidents
        + W_oom  * (vram_est_mb > worker_free_mb)     -- exclu, pas pénalisé
```

- `swap_cost_seconds` = somme des tailles des modèles non résidents ÷ débit de chargement mesuré de la machine (tiré de `gen_attempts.load_seconds`).
- **Garde-fou de famine** : un job qui attend plus de `max_affinity_delay` (30-60 s pour le standard, 5 s pour l'interactif) perd sa pénalité de swap, comme la règle « 1,5 s puis on charge » de SwarmUI **[CODE]**.
- **Fenêtre de candidats** : `claim` lit les 20 premiers `queued` compatibles (sans verrou long), les classe en mémoire, tente `SKIP LOCKED` dans l'ordre.
- **Résidence** : maintien LRU des modèles par agent avec un budget (`residency_budget_mb`) ; le plan de VRAM se fait par composant (encodeur de texte, DiT, VAE) et non par modèle entier.

### 7.3 Planification VRAM (valeurs à mesurer, pas à croire)

Chaque recette déclare par profil : poids (Go), activations estimées, VAE (pic de décodage), encodeur de texte. Procédure : mesurer le pic réel sur chaque classe de GPU pendant les spikes, stocker `vram_est_mb` dans la recette avec une marge de 10-15 %, et refuser le claim si `vram_est_mb > mémoire libre de l'agent`.

Ordres de grandeur utiles pour le dimensionnement [MESURÉ publié] : Wan2.1 1.3B en 3 pas sur GB10 = pic 8,4 Go ; FastH3 « Trim » NVFP4 « tient en 8 Go » de GPU ; CompactH3 NVFP4 tient sur une 5090 de 32 Go avec encodeur en mémoire épinglée ; DiT FastH3 complet = 65 Go (donc réservé au GB10) **[DOC]** (README et blogs FastVideo).

### 7.4 Profils Rapide / Équilibré / Qualité

Un profil est un contrat produit, pas un simple jeu de paramètres. Il est défini par recette et versionné.

| Profil | Intention | Réglages typiques (à calibrer) | Cible machine | Latence cible (5 s de vidéo 480p, à confirmer par spike) |
|---|---|---|---|---|
| **Rapide** | Brouillon, itération, aperçu | Modèle distillé 4-8 pas, résolution 480p, NVFP4/FP8, attention creuse, VAE léger (type TAEH3), cache activé | 5090 d'abord ; 5080 si le modèle tient | Ordre de grandeur publié : 9-15 s (5090, modèles dédiés) **[MESURÉ publié]** |
| **Équilibré** | Livraison standard | 8-20 pas, 720p, FP8, VAE complet | 5090 ; GB10 en secours hors heures de pointe | 40-120 s (5090) ; ≈ 6 min (GB10, LTX2.3 8 pas) **[MESURÉ publié]** |
| **Qualité** | Rendu final, modèle le plus gros | Modèle complet ou 14B, 30+ pas, 720p-1080p, bf16/fp16, VAE complet, sans accélérations à perte | GB10 (capacité) en batch ; 5090 si tient | Minutes à dizaines de minutes ; GB10 : 12-47 min pour modèles 50 pas **[MESURÉ publié]** |

Règle d'or : **ne jamais faire dépendre le prix d'un profil de la machine qui l'exécute** ; la machine est un détail d'ordonnancement. Si une recette n'a pas de mise en œuvre validée sur une classe de GPU, cette classe ne la prend pas.

---

## 8. Plan par machine

| Machine | Rôle | À installer (plus tard, après validation) | À ne pas faire | À mesurer d'abord |
|---|---|---|---|---|
| **RTX 5090 32 Go** (x86_64 présumé) | Production vidéo/image à faible latence ; profils Rapide et Équilibré ; images ComfyUI figées | Conteneur moteur durci ; FastVideo/LightX2V/SGLang pour vidéo, ComfyUI compilé pour image/ControlNet/LoRA ; NVFP4 (Nunchaku, LightX2V, FastH3 CompactH3) ; DCGM-exporter | Co-localiser deux moteurs lourds ; exposer le port ; 2 jobs simultanés | Temps de bout en bout par recette (froid/chaud), pic VRAM, stabilité thermique sous charge continue (575 W) |
| **DGX Spark / GB10 128 Go** (aarch64) | Capacité : modèles volumineux, profil Qualité en batch, résidence de plusieurs modèles, services annexes (VAE lourds, LLM de prompt) | FastVideo (guide officiel Spark), ComfyUI (conteneur NGC ou roue `cu130` aarch64), SGLang à essayer ; limites cgroup strictes | Promettre de l'interactif vidéo ; compter sur `nvidia-smi`/DCGM mémoire ; installer des moteurs sans vérifier le noyau `sm_121` (LightX2V NVFP4, SageAttention3) ; mélanger services lourds | Rapport 5090/GB10 sur NOS recettes ; chargement de modèle ; effet d'un voisin gourmand ; stabilité mémoire (pas de gel) ; DCGM/NVML disponibles ? |
| **RTX 5080 16 Go** | Volume image, étapes annexes (upscale, interpolation, VAE, mux), modèles quantifiés qui tiennent en 16 Go ; renfort file Rapide | Mêmes images que la 5090 mais recettes filtrées par `vram_est_mb ≤ 14 Go` | Charger les modèles 14B non quantifiés ; offloading CPU agressif (« block swap » ralentit fortement le GB10, et dégrade aussi les cartes à faible VRAM **[DOC]** forum) | Jeu de recettes qui tiennent réellement ; ratio débit 5080/5090 |

Tous les agents partagent le même contrat. L'image moteur, elle, est **par architecture** (aarch64 pour le GB10, x86_64 pour les deux autres) ; la CI construit les deux et publie des digests distincts.

---

## 9. Plan de spikes et d'acceptation (aucun lancé à ce jour)

À exécuter par une personne autorisée à installer (hors périmètre de cette étude). Chaque spike produit un petit rapport avec commande, version, empreinte d'image, temps.

| # | Spike | Machine | Critère de succès | Durée estimée |
|---|---|---|---|---|
| S1 | Lister `torch.cuda.get_arch_list()` et exécuter un GEMM bf16/FP8/FP4 sur torch 2.14.1+cu130 | GB10 | `sm_121`/`sm_120` présents ; GEMM correct | ½ j |
| S2 | FastVideo : `fastvideo serve` + FastWan2.1-1.3B (référence ≈ 39 s) puis une recette qualité | GB10 | Reproduit ≈ 40 s ; pic ≈ 8,4 Go | 1 j |
| S3 | FastVideo/LightX2V/SGLang sur 5090 avec le même modèle distillé | 5090 | Temps ≤ ceux publiés (≈ 15 s à 480p pour FastH3 V2) | 1 j |
| S4 | ComfyUI figé : image durcie, nœuds listés, `--listen 127.0.0.1`, réseau coupé | 5090 | Aucune connexion sortante ; test négatif : nœud non listé refusé ; sorties restent dans `/scratch/out` | 1 j |
| S5 | Test de pannes : SIGKILL du moteur, SIGKILL de l'agent, coupure PostgreSQL, OOM provoqué (inspiré de la matrice d'injection de pannes de vLLM-Omni **[DOC]**) | 5090 puis GB10 | Zéro double facturation, zéro job perdu, bail récupéré < `lease_ttl` + 15 s | 1 j |
| S6 | Annulation par moteur : latence entre demande et arrêt GPU, nécessité de l'arrêt dur | 5090/GB10 | p95 d'arrêt mesuré, coût de rechargement mesuré | ½ j |
| S7 | Charge multi-locataires : 3 locataires, mélange de modèles, mesurer swaps et équité | 5090 + GB10 | Pas de famine, swaps réduits ≥ 30 % par rapport à FIFO | 1 j |
| S8 | DCGM-exporter et NVML sur GB10 | GB10 | Liste des champs disponibles | ½ j |
| S9 | Stockage objet : SeaweedFS vs Garage, URL pré-signées, expiration, plafonds | tout nœud | Signature et expiration conformes, débit suffisant | ½ j |
| S10 | Test d'évasion : nœud factice qui tente d'écrire hors scratch, d'ouvrir un socket, de lire `/proc`, de charger un pickle | 5090 | Tous bloqués et alertés | 1 j |

---

## 10. Registre des risques

| Risque | Probabilité | Impact | Réponse |
|---|---|---|---|
| Noyaux NVFP4/FP4 `sm_120a` inutilisables sur `sm_121` (LightX2V, SageAttention3, Cache-DiT FP4) | Élevée | Moyen : GB10 plus lent que prévu | FastVideo pour GB10 (supporté) ; se rabattre sur SDPA/FP8/bf16 ; suivre les tickets FastVideo #1598/#1647 |
| Écart de débit ≈ 10× entre 5090 et GB10 sous-estimé dans les prix | Moyenne | Marge négative sur Qualité | Prix par profil calibré sur le p95 mesuré par classe ; la marge se suit par classe |
| Gel du GB10 par saturation de la mémoire unifiée | Moyenne | Panne de machine | Limites cgroup, tuilage VAE, `nice`, un seul moteur lourd, surveillance `MemAvailable` |
| Configuration ComfyUI exposée par erreur | Faible si process, élevée sinon | Critique | Réseau sans entrée, contrôles de démarrage de l'agent, test de scan externe mensuel |
| Nœud personnalisé compromis (mise à jour) | Moyenne | Critique | Images figées par digest, empreintes de paquets, revue, aucune installation à l'exécution |
| Moteurs sans persistance : perte de jobs au redémarrage | Certaine | Moyen | Durabilité côté PostgreSQL, bail/heartbeat, tests S5 |
| Annulation non fiable (FastVideo, rôles désagrégés SGLang) | Certaine | Moyen (GPU gaspillé) | Arrêt dur après grâce ; facturation proportionnelle documentée |
| Dérive des moteurs (versions publiées tous les quelques jours) | Élevée | Régressions | Épingler versions et digests, bancs de non-régression par recette (qualité + temps) |
| Projets peu actifs (Nunchaku, SageAttention, ComfyDeploy) | Moyenne | Dette | Ne pas bâtir de dépendance critique ; alternatives identifiées |
| Licences GPL/AGPL (ComfyUI, ViewComfy, worker-comfyui, beta9, ComfyDeploy) | Moyenne | Juridique | Processus séparé, aucun code AGPL copié, avis juridique |
| MinIO Community archivé | Certaine | Faible | Choisir SeaweedFS/Garage dès le départ |
| gVisor/Kata non disponibles pour nos GPU | Certaine | Moyen : isolation plus faible | Conteneurs durcis + réseau coupé + FS lecture seule + un job par GPU ; VM/VFIO pour 5090/5080 en phase 2 |
| Jeton de service/identifiants de l'hôte volés via le moteur | Faible | Haute | Moteur sans secret ; agent distinct ; fonctions SQL à privilèges limités |
| Hypothèses de ce rapport non testées (chiffres 5080, DCGM sur GB10, SeaweedFS pré-signé) | Certaine | Variable | Spikes S1-S10 avant tout engagement |

---

## 11. Questions ouvertes pour Nexora

1. Quel est le schéma exact du grand livre de crédits (réservations existantes ? soldes matérialisés ?) ? Le contrat 5.8 suppose un `HOLD/CAPTURE/RELEASE` idempotent.
2. Quelle est la durée maximale acceptable d'un job par profil et par client ? Cela fixe `lease_ttl` et `deadline_at`.
3. Quels modèles précis (Wan 2.2 14B, LTX 2.x, HunyuanVideo 1.5, FLUX.2, Qwen-Image…) sont au catalogue ? Le choix du moteur dépend d'eux et de leurs licences d'usage commercial, que ce rapport n'a pas auditées.
4. Quels clients exigent le mode « strict » (conteneur recréé par job) ?
5. Peut-on dédier une machine ou un GPU aux jobs interactifs ?
6. Les 5090 et 5080 sont-elles dans la même machine ou dans deux machines distinctes ? (Impacte VFIO, thermique, bande passante PCIe.)

---

## 12. Sources web consultées

- Blog FastVideo, « FastH3 RTX » : https://haoailab.com/blogs/fasth3-rtx/ et « FastH3 local » : https://haoailab.com/blogs/fasth3-local/
- NVIDIA DGX Spark, matériel : https://docs.nvidia.com/dgx/dgx-spark/hardware.html ; problèmes connus : https://docs.nvidia.com/dgx/dgx-spark/known-issues.html
- Forum NVIDIA, Wan 2.2 I2V sur Spark : https://forums.developer.nvidia.com/t/image-to-video-generation-using-the-spark-vs-pc/370077
- Blog ComfyUI sur DGX Spark : https://blog.comfy.org/p/comfyui-on-nvidia-dgx-spark
- Forum PyTorch, GB10/sm_121 : https://discuss.pytorch.org/t/dgx-spark-gb10-cuda-13-0-python-3-12-sm-121/223744
- Index de roues PyTorch cu130 : https://download.pytorch.org/whl/cu130/torch/
- Fiche HF LightWan2.2-A14B : https://huggingface.co/lightx2v/LightWan2.2-A14B
- Pages NVIDIA RTX 5090/5080 : https://www.nvidia.com/en-us/geforce/graphics-cards/50-series/rtx-5090/ et `…/rtx-5080/`
- Sécurité ComfyUI : https://thehackernews.com/2026/04/over-1000-exposed-comfyui-instances.html ; https://blog.comfy.org/p/upscaler-4k-malicious-node-pack-post ; bulletin CVE-2026-22777 (BytePlus) https://docs.byteplus.com/en/docs/byteplus-security-bulletins/CVE-2026-22777
- Temporal : https://docs.temporal.io/workflow-execution/event et https://docs.temporal.io/develop/typescript/cancellation
- Ray : https://docs.ray.io/en/latest/ray-core/fault_tolerance/tasks.html ; Celery : https://docs.celeryq.dev/en/stable/userguide/configuration.html
- gVisor GPU : https://gvisor.dev/docs/user_guide/gpu ; k8s-device-plugin issue #1482 : https://github.com/NVIDIA/k8s-device-plugin/issues/1482
- MinIO (articles tiers) : https://itsfoss.com/news/minio-moves-away-from-open-source/ ; https://glukhov.org/data-infrastructure/object-storage/minio-dead/
- NVIDIA, optimisations Spark : https://developer.nvidia.com/blog/new-software-and-model-optimizations-supercharge-nvidia-dgx-spark
