"""CLIs: ``export-avro`` (MongoDB → Avro parts), ``verify-export`` (check a finished export) and
``write-raw-schemas`` (committed schema files)."""
from __future__ import annotations

import argparse
import json
import logging
import os
from pathlib import Path
import re
import signal
import sys

from pymongo.errors import PyMongoError

from glamira_pipeline.config import PROJECT_ROOT
from glamira_pipeline.export.exporter import ExportError, ExportInterrupted, ExportOptions, export_table, \
    write_schema_files
from glamira_pipeline.export.pii import hasher_from_env
from glamira_pipeline.export.state import StateError
from glamira_pipeline.export.tables import TABLES
from glamira_pipeline.export.verify import VerificationError, table_directories, verify_table
from glamira_pipeline.mongo import client_from_env

EXIT_FAILED, EXIT_INTERRUPTED = 1, 130
SCHEMA_DIR = PROJECT_ROOT / "schemas" / "raw"
EXPORT_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$")


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
    """Export raw-layer tables from MongoDB into Avro files ready for GCS and BigQuery.

    Rerunning the same command resumes the export: committed chunks are
    verified and skipped, and only uncommitted work is redone.
    """
    parser = argparse.ArgumentParser(description=export_main.__doc__)
    parser.add_argument("--table", action="append", choices=[*TABLES, "all"], required=True,
                        help="table to export; repeat the option or use 'all'")
    parser.add_argument("--output-dir", type=Path, required=True, help="export root directory")
    parser.add_argument("--export-id", required=True,
                        help="name of this export, e.g. 2026-11-17; files go to <output-dir>/<export-id>/<table>, "
                             "and rerunning with the same ID resumes")
    parser.add_argument("--database", default="countly")
    parser.add_argument("--limit", type=int, help="export only the first N documents by _id (non-random sample)")
    parser.add_argument("--rows-per-file", type=int, default=1_000_000)
    parser.add_argument("--workers", type=int, default=1,
                        help="processes exporting chunks in parallel (default 1); leave a core for mongod")
    args = parser.parse_args()
    if args.limit is not None and args.limit < 1 or args.rows_per_file < 1:
        parser.error("--limit and --rows-per-file must be positive")
    if not 1 <= args.workers <= (os.cpu_count() or 1):
        parser.error(f"--workers must be between 1 and {os.cpu_count()}")
    if not EXPORT_ID.match(args.export_id):
        parser.error("--export-id must be 1-64 letters, digits, '.', '_' or '-'")
    export_dir = args.output_dir / args.export_id
    names = list(TABLES) if "all" in args.table else list(dict.fromkeys(args.table))
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    options = ExportOptions(rows_per_file=args.rows_per_file, limit=args.limit, workers=args.workers)
    stop = _StopFlag()
    results = []
    try:
        hasher = hasher_from_env()
        with client_from_env() as client:
            database = client[args.database]
            for name in names:
                table = TABLES[name]
                manifest = export_table(table, database[table.source_collection], export_dir,
                                        hasher, options, stop, connect=client_from_env)
                results.append({k: manifest.get(k) for k in ("table", "rows", "bytes", "content_sha256", "workers",
                                                         "wall_seconds", "seconds", "conversions")})
    except ExportInterrupted as exc:
        parser.exit(EXIT_INTERRUPTED, f"{exc}\n")
    except (ValueError, ExportError, StateError, PyMongoError, OSError) as exc:
        parser.exit(EXIT_FAILED, f"export failed ({type(exc).__name__}): {exc}\n")
    print(json.dumps(results, indent=2))


def verify_main() -> None:
    """Check a finished export against its manifests and the committed schemas, without decoding rows."""
    parser = argparse.ArgumentParser(description=verify_main.__doc__)
    parser.add_argument("directory", type=Path,
                        help="a table export directory, or an export directory holding several tables")
    parser.add_argument("--full", action="store_true",
                        help="also decode every record (slow; to test the Avro library, e.g. after an upgrade)")
    parser.add_argument("--schema-dir", type=Path, default=SCHEMA_DIR, help="committed Avro schemas")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    try:
        results = [verify_table(directory, args.schema_dir, full=args.full)
                   for directory in table_directories(args.directory)]
    except (VerificationError, OSError, ValueError, KeyError) as exc:
        parser.exit(EXIT_FAILED, f"verification failed ({type(exc).__name__}): {exc}\n")
    print(json.dumps([vars(result) for result in results], indent=2))


def schemas_main() -> None:
    """Write the Avro and BigQuery schema of every raw table (default: schemas/raw)."""
    parser = argparse.ArgumentParser(description=schemas_main.__doc__)
    parser.add_argument("--output-dir", type=Path, default=SCHEMA_DIR)
    args = parser.parse_args()
    for table in TABLES.values():
        write_schema_files(table, args.output_dir)
    sys.stdout.write(f"wrote {len(TABLES) * 2} schema files to {args.output_dir}\n")
