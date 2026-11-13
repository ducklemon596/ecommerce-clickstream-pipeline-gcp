"""Paced, concurrent crawl of ``react_data`` with batched, idempotent writes.

The written data is the checkpoint: finished IDs come from the store, and a run
crawls ``input IDs − finished IDs`` in input order (no sorting needed). Each
product is requested from the first store in priority order and falls back to
the next only on ``404 Product not found``. A ``blocked`` response stops new
requests at once; buffered results are always flushed before returning, so at
most the requests still in flight are repeated by the next run.
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
import signal
import statistics
import time
from typing import Protocol

from glamira_pipeline.products.http_client import FetchResult, fetch, react_data_url
from glamira_pipeline.products.mongo_store import BatchItem
from glamira_pipeline.products.react_data import option_value_documents, product_document
from glamira_pipeline.products.stores import STORES, Store

LOGGER = logging.getLogger(__name__)
STATUS_NAMES = {"ok": "success", "not_found": "not_found", "error": "error", "blocked": "blocked"}


class CrawlStopped(RuntimeError):
    """The site signalled a block or the network failed repeatedly.

    ``metrics`` and ``progress`` describe the run up to the stop.
    """

    metrics: dict = {}
    progress: dict = {}


class CrawlStore(Protocol):
    """Checkpoint and sink used by the crawler (see ``MongoProductStore``)."""

    run_id: str

    def load_checkpoint(self, max_attempts: int) -> tuple[set[str], dict[str, int]]:
        """Return finished IDs and the attempt count of every unfinished known ID."""

    def write_batch(self, items: Sequence[BatchItem]) -> None:
        """Persist a batch idempotently (replaying it must leave identical data)."""

    def heartbeat(self, progress: dict, metrics: dict | None = None) -> None:
        """Record progress and keep the run lock fresh."""


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


class _Pacer:
    """Space request *starts* by ``delay + uniform(0, jitter)`` seconds.

    Starts are serialized, so ``delay_s`` bounds the request rate however many
    requests are in flight.
    """

    def __init__(self, delay_s: float, jitter_s: float, rng: random.Random,
                 sleep: Callable[[float], Awaitable[None]], clock: Callable[[], float]) -> None:
        self._delay, self._jitter, self._rng = delay_s, jitter_s, rng
        self._sleep, self._clock = sleep, clock
        self._next: float | None = None
        self._lock = asyncio.Lock()

    async def wait(self) -> None:
        """Sleep until the next request may start, then reserve the following slot."""
        async with self._lock:
            if self._next is not None and self._clock() < self._next:
                await self._sleep(self._next - self._clock())
            self._next = self._clock() + self._delay + self._rng.uniform(0, self._jitter)


def _write_raw(raw_dir: Path, product_id: str, store: Store, body: bytes) -> None:
    """Save one raw payload as ``<raw_dir>/<host>/<id>.json.gz``, atomically (opt-in debugging aid)."""
    target = raw_dir / store.host / f"{product_id}.json.gz"
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_suffix(".tmp")
    temporary.write_bytes(gzip.compress(body))
    os.replace(temporary, target)


def _batch_item(product_id: str, store: Store, result: FetchResult, run_id: str, previous_attempts: int) -> BatchItem:
    """Convert one final fetch result into documents; unparseable data becomes ``error``.

    A ``blocked`` result is not the product's fault, so it does not count as an attempt.
    """
    now = datetime.now(timezone.utc)
    status = STATUS_NAMES[result.status]
    source = {"host": store.host, "store_code": store.store_code, "url": result.url,
              "requested_currency": store.currency}
    common = dict(product_id=product_id, status_code=result.http_status, source=source,
                  run_id=run_id, crawled_at=now)
    try:
        if status == "success":
            item = BatchItem(product_document(status=status, payload=result.payload, **common),
                             option_value_documents(result.payload, run_id=run_id, crawled_at=now))
        else:
            item = BatchItem(product_document(status=status, payload=None, error=result.error, **common))
    except (ValueError, TypeError, KeyError) as exc:
        LOGGER.warning("id %s: unparseable payload (%s)", product_id, exc)
        item = BatchItem(product_document(status="error", payload=None, error=f"parse error: {exc}", **common))
    item.product["attempts"] = previous_attempts + (item.product["status"] != "blocked")
    return item


def crawl(store_sink: CrawlStore, product_ids: Iterable[str], *, stores: Sequence[Store] = STORES,
          max_stores: int = 3, delay_s: float = 3.0, jitter_s: float = 0.0, concurrency: int = 1,
          batch_size: int = 200, flush_interval_s: float = 30.0, max_attempts: int = 3,
          max_consecutive_errors: int = 3, limit: int | None = None, raw_dir: Path | None = None,
          fetcher: Callable[[str], FetchResult] = fetch,
          sleep: Callable[[float], Awaitable[None]] = asyncio.sleep,
          clock: Callable[[], float] = time.monotonic, rng: random.Random | None = None) -> dict:
    """Crawl unfinished IDs and return ``{"metrics", "progress"}``; raise ``CrawlStopped`` on a block.

    ``limit`` takes the first N input IDs *before* removing finished ones, so
    the same command converges to the same set. Batches flush on ``batch_size``
    items or ``flush_interval_s`` seconds, and always before returning.
    """
    if concurrency < 1 or batch_size < 1:
        raise ValueError("concurrency and batch_size must be at least 1")
    selected = list(product_ids)[:limit] if limit is not None else list(product_ids)
    done, attempts = store_sink.load_checkpoint(max_attempts)
    pending = [product_id for product_id in selected if product_id not in done]
    try:
        return asyncio.run(_crawl(store_sink, selected, pending, len(selected) - len(pending), attempts, stores=stores,
                                  max_stores=max_stores, delay_s=delay_s, jitter_s=jitter_s,
                                  concurrency=concurrency, batch_size=batch_size,
                                  flush_interval_s=flush_interval_s, max_consecutive_errors=max_consecutive_errors,
                                  raw_dir=raw_dir, fetcher=fetcher, sleep=sleep, clock=clock,
                                  rng=rng or random.Random()))
    except asyncio.CancelledError:
        raise KeyboardInterrupt from None  # forced abort after a repeated signal


async def _crawl(sink, selected, pending, already_finished, previous_attempts, *, stores, max_stores, delay_s, jitter_s,
                 concurrency, batch_size, flush_interval_s, max_consecutive_errors, raw_dir,
                 fetcher, sleep, clock, rng) -> dict:
    """Run ``concurrency`` workers over ``pending`` sharing one pacer and one write buffer.

    All state lives on the event loop thread; only HTTP calls run in worker
    threads, so the buffer and counters need no locks.
    """
    pacer = _Pacer(delay_s, jitter_s, rng, sleep, clock)
    queue = iter(pending)
    results: list[FetchResult] = []
    outcome: Counter = Counter()
    buffer: list[BatchItem] = []
    state = {"consecutive_errors": 0, "stop_reason": None, "last_flush": time.monotonic(), "written": 0}
    started = time.monotonic()

    def progress() -> dict:
        return {"selected": len(selected), "already_finished": already_finished,
                "pending_at_start": len(pending), "written_this_run": state["written"]}

    def metrics() -> dict:
        data = run_metrics(results, time.monotonic() - started)
        data.update(outcome, stop_reason=state["stop_reason"])
        return data

    def flush() -> None:
        """Write the buffer as one batch, then heartbeat.

        Synchronous on purpose: it also runs from ``finally`` during
        cancellation, when awaiting is no longer possible.
        """
        if not buffer:
            return
        batch = buffer[:]
        sink.write_batch(batch)
        del buffer[:len(batch)]
        state["written"] += len(batch)
        state["last_flush"] = time.monotonic()
        sink.heartbeat(progress(), metrics())

    def stop(reason: str) -> None:
        state["stop_reason"] = state["stop_reason"] or reason

    async def handle(product_id: str) -> None:
        """Fetch one product, falling back through stores only on 404, and buffer the outcome."""
        final: tuple[Store, FetchResult] | None = None
        for store in stores[:max_stores]:
            await pacer.wait()
            if state["stop_reason"]:
                return  # left unfinished for the next run
            result = await asyncio.to_thread(fetcher, react_data_url(store.host, product_id, store.currency))
            results.append(result)
            final = (store, result)
            if result.status == "blocked":
                stop(f"blocked (HTTP {result.http_status}) at {store.host} id {product_id}")
                break
            if result.status == "error":
                state["consecutive_errors"] += 1
                LOGGER.warning("error %s id %s: %s", store.host, product_id, result.error or result.http_status)
                if state["consecutive_errors"] >= max_consecutive_errors:
                    stop(f"{state['consecutive_errors']} consecutive errors")
                break  # retried by a later run, not on another store
            state["consecutive_errors"] = 0
            if result.status == "ok":
                if raw_dir is not None:
                    _write_raw(raw_dir, product_id, store, result.raw)
                break
        if final is None:
            return
        store, result = final
        # A product with an error or block is still written, so the next run knows its attempts.
        item = _batch_item(product_id, store, result, sink.run_id, previous_attempts.get(product_id, 0))
        buffer.append(item)
        outcome[f"products_{item.product['status']}"] += 1
        LOGGER.info("id %s -> %s", product_id, item.product["status"])
        if len(buffer) >= batch_size or time.monotonic() - state["last_flush"] >= flush_interval_s:
            flush()

    async def worker() -> None:
        while not state["stop_reason"]:
            product_id = next(queue, None)
            if product_id is None:
                return
            await handle(product_id)

    loop = asyncio.get_running_loop()
    main_task = asyncio.current_task()
    handled = []
    first_signal: list[float] = []

    def on_signal(signum: int) -> None:
        """First signal: stop gracefully (finish in-flight, flush). A repeat >2 s later aborts.

        Repeats within 2 s are ignored because ``uv run`` and the terminal can
        both deliver one Ctrl+C to the process.
        """
        name = signal.Signals(signum).name
        if not first_signal:
            first_signal.append(time.monotonic())
            stop(f"interrupted ({name})")
            LOGGER.warning("%s received: finishing in-flight requests; repeat to abort", name)
        elif time.monotonic() - first_signal[0] > 2:
            LOGGER.warning("%s received again: aborting without waiting", name)
            main_task.cancel()

    for signum in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(signum, on_signal, signum)
            handled.append(signum)
        except (NotImplementedError, RuntimeError, ValueError):
            pass  # e.g. not on the main thread or not supported on this platform
    try:
        await asyncio.gather(*(worker() for _ in range(concurrency)))
    finally:
        for signum in handled:
            loop.remove_signal_handler(signum)
        flush()
    report = {"metrics": metrics(), "progress": progress()}
    if state["stop_reason"]:
        exc = CrawlStopped(state["stop_reason"])
        exc.metrics, exc.progress = report["metrics"], report["progress"]
        raise exc
    return report


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
