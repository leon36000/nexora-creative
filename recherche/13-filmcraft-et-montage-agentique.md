# 13 — FilmCraft et le montage agentique : quelle base, quels composants, quels outils pour un LLM bon marché (02/11/2026)

Demande du fondateur : des capacités de montage **hors du commun**, obtenues par un **LLM moins cher** (aujourd'hui `z-ai/glm-5.3` via OpenRouter) qui monte avec H3, Qwen-Image et Music3 ; piste suggérée : <https://github.com/storytold/filmcraft>, « mégasimplifié et boosté par l'IA » ; consigne : ne négliger aucune piste.
Statut : **recherche** [PROPOSÉ]. Rien n'a été installé ni exécuté ; les dépôts ont été clonés en lecture seule puis supprimés.

**Niveaux de vérification** utilisés dans les tableaux : **C** = code lu (en-têtes de modules, schémas, listes d'opérations, scripts) ; **R** = README, documentation et métadonnées GitHub (licence, étoiles, dernier commit au 02/11/2026) ; **M** = métadonnées seules. Les licences sont seulement relevées, sans analyse.

## 1. Verdict en cinq lignes

1. **FilmCraft n'est pas une base pour nous : c'est une source d'idées et de spécifications.** C'est un éditeur non linéaire complet « façon Premiere » en **Rust pur** (≈ 440 000 lignes dans `crates/`, interface egui, codecs maison, sans FFmpeg), au stade « alpha » selon son propre `ROADMAP.md`. Notre pile est TypeScript/React/Fastify + Mediabunny + ffmpeg ; rien du code ne s'y branche sans une réécriture.
2. **Son « IA » n'est pas de la génération ni de la planification** : c'est une surface de commandes pilotable par un agent (serveur MCP `command_list` / `command_run` / `command_batch` / `render_frame`), plus une transcription Whisper à mots horodatés. L'éditeur n'invente rien tout seul.
3. **Ce qu'on prend de FilmCraft, ce sont des principes** (registre de commandes auto-descriptif, lot atomique = un seul pas d'annulation, temps en entiers, transcription par mots dont les temps sont ceux du média, retrait des pauses/mots parasites, lien OTIO/EDL) — nous en avons déjà une partie dans `mode-studio/src/features/nexora/`.
4. **Le vrai gisement est ailleurs** : **FableCut** (MIT, JS sans dépendance, conçu pour être piloté par un agent) fournit en modules autonomes presque tout ce qu'il faut côté « oreilles » (battues, silences, ducking, sonie BS.1770, recadrage 9:16 qui suit le sujet, suivi de zone, meilleurs moments, étalonnage, opérations de timeline), et **browser-use/video-use** (MIT) fournit le **contrat EDL, les règles dures de correction et la boucle d'auto-vérification** qu'un petit modèle doit subir.
5. **Notre avantage que personne n'a** : l'éditeur peut **commander des plans manquants** (H3/Qwen/Music3) au lieu de se limiter à couper ce qui existe — et nous avons déjà, dans `marketing/creative/video-v3/`, une chaîne qui a prouvé le schéma « musique d'abord → courbe d'énergie → coupes sur les coups → auto-revue ». La feuille de route (§7) consiste à **en faire un contrat typé, appelable par n'importe quel LLM**.

## 2. FilmCraft : ce qu'on a lu

Dépôt `storytold/filmcraft` (équipe ArtCraft), double licence **MIT OU Apache-2.0** (`LICENSE-MIT`, `LICENSE-APACHE`, `NOTICE` ; marques ArtCraft exclues). Dernier commit relevé : 02/11/2026 (clone superficiel, historique non évalué). Niveau **C** sur docs et crates, pas d'exécution.

| Sujet | Constat |
|---|---|
| Architecture | Espace de travail Cargo : `crates/` = `engine` (66 k lignes), `render` (25 k), `audio-dsp` (14 k), `interchange` (17 k), `project` (12 k), `export` (11 k), `captions` (5 k), `edit` (5 k), `speech` (2,6 k), `automation` (1,8 k), codecs (h264, hevc, av1, prores, aac, opus…) ; applis `filmcraft` (bureau), `filmcraft-cli` (CLI + MCP), `filmcraft-web` (WASM/WebGPU, canevas egui). |
| Modèle de données | Fichier `.fcproj` = JSON versionné (`schema_version` 17) : `project` {bins, médias, **séquences → pistes → clips**, effets, images-clés, marqueurs}, `view` à part (hors annulation). Médias référencés par chemin. **Temps en ticks entiers** (254 016 000 000 par seconde) ; les commandes acceptent aussi `seconds`, `frame`, `timecode`. Pas de notion native de « scène/plan narratif » : c'est un NLE, pas un outil de storyboard. |
| Ce qui est piloté par agent | `engine.execute` + registre `engine.commands` (avec état « activé/désactivé » selon la sélection) ; plus d'une centaine de commandes relevées : `timeline.place/trim/move/razor`, `sequence.setTransition/applyVideoTransition/extract/lift/closeGap/simplify/renderInToOut`, `clip.speedDuration/frameHold/sceneEditDetection/automateToSequence/synchronize/createMulticam`, `effects.setParam/addKeyframe`, `captions.add/export`, `transcript.generate/set/createCaptions/removePauses`, `mixer.*`, `markers.*`. Authentification par jeton, boucle locale uniquement, lots avec erreurs claires (`docs/agents.md`, `docs/control-protocol.md`). |
| IA réelle | Transcription Whisper (candle, CPU), diarisation, **édition par le texte** (retrait de pauses et de mots parasites), TTS (`crates/tts`), détection de coupes (`scene_detect.rs`). **Aucune génération, aucune planification, aucun juge.** |
| Rendu | Compositeur GPU wgpu en lumière linéaire, décodeurs/encodeurs maison, export MP4/MOV/WebM. Chemin entièrement distinct de ffmpeg et de Mediabunny. |
| Interchange | Crate `interchange` : CMX 3600, FCP7 XML, FCPXML, **OpenTimelineIO**, AAF/OMF, ALE — écrit « à partir des spécifications publiques ». |
| Audio | Crate `audio-dsp` sans dépendance, compilable en WASM : sonie BS.1770-4 / EBU R128, ducking, compresseurs, etc. |
| Maturité | Étiquette « alpha », ~19 points « prêt pour le vrai travail » selon eux ; `docs/gaps.md` liste des manques bloquants (ouverture de `.prproj`, mesures). Très jeune, très actif, largement écrit par agents. |

**Décision : inspiration + spécifications, aucun code repris.** Raisons : (a) langage et chaîne de rendu incompatibles (Rust/egui/WebGPU contre React/DOM/WebCodecs) ; (b) 440 k lignes de NLE pour résoudre un problème que nous avons déjà résolu avec FreeCut ; (c) l'extraction « mégasimplifiée » qu'imagine le fondateur existe déjà en JS dans FableCut (§3) ; (d) le temps en ticks et le registre de commandes sont des **idées**, pas du code à greffer.

Plan d'intégration des idées FilmCraft :

| Idée | Où | Action |
|---|---|---|
| Registre de commandes auto-descriptif (`command_list`) | `app/server/nexora/` | Les outils de montage (§5) exposent nom, schéma Zod, **état d'activation** (ex. `reframe` désactivé sans plan vidéo) ; l'agent reçoit la liste filtrée à chaque tour, ce qui réduit les erreurs d'un petit modèle. |
| `command_batch` atomique = un pas d'annulation | `mode-studio/src/features/nexora/timeline.ts` (`enUnePas`, `appliquerCommandes` existent déjà) | Garder ; étendre aux nouvelles opérations. |
| Temps entier exact | contrat EDL (§5.1) | Durées en **images** (entier) + cadence, jamais en flottants, pour éviter la dérive aux coupes. |
| Transcription par mots, temps = temps du média | `app/server/whisper.ts` | Stocker mots {id, t0, t1, locuteur, confiance} par média ; la « transcription de séquence » est **dérivée**, jamais stockée (principe de FilmCraft, `docs/transcripts.md`). |
| Export d'échange | rapport 02 §4.1 | Écrire l'EDL en OTIO JSON (format simple) ; ne pas embarquer la crate Rust. |

## 3. Balayage au-delà de FilmCraft : composants jugés

### 3.1 Tableau donneur / base

| # | Nom | URL | Licence | Maturité (02/11/2026) | Vérif. | Ce qu'on prend | Où ça se branche |
|---|---|---|---|---|---|---|---|
| 1 | **FableCut** | github.com/ronak-create/FableCut | MIT | 774 ★, dernier commit 30/10/2026, **très jeune**, 24 outils MCP, historique de versions | **C** | Modules UMD **sans dépendance** : `beats.js` (458 l., onsets → battues, BPM, courbe d'énergie, « drop », grille, `snapOps`/`retimeOps`), `silence.js` (97), `ducking.js` (127), `loudness.js` (135, BS.1770-4), `reframe.js` (297, caméra virtuelle à zone morte) + `tracker.js` (253), `highlights.js` (296, meilleurs moments sans coupe interne), `captions.js` (227), `color.js` (1076, étalonnage + oscilloscopes + stats d'image), `edit-ops.js` (1015, split, ripple, roll, slip, slide, fondu enchaîné), `project-ops.js` (patch d'opérations) | `mode-studio/src/features/nexora/` (navigateur) **et** Node côté `app/server/` (mêmes fichiers, testables sans navigateur). `NEXORA.md` dit déjà « algorithmes d'édition par agent inspirés de FableCut » : **auditer ce qui est déjà porté avant de recopier**. |
| 2 | **browser-use/video-use** | github.com/browser-use/video-use | MIT | 30 361 ★, 08/10/2026, Python | **C** (SKILL.md, `render.py`, `grade.py`) | (a) **Contrat EDL** `{sources, ranges[{source,start,end,beat,quote,reason}], grade, overlays[{file,start_in_output,duration}], subtitles}` ; (b) **12 règles dures** : sous-titres appliqués en dernier, extraction par segment puis concat sans réencodage, **fondus de 30 ms à chaque coupe**, overlays décalés par `setpts`, SRT en temps de sortie, ne jamais couper dans un mot, marge de 30-200 ms, transcription au mot et en cache, stratégie confirmée avant exécution ; (c) `loudnorm` à deux passes ; (d) vue texte `takes_packed.md` (12 Ko lisibles par le LLM, pas la vidéo) + `timeline_view` (bande d'images + onde + mots) **à la demande** ; (e) `project.md` de mémoire de session ; (f) 8-10 préréglages d'étalonnage en chaîne ffmpeg. **Écarter** : dépendance ElevenLabs Scribe (payante) → `faster-whisper` déjà présent. | Contrat d'EDL, règles dures → validateur ; `loudnorm` → `mix_audio` ; `takes_packed` → `analyze_media` (vue texte) ; `timeline_view` → `critique`. Rendu : on garde `film.py`/`montage_v3.py`. |
| 3 | **PySceneDetect** | github.com/Breakthrough/PySceneDetect | BSD-3-Clause | 5 314 ★, 02/11/2026 | R | Coupes franches et fondus (adaptatif, seuil, contenu) | `analyze_media` côté serveur (Python déjà présent pour `film.py`). Repli sans dépendance : `scdet` de ffmpeg. |
| 4 | **HyperFrames** (HeyGen) | github.com/heygen-com/hyperframes | Apache-2.0 | 77 330 ★, 02/11/2026, TypeScript | R + compétence installée | HTML → vidéo déterministe : titres cinétiques, sous-titres animés au mot, cartons, graphiques ; ~450 blocs prêts (registre) | Couche « overlays » : rend un `.mp4`/`.webm` alpha posé comme un clip ; `captions` stylisées ; remplace une partie de `couches.py`/`carton_nexora.py`. |
| 5 | **OpenTimelineIO** | github.com/AcademySoftwareFoundation/OpenTimelineIO | Apache-2.0 | 2 052 ★, 31/10/2026 | R | Format d'échange (`.otio` JSON) vers Resolve/Premiere/Kdenlive | Export seulement (rapport 02 §4.1 confirmé) ; pas de format de stockage. |
| 6 | **faster-whisper** | github.com/SYSTRAN/faster-whisper | MIT | 26 393 ★, 31/10/2026 | R | Mots horodatés, déjà utilisé (`NEXORA.md`) ; ajouter l'alignement fin (WhisperX BSD-2, 25 k ★) seulement si les sous-titres dérivent | `analyze_media` / `captions` |
| 7 | **Silero VAD** | github.com/snakers4/silero-vad | MIT | 10 579 ★, 22/10/2026 | M | Détection de parole fiable pour couper les silences et caler le ducking mieux qu'un seuil RMS | `analyze_media`, `mix_audio` |
| 8 | **Mediabunny** | github.com/Vanilagy/mediabunny | MPL-2.0 | 7 420 ★, 30/10/2026 | R (rapport 02) | Entrée/sortie et export WebCodecs, déjà dans FreeCut | Rendu navigateur |
| 9 | **FreeCut** | github.com/walterlow/freecut | MIT | 2 304 ★, 29/10/2026 | C (déjà notre base) | Éditeur, timeline, `headless/` (`edit-operations.mjs`, `frame.mjs`, `agent.mjs`) | Surface « utilisateur » ; cible des `EditPlan` |
| 10 | **librosa** | github.com/librosa/librosa | ISC | 8 753 ★, 06/10/2026 | M | Battues/onsets côté serveur si `beats.js` insuffisant (musique dense) | `analyze_media` (repli) |
| 11 | **KyaniteLabs/kinocut** (ex-mcp-video) | github.com/KyaniteLabs/kinocut | Apache-2.0 | 236 ★, 02/11/2026 | R | **Contre-exemple utile** : 205 outils MCP, « garde-fous » de qualité et « reçus vidéo ». Trop large pour un petit modèle (le rapport 09 plaide pour peu d'outils). À lire pour ses contrôles qualité, pas à intégrer. | Inspiration de `critique` |
| 12 | Motion Canvas | github.com/motion-canvas/motion-canvas | MIT | 19 640 ★, dernier commit 07/2026 | M | Animations par code ; recouvert par HyperFrames pour notre usage | Écarté pour l'instant |
| 13 | OpenCut | github.com/OpenCut-app/OpenCut | MIT | 97 105 ★ ; dernier commit 24/09/2026 | M | Déjà écarté au rapport 02 (réécriture) | — |
| 14 | Editly | github.com/mifi/editly | MIT | 5 576 ★, dernier commit 05/2025 | M | Montage déclaratif JSON → ffmpeg ; inactif depuis 2025 | Idée seulement |

### 3.2 Écartés pour des raisons techniques

| Nom | Pourquoi |
|---|---|
| Ultralytics (suivi de sujet), Essentia, aubio | AGPL / GPL : incompatibles avec un service en réseau sans publier le code ; pour le recadrage, `reframe.js` (mouvement + détail + couleur, sans modèle) suffit au départ, puis détecteur sous Apache (YOLOX) ou AutoFlip de MediaPipe (Apache-2.0, 37 k ★) si on a besoin de visages. |
| Remotion | Licence spécifique (relevé `NOASSERTION`), déjà écarté au rapport 02. |
| madmom (battues) | Licence du code non déterminée par l'API et modèles possiblement non commerciaux : **à vérifier** avant tout usage ; `beats.js`/librosa suffisent. |
| TransNetV2 | Poids MIT mais dépôt inactif depuis 12/2023 ; PySceneDetect + `scdet` d'abord. |
| open_clip (appariement de plans B-roll) | Licence relevée `NOASSERTION` : **à vérifier** ; SigLIP via transformers est l'alternative. Reporté en P3. |
| Demucs | Dépôt Meta archivé (fork `adefossez/demucs` actif, MIT) : utile plus tard pour séparer voix/musique d'un média importé, pas prioritaire. |

### 3.3 Ce que font les leaders (sources primaires, pages publiques lues le 02/11/2026)

Vérification limitée : seules les pages ci-dessous ont été lues ; **CapCut, Veed, Kapwing, Captions, LTX Studio et Google Flow n'ont pas été vérifiés** (recherche sans résultat exploitable sur leurs domaines).

| Acteur | Ce que dit sa page | Leçon pour nous |
|---|---|---|
| **Descript — Underlord** (help.descript.com) | « Co-éditeur » agentique : sous-titres stylés au mot (police, mot actif en couleur de marque), « découpe en 5 clips de 1 min maximum », « 60-90 s au format vertical », outils *Remove Filler Words / Shorten Word Gaps / Edit for Clarity* ; avertit que le modèle « se trompe parfois » et que l'agent a eu besoin de **garde-fous pour ne pas promettre l'irréalisable**. | L'agent doit connaître la liste de ce qui est réalisable (registre de capacités) et refuser le reste : nos outils exposent leur état d'activation. |
| **OpusClip — ClipAnything** (opus.pro) | Trouver n'importe quel moment par **requête en langage naturel**, analyse image + son + sentiment. | `find_moments` (requête texte → intervalles) sur légendes d'images + transcription + énergie. |
| **Higgsfield — AI Video Editor** (higgsfield.ai) | Édition **générative par prompt** (retrait d'objet, restyle, changement de fond, amélioration 4K, interpolation, doublage en 18 langues, recadrage). | Une partie du « montage » est de la **régénération** : c'est notre terrain (H3), pas celui d'un NLE. |
| **Runway — Aleph / Edit Studio** (academy.runwayml.com) | Transformation de vidéo existante par prompt dans un studio d'édition. | Même constat : l'édition générative est un type d'outil à part, à devis. |

## 4. Les règles qui font réussir un modèle bon marché

Constats tirés de `video-use`, de FableCut et de notre V3 :

1. **Le LLM ne regarde pas la vidéo, il lit des vues texte compactes** : transcription au mot en 12 Ko, plan par plan en une ligne, courbe d'énergie en ~30 nombres, battues numérotées. Une image n'est montrée qu'aux points de décision.
2. **Le LLM choisit des identifiants, le code calcule des secondes.** Il dit « coupe au clip c3 sur la battue 12 » ; le code recale sur la battue, le mot, la coupe de plan et l'image entière, applique les marges et les fondus de 30 ms.
3. **Planifier puis compiler** : un seul appel de planification (liste de plans sur une courbe d'énergie) puis compilation déterministe, plutôt qu'une longue conversation d'opérations.
4. **Juger avec des mesures avant de juger avec un modèle** : `revue.py` calcule déjà rythme de coupe par section, crête du son dans ±60 ms d'une coupe, sonie intégrée, crête vraie. Le juge visuel ne reçoit que la planche contact + ces nombres + une grille de notation.
5. **Réviser par rustines** sur les seuls identifiants signalés, au plus 2 tours.
6. **Recettes en données** (hook → montée → drop → climax ; tête parlante nettoyée ; clip vertical ; publicité produit) : un petit modèle imite mieux qu'il n'invente.

## 5. L'API de montage (outils typés pour le LLM)

### 5.1 Contrat unique : `EditPlan` (EDL) v1

Une seule structure, partagée par le serveur (`app/server/nexora/`), Mode Studio et les scripts Python, validée par Zod ; dérivée de l'EDL de `video-use` et des `montage-v3.json` / `film.py` existants.

```jsonc
{
  "version": 1, "fps": 24, "format": "16:9",            // 16:9 | 9:16 | 1:1 ; durées en IMAGES (entiers)
  "sources": { "m12": {"media": 12, "kind": "video"}, "mus": {"media": 40, "kind": "audio"} },
  "tracks": [
    { "id": "V1", "kind": "video", "clips": [
        { "id": "c1", "src": "m12", "in": 48, "dur": 31, "speed": 1.0,
          "transition_in": {"type": "cut|fade|dip|wipe", "dur": 0},
          "reframe": {"mode": "center|follow", "keys": []}, "grade": "preset:froid-contraste",
          "tags": {"section": "drop", "energy": 8, "why": "premier coup de la musique"} } ] },
    { "id": "A1", "kind": "audio", "role": "music", "clips": [ { "id": "a1", "src": "mus", "in": 0, "dur": 1272, "gain_db": -2 } ] }
  ],
  "overlays": [ { "kind": "title|caption|lowerthird", "t": 72, "dur": 58, "text": "Imaginez.", "style": "titre", "accent": "mot" } ],
  "mix": { "duck_under": "voice", "target_lufs": -14, "true_peak_db": -1.0 },
  "intent": { "brief": "…", "energy_curve": [[0,1],[8,3],[16,8],[43,10]], "grid": "beats:mus" }
}
```

### 5.2 Les douze outils

Tous renvoient `{ok, result, warnings[], cost}` ; tout refus indique la règle violée en une phrase pour que le modèle corrige. Aucun outil de montage ne dépense de crédits ; ceux qui engagent une génération passent par `proposer_production` (devis validé par la personne).

| # | Outil | Entrée (résumé) | Sortie | Composant | Garde-fous câblés (le LLM ne peut jamais) |
|---|---|---|---|---|---|
| 1 | `analyze_media` | `{media_ids[], want: ["shots","beats","energy","words","silence","luma","keyframe_captions"]}` | par média : coupes de plan `[{id,t}]`, battues `[{n,t}]`+BPM, courbe d'énergie (pas 0,5 s), mots `{id,t0,t1,spk}`, silences, luminance moyenne ; **vue texte compacte** (`takes_packed`) ; résultat **en cache** par empreinte du fichier | `beats.js`/librosa, PySceneDetect/`scdet`, `faster-whisper`, `silence.js`+Silero | Analyse **seulement** des médias de l'organisation (déjà la règle de `NEXORA.md`) ; durée maximale par média ; jamais de retranscription d'un fichier inchangé |
| 2 | `find_moments` | `{query, media_ids[], max, min_dur, max_dur}` | intervalles classés avec raison | `highlights.js` + légendes d'images + mots | ne traverse jamais une coupe de plan ; bornes de durée |
| 3 | `plan_edit` | `{brief, recipe, media_ids[], music_id?, target_dur, format}` | `intent` + liste de plans `[{src, intent, energy, dur_hint}]` (pas encore de secondes) | LLM + recette ; données de `analyze_media` | durée totale ≤ `DUREE_MAX_S` (120 s aujourd'hui) ; nombre de plans ≤ `MAX_PLANS` ; plans manquants listés à part (→ commande de génération sous devis) |
| 4 | `build_timeline` | `{plan, grid}` | `EditPlan` complet + rapport de validation | compilateur déterministe (`montage_v3.py` porté), `edit-ops.js` | **Validateur dur** : sources existantes et autorisées, aucun chevauchement, jamais de coupe dans un mot, marge 30-200 ms, fondus 30 ms, vitesse ∈ [0,25 ; 4], durée min d'un clip 0,05 s, sous-titres rendus en dernier, au plus N clips |
| 5 | `cut_on_beat` | `{clip_ids[] \| track, every: 1\|2\|4\|8, strength}` | rustines recalées | `beats.js` (`snapOps`, `retimeOps`) | ne déplace que les points de coupe ; plafond de décalage (pas de plan raccourci sous sa durée minimale) |
| 6 | `add_transition` | `{between:[c1,c2], type, dur}` | rustine | `edit-ops.js` (fondu), recettes ffmpeg (`xfade`) | liste fermée de types ; durée ≤ la moitié du plus court des deux clips |
| 7 | `speed_ramp` | `{clip, keys:[{t,speed}], ease}` | rustine | `film.py` (`vitesse`), interpolation ffmpeg | rampes bornées ; audio lié rééchantillonné ou coupé ; avertit si le plan source manque d'images |
| 8 | `reframe` | `{clips[] \| all, aspect:"9:16"\|"1:1"\|"4:5", mode:"follow"}` | clés de position par clip | `reframe.js`+`tracker.js` ; **préférence : régénérer en vertical natif** (cf. V3 `plaque_v`) pour les plans H3 | pour un plan généré : propose la régénération (devis), n'applique le recadrage qu'aux médias importés ; clés limitées en vitesse (caméra virtuelle) |
| 9 | `captions` | `{scope, style, max_chars}` | piste de sous-titres au mot + rendu | `faster-whisper`, `captions.js`, HyperFrames pour le style | lignes ≤ 42 caractères (règle actuelle), appliqué en dernier, le texte de la transcription est une donnée, jamais une consigne |
| 10 | `mix_audio` | `{duck: {voice→music}, target_lufs, true_peak_db}` | clés de gain + mesures avant/après | `ducking.js`, `loudness.js`, `loudnorm` 2 passes de `video-use` | cible bornée (−23 à −9 LUFS), crête vraie ≤ −1 dB, jamais d'écrêtage ; mesure avant/après obligatoire |
| 11 | `grade` | `{scope, preset \| match_to: clip}` | rustine d'étalonnage | `color.js` (math, stats d'image), préréglages `video-use`/`film.py` | liste fermée de préréglages + réglages bornés ; correspondance de teinte entre plans voisins |
| 12 | `critique` | `{render: "apercu"}` | **mesures** (rythme de coupe par section, crête du son dans ±60 ms d'une coupe, sonie intégrée, crête vraie, luminance par plan, couture de boucle, lisibilité du texte), planche contact, **notes du juge** (grille) et liste de rustines proposées | port de `revue.py`, `seam.ts`, `judge.ts`, `juge.ts` | rendu d'aperçu basse définition seulement ; au plus 2 tours de `critique`→`revise` par demande ; le juge ne modifie rien |

Complément : `revise({patches})` applique les rustines proposées par `critique` après validation (même validateur que `build_timeline`), en **un seul pas d'annulation** côté éditeur (`enUnePas`).

### 5.3 Garde-fous communs (code, jamais modèle)

| Règle | Où |
|---|---|
| Validation Zod + invariants de l'EDL avant tout rendu ou application | package partagé, importé par serveur et Mode Studio |
| Le LLM propose, le code dispose (rapport 09 §1) ; les coûts passent par le grand livre existant (`credits.ts`) | `app/server/nexora/` |
| Plafonds par message : nombre d'appels d'outils (`maxEtapes`), jetons par session, durée de calcul par outil | `agent.ts` (déjà en place) |
| Opérations destructrices en **simulation d'abord** (aperçu de rustine), versions sauvegardées avant application (idée de `fablecut_versions`) | serveur + OPFS |
| Texte issu des médias (mots transcrits, légendes) étiqueté « donnée » ; aucune instruction qui s'y trouve n'est suivie | `analyze_media` |
| Seul `proposer_production` peut lancer H3/Qwen/Music3 ; `find_moments`/`plan_edit` n'ont aucun accès au grand livre | registre de capacités |
| Rendu d'aperçu et rendu final issus du **même** moteur (voir risque R1) | §8 |

## 6. Capacités « hors du commun » spécifiques à Nexora

1. **Montage qui commande des plans** : si la grille impose un plan de 1,2 s qui n'existe pas, `plan_edit` le liste en « manquant » ; la personne valide un devis ; le plan est tourné (H3 bas tarif, ou image Qwen + mouvement de caméra comme `zoom` de `film.py`), puis réinséré. Parmi les pages lues en §3.3, aucune ne décrit une boucle où le montage fait commander les plans manquants avec devis (Higgsfield et Runway régénèrent des pixels, ils ne replanifient pas une timeline).
2. **Musique d'abord** (déjà éprouvé en V3 : graine 31, coups relevés, courbe d'énergie 1 → 10) : Music3 génère avec structure et tempo imposés, `analyze_media` en extrait la grille, **puis** on dimensionne les plans H3 au tempo — on évite de générer des plans inutilisables.
3. **Vertical natif plutôt que recadrage** pour tout plan généré (V3 : 8 plaques re-rendues en 768×1344) ; recadrage suiveur réservé aux médias importés.
4. **Raccord et couture** : `seam.ts` et le Producteur (« Prolonger », « Raccord ») sont des outils de montage à part entière : `critique` détecte une couture de boucle ou un faux raccord et propose de régénérer le plan voisin.
5. **Édition par le texte** (idée FilmCraft/Descript) : supprimer des mots dans la transcription = couper dans la timeline ; déjà amorcé par « couper les silences ».
6. **Mémoire de projet** (`project.md` de `video-use`) : décisions et raisons de chaque coupe (`tags.why`) conservées, ce qui permet à un modèle bon marché de reprendre le travail d'une session à l'autre sans tout relire.
7. **Exposition MCP** : même registre d'outils servi en MCP (comme FableCut et kinocut) pour que Claude Code ou tout agent externe pilote Nexora — utile en démonstration et en test.

## 7. Feuille de route classée (gain de qualité avec un modèle bon marché)

| Rang | Chantier | Effort | Pourquoi dans cet ordre |
|---|---|---|---|
| **P0-1** | **`EditPlan` v1 + validateur** (package TS partagé, tests) ; import des `montage-v3.json`/`film.py` comme premiers exemples | 2-3 j | Sans contrat validé, aucun modèle bon marché ne tient la route ; c'est le filet de sécurité de tout le reste. |
| **P0-2** | **`analyze_media`** (battues+énergie, coupes de plan, mots, silences, vue texte compacte, cache) | 3-4 j | Donne au modèle des « yeux et des oreilles » lisibles pour quelques milliers de jetons. Porter `beats.js`/`silence.js` après audit de ce qui est déjà dans `timeline.ts`. |
| **P0-3** | **`critique`** (port de `revue.py` en service + planche contact + notes du juge) | 3 j | Le multiplicateur de qualité : un juge qui mesure permet à un modèle moyen de s'améliorer en deux tours. |
| **P1-1** | **`build_timeline` + `plan_edit` + 4 recettes** | 4-5 j | Transforme un brief en montage correct du premier coup. |
| **P1-2** | **`cut_on_beat` + `mix_audio`** (ducking, sonie 2 passes −14 LUFS) | 3 j | Les deux réglages que l'oreille juge le plus vite. |
| **P2** | `captions` au mot (style HyperFrames), `reframe` (suiveur, sinon régénération verticale), `grade`, `add_transition`, `speed_ramp` | 1-2 sem. | Finition, chacun indépendant. |
| **P3** | `find_moments` (requête naturelle), appariement B-roll par embeddings, plans manquants sous devis, export OTIO, serveur MCP, mémoire de projet | 2-3 sem. | Différenciation et ouverture. |

**Mesure d'acceptation proposée** : sur 10 briefs fixes, comparer `glm-5.3` avec et sans la boucle `critique`, et avec un modèle plus cher en référence ; critères = score du juge, taux d'EDL valides du premier coup, nombre de tours, coût en jetons. Cela fonde le choix de modèle (rapport 09 §6) sur des chiffres.

## 8. Risques

| # | Risque | Parade |
|---|---|---|
| R1 | **Deux moteurs de rendu** (FreeCut/WebCodecs pour l'aperçu, ffmpeg/Python pour le film) : un montage jugé bon sur l'un peut différer sur l'autre | Produire la planche de `critique` avec le même moteur que la livraison ; utiliser `mode-studio/headless/frame.mjs` pour les images (fichiers vus, comportement **à vérifier**) ; test d'écart image à image |
| R2 | FableCut est **très jeune** (quelques semaines), un seul auteur apparent | Copier les modules dans l'arbre avec leurs tests et la mention MIT ; ne pas suivre l'amont ; revue de chaque port |
| R3 | `video-use` suppose des têtes parlantes et un STT payant | N'en prendre que le contrat, les règles et `loudnorm` ; garder `faster-whisper` |
| R4 | Un petit modèle produit des EDL invalides ou incohérents | Sortie structurée + réparation à 2 essais + messages de refus précis ; mesure d'acceptation §7 |
| R5 | Boucle `critique`→`revise` coûteuse ou sans fin | Plafond de 2 tours, aperçu basse définition, coût journalisé |
| R6 | Explosion de la surface d'outils (kinocut : 205) | Rester à ≈ 12 outils ; verbes de rustine regroupés dans `revise` |
| R7 | Dérive des temps (flottants) et coupes dans un mot | Images entières, recalage sur mots/battues, marges et fondus de 30 ms imposés par le validateur |
| R8 | Détection de sujet insuffisante pour le recadrage suiveur | `reframe.js` d'abord (sans modèle), détecteur Apache ensuite ; régénération verticale pour le généré |
| R9 | Mesure de qualité subjective du juge | Grille fixe, mesures objectives en tête, jeux de 10 briefs |

## 9. Ce qui reste non vérifié

- Aucune exécution : ni les tests de FableCut, ni les scripts de `video-use`, ni les modules de FilmCraft n'ont été lancés.
- Pages des leaders lues uniquement pour Descript, OpusClip, Higgsfield et Runway (extraits) ; CapCut, Veed, Kapwing, Captions, LTX Studio, Flow non vérifiés.
- Licences `NOASSERTION` (madmom, ffmpeg-normalize, open_clip, Remotion) à lire fichier par fichier avant usage ; HyperFrames, PySceneDetect, OTIO, Silero, librosa jugés sur métadonnées et documentation, non sur le code.
- Ce qui est déjà porté de FableCut dans `mode-studio/src/features/nexora/timeline.ts` (503 lignes) n'a pas été comparé ligne à ligne.
