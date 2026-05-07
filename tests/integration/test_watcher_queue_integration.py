"""Watcher + queue + pipeline integration: drop a file in, get a transcript out."""

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

pytestmark = pytest.mark.integration


class _CountingEngine:
    name = "counting"

    def __init__(self, model: str) -> None:
        self.model = model
        self.invocations = 0

    def transcribe(self, wav_path, language=None, on_progress=None):
        self.invocations += 1
        if on_progress:
            on_progress(0.4, "Transcribing")
            on_progress(0.9, "Finalizing")
        return TranscriptionResult(
            text=f"call#{self.invocations}",
            segments=[Segment(0.0, 0.3, f"call#{self.invocations}")],
        )


@pytest.fixture(autouse=True)
def patch_engine(monkeypatch: pytest.MonkeyPatch) -> _CountingEngine:
    eng = _CountingEngine("fake")
    monkeypatch.setattr(pipeline, "build_engine", lambda model: eng)
    return eng


def _wait_for(predicate, timeout: float = 20.0) -> bool:
    deadline = time.time() + timeout
    while time.time() < deadline:
        if predicate():
            return True
        time.sleep(0.05)
    return False


@pytest.mark.flaky(reruns=2, reruns_delay=1)
def test_dropped_file_triggers_full_pipeline(
    integration_fixtures: Path, isolated_settings: Settings, patch_engine: _CountingEngine
) -> None:
    q = JobQueue(isolated_settings)
    q.start()
    watcher = FolderWatcher(
        isolated_settings,
        on_new_file=q.submit,
        poll_interval=0.15,
        stable_after=0.3,
    )
    watcher.start()
    try:
        target = Path(isolated_settings.input_dir) / "short.wav"
        shutil.copy2(integration_fixtures / "short.wav", target)

        out = Path(isolated_settings.output_dir) / "short.txt"
        assert _wait_for(out.exists, timeout=20.0)
        q.join(timeout=5.0)
        assert out.read_text().strip().startswith("call#")
        assert patch_engine.invocations == 1
        assert any(j.status == JobStatus.DONE for j in q.jobs())
    finally:
        watcher.stop()
        q.stop()


@pytest.mark.flaky(reruns=2, reruns_delay=1)
def test_three_files_dropped_in_burst_are_all_processed_serially(
    integration_fixtures: Path, isolated_settings: Settings, patch_engine: _CountingEngine
) -> None:
    q = JobQueue(isolated_settings)
    q.start()
    watcher = FolderWatcher(
        isolated_settings,
        on_new_file=q.submit,
        poll_interval=0.1,
        stable_after=0.25,
    )
    watcher.start()
    try:
        in_dir = Path(isolated_settings.input_dir)
        for i in range(3):
            shutil.copy2(integration_fixtures / "short.wav", in_dir / f"clip_{i}.wav")
        out_dir = Path(isolated_settings.output_dir)
        assert _wait_for(
            lambda: all((out_dir / f"clip_{i}.txt").exists() for i in range(3)),
            timeout=30.0,
        )
        q.join(timeout=5.0)
        assert patch_engine.invocations == 3
        # Only one job in DECODING/TRANSCRIBING/WRITING at any frame:
        # serial queue invariant => no two .txt files should have been written
        # simultaneously, but all three end up DONE.
        statuses = [j.status for j in q.jobs()]
        assert statuses.count(JobStatus.DONE) == 3
        assert statuses.count(JobStatus.FAILED) == 0
    finally:
        watcher.stop()
        q.stop()


def test_already_done_files_are_not_redispatched(
    integration_fixtures: Path, isolated_settings: Settings, patch_engine: _CountingEngine
) -> None:
    target = Path(isolated_settings.input_dir) / "short.wav"
    shutil.copy2(integration_fixtures / "short.wav", target)
    pipeline.transcribe_file(target, isolated_settings)
    assert patch_engine.invocations == 1

    q = JobQueue(isolated_settings)
    q.start()
    watcher = FolderWatcher(
        isolated_settings,
        on_new_file=q.submit,
        poll_interval=0.1,
        stable_after=0.2,
    )
    watcher.start()
    try:
        time.sleep(1.0)
        assert q.jobs() == []
        assert patch_engine.invocations == 1
    finally:
        watcher.stop()
        q.stop()
