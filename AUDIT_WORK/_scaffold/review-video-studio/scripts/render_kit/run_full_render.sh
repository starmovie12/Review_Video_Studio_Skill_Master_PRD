#!/usr/bin/env bash
# RP-3 (File 25): phone par poora render (1080p_fhd only on Termux — tier gate DEC-12). Output → /sdcard/Download/
# Usage: bash scripts/render_kit/run_full_render.sh spec.json
set -euo pipefail
SPEC="${1:?usage: run_full_render.sh spec.json}"
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
WORK="${RVS_WORK:-$HOME/rvs_work}"
OUT="${RVS_OUT:-/sdcard/Download}"; [ -d "$OUT" ] || OUT="$WORK"
mkdir -p "$WORK"
if [ -f "$HOME/.rvs_venv/bin/activate" ]; then
  # shellcheck disable=SC1091
  . "$HOME/.rvs_venv/bin/activate"
fi
export RVS_TIMEOUT_SCALE="${RVS_TIMEOUT_SCALE:-3}"
if command -v termux-wake-lock >/dev/null 2>&1; then termux-wake-lock; fi
ok() { local rc=$?; [ $rc -eq 0 ] || [ $rc -eq 10 ]; }
python3 "$ROOT/scripts/preflight.py" --spec "$SPEC" --json "$WORK/preflight.json" || ok
python3 "$ROOT/scripts/voice_pack.py" --spec "$SPEC" --work "$WORK" || ok
python3 "$ROOT/scripts/character_overlay.py" --spec "$SPEC" --words "$WORK/words.json" --voice "$WORK/voice_master.wav" --work "$WORK" || ok
python3 "$ROOT/scripts/build_video.py" --spec "$SPEC" --words "$WORK/words.json" --voice "$WORK/voice_master.wav" --work "$WORK" \
  --out "$WORK/final_master_16x9.mp4" --char-timeline "$WORK/char_timeline.txt" || ok
python3 "$ROOT/scripts/qa_contact_sheet.py" --video "$WORK/final_master_16x9.mp4" --spec "$SPEC" --words "$WORK/words.json" --work "$WORK" || ok
cp "$WORK/final_master_16x9.mp4" "$WORK/contact_sheet.jpg" "$OUT/" && echo "✅ final_master_16x9.mp4 + contact_sheet.jpg → $OUT"
if command -v termux-wake-unlock >/dev/null 2>&1; then termux-wake-unlock; fi
