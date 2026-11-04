# Incrustations de la chaîne (annexe des EditPlan)

Tracées en code à la résolution finale (1920×1080 ou 1080×1920), par-dessus l'image, chiffres et textes exacts. Style commun :
verre holographique (fond encre translucide, filets bleu ion, léger balayage), Geist pour les titres, JetBrains Mono pour les
données, un seul accent orange signal. Animation d'entrée (0,3 à 0,6 s) et de sortie (0,22 s) automatiques.

Champs communs à toutes : `type`, `debut_f` (image de début, 24 i/s, sur la ligne de temps du film), `duree_f`,
`position` (`centre`, `gauche`, `droite`, `haut`, `bas`, `haut-gauche`, `haut-droite`, `bas-gauche`, `bas-droite`),
`echelle` (1,0 par défaut). Les textes acceptent `*mot*` (accent orange) et `|` (retour à la ligne voulu).

| type | champs propres | rendu |
|---|---|---|
| `titre` | `texte`, `zone` (`colonne`, `haut`, `bas`, `centre`) | mots révélés un à un sous un cache de ligne (≤ 7 mots) |
| `impact` | `texte` | phrase seule au centre, arrivée en échelle et flou (sur un coup) |
| `pile` | `lignes` : [texte, …] | lignes révélées l'une après l'autre |
| `surtitre` | `texte` | mono capitales, puce orange (« M3 · ESTIMATION ») |
| `etiquette` | `texte` (`VISION`, `EN PRÉPARATION`) | étiquette à contour orange, petite, en coin |
| `statut` | `texte` | message d'état de l'IA, mono, point qui pulse, frappé lettre à lettre (« Photo reçue. Mesures en cours… ») |
| `document` | `titre`, `destinataire`, `lignes` : [[libellé, valeur], …], `total`, `tampon` (texte ou null) | carte holographique qui s'assemble ligne par ligne ; le total compte jusqu'à sa valeur ; tampon à la fin |
| `compteur` | `de`, `a`, `decimales`, `prefixe`, `suffixe`, `etiquette` | grand nombre qui monte (accélération puis arrêt net) |
| `courbe` | `points` : [v, …] (≥ 3 valeurs), `etiquette`, `valeur` (texte affiché à la fin), `pointille_depuis` (indice où commence la projection) | courbe qui se trace, zone remplie, partie projetée en pointillé, valeur finale |
| `cedule` | `titre`, `semaines` (1 à 4), `jours` (défaut Lun à Ven), `blocs` : [[semaine, jour_debut, jour_fin, rangee, texte], …] (indices à partir de 0) | grille qui se dessine puis se remplit de blocs étiquetés |
| `pointage` | `heure` (« 07:02 »), `nom`, `etat` (« ARRIVÉE ») | heure frappée en grand, nom et état en mono, bip visuel |
| `appel` | `nom`, `sous_titre`, `voix` (id de réplique : l'onde suit la vraie voix) | carte d'appel avec onde vocale animée |
| `trajet` | `points` : [[x, y], …] en fractions du cadre, `couleur` (`ion` ou `signal`) | ligne lumineuse qui se trace d'un point à l'autre, impulsion qui court dessus (le signal) |
| `flash` | `intensite` (0 à 1) | éclair blanc chaud de 3 images |
| `glitch` | `intensite` (0 à 1) | décalage RVB et bandes, 4 à 8 images |
| `carton` | (aucun : lit `marque-opsys.json`) | carton final remplaçable : nom, logo, signature, mentions |

Bruitages (`sfx`) : `fouet`, `impact`, `montee`, `inverse`, `chute`, `clic`, `frappe`, `souffle`, `boom`, `drone`, avec
`debut_f`, `db` (gain), `duree_s` optionnelle. Son natif des plans (`son_plans`) : `{"plan": "p04", "db": -10}`.
Étalonnage (`etalonnage`) : `{"contraste": 1.0, "saturation": 1.0, "chaleur": 0.0, "grain": 1.0}` pour tout le film.
