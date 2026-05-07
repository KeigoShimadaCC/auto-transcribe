from __future__ import annotations

from auto_transcribe.config import DEFAULT_MODEL, Settings


def test_settings_engine_routing() -> None:
    s = Settings(model="mlx-community/whisper-large-v3-turbo")
    assert s.engine == "mlx-whisper"

    s = Settings(model="mlx-community/parakeet-tdt-0.6b-v2")
    assert s.engine == "parakeet"


def test_settings_default_model() -> None:
    s = Settings()
    assert s.model == DEFAULT_MODEL
