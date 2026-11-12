"""Product CLIs: configuration deduplication, distinct IDs and react_data crawl."""
import argparse
from datetime import datetime, timezone
import json
import logging
import os
from pathlib import Path
import sqlite3

from pymongo import MongoClient
from pymongo.errors import PyMongoError
from glamira_pipeline.products.catalog_ids import aggregation_pipeline, run_distinct
from glamira_pipeline.products.crawl import CrawlStopped, crawl, export, open_checkpoint, read_product_ids, select_ids
from glamira_pipeline.products.pipeline import run_deduplication
from glamira_pipeline.products.stores import STORES


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


def _mongo_client(parser: argparse.ArgumentParser) -> MongoClient:
    """Connect with MONGODB_URI (e.g. through an SSH tunnel); never log the URI."""
    uri = os.environ.get("MONGODB_URI")
    if not uri:
        parser.error("set MONGODB_URI in the environment")
    return MongoClient(uri, directConnection=True, serverSelectionTimeoutMS=10000)


def list_ids_main() -> None:
    """List every distinct product ID referenced in MongoDB events, with timing."""
    parser = argparse.ArgumentParser(description=list_ids_main.__doc__)
    parser.add_argument("--database", default="countly")
    parser.add_argument("--collection", default="summary")
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--explain", action="store_true", help="Print the query plan only; no scan")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    try:
        with _mongo_client(parser) as client:
            collection = client[args.database][args.collection]
            if args.explain:
                plan = client[args.database].command("explain", {"aggregate": args.collection,
                    "pipeline": aggregation_pipeline(), "cursor": {}}, verbosity="queryPlanner")
                print(json.dumps(plan.get("queryPlanner", plan.get("stages", plan)), default=str, indent=2)[:4000])
                return
            summary = run_distinct(collection, args.output_dir)
    except (OSError, ValueError, PyMongoError) as exc:
        parser.exit(1, f"Product ID listing failed ({type(exc).__name__}: {exc}).\n")
    print(f"Distinct product IDs: {summary['distinct_ids']:,} in {summary['query_seconds']:.1f}s")
    print(f"Outputs: {args.output_dir}")


def crawl_main() -> None:
    """Crawl react_data for product IDs with pacing; stop on any block."""
    parser = argparse.ArgumentParser(description=crawl_main.__doc__)
    parser.add_argument("--ids-file", type=Path, required=True, help="JSONL with a product_id field")
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--sample", type=int, help="Seeded random sample size drawn before --limit")
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--limit", type=int)
    parser.add_argument("--delay", type=float, default=3.0, help="Minimum seconds between request starts")
    parser.add_argument("--concurrency", type=int, default=1, help="Products in flight (1-4)")
    parser.add_argument("--jitter", type=float, default=0.0, help="Extra uniform random seconds")
    parser.add_argument("--max-stores", type=int, default=3, help="Stores tried on 404, in priority order")
    parser.add_argument("--raw-dir", type=Path, help="Also save raw JSON (gzip); off by default")
    args = parser.parse_args()
    if args.delay < 0.5:
        parser.error("--delay below 0.5s is not allowed (max 2 requests/second)")
    if not 1 <= args.concurrency <= 4:
        parser.error("--concurrency must be 1..4")
    if not 1 <= args.max_stores <= len(STORES):
        parser.error(f"--max-stores must be 1..{len(STORES)}")
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    connection = open_checkpoint(args.output_dir / "crawl.sqlite3")
    exit_code, stopped = 0, None
    try:
        ids = select_ids(read_product_ids(args.ids_file), sample=args.sample, seed=args.seed, limit=args.limit)
        try:
            metrics = crawl(connection, ids, max_stores=args.max_stores, delay_s=args.delay, concurrency=args.concurrency,
                            jitter_s=args.jitter, raw_dir=args.raw_dir)
        except CrawlStopped as exc:
            metrics, stopped, exit_code = exc.metrics, str(exc), 3
        metrics.update(export(connection, args.output_dir), selected_ids=len(ids), sample=args.sample,
                       seed=args.seed if args.sample is not None else None,
                       finished_at=datetime.now(timezone.utc).isoformat())
        runs = args.output_dir / "runs.jsonl"
        with runs.open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(metrics) + "\n")
    except (OSError, ValueError, sqlite3.Error) as exc:
        parser.exit(1, f"Product crawl failed ({type(exc).__name__}: {exc}).\n")
    finally:
        connection.close()
    print(json.dumps(metrics, indent=2))
    if stopped:
        parser.exit(exit_code, f"Stopped: {stopped}. Not retrying.\n")
