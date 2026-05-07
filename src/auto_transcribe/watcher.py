from __future__ import annotations

import threading
import time
from pathlib import Path
from typing import Callable

from auto_transcribe.config import SUPPORTED_EXTS, Settings
from auto_transcribe.pipeline import already_done, is_supported


class FolderWatcher:
    """Polling-based watcher.

    Avoids watchdog's threading quirks under Tk by simply scanning the input
    directory at a small interval. Plenty fast for a folder of dozens of
    files; the heavy work happens during transcription anyway.
    """

    def __init__(
        self,
        settings: Settings,
        on_new_file: Callable[[Path], None],
        poll_interval: float = 1.0,
        stable_after: float = 2.0,
    ) -> None:
        self.settings = settings
        self.on_new_file = on_new_file
        self.poll_interval = poll_interval
        self.stable_after = stable_after
        self._thread: threading.Thread | None = None
        self._stop = threading.Event()
        self._seen: dict[str, tuple[int, float]] = {}
        self._dispatched: set[str] = set()

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._stop.clear()
        self._thread = threading.Thread(target=self._run, name="folder-watcher", daemon=True)
        self._thread.start()

    def stop(self, timeout: float = 3.0) -> None:
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=timeout)

    def _run(self) -> None:
        in_dir = Path(self.settings.input_dir)
        in_dir.mkdir(parents=True, exist_ok=True)
        while not self._stop.is_set():
            try:
                self._scan_once(in_dir)
            except Exception:  # noqa: BLE001
                pass
            self._stop.wait(self.poll_interval)

    def _scan_once(self, in_dir: Path) -> None:
        now = time.time()
        for p in in_dir.iterdir():
            if not is_supported(p):
                continue
            key = str(p.resolve())
            if key in self._dispatched:
                continue
            try:
                size = p.stat().st_size
            except FileNotFoundError:
                continue
            prev = self._seen.get(key)
            if prev is None or prev[0] != size:
                self._seen[key] = (size, now)
                continue
            if now - prev[1] >= self.stable_after:
                if already_done(self.settings, p):
                    self._dispatched.add(key)
                    continue
                self._dispatched.add(key)
                try:
                    self.on_new_file(p)
                except Exception:  # noqa: BLE001
                    pass
