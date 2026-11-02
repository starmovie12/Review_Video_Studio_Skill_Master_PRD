"""qa_contact_sheet.py — S9-L/S13 contact sheet + programmatic 16-Point QA (File 20, PRD v5.1 App G.5, OSS-SKL-09).
HARD checks block delivery (RVS_ERR_060, exit 60). ADVISORY checks are reported as RVS_WARN_061 + NEEDS-HUMAN visual items.
CLI: python scripts/qa_contact_sheet.py --video out.mp4 --spec spec.json --words words.json --work WORK [--json report.json]
"""
from __future__ import annotations

import argparse
import colorsys
import json
import math
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from PIL import Image, ImageStat  # noqa: E402

from rvs_common import RvsError, log_event, main_wrapper, run_cmd, stage_end, stage_start, warn  # noqa: E402

VALID_RES = {"16:9": {(1920, 1080), (2560, 1440), (3840, 2160), (7680, 4320)},
             "9:16": {(1080, 1920), (1440, 2560), (2160, 3840), (4320, 7680)}}
LOUD_TARGET, LOUD_TOL, TP_CEIL, CHAPTER_SPREAD = -14.0, 1.5, -1.0, 2.0  # §6.4 #6 (PRD target, DEC-09)


def probe(path):
    cp = run_cmd(["ffprobe", "-v", "error", "-show_format", "-show_streams", "-of", "json", path], "QA", 60, "RVS_ERR_051")
    return json.loads(cp.stdout)


def faststart_ok(path) -> bool:
    """moov before mdat (+faststart): scan top-level atoms."""
    with open(path, "rb") as f:
        pos, order = 0, []
        size = os.path.getsize(path)
        while pos < size and len(order) < 12:
            f.seek(pos)
            hdr = f.read(16)
            if len(hdr) < 8:
                break
            n = int.from_bytes(hdr[:4], "big")
            typ = hdr[4:8].decode("latin-1")
            if n == 1:
                n = int.from_bytes(hdr[8:16], "big")
            order.append(typ)
            if n < 8:
                break
            pos += n
    return "moov" in order and "mdat" in order and order.index("moov") < order.index("mdat")


def filter_report(path, vf, dur) -> str:
    cp = run_cmd(["ffmpeg", "-hide_banner", "-nostats", "-i", path, "-vf", vf, "-an", "-f", "null", "-"], "QA", 60 + 4 * dur, "RVS_ERR_051")
    return cp.stderr


def ebur128(path, dur, start=None, length=None) -> dict:
    cmd = ["ffmpeg", "-hide_banner", "-nostats"]
    if start is not None:
        cmd += ["-ss", f"{start:.3f}", "-t", f"{length:.3f}"]
    cmd += ["-i", path, "-vn", "-af", "ebur128=peak=true", "-f", "null", "-"]
    err = run_cmd(cmd, "QA", 60 + 2 * dur, "RVS_ERR_051").stderr
    tail = err[err.rfind("Summary:"):]
    g = lambda p: float(re.search(p, tail).group(1))
    return {"I": g(r"I:\s+(-?[\d.]+) LUFS"), "TP": g(r"Peak:\s+(-?[\d.]+) dBFS")}


def build_contact_sheet_and_qa(video, spec, words, work_dir) -> dict:
    stage_start("S9-L", "16-Point QA")
    meta = spec["meta"]
    aspect = meta["aspect"]
    info = probe(video)
    vs = next((s for s in info["streams"] if s["codec_type"] == "video"), None)
    au = next((s for s in info["streams"] if s["codec_type"] == "audio"), None)
    hard, adv, details = {}, {}, {}
    if vs is None or au is None:
        hard["streams_present"] = False
        return _finish(hard, adv, details, video, work_dir)
    dur = float(info["format"]["duration"])
    W, H = int(vs["width"]), int(vs["height"])
    fps = vs.get("r_frame_rate", "0/1")
    # 1 resolution/SAR/fps/pix_fmt/faststart
    hard["01_resolution_sar_fps_pixfmt_faststart"] = ((W, H) in VALID_RES.get(aspect, set()) and (W, H) == (int(meta["width"]), int(meta["height"]))
                                                      and vs.get("sample_aspect_ratio", "1:1") in ("1:1", "0:1") and fps in ("30/1", "60/1")
                                                      and vs.get("pix_fmt") in ("yuv420p", "yuv420p10le") and faststart_ok(video))
    # 2 audio spec
    br = int(au.get("bit_rate") or 0)
    hard["02_audio_aac_48k_stereo_160k"] = (au.get("codec_name") == "aac" and int(au.get("sample_rate", 0)) == 48000
                                            and int(au.get("channels", 0)) == 2 and (br == 0 or br >= 160000))
    # 3 duration sync + target ±10 %
    vd, ad = float(vs.get("duration", dur)), float(au.get("duration", dur))
    target = float(meta["target_sec"])
    details["durations"] = {"video": vd, "audio": ad, "target": target}
    hard["03_av_sync_0p15s"] = abs(vd - ad) <= 0.15
    (hard if meta.get("format") in ("long_master", "short_derived") else adv)["03b_length_within_10pct"] = abs(dur - target) <= 0.10 * target
    # 4/5 black + freeze
    fd = 2.5 if aspect == "9:16" else 8.5  # DEC-15
    rep = filter_report(video, f"blackdetect=d=0.10:pix_th=0.10,freezedetect=n=-60dB:d={fd}", dur)
    details["black_intervals"] = len(re.findall(r"black_start", rep))
    details["freeze_intervals"] = len(re.findall(r"freeze_start", rep))
    hard["04_no_black_frames"] = details["black_intervals"] == 0
    hard["05_no_frozen_windows"] = details["freeze_intervals"] == 0
    # 6 loudness + chapter spread
    lo = ebur128(video, dur)
    details["loudness"] = lo
    hard["06_loudness_-14_pm1p5_tp_le_-1"] = abs(lo["I"] - LOUD_TARGET) <= LOUD_TOL and lo["TP"] <= TP_CEIL
    by_id = {c["chunk_id"]: c for c in words["chunks"]}
    wins = []  # chapter windows come from the MEASURED words.json timeline (spec ms are plans, not measurements)
    for ch in spec.get("chapters", []):
        cs = [by_id[i] for i in ch["chunk_ids"] if i in by_id]
        if cs:
            s0, e0 = min(c["start_ms"] for c in cs), max(c["end_ms"] + c["pause_after_ms"] for c in cs)
            if e0 - s0 >= 1500:
                wins.append((s0, e0))
    if len(wins) >= 2:
        vals = [ebur128(video, dur, s0 / 1000, (e0 - s0) / 1000)["I"] for s0, e0 in wins]
        vals = [v for v in vals if v > -70]
        details["chapter_lufs"] = vals
        hard["06b_chapter_spread_le_2LU"] = (max(vals) - min(vals)) <= CHAPTER_SPREAD if vals else True
    # 7 contact sheet completeness
    n = max(16, 2 * len(spec.get("chapters", [])))
    cols, rows = 4, math.ceil(n / 4)
    tile = "360:640" if aspect == "9:16" else "640:360"
    sheet = os.path.join(work_dir, "contact_sheet.jpg")
    run_cmd(["ffmpeg", "-v", "error", "-y", "-i", video, "-vf", f"fps={n}/{max(0.5, dur * 0.95):.4f},scale={tile},tile={cols}x{rows}",
             "-frames:v", "1", "-update", "1", sheet], "QA", 60 + 2 * dur, "RVS_ERR_051")
    with Image.open(sheet) as im:
        sw, sh = im.size
        tw, th = sw // cols, sh // rows
        last_idx = n - 1
        lx, ly = (last_idx % cols) * tw, (last_idx // cols) * th
        ext = im.crop((lx, ly, lx + tw, ly + th)).convert("L").getextrema()
        hard["07_contact_sheet_last_tile_populated"] = (ext[1] - ext[0]) > 12
        small = im.resize((64, 64)).convert("RGB")
        sats = [colorsys.rgb_to_hsv(r / 255, g / 255, b / 255)[1] for r, g, b in small.getdata()]
        details["mean_saturation"] = round(sum(sats) / len(sats), 3)
        details["luma_std"] = round(ImageStat.Stat(small.convert("L")).stddev[0], 2)
    # 11 stars present on verdict frame (gold pixels R>200,G>160,B<90) — only if endcard enabled
    ec = spec.get("endcard", {})
    if ec.get("enabled", True) and words["chunks"]:
        last_beat = max(c["beat"] for c in words["chunks"])
        vc = [c for c in words["chunks"] if c["beat"] == last_beat]
        t = (vc[0]["start_ms"] + vc[-1]["end_ms"]) / 2000.0
        fr = os.path.join(work_dir, "qa_verdict_frame.png")
        run_cmd(["ffmpeg", "-v", "error", "-y", "-ss", f"{t:.2f}", "-i", video, "-frames:v", "1", fr], "QA", 60, "RVS_ERR_051")
        with Image.open(fr) as im:
            px = im.convert("RGB").resize((im.width // 4, im.height // 4)).getdata()
            gold = sum(1 for r, g, b in px if r > 200 and g > 160 and b < 90)
        details["gold_star_pixels_quarter_res"] = gold
        hard["11_vector_stars_visible"] = gold >= 20
    # 15 vibrance (advisory, TARGET thresholds)
    adv["15_vibrance_S_ge_0p18_and_lumastd_ge_24"] = details["mean_saturation"] >= 0.18 and details["luma_std"] >= 24.0
    # 16 colour signalling (hard) — matrix conversion is enforced in build_video.final_encode
    hard["16_bt709_tagged"] = (vs.get("color_space") == "bt709" and vs.get("color_primaries") == "bt709" and vs.get("color_transfer") == "bt709")
    # speech presence guard (D-126): voice track must contain speech-level audio in ≥50 % of chunk windows
    if words["chunks"]:
        probes = words["chunks"][:: max(1, len(words["chunks"]) // 8)]
        loud = 0
        for c in probes:
            seg = ebur128(video, dur, c["start_ms"] / 1000, max(0.4, (c["end_ms"] - c["start_ms"]) / 1000))
            loud += seg["I"] > -40
        hard["17_speech_present"] = loud >= max(1, len(probes) // 2)
    # NEEDS-HUMAN visual checks (8 safe-zones, 9 glyphs, 10 face framing, 12 cover, 13/14 host cues & FX) → advisory flags
    for k in ("08_safe_zones", "09_glyph_integrity", "10_face_framing", "12_cover_grid", "13_host_cue_timing", "14_host_fx"):
        adv[k] = None
    return _finish(hard, adv, details, video, work_dir)


def _finish(hard, adv, details, video, work_dir):
    failed = [k for k, v in hard.items() if v is False]
    advisory = [k for k, v in adv.items() if v is False]
    needs_human = [k for k, v in adv.items() if v is None]
    rep = {"video": video, "hard": hard, "advisory": adv, "details": details, "failed_hard": failed,
           "failed_advisory": advisory, "needs_human": needs_human, "all_hard_passed": not failed}
    with open(os.path.join(work_dir, "qa_report.json"), "w", encoding="utf-8") as f:
        json.dump(rep, f, indent=2, ensure_ascii=False)
    if advisory or needs_human:
        warn("RVS_WARN_061", "S9-L", f"advisory={advisory} needs_human={needs_human} — contact_sheet.jpg dekh kar confirm karo")
    stage_end("S9-L", f"hard_failed={failed}")
    if failed:
        raise RvsError("RVS_ERR_060", f"failed: {failed}")
    return rep


def main():
    ap = argparse.ArgumentParser(description="16-point QA")
    for k in ("video", "spec", "words", "work"):
        ap.add_argument(f"--{k}", required=True)
    ap.add_argument("--debug", action="store_true")
    a = ap.parse_args()
    build_contact_sheet_and_qa(a.video, json.load(open(a.spec, encoding="utf-8")), json.load(open(a.words, encoding="utf-8")), a.work)
    log_event("INFO", "S9-L", "qa_done", None, "qa_report.json written")
    return None


if __name__ == "__main__":
    sys.exit(main_wrapper(main, "S9-L"))
