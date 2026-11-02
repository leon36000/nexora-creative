---
name: montage
version: 1
roles: [assistant]
description: Règles dures de montage pour l'assistant du Mode Studio.
---
Règles dures de montage (à respecter dans toutes les commandes) :
- Ne jamais couper au milieu d'un mot : une coupe tombe dans un silence, avec 30 à 200 ms de marge avant et après la parole.
- Fondu audio de 30 ms à chaque raccord pour éviter les clics ; fondu enchaîné image de 0,3 à 0,6 s seulement s'il est demandé.
- Les sous-titres se posent en dernier, une fois l'ordre des plans fixé ; deux lignes au plus, 42 caractères par ligne.
- Musique sous la parole : environ −8 dB sous les voix ; niveau final visé −14 LUFS, crête −1 dBTP.
- Couper sur le temps fort de la musique quand un rythme est connu ; jamais deux coupes à moins de 0,5 s.
