## Appendix K — Execution Time Budgets / SLAs (v5.1, addition D)

### K.1 Baselines
- **B1 — Cloud VM (RP-1/RP-2 render side):** reference = the v5.1 audit VM: 4 vCPU x86-64, 15 GiB RAM, FFmpeg 6.1.1, Python 3.13 (the PRD had no VM spec; defined here — DEC-12).
- **B2 — Android Termux (RP-2 voice / RP-3 render):** reference device class = Android 12+, 8-core ARM64 mid-range SoC, 8 GB RAM, Termux from F-Droid (defined here; no device was available in the audit → all B2 numbers are ESTIMATE until `--bench` is run).
- Labels: **MEASURED** = timed in the audit (2 Nov 2026, 15 s smoke sample, 6 chunks); **ESTIMATE** = linear extrapolation from MEASURED per-second rates (method shown); **TARGET** = design goal. Hard timeouts are enforced in code by `rvs_common.run_cmd(timeout_s=…)` with `build_video.tmo(base, seconds, tier) = (base + factor × output_seconds) × RVS_TIMEOUT_SCALE` (factor 6 / 10 / 25 / 90 s per output second for 1080p / 1440p / 4K / 8K); render kit sets `RVS_TIMEOUT_SCALE=3` on Termux.

### K.2 Budget table
| Stage | Tier / length | Baseline | Soft budget (warn `RVS_WARN_071`) | Hard timeout (`RVS_ERR_070`) | Label & method |
|---|---|---|---|---|---|
| `S7-L` preflight | any | B1 | 5 s | 30 s per probe | MEASURED 0.6 s |
| `S7-L` preflight | any | B2 | 15 s | 90 s | ESTIMATE (B1 × 3, TARGET) |
| `S7-L` voice — `kokoro-onnx` | Long 10 min (600 s audio) | B1 | 300 s | 900 s | ESTIMATE: RTF 0.35 MEASURED × 600 s = 210 s + 3 s load |
| `S7-L` voice — `kokoro-onnx` | Long 10 min | B2 | 1800 s | 3600 s | ESTIMATE (ARM RTF assumed 1.5–3.0; `--bench` required) |
| `S7-L` voice — `edge-tts` | Long 10 min (~300 chunks) | B1/B2 | 300 s | 60 s per chunk attempt × 3 | ESTIMATE (network-bound; NOT-RUN in audit — confidentiality rule) |
| `S7-L` voice — any | Short 60 s / derived 2 chunks | B1 | 30 s | 180 s | MEASURED smoke 7.2 s for 15 s audio (Kokoro, incl. load) |
| `S8-L` host timeline | Long 10 min | B1 | 120 s | 600 s | ESTIMATE: MEASURED 8.0 s for 15 s incl. one-time 96-sprite build (≈6 s) → ≈0.13 s per audio second |
| `S8-L` render 1080p_fhd | Long 10 min | B1 | 2400 s | per scene `30 + 6 × scene_s`; final `60 + 6 × 600 = 3660` s | ESTIMATE: MEASURED 48.3 s for 15 s (≈3.2 s per output second) × 600 s ≈ 1930 s |
| `S8-L` render 1080p_fhd | Long 10 min | B2 | 7200 s | ×3 scale | ESTIMATE (B1 × 3–4; RP-2 recommended, `RVS_WARN_072`) |
| `S8-L` render 1080p_fhd | Derived 60 s | B1 | 240 s | `60 + 6 × 60 = 420` s | ESTIMATE: MEASURED 55.6 s for a 15.3 s derived reel |
| `S8-L` render 4k_uhd | Long 10 min | B1 | 9000 s | `60 + 25 × 600 = 15060` s | ESTIMATE (upscale + x265; TARGET; `--bench` required) |
| `S8-L` render 8k_uhd | Long 10 min | B1 only (≥16 GiB) | 36000 s | `60 + 90 × 600 = 54060` s | ESTIMATE/TARGET (not allowed on B2) |
| `S9-L` QA | Long 10 min | B1 | 180 s | `60 + 4 × 600` s per filter pass | ESTIMATE: MEASURED 3.6 s for 15 s × 40 |
| `S10-L` covers | any | B1 | 5 s | 60 s | MEASURED 0.6 s |
| `S11–S12` repurpose (spec + slices + 2 TTS chunks) | per clip | B1 | 30 s | 180 s | ESTIMATE from MEASURED fresh-TTS 2 chunks ≈ 3 s |

### K.3 Disk & RAM minimums (TARGET; enforced by `check_disk_space` / tier gate)
`1080p_fhd` 2 GiB free disk, 2 GiB RAM · `1440p_qhd` 4 GiB / 4 GiB · `4k_uhd` 8 GiB / 8 GiB · `8k_uhd` 20 GiB / 16 GiB.

### K.4 `--bench` procedure (produces the real numbers for any device)
1. `bash scripts/render_kit/run_full_render.sh assets/fonts/sample_spec_smoke.json` (Termux) or the same 5 CLIs on the VM.
2. Read stage durations: `grep '"event": "stage_end"' logs/run_*.jsonl` (`duration_ms` per stage) and the `run_summary` line.
3. Per-second rate = `duration_ms / 1000 / 15` (smoke audio ≈ 15 s); multiply by the target length; update K.2 rows to **MEASURED** with device + date.
