# Vérification locale du 4 novembre 2026

- 37 tests unitaires hors ligne : validation, budgets et grille 17k+5,
  références, contrats réels V6 dans les deux langues, substitution récursive,
  calage, plafond de six travaux, relance unique, réservation des unités,
  révision, interruption après POST, reprise sans doublon, Flex et coûts,
  deux prises de voix, piste déjà reçue après interruption de mesure.
- `v7.py valider essai` : **OK**. Avertissements attendus : 10 s et une piste.
- `v7.py monter essai --a-blanc --brouillon` : **OK**, vrai montage CPU V6.
- `preuve.py` : onze commandes exercées avec `urlopen` interdit ; aucun appel
  GPU, API payante ou SSH. Durée de la preuve complète : 72,58 s.
- Deux films : 10,000 s chacun, 24 i/s, H.264/AAC, 960×540 et 540×960.
- Copies téléphone : 4 967 113 et 4 820 921 octets ; atom `moov` avant `mdat`.
- Grilles, onsets, LRA, planches et manifeste d'archive local produits.
- Rapport détaillé et médias locaux sous `.a-blanc/essai/`, ignorés par Git.

Reproduction depuis `marketing/creative/video-v7/` :

```bash
python3 -B -m unittest discover -s chaine/tests -v
python3 -B chaine/v7.py valider essai
python3 -B chaine/v7.py monter essai --a-blanc --brouillon
python3 -B chaine/preuve.py
```

Les services réels ComfyUI, studio Music3, OpenRouter, Whisper et SSH/pc1 n'ont
pas été exécutés. Les voix, notes et grilles du mode à blanc sont explicitement
marquées comme doublures. Les mesures audio et les exports CPU ont été exécutés.
