from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import tempfile
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator

from auto_transcribe.config import SUPPORTED_EXTS, Settings
from auto_transcribe.engines import build_engine
from auto_transcribe.engines.base import ProgressCallback, TranscriptionResult


class PipelineError(RuntimeError):
    pass


def is_supported(path: Path) -> bool:
    return path.is_file() and path.suffix.lower() in SUPPORTED_EXTS


def _ffmpeg_available() -> bool:
    return shutil.which("ffmpeg") is not None


@contextmanager
def _decoded_wav(src: Path) -> Iterator[Path]:
    if not _ffmpeg_available():
        raise PipelineError("ffmpeg not found on PATH")
    with tempfile.TemporaryDirectory(prefix="auto-transcribe-") as td:
        out = Path(td) / "audio.wav"
        cmd = [
            "ffmpeg",
            "-y",
            "-loglevel",
            "error",
            "-i",
            str(src),
            "-ac",
            "1",
            "-ar",
            "16000",
            "-vn",
            "-f",
            "wav",
            str(out),
        ]
        try:
            subprocess.run(cmd, check=True, capture_output=True)
        except subprocess.CalledProcessError as e:
            stderr = e.stderr.decode("utf-8", errors="replace") if e.stderr else ""
            raise PipelineError(f"ffmpeg failed: {stderr}") from e
        yield out


def _file_signature(path: Path) -> str:
    st = path.stat()
    h = hashlib.sha1()
    h.update(str(path.resolve()).encode())
    h.update(str(st.st_size).encode())
    h.update(str(int(st.st_mtime)).encode())
    return h.hexdigest()


def _state_path(settings: Settings) -> Path:
    p = Path(settings.state_dir) / "state.json"
    p.parent.mkdir(parents=True, exist_ok=True)
    return p


def load_state(settings: Settings) -> dict[str, str]:
    p = _state_path(settings)
    if not p.exists():
        return {}
    try:
        return json.loads(p.read_text())
    except json.JSONDecodeError:
        return {}


def save_state(settings: Settings, state: dict[str, str]) -> None:
    _state_path(settings).write_text(json.dumps(state, indent=2))


def already_done(settings: Settings, src: Path) -> bool:
    sig = _file_signature(src)
    return load_state(settings).get(str(src.resolve())) == sig


def mark_done(settings: Settings, src: Path) -> None:
    state = load_state(settings)
    state[str(src.resolve())] = _file_signature(src)
    save_state(settings, state)


def _format_srt_timestamp(seconds: float) -> str:
    if seconds < 0:
        seconds = 0
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    ms = int(round((seconds - int(seconds)) * 1000))
    if ms == 1000:
        s += 1
        ms = 0
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def _write_outputs(
    settings: Settings, src: Path, result: TranscriptionResult
) -> dict[str, Path]:
    out_dir = Path(settings.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    stem = src.stem
    written: dict[str, Path] = {}

    txt_path = out_dir / f"{stem}.txt"
    txt_path.write_text(result.text + ("\n" if result.text and not result.text.endswith("\n") else ""))
    written["txt"] = txt_path

    if settings.save_srt and result.segments:
        srt_path = out_dir / f"{stem}.srt"
        lines: list[str] = []
        for i, seg in enumerate(result.segments, start=1):
            lines.append(str(i))
            lines.append(
                f"{_format_srt_timestamp(seg.start)} --> {_format_srt_timestamp(seg.end)}"
            )
            lines.append(seg.text.strip())
            lines.append("")
        srt_path.write_text("\n".join(lines))
        written["srt"] = srt_path

    if settings.save_json:
        json_path = out_dir / f"{stem}.json"
        payload = {
            "text": result.text,
            "language": result.language,
            "segments": [
                {"start": s.start, "end": s.end, "text": s.text} for s in result.segments
            ],
        }
        json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2))
        written["json"] = json_path

    return written


@dataclass
class TranscriptionJobResult:
    source: Path
    outputs: dict[str, Path]
    text: str
    language: str | None
    duration_audio: float | None = None
    elapsed_seconds: float | None = None


def transcribe_file(
    src: Path,
    settings: Settings,
    on_progress: ProgressCallback | None = None,
) -> TranscriptionJobResult:
    if not is_supported(src):
        raise PipelineError(f"Unsupported file: {src}")

    if on_progress:
        on_progress(0.0, "Decoding")

    engine = build_engine(settings.model)

    with _decoded_wav(src) as wav:
        result = engine.transcribe(
            wav,
            language=None if settings.language == "auto" else settings.language,
            on_progress=on_progress,
        )

    outputs = _write_outputs(settings, src, result)
    mark_done(settings, src)

    if on_progress:
        on_progress(1.0, "Done")

    duration: float | None = None
    if result.segments:
        duration = max(s.end for s in result.segments)

    return TranscriptionJobResult(
        source=src,
        outputs=outputs,
        text=result.text,
        language=result.language,
        duration_audio=duration,
    )


def iter_pending_inputs(settings: Settings) -> list[Path]:
    in_dir = Path(settings.input_dir)
    if not in_dir.exists():
        return []
    files = [p for p in sorted(in_dir.iterdir()) if is_supported(p)]
    return [p for p in files if not already_done(settings, p)]
