"""Identity of product pipeline inputs (files and MongoDB collections)."""
from __future__ import annotations

import hashlib
from collections.abc import Iterator
from pathlib import Path

from pymongo.collection import Collection

def json_identity(path: Path) -> dict:
    """Hash a local JSON input in bounded blocks for safe checkpoint reuse."""
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        while block := stream.read(1024 * 1024):
            digest.update(block)
    return {"kind": "json", "path": str(path.resolve()), "sha256": digest.hexdigest()}


def mongo_identity(collection: Collection) -> dict:
    """Return namespace, server endpoint and collection UUID without credentials."""
    info = next(collection.database.list_collections(filter={"name": collection.name}), None)
    if not info or not info.get("info", {}).get("uuid"):
        raise ValueError("source collection UUID unavailable")
    return {"kind": "mongodb", "namespace": collection.full_name,
            "endpoint": list(collection.database.client.address),
            "uuid": bytes(info["info"]["uuid"]).hex()}
