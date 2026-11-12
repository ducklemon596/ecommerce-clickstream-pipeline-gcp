"""Product configuration deduplication CLI for local JSON and VM MongoDB."""
import argparse
import logging
import os
from pathlib import Path
import sqlite3

from pymongo import MongoClient
from pymongo.errors import PyMongoError
from glamira_pipeline.products.pipeline import run_deduplication


def main() -> None:
    """Parse source and runtime settings; exit nonzero without logging raw events."""
    parser = argparse.ArgumentParser(description=__doc__)
    inputs = parser.add_mutually_exclusive_group(required=True)
    inputs.add_argument("--sample", type=Path, help="Local Extended JSON array")
    inputs.add_argument("--mongo", action="store_true", help="Read MONGODB_URI from protected environment")
    parser.add_argument("--database", default="countly")
    parser.add_argument("--collection", default="summary")
    parser.add_argument("--limit", type=int, help="Exact maximum source documents before event filtering")
    parser.add_argument("--batch-size", type=int, default=5000)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    try:
        settings = {"limit": args.limit, "batch_size": args.batch_size}
        if args.sample is not None:
            summary = run_deduplication(args.output_dir, sample=args.sample, **settings)
        else:
            uri = os.environ.get("MONGODB_URI")
            if not uri:
                parser.error("set MONGODB_URI in the environment")
            with MongoClient(uri, serverSelectionTimeoutMS=10000) as client:
                summary = run_deduplication(args.output_dir,
                    collection=client[args.database][args.collection], **settings)
    except (OSError, ValueError, TypeError, sqlite3.Error, PyMongoError) as exc:
        parser.exit(1, f"Product deduplication failed ({type(exc).__name__}); inspect input/settings. Raw data is not logged.\n")
    print(f"Scanned {summary.get('documents_scanned', 0):,}; unique configurations {summary['unique_configurations']:,}")
    print(f"Outputs: {args.output_dir}")
