from __future__ import annotations

import shutil
from pathlib import Path
from types import SimpleNamespace

import pytest

from auto_transcribe import pipeline
from auto_transcribe.config import Settings
from auto_transcribe.engines.base import Segment, TranscriptionResult


class _FakeEngine:
    name = "fake"

    def __init__(self, model: str) -> None:
        self.model = model

    def transcribe(self, wav_path, language=None, on_progress=None):
        if on_progress:
            on_progress(0.5, "Transcribing")
        return TranscriptionResult(
            text="hello world",
            language="en",
            segments=[Segment(start=0.0, end=1.0, text="hello world")],
        )


@pytest.fixture
def patch_engine(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(pipeline, "build_engine", lambda model: _FakeEngine(model))


def test_is_supported(tmp_path: Path) -> None:
    f = tmp_path / "a.mp3"
    f.write_bytes(b"x")
    assert pipeline.is_supported(f)
    bad = tmp_path / "a.txt"
    bad.write_text("x")
    assert not pipeline.is_supported(bad)


def test_transcribe_file_writes_outputs(
    isolated_settings: Settings, fixtures_dir: Path, patch_engine: None
) -> None:
    src = Path(isolated_settings.input_dir) / "tone.wav"
    shutil.copy2(fixtures_dir / "tone.wav", src)

    isolated_settings.save_srt = True
    isolated_settings.save_json = True

    result = pipeline.transcribe_file(src, isolated_settings)
    assert result.outputs["txt"].read_text().strip() == "hello world"
    assert result.outputs["srt"].exists()
    assert result.outputs["json"].exists()
    srt = result.outputs["srt"].read_text()
    assert "00:00:00,000 --> 00:00:01,000" in srt


def test_state_dedup(
    isolated_settings: Settings, fixtures_dir: Path, patch_engine: None
) -> None:
    src = Path(isolated_settings.input_dir) / "tone.wav"
    shutil.copy2(fixtures_dir / "tone.wav", src)
    pipeline.transcribe_file(src, isolated_settings)
    assert pipeline.already_done(isolated_settings, src)

    pending = pipeline.iter_pending_inputs(isolated_settings)
    assert pending == []


def test_format_srt_timestamp() -> None:
    assert pipeline._format_srt_timestamp(0) == "00:00:00,000"
    assert pipeline._format_srt_timestamp(3661.5) == "01:01:01,500"
    assert pipeline._format_srt_timestamp(0.999) == "00:00:00,999"
