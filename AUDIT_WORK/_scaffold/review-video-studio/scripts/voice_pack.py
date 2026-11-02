"""voice_pack.py — S7-L Master Voice: phonetic normalizer, engine adapter (per-run switch), engine-keyed SHA-256 cache,
double-reverse silence trim, frame-accurate words.json (File 17, PRD v5.1 App G.2, OSS-SKL-01).
CLI: python scripts/voice_pack.py --spec spec.json --work WORK_DIR [--debug]
"""
from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import os
import re
import sys
import wave

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from rvs_common import (EXIT, RvsError, SKILL_ROOT, log_event, main_wrapper, run_cmd, stage_end, stage_start,  # noqa: E402
                        warn)
from voice_engines import EngineFailed, engine_chain, report_engine_switch  # noqa: E402

SR = 48000
BYTES_PER_FRAME = 4  # 16-bit stereo
HALF_NUM_MAP = {"1.5": "डेढ़", "2.5": "ढाई", "3.5": "साढ़े तीन", "4.5": "साढ़े चार"}
INT_NUM_MAP = {"0": "शून्य", "1": "एक", "2": "दो", "3": "तीन", "4": "चार", "5": "पांच",
               "6": "छह", "7": "सात", "8": "आठ", "9": "नौ", "10": "दस"}
ACRONYM_MAP = {r"\bOTT\b": "ओटीटी", r"\bBGM\b": "बीजीएम", r"\bVFX\b": "वीएफएक्स", r"\bCGI\b": "सीजीआई",
               r"\bIMDb\b": "आईएमडीबी", r"\bUI/UX\b": "यूआई यूएक्स", r"\bFPS\b": "एफपीएस"}
LEFTOVER_RATING_RE = re.compile(r"\d+(?:\.\d+)?\s*/\s*(?:5|10)\b")


def normalize_tts_say(text: str) -> str:
    """Ratings, multipliers, currency and acronyms → spoken Devanagari Hinglish (deterministic, stdlib only)."""
    out = text
    out = re.sub(r"(?<![0-9.])0\.5\s*/\s*5\b", "पांच में से आधा स्टार", out)
    for k, v in HALF_NUM_MAP.items():
        out = re.sub(rf"(?<![0-9.]){re.escape(k)}\s*/\s*5\b", f"पांच में से {v} स्टार", out)

    def _rep_dec(m: re.Match, denom_word: str, suffix: str = "") -> str:
        a, b = m.group(1), m.group(2)
        return f"{denom_word} में से {INT_NUM_MAP.get(a, a)} पॉइंट {INT_NUM_MAP.get(b, b)}{suffix}"

    out = re.sub(r"(?<![0-9.])([0-9])\.([0-9])\s*/\s*5\b", lambda m: _rep_dec(m, "पांच", " स्टार"), out)
    for k, v in INT_NUM_MAP.items():
        out = re.sub(rf"(?<![0-9.]){k}\s*/\s*5\b", f"पांच में से {v} स्टार", out)
    out = re.sub(r"(?<![0-9.])10\.0\s*/\s*10\b", "दस में से दस", out)
    out = re.sub(r"(?<![0-9.])([0-9])\.([0-9])\s*/\s*10\b", lambda m: _rep_dec(m, "दस"), out)
    for k, v in sorted(INT_NUM_MAP.items(), key=lambda x: -len(x[0])):
        out = re.sub(rf"(?<![0-9.]){k}\s*/\s*10\b", f"दस में से {v}", out)
    out = re.sub(r"(?<![0-9.])1\.5x\b", "डेढ़ गुना", out, flags=re.IGNORECASE)
    out = re.sub(r"(?<![0-9.])2x\b", "दोगुना", out, flags=re.IGNORECASE)
    out = re.sub(r"₹\s*([0-9][0-9,]*(?:\.[0-9]+)?)\s*(?:Cr|Crore)\b", r"\1 करोड़ रुपये", out, flags=re.IGNORECASE)
    out = re.sub(r"₹\s*([0-9][0-9,]*)\b", r"\1 रुपये", out)
    for pat, rep in ACRONYM_MAP.items():
        out = re.sub(pat, rep, out)
    return out


def trim_chunk_silence_48k_stereo(raw_audio_path: str, trimmed_wav_path: str) -> int:
    """Double-reverse silenceremove (-45 dB) + 48 kHz stereo lock. MEASURED (FFmpeg 6.1.1, App O.2): voiced span kept ±10 ms."""
    af = ("silenceremove=start_periods=1:start_threshold=-45dB,areverse,"
          "silenceremove=start_periods=1:start_threshold=-45dB,areverse,aformat=sample_rates=48000:channel_layouts=stereo")
    tmp = trimmed_wav_path + ".part.wav"
    run_cmd(["ffmpeg", "-v", "error", "-y", "-i", raw_audio_path, "-af", af, "-ar", str(SR), "-ac", "2", "-c:a", "pcm_s16le", tmp],
            "S7-L", 60, "RVS_ERR_050")
    os.replace(tmp, trimmed_wav_path)
    with wave.open(trimmed_wav_path, "rb") as wf:
        return wf.getnframes()


def cache_key(engine: str, engine_ver: str, voice_id: str, rate: str, pitch: str, say_norm: str) -> str:
    return hashlib.sha256(json.dumps([engine, engine_ver, voice_id, rate, pitch, say_norm], ensure_ascii=False).encode()).hexdigest()[:20]


async def _synth_all(chunks: list[dict], voice_cfg: dict, cache_dir: str, engines: list) -> tuple[list[str], dict]:
    """Synthesises every chunk with ONE engine; if it fails, the whole run restarts on the next engine (DEC-03)."""
    sem = asyncio.Semaphore(int(os.environ.get("RVS_TTS_CONCURRENCY", "2")))
    for idx, eng in enumerate(engines):
        reused = 0

        async def one(chk):
            nonlocal reused
            key = cache_key(eng.name, eng.version(), voice_cfg["voice_id"], voice_cfg["rate"], voice_cfg["pitch"], chk["_say_norm"])
            final = os.path.join(cache_dir, f"chk_{key}.wav")
            if os.path.exists(final) and os.path.getsize(final) > 1024:
                reused += 1
                return final
            for attempt in range(2):  # empty-audio guard (RVS_WARN_126)
                res = await eng.synth(chk["_say_norm"], "hi", voice_cfg["voice_id"], voice_cfg["rate"], voice_cfg["pitch"],
                                      os.path.join(cache_dir, f"raw_{key}"), sem)
                frames = await asyncio.to_thread(trim_chunk_silence_48k_stereo, res["wav"], final)
                if frames >= int(0.1 * SR):
                    return final
                warn("RVS_WARN_126", "S7-L", f"{chk['chunk_id']} audio <100 ms (attempt {attempt + 1})")
            raise EngineFailed("RVS_ERR_040", f"{chk['chunk_id']} empty audio twice")

        try:
            paths = await asyncio.gather(*(one(c) for c in chunks))
            if reused:
                warn("RVS_WARN_124", "S7-L", f"{reused} chunks cache se reuse hue")
            return list(paths), {"engine": eng.name, "engine_version": eng.version()}
        except EngineFailed as e:
            nxt = engines[idx + 1].name if idx + 1 < len(engines) else None
            if not nxt:
                raise RvsError("RVS_ERR_040", f"{eng.name}: {e.detail}") from e
            report_engine_switch(eng.name, e.code if e.code.startswith("RVS_WARN") else "RVS_WARN_041", e.detail, nxt)
    raise RvsError("RVS_ERR_040", "engine chain exhausted")


def build_voice_pack(spec: dict, work_dir: str) -> dict:
    """spec.json → voice_master.wav (48 kHz s16 stereo, unmastered stem) + words.json (frame-accurate timeline)."""
    stage_start("S7-L", "Master voice synthesis")
    cache_dir = os.path.join(work_dir, "chunk_cache")
    os.makedirs(cache_dir, exist_ok=True)
    voice_cfg = spec["voice"]
    for chk in spec["chunks"]:
        say = chk["say"]
        chk["_say_norm"] = normalize_tts_say(say) if voice_cfg.get("phonetic_normalize", True) else say
        if LEFTOVER_RATING_RE.search(chk["_say_norm"]):
            warn("RVS_WARN_125", "S7-L", f"{chk['chunk_id']}: unnormalised number left: {LEFTOVER_RATING_RE.search(chk['_say_norm']).group(0)}")
    engines = engine_chain(voice_cfg.get("engine", "edge-tts"))
    paths, prov = asyncio.run(_synth_all(spec["chunks"], voice_cfg, cache_dir, engines))

    master = os.path.join(work_dir, "voice_master.wav")
    tmp = master + ".part"
    cursor_frames = 0
    words = []
    with wave.open(tmp, "wb") as out:
        out.setnchannels(2)
        out.setsampwidth(2)
        out.setframerate(SR)
        for chk, p in zip(spec["chunks"], paths):
            with wave.open(p, "rb") as wf:
                n = wf.getnframes()
                out.writeframes(wf.readframes(n))
            pause_ms = int(chk.get("pause_after_ms", 55))
            pause_frames = pause_ms * SR // 1000
            if pause_frames:
                out.writeframes(b"\x00" * pause_frames * BYTES_PER_FRAME)
            start_ms = round(cursor_frames * 1000 / SR)
            end_ms = round((cursor_frames + n) * 1000 / SR)
            item = {"chunk_id": chk["chunk_id"], "beat": chk["beat"], "start_ms": start_ms, "end_ms": end_ms,
                    "duration_ms": end_ms - start_ms, "pause_after_ms": pause_ms, "say_raw": chk["say"],
                    "say_normalized": chk["_say_norm"], "show": chk["show"]}
            for k in ("highlight_word", "sub_cut", "expression", "gojo_cue", "gojo_power", "fact_ref"):
                if k in chk:
                    item[k] = chk[k]
            words.append(item)
            cursor_frames += n + pause_frames
    os.replace(tmp, master)
    words_data = {"voice_id": voice_cfg["voice_id"], "engine": prov["engine"], "engine_version": prov["engine_version"],
                  "sample_rate_hz": SR, "channels": 2, "total_duration_ms": max(1000, round(cursor_frames * 1000 / SR)), "chunks": words}
    validate_words(words_data)
    with open(os.path.join(work_dir, "words.json"), "w", encoding="utf-8") as f:
        json.dump(words_data, f, ensure_ascii=False, indent=2)
    target_ms = int(spec["meta"]["target_sec"]) * 1000
    if words_data["total_duration_ms"] > 1.10 * target_ms:
        warn("RVS_WARN_120", "S7-L", f"voice {words_data['total_duration_ms']} ms > 110% of target {target_ms} ms — rate +8% suggest")
    stage_end("S7-L", f"{len(words)} chunks, {words_data['total_duration_ms']} ms, engine={prov['engine']}")
    return words_data


def validate_words(words_data: dict) -> None:
    try:
        import jsonschema
        schema = json.loads((SKILL_ROOT / "schemas" / "words.schema.json").read_text(encoding="utf-8"))
        errs = sorted(jsonschema.Draft202012Validator(schema).iter_errors(words_data), key=lambda e: e.path)
        if errs:
            raise RvsError("RVS_ERR_002", "; ".join(e.message for e in errs[:5]))
    except ImportError:
        warn("RVS_WARN_035", "S7-L", "jsonschema missing — words.json minimal check only")
        if not words_data["chunks"] or any(c["end_ms"] < c["start_ms"] for c in words_data["chunks"]):
            raise RvsError("RVS_ERR_002", "chunk timeline invalid")


def main() -> int:
    ap = argparse.ArgumentParser(description="S7-L voice pack builder")
    ap.add_argument("--spec", required=True)
    ap.add_argument("--work", required=True)
    ap.add_argument("--debug", action="store_true")
    a = ap.parse_args()
    os.makedirs(a.work, exist_ok=True)
    try:
        spec = json.load(open(a.spec, encoding="utf-8"))
    except (OSError, ValueError) as e:
        raise RvsError("RVS_ERR_001", f"spec unreadable: {e}") from e
    build_voice_pack(spec, a.work)
    log_event("INFO", "S7-L", "done", None, f"voice_master.wav + words.json in {a.work}")
    return None


if __name__ == "__main__":
    sys.exit(main_wrapper(main, "S7-L"))
