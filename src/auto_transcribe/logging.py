"""Structured logging for auto-transcribe.

Wraps loguru with a path-redaction patcher so private filesystem paths
(the user's home directory and ``ExampleData/`` contents) never leak
verbatim into log files. The stderr sink is human-readable and colorized;
an optional rotating file sink at
``~/.auto-transcribe/logs/auto-transcribe.log`` emits structured JSON.

Configuration is idempotent: the first import of the package configures
the logger once. Re-imports become no-ops.
"""

from __future__ import annotations

import os
import re
import sys
from pathlib import Path
from typing import Any

from loguru import logger as _logger

__all__ = ["LOG_DIR", "configure_logging", "get_logger", "redact_paths"]


def _resolve_log_dir() -> Path:
    return Path(
        os.environ.get(
            "AUTO_TRANSCRIBE_LOG_DIR",
            str(Path.home() / ".auto-transcribe" / "logs"),
        )
    )


LOG_DIR = _resolve_log_dir()

_HOME_RE = re.compile(re.escape(str(Path.home())))
_EXAMPLE_DATA_RE = re.compile(r"(ExampleData/)([^/\s\"']+)")


def _redact_text(text: str) -> str:
    text = _HOME_RE.sub("<home>", text)
    return _EXAMPLE_DATA_RE.sub(lambda m: f"{m.group(1)}<redacted>", text)


def redact_paths(record: Any) -> None:
    """Loguru patcher: scrub home dir and ExampleData paths from messages."""
    record["message"] = _redact_text(record["message"])


_state: dict[str, bool] = {"configured": False}


def configure_logging(*, file_logging: bool = False) -> None:
    """Install the stderr sink (always) and the rotating file sink (opt-in).

    File logging is OFF by default so importing the package in tests / one-off
    scripts never touches the user's home dir. The CLI entry point opts in.

    Safe to call repeatedly; only the first call has effect.
    """
    if _state["configured"]:
        return

    _logger.remove()
    _logger.add(
        sys.stderr,
        level=os.environ.get("AUTO_TRANSCRIBE_LOG_LEVEL", "INFO"),
        format=(
            "<green>{time:HH:mm:ss}</green> "
            "<level>{level: <7}</level> "
            "<cyan>{extra[name]}</cyan>: {message}"
        ),
        colorize=True,
        backtrace=False,
        diagnose=False,
    )

    if file_logging:
        try:
            LOG_DIR.mkdir(parents=True, exist_ok=True)
            _logger.add(
                LOG_DIR / "auto-transcribe.log",
                level="DEBUG",
                rotation="10 MB",
                retention="7 days",
                serialize=True,
            )
        except OSError:
            pass

    _logger.configure(extra={"name": "auto_transcribe"}, patcher=redact_paths)
    _state["configured"] = True


def get_logger(name: str) -> Any:
    """Return a logger bound to a logical component name (module-style)."""
    if not _state["configured"]:
        configure_logging()
    return _logger.bind(name=name)
