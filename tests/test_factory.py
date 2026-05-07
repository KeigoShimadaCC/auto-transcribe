from __future__ import annotations

import pytest

from auto_transcribe.engines.factory import build_engine


def test_factory_routes_whisper_models() -> None:
    eng = build_engine("mlx-community/whisper-large-v3-turbo")
    assert eng.name == "mlx-whisper"
    assert eng.model == "mlx-community/whisper-large-v3-turbo"


def test_factory_routes_parakeet_models() -> None:
    eng = build_engine("mlx-community/parakeet-tdt-0.6b-v2")
    assert eng.name == "parakeet-mlx"
    assert eng.model == "mlx-community/parakeet-tdt-0.6b-v2"


def test_factory_is_case_insensitive_on_parakeet_match() -> None:
    eng = build_engine("Org/Parakeet-CUSTOM-Model")
    assert eng.name == "parakeet-mlx"


@pytest.mark.parametrize(
    "model",
    [
        "mlx-community/whisper-tiny",
        "mlx-community/whisper-base",
        "mlx-community/whisper-small",
        "mlx-community/whisper-medium",
        "mlx-community/whisper-large-v3",
    ],
)
def test_factory_defaults_to_whisper(model: str) -> None:
    assert build_engine(model).name == "mlx-whisper"
