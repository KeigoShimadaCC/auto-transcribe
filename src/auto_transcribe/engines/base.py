from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Protocol


@dataclass
class Segment:
    start: float
    end: float
    text: str


@dataclass
class TranscriptionResult:
    text: str
    language: str | None = None
    segments: list[Segment] = field(default_factory=list)


ProgressCallback = Callable[[float, str], None]
"""Receives (fraction_in_0_1, status_text)."""


class Transcriber(Protocol):
    name: str
    model: str

    def transcribe(
        self,
        wav_path: Path,
        language: str | None = None,
        on_progress: ProgressCallback | None = None,
    ) -> TranscriptionResult: ...
