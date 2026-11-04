#!/bin/bash
# Lève à l'exécution le plafond fp16/bf16 -> accumulation fp32 des GeForce Turing
# (gpu-unlock PR #294, module gpu_unlock), carte par carte, sans option noyau :
# détache nvidia de la carte, charge le module (il agit puis rend la main), rattache nvidia.
# Contrôle de santé : si nvidia ne revoit pas toutes les cartes, on retire le module et on rattache.
# Désactiver : sudo touch /etc/nexora/gpu-unlock.disabled  (puis redémarrer la VM)
TARGETS="${NEXORA_GPU_UNLOCK_TARGETS:-0000:01:00.0 0000:02:00.0}"
log() { logger -t nexora-gpu-unlock -- "$*"; echo "$*"; }
[ -e /etc/nexora/gpu-unlock.disabled ] && { log "désactivé (/etc/nexora/gpu-unlock.disabled)"; exit 0; }
NDEV=$(echo $TARGETS | wc -w)
for i in $(seq 60); do
  ok=1; for d in $TARGETS; do [ -e /sys/bus/pci/drivers/nvidia/$d ] || ok=0; done
  [ $ok = 1 ] && break; sleep 1
done
[ $ok = 1 ] || { log "nvidia non attaché aux cartes : abandon"; exit 1; }
if fuser -s /dev/nvidia[0-9]* 2>/dev/null; then log "des processus utilisent les GPU : abandon (arrêter les services d'abord)"; exit 1; fi
PERSIST=0; systemctl is-active -q nvidia-persistenced && { PERSIST=1; systemctl stop nvidia-persistenced; }
rmmod gpu_unlock 2>/dev/null
for d in $TARGETS; do
  [ -e /sys/bus/pci/drivers/nvidia/$d ] && echo $d > /sys/bus/pci/drivers/nvidia/unbind
  rmmod gpu_unlock 2>/dev/null
  if timeout 90 modprobe gpu_unlock targets=$d; then
    log "$d : gpu_unlock chargé ($(dmesg | grep "$d: gpu_unlock: unlocked" | tail -1 | wc -l) débloquée)"
  else
    log "$d : échec de gpu_unlock (code $?)"
  fi
  rmmod gpu_unlock 2>/dev/null
  echo $d > /sys/bus/pci/drivers/nvidia/bind 2>/dev/null || log "$d : rattachement nvidia refusé"
done
sleep 2
N=$(nvidia-smi -L 2>/dev/null | grep -c '^GPU')
if [ "$N" != "$NDEV" ]; then
  log "SANTÉ : nvidia voit $N cartes sur $NDEV : retour arrière"
  rmmod gpu_unlock 2>/dev/null
  for d in $TARGETS; do [ -e /sys/bus/pci/drivers/nvidia/$d ] || echo $d > /sys/bus/pci/drivers/nvidia/bind 2>/dev/null; done
  sleep 2; N=$(nvidia-smi -L 2>/dev/null | grep -c '^GPU')
  [ "$N" = "$NDEV" ] || { rmmod nvidia_uvm nvidia_drm nvidia_modeset nvidia 2>/dev/null; modprobe nvidia; modprobe nvidia_uvm; sleep 2; N=$(nvidia-smi -L 2>/dev/null | grep -c '^GPU'); }
  log "SANTÉ après retour arrière : $N/$NDEV cartes"
  [ $PERSIST = 1 ] && systemctl start nvidia-persistenced
  exit 1
fi
[ $PERSIST = 1 ] && systemctl start nvidia-persistenced
log "OK : $N cartes présentes après déblocage"
exit 0
