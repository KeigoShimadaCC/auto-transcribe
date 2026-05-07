from __future__ import annotations

from auto_transcribe.engines.base import Transcriber


def build_engine(model: str) -> Transcriber:
    lower = model.lower()
    if "parakeet" in lower:
        from auto_transcribe.engines.parakeet import ParakeetEngine

        return ParakeetEngine(model)
    from auto_transcribe.engines.mlx_whisper import MLXWhisperEngine

    return MLXWhisperEngine(model)
