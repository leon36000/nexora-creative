# Boucles et ambiances (sans texte ni logo)

Fonds propres pour la vidéo de couverture Facebook, l'arrière-plan du site et les stories. Chaque boucle existe sans marque et avec le petit symbole officiel **blanc** (SVG monochrome blanc, jamais le symbole en couleur sur une image chargée) discret en coin bas droit, à 72 % d'opacité. **Pas de piste audio** (fonds à lire en sourdine).

## Fichiers (`final/`)
| Fichier | Durée | Format |
|---|---|---|
| `boucle-aurore-16x9-20s.mp4` (+ `-symbole`) | 20,00 s | 1920×1080 : aurore braise sur forêt enneigée, carrés qui montent. Couverture Facebook / fond de site. |
| `boucle-aurore-9x16-20s.mp4` (+ `-symbole`) | 20,00 s | 1080×1920 : version stories (symbole au-dessus des 380 px du bas). |
| `ambiance-ville-16x9-12s.mp4` (+ `-symbole`) | 12,00 s | village québécois au crépuscule, fenêtres orange. |
| `ambiance-fleuve-16x9-12s.mp4` (+ `-symbole`) | 12,00 s | fleuve à l'aube, brume, quelques carrés orange sur l'eau. |
| `ambiance-atelier-16x9-12s.mp4` (+ `-symbole`) | 12,00 s | atelier chaud à la lanterne, poussières dorées. |

## Comment la boucle est faite (et vérifiée)
Des plans H3 de 10 s (2 à 3 par boucle) sont enchaînés par des fondus de 2 à 2,5 s **circulaires** : le dernier plan se fond dans le premier, de sorte que l'image qui suivrait la dernière image est exactement la première (`O(L) = S(L) = O(0)`, voir l'en-tête de `outils/boucles.py`). Contrôle avec `outils/verifier_boucle.py` : la différence moyenne entre la dernière et la première image est du même ordre que celle de deux images consécutives ordinaires (aurore 16:9 : 1,36 pour une médiane de 0,53 et un p95 de 1,91 ; 9:16 : 0,72 / 0,65 ; ville : 0,25 / 0,22 ; fleuve : 0,44 / 0,42 ; atelier : 0,25 / 0,22) : la jonction est invisible. Les plans ont été contrôlés un par un avec `outils/coupes.py` (un plan H3 qui change de scène en cours de route est rejeté : `aurore-169-2` a une coupe brutale à 6,7 s, remplacé par `aurore-169-4` et `-5`).

Limites : les fondus entre deux plans différents laissent une brève double exposition (volontaire, c'est une ambiance) ; la vignette des plans « fleuve » vient en partie du plan généré. Pour la couverture Facebook, le cadrage 16:9 est recadré par l'interface (surtout sur mobile) : garder le sujet au centre et vérifier l'aperçu au dépôt.

## Régénérer
Plans bruts : `../../sources/teasers/boucles/*.mp4` (générés par `lancer-teasers.py boucles` et `extras`, prompts dans `plans-teasers.json`).
```
python3 ../../sources/teasers/outils/fabriquer_boucles.py                       # tout
python3 ../../sources/teasers/outils/fabriquer_boucles.py ambiance-ville-16x9-12s  # une seule
```
Le choix et l'ordre des plans de chaque boucle sont dans le tableau `CHOIX` de `fabriquer_boucles.py`.
