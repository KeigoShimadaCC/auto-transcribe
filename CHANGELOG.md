# Changelog

All notable changes to this project will be documented in this file. The format
is maintained automatically by [release-please](https://github.com/googleapis/release-please)
based on [Conventional Commits](https://www.conventionalcommits.org/) in the
git history.

## [0.1.0] - 2026-05-07

### Features

- Local audio/video transcription pipeline (ffmpeg → engine → `.txt`/`.srt`/`.json`).
- Two MLX-backed engines selectable at runtime: `mlx-whisper` (default,
  multilingual) and `parakeet-mlx` (English speed champion).
- Folder watcher with size-stable debounce and sha1 dedupe state.
- Tkinter progress UI with model/language pickers, queue list, and
  "Open output folder" action.
- Double-click launchers (`scripts/AutoTranscribe.command`,
  `scripts/Transcribe.command`) that auto-bootstrap the venv and the
  Homebrew `python-tk@<ver>` Tk binding when missing.
- CLI: `python -m auto_transcribe` with `--once`, `--no-ui`,
  `--save-srt`, `--save-json`, `--model`, `--language`.

### Documentation

- Full `README.md`, `QUICKSTART.md`, and `AGENTS.md` covering install,
  usage, models, configuration, architecture, and contribution guide.

### Tests

- Unit tests for config, pipeline, queue/watcher, and CLI using a fake
  engine and a synthetic ffmpeg-generated WAV.
- Opt-in end-to-end suite (`RUN_E2E=1`) over `ExampleData/` writing a
  per-file timing report.
