"""Read-only JSON and MongoDB sources for product extraction."""
from __future__ import annotations

import hashlib
from collections.abc import Iterator
from itertools import islice
from pathlib import Path

from pymongo.collection import Collection
from glamira_pipeline.sampling.json_reader import iter_json_documents

PROJECTION = {"_id": 1, "collection": 1, "product_id": 1, "store_id": 1,
              "current_url": 1, "viewing_product_id": 1, "option": 1}


def json_identity(path: Path) -> dict:
    """Hash a local JSON input in bounded blocks for safe checkpoint reuse."""
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        while block := stream.read(1024 * 1024):
            digest.update(block)
    return {"kind": "json", "path": str(path.resolve()), "sha256": digest.hexdigest()}


def json_events(path: Path, skip: int, remaining: int | None) -> Iterator[dict]:
    """Yield a JSON prefix after committed rows; resume reparses the prefix."""
    yield from islice(iter_json_documents(path), skip, None if remaining is None else skip + remaining)


def mongo_identity(collection: Collection) -> dict:
    """Return namespace, server endpoint and collection UUID without credentials."""
    info = next(collection.database.list_collections(filter={"name": collection.name}), None)
    if not info or not info.get("info", {}).get("uuid"):
        raise ValueError("source collection UUID unavailable")
    return {"kind": "mongodb", "namespace": collection.full_name,
            "endpoint": list(collection.database.client.address),
            "uuid": bytes(info["info"]["uuid"]).hex()}


def mongo_events(collection: Collection, last_id, remaining: int | None, batch_size: int) -> Iterator[dict]:
    """Yield projected events in indexed _id order, closing the cursor on failure.

    Source must be immutable and use ObjectId identifiers. Sorting enables
    keyset resume without skip; no new index or source writes are performed.
    """
    from bson import ObjectId
    query = {} if last_id is None else {"_id": {"$gt": last_id}}
    cursor = collection.find(query, PROJECTION).sort("_id", 1).batch_size(batch_size)
    if remaining is not None:
        cursor = cursor.limit(remaining)
    try:
        for event in cursor:
            if not isinstance(event.get("_id"), ObjectId):
                raise ValueError("MongoDB resume requires ObjectId source identifiers")
            yield event
    finally:
        cursor.close()
