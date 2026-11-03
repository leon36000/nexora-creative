# Voix et musique : banc d'écoute pour le fondateur (03/11/2026)

Objet : le fondateur a jugé la narration des 12 films (Chatterbox) et la musique à 0,1/10, a préféré la voix des vidéos Codex précédentes et veut la voix **la plus réaliste hors temps réel** (ton visé : publicité Apple, calme, intime, assuré, grandes pauses). Tous les échantillons et le tableau complet (fichier, candidat, fabrication, durée, coût, temps, licence, EMR Whisper, BPM) sont dans `~/nexora-creative-data/work/ecoute/INDEX.md` sur pc6 et dans `/home/pc1/Bureau/Nexora-Livrables/ecoute/` sur pc1 (≈ 150 voix, 6 musiques Lyria, 3 Music 3, WAV des finalistes dans `wav/`, essais techniques ratés dans `ecartes/`, aucun échantillon supprimé). **Tout classement ci-dessous est de machine ; seules les oreilles du fondateur tranchent.**

## 1. Comment les voix des vidéos Codex ont été faites (fait vérifié dans le projet)

- Les films OPSYS-AI du projet Codex (pc1, `video-opsys-ai/`) utilisent une voix **ElevenLabs v4 « Alexandre Boutin », catalogue French Canadian/Québec** (ID dans `scripts/brochure_voice.py`), obtenue via la passerelle OpenRouter/LiteLLM de pc1, avec la balise `[energetic, passionate, warm, confident]` et le nom écrit « OPSYS /eɪ aɪ/ ». Il existe aussi la voix Adam (Québec, « warm and friendly »). 27 prises mp3, 119 mots de narration.
- Le graphe H3 de ces projets (`baseline-request.json`, `queue_shot.py`) est **vidéo seule** : `VAEDecode` puis `CreateVideo` sans `VAEDecodeAudio`. L'avatar « AVATAR-TRAVAIL-r14 » a été « synchronisé sur la voix » en donnant un extrait d'Alexandre comme guide audio (`MiniMaxH3AddGuide`) : le son entendu dans ces films est donc **la voix ElevenLabs Alexandre, pas une voix générée par H3**. La voix que le fondateur a aimée est très probablement celle-là. Rien ne dit que le fichier de H3 ait jamais porté une voix native.
- H3 sait pourtant générer l'audio : notre recette (`app/server/graphs/h3.ts`, option `withAudio`) décode l'audio, et le nœud `MiniMaxH3ReferenceToVideo` accepte une **référence audio** (`<Audio 1>` dans le prompt).

## 2. Candidat A : voix native de MiniMax H3, reproduite

Recette : checkpoint `10Eros_Max_h3_8stepTURBO_beta7_SingularityV2_ref2va_int8HQ`, 8 étapes, euler/simple, décalage 12/3, 960x544, portrait synthétique (`F01-avatar-male-anchor.png` du projet Codex) en `<Picture 1>`, prompt d'ambiance de studio + « Québécois French, calm, intimate, confident, long pauses » + le texte entre guillemets ; `VAEDecodeAudio` branché dans `CreateVideo` ; moteur ComfyUI de pc1 (RTX 5090, port 18388, mon instance, tunnel 37288). Deux variantes : prompt seul, et référence vocale `<Audio 1>` = prise Alexandre (« His voice is the voice of <Audio 1> »). 3 passages chacune (graine 7001), 50 à 95 s par plan de 5 à 8 s. Voix isolée ensuite par Demucs (pc5) : fichiers `…-propre-…`.

Résultat mesuré : H3 prononce les 3 passages mot pour mot (EMR Whisper 0), cadence ≈ 10,7 c/s. Le timbre, l'accent et le naturel ne sont pas jugeables par machine. Variantes non faites faute de budget : 2e graine, `AddGuide` audio, FastH3.

## 3. Candidat B : Fish Audio Drama 3

**Via OpenRouter (fait, remplace le téléchargement)** : `fish-audio/drama-3`, `POST /api/v1/audio/speech`, 2 USD par million de caractères, soit **≈ 0,0004 USD les trois passages** (0,001 avec direction). Paramètres vérifiés dans la doc OpenRouter : `instructions` (style en langage naturel, accepté par les modèles Fish et Gemini), `input_references` (clonage sans état : prise de référence en base64 + transcription), balises entre crochets dans le texte. Testés : sans consigne ; `instructions` ; direction en crochets dans le texte ; `[long pause]` / `[pause]` entre les phrases ; **clonage de la prise Alexandre** (avec et sans direction) ; balises ponctuelles `[long pause]` `[exhales softly]`. Tous acceptés, français reconnu à 100 % par Whisper (EMR 0 à 0,04 selon variante), marque « Nexora, OPSYS-AI, WorkStudio » reconnue (EMR 0). La direction et les pauses allongent bien les phrases (5,9 s → 7,6 à 8,5 s sur le passage 1), preuve que le contrôle agit ; qu'il rende l'accent québécois reste à écouter. Les presets de voix n'existent pas (aucune liste) : seule la voix par défaut ou le clonage.
Dans le classement « audiorealism » publié par OpenRouter, Drama 3 est n°4 (958) et S2.1 Pro n°5 (953), derrière MAI-Voice-2 (n°1), MAI-Voice-2-flash et Gemini 3.8 flash TTS ; ces trois n'offrent pas de voix québécoise (MAI : fr-FR seulement).

**En local (tenté avant le changement de consigne, arrêté)** : poids int4 communautaire `fishaudio/drama-3-int4` (22 Go, complet) et poids FP8 officiels (36 Go sur 41,5, interrompu à la consigne) téléchargés dans `/run/media/pc1/Infrastructure/NexoraStudioWork/voix-bench/`. SGLang-Omni 0.5.23 installé sur pc1 (Python 3.12, torch 2.14.1+cu130, la 5090 est vue en sm_120). Le serveur n'a **pas démarré** : le module JIT `sgl_kernel_jit_gptq_marlin_repack` (sm120f) échoue à la compilation CUDA (glibc 2.43 de pc1, nvcc non installé sur le système ; le journal est `voix-bench/serve-int4.log`). Rien n'a été essayé sur la GB10 (aarch64, sm_121) ni sur vLLM-Omni. Le FP8 ne tient pas sur 32 Go ; l'int4 (20,8 Go de poids) tiendrait sur la 5090 si la compilation était résolue. Licence (fait, fiche HF) : « fish-audio-research-license » ; la fiche de l'int4 indique « fish-audio-community-license » ; l'usage commercial n'a pas été vérifié ici.
**Avis** : le modèle (35 B dont 3 B actifs, balises de direction, clonage, 80+ langues) est le plus intéressant du lot pour le ton Apple et coûte presque rien en API ; il n'y a aucune raison de le mettre en local avant d'avoir écouté les échantillons API. Les poids sont toujours sur pc1 (59 Go) : à supprimer si le fondateur ne les veut plus.

## 4. Autres moteurs de parole testés (OpenRouter, mêmes 4 textes)

Coût en USD pour les 3 passages. Les EMR sont dans l'INDEX.

| moteur | voix / option | coût | remarque mesurée |
|---|---|---|---|
| ElevenLabs v4 | Alexandre (ID Codex), Adam | 0,025 | référence de qualité (D) ; v3 aussi (EMR 0,08, « salon glais » pour « seul onglet ») |
| Fish S2.1 Pro | instructions, clonage Alexandre | 0,003 | EMR 0 ; supporte clonage et `instructions` |
| Fish S2 Pro | direction en crochets | 0,006 | EMR 0,03 |
| MiniMax Speech 2.8 HD | French_MaleNarrator, French_Male_Speech_New | 0,027 | pauses `<#0.9#>`, cadence lente 8,3 c/s ; EMR 0,05 et 0,10 |
| Gemini 3.8 flash TTS | Charon, Orus + `instructions` | < 0,01 | la consigne passée dans le texte était lue à voix haute (fichiers dans `ecartes/`) ; avec `instructions` c'est propre ; lent (≈ 9 c/s) |
| gpt-audio | cedar, marin, ash, ballad | 0,04 à 0,05 | via /chat/completions, consigne système ; EMR 0 à 0,03 |
| HeyGen Voice 1 | clonage Alexandre | 0,003 | EMR 0,03 ; pcm seulement |
| Seed Audio 1.0 | clonage Alexandre | non mesuré | tarif à la seconde générée, non relevé |
| MAI-Voice-2.1 | fr-FR-Marc | 0,005 | accent de France |
| Voxtral, Grok, Deepgram, AssemblyAI, Qwen TTS plus | un preset chacun | 0,003 à 0,006 | tous lisibles ; pas de voix québécoise |
| Chatterbox (pc5) | sans référence / avec Alexandre | 0 | **EMR 0,17 sans référence, le pire** (« Comme Nexora… ») |
| Kokoro (pc5) | ff_siwis | 0 | EMR 0,107 |

Dépense OpenRouter de ce banc : environ 0,8 USD (voix ≈ 0,4, Lyria 0,40), sous le plafond de 5 USD.

## 5. Musique

| source | brief | durée | BPM mesuré (demandé) | coût | temps |
|---|---|---|---|---|---|
| Lyria 3 Pro | (i) piano minimal | 61 s | 82,5 (90) | 0,08 | 17 s |
| Lyria 3 Pro | (ii) tech chaleureux | 64 s | 109 (110) | 0,08 | 25 s |
| Lyria 3 Pro | (iii) épique retenu | 58 s | 80 (80) | 0,08 | 33 s |
| Lyria 3 Clip | (i), (ii), (iii) | 29, 28, 31 s | 91, 109, 80 | 0,04 | 9 à 10 s |
| MiniMax Music 3 (GB10, base à 0,1/10) | (i), (ii), (iii) | 16, 20, 30 s | 82,5, 119, 119 | 0 | 45 à 70 s |

Constats : Lyria suit le BPM du brief et ses structures ; la longueur est imposée par le modèle (≈ 60 s pour Pro, 30 s pour Clip) : il faut couper et caler le moment fort au montage (colonne « 1er saut d'énergie » de l'INDEX). Music 3 a produit des morceaux plus courts que demandé, plus faibles en niveau, et un tempo peu fidèle sur (ii) et (iii). Aucun modèle ouvert supplémentaire (ACE-Step, YuE…) n'a été essayé : budget de jetons. Licences (faits) : Music 3 « MiniMax-Music3 Community », afficher « MiniMax-Music3 » ; Lyria : conditions Google via OpenRouter, non analysées ici.

## 6. Pipeline recommandé (provisoire, jusqu'à l'écoute)

Voix : 1) écouter d'abord Drama 3 (clone + direction), ElevenLabs Alexandre et H3 natif ; 2) générer **phrase par phrase** et poser les silences au montage (les pauses de 1 s des modèles ne sont pas fiables) ; 3) contrôle automatique Whisper (EMR et marque) puis loudnorm −14 LUFS ; 4) garder H3 natif seulement pour les plans où un visage doit parler, en lui donnant la voix choisie comme référence audio (`ref_audios`) ; 5) abandonner Chatterbox. Musique : Lyria 3 Pro par brief (0,08 USD), choisir la meilleure des trois, couper à la longueur du film, caler le « saut d'énergie » sur la coupe voulue, ducking sous la voix. Règle économique : tout le banc coûte moins de 2 USD, donc générer 3 prises par ligne et laisser l'oreille choisir.

## 7. Limites

Aucune écoute humaine ni de machine sur le timbre, l'accent et le naturel ; EMR et BPM sont des mesures de proxy. Les 4 passages sont courts (3 à 12 s) : la tenue sur 45 s d'une narration complète n'est pas testée. Les droits de la voix Alexandre servant de référence de clonage restent du ressort du fondateur.
