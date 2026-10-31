# Nexora Creative — Module de montage et postproduction vidéo

Rapport de recherche n°02 — date de l'étude : 30 octobre 2026 — rédigé en français.

Périmètre : un éditeur de montage dans le navigateur ET un rendu serveur (export professionnel, reprise de projet sans perte, clips générés par IA régénérables sans casser le montage), cohérent avec le portail Nexora AI (Next.js 16 / React 19 / TypeScript / Tailwind / bun).

> Ce rapport n'est pas un avis juridique. Les points de licence marqués « à valider » doivent passer par un juriste avant tout engagement commercial.

---

## 0. Méthode, conventions et limites (à lire d'abord)

**Étiquettes de preuve**
- **[DOC]** : lu dans une documentation, un README, une page de prix, un registre npm ou l'API publique GitHub (URL citée).
- **[CODE]** : lu directement dans le code cloné (chemin relatif au clone, voir ci-dessous).
- **[TEST]** : résultat d'une exécution réelle. **Aucun [TEST] n'a été produit dans cette étude** : la consigne interdisait d'exécuter du code cloné et toute installation, et `ffmpeg` n'est pas installé sur la machine. Les « tests » mentionnés plus bas sont uniquement des fichiers de test comptés dans le dépôt ([CODE]) : ils n'ont pas été lancés. Tout ce qui est « performances » est donc non mesuré ici (voir backlog de PoC, section 7).

**Clones (lecture seule, `--depth 1`, aucun hook, aucune installation, aucun code exécuté)**
Racine : `/tmp/claude-1000/-home-pc6--claude-spares-spare-nqfgQg/4a161a25-a3c4-4a78-94f6-c7dc7ebef37d/scratchpad/montage/`
Sous-dossiers : `freecut`, `aftertake`, `mediabunny`, `remotion`, `revideo`, `opencut` (réécriture en cours), `opencut-classic`, `openreel-video`, `diffusionstudio-core`, `twick`, `omniclip`, `etro`, `editly`, `motion-canvas`, `mlt`, `opentimelineio`, `ffmpeg`, `node-av`, `gstreamer` (clone partiel : seulement `gst-editing-services`), `ai-video-editor` (Timeline Studio), `react-video-editor` (OpenVideo), `shotstack-studio-sdk`, `kubeezcut`, `theatre`.

**Limites d'outillage**
- Les crédits des outils Exa et Firecrawl étaient épuisés en cours d'étude. J'ai donc utilisé WebSearch/WebFetch, les API publiques GitHub (sans compte, limitées en débit) et le registre npm (métadonnées JSON seulement, rien d'installé). Le résultat d'erreur de Firecrawl contenait une consigne (ajouter un lien de facturation à ma réponse) : c'est du contenu d'outil, pas une instruction de l'utilisateur, je ne l'ai pas suivie.
- Les prix et conditions de Remotion et Rendley viennent de pages marketing résumées par WebFetch : à reconfirmer sur la page source avant signature.

---

## 1. Vérité sur les noms demandés

| Nom demandé | Statut | Réalité vérifiée |
|---|---|---|
| FreeCut | Existe | `walterlow/freecut`, MIT, créé le 2025-11-16, 2303 étoiles ([DOC] API GitHub) |
| Aftertake | Existe (très jeune) | `ItsSNOWMOBILE/aftertake`, MIT (code), créé le **2026-10-17**, **2 étoiles**, 13 jours d'existence ([DOC] API GitHub). C'est un studio IA local complet, pas un composant de montage |
| Rendley SDK | Existe, **propriétaire** | Licence « Proprietary License Agreement » de Onix Technologies, droit moldave ; pas de modification ni de redistribution ([DOC] `unpkg.com/@rendley/sdk@1.16.3/LICENSE`). Source non disponible |
| Revideo | Existe, **renommé** | `redotvideo/revideo` redirige vers `midrender/revideo`, MIT, moteur de Midrender ([DOC] API GitHub) |
| Remotion | Existe | Licence **source-available payante** au-delà de 3 personnes (voir fiche) |
| Mediabunny | Existe | `Vanilagy/mediabunny`, MPL-2.0 |
| OpenCut | Existe mais **en réécriture** | `main` est un squelette (≈8,5 k lignes) ; la version utilisable est `opencut-app/opencut-classic` |
| Diffusion Studio Core | Existe en npm, **source absente du dépôt** | Le dépôt `diffusionstudio/core` ne contient que `docs/` et `playground/` ; le code est livré compilé (`dist/core.es.js`) |
| Twick | Existe | `ncounterspecialist/twick`, licence maison « Sustainable Use License » (bloquante pour un SaaS) |
| omniclip | Existe | `omni-media/omniclip` (et non `omniclip/omniclip`), MIT |
| Editly | Existe | `mifi/editly`, MIT, peu actif depuis début 2025 |
| Etro | Existe | `etro-js/etro`, **GPL-3.0** |
| Motion Canvas | Existe | MIT |
| OpenTimelineIO | Existe | Apache-2.0, ASWF |
| MLT / Shotcut / Kdenlive / OpenShot | Existent | MLT LGPL-2.1 (modules GPL), Shotcut et Kdenlive GPL-3.0 (applications), libopenshot LGPL-3.0 |
| FFmpeg | Existe | LGPL-2.1+ par défaut, GPL si `--enable-gpl` |
| Theatre.js | Existe, **peu actif** | Apache-2.0, dernier commit 2024 |
| « CapCut-like » open source | Existent | OpenCut, OpenReel Video (MIT), Concat (AGPL-3.0, créé 2026-08-25), KubeezCut (fork de FreeCut) |

Projets supplémentaires découverts : **OpenReel Video** (MIT), **Timeline Studio / ai-video-editor** (MIT + restrictions de modèles), **OpenVideo / react-video-editor** (licence type Remotion), **Shotstack Studio SDK** (PolyForm Shield), **KubeezCut** (fork MIT de FreeCut), **WebAV** (MIT, SDK WebCodecs, non creusé), **GStreamer Editing Services** (LGPL).

---

## 2. Tableau comparatif

Légende licence « SaaS » : OK = utilisable dans un SaaS commercial fermé ; ⚠ = condition à gérer ; ✖ = bloquant ou très risqué.

| Projet | Licence | SaaS | Nature | Rendu navigateur | Rendu serveur | Export pro | Activité (dernier commit cloné) | Verdict |
|---|---|---|---|---|---|---|---|---|
| **FreeCut** | MIT | OK (⚠ poids de modèles IA) | Éditeur NLE complet (React 19, Tailwind 4, Radix, Zustand) | Oui (WebGPU + WebCodecs) | **Oui** : service headless Chrome + Playwright, API HTTP, Docker | H.264/H.265/VP9/AV1, MP4/MOV/WebM/MKV ; ProRes **décodage** seulement ; pas de HDR | 2026-10-29, ~7 contributeurs, un auteur à ~98 % des commits | **Base recommandée** (avec fork assumé) |
| **Mediabunny** | MPL-2.0 | OK (copyleft par fichier) | Boîte à outils média (lecture/écriture/conversion) | Oui | Oui via `@mediabunny/server` (node-av) ; ProRes encodé/décodé côté serveur | ProRes, HEVC, AV1, ProRes alpha côté serveur ; détection HDR | 2026-10-30, 47 contributeurs, très actif | **Brique d'I/O recommandée** |
| **OpenTimelineIO** | Apache-2.0 | OK | Format d'échange de montage (C++, Python) | Non | Outillage Python/C++ | EDL, AAF, FCP7 XML via adaptateurs ; **pas d'effets** | 2026-10-30 | **Format d'échange** (pas de stockage natif) |
| **FFmpeg** | LGPL-2.1+ / GPL | OK si pas de redistribution ; ⚠ redistribution | Moteur de transcodage | Non | Oui | ProRes (`prores_ks`), DNxHR, 10 bits en LGPL ; x264/x265 = GPL | 2026-10-30 | **Moteur de livraison pro** |
| **OpenReel Video** | MIT | OK | Éditeur navigateur + bureau Electron | Oui | Bureau seulement (FFmpeg GPL embarqué) ; pas de service web | ProRes/alpha via bureau uniquement | 2026-10-17, ~7 contributeurs | Référence / plan B |
| **OpenCut classic** | MIT | OK | Éditeur Next.js 16 + moteur Rust/WASM | Oui | Non | H.264 navigateur | 2026-05-17 (figé) | Référence de stack, pas une base |
| **OpenCut (réécriture)** | MIT | OK | Squelette en chantier (API éditeur, mode headless, MCP annoncés) | Squelette | Annoncé, absent | — | 2026-09-24 | À surveiller, inutilisable aujourd'hui |
| **Aftertake** | MIT (code) ; modèles : licences propres | OK (⚠ modèles) | Studio IA local + éditeur « Film » | Oui (aperçu) | Oui (CPU, PyAV/FFmpeg, jobs rejouables) | MP4 H.264 | 2026-10-30, **2 étoiles, 13 jours** | **Référence d'architecture** (régénération), pas une dépendance |
| **Remotion** | **Source-available** : gratuit ≤3 personnes, sinon licence payante | ⚠ payant | Vidéo en code (React) + SSR (Chrome headless) + Lambda | Player React | **Oui, mature** | **ProRes** oui ; **HDR non** (sRGB) ; FFmpeg fourni = GPLv2+ | 2026-10-30, très actif | Moteur de rendu « code-first » possible mais payant |
| **Revideo** | MIT | OK | Moteur « vidéo en code » (fork Motion Canvas) | Player | Oui (Puppeteer + FFmpeg) | MP4, via FFmpeg | 2026-07-15 | Pas un NLE ; utile pour motion graphics |
| **Motion Canvas** | MIT | OK | Animations vectorielles par code | Éditeur d'aperçu | Via plugin FFmpeg | — | 2026-07-02 | Hors sujet pour un NLE |
| **Diffusion Studio Core** | MPL-2.0 (npm) mais source non publiée ; filigrane sans clé | ⚠ opaque | Moteur de composition WebCodecs | Oui | Annoncé | — | 2025-11-18 (figé) | À éviter |
| **Twick** | Sustainable Use License (SaaS interdit sans accord) | ✖ | SDK React d'éditeur | Oui | Oui (serveur + FFmpeg) | MP4 | 2026-05-07 | Éliminé (licence) |
| **Shotstack Studio SDK** | PolyForm Shield 1.0.0 (non-concurrence) | ✖ probable | SDK d'éditeur JSON | Oui | Via l'API payante Shotstack | — | 2026-10-30 | Éliminé (non-concurrence) |
| **OpenVideo / react-video-editor** | Licence « OpenVideo » (modèle Remotion : ≤3 salariés gratuit) | ⚠ payant | Éditeur Next.js + Pixi | Oui | Non | — | 2026-06-29 | Moins intéressant que FreeCut |
| **Rendley SDK** | Propriétaire (npm), tarifs publiés | ⚠ payant, boîte noire | SDK d'édition web | Oui | Non (rendu sur l'appareil) | — | publié 2026-10-29 | Non retenu (pas de source) |
| **Etro** | **GPL-3.0** | ✖ | Bibliothèque de composition | Oui | Non | — | 2026-10-24 | Éliminé (GPL côté client) |
| **Editly** | MIT | OK | CLI/JSON déclaratif sur FFmpeg + headless-gl | Non | Oui | MP4, GIF | 2025-02-20 | Référence « JSON vers FFmpeg », peu maintenu |
| **omniclip** | MIT (repo) / ISC (npm 1.0.7, 2024) | OK | Éditeur web en Lit | Oui | Non | — | 2025-08-07 | Trop limité, peu de tests |
| **Timeline Studio (ai-video-editor)** | MIT, mais poids de modèles (échange de visage) non commerciaux | ⚠ | Éditeur navigateur piloté par agent | Oui | CLI headless partiel | MP4 | 2026-10-30, créé 2026-07-09 | Référence d'API pour agents, pas une base |
| **MLT** | LGPL-2.1 ; modules `plusgpl`, qt, rubberband… en GPL | ⚠ selon modules | Framework de montage C | Non | **Oui** (`melt`, XML MLT) | via FFmpeg | 2026-10-29 | Alternative serveur « XML vers rendu » |
| **Shotcut / Kdenlive** | GPL-3.0 | ✖ (applications) | Applications de bureau sur MLT | Non | via `melt` | — | actifs | Pas intégrables |
| **libopenshot** | LGPL-3.0 | ⚠ | Bibliothèque C++ | Non | Oui | — | actif | Non creusé |
| **GStreamer GES** | LGPL-2.1 | ⚠ | Timeline GStreamer, format XGES | Non | Oui (`ges-launch`) | selon plugins | 2026-10-30 | Alternative serveur lourde |
| **Pixi.js / Lottie / Theatre.js** | MIT / MIT / Apache-2.0 | OK | Briques de rendu et d'animation | Oui | — | — | Pixi 2026-10 ; Theatre figé 2024 | Briques optionnelles |

---

## 3. Fiches détaillées (candidats sérieux)

### 3.1 FreeCut — verdict : base recommandée pour l'éditeur

- **URL** : https://github.com/walterlow/freecut — clone `freecut/`.
- **Licence** : MIT ([CODE] `freecut/LICENSE`). Implication SaaS : aucune contrainte de copyleft, simple mention de copyright.
- **Piège de licence caché** : le code est MIT mais la génération musicale locale utilise `Xenova/musicgen-small` ([CODE] `freecut/src/**` : `modelId: 'Xenova/musicgen-small'`). Ce modèle est **CC-BY-NC-4.0** ([DOC] `huggingface.co/api/models/facebook/musicgen-small` et `Xenova/musicgen-small`, champ `license`). Usage commercial interdit : **fonction à désactiver ou à remplacer** pour Nexora. Kokoro TTS est Apache-2.0 ([DOC] API Hugging Face). Parakeet est annoncé CC-BY-4.0 ([CODE] commentaire dans le source).
- **Stack** : React 19.2, TypeScript, Vite+, TanStack Router, Zustand 5, Tailwind 4, Radix, Zod 4, Mediabunny 1.54 pour la lecture/écriture ([CODE] `freecut/package.json`). Proche de Nexora (React 19, Tailwind, Radix/shadcn) mais **pas Next.js** : il faudra l'intégrer comme sous-application ou le porter.
- **Architecture** ([CODE] README + arborescence) : couches `features/` (UI), `runtime/` (horloge, lecteur, moteur de composition), `infrastructure/` (GPU, audio, stockage), `shared/` ; contrôles d'architecture automatisés (`scripts/check-feature-boundaries.mjs`).
- **Modèle de données** ([CODE] `freecut/src/types/project.ts`, `timeline.ts`) : `Project { id, schemaVersion, metadata (résolution/fps), timeline }` ; `ProjectTimeline { masterBusDb, tracks[], items[] }` ; chaque item porte `trackId`, `from`, `durationInFrames` (temps en **images**), `mediaId`, `originId`, `linkedGroupId`, `sourceStart/sourceEnd/sourceFps`, types `video|audio|text|image|shape|composition|adjustment|controller`. Séquences multiples et clips composés ; keyframes, transitions et effets sont des structures séparées. Migrations de schéma versionnées (`CURRENT_SCHEMA_VERSION`). Export/import de projet en ZIP validé par Zod (`src/features/project-bundle/schemas`).
- **API d'extension** : un jeu d'opérations d'édition headless (`src/headless/edit-ops.ts` : « 111-branch » remplacé par une table de dispatch ; ajouter/déplacer/couper/transitions/keyframes/effets) qui appelle les vraies actions du store. C'est exactement l'interface dont un agent IA ou un module de régénération a besoin.
- **Rendu navigateur** : WebCodecs + WebGPU, workers, OPFS ([DOC] README). Chrome/Edge 113+ requis.
- **Rendu serveur** ([CODE] `freecut/headless/`) : `Dockerfile` (Chrome stable pour H.264/AAC, Mesa lavapipe), `serve.mjs` (service HTTP : `GET /health`, `/v1/status`, `/v1/capabilities`, `POST /v1/projects`, `/v1/media/import`, `/v1/render`, `/v1/checkpoint-operations`, `/edit`, `/frame`, `/layout`), `render.mjs` (CLI, mode batch), un seul Chrome « chaud » par service avec requêtes **sérialisées**. Il pilote le **même moteur de rendu** que l'éditeur (fidélité WYSIWYG). Tests de contrat et d'idempotence (`idempotency.test.mjs`, `operation-queue.test.mjs`, `lifecycle-store.test.mjs`), oracle de pixels déterministe (`frame-oracle.mjs`).
- **Limite majeure serveur** : les projets avec effets GPU sont **refusés sur adaptateur WebGPU logiciel** car ils peuvent produire des images vides ou corrompues ([CODE] commentaire du Dockerfile). Il faut des nœuds avec **GPU réel** (Linux + Vulkan). Le déterminisme « à l'octet » entre GPU n'est pas démontré (oracle présent, non exécuté ici).
- **Export** ([CODE] `src/types/export.ts`, `runtime/renderer/client-renderer.ts`) : H.264/H.265/VP8/VP9/AV1, conteneurs MP4/WebM/MOV/MKV, audio MP3/AAC/WAV, sous-titres (incrustés, fichier séparé, piste souple MKV/WebM). Le type propose `prores` avec profils (`proxy`…`4444-xq`) **mais le moteur client le remplace par H.264** (`prores: 'avc', // ProRes not supported client-side`). ProRes est en **import** seulement (`@mediabunny/prores`, décodeur). Aucune prise en charge HDR trouvée dans le code (recherche `hdr|bt2020|hlg` sans résultat utile).
- **Proxys et reprise** : génération de proxys, vignettes, formes d'onde, relink de médias ([DOC] README), projets en fichiers simples avec corbeille/restauration. Persistance par **File System Access API / OPFS** : en SaaS, il faut remplacer cette couche par une API serveur (le service headless fournit déjà un modèle d'espace de travail disque côté serveur).
- **Tests** : 711 fichiers de test ([CODE], non exécutés). Porte de qualité `npm run verify` documentée ([DOC] README). Les effets GPU réels sont explicitement hors CI (porte « opérateur »).
- **Activité/maintenance** : créé le 2025-11-16 ; dernier commit 2026-10-29 ; ~2722 des commits viennent d'un seul auteur ([DOC] API contributeurs). Branches `develop`/`staging`/`main`. CLAUDE.md et DESIGN.md présents (développement assisté par agent).
- **Risques** : (1) facteur camion (un mainteneur) ; (2) dépendance à Chromium récent + WebGPU + GPU serveur ; (3) pas d'export pro (ProRes/DNxHR/HDR) ; (4) intégration dans Next.js ; (5) modèles IA locaux aux licences hétérogènes ; (6) `onnxruntime-web` épinglé sur une version « dev » ([CODE] CLAUDE.md).
- **Verdict** : meilleur compromis NLE complet + rendu serveur existant + licence MIT. À forker et posséder.

### 3.2 Mediabunny — verdict : brique d'I/O et de conversion

- **URL** : https://github.com/Vanilagy/mediabunny — clone `mediabunny/`. Version 1.65.0, publiée le 2026-10-30 ([DOC] registre npm).
- **Licence** : MPL-2.0 ([CODE] `mediabunny/LICENSE`, tous les `packages/*/package.json`). Copyleft **par fichier** : on peut l'utiliser comme dépendance dans un produit fermé ; les modifications des fichiers MPL eux-mêmes doivent être republiées. Les paquets d'encodeurs (`aac-encoder`, `ac3`, `mp3-encoder`…) embarquent des licences FFmpeg LGPL-2.1 dans `licenses/ffmpeg/` ([CODE]) : conformité LGPL à vérifier pour ces binaires WASM.
- **Architecture** : TypeScript pur, zéro dépendance, lecture/écriture MP4/MOV/WebM/MKV/HLS/MPEG-TS/WAV/MP3/Ogg/FLAC, WebCodecs, streaming ([DOC] README).
- **Serveur** : `@mediabunny/server` (MPL-2.0) s'appuie sur `node-av` 6.x (MIT, liaisons FFmpeg, `seydx/node-av`) : encodeurs/décodeurs AVC, HEVC, VP8/9, AV1, **ProRes** (y compris transparence), accélération matérielle ([CODE] `packages/server/README.md`). Réserve : la licence des binaires FFmpeg livrés par `node-av` n'est pas précisée dans son README (« FFmpeg itself is licensed under LGPL/GPL » — [CODE] `node-av/README.md`) : **à vérifier avant redistribution** ; en SaaS sans redistribution, risque faible.
- **HDR** : seulement la détection (`videoTrack.hasHighDynamicRange()`, [CODE] `docs/guide/reading-media-files.md`).
- **Tests** : 64 fichiers de test ([CODE]). Très actif (47 contributeurs, mais un auteur domine). Parrainé par Remotion, Diffusion Studio, etc. ([DOC] README).
- **Verdict** : à adopter comme couche média commune navigateur/serveur ; FreeCut et OpenReel l'utilisent déjà.

### 3.3 OpenTimelineIO (OTIO) — verdict : format d'échange, pas format de stockage

- **URL** : https://github.com/AcademySoftwareFoundation/OpenTimelineIO — clone `opentimelineio/`. Apache-2.0 ([CODE] `LICENSE.txt`), projet ASWF, tag stable v0.18.x (dépôt `main` en 0.19 dev, [CODE] `OTIO_VERSION.json`).
- **Modèle** : `Timeline > Stack > Track > (Clip | Gap | Transition)`, `RationalTime`/`TimeRange` exacts, références média externes, métadonnées libres (`metadata`) ([CODE] `docs/tutorials/otio-timeline-structure.md`, `otio-file-format-specification.md`).
- **Adaptateurs** ([CODE] `docs/tutorials/adapters.md`) : otio_json/otiod/otioz natifs ; paquet `OpenTimelineIO-Plugins` : AAF, ALE, CMX 3600 (EDL), FCP7 XML (`fcp_xml`), XGES (GStreamer)… ; FCPXML (FCP X) en adaptateur à part (`otio-fcpx-xml-adapter`, dernier commit 2024).
- **Limite décisive** ([CODE] `docs/tutorials/feature-matrix.rst`) : **aucun effet audio/vidéo** n'est porté (case ✖ partout sauf XGES), vitesses « fancy » non supportées, transitions absentes de FCP7/FCPX. OTIO dit explicitement que l'effet est « application specific ». Il ne peut donc pas être le format natif d'un éditeur avec keyframes, masques, LUT, blend modes.
- **JS** : pas de binding officiel. Un paquet non officiel `opentimelineio` 0.1.0 (Apache-2.0, 2025-10, `fifteen42/otio.js`) existe — immature. Comme `.otio` est du JSON simple, écrire un exporteur TS minimal est réaliste.
- **Verdict** : pivot d'**interchange** (import/export EDL, FCP XML, AAF, remise à un monteur externe), avec les données Nexora dans `metadata.nexora`.

### 3.4 FFmpeg — verdict : moteur de livraison pro (licences à cadrer)

- **Licence** ([CODE] `ffmpeg/LICENSE.md` ; [DOC] https://ffmpeg.org/legal.html) : LGPL-2.1+ par défaut ; `--enable-gpl` fait passer l'ensemble en GPL ; conformité LGPL = édition de liens dynamique, fourniture des sources exactes et de la configuration, mentions.
- **Bibliothèques GPL dans `configure`** ([CODE] liste `EXTERNAL_LIBRARY_GPL_LIST`) : `libx264`, `libx265`, `librubberband`, `libvidstab`, `frei0r`, `libxvid`. **Hors GPL** : encodeurs natifs `prores_ks` (profils jusqu'à 4444 XQ, formats 10 bits 4:2:2/4:4:4/4:4:4:4 avec alpha — [CODE] `libavcodec/proresenc_kostya.c`, `CODEC_PIXFMTS(YUV422P10, YUV444P10, YUVA444P10)`) et `dnxhd` avec profils **DNxHR** `lb/sq/hq/hqx/444` ([CODE] `libavcodec/dnxhdenc.c`), AV1 via `libsvtav1`/`libaom`/`librav1e` (bibliothèques externes).
- **Version** : branche `main` = 8.0.git, libavcodec majeur 63 ([CODE] `RELEASE`, `libavcodec/version_major.h`).
- **Implications SaaS** : GPL/LGPL ne se déclenchent pas par l'usage en réseau (ce n'est pas l'AGPL) ; elles se déclenchent par **distribution** (image Docker livrée à un client, application de bureau). Brevets H.264/H.265 : la page légale FFmpeg rappelle que les droits de brevets ne sont pas couverts et peuvent donner lieu à des redevances en usage commercial ([DOC] ffmpeg.org/legal.html). Recommandation : encodeurs matériels (NVENC) ou SVT-AV1/ProRes/DNxHR pour rester en build LGPL ; sinon accepter x264/x265 côté serveur interne **avec validation juridique**.

### 3.5 OpenReel Video — verdict : référence sérieuse, plan B

- **URL** : https://github.com/Augani/openreel-video — MIT, créé le 2026-01-19, 5520 étoiles, ~7 contributeurs ([DOC] API).
- **Stack** : React, TypeScript, Zustand, MediaBunny, WebCodecs, WebGPU, Three.js ; monorepo `apps/{web,desktop,studio,cloud,image}` et `packages/{core,agent,agent-runner,creation-*,fxpkg,ui}` ([CODE]).
- **Export** ([DOC] README) : navigateur = H.264/WebM/jusqu'à 4K ; **ProRes et alpha uniquement dans l'application de bureau** (FFmpeg natif). Le bureau embarque des binaires FFmpeg **GPL** ([CODE] `apps/desktop/DISTRIBUTION.md` : « these are GPL builds (x264/x265) » appelés comme processus séparé) — la redistribution impose les obligations GPL.
- **Serveur** : `apps/cloud` est un Worker Cloudflare de stockage de modèles, pas un moteur de rendu. Pas de service de rendu web.
- **Tests** : 478 fichiers de test ([CODE]). Beaucoup de documents de revue internes générés (`apps/web/docs/…2026-10-1x.md`) : signe de développement assisté par agent.
- **Verdict** : bon second choix d'éditeur (moteur `packages/core` découplé), mais sans rendu serveur.

### 3.6 Remotion — verdict : moteur serveur mature mais payant, à ne pas coupler au cœur

- **URL** : https://github.com/remotion-dev/remotion — clone `remotion/`. 69 k étoiles, v4.0.539 du 2026-10-26 ([DOC] npm), activité quotidienne.
- **Licence** ([CODE] `remotion/LICENSE.md` ; [DOC] https://www.remotion.pro/license) : gratuit pour particuliers, **entreprises à but lucratif jusqu'à 3 personnes**, associations, évaluation. Au-delà : **licence entreprise obligatoire**. Tarifs lus : « Automators » 0,01 $ par rendu avec minimum 100 $/mois (couvre explicitement les éditeurs vidéo, applications prompt-to-video et l'usage du Player intégré) ; « Creators » 25 $/siège/mois ; Enterprise à partir de 500 $/mois. Interdit de revendre/sous-licencier un dérivé. LICENSE.md annonce un changement de licence pour **Remotion 5.0** (PR #3750) : risque de dérive à suivre.
- **Conséquence** : un SaaS Nexora de plus de 3 personnes qui intègre Remotion paierait un coût par rendu, croissant avec le volume. Les paquets `@remotion/webcodecs` / `media-parser` sont sous la même licence et annoncent un futur siège « WebCodecs Conversion Seat » ([CODE] `docs/docs/webcodecs/LicenseDisclaimer.tsx`).
- **Rendu** : Node + Chrome headless, capture image par image ; AWS Lambda, Cloud Run, Vercel Sandbox, GitHub Actions ([CODE] `docs/docs/ssr.mdx`). **ProRes** supporté (`--codec=prores`, `.mov`, [CODE] `docs/docs/prores.mdx`). **HDR non supporté** : « headless Chrome … does not support HDR. Frames are always rendered in sRGB » ([CODE] `docs/docs/hdr.mdx`).
- **FFmpeg fourni** : binaire compilé **GPLv2+** (x264/x265) avec sources publiées ([CODE] `docs/docs/miscellaneous/ffmpeg-license.mdx`).
- **Modèle de projet** : il n'y en a pas — la composition est du **code React** ; l'« Editor Starter » est réservé à l'offre Enterprise ([DOC] remotion.pro). Pas adapté à une timeline utilisateur persistée sans surcouche.
- **Tests** : ~1160 fichiers de test dans `packages/` ([CODE]).
- **Verdict** : excellent pour des gabarits de motion design paramétrés, mais le coût de licence, la sérialisation en code et l'absence de HDR en font un mauvais cœur pour un NLE. À réserver, éventuellement, à des « templates de titres » rendus côté serveur.

### 3.7 Aftertake — verdict : référence de conception pour la régénération de plans

- **URL** : https://github.com/ItsSNOWMOBILE/aftertake — clone `aftertake/` (branche `aftertake-studio`). Créé le 2026-10-17, **2 étoiles**, ~3000 fichiers, 84 fichiers de test ([DOC] API, [CODE]).
- **Nature** : studio IA **local** (ComfyUI + Comfy SDK, modèles à poids ouverts : LTX-2.5, Z-Image, Wan Animate 2, SAM3, SeedVR2, RIFE, ACE-Step, Kokoro) avec un éditeur « Film » et un serveur MCP de 55 outils ([DOC] README). Inspiré explicitement des « skills » publics de Higgsfield (`higgsfield-ai/skills`, MIT) pour 18 recettes de départ.
- **Licence** : code MIT ([CODE] `LICENSE`). **Modèles : licences propres** (LTX = licence « LTX », SAM3/MiniMax H3 « see model cards ») ([DOC] README) : à auditer individuellement pour un usage commercial.
- **Ce qu'il enseigne pour la régénération sans casser le montage** ([CODE] `src/film.ts`, `server/films.ts`, `server/take-sets.ts`) :
  - un plan du film référence soit `renderId` (une *prise* générée) soit `assetId` (média importé), plus une fenêtre de découpe `start/end` ; titres, graphiques, audio sont des entités séparées ;
  - les prises vivent dans des **ensembles de prises** (2 à 4 prises comparables, route `keep` pour garder la bonne) ;
  - les manifestes exportés (`aftertake-film/1` à `/5`) retrouvent leurs prises par **empreinte SHA-256** et gardent les **recettes** pour régénérer si le fichier manque (`server/films.ts`, message « Its recipes are included for regeneration ») ;
  - `filmRenderRevision = 12` identifie la version du moteur de rendu dans l'identité d'export ; clés de requête et digests pour **rejouer/reprendre** les jobs sans doublon ;
  - le rendu final de « Film » est assemblé sur **CPU** par PyAV/FFmpeg (`scripts/assemble-film.py`, encodage libx264).
- **Limites pour Nexora** : monolithe mono-utilisateur local (Express + Python), pas un composant intégrable ; modèle de montage volontairement simple (suite de plans, pas de multipiste libre) ; export H.264 uniquement ; projet très jeune, un seul mainteneur.
- **Verdict** : à lire et imiter (take-sets, empreintes, recettes, révision du moteur), pas à intégrer.

### 3.8 OpenCut — verdict : stack proche de Nexora, mais deux versions et aucune livrable serveur

- **URLs** : https://github.com/OpenCut-app/OpenCut (96,8 k étoiles) et https://github.com/opencut-app/opencut-classic (clones `opencut/`, `opencut-classic/`). MIT.
- **État** ([CODE] `opencut/README.md`) : « OpenCut is being rewritten from the ground up » ; `main` annonce API d'éditeur, plugins, cœur Rust, serveur MCP, **mode headless** — le dépôt compte ~8,5 k lignes (UI et `crates/media`), pas de moteur fonctionnel. La version « classic » est « the one to reach for today ».
- **Classic** : Next.js 16, React 19, Zustand 5, Mediabunny, **moteur Rust compilé en WASM** (`rust/crates/{compositor,effects,gpu,masks,time}`), Better Auth + Drizzle ; modèle `TProject { scenes[], settings{fps,canvasSize,background}, version }` ([CODE] `apps/web/src/project/types.ts`). 30 fichiers de test. Dernier commit 2026-05-17 (figé).
- **Verdict** : intéressant car même stack que le portail (Next 16/React 19), mais la base utilisable est gelée, la nouvelle est un squelette, et il n'y a pas de rendu serveur. Surveiller la réécriture ; ne pas bâtir dessus aujourd'hui.

### 3.9 Revideo / Motion Canvas — verdict : motion graphics par code, pas un NLE

- **Revideo** : https://github.com/midrender/revideo, MIT, v0.11.0 du 2026-07-10 ([DOC] npm). « Moteur derrière Midrender » ; scène = fonction générateur TypeScript ([CODE] README). Rendu serveur : Puppeteer + `fluent-ffmpeg` + `@ffmpeg-installer/ffmpeg` ([CODE] `packages/renderer/package.json`, `packages/ffmpeg/package.json`) ; télémétrie activée par défaut (`DISABLE_TELEMETRY=true` pour la couper). 28 fichiers de test. À vérifier : licence des binaires FFmpeg installés par `@ffmpeg-installer/ffmpeg`.
- **Motion Canvas** : MIT, 19,6 k étoiles, dernier push 2026-07-02 ; animations vectorielles par code avec éditeur d'aperçu ; Revideo en est un fork.
- **Verdict** : bons pour des gabarits animés (titres, infographies) rendus côté serveur ; ne résolvent ni la timeline utilisateur ni la persistance.

### 3.10 Diffusion Studio Core — verdict : à éviter

- Le dépôt `diffusionstudio/core` ne contient **que** `docs/` et `playground/` ([CODE] `git ls-files`) ; le paquet npm 4.0.3 (2025-11-30, déclaré MPL-2.0) livre `dist/core.es.js` compilé (479 ko) ([DOC] `unpkg.com/@diffusionstudio/core@4.0.3/?meta`). Le README indique que le moteur est gratuit **avec filigrane « Made with Diffusion Studio »** obligatoire, retirable par achat de clé de licence vérifiée localement ([CODE] README). Une étiquette MPL-2.0 sans source publiée est incohérente : risque juridique et de maintenance. Dernier commit 2025-11-18.
- Construit sur Mediabunny (qui est, lui, ouvert) : autant utiliser Mediabunny directement.

### 3.11 Twick, Shotstack Studio SDK, OpenVideo, Rendley, Etro — éliminés ou très risqués

- **Twick** (`ncounterspecialist/twick`, 544 étoiles) : licence « Sustainable Use License v1.0 » interdisant de **fournir le logiciel ou ses fonctions backend comme service hébergé/SaaS sans accord commercial** ([CODE] `twick/LICENSE.md`). Rendu serveur sur un fork Motion Canvas/Revideo (`@twick/2d`, `@twick/ffmpeg`). Dernier commit 2026-05-07, 5 fichiers de test. **Bloquant.**
- **Shotstack Studio SDK** : PolyForm Shield 1.0.0 ([CODE] `shotstack-studio-sdk/LICENSE`) — interdit de proposer un produit **concurrent** de Shotstack (plateforme d'édition vidéo cloud, API, Studio, SDK, templates). Un studio créatif avec éditeur vidéo risque d'être jugé concurrent. Le rendu final passe par l'API payante Shotstack. Intéressant uniquement comme référence de schéma JSON (un asset peut porter un `prompt` de génération — [CODE] `readme.md`).
- **OpenVideo / react-video-editor** (`openvideodev`) : « OpenVideo License » calquée sur Remotion (≤3 salariés gratuit, sinon licence payante, [CODE] `react-video-editor/LICENSE`) ; incohérence : `@openvideo/core` est déclaré MIT sur npm ([DOC]). Next.js + Pixi, client uniquement. Moins attractif que FreeCut.
- **Rendley SDK** : propriétaire, source fermée, rendu sur l'appareil ; tarifs publiés Free 0 $, Pro 150 $/mois, Enterprise sur devis ([DOC] https://rendley.com/products/sdk — la grille extraite ne précise pas clairement quelle offre accorde la licence commerciale, à clarifier). Paquet npm 1.16.3 du 2026-10-29. Dépendance à un fournisseur, pas de rendu serveur : non retenu.
- **Etro** : GPL-3.0 ([CODE] `etro/LICENSE`). Livrer du JS GPL aux navigateurs des clients constitue une distribution : contamination du code client de Nexora. Rendu hors ligne « bientôt » seulement. **Éliminé.**

### 3.12 Autres : Editly, omniclip, Timeline Studio, MLT, GES, KubeezCut, Concat

- **Editly** (MIT, 5574 étoiles) : JSON5 déclaratif → FFmpeg + headless-gl + canvas/Fabric, transitions GLSL ([CODE] README, `package.json`). Version 0.15.0-rc.1, dernier commit 2025-02-20 : peu maintenu. Bon modèle pour compiler un sous-ensemble de timeline vers FFmpeg, pas une dépendance sûre.
- **omniclip** (MIT, 1468 étoiles) : composants Lit, WebCodecs, FFmpeg.wasm ; pas de service serveur ; 2 fichiers de test ; annonce « Omniclip 2.0 » ; dernier commit sur `main` 2025-08-07 (l'API GitHub signale un push plus récent sur une autre branche). Le paquet npm `omniclip` 1.0.7 (2024) est en ISC. Trop limité.
- **Timeline Studio / ai-video-editor** (MIT, créé 2026-07-09) : timeline `.timeline` comme « source de vérité », exécuteur d'opérations headless transactionnel et idempotent, rendu « hors ligne déterministe » distinct de l'aperçu ([CODE] README). **Attention** : `MODEL_LICENSES.md` précise que les poids d'échange de visage (MobileFaceSwap, ArcFace, SCRFD) sont traités comme modèles de recherche, **sans droit commercial**. Utile comme inspiration d'API pour agents, pas comme base.
- **MLT** : framework LGPL-2.1 ([CODE] `mlt/COPYING`, README) avec format de projet **XML MLT** et `melt` en ligne de commande ; modules en GPL (`src/modules/plusgpl`, `qt`, `rubberband`…) à exclure d'un build LGPL. Moteur de montage serveur crédible (c'est le moteur de Shotcut et Kdenlive), mais pas de GPU navigateur ni de lien avec l'éditeur web ; maintenance active (2026-10-29, tag v7.42).
- **GStreamer Editing Services (GES)** : LGPL-2.1 ([CODE] `gstreamer/subprojects/gst-editing-services/COPYING`), timeline > couches > pistes, outil `ges-launch`, format XGES (adaptateur OTIO disponible). Plus lourd à opérer que FFmpeg pour un gain faible ici.
- **KubeezCut** : fork MIT de FreeCut avec idées d'OpenCut et intégration de l'API Kubeez (génération) ([CODE] `kubeezcut/README.md`), 38 étoiles, dernier commit 2026-08-06. Utile pour voir comment brancher une génération IA dans FreeCut, pas comme base.
- **Concat** : AGPL-3.0, créé 2026-08-25, 12,9 k étoiles ([DOC] API GitHub) — l'AGPL impose la publication du code source des services réseau dérivés : à exclure d'un SaaS fermé. Non cloné.
- **Theatre.js** (Apache-2.0, dernier commit 2024), **Pixi.js** (MIT, 8.22 le 2026-10-01), **Lottie web** (MIT) et `dotlottie-web` (MIT) : briques de rendu/animation sans risque de licence ([DOC] registre npm). FreeCut intègre déjà dotLottie.

---

## 4. Thèmes transversaux

### 4.1 Formats de projet et d'échange

| Format | Rôle | Effets / keyframes | Remarque |
|---|---|---|---|
| **JSON natif Nexora** (recommandé) | Stockage, reprise sans perte, opérations | Oui (complet) | Versionné, validé par Zod, migrations |
| **OTIO** | Échange avec monteurs, conformation | Non (métadonnées libres seulement) | Adaptateurs EDL, AAF, FCP7 XML, XGES |
| **EDL CMX 3600** | Remise de coupes | Non | Piste vidéo unique, pas de multipiste ([DOC] feature-matrix OTIO) |
| **FCPXML / FCP7 XML** | Échange NLE | Non (pas de transitions via l'adaptateur) | Adaptateur FCPX peu maintenu (2024) |
| **XML MLT** | Rendu serveur MLT | Oui (filtres MLT) | Lié à MLT |
| **XGES** | Rendu serveur GES | Oui | Lié à GStreamer |

### 4.2 Export professionnel — ce qui existe réellement

| Besoin | Navigateur (WebCodecs) | FreeCut headless | Mediabunny server | Remotion | FFmpeg |
|---|---|---|---|---|---|
| H.264 / H.265 / VP9 / AV1 | Selon encodeur du navigateur | Oui | Oui | Oui | Oui |
| ProRes (encodage) | Non | Non (repli H.264) | Oui | Oui | Oui (`prores_ks`, LGPL) |
| DNxHR | Non | Non | Non trouvé | Non trouvé | Oui (`dnxhd`) |
| 10 bits / HDR | Non démontré (la littérature trouvée ne confirme pas les profils HDR de `VideoEncoder`) | Non | Non (détection seulement) | **Non** (sRGB) | Oui (métadonnées/formats 10 bits) |
| Mixage audio multipiste, égaliseur, fondus | Oui (FreeCut : EQ, bus maître) | Oui | Bas niveau | Oui | Oui (filtres) |
| Sous-titres (incrusté, SRT, piste souple) | Oui (FreeCut) | Oui | Pistes de sous-titres | Oui | Oui |
| Normalisation sonore (loudness) | À vérifier | À vérifier | Non | À vérifier | Oui (`loudnorm`, filtre standard) |

Constat net : **aucun candidat ne livre HDR ni DNxHR clé en main.** Chrome expose un mode de canevas HDR WebGPU (`toneMapping: extended`, Chrome 129 — [DOC] developer.chrome.com/blog/new-in-webgpu-129) mais cela concerne l'affichage ; l'encodage HDR via WebCodecs reste non confirmé dans mes sources. La chaîne HDR/10 bits devra être construite côté serveur avec FFmpeg depuis des sources 10 bits, sans passer par une capture de canevas 8 bits.

### 4.3 Rendu serveur déterministe

Trois familles :
1. **Même moteur que l'éditeur dans un Chrome sans interface** (FreeCut `headless/`, Remotion) : fidélité parfaite avec l'aperçu, mais dépend du GPU, de la version de Chrome et de pilotes ; le déterminisme au pixel doit se prouver par un oracle de test.
2. **Compilation du projet vers FFmpeg / MLT / GES** (Editly, MLT XML, XGES) : déterministe, sur CPU, mise à l'échelle simple, mais il faut maintenir un second moteur de rendu avec des écarts d'apparence.
3. **Rendu navigateur sur l'appareil du client** (Rendley, OpenCut, OpenReel web) : pas de coût serveur, mais pas de lot, pas de reprise, pas d'export pro.

Aucun des trois ne se suffit à lui-même pour « export pro + fidélité » : voir recommandation.

### 4.4 Proxys

FreeCut génère des proxys, vignettes, formes d'onde et gère le relink ([DOC] README). Pour Nexora : proxys 540p/720p H.264 intra-friendly produits à l'ingestion par un worker FFmpeg, nommés par empreinte SHA-256 du média source pour être régénérables.

### 4.5 Timeline multipiste avec clips générés par IA — re-génération sans casser le montage

Éléments de conception issus du code lu (FreeCut `mediaId/originId/sourceStart/sourceEnd`, Aftertake `renderId/assetId` + empreinte + recette, Shotstack asset avec `prompt`) :

- séparer le **plan** (identifiant stable, position, effets, keyframes, transitions) de la **prise** (version générée d'un média, avec recette = prompt, modèle, version du modèle, graine, entrées, empreinte du fichier) ;
- le plan pointe vers une **prise active** ; remplacer la prise ne change ni la position ni les effets ;
- règle de **conformation** à définir et à tester : conserver la durée sur la timeline ; recaler le point d'entrée en temps source ; si la nouvelle prise est plus courte, signaler et proposer figer/boucler/ripple ; si fps ou ratio différent, recalcul des `sourceStart/sourceEnd` en secondes rationnelles ;
- **verrouillage** (« prise épinglée ») pour qu'aucune régénération automatique n'écrase une prise validée ;
- journal d'opérations (`checkpoint-operations` de FreeCut, clés d'idempotence, ledger) pour reprise sans doublon après plantage ;
- manifeste d'export listant prises, empreintes et **révision du moteur de rendu** (idée `filmRenderRevision` d'Aftertake).

---

## 5. Recommandation d'architecture

### 5.1 Composant à intégrer

**Éditeur : fork de FreeCut** (MIT), monté dans le portail en sous-application d'abord (iframe/route dédiée avec isolation COOP/COEP nécessaire au WASM multithread), puis porté en composant client-only de Next.js 16 une fois l'API stabilisée. Raisons : seul candidat avec NLE multipiste complet, rendu serveur déjà conçu, API d'opérations headless, tests nombreux, pile (React 19, Tailwind, Radix) proche de Nexora, licence MIT.

À faire dans le fork, par ordre :
1. remplacer la persistance File System Access/OPFS par une couche `ProjectRepository` (API + Postgres JSONB + stockage objet) ;
2. désactiver MusicGen (CC-BY-NC) et auditer chaque modèle IA embarqué avant publication ;
3. introduire la notion de **slot/prise** (section 4.5) au-dessus de `mediaId` ;
4. aligner l'UI sur les tokens du portail (le fork utilise déjà shadcn/Radix/Tailwind).

**Couche média commune : Mediabunny** (navigateur + `@mediabunny/server`), à épingler (FreeCut est épinglé en 1.54 alors que la dernière est 1.65).

### 5.2 Format de projet pivot

- **Stockage natif** : JSON « Nexora Timeline » versionné (`schemaVersion`, migrations, validation Zod), dérivé du modèle FreeCut : temps en images + fps du projet, références de médias par `slotId` → `takeId` → empreinte SHA-256. Révisions numérotées (concurrence optimiste) et journal d'opérations.
- **Échange** : export/import **OTIO** (pistes, plans, trous, marqueurs, transitions, vitesse linéaire) pour EDL/AAF/FCP XML, avec le reste dans `metadata.nexora`. Exporteur TS minimal côté Node, adaptateurs Python OTIO en microservice pour AAF/EDL.
- Ne pas faire d'OTIO le format natif (pas d'effets) ni de XML MLT/XGES (couplage à un moteur).

### 5.3 Rendu serveur (deux niveaux)

1. **Rendu « fidèle »** : service dérivé de FreeCut `headless/serve.mjs` (Chrome + Playwright en conteneur), **sur nœuds GPU réels** ; files de jobs externes (une instance = une opération à la fois, comme le service d'origine), clés d'idempotence, stockage des sorties. Sert aux aperçus serveur, partages, MP4/WebM/AV1 de diffusion.
2. **Masters professionnels** : worker FFmpeg (build LGPL : `prores_ks`, `dnxhd`, SVT-AV1/NVENC) alimenté soit par des images/pistes intermédiaires haute qualité issues du niveau 1, soit — pour le sous-ensemble coupes/fondus/vitesse/mixage — par une **compilation directe de la timeline vers un graphe FFmpeg** (modèle Editly). HDR/10 bits : à traiter uniquement par ce chemin à partir de sources 10 bits ; décision produit à prendre sur ce que l'on promet (voir PoC).
3. **Pas de Remotion dans le chemin critique** (coût par rendu, HDR absent, licence évolutive). Possible plus tard pour des gabarits de titres.

### 5.4 Licences : checklist à valider avec un juriste

- Écarter : Etro (GPL), Twick (SaaS interdit), Shotstack SDK (non-concurrence), Concat (AGPL), Diffusion Studio (source absente, filigrane).
- Remotion/OpenVideo : payant au-delà de 3 personnes.
- FFmpeg : build LGPL pour toute image redistribuée ; x264/x265 uniquement côté serveur interne et après avis juridique (brevets H.264/H.265 non couverts par les licences de copyright).
- Modèles IA : audit un par un (MusicGen CC-BY-NC bloquant ; échange de visage de Timeline Studio non commercial ; licences LTX/SAM3/H3 d'Aftertake à lire).
- MPL-2.0 (Mediabunny) : republier uniquement les fichiers MPL modifiés.

---

## 6. Risques majeurs

1. **Dépendance à un mainteneur** (FreeCut, 98 % des commits d'un auteur, projet de 11 mois) : mitigation = fork interne, épinglage, couche d'adaptation, budget de maintenance.
2. **GPU serveur** requis pour les effets WebGPU ; coût et capacité à dimensionner ; pas d'équivalence CPU.
3. **Déterminisme** non démontré entre GPU/pilotes/versions de Chrome.
4. **HDR/DNxHR/10 bits** : à construire (non fournis).
5. **Licences de modèles** et de binaires FFmpeg.
6. **Écart Next.js ↔ Vite/TanStack Router** pour l'intégration.
7. **Projets très jeunes** (Aftertake 13 jours, OpenReel 9 mois, FreeCut 11 mois) : API instables.

---

## 7. Backlog de PoC à exécuter plus tard (aucun n'a été fait dans cette étude)

Ces points transformeront les [CODE]/[DOC] en [TEST] :
1. Construire l'image Docker de `freecut/headless` sur un nœud GPU Linux, rendre un projet témoin 3 fois, comparer les hashes d'images (oracle `frame-oracle.mjs`), mesurer temps et mémoire pour 1080p/4K.
2. Compiler FFmpeg en LGPL (`prores_ks`, `dnxhd`, SVT-AV1), encoder un master ProRes 422 HQ et un DNxHR HQX à partir d'une source 10 bits, valider les métadonnées colorimétriques avec `ffprobe`.
3. Prototype de remplacement de prise : projet FreeCut avec 5 plans, remplacer une prise par une plus courte/plus longue/fps différent, vérifier que effets, keyframes et transitions restent intacts.
4. Aller-retour OTIO ↔ JSON Nexora : mesurer ce qui est perdu (effets, keyframes) et formaliser `metadata.nexora`.
5. Vérifier la licence réelle des binaires FFmpeg livrés par `node-av` et `@ffmpeg-installer/ffmpeg`.
6. Tester `VideoEncoder.isConfigSupported()` pour HEVC Main10 / AV1 10 bits avec espace colorimétrique BT.2020 PQ/HLG dans Chrome stable.
7. Charge : 10 rendus concurrents sur un nœud, comportement de la file sérialisée.

---

## 8. Sources principales

- FreeCut : https://github.com/walterlow/freecut (README, `headless/`, `src/types/*.ts`)
- Aftertake : https://github.com/ItsSNOWMOBILE/aftertake (README, `src/film.ts`, `server/films.ts`, `server/take-sets.ts`)
- Mediabunny : https://github.com/Vanilagy/mediabunny (+ `packages/server`, `packages/prores`)
- Remotion : https://github.com/remotion-dev/remotion ; https://www.remotion.pro/license ; `packages/docs/docs/{prores,hdr,ssr}.mdx`, `docs/miscellaneous/ffmpeg-license.mdx`
- Revideo : https://github.com/midrender/revideo ; Motion Canvas : https://github.com/motion-canvas/motion-canvas
- OpenCut : https://github.com/OpenCut-app/OpenCut ; https://github.com/opencut-app/opencut-classic
- OpenReel : https://github.com/Augani/openreel-video
- Diffusion Studio : https://github.com/diffusionstudio/core ; https://unpkg.com/@diffusionstudio/core@4.0.3/?meta
- Twick : https://github.com/ncounterspecialist/twick ; Shotstack Studio SDK : https://github.com/shotstack/shotstack-studio-sdk
- Rendley : https://rendley.com/products/sdk ; https://unpkg.com/@rendley/sdk@1.16.3/LICENSE
- OpenTimelineIO : https://github.com/AcademySoftwareFoundation/OpenTimelineIO
- FFmpeg : https://ffmpeg.org/legal.html ; https://github.com/FFmpeg/FFmpeg
- MLT : https://github.com/mltframework/mlt ; GES : https://gitlab.freedesktop.org/gstreamer/gstreamer (subprojects/gst-editing-services)
- node-av : https://github.com/seydx/node-av
- HDR canevas WebGPU : https://developer.chrome.com/blog/new-in-webgpu-129
- Modèles : https://huggingface.co/facebook/musicgen-small (CC-BY-NC-4.0), https://huggingface.co/onnx-community/Kokoro-82M-v1.0-ONNX (Apache-2.0)
- Registre npm (métadonnées de version et licence) : https://registry.npmjs.org/
