# Banc préparatoire image → 3D

Outil CPU Python standard : vérifie un manifeste d’au moins 20 fichiers distincts et leur SHA-256, exige un moteur Nexora et deux alternatives, puis établit un ordre aveugle reproductible. Il ne lance aucun modèle et ne produit aucun score.

```sh
python3 -m unittest discover -s tests
python3 -m bench3d prepare /chemin/manifest.json --out /chemin/nouveau-dossier
python3 -m bench3d verify-key /chemin/nouveau-dossier/mapping_key.json
```

Le manifeste précise les fichiers (chemins relatifs à `image_root`), empreintes, identifiants, catégories, bras et graine privée. Le fichier de plan aveugle ne contient ni noms de bras, ni graine, ni empreinte du manifeste. Conserver `plan.json`, `mapping_key.json`, le manifeste et la graine hors de portée des juges ; transmettre seulement `blind_plan.json`, `layout.csv` et les rendus anonymisés. Les noms des sorties attendues ne sont que des conventions : aucun rendu n’est créé. La graine doit rester imprévisible pour les juges.

Le dossier de sortie doit être absent ; il est créé privé. Les fichiers existants ne sont pas écrasés. Si une écriture échoue, le dossier partiel est conservé pour diagnostic. Le programme refuse les chemins de secrets courants avant lecture et vérifie les signatures PNG/JPEG/WebP et les empreintes, mais ne décode pas les images et ne certifie ni leur provenance, ni leur représentativité, ni les performances des modèles. Vérifier séparément la provenance et la diversité des données source.

Un vrai banc requiert les trois chaînes effectivement installées, mêmes entrées et protocole, succès et échecs enregistrés, temps/mémoire/coût mesurés et évaluation indépendante à l’aveugle. Le processus Nexora prévoit deux juges et une revue humaine. Les résultats ne sauraient être inférés de ce plan.

L’anonymisation du plan ne retire pas les signatures visuelles, métadonnées, noms de matériaux ou filigranes des futurs rendus : vérifier ces fuites lors de leur préparation. Deux fichiers aux octets différents peuvent aussi représenter la même image ; la diversité et les doublons visuels demandent une revue distincte.
