# Processus standard pour créer une technologie Nexora

Décidé par le fondateur (04/11/2026), à l'image de ce qui est fait pour Nexora Mesh (le 3D de Creative). S'applique à chaque technologie : 3D, détourage, synchronisation labiale, voix, musique, transcription, montage, effets spéciaux, avatars, etc. Objectif : la technologie la plus qualitative et la plus puissante possible **en local**, au niveau (ou au-dessus) des concurrents, simple pour le commun des mortels.

1. **Recherche approfondie** : littérature scientifique (arXiv, conférences 2025-2026) et logiciels libres (GitHub, GitLab, Hugging Face). Liens vérifiés, dates, licence en un mot (usage commercial dans un service payant, territoires exclus), matériel requis, maturité. Note dans `recherche/NN-<sujet>.md`.
2. **Concurrents** : fonctions, ergonomie, prix, démonstrations publiques (Higgsfield, OpenArt, Meshy, Runway, Kling, etc.). Aucun compte créé, aucun achat.
3. **Banc local honnête** : au moins deux alternatives ouvertes contre notre moteur, 20 entrées variées, juge à l'aveugle (Gemini Argon Flex élevé, GPT-6.1 Sol via Codex) plus un regard humain sévère sur les planches ; mesures de temps, mémoire, coût. Verdict clair : avons-nous la meilleure technologie possible ?
4. **Meilleure chaîne locale** : assembler les meilleures briques libres étage par étage (plusieurs candidats triés par un juge automatique), sur les machines qui conviennent (petits modèles sur les cartes de pc5, gros sur les cartes lourdes).
5. **Module indépendant** dans le dépôt Creative : dossier, README, tests, contrat d'entrée et de sortie, bilingue FR/EN, conteneur (Dockerfile + manifeste), entrée dans le manifeste des modèles de `nexora-plateforme`, **fiche d'outil MCP** (pour les plugins Codex et Claude).
6. **Interface** : sa place dans Creative et, si le produit le mérite, un **espace de travail complet dédié** (comme Nexora Mesh).
7. **Marketing** : page dédiée, démonstrations reproductibles, films (grammaire de `recherche/23-grammaire-promos-ia.md`).
8. **Copie GitLab par technologie** (miroir en lecture seule) quand le module est stable et réutilisable ailleurs.
9. Documenter : `docs/JOURNAL.md`, `docs/PASSATION-AGENTS.md`, `docs/backlog/`.

Technologies déjà prévues pour Creative : `docs/backlog/creative-triple-a.md` (TA1 à TA25).
