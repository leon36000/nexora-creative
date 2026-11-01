# Teaser Nexora RAG (15 s)

Teaser de lancement de **Nexora RAG** (fr-CA) / **Nexora RAG** (en-CA). État affiché sur la carte de fin : **BIENTÔT** / SOON (Bientôt au registre du site : `web/src/i18n/apps.ts` et `product-family.tsx`). Rien de plus que l'état réel n'est annoncé.

## Fichiers
| Fichier | Durée | Format | Niveau |
|---|---|---|---|
| `final/teaser-rag-en-CA-1x1.mp4` | 15.00 s | 1080×1080 | -14.0 LUFS |
| `final/teaser-rag-en-CA-9x16.mp4` | 15.00 s | 1080×1920 | -14.0 LUFS |
| `final/teaser-rag-fr-CA-1x1.mp4` | 15.00 s | 1080×1080 | -14.0 LUFS |
| `final/teaser-rag-fr-CA-9x16.mp4` | 15.00 s | 1080×1920 | -14.0 LUFS |

Les versions fr-CA et en-CA ont exactement les mêmes images ; seuls les textes changent. La version 1:1 est un recadrage centré du 9:16 (le texte est replacé pour le carré).

## Montage
- Plan 1 (0 → 2.99 s) : métaphore du rêve de l'outil, texte « Tout ce que vous savez. » / « Everything you know. ».
- Plan 2 (2.99 → 5.19 s) : texte « Une réponse s’allume. » / « One answer lights up. ».
- Plan 3 (5.19 → 10.32 s, la respiration) : signature de campagne « Rêvez grand. Gardez le contrôle. » / « Dream big. Stay in control. » (en haut du cadre, sur fond assombri pour le contraste).
- Carte de fin (10.32 → 15 s) : symbole officiel qui s'allume (la diagonale en dernier, tintement cristallin), nom exact « Nexora RAG », accroche du site « Vos documents, interrogeables » / « Your documents, searchable », état, ligne « IA souveraine au Québec ».
- Coupes recalées sur les temps de la musique (≈ 82 BPM détectés). Zone de sécurité des plateformes : aucun texte dans les 250 px du haut ni les 380 px du bas.
- Plans H3 retenus (v1/v2 comparées image par image) : p1 = v1, p2 = v1, p3 = v1.

## Régénérer
Plans et musique dans `../../sources/teasers/rag/` et `../../sources/teasers/musique/rag.flac` (générés par `lancer-teasers.py` et `lancer-musiques.py`).
```
python3 ../../sources/teasers/outils/teasers.py rag            # 4 fichiers : fr-CA et en-CA, 9:16 et 1:1
python3 ../../sources/teasers/outils/teasers.py rag --rapide   # aperçu 540p pour juger le rythme
```
Le montage JSON de chaque version est dans `sources/montage-*.json` (moteur : `video/outils/film.py`).
