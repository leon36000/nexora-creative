# 21. Relief : banc comparatif des modèles 3D (04/11/2026)

Question du fondateur : « TRELLIS.2 est-il le meilleur ? ». Réponse courte : **oui, pour ce que nous pouvons faire tourner et licencier : on le garde** ; Pixal3D, seul concurrent qui a pu être mesuré, est plus lent, plus fragile en pose et moins bien noté sur 4 sujets sur 6. Le banc est honnête sur ses limites : un seul concurrent a tourné (§4).

## 1. Méthode

- **Six images** (`~/nexora-creative-data/relief-banc/images`, générées par Qwen-Image-2.1, objet seul sur fond clair) : chaise tressée, basket, robot-jouet en fer-blanc, vase émaillé bleu, figurine de guerrier sans détail de visage, pièce mécanique (engrenage sur palier).
- **Mêmes entrées, mêmes réglages** : détourage BiRefNet, `OBJECT_QUALITY.draft` (150 k faces, textures 2K) ou `quality` (400 k faces, 4K, normales et occlusion cuites), graine fixe.
- **Machines** : GB10 (DGX Spark, mémoire unifiée, partagée avec Qwen, Musique et d'autres agents pendant les mesures : les temps ont du bruit vers le haut) ; RTX 2080 SUPER (VM `nexora-gpu` de pc5, 8 Go de VRAM, 8 Go de RAM, 4 vCPU). La RTX 5090 de pc1 (production de films) n'a pas été utilisée.
- **Notes** : (a) juge vision de Relief (`juge3d`, `qwen/qwen3.8-27b` via OpenRouter, planche 2×2 de quatre côtés, `temperature 0`) ; (b) ma note sévère, donnée à la main d'après les planches (`marketing/creative/captures-v3/relief-*.jpg`). Le juge est indulgent : il note 7 à 8 presque tout ; il ne départage bien que les cas franchement cassés.

## 2. Résultats

Médianes sur les six sujets (minimum à maximum entre parenthèses).

| Configuration | Temps | VRAM pic | Triangles | GLB | Juge (moy. /10) | Ma note (moy. /10) |
|---|---|---|---|---|---|---|
| **TRELLIS.2 aperçu, GB10** | **46 s** (34 à 119) | mémoire unifiée | 150 k | 11,9 Mo | **7,8** | **6,9** |
| TRELLIS.2 qualité, GB10 | 189 s (143 à 572) | mémoire unifiée | 400 k | 47,1 Mo | 7,2 | 7,0 |
| TRELLIS.2 aperçu, RTX 2080 SUPER | 190 s (126 à 733) | 7,6 Go (plafond de la carte) | 150 k | 12,0 Mo | 7,5 | non revue une à une |
| Pixal3D aperçu, RTX 2080 SUPER | 196 s (104 à 423) | 7,6 Go (plafond) | 150 k | 12,1 Mo | 6,7 | 5,7 |

Détail par sujet (juge ; ma note) :

| Sujet | TRELLIS aperçu GB10 | TRELLIS qualité GB10 | TRELLIS aperçu 2080 S | Pixal3D aperçu 2080 S |
|---|---|---|---|---|
| Chaise | 8 ; 7,5 | 6 ; 7 | 8 | 5 ; 4,5 |
| Basket | 8 ; 6,5 | 8 ; 7 | 8 | 7 ; 6 |
| Robot | 8 ; 7,5 | 7 ; 8 | 7 | 8 ; 7 |
| Vase | 8 ; 7,5 | 8 ; 6 | 7 | 8 ; 5 |
| Figurine | 7 ; 5,5 | 7 ; 6 | 7 | 6 ; 6,5 |
| Pièce mécanique | 8 ; 7 | 7 ; 8 | 8 | 6 ; 5 |

Lectures :

1. **Le mode qualité ne bat pas l'aperçu au point de justifier 4× le temps sur tous les sujets** : meilleur sur le robot et la pièce (normales cuites, détails), pire sur le vase (texture striée) et la chaise (traînées sous l'assise). C'est un choix « pour le gardien », pas un mode « toujours meilleur ».
2. **Temps très inégaux selon le sujet** : vase et pièce coûtent 112 à 119 s en aperçu sur la GB10 (contre 34 à 47 s) et 730 s sur la 2080 SUPER : l'étage de remaillage et de cuisson de texture (processeur) dépend de la géométrie, et sur 8 Go de VRAM le modèle déborde. Ce sont les **médianes** qui servent aux devis et au routage (`MESURES_OBJET_GB10`, `NEXORA_MOTEUR_SECONDES`), non le meilleur cas (38 s sur une chaise, GB10 au repos).
3. **Pixal3D rend le maillage dans le repère de la caméra, pas debout** : vase et chaise penchés, pièce tournée et petite sur la planche (`relief-pixal3d-draft-2080s-0*.jpg`). C'est son principe (alignement pixel à pixel avec l'image) ; pour un actif que l'on pose dans une scène ou imprime, il faudrait le redresser. TRELLIS.2 rend un objet debout et centré. Pixal3D est meilleur sur la figurine (armure plus nette, cape de dos), pire ailleurs ; chaise : pieds tordus (5/10).
4. **Variabilité de graine** : la même chaise passe de 8/10 (graine du banc) à 5/10 (graine de l'application, take 14, 2080 SUPER, 183 s). C'est la justification de la relance automatique du juge (§5), pas un défaut du moteur.

## 3. Multi-images (Pixal3D multi-vues), mesuré dans l'application

Boucle fermée : quatre rendus d'un robot TRELLIS (images 0, 8, 16, 24 de sa tournette de 32) fournis comme face, gauche, dos, droite.

| Vues fournies | Résultat | Temps (2080 SUPER) |
|---|---|---|
| face + dos | modèle debout, dos cohérent (`relief-multivues-pixal3d-robot-face-dos.jpg`) | 204 s |
| face + gauche + dos | terminé | 195 s |
| face + gauche + dos + droite | **ComfyUI tué par le noyau (mémoire), 3 essais** | n/a |

La VM de 8 Go de RAM tient 3 vues au plus ; le serveur refuse la quatrième avec un message clair (`NEXORA_RELIEF_VUES_MAX`, défaut 3). Quatre vues demandent de doter la VM de 16 Go de RAM (l'hôte en a 62, 30 engagés) : décision du fondateur. Le modèle multi-vues (`pixal3d_multiview_int8_convrot`, 5,58 Go) a remplacé le modèle mono-vue (même taille) sur le disque de la VM.

## 4. Ce qui n'a pas pu être comparé, et pourquoi

| Candidat | Licence | Poids | Verdict |
|---|---|---|---|
| TripoSG (VAST-AI) | MIT | 7,95 Go en fp32 (transformeur 5,76 + VAE 0,97 + DINOv2 1,22), **forme seule, sans texture** | non lancé : plus que les 6 Go du lot, disque de la VM pc5 plein (4 Go libres), disque de pc6 à 99 % ; le script de banc est prêt (`~/nexora-creative-data/relief-banc/outils/triposg_banc.py`, dépôt cloné sur la VM) |
| Step1X-3D (StepFun) | Apache-2.0 (texture : OpenRAIL++) | 19,6 Go (forme 7,3 + texture 3,6 + variantes) | hors budget |
| Direct3D-S2 | MIT | 3,1 Go à 512³ (1,5 + 1,1 + 0,3) | non lancé : noyaux de convolution creuse à compiler, pas de `nvcc` sur la VM Turing |
| Hunyuan3D 2.0 / 2.1 / Omni | licence « autre » : exclue par territoire | n/a | **écarté, noté seulement** (recherche/18) |
| SAM 3D Objects (Meta) | licence « autre » | gros | non évalué |
| Nouveautés 2026 vues sur HF (TripoSplat, 3D-Fixer, idol) | MIT / Apache | n/a | splats ou scènes, pas image → objet texturé : hors sujet |

**Conclusion honnête** : le banc ne prouve pas que TRELLIS.2 bat tout ; il prouve qu'il bat le seul concurrent permissif que nous avons pu faire tourner, avec le meilleur temps (46 s sur GB10) et le seul rendu « debout ». Le prochain pas utile serait TripoSG (forme) combiné à une retexture, une fois du disque libéré.

## 5. Juge et relance

- `juge3d` : planche 2×2 de quatre images régulièrement espacées de la tournette ; note 0 à 10, défauts, une phrase. Jetons mesurés à chaque appel : **≈ 2 200 jetons (1 220 d'image et de consigne, 700 à 1 400 de réponse), ≈ 0,002 USD, ≈ 0,3 crédit** ; 29 planches du banc : 71 553 jetons, 0,07 USD. Facturé comme les appels du Producteur : réservation au plafond du devis, règlement du réel, ligne `juge3d` au grand livre.
- **Texte → 3D, de bout en bout dans l'application** (« lampe de bureau articulée en laiton brossé, abat-jour vert émeraude ») : image de référence, modèle, juge 5/10, relance automatique avec une autre graine, juge 5/10, garde la meilleure. La relance ne change que la graine du modèle : ici le défaut vient de l'image de référence (lampe non articulée), qu'il faudrait aussi refaire.
- Image → 3D : note à la demande (bouton « Faire juger sur quatre côtés »), pas de relance automatique.

## 6. Reproduire

`~/nexora-creative-data/relief-banc/` : `images/`, `glb/`, `runs/*.json` (mesures), `juge-qwen38.jsonl` (notes), `outils/` (`run_graph.py`, `banc-pc5.sh`, `planches.sh`, `agrege.py`). Juge : `app/scripts/relief-juge.ts`. Planches : `app/scripts/planche-3d.mjs`.
