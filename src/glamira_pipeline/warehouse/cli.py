"""CLI: ``publish-export`` (verified export → GCS)."""
from __future__ import annotations

import argparse
from dataclasses import asdict
import json
import logging
from pathlib import Path

from google.api_core.exceptions import GoogleAPICallError

from glamira_pipeline.config import PROJECT_ROOT
from glamira_pipeline.export.verify import VerificationError, table_directories
from glamira_pipeline.warehouse.publish import PublishError, publish_table

EXIT_FAILED = 1
SCHEMA_DIR = PROJECT_ROOT / "schemas" / "raw"


def publish_main() -> None:
    """Verify a finished export and upload it to GCS; the final _load.json triggers the BigQuery load.

    Safe to rerun: objects already in the bucket with the same CRC32C are skipped.
    """
    parser = argparse.ArgumentParser(description=publish_main.__doc__)
    parser.add_argument("directory", type=Path, help="an export directory, or one table directory in it")
    parser.add_argument("--bucket", required=True, help="target bucket name, without gs://")
    parser.add_argument("--prefix", default="raw", help="object prefix (default: raw)")
    parser.add_argument("--dataset", default="raw", help="BigQuery dataset the load spec targets (default: raw)")
    parser.add_argument("--workers", type=int, default=4, help="parallel part uploads (default 4)")
    parser.add_argument("--schema-dir", type=Path, default=SCHEMA_DIR, help="committed Avro schemas")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    from google.cloud import storage

    try:
        bucket = storage.Client().bucket(args.bucket)
        results = [publish_table(directory, bucket, prefix=args.prefix, dataset=args.dataset,
                                 schema_dir=args.schema_dir, workers=args.workers)
                   for directory in table_directories(args.directory)]
    except (PublishError, VerificationError, GoogleAPICallError, OSError, ValueError, KeyError) as exc:
        parser.exit(EXIT_FAILED, f"publish failed ({type(exc).__name__}): {exc}\n")
    print(json.dumps([asdict(result) for result in results], indent=2))
