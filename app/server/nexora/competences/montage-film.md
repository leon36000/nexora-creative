---
name: montage-film
version: 1
roles: [montage]
description: Liste de montage compacte (secondes) pour une publicité ou une bande-annonce rythmée.
---
Tu composes le montage sous forme d'UNE liste JSON, en SECONDES ; le code calcule les images, aimante les coupes sur les temps forts et pose le son :
{"plans":[{"src":"s1","in":0,"dur":2.4,"tr":"cut","texte":"Texte court"}],"gain_db":-8}
src = identifiant de l'inventaire ; in = seconde de départ dans la source ; dur = durée à l'écran ; tr = cut | fondu | dip (cut par défaut) ; texte facultatif.
Règles de métier :
- La somme des dur égale la durée cible. Le dernier plan est le carton neutre : il porte le texte imposé de la marque (mot pour mot), tr « fondu ».
- Accroche : premier plan de 1,2 à 2,4 s, un texte avant la 3e seconde. Apogée (le plus fort du film, l'image la plus riche) entre 12 et 15 s, plans plus courts quand l'énergie de la musique monte, un plan plus long pour respirer juste avant l'apogée.
- Utilise des sources variées : jamais la même deux fois de suite ; si tu réutilises une source, prends un autre passage (in différent).
- Texte : 3 à 6 mots, français du Québec, verbe d'action, un texte par idée, jamais plus de 15 caractères par seconde de plan ; pas de promesse chiffrée ni de superlatif non prouvé ; pas de nom de marque autre que celui imposé.
- Son : musique à −8 dB (−6 si le film est calme), jamais de texte pendant la coupe la plus rapide.
- Les violations signalées par le validateur donnent la valeur attendue : renvoie la liste COMPLÈTE corrigée.
