# Teaser Nexora WorkStudio (15 s)

Teaser de lancement de **Nexora WorkStudio** (fr-CA) / **Nexora WorkStudio** (en-CA). État affiché sur la carte de fin : **DISPONIBLE** / AVAILABLE (Disponible au registre du site : `web/src/i18n/apps.ts` et `product-family.tsx`). Rien de plus que l'état réel n'est annoncé.

## Fichiers
| Fichier | Durée | Format | Niveau |
|---|---|---|---|
| `final/teaser-workstudio-en-CA-1x1.mp4` | 15.00 s | 1080×1080 | -14.0 LUFS |
| `final/teaser-workstudio-en-CA-9x16.mp4` | 15.00 s | 1080×1920 | -14.0 LUFS |
| `final/teaser-workstudio-fr-CA-1x1.mp4` | 15.00 s | 1080×1080 | -14.0 LUFS |
| `final/teaser-workstudio-fr-CA-9x16.mp4` | 15.00 s | 1080×1920 | -14.0 LUFS |

Les versions fr-CA et en-CA ont exactement les mêmes images ; seuls les textes changent. La version 1:1 est un recadrage centré du 9:16 (le texte est replacé pour le carré).

## Montage
- Plan 1 (0 → 2.64 s) : métaphore du rêve de l'outil, texte « Des tâches éparpillées. » / « Scattered tasks. ».
- Plan 2 (2.64 → 5.51 s) : texte « Des agents qui les assemblent. » / « Agents that assemble them. ».
- Plan 3 (5.51 → 9.81 s, la respiration) : signature de campagne « Rêvez grand. Gardez le contrôle. » / « Dream big. Stay in control. » (en haut du cadre, sur fond assombri pour le contraste).
- Carte de fin (9.81 → 15 s) : symbole officiel qui s'allume (la diagonale en dernier, tintement cristallin), nom exact « Nexora WorkStudio », accroche du site « Agents et flux de travaux » / « Agents and workflows », état, ligne « IA souveraine au Québec ».
- Coupes recalées sur les temps de la musique (≈ 84 BPM détectés). Zone de sécurité des plateformes : aucun texte dans les 250 px du haut ni les 380 px du bas.
- Plans H3 retenus (v1/v2 comparées image par image) : p1 = v1, p2 = v2, p3 = v1.

## Régénérer
Plans et musique dans `../../sources/teasers/workstudio/` et `../../sources/teasers/musique/workstudio.flac` (générés par `lancer-teasers.py` et `lancer-musiques.py`).
```
python3 ../../sources/teasers/outils/teasers.py workstudio            # 4 fichiers : fr-CA et en-CA, 9:16 et 1:1
python3 ../../sources/teasers/outils/teasers.py workstudio --rapide   # aperçu 540p pour juger le rythme
```
Le montage JSON de chaque version est dans `sources/montage-*.json` (moteur : `video/outils/film.py`).
