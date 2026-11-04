#!/usr/bin/env bash
# Met à jour Nexora Creative sur la VM Proxmox nexora-creative : construit le Mode Studio ici, copie le code, installe
# les dépendances et reconstruit l'interface sur la VM (amd64), puis redémarre le service. Ne touche ni à la base ni aux
# rendus de la VM, ni à /etc/nexora/creative.env.
set -euo pipefail
ICI="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
VM="${NEXORA_CREATIVE_VM:-nexora-creative}"
echo "== Mode Studio : construction"
(cd "$ICI/mode-studio" && node_modules/.bin/vp build >/dev/null)
echo "== copie"
rsync -a --delete --exclude node_modules --exclude dist --exclude .env --exclude '*.log' "$ICI/app/" "$VM:/srv/creative/app/"
rsync -a --delete "$ICI/mode-studio/dist/" "$VM:/srv/creative/mode-studio/dist/"
echo "== VM : dépendances, interface, redémarrage"
ssh "$VM" 'cd /srv/creative/app && npm ci --no-audit --no-fund >/dev/null 2>&1 && npx vite build >/dev/null 2>&1 && sudo systemctl restart nexora-creative'
echo "== VM : impression (Chromium, Ghostscript, poppler ; idempotent, voir IMPRESSION-VM.md)"
ssh "$VM" 'cd /srv/creative/app && (ls ~/.cache/ms-playwright 2>/dev/null | grep -q chromium || { npx playwright-core install chromium >/dev/null 2>&1 && sudo npx playwright-core install-deps chromium >/dev/null 2>&1; }); (command -v gs >/dev/null && command -v pdftocairo >/dev/null) || sudo apt-get install -y ghostscript poppler-utils >/dev/null 2>&1; true'
for i in $(seq 1 30); do
  if ssh "$VM" 'curl -sf -m 3 http://127.0.0.1:3161/api/nexora/etat' >/dev/null 2>&1; then echo "== en ligne"; ssh "$VM" 'curl -s http://127.0.0.1:3161/api/nexora/etat'; echo; exit 0; fi
  sleep 2
done
echo "Le service ne répond pas après la mise à jour." >&2; exit 1
