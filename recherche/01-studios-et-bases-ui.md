# 01 - Studios créatifs IA open source : quelle base pour l'interface Nexora Creative ?

Date de l'enquête : 30 octobre 2026. Auteur : agent de recherche (Claude).
Méthode : lecture seule. Aucun code cloné n'a été exécuté, aucune installation (npm/pip/bun), aucun compte, aucune dépense.

Légende des preuves :
- **[DOC]** lu dans un README, une doc ou une page web.
- **[CODE]** vérifié en lisant le code ou les fichiers de configuration du dépôt cloné.
- **[TEST]** exécuté : **aucun** (rien n'a été lancé). Les affirmations de type "ça marche" ne sont donc jamais vérifiées ici.

Dossier des clones (`--depth 1`, un dossier neuf par projet) :
`SCR = /tmp/claude-1000/-home-pc6--claude-spares-spare-nqfgQg/4a161a25-a3c4-4a78-94f6-c7dc7ebef37d/scratchpad/studios/<nom>/repo`
Les chemins de fichiers cités plus bas sont relatifs à ce dossier `repo` de chaque projet.

Limites de l'enquête (à lire avant de se fier aux chiffres) :
- Étoiles, forks, nombre de commits : relevés le 30/10/2026 dans le JSON embarqué des pages publiques github.com (l'API GitHub non authentifiée était à court de quota, les crédits Firecrawl se sont épuisés en cours de route). Ce sont des ordres de grandeur, pas des mesures auditées.
- Les licences des **dépendances transitives** n'ont pas été auditées (il aurait fallu installer ou résoudre les arbres de dépendances). Seuls les `package.json`/`pyproject.toml` de premier niveau et les fichiers LICENSE ont été lus.
- Les clones étant `--depth 1`, l'historique (changements de licence passés, qualité des commits) n'est pas visible. Les sous-modules git n'ont pas été récupérés.
- Les étoiles élevées avec peu de commits (Open-Generative-AI : 31 887 étoiles pour 487 commits ; Toonflow : 19 993 étoiles pour 86 commits) ne prouvent pas la qualité. Je ne tire aucune conclusion sur l'origine de ces chiffres, mais je ne les utilise pas comme argument.

---

## 0. Contexte : le paysage a changé il y a deux semaines

**[DOC]** https://comfy.org/open-source-higgsfield/ : Comfy a lancé le concours "Open Source Higgsfield" (inscriptions 15/10, dépôt des projets jusqu'au 30/10/2026 9h PT, résultats 6/11). Résultat : une vague de dépôts très jeunes (2 à 15 jours) taggés `open-source-higgsfield` (18 dépôts au 30/10, https://github.com/topics/open-source-higgsfield). Presque tous ont moins de 10 étoiles, 1 à quelques commits publics et sont des **œuvres de concours** : utiles comme idées, pas comme fondations. Le concours exige une licence open source et propose trois applications modèles (Cinematic Studio, Re-shoot, Openjutsu) dont la page du hub (`comfy.org/hub/apps/cinematic-studio/`) est rendue en JavaScript : je n'ai pas pu en lire le contenu (auteur, licence, contrôles inconnus).

**[DOC]** https://higgsfield.ai/blog/cinema-studio-4-0-complete-guide : le "Cinema Studio" de Higgsfield combine des références avec des contrôles de mouvement de caméra, objectifs, éclairage, rythme et jeu des personnages ; accessible aussi via MCP et API. C'est la cible fonctionnelle.

---

## 1. Noms exacts ou inexacts : réponse franche

| Nom donné | Réalité vérifiée |
|---|---|
| **BeatDesign** | Existe : `BeatAPI/BeatDesign` (Apache-2.0). Sérieux, voir fiche 2. |
| **OpenField** | **Ambigu : plusieurs dépôts sans rapport**. `VedSoni-dev/openfield` (MIT, "Open-source Higgsfield", presets en prompts, Node, 2 étoiles, dernier commit 31/07/2026) ; `TechGenDM/OpenField` (MIT, **sans rapport** : moteur d'"études de terrain" avec Gemma/Ollama, Next.js, Hacktoberfest) ; `JKWIS1/openfield` (skills Claude Code) ; `allengaller/open-field` ; `MatthewLeeWilcox/OpenfieldMCP` (sans rapport). Aucun n'est un projet de référence. Je n'ai pas trouvé de "OpenField" notable. |
| **Backlot** | Existe : `Arfolomew/backlot` (MIT, 4 étoiles, 55 commits, Python (`app/server.py`) + HTML, concours). Il y a aussi `lnguyen503/backlot` (MIT, rendu ComfyUI + MCP + studio web, juillet 2026) et `liminalframesai/backlot-h3-open-source`. Peu de maturité. |
| **FreeField / Freefield** | Existe : `droppedmyza/freefield` (MIT, 4 étoiles, **2 commits** publics, Python, presets d'effets = un dossier ComfyUI workflow + `preset.json`). Concours. |
| **Open Generative AI / Open-Higgsfield-AI** | Existe sous **deux** dépôts quasi identiques : l'original `Anil-matcha/Open-Generative-AI` (MIT, 31 887 étoiles) et `Autom8AI/Open-Higgsfield-AI` (1 716 étoiles, **aucun fichier LICENSE** dans le dépôt alors que le README annonce "MIT"). Voir fiche 3. |
| **ComfyStudio (xmyx)** | Existe mais **ce n'est pas l'éditeur vidéo** : `XmYx/ComfyStudio` est une application **PyQt6** de bureau (MIT, 24 étoiles, dernier commit 20/07/2026). L'éditeur vidéo "ComfyStudio" est `JaimeIsMe/comfystudio`, **renommé Velorn** (`VelornLabs/velorn`, GPL-3.0). Voir fiche 6. |
| **ComfyTV (jtydhr88)** | Existe, 1 150 étoiles. **Incohérence de licence** (MIT dans LICENSE, GPL-3.0 dans le README). Fiche 4. |
| **Director's Console (nickpittas)** | Existe : `NickPittas/DirectorsConsole` (MIT). Fiche 5. |
| **AI Movie Studio 2** | **Non confirmé.** Je n'ai trouvé aucun dépôt de référence : seulement `User-Olares/aimoviestudio` (packaging Olares), `869413421/ai-moive-studio` (nom mal orthographié, canvas infini) et `PRANAY1258/ai-movie-studio2` (vide, 0 étoile). Je ne l'ai pas analysé en profondeur. |
| **Comfy "Cinematic Studio" (hub)** | Existe comme app de démonstration du hub Comfy, contenu illisible (JS). Non analysable. |
| **Comfy-Org "apps / App Mode"** | Existe côté frontend ComfyUI : mode "linear / app mode" avec onglet "Apps" (`src/platform/workflow/management/composables/useAppsSidebarTab.ts`, clés i18n `linearMode.appModeToolbar.apps`) **[CODE]**. Pas une base utilisable : intégré au frontend GPL-3.0. |
| **LibTV / TapNow** | Produits commerciaux fermés (canvas de nœuds). Seuls des **clones ouverts** existent (ComfyTV, Toonflow, BeatDesign). |
| **Pollinations** | Existe (`pollinations/pollinations`, MIT, 5 257 étoiles, 12 376 commits) : plateforme/API de génération, pas un studio UI. Seules les métadonnées ont été vérifiées, pas le code. |

---

## 2. Tableau comparatif

Étoiles/commits : relevés du 30/10/2026 (voir limites). "Multi-utilisateur" = capacité native à servir plusieurs comptes isolés.

| Projet | Licence (fichier) | Stack | Étoiles / commits | Dernier commit (clone) | Multi-user / tenant | Couplage ComfyUI | Tests / CI | Verdict |
|---|---|---|---|---|---|---|---|---|
| BeatDesign | Apache-2.0 [CODE] `LICENSE` | TypeScript, TanStack Start + Vite 8, React 19, SQLite (libsql/drizzle), React Flow | 281 / 106 | 2026-10-30 | **Non** : "single-user, no account boundary" (`docs/ARCHITECTURE.md`) | Aucun (fournisseur BeatAPI) | 152 fichiers de tests unitaires + 5 e2e, CI Linux+Windows | **Meilleure source d'architecture** |
| Open-Generative-AI | MIT [CODE] `LICENSE` | JS (pas TS), Next.js (App Router) + Vite + Electron, Tailwind | 31 887 / 487 | 2026-10-29 | **Non** (clé API en localStorage) | Non (MuAPI ; local : sd.cpp, Wan2GP) | 8 fichiers de tests, **0 CI** | Source d'idées (cinéma, catalogue) ; pas une base |
| Open-Higgsfield-AI (Autom8AI) | **Aucun fichier LICENSE** (README : MIT) | idem, Vite | 1 716 / 78 | 2026-10-25 | Non | Non | 0 test, 0 CI | **À éviter** (doublon, licence non prouvée) |
| ComfyTV | LICENSE = MIT, mais README = **GPL-3.0** + code GPL vendoré [CODE] | Vue 3 + Pinia + Python (custom node ComfyUI), SQLAlchemy | 1 150 / 414 | 2026-10-27 | Présence collaborative par cookie `comfytv_sid`, **pas de comptes** | **Total** (tourne dans ComfyUI) | 118 tests py + 306 ts + e2e Playwright, 1 CI | Source d'idées ; base impossible (GPL/Vue) |
| Director's Console | MIT [CODE] | Python FastAPI x2 + React 18/Vite/Zustand, SQLite | 364 / 80 | 2026-10-02 | **Non** (aucune authentification) | Fort (REST/WS ComfyUI) | 52 fichiers de tests, 1 CI | **Meilleure source de vocabulaire cinéma** (réutilisable) |
| Velorn (ex-ComfyStudio) | **GPL-3.0-only** + CLA permettant une relicence par le mainteneur [CODE] | Electron + React 18 (JSX), ffmpeg | 518 / 424 | 2026-10-12 | Non (application de bureau) | Fort (génération = ComfyUI local obligatoire) | 133 fichiers de tests, 7 workflows CI | Source d'idées (montage) ; **à éviter comme base** (GPL) |
| XmYx/ComfyStudio | MIT | Python PyQt6 | 24 / ? | 2026-07-20 | Non | Fort | non vérifié | À éviter (bureau Qt) |
| ComfyUI | **GPL-3.0** | Python, aiohttp | 144 207 / 6 246 | 2026-10-29 | `--multi-user` : profils par **en-tête `comfy-user`**, **sans authentification** [CODE] | (c'est le moteur) | 29 workflows CI | **Moteur uniquement, derrière une API réseau** |
| ComfyUI_frontend | **GPL-3.0-only** ; certains paquets MIT (account-core, design-system) [CODE] | Vue 3 + TS + pnpm | 2 107 / 12 026 | 2026-10-31 | via backend | Total | 1 835 fichiers de tests, 89 workflows CI | **À éviter comme base** (GPL, Vue) |
| InvokeAI | Apache-2.0 + licences de modèles (RAIL) [CODE] | Python FastAPI + React, SQLite | 28 930 / 23 567 | 2026-10-30 | **Oui, optionnel** : `multiuser` + services `auth/users/board_access` [CODE] | Aucun (moteur propre) | 872 fichiers de tests py, 17 workflows CI | **Meilleur candidat "moteur image alternatif"**, UI trop liée |
| SwarmUI | MIT [CODE] | C# / ASP.NET, JS | 4 724 / 5 051 | 2026-10-30 | Comptes **expérimentaux** ; comptes par défaut sans workflows ComfyUI personnalisés (`docs/Sharing Your Swarm.md`) | Backend ComfyUI par défaut (auto-install) | `SwarmUITests`, 2 CI | Source d'idées (multi-backend) ; stack C#, pas image-first |
| Krita AI Diffusion | **GPL-3.0** | Python (plugin Krita) | 10 808 / 1 786 | 2026-10-03 | n/a | Client ComfyUI | 1 CI | Hors sujet (plugin de bureau) |
| Pinokio | MIT | Electron | 8 337 / 677 | 2026-09-02 | n/a | n/a | 2 CI | Hors sujet (lanceur d'apps locales) |
| Fooocus | GPL-3.0 | Python/Gradio | 53 769 / 1 144 | n/c | n/a | Non | n/c | À éviter : README en "LTS, corrections de bugs seulement", image seulement |
| OpenCut | MIT | Réécriture en cours (Rust + Vite/React 19) | 96 862 / 1 599 | 2026-09-24 | n/a | n/a | 1 CI | Source d'idées pour la timeline ; **projet en pleine réécriture** |
| Toonflow-app | MIT [CODE] | Bun + Vue + vue-flow, plugins de nœuds, agents | 19 993 / 86 | n/c | Non vérifié | Via adaptateurs | non vérifié | Source d'idées (courts métrages) ; doc surtout en chinois |
| Comfield | MIT | Hono (Node 22) + React/Tailwind, `@comfyorg/sdk` | 6 / 2 | 2026-10-17 | Non | Via Comfy SDK/Router | 3 tests | **Utile pour ses presets de caméra** |
| Rosesfield | MIT (nom/logo = marques) | Bun + Hono + React/Vite, drizzle (SQLite/D1), packages `kernel/contract/catalog` | 2 / 1 286 | 2026-10-30 | "Aucun compte" : la clé Comfy fait office de login, données isolées par hash du compte | Via Comfy Router | 482 fichiers `.test.ts`, 2 CI | Source d'idées d'architecture (ports) |
| Backlot, FreeField, Gobo, Cheapsfield, Kinoloom, Mix-Studio, OpenField (x) | MIT/Apache/GPL | divers | 0 à 20 | oct. 2026 | Non | Comfy SDK/ComfyUI | quasi aucun | Œuvres de concours : idées ponctuelles seulement |

---

## 3. Fiches par candidat

### 3.1 BeatDesign - `BeatAPI/BeatDesign` - verdict : source d'architecture (la meilleure), pas un fork direct

- **Licence** [CODE] `LICENSE` Apache-2.0 ; `package.json` "license": "Apache-2.0". Fichier `docs/TRADEMARKS.md` : les noms BeatDesign/BeatAPI ne peuvent pas être réutilisés (interdit d'impliquer un produit officiel). Dépendance vendorée `third_party/mediabunny` sous **MPL-2.0** (copyleft au niveau fichier) [CODE]. Pas de GPL/AGPL au premier niveau.
- **Stack** [CODE] `package.json` : TanStack Start 1.168 + Vite 8 + React 19, `@xyflow/react` (canvas de nœuds), drizzle + `@libsql/client` (SQLite), zod 4, Playwright, serveur MCP (`@modelcontextprotocol/server`), i18n Paraglide. **Ce n'est pas Next.js** ; il faudrait réécrire le routage et le serveur pour l'intégrer à Nexora.
- **Taille** : 590 fichiers, 7 Mo. Dépôt jeune mais soigné : 106 commits, CI (`.github/workflows`, Ubuntu + Windows : `pnpm build`, `typecheck`, `test`, `i18n:check`, Playwright), 152 fichiers `*.test.ts*` sous `src`.
- **Architecture** [DOC+CODE] `docs/ARCHITECTURE.md` : monolithe local-first. Les vues Studio / Canvas / Editor / Assets sont des vues sur les mêmes services. Modèle **centré sur l'asset** : une génération crée un `Asset` ; un nœud du canvas référence un Asset/Generation/Timeline ; un clip de timeline épingle un Asset concret ; un "Take" est un Asset alternatif pour un clip ; la généalogie de génération est stockée séparément des arêtes visuelles. Noyau de commandes unique (UI et MCP passent par `src/core/commands/` avec contrôle de révision CAS et reçus d'idempotence, `project_command_receipt`).
- **Multi-utilisateur** : **impossible en l'état**. Le document dit textuellement "single-user ... no account boundary" et "No user, session, role, order ... table belongs in this repository" ; écoute limitée à loopback (`src/lib/trusted-local-request.ts`, `trusted-workspace-host.ts`). Les clés fournisseur sont chiffrées dans une table `config` locale.
- **Schéma de données** [DOC] 12 tables SQLite : `project`, `project_canvas_state`, `project_timeline_state`, `project_command_receipt`, `project_workflow_state`, `generation_history`, `generation_upload_intent`, `generation_intent_upload`, `asset`, `generation_asset_link`, `project_asset_membership`, `config`.
- **Ajout d'un modèle** [CODE] `src/core/effects/effect-registry.ts` (catalogue logique, 645 lignes) + `src/core/generation-providers/` (contrats, registre, `submit.ts`) + `src/core/adapters/` (`base-adapter.ts`, `beatapi-adapter.ts`, `mock-adapter.ts`). Un autre fournisseur = un adaptateur enregistré dans `src/config/generation-providers.ts` (`docs/PROVIDERS.md`). C'est le meilleur patron d'abstraction vu dans l'enquête.
- **Timeline / montage** [CODE] `src/core/editor/timeline-document.ts` : types `TimelineTrackKind` ('video'|'overlay'|'audio'|'caption'), `TimelineClip`, `TimelineTake`, `TimelineDocument`; sous-titres SRT stylés, export MP4 dans le navigateur (mediabunny), rendu côté MCP via ffmpeg (`render-project-timeline.ts`).
- **Cinema Studio (caméra/objectifs/éclairage)** : **absent** (seulement ratios d'aspect). Pas de bibliothèque de personnages/LoRA ; la notion d'"Elements" (références réutilisables, versionnées) existe dans le code non publié [DOC README].
- **Projets / reprise** : oui, révisions et reçus, `docs/PROJECT_ORGANIZATION.md`.
- **Réutilisable précisément** : (1) le modèle asset-first + lignée séparée du layout ; (2) le Command Kernel avec CAS et idempotence (`src/core/commands/executor.ts`, `persist.ts`, `receipts.ts`) ; (3) le contrat de fournisseur (`src/core/generation-providers/contracts.ts`) ; (4) le schéma `TimelineDocument` ; (5) le principe "preflight puis soumission confirmée" (`generation_upload_intent`). Apache-2.0 permet la réutilisation avec mention (NOTICE) ; ne pas reprendre le nom ni le logo.
- **Risques** : dépendance de conception à l'API commerciale BeatAPI ; pas Next.js ; SQLite mono-utilisateur à remplacer par Postgres ; très jeune (créé en 2026), un seul mainteneur apparent.

### 3.2 Open-Generative-AI (Anil-matcha) et Open-Higgsfield-AI (Autom8AI) - verdict : source d'idées, **ne pas forker**

- **Licence** : `Anil-matcha/Open-Generative-AI/LICENSE` = MIT [CODE]. `Autom8AI/Open-Higgsfield-AI` : **pas de fichier LICENSE** dans l'arbre cloné (`ls` du dépôt) ; seul le README dit "MIT" [DOC]. Pour un usage commercial, un README ne vaut pas une licence : traiter comme non licencié tant que le fichier n'existe pas. Ce dépôt est par ailleurs quasi identique à l'original (même `packages/studio`).
- **Stack** [CODE] : JavaScript (JSX, pas TypeScript) ; `next dev`, mais aussi Vite + Electron ; `packages/studio` (bibliothèque React) ; sous-modules git `Vibe-Workflow`, `Open-Poe-AI`, `Open-AI-Design-Agent` (`.gitmodules`) non récupérés. Architecture : `packages/studio/src/models.js` (35 146 lignes, catalogue "source de vérité"), `muapi.js` (client API, clé en premier paramètre), composants `ImageStudio`, `VideoStudio`, `CinemaStudio`, `WorkflowStudio`, `LipSyncStudio`, `AiInfluencerStudio`, etc.
- **Couplage** : au service commercial **MuAPI** (README : "Powered by MuAPI", "White Label ... Plans start at $49/mo"), clé API stockée dans le `localStorage` du navigateur [DOC]. Inférence locale uniquement en application de bureau (sd.cpp, Wan2GP) [DOC]. Le README se vend comme "no content filters, no guardrails" : positionnement difficile à concilier avec un portail d'entreprise.
- **Multi-utilisateur** : impossible (aucun backend, aucune base).
- **Tests/CI** : 8 fichiers de tests (inférence locale), aucun workflow CI.
- **Cinema Studio** [CODE] `packages/studio/src/components/CinemaStudio.jsx` : tables `CAMERA_MAP` (6 caméras), `LENS_MAP` (10 objectifs), `FOCAL_PERSPECTIVE` (8, 14, 24, 35, 50, 85 mm), `APERTURE_EFFECT` (f/1.4, f/4, f/11) et `buildNanoBananaPrompt(...)` qui compose "shot on a ..., using a ... lens at 35mm (...), aperture f/..., cinematic lighting ...". Utile comme prototype, **pauvre** comparé à Director's Console. Pas de contrôle d'éclairage structuré.
- **Réutilisable** : l'idée du compilateur de prompt ; la structure `*Models.js` + `*Parameters.js` (une famille de modèles = un fichier de métadonnées + un fichier de paramètres) est une bonne pratique pour piloter un formulaire dynamique à partir d'un schéma. Le code lui-même (JS, sans types, 35k lignes de catalogue figé) ne vaut pas un fork.
- **Risques** : gouvernance par un revendeur d'API, absence de licence nette (Autom8AI), absence de CI, étoiles non corrélées à la qualité de l'ingénierie.

### 3.3 ComfyTV (jtydhr88) - verdict : source d'idées ; **base impossible**

- **Licence : incohérente** [CODE+DOC]. `LICENSE` = MIT (Copyright 2026 Terry Jia) ; `pyproject.toml` et `package.json` : MIT ; mais `README.md` (section License) dit **GPL-3.0** et précise que le panneau bot `src/agent/native` est vendoré depuis ComfyUI_frontend (GPL-3.0) ; `src/agent/native/UPSTREAM` : "19085e4... 2026-09-21 src/workbench/extensions/agent (GPL-3.0, Comfy-Org/ComfyUI_frontend)". Conséquence : au minimum cette partie est GPL-3.0, et l'ensemble distribué est probablement à traiter comme GPL. **À faire valider par un juriste avant toute réutilisation.**
- **Stack** [CODE] : extension (`custom_nodes`) de ComfyUI : Python (aiohttp, SQLAlchemy `db.py`) + frontend **Vue 3**, Pinia, Tiptap, three.js, mediabunny, `animation-timeline-js`. ~190 "stages" (nœuds) : image, vidéo (~100 nœuds de montage/étalonnage/incrustation), audio, musique, 3D, "Director console" (timeline plan par plan, cast de références partagé, cache par contenu) [DOC README].
- **Taille/activité** : 3 758 fichiers, 257 Mo ; 414 commits ; version 1.11.2 ; 118 tests Python, 306 tests TypeScript, e2e Playwright, une CI.
- **Couplage** : **total**. Il ne fonctionne que comme extension dans ComfyUI (installation par `git clone` dans `ComfyUI/custom_nodes`).
- **Multi-utilisateur** : `api/collab.py` gère présence/édition collaborative (protocole v1, cookie de session `comfytv_sid`, 365 jours) **sans comptes** ni isolation.
- **Cinema/caméra** [CODE] `src/widgets/three/scene3d/filmVocab.ts` : échelle de plans (`SIZE_LADDER` de "extreme close-up" à "extreme wide shot"), niveaux d'angle (`shotLevelLabel` : ground level, low angle, eye level, high angle, bird's-eye), vues (`shotViewLabel`), échelle focale (14-135 mm), `describeShotPose`. Idée excellente : **dériver le texte du plan à partir d'une pose de caméra 3D**.  Widget "multiangle" azimut/élévation/distance -> prompt de vue (`docs/image-tools.md`).
- **Réutilisable** : uniquement **concepts** (jamais copier le code tant que la licence n'est pas tranchée) : pose caméra 3D -> phrase de cadrage ; stages avec snapshot amont ; cast de références partagé ; bibliothèque `@`-références dans les prompts.
- **Risques** : licence ambiguë, Vue (Nexora est React), dépendance à ComfyUI, énorme surface (190 stages).

### 3.4 Director's Console (NickPittas) - verdict : **source de données/règles cinéma à réutiliser** (MIT)

- **Licence** [CODE] `LICENSE` MIT (Copyright 2026 Nick Pittas). Aucune dépendance copyleft vue au premier niveau (non audité en profondeur).
- **Stack** : trois services Python/FastAPI + frontend React 18/Vite/Zustand/three.js ; lanceur `start.py` (ports 9800/9820/5173) [DOC `README.md`, `codemap.md`]. SQLite pour la galerie. 80 commits, 364 étoiles, 52 fichiers de tests, une CI. Dernier commit du clone : 2026-10-02.
- **Couplage ComfyUI** : fort pour l'exécution (REST/WebSocket directement du navigateur vers un ou plusieurs nœuds ComfyUI, génération parallèle), **nul pour la partie cinéma** : le module `CinemaPromptEngineering/cinema_rules` est autonome (`target_models.py` : "Keep this module dependency-free").
- **Multi-utilisateur** : **non** (aucune authentification dans `Orchestrator/orchestrator/api/server.py`, seulement CORS). Un fichier SQLite `Orchestrator/data/orchestrator.db` est même commité dans le dépôt (mauvaise hygiène).
- **Cinema Studio** [CODE] `CinemaPromptEngineering/cinema_rules/` : `schemas/live_action.py` (569 lignes : énumérations `CameraBody`, `CameraManufacturer`, `SensorSize`, `FilmStock`, `AspectRatio`, `LensFamily`, `LensMountType`, `MovementEquipment`, `MovementType`, `MovementTiming`, `TimeOfDay`, `LightingSource`, `LightingStyle`, modèles Pydantic `CameraConfig`, `LensConfig`, `MovementConfig`, `LightingConfig`, `LiveActionConfig`), `rules/engine.py` (1 953 lignes : validation de compatibilité caméra/objectif/époque/support), `prompts/generator.py` (262 lignes), `presets/live_action.py` (1 599 lignes), `presets/animation.py`, `presets/cinematography_styles.py` (964 lignes), `target_models.py` (profils de prompt par modèle cible : Midjourney, FLUX.x, Veo, Kling, LTX, Wan...). Doc de référence : `docs/cinematography-reference.md` (ARRI, RED, Sony, Panavision, Cooke, Zeiss, stocks Kodak Vision3, focales 8-1200 mm...). C'est le **vocabulaire de cinéma le plus riche de l'enquête**.
- **Bibliothèque / projets** : Gallery (notes, étiquettes, comparaison, corbeille), projets sur disque, reprise de session (`docs/session-recovery.md`). Pas de bibliothèque LoRA/personnages structurée.
- **Réutilisable précisément** : (1) les énumérations et modèles Pydantic comme **source** pour générer des types TypeScript/zod ; (2) `cinema_rules/rules/engine.py` comme spécification de règles de compatibilité (à porter en TS ou à exposer en micro-service Python) ; (3) `target_models.py` : IDs stables de modèles cibles + profils d'amélioration (`Documentation/PROMPT_ENHANCEMENT_PROFILES.md`) ; (4) les presets "films" (`presets/live_action.py`).
- **Risques** : projet d'un seul auteur ; interface à trois services bricolée (lanceur `.bat`, chemins Windows `c:\Users\npittas` dans `codemap.md`) ; marques commerciales (ARRI, RED...) dans les libellés : à relire par le juridique si exposé à des clients.

### 3.5 Velorn (ex-ComfyStudio de JaimeIsMe) - verdict : source d'idées de montage, **à éviter comme base** (GPL)

- **Licence** [CODE] `LICENSE` = GNU GPL v3 ; `package.json` "GPL-3.0-only" ; README : "Versions released before this license change remain available under the license terms they were released with" -> la licence a changé (l'ancienne n'est pas visible dans un clone `--depth 1`). `CONTRIBUTOR_LICENSE_AGREEMENT.md` autorise le mainteneur à redistribuer vos contributions "under future project licenses, including open-source, source-available, d[ual/commercial]..." : le mainteneur garde donc la porte ouverte à une licence commerciale que **vous** n'auriez pas.
- **Stack** [CODE] : Electron + React 18 (JSX), ffmpeg, whisper, RIFE, serveur MCP embarqué (`electron/mcpServer.js`), 133 fichiers de tests, 7 workflows CI. 424 commits, 518 étoiles.
- **Multi-utilisateur** : n/a, application de bureau mono-poste. Génération = ComfyUI local obligatoire ("All current generation features require a locally running ComfyUI") [DOC].
- **Fonctions** [DOC] : éditeur à pistes, transitions, effets, sous-titres, export, génération depuis la timeline, création de clips musicaux/UGC, projets.
- **Réutilisable** : concepts de timeline uniquement (dérive GPL si copie). Dépôt de 309 Mo (assets), à ne pas intégrer.

### 3.6 ComfyUI (moteur) et ComfyUI_frontend - verdict : **moteur derrière une API réseau**, frontend à éviter

- **Licence** [CODE] `LICENSE` GPL-3.0 pour `comfyanonymous/ComfyUI` et `Comfy-Org/ComfyUI_frontend` (`package.json` "GPL-3.0-only"). Quelques paquets du monorepo frontend sont MIT (`packages/account-core`, `account-ui`, `billing-contract`, `design-system`, `ingest-types`) et d'autres GPL (`object-info-parser`).
- **Implications (pas un avis juridique)** :
  - Faire **tourner** ComfyUI comme service interne et lui parler en HTTP/WebSocket n'oblige pas à publier le code de l'interface Nexora ; c'est un programme distinct communiquant par réseau (cas usuel de la GPL, qui n'a pas la clause réseau de l'AGPL). 
  - **Embarquer, modifier ou redistribuer** ComfyUI, son frontend, ou des custom nodes GPL dans une offre livrée aux clients (on-prem, image Docker distribuée) déclenche les obligations GPL-3.0 pour ces composants.
  - **Importer du code** du frontend ComfyUI (Vue) ou de projets qui le vendorent (ComfyTV) dans l'interface Nexora la rendrait dérivée -> GPL-3.0 à tout le portail. À proscrire.
  - Le SDK TypeScript officiel `@comfyorg/sdk` 0.5.0 est **MIT** (registre npm : dépôt `Comfy-Org/comfy-typescript-sdk`, "TypeScript SDK for running ComfyUI workflows via the Comfy API v2 (self-hosted, Comfy Cloud, serverless)") : c'est le point d'intégration propre.
- **API** [CODE] `openapi.yaml` (racine de ComfyUI) : `/api/prompt`, `/api/queue`, `/api/jobs`, `/api/jobs/{id}`, `/api/jobs/{id}/assets`, `/api/assets`, `/api/view`, `/api/upload/image`, `/api/object_info`, `/api/history_v2`, `/api/interrupt`, `/api/workflows`, `/api/userdata`... Surface stable et riche.
- **Multi-utilisateur** [CODE] `comfy/cli_args.py:225` `--multi-user` ("Enables per-user storage"), `app/user_manager.py:61` : l'utilisateur est lu dans l'en-tête `comfy-user`, **sans mot de passe ni jeton**. C'est de l'isolation de rangement, **pas de la sécurité** : un client qui atteint l'API peut usurper n'importe quel utilisateur. Il faut donc que seul le backend Nexora atteigne ComfyUI (réseau privé) et que Nexora gère les comptes, quotas et files.
- **Ajout d'un modèle** : via workflows JSON au format API + nœuds `comfy_api_nodes` (partenaires) ; pas de registre central de modèles côté UI.
- **Frontend ComfyUI** : Vue 3, 12 026 commits, 89 workflows CI, 1 835 fichiers de tests. Remplaçable (`--front-end-root`, `comfy/cli_args.py:259`) mais GPL : non.

### 3.7 InvokeAI - verdict : meilleur moteur/outil alternatif pour l'image, pas une base d'UI vidéo

- **Licence** [CODE] `LICENSE` Apache-2.0 (+ notices pour code vendoré : `LICENSE-HiDiffusion.txt`, `LICENSE-PiD.txt`) et licences de modèles `LICENSE-SD1+SD2.txt` (CreativeML OpenRAIL-M), `LICENSE-SDXL.txt` (OpenRAIL++-M) : restrictions d'usage des **poids**, à traiter séparément.
- **Stack** : Python FastAPI + frontend React/TS (dossier `invokeai/frontend/web`, non lu en détail) ; 23 567 commits, 28 930 étoiles, 872 fichiers de tests Python, 17 workflows CI. Dernier commit 2026-10-30.
- **Multi-utilisateur** [CODE] `invokeai/app/services/config/config_default.py:302` `multiuser` (défaut `False` : "single-user mode using a default system account with administrator privileges"; activé : authentification/autorisation) ; services `auth/` (`password_utils.py`, `token_service.py`), `users/`, `board_access/`. **Seul projet de l'enquête avec une vraie couche comptes native** (non testée ici).
- **Abstraction des modèles** : gestionnaire de modèles (`model_manager`, `model_install`, `model_records`), graphe de nœuds (`session_queue`, `invocation_*`), et un service `external_generation/` avec une classe abstraite `ExternalProvider` (`provider_id`, `is_configured`, ...) pour brancher des API externes [CODE `external_generation_base.py`]. Des services `video_files`, `video_records`, `board_video_records`, `videos` existent [CODE] : maturité vidéo non évaluée.
- **Cinema Studio** : absent.
- **Pourquoi pas une base d'UI** : l'interface est celle d'InvokeAI (produit complet, canvas unifié, galerie) ; l'intégrer en iframe/portail ou la forker reviendrait à maintenir un très gros produit tiers. En revanche, **comme moteur multi-utilisateur pour l'image** derrière l'API Nexora, c'est une piste sérieuse à comparer à ComfyUI.

### 3.8 SwarmUI - verdict : source d'idées (multi-backend), pas une base

- **Licence** [CODE] `LICENSE.txt` MIT ; mais installe ComfyUI (GPL) comme backend (README : "auto-install ComfyUI (GPL)").
- **Stack** : C# / ASP.NET, interface JS ; 5 051 commits, 4 724 étoiles ; `src/Accounts/` (`User.cs`, `SessionHandler.cs`), `src/Backends/`, `src/WebAPI/`. Le doc `docs/Advanced Usage.md` annonce le support multi-utilisateur "in an initial experimental form" avec "a barrier in front" requis ; `docs/Sharing Your Swarm.md` : les comptes standard ne peuvent pas utiliser les workflows ComfyUI personnalisés "because it is difficult to perform security validation on the comfy backend" (aveu utile sur le risque de laisser des workflows arbitraires à des utilisateurs).
- **Réutilisable** : le concept de pool de backends GPU, les permissions par rôle, la politique "pas de workflow libre pour les comptes standards". Stack C# incompatible avec Nexora.

### 3.9 Candidats secondaires (analyse légère)

- **Comfield** (`synthetic-ape/comfield`, MIT, 2 commits, 6 étoiles) : `shared/presets.ts` (183 lignes) = **27 mouvements de caméra** (`MOTIONS`) avec pour chacun un texte de prompt, un identifiant d'animation de prévisualisation et, si pertinent, la **commande native Veo** (`veo: "push_in"`, `"pan_left"`, ...) ou **Kling** (`kling: { type: "simple", config: { zoom: 5 } }`), plus 14 styles (`STYLES`) et `ShotSettings` (taille de plan, angle, objectif, profondeur de champ, éclairage). `shared/types.ts` : `ModelFeatures`, `GenerateRequest`, `Generation` avec jusqu'à 4 "takes" A-D. Architecture Hono + React, appel à `@comfyorg/sdk` (Comfy Router / API v2). Tests de validation des corps de requêtes contre les schémas publiés des modèles (`tests/router-schemas.test.ts`). **Très réutilisable pour le vocabulaire caméra->modèle** (fichier court, MIT, à relire/valider avant copie car dépôt de concours).
- **Rosesfield** (`rossaai/rosesfield`, MIT, 1 286 commits, 2 étoiles, publié en octobre) : monorepo Bun/Hono/React avec paquets `kernel`, `contract`, `catalog`, `generation`, `library`, `agent` ; règle d'architecture "le moteur reste derrière un port" (`CLAUDE.md`), idempotence + timeout + nombre de relances sur chaque appel payant, "owner lock", données isolées par hash du compte Comfy (`docs/architecture.md`), SQLite/D1 via drizzle. Bon exemple de **séparation domaine/moteur**, mais single-owner. Le nom et le logo sont des marques (TRADEMARKS.md).
- **Backlot** (`Arfolomew/backlot`) : `app/cinema.json` et `app/moves.json` = données de caméras/mouvements  ; serveur Python `app/server.py` ; orienté 16 Go de VRAM ; MIT. À consulter comme jeu de données, pas comme base.
- **FreeField** (`droppedmyza/freefield`) : idée à retenir : un **preset = un dossier** (workflow ComfyUI + `preset.json` qui expose les entrées) + vérifications automatiques de sortie (`freefield/output_checks.py`, `edge_check.py`) et relance. Dépôt à 2 commits.
- **Gobo** (`RickBL99/gobo`, Apache-2.0/MIT, 0 étoile) : "Say the film" : pilotage automatique, Rust/WASM pour l'étalonnage ; mentionne caméra, objectif, focale, ouverture, cadrage, angle, mouvement, lumière, pellicule : mêmes catégories que Director's Console ; très jeune.
- **Toonflow-app** (`HBAI-Ltd/Toonflow-app`, MIT [CODE `LICENSE`], Bun + Vue + vue-flow, monorepo `apps/{web,server,desktop,mobile}` et `packages/{nodes,tools,ext,providers,mcp,teams,...}`) : plateforme "court-métrage / manhua" avec agents, plugins de nœuds (`packages/nodes/director3dNode`...), adaptateurs de fournisseurs (dont ComfyUI). Documentation principalement en chinois. Idée utile : **plug-ins de nœuds** et fournisseurs configurables. Non analysé en profondeur.
- **OpenCut** (MIT, 96 862 étoiles) : éditeur vidéo web ; **réécriture complète annoncée** (noyau Rust, API d'éditeur, MCP, plugins), l'ancienne version est dans `opencut-app/opencut-classic`. Référence pour une future timeline, instable aujourd'hui.
- **Pollinations**, **Pinokio**, **Krita AI Diffusion**, **Fooocus**, **XmYx/ComfyStudio**, **Mix-Studio** (GPL-3.0, interface mobile pour ComfyUI), **Kinoloom**, **Cheapsfield** : voir tableau ; pas de base pertinente pour un portail Next.js multi-utilisateur.

---

## 4. Synthèse transversale (réponses aux questions posées)

**Multi-utilisateur / multi-tenant**
- Natif et sérieux : **aucun** studio de type Higgsfield. InvokeAI (comptes optionnels) et SwarmUI (expérimental) sont des outils de génération, pas des studios de projets/montage.
- ComfyUI : isolation par en-tête non authentifié -> **ne jamais l'exposer directement** ; Nexora doit être l'unique client.
- Tous les studios "à la Higgsfield" de cette enquête sont **mono-utilisateur local** (SQLite, localStorage, clé API de l'utilisateur) : BeatDesign (explicitement), Director's Console, Open-Generative-AI, Rosesfield, Comfield, Velorn. Stockage multi-tenant (Postgres, buckets, quotas, files d'attente) est donc à construire dans tous les cas.

**Abstraction des modèles (comment ajouter un modèle)**
- Meilleurs patrons : BeatDesign (`effect-registry.ts` logique + `generation-providers/` + adaptateurs), InvokeAI (`ExternalProvider` abstrait), Open-Generative-AI (`*Models.js` + `*Parameters.js` pilotant des formulaires), Rosesfield (ports), Comfield (`ModelInfo`/`ModelFeatures`).
- Aucun ne gère proprement un **moteur GPU interne** à la fois : ils appellent des API cloud (MuAPI, BeatAPI, Comfy Router) ou un ComfyUI unique.

**Fonctions Cinema Studio (caméra, objectifs, éclairage)**
- Le plus riche : Director's Console (`cinema_rules`), puis Comfield (`shared/presets.ts` avec mappage natif Veo/Kling), ComfyTV (`filmVocab.ts`, pose 3D -> texte), Open-Generative-AI (`CinemaStudio.jsx`, simple).
- Higgsfield annonce en plus rythme et jeu des personnages [DOC] : non couvert par ces projets, sauf par des "skills" de prompts hors sujet (ex. `OSideMedia/higgsfield-ai-prompt-skill`, dépôt de prompts, 826 étoiles, non analysé).

**Timeline / montage** : Velorn (complet mais GPL, bureau), ComfyTV (nœuds + Director console, GPL/Vue), BeatDesign (document de timeline propre + export navigateur), OpenCut (en réécriture). Le montage complet n'est pas indispensable au MVP du mode simple.

**Bibliothèque de personnages / LoRA** : peu de choses réutilisables : ComfyTV (cast partagé, `@`-références, GPL), Rosesfield (personnages dans le modèle de données), BeatDesign ("Elements" versionnés, non publié), Backlot (modes références, 9 images). Aucun gestionnaire LoRA multi-tenant. À concevoir dans Nexora.

**Projets sauvegardés / reprise** : bien résolu par BeatDesign (révisions CAS, reçus d'idempotence) et par Comfield (reprise après redémarrage via Comfy Router).

**Mode simple + mode expert** : le meilleur schéma est celui de ComfyUI App Mode / ComfyTV (graphe expert derrière une surface simplifiée) et de Gobo/Backlot (réglages avancés repliables). Rien à copier tel quel.

---

## 5. Recommandation

### Choix : (b) construire l'interface Nexora Creative nativement dans le portail Next.js, en important des **contrats, schémas et jeux de données** (pas des applications), et en parlant aux moteurs GPU par une couche d'adaptateurs.

**Pourquoi pas (a) un fork d'un studio existant**
1. **Aucun candidat ne coche les cases de départ** : multi-utilisateur, Postgres, Next.js/React 19/Tailwind, moteurs GPU privés. Le fork le plus proche en philosophie (BeatDesign) est TanStack Start + SQLite mono-utilisateur, "no account boundary" par conception : on réécrirait le serveur, l'auth, la persistance et les routes, soit l'essentiel de la valeur.
2. **Licences** : Velorn (GPL-3.0 + CLA qui réserve une relicence au mainteneur), ComfyTV (MIT/GPL contradictoires + code GPL vendoré), ComfyUI et son frontend (GPL-3.0) sont incompatibles avec un portail fermé s'ils sont fusionnés ; Open-Higgsfield-AI (Autom8AI) n'a même pas de fichier de licence.
3. **Dette et gouvernance** : Open-Generative-AI est un front JavaScript sans types ni CI couplé à un revendeur d'API et à des clés en `localStorage` ; les projets de concours ont 1 à quelques commits et un seul auteur. Un fork nous rendrait responsables de milliers de lignes que nous n'avons pas conçues.

**Pourquoi pas (c) un portage vers InvokeAI ou ComfyUI comme interface**
- InvokeAI (Apache-2.0, comptes optionnels) est une très bonne piste de **moteur image** à évaluer en spike, pas une UI de studio vidéo ; ComfyUI/SwarmUI imposent GPL/C# ou un modèle de sécurité (en-tête `comfy-user`) inadapté à du multi-tenant.

**Ce qu'il faut concrètement prendre dans chaque projet (licence permettant)**

| Besoin Nexora | Source | Comment | Licence |
|---|---|---|---|
| Modèle de données projets/assets/généalogie/takes | BeatDesign `docs/ARCHITECTURE.md`, `src/core/db/`, `src/core/commands/` | Réécrire en Postgres (drizzle ou autre) avec `tenant_id`, garder CAS + reçus d'idempotence | Apache-2.0 (mention + NOTICE si code copié) |
| Contrat fournisseur de génération | BeatDesign `generation-providers/contracts.ts`, InvokeAI `ExternalProvider`, Rosesfield "port" | Définir un `GenerationEngine` TS avec adaptateurs : ComfyUI (via `@comfyorg/sdk` MIT ou HTTP), API cloud, futur moteur maison | idées / Apache / MIT |
| Vocabulaire Cinema Studio | Director's Console `cinema_rules/` (énumérations + règles + profils par modèle) ; Comfield `shared/presets.ts` (27 mouvements + mappage Veo/Kling) ; ComfyTV `filmVocab.ts` (**idée seulement**) | Générer des types zod depuis les énumérations Pydantic, porter `engine.py` en TS (ou service Python isolé), copier `MOTIONS`/`STYLES` | MIT (DC, Comfield) ; ComfyTV : ne pas copier |
| Timeline | BeatDesign `timeline-document.ts` (schéma) ; mediabunny pour export navigateur | Schéma + moteur de lecture propre ; mediabunny est **MPL-2.0** (obligations au niveau fichier) | Apache/MPL-2.0 |
| Presets "effets" (mode simple) | FreeField (preset = workflow + `preset.json`) | Format de preset déclaratif versionné, validations de sortie | MIT, concept |
| Mode simple vs expert | ComfyUI App Mode (concept), Gobo | Mode simple = presets/compilateur de prompt ; expert = paramètres avancés par modèle et, plus tard, éditeur de workflow réservé à des rôles de confiance (cf. SwarmUI) | concepts |
| Intégration moteur | `@comfyorg/sdk` (MIT) et API HTTP ComfyUI (`openapi.yaml`) | Backend Nexora seul client, réseau privé, quotas/files côté Nexora | MIT / GPL (service distinct) |

**Plan de réduction du risque (suggestion, 1 à 2 semaines)**
1. Faire valider par le juridique : (i) usage de ComfyUI/ComfyUI_frontend en service interne vs livraison à des clients ; (ii) l'ambiguïté MIT/GPL de ComfyTV ; (iii) les poids de modèles (RAIL, licences LTX/Wan/MiniMax) ; (iv) l'usage de noms de marques (ARRI, RED, Higgsfield) dans l'UI.
2. Spike A : un `GenerationEngine` avec adaptateur ComfyUI via `@comfyorg/sdk` sur un moteur GPU, file Postgres, assets en stockage objet, un utilisateur isolé -> prouver le multi-tenant (le point qu'aucun studio ne résout).
3. Spike B : porter 20 presets de caméra (Comfield + Director's Console) en JSON versionné et un compilateur de prompt par modèle cible ; mesurer le gain qualité sur 2 modèles réels (nécessite un test que cette enquête n'a pas fait : **[TEST] manquant**).
4. Spike C (optionnel) : évaluer InvokeAI en mode `multiuser` comme moteur image alternatif.
5. Ne pas démarrer de montage non linéaire complet au MVP : utiliser un schéma de timeline minimal (modèle BeatDesign) et réévaluer OpenCut quand sa réécriture sera stable.

### Points non vérifiés / à ne pas prendre pour acquis
- Aucune exécution : performances, fiabilité et qualité réelle des sorties de tous ces projets sont inconnues.
- Licences transitives, vulnérabilités (npm audit/pip-audit) non évaluées.
- Maturité vidéo d'InvokeAI (présence de services vidéo seulement constatée dans le code).
- Les pages du hub Comfy (Cinematic Studio, Re-shoot, Openjutsu) n'ont pas pu être lues.
- "AI Movie Studio 2" et la plupart des variantes de "OpenField" : introuvables ou sans rapport.
- Les chiffres de popularité sont des relevés ponctuels, sans validation d'authenticité.
