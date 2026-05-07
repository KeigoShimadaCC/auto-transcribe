from __future__ import annotations

import queue
import subprocess
import sys
import threading
import time
import tkinter as tk
from pathlib import Path
from tkinter import ttk

from auto_transcribe.config import ALL_MODELS, Settings
from auto_transcribe.queue import Job, JobQueue, JobStatus
from auto_transcribe.watcher import FolderWatcher

LANGUAGES = ["auto", "en", "ja", "es", "fr", "de", "zh", "ko", "it", "pt"]


class TranscribeApp:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.queue = JobQueue(settings)
        self.queue.add_listener(self._on_job_event)
        self.watcher: FolderWatcher | None = None

        self._event_q: queue.Queue[Job] = queue.Queue()
        self._row_by_id: dict[str, str] = {}

        self.root = tk.Tk()
        self.root.title("Auto-Transcribe")
        self.root.geometry("640x420")
        self._build_ui()

        self.queue.start()

        if self.watch_var.get():
            self._start_watcher()

        self.root.after(100, self._drain_events)
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    def _build_ui(self) -> None:
        top = ttk.Frame(self.root, padding=8)
        top.pack(fill=tk.X)

        ttk.Label(top, text="Model:").grid(row=0, column=0, sticky=tk.W)
        self.model_var = tk.StringVar(value=self.settings.model)
        model_box = ttk.Combobox(
            top, textvariable=self.model_var, values=ALL_MODELS, width=42, state="readonly"
        )
        model_box.grid(row=0, column=1, padx=6, sticky=tk.W)
        model_box.bind("<<ComboboxSelected>>", self._on_model_change)

        ttk.Label(top, text="Lang:").grid(row=0, column=2, sticky=tk.W, padx=(12, 0))
        self.lang_var = tk.StringVar(value=self.settings.language)
        lang_box = ttk.Combobox(
            top, textvariable=self.lang_var, values=LANGUAGES, width=6, state="readonly"
        )
        lang_box.grid(row=0, column=3, padx=6)
        lang_box.bind("<<ComboboxSelected>>", self._on_lang_change)

        self.watch_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            top,
            text=f"Watch {self.settings.input_dir}",
            variable=self.watch_var,
            command=self._toggle_watcher,
        ).grid(row=1, column=0, columnspan=4, sticky=tk.W, pady=(6, 0))

        self.tree = ttk.Treeview(
            self.root,
            columns=("status", "progress", "elapsed"),
            show="tree headings",
        )
        self.tree.heading("#0", text="File")
        self.tree.heading("status", text="Status")
        self.tree.heading("progress", text="Progress")
        self.tree.heading("elapsed", text="Elapsed")
        self.tree.column("#0", width=300, anchor=tk.W)
        self.tree.column("status", width=120, anchor=tk.W)
        self.tree.column("progress", width=80, anchor=tk.E)
        self.tree.column("elapsed", width=80, anchor=tk.E)
        self.tree.pack(fill=tk.BOTH, expand=True, padx=8, pady=(8, 4))

        bottom = ttk.Frame(self.root, padding=8)
        bottom.pack(fill=tk.X)
        ttk.Button(bottom, text="Run once", command=self._run_once).pack(side=tk.LEFT)
        ttk.Button(bottom, text="Open output folder", command=self._open_output).pack(
            side=tk.LEFT, padx=6
        )
        ttk.Button(bottom, text="Quit", command=self._on_close).pack(side=tk.RIGHT)

        self.status_var = tk.StringVar(value="Idle")
        ttk.Label(self.root, textvariable=self.status_var, anchor=tk.W).pack(
            fill=tk.X, padx=8, pady=(0, 6)
        )

    def _on_model_change(self, _event: object = None) -> None:
        self.settings.model = self.model_var.get()
        self.settings.save()

    def _on_lang_change(self, _event: object = None) -> None:
        self.settings.language = self.lang_var.get()
        self.settings.save()

    def _start_watcher(self) -> None:
        if self.watcher is None:
            self.watcher = FolderWatcher(self.settings, on_new_file=self.queue.submit)
        self.watcher.start()
        self.status_var.set(f"Watching {self.settings.input_dir}")

    def _stop_watcher(self) -> None:
        if self.watcher is not None:
            self.watcher.stop()
            self.watcher = None
        self.status_var.set("Watcher stopped")

    def _toggle_watcher(self) -> None:
        if self.watch_var.get():
            self._start_watcher()
        else:
            self._stop_watcher()

    def _run_once(self) -> None:
        from auto_transcribe.pipeline import iter_pending_inputs

        def _enqueue() -> None:
            for p in iter_pending_inputs(self.settings):
                self.queue.submit(p)

        threading.Thread(target=_enqueue, daemon=True).start()

    def _open_output(self) -> None:
        out = Path(self.settings.output_dir)
        out.mkdir(parents=True, exist_ok=True)
        if sys.platform == "darwin":
            subprocess.run(["open", str(out)], check=False)
        elif sys.platform.startswith("linux"):
            subprocess.run(["xdg-open", str(out)], check=False)
        else:
            subprocess.run(["explorer", str(out)], check=False)

    def _on_job_event(self, job: Job) -> None:
        self._event_q.put(job)

    def _drain_events(self) -> None:
        try:
            while True:
                job = self._event_q.get_nowait()
                self._upsert_row(job)
        except queue.Empty:
            pass
        self.root.after(100, self._drain_events)

    def _upsert_row(self, job: Job) -> None:
        elapsed = ""
        if job.started_at:
            end = job.finished_at or time.time()
            elapsed = f"{end - job.started_at:.1f}s"
        progress_text = f"{int(job.progress * 100)}%"
        if job.id in self._row_by_id:
            iid = self._row_by_id[job.id]
            self.tree.item(
                iid,
                text=job.source.name,
                values=(job.status.value, progress_text, elapsed),
            )
        else:
            iid = self.tree.insert(
                "",
                tk.END,
                text=job.source.name,
                values=(job.status.value, progress_text, elapsed),
            )
            self._row_by_id[job.id] = iid
        if job.status == JobStatus.DONE:
            self.status_var.set(job.message)
        elif job.status == JobStatus.FAILED:
            self.status_var.set(f"{job.source.name}: {job.message}")
        else:
            self.status_var.set(f"{job.source.name}: {job.message}")

    def _on_close(self) -> None:
        self._stop_watcher()
        self.queue.stop(timeout=1.0)
        self.root.destroy()

    def run(self) -> None:
        self.root.mainloop()


def run(settings: Settings) -> None:
    TranscribeApp(settings).run()
