from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

from auto_transcribe.config import ALL_MODELS, Settings


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="auto-transcribe",
        description="Local audio/video transcription for Apple Silicon.",
    )
    p.add_argument("--once", action="store_true", help="Transcribe pending files and exit")
    p.add_argument("--no-ui", action="store_true", help="Headless watcher (no Tk window)")
    p.add_argument("--input", type=Path, help="Override input folder")
    p.add_argument("--output", type=Path, help="Override output folder")
    p.add_argument("--model", choices=ALL_MODELS, help="Model to use")
    p.add_argument("--language", help="Language code or 'auto'")
    p.add_argument("--save-srt", action="store_true", help="Also write .srt")
    p.add_argument("--save-json", action="store_true", help="Also write .json")
    p.add_argument("files", nargs="*", type=Path, help="Specific files to transcribe")
    return p


def _apply_overrides(settings: Settings, args: argparse.Namespace) -> Settings:
    if args.input:
        settings.input_dir = str(args.input.resolve())
    if args.output:
        settings.output_dir = str(args.output.resolve())
    if args.model:
        settings.model = args.model
    if args.language:
        settings.language = args.language
    if args.save_srt:
        settings.save_srt = True
    if args.save_json:
        settings.save_json = True
    return settings


def _print_progress(prefix: str) -> "callable":
    state = {"last": -1}

    def cb(fraction: float, status: str) -> None:
        pct = int(fraction * 100)
        if pct != state["last"]:
            state["last"] = pct
            print(f"  [{pct:3d}%] {prefix}: {status}", flush=True)

    return cb


def _run_once(settings: Settings, files: list[Path] | None = None) -> int:
    from auto_transcribe.pipeline import iter_pending_inputs, transcribe_file

    targets = files if files else iter_pending_inputs(settings)
    if not targets:
        print("No pending files in", settings.input_dir)
        return 0
    rc = 0
    for src in targets:
        print(f"-> {src.name}")
        t0 = time.time()
        try:
            result = transcribe_file(src, settings, on_progress=_print_progress(src.name))
        except Exception as e:  # noqa: BLE001
            print(f"   FAILED: {e}", file=sys.stderr)
            rc = 1
            continue
        elapsed = time.time() - t0
        print(f"   wrote {result.outputs['txt']} ({elapsed:.1f}s)")
    return rc


_TK_HINT = (
    "Tk UI unavailable: this Python build is missing the `tkinter` module.\n"
    "  - Homebrew Python: run `brew install python-tk@<your-version>`\n"
    "    (e.g. `brew install python-tk@3.14`).\n"
    "  - Or use the python.org installer / system Python which ships Tk.\n"
    "Falling back to headless watcher. Use --no-ui to silence this message."
)


def _run_watch(settings: Settings, headless: bool) -> int:
    if not headless:
        try:
            from auto_transcribe.ui_tk import run as run_ui
        except ImportError as e:
            if "tkinter" in str(e) or "_tkinter" in str(e):
                print(_TK_HINT, file=sys.stderr)
                headless = True
            else:
                raise
        else:
            run_ui(settings)
            return 0

    from auto_transcribe.queue import JobQueue
    from auto_transcribe.watcher import FolderWatcher

    q = JobQueue(settings)
    q.add_listener(
        lambda j: print(
            f"[{j.status.value}] {j.source.name}: {int(j.progress * 100)}% {j.message}"
        )
    )
    q.start()
    w = FolderWatcher(settings, on_new_file=lambda p: q.submit(p))
    w.start()
    print(f"Watching {settings.input_dir} ... Ctrl-C to stop.")
    try:
        while True:
            time.sleep(1.0)
    except KeyboardInterrupt:
        pass
    finally:
        w.stop()
        q.stop()
    return 0


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    settings = Settings.load()
    settings = _apply_overrides(settings, args)
    settings.save()

    Path(settings.input_dir).mkdir(parents=True, exist_ok=True)
    Path(settings.output_dir).mkdir(parents=True, exist_ok=True)

    if args.files or args.once:
        return _run_once(settings, files=[p.resolve() for p in args.files] or None)

    return _run_watch(settings, headless=args.no_ui)


if __name__ == "__main__":
    raise SystemExit(main())
