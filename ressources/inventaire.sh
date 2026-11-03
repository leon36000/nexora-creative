#!/usr/bin/env bash
# Inventaire des ressources Nexora (LECTURE SEULE : ne modifie, ne supprime et ne crée rien).
# Usage : ressources/inventaire.sh [pc5|pc6|pc1|tout]   (défaut : tout)
# Dépend des alias SSH pc5-proxmox, pc1 et de nexora-pile/-creative/-workstudio (voir docs/ENVIRONNEMENTS.md).
# Marqueurs : [!] à traiter, [ok] conforme. Règles : docs/RESSOURCES.md.
set -u
export LC_ALL=C
CIBLE="${1:-tout}"
DATA="${NEXORA_DATA:-$HOME/nexora-creative-data}"
PC1_RACINE="/run/media/pc1/Infrastructure/NexoraStudioWork"
RETENTION_JOURS=14
SSH="ssh -o ConnectTimeout=8 -o BatchMode=yes"
t() { printf '\n== %s\n' "$*"; }
drapeau() { printf '[!] %s\n' "$*"; }
ok() { printf '[ok] %s\n' "$*"; }

# Volumes logiques connus (registre : docs/RESSOURCES.md). Tout autre LV est signalé orphelin.
LV_CONNUS="root swap data backups ssd-1tb nexora-archives vm-201-disk-0 vm-202-disk-0 vm-203-disk-0 base-9000-disk-0 vm-201-cloudinit vm-202-cloudinit vm-203-cloudinit vm-9000-cloudinit vm-9100-cloudinit vm-9100-disk-0"

pc5() {
  t "pc5 (Proxmox pve) : machines virtuelles, étiquettes, allocation"
  $SSH pc5-proxmox 'bash -s' <<'DISTANT'
for conf in /etc/pve/qemu-server/*.conf; do
  v=$(basename "$conf" .conf)
  nom=$(awk -F': ' '$1=="name"{print $2}' "$conf")
  tags=$(awk -F': ' '$1=="tags"{print $2}' "$conf")
  desc=$(grep -c '^#' "$conf")
  ram=$(awk -F': ' '$1=="memory"{print $2}' "$conf")
  cpu=$(awk -F': ' '$1=="cores"{print $2}' "$conf")
  etat=$(qm status "$v" 2>/dev/null | awk '{print $2}')
  printf '%-5s %-22s %-8s RAM %6s Mo  vCPU %-2s tags=[%s]\n' "$v" "$nom" "$etat" "$ram" "$cpu" "$tags"
  [ -z "$tags" ] && printf '[!] VM %s sans étiquette (tags)\n' "$v"
  [ "$desc" -eq 0 ] && printf '[!] VM %s sans description (propriétaire/usage/date)\n' "$v"
done
echo; echo "-- stockages"; pvesm status
echo; echo "-- volumes logiques (taille virtuelle, occupation réelle)"
lvs --units g --noheadings -o vg_name,lv_name,lv_size,data_percent,pool_lv 2>/dev/null | awk '{printf "%-8s %-20s %9s  occupé %s%%\n",$1,$2,$3,$4}'
echo; echo "-- points de montage dédiés"; df -h /mnt/nexora-archives /mnt/nexora-backups / 2>/dev/null
echo; echo "-- sauvegardes vzdump (rétention keep-last=1)"; pvesm list backup-nvme0 2>/dev/null | awk 'NR>1{printf "%s  %.1f Go\n",$1,$4/1073741824}'
grep -A4 '^dir: backup-nvme0' /etc/pve/storage.cfg | grep prune
n=$(pvesm list backup-nvme0 2>/dev/null | awk 'NR>1' | wc -l); [ "$n" -gt 3 ] && printf '[!] %s sauvegardes sur NVMe (attendu : 3, une par VM)\n' "$n"
echo; echo "-- ISO / gabarits / disques orphelins"
ls -la /var/lib/vz/template/iso /var/lib/vz/template/cache 2>/dev/null | awk 'NF>8{print}'
DISTANT
  # LV non enregistrés
  for lv in $($SSH pc5-proxmox "lvs --noheadings -o lv_name" 2>/dev/null); do
    case " $LV_CONNUS " in *" $lv "*) ;; *) drapeau "volume logique non enregistré (orphelin ?) : $lv";; esac
  done
  t "pc5 : occupation dans les VM (disque, mémoire, Docker)"
  for h in nexora-pile nexora-creative nexora-workstudio; do
    printf -- '-- %s\n' "$h"
    $SSH "$h" 'df -h / | tail -1; free -m | sed -n 2p; docker system df 2>/dev/null | sed -n 1,5p' 2>&1 | sed 's/^/   /'
  done
  t "pc5 : archives par produit (convention <produit>/<année>-<mois>/…)"
  $SSH pc5-proxmox 'cd /mnt/nexora-archives && du -sh * 2>/dev/null; find . -maxdepth 1 -mindepth 1 -type d ! -name lost+found ! -name creative ! -name pc1 ! -name pc6 ! -name opsys ! -name workstudio ! -name site | sed "s/^/[!] dossier hors convention : /"; test -f MANIFESTE.md && echo "[ok] MANIFESTE.md présent" || echo "[!] MANIFESTE.md absent"'
}

pc6() {
  t "pc6 : disque"
  df -h / | tail -1
  t "pc6 : $DATA (par dossier, README et ancienneté)"
  for d in "$DATA"/*/; do
    n=$(basename "$d"); s=$(du -sh "$d" 2>/dev/null | cut -f1)
    vieux=$(find "$d" -type f -mtime +"$RETENTION_JOURS" 2>/dev/null | head -1)
    r="sans README"; [ -f "$d/README.md" ] && r="README"
    printf '%-24s %7s  %s\n' "$n" "$s" "$r"
  done
  if [ -f "$DATA/README.md" ]; then ok "README racine présent (registre des dossiers)"; else drapeau "README racine absent"; fi
  # Dossiers d'expériences et de brouillons : retenue maximale 14 jours
  for d in work outputs output rendus; do
    [ -d "$DATA/$d" ] || continue
    n=$(find "$DATA/$d" -type f -mtime +"$RETENTION_JOURS" 2>/dev/null | wc -l)
    [ "$n" -gt 0 ] && drapeau "$d : $n fichier(s) de plus de $RETENTION_JOURS jours (finals à archiver sur pc5, brouillons à supprimer)"
  done
  t "pc6 : Docker par projet (conteneurs, volumes, images)"
  docker ps -a --format '{{.Label "com.docker.compose.project"}}|{{.Names}}|{{.Status}}' | awk -F'|' '{p=($1==""?"(hors compose)":$1); n[p]++} END{for(p in n) printf "%-26s %3d conteneur(s)\n",p,n[p]}' | sort
  docker system df | sed -n 1,4p
  nd=$(docker volume ls -f dangling=true -q | wc -l)
  [ "$nd" -gt 0 ] && drapeau "$nd volume(s) Docker orphelin(s) : docker volume ls -f dangling=true (anonymes de plus de 24 h supprimables)" || ok "aucun volume Docker orphelin"
  ni=$(docker image ls -f dangling=true -q | wc -l)
  [ "$ni" -gt 0 ] && drapeau "$ni image(s) Docker sans nom" || ok "aucune image Docker sans nom"
  ne=$(docker ps -a -f status=exited -q | wc -l)
  [ "$ne" -gt 0 ] && drapeau "$ne conteneur(s) arrêté(s) : vérifier s'ils servent encore"
  t "pc6 : caches régénérables (> 200 Mo signalés)"
  for c in "$HOME/.cache/uv" "$HOME/.cache/pip" "$HOME/.npm/_cacache" "$HOME/.bun/install/cache" "$HOME/.cache/huggingface" "$HOME/.cache/ms-playwright" "$HOME/.cache/pc5-mass-ingestion"; do
    [ -e "$c" ] || continue
    k=$(du -sk "$c" 2>/dev/null | cut -f1)
    if [ "$k" -gt 204800 ]; then printf '[!] %-48s %6.1f Go\n' "$c" "$(awk "BEGIN{print $k/1048576}")"; fi
  done
  t "pc6 : /tmp (plus de 2 jours)"
  find /tmp -maxdepth 1 -mindepth 1 -user "$USER" -mtime +2 2>/dev/null | head -20 | sed 's/^/[!] /'
  t "pc6 : copies de travail Nexora hors dépôt principal"
  for d in "$HOME/Desktop"/Nexora*/; do printf '%-45s %s\n' "$d" "$(du -sh "$d" 2>/dev/null | cut -f1)"; done
}

pc1() {
  t "pc1 : $PC1_RACINE"
  $SSH pc1 "df -h $PC1_RACINE | tail -1; cd $PC1_RACINE/minimax-h3 && du -sh * 2>/dev/null | sort -rh | head -12; echo; find output -type f -mtime +$RETENTION_JOURS 2>/dev/null | wc -l | sed 's/^/fichiers de sortie > $RETENTION_JOURS j : /'; du -sh ~/.cache/pip ~/.cache/tracker3 2>/dev/null; lsof -iTCP -sTCP:LISTEN -nP 2>/dev/null | grep -E ':(18288|18388) ' | awk '{print \"ComfyUI en écoute : \" \$9}'" 2>&1
}

case "$CIBLE" in
  pc5) pc5;; pc6) pc6;; pc1) pc1;;
  tout) pc5; pc6; pc1;;
  *) echo "usage : $0 [pc5|pc6|pc1|tout]" >&2; exit 2;;
esac
printf '\nInventaire terminé le %s (lecture seule).\n' "$(date +%F\ %H:%M)"
