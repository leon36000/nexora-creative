---
name: montage-outils
version: 1
roles: [producteur]
description: Procédure des outils de montage du Producteur (analyze_media, plan_edit, critique, revise).
---
Montage de médias existants (la personne fournit des vidéos, une musique, une voix) : n'utilise PAS proposer_production, qui sert à tourner de nouveaux plans.
1. analyze_media sur les identifiants de médias donnés : durées, coupes de plan, tempo, énergie. Gratuit.
2. plan_edit avec le brief, le genre, le format, la durée, les médias, la musique, les textes imposés mot pour mot. Le code valide le plan ; si le modèle échoue, le montage automatique est livré : dis-le simplement.
3. critique (2 tours au plus) : lis les écarts typés et leurs indices, puis revise avec des rustines ciblées par identifiant de plan (regler_plan, echanger, supprimer, inserer_apres, regler_texte, regler_audio). Si tu raccourcis un plan, rallonge-en un autre du même nombre d'images.
4. Réponds en 2 à 4 phrases : durée, nombre de plans, score, ce qui a été corrigé. Ne promets pas de rendu : le rendu se lance depuis l'interface.
Une rustine refusée (plan invalide ou score en baisse) ne change rien : garde le plan actuel plutôt que d'insister.
