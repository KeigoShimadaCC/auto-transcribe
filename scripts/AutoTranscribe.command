#!/usr/bin/env bash
# Launch the watcher + Tk UI. Drop files into ./input and they get transcribed.
set -euo pipefail
cd "$(dirname "$0")/.."

if [ ! -d ".venv" ]; then
  echo "Setting up virtualenv (first run)..."
  python3 -m venv .venv
  ./.venv/bin/pip install --upgrade pip
  ./.venv/bin/pip install -e ".[parakeet]"
fi

exec ./.venv/bin/python -m auto_transcribe "$@"
