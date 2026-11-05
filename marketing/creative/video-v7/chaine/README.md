# Chaîne commune V7

Depuis `marketing/creative/video-v7/`. Python 3.10+, NumPy, Pillow, ffmpeg/ffprobe.
Aucun commit ni changement des dossiers créatifs n'est effectué par la chaîne.

## Vérification sans GPU, API payante ni SSH

```bash
python3 -B -m unittest discover -s chaine/tests -v
python3 -B chaine/v7.py valider essai
python3 -B chaine/v7.py monter essai --a-blanc --brouillon
python3 -B chaine/preuve.py
```

`essai` désigne ici `chaine/equipes/essai/dossier.json` (2 clés, 2 plans,
1 réplique, 1 piste, 10 s). Cette localisation respecte le périmètre d'écriture
imposé. Les équipes réelles sont cherchées d'abord dans `equipes/<nom>/`.
Un chemin explicite vers `dossier.json` ou son répertoire est aussi accepté :

```bash
python3 -B chaine/valider.py chaine/equipes/essai/dossier.json
```

`--a-blanc` fabrique de vrais médias de test sur CPU ; le montage et le
mastering utilisent réellement `monter_v6.py`. Les moteurs, Whisper et les
juges distants sont doublés. `archiver --a-blanc` produit un manifeste local,
sans connexion. `preuve.py` interdit en plus tout `urlopen`, exerce les onze
commandes, contrôle les deux films, le triptyque, la limite de 28 Mo et
`moov` avant `mdat`. Il écrit `.a-blanc/essai/preuve.json` et conserve les MP4.
Les données à blanc sont isolées dans `chaine/.a-blanc/<équipe>/`, ignorées
par Git. La grille à blanc est elle aussi une doublure explicitement marquée.

## Production

Ces commandes sont fournies pour la production ultérieure. Sans `--a-blanc`,
`cles`, `plans`, `voix`, `musique`, `juger-musique` peuvent consommer GPU/API ;
`archiver` copie sur pc1.

```bash
python3 -B chaine/v7.py valider opus
python3 -B chaine/v7.py cles opus
python3 -B chaine/v7.py plans opus
python3 -B chaine/v7.py voix opus
python3 -B chaine/v7.py musique opus
python3 -B chaine/v7.py monter opus --musique m1 --anglais
python3 -B chaine/v7.py monter opus --musique m2 --brouillon
python3 -B chaine/v7.py juger-musique opus
python3 -B chaine/v7.py planche opus
python3 -B chaine/v7.py telephone opus
python3 -B chaine/v7.py archiver opus
python3 -B chaine/v7.py bilan opus
```

`--langue fr --langue en` équivaut à `--anglais` ; `--format 16x9` ou
`--format 9x16` limite les exports. Sans options : français et les deux rapports,
master web. `--jobs N` fixe les processus CPU. `--musique` sélectionne une
piste pour un export ; répéter `monter` pour chaque variante voulue.
`juger-musique` produit automatiquement un montage mixé par piste en 960×540.

Sorties lourdes : `~/nexora-creative-data/promo/v7-creative/<équipe>/`.
`--donnees <racine>` remplace cette racine, notamment pour les tests.
Les caches de montage y sont dirigés par `V6_CACHE`, jamais vers `video-v7/.cache`.
Les binaires sous `~/nexora-creative-data/engine/ffmpeg/` sont prioritaires.

## Contrats et budgets

Le validateur contrôle le schéma du §8, les identifiants, références, formats,
la grille H3 `124 + 17k` jusqu'à 243, les mots interdits au positif (casse et
tirets normalisés), `No text`, et appelle le vrai `monter_v6.charger()` dans
les deux langues. Il substitue seulement les assets générés par des fichiers
factices avec leurs durées de rush exactes. Captures, marque, textes, polices,
boost et autres fichiers restent vérifiés sur disque. Les erreurs bloquent
les commandes ; la durée hors 40–70 s, les plans >6 s et textes >4 mots sont
des avertissements. Moins de trois pistes signale un dossier incomplet, tout
en permettant l'essai technique à une piste.

Plafonds du dossier : 24 clés, 20 unités horizontales, 4 verticales, 8 répliques,
3 pistes. Les tentatives H3 consomment les mêmes enveloppes, relances incluses.
Les unités nécessaires aux plans initiaux sont réservées avant les relances.
Une image sous 6,5 reçoit exactement une relance à graine +1000, hors quota de
24 créations. Une vidéo n'en reçoit qu'une si les unités restent disponibles.
La meilleure note gagne ; à égalité, la première prise est conservée.

Pour la ronde de révision, ajouter `"revision": true` à la racine du dossier :
les plans dont la signature a changé consomment l'enveloppe distincte de
6 unités, et une quatrième musique est acceptée. Garder le même répertoire
de données ; les plans inchangés sont repris depuis l'état existant. Les
anciennes prises sont conservées. Les clés modifiées consomment une création
supplémentaire dans les 24. Le bilan distingue les unités de révision.

Les chemins montage sont relatifs à `dossier.json`, comme le contrat V6.
Les ressources communes `captures/…` et `marque-v7.json` ont un repli vers
`video-v7/`. Fournir un chemin absolu pour lever toute ambiguïté. Les
références `plan_v:<id>` doivent désigner un plan de format 9:16 ; les
identifiants restent uniques dans la liste des plans. Les références
fonctionnent aussi dans mosaïques, couches et sources imbriquées. Une voix
`h3-natif` est retirée des pistes additionnelles : son dialogue appartient au
son natif du plan ; activer `son_db` dans le montage pour l'entendre.

## File, reprise et journaux

Chaque processus prend un verrou local par équipe. Les quatre équipes peuvent
tourner en parallèle. Le contrôle `/queue` compte les travaux de cette équipe
(préfixe `v7-<équipe>/`), y compris le travail courant, avant chaque soumission.
Le plafond est six pour H3 ; aucun travail des autres équipes n'est déplacé.
Les graphes Qwen/H3 sont importés de `video-v3/moteur.py`, avec les réglages
fixes du brief et le négatif de `recette_live.py`.

`cles/etat.json` et `plans/etat.json` conservent signature, préfixe, prompt_id,
graine, rendu, temps moteur, note et choix. Écriture atomique et fsync.
Une intention est persistée avant le POST. Après coupure, elle est recherchée
par son préfixe dans `/queue` puis `/history`. Si elle reste introuvable,
la commande s'arrête avec « soumission ambiguë » : il faut vérifier le serveur,
sans effacer l'état ni relancer à l'aveugle. Un rendu terminé mais pas encore
jugé est jugé à la reprise, sans nouveau calcul GPU. Un état « soumis » dont
le serveur a effacé l'historique doit être diagnostiqué manuellement.

`journal.jsonl` par étape garde les prises, prompts, graines, notes, défauts et
temps moteur. Les prises non retenues sont conservées sous `prises/`.
`openrouter.jsonl` journalise les coûts renvoyés, jamais la clé. Configurer
explicitement `V7_API_BASE_URL` et `V7_API_KEY` ; aucun fichier secret n'est lu.
Tous les appels directs à Gemini 4 Argon imposent
`provider.order=["google-ai-studio/flex"]`, `allow_fallbacks=false`, y compris
l'oreille du banc. La chaîne ne bascule pas vers un autre fournisseur.

## Audio, mesures et limites

Les voix réutilisent `CANDIDATS`, `generer()` et `juger()` du banc. Deux prises,
Whisper `small` sur CPU dans le venv de transcription, WER normalisé sans
ponctuation ; sélection selon la note pondérée du banc, pénalisée de `5×WER`.
Les transcriptions et deux prises restent consultables. `h3-natif` ne génère
rien. La chaîne ne traduit pas les répliques : fournir les voix/captures
localisées dans le montage si une adaptation anglaise complète est souhaitée.

Lyria reprend le client SSE existant ; Music3 utilise le studio s'il répond,
sinon un graphe équivalent à `app/server/graphs/music3.ts` sur la GB10. Après
une soumission studio, une erreur ne déclenche jamais un second calcul sur
ComfyUI. Les identifiants des prises Music3 sont conservés pour reprise. Pour
modifier un prompt Music3 existant, employer un nouvel identifiant de piste.
La mesure réelle réutilise `grille()` de l'outil musical V5/V6.

`calage: "auto"` choisit l'entrée qui place le plus grand saut positif de
l'énergie (pas de 0,5 s) sur le premier élément chronologique de `temps_forts`.
On retient les entrées non négatives qui laissent assez de piste pour tout
le film. Sans candidat, entrée 0. Pour un Clip de 30 s sous un film de 60 s,
prévoir explicitement les coupes musicales ; l'auto-calage ne compose ni ne
boucle la musique. Les autres réglages (trous, gain, ducking, coupes) sont
conservés. Le tempo/phase mesurés sont transmis au montage ; les coupes visuelles
écrites par l'équipe restent aux temps demandés par le contrat V6.

Le juge musique reçoit d'abord le MP4 réellement mixé. Sur refus HTTP du format
vidéo (400/413/415/422), repli vers 16 images chronologiques + l'audio **du mix**.
Le rapport précise la modalité. Tempo et phase sont estimés par la grille ;
les onsets forts sont des pics de flux spectral à environ 100 Hz. Le rapport
mesure les coupes audibles à ±2 images des temps, l'écart moyen de chaque impact
à la coupe la plus proche, et le LRA EBU R128 de la piste via ffmpeg. Les trous
musicaux sont exclus des mesures de synchronisation. Il ne s'agit pas d'une
analyse de partition. La mémorabilité et l'adéquation restent des avis de modèle.

Les copies téléphone utilisent deux passes H.264, ≈3,8 Mb/s ou moins selon la
durée, AAC 128 k, `+faststart`, puis contrôlent la limite **28 000 000 octets**.
L'archive copie récursivement tous les MP4, y compris variantes, rushes, prises
et caches ; elle conserve leur arborescence. L'inventaire a les 15 colonnes V6
et déduplique les sha256 sous un verrou distant pour les écritures concurrentes.

Le bilan additionne les temps **moteur** disponibles ; le temps de file n'est
pas présenté comme du temps GPU. Les temps absents restent signalés comme
inconnus, notamment si le studio ne les expose pas. Les réponses audio binaires
peuvent ne pas fournir leur coût : somme connue et nombre de coûts absents sont
séparés. Les intégrations GPU/API/SSH n'ont pas été exercées en réel pendant ce
travail ; elles doivent être vérifiées au premier lancement de production.

Références API consultées pour le format des requêtes :
[entrée vidéo OpenRouter](https://openrouter.ai/docs/guides/overview/multimodal/videos),
[Lyria Clip](https://openrouter.ai/google/lyria-3-clip-preview).
