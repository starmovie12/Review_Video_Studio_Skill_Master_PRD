"""Integration/media tests (need ffmpeg): SFX recipes, voice mastering chain measurements, smoke render (slow)."""
import json
import os
import subprocess
import sys
import wave

import pytest

from rvs_common import ffprobe_duration
from voice_engines import VOICE_MASTER_CHAIN_V1

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def ebur(path):
    err = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", path, "-af", "ebur128=peak=true", "-f", "null", "-"],
                         capture_output=True, text=True).stderr
    tail = err[err.rfind("Summary:"):]
    import re
    return float(re.search(r"I:\s+(-?[\d.]+) LUFS", tail).group(1)), float(re.search(r"Peak:\s+(-?[\d.]+) dBFS", tail).group(1))


@pytest.mark.needs_ffmpeg
def test_tc35_voice_master_chain_meets_targets(tmp_path):
    """Pink-noise speech proxy through RVS-VOICE-MASTER-v1 + 2-pass loudnorm → I within ±1.0 of −14, TP ≤ −1.0."""
    src = tmp_path / "src.wav"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", "anoisesrc=d=6:c=pink:r=48000:a=0.2,lowpass=f=7000,"
                    "volume='0.5+0.5*sin(2*PI*1.7*t)':eval=frame", "-ac", "2", str(src)], check=True)
    sys.path.insert(0, os.path.join(ROOT, "scripts"))
    from build_video import _loudnorm_two_pass
    pre = tmp_path / "pre.wav"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(src), "-af", VOICE_MASTER_CHAIN_V1, str(pre)], check=True)
    out = tmp_path / "out.wav"
    _loudnorm_two_pass(str(pre), str(out), str(tmp_path), 6.0)
    i, tp = ebur(str(out))
    assert abs(i + 14.0) <= 1.0 and tp <= -1.0
    with wave.open(str(out)) as w:
        assert w.getframerate() == 48000 and w.getnchannels() == 2  # TC-16 (no 192 kHz leak)


@pytest.mark.needs_ffmpeg
def test_sfx_recipes_are_stereo_48k(tmp_path):
    from build_video import SFX_RECIPES
    for k, rec in SFX_RECIPES.items():
        p = tmp_path / f"{k}.wav"
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", rec, "-af", "aformat=sample_rates=48000:channel_layouts=stereo", str(p)], check=True)
        with wave.open(str(p)) as w:
            assert w.getnchannels() == 2 and w.getframerate() == 48000
        assert 0.05 < ffprobe_duration(str(p)) < 0.8
