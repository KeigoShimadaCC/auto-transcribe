"""Integration-test fixtures.

Integration tests in this folder exercise multiple modules together using the
real ffmpeg binary plus a fake (in-memory) transcription engine. They are
strictly faster than the e2e suite (which downloads the real ML model) but
broader in scope than the unit tests in `tests/`.
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest


def _ffmpeg_available() -> bool:
    return shutil.which("ffmpeg") is not None


@pytest.fixture(scope="session")
def integration_fixtures(tmp_path_factory: pytest.TempPathFactory) -> Path:
    if not _ffmpeg_available():
        pytest.skip("ffmpeg not available")
    d = tmp_path_factory.mktemp("integration_fixtures")

    short_wav = d / "short.wav"
    subprocess.run(
        [
            "ffmpeg", "-y", "-loglevel", "error",
            "-f", "lavfi", "-i", "sine=frequency=440:duration=1",
            "-ac", "1", "-ar", "16000", str(short_wav),
        ],
        check=True,
    )

    long_wav = d / "long.wav"
    subprocess.run(
        [
            "ffmpeg", "-y", "-loglevel", "error",
            "-f", "lavfi", "-i", "sine=frequency=220:duration=3",
            "-ac", "2", "-ar", "44100", str(long_wav),
        ],
        check=True,
    )

    fake_video = d / "fake.mp4"
    subprocess.run(
        [
            "ffmpeg", "-y", "-loglevel", "error",
            "-f", "lavfi", "-i", "color=size=64x64:rate=10:duration=1",
            "-f", "lavfi", "-i", "sine=frequency=880:duration=1",
            "-c:v", "libx264", "-pix_fmt", "yuv420p",
            "-c:a", "aac", "-shortest", str(fake_video),
        ],
        check=True,
    )

    return d
