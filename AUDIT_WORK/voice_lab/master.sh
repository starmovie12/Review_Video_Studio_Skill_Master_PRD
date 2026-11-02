#!/usr/bin/env bash
# usage: master.sh in.wav out.wav "<pre-chain or empty>"   (two-pass loudnorm I=-14 TP=-1.5 LRA=11, 48k stereo)
set -euo pipefail
in="$1"; out="$2"; pre="${3:-}"
base="aformat=sample_rates=48000:channel_layouts=stereo"
chain="$base"; [ -n "$pre" ] && chain="$base,$pre"
j=$(ffmpeg -hide_banner -nostats -i "$in" -af "$chain,loudnorm=I=-14:TP=-1.5:LRA=11:print_format=json" -f null - 2>&1 | awk '/^\{/,/^\}/')
gi(){ echo "$j" | python3 -c "import json,sys; print(json.load(sys.stdin)['$1'])"; }
ffmpeg -hide_banner -v error -y -i "$in" -af "$chain,loudnorm=I=-14:TP=-1.5:LRA=11:measured_I=$(gi input_i):measured_TP=$(gi input_tp):measured_LRA=$(gi input_lra):measured_thresh=$(gi input_thresh):offset=$(gi target_offset):linear=true:print_format=summary,aformat=sample_rates=48000:channel_layouts=stereo" -ar 48000 -ac 2 "$out" 2>"$out.ln.txt"
grep -i "normalization type" "$out.ln.txt" | tr -s ' ' || true
