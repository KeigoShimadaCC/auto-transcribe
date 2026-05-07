from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from auto_transcribe import cli, pipeline
from auto_transcribe.engines.base import Segment, TranscriptionResult


class _FakeEngine:
    name = "fake"

    def __init__(self, model: str) -> None:
        self.model = model

    def transcribe(self, wav_path, language=None, on_progress=None):
        return TranscriptionResult(
            text="cli-hello",
            segments=[Segment(0.0, 0.5, "cli-hello")],
        )


@pytest.fixture(autouse=True)
def patch_engine(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(pipeline, "build_engine", _FakeEngine)


def test_cli_once_processes_pending(
    tmp_path: Path, fixtures_dir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    settings_file = tmp_path / "settings.json"
    monkeypatch.setenv("AUTO_TRANSCRIBE_SETTINGS", str(settings_file))
    in_dir = tmp_path / "input"
    out_dir = tmp_path / "output"
    in_dir.mkdir()
    out_dir.mkdir()
    shutil.copy2(fixtures_dir / "tone.wav", in_dir / "tone.wav")

    rc = cli.main(
        [
            "--once",
            "--input",
            str(in_dir),
            "--output",
            str(out_dir),
            "--model",
            "mlx-community/whisper-tiny",
        ]
    )
    assert rc == 0
    assert (out_dir / "tone.txt").read_text().strip() == "cli-hello"
