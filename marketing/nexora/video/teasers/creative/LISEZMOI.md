# Teaser Nexora Creative (15 s)

Teaser de lancement de **Nexora Creative** (fr-CA) / **Nexora Creative** (en-CA). État affiché sur la carte de fin : **PLUS TARD** / LATER (Plus tard au registre du site : `web/src/i18n/apps.ts` et `product-family.tsx`). Rien de plus que l'état réel n'est annoncé.

## Fichiers
| Fichier | Durée | Format | Niveau |
|---|---|---|---|
| `final/teaser-creative-en-CA-1x1.mp4` | 15.00 s | 1080×1080 | -13.6 LUFS |
| `final/teaser-creative-en-CA-9x16.mp4` | 15.00 s | 1080×1920 | -13.6 LUFS |
| `final/teaser-creative-fr-CA-1x1.mp4` | 15.00 s | 1080×1080 | -13.6 LUFS |
| `final/teaser-creative-fr-CA-9x16.mp4` | 15.00 s | 1080×1920 | -13.6 LUFS |

Les versions fr-CA et en-CA ont exactement les mêmes images ; seuls les textes changent. La version 1:1 est un recadrage centré du 9:16 (le texte est replacé pour le carré).

## Montage
- Plan 1 (0 → 2.47 s) : métaphore du rêve de l'outil, texte « Une image naît. » / « An image is born. ».
- Plan 2 (2.47 → 5.54 s) : texte « Elle devient film. » / « It becomes a film. ».
- Plan 3 (5.54 → 9.84 s, la respiration) : signature de campagne « Rêvez grand. Gardez le contrôle. » / « Dream big. Stay in control. » (en haut du cadre, sur fond assombri pour le contraste).
- Carte de fin (9.84 → 15 s) : symbole officiel qui s'allume (la diagonale en dernier, tintement cristallin), nom exact « Nexora Creative », accroche du site « Image, son et vidéo » / « Image, sound and video », état, ligne « IA souveraine au Québec ».
- Coupes recalées sur les temps de la musique (≈ 98 BPM détectés). Zone de sécurité des plateformes : aucun texte dans les 250 px du haut ni les 380 px du bas.
- Plans H3 retenus (v1/v2 comparées image par image) : p1 = v3, p2 = v1, p3 = v1 ; p1 = lecture inversée de v1 (l'image « se développe »).

## Régénérer
Plans et musique dans `../../sources/teasers/creative/` et `../../sources/teasers/musique/creative.flac` (générés par `lancer-teasers.py` et `lancer-musiques.py`).
```
python3 ../../sources/teasers/outils/teasers.py creative            # 4 fichiers : fr-CA et en-CA, 9:16 et 1:1
python3 ../../sources/teasers/outils/teasers.py creative --rapide   # aperçu 540p pour juger le rythme
```
Le montage JSON de chaque version est dans `sources/montage-*.json` (moteur : `video/outils/film.py`).
