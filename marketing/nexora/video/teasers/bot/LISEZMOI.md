# Teaser Nexora Bot (15 s)

Teaser de lancement de **Nexora Bot** (fr-CA) / **Nexora Bot** (en-CA). État affiché sur la carte de fin : **BIENTÔT** / SOON (Bientôt au registre du site : `web/src/i18n/apps.ts` et `product-family.tsx`). Rien de plus que l'état réel n'est annoncé.

## Fichiers
| Fichier | Durée | Format | Niveau |
|---|---|---|---|
| `final/teaser-bot-en-CA-1x1.mp4` | 15.00 s | 1080×1080 | -13.9 LUFS |
| `final/teaser-bot-en-CA-9x16.mp4` | 15.00 s | 1080×1920 | -13.9 LUFS |
| `final/teaser-bot-fr-CA-1x1.mp4` | 15.00 s | 1080×1080 | -13.9 LUFS |
| `final/teaser-bot-fr-CA-9x16.mp4` | 15.00 s | 1080×1920 | -13.9 LUFS |

Les versions fr-CA et en-CA ont exactement les mêmes images ; seuls les textes changent. La version 1:1 est un recadrage centré du 9:16 (le texte est replacé pour le carré).

## Montage
- Plan 1 (0 → 2.58 s) : métaphore du rêve de l'outil, texte « Jamais seul
sur le chemin. » / « Never alone
on the road. ».
- Plan 2 (2.58 → 5.58 s) : texte « Un compagnon qui éclaire. » / « A companion that lights the way. ».
- Plan 3 (5.58 → 10.08 s, la respiration) : signature de campagne « Rêvez grand. Gardez le contrôle. » / « Dream big. Stay in control. » (en haut du cadre, sur fond assombri pour le contraste).
- Carte de fin (10.08 → 15 s) : symbole officiel qui s'allume (la diagonale en dernier, tintement cristallin), nom exact « Nexora Bot », accroche du site « Un bot relié à votre compte » / « A bot tied to your account », état, ligne « IA souveraine au Québec ».
- Coupes recalées sur les temps de la musique (≈ 80 BPM détectés). Zone de sécurité des plateformes : aucun texte dans les 250 px du haut ni les 380 px du bas.
- Plans H3 retenus (v1/v2 comparées image par image) : p1 = v1, p2 = v2, p3 = v1.

## Régénérer
Plans et musique dans `../../sources/teasers/bot/` et `../../sources/teasers/musique/bot.flac` (générés par `lancer-teasers.py` et `lancer-musiques.py`).
```
python3 ../../sources/teasers/outils/teasers.py bot            # 4 fichiers : fr-CA et en-CA, 9:16 et 1:1
python3 ../../sources/teasers/outils/teasers.py bot --rapide   # aperçu 540p pour juger le rythme
```
Le montage JSON de chaque version est dans `sources/montage-*.json` (moteur : `video/outils/film.py`).
