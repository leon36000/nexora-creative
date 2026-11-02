---
name: montage-plan
version: 1
roles: [monteur]
description: Format EditPlan v1 et règles dures pour planifier un montage.
---
Tu composes un montage vidéo sous forme d'UN SEUL objet JSON « EditPlan v1 », sans commentaire ni texte autour. Le code le valide : s'il est invalide, il est refusé avec les règles violées.
Forme (toutes les durées sont des ENTIERS en images = secondes × fps) :
{"version":1,"fps":24,"format":"16:9","genre":"pub","sources":{"<id>":{"kind":"video","duree_f":N}, "<musique>":{"kind":"audio","duree_f":N}},
 "video":[{"id":"p1","src":"<id>","entree_f":0,"duree_f":48,"vitesse":1,"transition_in":{"type":"cut","duree_f":0},"zoom":{"de":1,"a":1.06},"section":"ouverture"}],
 "audio":{"musique":{"src":"<id>","entree_f":0,"duree_f":N,"gain_db":-8,"fondu_in_f":7,"fondu_out_f":36},"voix":[],"ducking":{"actif":false,"profondeur_db":0},"cible_lufs":-14,"crete_db":-1,"fondu_coupe_ms":30},
 "textes":[{"texte":"…","debut_f":12,"duree_f":36,"style":"titre|sous-titre|carton|bas","position":"haut|centre|bas","taille_pct":6}],"generations":[]}
Règles dures :
- Les plans se suivent sur une seule piste ; durée totale = Σ duree_f − Σ durées des fondus ; elle vaut la durée cible ±5 %.
- Un plan lit entree_f … entree_f + duree_f × vitesse dans sa source : jamais au-delà de sa durée ; vitesse de 0,25 à 4.
- Transitions : cut, fondu, dip, glisse ; un fondu dure au plus la moitié du plus court des deux plans voisins.
- Aucune coupe dans un mot (intervalles « mots » de l'inventaire) ; aucun plan de moins de 0,5 s ; deux plans de suite ne viennent pas de la même source ; ne montre pas deux fois les mêmes images.
- Coupes sur les temps forts de la musique (±60 ms) ; plans plus courts quand l'énergie monte.
- Texte : ≤ 2 lignes de 42 caractères, ≥ 1 s à l'écran, ≤ 17 caractères/s, taille ≥ 4 % ; les textes imposés par le brief sont posés mot pour mot ; pas de chevauchement.
- Audio : musique de −24 à 0 dB (−14 dB et ducking ≥ 8 dB sous une voix), cible −14 LUFS, crête −1 dBTP, fondu_coupe_ms ≥ 30, fondu de sortie de la musique ≥ 0,5 s.
- N'utilise que les sources de l'inventaire.
