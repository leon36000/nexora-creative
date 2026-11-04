# Voix, manche 2 : accélérer Drama 3, le faire tourner en local, autres voix (03/11/2026)

Verdict du fondateur après la manche 1 : Drama 3 est bon mais lent, ElevenLabs est le meilleur pour l'instant, qualité maximale d'abord, mais à qualité comparable on privilégie le local. Tous les échantillons et le tableau complet (fichier, candidat, levier, débit, EMR Whisper, durée, temps, coût, matériel, licence) sont dans `~/nexora-creative-data/work/ecoute/manche-2/INDEX.md` (126 fichiers, 21 Mo ; copie sur pc1 : `/home/pc1/Bureau/Nexora-Livrables/ecoute/manche-2/`). **Tout ce qui suit est mesuré par machine (Whisper medium, silencedetect, ebur128) ; seules les oreilles du fondateur décident du timbre, de l'accent et du naturel.**

Définitions : c/s = caractères du texte (espaces compris) par seconde de durée utile, pauses comprises ; « artic. » = hors pauses internes. Quatre passages : p1, p2, p3 de la manche 1 et p5 (25 s : p1 + p2 + deux phrases de liaison + p3) pour la stabilité.

## 1. Mesurer la cible : à quel point Drama 3 est-il « lent » ?

| prise (p1 / p2 / p3, c/s globaux) | débit | % d'ElevenLabs |
|---|---|---|
| ElevenLabs v4 Alexandre (manche 1) | 14,8 / 11,7 / 13,0 (artic. 16,6 à 18,9) | 100 % |
| Drama 3, clone Alexandre **sans consigne** | 14,3 / 11,2 / 13,4 | 98 % |
| Drama 3, clone + direction en crochets + `[pause]` (ce que le fondateur a le plus probablement entendu) | 11,0 / 9,5 / 13,1 (artic. 14,7 à 15,9) | 85 % |
| Drama 3, consigne « lent, intime » | 10,0 / 7,5 / 10,9 | 70 % |

Constat : **Drama 3 n'est lent que lorsqu'on lui demande d'être lent**. La direction « calme, intime, pauses » ralentit l'articulation d'environ 12 % et ajoute 1 à 3 s de silence par passage. Le clone seul tient le rythme d'ElevenLabs à 2 % près (p5 : Drama 3 21,9 s contre 21,1 s pour ElevenLabs, 14,2 contre 14,8 c/s).

## 2. Leviers pour accélérer (OpenRouter, `fish-audio/drama-3`, ≈ 0,0007 USD le passage de 25 s)

Base : clone Alexandre (9 s + transcription), sans consigne. EMR = erreur de mots Whisper.

| levier | résultat mesuré | EMR | verdict machine |
|---|---|---|---|
| (a) consigne EN « brisk, natural narration pace, never dragging » | p5 14,9 c/s (+5 %) | 0 | léger, sûr |
| (a) consigne FR « débit soutenu, naturel, sans traîner » | aucun gain, p1 plus lent (13,6 c/s) | 0,17 sur p1 | à éviter |
| (b) référence étirée ×1,15 (prise Alexandre accélérée) | p1-3 : +6 % ; p5 14,4 c/s | 0 | gain faible et irrégulier |
| (b) référence étirée ×1,25 | p1 18,5 c/s (+24 %) | 0 | efficace, risque de voix plus nerveuse : à écouter |
| (b) prise Codex 06 (plus rapide de 8 %) comme référence | pas de gain net (p1 15,8 ; p2 11,2) | 0 | inutile |
| **(d) paramètre API `speed`** (honoré par Drama 3 sur OpenRouter) | 1,10 : p5 15,1 c/s (+6 %) ; 1,15 : 16,5 (+16 %) ; 1,20 : 16,7 (+17 %) ; 1,30 : p1 19,6 c/s (+32 %) | 0 partout, jusqu'à 1,30 | **le levier le plus propre** ; la hauteur médiane ne dérive pas (test autocorrélation grossier) |
| (e) Rubber Band ×1,08 / ×1,12 / ×1,18 (hauteur conservée) | p5 15,2 / 15,8 / 16,6 c/s | 0,039 (×1,08, un mot) puis 0 | propre à l'oreille de la machine ; −3,5 LU de niveau à rattraper par la normalisation −14 LUFS |
| (e) `atempo` ×1,12 | identique à Rubber Band en débit | 0 | idem ; moins de contrôle des transitoires |
| (c) phrase par phrase, silence de 0,35 s posé au montage | p5 23,4 s (13,4 c/s) : trop lent | 0 | donne le contrôle mais 0,35 s est trop long ; avec `speed` 1,10 : 14,5 c/s ; viser 0,15 à 0,20 s |

À retenir : (1) ne pas demander « lent » ; (2) `speed` 1,10 à 1,15 pour un gain naturel de 6 à 16 % ; (3) l'étirement après coup (Rubber Band) est utilisable jusqu'à ×1,12 sans erreur de mots, ×1,18 reste sans erreur mais c'est à écouter (étalement spectral non mesuré : seule l'écoute tranche) ; (4) les pauses de la narration se posent au montage, phrase par phrase. Le débit visé d'ElevenLabs (≈ 13 à 15 c/s) s'obtient avec le clone seul ou `speed` 1,05 à 1,10.

## 3. Drama 3 en local : ça marche, sur les deux machines

**Cause de l'échec de la manche 1 sur la 5090** : pas l'architecture sm120 mais le JIT `gptq_marlin_repack` de SGLang : nvcc 13.1 contre glibc 2.43 (« exception specification is incompatible » sur `rsqrt`/`rsqrtf` entre `bits/mathcalls.h` et `crt/math_functions.h` de CUDA). **Contournement sans sudo** : copie privée de la toolchain CUDA 13.1 (`voix-bench/cuda-priv`) avec `noexcept(true)` ajouté aux lignes 629 et 653 de `crt/math_functions.h`, puis `CUDA_HOME` vers cette copie. Rien n'a été modifié dans `/usr/local`.

| | RTX 5090 pc1 (int4 GPTQ-Marlin, 22 Go) | GB10 pc6 (FP8 officiel, 37 Go) |
|---|---|---|
| moteur | SGLang-Omni 0.5.23 (venv `voix-bench/sgl`) | SGLang-Omni, venv `~/nexora-creative-data/work/voix2-modeles/sgl-gb10` |
| chargement à froid / à chaud | ≈ 5 min (compilation) / 29 à 34 s | ≈ 6 min dont 4 min 40 de lecture des poids par sshfs / non mesuré |
| mémoire | 29,8 Go GPU au total | ≈ 50 Go de mémoire unifiée (non mesuré précisément) |
| premier audio | 60 à 85 ms | 330 à 360 ms |
| RTF (ligne de 5 s / passage de 25 s) | 0,12 à 0,13 / 0,116 | 0,87 / 0,83 |
| passage de 25 s | 2,2 s pour 18,8 s d'audio | 17,7 s pour 21,3 s d'audio |
| EMR p1-3 / p5 | 0,022 / 0,020 | 0 / 0 |
| débit p5 | 16,5 c/s (111 % d'ElevenLabs) | 14,7 c/s (99 %) |

**Recette 5090** : `ssh pc1`, puis `voix-bench/serve-int4-5090.sh --tts_engine.gpu_memory_fraction 0.70 --vocoder.gpu_memory_fraction 0.10 --preprocessing.total_reserve_bytes 3GiB --tts_engine.factory.max_new_tokens 700 --tts_engine.engine.cuda_graph_backend_prefill disabled` (le script pose `CUDA_HOME`, `TRITON_CACHE_DIR`, `TMPDIR` et `--vocoder.factory.codec_path` vers le dossier int4, port 8000). Fraction moteur 0,75 : mémoire insuffisante à la préparation de la référence ; `max_new_tokens` 1024 : le vocodeur refuse de démarrer. La première requête après démarrage prend 9,5 s (noyaux).
**Recette GB10** : poids de pc1 montés en lecture seule par sshfs (binaire extrait d'un `.deb`, sans sudo, rien copié sur le disque de pc6) ; `voix2-modeles/run/serve-fp8-gb10.sh --tts_engine.gpu_memory_fraction 0.40` (port 8011), avec `--vocoder.factory.codec_path` vers `drama-3` (sinon tentative de téléchargement). Il a fallu retirer `dots.tts` et `nemo_text_processing` du `pyproject.toml` d'une copie des sources (`pynini` ne compile pas sur aarch64 ; inutiles pour Drama 3) et extraire les en-têtes `Python.h` par `apt-get download` (Triton compile à l'exécution). vLLM-Omni n'a pas été essayé : SGLang-Omni a suffi.
**Clonage** : `/v1/audio/speech`, `references:[{data: base64, media_type, text}]`, flux `pcm` (client `voix2-modeles/run/gen.py`). Pas d'équivalent du champ `instructions` d'OpenRouter, ni de `speed`, testé en local : seules les balises `[...]` dans le texte.

**Même voix qu'en API ?** Oui d'après les mesures grossières : Whisper redonne le texte, durées et débits proches (14 à 17 c/s contre 15), corrélation spectrale 0,97 à 0,99 ; pas de modèle d'empreinte de locuteur, donc à confirmer à l'oreille (`voix2-dramalocal-*` contre `voix2-drama3-base-*`). **Variance entre prises** : p2 est passé de 5,9 s à 9,8 s sur la 5090 (silence ajouté) ; plafonner `max_new_tokens` et générer plusieurs prises.

Faits de licence (citations des fichiers, pas d'interprétation) : fiche HF de `fishaudio/drama-3` : `license: other`, `license_name: fish-audio-research-license` ; le fichier LICENSE des deux dossiers est intitulé « Fish Audio Community License Agreement, Version 1.0, 13 octobre 2026 » ; la fiche int4 annonce `fish-audio-community-license`. Le fondateur tranche l'usage.

Incident à signaler : la 5090 était occupée par ComfyUI (31 Go, inactif, file vide) ; l'agent a appelé son API `/free` (déchargement des modèles, rien tué). ComfyUI rechargera ses modèles à la prochaine tâche. Le shard FP8 14 était tronqué et le 15 manquait ; les 15 sont maintenant complets et vérifiés sur pc1.

## 4. Autres voix

### ElevenLabs v4 (OpenRouter, 0,08 USD / 1000 caractères)
Les ID de bibliothèque publique s'utilisent directement dans `voice` ; les noms prédéfinis acceptés par le modèle sont : george, sarah, adam, alice, bella, bill, brian, callum, charlie, chris, daniel, eric, harry, jessica, laura, liam, lily, matilda, river, roger, will (ces voix prédéfinies parlent français avec l'accent de leur langue d'origine). Voix québécoises masculines trouvées (galerie publique JSON2Video, ID relevés) : **Thomas** « Clear, Warm and Professional » `4FLkNETtL5THnClfpjpb`, **Frederic** « Professional and Confident » `oziFLKtaxVDHQAh7o45V`, **Adam** (Québec) `93nuHbke4dTER9x2pDwE`, **Alexandre Boutin** `IPgYtHTNLjC7Bq7IPHrm` (la voix des films V5). Fichiers : `voix2-eleven4-{thomas,frederic,adam-qc,brian,daniel}-plain-{1,2,3,5}.mp3` et `voix2-eleven4-alexandre-plain-5.mp3`. Tous EMR 0 ; débits 93 à 109 % de la cible. Coût ≈ 0,04 USD par voix pour les quatre passages.

### Modèles ouverts avec clonage français (GB10, référence Alexandre 9 s, sans écoute)
| modèle | licence (fiche HF) | fr / clonage | EMR p1 / p2 / p3 / p5 | c/s p1 / p2 / p3 / p5 | génération |
|---|---|---|---|---|---|
| OmniVoice (k2-fsa) | README : « pre-trained model is licensed under the CC-BY-NC » (rien dans les métadonnées) | oui, avec transcription | 0 / 0 / 0 / 0 | 13,3 / 14,4 / 13,7 / 14,1 | RTF 0,25 à 0,65 |
| Qwen3-TTS 1.7B Base | apache-2.0 | oui, avec transcription | 0 / 0,07 / 0 / 0 | 16,8 / 13,3 / 15,2 / 16,5 | RTF 0,9 à 1,3 |
| VoxCPM2 | apache-2.0 | oui, avec transcription | 0 / 0 / 0 / 0 | 16,4 / 14,8 / 14,8 / 17,6 | RTF 1,2 à 1,8 |
| Chatterbox multilingue | mit | oui, sans transcription | 0 / 0 / 0,125 / 0,04 | 15,2 / 12,6 / 11,3 / 16,8 | RTF 0,5 à 0,8 |
| Ming 3.0 TTS 0,5B | mit | oui, avec transcription | 0 / 0,2 / 0 / 0,04 | 17,7 / 16,2 / 15,3 / 17,1 | RTF 0,5 à 1,0 |

Leviers de débit : OmniVoice `speed=0,85` → 12,0 c/s (EMR 0), seul levier propre ; Qwen3-TTS : référence étirée ×1,15 → 19,3 c/s, ×0,87 → 14,4 c/s (EMR 0, mais 5 s de pause en plus) ; VoxCPM2 : le préfixe de style « (speaking slowly…) » est lu à voix haute (EMR 0,42 sur p1), inutilisable ; Ming : le contrôle `speed` ne ralentit pas ; Chatterbox : `cfg_weight` sans effet net.

Écartés (raison sur fiche) : **Kyutai TTS en_fr** (cc-by-4.0) : le clonage est limité à des embeddings de voix précalculés, pas de clonage d'Alexandre ; IndexTTS-2 : langues en et zh, pas de licence dans les métadonnées ; Higgs Audio v2 : en, zh, de, ko ; Higgs TTS 3 4B : licence « other », non testé ; Fish Audio S2-pro : licence « other », 11 Go, disque insuffisant, non testé ; Voxtral-4B-TTS : cc-by-nc-4.0, non testé ; CosyVoice 3 : apache-2.0, français, 9,75 Go, installation lourde, non testé. H3 natif avec référence plus rapide : non refait (10,7 c/s en manche 1, EMR 0).

## 5. Classement de machine (n'est pas un verdict)

Critères : EMR, débit proche d'ElevenLabs (13,2 c/s sur p1-3, 14,8 sur p5), tenue sur 25 s, local, vitesse. Détail dans INDEX.md.

1. **Drama 3 local GB10 FP8** (EMR 0, débit 99 %, RTF 0,83) et 2. **Drama 3 local 5090 int4** (EMR 0,02, 111 %, RTF 0,12) : même voix que l'API, la 5090 est 7 fois plus rapide mais l'int4 est un peu plus nerveux ;
3. Drama 3 API clone seul (+ `speed` 1,10) ;
4. OmniVoice (débit 95 %, rapide, mais CC-BY-NC) ;
5. Qwen3-TTS 1.7B (apache-2.0) ; 6. VoxCPM2 (apache-2.0, un peu rapide : 118 %) ; 7. Chatterbox multilingue ; 8. Ming 0,5B.
Référence : ElevenLabs v4 Alexandre.

## 6. Écoute conseillée (passage 5, 25 s)

`voix2-eleven4-alexandre-plain-5` (référence) ; `voix2-drama3-base-5` ; `voix2-drama3-speed110-5` ; `voix2-drama3-rb112-5` ; `voix2-dramalocal-5090-int4-5` ; `voix2-dramalocal-gb10-fp8-5` ; `voix2-qwen3tts-1.7b-clone-5` ; `voix2-omnivoice-default-5` ; `voix2-voxcpm2-clone-5` ; `voix2-eleven4-thomas-plain-5` et `voix2-eleven4-frederic-plain-5`. Pour comparer « le Drama 3 lent » : `ecoute/voix-B-drama3-clone-alexandre-direction-2` contre `voix2-drama3-base-2` et `voix2-drama3-speed115-2`.

## 7. Pipeline recommandé

1. **Local d'abord** : Drama 3 sur la 5090 (int4, RTF 0,12) ou la GB10 (FP8, RTF 0,83), clone Alexandre seul, sans consigne « lente », phrase par phrase avec pauses posées au montage (0,15 à 0,25 s), plusieurs prises (la durée varie de plus de 50 % d'une prise à l'autre sur la 5090), contrôle Whisper automatique (EMR ≤ 0,03 et durée dans ±15 % de l'attendu), puis loudnorm −14 LUFS. Si l'écoute confirme que le local égale ElevenLabs, c'est le chemin par défaut.
2. **Repli ElevenLabs v4 Alexandre via OpenRouter** pour toute ligne où le local échoue au contrôle ou ne convainc pas à l'écoute (0,026 USD le passage de 25 s).
3. Si le débit paraît court : `speed` 1,05 à 1,10 (API seulement) ou Rubber Band jusqu'à ×1,12.
4. À décider à l'oreille : la voix locale égale-t-elle Alexandre ? Si non, Qwen3-TTS (apache-2.0) est le meilleur candidat ouvert à licence permissive.

## 8. Limites

Aucune écoute ; un seul tirage par cellule (écart de ±5 % entre prises d'une même variante) ; test de hauteur par autocorrélation grossier ; pas de mesure de similarité de locuteur ; étalement spectral des étirements non mesuré ; `dirspeed112` et `nofr_speed112` viennent d'une passe dont le journal a été perdu à la coupure de courant (deux fichiers `postrb108` tronqués rangés dans `ecartes/`). Dépense OpenRouter journalisée de cette manche : ≈ 0,24 USD sur 4 USD. Disque de pc6 à 99 % (14 Go libres) : les venv `voix2-modeles/chatterbox` (5,7 Go) et `sgl-gb10` (9,3 Go) peuvent être supprimés après décision.
