#!/usr/bin/env python3
"""Builds schemas/error_codes.json (single source of truth) + its JSON Schema + the PRD Markdown table.
Usage: build_registry.py OUT_DIR   -> OUT_DIR/schemas/error_codes.json, error_codes.schema.json, AUDIT_WORK/drafts/error_table.md"""
import json, os, sys

# code, sev, stage, script/raiser, trigger, edge_ids, message_hinglish, action, exit, resume_hint, test_id
C = [
 ("RVS_ERR_001","ERR","S7-L/S12","preflight.py","spec.json fails spec.schema.json (Draft 2020-12) or semantic checks (chapters ascending, ≥10 s, tier↔dimension)","EC-44","spec.json invalid hai — field list neeche diya hai, theek karke dobara BUILD MASTER bolo.","abort; no render","INPUT","spec.json fix karke same command","TC-23"),
 ("RVS_ERR_002","ERR","S7-L/S8-L","voice_pack.py, build_video.py","words.json missing or fails words.schema.json","EC-44","words.json kharab/missing hai — voice step dobara chalega.","abort","INPUT","voice_pack.py dobara chalao (cache se fast)","TC-23"),
 ("RVS_ERR_003","ERR","S8-L","build_video.py","Operator asset cannot be decoded by Pillow/ffprobe (corrupt file)","EC-45","Asset file corrupt hai — doosri file do ya fallback card use hoga.","abort scene; ask Operator","INPUT","Asset replace karke resume","TC-24"),
 ("RVS_ERR_004","ERR","S7-L","preflight.py","resolution_tier/aspect/width/height mismatch","EC-44","Resolution tier aur width/height match nahi karte.","abort","INPUT","SET RES dobara chuno","TC-23"),
 ("RVS_ERR_030","ERR","S7-L","rvs_common.run_cmd, preflight.py","ffmpeg/ffprobe/espeak binary not found on PATH","EC-13, EC-46","FFmpeg nahi mila — RP-4 manual path ya Termux setup (§14.2) chalao.","abort → RP-4 hint","ENV","§14.2 setup, phir resume","TC-25"),
 ("RVS_ERR_031","ERR","S7-L","preflight.py","A filter in REQUIRED_FILTERS missing from `ffmpeg -filters`","EC-46","FFmpeg build mein zaroori filter missing hai.","abort → RP-2/RP-4","ENV","FFmpeg ≥5.1 full build install karo","TC-25"),
 ("RVS_ERR_032","ERR","S7-L/S8-L","rvs_common.check_disk_space","free disk < tier minimum (App K)","EC-41","Disk space kam hai — purani renders delete karo.","abort before render","ENV","Space free karke resume","TC-26"),
 ("RVS_ERR_033","ERR","S7-L","preflight.py","no Latin or no Devanagari font found in resolver chain","EC-13","Font nahi mila — assets/fonts bundle check karo.","abort","ENV","Fonts copy karke resume","TC-25"),
 ("RVS_ERR_036","ERR","S7-L","preflight.py","available RAM below tier minimum and no lower tier allowed","EC-42","RAM kam hai is resolution ke liye.","abort (or auto-downgrade, see WARN_073)","ENV","SET RES 1080P","TC-27"),
 ("RVS_ERR_040","ERR","S7-L/S12","voice_engines.py","every engine in the chain failed for a chunk (no audio)","EC-35, EC-47","Koi bhi voice engine kaam nahi kiya — internet/Termux voice pack (RP-2) use karo.","abort; no beep fallback","SERVICE","RP-2 voice pack ya network ke baad resume","TC-28"),
 ("RVS_ERR_050","ERR","S8-L/S12","build_video.py (run_cmd)","FFmpeg render/encode returned non-zero","EC-14, EC-16","Render fail hua — crash_report dekho, resume se wahi scene dobara banega.","abort; keep valid scenes","RENDER","Same command; valid scene_*.mp4 skip honge","TC-15"),
 ("RVS_ERR_051","ERR","S8-L/S9-L","rvs_common.ffprobe_duration, qa_contact_sheet.py","ffprobe cannot read output duration/streams","EC-45","Output file padhi nahi ja rahi.","abort","RENDER","Scene cache clear karke resume","TC-24"),
 ("RVS_ERR_055","ERR","S8-L","build_video.py","scene concat failed or concat duration ≠ Σ scene durations ±0.2 s","EC-37","Scenes jodne mein galti.","abort","RENDER","Resume","TC-29"),
 ("RVS_ERR_060","ERR","S9-L/S13","qa_contact_sheet.py","one or more HARD QA checks (§6.4) failed","EC-15, EC-17, EC-22, EC-23","16-Point QA fail — video deliver nahi hogi; failing checks list dekho.","block delivery","QA","Fix + re-render failing scenes","TC-30"),
 ("RVS_ERR_070","ERR","any","rvs_common.run_cmd","subprocess exceeded hard timeout (App K)","EC-48","Step time-limit se zyada chala — RP-2/lower tier try karo.","abort; resumable","TIMEOUT","Resume; ya SET RES 1080P","TC-31"),
 ("RVS_ERR_080","ERR","S5-L/S13","similarity_check.py","≥7-gram raw or phonetic match with any benchmark transcript","EC-20","Script ki line kisi transcript se copy lag rahi hai — auto-rewrite.","exit 60; rewrite chunk","QA","Rewrite ke baad similarity_check dobara","TC-09"),
 ("RVS_ERR_098","ERR","any","rvs_common.main_wrapper","KeyboardInterrupt / SIGINT","EC-37","Run roka gaya.","stop; caches kept","CRASH","Same command se resume","TC-31"),
 ("RVS_ERR_099","ERR","any","rvs_common.main_wrapper","unexpected exception (bug)","—","Unexpected crash — crash_report file share karo.","crash_report; exit 99","CRASH","--debug ke saath dobara chalao","TC-32"),
 ("RVS_WARN_003","WARN","S8-L","build_video.ensure_poster_exists","poster file missing → synthetic gradient poster used","EC-08","Poster nahi mila — synthetic poster/cards se video ban rahi hai.","fallback poster_zoom/cards","WARN","Poster attach karke re-render (optional)","TC-11"),
 ("RVS_WARN_034","WARN","S7-L","preflight.py","Pillow raqm/freetype missing or Devanagari shaping test fails","EC-29","Devanagari shaping fail — captions Roman Hinglish mein honge.","caption_script=roman_hinglish","WARN","RP-3/RP-1 with raqm","TC-12"),
 ("RVS_WARN_035","WARN","S7-L","preflight.py","optional python dependency missing (jsonschema/rapidfuzz/kokoro_onnx/dotenv)","EC-12","Optional library missing — built-in fallback use ho raha hai.","fallback implementation","WARN","requirements install (§14.2)","TC-25"),
 ("RVS_WARN_041","WARN","S7-L","voice_engines.py","edge-tts failed after 3 retries (403/429/NoAudioReceived/timeout/blocked)","EC-11, EC-35, EC-43","edge-tts nahi chala — poori run agle engine (Kokoro) par switch.","switch engine for the whole run","WARN","Network aane par fresh run (cache engine-keyed)","TC-28"),
 ("RVS_WARN_042","WARN","S7-L","voice_engines.py (premium)","premium TTS returned 401/403 (key rejected)","EC-49","Premium voice key reject hui — local engine use ho raha hai.","fallback to default chain","WARN","Key rotate karo (App H.4)","TC-33"),
 ("RVS_WARN_043","WARN","any","rvs_common.load_env_file",".env permissions wider than 600","EC-50",".env file dusre users padh sakte hain — chmod 600 .env karo.","continue","WARN","chmod 600 .env","TC-34"),
 ("RVS_WARN_044","WARN","S7-L","voice_engines.py (premium)","premium TTS 429 / quota exhausted","EC-49","Premium quota khatam — local engine.","fallback","WARN","Quota reset ke baad","TC-33"),
 ("RVS_WARN_045","WARN","S7-L","voice_engines.py (premium)","premium TTS timeout/5xx/network error","EC-49","Premium service slow/down — local engine.","fallback","WARN","Baad mein retry","TC-33"),
 ("RVS_WARN_046","WARN","S7-L","preflight.py","ELEVENLABS_API_KEY present but RVS_PREMIUM_TTS is not 'on'","EC-50","Premium key mili par toggle OFF hai — premium use NAHI hoga.","continue offline-first","WARN","PREMIUM VOICE ON bolo agar chahiye","TC-34"),
 ("RVS_WARN_047","WARN","S7-L","preflight.py","RVS_PREMIUM_TTS=on but key missing","EC-50","Premium ON hai par key missing — default engine.","fallback","WARN",".env mein key daalo","TC-34"),
 ("RVS_WARN_048","WARN","S7-L","preflight.py","key present but malformed (length/space check)","EC-50","Premium key ka format galat lag raha hai.","fallback","WARN","Key dobara copy karo","TC-34"),
 ("RVS_WARN_052","WARN","S8-L","build_video.py","cached scene file invalid (ffprobe duration off >1 frame) → re-render","EC-37","Purani scene file kharab thi — dobara render.","re-render scene","WARN","—","TC-29"),
 ("RVS_WARN_053","WARN","S8-L/S12","build_video.mix_and_normalize_audio_two_pass","voice master chain v1 failed → fallback chain → bypass","EC-51","Voice mastering chain fail — safe chain use hua.","fallback chain, never abort","WARN","FFmpeg version check","TC-35"),
 ("RVS_WARN_054","WARN","S8-L","character_overlay.py","custom sprite dir incomplete (missing closed/half/open/wide/blink)","EC-40","Custom host sprites adhoore — original procedural host use.","procedural rig","WARN","Missing PNGs add karo","TC-21"),
 ("RVS_WARN_061","WARN","S9-L","qa_contact_sheet.py","advisory/visual QA check needs human or soft threshold missed (vibrance, face framing)","EC-10","Visual check manual confirm karo (contact_sheet.jpg).","flag in build_report","WARN","Operator visual OK","TC-30"),
 ("RVS_WARN_071","WARN","any","rvs_common.run_summary","stage exceeded soft time budget (App K)","EC-48","Step expected time se lamba chala.","continue; report","WARN","—","TC-31"),
 ("RVS_WARN_072","WARN","S7-L","preflight.py","Termux render path and target_sec > 300","EC-38","Phone par lamba render — garam ho sakta hai; RP-2 recommend.","warn; continue if Operator OKs","WARN","RP-2 Hybrid","TC-27"),
 ("RVS_WARN_073","WARN","S7-L","preflight.py","requested tier not allowed on this render path/RAM → auto-downgraded","EC-42","Is device par 4K/8K allowed nahi — 1080p mein banega.","downgrade tier","WARN","RP-1/PC par SET RES","TC-27"),
 ("RVS_WARN_081","WARN","S5-L","similarity_check.py","5–6-gram overlap (or fuzzy ≥90) found","EC-20","Kuch phrases milte-julte hain — paraphrase suggest.","report warnings","WARN","—","TC-09"),
 ("RVS_WARN_082","WARN","S6-L/S8-L","build_video.py","third-party clip exceeds single (6.0 s) or total cap (§8.1) → trimmed","EC-34","Clip cap se lambi thi — trim kar di.","trim/drop clip","WARN","—","TC-36"),
 ("RVS_WARN_083","WARN","S6-L/S8-L","character_overlay.py, preflight.py","third-party character preset without declared asset_rights → original host rendered","EC-52","Character rights declare nahi hue — original RVS host use ho raha hai.","render CHAR-RVS-ORIGINAL","WARN","asset_rights declare karo (§7.11.3)","TC-37"),
 ("RVS_WARN_084","WARN","S3","similarity_check.sanitize_untrusted_text","prompt-injection pattern stripped from untrusted input","EC-36","External text mein instruction-jaisa text mila — hata diya.","strip + wrap <untrusted_evidence>","WARN","—","TC-38"),
 ("RVS_WARN_085","WARN","S3","similarity_check.strip_lyrics_and_sponsors","GAANA/SPONSOR_AD blocks stripped","EC-04, EC-21","Lyrics/sponsor hissa analysis se hataya.","strip","WARN","—","TC-10"),
 ("RVS_WARN_101","WARN","S2","SKILL.md (LLM stage)","release <48 h and no ≥1M-view benchmark","EC-01","Fresh release — 50K+ view benchmarks use honge.","Fresh Release Tier","WARN","—","EV-PR05-02"),
 ("RVS_WARN_102","WARN","S3","SKILL.md (LLM stage)","BOLA words/min < 85 or DIKHA missing","EC-02","Transcript summary jaisa hai — PR-07 chalao.","emit PR-07","WARN","—","EV-PR05-03"),
 ("RVS_WARN_103","WARN","S3","SKILL.md (LLM stage)","last timestamp < duration − 15 s or ⏸️ PAUSED AT present","EC-03","Transcript adhoora — PR-06 continuation do.","emit PR-06","WARN","—","EV-PR06-01"),
 ("RVS_WARN_105","WARN","S4","SKILL.md (LLM stage)",">35 % gap Day-1 vs Day-3+ sentiment","EC-05","Review-bombing/PR distortion signal.","flag + HK-SPLIT","WARN","—","EV-PR01-02"),
 ("RVS_WARN_106","WARN","S3","SKILL.md (LLM stage)","<3 transcripts supplied","EC-06","Kam transcripts — Confidence: Medium.","continue with confidence flag","WARN","—","EV-S3-01"),
 ("RVS_WARN_107","WARN","S3","SKILL.md (LLM stage)","transcripts > 35,000 words total","EC-07","Transcripts bahut lambe — disk + Digest Cards.","digest mode","WARN","—","EV-S3-01"),
 ("RVS_WARN_108","WARN","S6-L","SKILL.md (LLM stage)","Operator has no clips","EC-08","Poster-Plus mode.","poster + cards","WARN","—","TC-11"),
 ("RVS_WARN_109","WARN","S8-L","build_video.py","poster < 600 px or wrong aspect","EC-09","Poster chhota hai — blur backdrop + sharpened card.","upscale+card","WARN","—","TC-11"),
 ("RVS_WARN_110","WARN","S3","SKILL.md (LLM stage)","research covers <3 categories","EC-25","Research patli hai — Confidence: Low + narrow follow-up prompt.","follow-up prompt","WARN","—","EV-PR10B-01"),
 ("RVS_WARN_111","WARN","S3","SKILL.md (LLM stage)","no language dominates token ratio","EC-26","Mixed-language transcript — as-is use.","note in digest","WARN","—","EV-S3-01"),
 ("RVS_WARN_112","WARN","S3","SKILL.md (LLM stage)","BOLA words ≪ DIKHA notes","EC-27","Video mein bolna kam — visual notes par weight.","lower weight","WARN","—","EV-S3-01"),
 ("RVS_WARN_113","WARN","S1/S2","SKILL.md (LLM stage)","web search tool unavailable","EC-28","Search tool nahi — PR-08A recipe se tum results laao.","emit PR-08A","WARN","—","EV-PR08-01"),
 ("RVS_WARN_114","WARN","S1/S5-L","SKILL.md (LLM stage)","sensitive real event / spoiler-heavy topic","EC-30","Sensitive topic — measured tone + spoiler flag.","editorial care","WARN","—","EV-S5-02"),
 ("RVS_WARN_115","WARN","S1","SKILL.md (LLM stage)","OS-A requested without PR-08B answers","EC-31","Bina dekhe 'maine dekhi' nahi — OS-B use.","force OS-B","WARN","—","EV-PR08-02"),
 ("RVS_WARN_116","WARN","S0","SKILL.md (LLM stage)","no topic given","EC-32","Topic nahi diya — Trend Radar chal raha hai.","run TREND RADAR","WARN","—","EV-S1-01"),
 ("RVS_WARN_117","WARN","STAGE-2","Builder (Appendix E)","ported technique failed smoke test twice","EC-33","Technique drop — simple recipe use.","drop technique","WARN","—","TC-32"),
 ("RVS_WARN_118","WARN","S11","repurpose_shorts.mine_moments","fewer than 2 moments score ≥75","EC-53","Strong moments kam — ≥60 wale context patch ke saath.","lower threshold to 60 / report","WARN","—","TC-20"),
 ("RVS_WARN_119","WARN","S11","repurpose_shorts.mine_moments","moment self-contained clarity < 18/25 → context patch","EC-39","Moment ko context patch chahiye.","prepend context patch","WARN","—","TC-20"),
 ("RVS_WARN_120","WARN","S7-L","voice_pack.py","synth duration > 110 % of target_sec","EC-19","Voice target se lambi — rate +8 %, pauses −30 %.","re-synth with faster rate","WARN","—","TC-28"),
 ("RVS_WARN_121","WARN","S3","SKILL.md (LLM stage)","Gemini reply says ACCESS FAILED","EC-54","Gemini video nahi khol paya — PR-07 ya doosra URL.","emit PR-07/replace URL","WARN","—","EV-PR05-01"),
 ("RVS_WARN_122","WARN","S3","SKILL.md (LLM stage)","dossier numbers without URL","EC-25","Bina source ke numbers — PR-10B audit prompt.","emit PR-10B","WARN","—","EV-PR10B-01"),
 ("RVS_WARN_123","WARN","any","SKILL.md (LLM stage)","chat quota/session ends","EC-24","Nayi chat mein RESUME PACK + RVS RESUME paste karo.","emit RESUME PACK","WARN","RVS RESUME","TC-18"),
 ("RVS_WARN_124","WARN","S7-L/S8-L","voice_pack.py, build_video.py","resumed from cache (chunks/scenes reused)","EC-37","Pichli run ke cache se resume.","skip completed work","WARN","—","TC-29"),
 ("RVS_WARN_125","WARN","S7-L","voice_pack.normalize_tts_say","unnormalised rating/number pattern left in say text (e.g. 8.25/10)","EC-18","Kuch number TTS ke liye normalize nahi hua — script check karo.","synthesize as-is; report","WARN","—","TC-14"),
 ("RVS_WARN_126","WARN","S7-L","voice_engines.py","engine returned <100 ms audio for a chunk → retried once","EC-47","Chunk audio khali tha — dobara synth.","retry once then next engine","WARN","—","TC-28"),
]

def main(out_dir):
    entries = []
    for (code, sev, stage, script, trig, edges, msg, action, exit_c, hint, test) in C:
        entries.append({"code": code, "severity": sev, "stage": stage, "raised_by": script, "trigger": trig,
                        "edge_case_ids": [e.strip() for e in edges.split(",") if e.strip() and e.strip() != "—"],
                        "message_hinglish": msg, "action": action, "exit": exit_c, "resume_hint": hint, "test_id": test})
    codes = [e["code"] for e in entries]
    assert len(codes) == len(set(codes)), "duplicate code"
    reg = {"registry_version": "1.0.0", "prd_version": "5.1", "format": "RVS_(ERR|WARN)_nnn",
           "exit_codes": {"OK": 0, "WARN": 10, "INPUT": 20, "ENV": 30, "SERVICE": 40, "RENDER": 50, "QA": 60, "TIMEOUT": 70, "CRASH": 99},
           "codes": entries}
    schema = {"$schema": "https://json-schema.org/draft/2020-12/schema", "$id": "https://review-video-studio.local/schemas/error_codes.schema.json",
              "title": "RvsErrorRegistry", "type": "object", "required": ["registry_version", "format", "exit_codes", "codes"],
              "additionalProperties": False,
              "properties": {"registry_version": {"type": "string"}, "prd_version": {"type": "string"}, "format": {"type": "string"},
                             "exit_codes": {"type": "object", "additionalProperties": {"type": "integer", "minimum": 0, "maximum": 255}},
                             "codes": {"type": "array", "minItems": 1, "items": {"type": "object", "additionalProperties": False,
                                       "required": ["code", "severity", "stage", "raised_by", "trigger", "edge_case_ids", "message_hinglish", "action", "exit", "resume_hint", "test_id"],
                                       "properties": {"code": {"type": "string", "pattern": "^RVS_(ERR|WARN)_[0-9]{3}$"},
                                                      "severity": {"enum": ["ERR", "WARN"]}, "stage": {"type": "string"}, "raised_by": {"type": "string"},
                                                      "trigger": {"type": "string", "minLength": 5}, "edge_case_ids": {"type": "array", "items": {"type": "string", "pattern": "^EC-[0-9]{2}$"}},
                                                      "message_hinglish": {"type": "string", "minLength": 5}, "action": {"type": "string"},
                                                      "exit": {"enum": ["OK", "WARN", "INPUT", "ENV", "SERVICE", "RENDER", "QA", "TIMEOUT", "CRASH"]},
                                                      "resume_hint": {"type": "string"}, "test_id": {"type": "string", "pattern": "^(TC-[0-9]{2}|EV-[A-Z0-9-]+)$"}}}}}}
    os.makedirs(os.path.join(out_dir, "schemas"), exist_ok=True)
    json.dump(reg, open(os.path.join(out_dir, "schemas", "error_codes.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    json.dump(schema, open(os.path.join(out_dir, "schemas", "error_codes.schema.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    rows = ["| Code | Sev | Stage | Raised by | Trigger (measurable) | Edge-case IDs | User message (Hinglish) | Auto action | Exit | Resume hint | Test |",
            "|---|---|---|---|---|---|---|---|---|---|---|"]
    for e in entries:
        cell = lambda s: str(s).replace("|", "\\|")
        rows.append("| " + " | ".join(cell(x) for x in [f"`{e['code']}`", e["severity"], e["stage"], e["raised_by"], e["trigger"],
                                                           ", ".join(e["edge_case_ids"]) or "—", e["message_hinglish"], e["action"],
                                                           f"{e['exit']} ({reg['exit_codes'][e['exit']]})", e["resume_hint"], e["test_id"]]) + " |")
    os.makedirs(os.path.join(os.path.dirname(__file__), "..", "drafts"), exist_ok=True)
    open(os.path.join(os.path.dirname(__file__), "..", "drafts", "error_table.md"), "w", encoding="utf-8").write("\n".join(rows) + "\n")
    print(f"codes={len(entries)} ERR={sum(e['severity']=='ERR' for e in entries)} WARN={sum(e['severity']=='WARN' for e in entries)}")

if __name__ == "__main__":
    main(sys.argv[1])
