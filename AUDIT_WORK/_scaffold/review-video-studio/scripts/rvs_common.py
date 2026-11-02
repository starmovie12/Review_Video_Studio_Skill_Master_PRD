"""rvs_common.py — shared runtime helpers for every review-video-studio script (File 32, PRD v5.1 App G.9).

Single place for: structured telemetry (console + JSON Lines), crash reports, the error-code registry,
standard exit codes, secrets loading + redaction, budget-aware subprocess calls and atomic writes.
Python stdlib only (python-dotenv is optional). Technique: CPython `logging` (stdlib) — OSS-SKL-12.
"""
from __future__ import annotations

import datetime as _dt
import hashlib
import json
import logging
import os
import platform
import re
import shutil
import subprocess
import sys
import time
import traceback
import uuid
from collections import deque
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parent.parent
REGISTRY_PATH = SKILL_ROOT / "schemas" / "error_codes.json"
SCRIPT_VERSION = "5.1.0"

# Exit codes (App J.3): 0 ok, 10 ok-with-warnings, 20 input/spec error, 30 environment/dependency error,
# 40 external service error, 50 render/encode error, 60 QA gate failed, 70 timeout/budget exceeded, 99 unexpected crash
EXIT = {"OK": 0, "WARN": 10, "INPUT": 20, "ENV": 30, "SERVICE": 40, "RENDER": 50, "QA": 60, "TIMEOUT": 70, "CRASH": 99}

SECRET_ENV_VARS = ("ELEVENLABS_API_KEY",)
_SECRET_PATTERNS = [re.compile(p) for p in (
    r"sk_[A-Za-z0-9]{20,}",            # ElevenLabs-style keys
    r"sk-[A-Za-z0-9_-]{20,}",          # generic sk- keys (OpenAI/Anthropic style)
    r"xi-api-key\s*[:=]\s*\S+",        # header form
    r"(?i)(api[_-]?key|token|secret)\s*[=:]\s*['\"]?[A-Za-z0-9_\-]{16,}",
)]


class RvsError(Exception):
    """Raised with a registry code; carries the resume hint and exit-code class."""

    def __init__(self, code: str, detail: str = "", **ctx):
        self.code = code
        self.detail = detail
        self.ctx = ctx
        info = load_registry().get(code, {})
        self.exit_class = info.get("exit", "CRASH")
        self.user_message = info.get("message_hinglish", code)
        self.resume_hint = info.get("resume_hint", "")
        super().__init__(f"{code}: {detail}")


_REGISTRY: dict | None = None


def load_registry() -> dict:
    """Loads schemas/error_codes.json once; returns {code: entry}. Missing registry → empty dict (never crash)."""
    global _REGISTRY
    if _REGISTRY is None:
        try:
            data = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
            _REGISTRY = {e["code"]: e for e in data["codes"]}
        except (OSError, ValueError, KeyError):
            _REGISTRY = {}
    return _REGISTRY


# ---------------- secrets (App H) ----------------
def load_env_file(path: str | os.PathLike | None = None) -> None:
    """Load order: OS environment first, then .env (never overrides an existing OS variable).
    Uses python-dotenv when installed, else a minimal KEY=VALUE parser. The values are never logged."""
    p = Path(path) if path else SKILL_ROOT / ".env"
    if not p.exists():
        return
    try:
        if os.name == "posix" and (p.stat().st_mode & 0o077):
            log_event("WARN", "secrets", "env_permissions", "RVS_WARN_043", ".env readable by group/others; run chmod 600 .env")
    except OSError:
        pass
    try:
        from dotenv import load_dotenv  # optional dependency (theskumar/python-dotenv)
        load_dotenv(p, override=False)
        return
    except ImportError:
        pass
    for raw in p.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        k, v = k.strip(), v.strip().strip('"').strip("'")
        if k and k not in os.environ:
            os.environ[k] = v


def secret_status(name: str) -> str:
    """Returns only 'present' / 'missing' / 'malformed' — never the value."""
    v = os.environ.get(name, "")
    if not v:
        return "missing"
    if name == "ELEVENLABS_API_KEY" and (len(v) < 20 or " " in v):
        return "malformed"
    return "present"


def redact(text: str) -> str:
    """Masks known key shapes and the literal value of every loaded secret variable."""
    out = str(text)
    for name in SECRET_ENV_VARS:
        val = os.environ.get(name)
        if val and len(val) >= 6:
            out = out.replace(val, f"<{name}:redacted>")
    for pat in _SECRET_PATTERNS:
        out = pat.sub("<redacted>", out)
    return out


# ---------------- telemetry (App I) ----------------
RUN_ID = os.environ.get("RVS_RUN_ID") or _dt.datetime.now(_dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "-" + uuid.uuid4().hex[:6]
_SCRIPT = Path(sys.argv[0]).stem or "rvs"
_LOG_DIR = Path(os.environ.get("RVS_LOG_DIR", "logs"))
_TAIL: deque[str] = deque(maxlen=50)
_STAGE_T0: dict[str, float] = {}
_SUMMARY = {"warnings": [], "errors": [], "stage_ms": {}}
LOG_MAX_BYTES = int(os.environ.get("RVS_LOG_MAX_BYTES", str(5 * 1024 * 1024)))  # TARGET 5 MB cap per run file
_console = logging.getLogger("rvs")
if not _console.handlers:
    h = logging.StreamHandler(sys.stderr)
    h.setFormatter(logging.Formatter("%(message)s"))
    _console.addHandler(h)
    _console.setLevel(logging.DEBUG if os.environ.get("RVS_DEBUG") else logging.INFO)


def _jsonl_path() -> Path:
    _LOG_DIR.mkdir(parents=True, exist_ok=True)
    return _LOG_DIR / f"run_{RUN_ID}.jsonl"


def log_event(level: str, stage: str, event: str, error_code: str | None = None, message: str = "",
              duration_ms: int | None = None, **ctx) -> None:
    """Console: '[LEVEL] [script] STAGE message'. File: one JSON object per line (UTC ISO-8601)."""
    msg = redact(message)
    line = f"[{level}] [{_SCRIPT}] {stage} {msg}" + (f" ({error_code})" if error_code else "")
    _TAIL.append(line)
    {"DEBUG": _console.debug, "INFO": _console.info, "WARN": _console.warning, "ERROR": _console.error}.get(level, _console.info)(line)
    rec = {"ts": _dt.datetime.now(_dt.timezone.utc).isoformat(timespec="milliseconds"), "level": level, "run_id": RUN_ID,
           "script": _SCRIPT, "stage": stage, "event": event, "error_code": error_code, "duration_ms": duration_ms,
           "message": msg, "context": json.loads(redact(json.dumps(ctx, default=str, ensure_ascii=False)))}
    if level == "WARN" and error_code:
        _SUMMARY["warnings"].append(error_code)
    if level == "ERROR" and error_code:
        _SUMMARY["errors"].append(error_code)
    try:
        p = _jsonl_path()
        if not p.exists() or p.stat().st_size < LOG_MAX_BYTES:
            with p.open("a", encoding="utf-8") as f:
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    except OSError:
        pass  # logging must never crash the pipeline


def warn(code: str, stage: str, message: str = "", **ctx) -> None:
    log_event("WARN", stage, "warning", code, message or load_registry().get(code, {}).get("message_hinglish", ""), **ctx)


def stage_start(stage: str, message: str = "") -> None:
    _STAGE_T0[stage] = time.monotonic()
    log_event("INFO", stage, "stage_start", None, message)


def stage_end(stage: str, message: str = "") -> int:
    ms = int((time.monotonic() - _STAGE_T0.pop(stage, time.monotonic())) * 1000)
    _SUMMARY["stage_ms"][stage] = ms
    log_event("INFO", stage, "stage_end", None, message, duration_ms=ms)
    return ms


def tool_versions() -> dict:
    v = {"python": platform.python_version(), "os": platform.platform(), "script_version": SCRIPT_VERSION}
    ff = shutil.which("ffmpeg")
    if ff:
        try:
            v["ffmpeg"] = subprocess.run([ff, "-version"], capture_output=True, text=True, timeout=10).stdout.split("\n")[0]
        except (OSError, subprocess.SubprocessError):
            v["ffmpeg"] = "unavailable"
    return v


def file_sha256(path: str | os.PathLike, limit_mb: int = 64) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        h.update(f.read(limit_mb * 1024 * 1024))
    return h.hexdigest()[:16]


def write_crash_report(exc: BaseException, stage: str, inputs: list[str] | None = None) -> str:
    code = getattr(exc, "code", "RVS_ERR_099")
    rep = {"error_code": code, "stage": stage, "script": _SCRIPT, "run_id": RUN_ID, "tool_versions": tool_versions(),
           "command_line": redact(" ".join(sys.argv)), "last_log_lines": list(_TAIL)[-30:],
           "input_hashes": {p: file_sha256(p) for p in (inputs or []) if p and os.path.isfile(p)},
           "traceback": redact("".join(traceback.format_exception(type(exc), exc, exc.__traceback__))),
           "resume_hint": getattr(exc, "resume_hint", "") or "Same command dobara chalao; completed chunks/scenes cache se skip honge."}
    _LOG_DIR.mkdir(parents=True, exist_ok=True)
    path = _LOG_DIR / f"crash_report_{RUN_ID}.json"
    path.write_text(json.dumps(rep, ensure_ascii=False, indent=2), encoding="utf-8")
    return str(path)


def run_summary(budgets: dict[str, float] | None = None) -> dict:
    s = dict(_SUMMARY)
    if budgets:
        s["over_budget"] = {k: v for k, v in s["stage_ms"].items() if k in budgets and v > budgets[k] * 1000}
    log_event("INFO", "SUMMARY", "run_summary", None, json.dumps(s, ensure_ascii=False))
    return s


def main_wrapper(fn, stage: str):
    """Top-level handler: no raw traceback on console unless --debug/RVS_DEBUG; maps errors to exit codes."""
    debug = "--debug" in sys.argv or bool(os.environ.get("RVS_DEBUG"))
    try:
        load_env_file()
        rc = fn()
        if rc is None:
            rc = EXIT["WARN"] if _SUMMARY["warnings"] else EXIT["OK"]
        run_summary()
        return rc
    except RvsError as e:
        log_event("ERROR", stage, "fatal", e.code, f"{e.user_message} | {e.detail}")
        path = write_crash_report(e, stage)
        _console.error(f"[ERROR] crash_report: {path} | resume: {e.resume_hint}")
        if debug:
            traceback.print_exc()
        return EXIT.get(e.exit_class, EXIT["CRASH"])
    except KeyboardInterrupt:
        log_event("ERROR", stage, "interrupted", "RVS_ERR_098", "Operator ne run roka (Ctrl+C)")
        return EXIT["CRASH"]
    except Exception as e:  # unexpected
        e.code = "RVS_ERR_099"  # type: ignore[attr-defined]
        log_event("ERROR", stage, "crash", "RVS_ERR_099", f"{type(e).__name__}: {e}")
        path = write_crash_report(e, stage)
        _console.error(f"[ERROR] Unexpected crash — crash_report: {path}")
        if debug:
            traceback.print_exc()
        return EXIT["CRASH"]


# ---------------- subprocess + files ----------------
def run_cmd(cmd: list[str], stage: str, timeout_s: float, error_code: str = "RVS_ERR_050", cwd: str | None = None,
            capture: bool = False) -> subprocess.CompletedProcess:
    """Runs an external tool with a hard timeout (App K budgets). stderr tail goes to the log, never secrets."""
    t0 = time.monotonic()
    try:
        cp = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=timeout_s)
    except FileNotFoundError as e:
        raise RvsError("RVS_ERR_030", f"binary missing: {cmd[0]}") from e
    except subprocess.TimeoutExpired as e:
        raise RvsError("RVS_ERR_070", f"{Path(cmd[0]).name} exceeded hard timeout {timeout_s:.0f}s", stage=stage) from e
    ms = int((time.monotonic() - t0) * 1000)
    if cp.returncode != 0:
        tail = redact((cp.stderr or "")[-1200:])
        log_event("ERROR", stage, "subprocess_failed", error_code, f"{Path(cmd[0]).name} rc={cp.returncode}", ms, stderr_tail=tail)
        raise RvsError(error_code, f"{Path(cmd[0]).name} rc={cp.returncode}: {tail[-300:]}")
    log_event("DEBUG", stage, "subprocess_ok", None, Path(cmd[0]).name, ms)
    return cp


def atomic_replace(tmp_path: str, final_path: str) -> None:
    os.replace(tmp_path, final_path)


def ffprobe_duration(path: str, timeout_s: float = 30) -> float:
    cp = run_cmd(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=nw=1:nk=1", path],
                 "PROBE", timeout_s, "RVS_ERR_051")
    try:
        return float(cp.stdout.strip())
    except ValueError as e:
        raise RvsError("RVS_ERR_051", f"unreadable duration for {path}") from e


def check_disk_space(path: str, need_mb: int) -> None:
    free_mb = shutil.disk_usage(path).free // (1024 * 1024)
    if free_mb < need_mb:
        raise RvsError("RVS_ERR_032", f"free {free_mb} MB < required {need_mb} MB at {path}")
