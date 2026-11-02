## Appendix J — System Error Code Catalog (v5.1, addition C)

### J.1 Rules
- Format `RVS_ERR_nnn` = fatal (run stops, exit code ≠ 0/10), `RVS_WARN_nnn` = fail-soft (run continues, final exit `10`). `RVS` = Review Video Studio (DEC-08). Numbers are never reused.
- **Single source of truth:** `schemas/error_codes.json` (File 34) validated by `schemas/error_codes.schema.json` (File 35); scripts import it via `rvs_common.load_registry()`; this table is generated from the same data (checked by `tools/error_codes.py` in the audit — table == registry).
- Every §10 row `EC-01..EC-54` maps to ≥1 code and every code maps back to ≥1 `EC` row or a requirement; every code is raised in G.1–G.10 code or (LLM-stage codes, `raised_by: SKILL.md`) by the Skill's turn logic, and appears in ≥1 test (`TC-*`) or eval case (`EV-*`).
- Families: `001–019` input/spec · `030–039` environment · `040–049` voice/external service · `050–059` render · `060–069` QA · `070–079` time budget · `080–089` originality/policy · `090–099` process · `101–126` LLM-stage & S11–S13 heuristics.

### J.2 Catalog (66 codes: 18 ERR, 48 WARN)
| Code | Sev | Stage | Raised by | Trigger (measurable) | Edge-case IDs | User message (Hinglish) | Auto action | Exit | Resume hint | Test |
|---|---|---|---|---|---|---|---|---|---|---|
| `RVS_ERR_001` | ERR | S7-L/S12 | preflight.py | spec.json fails spec.schema.json (Draft 2020-12) or semantic checks (chapters ascending, ≥10 s, tier↔dimension) | EC-44 | spec.json invalid hai — field list neeche diya hai, theek karke dobara BUILD MASTER bolo. | abort; no render | INPUT (20) | spec.json fix karke same command | TC-23 |
| `RVS_ERR_002` | ERR | S7-L/S8-L | voice_pack.py, build_video.py | words.json missing or fails words.schema.json | EC-44 | words.json kharab/missing hai — voice step dobara chalega. | abort | INPUT (20) | voice_pack.py dobara chalao (cache se fast) | TC-23 |
| `RVS_ERR_003` | ERR | S8-L | build_video.py | Operator asset cannot be decoded by Pillow/ffprobe (corrupt file) | EC-45 | Asset file corrupt hai — doosri file do ya fallback card use hoga. | abort scene; ask Operator | INPUT (20) | Asset replace karke resume | TC-24 |
| `RVS_ERR_004` | ERR | S7-L | preflight.py | resolution_tier/aspect/width/height mismatch | EC-44 | Resolution tier aur width/height match nahi karte. | abort | INPUT (20) | SET RES dobara chuno | TC-23 |
| `RVS_ERR_030` | ERR | S7-L | rvs_common.run_cmd, preflight.py | ffmpeg/ffprobe/espeak binary not found on PATH | EC-13, EC-46 | FFmpeg nahi mila — RP-4 manual path ya Termux setup (§14.2) chalao. | abort → RP-4 hint | ENV (30) | §14.2 setup, phir resume | TC-25 |
| `RVS_ERR_031` | ERR | S7-L | preflight.py | A filter in REQUIRED_FILTERS missing from `ffmpeg -filters` | EC-46 | FFmpeg build mein zaroori filter missing hai. | abort → RP-2/RP-4 | ENV (30) | FFmpeg ≥5.1 full build install karo | TC-25 |
| `RVS_ERR_032` | ERR | S7-L/S8-L | rvs_common.check_disk_space | free disk < tier minimum (App K) | EC-41 | Disk space kam hai — purani renders delete karo. | abort before render | ENV (30) | Space free karke resume | TC-26 |
| `RVS_ERR_033` | ERR | S7-L | preflight.py | no Latin or no Devanagari font found in resolver chain | EC-13 | Font nahi mila — assets/fonts bundle check karo. | abort | ENV (30) | Fonts copy karke resume | TC-25 |
| `RVS_ERR_036` | ERR | S7-L | preflight.py | available RAM below tier minimum and no lower tier allowed | EC-42 | RAM kam hai is resolution ke liye. | abort (or auto-downgrade, see WARN_073) | ENV (30) | SET RES 1080P | TC-27 |
| `RVS_ERR_040` | ERR | S7-L/S12 | voice_engines.py | every engine in the chain failed for a chunk (no audio) | EC-35, EC-47 | Koi bhi voice engine kaam nahi kiya — internet/Termux voice pack (RP-2) use karo. | abort; no beep fallback | SERVICE (40) | RP-2 voice pack ya network ke baad resume | TC-28 |
| `RVS_ERR_050` | ERR | S8-L/S12 | build_video.py (run_cmd) | FFmpeg render/encode returned non-zero | EC-14, EC-16 | Render fail hua — crash_report dekho, resume se wahi scene dobara banega. | abort; keep valid scenes | RENDER (50) | Same command; valid scene_*.mp4 skip honge | TC-15 |
| `RVS_ERR_051` | ERR | S8-L/S9-L | rvs_common.ffprobe_duration, qa_contact_sheet.py | ffprobe cannot read output duration/streams | EC-45 | Output file padhi nahi ja rahi. | abort | RENDER (50) | Scene cache clear karke resume | TC-24 |
| `RVS_ERR_055` | ERR | S8-L | build_video.py | scene concat failed or concat duration ≠ Σ scene durations ±0.2 s | EC-37 | Scenes jodne mein galti. | abort | RENDER (50) | Resume | TC-29 |
| `RVS_ERR_060` | ERR | S9-L/S13 | qa_contact_sheet.py | one or more HARD QA checks (§6.4) failed | EC-15, EC-17, EC-22, EC-23 | 16-Point QA fail — video deliver nahi hogi; failing checks list dekho. | block delivery | QA (60) | Fix + re-render failing scenes | TC-30 |
| `RVS_ERR_070` | ERR | any | rvs_common.run_cmd | subprocess exceeded hard timeout (App K) | EC-48 | Step time-limit se zyada chala — RP-2/lower tier try karo. | abort; resumable | TIMEOUT (70) | Resume; ya SET RES 1080P | TC-31 |
| `RVS_ERR_080` | ERR | S5-L/S13 | similarity_check.py | ≥7-gram raw or phonetic match with any benchmark transcript | EC-20 | Script ki line kisi transcript se copy lag rahi hai — auto-rewrite. | exit 60; rewrite chunk | QA (60) | Rewrite ke baad similarity_check dobara | TC-09 |
| `RVS_ERR_098` | ERR | any | rvs_common.main_wrapper | KeyboardInterrupt / SIGINT | EC-37 | Run roka gaya. | stop; caches kept | CRASH (99) | Same command se resume | TC-31 |
| `RVS_ERR_099` | ERR | any | rvs_common.main_wrapper | unexpected exception (bug) | — | Unexpected crash — crash_report file share karo. | crash_report; exit 99 | CRASH (99) | --debug ke saath dobara chalao | TC-32 |
| `RVS_WARN_003` | WARN | S8-L | build_video.ensure_poster_exists | poster file missing → synthetic gradient poster used | EC-08 | Poster nahi mila — synthetic poster/cards se video ban rahi hai. | fallback poster_zoom/cards | WARN (10) | Poster attach karke re-render (optional) | TC-11 |
| `RVS_WARN_034` | WARN | S7-L | preflight.py | Pillow raqm/freetype missing or Devanagari shaping test fails | EC-29 | Devanagari shaping fail — captions Roman Hinglish mein honge. | caption_script=roman_hinglish | WARN (10) | RP-3/RP-1 with raqm | TC-12 |
| `RVS_WARN_035` | WARN | S7-L | preflight.py | optional python dependency missing (jsonschema/rapidfuzz/kokoro_onnx/dotenv) | EC-12 | Optional library missing — built-in fallback use ho raha hai. | fallback implementation | WARN (10) | requirements install (§14.2) | TC-25 |
| `RVS_WARN_041` | WARN | S7-L | voice_engines.py | edge-tts failed after 3 retries (403/429/NoAudioReceived/timeout/blocked) | EC-11, EC-35, EC-43 | edge-tts nahi chala — poori run agle engine (Kokoro) par switch. | switch engine for the whole run | WARN (10) | Network aane par fresh run (cache engine-keyed) | TC-28 |
| `RVS_WARN_042` | WARN | S7-L | voice_engines.py (premium) | premium TTS returned 401/403 (key rejected) | EC-49 | Premium voice key reject hui — local engine use ho raha hai. | fallback to default chain | WARN (10) | Key rotate karo (App H.4) | TC-33 |
| `RVS_WARN_043` | WARN | any | rvs_common.load_env_file | .env permissions wider than 600 | EC-50 | .env file dusre users padh sakte hain — chmod 600 .env karo. | continue | WARN (10) | chmod 600 .env | TC-34 |
| `RVS_WARN_044` | WARN | S7-L | voice_engines.py (premium) | premium TTS 429 / quota exhausted | EC-49 | Premium quota khatam — local engine. | fallback | WARN (10) | Quota reset ke baad | TC-33 |
| `RVS_WARN_045` | WARN | S7-L | voice_engines.py (premium) | premium TTS timeout/5xx/network error | EC-49 | Premium service slow/down — local engine. | fallback | WARN (10) | Baad mein retry | TC-33 |
| `RVS_WARN_046` | WARN | S7-L | preflight.py | ELEVENLABS_API_KEY present but RVS_PREMIUM_TTS is not 'on' | EC-50 | Premium key mili par toggle OFF hai — premium use NAHI hoga. | continue offline-first | WARN (10) | PREMIUM VOICE ON bolo agar chahiye | TC-34 |
| `RVS_WARN_047` | WARN | S7-L | preflight.py | RVS_PREMIUM_TTS=on but key missing | EC-50 | Premium ON hai par key missing — default engine. | fallback | WARN (10) | .env mein key daalo | TC-34 |
| `RVS_WARN_048` | WARN | S7-L | preflight.py | key present but malformed (length/space check) | EC-50 | Premium key ka format galat lag raha hai. | fallback | WARN (10) | Key dobara copy karo | TC-34 |
| `RVS_WARN_052` | WARN | S8-L | build_video.py | cached scene file invalid (ffprobe duration off >1 frame) → re-render | EC-37 | Purani scene file kharab thi — dobara render. | re-render scene | WARN (10) | — | TC-29 |
| `RVS_WARN_053` | WARN | S8-L/S12 | build_video.mix_and_normalize_audio_two_pass | voice master chain v1 failed → fallback chain → bypass | EC-51 | Voice mastering chain fail — safe chain use hua. | fallback chain, never abort | WARN (10) | FFmpeg version check | TC-35 |
| `RVS_WARN_054` | WARN | S8-L | character_overlay.py | custom sprite dir incomplete (missing closed/half/open/wide/blink) | EC-40 | Custom host sprites adhoore — original procedural host use. | procedural rig | WARN (10) | Missing PNGs add karo | TC-21 |
| `RVS_WARN_061` | WARN | S9-L | qa_contact_sheet.py | advisory/visual QA check needs human or soft threshold missed (vibrance, face framing) | EC-10 | Visual check manual confirm karo (contact_sheet.jpg). | flag in build_report | WARN (10) | Operator visual OK | TC-30 |
| `RVS_WARN_071` | WARN | any | rvs_common.run_summary | stage exceeded soft time budget (App K) | EC-48 | Step expected time se lamba chala. | continue; report | WARN (10) | — | TC-31 |
| `RVS_WARN_072` | WARN | S7-L | preflight.py | Termux render path and target_sec > 300 | EC-38 | Phone par lamba render — garam ho sakta hai; RP-2 recommend. | warn; continue if Operator OKs | WARN (10) | RP-2 Hybrid | TC-27 |
| `RVS_WARN_073` | WARN | S7-L | preflight.py | requested tier not allowed on this render path/RAM → auto-downgraded | EC-42 | Is device par 4K/8K allowed nahi — 1080p mein banega. | downgrade tier | WARN (10) | RP-1/PC par SET RES | TC-27 |
| `RVS_WARN_081` | WARN | S5-L | similarity_check.py | 5–6-gram overlap (or fuzzy ≥90) found | EC-20 | Kuch phrases milte-julte hain — paraphrase suggest. | report warnings | WARN (10) | — | TC-09 |
| `RVS_WARN_082` | WARN | S6-L/S8-L | build_video.py | third-party clip exceeds single (6.0 s) or total cap (§8.1) → trimmed | EC-34 | Clip cap se lambi thi — trim kar di. | trim/drop clip | WARN (10) | — | TC-36 |
| `RVS_WARN_083` | WARN | S6-L/S8-L | character_overlay.py, preflight.py | third-party character preset without declared asset_rights → original host rendered | EC-52 | Character rights declare nahi hue — original RVS host use ho raha hai. | render CHAR-RVS-ORIGINAL | WARN (10) | asset_rights declare karo (§7.11.3) | TC-37 |
| `RVS_WARN_084` | WARN | S3 | similarity_check.sanitize_untrusted_text | prompt-injection pattern stripped from untrusted input | EC-36 | External text mein instruction-jaisa text mila — hata diya. | strip + wrap <untrusted_evidence> | WARN (10) | — | TC-38 |
| `RVS_WARN_085` | WARN | S3 | similarity_check.strip_lyrics_and_sponsors | GAANA/SPONSOR_AD blocks stripped | EC-04, EC-21 | Lyrics/sponsor hissa analysis se hataya. | strip | WARN (10) | — | TC-10 |
| `RVS_WARN_101` | WARN | S2 | SKILL.md (LLM stage) | release <48 h and no ≥1M-view benchmark | EC-01 | Fresh release — 50K+ view benchmarks use honge. | Fresh Release Tier | WARN (10) | — | EV-PR05-02 |
| `RVS_WARN_102` | WARN | S3 | SKILL.md (LLM stage) | BOLA words/min < 85 or DIKHA missing | EC-02 | Transcript summary jaisa hai — PR-07 chalao. | emit PR-07 | WARN (10) | — | EV-PR05-03 |
| `RVS_WARN_103` | WARN | S3 | SKILL.md (LLM stage) | last timestamp < duration − 15 s or ⏸️ PAUSED AT present | EC-03 | Transcript adhoora — PR-06 continuation do. | emit PR-06 | WARN (10) | — | EV-PR06-01 |
| `RVS_WARN_105` | WARN | S4 | SKILL.md (LLM stage) | >35 % gap Day-1 vs Day-3+ sentiment | EC-05 | Review-bombing/PR distortion signal. | flag + HK-SPLIT | WARN (10) | — | EV-PR01-02 |
| `RVS_WARN_106` | WARN | S3 | SKILL.md (LLM stage) | <3 transcripts supplied | EC-06 | Kam transcripts — Confidence: Medium. | continue with confidence flag | WARN (10) | — | EV-S3-01 |
| `RVS_WARN_107` | WARN | S3 | SKILL.md (LLM stage) | transcripts > 35,000 words total | EC-07 | Transcripts bahut lambe — disk + Digest Cards. | digest mode | WARN (10) | — | EV-S3-01 |
| `RVS_WARN_108` | WARN | S6-L | SKILL.md (LLM stage) | Operator has no clips | EC-08 | Poster-Plus mode. | poster + cards | WARN (10) | — | TC-11 |
| `RVS_WARN_109` | WARN | S8-L | build_video.py | poster < 600 px or wrong aspect | EC-09 | Poster chhota hai — blur backdrop + sharpened card. | upscale+card | WARN (10) | — | TC-11 |
| `RVS_WARN_110` | WARN | S3 | SKILL.md (LLM stage) | research covers <3 categories | EC-25 | Research patli hai — Confidence: Low + narrow follow-up prompt. | follow-up prompt | WARN (10) | — | EV-PR10B-01 |
| `RVS_WARN_111` | WARN | S3 | SKILL.md (LLM stage) | no language dominates token ratio | EC-26 | Mixed-language transcript — as-is use. | note in digest | WARN (10) | — | EV-S3-01 |
| `RVS_WARN_112` | WARN | S3 | SKILL.md (LLM stage) | BOLA words ≪ DIKHA notes | EC-27 | Video mein bolna kam — visual notes par weight. | lower weight | WARN (10) | — | EV-S3-01 |
| `RVS_WARN_113` | WARN | S1/S2 | SKILL.md (LLM stage) | web search tool unavailable | EC-28 | Search tool nahi — PR-08A recipe se tum results laao. | emit PR-08A | WARN (10) | — | EV-PR08-01 |
| `RVS_WARN_114` | WARN | S1/S5-L | SKILL.md (LLM stage) | sensitive real event / spoiler-heavy topic | EC-30 | Sensitive topic — measured tone + spoiler flag. | editorial care | WARN (10) | — | EV-S5-02 |
| `RVS_WARN_115` | WARN | S1 | SKILL.md (LLM stage) | OS-A requested without PR-08B answers | EC-31 | Bina dekhe 'maine dekhi' nahi — OS-B use. | force OS-B | WARN (10) | — | EV-PR08-02 |
| `RVS_WARN_116` | WARN | S0 | SKILL.md (LLM stage) | no topic given | EC-32 | Topic nahi diya — Trend Radar chal raha hai. | run TREND RADAR | WARN (10) | — | EV-S1-01 |
| `RVS_WARN_117` | WARN | STAGE-2 | Builder (Appendix E) | ported technique failed smoke test twice | EC-33 | Technique drop — simple recipe use. | drop technique | WARN (10) | — | TC-32 |
| `RVS_WARN_118` | WARN | S11 | repurpose_shorts.mine_moments | fewer than 2 moments score ≥75 | EC-53 | Strong moments kam — ≥60 wale context patch ke saath. | lower threshold to 60 / report | WARN (10) | — | TC-20 |
| `RVS_WARN_119` | WARN | S11 | repurpose_shorts.mine_moments | moment self-contained clarity < 18/25 → context patch | EC-39 | Moment ko context patch chahiye. | prepend context patch | WARN (10) | — | TC-20 |
| `RVS_WARN_120` | WARN | S7-L | voice_pack.py | synth duration > 110 % of target_sec | EC-19 | Voice target se lambi — rate +8 %, pauses −30 %. | re-synth with faster rate | WARN (10) | — | TC-28 |
| `RVS_WARN_121` | WARN | S3 | SKILL.md (LLM stage) | Gemini reply says ACCESS FAILED | EC-54 | Gemini video nahi khol paya — PR-07 ya doosra URL. | emit PR-07/replace URL | WARN (10) | — | EV-PR05-01 |
| `RVS_WARN_122` | WARN | S3 | SKILL.md (LLM stage) | dossier numbers without URL | EC-25 | Bina source ke numbers — PR-10B audit prompt. | emit PR-10B | WARN (10) | — | EV-PR10B-01 |
| `RVS_WARN_123` | WARN | any | SKILL.md (LLM stage) | chat quota/session ends | EC-24 | Nayi chat mein RESUME PACK + RVS RESUME paste karo. | emit RESUME PACK | WARN (10) | RVS RESUME | TC-18 |
| `RVS_WARN_124` | WARN | S7-L/S8-L | voice_pack.py, build_video.py | resumed from cache (chunks/scenes reused) | EC-37 | Pichli run ke cache se resume. | skip completed work | WARN (10) | — | TC-29 |
| `RVS_WARN_125` | WARN | S7-L | voice_pack.normalize_tts_say | unnormalised rating/number pattern left in say text (e.g. 8.25/10) | EC-18 | Kuch number TTS ke liye normalize nahi hua — script check karo. | synthesize as-is; report | WARN (10) | — | TC-14 |
| `RVS_WARN_126` | WARN | S7-L | voice_engines.py | engine returned <100 ms audio for a chunk → retried once | EC-47 | Chunk audio khali tha — dobara synth. | retry once then next engine | WARN (10) | — | TC-28 |

### J.3 Exit Codes (all CLIs, `rvs_common.EXIT`)
| Exit | Class | Meaning |
|---|---|---|
| `0` | OK | success, no warnings |
| `10` | WARN | success with ≥1 `RVS_WARN_*` (deliverable OK; read the summary) |
| `20` | INPUT | spec/words/media input invalid |
| `30` | ENV | missing binary/filter/font/RAM/disk |
| `40` | SERVICE | every voice engine failed |
| `50` | RENDER | FFmpeg render/concat/probe failure |
| `60` | QA | 16-Point QA hard fail or 7-gram originality fail — delivery blocked |
| `70` | TIMEOUT | hard time budget exceeded |
| `99` | CRASH | unexpected exception / interrupt (crash report written) |

### J.4 Registry file `schemas/error_codes.json` (File 34)
```json
{
  "registry_version": "1.0.0",
  "prd_version": "5.1",
  "format": "RVS_(ERR|WARN)_nnn",
  "exit_codes": {"OK": 0, "WARN": 10, "INPUT": 20, "ENV": 30, "SERVICE": 40, "RENDER": 50, "QA": 60, "TIMEOUT": 70, "CRASH": 99},
  "codes": [
    {
      "code": "RVS_ERR_001",
      "severity": "ERR",
      "stage": "S7-L/S12",
      "raised_by": "preflight.py",
      "trigger": "spec.json fails spec.schema.json (Draft 2020-12) or semantic checks (chapters ascending, ≥10 s, tier↔dimension)",
      "edge_case_ids": ["EC-44"],
      "message_hinglish": "spec.json invalid hai — field list neeche diya hai, theek karke dobara BUILD MASTER bolo.",
      "action": "abort; no render",
      "exit": "INPUT",
      "resume_hint": "spec.json fix karke same command",
      "test_id": "TC-23"
    },
    {
      "code": "RVS_ERR_002",
      "severity": "ERR",
      "stage": "S7-L/S8-L",
      "raised_by": "voice_pack.py, build_video.py",
      "trigger": "words.json missing or fails words.schema.json",
      "edge_case_ids": ["EC-44"],
      "message_hinglish": "words.json kharab/missing hai — voice step dobara chalega.",
      "action": "abort",
      "exit": "INPUT",
      "resume_hint": "voice_pack.py dobara chalao (cache se fast)",
      "test_id": "TC-23"
    },
    {
      "code": "RVS_ERR_003",
      "severity": "ERR",
      "stage": "S8-L",
      "raised_by": "build_video.py",
      "trigger": "Operator asset cannot be decoded by Pillow/ffprobe (corrupt file)",
      "edge_case_ids": ["EC-45"],
      "message_hinglish": "Asset file corrupt hai — doosri file do ya fallback card use hoga.",
      "action": "abort scene; ask Operator",
      "exit": "INPUT",
      "resume_hint": "Asset replace karke resume",
      "test_id": "TC-24"
    },
    {"code": "RVS_ERR_004", "severity": "ERR", "stage": "S7-L", "raised_by": "preflight.py", "trigger": "resolution_tier/aspect/width/height mismatch", "edge_case_ids": ["EC-44"], "message_hinglish": "Resolution tier aur width/height match nahi karte.", "action": "abort", "exit": "INPUT", "resume_hint": "SET RES dobara chuno", "test_id": "TC-23"},
    {
      "code": "RVS_ERR_030",
      "severity": "ERR",
      "stage": "S7-L",
      "raised_by": "rvs_common.run_cmd, preflight.py",
      "trigger": "ffmpeg/ffprobe/espeak binary not found on PATH",
      "edge_case_ids": ["EC-13", "EC-46"],
      "message_hinglish": "FFmpeg nahi mila — RP-4 manual path ya Termux setup (§14.2) chalao.",
      "action": "abort → RP-4 hint",
      "exit": "ENV",
      "resume_hint": "§14.2 setup, phir resume",
      "test_id": "TC-25"
    },
    {"code": "RVS_ERR_031", "severity": "ERR", "stage": "S7-L", "raised_by": "preflight.py", "trigger": "A filter in REQUIRED_FILTERS missing from `ffmpeg -filters`", "edge_case_ids": ["EC-46"], "message_hinglish": "FFmpeg build mein zaroori filter missing hai.", "action": "abort → RP-2/RP-4", "exit": "ENV", "resume_hint": "FFmpeg ≥5.1 full build install karo", "test_id": "TC-25"},
    {"code": "RVS_ERR_032", "severity": "ERR", "stage": "S7-L/S8-L", "raised_by": "rvs_common.check_disk_space", "trigger": "free disk < tier minimum (App K)", "edge_case_ids": ["EC-41"], "message_hinglish": "Disk space kam hai — purani renders delete karo.", "action": "abort before render", "exit": "ENV", "resume_hint": "Space free karke resume", "test_id": "TC-26"},
    {"code": "RVS_ERR_033", "severity": "ERR", "stage": "S7-L", "raised_by": "preflight.py", "trigger": "no Latin or no Devanagari font found in resolver chain", "edge_case_ids": ["EC-13"], "message_hinglish": "Font nahi mila — assets/fonts bundle check karo.", "action": "abort", "exit": "ENV", "resume_hint": "Fonts copy karke resume", "test_id": "TC-25"},
    {"code": "RVS_ERR_036", "severity": "ERR", "stage": "S7-L", "raised_by": "preflight.py", "trigger": "available RAM below tier minimum and no lower tier allowed", "edge_case_ids": ["EC-42"], "message_hinglish": "RAM kam hai is resolution ke liye.", "action": "abort (or auto-downgrade, see WARN_073)", "exit": "ENV", "resume_hint": "SET RES 1080P", "test_id": "TC-27"},
    {
      "code": "RVS_ERR_040",
      "severity": "ERR",
      "stage": "S7-L/S12",
      "raised_by": "voice_engines.py",
      "trigger": "every engine in the chain failed for a chunk (no audio)",
      "edge_case_ids": ["EC-35", "EC-47"],
      "message_hinglish": "Koi bhi voice engine kaam nahi kiya — internet/Termux voice pack (RP-2) use karo.",
      "action": "abort; no beep fallback",
      "exit": "SERVICE",
      "resume_hint": "RP-2 voice pack ya network ke baad resume",
      "test_id": "TC-28"
    },
    {
      "code": "RVS_ERR_050",
      "severity": "ERR",
      "stage": "S8-L/S12",
      "raised_by": "build_video.py (run_cmd)",
      "trigger": "FFmpeg render/encode returned non-zero",
      "edge_case_ids": ["EC-14", "EC-16"],
      "message_hinglish": "Render fail hua — crash_report dekho, resume se wahi scene dobara banega.",
      "action": "abort; keep valid scenes",
      "exit": "RENDER",
      "resume_hint": "Same command; valid scene_*.mp4 skip honge",
      "test_id": "TC-15"
    },
    {"code": "RVS_ERR_051", "severity": "ERR", "stage": "S8-L/S9-L", "raised_by": "rvs_common.ffprobe_duration, qa_contact_sheet.py", "trigger": "ffprobe cannot read output duration/streams", "edge_case_ids": ["EC-45"], "message_hinglish": "Output file padhi nahi ja rahi.", "action": "abort", "exit": "RENDER", "resume_hint": "Scene cache clear karke resume", "test_id": "TC-24"},
    {"code": "RVS_ERR_055", "severity": "ERR", "stage": "S8-L", "raised_by": "build_video.py", "trigger": "scene concat failed or concat duration ≠ Σ scene durations ±0.2 s", "edge_case_ids": ["EC-37"], "message_hinglish": "Scenes jodne mein galti.", "action": "abort", "exit": "RENDER", "resume_hint": "Resume", "test_id": "TC-29"},
    {
      "code": "RVS_ERR_060",
      "severity": "ERR",
      "stage": "S9-L/S13",
      "raised_by": "qa_contact_sheet.py",
      "trigger": "one or more HARD QA checks (§6.4) failed",
      "edge_case_ids": ["EC-15", "EC-17", "EC-22", "EC-23"],
      "message_hinglish": "16-Point QA fail — video deliver nahi hogi; failing checks list dekho.",
      "action": "block delivery",
      "exit": "QA",
      "resume_hint": "Fix + re-render failing scenes",
      "test_id": "TC-30"
    },
    {"code": "RVS_ERR_070", "severity": "ERR", "stage": "any", "raised_by": "rvs_common.run_cmd", "trigger": "subprocess exceeded hard timeout (App K)", "edge_case_ids": ["EC-48"], "message_hinglish": "Step time-limit se zyada chala — RP-2/lower tier try karo.", "action": "abort; resumable", "exit": "TIMEOUT", "resume_hint": "Resume; ya SET RES 1080P", "test_id": "TC-31"},
    {
      "code": "RVS_ERR_080",
      "severity": "ERR",
      "stage": "S5-L/S13",
      "raised_by": "similarity_check.py",
      "trigger": "≥7-gram raw or phonetic match with any benchmark transcript",
      "edge_case_ids": ["EC-20"],
      "message_hinglish": "Script ki line kisi transcript se copy lag rahi hai — auto-rewrite.",
      "action": "exit 60; rewrite chunk",
      "exit": "QA",
      "resume_hint": "Rewrite ke baad similarity_check dobara",
      "test_id": "TC-09"
    },
    {"code": "RVS_ERR_098", "severity": "ERR", "stage": "any", "raised_by": "rvs_common.main_wrapper", "trigger": "KeyboardInterrupt / SIGINT", "edge_case_ids": ["EC-37"], "message_hinglish": "Run roka gaya.", "action": "stop; caches kept", "exit": "CRASH", "resume_hint": "Same command se resume", "test_id": "TC-31"},
    {"code": "RVS_ERR_099", "severity": "ERR", "stage": "any", "raised_by": "rvs_common.main_wrapper", "trigger": "unexpected exception (bug)", "edge_case_ids": [], "message_hinglish": "Unexpected crash — crash_report file share karo.", "action": "crash_report; exit 99", "exit": "CRASH", "resume_hint": "--debug ke saath dobara chalao", "test_id": "TC-32"},
    {
      "code": "RVS_WARN_003",
      "severity": "WARN",
      "stage": "S8-L",
      "raised_by": "build_video.ensure_poster_exists",
      "trigger": "poster file missing → synthetic gradient poster used",
      "edge_case_ids": ["EC-08"],
      "message_hinglish": "Poster nahi mila — synthetic poster/cards se video ban rahi hai.",
      "action": "fallback poster_zoom/cards",
      "exit": "WARN",
      "resume_hint": "Poster attach karke re-render (optional)",
      "test_id": "TC-11"
    },
    {"code": "RVS_WARN_034", "severity": "WARN", "stage": "S7-L", "raised_by": "preflight.py", "trigger": "Pillow raqm/freetype missing or Devanagari shaping test fails", "edge_case_ids": ["EC-29"], "message_hinglish": "Devanagari shaping fail — captions Roman Hinglish mein honge.", "action": "caption_script=roman_hinglish", "exit": "WARN", "resume_hint": "RP-3/RP-1 with raqm", "test_id": "TC-12"},
    {
      "code": "RVS_WARN_035",
      "severity": "WARN",
      "stage": "S7-L",
      "raised_by": "preflight.py",
      "trigger": "optional python dependency missing (jsonschema/rapidfuzz/kokoro_onnx/dotenv)",
      "edge_case_ids": ["EC-12"],
      "message_hinglish": "Optional library missing — built-in fallback use ho raha hai.",
      "action": "fallback implementation",
      "exit": "WARN",
      "resume_hint": "requirements install (§14.2)",
      "test_id": "TC-25"
    },
    {
      "code": "RVS_WARN_041",
      "severity": "WARN",
      "stage": "S7-L",
      "raised_by": "voice_engines.py",
      "trigger": "edge-tts failed after 3 retries (403/429/NoAudioReceived/timeout/blocked)",
      "edge_case_ids": ["EC-11", "EC-35", "EC-43"],
      "message_hinglish": "edge-tts nahi chala — poori run agle engine (Kokoro) par switch.",
      "action": "switch engine for the whole run",
      "exit": "WARN",
      "resume_hint": "Network aane par fresh run (cache engine-keyed)",
      "test_id": "TC-28"
    },
    {"code": "RVS_WARN_042", "severity": "WARN", "stage": "S7-L", "raised_by": "voice_engines.py (premium)", "trigger": "premium TTS returned 401/403 (key rejected)", "edge_case_ids": ["EC-49"], "message_hinglish": "Premium voice key reject hui — local engine use ho raha hai.", "action": "fallback to default chain", "exit": "WARN", "resume_hint": "Key rotate karo (App H.4)", "test_id": "TC-33"},
    {"code": "RVS_WARN_043", "severity": "WARN", "stage": "any", "raised_by": "rvs_common.load_env_file", "trigger": ".env permissions wider than 600", "edge_case_ids": ["EC-50"], "message_hinglish": ".env file dusre users padh sakte hain — chmod 600 .env karo.", "action": "continue", "exit": "WARN", "resume_hint": "chmod 600 .env", "test_id": "TC-34"},
    {"code": "RVS_WARN_044", "severity": "WARN", "stage": "S7-L", "raised_by": "voice_engines.py (premium)", "trigger": "premium TTS 429 / quota exhausted", "edge_case_ids": ["EC-49"], "message_hinglish": "Premium quota khatam — local engine.", "action": "fallback", "exit": "WARN", "resume_hint": "Quota reset ke baad", "test_id": "TC-33"},
    {"code": "RVS_WARN_045", "severity": "WARN", "stage": "S7-L", "raised_by": "voice_engines.py (premium)", "trigger": "premium TTS timeout/5xx/network error", "edge_case_ids": ["EC-49"], "message_hinglish": "Premium service slow/down — local engine.", "action": "fallback", "exit": "WARN", "resume_hint": "Baad mein retry", "test_id": "TC-33"},
    {
      "code": "RVS_WARN_046",
      "severity": "WARN",
      "stage": "S7-L",
      "raised_by": "preflight.py",
      "trigger": "ELEVENLABS_API_KEY present but RVS_PREMIUM_TTS is not 'on'",
      "edge_case_ids": ["EC-50"],
      "message_hinglish": "Premium key mili par toggle OFF hai — premium use NAHI hoga.",
      "action": "continue offline-first",
      "exit": "WARN",
      "resume_hint": "PREMIUM VOICE ON bolo agar chahiye",
      "test_id": "TC-34"
    },
    {"code": "RVS_WARN_047", "severity": "WARN", "stage": "S7-L", "raised_by": "preflight.py", "trigger": "RVS_PREMIUM_TTS=on but key missing", "edge_case_ids": ["EC-50"], "message_hinglish": "Premium ON hai par key missing — default engine.", "action": "fallback", "exit": "WARN", "resume_hint": ".env mein key daalo", "test_id": "TC-34"},
    {"code": "RVS_WARN_048", "severity": "WARN", "stage": "S7-L", "raised_by": "preflight.py", "trigger": "key present but malformed (length/space check)", "edge_case_ids": ["EC-50"], "message_hinglish": "Premium key ka format galat lag raha hai.", "action": "fallback", "exit": "WARN", "resume_hint": "Key dobara copy karo", "test_id": "TC-34"},
    {"code": "RVS_WARN_052", "severity": "WARN", "stage": "S8-L", "raised_by": "build_video.py", "trigger": "cached scene file invalid (ffprobe duration off >1 frame) → re-render", "edge_case_ids": ["EC-37"], "message_hinglish": "Purani scene file kharab thi — dobara render.", "action": "re-render scene", "exit": "WARN", "resume_hint": "—", "test_id": "TC-29"},
    {
      "code": "RVS_WARN_053",
      "severity": "WARN",
      "stage": "S8-L/S12",
      "raised_by": "build_video.mix_and_normalize_audio_two_pass",
      "trigger": "voice master chain v1 failed → fallback chain → bypass",
      "edge_case_ids": ["EC-51"],
      "message_hinglish": "Voice mastering chain fail — safe chain use hua.",
      "action": "fallback chain, never abort",
      "exit": "WARN",
      "resume_hint": "FFmpeg version check",
      "test_id": "TC-35"
    },
    {"code": "RVS_WARN_054", "severity": "WARN", "stage": "S8-L", "raised_by": "character_overlay.py", "trigger": "custom sprite dir incomplete (missing closed/half/open/wide/blink)", "edge_case_ids": ["EC-40"], "message_hinglish": "Custom host sprites adhoore — original procedural host use.", "action": "procedural rig", "exit": "WARN", "resume_hint": "Missing PNGs add karo", "test_id": "TC-21"},
    {
      "code": "RVS_WARN_061",
      "severity": "WARN",
      "stage": "S9-L",
      "raised_by": "qa_contact_sheet.py",
      "trigger": "advisory/visual QA check needs human or soft threshold missed (vibrance, face framing)",
      "edge_case_ids": ["EC-10"],
      "message_hinglish": "Visual check manual confirm karo (contact_sheet.jpg).",
      "action": "flag in build_report",
      "exit": "WARN",
      "resume_hint": "Operator visual OK",
      "test_id": "TC-30"
    },
    {"code": "RVS_WARN_071", "severity": "WARN", "stage": "any", "raised_by": "rvs_common.run_summary", "trigger": "stage exceeded soft time budget (App K)", "edge_case_ids": ["EC-48"], "message_hinglish": "Step expected time se lamba chala.", "action": "continue; report", "exit": "WARN", "resume_hint": "—", "test_id": "TC-31"},
    {"code": "RVS_WARN_072", "severity": "WARN", "stage": "S7-L", "raised_by": "preflight.py", "trigger": "Termux render path and target_sec > 300", "edge_case_ids": ["EC-38"], "message_hinglish": "Phone par lamba render — garam ho sakta hai; RP-2 recommend.", "action": "warn; continue if Operator OKs", "exit": "WARN", "resume_hint": "RP-2 Hybrid", "test_id": "TC-27"},
    {"code": "RVS_WARN_073", "severity": "WARN", "stage": "S7-L", "raised_by": "preflight.py", "trigger": "requested tier not allowed on this render path/RAM → auto-downgraded", "edge_case_ids": ["EC-42"], "message_hinglish": "Is device par 4K/8K allowed nahi — 1080p mein banega.", "action": "downgrade tier", "exit": "WARN", "resume_hint": "RP-1/PC par SET RES", "test_id": "TC-27"},
    {"code": "RVS_WARN_081", "severity": "WARN", "stage": "S5-L", "raised_by": "similarity_check.py", "trigger": "5–6-gram overlap (or fuzzy ≥90) found", "edge_case_ids": ["EC-20"], "message_hinglish": "Kuch phrases milte-julte hain — paraphrase suggest.", "action": "report warnings", "exit": "WARN", "resume_hint": "—", "test_id": "TC-09"},
    {"code": "RVS_WARN_082", "severity": "WARN", "stage": "S6-L/S8-L", "raised_by": "build_video.py", "trigger": "third-party clip exceeds single (6.0 s) or total cap (§8.1) → trimmed", "edge_case_ids": ["EC-34"], "message_hinglish": "Clip cap se lambi thi — trim kar di.", "action": "trim/drop clip", "exit": "WARN", "resume_hint": "—", "test_id": "TC-36"},
    {
      "code": "RVS_WARN_083",
      "severity": "WARN",
      "stage": "S6-L/S8-L",
      "raised_by": "character_overlay.py, preflight.py",
      "trigger": "third-party character preset without declared asset_rights → original host rendered",
      "edge_case_ids": ["EC-52"],
      "message_hinglish": "Character rights declare nahi hue — original RVS host use ho raha hai.",
      "action": "render CHAR-RVS-ORIGINAL",
      "exit": "WARN",
      "resume_hint": "asset_rights declare karo (§7.11.3)",
      "test_id": "TC-37"
    },
    {
      "code": "RVS_WARN_084",
      "severity": "WARN",
      "stage": "S3",
      "raised_by": "similarity_check.sanitize_untrusted_text",
      "trigger": "prompt-injection pattern stripped from untrusted input",
      "edge_case_ids": ["EC-36"],
      "message_hinglish": "External text mein instruction-jaisa text mila — hata diya.",
      "action": "strip + wrap <untrusted_evidence>",
      "exit": "WARN",
      "resume_hint": "—",
      "test_id": "TC-38"
    },
    {"code": "RVS_WARN_085", "severity": "WARN", "stage": "S3", "raised_by": "similarity_check.strip_lyrics_and_sponsors", "trigger": "GAANA/SPONSOR_AD blocks stripped", "edge_case_ids": ["EC-04", "EC-21"], "message_hinglish": "Lyrics/sponsor hissa analysis se hataya.", "action": "strip", "exit": "WARN", "resume_hint": "—", "test_id": "TC-10"},
    {"code": "RVS_WARN_101", "severity": "WARN", "stage": "S2", "raised_by": "SKILL.md (LLM stage)", "trigger": "release <48 h and no ≥1M-view benchmark", "edge_case_ids": ["EC-01"], "message_hinglish": "Fresh release — 50K+ view benchmarks use honge.", "action": "Fresh Release Tier", "exit": "WARN", "resume_hint": "—", "test_id": "EV-PR05-02"},
    {"code": "RVS_WARN_102", "severity": "WARN", "stage": "S3", "raised_by": "SKILL.md (LLM stage)", "trigger": "BOLA words/min < 85 or DIKHA missing", "edge_case_ids": ["EC-02"], "message_hinglish": "Transcript summary jaisa hai — PR-07 chalao.", "action": "emit PR-07", "exit": "WARN", "resume_hint": "—", "test_id": "EV-PR05-03"},
    {"code": "RVS_WARN_103", "severity": "WARN", "stage": "S3", "raised_by": "SKILL.md (LLM stage)", "trigger": "last timestamp < duration − 15 s or ⏸️ PAUSED AT present", "edge_case_ids": ["EC-03"], "message_hinglish": "Transcript adhoora — PR-06 continuation do.", "action": "emit PR-06", "exit": "WARN", "resume_hint": "—", "test_id": "EV-PR06-01"},
    {"code": "RVS_WARN_105", "severity": "WARN", "stage": "S4", "raised_by": "SKILL.md (LLM stage)", "trigger": ">35 % gap Day-1 vs Day-3+ sentiment", "edge_case_ids": ["EC-05"], "message_hinglish": "Review-bombing/PR distortion signal.", "action": "flag + HK-SPLIT", "exit": "WARN", "resume_hint": "—", "test_id": "EV-PR01-02"},
    {"code": "RVS_WARN_106", "severity": "WARN", "stage": "S3", "raised_by": "SKILL.md (LLM stage)", "trigger": "<3 transcripts supplied", "edge_case_ids": ["EC-06"], "message_hinglish": "Kam transcripts — Confidence: Medium.", "action": "continue with confidence flag", "exit": "WARN", "resume_hint": "—", "test_id": "EV-S3-01"},
    {"code": "RVS_WARN_107", "severity": "WARN", "stage": "S3", "raised_by": "SKILL.md (LLM stage)", "trigger": "transcripts > 35,000 words total", "edge_case_ids": ["EC-07"], "message_hinglish": "Transcripts bahut lambe — disk + Digest Cards.", "action": "digest mode", "exit": "WARN", "resume_hint": "—", "test_id": "EV-S3-01"},
    {"code": "RVS_WARN_108", "severity": "WARN", "stage": "S6-L", "raised_by": "SKILL.md (LLM stage)", "trigger": "Operator has no clips", "edge_case_ids": ["EC-08"], "message_hinglish": "Poster-Plus mode.", "action": "poster + cards", "exit": "WARN", "resume_hint": "—", "test_id": "TC-11"},
    {"code": "RVS_WARN_109", "severity": "WARN", "stage": "S8-L", "raised_by": "build_video.py", "trigger": "poster < 600 px or wrong aspect", "edge_case_ids": ["EC-09"], "message_hinglish": "Poster chhota hai — blur backdrop + sharpened card.", "action": "upscale+card", "exit": "WARN", "resume_hint": "—", "test_id": "TC-11"},
    {"code": "RVS_WARN_110", "severity": "WARN", "stage": "S3", "raised_by": "SKILL.md (LLM stage)", "trigger": "research covers <3 categories", "edge_case_ids": ["EC-25"], "message_hinglish": "Research patli hai — Confidence: Low + narrow follow-up prompt.", "action": "follow-up prompt", "exit": "WARN", "resume_hint": "—", "test_id": "EV-PR10B-01"},
    {"code": "RVS_WARN_111", "severity": "WARN", "stage": "S3", "raised_by": "SKILL.md (LLM stage)", "trigger": "no language dominates token ratio", "edge_case_ids": ["EC-26"], "message_hinglish": "Mixed-language transcript — as-is use.", "action": "note in digest", "exit": "WARN", "resume_hint": "—", "test_id": "EV-S3-01"},
    {"code": "RVS_WARN_112", "severity": "WARN", "stage": "S3", "raised_by": "SKILL.md (LLM stage)", "trigger": "BOLA words ≪ DIKHA notes", "edge_case_ids": ["EC-27"], "message_hinglish": "Video mein bolna kam — visual notes par weight.", "action": "lower weight", "exit": "WARN", "resume_hint": "—", "test_id": "EV-S3-01"},
    {"code": "RVS_WARN_113", "severity": "WARN", "stage": "S1/S2", "raised_by": "SKILL.md (LLM stage)", "trigger": "web search tool unavailable", "edge_case_ids": ["EC-28"], "message_hinglish": "Search tool nahi — PR-08A recipe se tum results laao.", "action": "emit PR-08A", "exit": "WARN", "resume_hint": "—", "test_id": "EV-PR08-01"},
    {"code": "RVS_WARN_114", "severity": "WARN", "stage": "S1/S5-L", "raised_by": "SKILL.md (LLM stage)", "trigger": "sensitive real event / spoiler-heavy topic", "edge_case_ids": ["EC-30"], "message_hinglish": "Sensitive topic — measured tone + spoiler flag.", "action": "editorial care", "exit": "WARN", "resume_hint": "—", "test_id": "EV-S5-02"},
    {"code": "RVS_WARN_115", "severity": "WARN", "stage": "S1", "raised_by": "SKILL.md (LLM stage)", "trigger": "OS-A requested without PR-08B answers", "edge_case_ids": ["EC-31"], "message_hinglish": "Bina dekhe 'maine dekhi' nahi — OS-B use.", "action": "force OS-B", "exit": "WARN", "resume_hint": "—", "test_id": "EV-PR08-02"},
    {"code": "RVS_WARN_116", "severity": "WARN", "stage": "S0", "raised_by": "SKILL.md (LLM stage)", "trigger": "no topic given", "edge_case_ids": ["EC-32"], "message_hinglish": "Topic nahi diya — Trend Radar chal raha hai.", "action": "run TREND RADAR", "exit": "WARN", "resume_hint": "—", "test_id": "EV-S1-01"},
    {"code": "RVS_WARN_117", "severity": "WARN", "stage": "STAGE-2", "raised_by": "Builder (Appendix E)", "trigger": "ported technique failed smoke test twice", "edge_case_ids": ["EC-33"], "message_hinglish": "Technique drop — simple recipe use.", "action": "drop technique", "exit": "WARN", "resume_hint": "—", "test_id": "TC-32"},
    {"code": "RVS_WARN_118", "severity": "WARN", "stage": "S11", "raised_by": "repurpose_shorts.mine_moments", "trigger": "fewer than 2 moments score ≥75", "edge_case_ids": ["EC-53"], "message_hinglish": "Strong moments kam — ≥60 wale context patch ke saath.", "action": "lower threshold to 60 / report", "exit": "WARN", "resume_hint": "—", "test_id": "TC-20"},
    {"code": "RVS_WARN_119", "severity": "WARN", "stage": "S11", "raised_by": "repurpose_shorts.mine_moments", "trigger": "moment self-contained clarity < 18/25 → context patch", "edge_case_ids": ["EC-39"], "message_hinglish": "Moment ko context patch chahiye.", "action": "prepend context patch", "exit": "WARN", "resume_hint": "—", "test_id": "TC-20"},
    {"code": "RVS_WARN_120", "severity": "WARN", "stage": "S7-L", "raised_by": "voice_pack.py", "trigger": "synth duration > 110 % of target_sec", "edge_case_ids": ["EC-19"], "message_hinglish": "Voice target se lambi — rate +8 %, pauses −30 %.", "action": "re-synth with faster rate", "exit": "WARN", "resume_hint": "—", "test_id": "TC-28"},
    {"code": "RVS_WARN_121", "severity": "WARN", "stage": "S3", "raised_by": "SKILL.md (LLM stage)", "trigger": "Gemini reply says ACCESS FAILED", "edge_case_ids": ["EC-54"], "message_hinglish": "Gemini video nahi khol paya — PR-07 ya doosra URL.", "action": "emit PR-07/replace URL", "exit": "WARN", "resume_hint": "—", "test_id": "EV-PR05-01"},
    {"code": "RVS_WARN_122", "severity": "WARN", "stage": "S3", "raised_by": "SKILL.md (LLM stage)", "trigger": "dossier numbers without URL", "edge_case_ids": ["EC-25"], "message_hinglish": "Bina source ke numbers — PR-10B audit prompt.", "action": "emit PR-10B", "exit": "WARN", "resume_hint": "—", "test_id": "EV-PR10B-01"},
    {"code": "RVS_WARN_123", "severity": "WARN", "stage": "any", "raised_by": "SKILL.md (LLM stage)", "trigger": "chat quota/session ends", "edge_case_ids": ["EC-24"], "message_hinglish": "Nayi chat mein RESUME PACK + RVS RESUME paste karo.", "action": "emit RESUME PACK", "exit": "WARN", "resume_hint": "RVS RESUME", "test_id": "TC-18"},
    {"code": "RVS_WARN_124", "severity": "WARN", "stage": "S7-L/S8-L", "raised_by": "voice_pack.py, build_video.py", "trigger": "resumed from cache (chunks/scenes reused)", "edge_case_ids": ["EC-37"], "message_hinglish": "Pichli run ke cache se resume.", "action": "skip completed work", "exit": "WARN", "resume_hint": "—", "test_id": "TC-29"},
    {"code": "RVS_WARN_125", "severity": "WARN", "stage": "S7-L", "raised_by": "voice_pack.normalize_tts_say", "trigger": "unnormalised rating/number pattern left in say text (e.g. 8.25/10)", "edge_case_ids": ["EC-18"], "message_hinglish": "Kuch number TTS ke liye normalize nahi hua — script check karo.", "action": "synthesize as-is; report", "exit": "WARN", "resume_hint": "—", "test_id": "TC-14"},
    {"code": "RVS_WARN_126", "severity": "WARN", "stage": "S7-L", "raised_by": "voice_engines.py", "trigger": "engine returned <100 ms audio for a chunk → retried once", "edge_case_ids": ["EC-47"], "message_hinglish": "Chunk audio khali tha — dobara synth.", "action": "retry once then next engine", "exit": "WARN", "resume_hint": "—", "test_id": "TC-28"}
  ]
}
```

### J.5 Registry schema `schemas/error_codes.schema.json` (File 35)
```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://review-video-studio.local/schemas/error_codes.schema.json",
  "title": "RvsErrorRegistry",
  "type": "object",
  "required": ["registry_version", "format", "exit_codes", "codes"],
  "additionalProperties": false,
  "properties": {
    "registry_version": {"type": "string"},
    "prd_version": {"type": "string"},
    "format": {"type": "string"},
    "exit_codes": {"type": "object", "additionalProperties": {"type": "integer", "minimum": 0, "maximum": 255}},
    "codes": {
      "type": "array",
      "minItems": 1,
      "items": {
        "type": "object",
        "additionalProperties": false,
        "required": ["code", "severity", "stage", "raised_by", "trigger", "edge_case_ids", "message_hinglish", "action", "exit", "resume_hint", "test_id"],
        "properties": {
          "code": {"type": "string", "pattern": "^RVS_(ERR|WARN)_[0-9]{3}$"},
          "severity": {"enum": ["ERR", "WARN"]},
          "stage": {"type": "string"},
          "raised_by": {"type": "string"},
          "trigger": {"type": "string", "minLength": 5},
          "edge_case_ids": {"type": "array", "items": {"type": "string", "pattern": "^EC-[0-9]{2}$"}},
          "message_hinglish": {"type": "string", "minLength": 5},
          "action": {"type": "string"},
          "exit": {"enum": ["OK", "WARN", "INPUT", "ENV", "SERVICE", "RENDER", "QA", "TIMEOUT", "CRASH"]},
          "resume_hint": {"type": "string"},
          "test_id": {"type": "string", "pattern": "^(TC-[0-9]{2}|EV-[A-Z0-9-]+)$"}
        }
      }
    }
  }
}
```
