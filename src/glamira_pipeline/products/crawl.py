"""Resumable, paced crawl of ``react_data`` into a SQLite checkpoint and JSONL.

Each product is requested from the first store in priority order and falls
back to the next store only on ``404 Product not found``. Requests run
concurrently up to a limit, with request starts paced. A ``blocked``
response stops the run immediately (no retry, no store switching); repeated
network errors also stop it. Finished products (``ok`` or ``not_found`` on
every tried store) are skipped on rerun, so resuming is safe and idempotent.
"""
from __future__ import annotations

import asyncio
from collections import Counter
from collections.abc import Awaitable, Callable, Iterable, Sequence
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


class _Pacer:
    """Space request *starts* by ``delay + uniform(0, jitter)`` seconds.

    Starts are serialized, so ``delay_s`` bounds the request rate (0.5 s means
    at most 2 starts per second) however many requests are in flight.
    """

    def __init__(self, delay_s: float, jitter_s: float, rng: random.Random,
                 sleep: Callable[[float], Awaitable[None]], clock: Callable[[], float]) -> None:
        self._delay, self._jitter, self._rng = delay_s, jitter_s, rng
        self._sleep, self._clock = sleep, clock
        self._next: float | None = None
        self._lock = asyncio.Lock()

    async def wait(self) -> None:
        async with self._lock:
            if self._next is not None and self._clock() < self._next:
                await self._sleep(self._next - self._clock())
            self._next = self._clock() + self._delay + self._rng.uniform(0, self._jitter)


def crawl(connection: sqlite3.Connection, product_ids: Iterable[str], *,
          stores: Sequence[Store] = STORES, max_stores: int = 3, delay_s: float = 3.0,
          jitter_s: float = 0.0, concurrency: int = 1, max_consecutive_errors: int = 3,
          raw_dir: Path | None = None, fetcher: Callable[[str], FetchResult] = fetch,
          sleep: Callable[[float], Awaitable[None]] = asyncio.sleep,
          clock: Callable[[], float] = time.monotonic, rng: random.Random | None = None) -> dict:
    """Crawl unfinished IDs; return per-run metrics. Raises ``CrawlStopped`` on a block.

    Up to ``concurrency`` products are in flight; request starts are paced by
    ``delay_s + uniform(0, jitter_s)``. A block or repeated errors stop new
    requests at once; in-flight responses are still recorded. SQLite is used
    only from the event-loop thread. Metrics cover this invocation only.
    """
    return asyncio.run(_crawl(connection, product_ids, stores=stores, max_stores=max_stores,
                              delay_s=delay_s, jitter_s=jitter_s, concurrency=concurrency,
                              max_consecutive_errors=max_consecutive_errors, raw_dir=raw_dir,
                              fetcher=fetcher, sleep=sleep, clock=clock, rng=rng or random.Random()))


async def _crawl(connection, product_ids, *, stores, max_stores, delay_s, jitter_s, concurrency,
                 max_consecutive_errors, raw_dir, fetcher, sleep, clock, rng) -> dict:
    if concurrency < 1:
        raise ValueError("concurrency must be at least 1")
    done = finished_ids(connection)
    pacer = _Pacer(delay_s, jitter_s, rng, sleep, clock)
    pending = iter(product_ids)
    results: list[FetchResult] = []
    outcome: Counter = Counter()
    state = {"consecutive_errors": 0, "stop_reason": None}
    started = time.monotonic()

    def stop(reason: str) -> None:
        state["stop_reason"] = state["stop_reason"] or reason

    async def handle(product_id: str) -> None:
        final = None
        for store in stores[:max_stores]:
            await pacer.wait()
            if state["stop_reason"]:
                return  # leave the ID unfinished for the next run
            result = await asyncio.to_thread(fetcher, react_data_url(store.host, product_id, store.currency))
            results.append(result)
            with connection:
                _record_attempt(connection, product_id, store, result)
                if result.status == "ok":
                    _save_product(connection, product_id, store, result)
            if result.status == "blocked":
                stop(f"blocked (HTTP {result.http_status}) at {store.host} id {product_id}")
                return
            if result.status == "error":
                state["consecutive_errors"] += 1
                LOGGER.warning("error %s id %s: %s", store.host, product_id, result.error or result.http_status)
                if state["consecutive_errors"] >= max_consecutive_errors:
                    stop(f"{state['consecutive_errors']} consecutive errors")
                final = "error"
                break  # retry this ID on the next run, not on another store
            state["consecutive_errors"] = 0
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

    async def worker() -> None:
        while not state["stop_reason"]:
            product_id = next(pending, None)
            if product_id is None:
                return
            if product_id in done:
                outcome["skipped_finished"] += 1
                continue
            await handle(product_id)

    await asyncio.gather(*(worker() for _ in range(concurrency)))
    metrics = run_metrics(results, time.monotonic() - started)
    metrics.update(outcome, stop_reason=state["stop_reason"], delay_s=delay_s, jitter_s=jitter_s,
                   max_stores=max_stores, concurrency=concurrency)
    if state["stop_reason"]:
        exc = CrawlStopped(state["stop_reason"])
        exc.metrics = metrics
        raise exc
    return metrics


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
