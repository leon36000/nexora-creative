#!/usr/bin/env bash
# Nexora : limite de puissance (GPU à 80 % de leur plafond d'usine, CPU à 87 % de leur fréquence maximale).
# Raison : le disjoncteur a sauté quand tous les PC tournaient à plein régime ; économie d'électricité, de chaleur et d'usure.
# Appliqué au démarrage par nexora-limite-puissance.service. Pour revenir en arrière : systemctl disable --now nexora-limite-puissance, puis redémarrer.
GPU_PCT=${GPU_PCT:-80}
CPU_PCT=${CPU_PCT:-87}

# GPU NVIDIA
if [ -z "$GPU_SKIP" ] && command -v nvidia-smi >/dev/null 2>&1; then
  nvidia-smi -pm 1 >/dev/null 2>&1
  for i in $(nvidia-smi --query-gpu=index --format=csv,noheader 2>/dev/null); do
    d=$(nvidia-smi -i "$i" --query-gpu=power.default_limit --format=csv,noheader,nounits 2>/dev/null | cut -d. -f1)
    case "$d" in ''|*[!0-9]*) echo "GPU $i : plafond non réglable"; continue;; esac
    t=$((d * GPU_PCT / 100))
    nvidia-smi -i "$i" -pl "$t" >/dev/null 2>&1 && echo "GPU NVIDIA $i : $d W -> $t W" || echo "GPU NVIDIA $i : échec du réglage à $t W"
  done
fi

# GPU AMD (amdgpu, hwmon)
for h in /sys/class/drm/card[0-9]*/device/hwmon/hwmon*; do
  [ -z "$GPU_SKIP" ] || continue
  [ -f "$h/power1_cap" ] || continue
  df=0; for essai in 1 2 3 4 5 6; do df=$(cat "$h/power1_cap_default" 2>/dev/null || echo 0); [ "$df" -gt 0 ] 2>/dev/null && break; sleep 2; done
  mn=$(cat "$h/power1_cap_min" 2>/dev/null || echo 0)
  if ! [ "$df" -gt 0 ] 2>/dev/null; then echo "GPU AMD $h : plafond illisible, non modifié"; continue; fi
  t=$((df * GPU_PCT / 100)); [ "$t" -lt "$mn" ] && t=$mn
  echo "$t" > "$h/power1_cap" 2>/dev/null && echo "GPU AMD $h : $((df/1000000)) W -> $((t/1000000)) W" || echo "GPU AMD $h : échec"
done

# CPU
P=/sys/devices/system/cpu/intel_pstate
if [ -w "$P/max_perf_pct" ]; then
  echo "$CPU_PCT" > "$P/max_perf_pct" && echo "CPU intel_pstate : maximum $CPU_PCT %"
else
  n=0
  for c in /sys/devices/system/cpu/cpu[0-9]*/cpufreq; do
    m=$(cat "$c/cpuinfo_max_freq" 2>/dev/null) || continue
    echo $((m * CPU_PCT / 100)) > "$c/scaling_max_freq" 2>/dev/null && n=$((n + 1))
  done
  echo "CPU cpufreq : $n coeurs à $CPU_PCT % de la fréquence maximale"
fi
exit 0
