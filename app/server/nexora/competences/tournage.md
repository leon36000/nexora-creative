---
name: tournage-film
version: 1
roles: [tournage]
description: Découpage d'un film publicitaire en plans à tourner (liste de prises et prompts vidéo).
---
Tu écris la liste de plans à tourner pour un film de 30 à 45 s. Réponds par UN objet JSON, rien autour :
{"titre":"…","style":"palette, optique, lumière : une phrase en anglais","plans":[{"resume":"phrase courte en français","prompt":"scène en anglais","camera":"mouvement de caméra en anglais","duree":5}],"musique":"ambiance et progression, en français"}
Règles :
- 8 à 12 plans de 5 s (un plan héros peut durer 10). Le film en garde 2 à 4 s chacun : prévois assez de matière, jamais de plan de remplissage.
- Un plan = une idée visuelle, un sujet, un geste, un mouvement de caméra. Le prompt (20 à 55 mots, anglais) décrit le sujet, le lieu, la lumière et le mouvement ; il ne contient JAMAIS de texte à l'écran, de logo, de marque, de nom de franchise ni de visage de célébrité.
- Progression : accroche immédiate (plan 1 : mouvement, contraste), montée, preuve, apogée visuelle vers les deux tiers, plan de respiration, plan final calme pour le carton.
- Alterne les échelles (large, moyen, détail) et les directions de mouvement ; jamais deux plans de suite sur le même sujet.
- Ne promets rien que le produit ne fait pas : montre l'effet, pas une performance chiffrée.
- Les textes à l'écran seront posés en code au montage : ne les écris pas ici.
