# Diagnostic et reconstruction CPU — laboratoire

Cet outil produit un diagnostic géométrique et, facultativement, un STL dérivé expérimental. Il ne modifie pas le GLB ni les tableaux source. Il ne conserve pas les UV ou textures dans le STL et ne qualifie pas le modèle pour l’impression. Le diagnostic ne détecte pas les auto-intersections.

Dans le dépôt, avec les dépendances Node de l’application et NumPy déjà disponibles :

```sh
app/node_modules/.bin/tsx outils/labo/mesh-topologie/extract-glb.ts source.glb nouveau-dossier-extraction
python3 outils/labo/mesh-topologie/topology.py --positions nouveau-dossier-extraction/positions.f64le --faces nouveau-dossier-extraction/faces.u32le --out nouveau-rapport.json
python3 -m unittest discover -s outils/labo/mesh-topologie -p 'test_*.py'
```

L’extracteur utilise la scène et les transformations traitées par `lireGlb`, et écrit les positions monde en float64 little-endian, les indices uint32 little-endian et leurs SHA-256. La sortie doit être un dossier neuf. Le diagnostic compare la soudure de positions exactement égales à la quantification q=100000, applique le seuil de norme au carré du produit vectoriel de `analyser` (1e-18), et indique les arêtes ouvertes, non manifold, composantes et tailles. Des sommets distincts peuvent être fusionnés par quantification ; une différence de résultats doit être examinée.

`raw_indices` mesure les statistiques avec les indices source ; `exact` et `quantized` restent inchangés.
Les coutures UV peuvent dupliquer des sommets malgré des positions identiques.
Une différence entre ces vues est descriptive : elle ne prouve ni défaut ni étanchéité.
Les seuils et les données d’entrée ne sont pas modifiés.

Pour un essai volumique distinct, avec `meshlib-core` et NumPy installés dans un environnement privé :

```sh
python outils/labo/mesh-topologie/repair.py --positions nouveau-dossier-extraction/positions.f64le --faces nouveau-dossier-extraction/faces.u32le --out nouveau-dossier-reparation --voxel-divisor 200 --fix-degeneracies
```

Le dossier exclusif contient un STL avant correction, un STL dérivé et un reçu (paramètres, version, SHA, temps et diagnostic du STL). La reconstruction utilise `HoleWindingRule` et un voxel égal à la diagonale de la boîte divisée par le paramètre ; `--fix-degeneracies` ajoute le remesh local. Le choix du voxel peut supprimer des détails ou créer des îlots. Les mesures d’écart, les composantes, les auto-intersections et l’apparence nécessitent un contrôle séparé ; les sorties restent des essais.
