# Preuve du moteur V6

Quatre essais de 12,00 s / 288 images à 24 i/s sont conservés dans `.cache/essais/` (ignoré par git).
Les deux sorties paysage sont en 1920×1080 ; les portraits sont en brouillon 540×960.
Tous sont H.264 High, CRF 16, yuv420p, AAC 320 kbit/s demandé, avec `moov` avant `mdat` (`+faststart`).

| Sortie | Temps CPU mural | Secondes de calcul / seconde de film | LUFS intégrés du MP4 | Crête vraie |
|---|---:|---:|---:|---:|
| `essai-16x9-en.mp4` | 42.471 s | 3.539 | -14.05 | -1.68 dBTP |
| `essai-16x9-fr.mp4` | 42.125 s | 3.510 | -14.05 | -1.68 dBTP |
| `essai-9x16-en.mp4` | 16.116 s | 1.343 | -14.05 | -1.68 dBTP |
| `essai-9x16-fr.mp4` | 16.748 s | 1.396 | -14.05 | -1.68 dBTP |

Rendus séquentiels, trois processus de segment et deux threads x264 par segment. Les temps comprennent le mixage, le mastering et la mesure AAC ; aucun segment de ces rendus ne provenait du cache.

Chaîne essayée : saisie réelle s01 → boost du texte réel → titre claque → 765 avec rampe de vitesse, secousse et son natif retimé → chapitre → balayage du 765 désaturé vers le même 765 en couleur → carton de marque.

Un export supplémentaire anglais de 8 s, `--de 0.25 --a 8.25 --master reseaux`, a aussi couvert mosaïque, titre empilé, titre sur vidéo, marche arrière, chapitre MP4, chapitre à captures, badge et trois couches avec damier. Résultat final : **−10,10 LUFS / −1,42 dBTP**. Son rapport est conservé dans `.cache/essais/verification-reseaux-plage.json` ; le MP4 de ce contrôle est temporaire et nettoyé.

Les mesures détaillées et les commandes réellement exécutées sont dans les `*.rendu.json`. `verification-sorties.json` confirme les dimensions, 288 images, les codecs et `+faststart`. Les planches `planche-*.jpg` montrent une image par seconde ; `details-boost-fr.jpg` détaille le jaillissement entre 2,20 et 2,80 s.

## Commandes de reproduction

Depuis la racine du dépôt, commandes utilisées pour les essais français :

```bash
python3 -B marketing/creative/video-v6/monter_v6.py marketing/creative/video-v6/montage-essai.json --format 16x9 --langue fr --sortie marketing/creative/video-v6/.cache/essais/essai-16x9-fr.mp4 --master web --jobs 3
python3 -B marketing/creative/video-v6/monter_v6.py marketing/creative/video-v6/montage-essai.json --format 9x16 --langue fr --sortie marketing/creative/video-v6/.cache/essais/essai-9x16-fr.mp4 --master web --jobs 3 --brouillon
python3 -B marketing/creative/video-v6/planche_v6.py marketing/creative/video-v6/.cache/essais/essai-16x9-fr.mp4 marketing/creative/video-v6/.cache/essais/planche-16x9-fr.jpg
python3 -B marketing/creative/video-v6/planche_v6.py marketing/creative/video-v6/.cache/essais/essai-9x16-fr.mp4 marketing/creative/video-v6/.cache/essais/planche-9x16-fr.jpg
```

Les sorties anglaises utilisent les mêmes commandes, avec `--langue en` et les suffixes `-en` pour les MP4/JPG. Pour le portrait définitif 1080×1920, enlever `--brouillon`.

```bash
python3 -B marketing/creative/video-v6/test_monter_v6.py
```

La suite couvre les horloges image/audio, les coupes, le ducking et les fondus, les neuf types de segment dans les deux langues/formats, les marges du titre à quatre mots pendant la claque, et un vrai export partiel avec mastering réseaux et contrôle AAC.

## Limites à juger au montage

- Ralenti par répétition des images à 24 i/s ; le son retimé change aussi de hauteur.
- Profondeur, traînées et aspiration du boost sont des simulations 2D. Les vagues se chevauchent pour faire jaillir le prompt complet dans environ une seconde.
- Les textes de marque et les voix sont sélectionnés par langue. Les captures et le prompt source s01 restent français dans ces essais anglais.
- Le pipeline de voix est testé sur son horloge et son ducking ; aucune voix de narration n’est incluse dans cet essai qui utilise seulement les médias du brief.

Les segments encodés, WAV et fichiers de contrôle temporaires sont nettoyés après vérification. Les quatre MP4, planches et rapports d’essai restent disponibles. Aucun rendu GPU, aucun service modifié et aucun commit.
