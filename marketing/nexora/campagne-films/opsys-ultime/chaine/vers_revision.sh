#!/bin/bash
# Prépare et lance la ronde de révision d'une équipe dès que ses plans 16:9 sont tournés :
# premier montage (long et court, brouillon), juge audio-vidéo, juge « réel contre synthèse », REVUE.md et planches,
# copie du matériel dans le dossier de l'équipe (bac à sable), puis session de révision du sous-agent (sauf « opus »).
# Usage : vers_revision.sh <equipe>
set -u
EQ=$1
C=/home/pc6/Desktop/NexoraCreative-opsys-ultime/marketing/nexora/campagne-films/opsys-ultime
W=/home/pc6/nexora-creative-data/work/opsys-ultime
SA=$W/sa/$EQ
cd "$C/chaine" || exit 1
attendus=$(python3 -c "import json;d=json.load(open('$C/equipes/$EQ/dossier.json'));print(sum(1 for p in d['plans'] if p.get('format','16:9')=='16:9'))")
until [ "$(ls $W/$EQ/plans/*-r1.mp4 2>/dev/null | grep -v -- '-v-r1' | wc -l)" -ge "$attendus" ]; do sleep 60; done
echo "$(date +%T) $EQ : $attendus plans 16:9 tournés"
python3 juge.py reel "$EQ" > "$W/$EQ-juge-reel.log" 2>&1
python3 monter.py "$EQ" long --brouillon --jobs 12 > "$W/$EQ-montage1.log" 2>&1
python3 monter.py "$EQ" court --brouillon --jobs 12 >> "$W/$EQ-montage1.log" 2>&1
python3 juge.py film "$W/$EQ/montage/$EQ-long-brouillon.mp4" "Premier montage (brouillon) de la publicité OPSYS-AI de l'équipe $EQ." > "$W/$EQ-juge-film.log" 2>&1
python3 revue.py "$EQ" > /dev/null 2>&1
echo "$(date +%T) $EQ : premier montage, juges et REVUE prêts"
if [ "$EQ" != opus ]; then
  mkdir -p "$SA/revue" "$SA/reference" "$SA/casting"
  cp "$W/$EQ/revue/"* "$SA/revue/"
  cp "$C/casting/PALETTE.md" "$C/casting/palette.json" "$C/casting/MOTEURS.md" "$SA/casting/"
  cp "$C/chaine/valider.py" "$C/chaine/INCRUSTATIONS.md" "$SA/chaine/"
  cp "$C/BRIEF.md" "$SA/"
  [ -f /home/pc6/Desktop/NexoraCreative-opsys-ultime/recherche/26-recette-live-action.md ] && cp /home/pc6/Desktop/NexoraCreative-opsys-ultime/recherche/26-recette-live-action.md "$SA/reference/"
  cp "$C/equipes/$EQ/CORRECTIONS.md" "$SA/equipes/$EQ/" 2>/dev/null
  sed "s/{EQUIPE}/$EQ/g" "$C/chaine/prompt-revision.md" > "$SA/PROMPT-REVISION.md"
  case $EQ in gemini) MOD=gemini-eleve; EF="";; *) MOD=$EQ; EF=max;; esac
  cd /home/pc6/Desktop/NexoraCreative-opsys-ultime
  SA_TIMEOUT=4200 SA_EFFORT=$EF SA_TAG=ou SA_OUT=$W/sa/runs/$EQ-revision outils/sous-agents/sous-agent.sh -w $MOD "$SA/PROMPT-REVISION.md" "$SA" 150 6.0
  echo "$(date +%T) $EQ : session de révision terminée : $(cat $W/sa/runs/$EQ-revision/summary.txt | cut -c1-160)"
fi
