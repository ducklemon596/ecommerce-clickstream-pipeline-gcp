"""Bounded, resumable IP enrichment for a complete MongoDB collection."""
from __future__ import annotations

import base64
import csv
from datetime import datetime, timezone
import json
import logging
import os
from pathlib import Path
import sqlite3
import time
from typing import Any

import IP2Location
from bson import BSON
from pymongo import ReplaceOne
from pymongo.collection import Collection

from glamira_pipeline.ip_location.lookup import bin_metadata, event_address, lookup_address
from glamira_pipeline.ip_location.source import RUN_COLLECTION, file_sha256

SCAN_BATCH = 5_000
LOOKUP_BATCH = 500
logger = logging.getLogger(__name__)


def collection_identity(collection: Collection, bin_sha256: str) -> dict:
    """Return the source namespace and UUID for checkpoint binding."""
    info = next(collection.database.list_collections(filter={"name": collection.name}), None)
    if not info or not info.get("info", {}).get("uuid"):
        raise ValueError("source collection identity is unavailable")
    return {"namespace": collection.full_name,
            "collection_uuid": bytes(info["info"]["uuid"]).hex(),
            "bin_sha256": bin_sha256}


def ensure_target_identity(target: Collection) -> str:
    """Create an absent output collection and return its stable Mongo UUID."""
    info = next(target.database.list_collections(filter={"name": target.name}), None)
    if info is None:
        target.database.create_collection(target.name)
        info = next(target.database.list_collections(filter={"name": target.name}), None)
    if not info or not info.get("info", {}).get("uuid"):
        raise ValueError("target collection identity is unavailable")
    return bytes(info["info"]["uuid"]).hex()


def open_full_checkpoint(path: Path, identity: dict) -> sqlite3.Connection:
    """Create or resume a private disk-backed full-collection checkpoint."""
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path)
    os.chmod(path, 0o600)
    connection.row_factory = sqlite3.Row
    connection.executescript("""
        CREATE TABLE IF NOT EXISTS meta (key TEXT PRIMARY KEY, value TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS invalid (category TEXT PRIMARY KEY, events INTEGER NOT NULL);
        CREATE TABLE IF NOT EXISTS addresses (
            ip TEXT PRIMARY KEY, version INTEGER NOT NULL, events INTEGER NOT NULL,
            status TEXT NOT NULL DEFAULT 'pending', country_code TEXT, country_name TEXT,
            region TEXT, city TEXT
        );
        CREATE INDEX IF NOT EXISTS idx_addresses_status_ip ON addresses(status, ip);
    """)
    serialized = json.dumps(identity, sort_keys=True, separators=(",", ":"))
    stored = connection.execute("SELECT value FROM meta WHERE key='identity'").fetchone()
    if stored and stored["value"] != serialized:
        connection.close()
        raise ValueError("checkpoint does not match source collection or BIN")
    if not stored:
        with connection:
            connection.execute("INSERT INTO meta VALUES ('identity', ?)", (serialized,))
            connection.execute("INSERT INTO meta VALUES ('last_id', '')")
    return connection


def _last_source_id(connection: sqlite3.Connection) -> Any | None:
    """Decode the BSON source `_id` persisted after the last committed scan batch."""
    value = connection.execute("SELECT value FROM meta WHERE key='last_id'").fetchone()[0]
    return BSON(base64.b64decode(value)).decode()["value"] if value else None


def _save_scan_batch(connection: sqlite3.Connection, events: list[dict]) -> None:
    """Atomically persist IP frequencies and the final BSON `_id` of one batch."""
    with connection:
        for event in events:
            category, address, version = event_address(event)
            if address is None:
                connection.execute(
                    "INSERT INTO invalid VALUES (?, 1) ON CONFLICT(category) DO UPDATE SET events=events+1",
                    (category,),
                )
            else:
                connection.execute(
                    "INSERT INTO addresses(ip,version,events) VALUES (?,?,1) "
                    "ON CONFLICT(ip) DO UPDATE SET events=events+1", (address, version),
                )
        encoded_id = base64.b64encode(BSON.encode({"value": events[-1]["_id"]})).decode("ascii")
        connection.execute("UPDATE meta SET value=? WHERE key='last_id'", (encoded_id,))


def scan_collection(source: Collection, connection: sqlite3.Connection) -> int:
    """Stream source events in `_id` order and checkpoint bounded batches."""
    last_id = _last_source_id(connection)
    query = {"_id": {"$gt": last_id}} if last_id is not None else {}
    cursor = source.find(query, {"ip": 1}).sort("_id", 1).batch_size(SCAN_BATCH)
    batch: list[dict] = []
    total = 0
    next_report = 5_000_000
    started = time.monotonic()
    for event in cursor:
        batch.append(event)
        if len(batch) >= SCAN_BATCH:
            _save_scan_batch(connection, batch)
            total += len(batch)
            batch.clear()
            if total >= next_report:
                logger.info("scanned_events=%s elapsed_seconds=%.0f", f"{total:,}", time.monotonic() - started)
                next_report += 5_000_000
    if batch:
        _save_scan_batch(connection, batch)
        total += len(batch)
    logger.info("source_scan_complete events_this_run=%s elapsed_seconds=%.0f",
                f"{total:,}", time.monotonic() - started)
    return total


def _location_document(row: sqlite3.Row, result: dict, database_id: str) -> dict:
    """Build the agreed `ip_locations` schema without event frequency fields."""
    return {"_id": row["ip"], "ip_version": row["version"], **result,
            "database_id": database_id}


def lookup_pending(connection: sqlite3.Connection, target: Collection, bin_path: Path,
                   bin_info: dict, *, retry_failed: bool = False) -> int:
    """Lookup unique pending IPs and idempotently upsert bounded write batches."""
    if retry_failed:
        with connection:
            connection.execute("UPDATE addresses SET status='pending' WHERE status='lookup_failed'")
    reader = IP2Location.IP2Location(str(bin_path), mode="SHARED_MEMORY")
    processed = 0
    next_report = 10_000
    started = time.monotonic()
    try:
        while True:
            rows = connection.execute(
                "SELECT * FROM addresses WHERE status='pending' ORDER BY ip LIMIT ?", (LOOKUP_BATCH,),
            ).fetchall()
            if not rows:
                break
            updates = []
            writes = []
            for row in rows:
                result = lookup_address(reader, row["ip"], bin_info["ipv6_supported"])
                writes.append(ReplaceOne(
                    {"_id": row["ip"]},
                    _location_document(row, result, bin_info["database_id"]), upsert=True,
                ))
                updates.append({**result, "ip": row["ip"]})
            # If the client loses acknowledgement, replaying these replacements is safe.
            target.bulk_write(writes, ordered=True)
            with connection:
                connection.executemany(
                    "UPDATE addresses SET status=:status,country_code=:country_code,"
                    "country_name=:country_name,region=:region,city=:city WHERE ip=:ip", updates,
                )
            processed += len(rows)
            if processed >= next_report:
                logger.info("looked_up_unique_ips=%s elapsed_seconds=%.0f",
                            f"{processed:,}", time.monotonic() - started)
                next_report += 10_000
    finally:
        reader.close()
    logger.info("unique_ip_lookups_complete ips_this_run=%s elapsed_seconds=%.0f",
                f"{processed:,}", time.monotonic() - started)
    return processed


def _write_run(target: Collection, bin_path: Path, info: dict) -> None:
    """Upsert provenance for the exact BIN bytes used by this processing run."""
    run = {"_id": info["database_id"], "database_id": info["database_id"],
           "source": bin_path.name, "database_date": info["date"],
           "database_edition": info["edition"], "database_sha256": info["sha256"],
           "processed_at": datetime.now(timezone.utc)}
    target.database[RUN_COLLECTION].replace_one({"_id": run["_id"]}, run, upsert=True)


def full_metrics(connection: sqlite3.Connection, info: dict) -> dict:
    """Calculate event-weighted and unique-IP coverage from disk-backed counts."""
    invalid = {r["category"]: r["events"] for r in connection.execute("SELECT * FROM invalid")}
    statuses = {r["status"]: {"unique_ips": r["ips"], "events": r["events"]}
                for r in connection.execute("SELECT status,COUNT(*) ips,SUM(events) events FROM addresses GROUP BY status")}
    versions = {str(r["version"]): {"unique_ips": r["ips"], "events": r["events"]}
                for r in connection.execute("SELECT version,COUNT(*) ips,SUM(events) events FROM addresses GROUP BY version")}
    total_events = sum(invalid.values()) + sum(v["events"] for v in statuses.values())
    total_ips = sum(v["unique_ips"] for v in statuses.values())
    resolved = statuses.get("resolved", {"events": 0, "unique_ips": 0})
    return {"events": total_events, "unique_ips": total_ips, "invalid_events": invalid,
            "lookup_statuses": statuses, "ip_versions": versions,
            "event_coverage_percent": 100 * resolved["events"] / total_events if total_events else 0,
            "unique_ip_coverage_percent": 100 * resolved["unique_ips"] / total_ips if total_ips else 0,
            "bin": info, "sample_method": "full MongoDB collection scan ordered by _id"}


def write_full_outputs(connection: sqlite3.Connection, directory: Path, summary: dict) -> None:
    """Stream the agreed location schema to a private CSV and write aggregate metrics."""
    directory.mkdir(parents=True, exist_ok=True)
    target = directory / "ip_locations.csv"
    temporary = target.with_suffix(".tmp")
    fields = ("_id", "ip_version", "status", "country_code", "country_name", "region", "city", "database_id")
    with temporary.open("w", newline="", encoding="utf-8") as stream:
        os.chmod(temporary, 0o600)
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        for row in connection.execute("SELECT * FROM addresses ORDER BY ip"):
            result = {k: row[k] for k in ("status", "country_code", "country_name", "region", "city")}
            writer.writerow({"_id": row["ip"], "ip_version": row["version"], **result,
                             "database_id": summary["bin"]["database_id"]})
    os.replace(temporary, target)
    (directory / "ip_location_metrics.json").write_text(json.dumps(summary, indent=2) + "\n")


def enrich_full_collection(source: Collection, target: Collection, bin_path: Path,
                           checkpoint_path: Path, output_dir: Path, *, retry_failed: bool = False) -> dict:
    """Scan, deduplicate, lookup and export one full source collection with resume.

    Use on a host with the BIN and a MongoDB connection to the source. Source
    reads and SQLite state are bounded; the BIN uses memory-mapped lookups.
    """
    info = bin_metadata(bin_path)
    info["sha256"] = file_sha256(bin_path)
    info["database_id"] = info["sha256"]
    identity = collection_identity(source, info["sha256"])
    identity["destination"] = target.full_name
    identity["destination_uuid"] = ensure_target_identity(target)
    connection = open_full_checkpoint(checkpoint_path, identity)
    try:
        scan_collection(source, connection)
        _write_run(target, bin_path, info)
        lookup_pending(connection, target, bin_path, info, retry_failed=retry_failed)
        summary = full_metrics(connection, info)
        write_full_outputs(connection, output_dir, summary)
        return summary
    finally:
        connection.close()
