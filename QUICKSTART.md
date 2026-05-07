# Quickstart

Get from "fresh clone" to "first transcript" in under five minutes.

## 1. Prerequisites

- Apple Silicon Mac (M1/M2/M3/M4)
- Python 3.10+ (`python3 --version`)
- `ffmpeg` (`brew install ffmpeg` if missing)

## 2. Get the code

```bash
git clone https://github.com/KeigoShimadaCC/auto-transcribe.git
cd auto-transcribe
```

## 3. First run (one of three flavors)

### A. Easiest — double-click

Open the project folder in Finder, then double-click:

- `scripts/AutoTranscribe.command` — opens the GUI watcher
- `scripts/Transcribe.command` — one-shot batch over `input/`

The first launch takes a minute: it builds a `.venv`, installs dependencies, and downloads the default model (~1.6 GB).

> If macOS blocks the script with "cannot be opened because the developer cannot be verified", right-click → **Open** → **Open** once. After that it runs normally.

### B. CLI — watcher with UI

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -e ".[parakeet]"

python -m auto_transcribe
```

### C. CLI — one-shot, headless

```bash
python -m auto_transcribe --once
```

## 4. Try it

Drag any audio or video file into `input/`:

```bash
cp ~/Movies/some_talk.mp4 input/
```

Within a second or two the queue picks it up. When it finishes you'll find:

```
output/some_talk.txt
```

## 5. Pick a model

| Need | Model |
|---|---|
| Best quality, multilingual (default) | `mlx-community/whisper-large-v3-turbo` |
| Fastest English-only | `mlx-community/parakeet-tdt-0.6b-v2` |
| Smoke test / tiny | `mlx-community/whisper-tiny` |

Either change it in the UI dropdown or pass `--model <id>` on the CLI.

## 6. Common one-liners

```bash
# Transcribe one specific file with subtitles + json
python -m auto_transcribe --once --save-srt --save-json path/to/lecture.mp4

# Force Japanese
python -m auto_transcribe --once --language ja

# Use the speed-king for English
python -m auto_transcribe --once \
  --model mlx-community/parakeet-tdt-0.6b-v2 --language en

# Watch a different folder
python -m auto_transcribe --input ~/Downloads --output ~/Transcripts
```

## 7. Run the tests (optional)

```bash
pip install -e ".[dev]"
pytest                          # ~3 s, fake engine + real ffmpeg
RUN_E2E=1 pytest -m e2e         # full sweep over ExampleData/ (slow)
```

## 8. Where things live

| Path | What |
|---|---|
| `input/` | drop zone (contents gitignored) |
| `output/` | transcripts (contents gitignored) |
| `ExampleData/` | private test media (entirely gitignored) |
| `~/.auto-transcribe/settings.json` | persisted settings |
| `.state/state.json` | dedupe state for already-transcribed files |
| `~/.cache/huggingface/` | downloaded models |

## 9. Stuck?

See **Troubleshooting** in [README.md](./README.md#troubleshooting).
