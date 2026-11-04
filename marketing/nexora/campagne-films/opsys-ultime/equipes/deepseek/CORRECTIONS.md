# Corrections techniques du producteur : équipe deepseek

Aucune réécriture de la création. Seulement ce qui empêchait la chaîne de tourner.

1. (04/11 00:35) `musique.prompts` est une liste d'objets `{id, duree_s, prompt}` (le brief prévoyait une liste de textes) :
   la chaîne accepte désormais cette forme telle quelle ; `m01` → génération 1 (film long), `m02` → génération 2 (version
   courte), `m03` → génération 3 (vertical) ; une source musique de l'EditPlan nommée `m02` utilise la génération 2.
   Aucun changement dans `dossier.json`.
