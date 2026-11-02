"""repurpose_shorts.py — S11 Moment Miner, S12 derived spec + derived audio (Master body slices + fresh hook/CTA TTS),
S13 hand-off (File 23, PRD v5.1 App G.8, OSS-SKL-07). Own design; pattern studied: Anil-matcha/AI-Youtube-Shorts-Generator
(virality scoring + >50 % overlap dedupe). Score is a deterministic PROXY (TARGET heuristic), rescaled to 0–100.
CLI: python scripts/repurpose_shorts.py --spec spec.json --words words.json --voice voice_master.wav --work WORK [--max 5]
"""
import argparse
import asyncio
import copy
import json
import math
import os
import struct
import sys
import wave

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from rvs_common import RvsError, SKILL_ROOT, log_event, main_wrapper, stage_end, stage_start, warn  # noqa: E402

def score_candidate_moment(chunks: list[dict], scenes: list[dict]) -> int:
    """Scores a candidate segment out of 100 on Hook Strength, Self-Contained Clarity, Payoff, Visual Fit, and Gap Bonus."""
    if not chunks:
        return 0
    has_question_or_stat = any("?" in c["show"] or any(ch.isdigit() for ch in c["show"]) for c in chunks[:2])
    hook_pts = 24 if has_question_or_stat else 18
    self_contained_pts = 23 if len(chunks) >= 3 else 15
    payoff_pts = 19 if any(c.get("expression") in ("shocked", "verdict_salute", "hyped") for c in chunks) else 14
    visual_pts = 14 if len(scenes) >= 2 else 10
    gap_pts = 14 if any(c.get("fact_ref", "NONE") != "NONE" for c in chunks) else 8
    raw = hook_pts + self_contained_pts + payoff_pts + visual_pts + gap_pts  # proxy range 65..94
    return max(0, min(100, round((raw - 65) * 100 / 29)))  # rescaled to 0..100 (D-150); threshold 75 ≈ raw 87

def slice_wav_with_cosine_fade(
    master_wav_path: str, start_ms: int, end_ms: int, out_wav_path: str, fade_ms: int = 15
) -> int:
    """Slices voice_master.wav between [start_ms, end_ms] with 15ms cosine fade-in/out so cut points never click/pop."""
    with wave.open(master_wav_path, "rb") as wf:
        sr = wf.getframerate()
        n_ch = wf.getnchannels()
        total_frames = wf.getnframes()
        start_f = max(0, min(total_frames, int((start_ms / 1000.0) * sr)))
        end_f = max(start_f + 1, min(total_frames, int((end_ms / 1000.0) * sr)))
        wf.setpos(start_f)
        raw = bytearray(wf.readframes(end_f - start_f))

    n_slice_frames = len(raw) // (2 * n_ch)
    fade_frames = min(n_slice_frames // 4, int((fade_ms / 1000.0) * sr))
    for i in range(fade_frames):
        gain = 0.5 * (1.0 - math.cos(math.pi * (i / float(max(1, fade_frames)))))
        # Fade-in at start
        for ch in range(n_ch):
            pos = (i * n_ch + ch) * 2
            sample = struct.unpack_from("<h", raw, pos)[0]
            struct.pack_into("<h", raw, pos, int(sample * gain))
        # Fade-out at end
        rev_i = n_slice_frames - 1 - i
        for ch in range(n_ch):
            pos = (rev_i * n_ch + ch) * 2
            sample = struct.unpack_from("<h", raw, pos)[0]
            struct.pack_into("<h", raw, pos, int(sample * gain))

    with wave.open(out_wav_path, "wb") as out_wf:
        out_wf.setnchannels(n_ch)
        out_wf.setsampwidth(2)
        out_wf.setframerate(sr)
        out_wf.writeframes(bytes(raw))
    return int(round((n_slice_frames / float(sr)) * 1000))

def build_derived_short_spec(master_spec: dict, master_words: dict, moment: dict) -> dict:
    """Transforms a 16:9 Long Master spec + moment definition into a validated 9:16 short_derived spec."""
    derived = copy.deepcopy(master_spec)
    m_id = moment["id"].lower().replace("-", "_")
    target = moment["target"]
    derived["meta"]["project_slug"] = f"{master_spec['meta']['project_slug']}_{target}_{m_id}"
    derived["meta"]["format"] = "short_derived"
    derived["meta"]["parent_id"] = master_spec["meta"]["project_slug"]
    derived["meta"]["aspect"] = "9:16"
    derived["meta"]["width"] = 1080
    derived["meta"]["height"] = 1920

    selected_ids = set(moment["chunk_ids"])
    body_chunks = [copy.deepcopy(c) for c in master_spec["chunks"] if c["chunk_id"] in selected_ids]

    derived["meta"]["resolution_tier"] = "1080p_fhd"
    hook_chunk = {
        "chunk_id": "CHK-01",
        "beat": 1,
        "say": moment["new_hook_say"],
        "show": moment["new_hook_show"],
        "highlight_word": moment["new_hook_show"].split()[0] if moment["new_hook_show"] else "",
        "pause_after_ms": 180,
        "sub_cut": "punch_in",
        "expression": "surprise_shock" if target == "reel" else "confident_smirk",
        "gojo_cue": "hook_entry",
        "gojo_power": "blue",
        "fact_ref": "NONE",
    }
    reindexed_chunks = [hook_chunk]
    beat_map = {b: i + 2 for i, b in enumerate(sorted({c["beat"] for c in body_chunks}))}  # hook=1, body=2.., CTA=last+1
    for idx, bc in enumerate(body_chunks, start=2):
        bc["chunk_id"] = f"CHK-{idx:02d}"
        bc["beat"] = beat_map[bc["beat"]]
        reindexed_chunks.append(bc)

    cta_chunk = {
        "chunk_id": f"CHK-{len(reindexed_chunks) + 1:02d}",
        "beat": max(c["beat"] for c in reindexed_chunks) + 1,
        "say": moment["new_cta_say"],
        "show": moment["new_cta_show"],
        "highlight_word": "BIO" if target == "reel" else "VIDEO",
        "pause_after_ms": 0,
        "sub_cut": "none",
        "expression": "outro_salute",
        "gojo_cue": "outro_signature",
        "gojo_power": "infinity",
        "fact_ref": "NONE",
    }
    reindexed_chunks.append(cta_chunk)
    derived["chunks"] = reindexed_chunks
    derived["meta"]["target_sec"] = max(15, min(180, len(reindexed_chunks) * 3))
    derived.pop("repurpose", None)
    derived.pop("chapters", None)
    # scenes: remap master beats → derived beats; hook (beat 1) and CTA (last beat) reuse the first/last selected visual
    scenes = []
    for s in master_spec["scenes"]:
        if s["beat"] in beat_map:
            c = copy.deepcopy(s)
            c["beat"] = beat_map[s["beat"]]
            scenes.append(c)
    if scenes:
        hook_sc = copy.deepcopy(scenes[0]); hook_sc.update(beat=1, sfx="whoosh")
        cta_sc = copy.deepcopy(scenes[-1]); cta_sc.update(beat=cta_chunk["beat"], sfx="pop")
        scenes = [hook_sc] + scenes + [cta_sc]
    derived["scenes"] = scenes or [copy.deepcopy(master_spec["scenes"][0])]
    validate_spec(derived)
    return derived


def validate_spec(spec: dict) -> None:
    try:
        import jsonschema
        schema = json.loads((SKILL_ROOT / "schemas" / "spec.schema.json").read_text(encoding="utf-8"))
        errs = list(jsonschema.Draft202012Validator(schema).iter_errors(spec))
        if errs:
            raise RvsError("RVS_ERR_001", "derived spec: " + "; ".join(e.message for e in errs[:3]))
    except ImportError:
        warn("RVS_WARN_035", "S12", "jsonschema missing — derived spec not schema-validated")


def mine_moments(spec: dict, words: dict, max_clips: int = 5, win_s=(30, 60), threshold: int = 75) -> list[dict]:
    """S11: slide beat-aligned windows (30–60 s), score, drop windows overlapping a better one by >50 %, keep the best
    reel + short (+ up to max_clips). If <2 reach the threshold, accept ≥60 with a context patch (RVS_WARN_118/119)."""
    chunks = words["chunks"]
    beats = sorted({c["beat"] for c in chunks})
    cands = []
    for i, b0 in enumerate(beats):
        sel = []
        for b in beats[i:]:
            sel += [c for c in chunks if c["beat"] == b]
            span = (sel[-1]["end_ms"] - sel[0]["start_ms"]) / 1000
            if span > win_s[1]:
                break
            if span >= win_s[0] or (b == beats[-1] and span >= 15):
                spec_chunks = [sc for sc in spec["chunks"] if sc["chunk_id"] in {c["chunk_id"] for c in sel}]
                scn = [s for s in spec["scenes"] if s["beat"] in {c["beat"] for c in sel}]
                cands.append({"chunk_ids": [c["chunk_id"] for c in sel], "src_start_ms": sel[0]["start_ms"],
                              "src_end_ms": sel[-1]["end_ms"], "score": score_candidate_moment(spec_chunks, scn),
                              "clarity_ok": len(sel) >= 3})
    cands.sort(key=lambda c: -c["score"])
    picked = []
    for c in cands:
        ov = any(min(c["src_end_ms"], p["src_end_ms"]) - max(c["src_start_ms"], p["src_start_ms"]) >
                 0.5 * (c["src_end_ms"] - c["src_start_ms"]) for p in picked)
        if not ov:
            picked.append(c)
    strong = [c for c in picked if c["score"] >= threshold]
    if len(strong) < 2:
        warn("RVS_WARN_118", "S11", f"only {len(strong)} moments ≥{threshold}; using ≥60 with context patch")
        strong = [c for c in picked if c["score"] >= 60][:max(2, len(strong))]
    for c in strong:
        if not c["clarity_ok"]:
            warn("RVS_WARN_119", "S11", f"moment {c['src_start_ms']}–{c['src_end_ms']} needs context patch")
    return strong[:max_clips]


def assemble_derived_audio(master_wav: str, master_words: dict, derived: dict, moment: dict, work_dir: str) -> tuple[str, dict]:
    """S12: hook TTS + master body slice (15 ms cosine fades, NO re-TTS) + CTA TTS → derived voice + words.json (timeline shifted)."""
    from voice_pack import build_voice_pack  # reuse engine chain + cache for the 2 fresh chunks only
    os.makedirs(work_dir, exist_ok=True)
    fresh = copy.deepcopy(derived)
    fresh["chunks"] = [derived["chunks"][0], derived["chunks"][-1]]
    fresh_words = build_voice_pack(fresh, os.path.join(work_dir, "fresh_tts"))
    by_id = {c["chunk_id"]: c for c in master_words["chunks"]}
    sel = [by_id[i] for i in moment["chunk_ids"] if i in by_id]
    if not sel:
        raise RvsError("RVS_ERR_002", f"{moment['id']}: chunk_ids not in words.json")
    # slice at MEASURED chunk boundaries from words.json (spec src_*_ms are planning values only)
    src_start, src_end = sel[0]["start_ms"], sel[-1]["end_ms"] + sel[-1]["pause_after_ms"]
    moment = dict(moment, src_start_ms=src_start, src_end_ms=src_end)
    body = os.path.join(work_dir, "body_slice.wav")
    slice_wav_with_cosine_fade(master_wav, src_start, src_end, body)
    fresh_wav = os.path.join(work_dir, "fresh_tts", "voice_master.wav")
    hook_end = fresh_words["chunks"][0]["end_ms"] + fresh_words["chunks"][0]["pause_after_ms"]
    out = os.path.join(work_dir, "voice_master.wav")
    with wave.open(fresh_wav, "rb") as fw, wave.open(body, "rb") as bw, wave.open(out, "wb") as ow:
        ow.setnchannels(2)
        ow.setsampwidth(2)
        ow.setframerate(48000)
        hook_frames = hook_end * 48
        ow.writeframes(fw.readframes(hook_frames))
        ow.writeframes(bw.readframes(bw.getnframes()))
        body_ms = round(bw.getnframes() / 48)
        ow.writeframes(fw.readframes(fw.getnframes()))
    items, shift = [dict(fresh_words["chunks"][0], chunk_id="CHK-01")], hook_end - moment["src_start_ms"]
    for dc, src_id in zip(derived["chunks"][1:-1], moment["chunk_ids"]):
        mc = dict(by_id[src_id])
        mc.update(chunk_id=dc["chunk_id"], beat=dc["beat"], start_ms=mc["start_ms"] + shift, end_ms=mc["end_ms"] + shift)
        items.append(mc)
    cta = dict(fresh_words["chunks"][1])
    cta_off = hook_end + body_ms - fresh_words["chunks"][1]["start_ms"]
    cta.update(chunk_id=derived["chunks"][-1]["chunk_id"], beat=derived["chunks"][-1]["beat"],
               start_ms=cta["start_ms"] + cta_off, end_ms=cta["end_ms"] + cta_off)
    items.append(cta)
    w = {"voice_id": master_words["voice_id"], "engine": master_words.get("engine", "edge-tts"),
         "engine_version": master_words.get("engine_version", "unknown"), "sample_rate_hz": 48000, "channels": 2,
         "total_duration_ms": items[-1]["end_ms"] + items[-1]["pause_after_ms"], "chunks": items}
    json.dump(w, open(os.path.join(work_dir, "words.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    return out, w


def main():
    ap = argparse.ArgumentParser(description="S11–S13 repurpose engine")
    for k in ("spec", "words", "voice", "work"):
        ap.add_argument(f"--{k}", required=True)
    ap.add_argument("--max", type=int, default=5)
    ap.add_argument("--debug", action="store_true")
    a = ap.parse_args()
    spec, words = json.load(open(a.spec, encoding="utf-8")), json.load(open(a.words, encoding="utf-8"))
    stage_start("S11", "moment mining")
    moments = spec.get("repurpose", {}).get("moments") or []
    if not moments:
        raise RvsError("RVS_ERR_001", "spec.repurpose.moments empty — run mine_moments() in S11 and let the Skill write hooks/CTAs")
    hooks = {(m["target"], m.get("hook_archetype")) for m in moments}
    if len({m.get("hook_archetype") for m in moments if m["target"] == "reel"} & {m.get("hook_archetype") for m in moments if m["target"] == "short"}):
        warn("RVS_WARN_118", "S11", "Reel and Short share a hook archetype — platform-distinct rule (§5.4) violated; rewrite hook")
    for m in moments[: a.max]:
        d = build_derived_short_spec(spec, words, m)
        wd = os.path.join(a.work, d["meta"]["project_slug"])
        os.makedirs(wd, exist_ok=True)
        json.dump(d, open(os.path.join(wd, "spec.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=2)
        assemble_derived_audio(a.voice, words, d, m, wd)
        log_event("INFO", "S12", "derived_ready", None, f"{m['id']} → {wd} (render with build_video.py)")
    stage_end("S11", f"{len(moments[: a.max])} derived specs; hooks={sorted(map(str, hooks))}")
    return None


if __name__ == "__main__":
    sys.exit(main_wrapper(main, "S11"))
