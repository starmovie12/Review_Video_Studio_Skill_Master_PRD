# PRD Audit Report — Review Video Studio Master PRD v5.0 → v5.1 (INTERIM CHECKPOINT)

> **Status: AUDIT INCOMPLETE — checkpoint save (2 Nov 2026).** Phase 0–4 (probe, intake, full read, OSS sweep, voice lab, enterprise layer, PRD edits) ho chuke hain. **Phase 5 (adversarial re-audit rounds + cold-read subagent pass) aur final report abhi baaki hain** — RESUME PACK: `AUDIT_WORK/STATE.md`. Is liye completion stamp print nahi kiya gaya.

## 1. Pehle ye dekho — HIGH-IMPACT decisions (undo instructions ke saath)
| ID | Decision | Kyun | Undo |
|---|---|---|---|
| DEC-01 | Hard Rule 1 amended: runtime network sirf 2 enumerated exceptions (default `edge-tts`, optional Premium Voice) | PRD ka core contradiction (D-006): "zero external server" vs `edge-tts` online | Exception list hata kar default engine `kokoro-onnx` karo |
| DEC-02 | Optional Premium Voice Path (ElevenLabs `eleven_multilingual_v2`), **default OFF**, toggle + key dono zaroori | OWNER-09 / M1.4 | `ElevenLabsPremium` class, 4 env vars, D17, App O.4 hatao |
| DEC-03 | Engine chain per-run switch: edge-tts → **kokoro-onnx (Primary HQ LOCAL)** → espeak-ng; sine-beep fallback removed | P0 D-126 (beeps instead of speech), D-125 cache poisoning | — (v5.0 behaviour unsafe) |
| DEC-04 | Character Asset Rights Gate: Gojo/L/Conan presets sirf declared rights ke saath; warna `CHAR-RVS-ORIGINAL` | P0 D-063 third-party IP risk — **lawyer se confirm (NEEDS-HUMAN)** | `asset_rights` default `licensed` |
| DEC-05/06 | Repos replaced/dropped (Piper archived, color-thief inactive, pysubs2 445★, ShortGPT inactive, Automated-Video-Generator 121★) | OSS qualification bar | App P se purane naam wapas (not recommended) |
| DEC-07 | License Gate me "Dependency use" column (LGPL lib OK, GPL sirf separate process) | edge-tts LGPL-3.0, FFmpeg GPL build | Column hatao → edge-tts drop karna padega |

## 2. Capability probe, integrity, hashes
- Probe: files ✓, bash ✓, python 3.13.18, git, gh (token invalid), WebSearch/WebFetch ✓, subagents ✓, FFmpeg/ffprobe 6.1.1 (sab required filters ✓), node 22, pytest, shellcheck, jq; HF/PyPI/npm/deps.dev/ecosyste.ms reachable; github.com + api.github.com **blocked** (session policy) → GitHub "Used by" counts NOT-RUN.
- Original `PRD.md`: 378,490 B, sha256 `34027b60…f4c77`, 3,753 lines, 124 headings, 21 tables, 42 code blocks, fences balanced — **sha256 unchanged at checkpoint ✓**.
- `PRD_UPDATED.md`: 607,163 B, sha256 `36ab46a9728a53b6fb8e9268a71b9e3b1b985c6b546049b0f778b5fe340b11fe`, 6,664 lines, 185 headings, 37 tables, 65 code blocks, integrity PASS (0 hard issues).
- Coverage ledger: 124/124 original sections READ (`AUDIT_WORK/ledger.csv`); per-lens matrix fill = Phase 5 task.

## 3. Defect Register summary (`AUDIT_WORK/defects.csv`)
- 150 findings: **P0 5, P1 70, P2 74** + 1 withdrawn (D-001 = audit-tool false positive, documented).
- Status at checkpoint: 149 marked FIXED in PRD_UPDATED (mechanically linked via `patches.log` batch IDs — **Phase 5 re-audit must confirm each**), 1 WONT-FIX (D-001), 0 OPEN.
- P0 list: D-002 overstated "sandbox-verified" claims · D-006 zero-server vs edge-tts contradiction · D-063 Gojo/third-party character IP · D-126 silent sine-beep voice fallback · D-131 verdict stars literal `\\n` join (stars rendered as garbage).

## 4. OSS (Appendix P) — 32 components, 13 skills
Replaced: `rhasspy/piper` → kokoro-onnx + Kokoro-82M / espeak-ng · `fengsp/color-thief-py` → `python-pillow/Pillow` · `tkarabela/pysubs2` → `libass/libass` · `itsPremkumar/Automated-Video-Generator` → `FFmpeg/FFmpeg` · `RayVentura/ShortGPT` dropped. New skills: OSS-SKL-11 (voice mastering), -12 (ops layer), -13 (test/eval/CI). Reference-only (independent signal not verifiable without github.com): MoneyPrinterTurbo, Open-LLM-VTuber, rhubarb-lip-sync, AI-Youtube-Shorts-Generator, ffmpeg-normalize.

## 5. Voice module (Appendix O) — MEASURED
Kokoro-82M (Hindi) RTF 0.35, peak RSS ≈690 MB. Prompt hypothesis chain **rejected** (sibilance +2.6–3.0 dB). Accepted `RVS-VOICE-MASTER-v1`: −14.0 LUFS ±0.2, TP ≤ −1.5 dBTP, 0 clipping, sibilance −0.3…−2.7 dB, warmth +0.7…+0.9 dB. loudnorm native output 192 kHz (v5.0 said 96 kHz). **Awaaz khud sunkar check karo — 6-point checklist App O.6 (NEEDS-HUMAN).**

## 6. Enterprise layer
Secrets (App H, `.env.example` parity: code-read vars == file), telemetry + crash reports (App I), 66 error codes (18 ERR / 48 WARN) with registry + schema, EC-01..EC-54 all mapped (App J), time budgets B1 MEASURED/B2 ESTIMATE (App K), cost table reproducible (App L), 12 eval suites / 37 cases (App M), 38 TCs + traceability 0 orphans (App N), 8 Mermaid diagrams — **mermaid-cli 11.4.2: 8/8 rendered** (App Q).

## 7. Verification evidence (this session)
pytest 24/24 · evals 37/37 (broken-expectation self-test exits 1) · cost --check match · shellcheck clean · schemas valid · smoke E2E + derived reel E2E QA hard pass · integrity PASS · banned names outside changelog: 0.

## 8. Needs human verification / NOT-RUN
Voice listening (O.6) · legal: character IP, edge-tts ToS, IT Rules 2026 creator duties, CCPA penalties · edge-tts / ElevenLabs / Termux / 4K-8K / GitHub Actions runs (NOT-RUN) · GitHub "Used by" for reference-only repos · UNVERIFIED-OFFLINE v5.0 sources listed in App D.

## 9. Remaining work (Phase 5–6) — see RESUME PACK
Re-audit round(s) A–D on PRD_UPDATED (incl. fresh-context cold-read subagent), fill ledger lens matrix, run ids/xref/scaffold/mermaid/error_codes/budgets/secrets scripts as standalone tools, diff_report, final report + stamp decision.

AUDIT INCOMPLETE: 0 OPEN (re-audit Phase 5 pending — defects marked FIXED are not yet independently re-verified)
