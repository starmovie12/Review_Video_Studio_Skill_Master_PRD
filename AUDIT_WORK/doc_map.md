# Document map of PRD.md (3753 lines)

## Headings (outside fences)

| # | line | end | lvl | heading |
|---|---|---|---|---|
| 1 | 1 | 79 | H1 | Review Video Studio Skill — Master PRD v5.0 (Open-Source-First Audited + Full HD / 4K / 8K UHD Cinema-Grade + Long-First + Gojo Co-Host Edition) |
| 2 | 80 | 114 | H2 | 0. Pehle Ye Padho (2 Minute Executive Summary) |
| 3 | 115 | 128 | H2 | 1. Tumne Kya Bataya → PRD v5.0 Mapping & 25 Next-Level Engineering Upgrades |
| 4 | 129 | 155 | H3 | 25 Next-Level Engineering Upgrades Built into PRD v5.0 |
| 5 | 156 | 173 | H3 | 1.2 Unified Master ID & Term Glossary (Fixes Audit E-04) |
| 6 | 174 | 175 | H2 | 2. Problem, Solution & 10 Core Principles (Skill ka Samvidhan) |
| 7 | 176 | 179 | H3 | 2.1 Problem Statement |
| 8 | 180 | 184 | H3 | 2.2 Solution Architecture |
| 9 | 185 | 196 | H3 | 2.3 Skill ke 10 Core Principles (Samvidhan) |
| 10 | 197 | 206 | H2 | 3. Roles & Strict Boundaries — Kaun Kya Karega |
| 11 | 207 | 208 | H2 | 4. Scope, 5 Content Categories, Modes & Opinion Source Rules |
| 12 | 209 | 215 | H3 | 4.1 Five Content Categories (`CAT-*`) |
| 13 | 216 | 219 | H3 | 4.2 Operating Modes (`MODE-REVIEW` vs `MODE-PROMO`) |
| 14 | 220 | 226 | H3 | 4.3 Opinion Source Rules (`OS-A`, `OS-B`, `OS-C`) |
| 15 | 227 | 228 | H2 | 5. End-to-End Stage Flow (`S0`–`S13` Long-First + Derived Shorts), Runtime Matrix & Beat Maps |
| 16 | 229 | 248 | H3 | 5.1 Master Long-First Pipeline (`S0`–`S13`) |
| 17 | 249 | 271 | H3 | 5.2.1 AI Runtime Decision Matrix (AI Khud Tay Karegi Kitne Minute Ki Long Video Banegi — Fixes Audit A-04) |
| 18 | 272 | 273 | H3 | 5.2 Detailed Stage Rules & Formulas |
| 19 | 274 | 279 | H4 | `S0` (Rapid Intake) & `S1` (Topic Lock / Trend Radar) |
| 20 | 280 | 290 | H4 | `S2` (Mission Pack — 3 Copy-Paste Deliverables in 1 Message) |
| 21 | 291 | 305 | H4 | `S3` (Data Intake, Quantitative QC & Context-Safe Digest Engine) |
| 22 | 306 | 321 | H4 | `S4` (Insight Brief & Master Fact Sheet) + `S5` (Chunked Beat Script) + `S6` (Asset Checklist) |
| 23 | 322 | 332 | H3 | 5.3 Second-by-Second Beat Maps & Word Budgets |
| 24 | 333 | 349 | H3 | 5.4 Repurpose Engine (`S11`–`S13`): Long Master Video Se Instagram Reel Aur YouTube Short Kaise Banta Hai (`scripts/repurpose_shorts.py` — Fixes Audit A-03) |
| 25 | 350 | 351 | H2 | 6. Quality Bar: 100-Pt Scorecard, Hook Taxonomy, Guards & 12-Pt Video QA |
| 26 | 352 | 353 | H3 | 6.1 Dual 100-Point Script Scorecards (Pass Floor: `≥ 80 / 100` — Fixes Audit C-01 & C-03) |
| 27 | 354 | 361 | H4 | 6.1A Long-Form Master (`16:9`, `5–15 Min`) 100-Point Scorecard |
| 28 | 362 | 370 | H4 | 6.1B Derived Reel / Short (`9:16`, `30–60s` / `≤180s`) 100-Point Scorecard |
| 29 | 371 | 377 | H3 | 6.2 Five Rotating Hook Archetypes (`HK-*`) |
| 30 | 378 | 382 | H3 | 6.3 Originality Guard (`scripts/similarity_check.py` — Powered by `rapidfuzz/RapidFuzz` Technique `OSS-SKL-08`) |
| 31 | 383 | 404 | H3 | 6.4 16-Point Automated & Visual Video QA (Including 8K/4K UHD Super-Resolution, Gojo Co-Host & Cinema Color Realism QA — `scripts/qa_contact_sheet.py`) |
| 32 | 405 | 406 | H2 | 7. Video Engine v5.0: Preflight, Phonetic TTS (`rany2/edge-tts` + `thewh1teagle/kokoro-onnx`), Pillow-Cached Fast FFmpeg (`harry0703/MoneyPrinterTurbo`), ASS Ve |
| 33 | 407 | 423 | H3 | 7.1 Preflight Diagnostic, Schema Validator & 4 Render Paths (`scripts/preflight.py` — Powered by `python-jsonschema/jsonschema` & `itsPremkumar/Automated-Video- |
| 34 | 424 | 446 | H3 | 7.2 Voice Engine, Hinglish Phonetic Normalizer, Rate-Limit Guard & Variable Pause Matrix (`scripts/voice_pack.py` — Powered by `rany2/edge-tts`, `thewh1teagle/k |
| 35 | 447 | 464 | H3 | 7.3 Canvas-Aware (`16:9` + `9:16`) Fast Pillow-Cached Pipeline, Sidechain BGM Ducking & Resumable Render (`scripts/build_video.py` — Powered by `harry0703/Money |
| 36 | 465 | 481 | H3 | 7.4 ASS Vector Stars (`\an7` Locked) & Dual-Font Caption Architecture (`captions.ass` — Powered by `tkarabela/pysubs2` & `harry0703/MoneyPrinterTurbo` Skill `OS |
| 37 | 482 | 494 | H3 | 7.5 Five Cinema-Grade Colourful Visual Style Packs & Realistic Graphics Engine (`references/style-packs.md`) |
| 38 | 495 | 499 | H4 | 7.5.1 Pillar 1 — Dynamic Poster-Dominant Ambilight Color-Bleeding (`extract_dominant_palette` — Powered by `fengsp/color-thief-py` Skill `OSS-SKL-04`) |
| 39 | 500 | 505 | H4 | 7.5.2 Pillar 2 — True Frosted Glassmorphism UI Cards, 3D Drop Shadows & Glowing Meter Bars (`render_data_card`) |
| 40 | 506 | 511 | H4 | 7.5.3 Pillar 3 — Studio Key-Art Composite & Volumetric Lighting for Gojo (`character_overlay.py`) |
| 41 | 512 | 521 | H4 | 7.5.4 Pillar 4 — FFmpeg 4-Stage Cinema Color-Grading & 4K Crispness Filter (`CINEMA_GRADE_FILTER`) |
| 42 | 522 | 557 | H4 | 7.5.5 Pillar 5 — True `8K UHD (7680×4320)` / `4K UHD (3840×2160)` / `Full HD (1920×1080)` Super-Resolution, Anti-Jitter & 10-Bit Anti-Banding Engine |
| 43 | 558 | 564 | H3 | 7.6 Procedural FFmpeg Sound Effects (`whoosh`, `pop`, `riser`, `stamp`) & Stereo WAV Bed Mixer |
| 44 | 565 | 568 | H3 | 7.7 Dual Grid-Safe Cover (`3:4` `1080×1440` + `4:5` `1080×1350`) & 16:9 Thumbnail (`scripts/make_cover.py` — Powered by `fengsp/color-thief-py` & Pillow `ImageO |
| 45 | 569 | 572 | H3 | 7.8 Aspect-Aware `max(16, chapters×2)` Contact Sheet & Automated 16-Point Stream/Pixel QA (`scripts/qa_contact_sheet.py` — Powered by `itsPremkumar/Automated-Vi |
| 46 | 573 | 576 | H3 | 7.9 Cross-Script Phonetic Originality Guard & Prompt-Injection Sanitizer (`scripts/similarity_check.py` — Powered by `rapidfuzz/RapidFuzz` Skill `OSS-SKL-08`) |
| 47 | 577 | 627 | H3 | 7.10 Proven-Code & Live Reverse-Engineering Policy — Code Scratch Se Nahi, Proven Repos Se (AI Directive) |
| 48 | 628 | 632 | H3 | 7.11 Gojo Recurring Anime Review Co-Host & Hybrid 2D Character Rig + FFmpeg Engine (`scripts/character_overlay.py` — Powered by `Open-LLM-VTuber/Open-LLM-VTuber |
| 49 | 633 | 644 | H4 | 7.11.1 Gojo Ke 6 Signature Trigger Moments (`gojo_cue` in `spec.json`) |
| 50 | 645 | 657 | H4 | 7.11.2 Hybrid 2D Character Rig + FFmpeg Implementation Matrix |
| 51 | 658 | 659 | H2 | 8. Safety, Copyright Fair Dealing, India IT Rules 2026, CCPA/ASCI & Platform Policies |
| 52 | 660 | 667 | H3 | 8.1 Copyright & Fair Dealing Engineering Rules (India Copyright Act §52(1)(a)) |
| 53 | 668 | 673 | H3 | 8.2 India MeitY IT Amendment Rules (Feb 2026) & CCPA Endorsement Rules |
| 54 | 674 | 687 | H3 | 8.3 Instagram Reels & YouTube Shorts Platform Rules (Nov 2026 Baseline) |
| 55 | 688 | 691 | H3 | 8.4 People, Fairness & Honest Engagement (Carried Forward from PRD v1.1) |
| 56 | 692 | 693 | H2 | 9. Operator UX, Non-Clashing Command Vocabulary & Turn Protocol |
| 57 | 694 | 704 | H3 | 9.1 Dedicated Command Words (No Clash with `continue` or `state.json`) |
| 58 | 705 | 730 | H3 | 9.2 Standard 5-Block Turn Format |
| 59 | 731 | 775 | H2 | 10. Comprehensive Edge Cases & Fail-Soft Matrix (40 Scenarios) |
| 60 | 776 | 802 | H2 | 11. Metrics, Golden Runs & 22 Acceptance Test Cases (`TC-01` to `TC-22`) |
| 61 | 803 | 815 | H2 | 12. Priorities (`P0`/`P1`/`P2`) & 5-Stage Build Roadmap (`M0`–`M4` / `STAGE-0`–`STAGE-4` — All 31 Files) |
| 62 | 816 | 831 | H2 | 13. Technical Risk Register & Verified Mitigations |
| 63 | 832 | 833 | H2 | 14. Locked Decisions (`D1`–`D16`), Termux PEP-668 Setup & Closed Architecture Decisions (`Q1`–`Q7`) |
| 64 | 834 | 853 | H3 | 14.1 Locked Default Decisions (`D1`–`D16` — Upgraded for Long-First + Anime Host) |
| 65 | 854 | 868 | H3 | 14.2 One-Time Termux Setup (PEP-668 & `raqm` Safe — For `RP-2` & `RP-3` on Android Phone) |
| 66 | 869 | 881 | H3 | 14.3 Closed Architecture & Product Decisions (`Q1`–`Q7` Resolved with Rationale — Zero Open Questions) |
| 67 | 882 | 883 | H2 | Appendix A — Skill Folder Capture (31 Files + 2 Companions), Inventory, Full `SKILL.md` & Full `PRIMER.md` |
| 68 | 884 | 927 | H3 | A.1 Complete Skill Directory Tree (`review-video-studio/`) |
| 69 | 928 | 963 | H3 | A.2 Master 31-File Inventory Table |
| 70 | 964 | 966 | H3 | A.2.1 Quick Lookup: Kis Stage Par Kaunsi Reference File Padhni Hai |
| 71 | 967 | 969 | H3 | A.2.2 Quick Lookup: `TPL-01`..`06` Templates Kis Reference File Mein Rakhi Jayengi |
| 72 | 970 | 1003 | H3 | A.3 Complete Production Draft of `SKILL.md` (File 01 of 31 — Upgraded for v5.0 Open-Source-First + 8K UHD + Long-First + Gojo Co-Host) |
| 73 | 1004 | 1032 | H3 | A.4 Complete Standalone `PRIMER.md` (Companion File 1 — Paste in Any AI Chat Without Installing ZIP) |
| 74 | 1033 | 1036 | H2 | Appendix B — Complete Pre-Written Next-Level Prompt Library (`PR-01` to `PR-10`) |
| 75 | 1037 | 1117 | H3 | `PR-01` — Next-Level Entertainment Deep Research Prompt (`CAT-ENT`: Movie / Web Series / TV Show) |
| 76 | 1118 | 1143 | H3 | `PR-02` — Next-Level Software / App / AI Tool Deep Research Prompt (`CAT-SOFT`) |
| 77 | 1144 | 1163 | H3 | `PR-03` — Next-Level Physical Product / Gadget Deep Research Prompt (`CAT-PROD`) |
| 78 | 1164 | 1183 | H3 | `PR-04` — Promotional / Brand Video Research & Compliance Prompt (`MODE-PROMO`) |
| 79 | 1184 | 1232 | H3 | `PR-05` — Gemini Verbatim Audio + Visual Blueprint Prompt (`S2-C` Master Single-Video Prompt) |
| 80 | 1233 | 1241 | H3 | `PR-06` — Truncated Transcript Continuation Prompt |
| 81 | 1242 | 1254 | H3 | `PR-07` — Tier-2 Fallback Prompt (YouTube Raw Transcript + Gemini Visual-Only Pass) |
| 82 | 1255 | 1264 | H3 | `PR-08` — Offline YouTube Benchmark Search Recipe & `OS-A` Operator Interview |
| 83 | 1265 | 1284 | H3 | `PR-09` — Next-Level Video Game / Mobile Game Deep Research Prompt (`CAT-GAME` — Added in v3.0) |
| 84 | 1285 | 1302 | H3 | `PR-10` — Batch Short-Video Blueprint Prompt & External AI Fact-Audit Prompt (Added in v3.0) |
| 85 | 1303 | 1304 | H2 | Appendix C — Operational Templates (`TPL-01` to `TPL-06`) & Strict JSON Schemas v5.0 |
| 86 | 1305 | 1311 | H3 | C.1–C.6 Operational Templates Summary |
| 87 | 1312 | 1399 | H3 | C.1–C.6 Fillable Template Bodies (Copy-Paste Ready — Builder `STAGE-1` Isi Text Ko `references/*.md` Files Mein Save Karegi) |
| 88 | 1400 | 1624 | H3 | C.7 Upgraded JSON Schema 1: `schemas/spec.schema.json` (v4.0 — Supports Long-First `16:9`, `chapters`, `repurpose`, `character` Anime Host & `bgm`) |
| 89 | 1625 | 1668 | H3 | C.8 Upgraded JSON Schema 2: `schemas/words.schema.json` |
| 90 | 1669 | 1770 | H3 | C.9 Validated Sample Blueprint: `assets/fonts/sample_spec_smoke.json` (16:9 Long Master + Anime Reviewer Host + Repurpose Moments) |
| 91 | 1771 | 1830 | H2 | Appendix D — Verified Policy & Technical Sources Baseline (November 2026) |
| 92 | 1831 | 1834 | H2 | Appendix E — 5-Stage Chat-Safe Skill Build Prompts (`STAGE-0` to `STAGE-4` — Synchronized to All 31 Files) |
| 93 | 1835 | 1854 | H3 | `STAGE-0` Build Prompt (Open-Source Verification & Skill Catalog — Files 02, 11, 12, 31 — MANDATORY FIRST STEP) |
| 94 | 1855 | 1869 | H3 | `STAGE-0B` Fallback Prompt (Repo-File Paste — Jab AI GitHub Khol Na Paye) |
| 95 | 1870 | 1882 | H3 | `STAGE-1` Build Prompt (Core Brain, Schemas & Playbooks — Files 01, 03, 05, 06, 13, 14, 15) |
| 96 | 1883 | 1894 | H3 | `STAGE-2` Build Prompt (Video Engine Scripts, Gojo Rig, Dual Fonts & Live 8K/FHD Smoke Test — Files 16, 17, 18, 20, 22, 27, 28, 29, 30) |
| 97 | 1895 | 1904 | H3 | `STAGE-3` Build Prompt (Covers, RapidFuzz Plagiarism Guard, Repurpose Engine, Termux Kit & Playbooks — Files 04, 07, 08, 09, 10, 19, 21, 23, 24, 25, 26) |
| 98 | 1905 | 1912 | H3 | `STAGE-4` Build Prompt (Companion Docs, Full 31-File Audit & Final ZIP Package) |
| 99 | 1913 | 1971 | H2 | Appendix F — Master Line-by-Line Audit Changelog: All 54 Audit Entries Fixed (v1.0 → v2.0 → v3.0 → v4.0 → v5.0 Open-Source-First + 8K UHD) |
| 100 | 1972 | 1973 | H2 | Appendix F2 — Open-Source-First Coverage Matrix & 10 Reverse-Engineered OSS Skills (`§7.10 Protocol` — Verified 2 Nov 2026) |
| 101 | 1974 | 1978 | H3 | F2.1 Status & Decision Legend (`oss_first_policy`) |
| 102 | 1979 | 1995 | H3 | F2.2 Master 12-Component Open-Source Coverage Matrix (All Code Components in PRD) |
| 103 | 1996 | 2005 | H3 | F2.3 Audit Log of Replaced & Dropped Repositories (`OWNER-06` Compliance) |
| 104 | 2006 | 2021 | H3 | F2.4 Technique Card Template (`references/reference-repos.md`) |
| 105 | 2022 | 2025 | H3 | F2.5 Complete Specifications of All 10 Reverse-Engineered Open-Source Skills (`OSS-SKL-01` to `OSS-SKL-10` — Saved as File 31 `references/oss-skills-catalog.md` |
| 106 | 2026 | 2045 | H4 | 1. `OSS-SKL-01` — Chunk-Level Neural TTS, `WordBoundary` Sync & Offline ONNX Voice Skill |
| 107 | 2046 | 2062 | H4 | 2. `OSS-SKL-02` — Multi-Aspect (`16:9` & `9:16`) HD/4K/8K Video Pipeline & FFmpeg Filtergraph Skill |
| 108 | 2063 | 2076 | H4 | 3. `OSS-SKL-03` — SubStation Alpha (`.ass`) Dual-Font Caption & `n7` Vector Star Skill |
| 109 | 2077 | 2088 | H4 | 4. `OSS-SKL-04` — Dominant HSV Palette Quantization, Ambilight Backdrop & Grid-Safe Cover Skill |
| 110 | 2089 | 2100 | H4 | 5. `OSS-SKL-05` — Two-Pass EBU R128 Linear `loudnorm`, Sidechain BGM Ducking & 48kHz Stereo Skill |
| 111 | 2101 | 2114 | H4 | 6. `OSS-SKL-06` — Event-Driven 2D Anime Co-Host (`CHAR-GOJO-HOST`) Viseme Lip-Sync & State-Machine Skill |
| 112 | 2115 | 2127 | H4 | 7. `OSS-SKL-07` — Virality-Scored Moment Mining (`S11`), Audio Chunk Slicer (`S12`) & `9:16` Repurpose Skill |
| 113 | 2128 | 2138 | H4 | 8. `OSS-SKL-08` — Cross-Script Phonetic `≥7-Gram` & `RapidFuzz` Token-Set Originality Guard Skill |
| 114 | 2139 | 2150 | H4 | 9. `OSS-SKL-09` — JSON Schema Draft 2020-12 Validator, Preflight Probe & 16-Point Contact-Sheet QA Skill |
| 115 | 2151 | 2162 | H4 | 10. `OSS-SKL-10` — Declarative Motion Token & MoviePy v2 Fallback Compositor Skill |
| 116 | 2163 | 2166 | H2 | Appendix G — Sandbox-Verified Reference Python Implementations (All 8 Core Engine Scripts: `G.1` to `G.8`) |
| 117 | 2167 | 2258 | H3 | G.1 `scripts/preflight.py` — Cross-Platform `SKILL_ROOT` + Termux Font Resolver, Environment Probe & Smoke Test |
| 118 | 2259 | 2441 | H3 | G.2 `scripts/voice_pack.py` — Phonetic Normalizer, Rate-Limit Guard, Double-Reverse Silence Trim & Stereo WAV Assembler |
| 119 | 2442 | 3050 | H3 | G.3 `scripts/build_video.py` — Dynamic Poster-Ambilight Extractor, Frosted Glassmorphism Cards, `32px` 3D Drop Shadows, `\an7` ASS Vector Stars & FFmpeg Cinema  |
| 120 | 3051 | 3101 | H3 | G.4 `scripts/make_cover.py` — Dual Grid-Safe (`3:4` `1080×1440` + `4:5` `1080×1350`) Cover & `16:9` Thumbnail Generator |
| 121 | 3102 | 3174 | H3 | G.5 `scripts/qa_contact_sheet.py` — Chapter-Aware `max(16, chapters×2)` Contact Sheet & 16-Point Stream, UHD Super-Resolution & Color Vibrance QA |
| 122 | 3175 | 3253 | H3 | G.6 `scripts/similarity_check.py` — Balanced Nested-Bracket Stripper, Prompt-Injection Sanitizer & Cross-Script Phonetic 7-Gram Guard |
| 123 | 3254 | 3642 | H3 | G.7 `scripts/character_overlay.py` — Studio Key-Art Composite & Volumetric Bloom Gojo Co-Host Engine (`Six Eyes`, `Blue`, `Red`, `Hollow Purple`, `Infinity` & E |
| 124 | 3643 | 3753 | H3 | G.8 `scripts/repurpose_shorts.py` — `S11–S13` Moment Miner, Master Audio Chunk Slicer (`15ms` Anti-Click Fade) & `16:9`→`9:16` Derived Reel/Short Builder |

## ID families (whole file incl. code)

| family | distinct | occurrences | sample |
|---|---|---|---|
| S-stage | 19 | 286 | S0, S1, S10, S11, S12, S13, S2, S2-A, S2-B, S2-C, S3, S4, S5, S6, S7, S7-A, S7-B, S8, S9 |
| TC | 22 | 52 | TC-01, TC-02, TC-03, TC-04, TC-05, TC-06, TC-07, TC-08, TC-09, TC-10, TC-11, TC-12, TC-13, TC-14, TC-15, TC-16, TC-17, TC-18, TC-19, TC-20, TC-21, TC-22 |
| PR | 14 | 128 | PR-01, PR-02, PR-03, PR-04, PR-05, PR-06, PR-07, PR-08, PR-08A, PR-08B, PR-09, PR-10, PR-10A, PR-10B |
| TPL | 6 | 45 | TPL-01, TPL-02, TPL-03, TPL-04, TPL-05, TPL-06 |
| D-locked | 16 | 32 | D1, D10, D11, D12, D13, D14, D15, D16, D2, D3, D4, D5, D6, D7, D8, D9 |
| Q | 7 | 17 | Q1, Q2, Q3, Q4, Q5, Q6, Q7 |
| R-risk | 11 | 42 | R1, R10, R11, R2, R3, R4, R5, R6, R7, R8, R9 |
| RP | 4 | 46 | RP-1, RP-2, RP-3, RP-4 |
| OSS-SKL | 10 | 105 | OSS-SKL-01, OSS-SKL-02, OSS-SKL-03, OSS-SKL-04, OSS-SKL-05, OSS-SKL-06, OSS-SKL-07, OSS-SKL-08, OSS-SKL-09, OSS-SKL-10 |
| DEF | 9 | 16 | DEF-01, DEF-02, DEF-03, DEF-04, DEF-05, DEF-06, DEF-07, DEF-16, DEF-20 |
| CAT | 5 | 54 | CAT-ENT, CAT-GAME, CAT-PROD, CAT-PROMO, CAT-SOFT |
| MODE | 2 | 25 | MODE-PROMO, MODE-REVIEW |
| OS | 3 | 60 | OS-A, OS-B, OS-C |
| HK | 5 | 27 | HK-MYTH, HK-SCENE, HK-SPLIT, HK-STAT, HK-TEST |
| STL | 5 | 44 | STL-CINEMA, STL-CLEAN, STL-DARK, STL-NEON, STL-ROAST |
| CHK | 12 | 43 | CHK-01, CHK-02, CHK-03, CHK-04, CHK-05, CHK-08, CHK-10, CHK-12, CHK-15, CHK-19, CHK-21, CHK-23 |
| CH | 8 | 31 | CH-01, CH-02, CH-03, CH-04, CH-05, CH-06, CH-07, CH-08 |
| AST | 4 | 24 | AST-B1, AST-P1, AST-S1, AST-V1 |
| M-roadmap | 5 | 14 | M0, M1, M2, M3, M4 |
| STAGE | 6 | 91 | STAGE-0, STAGE-0B, STAGE-1, STAGE-2, STAGE-3, STAGE-4 |
| EC-edge | 0 | 0 |  |
| E-audit | 31 | 58 | A-01, A-02, A-03, A-04, A-05, B-01, B-02, B-03, B-04, B-05, B-06, C-01, C-02, C-03, C-04, C-05, C-06, C-07, C-08, C-09, C-10, C-11, C-12, D-01, D-02 |
| CN | 0 | 0 |  |
| RVS-ERR | 0 | 0 |  |
| Flaw# | 29 | 94 | #1, #10, #11, #12, #13, #14, #15, #16, #2, #29, #3, #30, #31, #32, #33, #34, #35, #36, #38, #39, #4, #46, #47, #48, #5 |

## Tables

| # | start | end | header cols | rows | col-mismatch rows |
|---|---|---|---|---|---|
| 1 | 117 | 127 | 3 | 9 | - |
| 2 | 158 | 172 | 4 | 13 | - |
| 3 | 199 | 205 | 4 | 5 | - |
| 4 | 221 | 225 | 4 | 3 | - |
| 5 | 252 | 260 | 4 | 7 | - |
| 6 | 324 | 331 | 5 | 6 | - |
| 7 | 417 | 422 | 5 | 4 | - |
| 8 | 487 | 493 | 7 | 5 | - |
| 9 | 527 | 532 | 7 | 4 | - |
| 10 | 590 | 598 | 3 | 7 | - |
| 11 | 602 | 607 | 3 | 4 | - |
| 12 | 635 | 643 | 5 | 7 | - |
| 13 | 647 | 656 | 2 | 8 | - |
| 14 | 733 | 774 | 4 | 40 | - |
| 15 | 778 | 801 | 4 | 22 | - |
| 16 | 818 | 830 | 4 | 11 | - |
| 17 | 872 | 880 | 4 | 7 | - |
| 18 | 930 | 962 | 7 | 31 | - |
| 19 | 1915 | 1970 | 5 | 54 | [1961] |
| 20 | 1981 | 1994 | 10 | 12 | - |
| 21 | 1998 | 2004 | 4 | 5 | - |

## Code blocks

| # | start | end | lang | lines |
|---|---|---|---|---|
| 1 | 230 | 241 | text | 10 |
| 2 | 468 | 480 | text | 11 |
| 3 | 514 | 519 | text | 4 |
| 4 | 714 | 729 | text | 14 |
| 5 | 856 | 867 | bash | 10 |
| 6 | 885 | 924 | text | 38 |
| 7 | 971 | 1002 | markdown | 30 |
| 8 | 1007 | 1030 | markdown | 22 |
| 9 | 1038 | 1116 | text | 77 |
| 10 | 1119 | 1142 | text | 22 |
| 11 | 1145 | 1162 | text | 16 |
| 12 | 1165 | 1182 | text | 16 |
| 13 | 1187 | 1231 | text | 43 |
| 14 | 1234 | 1240 | text | 5 |
| 15 | 1243 | 1253 | text | 9 |
| 16 | 1266 | 1283 | text | 16 |
| 17 | 1287 | 1294 | text | 6 |
| 18 | 1296 | 1301 | text | 4 |
| 19 | 1315 | 1328 | text | 12 |
| 20 | 1331 | 1348 | text | 16 |
| 21 | 1351 | 1357 | text | 5 |
| 22 | 1360 | 1376 | text | 15 |
| 23 | 1379 | 1387 | text | 7 |
| 24 | 1390 | 1398 | text | 7 |
| 25 | 1401 | 1623 | json | 221 |
| 26 | 1626 | 1667 | json | 40 |
| 27 | 1670 | 1769 | json | 98 |
| 28 | 1836 | 1853 | text | 16 |
| 29 | 1858 | 1868 | text | 9 |
| 30 | 1871 | 1881 | text | 9 |
| 31 | 1884 | 1893 | text | 8 |
| 32 | 1896 | 1903 | text | 6 |
| 33 | 1906 | 1911 | text | 4 |
| 34 | 2007 | 2020 | text | 12 |
| 35 | 2168 | 2257 | python | 88 |
| 36 | 2260 | 2440 | python | 179 |
| 37 | 2443 | 3049 | python | 605 |
| 38 | 3052 | 3100 | python | 47 |
| 39 | 3103 | 3173 | python | 69 |
| 40 | 3176 | 3252 | python | 75 |
| 41 | 3255 | 3641 | python | 385 |
| 42 | 3644 | 3753 | python | 108 |
