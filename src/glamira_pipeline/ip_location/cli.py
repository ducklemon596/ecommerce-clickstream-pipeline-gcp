"""Command-line entry points for the local IP geolocation sample."""
from __future__ import annotations

import argparse
import logging
import os
from pathlib import Path
import sqlite3

from bson.errors import BSONError
from pymongo.errors import PyMongoError

from glamira_pipeline.config import DEFAULT_SAMPLE, PROJECT_ROOT
from glamira_pipeline.ip_location.pipeline import enrich_sample
from glamira_pipeline.ip_location.full_pipeline import enrich_full_collection
from glamira_pipeline.ip_location.source import MAX_SAMPLE, local_client, seed_sample

DEFAULT_DATABASE = "glamira_ip_sample"
DEFAULT_OUTPUT = PROJECT_ROOT / "data" / "ip_location_sample"
DEFAULT_BIN = PROJECT_ROOT / "IP-COUNTRY-REGION-CITY.BIN"


def _database_name(value: str) -> str:
    """Accept only dedicated local sample database names for destructive safety."""
    if value != DEFAULT_DATABASE and not value.startswith(DEFAULT_DATABASE + "_"):
        raise argparse.ArgumentTypeError("database must be glamira_ip_sample or start with glamira_ip_sample_")
    return value


def _data_path(value: str) -> Path:
    """Keep generated IP data inside the repository's ignored data directory."""
    path = Path(value).expanduser().resolve()
    if not path.is_relative_to((PROJECT_ROOT / "data").resolve()):
        raise argparse.ArgumentTypeError("generated IP files must be under the ignored data/ directory")
    return path


def _client():
    """Open a local MongoDB client using the optional MONGODB_URI environment variable."""
    uri = os.environ.get("MONGODB_URI", "mongodb://127.0.0.1:27017/")
    return uri, local_client(uri)


def seed_main() -> None:
    """Seed the isolated local MongoDB database from a bounded JSON sample."""
    parser = argparse.ArgumentParser(description=seed_main.__doc__)
    parser.add_argument("--sample", type=Path, default=DEFAULT_SAMPLE)
    parser.add_argument("--limit", type=int, default=1_000)
    parser.add_argument("--database", type=_database_name, default=DEFAULT_DATABASE)
    args = parser.parse_args()
    if not 1 <= args.limit <= MAX_SAMPLE:
        parser.error(f"limit must be between 1 and {MAX_SAMPLE}")
    try:
        _, client = _client()
        with client:
            identity = seed_sample(client[args.database], args.sample, args.limit)
        print(f"Seeded {identity['limit']:,} events into {args.database}.events (sequential sample)")
    except (OSError, ValueError, TypeError, BSONError, PyMongoError) as exc:
        parser.exit(1, f"Sample seed failed ({type(exc).__name__}); check local MongoDB and sample configuration.\n")


def enrich_main() -> None:
    """Enrich the local MongoDB sample with the offline IP2Location BIN."""
    parser = argparse.ArgumentParser(description=enrich_main.__doc__)
    parser.add_argument("--database", type=_database_name, default=DEFAULT_DATABASE)
    parser.add_argument("--sample", type=Path, default=DEFAULT_SAMPLE)
    parser.add_argument("--bin", type=Path, default=DEFAULT_BIN)
    parser.add_argument("--output-dir", type=_data_path, default=DEFAULT_OUTPUT)
    parser.add_argument("--checkpoint", type=_data_path, default=None)
    parser.add_argument("--retry-failed", action="store_true", help="Retry previously failed BIN lookups")
    args = parser.parse_args()
    checkpoint = args.checkpoint or args.output_dir / "checkpoint.sqlite3"
    try:
        uri, client = _client()
        with client:
            summary = enrich_sample(client[args.database], uri, args.sample, args.bin, checkpoint, args.output_dir, retry_failed=args.retry_failed)
        print(f"Processed {summary['events']:,} events and {summary['unique_ips']:,} unique valid IPs")
        print(f"Event coverage: {summary['event_coverage_percent']:.2f}%; unique-IP coverage: {summary['unique_ip_coverage_percent']:.2f}%")
        print(f"Wrote private CSV, checkpoint and aggregate reports to {args.output_dir}")
    except (OSError, ValueError, TypeError, BSONError, sqlite3.Error, PyMongoError) as exc:
        parser.exit(1, f"IP enrichment failed ({type(exc).__name__}); check the local inputs and checkpoint.\n")


def enrich_full_main() -> None:
    """Enrich a complete MongoDB collection using a disk-backed checkpoint."""
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    parser = argparse.ArgumentParser(description=enrich_full_main.__doc__)
    parser.add_argument("--database", default="countly")
    parser.add_argument("--source", default="summary")
    parser.add_argument("--target", default="ip_locations")
    parser.add_argument("--bin", type=Path, required=True)
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--retry-failed", action="store_true")
    args = parser.parse_args()
    if args.source == args.target:
        parser.error("source and target collections must differ")
    uri = os.environ.get("MONGODB_URI")
    if not uri:
        parser.error("set MONGODB_URI through a protected environment/configuration")
    try:
        client = local_client(uri)
        with client:
            database = client[args.database]
            summary = enrich_full_collection(
                database[args.source], database[args.target], args.bin,
                args.checkpoint, args.output_dir, retry_failed=args.retry_failed,
            )
        print(f"Processed {summary['events']:,} events and {summary['unique_ips']:,} unique valid IPs")
        print(f"Event coverage: {summary['event_coverage_percent']:.2f}%; unique-IP coverage: {summary['unique_ip_coverage_percent']:.2f}%")
        print(f"Wrote results and checkpoint under {args.output_dir}")
    except (OSError, ValueError, TypeError, BSONError, sqlite3.Error, PyMongoError) as exc:
        parser.exit(1, f"Full IP enrichment failed ({type(exc).__name__}); check inputs and checkpoint.\n")
