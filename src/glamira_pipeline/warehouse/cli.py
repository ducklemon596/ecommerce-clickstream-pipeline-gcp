"""CLIs: ``publish-export`` (verified export → GCS) and ``load-bigquery`` (load spec → BigQuery, by hand)."""
from __future__ import annotations

import argparse
from dataclasses import asdict
import json
import logging
from pathlib import Path

from google.api_core.exceptions import GoogleAPICallError

from glamira_pipeline.config import PROJECT_ROOT
from glamira_pipeline.export.verify import VerificationError, table_directories
from glamira_pipeline.warehouse.bigquery import LoadError, TransientLoadError
from glamira_pipeline.warehouse.publish import PublishError, publish_table
from glamira_pipeline.warehouse.runner import process_load_spec
from glamira_pipeline.warehouse.spec import LOAD_SPEC, LoadSpecError

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
    parser.add_argument("--dataset", default="glamira_raw",
                        help="BigQuery dataset the load spec targets (default: glamira_raw)")
    parser.add_argument("--workers", type=int, default=4, help="parallel part uploads (default 4)")
    parser.add_argument("--schema-dir", type=Path, default=SCHEMA_DIR, help="committed BigQuery schemas (schemas/raw)")
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


def load_main() -> None:
    """Load one published table into BigQuery from its _load.json, as the Cloud Function does.

    For a first load without the function, or a rerun after fixing a permanent
    failure. Idempotent: the deterministic job ID turns a repeat into a no-op.
    """
    parser = argparse.ArgumentParser(description=load_main.__doc__)
    parser.add_argument("spec", help="gs://<bucket>/<prefix>/<table>/export_id=<id>/_load.json")
    parser.add_argument("--project", help="BigQuery project (default: from the environment)")
    parser.add_argument("--ignore-marker", action="store_true",
                        help="run even if _LOADED.json exists (still no second load of the same export)")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    if not args.spec.startswith("gs://"):
        parser.error("spec must be a gs:// URI")
    bucket_name, _, name = args.spec.removeprefix("gs://").partition("/")
    from google.cloud import bigquery, storage

    try:
        outcome = process_load_spec(storage.Client(), bigquery.Client(project=args.project), bucket_name, name,
                                    ignore_marker=args.ignore_marker)
    except TransientLoadError as exc:
        parser.exit(EXIT_FAILED, f"load not finished, rerun later: {exc}\n")
    except (LoadError, LoadSpecError, GoogleAPICallError) as exc:
        parser.exit(EXIT_FAILED, f"load failed ({type(exc).__name__}): {exc}\n")
    if outcome.status == "ignored":
        parser.exit(EXIT_FAILED, f"{args.spec} does not name a {LOAD_SPEC}\n")
    print(json.dumps(asdict(outcome), indent=2, default=str))
