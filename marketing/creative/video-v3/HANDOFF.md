# Promo V3 Nexora Creative — passation (02/11/2026)

Arrêt demandé (budget de jetons) : plus aucune génération lancée. Tout ce qui suit est l'état réel à l'arrêt.

## Où sont les choses
- Sources (dépôt, ce dossier) : `moteur.py` (client ComfyUI H3 / Qwen), `plans_v3.py` (prompts H3), `specs-*.json` (specs soumises),
  `couches.py` (compositeur : flottes en parallaxe, traçants, rayons, explosions, débris, flashs, étalonnage, halo, reflets
  anamorphiques, tremblement, grain, cache 2,39), `interface.py` (moments produit + titres), `sfx_v3.py` (sound design),
  `montage_v3.py` → `montage-v3.json` (liste de montage + courbe d'énergie + versions 30 s / 15 s), `monter_v3.py` (rendu),
  `revue.py` (auto-revue), `livrer.sh` (livraison), `marque.json` (**seul endroit** du nom, slogan, textes fr/en), planche `planche-v3-16x9-fr.jpg`.
- Données (`~/nexora-creative-data/promo/v3/`, 1,9 Go) : `cles/` (images Qwen, 16:9 et `-v` 9:16), `plans/` (rushes H3),
  `audio/v3-musique-31.flac` (musique retenue ; 314 et 2718 écartées), `rendu/` (cache des plans composités), `brouillons/` (12 films),
  `comparaison/` (ronde H3), `tout-rendre.sh`, `nettoyage-pc1.log`.

## Films : FINAUX dans `brouillons/`, pas encore copiés ni encodés web
`v3-{16x9,9x16}-{fr,en}-{long,30,15}.mp4` (12 fichiers). Long = 60,5 s, 38 plans ; −14,4 LUFS, crête vraie −1,5 dBTP.
Coupes : montée 1,9 s de moyenne, action 1,6 s, climax 0,64 s ; 25/37 coupes avec attaque ≥ 3 dB (les autres sont dans le climax
déjà saturé de coups, ou le silence voulu avant le coup final). 9:16 : 8 plans rendus nativement en vertical (768×1344), le reste recadré.

## Plans
Bons et utilisés : p01 orbite nuit, p02 mur de flotte, p03 vague ennemie, p04 bordée (DROP), p05 hangar, p06 cockpit, p07 pilote
(ne pas dépasser 3 s : « 72 » d'interface vers 3,3 s), p08 vaisseau-mère, p09 rupture, p10 aube, t01 passage, t03 torpilles,
t04 explosion (recadré ×1,45 : hublot rond), t05 onde de choc, t06 tourelle (molle, une seule utilisation), t07 essaim.
Rejeté : t02 poursuite (chasseur en X façon X-wing). Prêts mais **non intégrés** : t08 tourelle et t09 onde de choc (re-générations
ciblées pour remplacer t06 à 22,2 s et t05 en fin de climax) — à regarder avant de les monter.

## Comparaison H3 (même prompt, graine 7777, 1344×768, 124 images)
| version | temps moteur | verdict |
|---|---|---|
| officiel ref2va int8, 24 étapes | 291 s | image nette, belle explosion, vaisseaux blancs « jouet » |
| FastH3 nvfp4, 8 étapes | 104 s | rapide, explosions correctes, look jeu vidéo |
| **10Eros-Max × Singularity V2 turbo 8 étapes (PRISM)** | 112 s | le plus de mouvement (12,3 vs 8,6), échelle, fumée, débris |
Retenus : **PRISM turbo** (héros + `h3-max`) et **FastH3** (volume + `h3-fast`, seul en famille fl2va : image de départ exacte).

## pc1 — ATTENTION : le nettoyage a déjà eu lieu
Le script gardé (file vide deux fois à 20 s, fichiers non ouverts d'après `lsof`, aucun lien) s'est déclenché à 03:17:39,
**juste avant** la consigne « ne rien supprimer » ; je l'ai annulé ensuite, rien d'autre n'a été touché. Supprimé dans
`minimax-h3/models/` seulement (≈ 134,2 Go) : fl2va int8 (20,97), ref2va bf16 (40,23), ref2va int8 (20,97), Singularity v2 int8
(20,97), 2 LoRA ref2v turbo 8 étapes (1,96 + 1,96), `sha256-turbo.txt`, encodeur `qwen3vl_32b…int8_convrot` (27,14).
Reste : `fastvideo_fasth3_8step_v2_pruned_nvfp4`, `10Eros_Max_h3_8stepTURBO_beta7_SingularityV2_ref2va_int8HQ` (nom d'origine
sans « ref2va », renommé pour l'aiguillage du studio), `qwen3vl_32b…nvfp4_awq`, VAE H3, fichiers Music3. Disque : 427 Go libres.
À faire (sans rien supprimer de plus) : effacer à la main les petits restes `.cache/huggingface/…incomplete` (≈ 0,8 Go) si le fondateur le veut.

## App : recettes repointées (fait, testé en unitaire, PAS encore par un vrai rendu)
`server/graphs/h3.ts` (points de contrôle distillés par famille + échantillonneur ; photo de départ → référence en ref2va),
`server/nexora/creer.ts` (`CHECKPOINT_H3_MAX`, 8 étapes), `registre.ts`, tests (114/114, `tsc` OK), `app/.env` (non versionné)
et `deploy/proxmox/creative.env.example`. **La VM 202 (`/etc/nexora/creative.env`) pointe encore sur fl2va int8, supprimé** :
y reporter `NEXORA_H3_MAX_CHECKPOINT=10Eros_Max_h3_8stepTURBO_beta7_SingularityV2_ref2va_int8HQ.safetensors` et `NEXORA_H3_MAX_ETAPES=8`,
puis `mettre-a-jour-creative.sh` (je n'ai pas touché aux VM). Vérifier ensuite un rendu par recette :
`curl -X POST 127.0.0.1:37161/api/nexora/creer -H 'content-type: application/json' -d '{"intention":"…","qualite":"rapide"}'` puis `"max"`.

## Notes honnêtes (/10)
Échelle 8,5 · rythme 8,5 · spectacle 8,5 · finition 8 · clarté produit 8,5 → **≈ 8,4**. Faiblesses : quelques chasseurs blancs
encore « jeu vidéo » (t01, t05, t07), t06 mou, traçants de code corrects mais génériques, carton de fin hérité (mosaïque « braise »
que la refonte Signal abandonne). Pour viser 9 : monter t08/t09, puis refaire t01/t07 à partir d'images clés Qwen.

## Reprendre
1. (option) monter t08/t09 : dans `montage_v3.py`, ajouter les plans `t08-tourelle`/`t09-onde-choc` (comme `t06`/`t05`) et remplacer
   `t06-tourelle` à `f(21.4)` et `t05-onde-choc` des coupes `-fin` ; `python3 montage_v3.py > montage-v3.json`.
2. `~/nexora-creative-data/promo/v3/tout-rendre.sh` (≈ 25 min CPU, 12 films) ; contrôle : `python3 revue.py montage-v3.json <film> planche.jpg [30|15]`.
3. `bash livrer.sh` → `promo/montage/Nexora-Creative-promo-V3-*.mp4`, `site-medias/film-creative-*.mp4` + affiche ; puis écrire
   `site-medias/manifest-creative.json` (ne pas toucher `manifest.json`) et pointer `marketing/creative/` et `marketing/nexora/partage/` vers V3.
4. Purger `promo/v3/brouillons/` et `rendu/` après livraison (garder < 8 Go sur pc6).
LTX-2.5 : non téléchargé (recommandation dans le rapport).
