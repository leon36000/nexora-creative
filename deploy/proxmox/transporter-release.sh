#!/usr/bin/env bash
# Transporte un artefact CI vérifié et ses outils Git vers un dossier VM exclusif.
set -euo pipefail
if [ "$#" -ne 6 ]; then
  printf '%s\n' 'usage : transporter-release.sh DEPOT SHA_GIT ARTEFACT SHA256 DOSSIER_LOCAL_NEUF IDENTIFIANT' >&2
  exit 2
fi
DEPOT="$1"; REVISION="$2"; ARTEFACT="$3"; SHA_ARTEFACT="$4"; LOCAL="$5"; ID="$6"
[[ "$REVISION" =~ ^[0-9a-f]{40}$ && "$SHA_ARTEFACT" =~ ^[0-9a-f]{64}$ ]] || { printf '%s\n' 'Empreintes invalides' >&2; exit 2; }
[[ "$ID" =~ ^[a-z0-9][a-z0-9-]{7,63}$ ]] || { printf '%s\n' 'Identifiant invalide' >&2; exit 2; }
[[ "$LOCAL" == /* ]] || { printf '%s\n' 'Dossier local absolu requis' >&2; exit 2; }
[[ "${ARTEFACT##*/}" != .env* && "${ARTEFACT##*/}" != .npmrc ]] || { printf '%s\n' 'Nom artefact interdit' >&2; exit 2; }
[ -f "$ARTEFACT" ] && [ ! -L "$ARTEFACT" ] || { printf '%s\n' 'Artefact ordinaire requis' >&2; exit 2; }
[ "$(git -C "$DEPOT" rev-parse "${REVISION}^{commit}")" = "$REVISION" ] || exit 1
[ "$(sha256sum "$ARTEFACT" | cut -d ' ' -f 1)" = "$SHA_ARTEFACT" ] || { printf '%s\n' 'Empreinte artefact différente' >&2; exit 1; }
env -i PATH=/usr/local/bin:/usr/bin:/bin HOME=/nonexistent python3 -B - "$ARTEFACT" "$REVISION" <<'PY'
import sys, tarfile
with tarfile.open(sys.argv[1], 'r:') as t:
    matches = [m for m in t if m.name == 'release/CI_COMMIT_SHA']
    if len(matches) != 1 or not matches[0].isfile() or matches[0].size > 64:
        raise SystemExit('reçu Git absent ou ambigu')
    with t.extractfile(matches[0]) as f:
        if f.read().decode('ascii').strip() != sys.argv[2]:
            raise SystemExit('SHA Git de l’artefact différent')
PY
mkdir -m 700 "$LOCAL"
for fichier in preparer_release.py transaction_release.py livrer_release.py mettre-a-jour-creative.sh; do
  git -C "$DEPOT" show "${REVISION}:deploy/proxmox/${fichier}" > "$LOCAL/$fichier"
done
cp -- "$ARTEFACT" "$LOCAL/release.tar"
printf '%s\n' "$SHA_ARTEFACT" > "$LOCAL/release.sha256"
printf '%s\n' "$REVISION" > "$LOCAL/commit.sha"
(cd "$LOCAL" && sha256sum release.tar release.sha256 commit.sha preparer_release.py transaction_release.py livrer_release.py mettre-a-jour-creative.sh > SHA256SUMS)
DISTANT="/srv/creative/livraisons/$ID"
ssh -o BatchMode=yes nexora-creative "test -d /srv/creative && test ! -L /srv/creative && for p in /srv/creative/livraisons /srv/creative/releases /srv/creative/backups; do { test -d \"\$p\" || mkdir -m 700 \"\$p\"; } && test ! -L \"\$p\" || exit 1; done && mkdir -m 700 '$DISTANT'"
tar -C "$LOCAL" -cf - release.tar release.sha256 commit.sha preparer_release.py transaction_release.py livrer_release.py mettre-a-jour-creative.sh SHA256SUMS | \
  ssh -o BatchMode=yes nexora-creative "tar --keep-old-files -xf - -C '$DISTANT'"
ssh -o BatchMode=yes nexora-creative "cd '$DISTANT' && sha256sum -c SHA256SUMS"
printf 'Artefact et outils vérifiés : %s\n' "$DISTANT"
printf "Importer : ssh -T nexora-creative 'env -i PATH=/usr/local/bin:/usr/bin:/bin HOME=/nonexistent PYTHONDONTWRITEBYTECODE=1 python3 -B %s/preparer_release.py importer %s/release.tar %s %s /srv/creative/releases/%s'\n" "$DISTANT" "$DISTANT" "$SHA_ARTEFACT" "$REVISION" "$ID"
printf "Plan : ssh -T nexora-creative 'env -i PATH=/usr/local/bin:/usr/bin:/bin HOME=/nonexistent PYTHONDONTWRITEBYTECODE=1 python3 -B %s/livrer_release.py plan /srv/creative/releases/%s /srv/creative %s/plan.json'\n" "$DISTANT" "$ID" "$DISTANT"
printf "Activer après revue : ssh -T nexora-creative 'sudo -n env -i PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin HOME=/nonexistent PYTHONDONTWRITEBYTECODE=1 python3 -B %s/livrer_release.py activer /srv/creative/releases/%s /srv/creative /srv/creative/data /srv/creative/backups/%s %s/plan.json'\n" "$DISTANT" "$ID" "$ID" "$DISTANT"
printf "Retour : ssh -T nexora-creative 'sudo -n env -i PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin HOME=/nonexistent PYTHONDONTWRITEBYTECODE=1 python3 -B %s/livrer_release.py retour /srv/creative /srv/creative/data /srv/creative/backups/%s'\n" "$DISTANT" "$ID"
