# Corrections techniques du producteur : équipe deepseek

Aucune réécriture de la création. Seulement ce qui empêchait la chaîne de tourner.

1. (04/11 00:35) `musique.prompts` est une liste d'objets `{id, duree_s, prompt}` (le brief prévoyait une liste de textes) :
   la chaîne accepte désormais cette forme telle quelle ; `m01` → génération 1 (film long), `m02` → génération 2 (version
   courte), `m03` → génération 3 (vertical) ; une source musique de l'EditPlan nommée `m02` utilise la génération 2.
   Aucun changement dans `dossier.json`.
2. (04/11 02:50) Répliques `l02` et `l08` (ElevenLabs) : la consigne de jeu contenait, après les balises entre crochets, une note en prose
   (« Sourire audible, débit vif et sûr… ») qu'ElevenLabs a **lue à voix haute** (prises de 13,4 s, transcription = la consigne). La chaîne
   ne transmet plus à ElevenLabs que les balises entre crochets ; les prises fautives sont rangées dans `voix/ecartes-consigne-lue/` et
   refaites avec le même texte, la même voix et les mêmes balises. Le plan `p13` (voix ancrée `l02`), refusé à la première passe parce que
   la prise dépassait 10 s, est remis dans la file. Aucun changement dans `dossier.json`.
