import os
import shutil
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
os.environ.setdefault("RVS_LOG_DIR", os.path.join(ROOT, "logs", "pytest"))


def pytest_configure(config):
    for m in ("slow: long-running render tests", "needs_ffmpeg: requires ffmpeg/ffprobe", "needs_network: calls external services",
              "needs_secret: needs ELEVENLABS_API_KEY (manual job only)"):
        config.addinivalue_line("markers", m)


def pytest_collection_modifyitems(config, items):
    has_ff = shutil.which("ffmpeg") and shutil.which("ffprobe")
    for it in items:
        if "needs_ffmpeg" in it.keywords and not has_ff:
            it.add_marker(pytest.mark.skip(reason="ffmpeg/ffprobe not installed"))
        if "needs_secret" in it.keywords and not os.environ.get("ELEVENLABS_API_KEY"):
            it.add_marker(pytest.mark.skip(reason="no secret in this job"))
        if "needs_network" in it.keywords and os.environ.get("RVS_OFFLINE_TESTS", "1") == "1":
            it.add_marker(pytest.mark.skip(reason="offline CI"))
