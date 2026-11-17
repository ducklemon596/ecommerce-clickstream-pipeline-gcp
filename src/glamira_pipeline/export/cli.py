"""CLIs: ``export-avro`` (MongoDB → Avro parts) and ``write-raw-schemas`` (committed schema files)."""
from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path
import signal
import sys

from pymongo.errors import PyMongoError

from glamira_pipeline.config import PROJECT_ROOT
from glamira_pipeline.export.exporter import ExportError, ExportInterrupted, ExportOptions, export_table, \
    verify_export, write_schema_files
from glamira_pipeline.export.pii import hasher_from_env
from glamira_pipeline.export.tables import TABLES
from glamira_pipeline.mongo import client_from_env

EXIT_FAILED, EXIT_INTERRUPTED = 1, 130
SCHEMA_DIR = PROJECT_ROOT / "schemas" / "raw"


class _StopFlag:
    """Set by SIGINT/SIGTERM/SIGHUP; the export stops at the next document."""

    def __init__(self) -> None:
        self.stopped = False
        for name in ("SIGINT", "SIGTERM", "SIGHUP"):
            if hasattr(signal, name):
                signal.signal(getattr(signal, name), self._handle)

    def _handle(self, signum: int, frame: object) -> None:
        self.stopped = True

    def __call__(self) -> bool:
        return self.stopped


def export_main() -> None:
    """Export raw-layer tables from MongoDB into Avro files ready for GCS and BigQuery."""
    parser = argparse.ArgumentParser(description=export_main.__doc__)
    parser.add_argument("--table", action="append", choices=[*TABLES, "all"], required=True,
                        help="table to export; repeat the option or use 'all'")
    parser.add_argument("--output-dir", type=Path, required=True,
                        help="export root; each table gets a new subdirectory (an existing one is refused)")
    parser.add_argument("--database", default="countly")
    parser.add_argument("--limit", type=int, help="export only the first N documents (non-random sample)")
    parser.add_argument("--rows-per-file", type=int, default=1_000_000)
    parser.add_argument("--no-verify", dest="verify", action="store_false",
                        help="skip re-reading the parts after writing")
    args = parser.parse_args()
    if args.limit is not None and args.limit < 1 or args.rows_per_file < 1:
        parser.error("--limit and --rows-per-file must be positive")
    names = list(TABLES) if "all" in args.table else list(dict.fromkeys(args.table))
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    options = ExportOptions(rows_per_file=args.rows_per_file, limit=args.limit)
    stop = _StopFlag()
    results = []
    try:
        hasher = hasher_from_env()
        with client_from_env() as client:
            database = client[args.database]
            for name in names:
                table = TABLES[name]
                manifest = export_table(table, database[table.source_collection], args.output_dir,
                                        hasher, options, stop)
                summary = {k: manifest[k] for k in ("table", "rows", "bytes", "seconds", "conversions")}
                if args.verify:
                    summary["verified"] = verify_export(args.output_dir / name)
                results.append(summary)
    except ExportInterrupted as exc:
        parser.exit(EXIT_INTERRUPTED, f"{exc}\n")
    except (ValueError, ExportError, PyMongoError, OSError) as exc:
        parser.exit(EXIT_FAILED, f"export failed ({type(exc).__name__}): {exc}\n")
    print(json.dumps(results, indent=2))


def schemas_main() -> None:
    """Write the Avro and BigQuery schema of every raw table (default: schemas/raw)."""
    parser = argparse.ArgumentParser(description=schemas_main.__doc__)
    parser.add_argument("--output-dir", type=Path, default=SCHEMA_DIR)
    args = parser.parse_args()
    for table in TABLES.values():
        write_schema_files(table, args.output_dir)
    sys.stdout.write(f"wrote {len(TABLES) * 2} schema files to {args.output_dir}\n")
