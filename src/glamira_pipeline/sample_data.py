"""Bounded BSON sample reading for local profiling."""
from __future__ import annotations

from itertools import islice
from pathlib import Path
from typing import Any, Iterator

from bson import decode_file_iter

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_SAMPLE = PROJECT_ROOT / "data/summary_sample.bson"
DEFAULT_REPORT_DIR = PROJECT_ROOT / "docs/reports"


def iter_sample_documents(path: Path) -> Iterator[dict[str, Any]]:
    """Yield BSON documents from a small extracted sample."""
    if not path.is_file():
        raise FileNotFoundError(
            f"Sample not found: {path}. Run `uv run extract-sample --limit 10000` first."
        )
    with path.open("rb") as stream:
        yield from decode_file_iter(stream)


def read_sample(path: Path = DEFAULT_SAMPLE, limit: int = 100_000) -> list[dict[str, Any]]:
    """Read at most ``limit`` documents, keeping profiling memory bounded."""
    if limit < 1:
        raise ValueError("Document limit must be at least 1")
    return list(islice(iter_sample_documents(path), limit))
