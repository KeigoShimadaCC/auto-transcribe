"""Unit tests for the structured-logging redaction patcher."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from auto_transcribe.logging import _redact_text, configure_logging, get_logger, redact_paths


def test_redact_text_replaces_home_dir() -> None:
    home = str(Path.home())
    assert _redact_text(f"loaded {home}/notes.txt") == "loaded <home>/notes.txt"


def test_redact_text_redacts_example_data_basenames() -> None:
    assert "ExampleData/<redacted>" in _redact_text("processing ExampleData/lecture-2026-01-04.m4a")


def test_redact_text_passthrough_when_no_sensitive_paths() -> None:
    msg = "transcribed clip in 1.2s"
    assert _redact_text(msg) == msg


def test_redact_paths_patcher_mutates_record_in_place() -> None:
    home = str(Path.home())
    record: dict[str, Any] = {"message": f"opened {home}/x"}
    redact_paths(record)
    assert record["message"] == "opened <home>/x"


def test_get_logger_writes_redacted_message_to_sink(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("AUTO_TRANSCRIBE_LOG_DIR", str(tmp_path))
    import auto_transcribe.logging as alog

    alog._state["configured"] = False
    monkeypatch.setattr(alog, "LOG_DIR", tmp_path, raising=False)
    configure_logging(file_logging=False)

    captured: list[str] = []
    from loguru import logger as _logger

    sink_id = _logger.add(captured.append, level="INFO", format="{message}")
    try:
        log = get_logger("test")
        log.info("path is {p}", p=str(Path.home() / "secret.txt"))
    finally:
        _logger.remove(sink_id)

    assert any("<home>/secret.txt" in line for line in captured)
    assert all(str(Path.home()) not in line for line in captured)
