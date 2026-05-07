# auto-transcribe

Local audio/video transcription for Apple Silicon. Drop a file into `input/`, get a `.txt` in `output/`. No cloud, no API keys, no per-minute fees.

Built and tuned for **Mac mini M4 Pro / 64 GB**, but works on any Apple Silicon Mac (M1 / M2 / M3 / M4).

> **TL;DR:** double-click `scripts/AutoTranscribe.command`, drag a video into `input/`, find the transcript in `output/`.

---

## Table of contents

- [Features](#features)
- [Why local? Why these models?](#why-local-why-these-models)
- [Requirements](#requirements)
- [Install](#install)
- [Usage](#usage)
  - [GUI watcher (recommended)](#gui-watcher-recommended)
  - [Manual one-shot](#manual-one-shot)
  - [CLI](#cli)
- [Models](#models)
- [Output formats](#output-formats)
- [Configuration](#configuration)
- [Architecture](#architecture)
- [Project layout](#project-layout)
- [Tests](#tests)
- [Troubleshooting](#troubleshooting)
- [FAQ](#faq)
- [License](#license)

---

## Features

- **Drop-and-go workflow.** Watcher mode picks up any file you put into `input/` and writes `<name>.txt` to `output/`.
- **Two trigger modes.** Background watcher *or* a double-click `.command` file for one-shot batch runs.
- **Tkinter UI.** Tiny window with model dropdown, language selector, queue list, per-file progress.
- **Two engines.**
  - `mlx-whisper` (default) — multilingual, runs on Apple's MLX framework, FP16 on the GPU.
  - `parakeet-mlx` — fastest option for English-only content.
- **Audio + video.** mp3, wav, m4a, aac, flac, ogg, opus, mp4, mov, mkv, webm, avi, m4v.
- **Idempotent.** sha1 of `(path, size, mtime)` is stored so re-runs skip already-transcribed files.
- **Optional outputs.** `.srt` (subtitles) and `.json` (segments + language) on demand.
- **Zero network at runtime.** After the model is cached, everything runs offline.

---

## Why local? Why these models?

In May 2026 the best free local options for Apple Silicon are:

| Engine | Model | Strengths | Trade-offs |
|---|---|---|---|
| **mlx-whisper** | `whisper-large-v3-turbo` | Best general accuracy, multilingual (incl. Japanese), 5-10× realtime on M-series | ~1.6 GB model |
| **parakeet-mlx** | `parakeet-tdt-0.6b-v2` | Fastest on M-series (often 30-50× realtime), excellent English WER | English-only |
| whisper.cpp (Metal) | `ggml-large-v3-turbo` | C++, no Python | Slightly slower than MLX in 2026 |
| Apple Speech | built-in | Zero deps | Lower accuracy on long-form |

**Default:** `mlx-community/whisper-large-v3-turbo` via `mlx-whisper`. With 64 GB of unified memory the FP16 turbo model is trivially cheap to keep resident.

---

## Requirements

- macOS 13+ on Apple Silicon (M1 / M2 / M3 / M4)
- Python 3.10+ (3.11 / 3.12 / 3.13 / 3.14 all fine)
- `ffmpeg` on `PATH` (already present if you have Homebrew: `brew install ffmpeg`)
- Tk for the GUI window. Homebrew Python ships **without** Tk; install it once:
  `brew install python-tk@3.14` (replace `3.14` with your Python version).
  If Tk is missing, the app automatically falls back to headless watcher mode.
- ~2 GB disk for the default model (cached under `~/.cache/huggingface/`)

---

## Install

```bash
git clone https://github.com/KeigoShimadaCC/auto-transcribe.git
cd auto-transcribe

python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -e ".[parakeet,dev]"
```

Or, if you only ever plan to double-click the launchers, skip this — the `.command` files create the venv on first run automatically.

---

## Usage

### GUI watcher (recommended)

```bash
./scripts/AutoTranscribe.command
```

(or double-click it in Finder)

A small window opens. Anything you drop into `./input` is transcribed in the background and the `.txt` appears in `./output`. Use the dropdown to switch models or language; the queue table shows progress.

### Manual one-shot

When you have a batch of files and don't want a long-running process:

```bash
./scripts/Transcribe.command
```

This processes everything currently in `./input` and exits.

### CLI

```bash
# Drop-folder watcher with UI
python -m auto_transcribe

# Headless watcher (no Tk window)
python -m auto_transcribe --no-ui

# One-shot over the input folder
python -m auto_transcribe --once

# Specific files, with extras
python -m auto_transcribe --once --save-srt --save-json path/to/talk.mp4

# Pick a model and language
python -m auto_transcribe --once \
  --model mlx-community/whisper-large-v3-turbo \
  --language ja
```

Full help:

```bash
python -m auto_transcribe --help
```

---

## Models

Available from the UI dropdown and `--model` flag:

| ID | Engine | Notes |
|---|---|---|
| `mlx-community/whisper-tiny` | mlx-whisper | ~75 MB, fastest, low accuracy. Great for smoke tests. |
| `mlx-community/whisper-base` | mlx-whisper | ~150 MB |
| `mlx-community/whisper-small` | mlx-whisper | ~500 MB |
| `mlx-community/whisper-medium` | mlx-whisper | ~1.5 GB |
| `mlx-community/whisper-large-v3` | mlx-whisper | ~3 GB, highest accuracy |
| **`mlx-community/whisper-large-v3-turbo`** | mlx-whisper | **Default.** ~1.6 GB, near-large quality, ~3× faster |
| `mlx-community/parakeet-tdt-0.6b-v2` | parakeet-mlx | English-only, very fast |

Models are downloaded the first time they're requested and cached under `~/.cache/huggingface/`.

---

## Output formats

| File | Always written | Trigger |
|---|---|---|
| `output/<name>.txt` | yes | always |
| `output/<name>.srt` | no | `--save-srt` or settings |
| `output/<name>.json` | no | `--save-json` or settings |

The `.json` form contains the full segment list and detected language.

---

## Configuration

Settings are persisted at `~/.auto-transcribe/settings.json` and look like:

```json
{
  "input_dir": "/abs/path/auto-transcribe/input",
  "output_dir": "/abs/path/auto-transcribe/output",
  "model": "mlx-community/whisper-large-v3-turbo",
  "language": "auto",
  "save_srt": false,
  "save_json": false,
  "state_dir": "/abs/path/auto-transcribe/.state"
}
```

Override the location with `AUTO_TRANSCRIBE_SETTINGS=/some/other.json`. CLI flags (`--input`, `--output`, `--model`, `--language`, `--save-srt`, `--save-json`) override and persist back.

The dedupe state (sha1 of `path + size + mtime` per processed file) lives in `.state/state.json` inside the project (gitignored).

---

## Architecture

```
input/   --watcher-->   queue   -->   pipeline   -->   output/
   ^                                    |   |
   |                                    v   v
 dropped                          ffmpeg   engine (MLX Whisper / Parakeet)
 by user                          (16k mono wav)
```

- **`pipeline.py`** — decode with ffmpeg to a 16 kHz mono WAV (in a temp dir), feed it to the chosen engine, write outputs, mark done.
- **`queue.py`** — single background thread that consumes one job at a time, emitting progress events to listeners (UI / CLI logger).
- **`watcher.py`** — polls `input/` once a second; when a file's size has been stable for 2 s, it submits the job. (Polling avoids watchdog/Tk threading quirks.)
- **`engines/`** — `Transcriber` protocol with `MLXWhisperEngine` and `ParakeetEngine` implementations; `build_engine(model)` routes by model id.
- **`ui_tk.py`** — the optional Tkinter window.

Per-file state machine:

```
Detected -> Decoding -> Transcribing -> Writing -> Done
                |             |
                +---Failed----+
```

---

## Project layout

```
auto-transcribe/
├── input/                  # drop files here  (contents gitignored)
├── output/                 # transcripts land here  (contents gitignored)
├── ExampleData/            # private test media  (entirely gitignored)
├── scripts/
│   ├── AutoTranscribe.command   # double-click: GUI watcher
│   └── Transcribe.command       # double-click: one-shot batch
├── src/auto_transcribe/
│   ├── cli.py
│   ├── config.py
│   ├── pipeline.py
│   ├── queue.py
│   ├── watcher.py
│   ├── ui_tk.py
│   └── engines/
│       ├── base.py
│       ├── factory.py
│       ├── mlx_whisper.py
│       └── parakeet.py
├── tests/
│   ├── conftest.py
│   ├── test_config.py
│   ├── test_pipeline.py
│   ├── test_watcher.py
│   ├── test_cli.py
│   └── test_e2e.py         # opt-in (RUN_E2E=1)
├── pyproject.toml
├── README.md
├── QUICKSTART.md
└── .gitignore
```

---

## Tests

The suite is split into three tiers:

| Tier | Path | Marker | What runs | Speed |
|---|---|---|---|---|
| Unit | `tests/test_*.py` | (none) | Pure logic + small ffmpeg fixture; engine is faked | ~3 s |
| Integration | `tests/integration/test_*.py` | `integration` | Real ffmpeg pipeline + watcher + queue + CLI; fake engine | ~30 s |
| E2E | `tests/test_e2e.py` | `e2e` | Real MLX model on `ExampleData/`, opt-in | minutes |

```bash
# Full default run (unit + integration), parallel across all cores,
# random order, with coverage gate at 80% and JUnit/HTML reports:
pytest

# Just the integration tier:
pytest tests/integration -m integration

# Full end-to-end sweep over ExampleData/ with the default model:
RUN_E2E=1 pytest -m e2e

# Override e2e model / language:
RUN_E2E=1 E2E_MODEL=mlx-community/whisper-tiny E2E_LANG=ja pytest -m e2e
```

**Plugins in use** (declared in the `dev` extra):
- `pytest-cov` — branch coverage with `--cov-fail-under=80`. Reports written to
  `coverage.xml`, `tests/_reports/htmlcov/`.
- `pytest-xdist` — parallel execution (`-n auto`).
- `pytest-randomly` — randomised test order each run; the seed is printed at
  the top of the output for reproduction.
- `pytest-rerunfailures` — opt-in retries via `@pytest.mark.flaky(reruns=2)`.
- `pytest-timeout` — per-test wall-clock limits.

**Reports & CI:** `.github/workflows/tests.yml` runs the suite on every push/PR
across Python 3.11 and 3.12, uploads `coverage.xml`, the HTML coverage report,
and `tests/_reports/junit.xml` as artifacts, and posts the slowest 10 tests to
the GitHub step summary so test-time regressions are visible.

---

## Troubleshooting

- **"ffmpeg not found on PATH"** — install via `brew install ffmpeg`.
- **`ModuleNotFoundError: No module named '_tkinter'`** — Homebrew Python doesn't bundle Tk. Install it: `brew install python-tk@$(./.venv/bin/python -c 'import sys;print(f"{sys.version_info.major}.{sys.version_info.minor}")')`. The launcher script does this automatically on next run; the CLI also falls back to a headless watcher if Tk is unavailable.
- **First run is slow** — that's the model download (~1.6 GB for `whisper-large-v3-turbo`). It's cached afterwards.
- **Parakeet output is empty / weird** — Parakeet is English-only. Use a Whisper model for other languages.
- **Watcher doesn't pick up a file** — files are debounced for 2 s of stable size to avoid grabbing partially copied data; if you're piping a still-growing file the watcher will wait until it stops growing.
- **Tk window won't open over SSH** — Tk needs a display. Use `--no-ui` for headless watching.
- **Transcript is wrong language** — set `--language ja` (or your target ISO code) instead of `auto`; auto-detection sometimes guesses wrong on noisy openings.
- **"Already done" but I want to re-run** — delete `.state/state.json` (or the matching entry inside it), or change the file's mtime.

---

## FAQ

**Does this send anything to the cloud?**
No. Models are downloaded once from Hugging Face, then everything runs locally.

**Why polling instead of FSEvents/watchdog?**
Polling at 1 Hz is essentially free for a folder of dozens of files and avoids subtle Tk + watchdog threading issues. The transcription cost dwarfs the watcher cost by orders of magnitude.

**Can I run this on a non-Apple machine?**
Not as-is — both engines are MLX-backed. For Linux/Windows you'd swap in `faster-whisper` or `whisper.cpp`. The `Transcriber` protocol in `engines/base.py` makes that a small change.

**Speaker diarization?**
Not in v1.

---

## Releases

Versioning and release notes are automated via
[release-please](https://github.com/googleapis/release-please). Commits to `main`
following [Conventional Commits](https://www.conventionalcommits.org/) drive a
"release PR" that bumps the version (`pyproject.toml`,
`src/auto_transcribe/__init__.py`) and prepends to `CHANGELOG.md`. Merging that
PR cuts a tagged GitHub release.

Section mapping (in `release-please-config.json`):

| Commit type | Changelog section |
|---|---|
| `feat:` | Features |
| `fix:` | Bug Fixes |
| `perf:` | Performance Improvements |
| `deps:` | Dependencies |
| `docs:` | Documentation |
| `refactor:` | Code Refactoring |
| `revert:` | Reverts |
| `test:` / `build:` / `ci:` / `chore:` | hidden from changelog |

Breaking changes (`feat!:` or `BREAKING CHANGE:` footer) trigger a major bump.

## License

MIT.
