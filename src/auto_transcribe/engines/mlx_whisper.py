from __future__ import annotations

from pathlib import Path

from auto_transcribe.engines.base import (
    ProgressCallback,
    Segment,
    TranscriptionResult,
)


class MLXWhisperEngine:
    name = "mlx-whisper"

    def __init__(self, model: str) -> None:
        self.model = model

    def transcribe(
        self,
        wav_path: Path,
        language: str | None = None,
        on_progress: ProgressCallback | None = None,
    ) -> TranscriptionResult:
        try:
            import mlx_whisper
        except ImportError as e:
            raise RuntimeError(
                "mlx-whisper is not installed. Run `pip install mlx-whisper`."
            ) from e

        if on_progress:
            on_progress(0.05, "Loading model")

        kwargs: dict[str, object] = {
            "path_or_hf_repo": self.model,
            "verbose": False,
        }
        if language and language != "auto":
            kwargs["language"] = language

        if on_progress:
            on_progress(0.15, "Transcribing")

        result = mlx_whisper.transcribe(str(wav_path), **kwargs)

        if on_progress:
            on_progress(0.95, "Finalizing")

        segments = [
            Segment(start=float(s["start"]), end=float(s["end"]), text=str(s["text"]))
            for s in result.get("segments", [])
        ]
        return TranscriptionResult(
            text=result.get("text", "").strip(),
            language=result.get("language"),
            segments=segments,
        )
