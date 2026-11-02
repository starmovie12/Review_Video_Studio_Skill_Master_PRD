"""preflight.py — S7-L environment probe, spec validation, tier/render-path gate, secrets presence (File 16, PRD v5.1 App G.1, OSS-SKL-09).
Never crashes on a missing tool: every probe is recorded and mapped to a render path (RP-1..RP-4) or an error code.
CLI: python scripts/preflight.py [--spec spec.json] [--json preflight.json] [--strict]   (exit 0/10/20/30)
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import socket
import subprocess
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from rvs_common import (EXIT, RvsError, SKILL_ROOT, log_event, main_wrapper, secret_status, stage_end,  # noqa: E402
                        stage_start, warn)

TERMUX_PREFIX = os.environ.get("PREFIX", "/data/data/com.termux/files/usr")
LATIN_FONT_CANDIDATES = [str(SKILL_ROOT / "assets/fonts/Poppins-Bold.ttf"), "/usr/share/fonts/truetype/noto/NotoSans-Bold.ttf",
                         "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", "/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf",
                         "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf", f"{TERMUX_PREFIX}/share/fonts/TTF/DejaVuSans-Bold.ttf",
                         "/system/fonts/Roboto-Bold.ttf"]
DEVA_FONT_CANDIDATES = [str(SKILL_ROOT / "assets/fonts/NotoSansDevanagari-Bold.ttf"), "/usr/share/fonts/truetype/noto/NotoSansDevanagari-Bold.ttf",
                        f"{TERMUX_PREFIX}/share/fonts/TTF/NotoSansDevanagari-Bold.ttf", "/system/fonts/NotoSansDevanagari-Bold.ttf"]
# Tier gate (DEC-12, App K): minimum RAM (GiB, TARGET) and allowed render paths
TIER_GATE = {"1080p_fhd": (2, {"RP-1", "RP-2", "RP-3"}), "1440p_qhd": (4, {"RP-1", "RP-2"}),
             "4k_uhd": (8, {"RP-1", "RP-2"}), "8k_uhd": (16, {"RP-1"})}


def resolve_font(cands: list[str]) -> str | None:
    return next((os.path.abspath(p) for p in cands if os.path.exists(p)), None)


def get_project_temp_dir(slug: str = "rvs_project") -> str:
    base = os.path.join(tempfile.gettempdir(), slug)  # Linux /tmp, Termux $TMPDIR
    for sub in ("transcripts", "chunk_cache"):
        os.makedirs(os.path.join(base, sub), exist_ok=True)
    return base


def ram_gib() -> float:
    try:
        with open("/proc/meminfo") as f:
            kv = {l.split(":")[0]: int(l.split()[1]) for l in f if ":" in l}
        return round(kv.get("MemAvailable", kv.get("MemTotal", 0)) / 1048576, 1)
    except (OSError, ValueError):
        return 0.0


def ffmpeg_filters(ffmpeg: str) -> set[str]:
    out = subprocess.run([ffmpeg, "-hide_banner", "-filters"], capture_output=True, text=True, timeout=20).stdout
    import re
    return {m.group(2) for m in (re.match(r"^\s([.A-Z|]{2,3})\s+(\S+)\s+\S+->\S+", ln) for ln in out.splitlines()) if m}


def probe_environment() -> dict:
    from build_video import REQUIRED_FILTERS
    r = {"ffmpeg": shutil.which("ffmpeg"), "ffprobe": shutil.which("ffprobe"), "espeak_ng": shutil.which("espeak-ng") or shutil.which("espeak"),
         "is_termux": os.path.exists("/data/data/com.termux"), "ram_gib": ram_gib(), "disk_free_mb": shutil.disk_usage(".").free // 1048576}
    try:
        from PIL import features
        r["raqm_ok"] = bool(features.check("raqm")) and bool(features.check("freetype2"))
    except ImportError:
        r["raqm_ok"] = False
    r["latin_font"], r["deva_font"] = resolve_font(LATIN_FONT_CANDIDATES), resolve_font(DEVA_FONT_CANDIDATES)
    r["missing_filters"] = []
    if r["ffmpeg"]:
        have = ffmpeg_filters(r["ffmpeg"])
        r["missing_filters"] = [f for f in REQUIRED_FILTERS if f not in have]
        enc = subprocess.run([r["ffmpeg"], "-hide_banner", "-encoders"], capture_output=True, text=True, timeout=20).stdout
        r["hw_h264_mediacodec"] = "h264_mediacodec" in enc
        r["libx265"] = "libx265" in enc
    for mod in ("jsonschema", "rapidfuzz", "edge_tts", "kokoro_onnx", "dotenv"):
        try:
            __import__(mod)
            r[f"py_{mod}"] = True
        except ImportError:
            r[f"py_{mod}"] = False
    try:  # TCP reachability only (proxies may still allow/deny WSS) — 2 s
        with socket.create_connection(("speech.platform.bing.com", 443), timeout=2.0):
            r["edge_tts_reachable"] = True
    except OSError:
        r["edge_tts_reachable"] = False
    from voice_engines import KokoroONNX
    r["kokoro_ready"] = KokoroONNX().available()
    r["premium_toggle"] = os.environ.get("RVS_PREMIUM_TTS", "off").lower()
    r["secrets"] = {"ELEVENLABS_API_KEY": secret_status("ELEVENLABS_API_KEY")}
    tts_ok = (r["edge_tts_reachable"] and r["py_edge_tts"]) or r["kokoro_ready"] or bool(r["espeak_ng"])
    render_ok = bool(r["ffmpeg"] and r["ffprobe"] and not r["missing_filters"] and r["latin_font"])
    r["selected_render_path"] = ("RP-3" if r["is_termux"] and render_ok else "RP-1" if render_ok and tts_ok
                                 else "RP-2" if render_ok else "RP-4")
    return r


def check_secrets(r: dict) -> None:
    st = r["secrets"]["ELEVENLABS_API_KEY"]
    if st == "present" and r["premium_toggle"] != "on":
        warn("RVS_WARN_046", "S7-L", "ELEVENLABS_API_KEY present, RVS_PREMIUM_TTS off → premium NOT used")
    if r["premium_toggle"] == "on" and st == "missing":
        warn("RVS_WARN_047", "S7-L", "RVS_PREMIUM_TTS=on but key missing")
    if st == "malformed":
        warn("RVS_WARN_048", "S7-L", "ELEVENLABS_API_KEY format looks wrong")


def validate_spec(spec: dict, r: dict) -> dict:
    """Schema + semantic checks + tier gate + long-render guard. Returns possibly downgraded meta (never edits the file)."""
    try:
        import jsonschema
        schema = json.loads((SKILL_ROOT / "schemas/spec.schema.json").read_text(encoding="utf-8"))
        errs = list(jsonschema.Draft202012Validator(schema).iter_errors(spec))
        if errs:
            raise RvsError("RVS_ERR_001", "; ".join(f"{list(e.path)}: {e.message}" for e in errs[:6]))
    except ImportError:
        warn("RVS_WARN_035", "S7-L", "jsonschema missing — minimal built-in checks only")
        for k in ("meta", "voice", "chunks", "scenes", "endcard"):
            if k not in spec:
                raise RvsError("RVS_ERR_001", f"missing '{k}'")
    chs = spec.get("chapters", [])
    for a, b in zip(chs, chs[1:]):
        if b["start_ms"] < a["end_ms"] or (a["end_ms"] - a["start_ms"]) < 10000:
            raise RvsError("RVS_ERR_001", f"{a['id']}: chapters must be ascending and ≥10 s (YouTube rule)")
    meta = dict(spec["meta"])
    tier = meta.get("resolution_tier", "1080p_fhd")
    need, paths = TIER_GATE[tier]
    if tier != "1080p_fhd" and (r["selected_render_path"] not in paths or (r["ram_gib"] and r["ram_gib"] < need)):
        warn("RVS_WARN_073", "S7-L", f"{tier} not allowed on {r['selected_render_path']} / {r['ram_gib']} GiB → 1080p_fhd")
        meta["resolution_tier"] = "1080p_fhd"
        meta["width"], meta["height"] = (1920, 1080) if meta["aspect"] == "16:9" else (1080, 1920)
    if r["is_termux"] and int(meta["target_sec"]) > 300:
        warn("RVS_WARN_072", "S7-L", f"Termux + {meta['target_sec']} s → RP-2 recommended (thermal/RAM)")
    ch = spec.get("character", {})
    if ch.get("enabled") and ch.get("preset_id") in {"CHAR-GOJO-HOST", "CHAR-L-DETECTIVE", "CHAR-CONAN-SLEUTH"} \
            and ch.get("asset_rights", "undeclared") not in {"licensed", "original_owned", "permission_granted"}:
        warn("RVS_WARN_083", "S7-L", "character rights undeclared → original host will render")
    return meta


def main():
    ap = argparse.ArgumentParser(description="S7-L preflight")
    ap.add_argument("--spec", default=None)
    ap.add_argument("--json", default=None)
    ap.add_argument("--strict", action="store_true", help="treat RP-4 as error")
    ap.add_argument("--debug", action="store_true")
    a = ap.parse_args()
    stage_start("S7-L-PRE", "preflight")
    r = probe_environment()
    if not r["ffmpeg"] or not r["ffprobe"]:
        log_event("ERROR", "S7-L-PRE", "missing_binary", "RVS_ERR_030", "ffmpeg/ffprobe not found → RP-4 manual path")
    if r["missing_filters"]:
        log_event("ERROR", "S7-L-PRE", "missing_filters", "RVS_ERR_031", ",".join(r["missing_filters"]))
    if not r["latin_font"] or not r["deva_font"]:
        log_event("ERROR", "S7-L-PRE", "missing_font", "RVS_ERR_033", f"latin={r['latin_font']} deva={r['deva_font']}")
    if not r["raqm_ok"]:
        warn("RVS_WARN_034", "S7-L-PRE", "raqm missing → caption_script=roman_hinglish")
    for mod in ("jsonschema", "rapidfuzz"):
        if not r[f"py_{mod}"]:
            warn("RVS_WARN_035", "S7-L-PRE", f"{mod} missing → built-in fallback")
    check_secrets(r)
    if a.spec:
        r["effective_meta"] = validate_spec(json.load(open(a.spec, encoding="utf-8")), r)
    if a.json:
        json.dump(r, open(a.json, "w", encoding="utf-8"), indent=2, default=str)
    stage_end("S7-L-PRE", f"render_path={r['selected_render_path']}")
    if r["selected_render_path"] == "RP-4" and a.strict:
        return EXIT["ENV"]
    return None


if __name__ == "__main__":
    sys.exit(main_wrapper(main, "S7-L-PRE"))
