from __future__ import annotations

from pathlib import Path

from auto_transcribe.engines.base import (
    ProgressCallback,
    Segment,
    TranscriptionResult,
)


class ParakeetEngine:
    name = "parakeet-mlx"

    def __init__(self, model: str) -> None:
        self.model = model

    def transcribe(
        self,
        wav_path: Path,
        language: str | None = None,
        on_progress: ProgressCallback | None = None,
    ) -> TranscriptionResult:
        try:
            from parakeet_mlx import from_pretrained
        except ImportError as e:
            raise RuntimeError(
                "parakeet-mlx is not installed. Run `pip install parakeet-mlx`."
            ) from e

        if on_progress:
            on_progress(0.05, "Loading Parakeet model")

        model = from_pretrained(self.model)

        if on_progress:
            on_progress(0.2, "Transcribing")

        result = model.transcribe(str(wav_path))

        text = getattr(result, "text", None) or str(result)
        raw_segments = getattr(result, "sentences", None) or getattr(result, "segments", [])
        segments: list[Segment] = []
        for s in raw_segments or []:
            start = float(getattr(s, "start", 0.0) or 0.0)
            end = float(getattr(s, "end", 0.0) or 0.0)
            seg_text = getattr(s, "text", "") or ""
            segments.append(Segment(start=start, end=end, text=seg_text))

        if on_progress:
            on_progress(0.95, "Finalizing")

        return TranscriptionResult(
            text=text.strip() if isinstance(text, str) else "",
            language="en",
            segments=segments,
        )
