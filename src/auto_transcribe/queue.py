from __future__ import annotations

import contextlib
import queue
import threading
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

from auto_transcribe.config import Settings
from auto_transcribe.pipeline import (
    PipelineError,
    TranscriptionJobResult,
    transcribe_file,
)


class JobStatus(str, Enum):
    PENDING = "pending"
    DECODING = "decoding"
    TRANSCRIBING = "transcribing"
    WRITING = "writing"
    DONE = "done"
    FAILED = "failed"


@dataclass
class Job:
    source: Path
    status: JobStatus = JobStatus.PENDING
    progress: float = 0.0
    message: str = ""
    error: str | None = None
    result: TranscriptionJobResult | None = None
    started_at: float | None = None
    finished_at: float | None = None
    id: str = field(default_factory=lambda: str(time.time_ns()))


JobListener = Callable[[Job], None]


class JobQueue:
    """Serial job queue: one transcription at a time, with progress events."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self._q: queue.Queue[Job] = queue.Queue()
        self._jobs: dict[str, Job] = {}
        self._listeners: list[JobListener] = []
        self._lock = threading.Lock()
        self._worker: threading.Thread | None = None
        self._stop = threading.Event()
        self._enqueued_paths: set[str] = set()

    def add_listener(self, listener: JobListener) -> None:
        self._listeners.append(listener)

    def _emit(self, job: Job) -> None:
        for listener in list(self._listeners):
            with contextlib.suppress(Exception):
                listener(job)

    def submit(self, source: Path) -> Job | None:
        key = str(source.resolve())
        with self._lock:
            if key in self._enqueued_paths:
                return None
            self._enqueued_paths.add(key)
            job = Job(source=source)
            self._jobs[job.id] = job
        self._q.put(job)
        self._emit(job)
        return job

    def jobs(self) -> list[Job]:
        with self._lock:
            return list(self._jobs.values())

    def start(self) -> None:
        if self._worker and self._worker.is_alive():
            return
        self._stop.clear()
        self._worker = threading.Thread(target=self._run, name="job-worker", daemon=True)
        self._worker.start()

    def stop(self, timeout: float = 5.0) -> None:
        self._stop.set()
        self._q.put(_SENTINEL)
        if self._worker:
            self._worker.join(timeout=timeout)

    def join(self, timeout: float | None = None) -> None:
        deadline = None if timeout is None else time.time() + timeout
        while True:
            with self._lock:
                pending = [
                    j
                    for j in self._jobs.values()
                    if j.status not in (JobStatus.DONE, JobStatus.FAILED)
                ]
            if not pending:
                return
            if deadline is not None and time.time() > deadline:
                return
            time.sleep(0.05)

    def _run(self) -> None:
        while not self._stop.is_set():
            try:
                job = self._q.get(timeout=0.5)
            except queue.Empty:
                continue
            if job is _SENTINEL:
                return
            self._process(job)

    def _process(self, job: Job) -> None:
        job.started_at = time.time()
        job.status = JobStatus.DECODING
        job.message = "Decoding"
        self._emit(job)

        def on_progress(fraction: float, status: str) -> None:
            job.progress = max(0.0, min(1.0, fraction))
            lower = status.lower()
            if "decod" in lower:
                job.status = JobStatus.DECODING
            elif "transcrib" in lower or "loading" in lower:
                job.status = JobStatus.TRANSCRIBING
            elif "final" in lower or "writ" in lower:
                job.status = JobStatus.WRITING
            job.message = status
            self._emit(job)

        try:
            result = transcribe_file(job.source, self.settings, on_progress=on_progress)
            job.result = result
            job.progress = 1.0
            job.status = JobStatus.DONE
            txt_out = result.outputs.get("txt")
            job.message = f"Wrote {txt_out.name if txt_out is not None else '?'}"
        except PipelineError as e:
            job.status = JobStatus.FAILED
            job.error = str(e)
            job.message = f"Failed: {e}"
        except Exception as e:
            job.status = JobStatus.FAILED
            job.error = repr(e)
            job.message = f"Failed: {e}"
        finally:
            job.finished_at = time.time()
            self._emit(job)


_SENTINEL: Job = Job(source=Path("/__sentinel__"))
