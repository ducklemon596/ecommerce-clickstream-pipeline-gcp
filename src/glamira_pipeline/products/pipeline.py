"""Batch orchestration and aggregate reporting for product configurations."""
from __future__ import annotations

from datetime import datetime, timezone
import json
import logging
from pathlib import Path
import resource
import sqlite3
import sys
import time
from collections.abc import Generator

import pymongo
from pymongo.collection import Collection

from glamira_pipeline.products.source import json_events, json_identity, mongo_events, mongo_identity
from glamira_pipeline.products.storage import commit_batch, export_jsonl, open_state, read_state, save_state
from glamira_pipeline.products.urls import export_urls

LOGGER = logging.getLogger(__name__)


def _scan(connection: sqlite3.Connection, events: Generator, batch_size: int, require_events: int | None) -> None:
    """Commit bounded input batches and mark completion only after enough rows."""
    batch = []
    next_progress = time.monotonic() + 30
    try:
        for event in events:
            batch.append(event)
            if len(batch) == batch_size:
                commit_batch(connection, batch)
                batch.clear()
                if time.monotonic() >= next_progress:
                    LOGGER.info("Committed %s source documents", read_state(connection, "counts")["documents_scanned"])
                    next_progress = time.monotonic() + 30
        if batch:
            commit_batch(connection, batch)
    finally:
        events.close()
    scanned = read_state(connection, "counts", {}).get("documents_scanned", 0)
    if require_events is not None and scanned != require_events:
        raise ValueError("source has fewer documents than the requested exact limit")
    with connection:
        save_state(connection, "complete", True)


def _report(connection: sqlite3.Connection, directory: Path, identity: dict) -> dict:
    """Validate count equations, export JSONL and write aggregate JSON/Markdown."""
    counts = {"documents_scanned": 0, "relevant_events": 0, "accepted_events": 0,
              "rejected_events": 0, "empty_configuration_events": 0,
              **read_state(connection, "counts", {})}
    unique, occurrences = connection.execute(
        "SELECT COUNT(*), COALESCE(SUM(occurrence_count),0) FROM configurations").fetchone()
    accepted = counts.get("accepted_events", 0)
    relevant = counts.get("relevant_events", 0)
    if occurrences != accepted or relevant != accepted + counts.get("rejected_events", 0):
        raise ValueError("configuration occurrence accounting failed")
    export_jsonl(connection, directory / "configurations.jsonl")
    url_counts = export_urls(connection, directory)
    seconds = read_state(connection, "processing_seconds", 0)
    # ru_maxrss is KiB on Linux, bytes on macOS; includes this CLI process only.
    rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    summary = {**counts, **url_counts, "unique_configurations": unique, "duplicate_events": accepted - unique,
        "occurrence_sum": occurrences, "processing_seconds": seconds,
        "documents_per_second": counts.get("documents_scanned", 0) / seconds if seconds else 0,
        "peak_rss_mib": rss / (1024 * 1024 if sys.platform == "darwin" else 1024),
        "source": identity, "observed_at": datetime.now(timezone.utc).isoformat(),
        "versions": {"python": sys.version.split()[0], "sqlite": sqlite3.sqlite_version,
                     "pymongo": pymongo.version},
        "measurement_notes": "Processing includes source reads and SQLite commits; excludes input hashing/export. RSS is process high-water mark for this invocation, not earlier resumed invocations."}
    (directory / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    lines = ["# Product configuration deduplication", "",
             "Observed source data only; JSON prefix samples are sequential and non-random.", "",
             "| Metric | Value |", "| --- | ---: |"]
    for key, value in summary.items():
        if isinstance(value, (int, float)):
            lines.append(f"| {key} | {value:.3f} |" if isinstance(value, float) else f"| {key} | {value:,} |")
    lines += ["", summary["measurement_notes"], "",
        "Options come only from nonempty URL parameters. No defaults are inferred. Unknown parameters are retained; explicit tracking/control keys are excluded.",
        "The event option field contains internal IDs: value equality to URL labels is unverified. Warnings do not discard accepted configurations.", ""]
    (directory / "summary.md").write_text("\n".join(lines))
    return summary


def run_deduplication(output_dir: Path, *, sample: Path | None = None, collection: Collection | None = None,
                      limit: int | None = None, batch_size: int = 5000) -> dict:
    """Extract a local JSON or MongoDB source into SQLite and JSONL; return metrics.

    Exactly one input is required. Limit counts all source documents, before
    event filtering, and must be fully available. Resume uses the same directory
    and identity; keep MongoDB immutable. No source writes or network crawl occur.
    """
    if (sample is None) == (collection is None) or batch_size < 1 or (limit is not None and limit < 1):
        raise ValueError("choose exactly one input and positive batch size/limit")
    source = json_identity(sample) if sample is not None else mongo_identity(collection)
    identity = {"source": source, "limit": limit, "normalization_version": 3}
    output_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
    connection = open_state(output_dir / "configurations.sqlite3", identity)
    try:
        if not read_state(connection, "complete", False):
            counts = read_state(connection, "counts", {})
            scanned = counts.get("documents_scanned", 0)
            remaining = None if limit is None else limit - scanned
            started = time.perf_counter()
            try:
                if remaining != 0:
                    events = (json_events(sample, scanned, remaining) if sample is not None else
                              mongo_events(collection, read_state(connection, "last_id"), remaining, batch_size))
                    _scan(connection, events, batch_size, limit)
                else:
                    with connection:
                        save_state(connection, "complete", True)
            finally:
                with connection:
                    save_state(connection, "processing_seconds",
                               read_state(connection, "processing_seconds", 0) + time.perf_counter() - started)
        return _report(connection, output_dir, identity)
    finally:
        connection.close()
