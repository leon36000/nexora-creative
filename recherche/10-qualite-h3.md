# 10 — Banc qualité MiniMax H3 sur deux GPU (31/10/2026)

Décision du fondateur du 31/10 : **MiniMax H3 seul** (Wan 2.2 retiré), qualité maximale, et deux moteurs pour les
essais : le DGX Spark GB10 de pc6 et la RTX 5090 de pc1 (où H3 était déjà installé). Ce banc a servi à choisir les
réglages du studio et à tourner la vidéo promotionnelle.

## Ce qu'il y a sur chaque machine

| Machine | Point de contrôle H3 | Famille | Remarque |
|---|---|---|---|
| pc6, GB10 (128 Go unifiés) | `fastvideo_fasth3_8step_v2_pruned_nvfp4` | FL2VA distillé 8 étapes (DMD2) | le moteur « rapide » du studio |
| pc1, RTX 5090 (32 Go) | `minimax_h3_fl2va_pruned_int8_convrot` | FL2VA officiel complet (Comfy-Org) | texte, première et dernière image |
| pc1 | `minimax_h3_ref2va_pruned_bf16` et `_int8_convrot` | Ref2VA officiel | images, vidéos et sons de référence (personnages constants) |
| pc1 | `Minimax-h3_Singularity_ref2va_v2_pruned_int8` | réglage fin communautaire (WarmBloodAban) | action, arts martiaux, effets ; la page dit Apache-2.0, mais c'est un dérivé de H3 : **licence H3** (I.11) |
| pc1 | `minimax_h3_ref2v_turbo_8step_v1.0/1.1_768p` | LoRA turbo Ref2V | non mesurés ici |

Le ComfyUI de pc1 (v0.43.0, port 18288) appartient à une autre session de travail. Nexora Creative s'en sert sans le
modifier, par un tunnel SSH en boucle locale (`~/nexora-creative-data/engine/tunnel-pc1.sh`, port 37288 de pc6). Les
modèles MiniMax Music 3 y ont été ajoutés (dossiers `diffusion_models`, `text_encoders`, `vae`, 12 Go).

## Mesures (1344×768, 124 images = 5,17 s, son stéréo)

| Moteur | Point de contrôle | Étapes | Temps moteur | Constat visuel (planches de 4 à 6 images) |
|---|---|---|---|---|
| RTX 5090 | FL2VA officiel int8 | 24 | **290 s** (dragon), 295-296 s (plans promo) | photoréaliste, très détaillé ; meilleur sur les humains |
| RTX 5090 | Singularity V2 int8 (nœud de référence sans image) | 24 | **292 s** (dragon), 290 s (karaté) | dragon très « bande-annonce », identité stable ; humains trop « jeu vidéo » (rendu 3D, visages moyens) |
| GB10 | FastH3 V2 NVFP4 | 8 | **344-353 s** | presque au niveau du modèle complet, un peu plus saturé |

Toutes mesures [MESURÉ] par `app/scripts/nexora-rendu.ts`, journaux dans `~/nexora-creative-data/promo/`.

Leçons :

1. **Les deux moteurs peuvent tourner les plans d'un même film** sans écart visible : le studio répartit les plans.
2. **« Cinematic CG » dans un prompt pousse H3 vers l'image de synthèse.** Pour des humains : « live-action, large-format
   cinema camera, real actors, photorealistic skin and fabric ». Pour créatures, vaisseaux, robots : « photorealistic
   cinematic CG » convient.
3. Le réécrivain LLM a laissé passer une note parasite (« (S1 is not applicable) »), un sujet renommé (« airships ») et
   deux mots français (« combattante », « retour ») : les deux premiers défauts sont désormais refusés par le code
   (`remarquesParasites`, consignes) ; les mots français restent à surveiller.
4. Singularity est un bon choix pour les plans d'action non humains ; le studio garde H3 officiel par défaut pour la
   recette « cinéma » (`NEXORA_H3_MAX_CHECKPOINT`).

## Musique : MiniMax Music 3

Modèle ouvert de MiniMax (licence « MiniMax-Music3 Community » : **aucune exclusion de territoire**, mention
« MiniMax-Music3 » dans l'interface, seuil de 20 M$ de revenus, garde-fous contre les usages contraires). Versions
ComfyUI de Comfy-Org : DiT int8 2,5 Go, encodeur texte élagué int8 9,2 Go, VAE 0,2 Go.

| Essai | Temps | Constat |
|---|---|---|
| 60-62 s de musique de bande-annonce, RTX 5090 | **27 s** de calcul (le reste des temps notés est l'attente en file derrière la vidéo) | style respecté (orchestral hybride, taikos, chœur) ; **le minutage demandé n'est pas suivi à la seconde** : on choisit la candidate dont la structure convient (analyse d'énergie) et on monte l'image sur ses temps forts |

Outils : `marketing/creative/outils/analyser_musique.py` (courbe d'énergie), `tempo.py` (tempo, attaques fortes).
