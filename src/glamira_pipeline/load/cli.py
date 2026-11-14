"""CLIs: ``load-summary`` (resumable bulk load) and ``reconcile-summary`` (read-only checks)."""
from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path

from pymongo.errors import PyMongoError

from glamira_pipeline.load.bson_stream import DEFAULT_MEMBER
from glamira_pipeline.load.checkpoint import RunLocked
from glamira_pipeline.load.loader import LoadError, LoadInterrupted, LoadOptions, load_summary
from glamira_pipeline.load.reconcile import reconcile
from glamira_pipeline.mongo import client_from_env

EXIT_FAILED, EXIT_LOCKED, EXIT_MISMATCH, EXIT_INTERRUPTED = 1, 2, 3, 130


def _common(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--archive", type=Path, required=True, help=".tar.gz mongodump archive")
    parser.add_argument("--member", default=DEFAULT_MEMBER, help="BSON file inside the archive")
    parser.add_argument("--database", required=True)
    parser.add_argument("--collection", required=True)
    parser.add_argument("--no-pigz", dest="pigz", action="store_const", const=False, default=None,
                        help="decompress with Python's tarfile even if pigz is installed")


def _summary(run: dict) -> str:
    keep = ("_id", "status", "progress", "metrics", "error")
    return json.dumps({k: run.get(k) for k in keep}, default=str, indent=2)


def load_main() -> None:
    """Stream a BSON dump member into MongoDB in parallel batches; rerun the same command to resume."""
    parser = argparse.ArgumentParser(description=load_main.__doc__)
    _common(parser)
    parser.add_argument("--workers", type=int, default=4, help="insert threads (1-16)")
    parser.add_argument("--batch-docs", type=int, default=1_000, help="documents per insert_many")
    parser.add_argument("--validator", choices=("warn", "off"), default="warn",
                        help="schema validator for a newly created target")
    args = parser.parse_args()
    if not 1 <= args.workers <= 16 or args.batch_docs < 1:
        parser.error("--workers must be 1-16 and --batch-docs positive")
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    options = LoadOptions(workers=args.workers, batch_docs=args.batch_docs, pigz=args.pigz,
                          validator=args.validator)
    try:
        with client_from_env() as client:
            run = load_summary(args.archive, args.member, client[args.database], args.collection, options)
    except ValueError as exc:
        parser.exit(EXIT_FAILED, f"load failed: {exc}\n")
    except RunLocked as exc:
        parser.exit(EXIT_LOCKED, f"{exc}\n")
    except LoadInterrupted as exc:
        parser.exit(EXIT_INTERRUPTED, f"{exc}\n")
    except (LoadError, PyMongoError, OSError, RuntimeError) as exc:
        parser.exit(EXIT_FAILED, f"load failed ({type(exc).__name__}): {exc}\n")
    print(_summary(run))


def reconcile_main() -> None:
    """Compare a loaded collection with its source dump: totals, per-event-type counts, sampled content."""
    parser = argparse.ArgumentParser(description=reconcile_main.__doc__)
    _common(parser)
    parser.add_argument("--sample-size", type=int, default=1_000)
    parser.add_argument("--seed", type=int, default=20191001)
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    try:
        with client_from_env() as client:
            result = reconcile(args.archive, args.member, client[args.database], args.collection,
                               sample_size=args.sample_size, seed=args.seed, pigz=args.pigz)
    except (ValueError, PyMongoError, OSError, RuntimeError) as exc:
        parser.exit(EXIT_FAILED, f"reconciliation failed ({type(exc).__name__}): {exc}\n")
    print(json.dumps(result, default=str, indent=2))
    if not result["ok"]:
        parser.exit(EXIT_MISMATCH, "reconciliation found differences\n")
