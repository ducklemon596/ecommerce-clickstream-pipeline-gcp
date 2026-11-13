"""Product CLIs: distinct product IDs, collection setup and the react_data crawl."""
import argparse
import json
import logging
import os
from pathlib import Path
import subprocess
import time

from pymongo import MongoClient
from pymongo.errors import PyMongoError

from glamira_pipeline.products.catalog_ids import aggregation_pipeline, run_distinct
from glamira_pipeline.products.crawl import CrawlStopped, crawl, read_product_ids
from glamira_pipeline.products.mongo_store import (MongoProductStore, ensure_collections, finish_run,
                                                    has_validators, start_run)
from glamira_pipeline.products.stores import STORES
from glamira_pipeline.provenance import file_sha256

# Hard rate ceiling for react_data requests: at most 8 request starts per second.
MIN_DELAY_S = 0.125


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


def setup_collections_main() -> None:
    """Create the product collections with schema validators and indexes (idempotent)."""
    parser = argparse.ArgumentParser(description=setup_collections_main.__doc__)
    parser.add_argument("--database", default="countly")
    args = parser.parse_args()
    try:
        with _mongo_client(parser) as client:
            for action in ensure_collections(client[args.database]):
                print(action)
    except PyMongoError as exc:
        parser.exit(1, f"Collection setup failed ({type(exc).__name__}: {exc}).\n")


def _git_sha() -> str | None:
    try:
        return subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True,
                              check=True, cwd=Path(__file__).parent).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return None


def crawl_main() -> None:
    """Crawl react_data into MongoDB in idempotent batches; resume skips finished IDs."""
    parser = argparse.ArgumentParser(description=crawl_main.__doc__)
    parser.add_argument("--ids-file", type=Path, required=True, help="JSONL with a product_id field")
    parser.add_argument("--database", default="countly")
    parser.add_argument("--limit", type=int, help="Use only the first N input IDs (before skipping finished)")
    parser.add_argument("--delay", type=float, default=3.0, help="Minimum seconds between request starts")
    parser.add_argument("--jitter", type=float, default=0.0, help="Extra uniform random seconds")
    parser.add_argument("--concurrency", type=int, default=1, help="Products in flight (1-8)")
    parser.add_argument("--max-stores", type=int, default=3, help="Stores tried on 404, in priority order")
    parser.add_argument("--batch-size", type=int, default=200, help="Products per MongoDB write")
    parser.add_argument("--max-attempts", type=int, default=3, help="Error attempts before an ID is skipped")
    parser.add_argument("--raw-dir", type=Path, help="Also save raw JSON (gzip) to files; off by default")
    parser.add_argument("--block-retries", type=int, default=0, help="Resumes after a block (0-3)")
    parser.add_argument("--block-wait", type=float, default=300.0,
                        help="Seconds to wait after the first block; doubles for each retry (min 300)")
    parser.add_argument("--recheck-not-found", action="store_true",
                        help="Crawl not_found IDs again (combine with --max-stores to try more stores)")
    args = parser.parse_args()
    if not 0 <= args.block_retries <= 3 or args.block_wait < 300:
        parser.error("--block-retries must be 0..3 and --block-wait at least 300 seconds")
    if args.delay < MIN_DELAY_S:
        parser.error(f"--delay below {MIN_DELAY_S}s is not allowed (max {1 / MIN_DELAY_S:.0f} requests/second)")
    if not 1 <= args.concurrency <= 8:
        parser.error("--concurrency must be 1..8")
    if not 1 <= args.max_stores <= len(STORES):
        parser.error(f"--max-stores must be 1..{len(STORES)}")
    if args.batch_size < 1 or args.max_attempts < 1 or (args.limit is not None and args.limit < 1):
        parser.error("--batch-size, --max-attempts and --limit must be positive")
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    params = {key: getattr(args, key) for key in
              ("limit", "delay", "jitter", "concurrency", "max_stores", "batch_size", "max_attempts",
               "block_retries", "block_wait", "recheck_not_found")}
    try:
        ids = read_product_ids(args.ids_file)
        input_info = {"file": args.ids_file.name, "sha256": file_sha256(args.ids_file), "ids": len(ids)}
    except (OSError, ValueError) as exc:
        parser.exit(1, f"Cannot read --ids-file ({type(exc).__name__}: {exc}).\n")
    waits = block_waits(args.block_wait, args.block_retries)
    try:
        with _mongo_client(parser) as client:
            db = client[args.database]
            if not has_validators(db):
                parser.exit(1, "Product collections are missing or outdated; run setup-product-collections.\n")
            for attempt in range(len(waits) + 1):
                try:
                    run_id = start_run(db, params={**params, "block_retry": attempt},
                                       input_info=input_info, git_sha=_git_sha())
                except RuntimeError as exc:
                    parser.exit(2, f"Refusing to start: {exc}.\n")
                print(f"run_id {run_id}")
                status, report, reason, code = _run_once(db, run_id, ids, args)
                print(json.dumps(report, indent=2, default=str))
                if not (code == 3 and reason and reason.startswith("blocked")) or attempt == len(waits):
                    break
                logging.warning("blocked; waiting %.0f s before retry %d/%d", waits[attempt], attempt + 1, len(waits))
                try:
                    time.sleep(waits[attempt])
                except KeyboardInterrupt:
                    reason, code = "interrupted while waiting after a block", 130
                    break
    except PyMongoError as exc:
        parser.exit(1, f"Product crawl failed ({type(exc).__name__}: {exc}).\n")
    if code:
        parser.exit(code, f"Run {status}: {reason}.\n")


def block_waits(first_s: float, retries: int) -> list[float]:
    """Waits before each retry after a block: ``first, 2×first, 4×first, …``."""
    return [first_s * 2 ** index for index in range(retries)]


def _run_once(db, run_id: str, ids: list[str], args: argparse.Namespace) -> tuple[str, dict, str | None, int]:
    """Run one crawl and always record its outcome; return (status, report, reason, exit code)."""
    status, report, reason, code = "failed", {}, None, 1
    try:
        report = crawl(MongoProductStore(db, run_id, recheck_not_found=args.recheck_not_found), ids, limit=args.limit, delay_s=args.delay,
                       jitter_s=args.jitter, concurrency=args.concurrency, max_stores=args.max_stores,
                       batch_size=args.batch_size, max_attempts=args.max_attempts, raw_dir=args.raw_dir)
        status, code = "completed", 0
    except CrawlStopped as exc:
        report, reason, status, code = {"metrics": exc.metrics, "progress": exc.progress}, str(exc), "stopped", 3
    except KeyboardInterrupt:
        reason, status, code = "interrupted", "stopped", 130
    except Exception as exc:
        reason = f"{type(exc).__name__}: {exc}"
        raise
    finally:
        finish_run(db, run_id, status=status, metrics=report.get("metrics"),
                   progress=report.get("progress"), stop_reason=reason)
    return status, report, reason, code
