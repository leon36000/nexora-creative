# Analyse de vidéos promotionnelles par lots (recherche/23)

1. `python3 -m venv $PROMOS_TRAVAIL/outils/venv && $PROMOS_TRAVAIL/outils/venv/bin/pip install yt-dlp`
2. Liste `id<TAB>marque` (voir `recherche/23-corpus/lot1.txt`).
3. `PROMOS_TRAVAIL=/chemin/de/travail outils/recherche-promos/lot_videos.sh liste.txt 6 medium` : télécharge en ≤ 480p (150 premières secondes), mesure (coupes, sonie) avec le ffmpeg de `~/nexora-creative-data/engine/ffmpeg/`, fait analyser la vidéo entière par Gemini 4 Argon via OpenRouter, **supprime la vidéo**, écrit `notes/<id>.json`.
4. `python3 -I outils/recherche-promos/agreger.py $PROMOS_TRAVAIL/notes liste.txt` : tableau, médianes, extraits (règles, accroches, voix, fins, musiques).
5. `verifier_refs.py fichiers.md` : contrôle des identifiants arXiv et des dépôts GitHub cités.

La clé OpenRouter est lue dans `/home/pc6/Desktop/Deepinfra.env` (`SA_KEYFILE` pour changer) par le script, jamais affichée. Coût observé : ≈ 0,045 USD par vidéo de 30 à 150 s.
