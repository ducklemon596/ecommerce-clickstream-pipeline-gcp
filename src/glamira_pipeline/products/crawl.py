"""Resumable, paced crawl of ``react_data`` into a SQLite checkpoint and JSONL.

Each product is requested from the first store in priority order and falls
back to the next store only on ``404 Product not found``. A ``blocked``
response stops the run immediately (no retry, no store switching); repeated
network errors also stop it. Finished products (``ok`` or ``not_found`` on
every tried store) are skipped on rerun, so resuming is safe and idempotent.
"""
from __future__ import annotations

from collections import Counter
from collections.abc import Callable, Iterable, Sequence
from datetime import datetime, timezone
import gzip
import json
import logging
import os
from pathlib import Path
import random
import sqlite3
import statistics
import time

from glamira_pipeline.products.http_client import FetchResult, fetch, react_data_url
from glamira_pipeline.products.react_data import parse_option_values, parse_product
from glamira_pipeline.products.stores import STORES, Store

LOGGER = logging.getLogger(__name__)
FINAL_STATUSES = ("ok", "not_found")


class CrawlStopped(RuntimeError):
    """The site signalled a block or the network failed repeatedly.

    ``metrics`` holds the run metrics up to the stop.
    """

    metrics: dict = {}


def read_product_ids(path: Path) -> list[str]:
    """Read numeric ``product_id`` values from JSONL, keeping first-seen order."""
    seen: dict[str, None] = {}
    with path.open(encoding="utf-8") as stream:
        for line in stream:
            if line.strip():
                value = json.loads(line).get("product_id")
                if isinstance(value, str) and value.isdigit():
                    seen.setdefault(value)
    return list(seen)


def select_ids(ids: Sequence[str], *, sample: int | None, seed: int | None, limit: int | None) -> list[str]:
    """Optionally draw a seeded random sample, then cap with ``limit``."""
    chosen = list(ids)
    if sample is not None:
        chosen = random.Random(seed).sample(chosen, min(sample, len(chosen)))
    return chosen[:limit] if limit is not None else chosen


def open_checkpoint(path: Path) -> sqlite3.Connection:
    """Open or create the crawl checkpoint (one writer)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path)
    connection.executescript("""
        CREATE TABLE IF NOT EXISTS products(
            product_id TEXT PRIMARY KEY, status TEXT NOT NULL, host TEXT,
            record TEXT, crawled_at TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS option_values(
            product_id TEXT NOT NULL, option_id TEXT NOT NULL, value_key TEXT NOT NULL,
            record TEXT NOT NULL, PRIMARY KEY(product_id, option_id, value_key));
        CREATE TABLE IF NOT EXISTS attempts(
            id INTEGER PRIMARY KEY, product_id TEXT, host TEXT, status TEXT, http_status INTEGER,
            elapsed_s REAL, response_bytes INTEGER, error TEXT, attempted_at TEXT);
    """)
    return connection


def finished_ids(connection: sqlite3.Connection) -> set[str]:
    rows = connection.execute("SELECT product_id FROM products WHERE status IN (?, ?)", FINAL_STATUSES)
    return {row[0] for row in rows}


def _record_attempt(connection: sqlite3.Connection, product_id: str, store: Store, result: FetchResult) -> None:
    connection.execute("INSERT INTO attempts(product_id,host,status,http_status,elapsed_s,response_bytes,error,attempted_at)"
                       " VALUES(?,?,?,?,?,?,?,?)",
                       (product_id, store.host, result.status, result.http_status, result.elapsed_s,
                        result.response_bytes, result.error, datetime.now(timezone.utc).isoformat()))


def _save_product(connection: sqlite3.Connection, product_id: str, store: Store, result: FetchResult) -> None:
    """Replace the product and its option rows atomically (caller's transaction)."""
    record = parse_product(result.payload, host=store.host, requested_currency=store.currency)
    if record["product_id"] != product_id:
        raise ValueError(f"payload product_id {record['product_id']} != requested {product_id}")
    now = datetime.now(timezone.utc).isoformat()
    record["crawled_at"] = now
    connection.execute("INSERT OR REPLACE INTO products VALUES(?,?,?,?,?)",
                       (product_id, "ok", store.host, json.dumps(record, ensure_ascii=False), now))
    connection.execute("DELETE FROM option_values WHERE product_id=?", (product_id,))
    connection.executemany("INSERT OR REPLACE INTO option_values VALUES(?,?,?,?)", [
        (product_id, str(row["option_id"]), "" if row["value_id"] is None else str(row["value_id"]),
         json.dumps(row, ensure_ascii=False)) for row in parse_option_values(result.payload)])


def _write_raw(raw_dir: Path, product_id: str, store: Store, body: bytes) -> None:
    target = raw_dir / store.host / f"{product_id}.json.gz"
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_suffix(".tmp")
    temporary.write_bytes(gzip.compress(body))
    os.replace(temporary, target)


def crawl(connection: sqlite3.Connection, product_ids: Iterable[str], *,
          stores: Sequence[Store] = STORES, max_stores: int = 3, delay_s: float = 3.0,
          jitter_s: float = 0.0, max_consecutive_errors: int = 3, raw_dir: Path | None = None,
          fetcher: Callable[[str], FetchResult] = fetch, sleep: Callable[[float], None] = time.sleep,
          rng: random.Random | None = None) -> dict:
    """Crawl unfinished IDs; return per-run metrics. Raises ``CrawlStopped`` on a block.

    A pause of ``delay_s + uniform(0, jitter_s)`` precedes every request after
    the first. Metrics cover only requests made in this invocation.
    """
    rng = rng or random.Random()
    done = finished_ids(connection)
    results: list[FetchResult] = []
    outcome: Counter = Counter()
    consecutive_errors = 0
    started = time.monotonic()
    stop_reason = None

    def request(product_id: str, store: Store) -> FetchResult:
        if results:
            sleep(delay_s + rng.uniform(0, jitter_s))
        result = fetcher(react_data_url(store.host, product_id, store.currency))
        results.append(result)
        return result

    def summarize() -> dict:
        metrics = run_metrics(results, time.monotonic() - started)
        metrics.update(outcome, stop_reason=stop_reason, delay_s=delay_s, jitter_s=jitter_s,
                       max_stores=max_stores)
        return metrics

    try:
        for product_id in product_ids:
            if product_id in done:
                outcome["skipped_finished"] += 1
                continue
            final = None
            for store in stores[:max_stores]:
                result = request(product_id, store)
                with connection:
                    _record_attempt(connection, product_id, store, result)
                    if result.status == "ok":
                        _save_product(connection, product_id, store, result)
                if result.status == "blocked":
                    stop_reason = f"blocked (HTTP {result.http_status}) at {store.host} id {product_id}"
                    raise CrawlStopped(stop_reason)
                if result.status == "error":
                    consecutive_errors += 1
                    LOGGER.warning("error %s id %s: %s", store.host, product_id, result.error or result.http_status)
                    if consecutive_errors >= max_consecutive_errors:
                        stop_reason = f"{consecutive_errors} consecutive errors"
                        raise CrawlStopped(stop_reason)
                    final = "error"
                    break  # retry this ID on the next run, not on another store
                consecutive_errors = 0
                final = result.status
                if result.status == "ok":
                    if raw_dir is not None:
                        _write_raw(raw_dir, product_id, store, result.raw)
                    break
            if final == "not_found":
                with connection:
                    connection.execute("INSERT OR REPLACE INTO products VALUES(?,?,?,?,?)",
                                       (product_id, "not_found", None, None, datetime.now(timezone.utc).isoformat()))
            outcome[f"products_{final}"] += 1
            LOGGER.info("id %s -> %s", product_id, final)
    except CrawlStopped as exc:
        exc.metrics = summarize()
        raise
    return summarize()


def run_metrics(results: Sequence[FetchResult], wall_s: float) -> dict:
    """Summarize request outcomes, latency and throughput for one invocation."""
    latencies = sorted(r.elapsed_s for r in results)
    def pct(q: float) -> float | None:
        return round(latencies[min(len(latencies) - 1, int(q * len(latencies)))], 3) if latencies else None
    return {"requests": len(results), "wall_seconds": round(wall_s, 2),
            "requests_per_second": round(len(results) / wall_s, 3) if wall_s > 0 else None,
            "latency_p50_s": pct(0.5), "latency_p95_s": pct(0.95),
            "latency_mean_s": round(statistics.fmean(latencies), 3) if latencies else None,
            "response_bytes_total": sum(r.response_bytes for r in results),
            "request_statuses": dict(Counter(r.status for r in results))}


def export(connection: sqlite3.Connection, output_dir: Path) -> dict:
    """Write ``products.jsonl`` and ``option_values.jsonl`` atomically; return row counts."""
    counts = {}
    queries = {"products.jsonl": "SELECT record FROM products WHERE status='ok' ORDER BY CAST(product_id AS INTEGER)",
               "option_values.jsonl": "SELECT record FROM option_values ORDER BY CAST(product_id AS INTEGER), option_id, value_key"}
    for name, query in queries.items():
        target = output_dir / name
        temporary = target.with_suffix(".jsonl.tmp")
        rows = 0
        try:
            with temporary.open("w", encoding="utf-8") as stream:
                for (record,) in connection.execute(query):
                    stream.write(record + "\n")
                    rows += 1
            os.replace(temporary, target)
        finally:
            temporary.unlink(missing_ok=True)
        counts[name.removesuffix(".jsonl") + "_rows"] = rows
    counts["products_not_found"] = connection.execute(
        "SELECT COUNT(*) FROM products WHERE status='not_found'").fetchone()[0]
    return counts
