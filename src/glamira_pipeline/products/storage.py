"""Transactional SQLite counts and source progress, plus bounded export."""
from __future__ import annotations

from collections import Counter
import json
import os
from pathlib import Path
import sqlite3
from typing import Any

from bson import json_util
from glamira_pipeline.products.normalize import InvalidConfiguration, normalize_event
from glamira_pipeline.products.urls import collect_urls, create_url_tables


def open_state(path: Path, identity: dict) -> sqlite3.Connection:
    """Open a private checkpoint bound to identity; reject incompatible resume.

    Returns a SQLite connection owned by the caller. Inputs include source
    identity, limit and policy version. Use once per run with one writer.
    """
    connection = sqlite3.connect(path)
    os.chmod(path, 0o600)
    connection.executescript("""
        PRAGMA cache_size=-8192;
        CREATE TABLE IF NOT EXISTS state(key TEXT PRIMARY KEY, value TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS configurations(
            product_id TEXT, store_id TEXT, hostname TEXT, options TEXT,
            source_url TEXT NOT NULL, occurrence_count INTEGER NOT NULL,
            PRIMARY KEY(product_id, store_id, hostname, options));
    """)
    encoded = json.dumps(identity, sort_keys=True)
    previous = connection.execute("SELECT value FROM state WHERE key='identity'").fetchone()
    if previous and previous[0] != encoded:
        connection.close()
        raise ValueError("checkpoint source or normalization settings changed")
    create_url_tables(connection)
    with connection:
        connection.execute("INSERT OR IGNORE INTO state VALUES('identity', ?)", (encoded,))
    return connection


def read_state(connection: sqlite3.Connection, key: str, default: Any = None) -> Any:
    """Decode a named checkpoint value or return default when not yet committed."""
    row = connection.execute("SELECT value FROM state WHERE key=?", (key,)).fetchone()
    return json_util.loads(row[0]) if row else default


def save_state(connection: sqlite3.Connection, key: str, value: Any) -> None:
    """Set a BSON-compatible state value inside the caller's transaction."""
    connection.execute("INSERT OR REPLACE INTO state VALUES(?, ?)", (key, json_util.dumps(value)))


def commit_batch(connection: sqlite3.Connection, batch: list[dict]) -> None:
    """Deduplicate a bounded batch and atomically commit counts and last source ID.

    All events contribute URL references; detail events also contribute normalized
    configurations. Rollback prevents either output from double-counting a batch.
    """
    counts = Counter(read_state(connection, "counts", {}))
    with connection:
        for event in batch:
            counts["documents_scanned"] += 1
            for key, value in collect_urls(connection, event).items():
                counts[key] += value
            if event.get("collection") != "view_product_detail":
                continue
            counts["relevant_events"] += 1
            try:
                row, warnings = normalize_event(event)
            except InvalidConfiguration as exc:
                counts["rejected_events"] += 1
                counts["rejected:" + str(exc)] += 1
                continue
            for warning in warnings:
                counts["warning:" + warning] += 1
            if not row["normalized_options"]:
                counts["empty_configuration_events"] += 1
            connection.execute("""INSERT INTO configurations VALUES(?,?,?,?,?,1)
                ON CONFLICT(product_id,store_id,hostname,options)
                DO UPDATE SET occurrence_count=occurrence_count+1""",
                (row["product_id"], row["store_id"], row["hostname"],
                 json.dumps(row["normalized_options"], sort_keys=True, separators=(",", ":")), row["source_url"]))
            counts["accepted_events"] += 1
        save_state(connection, "counts", dict(counts))
        if batch:
            save_state(connection, "last_id", batch[-1].get("_id"))


def export_jsonl(connection: sqlite3.Connection, path: Path) -> tuple[int, int]:
    """Stream configurations into an atomically published private JSONL file.

    Returns (unique configurations, summed occurrences); raises on write errors.
    Call only after the scan is marked complete.
    """
    temporary = path.with_suffix(".jsonl.tmp")
    unique = occurrences = 0
    try:
        with temporary.open("w", encoding="utf-8") as stream:
            os.chmod(temporary, 0o600)
            rows = connection.execute("SELECT * FROM configurations ORDER BY product_id,store_id,hostname,options")
            for product, store, host, options, url, count in rows:
                stream.write(json.dumps({"product_id": product, "store": store, "store_id": store,
                    "hostname": host, "normalized_options": json.loads(options),
                    "source_url": url, "occurrence_count": count}, ensure_ascii=False) + "\n")
                unique += 1
                occurrences += count
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)
    return unique, occurrences
