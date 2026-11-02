"""voice_engines.py — single TTS engine adapter + studio voice mastering chain (File 33, PRD v5.1 App G.10, OSS-SKL-01/11).

Contract (every engine): synth(text, lang, voice_id, rate, out_path) -> dict(wav=out_path, engine=..., engine_version=...).
Output of every engine is normalised by voice_pack.trim_chunk_silence_48k_stereo() to 48 kHz stereo PCM.
Engine order (DEC-03): [premium (only if RVS_PREMIUM_TTS=on AND key present)] → edge-tts (online) → kokoro-onnx (Primary HQ LOCAL)
→ espeak-ng (floor). The phonetic normalizer runs BEFORE every engine (voice_pack.normalize_tts_say).
Engine switching happens per RUN, never per chunk (voice consistency). No sine/beep fallback exists.
"""
from __future__ import annotations

import asyncio
import json
import os
import random
import shutil
import subprocess
import urllib.error
import urllib.request
from pathlib import Path

from rvs_common import RvsError, SKILL_ROOT, log_event, warn

# --- RVS-VOICE-MASTER-v1 (MEASURED 2 Nov 2026, App O.2): applied to the voice stem before the final two-pass loudnorm ---
VOICE_MASTER_CHAIN_V1 = ",".join([
    "highpass=f=70:poles=2",                                   # rumble/DC removal below speech fundamentals
    "lowshelf=f=160:g=3",                                      # +3 dB warmth (podcast-mic body)
    "equalizer=f=3000:t=q:w=1.0:g=1.0",                         # +1 dB presence/intelligibility
    "highshelf=f=6000:g=-4",                                   # −4 dB above 6 kHz: tames TTS sibilance/harshness
    "deesser=i=0.6:m=0.5:f=0.5:s=o",                            # dynamic de-esser safety net
    "acompressor=threshold=-20dB:ratio=2:attack=10:release=150:makeup=1:knee=4",  # gentle 2:1 levelling across chunks
    "alimiter=limit=0.89:attack=5:release=50:level=disabled",   # −1.0 dBFS sample ceiling before loudnorm
])
# Safe fallback (filters present in every FFmpeg ≥4.4 build incl. Debian 12's 5.1 and Termux): no deesser/alimiter
VOICE_MASTER_CHAIN_SAFE = "highpass=f=70,lowshelf=f=160:g=3,highshelf=f=6000:g=-4,acompressor=threshold=-20dB:ratio=2:attack=10:release=150"


def voice_master_chain() -> str | None:
    """RVS_VOICE_MASTER=v1 (default) | safe | off → returns the filter string or None (bypass)."""
    mode = os.environ.get("RVS_VOICE_MASTER", "v1").lower()
    return {"v1": VOICE_MASTER_CHAIN_V1, "safe": VOICE_MASTER_CHAIN_SAFE, "off": None}.get(mode, VOICE_MASTER_CHAIN_V1)


class EngineFailed(Exception):
    def __init__(self, code: str, detail: str):
        self.code, self.detail = code, detail
        super().__init__(f"{code}: {detail}")


# ---------------- engines ----------------
class EdgeTTS:
    name = "edge-tts"

    def available(self) -> bool:
        try:
            import edge_tts  # noqa: F401
            return True
        except ImportError:
            return False

    def version(self) -> str:
        try:
            import importlib.metadata as md
            return md.version("edge-tts")
        except Exception:
            return "unknown"

    async def synth(self, text: str, lang: str, voice_id: str, rate: str, pitch: str, out_path: str, sem: asyncio.Semaphore) -> dict:
        import edge_tts
        mp3 = out_path + ".mp3"
        last = ""
        async with sem:
            for attempt in range(3):  # 3 attempts, jittered exponential backoff 1.5 → 3.0 s (no sleep after last)
                try:
                    comm = edge_tts.Communicate(text=text, voice=voice_id, rate=rate, pitch=pitch, boundary="WordBoundary")
                    await asyncio.wait_for(comm.save(mp3), timeout=30)
                    if os.path.exists(mp3) and os.path.getsize(mp3) > 256:
                        return {"wav": mp3, "engine": self.name, "engine_version": self.version()}
                    last = "empty audio"
                except Exception as e:  # NoAudioReceived, WSServerHandshakeError (403/429), timeouts, DNS
                    last = f"{type(e).__name__}: {e}"[:200]
                if attempt < 2:
                    await asyncio.sleep(1.5 * (2 ** attempt) * (0.8 + 0.4 * random.random()))
        raise EngineFailed("RVS_WARN_041", last)


class KokoroONNX:
    """Primary HQ LOCAL engine: thewh1teagle/kokoro-onnx + hexgrad/Kokoro-82M (Apache-2.0 weights). Hindi voices hf_alpha,
    hf_beta, hm_omega, hm_psi (upstream grade C — NEEDS-HUMAN listening). Model files via RVS_KOKORO_MODEL / RVS_KOKORO_VOICES."""
    name = "kokoro-onnx"
    _k = None

    def _paths(self):
        d = SKILL_ROOT / "assets" / "models"
        return (os.environ.get("RVS_KOKORO_MODEL", str(d / "kokoro-v1.0.onnx")),
                os.environ.get("RVS_KOKORO_VOICES", str(d / "voices-v1.0.bin")))

    def available(self) -> bool:
        try:
            import kokoro_onnx  # noqa: F401
        except ImportError:
            return False
        m, v = self._paths()
        return os.path.exists(m) and os.path.exists(v)

    def version(self) -> str:
        try:
            import importlib.metadata as md
            return md.version("kokoro-onnx")
        except Exception:
            return "unknown"

    async def synth(self, text, lang, voice_id, rate, pitch, out_path, sem):
        import soundfile as sf
        from kokoro_onnx import Kokoro
        if KokoroONNX._k is None:
            KokoroONNX._k = Kokoro(*self._paths())
        voice = voice_id if voice_id.startswith(("hf_", "hm_", "af_", "am_", "bf_", "bm_")) else os.environ.get("RVS_KOKORO_VOICE", "hm_omega")
        speed = 1.0 + (int(rate.strip("%")) / 100.0 if rate and rate.strip("%").lstrip("+-").isdigit() else 0.0)
        try:
            samples, sr = await asyncio.to_thread(KokoroONNX._k.create, text, voice=voice, speed=max(0.5, min(2.0, speed)), lang="hi")
        except Exception as e:
            raise EngineFailed("RVS_ERR_040", f"kokoro: {type(e).__name__}: {e}"[:200]) from e
        wav = out_path + ".kokoro.wav"
        sf.write(wav, samples, sr)
        return {"wav": wav, "engine": self.name, "engine_version": self.version(), "voice": voice}


class EspeakNG:
    name = "espeak-ng"

    def available(self) -> bool:
        return shutil.which("espeak-ng") is not None or shutil.which("espeak") is not None

    def version(self) -> str:
        return "system"

    async def synth(self, text, lang, voice_id, rate, pitch, out_path, sem):
        exe = shutil.which("espeak-ng") or shutil.which("espeak")
        wav = out_path + ".espeak.wav"
        cp = await asyncio.to_thread(subprocess.run, [exe, "-v", "hi", "-s", "165", "-w", wav, "--stdin"],
                                     input=text, capture_output=True, text=True, timeout=60)
        if cp.returncode != 0 or not os.path.exists(wav):
            raise EngineFailed("RVS_ERR_040", f"espeak rc={cp.returncode}")
        return {"wav": wav, "engine": self.name, "engine_version": self.version()}


class ElevenLabsPremium:
    """Optional Premium Voice Path (DEC-02). Default OFF. Active only if RVS_PREMIUM_TTS=on AND ELEVENLABS_API_KEY present.
    API: POST https://api.elevenlabs.io/v1/text-to-speech/{voice_id}?output_format=pcm_24000 (header xi-api-key).
    Privacy: only the normalised `say` text of each chunk leaves the machine (App O.4)."""
    name = "elevenlabs"

    def available(self) -> bool:
        return os.environ.get("RVS_PREMIUM_TTS", "off").lower() == "on" and bool(os.environ.get("ELEVENLABS_API_KEY"))

    def version(self) -> str:
        return os.environ.get("RVS_ELEVENLABS_MODEL", "eleven_multilingual_v2")

    async def synth(self, text, lang, voice_id, rate, pitch, out_path, sem):
        voice = os.environ.get("RVS_ELEVENLABS_VOICE_ID", "")
        if not voice:
            raise EngineFailed("RVS_WARN_047", "RVS_ELEVENLABS_VOICE_ID missing")
        url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice}?output_format=pcm_24000"
        body = json.dumps({"text": text, "model_id": self.version()}).encode("utf-8")
        req = urllib.request.Request(url, data=body, method="POST", headers={
            "xi-api-key": os.environ["ELEVENLABS_API_KEY"], "Content-Type": "application/json", "Accept": "audio/pcm"})
        try:
            pcm = await asyncio.to_thread(lambda: urllib.request.urlopen(req, timeout=60).read())
        except urllib.error.HTTPError as e:
            code = "RVS_WARN_042" if e.code in (401, 403) else ("RVS_WARN_044" if e.code == 429 else "RVS_WARN_045")
            raise EngineFailed(code, f"HTTP {e.code}") from e
        except Exception as e:  # timeout / network
            raise EngineFailed("RVS_WARN_045", type(e).__name__) from e
        raw = out_path + ".el.pcm"
        Path(raw).write_bytes(pcm)
        wav = out_path + ".el.wav"
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "s16le", "-ar", "24000", "-ac", "1", "-i", raw, wav], check=True, timeout=60)
        return {"wav": wav, "engine": self.name, "engine_version": self.version()}


ENGINES = {"elevenlabs": ElevenLabsPremium, "edge-tts": EdgeTTS, "kokoro-onnx": KokoroONNX, "espeak-ng": EspeakNG}


def engine_chain(preferred: str) -> list:
    """Premium first only when explicitly toggled; then preferred engine; then the fixed fallback order."""
    order = []
    if ElevenLabsPremium().available():
        order.append("elevenlabs")
    for name in [preferred, "edge-tts", "kokoro-onnx", "espeak-ng"]:
        if name in ENGINES and name not in order:
            order.append(name)
    chain = [ENGINES[n]() for n in order]
    usable = [e for e in chain if e.available()]
    log_event("INFO", "S7-L", "engine_chain", None, " → ".join(e.name for e in usable) or "(none)")
    if not usable:
        raise RvsError("RVS_ERR_040", "no TTS engine available (edge-tts not installed/blocked, kokoro model missing, espeak-ng absent)")
    return usable


def report_engine_switch(failed: str, code: str, detail: str, nxt: str) -> None:
    warn(code, "S7-L", f"{failed} failed ({detail}); poori run {nxt} par switch")
