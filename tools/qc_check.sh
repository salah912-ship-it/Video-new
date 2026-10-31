#!/usr/bin/env bash
# Technical QC for the final master. Usage: tools/qc_check.sh 08_render/<file>.mp4
set -euo pipefail
F="$1"
echo "## Streams"; ffprobe -v error -show_entries stream=codec_name,profile,width,height,r_frame_rate,nb_frames,pix_fmt,sample_rate,channels,duration -show_entries format=duration,size,bit_rate -of compact "$F"
echo "## Black frames (pix_th 0.06, >=0.1 s)"; ffmpeg -nostats -i "$F" -vf "blackdetect=d=0.1:pix_th=0.06" -an -f null - 2>&1 | grep -o "black_start.*" || echo "none"
echo "## Frozen frames (>=0.6 s)"; ffmpeg -nostats -i "$F" -vf "freezedetect=n=0.001:d=0.6" -an -f null - 2>&1 | grep -o "freeze_start.*" || echo "none"
echo "## Loudness"; ffmpeg -nostats -i "$F" -vn -af ebur128=peak=true -f null - 2>&1 | grep -E "^\s+(I|LRA|Peak):" || true
