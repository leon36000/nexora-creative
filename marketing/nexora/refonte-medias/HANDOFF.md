# Médias de la refonte « Signal » : passation (02/11/2026)

Arrêt demandé par le fondateur (budget). Aucune génération n'est en cours ; les files GPU sont arrêtées.

## Livré (`~/nexora-creative-data/site-medias/`, décrit dans `manifest.json`)
- **Images** (2560×1440 + 4:5 1152×1440 + 9:16 810×1440, chacune en AVIF/WebP/JPG) : `hero-datacenter`, `hero-ville`, `hero-champ` (3 candidats du héros) ; `infra-dgx-spark` (4:5 et 9:16 = rendus natifs), `infra-dgx-station` (9:16 natif), `infra-racks` ; `reception-accueil`, `reception-onde` ; `surveillance-entrepot`, `surveillance-stationnement`, `surveillance-salle` ; `creative-atelier`, `creative-lumiere` ; `workstudio-flux` ; `code-poste` ; `methode-installation`, `methode-consultation` ; `souverainete-serveur`, `souverainete-coffre`.
- **Film Surveillance IA** : `film-surveillance-{fr,en}-{16x9,9x16}.mp4` (H.264, 22 Mo en 16:9, 15 Mo en 9:16) + `.webm` (AV1) + `-poster.{jpg,avif}` ; masters dans `masters/`. 40,5 s, −13,6 LUFS.
- `hero-boucle-{16x9,9x16}` : **abandonné** (jugé trop « bon marché » par le fondateur, refait par un autre agent). Les fichiers sont encore là ; à remplacer ou supprimer par cet agent.
- Rien n'est chargé dans Directus.

## Reste à faire (ordre de priorité)
1. **Réception virtuelle** : plans 16:9 faits et vus (`telephone`, `onde`, `cliente`, `texto`, `transfert`). Manquent `artisan` (v1 rejeté, prompt refait, `CHOIX` pointe sur v2), `matin`, `aube`, puis les 8 plans 9:16. Musique choisie : `recep-v1.flac`.
2. **Infrastructure IA** : aucun plan. Images de départ prêtes pour `spark` et `station` (I2VA, `DEPART` dans `plans.py`). Musique `infra-v1.flac` (chute à 26 s, calée sur « hébergée chez nous »).
3. **WorkStudio**, puis **Code** : aucun plan ; musiques choisies (`work-v2`, `code-v1`).
4. Creative : confié à un autre agent (ne pas toucher `film-creative-*` ni `manifest-creative.json`).

## Reprendre (depuis `marketing/nexora/refonte-medias/`)
```
python3 plans.py recep artisan --depart 2 && python3 plans.py recep            # 16:9, H3 complet (recette lue sur le moteur)
python3 plans.py recep --format 9:16 --moteur rapide                          # 9:16, FastH3 pleine définition
python3 plans.py infra && python3 plans.py infra --format 9:16 --moteur rapide
python3 montage.py reception fr 16x9   # puis en, et 9x16 ; écrit montages/*.json, master, web, poster, manifeste
python3 revue.py                       # planche-medias.jpg + revue/index.html
```
Une file séquentielle existe : `python3 outils/file.py ~/nexora-creative-data/site-medias-travail/file-5090.txt` (une ligne = une commande ; `.fait` = déjà lancées). Garder les rendus en séquence (un autre agent entretient pc1 entre deux tâches). Textes, accents et durées : `films.py` ; nom et signature : `marque.json` (puis relancer `montage.py`, sans GPU). Plans retenus : `CHOIX` dans `films.py`. Travail et brouillons : `~/nexora-creative-data/site-medias-travail/` (journal GPU : `journal-gpu.jsonl`).

## Défauts connus
- Produits (Spark, Station, baies) : rendus IA « type » DGX, sans logo NVIDIA ; à remplacer par des photos officielles si autorisées.
- La plupart des images Qwen sont sorties trop sombres : ombres relevées au post-traitement (gamma noté dans le rôle de chaque entrée du manifeste).
- `code-poste` : écran de code flouté en post-traitement (pseudo-code lisible à l'origine).
- Surveillance : boîtes de détection posées en code (suivi par gabarit pour l'entrepôt, images clés réglées à l'œil pour le stationnement) ; versions 9:16 des deux plans CCTV recadrées dans le 16:9 (définition plus faible, crédible pour de la vidéo de caméra).
- `hero-champ` 9:16 (boucle) : nuage de points ondulé, différent du 16:9.
- Son : aucune écoute humaine (mesures seulement) : −13,6 LUFS ; crêtes de −0,4 à +0,1 dBFS après encodage AAC malgré le limiteur final à −1,5 dB (la version anglaise 16:9 touche +0,1). À corriger en baissant `limit` de l'`alimiter` final dans `outils/film_signal.py` (0,84 → 0,79), puis relancer `montage.py`.
- Rejets et raisons : `rejets.txt`.
- Disque de pc6 : 15 Go libres (99 %), consommé surtout par d'autres travaux ; mes dossiers ≈ 0,6 Go.
