"""Deterministic local sample preparation for IP enrichment tests."""
from __future__ import annotations

import hashlib
from itertools import islice
from pathlib import Path
from typing import Any

from bson import BSON
from pymongo import ReplaceOne

from glamira_pipeline.provenance import file_sha256
from glamira_pipeline.sampling.json_reader import iter_json_documents

MAX_SAMPLE = 10_000
SOURCE_COLLECTION = "events"
METADATA_COLLECTION = "sample_metadata"
RESULT_COLLECTION = "ip_locations"
RUN_COLLECTION = "enrichment_runs"


def sample_record(row_id: int, event: dict) -> dict:
    """Return the stable MongoDB sample record for an event and ordinal ID."""
    record = {"_id": row_id}
    if "ip" in event:
        record["ip"] = event["ip"]
    return record


def collection_digest(collection: Any) -> tuple[int, str]:
    """Hash the ordered source sample, including BSON types and selected IP fields."""
    digest = hashlib.sha256()
    count = 0
    for event in collection.find({}, {"ip": 1}).sort("_id", 1):
        if event.get("_id") != count or isinstance(event.get("_id"), bool):
            raise ValueError("sample IDs must be contiguous and stable")
        digest.update(BSON.encode(sample_record(count, event)))
        count += 1
    return count, digest.hexdigest()


def seed_sample(db: Any, sample: Path, limit: int) -> dict:
    """Seed at most 10,000 sequential JSON events into an isolated local database.

    Inputs are a MongoDB database, Extended JSON file and row limit. Returns
    source metadata; reruns safely replace matching sample rows. Refuses a
    different input in an existing sample database.
    """
    if not 1 <= limit <= MAX_SAMPLE:
        raise ValueError(f"sample limit must be between 1 and {MAX_SAMPLE}")
    identity = {"sample_sha256": file_sha256(sample), "limit": limit,
                "selection": "sequential JSON prefix", "sample_file": sample.name}
    metadata = db[METADATA_COLLECTION]
    previous = metadata.find_one({"_id": "sample"})
    if previous and previous.get("identity") != identity:
        raise ValueError("existing local sample has a different identity; choose a new database")
    if previous and previous.get("status") == "complete":
        digest = hashlib.sha256()
        count = 0
        for count, event in enumerate(islice(iter_json_documents(sample), limit), start=1):
            digest.update(BSON.encode(sample_record(count - 1, event)))
        actual_count, actual_digest = collection_digest(db[SOURCE_COLLECTION])
        if count != limit or actual_count != limit or actual_digest != digest.hexdigest():
            raise ValueError("existing sample content changed")
        if previous.get("events_sha256") != actual_digest:
            metadata.update_one({"_id": "sample"}, {"$set": {"events_sha256": actual_digest}})
        return identity
    # Never overwrite an unrelated collection without a matching sample marker.
    if previous is None and SOURCE_COLLECTION in db.list_collection_names():
        raise ValueError("events collection already exists without sample metadata")
    metadata.replace_one({"_id": "sample"}, {"_id": "sample", "identity": identity, "status": "seeding"}, upsert=True)
    batch = []
    count = 0
    digest = hashlib.sha256()
    for count, event in enumerate(islice(iter_json_documents(sample), limit), start=1):
        record = sample_record(count - 1, event)
        digest.update(BSON.encode(record))
        batch.append(ReplaceOne({"_id": count - 1}, record, upsert=True))
        if len(batch) == 250:
            db[SOURCE_COLLECTION].bulk_write(batch, ordered=True)
            batch.clear()
    if batch:
        db[SOURCE_COLLECTION].bulk_write(batch, ordered=True)
    if count != limit:
        raise ValueError("sample contains fewer events than requested")
    metadata.replace_one({"_id": "sample"}, {"_id": "sample", "identity": identity,
                                                  "events_sha256": digest.hexdigest(), "status": "complete"})
    return identity
