# Moteur de montage V6

`monter_v6.py` assemble un montage JSON en H.264 High, CRF 16, yuv420p, 24 i/s,
AAC stéréo 48 kHz à 320 kbit/s, avec `+faststart`. Tout le calcul est sur CPU.
Pillow envoie les images directement dans un tube ffmpeg. Les segments encodés
sont rendus en parallèle puis concaténés sans second encodage vidéo.

Le moteur reprend les outils et l'architecture de `video-v4/monter_v4.py`, sans
l'importer. `effets_v6.py` contient la pellicule et les flous copiés de V3 ;
`sfx_v6.py` conserve ses synthèses et ajoute le clavier mécanique et le whoosh.
Aucun module V3/V4 n'est modifié ou importé, donc aucun cache Python n'y est écrit.

## Utilisation

Depuis la racine du dépôt :

```bash
python3 -B marketing/creative/video-v6/monter_v6.py \
  marketing/creative/video-v6/montage-essai.json \
  --format 16x9 --langue fr \
  --sortie marketing/creative/video-v6/.cache/essais/essai-16x9-fr.mp4 \
  --master web --jobs 3

python3 -B marketing/creative/video-v6/monter_v6.py \
  marketing/creative/video-v6/montage-essai.json \
  --format 9x16 --langue fr \
  --sortie marketing/creative/video-v6/.cache/essais/essai-9x16-fr.mp4 \
  --master web --jobs 3 --brouillon

python3 -B marketing/creative/video-v6/planche_v6.py \
  marketing/creative/video-v6/.cache/essais/essai-16x9-fr.mp4 \
  marketing/creative/video-v6/.cache/essais/planche-16x9-fr.jpg
```

`--langue en` sélectionne tous les textes et la voix anglais. `--brouillon`
divise les deux dimensions par deux (960×540 ou 540×960) en gardant 24 i/s et CRF 16.
`--tolerant` permet un animatique avec des médias manquants : chaque source
visuelle absente devient un noir portant son nom de fichier ; l'audio absent
devient du silence. Sans cette option, une source absente bloque le rendu.
Le rapport `*.rendu.json` contient `tolerant` et la liste dédupliquée des chemins
`medias_absents` (y compris les captures citées par un journal mais manquantes).
Les médias illisibles, JSON invalides, erreurs de montage et polices absentes
restent des erreurs ; cette option ne répare pas les fichiers endommagés.
`--de 3.25 --a 8` rend uniquement cette plage, en conservant les horloges du film
pour les mouvements, le son natif, la musique et le ducking. Les limites sont
arrondies à l'image la plus proche. Le mastering porte sur la plage exportée.

`V6_CACHE` remplace le cache par défaut `.cache/` de ce dossier. Le script limite
les écritures à ce dossier V6 et au cache. `V6_FFMPEG` / `V6_FFPROBE` permettent
de remplacer les binaires statiques arm64 de V3. Dépendances : Python 3.10+,
NumPy et Pillow avec FreeType/WOFF2 (validé ici avec NumPy 2.5.4, Pillow 10.2).

Les sources ne sont jamais recopiées. Les rushes sont décodés par blocs d'une
seconde en mémoire, au maximum deux blocs par source et par processus, y compris
en lecture inverse. Commencer avec `--jobs 3` ; chaque encodeur utilise deux threads.

## Contrat JSON

Les chemins relatifs du montage se résolvent par rapport au JSON ; ceux des
polices et du logo par rapport au JSON de marque. `~` et les variables
d'environnement sont acceptés. Les textes publicitaires, les noms, les couleurs,
les polices, le logo et les identifiants du carton sont dans `marque-v6.json`.
Le texte réel extrait de `boost.json` reste une donnée du média.

Dans tout segment ou objet source (`media`, `sur_video`, `couches`, `rushes`,
ainsi que musique et voix explicites), `fichier_fr` / `fichier_en` remplace
`fichier` pour la langue choisie. Pour les captures, `dossier_fr` / `dossier_en`
remplace `dossier`, notamment dans `saisie` et `boost` ; le `boost.json` implicite
est lu dans ce dossier sélectionné. Les chemins localisés ont la même base que
les autres chemins. Les variantes de l'autre langue ne sont pas validées.
Une variante absente produit un **avertissement** et utilise `fichier` (ou
`dossier`), même sans `--tolerant`. Si ce repli manque aussi, le comportement
strict / tolérant s'applique normalement.

```json
{"type": "plan", "debut": 0, "duree": 1,
 "fichier": "rush.mp4", "fichier_en": "rush-en.mp4",
 "fichier_vertical": "rush-vertical.mp4", "fichier_vertical_en": "rush-vertical-en.mp4"}
```

En portrait, `fichier_vertical_fr` / `fichier_vertical_en` a priorité sur
`fichier_vertical`, qui a lui-même priorité sur le `fichier` sélectionné.
Si la variante verticale de la langue manque, le repli est directement ce
`fichier` sélectionné, avec avertissement. L'image et le son natif emploient
la même source.

```json
{
  "marque": "marque-v6.json",
  "bpm": 124.8,
  "phase": 0,
  "musique": {
    "fichier": "~/nexora-creative-data/promo/v6-creative/musique/lyria-3.wav",
    "entree": 8.0086916112491,
    "gain_db": -7,
    "coupes": [],
    "trous": [[2.0, 2.5]],
    "ducking_db": 7
  },
  "dossiers_voix": {"fr": "voix/fr", "en": "voix/en"},
  "voix": [{"id": "ouverture", "t": 0.5}],
  "sfx": [{"t": 1.0, "type": "whoosh", "db": -12, "duree": 0.2}],
  "segments": [
    {"type": "noir", "debut": 0, "duree": 1},
    {"type": "carton", "debut": 1, "duree": 2}
  ]
}
```

Tous les temps sont en secondes. `debut` désigne toujours le placement dans le
film ; `entree` désigne toujours le point d'entrée dans la source. `duree`
globale est optionnelle : sinon la fin du dernier segment la détermine.
Les trous sont remplis en noir. Les chevauchements entre segments sont refusés.
Les coupes sont quantifiées **globalement** à 24 i/s, sans cumuler des durées
arrondies séparément. Pour écrire un montage sur le temps, utiliser
`debut = phase + indice_temps * 60 / bpm`. Le moteur respecte les temps demandés
et ne les déplace pas implicitement sur la grille. `phase` est une indication
pour l'auteur de la liste ; `empile` et la mosaïque battent à partir de leur début.

### `plan`

```json
{
  "type": "plan", "debut": 0, "duree": 3,
  "fichier": "rushes/765.mp4",
  "entree": 0.7,
  "vitesse": [[0, 1.4], [0.8, 0.25], [1.8, 0.25], [3, 1.3]],
  "cadrage": [[0, 0.5, 0.5, 1], [3, 0.55, 0.48, 1.1]],
  "cadrage_v": [[0, 0.56, 0.45, 1], [3, 0.52, 0.5, 1.1]],
  "secousses": [[0.8, 22, 0.4]],
  "flash": [[0.8, "os", 0.12]],
  "etalonnage": "nuit_feu", "son_db": -6
}
```

`fichier_vertical` optionnel remplace la source en 9:16. Sinon `cadrage_v`
recadre la source horizontale (repli sur `cadrage`, puis centre).
Les cadrages `[t, cx, cy, zoom]` sont lissés avec `ease`, zoom ≥ 1 ; le recadrage
reste dans l'image. Les plans sont rééchantillonnés en Lanczos et légèrement accentués.

La vitesse est un nombre strictement positif ou une rampe `[t, vitesse]`
**linéaire**, intégrée analytiquement par morceaux, constante avant/après les clés.
`inverse: true` soustrait cette intégrale à `entree` ; sans `entree`, on part de
la dernière image. Un plan dépassant sa source est refusé avant le rendu.
Les amplitudes des secousses sont en pixels à petit côté 1080, adaptées au brouillon.
Le mouvement amorti a un surcadre de protection et un flou directionnel.
Les couleurs des flashs peuvent être des noms de palette ou des triplets RGB.
Préréglages : `nuit_feu`, `espace`, `orage`, `aube`, `neutre`.

### `saisie`

`dossier`, `etapes`, `zone: [x0,y0,x1,y1]`, `viewport: [1600,900]` (optionnel).
Les coordonnées sont CSS. `journal.jsonl` règle les durées relatives des captures
retenues ; les pauses gardées sont conservées proportionnellement. Sans journal,
les fichiers `NNNN-etape.jpg` sont utilisés dans l'ordre, à durée égale.

La caméra cadre **dès la première image** la première ligne : `zone_texte` permet
de la donner explicitement, par exemple `[104,300,470,345]`. À défaut, elle prend
les 49 premiers pixels CSS de `zone`. La zone occupe 70 % de la largeur en paysage,
90 % en portrait. Pour une phrase courte, le moteur mesure les pixels clairs de
la dernière capture retenue et resserre encore le cadre : la ligne terminée vise
38 % de la largeur, donc dépasse 35 % sur les captures s01. Cette mesure fixe
le cadrage de toutes les frappes ; seule une poussée de 3,5 % reste animée.
`zoom_texte` (nombre positif fini, défaut `1`) multiplie le grossissement.
Les premières lettres seules occupent naturellement moins de place que la ligne
terminée. Les longues saisies et les zones comprenant d'autres textes peuvent
nécessiter une `zone_texte` plus précise.

La capture reste réelle : curseur et correcteur ne sont ni reconstruits ni
remplacés. La ligne reste nette, avec un léger flou ailleurs. Chaque nouvelle
capture `saisie` effectivement affichée déclenche un clavier (`clavier_db`,
défaut −20 dB). `sfx_auto: false` désactive les sons automatiques.

### `boost`

`dossier` sélectionne les captures et lit `boost.json` : `mots` fournit la saisie
initiale, `boost` le texte enrichi. `fichier` et `boost_json` restent des alternatives.
`texte` (chaîne ou `{fr,en}`) remplace le texte enrichi ; les `mots` du fichier sont
quand même lus. `mots` et `fautes` peuvent aussi être fournis sur le segment, avec
priorité sur le fichier. `mots` accepte une chaîne ou une liste de mots.

Le boost n'affiche plus de grille sur une capture. Sur l'encre :

1. **0–25 %** : très gros mono blanc centré, tremblement, puis éclatement de
   chaque lettre avec vitesse, rotation et traînées, sur un flash. Un petit
   lexique FR/EN embarqué marque les mots inconnus d'une vague rouge. Les accents
   comptent : « dragn » et « chateau » sont signalés, « château » et « feu » sont
   connus. Une liste `fautes` explicite remplace la détection ; `[]` ne souligne
   rien. Sans `mots`, cette phase reste sur l'encre, sans inventer une saisie.
2. **25–80 %** : mots du texte réel projetés en rayons depuis le centre, avec
   profondeur, grossissement, opacité et traînées radiales. Le reste défile en
   petits rubans mono gris. Les `termes_cles` claquent seuls au centre en signal,
   pendant **2 à 3 images** chacun, zoom 1,15 → 1. La hauteur visible des capitales
   vise 12–16 % du cadre ; en portrait, les expressions passent à la ligne et
   les lignes longues sont condensées horizontalement pour rester centrées.
3. **80–100 %** : aspiration ×3, flou radial, puis **deux images entièrement
   blanches**, comptées sur les images réellement exportées, même si `debut`
   n'est pas aligné sur 24 i/s.

L'ordre des clés dans le JSON donne leur priorité. Chaque clé exige au moins deux
images centrales : si la durée ne permet pas toutes les claques, les premières
sont retenues au centre ; toutes restent dans les projections secondaires. Pour
le segment 3 réel (18 images), cinq des sept clés peuvent claquer ; pour le
segment 32 (23 images), les six clés tiennent. La durée du montage reste intacte.
Une liste courte et priorisée produit les claques les plus lisibles.

Le texte intégral est conservé au chargement. Les mots en rayons sont bornés à
12 mots secondaires par seconde environ (6 à 24), répartis sur tout le texte,
en plus des clés. Le résultat est déterministe et ne dépend pas du nombre de
processus ni de l'ordre de rendu. Souffle et riser automatiques sont conservés.
Le lexique est petit : noms propres et vocabulaire spécialisé peuvent être
inconnus ; fournir `fautes` pour contrôler exactement les soulignements.

### `titre` et surimpressions

`texte_id` pointe vers `marque.textes[langue]`. Styles :

- `claque` : échelle 1,35 → 1 en quatre images, flou, secousse, impact automatique ;
- `balayage` : masque latéral sur 270 ms ;
- `empile` : un mot supplémentaire par temps, les mots restent empilés.

Le fond est l'encre de marque. `sur_video: "precedent"` ou `"suivant"` prend
les dernières/premières secondes du plan adjacent. Un objet source est aussi
accepté : `"sur_video": {"fichier": "rush.mp4", "entree": 1}`. Le portrait
revient automatiquement à la ligne et réserve 12 % en haut et 20 % en bas.

Chaque segment peut porter des `textes` dont `t` est **local au segment** :

```json
{"t": 0.2, "duree": 1, "texte_id": "preparation", "style": "legende", "position": "bas"}
```

`position` : `haut`, `centre`, `bas` ou `[cx,cy]` normalisé. `legende` (défaut)
est une pastille sombre ; `grand`, `claque`, `balayage`, `empile` donnent un
texte grand format. Un tableau `textes` à la racine utilise des temps **film**.
`langues: ["fr"]` peut limiter une surimpression, une voix ou un SFX à une langue.

### `chapitre`

`texte_id`, `media` (source JPEG/PNG/MP4, ou `{dossier, etapes}`),
`en_preparation: true` optionnel. Le titre utilise Geist **900**, avec des
capitales d'environ 10 % de la hauteur en paysage ; s'il comporte deux mots,
le second prend l'orange signal. Les titres longs reviennent à la ligne et
peuvent réduire leur corps pour tenir dans la réserve haute du portrait.

Le panneau occupe **86 % de la largeur en 16:9**, **92 % en 9:16**, après une
entrée de quatre images (échelle 0,92 → 1 et glissement vertical). Son contenu
pousse lentement de 1 → 1,06. Les doubles chevrons orange restent sur les côtés.
Une `media.zone` CSS, avec son `viewport`, est **découpée dans la source avant**
sa mise au rapport du panneau : le reste de l'interface ne revient pas dans le
cadre. Le fond utilise une version sombre et floue du média.
Le badge prend `marque.carton.preparation_id` et se traduit avec la marque.

### `avant_apres`

`couches` contient deux ou trois objets sources synchronisés. Par exemple :

```json
[
  {"fichier": "765.mp4", "entree": 1, "saturation": 0, "texte_id": "brut"},
  {"type": "damier", "texte_id": "masque"},
  {"fichier": "765.mp4", "entree": 1, "texte_id": "final"}
]
```

Le balayage révèle chaque couche successivement, de gauche à droite en paysage
et de haut en bas en portrait. Un fichier de masque peut remplacer le damier.
`saturation: 0` calcule la désaturation en mémoire : aucun rush dérivé à stocker.
Les identifiants d'étiquette par défaut sont `brut`, `masque`, `final`.

### `mosaique`, `noir`, `carton`

`mosaique.rushes` contient trois à neuf objets sources. Ils entrent un par temps,
en grille paysage ou en pile portrait dans les marges de sécurité. `temps`
peut fournir la liste des instants locaux d'apparition. Chaque rush démarre à
son apparition ; ses `entree`, vitesse et cadrages sont respectés.

`noir` accepte un `texte_id` optionnel et les surimpressions communes.

`carton` n'a aucun texte local : logo PNG si `marque.logo` est renseigné,
sinon `nom` puis `produit`, slogan, URL non vide et mentions. Tous les cartons
utilisent cette même fonction remplaçable. `marque.carton.slogan_id` et
`mentions_id` désignent les textes localisés. Les titres utilisent Geist 900,
le mono JetBrains 500 ; le poids titre est configurable entre 800 et 900.

Une source est généralement un objet `{fichier, entree, vitesse, cadrage,
cadrage_v, saturation}`. `media`, `couches` et `rushes` acceptent aussi des
chemins simples. Les MP4 sont échantillonnés à 24 i/s ; les sources secondaires
plus courtes sont maintenues sur leur dernière image. Pour `plan`, la validation
de durée est stricte. Le rôle d'`entree` reste identique partout.

## Audio et mesure

`musique.coupes` : `[[t_film, t_morceau], …]`. L'auteur choisit les sauts sur la
même position de mesure (à 124,8 BPM : un temps ≈ 0,48077 s, une mesure ≈ 1,92308 s).
Le moteur préserve exactement ces points d'ancrage et applique un fondu croisé
linéaire de 30 ms centré sur la coupe, sans dériver la phase suivante.
`gain_db` (alias `gain`) est exprimé en dB.

`musique.trous: [[t0, t1], …]` coupe **la musique seule** en temps film, après
les changements de source de `coupes`. Chaque plage est entièrement muette,
avec un fondu de sortie de 15 ms avant `t0` et d'entrée de 15 ms après `t1`.
Les plages peuvent se chevaucher ; elles doivent être finies et respecter
`0 ≤ t0 < t1`. Elles sont bornées à la durée du film. Voix, son natif et SFX
restent audibles, y compris lors d'un export `--de` / `--a`.

`voix: [{id,t,db}]` cherche `<id>.wav` dans `dossiers_voix[langue]`. Des listes
différentes peuvent être données : `voix: {fr: [...], en: [...]}`. Un élément
peut aussi préciser `fichier` (ou sa variante de langue). `voix[].db` règle le
gain de chaque voix en dB, avant le mastering du mix complet. Le ducking abaisse
**la musique seule** de `musique.ducking_db` dB (défaut 7, nombre fini ≥ 0 ;
0 désactive l'atténuation),
avec une attaque anticipée de 60 ms et un relâchement de 250 ms. Les voix qui
se chevauchent n'additionnent pas l'atténuation.

`plan.son_db` active le son natif, y compris sous les rampes et en marche arrière.
Il suit exactement l'intégrale des temps source de la vidéo, avec des fondus
de 10 ms aux deux coupes. Ce rééchantillonnage modifie aussi la hauteur du son.
Sans `son_db`, le plan est muet ; sans piste audio, un message le signale.

SFX V3 : `impact`, `boom`, `explosion`, `tir`, `canons`, `fouet`, `montee`,
`inverse`, `chute`, `drone`, `frappe`, `clic`, `souffle`. V6 ajoute `clavier`,
`whoosh`, `riser` (alias `montee`), `sub` (alias `chute`). Les événements peuvent
préciser `duree`. Désactiver `sfx_auto` sur le segment pour piloter entièrement
ses sons depuis la liste racine, sans doubler un impact ou un clavier.

Deux passes `loudnorm` maîtrisent le mix float32 : `web` cible −14 LUFS et
≤ −1,5 dBTP ; `reseaux` cible −10 LUFS et ≤ −1 dBTP. Une marge de 0,3 dB
précède l'AAC. Une calibration du WAV avec limitation suréchantillonnée à 192 kHz
ramène les plages courtes à leur cible quand les transitoires empêchent la
normalisation initiale d'y parvenir. La vraie sortie AAC est remesurée ; si
elle dépasse le plafond, le mix original est remasterisé avec une marge accrue,
en conservant la cible LUFS. L'export est refusé si la loudness reste à plus de
0,25 LUFS de la cible ou si la crête dépasse le plafond après quatre tentatives.
Le fichier voisin `*.rendu.json` donne **`loudness_aac.input_i`** et
**`input_tp`** : ce sont les mesures du MP4 final, pas les `output_*` de la passe
d'analyse. Il donne aussi la commande et le temps total de calcul.

Mesure indépendante :

```bash
~/nexora-creative-data/engine/ffmpeg/ffmpeg-7.0.2-arm64-static/ffmpeg \
  -hide_banner -i marketing/creative/video-v6/.cache/essais/essai-16x9-fr.mp4 \
  -vn -af loudnorm=I=-14:TP=-1.5:LRA=11:print_format=json -f null -
```

## Vérifications, cache et limites

```bash
python3 -B marketing/creative/video-v6/test_monter_v6.py
```

Les tests portent sur l'intégrale de vitesse, l'inversion, l'horloge audio/image,
les coupes, le fondu musical, le ducking, les événements clavier, les validations
et les neuf compositeurs dans les deux langues et les deux rapports.
Ils vérifient également les sources localisées et leurs replis, les trous et
leurs fondus de 15 ms, les gains voix et le ducking réglable, les médias absents
en mode strict / tolérant (avec un export et son rapport), ainsi qu'un boost
de six prompts réels concaténés dans les deux formats. Les tests visuels
contrôlent les clés séquentielles centrées, les fautes et leur surcharge JSON,
les deux images blanches finales, la largeur réelle de saisie et le découpage
CSS du panneau avec son entrée et son grand titre.
L'essai dure 25 temps, quantifiés à 288 images / 12,00 s. Son avant/après compare
le même rush désaturé puis en couleur, sans génération de nouveau média.

Le cache des segments est invalidé par le code, la marque, la langue, le format,
les réglages et les tailles/horodatages des sources. Les fichiers partiels sont
écrits sous un nom temporaire puis renommés après un encodage réussi. Les
listes de concaténation et les WAV de mixage sont nettoyés en fin de traitement.
`.cache/essais/` conserve les MP4, planches et rapports demandés. Les autres
segments de test peuvent être supprimés après vérification ; aucun PNG n'est créé.
Les tests suppriment leurs nouveaux segments de cache, même si une assertion
échoue, et retirent leurs fichiers temporaires. Les sorties d'essai antérieures
ne sont pas effacées.

Essai court du boost long (JSON autonome et six prompts réels conservés dans
`.cache/essais/boost-long-6-prompts.json`) :

```bash
python3 -B marketing/creative/video-v6/monter_v6.py \
  marketing/creative/video-v6/.cache/essais/boost-long-6-prompts.json \
  --format 16x9 --langue fr --brouillon --jobs 1 \
  --sortie marketing/creative/video-v6/.cache/essais/boost-long-6-prompts.mp4
```

Le segment demande 2 temps à 124,8 BPM (0,961538 s), quantifiés à 23 images
(0,958333 s) à 24 i/s. L'essai fait claquer les expressions clés et projette un échantillon
de mots ; la lecture intégrale de six prompts en moins d'une seconde est
impossible. Les mots gris servent de matière ; les clés sont les points de lecture.

Limites visuelles assumées : le ralenti répète des images, sans interpolation
optique ; profondeur, bougé et flou radial sont des simulations 2D. Le boost
sous-échantillonne les mots secondaires pour tenir en environ une seconde.
Les captures françaises et le texte réel du prompt restent français dans une
sortie anglaise, à moins de fournir un `dossier_en` / `fichier_en` ou un `texte`
localisé. Le moteur traduit les textes de marque et sélectionne les voix ; il
ne fabrique pas de nouvelle capture ni de voix. Les JSON de marque, narration et montage d'origine restent indépendants du moteur.

## Preuves codex3 — segments 2, 3, 26 et 32

```bash
export V6_CACHE=/home/pc6/nexora-creative-data/promo/v6-creative/cache-montage
python3 -B marketing/creative/video-v6/preuves_codex3.py
```

Le script rend huit MP4 `essais/codex3-{type}-s{numéro}-{format}-fr.mp4` :
saisie s02, boost s03, chapitre s26 et boost long s32, chacun en 1920×1080 et
540×960 brouillon, à 24 i/s avec audio masterisé web. Il travaille sur des copies
JSON temporaires et emploie `--de/--a`, en gardant l'horloge du film pour la
musique et les voix. Les copies, rapports et nouveaux segments de cache sont
supprimés dans un `finally` ; **seuls les MP4 de preuve restent**. Les fichiers
existants ne sont pas effacés. La synthèse finale sur stdout donne les temps de
rendu et les mesures AAC de chaque preuve.

Dans le bac à sable de cette session, le cache externe est monté **en lecture
seule**. Le repli explicite `--cache-local` écrit donc les preuves sous
`marketing/creative/video-v6/.cache/codex3/essais/`, sans changer la variable
`V6_CACHE`. Les tests se lancent avec `v.CACHE` dirigé vers un sous-dossier
V6 temporaire quand cette même restriction est présente. Aucun GPU ni commit.

Mesures des huit MP4 retenus dans cette session (un processus CPU, deux threads
x264 ; tests lancés en parallèle pendant une partie des rendus) :

| Preuve | Durée film | 16:9 plein format | 9:16 brouillon |
| --- | ---: | ---: | ---: |
| saisie s02 | 0,958 s / 23 images | 7,11 s | 6,46 s |
| boost s03 | 0,750 s / 18 images | 3,14 s | 2,21 s |
| chapitre s26 | 1,458 s / 35 images | 7,88 s | 2,65 s |
| boost long s32 | 0,958 s / 23 images | 3,85 s | 2,92 s |

Total des rendus retenus : **36,21 s**. AAC mesuré entre −14,13 et −14,02 LUFS,
crêtes ≤ −1,82 dBTP. Les 25 tests passent (33,89 s), puis les deux vérifications
du chapitre et des neuf compositeurs ont repassé après avoir limité le nouveau
découpage CSS au seul chapitre. Les deux images blanches ont aussi été vérifiées
dans les quatre MP4 boost décodés ; dimensions, 24 i/s, H.264 High yuv420p et AAC
stéréo 48 kHz ont été contrôlés sur les huit fichiers.

Le montage a été modifié sur disque pendant le travail : les scènes de référence
s26 (« 3D RELIEF ») et s32 (boost des six prompts) sont devenues les segments 27
et 33. Le script les retrouve par leur contenu, garde les noms de référence
pour les preuves et emploie leurs horaires actuels. `--segments 26 32` permet
de ne refaire que ces deux paires. Il échoue si cette correspondance devient
ambiguë. Aucun JSON source n'est réécrit par ce script.
