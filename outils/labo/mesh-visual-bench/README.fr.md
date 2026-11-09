# ESSAI — viewer comparatif apparié

Préparation CPU d’un viewer local pour un run terminé ; aucune soumission ni inférence. Il vérifie l’UUID, le graphe et l’historique, l’événement terminé unique, les cinq GLB et leurs empreintes/tailles, l’entrée et le cas dans le manifeste du corpus. Les cinq GLB sont vérifiés ; seuls A–D sont copiés. Les URL externes contenues dans le JSON des GLB sont refusées. Le manifeste et le sidecar sont des preuves de cohérence des fichiers fournis, pas une signature indépendante du calcul.

```sh
python3 outils/labo/mesh-visual-bench/prepare_viewer.py \
  --run /chemin/vers/run-termine --corpus-manifest /chemin/vers/manifest-v2.json \
  --case s04 --out /chemin/vers/nouveau-dossier
```

Three 0.186.1 doit être installé dans `app/node_modules/three` ; `--three-dir` permet un autre chemin explicite. Le dossier de sortie doit être inexistant. En cas d’échec pendant la copie, le dossier partiel est conservé pour inspection ; aucun remplacement automatique. Servir ensuite cette seule racine sur loopback, puis ouvrir la page. `?lang=en` active les libellés principaux anglais ; `?lang=fr` est le défaut.

Le bouton explicite mesure quatre vues historiques plus **dessus**, ajoutée en `five-view-v2` ; il ne modifie pas les anciens JSON. Les cibles font 512 × 512. L’IoU concerne des masques opaques, faces avant, sans transparence ni alpha ; l’écart RGB en unités 8 bits est calculé sur leur intersection. Ces deux mesures sont distinctes, non perceptuelles et ne constituent ni une note de qualité ni une preuve d’imprimabilité. L’export comprend matrices, caméra, versions WebGL/Three et SHA du sidecar, lui-même sans référence circulaire.

Tests locaux :

```sh
python3 -m unittest discover -s outils/labo/mesh-visual-bench -p 'test_*.py'
node --test outils/labo/mesh-visual-bench/metrics.test.mjs outils/labo/mesh-visual-bench/views.test.mjs
```
