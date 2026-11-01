# Stings, son signature, barres inférieures, transitions

Tout est fabriqué en code (Python, PIL, numpy, ffmpeg) : aucun fichier de banque d'images ou de sons. Le logo est celui du site (PNG rastérisés depuis les SVG officiels, `video/sources/logo/`), jamais redessiné ; l'image finale des stings est le logo officiel pixel pour pixel.

## Fichiers (`final/`)
| Fichier | Contenu |
|---|---|
| `sting-nexora-{16x9,9x16,1x1}-{fr-CA,en-CA}.mp4` | Sting de 4,58 s (110 images à 24 i/s) : braises → treize carrés se rassemblent en N → la diagonale orange s'allume carré par carré → le symbole se range et le logotype se révèle → ligne « IA souveraine au Québec » / « Sovereign AI, made in Québec ». Seule cette ligne change entre fr et en. Avec son (−14,9 LUFS : la crête à −1,5 dBTP limite le gain d'un clip aussi court). |
| `son-signature-nexora.wav` | Le son seul, stéréo 48 kHz 24 bits, 4,6 s, −14,5 LUFS : pouls grave à deux temps qui s'accélère, souffle qui gonfle, **tintement cristallin sur l'allumage du N** (trois notes qui montent, une par carré, à 2,0 s), sub grave qui se pose, souffle expiré, petite salle. Synthétisé par `son.py` (sinus, partiels de cloche inharmoniques, bruit filtré, réverbération par réponse impulsionnelle synthétique). |
| `barre-inferieure-{16x9,9x16,1x1}-{fr-CA,en-CA}-alpha.mov` | Barre inférieure de 5 s à superposer à une autre vidéo : **ProRes 4444 avec canal alpha** (fond transparent). Barre d'encre translucide avec le logo officiel et la ligne Québec, qui s'ouvre de gauche à droite (carré orange en tête) et se referme. En 9:16 elle reste au-dessus des 380 px du bas des plateformes. Pas d'audio. |
| `transition-1s-{16x9,9x16,1x1}-alpha.mov` | Transition de 1 s « carrés qui balaient l'écran » **avec alpha** (ProRes 4444) : une vague de carrés (rampe braise) couvre l'image de gauche à droite (couverture complète à 0,5 s : c'est l'instant de la coupe), puis se retire. |
| `transition-1s-{16x9,9x16,1x1}.mp4` | Même transition **sans alpha** (fond encre `#0A0A0E`), avec son de balayage (−15,4 LUFS), à insérer comme un plan entre deux vidéos. |

## Utilisation
- Fin de vidéo : sting de même format. Début de vidéo : idem, ou barre inférieure sur les premières secondes.
- Barre inférieure : poser le .mov sur une piste au-dessus de la vidéo (le canal alpha est lu par Premiere, DaVinci, Final Cut ; ffmpeg : `-filter_complex "[0:v][1:v]overlay=0:0:format=auto"`).
- Transition : poser le .mov alpha sur le point de coupe entre deux plans (la coupe se fait à 0,5 s), ou insérer le .mp4 entre deux vidéos.

## Régénérer
```
python3 ../sources/teasers/outils/fabriquer_stings.py        # tout le dossier final/ (≈ 2 min)
python3 ../sources/teasers/outils/sting.py 16:9 fr x.mp4     # un seul sting
python3 ../sources/teasers/outils/son.py x.wav               # le son seul
```
