"""End-to-end pipeline integration: real ffmpeg + real settings persistence
+ fake engine. Exercises the entire flow except the ML model itself."""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from auto_transcribe import pipeline
from auto_transcribe.config import Settings
from auto_transcribe.engines.base import Segment, TranscriptionResult

pytestmark = pytest.mark.integration


class _ScriptedEngine:
    """Engine that records every call so we can assert on the boundary."""

    name = "scripted"

    def __init__(self, model: str) -> None:
        self.model = model
        self.calls: list[tuple[Path, str | None]] = []

    def transcribe(self, wav_path, language=None, on_progress=None):
        self.calls.append((Path(wav_path), language))
        if on_progress:
            on_progress(0.5, "Transcribing")
        return TranscriptionResult(
            text="integration ok",
            language=language or "en",
            segments=[
                Segment(0.0, 0.4, "integration"),
                Segment(0.4, 1.0, "ok"),
            ],
        )


@pytest.fixture
def scripted_engine(monkeypatch: pytest.MonkeyPatch) -> _ScriptedEngine:
    instance = _ScriptedEngine("fake-model")
    monkeypatch.setattr(pipeline, "build_engine", lambda model: instance)
    return instance


def test_audio_wav_through_full_pipeline(
    integration_fixtures: Path,
    isolated_settings: Settings,
    scripted_engine: _ScriptedEngine,
) -> None:
    src = Path(isolated_settings.input_dir) / "short.wav"
    shutil.copy2(integration_fixtures / "short.wav", src)
    isolated_settings.save_srt = True
    isolated_settings.save_json = True

    result = pipeline.transcribe_file(src, isolated_settings)

    assert len(scripted_engine.calls) == 1
    wav_passed, lang = scripted_engine.calls[0]
    assert wav_passed.suffix == ".wav"
    assert lang is None  # "auto" maps to None at the engine boundary

    txt = result.outputs["txt"].read_text()
    assert txt.strip() == "integration ok"

    srt = result.outputs["srt"].read_text()
    assert "00:00:00,000 --> 00:00:00,400" in srt
    assert "00:00:00,400 --> 00:00:01,000" in srt

    import json

    data = json.loads(result.outputs["json"].read_text())
    assert data["language"] == "en"
    assert len(data["segments"]) == 2

    assert pipeline.already_done(isolated_settings, src)


def test_stereo_44k_audio_is_decoded_to_mono_16k(
    integration_fixtures: Path,
    isolated_settings: Settings,
    scripted_engine: _ScriptedEngine,
) -> None:
    """ffmpeg in the pipeline must downmix + resample regardless of the
    source layout — the engine is documented to receive 16 kHz mono."""
    import wave

    src = Path(isolated_settings.input_dir) / "long.wav"
    shutil.copy2(integration_fixtures / "long.wav", src)

    captured: dict[str, tuple[int, int]] = {}

    def _capture(wav_path, language=None, on_progress=None):
        with wave.open(str(wav_path), "rb") as w:
            captured["params"] = (w.getnchannels(), w.getframerate())
        return TranscriptionResult(text="ok")

    scripted_engine.transcribe = _capture  # type: ignore[assignment]

    pipeline.transcribe_file(src, isolated_settings)
    assert captured["params"] == (1, 16000)


def test_video_file_audio_is_extracted(
    integration_fixtures: Path,
    isolated_settings: Settings,
    scripted_engine: _ScriptedEngine,
) -> None:
    src = Path(isolated_settings.input_dir) / "fake.mp4"
    shutil.copy2(integration_fixtures / "fake.mp4", src)

    result = pipeline.transcribe_file(src, isolated_settings)

    assert (Path(isolated_settings.output_dir) / "fake.txt").exists()
    assert result.outputs["txt"].read_text().strip() == "integration ok"
    assert len(scripted_engine.calls) == 1


def test_explicit_language_override_reaches_engine(
    integration_fixtures: Path,
    isolated_settings: Settings,
    scripted_engine: _ScriptedEngine,
) -> None:
    isolated_settings.language = "ja"
    src = Path(isolated_settings.input_dir) / "short.wav"
    shutil.copy2(integration_fixtures / "short.wav", src)

    pipeline.transcribe_file(src, isolated_settings)

    assert scripted_engine.calls[0][1] == "ja"


def test_unsupported_extension_is_rejected(
    isolated_settings: Settings, scripted_engine: _ScriptedEngine, tmp_path: Path
) -> None:
    bad = Path(isolated_settings.input_dir) / "notes.txt"
    bad.write_text("not media")
    with pytest.raises(pipeline.PipelineError):
        pipeline.transcribe_file(bad, isolated_settings)
    assert scripted_engine.calls == []
