# Teaser Nexora WebPilot (15 s)

Teaser de lancement de **Nexora WebPilot** (fr-CA) / **Nexora WebPilot** (en-CA). État affiché sur la carte de fin : **BIENTÔT** / SOON (Bientôt au registre du site : `web/src/i18n/apps.ts` et `product-family.tsx`). Rien de plus que l'état réel n'est annoncé.

## Fichiers
| Fichier | Durée | Format | Niveau |
|---|---|---|---|
| `final/teaser-webpilot-en-CA-1x1.mp4` | 15.00 s | 1080×1080 | -14.1 LUFS |
| `final/teaser-webpilot-en-CA-9x16.mp4` | 15.00 s | 1080×1920 | -14.1 LUFS |
| `final/teaser-webpilot-fr-CA-1x1.mp4` | 15.00 s | 1080×1080 | -14.1 LUFS |
| `final/teaser-webpilot-fr-CA-9x16.mp4` | 15.00 s | 1080×1920 | -14.1 LUFS |

Les versions fr-CA et en-CA ont exactement les mêmes images ; seuls les textes changent. La version 1:1 est un recadrage centré du 9:16 (le texte est replacé pour le carré).

## Montage
- Plan 1 (0 → 2.80 s) : métaphore du rêve de l'outil, texte « Un immense
champ de pages. » / « A vast
field of pages. ».
- Plan 2 (2.80 → 5.60 s) : texte « Une lanterne trace la route. » / « A lantern marks the way. ».
- Plan 3 (5.60 → 9.79 s, la respiration) : signature de campagne « Rêvez grand. Gardez le contrôle. » / « Dream big. Stay in control. » (en haut du cadre, sur fond assombri pour le contraste).
- Carte de fin (9.79 → 15 s) : symbole officiel qui s'allume (la diagonale en dernier, tintement cristallin), nom exact « Nexora WebPilot », accroche du site « Recherche et navigation Web » / « Web search and browsing », état, ligne « IA souveraine au Québec ».
- Coupes recalées sur les temps de la musique (≈ 86 BPM détectés). Zone de sécurité des plateformes : aucun texte dans les 250 px du haut ni les 380 px du bas.
- Plans H3 retenus (v1/v2 comparées image par image) : p1 = v2, p2 = v1, p3 = v2.

## Régénérer
Plans et musique dans `../../sources/teasers/webpilot/` et `../../sources/teasers/musique/webpilot.flac` (générés par `lancer-teasers.py` et `lancer-musiques.py`).
```
python3 ../../sources/teasers/outils/teasers.py webpilot            # 4 fichiers : fr-CA et en-CA, 9:16 et 1:1
python3 ../../sources/teasers/outils/teasers.py webpilot --rapide   # aperçu 540p pour juger le rythme
```
Le montage JSON de chaque version est dans `sources/montage-*.json` (moteur : `video/outils/film.py`).
