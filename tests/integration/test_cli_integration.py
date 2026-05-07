"""CLI integration: invoke the public entry point end-to-end."""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from auto_transcribe import cli, pipeline
from auto_transcribe.engines.base import Segment, TranscriptionResult

pytestmark = pytest.mark.integration


class _Engine:
    name = "fake"

    def __init__(self, model: str) -> None:
        self.model = model

    def transcribe(self, wav_path, language=None, on_progress=None):
        return TranscriptionResult(
            text="cli integration",
            segments=[Segment(0.0, 0.5, "cli integration")],
        )


@pytest.fixture(autouse=True)
def patch_engine(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(pipeline, "build_engine", _Engine)


def test_cli_once_writes_outputs_for_two_files(
    tmp_path: Path,
    integration_fixtures: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setenv("AUTO_TRANSCRIBE_SETTINGS", str(tmp_path / "s.json"))
    in_dir = tmp_path / "input"
    out_dir = tmp_path / "output"
    in_dir.mkdir()
    out_dir.mkdir()
    shutil.copy2(integration_fixtures / "short.wav", in_dir / "a.wav")
    shutil.copy2(integration_fixtures / "long.wav", in_dir / "b.wav")

    rc = cli.main(
        [
            "--once",
            "--input",
            str(in_dir),
            "--output",
            str(out_dir),
            "--save-srt",
            "--save-json",
            "--model",
            "mlx-community/whisper-tiny",
        ]
    )
    assert rc == 0
    for name in ("a", "b"):
        assert (out_dir / f"{name}.txt").read_text().strip() == "cli integration"
        assert (out_dir / f"{name}.srt").exists()
        assert (out_dir / f"{name}.json").exists()
    captured = capsys.readouterr()
    assert "a.wav" in captured.out and "b.wav" in captured.out


def test_cli_specific_files_argument(
    tmp_path: Path,
    integration_fixtures: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("AUTO_TRANSCRIBE_SETTINGS", str(tmp_path / "s.json"))
    out_dir = tmp_path / "output"
    out_dir.mkdir()
    target = tmp_path / "elsewhere.wav"
    shutil.copy2(integration_fixtures / "short.wav", target)

    rc = cli.main(
        [
            "--output",
            str(out_dir),
            "--model",
            "mlx-community/whisper-tiny",
            str(target),
        ]
    )
    assert rc == 0
    assert (out_dir / "elsewhere.txt").exists()
