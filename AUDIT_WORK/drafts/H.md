## Appendix H — Secrets Management Strategy (v5.1, OWNER-10 / addition A)

### H.1 Secrets & Credentials Inventory
| Secret / Config | Env variable | Required? | Read by (script) | Loaded where | Minimum scope | Rotation note |
|---|---|---|---|---|---|---|
| ElevenLabs API key (Premium Voice Path) | `ELEVENLABS_API_KEY` | Optional — only when `RVS_PREMIUM_TTS=on` | `voice_engines.ElevenLabsPremium`, `preflight.check_secrets` (status only) | OS env → `.env` (`rvs_common.load_env_file`) | Text-to-speech only; set a monthly character quota in the ElevenLabs dashboard | Rotate every 90 days (TARGET) and immediately on suspected leak (H.4) |
| Premium toggle | `RVS_PREMIUM_TTS` | Optional (default `off`) | `voice_engines`, `preflight` | OS env → `.env` | — | — |
| ElevenLabs voice / model id | `RVS_ELEVENLABS_VOICE_ID`, `RVS_ELEVENLABS_MODEL` | Optional | `voice_engines` | OS env → `.env` | not secret | — |
| Research AI / Gemini / Claude accounts | — (never stored by the skill) | — | none — the Operator uses them in their own browser apps | — | — | — |

No other secret exists: `edge-tts` needs no key, Kokoro/espeak-ng are local, the Claude chat runs under the Operator's own plan. **No key ever enters a prompt, a chat message, `spec.json`, `words.json`, logs, crash reports, run reports, generated files or this PRD's examples.**

### H.2 Rules (enforced by code in `rvs_common.py`, G.9)
1. **Load order:** OS environment variable first, then `SKILL_ROOT/.env`; `.env` never overrides an existing OS variable. Loader = `theskumar/python-dotenv` (BSD-3-Clause, optional, `CN-021`) else the built-in `KEY=VALUE` parser (Termux-safe).
2. **Never** hardcode keys, pass them on a command line (process lists show argv), print them, or place them in prompts sent to any LLM.
3. **Redaction filter:** every console line, JSONL record and crash report goes through `redact()` — masks the literal value of every variable in `SECRET_ENV_VARS` and known key shapes (`sk_…`, `sk-…`, `xi-api-key: …`, `api_key=…`). Test `TC-34`.
4. **Preflight** prints only `present` / `missing` / `malformed` per secret (`secret_status`), and warns when a key exists but the toggle is off (`RVS_WARN_046`), the toggle is on without a key (`RVS_WARN_047`), or the key looks malformed (`RVS_WARN_048`).
5. **Files:** `.env` and `*.key`/`*.pem` are in `.gitignore` (File 37); `.env` must be mode `600` (`chmod 600 .env`; Termux has the same POSIX `chmod`) — wider permissions → `RVS_WARN_043`.
6. Premium API rejection (401/403) → `RVS_WARN_042`, quota/429 → `RVS_WARN_044`, timeout/5xx → `RVS_WARN_045`; the run always continues on the offline-first default chain.

### H.3 `.env.example` (File 36 — generated from the code's env reads; exact copy ships next to the PRD)
```text
# review-video-studio — environment variables (App H). Copy to .env, then: chmod 600 .env
# Load order: OS environment first, then .env (never overrides). Values are never logged.

# [optional] Premium Voice Path toggle (default off). Premium is used ONLY if this is "on" AND ELEVENLABS_API_KEY is set.
RVS_PREMIUM_TTS=off
# [optional, secret] ElevenLabs API key — required only when RVS_PREMIUM_TTS=on. Placeholder only:
ELEVENLABS_API_KEY=
# [optional] ElevenLabs voice id (from the Get voices endpoint) — required only when RVS_PREMIUM_TTS=on
RVS_ELEVENLABS_VOICE_ID=
# [optional] ElevenLabs model id (default eleven_multilingual_v2)
RVS_ELEVENLABS_MODEL=eleven_multilingual_v2
# [optional] Kokoro model + voices file paths (default assets/models/kokoro-v1.0.onnx, assets/models/voices-v1.0.bin)
RVS_KOKORO_MODEL=
RVS_KOKORO_VOICES=
# [optional] Kokoro voice when the spec voice_id is an edge voice (default hm_omega)
RVS_KOKORO_VOICE=hm_omega
# [optional] Voice mastering chain: v1 (default) | safe | off
RVS_VOICE_MASTER=v1
# [optional] TTS concurrency (default 2)
RVS_TTS_CONCURRENCY=2
# [optional] Multiply all hard timeouts (default 1; use 3 on slow phones)
RVS_TIMEOUT_SCALE=1
# [optional] Log directory (default ./logs), max bytes per run log (default 5242880), run id override, debug
RVS_LOG_DIR=logs
RVS_LOG_MAX_BYTES=5242880
RVS_RUN_ID=
RVS_DEBUG=
# [optional] Operator-supplied USD→INR rate for cost reports (no default: never invented)
RVS_USD_INR=
```
*(The scaffold check verifies that this file lists exactly the variables read by the G.1–G.10 code + render kit + CI — no more, no less; `PREFIX` (Termux system variable) and `RVS_WORK`/`RVS_OUT` (render-kit shell paths) and `RVS_OFFLINE_TESTS`/`RVS_EVAL_MODEL` (CI-only) are documented in Appendix N instead.)*

### H.4 Key Rotation & Leak Response Runbook
1. **Revoke** the key in the ElevenLabs dashboard immediately; set `RVS_PREMIUM_TTS=off`.
2. **Replace:** create a new key with a character quota, put it only in `.env` (mode 600) or the OS env.
3. **Scan:** `grep -rn "sk_" logs/ work/ .` and `git log -p | grep -n "sk_"`; if found in git history, treat the repo as leaked (rewrite history + force-rotate). Crash reports are redacted, but re-check the latest `logs/crash_report_*.json`.
4. **Record** the incident date in `build_report.md` (no key value).
