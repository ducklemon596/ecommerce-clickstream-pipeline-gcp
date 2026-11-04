"""Local sample seeding and Counter 50K enrichment commands."""
from __future__ import annotations
import argparse
import os
from pathlib import Path
from bson.errors import BSONError
from pymongo.errors import PyMongoError
from glamira_pipeline.config import DEFAULT_SAMPLE, PROJECT_ROOT
from glamira_pipeline.ip_location.source import MAX_SAMPLE, local_client, seed_sample
from glamira_pipeline.ip_location.pipeline import enrich_collection

DEFAULT_DATABASE = "glamira_ip_sample"


def _database_name(value: str) -> str:
    """Validate an isolated sample database name before seeding any records."""
    if value != DEFAULT_DATABASE and not value.startswith(DEFAULT_DATABASE + "_"):
        raise argparse.ArgumentTypeError("use glamira_ip_sample or a glamira_ip_sample_ prefix")
    return value


def _client():
    """Return the configured loopback URI and a managed MongoDB client."""
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
    """Enrich MongoDB IPs using an unsorted Counter scan with batch size 50K."""
    parser = argparse.ArgumentParser(description=enrich_main.__doc__)
    parser.add_argument("--database", default=DEFAULT_DATABASE)
    parser.add_argument("--source", default="events")
    parser.add_argument("--target", default="ip_locations")
    parser.add_argument("--bin", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--limit", type=int, help="Positive event limit for a non-random sample")
    args = parser.parse_args()
    if args.limit is not None and args.limit < 1:
        parser.error("--limit must be positive")
    try:
        _, client = _client()
        with client:
            summary = enrich_collection(client[args.database][args.source], args.target,
                                        args.bin, args.output_dir, limit=args.limit)
        print(f"Processed {summary['events']:,} events; {summary['unique_valid_ips']:,} unique valid IPs")
        print(f"Event coverage: {summary['event_coverage_percent']:.2f}%")
    except (OSError, ValueError, TypeError, BSONError, PyMongoError) as exc:
        parser.exit(1, f"IP enrichment failed ({type(exc).__name__}); inspect private staging artifacts.\n")
