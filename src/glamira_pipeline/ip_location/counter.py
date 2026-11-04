"""Scan IPs into RAM and persist a complete, checksummed counter."""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import itertools
import json
import os
from pathlib import Path
import time
from collections.abc import Iterator

from pymongo.collection import Collection

from glamira_pipeline.ip_location.lookup import event_address

SCAN_BATCH = 50_000
COUNTER_FILE = "ip_counter.jsonl"


@dataclass
class CounterScan:
    """Results and timings from one non-resumable in-memory source scan."""

    events: int
    addresses: Counter[tuple[str, int]]
    invalid: Counter[str]
    cursor_seconds: float
    normalize_seconds: float
    started_at: str
    finished_at: str


def scan_in_memory(source: Collection, limit: int | None = None) -> CounterScan:
    """Scan only `ip` using an unsorted 50,000-document cursor and RAM counters.

    Returns valid normalized IP frequencies and invalid-value counts. If the
    scan fails, the caller must start it again; this function writes no checkpoint.
    """
    cursor = source.find({}, {"_id": 0, "ip": 1}).batch_size(SCAN_BATCH)
    if limit is not None:
        if limit < 1:
            raise ValueError("limit must be positive")
        cursor = cursor.limit(limit)
    addresses: Counter[tuple[str, int]] = Counter()
    invalid: Counter[str] = Counter()
    events = 0
    cursor_seconds = normalize_seconds = 0.0
    started_at = datetime.now(timezone.utc).isoformat()
    try:
        while True:
            read_started = time.monotonic()
            batch = list(itertools.islice(cursor, SCAN_BATCH))
            cursor_seconds += time.monotonic() - read_started
            if not batch:
                break
            normalize_started = time.monotonic()
            for event in batch:
                category, address, version = event_address(event)
                if address is None:
                    invalid[category] += 1
                else:
                    addresses[(address, version)] += 1
                events += 1
            normalize_seconds += time.monotonic() - normalize_started
    finally:
        cursor.close()
    return CounterScan(events, addresses, invalid, cursor_seconds, normalize_seconds,
                       started_at, datetime.now(timezone.utc).isoformat())


def _manifest(scan: CounterScan, source_name: str, source_uuid: str,
              bin_info: dict, digest: str) -> dict:
    """Build the counter artifact's reproducibility and integrity metadata."""
    return {
        "record_type": "manifest", "format_version": 1,
        "source": source_name, "source_collection_uuid": source_uuid,
        "bin_sha256": bin_info["sha256"], "events": scan.events,
        "valid_events": sum(scan.addresses.values()),
        "unique_valid_ips": len(scan.addresses), "invalid_events": dict(scan.invalid),
        "counter_sha256": digest, "started_at": scan.started_at,
        "scan_finished_at": scan.finished_at,
    }


def persist_counter(scan: CounterScan, path: Path, source_name: str,
                   source_uuid: str, bin_info: dict) -> dict:
    """Atomically persist the completed counter before any IP lookup begins."""
    if path.exists():
        raise FileExistsError(f"counter artifact already exists: {path}")
    temporary = path.with_name(path.name + ".tmp")
    digest = hashlib.sha256()
    valid_events = 0
    try:
        with temporary.open("xb") as output:
            os.chmod(temporary, 0o600)
            for (address, version), frequency in scan.addresses.items():
                row = json.dumps({"ip": address, "ip_version": version, "events": frequency},
                                 separators=(",", ":"), sort_keys=True).encode() + b"\n"
                output.write(row)
                digest.update(row)
                valid_events += frequency
            manifest = _manifest(scan, source_name, source_uuid, bin_info, digest.hexdigest())
            if valid_events != manifest["valid_events"]:
                raise ValueError("counter event total changed during persistence")
            output.write(json.dumps(manifest, separators=(",", ":"), sort_keys=True).encode() + b"\n")
            output.flush()
            os.fsync(output.fileno())
        os.replace(temporary, path)
        directory_fd = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)
    except BaseException:
        temporary.unlink(missing_ok=True)
        raise
    return manifest


def counter_rows(path: Path) -> Iterator[dict]:
    """Yield rows from a completed JSONL path; raise ValueError on damaged data.

    Validation finishes at exhaustion, so consumers must exhaust this iterator
    before publishing output. Rows already processed must remain in staging.
    """
    digest = hashlib.sha256()
    manifest = None
    row_count = event_count = 0
    with path.open("rb") as source:
        for line in source:
            value = json.loads(line)
            if value.get("record_type") == "manifest":
                manifest = value
                if next(source, None) is not None:
                    raise ValueError("counter artifact has data after its manifest")
                break
            digest.update(line)
            row_count += 1
            event_count += value["events"]
            yield value
    if (manifest is None or manifest.get("format_version") != 1
            or digest.hexdigest() != manifest.get("counter_sha256")
            or row_count != manifest.get("unique_valid_ips")
            or event_count != manifest.get("valid_events")):
        raise ValueError("counter artifact is incomplete or failed its checksum")


