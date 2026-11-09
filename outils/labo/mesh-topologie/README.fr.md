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

## Graphes appariés TRELLIS — préparation uniquement

`buildPairedTrellisGraph` dans `paired-graph.ts` compose le constructeur officiel `buildTrellisGraph` sans contacter le moteur. Il accepte une image Comfy déjà nommée, une graine uint32, le profil `draft` ou `quality`, le retrait de fond et un préfixe `ESSAI/nom`. Sélectionner un à quatre identifiants parmi `A`, `B`, `C`, `D`, avec `A` obligatoire :

```ts
const { graph, outputs } = buildPairedTrellisGraph({
  image: 's01.png', seed: 0, quality: 'draft', removeBackground: true,
  filenamePrefix: 'ESSAI/comparaison', branches: ['A', 'B', 'C', 'D'],
});
// outputs : ['A_save', 'B_save', 'C_save', 'D_save']
```

Les branches partagent les nœuds amont `mesh` et `colors`, puis disposent chacune de leur propre remesh, décimation, UV, bake et `SaveGLB`. A conserve UDF, B active `fix_poles`, C utilise SDF/manifold sans QEF, D utilise solid/fill=20. Le constructeur refuse une modification de la référence remesh ou des liens de bake. Il retire le PreviewImage et désactive le turntable : les seuls nœuds de sortie sont les GLB demandés. Les différences de géométrie, les cartes cuites et les ressources ne sont pas mesurées par cette construction.

Le partage des IDs ne sérialise pas les voxels ; il n’est valable que dans le graphe proposé. Les graphes précédemment enregistrés ne contiennent aucun nœud de sauvegarde des voxels. `SaveGLB` accepte un `MESH` selon le code ComfyUI, ce qui permettrait théoriquement une sauvegarde séparée du mesh dense ; ce chemin n’a pas été exécuté, ne conserve pas le volume voxel et ne constitue pas un rejeu vérifié. Avant tout essai, vérifier la prise en charge effective des options dynamiques sur le moteur, la disponibilité mémoire et la file. Ne pas déduire une étanchéité ou une conservation visuelle des réglages.

Avant toute future préparation par une CLI, passer le `object_info` obtenu en lecture seule au validateur pur : `verifyPairedRemeshSchema(objectInfo, { graph, outputs })`. Il refuse notamment un mode dynamique modifié, un champ obligatoire inconnu, un type erroné ou une valeur hors des bornes annoncées. La fixture `remesh-schema.fixture.json` est une version élaguée du `object_info` réel, sans infobulles ; les tests ne contactent pas ComfyUI. Cette vérification est limitée à `RemeshMesh` : les autres nœuds, l’exécution et l’acceptation du graphe complet restent à contrôler séparément.
