## Appendix P — v5.1 Open-Source Coverage Matrix (32 components) & Skill Supplement (`OSS-SKL-01..13`)

*(Method, 2 Nov 2026: stars/forks/last push from `repos.ecosyste.ms` + `api.deps.dev`, licence from the repo's LICENSE file via `raw.githubusercontent.com`, weekly downloads from `pypistats.org` / `api.npmjs.org`, model data from the Hugging Face API. github.com and api.github.com were blocked in the audit session, so GitHub "Used by" counts could not be read — projects without another independent signal are marked REFERENCE-ONLY. Qualification bar: ≥1000★ + one independent signal, activity ≤12 months, open licence for code AND weights. Decisions: `USE-AS-SKILL` / `TECHNIQUE-ONLY` / `NONE-FOUND`. Score = fit 30 + adoption 15 + maintenance 15 + licence 15 + constraint fit 10 + docs 10 + security 5. Evidence: `AUDIT_WORK/evidence/repo_*.json`, `pypistats_*.json`.)*

### P.1 Matrix

| CN | Tier | Component | Where | Qualified choice (owner/name) — adoption, licence | Decision | Integration mode | Skill | Score | Rejected / reference-only (reason) |
|---|---|---|---|---|---|---|---|---|---|
| CN-001 | T1 | Per-chunk TTS synthesis + timing | §7.2 G.2 | rany2/edge-tts (12.4k★ LGPL-3.0; PyPI 2.63M/wk) + thewh1teagle/kokoro-onnx (2.8k★ MIT; PyPI 412k/wk) + hexgrad/Kokoro-82M weights (Apache-2.0; 7.3k likes 11.4M dl/mo) | USE-AS-SKILL | DEPENDENCY-PINNED | OSS-SKL-01 | 88 | rhasspy/piper archived 2025-08 → OHF-Voice/piper1-gpl GPL-3.0, Hindi voices NC → rejected; resemble-ai/chatterbox (27.5k MIT) needs torch → Reject List; ai4bharat/IndicF5 151★ → bar fail |
| CN-002 | T2 | Hinglish phonetic normalizer | §7.2 #2 G.2 | — | NONE-FOUND | own code (stdlib re) | OSS-SKL-01 | — | savoirfairelinux/num2words 970★ last push 2025-05 (bar fail); indic-transliteration 213★ (bar fail) |
| CN-003 | T3 | Silence trim + 48k stereo lock | §7.2 G.2 | FFmpeg/FFmpeg (65.7k★ LGPL/GPL; official) silenceremove/aformat | USE-AS-SKILL | DEPENDENCY (CLI) | OSS-SKL-01 | 90 | — |
| CN-004 | T1 | Studio voice mastering chain (M1) | App O | FFmpeg/FFmpeg filters highpass/lowshelf/equalizer/highshelf/deesser/acompressor/alimiter + loudnorm | USE-AS-SKILL | DEPENDENCY (CLI) | OSS-SKL-11 | 90 | prompt hypothesis chain rejected by measurement |
| CN-005 | T1 | Two-pass loudnorm + sidechain BGM mix | §7.3 G.3 | FFmpeg/FFmpeg loudnorm/sidechaincompress/amix | USE-AS-SKILL | DEPENDENCY (CLI) + PATTERN-REIMPLEMENTED | OSS-SKL-05 | 86 | slhck/ffmpeg-normalize 1.5k★ MIT studied as pattern; independent signal fail (PyPI 6.4k/wk <10k) → REFERENCE-ONLY |
| CN-006 | T1 | Multi-aspect compositing/Ken Burns/scene render/encode | §7.3 §7.5.5 G.3 | FFmpeg/FFmpeg + python-pillow/Pillow (13.9k★ MIT-CMU; PyPI 160M/wk) | USE-AS-SKILL | DEPENDENCY-PINNED + PATTERN-REIMPLEMENTED | OSS-SKL-02 | 87 | harry0703/MoneyPrinterTurbo 135.8k★ MIT studied as pattern; independent signal NOT-VERIFIED (github.com blocked) → REFERENCE-ONLY |
| CN-007 | T2 | ASS captions writer + vector stars | §7.4 G.3 | libass/libass (1.19k★ ISC; required by FFmpeg ass filter per FFmpeg docs) | USE-AS-SKILL | DEPENDENCY (via FFmpeg) + stdlib writer | OSS-SKL-03 | 80 | tkarabela/pysubs2 445★ (<1000) → REPLACED |
| CN-008 | T3 | Poster palette extraction | §7.5.1 G.3 | python-pillow/Pillow Image.quantize(MEDIANCUT) | USE-AS-SKILL | DEPENDENCY-PINNED | OSS-SKL-04 | 84 | fengsp/color-thief-py 1.1k★ last push 2022-10-31 (>24 mo) → REPLACED |
| CN-009 | T2 | Glass data cards + cover/thumbnail renderer | §7.5.2 §7.7 G.3 G.4 | python-pillow/Pillow | USE-AS-SKILL | DEPENDENCY-PINNED + own layout | OSS-SKL-04 | 80 | — |
| CN-010 | T1 | 2D co-host rig + RMS lip-sync + cue timeline | §7.11 G.7 | — | NONE-FOUND (own design on Pillow+FFmpeg) | own code | OSS-SKL-06 | — | Open-LLM-VTuber/Open-LLM-VTuber 14.4k★ MIT and DanielSWolf/rhubarb-lip-sync 2.7k★ studied as patterns; independent signal NOT-VERIFIED → REFERENCE-ONLY; rotejin/MotionPNGTuber CUDA → Reject |
| CN-011 | T1 | Moment miner + derived audio assembly | §5.4 G.8 | — | NONE-FOUND (own design) | own code | OSS-SKL-07 | — | Anil-matcha/AI-Youtube-Shorts-Generator 5.7k★ MIT studied (pattern); independent signal NOT-VERIFIED → REFERENCE-ONLY; RayVentura/ShortGPT last push 2025-02-10 (>12 mo) → DROPPED |
| CN-012 | T2 | 7-gram originality guard (+fuzzy tier) | §6.3 §7.9 G.6 | rapidfuzz/RapidFuzz (4.2k★ MIT; PyPI 31.7M/wk) | USE-AS-SKILL | DEPENDENCY-PINNED (optional fuzzy tier; stdlib exact tier) | OSS-SKL-08 | 85 | fuzzywuzzy GPL → rejected |
| CN-013 | T2 | Devanagari→Roman phonetic skeleton | §7.9 G.6 | — | NONE-FOUND | own code | OSS-SKL-08 | — | indic-transliteration 213★ (bar fail) |
| CN-014 | T3 | Untrusted-text sanitizer | §5.2 S3 G.6 | — | NONE-FOUND (policy + regex defence-in-depth) | own code | OSS-SKL-08 | — | no library can neutralise prompt injection |
| CN-015 | T2 | JSON Schema validation | §7.1 C.7 C.8 | python-jsonschema/jsonschema (5.0k★ MIT; PyPI 145M/wk) | USE-AS-SKILL | DEPENDENCY-PINNED | OSS-SKL-09 | 90 | Termux: stdlib minimal validator fallback (RVS_WARN code) |
| CN-016 | T3 | Preflight probe + font resolver | §7.1 G.1 | — | NONE-FOUND (stdlib + ffmpeg -filters) | own code | OSS-SKL-09 | — | — |
| CN-017 | T2 | Contact sheet + 16-pt QA parsers | §6.4 §7.8 G.5 | FFmpeg/FFmpeg ffprobe/blackdetect/freezedetect/ebur128/tile | USE-AS-SKILL | DEPENDENCY (CLI) | OSS-SKL-09 | 88 | itsPremkumar/Automated-Video-Generator 121★ → DROPPED |
| CN-018 | T3 | Procedural SFX | §7.6 G.3 | FFmpeg/FFmpeg lavfi anoisesrc/sine/aevalsrc | USE-AS-SKILL | DEPENDENCY (CLI) | OSS-SKL-02 | 85 | — |
| CN-019 | T3 | Upload pack + chapter timestamps | §5.1 S10-L TPL-04 | — | NONE-FOUND (stdlib) | own code | — | — | — |
| CN-020 | T3 | RESUME PACK / VIDEO CARD handoff | TPL-05/06 | — | NONE-FOUND (template) | template | — | — | LangGraph checkpoints need server/DB → Reject List |
| CN-021 | T2 | Secrets loader | App H | theskumar/python-dotenv (8.9k★ BSD-3; PyPI 172M/wk) | USE-AS-SKILL | DEPENDENCY-PINNED (optional) + stdlib fallback | OSS-SKL-12 | 86 | — |
| CN-022 | T2 | Structured logging + crash report | App I | CPython stdlib logging + json | USE-AS-SKILL | stdlib | OSS-SKL-12 | 90 | structlog/python-json-logger not needed (stdlib sufficient, fewer deps) |
| CN-023 | T2 | Error code registry loader | App J | — | NONE-FOUND (stdlib json) | own code | OSS-SKL-12 | — | — |
| CN-024 | T2 | Prompt eval harness | App M | promptfoo/promptfoo (26.6k★ MIT; npm 1.30M/wk) optional live runner + own stdlib harness for CI | USE-AS-SKILL | TOOL (optional) + own harness | OSS-SKL-13 | 82 | deepeval/inspect evaluated by name only (not needed) |
| CN-025 | T2 | Test runner + CI | App N | pytest-dev/pytest (14.7k★ MIT; PyPI 219M/wk) + GitHub Actions | USE-AS-SKILL | DEPENDENCY-PINNED | OSS-SKL-13 | 92 | — |
| CN-026 | T3 | Mermaid validation | App Q | mermaid-js/mermaid-cli (5.1k★ MIT; npm 822k/wk) | USE-AS-SKILL | TOOL (CI only) | OSS-SKL-13 | 84 | — |
| CN-027 | T3 | Shell lint for render kit | Files 24–25 | koalaman/shellcheck (40.2k★ GPL-3.0) | USE-AS-SKILL | TOOL (separate process; CI only) | OSS-SKL-13 | 88 | — |
| CN-028 | T3 | ZIP packager | STAGE-4 | CPython zipfile | USE-AS-SKILL | stdlib | — | 90 | — |
| CN-029 | T2 | Premium TTS adapter | App O.4 | ElevenLabs REST API (official docs) via stdlib urllib | USE-AS-SKILL (official API) | own code | OSS-SKL-11 | — | vendor SDK not needed (one POST) |
| CN-030 | T2 | RP-4 / PC fallback compositor + motion curves | §10 #33 F2 | Zulko/moviepy (15.1k★ MIT; PyPI 1.35M/wk) optional; remotion-dev/remotion (69.8k★ Remotion licence; npm 3.6M/wk) TECHNIQUE-ONLY | USE-AS-SKILL / TECHNIQUE-ONLY | optional DEPENDENCY / clean-room curves | OSS-SKL-10 | 80 | — |
| CN-031 | T3 | Cost model calculator | App L | — | NONE-FOUND (stdlib) | own code | — | — | — |
| CN-032 | T3 | Floor offline TTS | §7.2 | espeak-ng/espeak-ng (7.0k★ GPL-3.0) | USE-AS-SKILL | DEPENDENCY (separate process) | OSS-SKL-01 | 78 | robotic quality; floor only |

### P.2 Repos replaced / dropped in v5.1 (old → new; `OWNER-06`)
| Old (v5.0) | Action | New | Evidence & reason |
|---|---|---|---|
| `rhasspy/piper` | REMOVED from engine chain | `thewh1teagle/kokoro-onnx` + Kokoro-82M (offline), `espeak-ng/espeak-ng` (floor) | repo `archived: true` (last push 2025-08-26); successor `OHF-Voice/piper1-gpl` is GPL-3.0 and its Hindi voices are non-commercial (NOT-OPEN) |
| `fengsp/color-thief-py` | REPLACED | `python-pillow/Pillow` (`Image.quantize`) | last push 2022-10-31 (>24 months); same median-cut technique already in Pillow (13.9k★) |
| `tkarabela/pysubs2` | REPLACED | `libass/libass` (renderer) + stdlib writer | 445★ < MIN_STARS 1000; the code never imported it |
| `RayVentura/ShortGPT` | DROPPED | — (pattern ref `Anil-matcha/AI-Youtube-Shorts-Generator` kept) | last push 2025-02-10 (>12 months) |
| `itsPremkumar/Automated-Video-Generator` | REPLACED | `FFmpeg/FFmpeg` QA filters | 121★ |
Old names survive only in Appendix F (history). Verified by `tools/repo_names.py --banned` (0 occurrences outside the changelog).

### P.3 Skill Supplement — fields missing in F2.5 (D-120) + new skills 11–13
| Skill | Trigger (when to load) | Integration mode | Error codes | Eval/tests (normal · edge · failing) | Footprint (App K/L) | Do-not-use-when | Re-check |
|---|---|---|---|---|---|---|---|
| `OSS-SKL-01` chunk TTS sync | `S7-L`/`S12` need narration audio + `words.json` | DEPENDENCY-PINNED (`edge-tts` 7.3.1, `kokoro-onnx` 0.6.1) | ERR_040, WARN_041/120/124/125/126 | TC-14 · TC-28 (edge absent → kokoro) · all engines missing → ERR_040 | Kokoro RTF 0.35 (B1); $0 | text is not Hindi/Hinglish (voices are hi only) | monthly (edge-tts endpoint drift) |
| `OSS-SKL-02` multi-aspect pipeline | `S8-L`/`S12` render scenes/encode | DEPENDENCY (FFmpeg CLI, Pillow) + PATTERN | ERR_050/051/055/070, WARN_052/124 | TC-11 · TC-29 resume · corrupt scene → WARN_052 | ≈3.2 s per output s at 1080p (B1) | 4K/8K on Termux | quarterly |
| `OSS-SKL-03` ASS captions & stars | writing `captions.ass` | DEPENDENCY (libass via FFmpeg) + stdlib | ERR_060 (star check) | TC-13 · half-star 0.5 · rating > max clamps | negligible | non-libass players (VSFilter) — escapes differ | yearly |
| `OSS-SKL-04` palette + glass cards + covers | backdrop/cards/covers | DEPENDENCY-PINNED (Pillow) | ERR_003, WARN_003/109 | TC-17 · grey poster → default palette · unreadable file → ERR_003 | <1 s per asset | — | yearly |
| `OSS-SKL-05` loudnorm + duck | final audio mix | DEPENDENCY (FFmpeg) + PATTERN (ffmpeg-normalize) | ERR_050, WARN_053 | TC-16/TC-22 · silence-heavy mix → dynamic mode logged · bad filter → WARN_053 | seconds | — | quarterly (FFmpeg drift R17) |
| `OSS-SKL-06` co-host rig | `S8-L` when `character.enabled` | own code (PATTERN refs) | WARN_054/083 | TC-21 · TC-37 rights gate · custom dir incomplete → WARN_054 | 8 s per 15 s incl. sprites | real-person likeness (Reject List) | yearly |
| `OSS-SKL-07` repurpose | `CUT SHORTS` | own code | ERR_001/002, WARN_118/119 | TC-20 · <2 strong moments → WARN_118 · bad chunk ids → ERR_002 | ≈3 s TTS per clip | master not approved (G5-L) | yearly |
| `OSS-SKL-08` originality guard | script/derived text vs transcripts | DEPENDENCY-PINNED optional (`rapidfuzz`) + stdlib | ERR_080, WARN_081/084/085 | TC-09 · TC-10 · TC-38 | <1 s | — | yearly |
| `OSS-SKL-09` schema + preflight + QA | `S7-L` preflight, `S9-L`/`S13` QA | DEPENDENCY-PINNED (`jsonschema`) + FFmpeg | ERR_001/004/030/031/033/036/060, WARN_034/035/061/072/073 | TC-23/25/27/30 | QA ≈0.24 s per output s | — | quarterly |
| `OSS-SKL-10` motion curves + MoviePy fallback | RP-4/PC fallback only | optional DEPENDENCY (`moviepy`) / TECHNIQUE-ONLY (`remotion`) | WARN_117 | §10 EC-33 | — | runtime default path | yearly |
| **`OSS-SKL-11` studio voice mastering** (new) | any time a voice stem is mixed | DEPENDENCY (FFmpeg filters) | WARN_053 | TC-35 · old FFmpeg → safe chain · filter error → bypass | negligible | music-only stems | quarterly |
| **`OSS-SKL-12` ops: telemetry, secrets, error registry** (new) | every script entry point | stdlib + optional `python-dotenv` | ERR_098/099, WARN_043/046/047/048 | TC-32 · TC-34 · registry integrity unit test | negligible | — | yearly |
| **`OSS-SKL-13` test, eval & CI tooling** (new) | CI and Builder `STAGE-4` | TOOL (`pytest`, `promptfoo` optional, `mermaid-cli`, `shellcheck`) | — | `pytest -q`, `run_evals.py` (37 cases), shellcheck | CI minutes | runtime | quarterly |

**New skill entries (skill_spec_template):**
- **`OSS-SKL-11` — Studio Voice Mastering (`voice-master-ffmpeg`).** Source: `FFmpeg/FFmpeg` filters (65.7k★, LGPL/GPL build-dependent, separate process), studied via official filter docs + `ffmpeg -h filter=…` on 6.1.1 (READ-DOCS-ONLY). Purpose: `CN-004`, stages `S8-L`/`S12`. Why: no qualified Python mastering library is needed — FFmpeg is already a dependency; the prompt's hypothesis chain was measured and rejected (sibilance +2.6–3.0 dB). Definition: input voice stem (48 kHz stereo) → `VOICE_MASTER_CHAIN_V1` → mix → two-pass loudnorm; checkpoints: ffmpeg exit code, final ebur128 in QA #6. Fail-soft: v1 → safe → bypass (`RVS_WARN_053`). Limits: tuned on Kokoro/edge-style 24 kHz TTS; recorded human voices may need less de-essing. Attribution: FFmpeg notice in `NOTICE.md`. Files: `scripts/voice_engines.py`, `scripts/build_video.py`.
- **`OSS-SKL-12` — Ops Layer (`rvs-ops-telemetry-secrets`).** Source: CPython stdlib `logging`/`json` + `theskumar/python-dotenv` (8.9k★, BSD-3-Clause, PyPI 172 M/week, optional). Purpose: `CN-021..CN-023`. Definition: `main_wrapper` → codes/exit codes; `log_event` → console + JSONL; `write_crash_report`; `load_env_file` + `redact`; `run_cmd` timeouts; `check_disk_space`. Limits: log cap 5 MiB per run (TARGET). Files: `scripts/rvs_common.py`, `schemas/error_codes*.json`.
- **`OSS-SKL-13` — Test/Eval/CI Tooling (`rvs-quality-tooling`).** Sources: `pytest-dev/pytest` (14.7k★, MIT, PyPI 219 M/week), `promptfoo/promptfoo` (26.6k★, MIT, npm 1.30 M/week, optional live evals), `mermaid-js/mermaid-cli` (5.1k★, MIT, npm 822 k/week), `koalaman/shellcheck` (40.2k★, GPL-3.0, CI-only separate process). Files: `tests/`, `evals/`, `.github/workflows/ci.yml`, `docs/diagrams.md`.
- **Upstream re-check policy (all skills):** on every `STAGE-0` run and at the intervals above: re-read version, licence file, last activity and open security advisories (OSV) for each qualified dependency; a licence change or archive flag → HIGH-IMPACT decision + Appendix F entry.
