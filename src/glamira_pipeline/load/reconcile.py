"""Read-only reconciliation of a loaded collection against its source dump.

Three independent checks, recorded in ``load_runs`` as a ``summary_reconcile`` document:

1. Total documents: source stream vs target.
2. Documents per event type (``collection`` field): source vs a ``$group`` on the target.
3. Content: a seeded reservoir sample of source documents is fetched by ``_id``
   and compared byte-for-byte (SHA-256), with decoded equality as a fallback
   in case the server reordered fields.
"""
from __future__ import annotations

from collections import Counter
import hashlib
import logging
from pathlib import Path
import random
import time
import uuid

import bson
from bson.codec_options import CodecOptions
from bson.raw_bson import RawBSONDocument
from pymongo.database import Database

from glamira_pipeline.load.bson_stream import iter_documents, open_member
from glamira_pipeline.load.checkpoint import RUNS_COLLECTION, utcnow
from glamira_pipeline.provenance import file_sha256, git_sha

LOGGER = logging.getLogger(__name__)
RECONCILE_TYPE = "summary_reconcile"
MISSING = "<missing>"


def scan_source(archive: Path, member: str, *, sample_size: int, seed: int,
                pigz: bool | None = None) -> tuple[int, Counter, list[bytes]]:
    """Stream the source once: total count, count per ``collection`` value, and a reservoir sample."""
    rng = random.Random(seed)
    per_type: Counter = Counter()
    sample: list[bytes] = []
    total = 0
    with open_member(archive, member, pigz=pigz) as reader:
        for raw in iter_documents(reader):
            event_type = bson.decode(raw).get("collection", MISSING)
            per_type[event_type if isinstance(event_type, str) else f"<{type(event_type).__name__}>"] += 1
            if len(sample) < sample_size:
                sample.append(raw)
            else:
                slot = rng.randrange(total + 1)
                if slot < sample_size:
                    sample[slot] = raw
            total += 1
    return total, per_type, sample


def target_counts(db: Database, collection: str) -> Counter:
    """Count target documents per ``collection`` value with one server-side ``$group``."""
    pipeline = [{"$group": {"_id": {"$ifNull": ["$collection", MISSING]}, "n": {"$sum": 1}}}]
    return Counter({row["_id"] if isinstance(row["_id"], str) else f"<{type(row['_id']).__name__}>": row["n"]
                    for row in db[collection].aggregate(pipeline, allowDiskUse=True)})


def compare_sample(db: Database, collection: str, sample: list[bytes]) -> dict:
    """Fetch sampled documents by ``_id`` and compare them with the source bytes."""
    raw_coll = db.get_collection(collection, codec_options=CodecOptions(document_class=RawBSONDocument))
    expected = {bson.decode(raw)["_id"]: raw for raw in sample}
    found = {bson.decode(doc.raw)["_id"]: doc.raw for doc in raw_coll.find({"_id": {"$in": list(expected)}})}
    identical = equal_decoded = 0
    for _id, raw in expected.items():
        stored = found.get(_id)
        if stored is None:
            continue
        if hashlib.sha256(stored).digest() == hashlib.sha256(raw).digest():
            identical += 1
        elif bson.decode(stored) == bson.decode(raw):
            equal_decoded += 1
    return {"sampled": len(expected), "found": len(found), "identical_bytes": identical,
            "equal_after_decode": equal_decoded, "missing": len(expected) - len(found),
            "different": len(found) - identical - equal_decoded}


def reconcile(archive: Path, member: str, db: Database, collection: str, *,
              sample_size: int = 1_000, seed: int = 20191001, pigz: bool | None = None) -> dict:
    """Run all checks, store the result in ``load_runs`` and return it (``ok`` is the verdict)."""
    timings = {}
    started = time.perf_counter()
    source_sha = file_sha256(archive)
    timings["hash_s"] = time.perf_counter() - started

    started = time.perf_counter()
    total, source_types, sample = scan_source(archive, member, sample_size=sample_size, seed=seed, pigz=pigz)
    timings["source_scan_s"] = time.perf_counter() - started
    LOGGER.info("source: %s documents, %d event types", f"{total:,}", len(source_types))

    started = time.perf_counter()
    stored_types = target_counts(db, collection)
    timings["target_group_s"] = time.perf_counter() - started

    started = time.perf_counter()
    content = compare_sample(db, collection, sample)
    timings["sample_compare_s"] = time.perf_counter() - started

    type_diffs = {name: {"source": source_types.get(name, 0), "target": stored_types.get(name, 0)}
                  for name in sorted(set(source_types) | set(stored_types))
                  if source_types.get(name, 0) != stored_types.get(name, 0)}
    stored_total = sum(stored_types.values())
    result = {
        "_id": utcnow().strftime("reconcile-%Y%m%dT%H%M%SZ-") + uuid.uuid4().hex[:8], "type": RECONCILE_TYPE,
        "target": f"{db.name}.{collection}",
        "source": {"archive": archive.name, "sha256": source_sha, "member": member},
        "source_documents": total, "target_documents": stored_total,
        "event_types": len(source_types), "event_type_differences": type_diffs,
        "sample": {**content, "seed": seed}, "timings": {k: round(v, 2) for k, v in timings.items()},
        "git_sha": git_sha(), "checked_at": utcnow(),
    }
    result["ok"] = (total == stored_total and not type_diffs
                    and content["identical_bytes"] + content["equal_after_decode"] == content["sampled"])
    db[RUNS_COLLECTION].insert_one(result)
    return result
