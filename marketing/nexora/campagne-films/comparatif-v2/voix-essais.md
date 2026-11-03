# Voix fr-CA : essais du 03/11 (pc1, CPU Ryzen 9950X3D ; GPU laissé à ComfyUI)

Banc : 3 phrases narrateur (Nexora, OPSYS-AI, WorkStudio, M1–M10) + 1 phrase assistant, clonage depuis les prises ElevenLabs « Alexandre Boutin » (narrateur) et « Adam » (assistant) ; licence de ces références gérée par le fondateur. WER = aller-retour faster-whisper medium (pc6). « Strict » = Whisper sans invite de marques.

| Moteur | Licence | WER (strict) | Calcul/phrase (RTF) | Remarque |
|---|---|---|---|---|
| **Chatterbox multilingue** (Resemble) | MIT | 0,015 (0,047) | ≈ 10,6 s (≈ 2,0) | retenu ; réglage expressivité, filigrane Perth inaudible |
| Qwen3-TTS 1.7B Base | Apache-2.0 | 0,015 (0,047) | ≈ 22 s (4,1) | aussi bon, 2× plus lent ; plan B (VoiceDesign possible pour l'assistant) |
| XTTS-v2 (coqui-tts) | CPML **non commercial** | 0,015 (0,11) | ≈ 11 s (1,8) | « WorkStudio » mal rendu, 1 hallucination (a1 refaite) |
| F5-TTS finetune **québécois** (tontate) | CC-BY-NC **non commercial** | 0,015 (0,06) | ≈ 31 s (6,0) | seul modèle entraîné sur l'accent QC : à écouter, inutilisable en pub sans licence |
| Kokoro 82M (ff_siwis) | Apache-2.0 | 0,06 (0,14) | 0,6 s | témoin : voix de France, sans clonage, lit « É » comme « E accent aigu » |

Choix : Chatterbox, à égalité d'intelligibilité avec Qwen3, licence commerciale, plus rapide, débit naturel ≈ 2,6–2,85 mots/s avec expressivité 0,65 / cfg 0,5. Seul défaut commun : « OPSYS-AI » (lexique « Opsis é-aïe ») est entendu « Opsis et AI » par Whisper.
L'accent québécois n'est pas mesurable ici : le fondateur doit écouter. Échantillons sur pc6, 48 kHz −16 LUFS, `t1..t3` narrateur, `a1` assistant :
`~/nexora-creative-data/work/films-v2/voix-echantillons/{chatterbox,qwen3,xtts,f5,kokoro}/` (+ `voix.json` par moteur).
Outil : `voix.py narrer` (moteur choisi par VOIX_MOTEUR, défaut chatterbox) ; venvs et poids sur pc1 dans `NexoraStudioWork/films-v2/voix/` (uv, Python 3.11, torch CPU).
