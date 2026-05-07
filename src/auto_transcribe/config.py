from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]

AUDIO_EXTS = {".mp3", ".wav", ".m4a", ".aac", ".flac", ".ogg", ".opus"}
VIDEO_EXTS = {".mp4", ".mov", ".mkv", ".webm", ".avi", ".m4v"}
SUPPORTED_EXTS = AUDIO_EXTS | VIDEO_EXTS

DEFAULT_INPUT = PROJECT_ROOT / "input"
DEFAULT_OUTPUT = PROJECT_ROOT / "output"
DEFAULT_STATE_DIR = PROJECT_ROOT / ".state"


def settings_file() -> Path:
    return Path(
        os.environ.get(
            "AUTO_TRANSCRIBE_SETTINGS",
            str(Path.home() / ".auto-transcribe" / "settings.json"),
        )
    )


WHISPER_MODELS = [
    "mlx-community/whisper-tiny",
    "mlx-community/whisper-base",
    "mlx-community/whisper-small",
    "mlx-community/whisper-medium",
    "mlx-community/whisper-large-v3",
    "mlx-community/whisper-large-v3-turbo",
]
PARAKEET_MODELS = [
    "mlx-community/parakeet-tdt-0.6b-v2",
]
ALL_MODELS = WHISPER_MODELS + PARAKEET_MODELS
DEFAULT_MODEL = "mlx-community/whisper-large-v3-turbo"


@dataclass
class Settings:
    input_dir: str = str(DEFAULT_INPUT)
    output_dir: str = str(DEFAULT_OUTPUT)
    model: str = DEFAULT_MODEL
    language: str = "auto"
    save_srt: bool = False
    save_json: bool = False
    state_dir: str = str(DEFAULT_STATE_DIR)

    @property
    def engine(self) -> str:
        return "parakeet" if "parakeet" in self.model.lower() else "mlx-whisper"

    @classmethod
    def load(cls) -> Settings:
        path = settings_file()
        if path.exists():
            try:
                data = json.loads(path.read_text())
                return cls(**{k: v for k, v in data.items() if k in cls.__annotations__})
            except (OSError, json.JSONDecodeError, TypeError):
                pass
        return cls()

    def save(self) -> None:
        path = settings_file()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(asdict(self), indent=2))
