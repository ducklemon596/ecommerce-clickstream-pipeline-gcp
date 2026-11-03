"""Transactional local checkpoint and deduplicated sample IP counts."""
from __future__ import annotations

import json
import os
from pathlib import Path
import sqlite3
from typing import Iterable

from glamira_pipeline.ip_location.lookup import event_address


def open_checkpoint(path: Path, identity: dict) -> sqlite3.Connection:
    """Open a private SQLite checkpoint bound to source and BIN identity.

    Returns a connection for the caller to close. Existing checkpoints with a
    different identity are rejected; use a new path for a different run.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path)
    os.chmod(path, 0o600)
    connection.row_factory = sqlite3.Row
    connection.executescript("""
        CREATE TABLE IF NOT EXISTS meta (key TEXT PRIMARY KEY, value TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS invalid (category TEXT PRIMARY KEY, events INTEGER NOT NULL);
        CREATE TABLE IF NOT EXISTS addresses (
            ip TEXT PRIMARY KEY, version INTEGER NOT NULL, events INTEGER NOT NULL,
            status TEXT NOT NULL DEFAULT 'pending', country_code TEXT, country_name TEXT, region TEXT, city TEXT
        );
    """)
    serialized = json.dumps(identity, sort_keys=True, separators=(",", ":"))
    row = connection.execute("SELECT value FROM meta WHERE key = 'identity'").fetchone()
    if row and row["value"] != serialized:
        connection.close()
        raise ValueError("checkpoint does not match the source, destination, or BIN")
    if not row:
        with connection:
            connection.execute("INSERT INTO meta VALUES ('identity', ?)", (serialized,))
            connection.execute("INSERT INTO meta VALUES ('last_id', '-1')")
    return connection


def last_id(connection: sqlite3.Connection) -> int:
    """Return the last committed local sample row number from a checkpoint."""
    return int(connection.execute("SELECT value FROM meta WHERE key = 'last_id'").fetchone()[0])


def save_event_batch(connection: sqlite3.Connection, events: Iterable[dict]) -> int:
    """Atomically add event counts and advance the cursor for one ordered batch.

    Returns the number of rows committed. Use only with increasing integer IDs
    from the immutable seeded sample; a crash rolls back both counts and cursor.
    """
    cursor = last_id(connection)
    count = 0
    with connection:
        for event in events:
            row_id = event.get("_id")
            if not isinstance(row_id, int) or isinstance(row_id, bool) or row_id != cursor + 1:
                raise ValueError("sample IDs must be contiguous and stable")
            category, address, version = event_address(event)
            if address is None:
                connection.execute("INSERT INTO invalid VALUES (?, 1) ON CONFLICT(category) DO UPDATE SET events = events + 1", (category,))
            else:
                connection.execute("INSERT INTO addresses(ip, version, events) VALUES (?, ?, 1) ON CONFLICT(ip) DO UPDATE SET events = events + 1", (address, version))
            cursor = row_id
            count += 1
        connection.execute("UPDATE meta SET value = ? WHERE key = 'last_id'", (str(cursor),))
    return count
