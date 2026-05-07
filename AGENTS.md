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

- Framework: `pytest` (config in `pyproject.toml`). Three tiers, each with its own folder/marker:
  - **Unit** — `tests/test_*.py`. Must avoid network and ML model downloads; patch `pipeline.build_engine` with a fake (see `tests/test_pipeline.py`).
  - **Integration** — `tests/integration/test_*.py` with `@pytest.mark.integration`. Real ffmpeg + fake engine; exercises multiple modules together.
  - **E2E** — `tests/test_e2e.py` with `@pytest.mark.e2e`, gated by `RUN_E2E=1`. Real model, real `ExampleData/`.
- New engines: add a unit test that constructs the engine and asserts `name` / `model` (see `tests/test_factory.py`).
- **Coverage gate**: 80%, enforced by `pytest --cov-fail-under=80`. The gate measures only the testable surface (`ui_tk.py` and the two ML engine adapters are excluded in `[tool.coverage.run] omit`). Adding new modules without tests will fail CI.
- **Parallelism & isolation**: `pytest-xdist` (`-n auto`) runs the suite across all cores; `pytest-randomly` randomises order each run. Tests therefore must not rely on global state — use the `isolated_settings` fixture for any filesystem state, and pass `AUTO_TRANSCRIBE_SETTINGS` via `monkeypatch.setenv`.
- **Flaky tests**: mark a known transient with `@pytest.mark.flaky(reruns=2, reruns_delay=1)` (provided by `pytest-rerunfailures`). Quarantine policy: any test that needs rerunning twice in a week must be either fixed or moved into a `skip` block with a TODO referencing an issue.
- **Performance tracking**: `--durations=10` is on by default; CI uploads `tests/_reports/junit.xml` and `tests/_reports/htmlcov/` as artifacts and writes a "Slowest tests" table to the GitHub step summary on every run.

Run the full suite locally with `pytest`. Run only the integration tier with `pytest tests/integration -m integration`. Run the e2e sweep with `RUN_E2E=1 pytest -m e2e`.

## Commit & Pull Request Guidelines

- **Conventional Commits required.** Format: `<type>(<scope>)?: <subject>` where `<type>` is one of `feat`, `fix`, `perf`, `deps`, `revert`, `docs`, `refactor`, `test`, `build`, `ci`, `chore`. Examples: `feat(engine): add Parakeet adapter`, `fix(watcher): debounce by size-stable window`. Breaking changes append `!` to the type or include a `BREAKING CHANGE:` footer.
- Subject ≤ 72 chars, imperative mood; body explains *why* and lists user-visible changes.
- One logical change per commit. No build artifacts, models, or media files.
- PRs: clear description, linked issue, before/after notes for UI tweaks, and `pytest` output. Update `README.md` / `QUICKSTART.md` when behavior or flags change.

## Releases

- Versioning is automated via [release-please](https://github.com/googleapis/release-please).
- On every push to `main`, the `.github/workflows/release-please.yml` workflow opens or updates a "release PR" that bumps `pyproject.toml` / `src/auto_transcribe/__init__.py` and prepends to `CHANGELOG.md` based on Conventional Commits since the last tag.
- Merging the release PR creates a tagged GitHub release. Manifest lives at `.release-please-manifest.json`; section mapping in `release-please-config.json`.
- Do not edit `CHANGELOG.md` by hand for released versions; let release-please own it.

## Security & Configuration Tips

- Settings live at `~/.auto-transcribe/settings.json`; override via `AUTO_TRANSCRIBE_SETTINGS=...`.
- Never log file contents or transcripts to stderr beyond status messages.
- Keep all engines local — do not add cloud / API-key dependencies.
- Verify `git status` before committing: `ExampleData/`, `input/*`, `output/*`, `.venv/`, `*.egg-info/` must remain untracked.
