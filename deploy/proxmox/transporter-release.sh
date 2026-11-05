#!/usr/bin/env bash
# Transporte une archive Git et ses outils vers un répertoire VM exclusif ; aucune activation.
set -euo pipefail
if [ "$#" -ne 4 ]; then
  printf '%s\n' 'usage : transporter-release.sh DEPOT SHA_GIT DOSSIER_LOCAL_NEUF IDENTIFIANT' >&2
  exit 2
fi
DEPOT="$1"; REVISION="$2"; LOCAL="$3"; ID="$4"
[[ "$REVISION" =~ ^[0-9a-f]{40}$ ]] || { printf '%s\n' 'SHA Git complet requis' >&2; exit 2; }
[[ "$ID" =~ ^[a-z0-9][a-z0-9-]{7,63}$ ]] || { printf '%s\n' 'Identifiant invalide' >&2; exit 2; }
[[ "$LOCAL" == /* ]] || { printf '%s\n' 'Dossier local absolu requis' >&2; exit 2; }
[ "$(git -C "$DEPOT" rev-parse "${REVISION}^{commit}")" = "$REVISION" ] || exit 1
mkdir -m 700 "$LOCAL"
for fichier in preparer_release.py transaction_release.py livrer_release.py mettre-a-jour-creative.sh; do
  git -C "$DEPOT" show "${REVISION}:deploy/proxmox/${fichier}" > "$LOCAL/$fichier"
done
env -i PATH=/usr/local/bin:/usr/bin:/bin HOME=/nonexistent PYTHONDONTWRITEBYTECODE=1 \
  python3 -B "$LOCAL/preparer_release.py" archive "$DEPOT" "$REVISION" "$LOCAL/archive.tar" > "$LOCAL/archive.sha256"
(cd "$LOCAL" && sha256sum archive.tar archive.sha256 preparer_release.py transaction_release.py livrer_release.py mettre-a-jour-creative.sh > SHA256SUMS)
DISTANT="/srv/creative/livraisons/$ID"
ssh -o BatchMode=yes nexora-creative "test -d /srv/creative && test ! -L /srv/creative && for p in /srv/creative/livraisons /srv/creative/releases /srv/creative/backups; do { test -d \"\$p\" || mkdir -m 700 \"\$p\"; } && test ! -L \"\$p\" || exit 1; done && mkdir -m 700 '$DISTANT'"
tar -C "$LOCAL" -cf - archive.tar archive.sha256 preparer_release.py transaction_release.py livrer_release.py mettre-a-jour-creative.sh SHA256SUMS | \
  ssh -o BatchMode=yes nexora-creative "tar --keep-old-files -xf - -C '$DISTANT'"
ssh -o BatchMode=yes nexora-creative "cd '$DISTANT' && sha256sum -c SHA256SUMS"
printf 'Archive et outils vérifiés : %s\n' "$DISTANT"
SHA_ARCHIVE="$(cat "$LOCAL/archive.sha256")"
printf 'SHA archive : %s\n' "$SHA_ARCHIVE"
printf "Construire : ssh -T nexora-creative 'env -i PATH=/usr/local/bin:/usr/bin:/bin HOME=/nonexistent PYTHONDONTWRITEBYTECODE=1 python3 -B %s/preparer_release.py construire %s/archive.tar %s /srv/creative/releases/%s'\n" "$DISTANT" "$DISTANT" "$SHA_ARCHIVE" "$ID"
printf "Plan : ssh -T nexora-creative 'env -i PATH=/usr/local/bin:/usr/bin:/bin HOME=/nonexistent PYTHONDONTWRITEBYTECODE=1 python3 -B %s/livrer_release.py plan /srv/creative/releases/%s /srv/creative %s/plan.json'\n" "$DISTANT" "$ID" "$DISTANT"
printf "Activer après revue : ssh -T nexora-creative 'sudo -n env -i PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin HOME=/nonexistent PYTHONDONTWRITEBYTECODE=1 python3 -B %s/livrer_release.py activer /srv/creative/releases/%s /srv/creative /srv/creative/data /srv/creative/backups/%s %s/plan.json'\n" "$DISTANT" "$ID" "$ID" "$DISTANT"
printf "Retour : ssh -T nexora-creative 'sudo -n env -i PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin HOME=/nonexistent PYTHONDONTWRITEBYTECODE=1 python3 -B %s/livrer_release.py retour /srv/creative /srv/creative/data /srv/creative/backups/%s'\n" "$DISTANT" "$ID"
