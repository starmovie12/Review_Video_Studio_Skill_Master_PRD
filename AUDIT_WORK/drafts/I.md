## Appendix I — Structured Telemetry, Run Report & Crash Reports (v5.1, addition B)

### I.1 Console format (human-readable, stderr)
`[LEVEL] [script] STAGE message (ERROR_CODE)` — e.g. `[INFO] [build_video] S8-L render 1920x1080@30 tier=1080p_fhd`, `[WARN] [voice_pack] S7-L edge-tts failed (...); poori run kokoro-onnx par switch (RVS_WARN_041)`.

### I.2 Machine log — `logs/run_<RUN_ID>.jsonl` (one JSON object per line)
| Field | Type | Meaning |
|---|---|---|
| `ts` | string | UTC ISO-8601 with milliseconds |
| `level` | `DEBUG`/`INFO`/`WARN`/`ERROR` | severity |
| `run_id` | string | `YYYYMMDDTHHMMSSZ-<6 hex>` (or `RVS_RUN_ID`) shared by all scripts of one run |
| `script` | string | script stem (`voice_pack`, `build_video`, …) |
| `stage` | string | PRD stage ID (`S7-L`, `S8-L`, `S9-L`, `S10-L`, `S11`, …) |
| `event` | string | `stage_start`, `stage_end`, `subprocess_ok`, `subprocess_failed`, `warning`, `fatal`, `run_summary`, … |
| `error_code` | string/null | registry code (Appendix J) |
| `duration_ms` | int/null | for stage_end / subprocess events |
| `message` | string | redacted text |
| `context` | object | redacted extra data (e.g. `stderr_tail`) |
Size cap: `RVS_LOG_MAX_BYTES` (default `5 MiB`, TARGET for phones) per run file — further lines are dropped (console continues). Rotation: one file per run; the Operator deletes `logs/` older than 30 days (`find logs -mtime +30 -delete`).

### I.3 Crash report — `logs/crash_report_<RUN_ID>.json`
Written by `main_wrapper` on every fatal error: `error_code`, `stage`, `script`, `run_id`, `tool_versions` (python, OS, ffmpeg, `script_version` 5.1.0), `command_line` (redacted), `last_log_lines` (≤30), `input_hashes` (sha256 prefix of input files), full `traceback` (file only; printed to console only with `--debug` or `RVS_DEBUG=1`), `resume_hint`. Test `TC-32`.

### I.4 Run summary & build report
Every script ends with `run_summary` (stage durations vs Appendix K budgets, warning codes, error codes). The Skill copies the summary + `qa_report.json` + engine provenance (`words.json.engine`) into `build_report.md` (deliverable 12).
