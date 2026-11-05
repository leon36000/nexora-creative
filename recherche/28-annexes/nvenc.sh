#!/bin/bash
# Banc NVENC (essais-20261104) : temps, taille, SSIM/PSNR contre la source
cd /srv/nexora-gpu/essais-20261104
SRC=src.mp4
mesure() { # nom, args...
  local nom=$1; shift
  local out=out/$nom.mp4
  local t0=$(date +%s.%N)
  ffmpeg -v error -y -benchmark "$@" -an $out 2> out/$nom.log
  local t1=$(date +%s.%N)
  local sz=$(stat -c %s $out)
  local dur=$(ffprobe -v error -show_entries format=duration -of csv=p=0 $out)
  local kbps=$(python3 -c "print(round($sz*8/$dur/1000))")
  local m=$(ffmpeg -v info -i $out -i $SRC -lavfi "[0:v][1:v]ssim;[0:v][1:v]psnr" -f null - 2>&1 | grep -E "SSIM Y|PSNR y" | sed -E 's/.*All:([0-9.]+).*/ssim=\1/; s/.*average:([0-9.]+).*/psnr=\1/' | tr '\n' ' ')
  echo "$nom wall=$(python3 -c "print(round($t1-$t0,1))")s taille=$(python3 -c "print(round($sz/1e6,1))")Mo debit=${kbps}kbps $m"
}
case $1 in
x264) mesure x264_medium_crf18 -i $SRC -c:v libx264 -preset medium -crf 18 -pix_fmt yuv420p ;;
x264f) mesure x264_fast_crf18 -i $SRC -c:v libx264 -preset fast -crf 18 -pix_fmt yuv420p ;;
nv) # gpu preset codec
  g=$2; p=$3; c=$4; cq=$5
  extra=""
  mesure ${c}_g${g}_${p}_cq${cq} -i $SRC -c:v ${c}_nvenc -gpu $g -preset $p -tune hq -rc vbr -cq $cq -b:v 0 -spatial-aq 1 -temporal-aq 1 -rc-lookahead 20 -bf 3 -pix_fmt yuv420p ;;
nvhw) g=$2; p=$3; c=$4; cq=$5
  mesure ${c}_hwdec_g${g}_${p}_cq${cq} -hwaccel cuda -hwaccel_device $g -hwaccel_output_format cuda -i $SRC -c:v ${c}_nvenc -gpu $g -preset $p -tune hq -rc vbr -cq $cq -b:v 0 -spatial-aq 1 -temporal-aq 1 -rc-lookahead 20 -bf 3 ;;
esac
