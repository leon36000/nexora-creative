#!/usr/bin/env bash
# À lancer par le fondateur depuis le terminal normal de pc6.
# Documentation uniquement : aucun service, secret ou push.
set -euo pipefail
repo='/home/pc6/Desktop/NexoraCreative-doc-passation'
maitre='/home/pc6/Desktop/NEXORA-PASSATION-AGENTS.md'
annexes='/home/pc6/Desktop/NEXORA-PASSATION-ANNEXES'

branche=$(git -C "$repo" symbolic-ref --quiet --short HEAD)
if [[ "$branche" != 'docs/passation-maj' ]]; then
  echo 'Arrêt : la branche attendue est docs/passation-maj.' >&2
  exit 1
fi
if ! git -C "$repo" diff --cached --quiet; then
  echo 'Arrêt : des changements sont déjà indexés. Les examiner avant de continuer.' >&2
  exit 1
fi
cmp -s "$maitre" "$repo/docs/PASSATION-AGENTS.md"
for nom in REVUE-CATALOGUE-FONDATEUR.md REVUE-EXTRACTION-FONDATEUR.md REVUE-ETAT-DISQUE.md REVUE-AUDIT-CHANTIERS.md REVUE-AUDIT-DOCUMENTAIRE.md REVUE-SOURCES.md REVUE-RAPPORT.md; do
  cmp -s "$annexes/$nom" "$repo/docs/passation/$nom"
done
cmp -s /home/pc6/Desktop/PROMPT-POUR-CODEX.md "$repo/docs/passation/PROMPT-POUR-CODEX.md"
git -C "$repo" diff --check
git -C "$repo" add -- \
  docs/PASSATION-AGENTS.md docs/JOURNAL.md \
  docs/passation/PROMPT-POUR-CODEX.md \
  docs/passation/REVUE-CATALOGUE-FONDATEUR.md \
  docs/passation/REVUE-EXTRACTION-FONDATEUR.md \
  docs/passation/REVUE-ETAT-DISQUE.md \
  docs/passation/REVUE-AUDIT-CHANTIERS.md \
  docs/passation/REVUE-AUDIT-DOCUMENTAIRE.md \
  docs/passation/REVUE-SOURCES.md \
  docs/passation/REVUE-RAPPORT.md \
  docs/passation/commiter-passation.sh
git -C "$repo" diff --cached --check
git -C "$repo" commit \
  -m 'Passation : revue exhaustive, preuves et reprise Codex' \
  -m 'Co-Authored-By: GPT-6.1 Sol <noreply@openai.com>'
git -C "$repo" log -1 --format='%h %s%n%b'
echo 'Commit local créé. Aucun push effectué.'
