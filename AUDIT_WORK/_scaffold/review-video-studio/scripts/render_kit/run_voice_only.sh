#!/usr/bin/env bash
# RP-2 Hybrid (File 24): phone par sirf voice pack banao → voice_pack.zip (voice_master.wav + words.json) cloud chat mein attach karo.
# Usage: bash scripts/render_kit/run_voice_only.sh spec.json
set -euo pipefail
SPEC="${1:?usage: run_voice_only.sh spec.json}"
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
WORK="${RVS_WORK:-$HOME/rvs_work}"
mkdir -p "$WORK"
if [ -f "$HOME/.rvs_venv/bin/activate" ]; then
  # shellcheck disable=SC1091
  . "$HOME/.rvs_venv/bin/activate"
fi
if command -v termux-wake-lock >/dev/null 2>&1; then termux-wake-lock; fi
python3 "$ROOT/scripts/preflight.py" --spec "$SPEC" --json "$WORK/preflight.json" || [ $? -eq 10 ]
python3 "$ROOT/scripts/voice_pack.py" --spec "$SPEC" --work "$WORK" || [ $? -eq 10 ]
( cd "$WORK" && python3 -c "import zipfile; z=zipfile.ZipFile('voice_pack.zip','w',zipfile.ZIP_DEFLATED); [z.write(f) for f in ('voice_master.wav','words.json')]; z.close()" )
DEST="/sdcard/Download"; [ -d "$DEST" ] || DEST="$WORK"
cp "$WORK/voice_pack.zip" "$DEST/" && echo "✅ voice_pack.zip → $DEST (chat mein attach karo)"
if command -v termux-wake-unlock >/dev/null 2>&1; then termux-wake-unlock; fi
