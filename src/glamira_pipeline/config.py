"""Portable local paths and bounded sample defaults."""
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_ARCHIVE = PROJECT_ROOT / "glamira_ubl_oct2019_nov2019.tar.gz"
DEFAULT_SAMPLE = PROJECT_ROOT / "data/summary_sample.json"
DEFAULT_REPORT_DIR = PROJECT_ROOT / "docs/reports"
MAX_DOCUMENTS = 100_000
