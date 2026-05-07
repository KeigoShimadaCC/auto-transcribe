from __future__ import annotations

import shutil
import time
from pathlib import Path

import pytest

from auto_transcribe import pipeline
from auto_transcribe.config import Settings
from auto_transcribe.engines.base import Segment, TranscriptionResult
from auto_transcribe.queue import JobQueue, JobStatus
from auto_transcribe.watcher import FolderWatcher


class _FakeEngine:
    name = "fake"

    def __init__(self, model: str) -> None:
        self.model = model

    def transcribe(self, wav_path, language=None, on_progress=None):
        return TranscriptionResult(
            text="ok",
            language="en",
            segments=[Segment(start=0.0, end=0.5, text="ok")],
        )


@pytest.fixture(autouse=True)
def patch_engine(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(pipeline, "build_engine", _FakeEngine)


def _wait_for(predicate, timeout: float = 8.0) -> bool:
    deadline = time.time() + timeout
    while time.time() < deadline:
        if predicate():
            return True
        time.sleep(0.1)
    return False


@pytest.mark.flaky(reruns=2, reruns_delay=1)
def test_watcher_picks_up_new_file(isolated_settings: Settings, fixtures_dir: Path) -> None:
    q = JobQueue(isolated_settings)
    q.start()
    watcher = FolderWatcher(
        isolated_settings,
        on_new_file=q.submit,
        poll_interval=0.2,
        stable_after=0.4,
    )
    watcher.start()
    try:
        target = Path(isolated_settings.input_dir) / "tone.wav"
        shutil.copy2(fixtures_dir / "tone.wav", target)
        out = Path(isolated_settings.output_dir) / "tone.txt"
        assert _wait_for(out.exists, timeout=8.0), "output txt not produced"
        assert out.read_text().strip() == "ok"

        jobs = q.jobs()
        assert any(j.status == JobStatus.DONE for j in jobs)
    finally:
        watcher.stop()
        q.stop()


def test_watcher_dedupes_already_done(isolated_settings: Settings, fixtures_dir: Path) -> None:
    target = Path(isolated_settings.input_dir) / "tone.wav"
    shutil.copy2(fixtures_dir / "tone.wav", target)
    pipeline.transcribe_file(target, isolated_settings)

    q = JobQueue(isolated_settings)
    q.start()
    watcher = FolderWatcher(
        isolated_settings,
        on_new_file=q.submit,
        poll_interval=0.2,
        stable_after=0.3,
    )
    watcher.start()
    try:
        time.sleep(1.5)
        assert q.jobs() == []
    finally:
        watcher.stop()
        q.stop()
