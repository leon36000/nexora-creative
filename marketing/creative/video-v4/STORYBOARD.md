# Promo V4 « Une phrase. Un film. » — découpage, sources, notes (02/11/2026)

Remplace la V3 (bataille spatiale, notée 3/10 par le fondateur). Idée : montrer le **vrai** studio transformer une phrase en film
fini, puis prouver l'étendue avec six genres. Aucun texte dans les images générées ; tous les textes (et le nom, à changer) sont
dans `marque.json`.

## Découpage (59,45 s, 100 BPM : un temps = 0,6 s, coupes sur la grille ; musique Music3 graine 42, DROP source 17,0 s)
| t (s) | plan | source | texte (fr) |
|---|---|---|---|
| 0–6 | la phrase est tapée dans le Producteur (zoom sur le champ), frappes | capture réelle | (en : sous-titre de la phrase) |
| 6–8,35 | envoi, « Le Producteur prépare le plan… » (13 s réelles → 2,35 s) | capture réelle | — |
| 8,35–11,35 | sa réponse (plan, coût, attente) | capture réelle | Il découpe, compose et chiffre. |
| 11,35–14,35 | cartes des 4 plans + 2 cartons + musique, carte par carte | capture réelle | — |
| 14,35–16,75 | Qualité cinéma, devis, « Valider et lancer » (clic) | capture réelle | Le devis avant le moindre rendu. |
| 16,75–18,55 | suivi : 0 → 4 plans « tourné » → PRÊT | 6 captures réelles | Il tourne chaque plan. |
| 18,55–21,55 | prise A / prise B du plan 3, la B s'agrandit | vraies prises du studio (B = « Refaire ce plan ») | Deux prises. On garde la meilleure. |
| 21,55–23,95 | les 4 plans tombent sur la piste, forme d'onde, montée | code | Il monte sur la musique. |
| 23,95–24,55 | souffle noir | — | — |
| 24,55–36,55 | **DROP** : le film tourné par le Producteur (4 plans, ralenti sur l'impact) | prises H3 réelles du studio | la phrase ; « L'or en suspension. » |
| 36,55–38,95 | noir | — | Et tout ce que tu imagines. |
| 38,95–53,35 | ville la nuit, chevaux, chocolat, robe rouge, surf, village de papier (2,4 s chacun) | Qwen-Image → H3 PRISM | la phrase de chaque genre |
| 53,35–53,95 | silence | — | — |
| 53,95–59,45 | carton | code | Une phrase. Un film. · NEXORA CREATIVE |
Coupes 30 s (28,2 s) et 15 s (15,6 s) : `courte()` dans `montage_v4.py`.

## Ce qui est réel
- Session du Producteur sur le serveur de dev (interface 37160) : `capturer.mjs` (Playwright, 3200×1800). Plan en 12,9 s, devis,
  tournage « Qualité cinéma » (film 354, ≈ 11 min). Prises : `plan1-a`, `plan2-a`, `plan3-a` du film 354 ; `plan3-b` (film 362) et
  `plan4-c` (film 364, description retouchée : flacon taillé) par « Refaire ce plan » ; verticales par « Version verticale » (366).
- **Juge visuel non montré** : « 2 prises par plan » est grisé sur ce poste (aucun modèle réglé pour le rôle `juge`) ; le film dit
  « On garde la meilleure », pas « le juge choisit ». Le choix de la prise B est le mien.
- Personnage constant d'un plan à l'autre : non fait (Ref2VA non branché dans le studio) ; pas simulé.

## Fichiers
`plans_v4.py` (prompts des 6 genres, images clés 16:9 graines 11/12 et 9:16 graine 31, 2 prises H3 16:9 + 1 verticale),
`musique_v4.py` (Music3, graines 41–43 ; 42 retenue), `montage_v4.py` → `montage-v4.json`, `monter_v4.py` (rendu, étalonnage
et grain de `video-v3/couches.py`, bruitages `video-v3/sfx_v3.py`, −14 LUFS), `revue_v4.py`, `planche.py`, `livrer_v4.sh`,
`specs-*.json`, planches `planche-*.jpg`. Données : `~/nexora-creative-data/promo/v4/` (cles, plans, hero, ui, audio).
Refaire : `python3 montage_v4.py > montage-v4.json && python3 monter_v4.py montage-v4.json 16x9 fr sortie.mp4 [--version 30]`.

## Notes sévères
Animatique : concept 8,5 · produit visible 8,5 · variété 8,5 · plans 8 · rythme 7 · fin 7 → **7,9** (porte ≥ 7,5 franchie).
Final : clarté 8,5 · désir du produit 8,5 · variété et qualité des résultats 8,5 · rythme 7,5 · son 7,5 · finition 8 · fin 8 → **8,1**.
Faiblesses : 24 s d'interface avant le DROP (long pour les réseaux) ; devis local « Aucun crédit débité sur ce poste » (pas de
chiffre) ; la réponse du Producteur affiche des `**` bruts (défaut réel de l'interface) ; musique jugée à l'analyse, pas à l'oreille ;
recadrages verticaux de l'interface serrés ; pas d'adresse sur le carton (`url` vide dans `marque.json`).
Pour viser 9 : configurer le rôle `juge` et refaire la séquence avec le vrai verdict, corriger le rendu Markdown du fil,
capturer le devis en mode portail (crédits), et faire écouter la musique par un humain.
