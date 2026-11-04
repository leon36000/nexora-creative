#!/bin/bash
# Dernière étape, sans intervention : quand les quatre films finaux existent, mesures communes, rédaction de COMPARAISON.md par un
# sous-agent gemini-eleve (Argon Flex, effort élevé) à partir des seules données (mesures, juges, coûts, GPU, dossiers), commit et push.
set -u
R=/home/pc6/Desktop/NexoraCreative-opsys-ultime
C=$R/marketing/nexora/campagne-films/opsys-ultime
W=/home/pc6/nexora-creative-data/work/opsys-ultime
until [ "$(grep -l 'FINI' $W/apres-revision-{opus,deepseek,muse,gemini}.log 2>/dev/null | wc -l)" -ge 4 ]; do sleep 120; done
cd "$C/chaine" && python3 comparer.py > /dev/null 2>&1
D=$W/sa/comparaison; mkdir -p "$D/donnees"
cp $W/comparaison.json "$D/donnees/"
for e in opus deepseek muse gemini; do
  mkdir -p "$D/donnees/$e"
  cp "$C/equipes/$e/DOSSIER.md" "$C/equipes/$e/REVISION.json" "$D/donnees/$e/" 2>/dev/null
  cp $W/$e/montage/*.juge.json "$D/donnees/$e/" 2>/dev/null
  cp $W/$e/musique/evaluation-long.json "$D/donnees/$e/" 2>/dev/null
  cp $W/$e/juge-reel.json "$D/donnees/$e/" 2>/dev/null
  cp $W/$e/revue/REVUE.md "$D/donnees/$e/" 2>/dev/null
done
"$R/outils/sous-agents/cout.sh" --run ou > "$D/donnees/couts-sous-agents.txt" 2>&1
cp "$C/BRIEF.md" "$C/casting/PALETTE.md" "$D/donnees/"
cat > "$D/PROMPT.md" <<'EOF'
Tu es le rapporteur indépendant du concours du « film ultime » OPSYS-AI (quatre équipes : opus, deepseek, muse, gemini ; même brief,
même chaîne, même budget ; voir donnees/BRIEF.md §8). Écris `COMPARAISON.md` (français, clair, sans jargon) uniquement à partir des
données de `donnees/` : comparaison.json (durées, plans, secondes par plan, part de narration, sonie, GPU, jetons), les juges de
machine (*.juge.json : juge audio-vidéo Gemini sur le film mixé ; juge-reel.json : réel contre synthèse par plan ; evaluation-long.json :
musiques candidates), REVUE.md, DOSSIER.md, REVISION.json, couts-sous-agents.txt.
Contenu exigé : (1) un tableau des quatre films : titre, chemin du film long et de la version courte (champ « fichier » de
comparaison.json ; copies sur pc1 dans ~/Bureau/Nexora-Livrables/TOUS-LES-FILMS/opsys-ultime/<equipe>/montage/), durée, coût en
jetons (USD, requêtes ; l'équipe opus tourne sur l'abonnement Claude : coût non mesuré par la passerelle, le dire), temps GPU 5090 et
GB10 ; (2) pour chaque film, une note sévère sur 10 par critère : spectacle, clarté des fonctions, voix, musique, rythme, crédibilité,
et la moyenne, en t'appuyant sur les juges et les mesures mais en retirant 1 point aux notes des juges (nos juges et nos auto-notes ont
été trop généreux de 1 à 3 points) et en le disant ; (3) forces et faiblesses de chaque film en 3 lignes ; (4) ta recommandation (un
film, et ce qu'il faudrait encore pour atteindre 8/10, la porte du fondateur) ; (5) ce qui limite encore la qualité (moteurs, voix,
musique, GPU, synchronisation labiale). N'invente aucun chiffre : si une donnée manque, écris « non mesuré ». Pas de juridique.
EOF
cd "$R" && SA_TIMEOUT=2400 SA_TAG=rapport SA_OUT=$W/sa/runs/comparaison outils/sous-agents/sous-agent.sh -w gemini-eleve "$D/PROMPT.md" "$D" 60 3.0
cp "$D/COMPARAISON.md" "$C/COMPARAISON.md" 2>/dev/null
cd "$R" && git add "$C/COMPARAISON.md" "$C/HANDOFF.md" "$C/chaine" "$C/casting" "$C/equipes/opus" "$C/equipes/deepseek" "$C/equipes/muse" "$C/equipes/gemini" && git commit -q -m "Film ultime OPSYS-AI : films finaux des quatre équipes et COMPARAISON.md (rapporteur gemini-eleve, données de la chaîne)" -m "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>" && git push -q gitlab feat/opsys-ultime
echo "$(date +%T) COMPARAISON.md écrite et poussée"
