"""IP enrichment commands: seed a local test sample and enrich a MongoDB collection."""
from __future__ import annotations

import argparse
import logging
from pathlib import Path

from bson.errors import BSONError
from pymongo import MongoClient
from pymongo.errors import PyMongoError

from glamira_pipeline.config import DEFAULT_SAMPLE
from glamira_pipeline.ip_location.pipeline import enrich_collection
from glamira_pipeline.ip_location.source import MAX_SAMPLE, seed_sample
from glamira_pipeline.mongo import client_from_env

SAMPLE_DATABASE = "glamira_ip_sample"


def _sample_database(value: str) -> str:
    """Accept only isolated sample database names, so seeding never touches real data."""
    if value != SAMPLE_DATABASE and not value.startswith(SAMPLE_DATABASE + "_"):
        raise argparse.ArgumentTypeError(f"use {SAMPLE_DATABASE} or a {SAMPLE_DATABASE}_ prefix")
    return value


def _client(parser: argparse.ArgumentParser) -> MongoClient:
    """Connect with ``MONGODB_URI``; exit with a usage error when it is unset or not loopback."""
    try:
        return client_from_env()
    except ValueError as exc:
        parser.error(str(exc))


def seed_main() -> None:
    """Seed an isolated MongoDB database from a bounded JSON sample (for local tests)."""
    parser = argparse.ArgumentParser(description=seed_main.__doc__)
    parser.add_argument("--sample", type=Path, default=DEFAULT_SAMPLE)
    parser.add_argument("--limit", type=int, default=1_000)
    parser.add_argument("--database", type=_sample_database, default=SAMPLE_DATABASE)
    args = parser.parse_args()
    if not 1 <= args.limit <= MAX_SAMPLE:
        parser.error(f"limit must be between 1 and {MAX_SAMPLE}")
    try:
        with _client(parser) as client:
            identity = seed_sample(client[args.database], args.sample, args.limit)
    except (OSError, ValueError, TypeError, BSONError, PyMongoError) as exc:
        parser.exit(1, f"Sample seed failed ({type(exc).__name__}: {exc}).\n")
    print(f"Seeded {identity['limit']:,} events into {args.database}.events (sequential sample)")


def enrich_main() -> None:
    """Geolocate every event IP of a MongoDB collection into a new collection (offline BIN lookup)."""
    parser = argparse.ArgumentParser(description=enrich_main.__doc__)
    parser.add_argument("--database", default="countly")
    parser.add_argument("--source", default="summary")
    parser.add_argument("--target", default="ip_locations", help="New collection; must not exist")
    parser.add_argument("--bin", type=Path, required=True, help="IP2Location BIN file")
    parser.add_argument("--output-dir", type=Path, required=True, help="New private directory for artifacts")
    parser.add_argument("--limit", type=int, help="Positive event limit for a non-random test prefix")
    args = parser.parse_args()
    if args.limit is not None and args.limit < 1:
        parser.error("--limit must be positive")
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    try:
        with _client(parser) as client:
            summary = enrich_collection(client[args.database][args.source], args.target,
                                        args.bin, args.output_dir, limit=args.limit)
    except (OSError, ValueError, TypeError, BSONError, PyMongoError) as exc:
        # Messages name the failed check; raw IPs never appear in them.
        parser.exit(1, f"IP enrichment failed ({type(exc).__name__}: {exc}); "
                       "staging and artifacts are kept for inspection.\n")
    print(f"Processed {summary['events']:,} events; {summary['unique_valid_ips']:,} unique valid IPs")
    print(f"Event coverage: {summary['event_coverage_percent']:.2f}%")
