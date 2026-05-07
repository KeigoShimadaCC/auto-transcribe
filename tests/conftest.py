from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest

from auto_transcribe.config import Settings

PROJECT_ROOT = Path(__file__).resolve().parents[1]
EXAMPLE_DATA = PROJECT_ROOT / "ExampleData"


def _ffmpeg_available() -> bool:
    return shutil.which("ffmpeg") is not None


@pytest.fixture(scope="session")
def fixtures_dir(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """Generate a tiny synthetic WAV via ffmpeg so unit tests never depend on
    network downloads or large files."""
    if not _ffmpeg_available():
        pytest.skip("ffmpeg not available")
    d = tmp_path_factory.mktemp("fixtures")
    wav = d / "tone.wav"
    cmd = [
        "ffmpeg",
        "-y",
        "-loglevel",
        "error",
        "-f",
        "lavfi",
        "-i",
        "sine=frequency=440:duration=2",
        "-ac",
        "1",
        "-ar",
        "16000",
        str(wav),
    ]
    subprocess.run(cmd, check=True)
    return d


@pytest.fixture
def isolated_settings(tmp_path: Path) -> Settings:
    s = Settings(
        input_dir=str(tmp_path / "input"),
        output_dir=str(tmp_path / "output"),
        state_dir=str(tmp_path / ".state"),
        model="mlx-community/whisper-tiny",
        language="auto",
    )
    Path(s.input_dir).mkdir(parents=True, exist_ok=True)
    Path(s.output_dir).mkdir(parents=True, exist_ok=True)
    Path(s.state_dir).mkdir(parents=True, exist_ok=True)
    return s


@pytest.fixture
def example_data_dir() -> Path:
    if not EXAMPLE_DATA.exists():
        pytest.skip("ExampleData/ not present")
    return EXAMPLE_DATA
