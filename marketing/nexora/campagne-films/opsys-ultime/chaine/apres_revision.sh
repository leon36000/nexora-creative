#!/bin/bash
# Tout ce qui suit la ronde de révision d'une équipe, sans intervention : import du dossier révisé, contrôle, reprises de voix,
# reprises de plans (≤ 8 unités), musiques candidates (3 à 4, plusieurs moteurs), conformation au montage + juge audio-vidéo,
# choix de la musique (règle de l'équipe), montages finaux (long, court, vertical), juge final, archivage pc1, mesures.
# Usage : apres_revision.sh <equipe>      Journal : <travail>/apres-revision-<equipe>.log
set -u
EQ=$1
R=/home/pc6/Desktop/NexoraCreative-opsys-ultime
C=$R/marketing/nexora/campagne-films/opsys-ultime
W=/home/pc6/nexora-creative-data/work/opsys-ultime
cd "$C/chaine" || exit 1
t() { echo "$(date +%T) $EQ : $*"; }
# 1. import (les sous-agents écrivent dans leur bac à sable)
if [ "$EQ" != opus ]; then
  for f in dossier.json REVISION.json DOSSIER.md; do [ -f "$W/sa/$EQ/equipes/$EQ/$f" ] && cp "$W/sa/$EQ/equipes/$EQ/$f" "$C/equipes/$EQ/"; done
  cp "$W/sa/$EQ/equipes/$EQ/"*.py "$C/equipes/$EQ/" 2>/dev/null
fi
if ! python3 valider.py "$C/equipes/$EQ/dossier.json" "$C/casting/palette.json" > "$W/$EQ-valider-revision.log" 2>&1; then
  t "dossier révisé NON valide (voir $W/$EQ-valider-revision.log) : on continue avec ce qui est montable"
fi
cd "$R" && git add "marketing/nexora/campagne-films/opsys-ultime/equipes/$EQ" && git commit -q -m "Film ultime OPSYS-AI : dossier révisé de l'équipe $EQ (ronde de révision)" -m "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>" && git push -q gitlab feat/opsys-ultime; cd "$C/chaine"
# 2. voix (reprises et choix) puis reprises de plans
python3 tourner.py "$EQ" revision > "$W/$EQ-revision-voix.log" 2>&1
t "voix appliquées"
OPSYS_FILE_PAR_EQUIPE=1 python3 file.py reprises --equipes "$EQ" --max-file 3 > "$W/$EQ-reprises.log" 2>&1
t "reprises tournées : $(grep -c secondesMoteur "$W/$EQ-reprises.log")"
# 3. musique écrite pour le montage
python3 partition.py generer "$EQ" > "$W/$EQ-musique-candidats.log" 2>&1
python3 partition.py evaluer "$EQ" long > "$W/$EQ-musique-evaluation.log" 2>&1
python3 - "$EQ" <<'PY'
import json, sys
import tourner as T, partition as P
eq = sys.argv[1]
D = T.dossier(eq)
ev = json.loads((T.TRAVAIL / eq / "musique" / "evaluation-long.json").read_text()) if (T.TRAVAIL / eq / "musique" / "evaluation-long.json").exists() else {}
R = {}
f = T.RACINE / "equipes" / eq / "REVISION.json"
if f.exists():
    R = json.loads(f.read_text())
regle = (R.get("musique") or {}).get("choix", "juge") if isinstance(R.get("musique"), dict) else "juge"
if ev:
    best = regle if regle in ev else max(ev, key=lambda k: ev[k]["note_combinee"])
    cands = {c["id"]: c for c in D.get("musique", {}).get("candidats") or []}
    court = next((c["id"] for c in cands.values() if c.get("version") == "court" and (T.TRAVAIL / eq / "musique" / f"{c['id']}.wav").exists()), best)
    P.conformer(eq, court, "court")
    c = T.choix(eq)
    c["musique"] = {"long": f"conforme-{best}-long.wav", "court": f"conforme-{court}-court.wav"}
    if D["montage"].get("vertical"):
        P.conformer(eq, court, "vertical")
        c["musique"]["vertical"] = f"conforme-{court}-vertical.wav"
    T.ecrire_choix(eq, c)
    print("musique retenue", best, "court", court, "règle", regle)
PY
t "musique choisie : $(python3 -c "import json;print(json.load(open('$W/$EQ/choix.json')).get('musique'))")"
# 4. montages finaux, juge, archivage
for v in long court vertical; do
  python3 -c "import json,sys;d=json.load(open('$C/equipes/$EQ/dossier.json'));sys.exit(0 if d['montage'].get('$v') else 1)" || continue
  python3 monter.py "$EQ" "$v" --jobs 12 > "$W/$EQ-final-$v.log" 2>&1
done
python3 juge.py film "$W/$EQ/montage/$EQ-long.mp4" "Version finale de la publicité OPSYS-AI de l'équipe $EQ." > "$W/$EQ-juge-final.log" 2>&1
python3 archiver.py "$EQ" > "$W/$EQ-archive.log" 2>&1
python3 comparer.py > /dev/null 2>&1
t "FINI : $(ls $W/$EQ/montage/$EQ-*.mp4 | xargs -n1 basename | tr '\n' ' ')"
