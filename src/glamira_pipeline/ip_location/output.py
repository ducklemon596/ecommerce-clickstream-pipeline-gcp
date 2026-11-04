"""Offline lookup, verified staging output, and safe publication."""
from __future__ import annotations
from collections import Counter
import json
import os
from pathlib import Path
import time
import IP2Location
from pymongo import ReplaceOne
from pymongo.collection import Collection
from glamira_pipeline.ip_location.counter import counter_rows
from glamira_pipeline.ip_location.lookup import lookup_address

LOOKUP_BATCH = 500

def lookup_and_upsert(counter_path: Path, staging: Collection, bin_path: Path,
                      bin_info: dict) -> tuple[dict, int, float]:
    """Lookup persisted unique IPs and idempotently bulk-upsert staging documents."""
    reader = IP2Location.IP2Location(str(bin_path), mode="SHARED_MEMORY")
    status_ips: Counter[str] = Counter()
    status_events: Counter[str] = Counter()
    operations = []
    processed = 0
    started = time.monotonic()
    try:
        for row in counter_rows(counter_path):
            result = lookup_address(reader, row["ip"], bin_info["ipv6_supported"])
            status = result["status"]
            status_ips[status] += 1
            status_events[status] += row["events"]
            document = {"_id": row["ip"], "ip_version": row["ip_version"],
                        **result, "database_id": bin_info["database_id"]}
            operations.append(ReplaceOne({"_id": row["ip"]}, document, upsert=True))
            if len(operations) >= LOOKUP_BATCH:
                staging.bulk_write(operations, ordered=True)
                processed += len(operations)
                operations.clear()
        if operations:
            staging.bulk_write(operations, ordered=True)
            processed += len(operations)
    finally:
        reader.close()
    return {"status_unique_ips": dict(status_ips), "status_events": dict(status_events)}, processed, time.monotonic() - started


def verify_staging(staging: Collection, expected_unique: int) -> dict:
    """Validate staged output counts and status groups before collection publish."""
    groups = {row["_id"]: row["count"] for row in staging.aggregate([
        {"$group": {"_id": "$status", "count": {"$sum": 1}}}
    ])}
    count = sum(groups.values())
    if count != expected_unique:
        raise ValueError(f"staging collection has {count} documents; expected {expected_unique}")
    return {"documents": count, "status_unique_ips": groups}


def publish_collection(staging: Collection, target: str, report_path: Path, report: dict) -> None:
    """Write report atomically, then expose the verified staging collection."""
    temporary = report_path.with_name(report_path.name + ".tmp")
    if report_path.exists():
        raise FileExistsError(f"enrichment report already exists: {report_path}")
    try:
        with temporary.open("x", encoding="utf-8") as output:
            os.chmod(temporary, 0o600)
            json.dump(report, output, indent=2, sort_keys=True)
            output.write("\n")
            output.flush()
            os.fsync(output.fileno())
        # Publish the Mongo namespace only after the complete report is durable.
        staging.rename(target, dropTarget=False)
        os.replace(temporary, report_path)
        directory_fd = os.open(report_path.parent, os.O_RDONLY)
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)
    except BaseException:
        temporary.unlink(missing_ok=True)
        raise


