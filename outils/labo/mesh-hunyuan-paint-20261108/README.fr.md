# Laboratoire : retexture d’une chaise avec Hunyuan Paint 2.1

Ce dossier reproduit un essai de recherche précis. Il ne branche aucune fonction de Creative. Il attend une copie locale de la chaise du banc Nexora, son image de référence, les sources et les modèles listés dans `input-manifest.json`, ainsi que l’environnement Python et les deux extensions compilées épinglés. Aucun poids, environnement ni fichier d’entrée n’est fourni ici. Ce manifeste décrit la configuration testée sur pc1 ; une autre compilation des extensions doit être examinée et faire l’objet d’un manifeste distinct.

Le code amont Paint est figé au commit `82920d643c0dc2f7bfd7255f45f62d386edfe60c`, les poids Paint à `0b94677654c57bb9a6b6845cd7b704ccf551d327` et DINOv2 à `611a9d42f2335e0f921f1e313ad3c1b7178d206d`. Les chemins du manifeste sont relatifs à la racine privée provisionnée ; le vérificateur refuse notamment les chemins non canoniques et les liens symboliques dans cette racine. La vérification est une lecture ponctuelle, sans garantie contre une modification concurrente après la lecture.

La capsule utilise un verrou GPU coopératif existant, contrôle la mémoire et les PID de calcul avant de lancer une seule tâche, puis surveille ces PID pendant au plus 900 secondes. Le superviseur Sync arrête son propre processus si un autre PID de calcul apparaît ou si la surveillance échoue. `--sync-fd` maintient le verrou dans le wrapper tant qu’il vit. Après l’arrêt, un contrôle borné vérifie les identités du namespace et la sonde GPU : si la preuve manque ou si un tiers reste présent, il enregistre `non_verifie` et signale l’échec sans arrêter ce tiers. Le verrou ne réserve pas le GPU contre les tâches qui ne le respectent pas ; l’état de la file Comfy est indiqué comme inconnu. Le processus bwrap isole réseau et PID, monte `/proc`, rend code et modèles accessibles en lecture seule et ne rend inscriptible que le dossier du run. Il force `TORCH_FORCE_WEIGHTS_ONLY_LOAD=1` et l’accès hors ligne. Aucun service Comfy n’est redémarré.

Avant d’utiliser le GPU, la capsule vérifie tailles et SHA-256, l’exécutable Blender et les versions des dépendances, puis charge les composants du modèle sur CPU avec GPU masqué. Elle refuse un identifiant de run déjà présent. Le dossier `capsules/<run-id>` conserve les logs et les résultats partiels en cas d’échec ; il n’est pas supprimé automatiquement.

```sh
python3 capsule.py --root /chemin/experience-privee \
  --lock /chemin/verrou-gpu-existant \
  --blender /chemin/blender-5.2.3 --run-id essai-01 --dry-run
```

`--dry-run` vérifie les fichiers, versions et Blender, sans créer de run ni utiliser le GPU. Sans ce drapeau, la commande effectue le prévol CPU puis peut lancer le GPU : elle ne doit être utilisée qu’après coordination de la machine et vérification des ressources. Les entrées de cette version sont la chaise et sa référence spécifiées dans le manifeste ; ce n’est pas encore un adaptateur général pour tout GLB.

L’essai réel antérieur a utilisé `use_remesh=False` ; le code amont appelle néanmoins xatlas et peut réorganiser les indices et remplacer les UV. La sortie OBJ et ses cartes d’origine sont conservées, puis Blender 5.2.3 réalise une conversion GLB séparée. La conservation de surface, pose, UV, matériaux et pixels doit être vérifiée sur chaque résultat ; le simple fait de produire un GLB ne la prouve pas. Blender a averti que plusieurs nœuds image alimentaient une texture et que le sampler du premier serait utilisé. Dans le cas testé, les pixels de couleur et les canaux de métal et de rugosité sont conservés ; ce n’est pas une validation colorimétrique générale.

L’OBJ généré ne contenait aucune normale. Le convertisseur a reconstruit des normales lissées : une comparaison par coins a montré des écarts par rapport à l’entrée. Le helper expérimental ci-dessous transfère les normales source par appariement de triangles orientés en coordonnées monde. Il ne traite qu’une primitive triangulaire statique avec positions et normales Float32 non normalisées ; les maillages instanciés `EXT_mesh_gpu_instancing` sont refusés. Il refuse les correspondances ambiguës et les normales contradictoires sur un sommet de destination. Il préserve la normale du résultat aux sommets où la normale source est nulle et compte ces exceptions. Il vérifie à la réouverture les autres attributs, la matrice, les octets des textures et les matériaux avant d’écrire une nouvelle sortie, sans écraser les fichiers existants.

```sh
node outils/labo/mesh-hunyuan-paint-20261108/transfer-glb.cjs \
  /chemin/entree.glb /chemin/paint-brut.glb \
  /chemin/paint-normales.glb /chemin/rapport.json
```

Sur la chaise, les 149 942 triangles ont été appariés à 10⁻⁶ unité près ; deux sommets de sortie issus d’une normale source nulle conservent la normale Paint. Un comparateur indépendant a mesuré les 449 824 coins définis : erreur angulaire maximale 2,70×10⁻⁶ degré. Les positions, UV et indices du résultat Paint, ses images et son facteur `KHR_materials_specular` restent inchangés dans ce témoin. Ce contrôle ne promet ni conservation des UV d’origine, ni prise en charge des scènes multi-primitives, animées ou avec peau. Le GLB d’entrée ne comportait pas de facteur spéculaire équivalent ; la comparaison visuelle ne mesure donc pas un effet de texture isolé.

La sortie historique a été produite par des scripts privés antérieurs à ce refactor portable : le reçu interne mesure 759,28 s et le superviseur 763,50 s, avec des points de départ et d’arrêt différents. Ces scripts avaient limité OMP et MKL à deux threads, contrairement au réglage souhaité pour pc1 ; le présent lanceur n’impose pas cette limite. Son SHA-256 GLB est `b4b2b9b22bb3bdc2d5d1e22d639ed4918cda71a09f33cf38a7f27146bc26c84f`. Le refactor de ce dossier a été vérifié sur CPU et en `--dry-run` ; aucune inférence GPU n’a été revendiquée avec lui. Un rendu neutre à 1024² montre des fibres sur l’assise : la première vue à 384² les rendait peu visibles. La fidélité du motif et du relief à la référence reste à évaluer ; aucune qualité générale ni parité avec un service tiers n’est revendiquée.

### Rejouer un inpainting CPU depuis des NPY

`bench_inpaint.py` accepte une texture `float32` H×W×3 dans [0,1] et un masque `uint8` H×W binaire (0 ou 255), tous deux contigus en ordre C, chargés avec `allow_pickle=False`. Il vérifie la version et le répertoire du module `cv2` déjà disponible ; il ne l’installe pas et ne change pas l’environnement. Le chemin et le SHA attestent le module Python, pas individuellement les bibliothèques natives chargées.

```sh
python3 outils/labo/mesh-hunyuan-paint-20261108/bench_inpaint.py \
  --texture /chemin/mesh-texture.npy --mask /chemin/mesh-mask.npy \
  --opencv-version 4.11.0 --opencv-root /chemin/site-prive \
  --output-dir /chemin/nouveau-dossier
```

La sortie est exclusive. Le reçu contient les SHA des NPY et des deux tableaux uint8 effectivement remis à `cv2.inpaint`, vérifiés avant et après appel. Les durées de conversion et d’inpainting sont mesurées séparément et additionnées ; le hachage intermédiaire est exclu. Il s’agit d’un témoin CPU NS rayon 3, sans attestation de fidélité visuelle ou de gain produit. Le test de refus fonctionne sans OpenCV ; le test fonctionnel local a utilisé une véritable installation privée sur une petite image.
