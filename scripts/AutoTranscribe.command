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

if ! ./.venv/bin/python -c "import tkinter" >/dev/null 2>&1; then
  PYVER="$(./.venv/bin/python -c 'import sys;print(f"{sys.version_info.major}.{sys.version_info.minor}")')"
  echo "tkinter is missing from this Python build."
  if command -v brew >/dev/null 2>&1; then
    echo "Installing python-tk@${PYVER} via Homebrew..."
    brew install "python-tk@${PYVER}" || true
  else
    echo "Install Tk for Python ${PYVER} (e.g. via Homebrew: brew install python-tk@${PYVER}),"
    echo "or use a Python distribution that ships Tk."
  fi
fi

exec ./.venv/bin/python -m auto_transcribe "$@"
