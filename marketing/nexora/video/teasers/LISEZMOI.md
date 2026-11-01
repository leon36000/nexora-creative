# Teasers, stings et boucles du lancement de Nexora AI

Planche-contact : `apercu.png`. Tout est fabriqué avec nos outils (plans MiniMax H3 en mode rapide, musique MiniMax-Music3, bruitages et son signature synthétisés) et du code ; le texte et le logo sont toujours posés en code.

## Contenu
| Dossier | Quoi | Fichiers |
|---|---|---|
| `workstudio/` `code/` `rag/` `bot/` `creative/` `webpilot/` `privacy-router/` `vps/` | un teaser de 15 s par outil, 9:16 (1080×1920) et 1:1 (1080×1080), fr-CA et en-CA, H.264, AAC, −14 LUFS | `final/teaser-<outil>-<fr-CA|en-CA>-<9x16|1x1>.mp4` (4 par outil, 32 en tout), `LISEZMOI.md`, `sources/` (montages JSON, cartes de fin, tintement) |
| `stings/` | stings 4,6 s (16:9, 9:16, 1:1 × fr/en), son signature WAV, barres inférieures ProRes 4444 alpha, transitions de 1 s avec et sans alpha | voir `stings/LISEZMOI.md` |
| `boucles/` | boucle d'aurore de 20 s (16:9 et 9:16), trois ambiances de 12 s, avec et sans petit symbole | voir `boucles/LISEZMOI.md` |

## Structure d'un teaser (15 s)
Trois plans H3 (métaphore visuelle jamais littérale, deux variantes générées par plan, la meilleure retenue après lecture d'images extraites), un texte court par plan en Geist (3 à 6 mots), la signature de campagne « Rêvez grand. Gardez le contrôle. » / « Dream big. Stay in control. » sur le plan de respiration, puis la carte de fin : symbole officiel, nom exact, accroche du site (`family.items[*].tag`), **état honnête** (WorkStudio : Disponible ; Creative : **Plus tard** ; Code, RAG, Bot, WebPilot, Privacy Router, VPS : **Bientôt**, d'après `apps.ts` et `product-family.tsx`), ligne « IA souveraine au Québec ». Zones de sécurité : texte hors des 250 px du haut et des 380 px du bas. Un dégradé noir discret sous les textes garantit le contraste. Les coupes tombent sur les temps de la musique de chaque pièce (tempo détecté par `rythme.py`).

| Outil | Métaphore (plans retenus) | Texte fr-CA |
|---|---|---|
| Nexora WorkStudio | carrés de lumière qui s'assemblent sur un établi d'atelier | Des tâches éparpillées. / Des agents qui les assemblent. |
| Nexora Code | forgeron de lumière, escalier de carrés vers une porte | Chaque ligne se forge. / Marche après marche. |
| Nexora RAG | bibliothèque nocturne immense, une reliure s'allume, un livre s'ouvre | Tout ce que vous savez. / Une réponse s’allume. |
| Nexora Bot | un petit cube de lumière accompagne un marcheur dans la neige | Jamais seul sur le chemin. / Un compagnon qui éclaire. |
| Nexora Creative | une image de braise qui se développe, puis devient film | Une image naît. / Elle devient film. |
| Nexora WebPilot | une lanterne trace un chemin de carrés dans un champ de lumière | Un immense champ de pages. / Une lanterne trace la route. |
| Privacy Router | village sous un dôme de verre chaud pendant la tempête | Dehors, la tempête. / Vos données, à l’abri. |
| VPS au Québec | chalet aux fenêtres carrées orange, la vue s'élève sur la nuit québécoise | Un serveur bien à vous. / Ici, au Québec. |

Aucun chiffre, prix, date, statistique ni certification dans les textes ; aucun texte dans les images générées.

## Régénérer
Tous les scripts sont dans `../sources/teasers/outils/` ; les plans, la musique et les prompts dans `../sources/teasers/` (`plans-teasers.json`, `lancer-teasers.py`, `lancer-musiques.py`, `choix.json` pour le choix des variantes).
```
cd "…/video/sources/teasers/outils"
python3 teasers.py tous                    # les 8 teasers (32 fichiers) ; --langs fr --formats 9:16 pour une partie ; --rapide pour un aperçu 540p
python3 fabriquer_stings.py                # stings, son, barres, transitions
python3 fabriquer_boucles.py               # boucles et ambiances
python3 apercu.py                          # planche-contact apercu.png
python3 verifier_tout.py                   # durée, audio, niveau de tous les fichiers
python3 ecrire_lisezmoi.py                 # LISEZMOI des teasers
```
Pour changer un plan : générer une autre variante (`lancer-teasers.py`), l'indiquer dans `choix.json`, relancer `teasers.py <outil>`. Pour changer un texte : `outils/contenu.py`. Pour changer un état (Bientôt → Disponible) : `ETATS` et `TEASERS` dans le même fichier, après le registre du site.
