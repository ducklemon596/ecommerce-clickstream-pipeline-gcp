"""Orchestrate sample extraction, offline lookup, MongoDB output and reports."""
from __future__ import annotations

import csv
import json
import os
from pathlib import Path
import sqlite3
from datetime import datetime, timezone
from typing import Any

import IP2Location
from pymongo import ReplaceOne

from glamira_pipeline.ip_location.checkpoint import last_id, open_checkpoint, save_event_batch
from glamira_pipeline.ip_location.lookup import bin_metadata, lookup_address
from glamira_pipeline.ip_location.source import METADATA_COLLECTION, RESULT_COLLECTION, RUN_COLLECTION, SOURCE_COLLECTION, file_sha256, local_server_identity, sample_identity

BATCH_SIZE = 250


def collect_events(db: Any, connection: sqlite3.Connection, limit: int) -> None:
    """Read seeded events in ID order and atomically checkpoint each bounded batch."""
    cursor = db[SOURCE_COLLECTION].find({"_id": {"$gt": last_id(connection)}}, {"ip": 1}).sort("_id", 1).limit(limit).batch_size(BATCH_SIZE)
    batch = []
    for event in cursor:
        batch.append(event)
        if len(batch) == BATCH_SIZE:
            save_event_batch(connection, batch)
            batch.clear()
    if batch:
        save_event_batch(connection, batch)
    if last_id(connection) != limit - 1:
        raise ValueError("sample is incomplete or its IDs changed")


def location_document(row: sqlite3.Row, result: dict, bin_info: dict) -> dict:
    """Build a MongoDB document for one normalized IP and its lookup result."""
    return {"_id": row["ip"], "ip_version": row["version"], **result,
            "database_id": bin_info["database_id"]}


def run_document(bin_path: Path, bin_info: dict) -> dict:
    """Build metadata describing the exact BIN file used for this enrichment."""
    return {"_id": bin_info["database_id"], "database_id": bin_info["database_id"],
            "source": bin_path.name,
            "database_date": bin_info["date"], "database_edition": bin_info["edition"],
            "database_sha256": bin_info["sha256"],
            "processed_at": datetime.now(timezone.utc)}


def process_addresses(db: Any, connection: sqlite3.Connection, bin_path: Path, bin_info: dict, *, retry_failed: bool = False) -> None:
    """Look up pending unique IPs and save idempotent MongoDB results.

    MongoDB is written before SQLite is committed, so a crash between writes
    simply repeats an upsert. Set retry_failed to attempt previous lookup errors.
    """
    if retry_failed:
        with connection:
            connection.execute("UPDATE addresses SET status = 'pending' WHERE status = 'lookup_failed'")
    # SHARED_MEMORY maps the BIN for faster repeated lookups without decoding
    # its entire contents into Python objects.
    bin_info["database_id"] = bin_info["sha256"]
    db[RUN_COLLECTION].replace_one(
        {"_id": bin_info["database_id"]}, run_document(bin_path, bin_info), upsert=True,
    )
    reader = IP2Location.IP2Location(str(bin_path), mode="SHARED_MEMORY")
    try:
        while True:
            row = connection.execute("SELECT * FROM addresses WHERE status = 'pending' ORDER BY ip LIMIT 1").fetchone()
            if row is None:
                break
            result = lookup_address(reader, row["ip"], bin_info["ipv6_supported"])
            db[RESULT_COLLECTION].replace_one({"_id": row["ip"]}, location_document(row, result, bin_info), upsert=True)
            with connection:
                connection.execute("UPDATE addresses SET status=:status, country_code=:country_code, country_name=:country_name, region=:region, city=:city WHERE ip=:ip", {**result, "ip": row["ip"]})
    finally:
        reader.close()
    # Reconcile already checkpointed records if a prior run was interrupted.
    cursor = connection.execute("SELECT * FROM addresses WHERE status != 'pending' ORDER BY ip")
    while rows := cursor.fetchmany(BATCH_SIZE):
        operations = []
        for row in rows:
            result = {key: row[key] for key in ("status", "country_code", "country_name", "region", "city")}
            operations.append(ReplaceOne({"_id": row["ip"]}, location_document(row, result, bin_info), upsert=True))
        db[RESULT_COLLECTION].bulk_write(operations, ordered=True)


def metrics(connection: sqlite3.Connection, bin_info: dict) -> dict:
    """Return event-weighted and unique-IP coverage with aggregate status counts."""
    invalid = {row["category"]: row["events"] for row in connection.execute("SELECT * FROM invalid")}
    statuses = {row["status"]: {"unique_ips": row["ips"], "events": row["events"]} for row in connection.execute("SELECT status, COUNT(*) AS ips, SUM(events) AS events FROM addresses GROUP BY status")}
    events = sum(invalid.values()) + sum(value["events"] for value in statuses.values())
    unique_ips = sum(value["unique_ips"] for value in statuses.values())
    versions = {str(row["version"]): {"unique_ips": row["ips"], "events": row["events"]}
                for row in connection.execute("SELECT version, COUNT(*) AS ips, SUM(events) AS events FROM addresses GROUP BY version")}
    resolved = statuses.get("resolved", {"events": 0, "unique_ips": 0})
    event_coverage = 100 * resolved["events"] / events if events else 0
    return {"events": events, "unique_ips": unique_ips, "invalid_events": invalid,
            "lookup_statuses": statuses, "ip_versions": versions,
            "event_coverage_percent": event_coverage,
            "unique_ip_coverage_percent": 100 * resolved["unique_ips"] / unique_ips if unique_ips else 0,
            "coverage_target_percent": 80, "coverage_target_met": events > 0 and event_coverage >= 80,
            "bin": bin_info, "sample_method": "sequential JSON prefix; non-random"}


def write_outputs(connection: sqlite3.Connection, output_dir: Path, summary: dict) -> None:
    """Write a private IP CSV and aggregate JSON/Markdown reports to output_dir."""
    output_dir.mkdir(parents=True, exist_ok=True)
    csv_path = output_dir / "ip_locations.csv"
    temporary = csv_path.with_suffix(".tmp")
    fields = ("_id", "ip_version", "status", "country_code", "country_name", "region", "city", "database_id")
    with temporary.open("w", newline="", encoding="utf-8") as stream:
        os.chmod(temporary, 0o600)
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        for row in connection.execute("SELECT * FROM addresses ORDER BY ip"):
            result = {key: row[key] for key in ("status", "country_code", "country_name", "region", "city")}
            writer.writerow({"_id": row["ip"], "ip_version": row["version"], **result,
                             "database_id": summary["bin"]["database_id"]})
    os.replace(temporary, csv_path)
    (output_dir / "ip_location_metrics.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    lines = ["# IP geolocation — local sample", "", f"Events: {summary['events']:,}",
             f"Unique valid IPs: {summary['unique_ips']:,}",
             f"Event coverage: {summary['event_coverage_percent']:.2f}% (target: 80%)",
             f"Target met on this sample: {'yes' if summary['coverage_target_met'] else 'no'}",
             f"Unique-IP coverage: {summary['unique_ip_coverage_percent']:.2f}%", "",
             "| Lookup status | Unique IPs | Events |", "| --- | ---: | ---: |"]
    for status, counts in sorted(summary["lookup_statuses"].items()):
        lines.append(f"| {status} | {counts['unique_ips']} | {counts['events']} |")
    lines += ["", "| IP version | Unique IPs | Events |", "| --- | ---: | ---: |"]
    for version, counts in sorted(summary["ip_versions"].items()):
        lines.append(f"| IPv{version} | {counts['unique_ips']} | {counts['events']} |")
    lines += ["", "Invalid or missing event values: " + (", ".join(f"{k}: {v}" for k, v in sorted(summary["invalid_events"].items())) or "none"),
              "", f"BIN edition DB{summary['bin']['edition']}, dated {summary['bin']['date']}; IPv6 supported: {summary['bin']['ipv6_supported']}.",
              "Sample is a sequential, non-random prefix. Location is an estimate; this BIN predates the 2019 events.", ""]
    (output_dir / "ip_location_report.md").write_text("\n".join(lines), encoding="utf-8")


def enrich_sample(db: Any, uri: str, sample: Path, bin_path: Path, checkpoint: Path, output_dir: Path, *, retry_failed: bool = False) -> dict:
    """Run local sample enrichment and return aggregate metrics; resume via SQLite.

    Inputs are a local MongoDB database, URI, BIN file and output paths. A
    changed source collection, URI or BIN is rejected by the checkpoint.
    """
    source = sample_identity(db, sample)
    info = bin_metadata(bin_path)
    info["sha256"] = file_sha256(bin_path)
    info["database_id"] = info["sha256"]
    identity = {"source": source, "server": local_server_identity(uri),
                "bin_sha256": info["sha256"], "destination": RESULT_COLLECTION}
    connection = open_checkpoint(checkpoint, identity)
    try:
        marker = db[METADATA_COLLECTION].find_one({"_id": "ip_locations"})
        if marker and marker.get("identity") != identity:
            raise ValueError("result collection belongs to a different run")
        if not marker:
            if RESULT_COLLECTION in db.list_collection_names():
                raise ValueError("result collection exists without an ownership marker")
            marker = {"_id": "ip_locations", "identity": identity}
            db[METADATA_COLLECTION].insert_one(marker)
        info_collection = next(db.list_collections(filter={"name": RESULT_COLLECTION}), None)
        if marker.get("collection_uuid"):
            if not info_collection or bytes(info_collection["info"]["uuid"]).hex() != marker["collection_uuid"]:
                raise ValueError("result collection was deleted or recreated")
        else:
            # The marker precedes collection creation, so an interrupted setup can resume.
            if not info_collection:
                db.create_collection(RESULT_COLLECTION)
                info_collection = next(db.list_collections(filter={"name": RESULT_COLLECTION}))
            collection_uuid = bytes(info_collection["info"]["uuid"]).hex()
            db[METADATA_COLLECTION].update_one({"_id": "ip_locations"}, {"$set": {"collection_uuid": collection_uuid}})
        collect_events(db, connection, source["limit"])
        process_addresses(db, connection, bin_path, info, retry_failed=retry_failed)
        summary = metrics(connection, info)
        write_outputs(connection, output_dir, summary)
        return summary
    finally:
        connection.close()
