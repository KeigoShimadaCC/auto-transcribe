# Repository Guidelines

## Project Structure & Module Organization

- `src/auto_transcribe/` — Python package. Entry points: `cli.py`, `__main__.py`. Core: `pipeline.py`, `queue.py`, `watcher.py`, `config.py`, `ui_tk.py`. Engines live under `engines/` (`base.py` protocol, `factory.py` router, `mlx_whisper.py`, `parakeet.py`).
- `tests/` — pytest suite. `conftest.py` builds a synthetic WAV via ffmpeg; `test_e2e.py` is opt-in (`RUN_E2E=1`).
- `scripts/` — double-clickable `.command` launchers (`AutoTranscribe.command`, `Transcribe.command`).
- `input/`, `output/` — drop-folder + transcripts. Folders are tracked via `.gitkeep`; **contents are gitignored**.
- `ExampleData/` — private test media, **entirely gitignored**. Never commit lecture/audio assets.

## Build, Test, and Development Commands

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[parakeet,dev]"   # runtime + optional engine + test deps

python -m auto_transcribe           # GUI watcher
python -m auto_transcribe --once    # one-shot batch over input/
python -m auto_transcribe --no-ui   # headless watcher

pytest                              # fast unit suite (~3 s, fake engine)
RUN_E2E=1 pytest -m e2e             # full sweep over ExampleData/
```

## Coding Style & Naming Conventions

- Python 3.10+, 4-space indent, `from __future__ import annotations` at file top.
- Type hints on all public functions; prefer `dataclass` over dicts for state.
- Module/file: `snake_case.py`. Classes: `PascalCase`. Functions/vars: `snake_case`. Constants: `UPPER_SNAKE`.
- Engines implement the `Transcriber` protocol in `engines/base.py`; route from `engines/factory.py`.
- Imports sorted: stdlib, third-party, local (blank line between groups).
- Self-documenting code; comments only for non-obvious constraints.

## Testing Guidelines

- Framework: `pytest` (config in `pyproject.toml`). Files: `tests/test_*.py`. Functions: `test_*`.
- Unit tests must avoid network and ML model downloads — patch `pipeline.build_engine` with a fake (see `test_pipeline.py`).
- New engines: add a unit test that constructs the engine and asserts `name` / `model`.
- Mark long, real-model tests with `@pytest.mark.e2e` and gate behind `RUN_E2E=1`.

## Commit & Pull Request Guidelines

- Commits: imperative subject ≤ 72 chars (e.g. `Add Parakeet engine adapter`); body explains *why* and lists user-visible changes.
- One logical change per commit. No build artifacts, models, or media files.
- PRs: clear description, linked issue, before/after notes for UI tweaks, and `pytest` output. Update `README.md` / `QUICKSTART.md` when behavior or flags change.

## Security & Configuration Tips

- Settings live at `~/.auto-transcribe/settings.json`; override via `AUTO_TRANSCRIBE_SETTINGS=...`.
- Never log file contents or transcripts to stderr beyond status messages.
- Keep all engines local — do not add cloud / API-key dependencies.
- Verify `git status` before committing: `ExampleData/`, `input/*`, `output/*`, `.venv/`, `*.egg-info/` must remain untracked.
