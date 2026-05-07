#!/usr/bin/env bash
# Manual one-shot: process all pending files in ./input and exit.
set -euo pipefail
cd "$(dirname "$0")/.."

if [ ! -d ".venv" ]; then
  echo "Setting up virtualenv (first run)..."
  python3 -m venv .venv
  ./.venv/bin/pip install --upgrade pip
  ./.venv/bin/pip install -e ".[parakeet]"
fi

./.venv/bin/python -m auto_transcribe --once "$@"
echo
echo "Done. Press any key to close."
read -n 1 -s -r
