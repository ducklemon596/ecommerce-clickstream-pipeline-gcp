"""Profile field presence, nulls and BSON types per event type from a random MongoDB sample."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import logging
from pathlib import Path
import time

from pymongo.errors import PyMongoError

from glamira_pipeline.config import DEFAULT_REPORT_DIR, PROJECT_ROOT
from glamira_pipeline.mongo import client_from_env
from glamira_pipeline.profiling.report import write_outputs
from glamira_pipeline.profiling.schema import SchemaProfile
from glamira_pipeline.provenance import git_sha, mongo_collection_identity
from glamira_pipeline.sampling.mongo_sample import MAX_SAMPLE, sample_documents, uses_random_cursor

log = logging.getLogger(__name__)
PROGRESS_EVERY = 50_000


def main() -> None:
    """Sample the collection with ``$sample``, profile it and write Markdown + JSON."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database", default="countly")
    parser.add_argument("--collection", default="summary")
    parser.add_argument("--size", type=int, default=100_000, help=f"Documents to sample (1–{MAX_SAMPLE:,})")
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT_DIR / "schema_profile.md")
    parser.add_argument("--json", type=Path, default=PROJECT_ROOT / "data/profiling/schema_profile.json",
                        help="Machine-readable counts (no field values)")
    args = parser.parse_args()
    if not 1 <= args.size <= MAX_SAMPLE:
        parser.error(f"--size must be between 1 and {MAX_SAMPLE:,}")
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    try:
        client = client_from_env()
    except ValueError as exc:
        parser.error(str(exc))
    try:
        with client:
            collection = client[args.database][args.collection]
            estimate = collection.estimated_document_count()
            if not uses_random_cursor(args.size, estimate):
                parser.exit(2, f"--size {args.size:,} is not below 5% of ~{estimate:,} documents; "
                               "$sample would scan and sort the whole collection. Use a smaller size.\n")
            identity = mongo_collection_identity(collection)
            observed_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
            started = time.monotonic()
            profile = SchemaProfile()
            for document in sample_documents(collection, args.size):
                profile.observe(document)
                if profile.documents % PROGRESS_EVERY == 0:
                    log.info("profiled %s documents", f"{profile.documents:,}")
            elapsed = time.monotonic() - started
    except PyMongoError as exc:
        parser.exit(1, f"Schema profiling failed ({type(exc).__name__}); check the tunnel and permissions.\n")

    metadata = {
        "namespace": identity["namespace"], "collection_uuid": identity["uuid"],
        "observed_at": observed_at, "requested": args.size, "collection_estimate": estimate,
        "method": f"MongoDB `$sample` (size {args.size:,}, pseudo-random cursor, no seed; "
                  "documents may repeat and runs are not reproducible).",
        "elapsed_s": round(elapsed, 1), "git_sha": git_sha(),
    }
    write_outputs(profile, metadata, args.report, args.json)
    log.info("profiled %s documents across %d event types in %.1f s",
             f"{profile.documents:,}", len(profile.types), elapsed)
    print(f"Wrote {args.report}\nWrote {args.json}")


if __name__ == "__main__":
    main()
