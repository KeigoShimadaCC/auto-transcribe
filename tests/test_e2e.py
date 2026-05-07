from __future__ import annotations

import json
import os
import time
from pathlib import Path

import pytest

from auto_transcribe.config import DEFAULT_MODEL, Settings
from auto_transcribe.pipeline import is_supported, transcribe_file

pytestmark = pytest.mark.e2e


@pytest.fixture(scope="session")
def reports_dir() -> Path:
    p = Path(__file__).resolve().parent / "_reports"
    p.mkdir(exist_ok=True)
    return p


def _e2e_enabled() -> bool:
    return os.environ.get("RUN_E2E") == "1"


@pytest.mark.skipif(not _e2e_enabled(), reason="set RUN_E2E=1 to run")
def test_e2e_example_data(example_data_dir: Path, tmp_path: Path, reports_dir: Path) -> None:
    files = sorted([p for p in example_data_dir.iterdir() if is_supported(p)])
    assert files, "ExampleData/ has no supported media files"

    settings = Settings(
        input_dir=str(example_data_dir),
        output_dir=str(tmp_path / "output"),
        state_dir=str(tmp_path / ".state"),
        model=os.environ.get("E2E_MODEL", DEFAULT_MODEL),
        language=os.environ.get("E2E_LANG", "ja"),
    )
    Path(settings.output_dir).mkdir(parents=True, exist_ok=True)

    report: list[dict] = []
    for src in files:
        t0 = time.time()
        result = transcribe_file(src, settings)
        elapsed = time.time() - t0
        txt = result.outputs["txt"].read_text()
        assert txt.strip(), f"{src.name} produced empty transcript"
        rtf = None
        if result.duration_audio:
            rtf = elapsed / result.duration_audio
        report.append(
            {
                "file": src.name,
                "elapsed_s": round(elapsed, 2),
                "audio_s": result.duration_audio,
                "rtf": rtf,
                "chars": len(txt),
                "language": result.language,
            }
        )

    out = reports_dir / "e2e_report.json"
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2))
