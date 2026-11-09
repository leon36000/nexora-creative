# ESSAI CPU Antipodal

Banc de comparaison numérique du nombre d’enroulement généralisé (GWN), sans réparation ni classification automatique intérieur/extérieur. Il compile le code public [Antipodal](https://github.com/MartensCedric/antipodal/tree/127f18de2ed133c0f2d8577e5717182d48ed06ce), commit `127f18de2ed133c0f2d8577e5717182d48ed06ce`, fourni séparément. Aucun poids, Embree, TBB ou OpenGL. La référence indépendante est une somme directe des angles solides de triangles. Le code Antipodal complet associe intersection signée et intégrale de frontière ; il ne se réduit pas à une moyenne de rayons. Voir le [papier](https://arxiv.org/abs/2605.01536v1) et `gwn_mesh.hh` au commit indiqué.

Prévoir Python 3, Git et un compilateur C++20 Linux ; obtenir le dépôt public séparément et le placer exactement au commit indiqué. Le lanceur refuse une autre révision ou des modifications sous `src/antipodal`. Il vérifie SHA et comptes des tableaux et du GLB contre le sidecar, ainsi que le SHA du GLB de référence des points. Ces contrôles prouvent leur cohérence déclarée, pas une attestation indépendante d’extraction.

```sh
python3 outils/labo/mesh-antipodal/run.py \
  --upstream /chemin/vers/antipodal \
  --positions /chemin/positions.f64le --faces /chemin/faces.u32le \
  --glb /chemin/source.glb --source-json /chemin/source.json \
  --points outils/labo/mesh-antipodal/chair-points.json \
  --reference-glb /chemin/vers/chaise-D.glb --out /chemin/nouveau-dossier
```

Le dossier résultat doit être inexistant. Compilation, trois fixtures cube fermé/ouvert/triangle retourné, témoin face/arête ambiguës et maillage réel sont exécutés avec limite d’espace virtuel de 2 Gio et délai de 600 s par commande. Le reçu conserve commandes, versions/empreintes, sorties et 2 directions pour chaque point ; le programme natif relève son temps et son RSS. En cas d’échec, le dossier partiel et le message sont conservés. Maximum : 500 000 triangles, 1 500 000 sommets et 32 points ; le mesh dense de plusieurs millions de faces est hors périmètre.

Les sept paires de points près des arêtes non variées proviennent de la chaise D ; le centre et l’extérieur sont des candidats, et un point dans une jambe de D a été choisi après sondage exploratoire. Les positions sont des coordonnées monde des extractions concernées. Le SHA du rapport d’arêtes inscrit dans le fichier de points est informatif : le lanceur ne recharge ni ne vérifie ce rapport ; seul le GLB de référence des points est vérifié. Aucun seuil universel n’est appliqué : un GWN fractionnaire est possible sur une surface ouverte ou mal orientée, et inverser toutes les faces inverse son signe.

Les points proches d’une surface (tolérance `1e-10 × diagonale`) et les intersections positives proches d’une arête (barycentrique `< 1e-10`) sont signalés, ainsi que les valeurs non finies ; ils ne sont pas retirés. Ce contrôle est limité : une absence de marque ne prouve pas la robustesse numérique ou la validité d’intérieur. `NaiveIntersector` utilise Möller–Trumbore sans prédicats exacts ; les rayons sur une arête, un sommet ou une surface sont ambigus. L’accord entre deux calculs sur la même géométrie ne prouve ni étanchéité ni absence d’autointersection.

Tests de contrat hors dépendance externe : `python3 -m unittest discover -s outils/labo/mesh-antipodal -p 'test_*.py'`. Les fixtures C++ réelles nécessitent le checkout épinglé et sont exécutées par le lanceur ; elles ne sont pas simulées dans la CI Python.
